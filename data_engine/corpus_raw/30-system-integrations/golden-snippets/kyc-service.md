# Golden Snippet — `src/kyc/kyc.service.ts`

> **Couche:** `30-system-integrations` · **Source:** `afriwallet_codebase/src/kyc/kyc.service.ts`

Sessions KYC, mark verified/rejected, SmartSelfie.

```typescript
import { Injectable, NotFoundException } from '@nestjs/common';
import { KycStatus } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { SmileIdService } from '../providers/smile-id.service';

@Injectable()
export class KycService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly smileId: SmileIdService,
  ) {}

  async openKycSession(userId: string, reference: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    if (user.kycStatus === KycStatus.VERIFIED) {
      return {
        id: user.id,
        phoneNumber: user.phoneNumber,
        kycStatus: user.kycStatus,
        kycReference: user.kycReference,
      };
    }

    const updated = await this.prisma.user.update({
      where: { id: userId },
      data: {
        kycStatus: KycStatus.PENDING,
        kycReference: reference,
      },
    });

    return {
      id: updated.id,
      phoneNumber: updated.phoneNumber,
      kycStatus: updated.kycStatus,
      kycReference: updated.kycReference,
    };
  }

  async startKyc(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
    });
  
    if (!user) {
      throw new NotFoundException('User not found');
    }
  
    // Empêcher relance inutile
    if (user.kycStatus === KycStatus.VERIFIED) {
      return {
        message: 'KYC déjà validé',
        status: user.kycStatus,
      };
    }

    // Flow correct: on ouvre une "session" KYC côté backend.
    // Le SDK Smile ID + le webhook décideront VERIFIED/REJECTED.
    const reference = `kyc_${userId}_${Date.now()}`;
    return this.openKycSession(userId, reference);
  }

  async getUserKycState(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        phoneNumber: true,
        kycStatus: true,
        kycReference: true,
      },
    });
    if (!user) {
      throw new NotFoundException('User not found');
    }
    return user;
  }

  async markKycVerified(userId: string, reference: string) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      throw new NotFoundException('User not found');
    }

    if (user.kycStatus === KycStatus.VERIFIED) {
      return {
        id: user.id,
        phoneNumber: user.phoneNumber,
        kycStatus: user.kycStatus,
        kycReference: user.kycReference,
      };
    }

    const updated = await this.prisma.user.update({
      where: { id: userId },
      data: {
        kycStatus: KycStatus.VERIFIED,
        kycReference: reference,
      },
    });

    return {
      id: updated.id,
      phoneNumber: updated.phoneNumber,
      kycStatus: updated.kycStatus,
      kycReference: updated.kycReference,
    };
  }

  async markKycRejected(userId: string, reference?: string) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      throw new NotFoundException('User not found');
    }

    if (user.kycStatus === KycStatus.REJECTED) {
      return {
        id: user.id,
        phoneNumber: user.phoneNumber,
        kycStatus: user.kycStatus,
        kycReference: user.kycReference,
      };
    }

    const updated = await this.prisma.user.update({
      where: { id: userId },
      data: {
        kycStatus: KycStatus.REJECTED,
        kycReference: reference ?? user.kycReference ?? null,
      },
    });

    return {
      id: updated.id,
      phoneNumber: updated.phoneNumber,
      kycStatus: updated.kycStatus,
      kycReference: updated.kycReference,
    };
  }

  async confirmSmartSelfieJob(input: {
    userId: string;
    jobId: string;
    jobType: 2 | 4;
    smileStatus: unknown;
  }) {
    const user = await this.prisma.user.findUnique({ where: { id: input.userId } });
    if (!user) {
      throw new NotFoundException('User not found');
    }

    const payload = input.smileStatus as any;
    const jobSuccess = payload?.job_success === true;
    const jobComplete = payload?.job_complete === true;
    const partner = payload?.result?.PartnerParams ?? payload?.result?.partner_params ?? null;

    // Sécurité: si Smile renvoie un user_id, on exige qu'il corresponde.
    const smileUserId = partner?.user_id ?? null;
    if (smileUserId && String(smileUserId) !== input.userId) {
      throw new NotFoundException('SmartSelfie job does not belong to authenticated user');
    }

    const reason = (partner?.reason ?? null) ? String(partner.reason) : null;

    const now = new Date();

    const updated = await this.prisma.user.update({
      where: { id: input.userId },
      data:
        input.jobType === 4
          ? {
              smartSelfieEnrolledAt: jobSuccess ? now : user.smartSelfieEnrolledAt,
              smartSelfieEnrollJobId: input.jobId,
              smartSelfieEnrollReason: reason,
            }
          : {
              smartSelfieLastAuthAt: jobComplete ? now : user.smartSelfieLastAuthAt,
              smartSelfieLastAuthJobId: input.jobId,
              smartSelfieLastAuthReason: reason,
              smartSelfieLastAuthSuccess: jobSuccess,
            },
    });

    return {
      user: {
        id: updated.id,
        phoneNumber: updated.phoneNumber,
        kycStatus: updated.kycStatus,
        kycReference: updated.kycReference,
        smartSelfieEnrolledAt: updated.smartSelfieEnrolledAt,
        smartSelfieEnrollJobId: updated.smartSelfieEnrollJobId,
        smartSelfieEnrollReason: updated.smartSelfieEnrollReason,
        smartSelfieLastAuthAt: updated.smartSelfieLastAuthAt,
        smartSelfieLastAuthJobId: updated.smartSelfieLastAuthJobId,
        smartSelfieLastAuthReason: updated.smartSelfieLastAuthReason,
        smartSelfieLastAuthSuccess: updated.smartSelfieLastAuthSuccess,
      },
      smile: {
        job_complete: payload?.job_complete ?? null,
        job_success: payload?.job_success ?? null,
        result: payload?.result ?? null,
      },
    };
  }
}


```
