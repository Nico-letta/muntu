# Golden Snippet — `src/webhooks/webhooks.controller.ts`

> **Couche:** `20-backend-api` · **Source:** `afriwallet_codebase/src/webhooks/webhooks.controller.ts`

Surface HTTP webhooks, signatures, throttling.

```typescript
import { Body, Controller, ForbiddenException, Headers, Param, Post, Put, Req } from '@nestjs/common';
import { Throttle } from '@nestjs/throttler';
import { WebhooksService } from './webhooks.service';
import { SmileIdService } from '../providers/smile-id.service';
import { OnafriqWebhookService } from '../providers/onafriq-webhook.service';
import { BridgePaymentsWebhookService } from '../providers/bridge-payments-webhook.service';
import type { Request } from 'express';

interface SmileWebhookBody {
  signature?: string;
  timestamp?: string;
  job_success?: boolean;
  result?: {
    PartnerParams?: {
      user_id?: string;
      job_id?: string;
    };
  };
}

@Controller('webhooks')
export class WebhooksController {
  constructor(
    private readonly webhooksService: WebhooksService,
    private readonly smileIdService: SmileIdService,
    private readonly onafriqWebhookService: OnafriqWebhookService,
    private readonly bridgePaymentsWebhookService: BridgePaymentsWebhookService,
  ) {}

  /**
   * Webhook MTN MoMo (Collections requesttopay callback).
   * On configure le callback URL sous la forme:
   *   {MTN_MOMO_CALLBACK_BASE_URL}/webhooks/mtn/requesttopay/{referenceId}
   * afin de pouvoir corréler de façon fiable au X-Reference-Id.
   *
   * MTN peut appeler en POST ou PUT selon l'implémentation / produit.
   */
  @Post('mtn/requesttopay/:referenceId')
  @Throttle({ default: { ttl: 60_000, limit: 300 } })
  async mtnRequestToPayCallbackPost(
    @Param('referenceId') referenceId: string,
    @Body() body: unknown,
    @Headers('x-reference-id') xReferenceId: string | undefined,
    @Req() req: Request,
  ) {
    // Durcissement optionnel: allowlist IP si configurée.
    // Le contrôle fin (proxy trust, ranges, etc.) dépendra du déploiement.
    const ip = this.getRequestIp(req);
    return this.webhooksService.handleMtnRequestToPayCallback({
      referenceId: xReferenceId ?? referenceId,
      payload: body,
      requestIp: ip,
    });
  }

  @Put('mtn/requesttopay/:referenceId')
  @Throttle({ default: { ttl: 60_000, limit: 300 } })
  async mtnRequestToPayCallbackPut(
    @Param('referenceId') referenceId: string,
    @Body() body: unknown,
    @Headers('x-reference-id') xReferenceId: string | undefined,
    @Req() req: Request,
  ) {
    const ip = this.getRequestIp(req);
    return this.webhooksService.handleMtnRequestToPayCallback({
      referenceId: xReferenceId ?? referenceId,
      payload: body,
      requestIp: ip,
    });
  }

  // Callback Smile ID -> ton backend (validation KYC).
  @Post('smile-id')
  async smileIdCallback(@Body() body: SmileWebhookBody) {
    const { signature, timestamp } = body;
    if (!signature || !timestamp) {
      throw new ForbiddenException('Missing Smile ID signature or timestamp');
    }

    // Anti-replay: on refuse les signatures trop anciennes (± 5 minutes).
    const now = Date.now();
    const ts = new Date(timestamp).getTime();
    if (!Number.isFinite(ts)) {
      throw new ForbiddenException('Invalid timestamp');
    }
    if (Math.abs(now - ts) > 5 * 60 * 1000) {
      throw new ForbiddenException('Expired signature');
    }

    const valid = this.smileIdService.verifyCallbackSignature(
      signature,
      timestamp,
    );
    if (!valid) {
      throw new ForbiddenException('Invalid Smile ID signature');
    }

    // Le service gère idempotence + audit + transitions KYC.
    return this.webhooksService.handleSmileIdWebhook(body);
  }

  // Webhook Onafriq Cards -> ton backend (événements cartes).
  @Throttle({ default: { ttl: 60_000, limit: 120 } })
  @Post('onafriq/cards')
  async onafriqCardsCallback(
    @Headers('x-webhook-signature') signature: string | undefined,
    @Body() body: unknown,
  ) {
    if (!signature) {
      throw new ForbiddenException('Missing Onafriq webhook signature');
    }

    const valid = this.onafriqWebhookService.verifySignature(signature);
    if (!valid) {
      throw new ForbiddenException('Invalid Onafriq webhook signature');
    }

    await this.webhooksService.handleOnafriqWebhook(body);
    return { received: true };
  }

  @Throttle({ default: { ttl: 60_000, limit: 180 } })
  @Post('bridge/payments')
  async bridgePaymentsCallback(
    @Headers('bridgeapi-signature') signature: string | undefined,
    @Body() body: unknown,
    @Req() req: Request & { rawBody?: Buffer },
  ) {
    const raw = req.rawBody;
    const valid = this.bridgePaymentsWebhookService.verifySignature(signature, raw);
    if (!valid) {
      throw new ForbiddenException('Invalid Bridge payments webhook signature');
    }
    return this.webhooksService.handleBridgePaymentsWebhook(body);
  }

  private getRequestIp(req: Request): string | null {
    const xff = req.headers['x-forwarded-for'];
    const firstForwarded =
      typeof xff === 'string' ? xff.split(',')[0]?.trim() : Array.isArray(xff) ? xff[0] : null;
    return firstForwarded || req.ip || (req.socket && req.socket.remoteAddress) || null;
  }
}


```
