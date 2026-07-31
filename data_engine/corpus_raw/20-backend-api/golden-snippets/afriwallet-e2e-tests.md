# AfriWallet E2E Test Specifications

## `kyc.e2e-spec.ts`

```typescript
import { INestApplication, ValidationPipe, CanActivate, ExecutionContext } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { KycController } from '../src/kyc/kyc.controller';
import { KycService } from '../src/kyc/kyc.service';
import { SmileIdService } from '../src/providers/smile-id.service';
import { JwtAuthGuard } from '../src/auth/jwt-auth.guard';

class TestJwtGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const req = context.switchToHttp().getRequest();
    req.user = { userId: 'user_test_1', phoneNumber: '+234000000000' };
    return true;
  }
}

describe('KYC endpoints (e2e-lite)', () => {
  let app: INestApplication;

  const kycServiceMock = {
    startKyc: jest.fn(),
    openKycSession: jest.fn(),
  };

  const smileIdServiceMock = {
    generateSignatureForClient: jest.fn(),
    submitBiometricKyc: jest.fn(),
    submitDocumentVerification: jest.fn(),
    submitSmartSelfieAuth: jest.fn(),
    getJobStatus: jest.fn(),
    resetIdNumberRateLimit: jest.fn(),
    requestUploadUrl: jest.fn(),
    uploadZipToSmile: jest.fn(),
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    kycServiceMock.openKycSession.mockResolvedValue({
      id: 'user_test_1',
      phoneNumber: '+234000000000',
      kycStatus: 'PENDING',
      kycReference: 'kyc_user_test_1_123',
    });
    smileIdServiceMock.submitBiometricKyc.mockResolvedValue({ ok: true });
    smileIdServiceMock.submitDocumentVerification.mockResolvedValue({ ok: true });
    smileIdServiceMock.submitSmartSelfieAuth.mockResolvedValue({ ok: true });
    smileIdServiceMock.generateSignatureForClient.mockResolvedValue({
      timestamp: new Date().toISOString(),
      signature: 'signature',
      partnerId: 'partner',
      callbackUrl: 'https://example.com/webhooks/smile-id',
    });
    smileIdServiceMock.getJobStatus.mockResolvedValue({ job_complete: true });
    smileIdServiceMock.resetIdNumberRateLimit.mockResolvedValue({
      success: true,
      message: 'Rate limit reset successful',
    });
    smileIdServiceMock.requestUploadUrl.mockResolvedValue({
      smile_job_id: '000001',
      upload_url: 'https://signed-url.example.com/upload',
    });
    smileIdServiceMock.uploadZipToSmile.mockResolvedValue({ uploaded: true });

    const moduleFixture: TestingModule = await Test.createTestingModule({
      controllers: [KycController],
      providers: [
        { provide: KycService, useValue: kycServiceMock },
        { provide: SmileIdService, useValue: smileIdServiceMock },
      ],
    })
      .overrideGuard(JwtAuthGuard)
      .useClass(TestJwtGuard)
      .compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    );
    await app.init();
  });

  afterEach(async () => {
    await app.close();
  });

  it('rejects biometric NG/NIN with non-11-digit idNumber', async () => {
    await request(app.getHttpServer())
      .post('/kyc/biometric')
      .send({
        firstName: 'John',
        lastName: 'Doe',
        country: 'NG',
        idType: 'NIN',
        idNumber: '12345',
        dob: '1990-01-01',
        imageDetails: [{ image_type_id: 0, image: 'abc' }],
      })
      .expect(400);
  });

  it('rejects biometric with NIN outside NG', async () => {
    await request(app.getHttpServer())
      .post('/kyc/biometric')
      .send({
        firstName: 'John',
        lastName: 'Doe',
        country: 'CM',
        idType: 'NIN',
        idNumber: '12345678901',
        dob: '1990-01-01',
        imageDetails: [{ image_type_id: 0, image: 'abc' }],
      })
      .expect(400);
  });

  it('requires reason for smartselfie auth', async () => {
    await request(app.getHttpServer())
      .post('/kyc/smartselfie/auth')
      .send({
        imageDetails: [{ image_type_id: 0, image: 'abc' }],
      })
      .expect(400);
  });

  it('requires bankCode for NG/BANK_ACCOUNT', async () => {
    await request(app.getHttpServer())
      .post('/kyc/biometric')
      .send({
        firstName: 'John',
        lastName: 'Doe',
        country: 'NG',
        idType: 'BANK_ACCOUNT',
        idNumber: '0123456789',
        dob: '1990-01-01',
        imageDetails: [{ image_type_id: 0, image: 'abc' }],
      })
      .expect(400);
  });

  it('accepts smartselfie auth with valid reason', async () => {
    const response = await request(app.getHttpServer())
      .post('/kyc/smartselfie/auth')
      .send({
        reason: 'large_withdrawal',
        imageDetails: [{ image_type_id: 0, image: 'abc' }],
      })
      .expect(201);

    expect(response.body.reason).toBe('large_withdrawal');
    expect(response.body.jobId).toContain('large_withdrawal');
  });

  it('returns Smile job status through utility endpoint', async () => {
    const response = await request(app.getHttpServer())
      .post('/kyc/utils/job-status')
      .send({
        jobId: 'job_123',
        history: true,
        imageLinks: false,
      })
      .expect(201);

    expect(response.body).toEqual({ job_complete: true });
    expect(smileIdServiceMock.getJobStatus).toHaveBeenCalledWith({
      userId: 'user_test_1',
      jobId: 'job_123',
      history: true,
      imageLinks: false,
    });
  });

  it('creates biometric upload-url in REST upload flow', async () => {
    const response = await request(app.getHttpServer())
      .post('/kyc/biometric/upload-url')
      .send({
        country: 'NG',
        idType: 'NIN_V2',
        idNumber: '00000000000',
        firstName: 'John',
        lastName: 'Doe',
        dob: '1990-01-01',
      })
      .expect(201);

    expect(response.body.upload.upload_url).toBe('https://signed-url.example.com/upload');
    expect(smileIdServiceMock.requestUploadUrl).toHaveBeenCalled();
  });

  it('uploads zip payload to Smile signed URL', async () => {
    const response = await request(app.getHttpServer())
      .post('/kyc/smartselfie/upload-zip')
      .send({
        uploadUrl: 'https://signed-url.example.com/upload',
        zipBase64: 'UEsDBAoAAAAAA',
      })
      .expect(201);

    expect(response.body).toEqual({ uploaded: true });
    expect(smileIdServiceMock.uploadZipToSmile).toHaveBeenCalledWith({
      uploadUrl: 'https://signed-url.example.com/upload',
      zipBase64: 'UEsDBAoAAAAAA',
    });
  });

  it('creates document verification upload-url for Congo CG', async () => {
    const response = await request(app.getHttpServer())
      .post('/kyc/document-verification/upload-url')
      .send({
        country: 'CG',
        idType: 'IDENTITY_CARD',
        sandboxResult: '0',
      })
      .expect(201);

    expect(response.body.upload.upload_url).toBe('https://signed-url.example.com/upload');
  });

  it('submits document verification for Congo CG', async () => {
    const response = await request(app.getHttpServer())
      .post('/kyc/document-verification')
      .send({
        country: 'CG',
        idType: 'IDENTITY_CARD',
        imageDetails: [
          { image_type_id: 0, image: 'selfie_base64' },
          { image_type_id: 1, image: 'id_front_base64' },
        ],
      })
      .expect(201);

    expect(response.body.jobId).toContain('doc_');
    expect(smileIdServiceMock.submitDocumentVerification).toHaveBeenCalled();
  });
});

```

