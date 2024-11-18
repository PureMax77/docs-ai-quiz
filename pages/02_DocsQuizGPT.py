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
    
    사이드바에서 공부하길 원하는 Docs URL 또는 파일을 입력하면 퀴즈가 생성됩니다.

    퀴즈를 통해 공부했던 개발 지식을 확인하고 실력을 향상시켜보세요~~!
"""
)


# Streamlit UI
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""

if "parsed_sections" not in st.session_state:
    st.session_state.parsed_sections = None

if "generate_quiz" not in st.session_state:
    st.session_state.generate_quiz = False

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = None

all_title = "전체 내용"


class JsonOutputParser(BaseOutputParser):
    def parse(self, text):
        text = text.replace("```", "").replace("json", "")
        return json.loads(text)


output_parser = JsonOutputParser()


def initialize_openai_client():
    try:
        client = ChatOpenAI(
            temperature=0.7,
            api_key=st.session_state["openai_api_key"],
            model_name="gpt-4o",
        )
        a = client.invoke("hi")  # 정상작동 테스트
        return True
    except Exception as e:
        print(e)
        st.sidebar.error("Invalid API key. Please check your API key.")
        st.session_state["openai_api_key"] = ""
        return False


def get_llm():
    """OpenAI LLM 인스턴스를 반환합니다."""
    if not st.session_state.get("openai_api_key"):
        raise ValueError("OpenAI API key is not set")

    client = ChatOpenAI(
        temperature=0.7, api_key=st.session_state.openai_api_key, model_name="gpt-4o"
    )
    return client


@st.cache_data(show_spinner="퀴즈 생성중...")
def generate_dev_quiz(section_title, section_content):
    """개발 문서 기반 퀴즈 생성"""
    # 섹션 내용을 텍스트로 변환

    formatted_content = ""
    if not section_title == all_title:
        # 일부 섹션 선택의 경우
        for item in section_content:
            if item["type"] == "text":
                formatted_content += f"\t설명: {item['content']}\n\n"
            else:  # code
                formatted_content += f"\t코드 예제:\n{item['content']}\n\n"
    else:
        # 전체 내용 선택의 경우
        for title, content in section_content.items():
            # 섹션 제목 추가
            formatted_content += f"[{title}]\n\n"
            # 섹션 내용을 순회하며 텍스트 생성
            for item in content:
                if item["type"] == "text":
                    formatted_content += f"\t설명: {item['content']}\n\n"
                elif item["type"] == "code":
                    formatted_content += f"\t코드 예제:\n{item['content']}\n\n"

    template = """
    당신은 매우 강력한 개발 관련 퀴즈 생성기입니다.
    다음 개발문서 내용을 기반으로 2~5개의 퀴즈를 만들어주세요.
    퀴즈는 실제 개발자 면접이나 기술 테스트에서 나올 수 있는 수준으로 만들어주세요.
    
    개발문서 내용:
    {content}
    
    당신은 문제를 JSON 형식으로 포맷합니다. 
    
    예시 Input:
    Question: Next.js에서 새로운 페이지를 생성할 때 사용하는 파일 이름은?
    Answers: component.js|style.js|page.js|route.js

    Question: ```typescript
    export default function handler(req, res) {{
        if (req.method === 'GET') {{
        res.status(200).json({{ message: 'Hello' }})
        }}
    }}

    // 위 코드는 Next.js의 어떤 라우터 방식에서 사용되나요?
    ```
    Answers: Pages Router|App Router|Server Router|API Router
    
    Question: Next.js 개발 서버의 기본 포트 번호는?
    Answers: 5000번|8080번|3000번|4000번
    
    예시 Output:
    ```json
    {{
        "questions": [
            {{
                "question": "Next.js에서 새로운 페이지를 생성할 때 사용하는 파일 이름은?",
                "type": "text",
                "answers": [
                    {{
                        "answer": "component.js",
                        "correct": false
                    }},
                    {{
                        "answer": "style.js",
                        "correct": false
                    }},
                    {{
                        "answer": "page.js",
                        "correct": true
                    }},
                    {{
                        "answer": "route.js",
                        "correct": false
                    }}
                ],
                "reason": "Next.js의 App Router에서는 page.js 파일을 사용하여 새로운 페이지를 생성합니다. 이 파일은 해당 라우트의 UI를 정의하며, 폴더 구조가 곧 URL 경로가 됩니다."
            }},
            {{
                "question": "export default function handler(req, res) {{\\n  if (req.method === 'GET') {{\\n    res.status(200).json({{ message: 'Hello' }})\\n  }}\\n}}\\n\\n// 위 코드는 Next.js의 어떤 라우터 방식에서 사용되나요?",
                "type": "code",
                "code_type": "typescript",
                "answers": [
                    {{
                        "answer": "Pages Router",
                        "correct": true
                    }},
                    {{
                        "answer": "App Router",
                        "correct": false
                    }},
                    {{
                        "answer": "Server Router",
                        "correct": false
                    }},
                    {{
                        "answer": "API Router",
                        "correct": false
                    }}
                ],
                "reason": "이 코드는 Pages Router의 전형적인 API 라우트 핸들러 패턴입니다. App Router에서는 이런 방식 대신 HTTP 메서드명을 함수명으로 사용합니다."
            }},
            {{
                "question": "Next.js 개발 서버의 기본 포트 번호는?",
                "type": "text",
                "answers": [
                    {{
                        "answer": "5000번",
                        "correct": false
                    }},
                    {{
                        "answer": "8080번",
                        "correct": false
                    }},
                    {{
                        "answer": "3000번",
                        "correct": true
                    }},
                    {{
                        "answer": "4000번",
                        "correct": false
                    }}
                ],
                "reason": "Next.js 개발 서버는 기본적으로 3000번 포트에서 실행됩니다. 'npm run dev' 또는 'yarn dev' 명령어 실행 시 자동으로 http://localhost:3000 에서 서버가 시작됩니다."
            }}
        ]
    }}
    ```
    
    참고:
    - 실무에서 마주칠 수 있는 상황을 반영해주세요
    - 내용과 직접 관련된 퀴즈만 생성하고, 절대로 없는 내용을 상상으로 만들지마세요!
    - 코드형 질문의 경우:
        * question에 실제 코드와 질문을 주석으로 포함해주세요
        * code_type을 반드시 명시해주세요 (python, javascript, typescript 등)
        * answer는 텍스트 형태로 작성해주세요
    """

    prompt = PromptTemplate(input_variables=["content"], template=template)
    llm = get_llm()

    chain = prompt | llm | output_parser

    return chain.invoke({"content": formatted_content})


########### UI #####################
with st.sidebar:
    docs = None
    url = None

    api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state["openai_api_key"],
        type="password",
        placeholder="sk-...",
        help="Get your API key from https://platform.openai.com/api-keys",
    )

    if api_key != st.session_state["openai_api_key"]:
        st.session_state["openai_api_key"] = api_key
        if api_key:
            with st.spinner("Validating API key..."):
                is_valid = initialize_openai_client()
            if is_valid:
                st.success("API key is valid!")

    choice = st.selectbox("원하는 방식을 선택", ("Website", "File"))
    if choice == "Website":
        url = st.text_input("Website URL")
    else:
        st.write("준비중")


if "openai_api_key" not in st.session_state or not st.session_state["openai_api_key"]:
    st.warning(
        "퀴즈 진행을 위해서 좌측 사이드바에 당신의 OpenAI API key를 입력해주세요."
    )
else:
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
            options=[all_title] + list(st.session_state.parsed_sections.keys()),
        )
        # 퀴즈 생성 버튼 (한번 True가 되면 더 이상 변경 불가)
        if not st.session_state.generate_quiz:
            st.session_state.generate_quiz = st.button("퀴즈 생성")

    if st.session_state.generate_quiz:
        # 선택된 섹션의 내용으로 퀴즈 생성

        # 전체 내용 선택과 일부 섹션 선택의 데이터 분기
        section_data = (
            st.session_state.parsed_sections
            if selected_section == all_title
            else st.session_state.parsed_sections[selected_section]
        )

        res = generate_dev_quiz(selected_section, section_data)
        # 퀴즈 표시
        with st.form("questions_form"):
            for i, question in enumerate(res["questions"]):
                if i != 0:
                    st.write("")
                    st.write("")
                if question["type"] == "text":
                    st.write(question["question"])
                else:
                    st.code(
                        question["question"],
                        language=question["code_type"],
                        wrap_lines=True,
                    )

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
                        st.info(question["reason"])
                    else:
                        st.error("틀렸습니다!\n\n")
                        # enumerate와 함께 인덱스와 답안 모두 가져오기
                        correct_index, correct_answer = next(
                            (idx, answer)
                            for idx, answer in enumerate(question["answers"], 1)
                            if answer["correct"]
                        )
                        st.info(
                            f"{correct_index}번이 정답입니다.\n\n{question['reason']}"
                        )

            button = st.form_submit_button("제출")  # 버튼 텍스트 추가
