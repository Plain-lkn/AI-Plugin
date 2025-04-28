import os
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

def get_vectorstore_path(user_id: str):
    return f"faiss/subject_{user_id}"

def create_subject(docs, embeddings):
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    return vectorstore

def save_subject(vectorstore: FAISS, user_id: str, embeddings: OpenAIEmbeddings):
    vectorstore_path = get_vectorstore_path(user_id)

    if os.path.exists(vectorstore_path): # 이전 과제 내용과 병합
        new_vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
        new_vectorstore.merge_from(vectorstore)
        new_vectorstore.save_local(vectorstore_path)
    else: # 첫 과제 내용
        vectorstore.save_local(vectorstore_path)

def get_pass_subject(user_id: str):
    vectorstore_path = get_vectorstore_path(user_id)
    embeddings = OpenAIEmbeddings()

    if os.path.exists(vectorstore_path):
        vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
        return vectorstore.as_retriever()
    return RunnablePassthrough()

def process_pdf(pdf_url: str):
    loader = PyPDFLoader(pdf_url)
    documents = loader.load()
    documents = [doc for doc in documents if len(doc.page_content.strip()) > 30]

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=50, separator="\n")
    docs = text_splitter.split_documents(documents)

    return docs

def format_docs(docs: list[Document]):
    return "\n\n".join(doc.page_content for doc in docs)

def delete_subject(user_id: str):
    vectorstore_path = get_vectorstore_path(user_id)
    if os.path.exists(vectorstore_path):
        os.remove(vectorstore_path)
