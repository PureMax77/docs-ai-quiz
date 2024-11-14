from bs4 import BeautifulSoup
import requests
import re


class DevDocsParser:
    def __init__(self, url):
        self.url = url
        self.soup = None
        self.sections = {}

    def fetch_content(self):
        """웹 페이지 콘텐츠 가져오기"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(self.url, headers=headers)
        self.soup = BeautifulSoup(response.content, "html.parser")

    def clean_text(self, text):
        """텍스트 정제"""
        # 연속된 공백을 단일 공백으로 수정
        text = re.sub(r"\s+", " ", text)
        # 불필요한 특수문자 제거
        text = re.sub(r"[\n\t\r]", " ", text)
        return text.strip()

    def extract_code_blocks(self, section):
        """코드 블록 추출"""
        content_blocks = []

        # pre 태그 내부의 code 태그 처리
        pre_elements = section.find_all("pre")
        for pre in pre_elements:
            # pre 태그 내부의 모든 code 태그 찾기
            code_elements = pre.find_all("code")
            if code_elements:
                # code 태그가 있는 경우 각각의 내용을 코드 블록으로 추가
                for code in code_elements:
                    code_text = code.get_text().strip()
                    if code_text:
                        content_blocks.append({"type": "code", "content": code_text})
            else:
                # pre 태그 직접 내용이 있는 경우
                pre_text = pre.get_text().strip()
                if pre_text:
                    content_blocks.append({"type": "code", "content": pre_text})

        return content_blocks

    def parse_sections(self):
        """문서의 주요 섹션 파싱"""
        if not self.soup:
            self.fetch_content()

        # 주요 섹션 헤더 찾기 (h1, h2, h3)
        headers = self.soup.find_all(["h1", "h2", "h3"])

        for header in headers:
            section_content = []
            current = header.find_next_sibling()

            while current and current.name not in ["h1", "h2", "h3"]:
                # pre 태그 내의 코드 블록 처리
                code_blocks = self.extract_code_blocks(current)
                section_content.extend(code_blocks)

                # 일반 텍스트 콘텐츠 처리 (pre 태그가 아닌 경우)
                if not current.find_parent("pre"):
                    # 원본 HTML을 문자열로 변환하여 처리
                    text = str(current)
                    # pre 태그 밖의 code 태그를 일반 텍스트로 변환
                    soup = BeautifulSoup(text, "html.parser")
                    for code in soup.find_all("code"):
                        # code 태그를 그 내용으로 대체
                        code.replace_with(code.get_text())

                    # 변환된 텍스트 추출
                    final_text = self.clean_text(soup.get_text())
                    if final_text:
                        section_content.append({"type": "text", "content": final_text})

                current = current.find_next_sibling()

            # 섹션 제목과 내용 저장
            if section_content:
                self.sections[self.clean_text(header.get_text())] = section_content

        return self.sections
