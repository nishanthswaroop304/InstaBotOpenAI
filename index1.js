require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');

const app = express();
app.use(bodyParser.json());

const MY_INSTAGRAM_ACCOUNT_ID = process.env.INSTAGRAM_ACCOUNT_ID;
const PAGE_ACCESS_TOKEN = process.env.PAGE_ACCESS_TOKEN;

app.get('/webhook', (req, res) => {
    const VERIFY_TOKEN = process.env.VERIFY_TOKEN;
    const mode = req.query['hub.mode'];
    const token = req.query['hub.verify_token'];
    const challenge = req.query['hub.challenge'];

    if (mode && token) {
        if (mode === 'subscribe' && token === VERIFY_TOKEN) {
            console.log('WEBHOOK_VERIFIED');
            res.status(200).send(challenge);
        } else {
            res.sendStatus(403);
        }
    }
});
app.post('/webhook', (req, res) => {
    if (req.body && req.body.entry) {
        req.body.entry.forEach(entry => {
            entry.messaging.forEach(event => {
                if (event.message && event.sender.id !== MY_INSTAGRAM_ACCOUNT_ID) {
                    if (!event.message.is_echo) {
                        // Respond to the message
                        respondToMessage(event.sender.id, 'Hello World');
                    }
                }
            });
        });
    }
    res.status(200).send('EVENT_RECEIVED');
});

const respondToMessage = async (recipientId, messageText) => {
    // Function to send a message via the Instagram API
    const url = `https://graph.facebook.com/v19.0/me/messages`;
    const data = {
        recipient: { id: recipientId },
        message: { text: messageText },
        access_token: PAGE_ACCESS_TOKEN
    };

    try {
        await axios.post(url, data);
        console.log(`Message sent to ${recipientId}: ${messageText}`);
    } catch (error) {
        console.error('Error sending message:', error);
    }
};

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server is running on port ${port}`));