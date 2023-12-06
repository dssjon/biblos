import streamlit as st
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.chat_models import ChatAnthropic
import streamlit_analytics
import random

# Start tracking
streamlit_analytics.start_tracking(load_from_json="./data/analytics.json")

# Set page config
st.set_page_config(
    layout="wide",
    menu_items={
        "Get Help": "https://www.github.com/dssjon",
        "Report a bug": "https://www.github.com/dssjon",
        "About": "Made with <3 by https://www.github.com/dssjon",
    },
)

# Setup Bible database
@st.cache_resource
def setup_bible_db():
    embeddings = HuggingFaceInstructEmbeddings(
        model_name="hkunlp/instructor-large",
        query_instruction="Represent the Religious Bible verse text for semantic search:",
    )
    bible_db = Chroma(
        persist_directory="./data/db",
        embedding_function=embeddings,
    )
    return bible_db

# Setup Commentary database
@st.cache_resource
def setup_commentary_db():
    embeddings = HuggingFaceInstructEmbeddings(
        model_name="hkunlp/instructor-large",
        query_instruction="Represent the Religious bible commentary text for semantic search:",
    )
    commentary_db = Chroma(
        persist_directory="./data/commentary_db",
        embedding_function=embeddings,
    )
    return commentary_db

bible_db, commentary_db = setup_bible_db(), setup_commentary_db()

# Setup LLM
try:
    llm = ChatAnthropic(max_tokens=100000, model_name="claude-2.1")
except:
    st.error('No API token found, so LLM support is disabled.')
    llm = None

st.title("Biblos: Exploration Tool")
st.text("Semantic search the Bible and Church Fathers")

prompt = """Based on the user's search query, the topic is: {topic}
Please provide a concise summary of the key points made in the following Bible passages about the topic above, including chapter and verse references. Focus only on the content found in these specific verses. Explain connections between the passages and how they theologically relate to the overarching biblical meta narrative across both Old and New Testaments.
{passages}"""

commentary_summary_prompt = """Based on the user's search query, the topic is: {topic}
Please provide a concise summary of the key insights and interpretations offered in the following Church Fathers' commentaries on the topic above. Focus only on the content in these specific commentaries, highlighting how they contribute to understanding the scriptural texts. Include the church father and source text.
{commentaries}"""

test_queries = {
    "What did Jesus say about eternal life?": ["JHN 3", "JHN 17", "MAT 19"],
    "What is the fruit of the spirit?": ["GAL 5:22-23", "EPH 5:9", "COL 3:12-17"],
    "Guidance and protection in difficult times": ["PSA 23", "ISA 41:10", "PHI 4:6-7"],
    "What will happen during the end times?": ["REV 21", "REV 22", "MAT 24"],
    "What is love?": ["1CO 13", "JHN 15:12-13", "1JN 4:7-8"],
    "What is the Holy Spirit?": ["ACT 2", "JHN 14:26", "JHN 16:13-14"],
    "Understanding the Trinity (Father, Son, and Holy Spirit)": ["MAT 28:19", "JHN 1:1-14", "2CO 13:14"],
    "The importance of faith": ["HEB 11", "ROM 10:17", "EPH 2:8-9"],
    "Living a Christian life": ["ROM 12", "GAL 2:20", "COL 3:1-17"],
    "Forgiveness and reconciliation": ["MAT 6:14-15", "EPH 4:31-32", "COL 3:13"],
    "The role of prayer": ["MAT 6:5-15", "1TH 5:16-18", "PHI 4:6"],
    "Understanding salvation": ["EPH 2:8-9", "TIT 3:4-7", "ACT 16:30-31"],
    "The Beatitudes": ["MAT 5:3-12", "LUK 6:20-23"],
    "Overcoming temptation": ["1CO 10:13", "JAM 1:12-15", "EPH 6:10-18"],
    "The role of the church": ["ACT 2:42-47", "HEB 10:24-25", "EPH 4:11-16"],
    "Christian hope": ["ROM 5:1-5", "HEB 6:19", "1PE 1:3-5"],
    "Understanding Grace": ["2CO 12:9", "ROM 3:23-24", "TIT 2:11-14"],
    "Jesus' teachings on serving others": ["MAT 20:26-28", "JHN 13:12-17", "GAL 5:13"],
    "Biblical perspective on suffering": ["ROM 5:3-5", "2CO 1:3-4", "1PE 4:12-13"]
}


def get_next_query():
    return random.choice(list(test_queries.keys()))

if 'initialized' not in st.session_state:
    st.session_state.search_query = get_next_query()
    st.session_state.initialized = True

search_query = st.text_input("Keyword(s):", st.session_state.search_query)


church_fathers = [
    "Augustine of Hippo", "Thomas Aquinas", "John Chrysostom", "Athanasius of Alexandria"
]

# Initialize a dictionary to store the checkbox states
author_filters = {}
def update_author_selection(select_all=True):
    for author in church_fathers:
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
            for i, author in enumerate(church_fathers):
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

if len(selected_authors) > 0:
    commentary_search_results = commentary_db.similarity_search_with_relevance_scores(
        search_query,
        k=num_verses_to_retrieve,
        score_function="cosine",
        filter=author_filter_query
    )

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.caption("Bible search results:")
    for r in bible_search_results:
        content = r[0].page_content
        book = r[0].metadata["book"]
        chapter = r[0].metadata["chapter"]
        score = r[1]
        with st.expander(f"**{book}** {chapter}", expanded=True):
            st.write(f"{content}")
            st.write(f"**Similarity Score**: {score}")

with col2:
    st.caption("Commentary search results:")
    for r in commentary_search_results:
        content = r[0].page_content
        father_name = r[0].metadata["father_name"]
        source_title = r[0].metadata["source_title"]
        book = r[0].metadata["book"]
        score = r[1]
        with st.expander(f"**{father_name}**", expanded=True):
            st.write(f"{content}")
            # standardize the casing of the book name and source title
            if book:
                book = book.title()
            if source_title:
                source_title = source_title.title()
            if not source_title and book:
                st.write(f"**Source**: Commentary on {book}")
            if source_title:
                st.write(f"**Source**: {source_title}")
            st.write(f"**Similarity Score**: {score}")

with col3:
    st.caption("Summarize text:")

    if st.button("Scripture"):
        if llm is None:
            st.error("No API token found, so LLM support is disabled.")
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
                llm_query = prompt.format(topic=search_query, passages=all_results)
                llm_response = llm.predict(llm_query)
                st.success(llm_response)
    if st.button("Commentary"):
        if llm is None:
            st.error("No API token found, so LLM support is disabled.")
            st.stop()
        else:
            with st.spinner("Summarizing..."):
                results = []
                for r in commentary_search_results:
                    content = r[0].page_content
                    father_name = r[0].metadata["father_name"]
                    source_title = r[0].metadata["source_title"]
                    book = r[0].metadata["book"]
                    results.append(f"Source: {father_name}{book}{source_title}\nContent: {content}")

                if not results:
                    st.error("No results found")
                    st.stop()


                all_results = "\n".join(results)
    
                llm_query = commentary_summary_prompt.format(topic=search_query, commentaries=all_results)
                llm_response = llm.predict(llm_query)
                st.success(llm_response)

# Stop tracking
streamlit_analytics.stop_tracking(
    save_to_json="./data/analytics.json", unsafe_password="x"
)
