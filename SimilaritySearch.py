import os
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# Directory where your embeddings are stored
embeddings_dir = "Embeddings"
mapping_csv_path = os.path.join(embeddings_dir, 'mapping.csv')

# Load the mapping from CSV into a dictionary for quick lookup
def load_text_to_embedding_mapping(csv_file_path):
    mapping_df = pd.read_csv(csv_file_path)
    mapping_dict = pd.Series(mapping_df['text splits'].values, index=mapping_df['embeddings file']).to_dict()
    return mapping_dict

text_to_embedding_mapping = load_text_to_embedding_mapping(mapping_csv_path)

# Function to generate embeddings using OpenAI
def generate_embeddings(text):
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text,
        encoding_format="float"
    )
    return np.array(response.data[0].embedding)

# Function to create and load a FAISS index with embeddings
def create_faiss_index(embeddings_dir):
    embedding_files = [f for f in os.listdir(embeddings_dir) if f.endswith('.npy')]
    d = np.load(os.path.join(embeddings_dir, embedding_files[0])).shape[0]
    index = faiss.IndexFlatL2(d)
    for file in embedding_files:
        embedding = np.load(os.path.join(embeddings_dir, file))
        index.add(embedding.reshape(1, -1))
    return index, embedding_files

index, embedding_files = create_faiss_index(embeddings_dir)

# New function to get chat response
def get_chat_response(user_query, message_history):
    
    # Generate embedding for user's query and find the closest match
    query_embedding = generate_embeddings(user_query)
    D, I = index.search(query_embedding.reshape(1, -1), 1)
    best_match_file = embedding_files[I[0][0]]
    context_text = text_to_embedding_mapping.get(best_match_file, "Relevant information not found.")
    
    # Base system message defined outside the loop
    system_message_base = """You are a helpful assistant focused on credit card questions. 
    Use the relevenat information included to answer the user question but keep your response under 120 words and use emojis to make responses more relatable.
    Use bullet and numbering to make the response more readable.
    Remember your job is to be as helpful as possible so tap into your knowledge if necessary to provide answers but prioritize searching relevant context first."""

    # Prepare the dynamic system message with the current context
    user_query = f"Provide an answer to the question: {user_query}. We have extracted some knowledge for you to base your answer on. Here's the relevant information: {context_text}"

    # Append system and user messages to the history, ensuring the history does not exceed 10 messages
    #message_history = message_history[-9:]  # Keep only the last 9 interactions to make room for the new one
    message_history.append({"role": "system", "content": system_message_base})
    message_history.append({"role": "user", "content": user_query})

    #print(message_history)

    # Call OpenAI's chat completion API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=message_history
    )
    
    # Return assistant's response
    assistant_response_content = response.choices[0].message.content

    # Update message history with assistant's response
    message_history.append({"role": "assistant", "content": assistant_response_content})

    #print(message_history)

    return assistant_response_content, message_history