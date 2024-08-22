# commentary.py

import streamlit as st
from config import FATHER_NAME, SOURCE_TITLE, BOOK, APPEND_TO_AUTHOR_NAME, SCORE_RESULT

def display_commentary_results(results):
    if not results:
        st.write("No relevant commentary found for this query.")
        return

    results = sorted(results, key=lambda x: x[1], reverse=True)
    results = [r for r in results if r[1] >= 0.81 and len(r[0].page_content) >= 450]
    
    if not results:
        st.write("No commentary met the relevance threshold for this query.")
        return

    for i, r in enumerate(results):
        content, metadata = r[0].page_content, r[0].metadata
        father_name = metadata[FATHER_NAME]
        source_title = metadata[SOURCE_TITLE]
        book = metadata[BOOK]
        append_to_author_name = metadata[APPEND_TO_AUTHOR_NAME]
        score = r[1]
        
        with st.expander(f"**{father_name.title()}** - {source_title.title()}", expanded=True):
            st.write(f"{content}")
            if append_to_author_name:
                st.write(f"{append_to_author_name.title()}")
            st.write(SCORE_RESULT.format(value=round(score, 4)))

def format_commentary_results(commentary_results):
    return [
        f"Source: {r[0].metadata[FATHER_NAME]} - {r[0].metadata[SOURCE_TITLE]}\nContent: {r[0].page_content}"
        for r in commentary_results
    ]