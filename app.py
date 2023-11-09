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
        llm = ChatAnthropic(max_tokens=100000)
    except:
        # No API token, found, so don't enable LLM support.
        print(f'No API token found, so LLM support is disabled.')
        llm = None

    # Build a list of unique book names. This will be used for NT / OT filtering.
    books = {}
    testament = "OT"
    results = db.get(include=["metadatas"])
    metadatas = results['metadatas']
    for r in metadatas:
        # Print the datatype of the result
        book = r["book"]

        if book.lower().startswith("mat"):
            testament = "NT"
        if testament not in books:
            books[testament] = []
        if book not in books[testament]:
            books[testament].append(book)

    # Create an array that looks like: [{"book": "GEN"}, {"book": "EXO"}, {"book": "LEV"} ... ]
    # This will be passed to the OR filter in the search.
    #  More info: https://github.com/chroma-core/chroma/blob/main/examples/basic_functionality/where_filtering.ipynb
    ot_books = []
    nt_books = []
    for book in books["OT"]:
        ot_books.append({"book": book})
    for book in books["NT"]:
        nt_books.append({"book": book})

    testaments = {"OT": ot_books, "NT": nt_books}

    return db, llm, testaments

db, llm, testaments = setup()

st.title("Biblos: Exploration Tool")

prompt = "Can you provide key points about what these specific passages from the following texts say about the given topic, including related chapter and verse reference? Please restrict your summary to the content found exclusively in these verses and do not reference other biblical verses or context. Explain how they relate to each other, theologically, in the context of the meta narrative of the gospel, across Old and New Testaments. The topic is: "

default_query = "What did Jesus say about eternal life?"

search_query = st.text_input(
    "Semantic search:",
    default_query,
)

with st.expander("Search Options"):
    with st.header("Testament"):
        col1, col2 = st.columns([1, 1])
        with col1:
            # HACK: If we put a space between the words instead of a tab, then the app crashes.
            ot = st.checkbox("Old\tTestament", value=True)
        with col2:
            nt = st.checkbox("New\tTestament", value=True)
    with st.header("Number of Results"):
        num_verses_to_retrieve = st.slider(
            "Number of results:", min_value=1, max_value=10, value=4, step=1
        )

# Build a search filter for the testaments
if ot != nt:
    if ot:
        # NOTE: If / when the database has `testament` added as a metadata field, then this can be simplified to:
        #  testament_filter = {"testament": "OT"}
        #  Also, the `testaments` dictionary could then be removed, along with all of its associated code in `setup()`
        testament_filter = {"$or": testaments["OT"]}
    else:
        testament_filter = {"$or": testaments["NT"]}
else:
    testament_filter = None

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
                llm_query = f"{prompt} {search_query}:\n{all_results}"
                llm_response = llm.predict(llm_query)
                st.success(llm_response)

streamlit_analytics.stop_tracking(
    save_to_json="./data/analytics.json", unsafe_password="x"
)
