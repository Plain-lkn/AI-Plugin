from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

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

def generate_feedback(pass_context, context, query):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    rag_chain = (
        {
            "pass_context": pass_context,
            "context": context,
            "question": RunnablePassthrough()
        }
        | get_prompt()
        | llm
        | StrOutputParser()
    )

    res = rag_chain.invoke(query)
    # 피드백 결과도 vector store로 저장
    return res