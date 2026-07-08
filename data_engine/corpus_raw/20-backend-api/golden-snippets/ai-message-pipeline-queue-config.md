# Golden Snippet — `src/config/queue.js`

> **Couche:** `20-backend-api` · **Source:** `ai_message_codebase/src/config/queue.js`

File BullMQ whatsapp-queue, retries exponentiels, connexion Redis.

```javascript
const { Queue } = require('bullmq');

// Configuration de la connexion Redis commune
const redisConnection = {
    host: process.env.REDIS_HOST || '127.0.0.1',
    port: parseInt(process.env.REDIS_PORT || '6379', 10),
};

/**
 * Initialisation de la file d'attente pour les messages WhatsApp
 */
const whatsappQueue = new Queue('whatsapp-queue', {
    connection: redisConnection,
    defaultJobOptions: {
        attempts: 3, // En cas d'échec (ex: timeout de l'IA), on réessaye 3 fois
        backoff: {
            type: 'exponential',
            delay: 2000, // Attendre 2s avant le premier retry, puis 4s, etc.
        },
        removeOnComplete: true, // Nettoie Redis quand le job est fini avec succès
        removeOnFail: false,    // Garde l'historique dans Redis si ça plante (pratique pour débugger)
    }
});

console.log(' File d\'attente BullMQ [whatsapp-queue] initialisée.');

module.exports = {
    whatsappQueue,
    redisConnection // On l'exporte car notre futur Worker en aura besoin
};
```
