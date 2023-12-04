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
    try:
        llm = ChatAnthropic(max_tokens=100000, model_name="claude-2.1")
    except:
        print(f'No API token found, so LLM support is disabled.')
        llm = None

    return db, llm

db, llm = setup()

st.title("Biblos: Exploration Tool")

prompt = """Based on the user's search query, the topic is: {topic}

Please provide a concise summary of the key points made in the following Bible passages about the topic above, including chapter and verse references. Focus only on the content found in these specific verses. Explain connections between the passages and how they theologically relate to the overarching biblical meta narrative across both Old and New Testaments.  

{passages}"""

default_query = "What did Jesus say about eternal life?"

search_query = st.text_input(
    "Semantic search:",
    default_query,
)

with st.expander("Search Options"):
    with st.header("Testament"):
        col1, col2 = st.columns([1, 1])
        with col1:
            ot = st.checkbox("Old Testament", value=True)
        with col2:
            nt = st.checkbox("New Testament", value=True)
    with st.header("Number of Results"):
        num_verses_to_retrieve = st.slider(
            "Number of results:", min_value=1, max_value=10, value=4, step=1
        )

# Build a search filter for the testaments
testament_filter = {}
if ot != nt:
    if ot:
        testament_filter = {"testament": "OT"}
    else:
        testament_filter = {"testament": "NT"}

search_results = db.similarity_search_with_relevance_scores(
    search_query,
    k=num_verses_to_retrieve,
    score_function="cosine",
    filter=testament_filter,
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
        if llm is None:
            st.error("No API token found, so LLM support is disabled.")
            st.stop()
        else:
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
                llm_query = prompt.format(topic=search_query, passages=all_results)
                llm_response = llm.predict(llm_query)
                st.success(llm_response)

streamlit_analytics.stop_tracking(
    save_to_json="./data/analytics.json", unsafe_password="x"
)
