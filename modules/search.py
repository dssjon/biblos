# search.py

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from config import *
import streamlit as st

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

def get_selected_bible_filters(ot, nt):
    if ot != nt:
        return {"testament": "OT" if ot else "NT"}
    return {}

def perform_commentary_search(commentary_db, search_query):
    search_results = []
    for author in CHURCH_FATHERS:
        try:
            results = commentary_db.similarity_search_with_relevance_scores(
                search_query,
                k=1,
                filter={FATHER_NAME: author},
            )
            if results and results[0][1] >= 0.80:
                search_results.extend(results)
        except Exception as exc:
            print(f"Author search generated an exception for {author}: {exc}")
    return search_results

def perform_search(search_query, ot_checkbox, nt_checkbox, count):
    bible_db = setup_db(DB_DIR, DB_QUERY)
    commentary_db = setup_db(COMMENTARY_DB_DIR, COMMENTARY_DB_QUERY)

    bible_search_results = bible_db.similarity_search_with_relevance_scores(
        search_query,
        k=count,
        filter=get_selected_bible_filters(ot_checkbox, nt_checkbox),
    )

    commentary_results = []
    if st.session_state.enable_commentary:
        commentary_results = perform_commentary_search(commentary_db, search_query)

    return bible_search_results, commentary_results

def format_bible_results(bible_search_results):
    return [
        {
            "content": r[0].page_content,
            "metadata": {
                "book": BIBLE_BOOK_NAMES.get(r[0].metadata[BOOK], r[0].metadata[BOOK]),
                "chapter": r[0].metadata[CHAPTER],
            },
            "score": r[1]
        }
        for r in bible_search_results
    ]

def format_commentary_results(commentary_results):
    return [
        {
            "content": r[0].page_content,
            "metadata": {
                "father_name": r[0].metadata[FATHER_NAME],
                "source_title": r[0].metadata[SOURCE_TITLE],
                "book": r[0].metadata[BOOK],
                "append_to_author_name": r[0].metadata[APPEND_TO_AUTHOR_NAME],
            },
            "score": r[1]
        }
        for r in commentary_results
    ]