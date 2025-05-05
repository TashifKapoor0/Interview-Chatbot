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
AZURE_OPENAI_ENDPOINT="https://oai-ai-rd-sc-001.openai.azure.com/"
AZURE_OPENAI_KEY="9RYl5Z4DUIn7xarGTAhIWaG1K9gx8FN5GCK3NLKTo6bhfUyBlgUYJQQJ99BDACfhMk5XJ3w3AAABACOGfcbD"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4o"

AZURE_SEARCH_ENDPOINT="https://personalservices.search.windows.net"
AZURE_SEARCH_KEY="kPUhbbqDWgS0ZKLi9FOdncxdWr4hLECebotul2JpjQAzSeCc91gd"
AZURE_SEARCH_INDEX="vector-1746188137227"
AZURE_SEARCH_VECTOR_FIELD="text_vector"
AZURE_SEARCH_CONTENT_FIELD="chunk"  

COSMOS_ENDPOINT="https://cosno-ai-rd-sc-001.documents.azure.com:443/"
COSMOS_KEY="2YeNuohVTzPpkI9KX4Z6TCsEWWSgjVVpqE7ten8by02kV2hHUhQeI4VUiJAAW4TD83CcCh090Mg8ACDbDYZP8g=="
COSMOS_DB_NAME="Tashif-database"
COSMOS_CONTAINER_NAME="Conversations"
COSMOS_PARTITION_KEY="/session_id"


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

    # ------------------ SESSION STATE SETUP ------------------
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.ended = False

    # ------------------ CHAT DISPLAY ------------------
    for entry in st.session_state.chat_history:
        st.markdown(f"**You:** {entry['user']}")
        st.markdown(f"**Bot:** {entry['bot']}")

    # ------------------ CHAT INPUT ------------------
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

if __name__ == "__main__":
    chatbot_ui()
