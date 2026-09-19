import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


load_dotenv()

DATA_PATH = "data/"
PDF_FILENAME = "llama2.pdf"

def load_documents():
    """Loads documents from the specified data path."""
    pdf_path = os.path.join(DATA_PATH, PDF_FILENAME)
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"Loaded {len(documents)} page(s) from {pdf_path}.")
    return documents

# documents = load_documents() 

def split_documents(documents):
    """Splits the loaded documents into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex = False,
    )
    all_splits = text_splitter.split_documents(documents)
    print(f"Split into {len(all_splits)} chunks.")
    return all_splits

# load_docs = load_documents()
# chunks = split_documents(load_docs)


def get_embedding_function(model_name="nomic-embed-text"):
    """Initializes the Ollama embedding function."""
    # Ensure Ollama server is running (ollama serve)
    embeddings = OllamaEmbeddings(model=model_name)
    print(f"Initialized Ollama embeddings with model: {model_name}")
    return embeddings


CHROMA_PATH = "chroma_db"

def get_vector_store(embedding_function, persist_directory=CHROMA_PATH):
    """Initializes the Chroma vector store."""
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_function
    )
    print(f"Initialized Chroma vector store at: {persist_directory}")
    return vectorstore

# embedding_function = get_embedding_function()
# vector_store = get_vector_store(embedding_function)

def index_documents(chunks, embedding_function, persist_directory=CHROMA_PATH):
    """Indexes the document chunks into the Chroma vector store."""
    print(f"Indexing {len(chunks)} chunks into Chroma vector store...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=persist_directory
    )

    vectorstore.persist()   # ensure data is saved
    print(f"Indexing complete. Data saved to: {persist_directory}")
    return vectorstore

# vector_store = index_documents(chunks, embedding_function)

def create_rag_chain(vector_store, llm_model_name="qwen3:8b", context_window=8192):
    """Creates the RAG chain"""
    # initialize the LLM
    llm = ChatOllama(
        model=llm_model_name,
        temperature=0,
        num_ctx=context_window
    )

    print(f"Initialized ChatOllama with model: {llm_model_name}, context window: {context_window}")

    # create the retriever from the vector store
    retriever = vector_store.as_retriever(
        search_type= "similarity",
        search_kwargs={"k": 3} # retrieve top 3 relevant chunks
    )
    print("Retriever created.")

    # Define the prompt template for the RAG chain
    template = """Answer the question based ONLY on the following context:
    {context}
    
    Question: {question}"""
    prompt = ChatPromptTemplate.from_template(template)
    print("Prompt template created.")

    # Define the RAG chain
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough() }
        | prompt
        | llm
        | StrOutputParser()
        )
    print("RAG chain created.")
    return rag_chain

# vector_store = get_vector_store(embedding_function) # Assuming DB is already indexed
# rag_chain = create_rag_chain(vector_store)


def query_rag(chain, question):
    """Queries the RAG chain and prints the response."""
    print("\nQuerying RAG chain...")
    print(f"Question: {question}")
    response = chain.invoke(question)
    print("\nResponse:")
    print(response)


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
    rag_chain = create_rag_chain(vector_store, llm_model_name="qwen3:8b" )

    # 6. Query RAG chain
    sample_question = "What is the main topic of the document?"
    query_rag(rag_chain, sample_question)

    query_question2 = "Summarize the introduction section."
    query_rag(rag_chain, query_question2)