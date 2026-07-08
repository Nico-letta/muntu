# Golden Snippet — `src/providers/smile-id.service.ts`

> **Couche:** `30-system-integrations` · **Source:** `afriwallet_codebase/src/providers/smile-id.service.ts`

Client Smile ID: biometric, document, SmartSelfie.

```typescript
import { BadRequestException, Injectable, InternalServerErrorException } from '@nestjs/common';
import { Signature, WebApi } from 'smile-identity-core';

interface SmileConfig {
  baseUrl: string;
  partnerId: string;
  apiKey: string;
  signatureApiKey: string;
  callbackUrl: string;
  sidServer: number;
}

interface SmileImageDetail {
  image_type_id: number;
  image: string;
}

interface SmileJobOptions {
  return_job_status: boolean;
  return_history: boolean;
  return_image_links: boolean;
}

interface DocumentVerificationInput {
  userId: string;
  jobId?: string;
  imageDetails: SmileImageDetail[];
  country: string;
  idType: string;
  options?: Partial<SmileJobOptions>;
}

interface BiometricKycInput {
  userId: string;
  jobId?: string;
  imageDetails: SmileImageDetail[];
  firstName: string;
  lastName: string;
  country: string;
  idType: string;
  idNumber: string;
  dob: string; // yyyy-mm-dd
  bankCode?: string;
  secondaryIdNumber?: string;
  options?: Partial<SmileJobOptions>;
}

interface SmartSelfieAuthInput {
  userId: string;
  jobId?: string;
  imageDetails: SmileImageDetail[];
  options?: Partial<SmileJobOptions>;
}

interface JobStatusInput {
  userId: string;
  jobId: string;
  jobType?: 1 | 2 | 4 | 11;
  history?: boolean;
  imageLinks?: boolean;
}

interface IdNumberRateLimitResetInput {
  country: string;
  idType: string;
  idNumber: string;
}

interface RequestUploadUrlInput {
  userId: string;
  jobId: string;
  jobType: 1 | 2 | 4 | 11;
  callbackUrl?: string;
  modelParameters?: Record<string, unknown>;
  sourceSdkVersion?: string;
  fileName?: string;
  retry?: boolean;
  extraPartnerParams?: Record<string, unknown>;
}

@Injectable()
export class SmileIdService {
  private readonly config: SmileConfig;
  private readonly webApi: WebApi;

  constructor() {
    const {
      SMILE_ID_BASE_URL,
      SMILE_ID_PARTNER_ID,
      SMILE_ID_API_KEY,
      SMILE_ID_SIGNATURE_API_KEY,
      SMILE_ID_CALLBACK_URL,
      SMILE_ID_SERVER,
    } = process.env;

    this.config = {
      baseUrl: (SMILE_ID_BASE_URL ?? '').replace(/\/$/, ''),
      partnerId: SMILE_ID_PARTNER_ID ?? '',
      apiKey: SMILE_ID_API_KEY ?? '',
      signatureApiKey: SMILE_ID_SIGNATURE_API_KEY ?? '',
      callbackUrl: SMILE_ID_CALLBACK_URL ?? '',
      sidServer: Number(SMILE_ID_SERVER ?? '0'),
    };

    this.webApi = new WebApi(
      this.config.partnerId,
      this.config.callbackUrl,
      this.config.apiKey,
      this.config.sidServer,
    );
  }

  private assertConfig() {
    const missing: string[] = [];
    if (!this.config.partnerId) missing.push('SMILE_ID_PARTNER_ID');
    if (!this.config.apiKey) missing.push('SMILE_ID_API_KEY');
    if (!this.config.signatureApiKey) missing.push('SMILE_ID_SIGNATURE_API_KEY');
    if (!this.config.callbackUrl) missing.push('SMILE_ID_CALLBACK_URL');
    if (!this.config.baseUrl) missing.push('SMILE_ID_BASE_URL');
    if (missing.length) {
      throw new InternalServerErrorException(
        `Smile ID configuration missing: ${missing.join(', ')}`,
      );
    }
  }

  /**
   * Génère la signature que le frontend doit utiliser avec le SDK Smile ID.
   * Retourne timestamp ISO8601, signature, partnerId et callbackUrl.
   */
  generateSignatureForClient(): {
    timestamp: string;
    signature: string;
    partnerId: string;
    callbackUrl: string;
  } {
    this.assertConfig();

    const connection = new Signature(this.config.partnerId, this.config.signatureApiKey);
    const { timestamp: rawTimestamp, signature } = connection.generate_signature();
    const timestamp = String(rawTimestamp);

    return {
      timestamp,
      signature,
      partnerId: this.config.partnerId,
      callbackUrl: this.config.callbackUrl,
    };
  }

  /**
   * Vérifie la signature reçue depuis le webhook Smile ID.
   */
  verifyCallbackSignature(receivedSignature: string, receivedTimestamp: string): boolean {
    this.assertConfig();

    const connection = new Signature(this.config.partnerId, this.config.signatureApiKey);
    return connection.confirm_signature(receivedTimestamp, receivedSignature);
  }

  private throwFriendlyUploadError(status: number, body: any): never {
    // Smile ID renvoie souvent { code: "2215", error: "..." } quand un job existe déjà.
    if (body && String(body.code) === '2215') {
      throw new BadRequestException({
        message:
          "Smile ID: ce job_id existe déjà. Utilise un nouveau jobId, ou relance avec 'retry: true' sur l’endpoint upload-url.",
        provider: 'SMILE_ID',
        code: String(body.code),
        error: body.error ?? body.message ?? 'Job already exists',
      });
    }
    // Smile ID peut renvoyer 2209 quand un user est deja enroll et le job_type n'est pas adapte.
    if (body && String(body.code) === '2209') {
      throw new BadRequestException({
        message:
          "Smile ID: job type incompatible pour cet utilisateur (deja enrolled). Utilise un nouvel utilisateur pour Biometric KYC (job_type 1), ou bascule vers SmartSelfie (job_type 2/4) selon ton use-case.",
        provider: 'SMILE_ID',
        code: String(body.code),
        error: body.error ?? body.message ?? 'Wrong job type for enrolled user',
      });
    }
    throw new InternalServerErrorException({
      message: 'Smile ID upload URL request failed',
      status,
      body,
    });
  }

  private throwFriendlyJobStatusError(status: number, body: any): never {
    if (body && String(body.code) === '2304') {
      throw new BadRequestException({
        message:
          "Smile ID: job introuvable. Verifie le jobId, le user lie au token, et que le job a bien ete cree dans le meme environnement (test/prod).",
        provider: 'SMILE_ID',
        code: String(body.code),
        error: body.error ?? body.message ?? 'Job not found',
      });
    }
    throw new InternalServerErrorException({
      message: 'Smile ID job status request failed',
      status,
      body,
    });
  }

  /**
   * Soumet un job Enhanced Document Verification (job_type 11) via WebApi.
   * Les images doivent suivre le format officiel Smile ID (image_type_id, image).
   */
  async submitDocumentVerification(
    input: DocumentVerificationInput,
  ): Promise<unknown> {
    this.assertConfig();

    const partner_params = {
      job_id: input.jobId ?? `doc_${Date.now()}`,
      user_id: input.userId,
      job_type: 11,
    };

    const id_info = {
      country: input.country,
      id_type: input.idType,
    };

    const options: SmileJobOptions = {
      return_job_status: input.options?.return_job_status ?? true,
      return_history: input.options?.return_history ?? false,
      return_image_links: input.options?.return_image_links ?? false,
    };

    return this.webApi.submit_job(
      partner_params,
      input.imageDetails,
      id_info,
      options,
    );
  }

  /**
   * Soumet un job Biometric KYC (job_type 1) via WebApi.
   */
  async submitBiometricKyc(input: BiometricKycInput): Promise<unknown> {
    this.assertConfig();

    const partner_params = {
      job_id: input.jobId ?? `kyc_${Date.now()}`,
      user_id: input.userId,
      job_type: 1,
    };

    const id_info = {
      first_name: input.firstName,
      last_name: input.lastName,
      country: input.country,
      id_type: input.idType,
      id_number: input.idNumber,
      dob: input.dob,
      bank_code: input.bankCode,
      secondary_id_number: input.secondaryIdNumber,
      entered: 'true',
    };

    const options: SmileJobOptions = {
      return_job_status: input.options?.return_job_status ?? true,
      return_history: input.options?.return_history ?? false,
      return_image_links: input.options?.return_image_links ?? false,
    };

    return this.webApi.submit_job(
      partner_params,
      input.imageDetails,
      id_info,
      options,
    );
  }

  /**
   * Soumet un job SmartSelfie Authentication (job_type 2) via WebApi.
   */
  async submitSmartSelfieAuth(
    input: SmartSelfieAuthInput,
  ): Promise<unknown> {
    this.assertConfig();

    const partner_params = {
      job_id: input.jobId ?? `ssauth_${Date.now()}`,
      user_id: input.userId,
      job_type: 2,
    };

    const options: SmileJobOptions = {
      return_job_status: input.options?.return_job_status ?? true,
      return_history: input.options?.return_history ?? false,
      return_image_links: input.options?.return_image_links ?? false,
    };

    // SmartSelfie Auth n'a pas d'id_info spécifique, on passe un objet vide.
    return this.webApi.submit_job(
      partner_params,
      input.imageDetails,
      {},
      options,
    );
  }

  async getJobStatus(input: JobStatusInput): Promise<unknown> {
    this.assertConfig();
    const sdk = this.webApi as unknown as {
      get_job_status?: (
        partnerParams: Record<string, unknown>,
        options: Record<string, unknown>,
      ) => Promise<unknown>;
    };
    if (typeof sdk.get_job_status !== 'function') {
      throw new InternalServerErrorException('Smile ID SDK does not expose get_job_status');
    }

    const partnerParams = {
      user_id: input.userId,
      job_id: input.jobId,
      job_type: input.jobType ?? 1,
    };
    const options = {
      history: input.history ?? false,
      return_history: input.history ?? false,
      return_images: input.imageLinks ?? false,
    };
    try {
      return await sdk.get_job_status(partnerParams, options);
    } catch (error: any) {
      const status = Number(error?.response?.status ?? 500);
      const body = error?.response?.data ?? {
        message: error instanceof Error ? error.message : 'Unknown Smile ID error',
      };
      this.throwFriendlyJobStatusError(status, body);
    }
  }

  async resetIdNumberRateLimit(input: IdNumberRateLimitResetInput): Promise<unknown> {
    this.assertConfig();
    const connection = new Signature(this.config.partnerId, this.config.signatureApiKey);
    const { timestamp: rawTimestamp, signature } = connection.generate_signature();
    const timestamp = String(rawTimestamp);

    const response = await fetch(`${this.config.baseUrl}/v1/id_number_rate_limit_reset`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        signature,
        timestamp,
        partner_id: this.config.partnerId,
        country: input.country,
        id_type: input.idType,
        id_number: input.idNumber,
      }),
    });

    const payload = await response.json().catch(() => ({ success: false }));
    if (!response.ok) {
      throw new InternalServerErrorException({
        message: 'Smile ID rate limit reset failed',
        status: response.status,
        payload,
      });
    }
    return payload;
  }

  async requestUploadUrl(input: RequestUploadUrlInput): Promise<unknown> {
    this.assertConfig();
    const connection = new Signature(this.config.partnerId, this.config.signatureApiKey);
    const { timestamp: rawTimestamp, signature } = connection.generate_signature();
    const timestamp = String(rawTimestamp);

    const callbackUrl = input.callbackUrl ?? this.config.callbackUrl;
    const partnerParams = {
      job_id: input.jobId,
      user_id: input.userId,
      job_type: input.jobType,
      ...(input.extraPartnerParams ?? {}),
    };

    const payload = {
      callback_url: callbackUrl,
      model_parameters: input.modelParameters ?? {},
      partner_params: partnerParams,
      signature,
      smile_client_id: this.config.partnerId,
      source_sdk: 'rest_api',
      source_sdk_version: input.sourceSdkVersion ?? '1.0.0',
      timestamp,
      file_name: input.fileName ?? undefined,
      retry: input.retry === true ? true : undefined,
    };

    const response = await fetch(`${this.config.baseUrl}/v1/upload`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const body = await response.json().catch(() => ({ success: false }));
    if (!response.ok) {
      this.throwFriendlyUploadError(response.status, body);
    }
    return body;
  }

  async uploadZipToSmile(input: { uploadUrl: string; zipBase64: string }): Promise<{ uploaded: true }> {
    this.assertConfig();
    const uploadUrl = input.uploadUrl.trim();
    if (!uploadUrl) {
      throw new BadRequestException('uploadUrl is required');
    }
    try {
      const parsed = new URL(uploadUrl);
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        throw new BadRequestException('uploadUrl must be a valid http(s) URL');
      }
    } catch {
      throw new BadRequestException('uploadUrl must be a valid URL from the previous upload-url step');
    }

    const cleaned = input.zipBase64.replace(/\s+/g, '');
    if (!/^[A-Za-z0-9+/=]+$/.test(cleaned)) {
      throw new BadRequestException('zipBase64 must be a valid base64 string');
    }
    const binary = Buffer.from(cleaned, 'base64');
    if (!binary.length) {
      throw new BadRequestException('zipBase64 payload is empty or invalid');
    }

    const response = await fetch(uploadUrl, {
      method: 'PUT',
      headers: { 'content-type': 'application/zip' },
      body: binary,
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new InternalServerErrorException({
        message: 'Smile ID ZIP upload failed',
        status: response.status,
        body,
      });
    }
    return { uploaded: true };
  }
}


```
