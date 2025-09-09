# LegalDocInfo Backend

This is the backend for LegalDocInfo, built with FastAPI, LangChain, Google Generative AI, and FAISS for document processing and Q&A over PDF documents.

## Features

- Upload PDF documents and process them into vector stores for semantic search.
- Query uploaded documents using natural language.
- Powered by Google Generative AI (Gemini) models.
- API endpoints for upload, query, health check, etc.

## Prerequisites

- Python 3.10 or newer (recommended)
- [pip](https://pip.pypa.io/en/stable/installation/)
- Google Generative AI API key

## Installation

1. **Clone the repository**

    ```sh
    git clone https://github.com/rock-das-codes/LegalDocInfo.git
    cd LegalDocInfo/backend
    ```

2. **Create a virtual environment (recommended)**

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies**

    ```sh
    pip install -r requirements.txt
    ```

4. **Environment Variables**

    - Create a `.env` file in the `backend` folder (or set environment variables directly).
    - Add your Google API key:

      ```
      GOOGLE_API_KEY=your_google_api_key_here
      ```

    - You can obtain a key from [Google Generative AI](https://makersuite.google.com/) or your Google developer console.

## Running the Server

Start the FastAPI server using Uvicorn:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## API Usage

### 1. Health Check

- **Endpoint:** `GET /health`
- **Description:** Check if the API is running.

### 2. Upload a PDF Document

- **Endpoint:** `POST /upload`
- **Description:** Upload a PDF file to be processed.
- **Request:** `multipart/form-data` with a `file` field.
- **Response:** `{ "document_id": "<uuid>" }`

### 3. Query a Document

- **Endpoint:** `POST /api/query`
- **Description:** Query a previously uploaded document.
- **Request Body:** JSON
    ```json
    {
      "document_id": "<uuid>",
      "query": "your question here"
    }
    ```
- **Response:**
    ```json
    {
      "answer": "...",
      "source_text": "..."
    }
    ```

## Development Notes

- The backend currently stores vector stores in-memory (`document_store` dict). For production, consider persisting vector stores.
- CORS is enabled for all origins; restrict this in production for security.
- Only PDF files are supported for upload.

## Troubleshooting

- **Error: `GOOGLE_API_KEY environment variable not set or empty.`**
  - Ensure your `.env` file exists and is correctly formatted.
  - Restart the server after adding your API key.

- **Missing dependencies:**  
  - Run `pip install -r requirements.txt` in your virtual environment.
