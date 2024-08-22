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
from modules.reader import load_bible_xml, get_full_chapter_text, split_content_into_paragraphs
from modules.greek import display_greek_results
from modules.commentary import display_commentary_results
from modules.summaries import display_summaries, setup_llm

DEFAULT_SEARCH_QUERY = "What did Jesus say about eternal life?"

def main():
    st.markdown(HEADER_LABEL, unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Search Options")
        ot_checkbox = st.checkbox("Old Testament", value=True)
        nt_checkbox = st.checkbox("New Testament", value=True)
        st.session_state.enable_commentary = st.checkbox("Church Fathers", value=False)
        st.session_state.show_greek = st.checkbox("Greek NT", value=False)
        summarize = st.checkbox("Summarize", value=False)
        count = st.slider("Number of Bible Results", min_value=1, max_value=8, value=4, step=1)

    # Display Search Input
    search_query = st.text_input(SEARCH_LABEL, value=st.session_state.get('search_query', DEFAULT_SEARCH_QUERY))
    st.session_state.search_query = search_query

    # Perform search if query exists
    if search_query:
        with st.spinner("Searching..."):
            search_results, commentary_results = perform_search(search_query, ot_checkbox, nt_checkbox, count)

        # Update current book and chapter based on the first search result
        if search_results:
            first_result = search_results[0]
            st.session_state.current_book = first_result[0].metadata['book']
            st.session_state.current_chapter = first_result[0].metadata['chapter']

    # Display Reader Mode (Book/Chapter selectors)
    reader_mode_navigation()

    # Create two main columns: one for chapter text, one for results
    col1, col2 = st.columns([1, 1])

    with col1:
        display_chapter_text()

    with col2:
        # Display search results only if a search was performed
        if search_query:
            # Display Summary UI if applicable
            if summarize:
                llm = setup_llm()
                display_summaries(search_query, search_results, commentary_results)

            # Display search results
            display_results(search_results, commentary_results, st.session_state.show_greek)

def reader_mode_navigation():
    bible_xml = load_bible_xml(BIBLE_XML_FILE)

    if 'current_book' not in st.session_state:
        st.session_state.current_book = list(BIBLE_BOOK_NAMES.keys())[0]
    if 'current_chapter' not in st.session_state:
        st.session_state.current_chapter = 1

    col1, col2 = st.columns([3, 1])
    
    with col1:
        books = list(BIBLE_BOOK_NAMES.keys())
        book_options = [f"{BIBLE_BOOK_NAMES[book]} ({book})" for book in books]
        selected_book_option = st.selectbox("Book", book_options, index=books.index(st.session_state.current_book), key="book_select")
        selected_book = books[book_options.index(selected_book_option)]
    
    if selected_book != st.session_state.current_book:
        st.session_state.current_book = selected_book
        st.session_state.current_chapter = 1

    max_chapters = max(int(verse.get('c')) for verse in bible_xml.findall(f".//v[@b='{st.session_state.current_book}']"))
    with col2:
        st.session_state.current_chapter = st.number_input("Chapter", min_value=1, max_value=max_chapters, value=st.session_state.current_chapter, key="chapter_select")

def display_chapter_text():
    if 'current_book' in st.session_state and 'current_chapter' in st.session_state:
        book = st.session_state.current_book
        chapter = st.session_state.current_chapter
        chapter_text = get_full_chapter_text(book, chapter)
        #st.markdown(f"## {BIBLE_BOOK_NAMES[book]} {chapter}")
        paragraphs = split_content_into_paragraphs(chapter_text)
        for paragraph in paragraphs:
            st.markdown(paragraph)

def display_results(bible_results, commentary_results, show_greek):
    # Determine the number of columns based on enabled options
    num_columns = 1  # Bible results always shown
    if show_greek:
        num_columns += 1
    if st.session_state.enable_commentary:
        num_columns += 1
    
    # Create columns with equal width
    columns = st.columns([1] * num_columns)
    
    # Distribute content among columns
    col_index = 0
    
    # Bible results
    with columns[col_index]:
        #st.subheader("Search Results")
        for result in bible_results:
            display_search_result(result)
    col_index += 1
    
    # Greek results
    if show_greek:
        with columns[col_index]:
            st.subheader("Greek New Testament")
            display_greek_results(bible_results)
        col_index += 1
    
    # Commentary results
    if st.session_state.enable_commentary:
        with columns[col_index]:
            st.subheader("Church Fathers' Commentary")
            display_commentary_results(commentary_results)

def display_search_result(result):
    content, metadata, score = result[0].page_content, result[0].metadata, result[1]
    book = BIBLE_BOOK_NAMES.get(metadata['book'], metadata['book'])
    chapter = metadata['chapter']

    with st.expander(f"**{book} {chapter}**", expanded=True):
        st.markdown(content)
        st.write(SCORE_RESULT.format(value=round(score, 4)))

if __name__ == "__main__":
    main()

streamlit_analytics.stop_tracking(
    save_to_json=ANALYTICS_JSON_PATH, unsafe_password=UNSAFE_PASSWORD
)