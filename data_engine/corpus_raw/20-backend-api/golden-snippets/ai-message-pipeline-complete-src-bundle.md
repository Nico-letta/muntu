# IA message pipeline — Source JavaScript Complete Bundle

> Fichiers sous `ai_message_codebase/src/` pour entrainement MoE MUNTU.

## `src/app.js`

```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
require('dotenv').config();

const app = express();

// ==========================================
// MIDDLEWARES GLOBAUX DE SÉCURITÉ & PARSING
// ==========================================

// Configuration de Helmet pour sécuriser les en-têtes HTTP de l'admin web
app.use(helmet({
    contentSecurityPolicy: false, // À ajuster plus tard si des scripts externes bloquent sur l'UI admin
}));

// Activation du CORS (Utile si ton panel admin communique avec une autre origine)
app.use(cors());

// Intercepteurs de requêtes (Crucial pour capter les webhooks JSON de Notify)
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ==========================================
// CONFIGURATION DU MOTEUR DE RENDU (Pôle Média)
// ==========================================
app.set('view engine', 'ejs');
app.set('views', './src/views');
app.use(express.static('./src/public'));

// ==========================================
// ROUTE DE VÉRIFICATION OPÉRATIONNELLE (Healthcheck)
// ==========================================
app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'UP',
        timestamp: new Date(),
        env: process.env.NODE_ENV
    });
});

// ==========================================
// ZONES D'INJECTION DES ACCÈS FUTURS
// ==========================================
// app.use('/webhook', whatsappRouter);
// app.use('/admin', adminRouter);
const whatsappRouter = require('./controllers/whatsapp/whatsapp.routes');
app.use('/api/v1/webhook/whatsapp', whatsappRouter);

// Gestion globale des erreurs 404 (Route non trouvée)
app.use((req, res, next) => {
    res.status(404).json({ error: 'Ressource introuvable sur le serveur IA message pipeline' });
});

module.exports = app;
```

## `src/config/db.js`

```javascript
const { PrismaMariaDb } = require('@prisma/adapter-mariadb');
const { PrismaClient } = require('@prisma/client');

// On utilise l'URL native de JavaScript pour découper la chaîne unique DATABASE_URL
const dbUrl = new URL(process.env.DATABASE_URL);

const adapter = new PrismaMariaDb({
  host: dbUrl.hostname,
  port: parseInt(dbUrl.port || '3306', 10),
  user: dbUrl.username,
  password: decodeURIComponent(dbUrl.password),
  database: dbUrl.pathname.replace('/', ''), // Retire le slash initial pour avoir le nom de la BDD
  connectionLimit: 5,
});

const prisma = new PrismaClient({ adapter });

console.log('  Prisma Client connecté (Source unique : DATABASE_URL).');

module.exports = prisma;
```

## `src/config/queue.js`

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

## `src/controllers/whatsapp/whatsapp.controller.js`

```javascript
// src/controllers/whatsapp/whatsapp.controller.js
require('dotenv').config();
const { whatsappQueue } = require('../../config/queue');
/**
 * Validation du Webhook par Meta (Requête GET)
 */
const verifyWebhook = (req, res) => {
    const VERIFY_TOKEN = process.env.WHATSAPP_VERIFY_TOKEN || process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN;

    const mode = req.query['hub.mode'];
    const token = req.query['hub.verify_token'];
    const challenge = req.query['hub.challenge'];

    if (!VERIFY_TOKEN) {
        console.error(' [Meta Webhook] Token de vérification introuvable dans les variables d\'environnement.');
        return res.sendStatus(500);
    }

    if (mode && token) {
        if (mode === 'subscribe' && token === VERIFY_TOKEN) {
            console.log(' [Meta Webhook] Validation réussie !');
            return res.status(200).send(challenge);
        } else {
            console.log(' [Meta Webhook] Échec de validation (Tokens non correspondants)');
            return res.sendStatus(403);
        }
    }
    return res.sendStatus(400);
};

/**
 * Réception des messages WhatsApp (Requête POST)
 */
const receiveMessage = async (req, res) => {
    const body = req.body;

    if (body.object === 'whatsapp_business_account') {
        try {
            if (body.entry && body.entry[0].changes && body.entry[0].changes[0].value.messages) {
                const messageData = body.entry[0].changes[0].value.messages[0];

                const from = messageData.from;
                const messageType = messageData.type;

                if (messageType === 'text') {
                    const text = messageData.text.body;

                    console.log(` [Webhook] Nouveau message texte de ${from} : "${text}"`);

                    // Injection du job dans la file d'attente Redis
                    await whatsappQueue.add('whatsapp-job', { 
                        from, 
                        text,
                        name: body.entry[0].changes[0].value.contacts?.[0]?.profile?.name || 'Utilisateur'
                    });
                    
                    console.log(` [BullMQ] Job 'whatsapp-job' ajouté avec succès pour ${from}`);
                }
            }
            
            return res.status(200).send('EVENT_RECEIVED');
        } catch (error) {
            console.error(' [Webhook] Erreur lors du traitement du payload :', error);
            return res.status(200).send('EVENT_RECEIVED');
        }
    } else {
        return res.sendStatus(404);
    }
};

module.exports = {
    verifyWebhook,
    receiveMessage
};
```

