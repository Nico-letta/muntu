/**
 * Golden Snippet — Webhook idempotence (AfriWallet)
 * Source: afriwallet_codebase/src/webhooks/webhooks.service.ts
 * Regles: eventKey unique (P2002 ignore), compensation cash-out FAILED.
 */

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

// --- excerpt ---

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

// --- excerpt ---

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
