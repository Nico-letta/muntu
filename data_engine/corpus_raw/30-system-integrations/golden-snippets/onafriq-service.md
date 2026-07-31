# Golden Snippet — `src/providers/onafriq.service.ts`

> **Couche:** `30-system-integrations` · **Source:** `afriwallet_codebase/src/providers/onafriq.service.ts`

Client Onafriq cartes: OAuth, retry HTTP, registration.

```typescript
import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';

interface CreateRemoteCardInput {
  userId: string;
  phoneNumber: string;
  amountFcfa: number;
}

interface RemoteCard {
  token: string;
  lastFour: string;
  passCode: string | null;
  raw: unknown;
}

interface OnafriqConfig {
  idpBaseUrl: string;
  apiBaseUrl: string;
  tokenPath: string;
  registerPersonalizedPath: string;
  username: string;
  password: string;
  programId: string;
  countryCode: string;
  phoneCountryCode: string;
  stateRegion: string;
  city: string;
  addressLine1: string;
  idType: number;
  idValuePrefix: string;
  subCompany: number;
  referredBy: number;
  cardCurrency: string;
}

@Injectable()
export class OnafriqService {
  private readonly logger = new Logger(OnafriqService.name);
  private readonly config: OnafriqConfig;
  private accessToken: string | null = null;
  private accessTokenExpiresAtMs = 0;

  constructor() {
    const idpBaseUrl = process.env.ONAFRIQ_IDP_BASE_URL ?? 'https://cards-sbx.onafriqservices.com';
    const apiBaseUrl = process.env.ONAFRIQ_API_BASE_URL ?? 'https://cards-sbx.onafriqservices.com';
    const subCompany = Number(process.env.ONAFRIQ_SUB_COMPANY ?? '0');
    const referredBy = Number(process.env.ONAFRIQ_REFERRED_BY ?? String(subCompany || 0));
    const idType = Number(process.env.ONAFRIQ_DEFAULT_ID_TYPE ?? '4');

    this.config = {
      idpBaseUrl,
      apiBaseUrl,
      tokenPath: process.env.ONAFRIQ_TOKEN_PATH ?? '/idp/connect/token',
      registerPersonalizedPath:
        process.env.ONAFRIQ_REGISTER_PERSONALIZED_PATH ?? '/rest/api/v1/accounts/personalized',
      username: process.env.ONAFRIQ_CLIENT_USERNAME ?? '',
      password: process.env.ONAFRIQ_CLIENT_PASSWORD ?? '',
      programId: process.env.ONAFRIQ_PROGRAM_ID ?? '',
      countryCode: process.env.ONAFRIQ_DEFAULT_COUNTRY_CODE ?? 'CM',
      phoneCountryCode: process.env.ONAFRIQ_DEFAULT_PHONE_COUNTRY_CODE ?? '237',
      stateRegion: process.env.ONAFRIQ_DEFAULT_STATE_REGION ?? 'CM',
      city: process.env.ONAFRIQ_DEFAULT_CITY ?? 'Douala',
      addressLine1: process.env.ONAFRIQ_DEFAULT_ADDRESS_LINE1 ?? 'AfriWallet user',
      idType,
      idValuePrefix: process.env.ONAFRIQ_DEFAULT_ID_VALUE_PREFIX ?? 'AfriWallet',
      subCompany,
      referredBy,
      cardCurrency: process.env.ONAFRIQ_CARD_CURRENCY ?? 'XAF',
    };
  }

  private getTimeoutMs(): number {
    return Number(process.env.ONAFRIQ_HTTP_TIMEOUT_MS ?? '10000');
  }

  private getRetryCount(): number {
    return Number(process.env.ONAFRIQ_HTTP_RETRY_COUNT ?? '2');
  }

  private getRetryBackoffMs(): number {
    return Number(process.env.ONAFRIQ_HTTP_RETRY_BACKOFF_MS ?? '400');
  }

  private assertConfig() {
    const missing: string[] = [];

    if (!this.config.username) missing.push('ONAFRIQ_CLIENT_USERNAME');
    if (!this.config.password) missing.push('ONAFRIQ_CLIENT_PASSWORD');
    if (!this.config.programId) missing.push('ONAFRIQ_PROGRAM_ID');
    if (!this.config.subCompany) missing.push('ONAFRIQ_SUB_COMPANY');
    if (!this.config.referredBy) missing.push('ONAFRIQ_REFERRED_BY');

    if (missing.length) {
      throw new InternalServerErrorException(
        `Onafriq configuration missing: ${missing.join(', ')}`,
      );
    }
  }

  private getRequestId(prefix = 'zeno'): string {
    return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}`;
  }

  private async sleep(ms: number): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, ms));
  }

  private isRetriableStatus(status: number): boolean {
    return status === 408 || status === 429 || status >= 500;
  }

  private async requestWithRetry(
    correlationId: string,
    url: string,
    init: RequestInit,
  ): Promise<Response> {
    const attempts = Math.max(1, this.getRetryCount() + 1);
    const timeoutMs = Math.max(1000, this.getTimeoutMs());
    let lastError: unknown = null;

    for (let attempt = 1; attempt <= attempts; attempt++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const res = await fetch(url, {
          ...init,
          signal: controller.signal,
        });

        if (res.ok) {
          clearTimeout(timer);
          if (attempt > 1) {
            this.logger.log(
              `[${correlationId}] Onafriq request recovered on attempt ${attempt}/${attempts}`,
            );
          }
          return res;
        }

        if (!this.isRetriableStatus(res.status) || attempt === attempts) {
          clearTimeout(timer);
          return res;
        }

        this.logger.warn(
          `[${correlationId}] Onafriq request attempt ${attempt}/${attempts} failed with status ${res.status}, retrying`,
        );
      } catch (err) {
        lastError = err;
        if (attempt === attempts) {
          clearTimeout(timer);
          break;
        }
        this.logger.warn(
          `[${correlationId}] Onafriq request attempt ${attempt}/${attempts} errored (${err instanceof Error ? err.message : 'unknown error'}), retrying`,
        );
      } finally {
        clearTimeout(timer);
      }

      const delay = this.getRetryBackoffMs() * attempt;
      await this.sleep(delay);
    }

    throw new InternalServerErrorException(
      `Onafriq request failed after retries (${correlationId}): ${lastError instanceof Error ? lastError.message : 'unknown error'}`,
    );
  }

  private parsePhone(rawPhoneNumber: string): { countryCode: string; number: string; full: string } {
    const digits = rawPhoneNumber.replace(/\D/g, '');
    if (digits.length < 10) {
      throw new InternalServerErrorException('Invalid phone number for Onafriq card registration');
    }
    const configuredCc = this.config.phoneCountryCode;
    let countryCode = configuredCc;
    let number = digits;

    if (digits.startsWith(configuredCc) && digits.length > configuredCc.length + 7) {
      number = digits.slice(configuredCc.length);
    } else if (digits.length > 10) {
      countryCode = digits.slice(0, digits.length - 9);
      number = digits.slice(countryCode.length);
    }

    return { countryCode, number, full: `${countryCode}${number}` };
  }

  private formatBirthDateFromUserId(_userId: string): string {
    return process.env.ONAFRIQ_DEFAULT_BIRTH_DATE ?? '01-JAN-1990';
  }

  private buildBasicAuthHeader(): string {
    const encoded = Buffer.from(`${this.config.username}:${this.config.password}`).toString('base64');
    return `Basic ${encoded}`;
  }

  private async getAccessToken(): Promise<string> {
    const now = Date.now();
    if (this.accessToken && now < this.accessTokenExpiresAtMs - 30_000) {
      return this.accessToken;
    }

    const requestId = this.getRequestId('onafriq-token');
    const correlationId = requestId;
    const tokenUrl = `${this.config.idpBaseUrl}${this.config.tokenPath}`;
    const body = new URLSearchParams({ grant_type: 'client_credentials' });

    const res = await this.requestWithRetry(correlationId, tokenUrl, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        Authorization: this.buildBasicAuthHeader(),
        'Content-Type': 'application/x-www-form-urlencoded',
        programId: this.config.programId,
        requestId,
      },
      body: body.toString(),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `Onafriq token request failed (${correlationId}): ${res.status} ${text}`,
      );
    }

    const data = (await res.json()) as {
      access_token?: string;
      expires_in?: number;
    };
    if (!data.access_token) {
      throw new InternalServerErrorException('Onafriq token response missing access_token');
    }

    const expiresInSeconds = Number(data.expires_in ?? 300);
    this.accessToken = data.access_token;
    this.accessTokenExpiresAtMs = Date.now() + Math.max(60, expiresInSeconds) * 1000;
    return this.accessToken;
  }

  private buildCardRegistrationPayload(input: CreateRemoteCardInput) {
    const phone = this.parsePhone(input.phoneNumber);
    const shortUser = input.userId.slice(-8).toUpperCase();
    const firstName = 'AfriWallet';
    const lastName = `U${shortUser}`;
    const preferredName = `${firstName} ${lastName}`.slice(0, 19);

    return {
      firstName,
      middleName: '',
      lastName,
      preferredName,
      otherAccountId: input.userId,
      otherCompanyName: 'AfriWallet',
      address1: this.config.addressLine1,
      address2: '',
      address3: '',
      city: this.config.city,
      country: this.config.countryCode,
      stateRegion: this.config.stateRegion,
      postalCode: '',
      birthDate: this.formatBirthDateFromUserId(input.userId),
      idType: this.config.idType,
      idValue: `${this.config.idValuePrefix}-${shortUser}`,
      mobilePhoneNumber: {
        countryCode: phone.countryCode,
        number: phone.number,
      },
      emailAddress: `${input.userId.slice(-12)}@afriwallet.local`,
      accountSource: 'OTHER',
      referredBy: this.config.referredBy,
      subCompany: this.config.subCompany,
      return: null,
      solId: null,
      bvn: null,
    };
  }

  async createCard(input: CreateRemoteCardInput): Promise<RemoteCard> {
    this.assertConfig();
    const requestId = this.getRequestId('onafriq-create-card');
    const correlationId = requestId;
    const token = await this.getAccessToken();
    const url = `${this.config.apiBaseUrl}${this.config.registerPersonalizedPath}`;
    const payload = this.buildCardRegistrationPayload(input);

    const res = await this.requestWithRetry(correlationId, url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        programId: this.config.programId,
        requestId,
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `Onafriq create card failed (${correlationId}): ${res.status} ${text}`,
      );
    }

    const data = (await res.json()) as {
      registrationAccountId?: number | string;
      registrationLast4Digits?: string;
      registrationPassCode?: string | null;
    };

    const accountId = data.registrationAccountId != null ? String(data.registrationAccountId) : '';
    const lastFour = String(data.registrationLast4Digits ?? '').trim();

    if (!accountId || !lastFour) {
      throw new InternalServerErrorException(
        'Onafriq create card response missing registration identifiers',
      );
    }

    return {
      token: accountId,
      lastFour,
      passCode: data.registrationPassCode ?? null,
      raw: data,
    };
  }
}

```