## `src/controllers/whatsapp/whatsapp.routes.js`

```javascript
// src/controllers/whatsapp/whatsapp.routes.js
const express = require('express');
const router = express.Router();
const whatsappController = require('./whatsapp.controller');

// Route GET pour la vérification de Meta
router.get('/', whatsappController.verifyWebhook);

// Route POST pour la réception des messages
router.post('/', whatsappController.receiveMessage);

module.exports = router;
```

## `src/middlewares/auth.middleware.js`

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

## `src/server.js`

```javascript
require('dotenv').config();
const app = require('./app');

require('./workers/whatsapp.worker');

const PORT = process.env.PORT || 3000;

/**
 * Initialisation et démarrage du serveur de l'église I.C.C
 */
async function startServer() {
    try {
        // C'est ici que nous intégrerons l'initialisation des pools d'infrastructures :
        // await db.connect();      -> Connexion pool MySQL
        // await redis.connect();   -> Connexion Redis pour BullMQ
        const currentEnv = process.env.NODE_ENV || 'development';
        
        app.listen(PORT, () => {
            console.log(`=======================================================`);
            console.log(` SERVEUR IA message pipeline DEMARRÉ EN MODE [${currentEnv.toUpperCase()}]`);
            console.log(` Port d'écoute : ${PORT}`);
            console.log(` Vérification d'état : http://localhost:${PORT}/health`);
            console.log(`=======================================================`);
        });
    } catch (error) {
        console.error(' Échec critique lors du bootstrapping du serveur :', error);
        process.exit(1); // Arrêt immédiat du processus en cas de panne d'infrastructure
    }
}

startServer();
```

## `src/services/notify.service.js`

```javascript
/**
 * Service de communication officiel avec l'API Notify.cg
 */
async function sendWhatsAppMessage(lid, text, name = 'Fidèle') {
    //  Récupération de l'URL depuis le .env avec un fallback propre
    const url = process.env.NOTIFY_API_URL || 'https://app.notify.cg/api/external/send';
    
    //  Récupération du Token (Strictement requis !)
    const token = process.env.NOTIFY_API_TOKEN;

    if (!token) {
        throw new Error(" [Notify Service] Sécurité : Le token NOTIFY_API_TOKEN est introuvable dans le fichier .env");
    }

    console.log(` [Notify Service] Expédition de la réponse via l'API externe vers le LID: ${lid}...`);

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                canal: 'whatsapp',
                message: text,
                phoneNumber: lid,
                name: name
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Erreur API Notify (${response.status}) : ${errorText}`);
        }

        const contentType = response.headers.get("content-type");
        const result = contentType && contentType.includes("application/json") 
            ? await response.json() 
            : await response.text();

        console.log(` [Notify Service] Message transmis avec succès à la passerelle Notify !`);
        return result;

    } catch (error) {
        console.error(` [Notify Service] Échec de l'envoi HTTP :`, error.message);
        throw error;
    }
}

module.exports = {
    sendWhatsAppMessage
};
```

## `src/services/ollama.service.js`

```javascript
const axios = require('axios');

// Extraction des configurations depuis le .env avec des valeurs de secours (fallbacks)
const OLLAMA_URL = process.env.OLLAMA_URL || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'qwen2.5:latest';

/**
 * Génère une réponse de l'IA en lui passant l'historique de la conversation et son prompt système
 * @param {Array} conversationHistory - Le tableau des derniers messages [{role, content}]
 * @param {string} systemPrompt - Les instructions de comportement basées sur le statut du fidèle
 * @returns {Promise<string>} - Le message texte généré par Qwen
 */
async function generateResponse(conversationHistory, systemPrompt) {
    try {
        // Construction du payload complet pour le modèle de chat d'Ollama
        const messages = [
            { role: 'system', content: systemPrompt },
            ...conversationHistory
        ];

        console.log(` [Ollama Service] Envoi de la demande à ${OLLAMA_MODEL}...`);

        const response = await axios.post(`${OLLAMA_URL}/api/chat`, {
            model: OLLAMA_MODEL,
            messages: messages,
            stream: false // On désactive le streaming pour récupérer la réponse d'un bloc dans le Worker
        });

        // Extraction propre du texte de la réponse d'Ollama
        if (response.data && response.data.message) {
            return response.data.message.content.trim();
        }

        throw new Error("Structure de réponse Ollama invalide");

    } catch (error) {
        console.error(" [Ollama Service] Erreur lors de la génération de la réponse :", error.message);
        throw error;
    }
}

module.exports = {
    generateResponse
};
```

## `src/services/whatsapp.service.js`

```javascript
const axios = require('axios');

/**
 * Envoie un message texte simple à un utilisateur via l'API Cloud de WhatsApp
 * @param {string} to - Le numéro de téléphone du destinataire (format international sans +, ex: 24206xxxx)
 * @param {string} text - Le contenu du message à envoyer
 */
