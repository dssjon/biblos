import streamlit as st
import streamlit_analytics
from config import *

st.set_page_config(
    page_title="Bible Semantic Search & Study Tool | Biblos",
    layout="wide",
    menu_items={
        "Get Help": HELP_URL,
        "Report a bug": BUG_REPORT_URL,
        "About": ABOUT_URL,
    },
    initial_sidebar_state="auto"
)

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    .stDeployButton {
        display: none;
    }
    .css-18e3th9 {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .css-1d391kg {
        padding-top: 0rem;
    }
    div.st-emotion-cache-16txtl3.eczjsme4 {
        padding-top: 2rem !important;
    }
    </style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }
    </style>
    """, unsafe_allow_html=True)

streamlit_analytics.start_tracking(load_from_json=ANALYTICS_JSON_PATH)

from modules.search import perform_search
from modules.reader import load_bible_xml, get_full_chapter_text, split_content_into_paragraphs, find_matching_verses
from modules.greek import display_greek_results
from modules.commentary import display_commentary_results
from modules.summaries import generate_summaries, setup_llm

def main():
    st.markdown(HEADER_LABEL, unsafe_allow_html=True)

    if 'search_count' not in st.session_state:
        st.session_state.search_count = 4
    if 'current_book' not in st.session_state:
        st.session_state.current_book = list(BIBLE_BOOK_NAMES.keys())[0]
    if 'current_chapter' not in st.session_state:
        st.session_state.current_chapter = 1

    with st.sidebar:
        st.subheader("Search Options")
        ot_checkbox = st.checkbox("Old Testament", value=True)
        nt_checkbox = st.checkbox("New Testament", value=True)
        st.session_state.enable_commentary = st.checkbox("Church Fathers", value=False)
        st.session_state.show_greek = st.checkbox("Greek NT", value=False)
        summarize = st.checkbox("Insights", value=True)

        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 4px 0px; margin: 0px;">
            <p style="font-size: 0.75rem; color: #6b7280; margin: 0; display: flex; align-items: center;">
                Made with <span style="color: red; margin: 0 3px;">♥</span> by 
                <a href="https://www.github.com/dssjon" target="_blank" rel="noopener noreferrer" style="color: #6b7280; text-decoration: none; display: flex; align-items: center; margin-left: 4px;">
                    github.com/dssjon
                    <svg height="16" aria-hidden="true" viewBox="0 0 16 16" version="1.1" width="16" data-view-component="true" class="octicon octicon-mark-github v-align-middle" style="margin-left: 4px;">
                        <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                    </svg>
                </a>
            </p>
        </div>
        """, unsafe_allow_html=True)

    search_col, clear_col = st.columns([4, 1])

    with search_col:
        search_query = st.text_input(
            "Search",
            value=st.session_state.get('search_query', ''),
            key="search_input",
            placeholder="What did Jesus say about...?",
            on_change=lambda: st.session_state.update({'search_query': st.session_state['search_input'], 'clear_search': False, 'search_count': 4})
        )

    with clear_col:
        st.markdown('<div style="display: flex; align-items: center; height: 100%;">', unsafe_allow_html=True)
        if st.button("Clear Search"):
            st.session_state.search_query = ''
            st.session_state.clear_search = True
            st.session_state.search_count = 4
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    search_results = None
    commentary_results = None

    if search_query and not st.session_state.get('clear_search', False):
        with st.spinner("Searching..."):
            search_results, commentary_results = perform_search(search_query, ot_checkbox, nt_checkbox, st.session_state.search_count)

        if search_results:
            update_book_chapter_from_search(search_results[0][0].metadata)

    # Determine which tabs to display with alternative names
    tabs_to_display = [f"📖 **{BIBLE_BOOK_NAMES[st.session_state.current_book]} {st.session_state.current_chapter}** "]
    if search_results and len(search_results) > 1:
        tabs_to_display.append("🔍 More Results")
    if st.session_state.show_greek and search_results:
        tabs_to_display.append("☧ Greek NT")
    if st.session_state.enable_commentary and commentary_results:
        tabs_to_display.append("📜 Church Fathers")
    if summarize and search_results:
        tabs_to_display.append("📊 Insights")

    tabs = st.tabs(tabs_to_display)

    for i, tab_name in enumerate(tabs_to_display):
        with tabs[i]:
            #if tab_name == "📖 Bible Text":
            #instead of name check first tab
            if i == 0:
                display_chapter_text(search_results)
                book_col, chapter_col = st.columns([2, 1])
                with book_col:
                    select_book()
                with chapter_col:
                    select_chapter()

            elif tab_name == "🔍 More Results":
                display_results(search_results[1:])
                if len(search_results) == st.session_state.search_count and st.session_state.search_count < 8:
                    if st.button("Show more"):
                        st.session_state.search_count = min(8, st.session_state.search_count + 2)
                        st.rerun()

            elif tab_name == "☧ Greek NT":
                display_greek_results(search_results)

            elif tab_name == "📜 Church Fathers":
                display_commentary_results(commentary_results)

            elif tab_name == "📊 Insights":
                with st.spinner("Generating insights..."):
                    llm = setup_llm()
                    summaries = generate_summaries(search_query, search_results, commentary_results)
                    if 'bible' in summaries:
                        st.subheader("Insights")
                        st.success(summaries['bible'])
                    if 'commentary' in summaries:
                        st.subheader("Church Fathers' Insights")
                        st.success(summaries['commentary'])

    # show a footer line break to add white space
    st.write("---")
    
    # Reset the clear_search flag only after processing
    st.session_state.clear_search = False

def update_book_chapter_from_search(metadata):
    st.session_state.current_book = metadata['book']
    st.session_state.current_chapter = int(metadata['chapter'])

def select_book():
    books = list(BIBLE_BOOK_NAMES.keys())
    book_options = [f"{BIBLE_BOOK_NAMES[book]}" for book in books]
    current_book_index = books.index(st.session_state.current_book)
    selected_book_option = st.selectbox("Book", book_options, index=current_book_index, key="book_select", on_change=handle_book_change)
    
def handle_book_change():
    selected_book = [book for book, name in BIBLE_BOOK_NAMES.items() if name == st.session_state.book_select][0]
    if selected_book != st.session_state.current_book:
        st.session_state.current_book = selected_book
        st.session_state.current_chapter = 1
        st.session_state.clear_search = True

def select_chapter():
    bible_xml = load_bible_xml(BIBLE_XML_FILE)
    max_chapters = max(int(verse.get('c')) for verse in bible_xml.findall(f".//v[@b='{st.session_state.current_book}']"))
    selected_chapter = st.number_input("Chapter", min_value=1, max_value=max_chapters, value=st.session_state.current_chapter, key="chapter_select", on_change=handle_chapter_change)

def handle_chapter_change():
    if st.session_state.chapter_select != st.session_state.current_chapter:
        st.session_state.current_chapter = st.session_state.chapter_select
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
        #st.subheader(f"{BIBLE_BOOK_NAMES[book]} {chapter}")

        paragraphs = split_content_into_paragraphs(highlighted_text)
        for paragraph in paragraphs:
            st.markdown(paragraph, unsafe_allow_html=True)

def display_results(bible_results):
    for result in bible_results:
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