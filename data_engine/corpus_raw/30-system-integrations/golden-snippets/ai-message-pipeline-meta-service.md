# Golden Snippet — `src/services/whatsapp.service.js`

> **Couche:** `30-system-integrations` · **Source:** `ai_message_codebase/src/services/whatsapp.service.js`

Envoi message texte via Graph API v20.0 Meta WhatsApp Cloud.

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
