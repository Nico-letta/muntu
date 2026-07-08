# Golden Snippet — `src/middlewares/auth.middleware.js`

> **Couche:** `20-backend-api` · **Source:** `ai_message_codebase/src/middlewares/auth.middleware.js`

Validation WHATSAPP_WEBHOOK_SECRET sur requetes entrantes.

```javascript
/**
 * Middleware de sécurité pour valider les requêtes entrantes
 */

/**
 * Vérifie que la requête possède le token secret de Notify
 */
const validateWebhookSecret = (req, res, next) => {
    try {
        // Récupération du token envoyé par Notify dans les en-têtes HTTP
        // Note : En général, les plateformes envoient cela dans 'x-webhook-secret' ou l'en-tête standard 'authorization'
        const incomingSecret = req.headers['x-webhook-secret'] || req.headers['authorization'];

        const systemSecret = process.env.WHATSAPP_WEBHOOK_SECRET;

        // Si le secret n'est pas configuré sur notre serveur, sécurité maximale : on bloque
        if (!systemSecret) {
            console.error(' Erreur de configuration : WHATSAPP_WEBHOOK_SECRET n’est pas défini dans le fichier .env');
            return res.status(500).json({ error: 'Erreur interne de configuration du serveur' });
        }

        // Vérification de la correspondance
        if (!incomingSecret || incomingSecret !== systemSecret) {
            console.warn(` Tentative d'accès non autorisée bloquée ! Origin: ${req.ip}`);
            return res.status(401).json({ 
                error: 'Non autorisé', 
                message: 'Le jeton de validation du webhook est absent ou invalide.' 
            });
        }

        // Si tout est valide, on passe au middleware suivant (ou au contrôleur) 
        next();

    } catch (error) {
        console.error(' Erreur dans le middleware de sécurité :', error);
        return res.status(500).json({ error: 'Erreur interne du serveur' });
    }
};

module.exports = {
    validateWebhookSecret
};
```
