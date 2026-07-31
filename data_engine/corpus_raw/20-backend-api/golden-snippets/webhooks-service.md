# Golden Snippet — `src/webhooks/webhooks.service.ts`

> **Couche:** `20-backend-api` · **Source:** `afriwallet_codebase/src/webhooks/webhooks.service.ts`

Callbacks MTN, Smile, Onafriq, Bridge avec idempotence eventKey.

```typescript
import {
  BadRequestException,
  ForbiddenException,
  Injectable,
  Logger,
} from '@nestjs/common';
import { PaymentProvider, Prisma, TransactionStatus, TransactionType } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { KycService } from '../kyc/kyc.service';

interface SmileWebhookBody {
  signature?: string;
  timestamp?: string;
  job_success?: boolean;
  result?: {
    PartnerParams?: {
      user_id?: string;
      job_id?: string;
    };
  };
}

@Injectable()
export class WebhooksService {
  private readonly logger = new Logger(WebhooksService.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly kycService: KycService,
  ) {}

  /**
   * Webhook MTN MoMo (Collections RequestToPay) – prod-ready path.
   * Le callback URL inclut le referenceId (X-Reference-Id) => on peut corréler en DB via providerTxId.
   *
   * Le payload exact MTN peut varier; on traite de manière tolérante en lisant `status`/`reason`.
   */
  async handleMtnRequestToPayCallback(input: { referenceId: string; payload: unknown; requestIp?: string | null }) {
    const referenceId = input.referenceId?.trim();
    if (!referenceId) {
      throw new BadRequestException('Missing referenceId');
    }

    const payload = input.payload as any;
    const providerStatus = String(payload?.status ?? '').toUpperCase();
    const reason = payload?.reason ? String(payload.reason) : null;

    // Allowlist IP optionnelle (durcissement). Format: "1.2.3.4,5.6.7.8"
    const allowlistRaw = (process.env.MTN_MOMO_WEBHOOK_IP_ALLOWLIST ?? '').trim();
    if (allowlistRaw) {
      const allowed = allowlistRaw
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const requestIp = (input.requestIp ?? '').trim();
      if (!requestIp || !allowed.includes(requestIp)) {
        this.logger.warn(`MTN callback blocked by allowlist ip=${requestIp || 'unknown'} referenceId=${referenceId}`);
        throw new ForbiddenException('MTN callback rejected');
      }
    }

    const tx = await this.prisma.transaction.findUnique({
      where: { providerTxId: referenceId },
      include: { wallet: true },
    });
    if (!tx) {
      // On renvoie 200 pour éviter les retries côté provider, mais on log l'anomalie.
      this.logger.warn(`MTN callback received for unknown referenceId=${referenceId}`);
      return { received: true };
    }

    // Audit + idempotence en base, comme Smile ID.
    const eventKey = `mtn:r2p:${referenceId}`;
    try {
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.create({
        data: {
          provider: PaymentProvider.MTN_MOMO,
          eventKey,
          userId: tx.wallet.userId,
          kycReference: null,
          payload: payload as unknown as Prisma.InputJsonValue,
        },
      });
    } catch (err) {
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2002') {
        this.logger.warn(`Duplicate MTN webhook ignored for eventKey=${eventKey}`);
        return { received: true };
      }
      throw err;
    }

    // Si déjà finalisée, idempotent.
    if (tx.status === TransactionStatus.SUCCESS || tx.status === TransactionStatus.FAILED) {
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { processedAt: new Date() },
      });
      return { received: true };
    }

    try {
      if (providerStatus === 'SUCCESSFUL' || providerStatus === 'SUCCESS') {
        if (tx.type === TransactionType.CASH_IN_MOMO) {
          // Dépôt: créditer le wallet et finaliser.
          await this.prisma.$transaction([
            this.prisma.wallet.update({
              where: { id: tx.walletId },
              data: { balanceFcfa: { increment: tx.amountFcfa } },
            }),
            this.prisma.transaction.update({
              where: { id: tx.id },
              data: ({
                status: TransactionStatus.SUCCESS,
                metadata: payload as unknown as Prisma.InputJsonValue,
              } as any),
            }),
          ]);
        } else if (tx.type === TransactionType.CASH_OUT_MOMO) {
          // Retrait: rien à créditer (déjà décrémenté), juste finaliser.
          await this.prisma.transaction.update({
            where: { id: tx.id },
            data: ({
              status: TransactionStatus.SUCCESS,
              metadata: payload as unknown as Prisma.InputJsonValue,
            } as any),
          });
        } else {
          await this.prisma.transaction.update({
            where: { id: tx.id },
            data: ({
              status: TransactionStatus.SUCCESS,
              metadata: payload as unknown as Prisma.InputJsonValue,
            } as any),
          });
        }

        await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
          where: { eventKey },
          data: { processedAt: new Date() },
        });
        return { received: true };
      }

      if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
        if (tx.type === TransactionType.CASH_OUT_MOMO) {
          // Compensation: on recrédite le solde si un cash-out échoue.
          await this.prisma.$transaction([
            this.prisma.wallet.update({
              where: { id: tx.walletId },
              data: { balanceFcfa: { increment: tx.amountFcfa } },
            }),
            this.prisma.transaction.update({
              where: { id: tx.id },
              data: ({
                status: TransactionStatus.FAILED,
                failureReason: reason,
                metadata: payload as unknown as Prisma.InputJsonValue,
              } as any),
            }),
          ]);
        } else {
          await this.prisma.transaction.update({
            where: { id: tx.id },
            data: ({
              status: TransactionStatus.FAILED,
              failureReason: reason,
              metadata: payload as unknown as Prisma.InputJsonValue,
            } as any),
          });
        }

        await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
          where: { eventKey },
          data: { processedAt: new Date() },
        });
        return { received: true };
      }

      // Statut non-final => on enregistre le payload en metadata pour debug.
      await this.prisma.transaction.update({
        where: { id: tx.id },
        data: ({ metadata: payload as unknown as Prisma.InputJsonValue } as any),
      });
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { processedAt: new Date() },
      });
      return { received: true };
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown MTN webhook processing error';
      this.logger.error(`MTN webhook processing failed eventKey=${eventKey}: ${msg}`);
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { error: msg },
      });
      throw err;
    }
  }

  async handleOnafriqWebhook(payload: unknown): Promise<void> {
    const body = payload as Record<string, unknown>;
    const requestId = body.requestId != null ? String(body.requestId) : null;
    const customerId =
      body.customerId != null
        ? String(body.customerId)
        : body.accountId != null
          ? String(body.accountId)
          : null;
    const transactionId = body.transactionId != null ? String(body.transactionId) : null;
    const notificationType = body.notificationType != null ? String(body.notificationType) : 'unknown';
    const eventKey = `onafriq:${notificationType}:${requestId ?? 'no-request-id'}:${transactionId ?? customerId ?? 'unknown'}`;

    try {
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.create({
        data: {
          provider: PaymentProvider.ONAFRIQ,
          eventKey,
          userId: null,
          kycReference: null,
          payload: body as unknown as Prisma.InputJsonValue,
        },
      });
    } catch (err) {
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2002') {
        return;
      }
      throw err;
    }

    try {
      const lastFour =
        body.lastFourDigits != null
          ? String(body.lastFourDigits)
          : body.registrationLast4Digits != null
            ? String(body.registrationLast4Digits)
            : null;
      const cardStatus = body.cardStatus != null ? String(body.cardStatus).toUpperCase() : null;
      const shouldFreeze = cardStatus
        ? ['IA', 'LC', 'SC', 'DEACTIVATED', 'EX', 'INACTIVE', 'LOSTORSTOLEN'].includes(cardStatus)
        : null;

      if (customerId) {
        await this.prisma.virtualCard.updateMany({
          where: { cardToken: customerId },
          data: shouldFreeze == null ? {} : { isFrozen: shouldFreeze },
        });
      } else if (lastFour && shouldFreeze != null) {
        await this.prisma.virtualCard.updateMany({
          where: { lastFour },
          data: { isFrozen: shouldFreeze },
        });
      }

      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { processedAt: new Date() },
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown Onafriq webhook processing error';
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { error: msg },
      });
      throw err;
    }
  }

  async handleBridgePaymentsWebhook(payload: unknown): Promise<{ received: true }> {
    const body = payload as any;
    const type = String(body?.type ?? '');
    const content = body?.content ?? {};

    const paymentRequestId = String(content?.payment_request_id ?? '').trim();
    if (!paymentRequestId) {
      return { received: true };
    }

    const eventKey = `bridge:payments:${type}:${paymentRequestId}:${String(content?.status ?? '')}`;
    try {
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.create({
        data: {
          provider: PaymentProvider.BRIDGE,
          eventKey,
          userId: null,
          kycReference: null,
          payload: body as unknown as Prisma.InputJsonValue,
        },
      });
    } catch (err) {
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2002') {
        return { received: true };
      }
      throw err;
    }

    const tx = await this.prisma.transaction.findUnique({
      where: { providerTxId: paymentRequestId },
      include: { wallet: true },
    });
    if (!tx) {
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { processedAt: new Date() },
      });
      return { received: true };
    }

    const providerStatus = String(content?.status ?? '').toUpperCase();
    if (providerStatus === 'ACSC' && tx.status === TransactionStatus.PENDING) {
      await this.prisma.$transaction([
        this.prisma.wallet.update({
          where: { id: tx.walletId },
          data: { balanceFcfa: { increment: tx.amountFcfa } },
        }),
        this.prisma.transaction.update({
          where: { id: tx.id },
          data: { status: TransactionStatus.SUCCESS, metadata: body as any } as any,
        }),
      ]);
    } else if (providerStatus === 'RJCT' && tx.status === TransactionStatus.PENDING) {
      await this.prisma.transaction.update({
        where: { id: tx.id },
        data: {
          status: TransactionStatus.FAILED,
          failureReason: String(content?.status_reason ?? 'RJCT'),
          metadata: body as any,
        } as any,
      });
    } else {
      await this.prisma.transaction.update({
        where: { id: tx.id },
        data: { metadata: body as any } as any,
      });
    }

    await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
      where: { eventKey },
      data: { processedAt: new Date() },
    });
    return { received: true };
  }

  async handleSmileIdWebhook(body: SmileWebhookBody): Promise<{ received: true }> {
    const userId = body.result?.PartnerParams?.user_id ?? null;
    const jobId = body.result?.PartnerParams?.job_id ?? null;
    const signature = body.signature ?? '';
    const timestamp = body.timestamp ?? '';

    // Idempotence: job_id si présent, sinon fallback signature+timestamp+userId.
    const eventKey =
      jobId?.trim() ||
      `smile:${userId ?? 'unknown'}:${timestamp.trim()}:${signature.trim()}`;

    // Audit + idempotence en base
    try {
      const user = userId ? await this.kycService.getUserKycState(userId) : null;

      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.create({
        data: {
          provider: PaymentProvider.SMILE_ID,
          eventKey,
          userId,
          kycReference: user?.kycReference ?? null,
          payload: body as unknown as Prisma.InputJsonValue,
        },
      });
    } catch (err) {
      // Si eventKey existe déjà => on considère reçu (idempotent)
      // Prisma P2002: unique constraint failed
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2002') {
        this.logger.warn(`Duplicate Smile webhook ignored for eventKey=${eventKey}`);
        return { received: true };
      }
      throw err;
    }

    try {
      // Si on n'a pas de user_id, on s'arrête là (audit only).
      if (!userId) {
        await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
          where: { eventKey },
          data: { processedAt: new Date() },
        });
        this.logger.warn(`Smile webhook received without user_id eventKey=${eventKey}`);
        return { received: true };
      }

      const user = await this.kycService.getUserKycState(userId);
      if (!user.kycReference) {
        // Pas de session KYC => on garde l'event en audit mais on ne touche pas le user.
        await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
          where: { eventKey },
          data: { processedAt: new Date() },
        });
        this.logger.warn(`Smile webhook user without kycReference userId=${userId}`);
        return { received: true };
      }

      // États finaux => idempotent.
      if (user.kycStatus === 'VERIFIED' || user.kycStatus === 'REJECTED') {
        await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
          where: { eventKey },
          data: { processedAt: new Date() },
        });
        return { received: true };
      }

      if (body.job_success === true) {
        await this.kycService.markKycVerified(userId, user.kycReference);
      } else {
        await this.kycService.markKycRejected(userId, user.kycReference);
      }

      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { processedAt: new Date() },
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown webhook processing error';
      this.logger.error(`Smile webhook processing failed eventKey=${eventKey}: ${errorMessage}`);
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { error: errorMessage },
      });
      throw err;
    }

    return { received: true };
  }

  private toWalletResponse(wallet: { id: string; balanceFcfa: bigint }) {
    return {
      id: wallet.id,
      balanceFcfa: Number(wallet.balanceFcfa),
    };
  }

  private toTransactionResponse(tx: {
    id: string;
    walletId: string;
    amountFcfa: bigint;
    type: TransactionType;
    status: TransactionStatus;
    provider: PaymentProvider | null;
    providerTxId: string | null;
    createdAt: Date;
  }) {
    return {
      id: tx.id,
      walletId: tx.walletId,
      amountFcfa: Number(tx.amountFcfa),
      type: tx.type,
      status: tx.status,
      provider: tx.provider,
      providerTxId: tx.providerTxId,
      createdAt: tx.createdAt,
    };
  }
}


```
