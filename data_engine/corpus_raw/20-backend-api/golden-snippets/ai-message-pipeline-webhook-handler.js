/**
 * Golden Snippet — Webhook Meta verify + receive (IA message pipeline)
 * Source: ai_message_codebase/src/controllers/whatsapp/whatsapp.controller.js
 */

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
