# Golden Snippet — `src/payments/payments.service.ts`

> **Couche:** `20-backend-api` · **Source:** `afriwallet_codebase/src/payments/payments.service.ts`

Orchestration cash-in/cash-out MoMo, Bridge, polling et compensation.

```typescript
import { BadRequestException, Injectable, InternalServerErrorException } from '@nestjs/common';
import {
  KycStatus,
  PaymentProvider,
  TransactionStatus,
  TransactionType,
} from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { MtnService } from '../providers/mtn.service';
import { BridgePaymentsService } from '../providers/bridge-payments.service';

interface InitiateMomoDepositInput {
  phoneNumber: string;
  amountFcfa: number;
}

interface InitiateMomoWithdrawInput {
  phoneNumber: string;
  amountFcfa: number;
}

interface SyncMomoDepositStatusInput {
  userId: string;
  referenceId: string;
}

interface SyncMomoWithdrawStatusInput {
  userId: string;
  referenceId: string;
}

interface InitiateBridgeDepositInput {
  userId: string;
  phoneNumber: string;
  amountFcfa: number;
}

interface SyncBridgeDepositStatusInput {
  userId: string;
  paymentRequestId: string;
}

export interface PollingStatusResponse {
  provider: string;
  referenceId?: string;
  paymentRequestId?: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILED';
  providerStatus: string;
  isFinal: boolean;
  nextPollInMs: number | null;
  updatedAt: string;
  raw: unknown;
}

@Injectable()
export class PaymentsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly mtn: MtnService,
    private readonly bridge: BridgePaymentsService,
  ) {}

  async initiateMomoDeposit(input: InitiateMomoDepositInput) {
    const { phoneNumber, amountFcfa } = input;
    if (!phoneNumber || !amountFcfa || amountFcfa <= 0) {
      throw new BadRequestException('Invalid phoneNumber or amountFcfa');
    }

    const user = await this.prisma.user.findUnique({
      where: { phoneNumber },
      include: { wallets: true },
    });
    if (!user || user.wallets.length === 0) {
      throw new BadRequestException('User wallet not found');
    }
    if (user.kycStatus !== KycStatus.VERIFIED) {
      throw new BadRequestException('KYC verification required before MoMo deposit');
    }

    const wallet = user.wallets[0];

    // On initie chez MTN et on utilise referenceId comme providerTxId (idempotence webhook).
    const { referenceId, status } = await this.mtn.initiateDebit({
      phoneNumber,
      amountFcfa,
    });

    const currency = this.getMomoCurrency();

    try {
      await this.prisma.transaction.create({
        data: {
          walletId: wallet.id,
          amountFcfa: BigInt(amountFcfa),
          feeFcfa: BigInt(0),
          currency,
          description: 'Dépôt MoMo',
          type: TransactionType.CASH_IN_MOMO,
          status: TransactionStatus.PENDING,
          provider: PaymentProvider.MTN_MOMO,
          providerTxId: referenceId,
          metadata: {
            initiatedBy: 'api',
            phoneNumber,
          },
        },
      });
    } catch (err) {
      // Si la transaction existe déjà (même referenceId), on reste idempotent.
      if (typeof err === 'object' && err && 'code' in err && (err as { code?: string }).code === 'P2002') {
        return { status, referenceId };
      }
      throw new InternalServerErrorException('Failed to persist pending transaction');
    }

    return { status, referenceId };
  }

  async initiateMomoWithdraw(input: InitiateMomoWithdrawInput) {
    const { phoneNumber, amountFcfa } = input;
    if (!phoneNumber || !amountFcfa || amountFcfa <= 0) {
      throw new BadRequestException('Invalid phoneNumber or amountFcfa');
    }

    const user = await this.prisma.user.findUnique({
      where: { phoneNumber },
      include: { wallets: true },
    });
    if (!user || user.wallets.length === 0) {
      throw new BadRequestException('User wallet not found');
    }
    if (user.kycStatus !== KycStatus.VERIFIED) {
      throw new BadRequestException('KYC verification required before MoMo withdraw');
    }

    const wallet = user.wallets[0];
    const amountBigInt = BigInt(amountFcfa);
    if (wallet.balanceFcfa < amountBigInt) {
      throw new BadRequestException('Insufficient wallet balance');
    }

    const { referenceId, status } = await this.mtn.initiateTransfer({
      phoneNumber,
      amountFcfa,
    });

    const currency = this.getMomoCurrency();

    // On décrémente immédiatement le solde en "réservation" (PENDING).
    // En prod, on peut préférer une logique de ledger plus fine (hold/available).
    try {
      await this.prisma.$transaction([
        this.prisma.wallet.update({
          where: { id: wallet.id },
          data: { balanceFcfa: { decrement: amountBigInt } },
        }),
        this.prisma.transaction.create({
          data: {
            walletId: wallet.id,
            amountFcfa: amountBigInt,
            feeFcfa: BigInt(0),
            currency,
            description: 'Retrait MoMo',
            type: TransactionType.CASH_OUT_MOMO,
            status: TransactionStatus.PENDING,
            provider: PaymentProvider.MTN_MOMO,
            providerTxId: referenceId,
            metadata: {
              initiatedBy: 'api',
              phoneNumber,
            },
          },
        }),
      ]);
    } catch (err) {
      if (typeof err === 'object' && err && 'code' in err && (err as { code?: string }).code === 'P2002') {
        return { status, referenceId };
      }
      throw new InternalServerErrorException('Failed to persist pending cash-out transaction');
    }

    return { status, referenceId };
  }

  /**
   * Poll MTN status and (best-effort) sync DB for a given deposit.
   * NOTE: ceci ne remplace pas un vrai callback MTN, c'est un fallback.
   */
  async syncMomoDepositStatus(input: SyncMomoDepositStatusInput) {
    const referenceId = input.referenceId.trim();
    if (!referenceId) {
      throw new BadRequestException('referenceId is required');
    }

    const tx = await this.prisma.transaction.findUnique({
      where: { providerTxId: referenceId },
      include: { wallet: true },
    });
    if (!tx) {
      throw new BadRequestException('Transaction not found for referenceId');
    }
    if (tx.wallet.userId !== input.userId) {
      throw new BadRequestException('Transaction does not belong to authenticated user');
    }

    const status = await this.mtn.getRequestToPayStatus(referenceId);

    // On ne tente pas de mapper exhaustivement (les champs varient selon environnements).
    // On s'appuie sur les champs usuels: status + reason.
    const normalized = status as any;
    const providerStatus = String(normalized?.status ?? '').toUpperCase();

    if (providerStatus === 'SUCCESSFUL' || providerStatus === 'SUCCESS') {
      // Pour un dépôt: si tx est encore PENDING, on crédite et passe en SUCCESS.
      if (tx.status === TransactionStatus.PENDING) {
        await this.prisma.$transaction([
          this.prisma.wallet.update({
            where: { id: tx.walletId },
            data: { balanceFcfa: { increment: tx.amountFcfa } },
          }),
          this.prisma.transaction.update({
            where: { id: tx.id },
            data: {
              status: TransactionStatus.SUCCESS,
              metadata: normalized as any,
            } as any,
          }),
        ]);
      }
    } else if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
      if (tx.status === TransactionStatus.PENDING) {
        await this.prisma.transaction.update({
          where: { id: tx.id },
          data: { status: TransactionStatus.FAILED, metadata: normalized as any } as any,
        });
      }
    }

    return this.buildPollingStatusResponse({
      provider: 'MTN_MOMO',
      referenceId,
      providerStatus,
      raw: normalized,
    });
  }

  async syncMomoWithdrawStatus(input: SyncMomoWithdrawStatusInput) {
    const referenceId = input.referenceId.trim();
    if (!referenceId) {
      throw new BadRequestException('referenceId is required');
    }

    const tx = await this.prisma.transaction.findUnique({
      where: { providerTxId: referenceId },
      include: { wallet: true },
    });
    if (!tx) {
      throw new BadRequestException('Transaction not found for referenceId');
    }
    if (tx.wallet.userId !== input.userId) {
      throw new BadRequestException('Transaction does not belong to authenticated user');
    }
    if (tx.type !== TransactionType.CASH_OUT_MOMO) {
      throw new BadRequestException('referenceId is not a MoMo cash-out transaction');
    }

    const status = await this.mtn.getTransferStatus(referenceId);
    const normalized = status as any;
    const providerStatus = String(normalized?.status ?? '').toUpperCase();

    if (providerStatus === 'SUCCESSFUL' || providerStatus === 'SUCCESS') {
      if (tx.status === TransactionStatus.PENDING) {
        await this.prisma.transaction.update({
          where: { id: tx.id },
          data: { status: TransactionStatus.SUCCESS, metadata: normalized as any } as any,
        });
      }
    } else if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
      if (tx.status === TransactionStatus.PENDING) {
        // Compensation: recrédit si le retrait échoue.
        await this.prisma.$transaction([
          this.prisma.wallet.update({
            where: { id: tx.walletId },
            data: { balanceFcfa: { increment: tx.amountFcfa } },
          }),
          this.prisma.transaction.update({
            where: { id: tx.id },
            data: { status: TransactionStatus.FAILED, metadata: normalized as any } as any,
          }),
        ]);
      }
    }

    return this.buildPollingStatusResponse({
      provider: 'MTN_MOMO',
      referenceId,
      providerStatus,
      raw: normalized,
    });
  }

  async initiateBridgeDeposit(input: InitiateBridgeDepositInput) {
    const { userId, phoneNumber, amountFcfa } = input;
    if (!amountFcfa || amountFcfa <= 0) {
      throw new BadRequestException('Invalid amountFcfa');
    }

    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      include: { wallets: true },
    });
    if (!user || user.wallets.length === 0) {
      throw new BadRequestException('User wallet not found');
    }
    if (user.kycStatus !== KycStatus.VERIFIED) {
      throw new BadRequestException('KYC verification required before Bridge deposit');
    }

    const wallet = user.wallets[0];
    const bridgeResp = await this.bridge.createPaymentRequest({
      amount: amountFcfa,
      user: {
        firstName: 'AfriWallet',
        lastName: phoneNumber.slice(-4),
        externalReference: user.id,
      },
      label: 'Topup wallet AfriWallet',
      clientReference: `afw_${wallet.id}_${Date.now()}`,
    });

    const paymentRequestId = bridgeResp.id;
    const currency = this.bridge.getCurrency();

    try {
      await this.prisma.transaction.create({
        data: {
          walletId: wallet.id,
          amountFcfa: BigInt(amountFcfa),
          feeFcfa: BigInt(0),
          currency,
          description: 'Dépôt bancaire Bridge',
          type: TransactionType.ADJUSTMENT,
          status: TransactionStatus.PENDING,
          provider: PaymentProvider.BRIDGE,
          providerTxId: paymentRequestId,
          metadata: {
            initiatedBy: 'api',
            provider: 'bridge',
            phoneNumber,
            paymentRequestUrl: bridgeResp.url ?? null,
          },
        },
      });
    } catch (err) {
      if (typeof err === 'object' && err && 'code' in err && (err as { code?: string }).code === 'P2002') {
        return { status: 'PENDING', paymentRequestId, url: bridgeResp.url ?? null };
      }
      throw new InternalServerErrorException('Failed to persist pending Bridge transaction');
    }

    return { status: 'PENDING', paymentRequestId, url: bridgeResp.url ?? null };
  }

  async syncBridgeDepositStatus(input: SyncBridgeDepositStatusInput) {
    const paymentRequestId = input.paymentRequestId.trim();
    if (!paymentRequestId) {
      throw new BadRequestException('paymentRequestId is required');
    }

    const tx = await this.prisma.transaction.findUnique({
      where: { providerTxId: paymentRequestId },
      include: { wallet: true },
    });
    if (!tx) {
      throw new BadRequestException('Transaction not found for paymentRequestId');
    }
    if (tx.wallet.userId !== input.userId) {
      throw new BadRequestException('Transaction does not belong to authenticated user');
    }

    const status = await this.bridge.getPaymentRequest(paymentRequestId);
    const normalized = status as any;
    const providerStatus = String(normalized?.status ?? '').toUpperCase();

    if (providerStatus === 'ACSC') {
      if (tx.status === TransactionStatus.PENDING) {
        await this.prisma.$transaction([
          this.prisma.wallet.update({
            where: { id: tx.walletId },
            data: { balanceFcfa: { increment: tx.amountFcfa } },
          }),
          this.prisma.transaction.update({
            where: { id: tx.id },
            data: {
              status: TransactionStatus.SUCCESS,
              metadata: normalized as any,
            } as any,
          }),
        ]);
      }
    } else if (providerStatus === 'RJCT') {
      if (tx.status === TransactionStatus.PENDING) {
        await this.prisma.transaction.update({
          where: { id: tx.id },
          data: {
            status: TransactionStatus.FAILED,
            failureReason: String(normalized?.status_reason ?? 'RJCT'),
            metadata: normalized as any,
          } as any,
        });
      }
    }

    return this.buildPollingStatusResponse({
      provider: 'BRIDGE',
      paymentRequestId,
      providerStatus,
      raw: normalized,
    });
  }

  private getMomoCurrency(): string {
    const fromEnv = (process.env.MTN_MOMO_CURRENCY ?? '').trim();
    if (fromEnv) return fromEnv;
    const target = (process.env.MTN_MOMO_TARGET_ENVIRONMENT ?? 'sandbox').trim().toLowerCase();
    // MTN sandbox est souvent en EUR (d’après leurs use-cases). En prod, on laisse XAF par défaut.
    return target === 'sandbox' ? 'EUR' : 'XAF';
  }

  private buildPollingStatusResponse(input: {
    provider: string;
    referenceId?: string;
    paymentRequestId?: string;
    providerStatus: string;
    raw: unknown;
  }): PollingStatusResponse {
    const normalizedProviderStatus = input.providerStatus || 'UNKNOWN';
    const normalizedStatus = this.toNormalizedStatus(normalizedProviderStatus);
    const isFinal = normalizedStatus !== 'PENDING';

    return {
      provider: input.provider,
      referenceId: input.referenceId,
      paymentRequestId: input.paymentRequestId,
      status: normalizedStatus,
      providerStatus: normalizedProviderStatus,
      isFinal,
      nextPollInMs: isFinal ? null : this.getNextPollInMs(normalizedProviderStatus),
      updatedAt: new Date().toISOString(),
      raw: input.raw,
    };
  }

  private toNormalizedStatus(providerStatus: string): 'PENDING' | 'SUCCESS' | 'FAILED' {
    const s = providerStatus.toUpperCase();
    if (['SUCCESS', 'SUCCESSFUL', 'ACSC'].includes(s)) return 'SUCCESS';
    if (['FAILED', 'REJECTED', 'RJCT', 'CANC', 'CANCELLED', 'CANCELED'].includes(s)) {
      return 'FAILED';
    }
    return 'PENDING';
  }

  private getNextPollInMs(providerStatus: string): number {
    const s = providerStatus.toUpperCase();
    if (['CREA', 'ACTC'].includes(s)) return 2000;
    if (['PDNG', 'PENDING', 'UNKNOWN'].includes(s)) return 10000;
    return 30000;
  }
}


```
