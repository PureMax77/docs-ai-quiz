import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from utils.llm_utils import DevDocsParser

from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# Streamlit UI
if "parsed_sections" not in st.session_state:
    st.session_state.parsed_sections = None

st.set_page_config(page_title="DocsStudyGPT", page_icon="💼")

st.markdown(
    """
    # DocsStudyGPT
            
    Welcome to DocsStudyGPT.
            
    Write down the name of a company and our Agent will do the research for you.
"""
)

llm = ChatOpenAI(
    temperature=0.7, api_key=os.environ.get("OPENAI_API_KEY"), model_name="gpt-4o"
)


def generate_dev_quiz(section_content):
    """개발 문서 기반 퀴즈 생성"""
    # 섹션 내용을 텍스트로 변환
    formatted_content = ""
    for item in section_content:
        if item["type"] == "text":
            formatted_content += f"\t설명: {item['content']}\n\n"
        else:  # code
            formatted_content += f"\t코드 예제:\n{item['content']}\n\n"

    template = """
    다음 개발 문서 내용을 기반으로 3개 이하의 퀴즈를 만들어주세요.
    퀴즈는 실제 개발자 면접이나 기술 테스트에서 나올 수 있는 수준으로 만들어주세요.
    
    내용:
    {content}
    
    다음 형식으로 작성해주세요:
    
    Q1. [기술적인 질문]
    1) [보기1]
    2) [보기2]
    3) [보기3]
    4) [보기4]
    정답: [번호]
    
    설명: [정답에 대한 기술적 설명과 실제 사용 사례]
    
    참고:
    - 단순 암기가 아닌 개념 이해를 테스트하는 문제를 만들어주세요
    - 가능한 경우 코드박스를 포함한 코드 예제도 보기에 만들어주세요
    - 실무에서 마주칠 수 있는 상황을 반영해주세요
    - 내용과 직접 관련된 퀴즈만 생성하고 없는 내용을 상상으로 만들지마세요 
    """

    prompt = PromptTemplate(input_variables=["content"], template=template)

    chain = prompt | llm

    return chain.invoke({"content": formatted_content})


# Streamlit UI
st.title("개발 문서 퀴즈 생성기")
st.markdown(
    """
이 도구는 Next.js와 같은 개발 문서를 분석하여 실제 기술 면접이나 테스트에 도움이 될 수 있는 퀴즈를 생성합니다.
"""
)

url = st.text_input("개발 문서 URL을 입력하세요:")

if url and st.button("문서 분석"):
    try:
        with st.spinner("문서를 분석하는 중..."):
            parser = DevDocsParser(url)
            st.session_state.parsed_sections = parser.parse_sections()
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")

# 문서 분석 결과가 있을 때 섹션 선택과 퀴즈 생성 UI 표시
if st.session_state.parsed_sections:
    st.success("문서 분석 완료!")
    st.write(st.session_state.parsed_sections)
    selected_section = st.selectbox(
        "퀴즈를 생성할 섹션을 선택하세요:",
        options=list(st.session_state.parsed_sections.keys()),
    )

    if st.button("퀴즈 생성"):
        with st.spinner("퀴즈를 생성하는 중..."):
            # 선택된 섹션의 내용으로 퀴즈 생성
            quiz = generate_dev_quiz(st.session_state.parsed_sections[selected_section])

            # 퀴즈 표시
            st.markdown("### 생성된 퀴즈")
            st.write(quiz.content)

            # 원본 섹션 내용 표시 (접을 수 있는 형태로)
            with st.expander("원본 섹션 내용"):
                for item in st.session_state.parsed_sections[selected_section]:
                    if item["type"] == "text":
                        st.write(item["content"])
                    else:
                        st.code(item["content"])

# 사이드바에 도움말 추가
with st.sidebar:
    st.header("사용 가이드")
    st.markdown(
        """
    ### 특징
    - 개발 문서의 구조를 이해하고 섹션별로 분석
    - 코드 예제를 포함한 퀴즈 생성
    - 실제 기술 면접 스타일의 문제 생성
    
    ### 사용 팁
    1. 전체 문서 대신 특정 개념이나 API 문서 페이지를 입력하면 더 집중된 퀴즈 생성 가능
    2. 선택한 섹션의 내용을 확인하고 퀴즈의 적절성 검토
    3. 코드 예제가 포함된 섹션을 선택하면 더 실용적인 퀴즈 생성
    """
    )
