import streamlit as st

st.set_page_config(page_title="DocsQuizGPT", page_icon="💼")

st.markdown(
    """
    # DocsQuizGPT
            
    Welcome to DocsQuizGPT.
            
    Write down the name of a company and our Agent will do the research for you.
"""
)


with st.sidebar:
  docs = None
  choice = st.selectbox("원하는 방식을 선택", ("File", "Website"))
  if choice == "File":
    a =1
  else:
    url = st.text_input("Website URL")
    if url:
      docs = 3
      