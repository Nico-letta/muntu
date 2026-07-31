# Golden Snippet — `src/providers/bridge-payments.service.ts`

> **Couche:** `30-system-integrations` · **Source:** `afriwallet_codebase/src/providers/bridge-payments.service.ts`

Depot bancaire sandbox Bridge API.

```typescript
import { Injectable, InternalServerErrorException } from '@nestjs/common';

interface BridgePaymentUser {
  firstName: string;
  lastName: string;
  externalReference: string;
}

interface CreateBridgePaymentRequestInput {
  amount: number;
  user: BridgePaymentUser;
  label?: string;
  providerId?: number;
  clientReference?: string;
}

interface BridgePaymentsConfig {
  baseUrl: string;
  version: string;
  clientId: string;
  clientSecret: string;
  defaultProviderId: number;
  defaultCurrency: string;
  callbackBaseUrl?: string;
}

@Injectable()
export class BridgePaymentsService {
  private readonly config: BridgePaymentsConfig;

  constructor() {
    const callbackBaseUrl = (process.env.BRIDGE_CALLBACK_BASE_URL ?? '').trim();

    this.config = {
      baseUrl: (process.env.BRIDGE_API_BASE_URL ?? 'https://api.bridgeapi.io').trim(),
      version: (process.env.BRIDGE_API_VERSION ?? '2025-01-15').trim(),
      clientId: (process.env.BRIDGE_CLIENT_ID ?? '').trim(),
      clientSecret: (process.env.BRIDGE_CLIENT_SECRET ?? '').trim(),
      defaultProviderId: Number(process.env.BRIDGE_SANDBOX_PROVIDER_ID ?? '574'),
      defaultCurrency: (process.env.BRIDGE_PAYMENT_CURRENCY ?? 'EUR').trim() || 'EUR',
      callbackBaseUrl: callbackBaseUrl ? callbackBaseUrl.replace(/\/$/, '') : undefined,
    };
  }

  private assertConfig() {
    const missing: string[] = [];
    if (!this.config.clientId) missing.push('BRIDGE_CLIENT_ID');
    if (!this.config.clientSecret) missing.push('BRIDGE_CLIENT_SECRET');

    if (missing.length) {
      throw new InternalServerErrorException(
        `Bridge configuration missing: ${missing.join(', ')}`,
      );
    }
  }

  private headers(): Record<string, string> {
    return {
      'Bridge-Version': this.config.version,
      'Client-Id': this.config.clientId,
      'Client-Secret': this.config.clientSecret,
      'Content-Type': 'application/json',
    };
  }

  async createPaymentRequest(input: CreateBridgePaymentRequestInput): Promise<{ id: string; url?: string }> {
    this.assertConfig();

    const url = `${this.config.baseUrl}/v3/payment/payment-requests`;
    const callbackUrl = this.config.callbackBaseUrl
      ? `${this.config.callbackBaseUrl}/webhooks/bridge/payments`
      : undefined;

    const res = await fetch(url, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({
        callback_url: callbackUrl,
        provider_id: input.providerId ?? this.config.defaultProviderId,
        client_reference: input.clientReference,
        user: {
          first_name: input.user.firstName,
          last_name: input.user.lastName,
          external_reference: input.user.externalReference,
        },
        transactions: [
          {
            amount: input.amount,
            currency: this.config.defaultCurrency,
            label: input.label ?? 'Topup AfriWallet',
          },
        ],
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `Bridge createPaymentRequest failed: ${res.status} ${text}`,
      );
    }

    const data = (await res.json()) as { id?: string; url?: string };
    if (!data.id) {
      throw new InternalServerErrorException(
        'Bridge createPaymentRequest: missing id in response',
      );
    }

    return { id: data.id, url: data.url };
  }

  async getPaymentRequest(paymentRequestId: string): Promise<unknown> {
    this.assertConfig();
    const id = paymentRequestId.trim();
    if (!id) {
      throw new InternalServerErrorException('Bridge getPaymentRequest: paymentRequestId is required');
    }

    const url = `${this.config.baseUrl}/v3/payment/payment-requests/${encodeURIComponent(id)}`;
    const res = await fetch(url, {
      method: 'GET',
      headers: this.headers(),
    });

    const text = await res.text();
    if (!res.ok) {
      throw new InternalServerErrorException(
        `Bridge getPaymentRequest failed: ${res.status} ${text}`,
      );
    }

    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  getCurrency(): string {
    return this.config.defaultCurrency;
  }
}


```
