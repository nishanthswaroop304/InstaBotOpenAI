require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');

const app = express();
app.use(bodyParser.json());
const conversationHistories = {}; // Stores conversation history for each sender


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
                        const receivedMessage = event.message.text; // Extracting the text from the message
                        // Respond to the message with the extracted text
                        respondToMessage(event.sender.id, receivedMessage);
                    }
                }
            });
        });
    }
    res.status(200).send('EVENT_RECEIVED');
});

// Function to send a message via the Instagram API
const respondToMessage = async (recipientId, receivedMessage) => {
    const openaiApiKey = process.env.OPENAI_API_KEY;
    const currentTime = new Date().getTime();

    // Check and clear the conversation if more than 1 minute has passed since the last activity
    if (conversationHistories[recipientId] && currentTime - conversationHistories[recipientId].lastActivityTime > 600000) {
        delete conversationHistories[recipientId]; // Clear the conversation history after 1 minute of inactivity
    }

    // Initialize or update conversation history for the sender
    if (!conversationHistories[recipientId]) {
        conversationHistories[recipientId] = {
            messages: [{
                role: "system",
                content: "You are a helpful credit card picker assistant. Always respond politely and helpfully with emojis. Keep your responses under 50 words. Clarify in the beginning that you can help with any credit card questions. If anyone asks non-credit card questions, politely decline and suggest they ask a credit card question."
            }],
            lastActivityTime: currentTime // Set the initial last activity time
        };
    } else {
        // Update the last activity time for ongoing conversations
        conversationHistories[recipientId].lastActivityTime = currentTime;
    }

    // Add the received message to the sender's conversation history
    conversationHistories[recipientId].messages.push({
        role: "user",
        content: receivedMessage // This should be the actual latest message from the user
    });

    try {
        // Prepare the request payload including the conversation history
        const requestBody = {
            model: "gpt-3.5-turbo",
            messages: conversationHistories[recipientId].messages,
        };

        // Debugging: Log the requestBody to verify the conversation history structure
        console.log(JSON.stringify(requestBody, null, 2)); // This line is for debugging purposes

        // Send the conversation history to OpenAI's API
        const openaiResponse = await axios.post(
            'https://api.openai.com/v1/chat/completions',
            requestBody,
            {
                headers: {
                    'Authorization': `Bearer ${openaiApiKey}`,
                    'Content-Type': 'application/json'
                }
            }
        );

        // Extract the text response from OpenAI
        const aiTextResponse = openaiResponse.data.choices[0].message.content;

        // Add the AI's response to the sender's conversation history
        conversationHistories[recipientId].messages.push({
            role: "assistant",
            content: aiTextResponse
        });

        // Update the last activity time after receiving the response from OpenAI
        conversationHistories[recipientId].lastActivityTime = new Date().getTime();

        // Send the AI response back to the user via the Instagram API
        const url = `https://graph.facebook.com/v19.0/me/messages`;
        const data = {
            recipient: { id: recipientId },
            message: { text: aiTextResponse },
            access_token: PAGE_ACCESS_TOKEN
        };

        await axios.post(url, data);
        console.log(`AI Message sent to ${recipientId}: ${aiTextResponse}`);
    } catch (error) {
        console.error('Error sending message:', error.response ? error.response.data : error);
    }
};

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server is running on port ${port}`));