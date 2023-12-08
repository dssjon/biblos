import streamlit as st
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceInstructEmbeddings
#from langchain.chat_models import ChatAnthropic
import streamlit_analytics
import random
from constants import *
from concurrent.futures import ThreadPoolExecutor, as_completed

streamlit_analytics.start_tracking(load_from_json=ANALYTICS_JSON_PATH)

st.set_page_config(
    layout="wide",
    menu_items={
        "Get Help": HELP_URL,
        "Report a bug": BUG_REPORT_URL,
        "About": ABOUT_URL,
    },
)

st.markdown("""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-L728QPRD2Y"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-L728QPRD2Y');
    </script>
   """, unsafe_allow_html=True)

@st.cache_resource
def setup_db(persist_directory, query_instruction):
    embeddings = HuggingFaceInstructEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        query_instruction=query_instruction,
    )
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    return db


bible_db = setup_db(DB_DIR, DB_QUERY)
commentary_db = setup_db(COMMENTARY_DB_DIR, COMMENTARY_DB_QUERY)

st.title(TITLE)


def initialize_session_state(default_queries):
    if "initialized" not in st.session_state:
        st.session_state.search_query = random.choice(list(default_queries))
        st.session_state.initialized = True


initialize_session_state(DEFAULT_QUERIES)

search_query = st.text_input(SEARCH_LABEL, st.session_state.search_query)


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


def select_options():
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        ot = st.checkbox("Old Testament", value=True)
    with col2:
        nt = st.checkbox("New Testament", value=True)
    with col3:
        st.session_state.enable_commentary = st.checkbox("Church Fathers", value=False)
    with col4:
        count = st.slider("Number of Bible Results", min_value=1, max_value=15, value=3, step=1)
    return ot, nt, count



with st.expander("Search Options"):
    
    ot_checkbox, nt_checkbox, count = select_options()

def get_selected_bible_filters(ot, nt):
    if ot != nt:
        return {"testament": "OT"} if ot else {"testament": "NT"}
    return {}


bible_search_results = bible_db.similarity_search_with_relevance_scores(
    search_query,
    k=count,
    score_function=SCORE_FUNCTION,
    filter=get_selected_bible_filters(ot_checkbox, nt_checkbox),
)


def perform_commentary_search_parallel(commentary_db, search_query):
    search_results = []

    def search_for_author(author):
        return commentary_db.similarity_search_with_relevance_scores(
            search_query,
            k=1,
            score_function=SCORE_FUNCTION,
            filter={FATHER_NAME: author},
        )

    # Use ThreadPoolExecutor to run searches in parallel
    with ThreadPoolExecutor() as executor:
        # Submit all the search tasks and get a list of futures
        future_to_author = {
            executor.submit(search_for_author, author): author for author in CHURCH_FATHERS
        }

        # As each future completes, extend the search results
        for future in as_completed(future_to_author):
            author = future_to_author[future]
            try:
                results = future.result()
                if results:
                    search_results.extend(results)
            except Exception as exc:
                print(f"Author search generated an exception for {author}: {exc}")

    return search_results



def display_bible_results(results):
    # cols = st.columns(3)
    for i, r in enumerate(results):
    #     with cols[i % 3]:
        content = r[0].page_content
        book = r[0].metadata[BOOK]
        chapter = r[0].metadata[CHAPTER]
        score = r[1]
        with st.expander(f"**{book}** {chapter}", expanded=True):
            st.write(f"{content}")
            st.write(SCORE_RESULT.format(value=score))


def display_commentary_results(results):
    #cols = st.columns(3)
    results = sorted(results, key=lambda x: x[1], reverse=True)
    results = [r for r in results if r[1] >= 0.81 and len(r[0].page_content) >= 325]
    for i, r in enumerate(results):
        #with cols[i % 3]:
        content, metadata = r[0].page_content, r[0].metadata
        father_name = metadata[FATHER_NAME]
        source_title = metadata[SOURCE_TITLE]
        book = metadata[BOOK]
        score = r[1]
        with st.expander(f"**{father_name}**", expanded=True):
            st.write(f"{content}")
            source_info = ", ".join(
                filter(
                    None,
                    [
                        source_title.title() if source_title else None,
                        f"on {book.title()}" if book else None,
                    ],
                )
            )
            if source_info:
                st.write(f"**Source**: {source_info}")
            st.write(SCORE_RESULT.format(value=score))

def format_commentary_results(commentary_results):
    return [
        f"Source: {r[0].metadata[FATHER_NAME]}{r[0].metadata[BOOK]}{r[0].metadata[SOURCE_TITLE]}\nContent: {r[0].page_content}"
        for r in commentary_results
    ]


def format_bible_results(bible_search_results):
    formatted_results = [
        f"Source: {r[0].metadata[BOOK]}\nContent: {r[0].page_content}"
        for r in bible_search_results
    ]
    return formatted_results

display_bible_results(bible_search_results)


if st.session_state.enable_commentary:
   st.divider()
   commentary_results = perform_commentary_search_parallel(commentary_db, search_query)
   display_commentary_results(commentary_results)

streamlit_analytics.stop_tracking(
    save_to_json=ANALYTICS_JSON_PATH, unsafe_password=UNSAFE_PASSWORD
)
