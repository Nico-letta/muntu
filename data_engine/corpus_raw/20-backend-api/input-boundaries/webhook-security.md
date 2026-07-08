# Frontières d'entrée — Sécurité Webhooks

> **Couche** : `20-backend-api/input-boundaries` · **Axe** : Entrée non typée → verrous  
> **Source** : `src/webhooks/webhooks.service.ts`, `src/webhooks/webhooks.controller.ts`

## Contexte

Les webhooks sont le point d'entrée le plus sensible : payloads tiers, replays, doublons. AfriWallet applique **signature + idempotence** avant mutation du wallet.

## Contrat — Idempotence (eventKey)

```json
{
  "MTN_MOMO": "mtn:r2p:{referenceId}",
  "SMILE_ID": "{job_id}",
  "ONAFRIQ": "onafriq:{notificationType}:{requestId}:{transactionId|customerId}",
  "BRIDGE": "bridge:payments:{type}:{paymentRequestId}:{status}",
  "duplicate_behavior": "Prisma P2002 → return 200 silently, no double credit"
}
```

## Contrat — Signatures par provider

```json
{
  "SMILE_ID": {
    "method": "HMAC",
    "anti_replay_window": "±5 minutes on timestamp"
  },
  "ONAFRIQ": {
    "header": "x-webhook-signature",
    "method": "AES256",
    "secrets": ["ONAFRIQ_SECRET_KEY", "ONAFRIQ_WEBHOOK_SECRET"]
  },
  "BRIDGE": {
    "header": "bridgeapi-signature",
    "method": "HMAC-SHA256"
  },
  "MTN_MOMO": {
    "optional": "IP allowlist MTN_MOMO_WEBHOOK_IP_ALLOWLIST"
  }
}
```

## Contrat — Endpoints webhook (surface publique)

```json
{
  "MTN": "POST|PUT /webhooks/mtn/requesttopay/:referenceId",
  "SMILE_ID": "POST /webhooks/smile-id",
  "ONAFRIQ": "POST /webhooks/onafriq/cards",
  "BRIDGE": "POST /webhooks/bridge/payments"
}
```

## Règles de traitement

1. Transaction déjà `SUCCESS` ou `FAILED` → ignore (idempotent).
2. Cash-out MoMo `FAILED` → **compensation** recrédit wallet.
3. Smile webhook sans `user_id` → audit `WebhookEvent` only, pas de mutation User.
4. KYC déjà `VERIFIED`/`REJECTED` → ignore webhook Smile (idempotent).

---

## Golden Snippets — validation signatures (AfriWallet)

Extraits de référence depuis `src/webhooks/` et `src/providers/`. **Ne pas copier `src/` en entier** — seules les frontières à haute valeur métier sont documentées ici.

### Smile ID — anti-replay ±5 min + HMAC

Le controller rejette tout webhook sans signature/timestamp, puis délègue la vérification HMAC au SDK Smile Identity **avant** toute mutation `kycStatus`.

```typescript
// src/webhooks/webhooks.controller.ts — smileIdCallback()
@Post('smile-id')
async smileIdCallback(@Body() body: SmileWebhookBody) {
  const { signature, timestamp } = body;
  if (!signature || !timestamp) {
    throw new ForbiddenException('Missing Smile ID signature or timestamp');
  }

  // Anti-replay: fenêtre ± 5 minutes
  const now = Date.now();
  const ts = new Date(timestamp).getTime();
  if (!Number.isFinite(ts)) throw new ForbiddenException('Invalid timestamp');
  if (Math.abs(now - ts) > 5 * 60 * 1000) {
    throw new ForbiddenException('Expired signature');
  }

  const valid = this.smileIdService.verifyCallbackSignature(signature, timestamp);
  if (!valid) throw new ForbiddenException('Invalid Smile ID signature');

  return this.webhooksService.handleSmileIdWebhook(body);
}

// src/providers/smile-id.service.ts
verifyCallbackSignature(receivedSignature: string, receivedTimestamp: string): boolean {
  const connection = new Signature(this.config.partnerId, this.config.signatureApiKey);
  return connection.confirm_signature(receivedTimestamp, receivedSignature);
}
```

### Onafriq — signature AES256 (`x-webhook-signature`)

Le header est chiffré AES256 avec `ONAFRIQ_SECRET_KEY` ; le plaintext doit égaler `ONAFRIQ_WEBHOOK_SECRET`.

```typescript
// src/providers/onafriq-webhook.service.ts
verifySignature(xWebhookSignature: string): boolean {
  this.assertConfig();
  try {
    const decrypted = AES256.decrypt(xWebhookSignature, this.secretKey);
    return decrypted === this.webhookSecret;
  } catch {
    return false;
  }
}
```

### Bridge — HMAC-SHA256 timing-safe sur raw body

NestJS doit exposer `req.rawBody` (middleware) — la signature porte sur le payload brut, pas le JSON re-sérialisé.

```typescript
// src/providers/bridge-payments-webhook.service.ts
verifySignature(signatureHeader: string | undefined, rawBody: Buffer | string | undefined): boolean {
  const payload = Buffer.isBuffer(rawBody) ? rawBody.toString('utf8') : rawBody;
  const expected = createHmac('sha256', this.secret).update(payload).digest('hex').toUpperCase();

  const candidates = signatureHeader
    .split(',')
    .map((entry) => entry.trim())
    .filter((entry) => entry.toLowerCase().startsWith('v1='))
    .map((entry) => entry.slice(3).trim().toUpperCase());

  return candidates.some((candidate) => {
    const a = Buffer.from(candidate, 'utf8');
    const b = Buffer.from(expected, 'utf8');
    return a.length === b.length && timingSafeEqual(a, b);
  });
}
```

### Idempotence — `WebhookEvent.create` + catch P2002

Pattern canonique MTN MoMo : persister `eventKey` **avant** mutation wallet ; doublon = 200 silencieux.

```typescript
// src/webhooks/webhooks.service.ts — handleMtnRequestToPayCallback()
const eventKey = `mtn:r2p:${referenceId}`;
try {
  await this.prisma.webhookEvent.create({
    data: {
      provider: PaymentProvider.MTN_MOMO,
      eventKey,
      userId: tx.wallet.userId,
      payload: payload as Prisma.InputJsonValue,
    },
  });
} catch (err) {
  if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2002') {
    this.logger.warn(`Duplicate MTN webhook ignored for eventKey=${eventKey}`);
    return { received: true };
  }
  throw err;
}

// Transaction déjà finalisée → idempotent, pas de double crédit
if (tx.status === TransactionStatus.SUCCESS || tx.status === TransactionStatus.FAILED) {
  await this.prisma.webhookEvent.update({
    where: { eventKey },
    data: { processedAt: new Date() },
  });
  return { received: true };
}
```

## Voir aussi

- `20-backend-api/execution-lifecycle/async-pipeline-jobs.md`
- `30-system-integrations/provider-specs.md`
