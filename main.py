import uuid
import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse  # Import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient, PartitionKey

# Load environment
load_dotenv()

# Azure OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

# Azure Search
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
AZURE_SEARCH_VECTOR_FIELD = os.getenv("AZURE_SEARCH_VECTOR_FIELD")
AZURE_SEARCH_CONTENT_FIELD = os.getenv("AZURE_SEARCH_CONTENT_FIELD")

# Cosmos DB
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB_NAME = os.getenv("COSMOS_DB_NAME")
COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME")
COSMOS_PARTITION_KEY = os.getenv("COSMOS_PARTITION_KEY")

# Clients
openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version="2025-03-01-preview"
)
search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=AZURE_SEARCH_INDEX,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY)
)
cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
db = cosmos_client.create_database_if_not_exists(id=COSMOS_DB_NAME)
container = db.create_container_if_not_exists(
    id=COSMOS_CONTAINER_NAME,
    partition_key=PartitionKey(path=COSMOS_PARTITION_KEY)
)

# FastAPI setup
app = FastAPI()
templates = Jinja2Templates(directory=".")
session_memory = {}

SYSTEM_PROMPT = (
    "You are a strict Q&A bot. You must only respond with answers that are exactly as stored "
    "in the dataset. Do not paraphrase, summarize, or generate new content. If no matching answer "
    "is found, say 'No matching answer found in the dataset.'"
)

def get_embedding(text):
    response = openai_client.embeddings.create(
        input=[text],
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    )
    return response.data[0].embedding

def search_azure_index(query):
    embedding = get_embedding(query)
    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=10,
        fields=AZURE_SEARCH_VECTOR_FIELD
    )
    results = search_client.search(
        search_text="",
        vector_queries=[vector_query]
    )
    return [result[AZURE_SEARCH_CONTENT_FIELD] for result in results]

def ask_chatbot(query, passages):
    if not passages:
        return "No matching answer found in the dataset."
    context = "\n\n".join(passages)
    response = openai_client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\n\nRelevant Data:\n{context}"}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()

def save_to_cosmos(session_id, history):
    container.upsert_item({
        "id": session_id,
        "session_id": session_id,
        "conversation": history
    })

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "history": []})

@app.post("/chat")
async def chat(request: Request, user_input: str = Form(...)):
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    history = session_memory.get(session_id, [])

    user_message = {"user": user_input}
    history.append(user_message)

    if user_input.lower().strip() in ["exit", "end", "bye"]:
        save_to_cosmos(session_id, history)
        session_memory.pop(session_id, None)
        bot_reply = {"bot": "✅ Session ended and saved to Cosmos DB."}
        history.append(bot_reply)
        return JSONResponse({"history": history, "ended": True})  # Return JSON with ended flag

    passages = search_azure_index(user_input)
    bot_reply_text = ask_chatbot(user_input, passages)
    bot_reply = {"bot": bot_reply_text}
    history.append(bot_reply)
    session_memory[session_id] = history

    return JSONResponse({"history": history})  # Return JSON with updated history
