from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv
from markdown2 import markdown
from bs4 import BeautifulSoup

# Import the get_chat_response function from SimilaritySearch.py
from SimilaritySearch import get_chat_response

load_dotenv()

app = Flask(__name__)

MY_INSTAGRAM_ACCOUNT_ID = os.getenv('INSTAGRAM_ACCOUNT_ID')
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

# Dictionary to store conversation history for each user
user_conversation_histories = {}

def markdown_to_plain_text(markdown_text):
    # Convert Markdown to HTML
    html_text = markdown(markdown_text)
    # Use BeautifulSoup to remove HTML tags, leaving plain text
    plain_text = ''.join(BeautifulSoup(html_text, "html.parser").findAll(text=True))
    return plain_text

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print('WEBHOOK_VERIFIED')
            return challenge, 200
        else:
            return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def handle_messages():
    data = request.json
    if data and 'entry' in data:
        for entry in data['entry']:
            for event in entry.get('messaging', []):
                if event.get('message') and event['sender']['id'] != MY_INSTAGRAM_ACCOUNT_ID:
                    sender_id = event['sender']['id']
                    user_message = event['message'].get('text', '')
                    # Retrieve the user's conversation history
                    conversation_history = user_conversation_histories.get(sender_id, [])
                    # Get the chat response along with the updated conversation history
                    chat_response, updated_history = get_chat_response(user_message, conversation_history)
                    # Update the conversation history for the user
                    user_conversation_histories[sender_id] = updated_history
                    # Send the response back to the user
                    respond_to_message(sender_id, chat_response)
                    #print(user_conversation_histories)
    return 'EVENT_RECEIVED', 200


def respond_to_message(recipient_id, message_text):
    # Convert the Markdown formatted response to plain text
    plain_message = markdown_to_plain_text(message_text)

    url = f'https://graph.facebook.com/v19.0/me/messages'
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': plain_message},
        'access_token': PAGE_ACCESS_TOKEN
    }
    try:
        response = requests.post(url, json=payload)
        print(f'Message sent to {recipient_id}: {message_text}')
        print(f'Response Status: {response.status_code}, Body: {response.text}')  # Log API response
    except Exception as error:
        print(f'Error sending message: {error}')


if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT', 3000)), debug=True)
