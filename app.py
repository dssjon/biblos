import streamlit as st
import streamlit_analytics
from config import *

st.set_page_config(
    layout="wide",
    menu_items={
        "Get Help": HELP_URL,
        "Report a bug": BUG_REPORT_URL,
        "About": ABOUT_URL,
    },
    initial_sidebar_state="expanded",
)

streamlit_analytics.start_tracking(load_from_json=ANALYTICS_JSON_PATH)

from modules.search import perform_search
from modules.reader import reader_mode_navigation
from modules.greek import display_greek_results
from modules.commentary import display_commentary_results
from modules.summaries import display_summaries, setup_llm

def main():
    st.markdown(HEADER_LABEL, unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Search Options")
        ot_checkbox = st.checkbox("Old Testament", value=True)
        nt_checkbox = st.checkbox("New Testament", value=True)
        st.session_state.enable_commentary = st.checkbox("Church Fathers", value=False)
        gk = st.checkbox("Greek NT", value=False)
        summarize = st.checkbox("Summarize", value=False)
        count = st.slider("Number of Bible Results", min_value=1, max_value=8, value=4, step=1)

    # Display Reader Mode
    reader_mode_navigation()

    # Display Search Input and Results
    search_query = st.text_input(SEARCH_LABEL, value=st.session_state.get('search_query', ''))
    st.session_state.search_query = search_query

    if search_query:
        with st.spinner("Searching..."):
            bible_results, commentary_results = perform_search(search_query, ot_checkbox, nt_checkbox, count)

        display_results(bible_results, commentary_results, gk)

        if summarize:
            llm = setup_llm()
            display_summaries(search_query, bible_results, commentary_results)

def display_results(bible_results, commentary_results, show_greek):
    num_columns = 1 + int(st.session_state.enable_commentary) + int(show_greek)
    columns = st.columns(num_columns)

    with columns[0]:
        st.subheader("Search Results")
        for result in bible_results:
            display_bible_result(result)

    column_index = 1
    if show_greek:
        with columns[column_index]:
            st.subheader("Greek New Testament")
            display_greek_results(bible_results)
        column_index += 1

    if st.session_state.enable_commentary:
        with columns[column_index]:
            st.subheader("Church Fathers' Commentary")
            display_commentary_results(commentary_results)

def display_bible_result(result):
    content, metadata, score = result[0].page_content, result[0].metadata, result[1]
    book = BIBLE_BOOK_NAMES.get(metadata['book'], metadata['book'])
    chapter = metadata['chapter']

    with st.expander(f"**{book}** - Chapter {chapter}", expanded=True):
        st.markdown(content)
        st.write(SCORE_RESULT.format(value=round(score, 4)))

if __name__ == "__main__":
    main()

streamlit_analytics.stop_tracking(
    save_to_json=ANALYTICS_JSON_PATH, unsafe_password=UNSAFE_PASSWORD
)
