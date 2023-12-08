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

# Setup Bible database
@st.cache_resource
def setup_bible_db():
    embeddings = HuggingFaceInstructEmbeddings(
        model_name=HUGGINGFACE_INSTRUCT_MODEL_NAME,
        query_instruction=BIBLE_DB_QUERY_INSTRUCTION,
    )
    bible_db = Chroma(
        persist_directory=BIBLE_DB_PERSIST_DIRECTORY,
        embedding_function=embeddings,
    )
    return bible_db

# Setup Commentary database
@st.cache_resource
def setup_commentary_db():
    embeddings = HuggingFaceInstructEmbeddings(
        model_name=HUGGINGFACE_INSTRUCT_MODEL_NAME,
        query_instruction=COMMENTARY_DB_QUERY_INSTRUCTION,
    )
    commentary_db = Chroma(
        persist_directory=COMMENTARY_DB_PERSIST_DIRECTORY,
        embedding_function=embeddings,
    )
    return commentary_db

bible_db, commentary_db = setup_bible_db(), setup_commentary_db()

# Setup LLM
try:
    llm = ChatAnthropic(max_tokens=MAX_TOKENS, model_name=LLM_MODEL_NAME)
except:
    st.error('No API token found, so LLM support is disabled.')
    llm = None

st.title("Biblos: Exploration Tool")

if 'initialized' not in st.session_state:
    st.session_state.search_query = random.choice(list(DEFAULT_QUERIES))
    st.session_state.initialized = True

search_query = st.text_input("Semantic search the Bible and Church Fathers:", st.session_state.search_query)

# Initialize a dictionary to store the checkbox states
author_filters = {}
def update_author_selection(select_all=True):
    for author in CHURCH_FATHERS:
        st.session_state[author] = select_all

with st.expander("Search Options"):
    with st.header("Testament"):
        col1, col2 = st.columns([1, 1])
        with col1:
            ot = st.checkbox("Old Testament", value=True)
        with col2:
            nt = st.checkbox("New Testament", value=True)

    with st.header("Number of Results"):
        num_verses_to_retrieve = st.slider("Number of results:", min_value=1, max_value=15, value=3, step=1)
    
    st.divider()

    with st.header("Authors"):
            # Create a column layout for authors
            cols = st.columns(3)

            # Add Select All and Deselect All buttons
            with cols[0]:
                if st.button("Select All"):
                    update_author_selection(select_all=True)
            with cols[0]:
                if st.button("Deselect All"):
                    update_author_selection(select_all=False)

            # Initialize checkboxes with states stored in session_state
            for i, author in enumerate(CHURCH_FATHERS):
                col = cols[(i % 2) + 1]
                if author not in st.session_state:
                    st.session_state[author] = True  # Default state is checked
                author_filters[author] = col.checkbox(author, value=st.session_state[author])


# Build a search filter for the testaments
testament_filter = {}
if ot != nt:
    if ot:
        testament_filter = {"testament": "OT"}
    else:
        testament_filter = {"testament": "NT"}

# Perform searches on both databases
bible_search_results = bible_db.similarity_search_with_relevance_scores(
    search_query,
    k=num_verses_to_retrieve,
    score_function="cosine",
    filter=testament_filter,
)

selected_authors = [author for author, is_selected in author_filters.items() if is_selected]

if len(selected_authors) > 1:
    author_filter_query = {"$or": [{"father_name": author} for author in selected_authors]}
elif len(selected_authors) == 1:
    author_filter_query = {"father_name": selected_authors[0]}
else:
    commentary_search_results = []

commentary_search_results = []

if len(selected_authors) > 0:

    for author in selected_authors:
        # For each selected author, perform an individual search and get the top result
        individual_author_results = commentary_db.similarity_search_with_relevance_scores(
            search_query,
            k=1,  # We only want the top result for each author
            score_function="cosine",
            filter={"father_name": author}
        )
        if individual_author_results:
            commentary_search_results.extend(individual_author_results)

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
            llm_query = BIBLE_SUMMARY_PROMPT.format(topic=search_query, passages=all_results)
            llm_response = llm.predict(llm_query)
            st.success(llm_response)
st.divider()

# Display Commentary search results
st.caption("Commentary search results:")
cols = st.columns(3)  # Creating three columns for Commentary results
# sort and filter commentary results by score, excluding results < 0.819
commentary_search_results = sorted(commentary_search_results, key=lambda x: x[1], reverse=True)
commentary_search_results = [r for r in commentary_search_results if r[1] >= 0.819]
commentary_search_results = [r for r in commentary_search_results if len(r[0].page_content) >= 300]
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
                results.append(f"Source: {father_name}{book}{source_title}\nContent: {content}")

            if not results:
                st.error("No results found")
                st.stop()


            all_results = "\n".join(results)

            llm_query = COMMENTARY_SUMMARY_PROMPT.format(topic=search_query, commentaries=all_results)
            llm_response = llm.predict(llm_query)
            st.success(llm_response)

streamlit_analytics.stop_tracking(
    save_to_json=ANALYTICS_JSON_PATH, unsafe_password=UNSAFE_PASSWORD
)
