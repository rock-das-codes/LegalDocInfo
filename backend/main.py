from typing import Union, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from dotenv import load_dotenv
import os
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import traceback
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
import numpy as np

# Load environment variables
load_dotenv()

# --- FastAPI Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Variables ---
# This will hold our single, combined vector store
vector_store: Union[FAISS, None] = None

FAISS_INDEX_PATH = "/workspaces/LegalDocInfo/backend/faiss_index"

# --- Data Models ---
class Request(BaseModel):
    query: str

class Response(BaseModel):
    answer: str
    source_text: str

class GemmaEmbeddingWrapper:
    """
    Wrapper for SentenceTransformer to provide an embedding interface compatible with LangChain.
    """
    def __init__(self, model_name="google/embeddinggemma-300m"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        # Returns a list of numpy arrays
        return [np.array(self.model.encode_document([text])[0]) for text in texts]

    def embed_query(self, text):
        return np.array(self.model.encode_query(text))

    def __call__(self, text):
        # This makes the class compatible with LangChain's expectations
        return self.embed_query(text)

# --- Document Loading & Processing Logic ---
async def load_documents_from_urls():
    """
    Loads only the local EPF Act PDF from the data folder.
    """
    all_docs = []
    local_pdf_path = "/workspaces/LegalDocInfo/backend/data/EPFAct1952.pdf"
    try:
        print("Loading EPF Act PDF from local file...")
        pdf_loader_epf = PyPDFLoader(local_pdf_path)
        epf_docs = pdf_loader_epf.load()
        print(f"Loaded {len(epf_docs)} pages from EPF Act PDF.")
        all_docs.extend(epf_docs)
    except Exception as e:
        print(f"Error loading EPF Act PDF: {e}")
        traceback.print_exc()
    print(f"Total documents loaded: {len(all_docs)}")
    return all_docs

def create_vector_store(documents: List):
    """
    Splits documents into chunks and creates a FAISS vector store using Gemma embeddings.
    """
    try:
        print("Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        print(f"Total chunks created: {len(chunks)}")

        print("Creating Gemma embeddings...")
        embeddings = GemmaEmbeddingWrapper(model_name="google/embeddinggemma-300m")
        print("Creating FAISS vector store...")
        vector_store = FAISS.from_documents(chunks, embeddings)
        print("FAISS vector store created.")

        # Save the vector store to disk
        print(f"Saving FAISS index to {FAISS_INDEX_PATH} ...")
        vector_store.save_local(FAISS_INDEX_PATH)
        print("FAISS index saved.")
        return vector_store
    except Exception as e:
        print(f"Error creating vector store: {e}")
        traceback.print_exc()
        return None

def load_vector_store(embeddings):
    """
    Loads the FAISS vector store from disk if it exists.
    """
    if os.path.exists(FAISS_INDEX_PATH):
        try:
            print(f"Loading FAISS index from {FAISS_INDEX_PATH} ...")
            vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings)
            print("FAISS index loaded from disk.")
            return vector_store
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            traceback.print_exc()
    else:
        print("FAISS index not found on disk.")
    return None

@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs on application startup to load data.
    Loads vector store from disk if it exists, otherwise creates and saves it.
    """
    global vector_store

    print("Using Gemma embeddings (local, free).")
    embeddings = GemmaEmbeddingWrapper(model_name="google/embeddinggemma-300m")

    # Try to load vector store from disk first
    vector_store = load_vector_store(embeddings)
    if vector_store is not None:
        print("FAISS index found and loaded from disk. No need to create a new vector store.")
        print("Application startup complete. Vector store is ready to be queried.")
        return

    print("FAISS index not found. Creating a new vector store...")
    try:
        documents = await load_documents_from_urls()
        if not documents:
            print("No documents loaded. Vector store will not be created.")
            return
        vector_store = create_vector_store(documents)
        if vector_store is None:
            print("Vector store creation failed.")
        else:
            print("Application startup complete. Vector store is ready to be queried.")
    except Exception as e:
        print(f"Failed to load documents at startup: {e}")
        traceback.print_exc()

# --- API Endpoints ---
def query_helper_function(query:str, vector_store: FAISS):
    """
    Helper function to perform a similarity search and get an answer from the LLM.
    """
    relevant_chunks = vector_store.similarity_search(query, k=3)
    
    prompt_template = """
    You are a helpful legal assistant. Use the following pieces of context to answer the question at the end. Your answer must be based only on the provided text. If the answer is not in the context, say that you don't know.\n\n
    Context:\n {context}?\n
    Question:\n {question}\n

    Answer:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
    chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)
    response = chain({"input_documents": relevant_chunks, "question": query}, return_only_outputs=True)
    
    source_text = "\n---\n".join([chunk.page_content for chunk in relevant_chunks])
    
    return {"answer": response['output_text'], "source_text": source_text}


@app.post("/api/query", response_model=Response)
async def query_document(request: Request):
    """
    Accepts a query and returns an answer from the combined document store.
    """
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Document store not initialized. Please check application logs.")
        
    result = query_helper_function(request.query, vector_store)
    
    return result

@app.get("/")
def read_root():
    return {"message": "RAG solution for selection test is running. The document store is being initialized."}

@app.get("/health")
def health_check():
    return {"status": "ok", "vector_store_ready": vector_store is not None}