async function sendWhatsAppMessage(to, text) {
    const url = `https://graph.facebook.com/v20.0/${process.env.WHATSAPP_PHONE_NUMBER_ID}/messages`;
    
    const data = {
        messaging_product: "whatsapp",
        recipient_type: "individual",
        to: to,
        type: "text",
        text: {
            preview_url: true, // Permet d'afficher l'aperçu du lien web de ta future Webview !
            body: text
        }
    };

    try {
        const response = await axios.post(url, data, {
            headers: {
                'Authorization': `Bearer ${process.env.WHATSAPP_TOKEN}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log(` [Meta API] Message envoyé avec succès à ${to}. MessageID: ${response.data.messages[0].id}`);
        return response.data;
    } catch (error) {
        console.error(` [Meta API] Erreur lors de l'envoi du message à ${to} :`);
        if (error.response) {
            console.error(JSON.stringify(error.response.data, null, 2));
        } else {
            console.error(error.message);
        }
        throw error;
    }
}

module.exports = {
    sendWhatsAppMessage
};
```

## `src/workers/whatsapp.worker.js`

```javascript
const { Worker } = require('bullmq');
const { redisConnection } = require('../config/queue');
const prisma = require('../config/db');
const { generateResponse } = require('../services/ollama.service');
const { sendWhatsAppMessage } = require('../services/whatsapp.service');

console.log(' Le Worker WhatsApp IA message pipeline a été réveillé et guette la file...');

const whatsappWorker = new Worker('whatsapp-queue', async (job) => {
    const { from, text } = job.data;

    console.log(`\n [Worker] Traitement du job #${job.id} en cours...`);
    console.log(` Expéditeur (whatsappId) : ${from}`);
    console.log(` Contenu : "${text}"`);

    try {
        // 1. Récupérer ou créer l'utilisateur dans la table 'users' avec son niveau d'accès (tier)
        let user = await prisma.user.upsert({
            where: { whatsappId: from },
            update: {},
            create: {
                whatsappId: from,
                tier: 'PROSPECT' // Par défaut, un nouvel utilisateur est un PROSPECT (en attente de KYC)
            }
        });

        // Extraction du tier (gère l'adaptation si le champ s'appelle tier ou s'il y a une transition)
        const currentTier = user.tier || 'PROSPECT';
        console.log(` Utilisateur identifié : ID ${user.id} | Tier : ${currentTier}`);

        // 2. Enregistrer le message reçu dans la table 'message_logs'
        const savedMessage = await prisma.messageLog.create({
            data: {
                userId: user.id,
                role: 'user',
                content: text
            }
        });

        console.log(` Message enregistré en BDD avec l'ID : ${savedMessage.id}`);

        // 3. Récupérer l'historique récent pour donner de la mémoire à l'IA (Qwen2.5)
        const rawHistory = await prisma.messageLog.findMany({
            where: { userId: user.id },
            orderBy: { createdAt: 'desc' },
            take: 10
        });

        const conversationHistory = rawHistory.reverse().map(log => ({
            role: log.role,
            content: log.content
        }));

        console.log(` Mémoire chargée : ${conversationHistory.length} messages récupérés pour le contexte.`);

        // 4. Récupération dynamique du prompt système en BDD selon le TIER (PROSPECT, VERIFIED, PREMIUM)
        console.log(` [Worker] Recherche du prompt système pour le tier : ${currentTier}...`);
        
        const systemPromptRecord = await prisma.systemPrompt.findUnique({
            where: { tier: currentTier }
        });

        // Sécurité : Si aucun prompt n'est configuré en BDD, on utilise un prompt IA message pipeline de secours
        const currentPrompt = systemPromptRecord 
            ? systemPromptRecord.content 
            : `Tu es l'assistant officiel de IA message pipeline au Congo-Brazzaville. Sois professionnel et guide l'utilisateur vers la validation de son identité.`;
        
        // On lance l'inférence locale (Ollama / Qwen2.5) avec le prompt extrait de la BDD
        const aiResponse = await generateResponse(conversationHistory, currentPrompt);
        
        console.log(`\n [Qwen2.5] Réponse générée depuis le prompt BDD (${currentTier}) :`);
        console.log(` "${aiResponse}"\n`);

        // 5. Enregistrer la réponse de l'IA dans la table 'message_logs'
        const savedAssistantMessage = await prisma.messageLog.create({
            data: {
                userId: user.id,
                role: 'assistant',
                content: aiResponse
            }
        });

        console.log(` Réponse de l'IA enregistrée en BDD avec l'ID : ${savedAssistantMessage.id}`);

        // 6. Envoi du message final à l'utilisateur sur WhatsApp
        await sendWhatsAppMessage(from, aiResponse);

        console.log(` [Worker] Job #${job.id} traité avec succès !`);

    } catch (error) {
        console.error(` [Worker] Échec de traitement pour le job #${job.id} :`, error);
        throw error;
    }
}, {
    connection: redisConnection,
    concurrency: 1
});

module.exports = whatsappWorker;
```

