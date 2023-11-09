from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.chat_models import ChatAnthropic
import streamlit as st
import streamlit_analytics

streamlit_analytics.start_tracking(load_from_json="./data/analytics.json")

url = "https://www.github.com/dssjon"
st.set_page_config(
    layout="wide",
    menu_items={
        "Get Help": url,
        "Report a bug": url,
        "About": f"Made with <3 by {url}",
    },
)

@st.cache_resource
def setup():
    embeddings = HuggingFaceInstructEmbeddings(
        model_name="hkunlp/instructor-large",
        query_instruction="Represent the Religious Bible verse text for semantic search:",
    )
    db = Chroma(
        persist_directory="./data/db",
        embedding_function=embeddings,
    )
    llm = ChatAnthropic(max_tokens=100000)
    return db, llm


db, llm = setup()

st.title("Biblos: Exploration Tool")

prompt = "Can you provide key points about what these specific passages from the following texts say about the given topic, including related chapter and verse reference? Please restrict your summary to the content found exclusively in these verses and do not reference other biblical verses or context. Explain how they relate to each other, theologically, in the context of the meta narrative of the gospel, across Old and New Testaments. The topic is: "

default_query = "What did Jesus say about eternal life?"

search_query = st.text_input(
    "Semantic search:",
    default_query,
)

search_results = db.similarity_search_with_relevance_scores(
    search_query,
    k=4,
    score_function="cosine",
)

col1, col2 = st.columns([1, 1])

with col1:
    for r in search_results:
        content = r[0].page_content
        metadata = r[0].metadata["book"]
        chapter = r[0].metadata["chapter"]
        score = r[1]
        with st.expander(f"**{metadata}** {chapter}", expanded=True):
            st.write(f"{content}")
            st.write(f"**Similarity Score**: {score}")
with col2:
    if st.button("Summarize"):
        with st.spinner("Summarizing text..."):
            results = []
            for r in search_results:
                content = r[0].page_content
                metadata = r[0].metadata["book"]
                chapter = r[0].metadata["chapter"]
                results.append(f"Source: {metadata}\nContent: {content}")

            if results == "":
                st.error("No results found")
                st.stop()

            all_results = "\n".join(results)
            llm_query = f"{prompt} {search_query}:\n{all_results}"
            llm_response = llm.predict(llm_query)
            st.success(llm_response)

streamlit_analytics.stop_tracking(
    save_to_json="./data/analytics.json", unsafe_password="x"
)
