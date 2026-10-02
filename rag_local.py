import os
import logging
from pathlib import Path

from app.config import settings
from app.ingestion.service import IngestionService
from app.logging_config import configure_logging
from app.models import QueryRequest
from app.services.query_service import QueryService
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

DATA_PATH = str(settings.data_path)
PDF_FILENAME = "llama2.pdf"

def load_documents():
    """Loads documents from the specified data path."""
    pdf_path = os.path.join(DATA_PATH, PDF_FILENAME)
    documents = IngestionService().load_documents(Path(pdf_path))
    logger.info("Loaded documents", extra={"count": len(documents), "source": pdf_path})
    return documents

# documents = load_documents() 

def split_documents(documents):
    """Splits the loaded documents into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        is_separator_regex = False,
    )
    all_splits = text_splitter.split_documents(documents)
    logger.info("Split documents", extra={"count": len(all_splits)})
    return all_splits

# load_docs = load_documents()
# chunks = split_documents(load_docs)


def get_embedding_function(model_name=None):
    """Initializes the Ollama embedding function."""
    # Ensure Ollama server is running (ollama serve)
    model_name = model_name or settings.embedding_model
    embeddings = OllamaEmbeddings(model=model_name, base_url=settings.ollama_base_url)
    logger.info("Initialized Ollama embeddings", extra={"model": model_name})
    return embeddings


CHROMA_PATH = str(settings.chroma_path)

def get_vector_store(embedding_function, persist_directory=CHROMA_PATH):
    """Initializes the Chroma vector store."""
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_function
    )
    logger.info("Initialized Chroma vector store", extra={"path": persist_directory})
    return vectorstore

# embedding_function = get_embedding_function()
# vector_store = get_vector_store(embedding_function)

def index_documents(chunks, embedding_function, persist_directory=CHROMA_PATH):
    """Indexes the document chunks into the Chroma vector store."""
    logger.info("Indexing chunks", extra={"count": len(chunks)})
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=persist_directory
    )

    vectorstore.persist()   # ensure data is saved
    logger.info("Indexing complete", extra={"path": persist_directory})
    return vectorstore

# vector_store = index_documents(chunks, embedding_function)

def create_rag_chain(vector_store, llm_model_name=None, context_window=None):
    """Creates the RAG chain"""
    # initialize the LLM
    llm_model_name = llm_model_name or settings.chat_model
    context_window = context_window or settings.context_window
    llm = ChatOllama(
        model=llm_model_name,
        base_url=settings.ollama_base_url,
        temperature=0,
        num_ctx=context_window
    )

    logger.info("Initialized ChatOllama", extra={"model": llm_model_name, "context_window": context_window})

    # create the retriever from the vector store
    retriever = vector_store.as_retriever(
        search_type= "similarity",
        search_kwargs={"k": settings.retrieval_k}
    )
    logger.info("Retriever created", extra={"k": settings.retrieval_k})

    # Define the prompt template for the RAG chain
    template = """Answer the question based ONLY on the following context:
    {context}
    
    Question: {question}"""
    prompt = ChatPromptTemplate.from_template(template)

    # Define the RAG chain
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough() }
        | prompt
        | llm
        | StrOutputParser()
        )
    logger.info("RAG chain created")
    return rag_chain

# vector_store = get_vector_store(embedding_function) # Assuming DB is already indexed
# rag_chain = create_rag_chain(vector_store)


def query_rag(chain, question):
    """Queries the RAG chain and prints the response."""
    logger.info("Querying RAG chain", extra={"question": question})
    response = QueryService(chain).answer(
        QueryRequest(question=question)
    )
    logger.info("RAG response generated")
    return response.answer


# ---- Main Execution ----
if __name__ == "__main__":
    # 1. Load Doc
    docs = load_documents()

    # 2. split doc
    chunks = split_documents(docs)

    # 3. Get embedding function
    embedding_function = get_embedding_function()

    # 4. Index Documents (Only needs to be done once per document set)
    # Check if DB exists, if not, index. For simplicity, we might re-index here.
    #TODO:
    # A more robust approach would check if indexing is needed.
    print("Attempting to index documents...")
    vector_store = index_documents(chunks, embedding_function)

    # to load existing DB
    vector_store = get_vector_store(embedding_function)

    # 5. Create RAG chain
    rag_chain = create_rag_chain(vector_store)

    # 6. Query RAG chain
    sample_question = "What is the main topic of the document?"
    query_rag(rag_chain, sample_question)

    query_question2 = "Summarize the introduction section."
    query_rag(rag_chain, query_question2)