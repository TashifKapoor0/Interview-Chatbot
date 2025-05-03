# 🤖 AI Q&A Chatbot (Azure-Powered)

This is a secure, dataset-driven chatbot built with **Streamlit**, **Azure OpenAI**, **Azure AI Search**, and **Cosmos DB**. It answers user questions strictly based on pre-indexed content — no hallucinations, no paraphrasing.

## 🚀 Features

- Uses **vector search** via Azure AI Search
- Embeds queries with **Azure OpenAI Embeddings**
- Retrieves matching content only
- Generates responses using **Azure OpenAI Chat**
- Stores all chat history in **Cosmos DB**
- Session-based memory
- Web UI built with **Streamlit**
- `.env` file support (via `python-dotenv`)

## 💻 Local Setup

1. Clone the repo:
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    cd YOUR_REPO_NAME
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file and add your Azure configuration:
    ```dotenv
    AZURE_OPENAI_ENDPOINT=...
    AZURE_OPENAI_KEY=...
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=...
    AZURE_OPENAI_CHAT_DEPLOYMENT=...

    AZURE_SEARCH_ENDPOINT=...
    AZURE_SEARCH_KEY=...
    AZURE_SEARCH_INDEX=...
    AZURE_SEARCH_VECTOR_FIELD=...
    AZURE_SEARCH_CONTENT_FIELD=...

    COSMOS_ENDPOINT=...
    COSMOS_KEY=...
    COSMOS_DB_NAME=...
    COSMOS_CONTAINER_NAME=...
    COSMOS_PARTITION_KEY=/session_id
    ```

5. Run the chatbot:
    ```bash
    streamlit run app.py
    ```
