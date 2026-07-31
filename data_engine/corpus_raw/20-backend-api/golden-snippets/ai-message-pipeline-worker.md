# Golden Snippet — `src/workers/whatsapp.worker.js`

> **Couche:** `20-backend-api` · **Source:** `ai_message_codebase/src/workers/whatsapp.worker.js`

Worker BullMQ : upsert user/tier, historique MessageLog, prompt SystemPrompt par tier, Ollama, envoi Meta.

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
