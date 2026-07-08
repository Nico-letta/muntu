# Golden Snippet — `src/virtual-cards/virtual-cards.service.ts`

> **Couche:** `30-system-integrations` · **Source:** `afriwallet_codebase/src/virtual-cards/virtual-cards.service.ts`

Emission carte virtuelle Onafriq avec debit wallet atomique.

```typescript
import { BadRequestException, Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import { CardProvider, PaymentProvider, Prisma, TransactionStatus, TransactionType } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { OnafriqService } from '../providers/onafriq.service';

interface CreateVirtualCardInput {
  walletId: string;
  amountFcfa: number;
  userId: string;
  requireVerifiedKyc?: boolean;
}

@Injectable()
export class VirtualCardsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly onafriq: OnafriqService,
  ) {}

  async createVirtualCard(input: CreateVirtualCardInput) {
    const { walletId, amountFcfa, userId, requireVerifiedKyc = true } = input;

    if (!walletId || !amountFcfa) {
      throw new BadRequestException('Missing required fields');
    }

    const wallet = await this.prisma.wallet.findFirst({
      where: { id: walletId, userId },
      include: { user: true },
    });

    if (!wallet) {
      throw new NotFoundException('Wallet not found');
    }

    if (requireVerifiedKyc && wallet.user.kycStatus !== 'VERIFIED') {
      throw new ForbiddenException('KYC must be VERIFIED to create a virtual card');
    }

    const amountBigInt = BigInt(amountFcfa);

    if (wallet.balanceFcfa < amountBigInt) {
      throw new BadRequestException('Insufficient wallet balance');
    }

    const remoteCard = await this.onafriq.createCard({
      userId: wallet.user.id,
      phoneNumber: wallet.user.phoneNumber,
      amountFcfa,
    });
    const lastFour = remoteCard.lastFour;
    const cardToken = remoteCard.token;

    const [updatedWallet, virtualCard, transaction] = await this.prisma.$transaction([
      this.prisma.wallet.update({
        where: { id: wallet.id },
        data: {
          balanceFcfa: {
            decrement: amountBigInt,
          },
        },
      }),
      this.prisma.virtualCard.create({
        data: {
          walletId: wallet.id,
          provider: CardProvider.ONAFRIQ,
          lastFour,
          cardToken,
        },
      }),
      this.prisma.transaction.create({
        data: {
          walletId: wallet.id,
          amountFcfa: amountBigInt,
          type: TransactionType.CARD_ISSUANCE_FEE,
          status: TransactionStatus.SUCCESS,
          provider: PaymentProvider.ONAFRIQ,
          providerTxId: cardToken,
          metadata: {
            onafriq: remoteCard.raw as Prisma.InputJsonValue,
            registrationPassCode: remoteCard.passCode,
          } as Prisma.InputJsonValue,
        },
      }),
    ]);

    return {
      wallet: {
        id: updatedWallet.id,
        balanceFcfa: Number(updatedWallet.balanceFcfa),
      },
      virtualCard: {
        id: virtualCard.id,
        walletId: virtualCard.walletId,
        provider: virtualCard.provider,
        lastFour: virtualCard.lastFour,
        isFrozen: virtualCard.isFrozen,
      },
      transaction: {
        id: transaction.id,
        walletId: transaction.walletId,
        amountFcfa: Number(transaction.amountFcfa),
        type: transaction.type,
        status: transaction.status,
        provider: transaction.provider,
        createdAt: transaction.createdAt,
      },
    };
  }
}


```
