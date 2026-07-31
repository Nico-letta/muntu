# Golden Snippet — `src/providers/onafriq-webhook.service.ts`

> **Couche:** `30-system-integrations` · **Source:** `afriwallet_codebase/src/providers/onafriq-webhook.service.ts`

Verification signature webhook Onafriq AES256.

```typescript
import { Injectable, InternalServerErrorException } from '@nestjs/common';

// Librairie AES256 utilisée pour valider la signature.
// eslint-disable-next-line @typescript-eslint/no-var-requires
const AES256 = require('aes-everywhere') as {
  decrypt(cipherText: string, secret: string): string;
};

@Injectable()
export class OnafriqWebhookService {
  private readonly secretKey: string;
  private readonly webhookSecret: string;

  constructor() {
    this.secretKey = process.env.ONAFRIQ_SECRET_KEY ?? '';
    this.webhookSecret = process.env.ONAFRIQ_WEBHOOK_SECRET ?? '';
  }

  private assertConfig() {
    const missing: string[] = [];
    if (!this.secretKey) missing.push('ONAFRIQ_SECRET_KEY');
    if (!this.webhookSecret) missing.push('ONAFRIQ_WEBHOOK_SECRET');
    if (missing.length) {
      throw new InternalServerErrorException(
        `Onafriq webhook configuration missing: ${missing.join(', ')}`,
      );
    }
  }

  verifySignature(xWebhookSignature: string): boolean {
    this.assertConfig();

    try {
      const decrypted = AES256.decrypt(xWebhookSignature, this.secretKey);
      return decrypted === this.webhookSecret;
    } catch {
      return false;
    }
  }
}

```
