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
from modules.reader import find_matching_verses
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
        summarize = st.checkbox("Summarize", value=True)
        count = st.slider("Number of Bible Results", min_value=1, max_value=8, value=2, step=1)

    search_col, book_col, chapter_col = st.columns([3, 2, 1])

    with search_col:
        search_query = st.text_input(
            SEARCH_LABEL,
            value=st.session_state.get('search_query', DEFAULT_SEARCH_QUERY),
            key="search_input",
            on_change=lambda: st.session_state.update({'search_query': st.session_state['search_input'], 'clear_search': False})
        )

    search_results = None
    commentary_results = None

    if search_query and not st.session_state.get('clear_search', False):
        with st.spinner("Searching..."):
            search_results, commentary_results = perform_search(search_query, ot_checkbox, nt_checkbox, count)

        if search_results:
            update_book_chapter_from_search(search_results[0][0].metadata)

    with book_col:
        select_book()
    
    with chapter_col:
        select_chapter()

    col1, col2 = st.columns([1, 1])

    with col1:
        display_chapter_text(search_results)

    with col2:
        if search_query and not st.session_state.get('clear_search', False):
            if summarize:
                llm = setup_llm()
                display_summaries(search_query, search_results, commentary_results)

            display_results(search_results)

    if st.session_state.show_greek or st.session_state.enable_commentary:
        st.write("---")  # Add a separator

    if st.session_state.show_greek:
        st.subheader("Greek New Testament")
        display_greek_results(search_results)

    if st.session_state.enable_commentary:
        st.subheader("Church Fathers' Commentary")
        display_commentary_results(commentary_results)

    # Reset the clear_search flag only after processing
    st.session_state.clear_search = False

def update_book_chapter_from_search(metadata):
    st.session_state.current_book = metadata['book']
    st.session_state.current_chapter = int(metadata['chapter'])

def select_book():
    if 'current_book' not in st.session_state:
        st.session_state.current_book = list(BIBLE_BOOK_NAMES.keys())[0]

    books = list(BIBLE_BOOK_NAMES.keys())
    book_options = [f"{BIBLE_BOOK_NAMES[book]}" for book in books]
    current_book_index = books.index(st.session_state.current_book)
    selected_book_option = st.selectbox("Book", book_options, index=current_book_index, key="book_select", on_change=clear_search_and_update_book)
    selected_book = [book for book, name in BIBLE_BOOK_NAMES.items() if name == selected_book_option][0]
    
    if selected_book != st.session_state.current_book:
        st.session_state.current_book = selected_book
        st.session_state.current_chapter = 1

def select_chapter():
    bible_xml = load_bible_xml(BIBLE_XML_FILE)
    if 'current_chapter' not in st.session_state:
        st.session_state.current_chapter = 1

    max_chapters = max(int(verse.get('c')) for verse in bible_xml.findall(f".//v[@b='{st.session_state.current_book}']"))
    selected_chapter = st.number_input("Chapter", min_value=1, max_value=max_chapters, value=st.session_state.current_chapter, key="chapter_select", on_change=clear_search_and_update_chapter)
    
    if selected_chapter != st.session_state.current_chapter:
        st.session_state.current_chapter = selected_chapter

def clear_search_and_update_book():
    st.session_state.clear_search = True
    st.session_state.current_chapter = 1

def clear_search_and_update_chapter():
    st.session_state.clear_search = True

def display_chapter_text(search_results):
    if 'current_book' in st.session_state and 'current_chapter' in st.session_state:
        book = st.session_state.current_book
        chapter = st.session_state.current_chapter
        verses = get_full_chapter_text(book, chapter)

        matching_verses = []
        if search_results:
            first_result_content = search_results[0][0].page_content
            matching_verses = find_matching_verses(verses, first_result_content)

        highlighted_text = ""
        for verse_num, verse_text in verses:
            if verse_num in matching_verses:
                highlighted_text += f'<span style="background-color: #FFD700; color: #000000;"><sup>{verse_num}</sup> {verse_text}</span> '
            else:
                highlighted_text += f'<sup>{verse_num}</sup> {verse_text} '

        if search_results:
            score = search_results[0][1]
            highlighted_text = highlighted_text + f"\n\n**Similarity Score:** {round(score, 4)}\n"
        st.subheader(f"{BIBLE_BOOK_NAMES[book]} {chapter}")

        paragraphs = split_content_into_paragraphs(highlighted_text)
        for paragraph in paragraphs:
            st.markdown(paragraph, unsafe_allow_html=True)

def display_results(bible_results):
    # if more than 1 result show subheader
    if len(bible_results) > 1:
        st.subheader("Other results")
    # skip the first result as it is already displayed in the main text
    for result in bible_results[1:]:
        display_search_result(result)

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
