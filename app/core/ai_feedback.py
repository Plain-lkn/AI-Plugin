import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

# PDF를 읽고, 문서 쪼개는 함수
def process_pdf(pdf_url: str):
    loader = PyPDFLoader(pdf_url)
    documents = loader.load()
    documents = [doc for doc in documents if len(doc.page_content.strip()) > 30]

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=50, separator="\n")
    docs = text_splitter.split_documents(documents)

    return docs

def format_docs(docs: list[Document]):
    return "\n\n".join(doc.page_content for doc in docs)

def get_prompt():
    prompt = """
    너는 학생이 제출한 과제를 평가하고 피드백을 제공하는 AI 튜터야.
    학생의 **이전 과제 내용**과 **현재 제출한 과제 내용**을 참고해서 이번 과제에 대해 평가하고,
    학생이 발전한 점과 보완해야 할 점을 구체적으로 알려줘.
    무조건 한국어로 대답해줘.
    예외적으로 학생이 이번에 처음으로 과제를 제출할 경우 이전 과제 내용은 비어있어.

    이전 과제 내용:
    {pass_context}

    현재 제출한 과제 내용:
    {context}

    질문: {question}
    """
    return PromptTemplate.from_template(prompt)

def save_subject(vectorstore: FAISS, user_id: str, embeddings: OpenAIEmbeddings):
    vectorstore_path = f"subject_{user_id}"

    if os.path.exists(vectorstore_path): # 이전 과제 내용과 병합
        new_vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
        new_vectorstore.merge_from(vectorstore)
        new_vectorstore.save_local(vectorstore_path)
    else: # 첫 과제 내용
        vectorstore.save_local(vectorstore_path)

def get_pass_vector_store(user_id: str):
    vectorstore_path = f"subject_{user_id}"
    embeddings = OpenAIEmbeddings()

    if os.path.exists(vectorstore_path):
        vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
        return vectorstore.as_retriever()
    return RunnablePassthrough()

def generate_feedback(pdf_url: str, user_id: str):
    docs = process_pdf(pdf_url)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)

    pass_context = get_pass_vector_store(user_id)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    rag_chain = (
        {
            "pass_context": pass_context,
            "context": vectorstore.as_retriever() | format_docs,
            "question": RunnablePassthrough()
        }
        | get_prompt()
        | llm
        | StrOutputParser()
    )

    query = "문서에 대해 설명해줘"
    res = rag_chain.invoke(query)

    save_subject(vectorstore, user_id, embeddings)
    # 피드백 결과도 vector store로 저장
    return res

# 실행 예시
print(generate_feedback("/Users/sepro/Downloads/AI-Plugin/app/assets/pdf/transformer.pdf", "sepro"))