/**
 * Golden Snippet — MTN MoMo client (AfriWallet)
 * Source: afriwallet_codebase/src/providers/mtn.service.ts
 */

import { Injectable, InternalServerErrorException } from '@nestjs/common';
import { randomUUID } from 'crypto';

interface InitiateMomoDebitInput {
  phoneNumber: string;
  amountFcfa: number;
}

interface InitiateMomoTransferInput {
  phoneNumber: string;
  amountFcfa: number;
}

interface MtnConfig {
  baseUrl: string;
  subscriptionKey: string;
  apiUser: string;
  apiKey: string;
  tokenPath: string;
  requestToPayPath: string;
  requestToPayStatusPath: string;
  callbackBaseUrl?: string;
  currency: string;
  targetEnvironment: string;
  disbursementTokenPath: string;
  transferPath: string;
  transferStatusPath: string;
}

@Injectable()
export class MtnService {
  private readonly config: MtnConfig;

  constructor() {
    const {
      MTN_MOMO_BASE_URL,
      MTN_MOMO_SUBSCRIPTION_KEY,
      MTN_MOMO_API_USER,
      MTN_MOMO_API_KEY,
      MTN_MOMO_TOKEN_PATH,
      MTN_MOMO_REQUEST_TO_PAY_PATH,
      MTN_MOMO_REQUEST_TO_PAY_STATUS_PATH,
      MTN_MOMO_CURRENCY,
      MTN_MOMO_TARGET_ENVIRONMENT,
      MTN_MOMO_CALLBACK_BASE_URL,
      MTN_MOMO_DISBURSEMENT_TOKEN_PATH,
      MTN_MOMO_TRANSFER_PATH,
      MTN_MOMO_TRANSFER_STATUS_PATH,
    } = process.env;

    const targetEnvironment = MTN_MOMO_TARGET_ENVIRONMENT ?? 'sandbox';

    this.config = {
      baseUrl: MTN_MOMO_BASE_URL ?? 'https://sandbox.momodeveloper.mtn.com',
      subscriptionKey: MTN_MOMO_SUBSCRIPTION_KEY ?? '',
      apiUser: MTN_MOMO_API_USER ?? '',
      apiKey: MTN_MOMO_API_KEY ?? '',
      tokenPath: MTN_MOMO_TOKEN_PATH ?? '/collection/token/',
      requestToPayPath:
        MTN_MOMO_REQUEST_TO_PAY_PATH ?? '/collection/v1_0/requesttopay',
      requestToPayStatusPath:
        MTN_MOMO_REQUEST_TO_PAY_STATUS_PATH ??
        '/collection/v1_0/requesttopay/{referenceId}',
      callbackBaseUrl: MTN_MOMO_CALLBACK_BASE_URL?.replace(/\/$/, ''),
      currency:
        MTN_MOMO_CURRENCY ??
        (targetEnvironment.trim().toLowerCase() === 'sandbox' ? 'EUR' : 'XAF'),
      targetEnvironment,
      disbursementTokenPath:
        MTN_MOMO_DISBURSEMENT_TOKEN_PATH ?? '/disbursement/token/',
      transferPath: MTN_MOMO_TRANSFER_PATH ?? '/disbursement/v1_0/transfer',
      transferStatusPath:
        MTN_MOMO_TRANSFER_STATUS_PATH ??
        '/disbursement/v1_0/transfer/{referenceId}',
    };
  }

  private assertConfig() {
    const missing: string[] = [];
    if (!this.config.subscriptionKey) missing.push('MTN_MOMO_SUBSCRIPTION_KEY');
    if (!this.config.apiUser) missing.push('MTN_MOMO_API_USER');
    if (!this.config.apiKey) missing.push('MTN_MOMO_API_KEY');
    if (!this.config.targetEnvironment) missing.push('MTN_MOMO_TARGET_ENVIRONMENT');
    if (missing.length) {
      throw new InternalServerErrorException(
        `MTN MoMo configuration missing: ${missing.join(', ')}`,
      );
    }
  }

