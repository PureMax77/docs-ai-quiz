import streamlit as st
import json
from langchain.schema import BaseOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from utils.llm_utils import DevDocsParser

from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

st.set_page_config(page_title="DocsQuizGPT", page_icon="❓")

st.markdown(
    """
    # DocsQuizGPT
            
    DocsQuizGPT에 오신 것을 환영합니다.     
    퀴즈를 통해 공부했던 개발 지식을 확인하고 실력을 향상시켜보세요~~!
"""
)

# Streamlit UI
if "parsed_sections" not in st.session_state:
    st.session_state.parsed_sections = None

if "generate_quiz" not in st.session_state:
    st.session_state.generate_quiz = False

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = None


class JsonOutputParser(BaseOutputParser):
    def parse(self, text):
        text = text.replace("```", "").replace("json", "")
        return json.loads(text)


output_parser = JsonOutputParser()

llm = ChatOpenAI(
    temperature=0.7, api_key=os.environ.get("OPENAI_API_KEY"), model_name="gpt-4o"
)


@st.cache_data(show_spinner="퀴즈 생성중...")
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
    당신은 매우 강력한 개발 관련 퀴즈 생성기입니다.
    다음 개발문서 내용을 기반으로 2~4개의 퀴즈를 만들어주세요.
    퀴즈는 실제 개발자 면접이나 기술 테스트에서 나올 수 있는 수준으로 만들어주세요.
    
    개발문서 내용:
    {content}
    
    당신은 문제를 JSON 형식으로 포맷합니다.
    (o)이 있는 객관식 문항이 정답입니다.     
    
    예시 Input:
    Question: Next.js에서 새로운 페이지를 생성할 때 사용하는 파일 이름은?
    Answers: component.js|style.js|page.js(o)|route.js

    Question: Next.js에서 이미지나 폰트 같은 정적 파일은 어느 폴더에 위치해야 하나요?
    Answers: src/|public/(o)|assets/|static/

    Question: Next.js 개발 서버의 기본 포트 번호는?
    Answers: 5000번|8080번|3000번(o)|4000번
    
    예시 Output:
    ```json
    {{
        "questions": [
            {{
                "question": "Next.js에서 새로운 페이지를 생성할 때 사용하는 파일 이름은?",
                "answers": [
                    {{
                        "answer": "component.js",
                        "correct": false,
                        "reason": ""
                    }},
                    {{
                        "answer": "style.js",
                        "correct": false,
                        "reason": ""
                    }},
                    {{
                        "answer": "page.js",
                        "correct": true,
                        "reason": "Next.js의 App Router에서는 page.js 파일을 사용하여 새로운 페이지를 생성합니다. 이 파일은 해당 라우트의 UI를 정의하며, 폴더 구조가 곧 URL 경로가 됩니다."
                    }},
                    {{
                        "answer": "route.js",
                        "correct": false,
                        "reason": ""
                    }}
                ]
            }},
            {{
                "question": "Next.js에서 이미지나 폰트 같은 정적 파일은 어느 폴더에 위치해야 하나요?",
                "answers": [
                    {{
                        "answer": "src/",
                        "correct": false,
                        "reason": ""
                    }},
                    {{
                        "answer": "public/",
                        "correct": true,
                        "reason": "Next.js에서 public/ 폴더는 정적 자산을 저장하는 특별한 디렉토리입니다. 이 폴더 안에 있는 파일들은 코드에서 '/' 루트 경로로 직접 접근할 수 있습니다."
                    }},
                    {{
                        "answer": "assets/",
                        "correct": false,
                        "reason": ""
                    }},
                    {{
                        "answer": "static/",
                        "correct": false,
                        "reason": ""
                    }}
                ]
            }},
            {{
                "question": "Next.js 개발 서버의 기본 포트 번호는?",
                "answers": [
                    {{
                        "answer": "5000번",
                        "correct": false,
                        "reason": ""
                    }},
                    {{
                        "answer": "8080번",
                        "correct": false,
                        "reason": ""
                    }},
                    {{
                        "answer": "3000번",
                        "correct": true,
                        "reason": "Next.js 개발 서버는 기본적으로 3000번 포트에서 실행됩니다. 'npm run dev' 또는 'yarn dev' 명령어 실행 시 자동으로 http://localhost:3000 에서 서버가 시작됩니다."
                    }},
                    {{
                        "answer": "4000번",
                        "correct": false,
                        "reason": ""
                    }}
                ]
            }}
        ]
    }}
    ```

    설명: [
    
    참고:
    - 가능한 경우 코드박스를 포함한 코드 예제도 보기에 만들어주세요
    - 실무에서 마주칠 수 있는 상황을 반영해주세요
    - 내용과 직접 관련된 퀴즈만 생성하고, 절대로 없는 내용을 상상으로 만들지마세요!
    """

    prompt = PromptTemplate(input_variables=["content"], template=template)

    chain = prompt | llm | output_parser

    return chain.invoke({"content": formatted_content})


########### UI #####################
with st.sidebar:
    docs = None
    url = None
    choice = st.selectbox("원하는 방식을 선택", ("Website", "File"))
    if choice == "Website":
        url = st.text_input("Website URL")
    else:
        st.write("준비중")

if url:
    try:
        with st.spinner("문서를 분석하는 중..."):
            parser = DevDocsParser(url)
            st.session_state.parsed_sections = parser.parse_sections()
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")

# 문서 분석 결과가 있을 때 섹션 선택과 퀴즈 생성 UI 표시
if st.session_state.parsed_sections:
    # st.write(st.session_state.parsed_sections)
    selected_section = st.selectbox(
        "퀴즈를 생성할 섹션을 선택하세요:",
        options=list(st.session_state.parsed_sections.keys()),
    )
    # 퀴즈 생성 버튼 (한번 True가 되면 더 이상 변경 불가)
    if not st.session_state.generate_quiz:
        st.session_state.generate_quiz = st.button("퀴즈 생성")


if st.session_state.generate_quiz:
    # 선택된 섹션의 내용으로 퀴즈 생성
    res = generate_dev_quiz(st.session_state.parsed_sections[selected_section])
    # 퀴즈 표시
    with st.form("questions_form"):
        for question in res["questions"]:
            st.write(question["question"])
            value = st.radio(
                "Select an option.",
                [answer["answer"] for answer in question["answers"]],
                index=None,
            )

            if value is not None:  # 답변을 선택했을 때만 실행
                # 선택된 답변에 해당하는 answer 객체 찾기
                selected_answer = next(
                    answer
                    for answer in question["answers"]
                    if answer["answer"] == value
                )

                if selected_answer["correct"]:
                    st.success("정답입니다!\n\n")
                    st.info(selected_answer["reason"])
                else:
                    st.error("틀렸습니다!\n\n")
                    # enumerate와 함께 인덱스와 답안 모두 가져오기
                    correct_index, correct_answer = next(
                        (idx, answer)
                        for idx, answer in enumerate(question["answers"], 1)
                        if answer["correct"]
                    )
                    st.info(
                        f"{correct_index}번이 정답입니다.\n\n{correct_answer['reason']}"
                    )

        button = st.form_submit_button("제출")  # 버튼 텍스트 추가
