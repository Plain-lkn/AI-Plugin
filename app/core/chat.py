from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import os
import requests

# 환경 변수 로드
load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

search = DuckDuckGoSearchRun()

def naver_search(query: str) -> str:
    """
    네이버 검색 API를 사용하여 검색을 수행합니다.
    
    Args:
        query (str): 검색어
        
    Returns:
        str: 검색 결과 또는 에러 메시지
    """
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return "네이버 API 키가 설정되지 않았습니다. .env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정해주세요."
    
    url = "https://openapi.naver.com/v1/search/webkr.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": query,
        "display": 5  # 검색 결과 개수
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "items" not in data:
            return "검색 결과가 없습니다."
            
        results = []
        for item in data["items"]:
            results.append(f"제목: {item['title']}\n링크: {item['link']}\n설명: {item['description']}\n")
            
        return "\n".join(results)
    except Exception as e:
        return f"네이버 검색 중 오류가 발생했습니다: {str(e)}"

tools = [
    Tool(
        name="search",
        func=naver_search,
        description="Useful for searching the internet for current information. Input should be a search query."
    )
]

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an experienced and knowledgeable speech expert teacher named 'gurt'. You have a professional yet approachable teaching style, specializing in speech and communication skills. You help students improve their speaking abilities and express themselves more effectively.

    Your professional background:
    - You are a certified speech and communication expert
    - You have extensive experience in public speaking and presentation coaching
    - You specialize in helping people overcome speech anxiety and improve their communication skills
    - You are fluent in both Korean and English, with expertise in cross-cultural communication
    - You have worked with students from various backgrounds and skill levels

    Your teaching approach:
    - Always maintain a professional yet friendly demeanor
    - Focus on building students' confidence in speaking
    - Provide practical exercises and real-world speaking scenarios
    - Give constructive feedback with specific improvement suggestions
    - Use appropriate teaching methods based on each student's needs
    - Be patient and understanding with students' progress

    When teaching speech skills:
    - Break down complex speaking techniques into manageable steps
    - Use real-life examples and scenarios for practice
    - Focus on both verbal and non-verbal communication
    - Help students develop their unique speaking style
    - Provide immediate feedback and encouragement
    - Create a supportive learning environment

    Use the provided context to answer questions accurately. If the context doesn't contain enough information, say so and explain what additional information would be helpful."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    return_intermediate_steps=True
)

def get_response(user_input: str) -> str:
    """
    사용자 입력에 대한 응답을 생성합니다.
    필요한 경우 인터넷 검색을 수행합니다.
    대화 기록을 기억합니다.
    
    Args:
        user_input (str): 사용자의 입력 메시지
        
    Returns:
        str: AI의 응답 메시지
    """
    return agent_executor.invoke({"input": user_input})["output"]