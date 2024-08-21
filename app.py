import streamlit as st
import streamlit_analytics
from config import *

# Set page config at the very beginning
st.set_page_config(
    layout="wide",
    menu_items={
        "Get Help": HELP_URL,
        "Report a bug": BUG_REPORT_URL,
        "About": ABOUT_URL,
    },
    initial_sidebar_state="expanded",
)

# Start analytics tracking
streamlit_analytics.start_tracking(load_from_json=ANALYTICS_JSON_PATH)

# Import other modules after st.set_page_config
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
        reader_mode = st.checkbox("Reader Mode", value=False)
        count = st.slider("Number of Bible Results", min_value=1, max_value=8, value=4, step=1)

    if reader_mode:
        reader_mode_navigation()
    else:
        search_query = st.text_input(SEARCH_LABEL, value=st.session_state.get('search_query', ''))
        st.session_state.search_query = search_query

        if search_query:
            with st.spinner("Searching..."):
                bible_results, commentary_results = perform_search(search_query, ot_checkbox, nt_checkbox, count)

            display_results(bible_results, commentary_results, gk)

            if summarize:
                llm = setup_llm()
                display_summaries(llm, search_query, bible_results, commentary_results)

def display_results(bible_results, commentary_results, show_greek):
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader("Bible Results")
        for result in bible_results:
            display_bible_result(result)

    if show_greek:
        with col2:
            st.subheader("Greek New Testament")
            display_greek_results(bible_results)

    if st.session_state.enable_commentary:
        with col3:
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

# Stop analytics tracking
streamlit_analytics.stop_tracking(
    save_to_json=ANALYTICS_JSON_PATH, unsafe_password=UNSAFE_PASSWORD
)