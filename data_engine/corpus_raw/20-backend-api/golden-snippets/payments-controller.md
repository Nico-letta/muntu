# Golden Snippet — `src/payments/payments.controller.ts`

> **Couche:** `20-backend-api` · **Source:** `afriwallet_codebase/src/payments/payments.controller.ts`

Routes REST deposit/withdraw et polling status.

```typescript
import { Body, Controller, Get, Param, Post, Req, UseGuards } from '@nestjs/common';
import { IsInt, IsPositive } from 'class-validator';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { PaymentsService } from './payments.service';
import type { Request } from 'express';

class InitiateMomoDepositDto {
  @IsInt()
  @IsPositive()
  amountFcfa!: number;
}

class InitiateMomoWithdrawDto {
  @IsInt()
  @IsPositive()
  amountFcfa!: number;
}

class InitiateBridgeDepositDto {
  @IsInt()
  @IsPositive()
  amountFcfa!: number;
}

type AuthRequest = Request & { user?: { userId?: string; phoneNumber?: string } };

@Controller('payments')
export class PaymentsController {
  constructor(private readonly paymentsService: PaymentsService) {}

  @UseGuards(JwtAuthGuard)
  @Post('deposit/momo')
  async initiateMomoDeposit(@Req() req: AuthRequest, @Body() body: InitiateMomoDepositDto) {
    const phoneNumber = req.user?.phoneNumber;
    if (!phoneNumber) {
      // Le JWT contient phoneNumber (payload), on l'utilise pour initier le débit.
      throw new Error('Missing authenticated phoneNumber');
    }

    return this.paymentsService.initiateMomoDeposit({
      phoneNumber,
      amountFcfa: body.amountFcfa,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Post('withdraw/momo')
  async initiateMomoWithdraw(@Req() req: AuthRequest, @Body() body: InitiateMomoWithdrawDto) {
    const phoneNumber = req.user?.phoneNumber;
    if (!phoneNumber) {
      throw new Error('Missing authenticated phoneNumber');
    }

    return this.paymentsService.initiateMomoWithdraw({
      phoneNumber,
      amountFcfa: body.amountFcfa,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Post('deposit/bridge')
  async initiateBridgeDeposit(@Req() req: AuthRequest, @Body() body: InitiateBridgeDepositDto) {
    const userId = req.user?.userId;
    const phoneNumber = req.user?.phoneNumber;
    if (!userId || !phoneNumber) {
      throw new Error('Missing authenticated user context');
    }
    return this.paymentsService.initiateBridgeDeposit({
      userId,
      phoneNumber,
      amountFcfa: body.amountFcfa,
    });
  }

  /**
   * Fallback robuste si le callback MTN n'est pas reçu.
   * Le referenceId correspond au X-Reference-Id utilisé lors de l'init.
   */
  @UseGuards(JwtAuthGuard)
  @Get('deposit/momo/:referenceId/status')
  async getMomoDepositStatus(
    @Param('referenceId') referenceId: string,
    @Req() req: AuthRequest,
  ) {
    const userId = req.user?.userId;
    if (!userId) {
      throw new Error('Missing authenticated userId');
    }
    return this.paymentsService.syncMomoDepositStatus({
      userId,
      referenceId,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Get('withdraw/momo/:referenceId/status')
  async getMomoWithdrawStatus(
    @Param('referenceId') referenceId: string,
    @Req() req: AuthRequest,
  ) {
    const userId = req.user?.userId;
    if (!userId) {
      throw new Error('Missing authenticated userId');
    }
    return this.paymentsService.syncMomoWithdrawStatus({
      userId,
      referenceId,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Get('deposit/bridge/:paymentRequestId/status')
  async getBridgeDepositStatus(
    @Param('paymentRequestId') paymentRequestId: string,
    @Req() req: AuthRequest,
  ) {
    const userId = req.user?.userId;
    if (!userId) {
      throw new Error('Missing authenticated userId');
    }
    return this.paymentsService.syncBridgeDepositStatus({
      userId,
      paymentRequestId,
    });
  }
}


```
