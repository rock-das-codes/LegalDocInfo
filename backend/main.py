from typing import Union

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import faiss
import os
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain


if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")
app = FastAPI()
document_store = {}
class Request(BaseModel):
    document_id:str
    query:str

class Response(BaseModel):
    answer:str
    source_text:str
class UploadResponse(BaseModel
):
    document_id:str
    
def document_config(file_path:str):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    reader = PyPDFLoader(file_path)
    docs  = reader.load()
    chunks=text_splitter.split_documents(docs)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store


@app.post("/upload",response_model = UploadResponse)
async def uploadfile(file:UploadFile = File(...)):
    document_id = str(uuid.uuid4())
    file_path = f"temp_{document_id}.pdf"
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        print(f"Document {document_id} uploaded and saved to {file_path}")
        vector_store =document_config(file_path)
        document_store[document_id] = vector_store
        return {"document_id": document_id}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            
    
def query_helper_function(query:str,vector_store):
    relevant_chunks = vector_store.similarity_search(query,k=3)
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
    Accepts a document_id and a question, returns an answer.
    """
    # TODO: Add the query logic from Phase 1 here.
    vector_store = document_store.get(request.document_id)
    if not vector_store:
        raise HTTPException(status_code=404, detail="Document not found.")    
    

    result =query_helper_function(request.query,vector_store)

    return result
@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}