import os
import csv
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# Directory paths
data_dir = "CustomData"
embeddings_dir = "Embeddings"
mapping_filename = "mapping.csv"

# Create embeddings directory if it doesn't exist
if not os.path.exists(embeddings_dir):
    os.makedirs(embeddings_dir)

# Function to split text into chunks
def split_text(text, chunk_size=5000, overlap=500):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)
    return chunks

# Function to generate embeddings for text using OpenAI's API
def generate_embeddings(text):
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text,
        encoding_format="float"
    )
    # Directly access the embedding from the response object
    embeddings = response.data[0].embedding
    return np.array(embeddings)


# Initialize the mapping list
mappings = []

# Process each text file in the data directory
for filename in os.listdir(data_dir):
    if filename.endswith(".txt"):
        file_path = os.path.join(data_dir, filename)
        
        # Read and split text from the file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            text_splits = split_text(text)

            # Generate embeddings for each text split and save them
            for index, text_split in enumerate(text_splits):
                embeddings = generate_embeddings(text_split)
                embeddings_file_name = f"{filename}_split_{index}.npy"
                np.save(os.path.join(embeddings_dir, embeddings_file_name), embeddings)

                # Update the mapping with the text split and its corresponding embeddings file name
                mappings.append({'text splits': text_split, 'embeddings file': embeddings_file_name})

                # Add a console log for progress
                print(f"Processed: {filename}, Text Split: {text_split[:50]}...")

# Save the mappings to a CSV file
with open(os.path.join(embeddings_dir, mapping_filename), 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['text splits', 'embeddings file']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for mapping in mappings:
        writer.writerow(mapping)

print("Embeddings saved to '.npy' files and mappings saved to 'mapping.csv' in 'Embeddings' directory.")
