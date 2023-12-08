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

if "initialized" not in st.session_state:
    st.session_state.search_query = random.choice(list(DEFAULT_QUERIES))
    st.session_state.initialized = True

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

st.caption("Bible search results:")
cols = st.columns(3)  # Creating three columns for Bible results
for i, r in enumerate(bible_search_results):
    with cols[i % 3]:
        content = r[0].page_content
        book = r[0].metadata["book"]
        chapter = r[0].metadata["chapter"]
        score = r[1]
        with st.expander(f"**{book}** {chapter}", expanded=True):
            st.write(f"{content}")
            st.write(f"**Similarity Score**: {score}")

if st.button("Summarize"):
    if llm is None:
        st.error(LLM_ERROR)
        st.stop()
    else:
        with st.spinner("Summarizing..."):
            results = []
            for r in bible_search_results:
                content = r[0].page_content
                book = r[0].metadata["book"]
                chapter = r[0].metadata["chapter"]
                results.append(f"Source: {book}\nContent: {content}")

            if not results:
                st.error("No results found")
                st.stop()

            all_results = "\n".join(results)
            llm_query = BIBLE_SUMMARY_PROMPT.format(
                topic=search_query, passages=all_results
            )
            llm_response = llm.predict(llm_query)
            st.success(llm_response)
st.divider()

# Display Commentary search results
st.caption("Commentary search results:")
cols = st.columns(3)  # Creating three columns for Commentary results
# sort and filter commentary results by score, excluding results < 0.819
commentary_search_results = sorted(
    commentary_search_results, key=lambda x: x[1], reverse=True
)
commentary_search_results = [r for r in commentary_search_results if r[1] >= 0.819]
commentary_search_results = [
    r for r in commentary_search_results if len(r[0].page_content) >= 300
]
for i, r in enumerate(commentary_search_results):
    with cols[i % 3]:
        content = r[0].page_content
        father_name = r[0].metadata[FATHER_NAME]
        source_title = r[0].metadata[SOURCE_TITLE]
        book = r[0].metadata[BOOK]
        score = r[1]
        with st.expander(f"**{father_name}**", expanded=True):
            st.write(f"{content}")
            if book:
                book = book.title()
            if source_title:
                source_title = source_title.title()
            if not source_title and book:
                st.write(f"**Source**: Commentary on {book}")
            if not book and source_title:
                st.write(f"**Source**: {source_title}")
            if source_title and book:
                st.write(f"**Source**: {source_title}, on {book}")
            st.write(f"**Similarity Score**: {score}")

if st.button("Summarize Commentary"):
    if llm is None:
        st.error(LLM_ERROR)
        st.stop()
    else:
        with st.spinner("Summarizing..."):
            results = []
            for r in commentary_search_results:
                content = r[0].page_content
                father_name = r[0].metadata[FATHER_NAME]
                source_title = r[0].metadata[SOURCE_TITLE]
                book = r[0].metadata[BOOK]
                results.append(
                    f"Source: {father_name}{book}{source_title}\nContent: {content}"
                )

            if not results:
                st.error("No results found")
                st.stop()

            all_results = "\n".join(results)

            llm_query = COMMENTARY_SUMMARY_PROMPT.format(
                topic=search_query, commentaries=all_results
            )
            llm_response = llm.predict(llm_query)
            st.success(llm_response)

streamlit_analytics.stop_tracking(
    save_to_json=ANALYTICS_JSON_PATH, unsafe_password=UNSAFE_PASSWORD
)
