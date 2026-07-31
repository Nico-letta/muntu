# Golden Snippet — `src/services/ollama.service.js`

> **Couche:** `30-system-integrations` · **Source:** `ai_message_codebase/src/services/ollama.service.js`

Client Ollama /api/chat avec system prompt + historique conversation.

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
