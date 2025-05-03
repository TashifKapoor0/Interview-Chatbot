import uuid
import json
import streamlit as st
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient, PartitionKey
import os
from dotenv import load_dotenv

# -------------------- LOAD ENV --------------------
load_dotenv()

# -------------------- ENV CONFIGURATION --------------------
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
AZURE_SEARCH_VECTOR_FIELD = os.getenv("AZURE_SEARCH_VECTOR_FIELD")
AZURE_SEARCH_CONTENT_FIELD = os.getenv("AZURE_SEARCH_CONTENT_FIELD")

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB_NAME = os.getenv("COSMOS_DB_NAME")
COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME")
COSMOS_PARTITION_KEY = os.getenv("COSMOS_PARTITION_KEY")

# -------------------- CLIENT INITIALIZATION --------------------
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

# -------------------- SYSTEM RULES --------------------
SYSTEM_PROMPT = (
    "You are a strict Q&A bot. You must only respond with answers that are exactly as stored "
    "in the dataset. Do not paraphrase, summarize, or generate new content. If no matching answer "
    "is found, say 'No matching answer found in the dataset.'"
)

# -------------------- FUNCTIONS --------------------
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

    full_context = "\n\n".join(passages)
    response = openai_client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\n\nRelevant Data:\n{full_context}"}
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

# -------------------- STREAMLIT CHATBOT --------------------
def chatbot_ui():
    st.set_page_config(page_title="AI Q&A Chatbot", layout="centered")
    st.title("🤖 AI Q&A Chatbot")
    st.markdown("Ask any question. The chatbot will only respond with answers from the dataset.")

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.ended = False

    for entry in st.session_state.chat_history:
        st.markdown(f"**You:** {entry['user']}")
        st.markdown(f"**Bot:** {entry['bot']}")

    if not st.session_state.ended:
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("Type your question:", "")
            submit_button = st.form_submit_button("Send")

        if submit_button and user_input.strip():
            if user_input.lower().strip() in ["exit", "quit", "end"]:
                st.session_state.ended = True
                save_to_cosmos(st.session_state.session_id, st.session_state.chat_history)
                st.success("✅ Thank you for using the chatbot. Session ended.")
            else:
                results = search_azure_index(user_input)
                bot_response = ask_chatbot(user_input, results)
                st.session_state.chat_history.append({"user": user_input, "bot": bot_response})
                st.rerun()

# -------------------- CLI MODE --------------------
def chatbot_cli():
    session_id = str(uuid.uuid4())
    history = []
    print("AI Q&A Chatbot (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit", "end"]:
            print("Session ended. Saving chat...")
            save_to_cosmos(session_id, history)
            break
        results = search_azure_index(user_input)
        bot_response = ask_chatbot(user_input, results)
        history.append({"user": user_input, "bot": bot_response})
        print(f"Bot: {bot_response}\n")

# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        chatbot_cli()
    else:
        chatbot_ui()
