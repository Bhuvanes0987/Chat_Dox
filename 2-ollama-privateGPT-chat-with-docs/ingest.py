import os
import logging
import random
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from langchain.document_loaders import (
    CSVLoader,
    PyMuPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

# FastAPI Setup
app = FastAPI()

# Setup Static files directory for serving CSS, JS, etc.
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Logger Setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Load environment variables (set them directly or use environment variables)
persist_directory = os.environ.get('PERSIST_DIRECTORY', 'db')
source_directory = os.environ.get('SOURCE_DIRECTORY', 'source_documents')
embeddings_model_name = os.environ.get('EMBEDDINGS_MODEL_NAME', 'all-MiniLM-L6-v2')

# Define the log file path
response_log_file = 'query_response_log.txt'

# Pydantic model to validate incoming queries
class QueryModel(BaseModel):
    query: str

# FastAPI route to serve the home page (GET)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading template: {e}")
        return {"error": "Template load failed"}

# Function to load vector store (Chroma) with HuggingFace embeddings
def load_vectorstore():
    try:
        embedding_model = HuggingFaceEmbeddings(model_name=embeddings_model_name)
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)
        return vectorstore
    except Exception as e:
        logger.error(f"Error loading vector store: {e}")
        raise HTTPException(status_code=500, detail="Error loading vector store")

# Function to query the vector store and find the most relevant document
def query_documents_with_vectorstore(query: str):
    try:
        vectorstore = load_vectorstore()
        results = vectorstore.similarity_search(query, k=1)  # k=1 will return the most relevant document

        if results:
            content = results[0].page_content  # Get the full content
            return content
        else:
            logger.warning(f"No relevant documents found for query: {query}")
            return "No relevant documents found."
    except Exception as e:
        logger.error(f"Error querying vector store: {e}")
        raise HTTPException(status_code=500, detail="Error querying vector store")

# Function to clean up the response (remove unwanted line breaks or bullet points)
def clean_up_response(response: str) -> str:
    try:
        clean_response = response.replace('•', '').replace('\n', ' ').strip()
        clean_response = ' '.join(clean_response.split())  # Remove multiple spaces
        return clean_response
    except Exception as e:
        logger.error(f"Error cleaning up response: {e}")
        return response

# Function to log query and response to a file
def log_query_response(query: str, response: str):
    try:
        with open(response_log_file, 'a') as file:
            file.write(f"Query: {query}\n")
            file.write(f"Response: {response}\n")
            file.write("-" * 70 + "\n")  # Separator for clarity
    except Exception as e:
        logger.error(f"Error logging query and response: {e}")

# Function to randomly select a greeting response
def get_random_greeting():
    greetings = [
        "Hi, how are you?",
        "Hello! How's it going?",
        "Hey there! What's up?",
        "Greetings! How can I help you today?",
        "Hola! How's your day going?",
        "Howdy! What's on your mind?",
        "Good morning! Happy to see you"
    ]
    return random.choice(greetings)

# FastAPI route to handle user queries (POST)
@app.post("/query")
async def query_documents(query: QueryModel):
    try:
        logger.info(f"Received query: {query.query}")
        
        # Check if the query contains a greeting like "hi" or "hello"
        greeting_keywords = ['hi', 'hello', 'hey', 'greetings', 'hola', 'howdy', 'good morning', 'morning']
        if any(greeting in query.query.lower() for greeting in greeting_keywords):
            # Return a random greeting response
            response_content = get_random_greeting()
        else:
            # Query the vector store with the user's query if it's not a greeting
            response_content = query_documents_with_vectorstore(query.query)
        
        # Clean up the response text
        cleaned_response = clean_up_response(response_content)
        
        # Log the query and cleaned response to the file
        log_query_response(query.query, cleaned_response)
        
        # Log the result and send the response back
        logger.info(f"Returning response: {cleaned_response}")
        return {"response": cleaned_response}

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Run FastAPI app with Uvicorn (for local testing)
if __name__ == "__main__":
    import uvicorn
    # For development, use `reload=True`. For production, set `reload=False`.
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)  # change reload=False for production