  private async getAccessToken(tokenPath: string): Promise<string> {
    this.assertConfig();

    const url = `${this.config.baseUrl}${tokenPath}`;
    const auth = Buffer.from(
      `${this.config.apiUser}:${this.config.apiKey}`,
    ).toString('base64');

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Basic ${auth}`,
        'Ocp-Apim-Subscription-Key': this.config.subscriptionKey,
      },
    });

    if (!res.ok) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `MTN getAccessToken failed: ${res.status} ${text}`,
      );
    }

    const data = (await res.json()) as { access_token: string };
    if (!data.access_token) {
      throw new InternalServerErrorException(
        'MTN getAccessToken: missing access_token in response',
      );
    }
    return data.access_token;
  }

  /**
   * Collections: RequestToPay (cash-in).
   * Important: MTN est async. On récupère le statut via callback (si configuré) et/ou polling.
   */
  async initiateDebit(
    input: InitiateMomoDebitInput,
  ): Promise<{ status: 'PENDING'; referenceId: string }> {
    const { phoneNumber, amountFcfa } = input;
    const accessToken = await this.getAccessToken(this.config.tokenPath);

    const referenceId = randomUUID();
    const url = `${this.config.baseUrl}${this.config.requestToPayPath}`;

    const body = {
      amount: amountFcfa.toString(),
      currency: this.config.currency,
      externalId: referenceId,
      payer: {
        partyIdType: 'MSISDN',
        partyId: phoneNumber,
      },
      payerMessage: 'AfriWallet wallet top-up',
      payeeNote: 'AfriWallet wallet top-up',
    };

    const callbackUrl =
      this.config.callbackBaseUrl
        ? `${this.config.callbackBaseUrl}/webhooks/mtn/requesttopay/${referenceId}`
        : undefined;

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-Reference-Id': referenceId,
        'X-Target-Environment': this.config.targetEnvironment,
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': this.config.subscriptionKey,
        ...(callbackUrl ? { 'X-Callback-Url': callbackUrl } : {}),
      },
      body: JSON.stringify(body),
    });

    if (!res.ok && res.status !== 202) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `MTN initiateDebit failed: ${res.status} ${text}`,
      );
    }

    return { status: 'PENDING', referenceId };
  }

  /**
   * Collections: get RequestToPay status (polling fallback).
   */
  async getRequestToPayStatus(referenceId: string): Promise<unknown> {
    this.assertConfig();
    const id = referenceId.trim();
    if (!id) {
      throw new InternalServerErrorException('MTN getRequestToPayStatus: referenceId is required');
    }

    const accessToken = await this.getAccessToken(this.config.tokenPath);
    const path = this.config.requestToPayStatusPath.replace('{referenceId}', encodeURIComponent(id));
    const url = `${this.config.baseUrl}${path}`;

    const res = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-Target-Environment': this.config.targetEnvironment,
        'Ocp-Apim-Subscription-Key': this.config.subscriptionKey,
      },
    });

    const text = await res.text();
    if (!res.ok) {
      throw new InternalServerErrorException(
        `MTN getRequestToPayStatus failed: ${res.status} ${text}`,
      );
    }
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  /**
   * Disbursements: transfer (cash-out).
   */
  async initiateTransfer(
    input: InitiateMomoTransferInput,
  ): Promise<{ status: 'PENDING'; referenceId: string }> {
    const { phoneNumber, amountFcfa } = input;
    const accessToken = await this.getAccessToken(this.config.disbursementTokenPath);

    const referenceId = randomUUID();
    const url = `${this.config.baseUrl}${this.config.transferPath}`;

    const body = {
      amount: amountFcfa.toString(),
      currency: this.config.currency,
      externalId: referenceId,
      payee: {
        partyIdType: 'MSISDN',
        partyId: phoneNumber,
      },
      payerMessage: 'AfriWallet wallet cash-out',
      payeeNote: 'AfriWallet wallet cash-out',
    };

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-Reference-Id': referenceId,
        'X-Target-Environment': this.config.targetEnvironment,
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': this.config.subscriptionKey,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok && res.status !== 202) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `MTN initiateTransfer failed: ${res.status} ${text}`,
      );
    }

    return { status: 'PENDING', referenceId };
  }

  async getTransferStatus(referenceId: string): Promise<unknown> {
    this.assertConfig();
    const id = referenceId.trim();
    if (!id) {
      throw new InternalServerErrorException('MTN getTransferStatus: referenceId is required');
    }

    const accessToken = await this.getAccessToken(this.config.disbursementTokenPath);
    const path = this.config.transferStatusPath.replace('{referenceId}', encodeURIComponent(id));
    const url = `${this.config.baseUrl}${path}`;

    const res = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-Target-Environment': this.config.targetEnvironment,
        'Ocp-Apim-Subscription-Key': this.config.subscriptionKey,
      },
    });

    const text = await res.text();
    if (!res.ok) {
      throw new InternalServerErrorException(
        `MTN getTransferStatus failed: ${res.status} ${text}`,
      );
    }
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }
}

