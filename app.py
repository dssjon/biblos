import streamlit as st
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.chat_models import ChatAnthropic
import streamlit_analytics
import random
from constants import *

streamlit_analytics.start_tracking(load_from_json=ANALYTICS_JSON_PATH)

# Set page config
st.set_page_config(
    layout="wide",
    menu_items={
        "Get Help": HELP_URL,
        "Report a bug": BUG_REPORT_URL,
        "About": ABOUT_URL,
    },
)


@st.cache_resource
def setup_db(persist_directory, query_instruction):
    embeddings = HuggingFaceInstructEmbeddings(
        model_name=HUGGINGFACE_INSTRUCT_MODEL_NAME,
        query_instruction=query_instruction,
    )
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    return db


bible_db = setup_db(BIBLE_DB_PERSIST_DIRECTORY, BIBLE_DB_QUERY_INSTRUCTION)
commentary_db = setup_db(
    COMMENTARY_DB_PERSIST_DIRECTORY, COMMENTARY_DB_QUERY_INSTRUCTION
)

# Setup LLM
try:
    llm = ChatAnthropic(max_tokens=MAX_TOKENS, model_name=LLM_MODEL_NAME)
except:
    st.error("No API token found, so LLM support is disabled.")
    llm = None

st.title("Biblos: Exploration Tool")

def initialize_session_state(default_queries):
    if "initialized" not in st.session_state:
        st.session_state.search_query = random.choice(list(default_queries))
        st.session_state.initialized = True

initialize_session_state(DEFAULT_QUERIES)

search_query = st.text_input(
    "Semantic search the Bible and Church Fathers:", st.session_state.search_query
)

def update_author_selection(select_all=True):
    for author in CHURCH_FATHERS:
        st.session_state[author] = select_all

def create_author_filters(church_fathers, columns):
    author_filters = {}
    for i, author in enumerate(church_fathers):
        col = columns[(i % 2) + 1]
        if author not in st.session_state:
            st.session_state[author] = True 
        author_filters[author] = col.checkbox(author, value=st.session_state[author])
    return author_filters

with st.expander("Search Options"):
    with st.header("Testament"):
        col1, col2 = st.columns([1, 1])
        with col1:
            ot_checkbox = st.checkbox("Old Testament", value=True)
        with col2:
            nt_checkbox = st.checkbox("New Testament", value=True)

    with st.header("Number of Results"):
        num_verses_to_retrieve = st.slider(
            "Number of results:", min_value=1, max_value=15, value=3, step=1
        )

    st.divider()

    with st.header("Authors"):
        cols = st.columns(3)

        with cols[0]:
            if st.button("Select all"):
                update_author_selection(select_all=True)
            if st.button("De-select all"):
                update_author_selection(select_all=False)

        author_filters = create_author_filters(CHURCH_FATHERS, cols)


def get_selected_bible_filters(ot, nt):
    if ot != nt:
        return {"testament": "OT"} if ot else {"testament": "NT"}
    return {}

bible_search_results = bible_db.similarity_search_with_relevance_scores(
    search_query,
    k=num_verses_to_retrieve,
    score_function="cosine",
    filter=get_selected_bible_filters(ot_checkbox, nt_checkbox),
)

def perform_commentary_search(commentary_db, search_query, authors):
    search_results = []
    if authors:
        for author in authors:
            results = commentary_db.similarity_search_with_relevance_scores(
                search_query,
                k=1, 
                score_function="cosine",
                filter={"father_name": author},
            )
            if results:
                search_results.extend(results)
    return search_results

selected_authors = [author for author, is_selected in author_filters.items() if is_selected]

commentary_search_results = perform_commentary_search(commentary_db, search_query, selected_authors)

def display_bible_results(results):
    st.caption("Bible search results:")
    cols = st.columns(3)
    for i, r in enumerate(results):
        with cols[i % 3]:
            content = r[0].page_content
            book = r[0].metadata[BOOK]
            chapter = r[0].metadata[CHAPTER]
            score = r[1]
            with st.expander(f"**{book}** {chapter}", expanded=True):
                st.write(f"{content}")
                st.write(f"**Similarity Score**: {score}")

def display_commentary_results(results):
    st.caption("Commentary search results:")
    cols = st.columns(3)
    results = sorted(results, key=lambda x: x[1], reverse=True)
    results = [r for r in results if r[1] >= 0.819 and len(r[0].page_content) >= 300]
    for i, r in enumerate(results):
        with cols[i % 3]:
            content, metadata = r[0].page_content, r[0].metadata
            father_name = metadata[FATHER_NAME]
            source_title = metadata[SOURCE_TITLE]
            book = metadata[BOOK]
            score = r[1]
            with st.expander(f"**{father_name}**", expanded=True):
                st.write(f"{content}")
                source_info = ", ".join(filter(None, [source_title.title() if source_title else None, f"on {book.title()}" if book else None]))
                if source_info:
                    st.write(f"**Source**: {source_info}")
                st.write(f"**Similarity Score**: {score}")


display_bible_results(bible_search_results)

def summarize_results(llm, results, summary_prompt):
    if llm is None:
        st.error(LLM_ERROR)
        st.stop()
    else:
        with st.spinner("Summarizing..."):
            #TODO: add metadata to prompt
            #content, metadata = r[0].page_content, r[0].metadata
            #father_name = metadata[FATHER_NAME]
            #source_title = metadata[SOURCE_TITLE]
            #book = metadata[BOOK]
            formatted_results = [           
                f"Source: {r[0].metadata['book']}\nContent: {r[0].page_content}"
                for r in results
            ]

            if not formatted_results:
                st.error("No results found")
                st.stop()

            llm_query = summary_prompt.format(
                topic=search_query, content="\n".join(formatted_results)
            )
            return llm.predict(llm_query)

if st.button("Summarize"):
    llm_response = summarize_results(llm, bible_search_results, BIBLE_SUMMARY_PROMPT)
    if llm_response:
        st.success(llm_response)

st.divider()

display_commentary_results(commentary_search_results)

if st.button("Summarize commentary"):
    llm_response = summarize_results(llm, commentary_search_results, COMMENTARY_SUMMARY_PROMPT)
    if llm_response:
        st.success(llm_response)

streamlit_analytics.stop_tracking(
    save_to_json=ANALYTICS_JSON_PATH, unsafe_password=UNSAFE_PASSWORD
)
