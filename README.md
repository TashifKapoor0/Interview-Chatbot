# 💬 Smart Interview Q&A Bot (Azure-Powered)

Dive into a focused question-and-answer experience with this intelligent chatbot! Built with a sleek, WhatsApp-style interface, it leverages the power of **FastAPI**, **Azure OpenAI**, **Azure AI Search**, and **Cosmos DB** to provide precise answers based strictly on the knowledge it's been trained on. Say goodbye to irrelevant responses and hello to targeted information!

## ✨ Key Features

* **WhatsApp-Style UI:** Enjoy a familiar and intuitive chat interface with user messages on the right and bot responses on the left.
* **Powered by Azure AI:** Utilizes **Azure OpenAI Embeddings** for understanding user queries and **Azure OpenAI Chat** for generating accurate responses.
* **Intelligent Retrieval:** Employs **vector search** through Azure AI Search to find the most relevant information in its dataset.
* **Strict Q&A:** Designed to provide answers directly from the indexed content, ensuring no fabricated or paraphrased responses.
* **Conversation History:** Maintains session-based memory of your interactions.
* **Optional Data Persistence:** Chat history can be saved to **Azure Cosmos DB** for future reference.
* **Easy Configuration:** Uses `.env` files (via `python-dotenv`) for managing your Azure credentials.
* **Responsive Design:** The frontend is designed to work well on various screen sizes.

## 🛠️ Local Setup

1.  **Get the Code:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
    cd YOUR_REPO_NAME
    ```
    *(Replace `YOUR_USERNAME/YOUR_REPO_NAME.git` with your actual repository URL)*

2.  **Set Up Your Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate   # macOS/Linux
    venv\Scripts\activate.bat  # Windows
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Azure Credentials:**
    Create a `.env` file in your project's root and fill in your Azure service details:
    ```dotenv
    AZURE_OPENAI_ENDPOINT=YOUR_AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_KEY=YOUR_AZURE_OPENAI_KEY
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=YOUR_EMBEDDING_DEPLOYMENT_NAME
    AZURE_OPENAI_CHAT_DEPLOYMENT=YOUR_CHAT_DEPLOYMENT_NAME

    AZURE_SEARCH_ENDPOINT=YOUR_AZURE_SEARCH_ENDPOINT
    AZURE_SEARCH_KEY=YOUR_AZURE_SEARCH_KEY
    AZURE_SEARCH_INDEX=YOUR_AZURE_SEARCH_INDEX_NAME
    AZURE_SEARCH_VECTOR_FIELD=YOUR_VECTOR_FIELD_NAME
    AZURE_SEARCH_CONTENT_FIELD=YOUR_CONTENT_FIELD_NAME

    COSMOS_ENDPOINT=YOUR_COSMOS_ENDPOINT
    COSMOS_KEY=YOUR_COSMOS_KEY
    COSMOS_DB_NAME=YOUR_COSMOS_DATABASE_NAME
    COSMOS_CONTAINER_NAME=YOUR_COSMOS_CONTAINER_NAME
    COSMOS_PARTITION_KEY=/session_id
    ```
    *(Remember to add `.env` to your `.gitignore` for security!)*

## 🚀 Running the Chatbot

1.  **Navigate to the project directory in your terminal.**
2.  **Activate your virtual environment.**
3.  **Start the FastAPI backend:**
    ```bash
    uvicorn main:app --reload
    ```
    This will typically run your backend on `http://127.0.0.1:8000`.

4.  **Open the Frontend:**
    Open your web browser and go to `http://127.0.0.1:8000`. You should now see the interactive chat interface.

## 🤖 Interacting with the Bot

* Type your questions in the input field.
* Hit 'Send' to get a response based on the indexed knowledge.
* Enjoy the clean, WhatsApp-like flow of your conversation!
* To end the session and save the chat history (if configured), type `end`, `exit`, or `bye`.

## 📂 Project Structure
