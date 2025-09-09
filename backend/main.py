from typing import Union, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from dotenv import load_dotenv
import os
import asyncio
from fastapi.middleware.cors import CORSMiddleware

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

# --- Data Models ---
class Request(BaseModel):
    query: str

class Response(BaseModel):
    answer: str
    source_text: str

# --- Document Loading & Processing Logic ---
async def load_documents_from_urls():
    """
    Loads all specified documents from their respective URLs.
    """
    document_urls = {
        "epf_act": "https://www.epfindia.gov.in/site_docs/PDFs/Downloads_PDFs/EPFAct1952.pdf",
        "companies_act": "https://faolex.fao.org/docs/pdf/IND214525.pdf", # A PDF version of the Companies Act, 2013
        "tds_page": "https://incometaxindia.gov.in/Pages/Deposit_TDS_TCS.aspx"
    }
    
    all_docs = []

    # Load PDF documents
    pdf_loader_epf = PyPDFLoader(document_urls["epf_act"])
    pdf_loader_companies = PyPDFLoader(document_urls["companies_act"])
    
    all_docs.extend(pdf_loader_epf.load())
    all_docs.extend(pdf_loader_companies.load())

    # Load web page document
    web_loader = WebBaseLoader(web_paths=[document_urls["tds_page"]])
    all_docs.extend(web_loader.load())
    
    print("All documents loaded successfully.")
    return all_docs

def create_vector_store(documents: List):
    """
    Splits documents into chunks and creates a FAISS vector store.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    print("FAISS vector store created.")
    return vector_store

@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs on application startup to load data.
    """
    global vector_store
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY environment variable not set. Please set it to proceed.")
        return
    
    try:
        documents = await load_documents_from_urls()
        vector_store = create_vector_store(documents)
        print("Application startup complete. Vector store is ready to be queried.")
    except Exception as e:
        print(f"Failed to load documents at startup: {e}")

# --- API Endpoints ---
def query_helper_function(query:str, vector_store: FAISS):
    """
    Helper function to perform a similarity search and get an answer from the LLM.
    """
    relevant_chunks = vector_store.similarity_search(query, k=3)
    
    prompt_template = """
    You are a helpful civil engineer assistant. Use the following pieces of context to answer the question at the end. Your answer must be based only on the provided text. If the answer is not in the context, say that you don't know.\n\n
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
