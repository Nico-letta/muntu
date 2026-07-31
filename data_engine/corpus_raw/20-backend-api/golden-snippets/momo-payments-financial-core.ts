/**
 * Golden Snippet — MoMo payments BigInt + compensation (AfriWallet)
 * Source: afriwallet_codebase/src/payments/payments.service.ts
 */

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


// --- excerpt ---

@Injectable()
export class PaymentsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly mtn: MtnService,
    private readonly bridge: BridgePaymentsService,
  ) {}

// --- excerpt ---

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

// --- excerpt ---

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

// --- excerpt ---

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

// --- excerpt ---

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
