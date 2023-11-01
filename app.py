from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.chat_models import ChatAnthropic
import streamlit as st
import streamlit_analytics
from htbuilder import (
    HtmlElement,
    div,
    hr,
    a,
    p,
    img,
    styles,
)
from htbuilder.units import percent, px

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
    model_name = "BAAI/bge-large-en-v1.5"
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": True}
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )
    db = Chroma(
        persist_directory="./data/db",
        embedding_function=embeddings,
    )
    llm = ChatAnthropic(max_tokens=100000)
    return db, llm


db, llm = setup()

st.title("Biblos: Exploration Tool")

prompt = "Can you provide key points about what these specific passages from the following texts say about the given topic, including related chapter and verse reference? Please restrict your summary to the content found exclusively in these verses and do not reference other biblical verses or context. Explain how they relate to eachother, theologically, in the context of the meta narrative of the gospel, across old and new testaments. The topic is: "

default_query = "What did Jesus say about eternal life?"

search_query = st.text_input(
    "Semantic search (use keywords only for broader results, e.g. 'Kingdom of Heaven')",
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


def image(src_as_string, **style):
    return img(src=src_as_string, style=styles(**style))


def link(link, text, **style):
    return a(_href=link, _target="_blank", style=styles(**style))(text)


def layout(*args):
    style = """
    <style>
    # MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { bottom: 40px; }
    img[src*='img.buymeacoffee.com'] {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    max-width: 200px;
    width: 20%;
    height: auto;
    margin-right: 10px;
    margin-bottom: 5px;
    }

    /* Apply different styles for screens smaller than 600px */
    @media screen and (max-width: 600px) {
    img[src*='img.buymeacoffee.com'] {
        width: 40%;
        max-width: 200px;
    }
    }
    </style>
    """

    style_div = styles(
        position="fixed",
        left=0,
        bottom=0,
        width=percent(100),
        color="black",
        text_align="right",
        height="auto",
        opacity=1,
    )

    style_hr = styles(
        display="block",
        margin=0,
        border_width=px(0),
    )

    body = p()
    foot = div(style=style_div)(hr(style=style_hr), body)

    st.markdown(style, unsafe_allow_html=True)

    for arg in args:
        if isinstance(arg, str):
            body(arg)

        elif isinstance(arg, HtmlElement):
            body(arg)

    st.markdown(str(foot), unsafe_allow_html=True)


def footer():
    myargs = [
        link(
            "https://www.buymeacoffee.com/biblos",
            image(
                "https://img.buymeacoffee.com/button-api/?text=Community Supported &emoji=☕&slug=biblos&button_colour=ffffff&font_colour=000000&font_family=Poppins&outline_colour=000000&coffee_colour=ffffff"
            ),
        ),
    ]
    layout(*myargs)


if __name__ == "__main__":
    footer()
