import streamlit as st
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceInstructEmbeddings
import streamlit_analytics
import random
from constants import *
import xml.etree.ElementTree as ET
import os 
import re

streamlit_analytics.start_tracking(load_from_json=ANALYTICS_JSON_PATH)

st.set_page_config(
    layout="wide",
    menu_items={
        "Get Help": HELP_URL,
        "Report a bug": BUG_REPORT_URL,
        "About": ABOUT_URL,
    },
)


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

@st.cache_resource
def load_bible_xml(input_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    return root

@st.cache_resource
def load_lexicon_xml(input_file):
    lexicon = {}
    # Parse the XML file
    tree = ET.parse(input_file)
    root = tree.getroot()

    ns = {'tei': 'http://www.crosswire.org/2008/TEIOSIS/namespace'}

    # Iterate over each 'entry' element
    for entry in root.findall('tei:entry', ns):
        # Extract the 'n' attribute from the 'entry' element
        entry_id = entry.get('n')

        # Find the 'orth' element
        orth_element = entry.find('tei:orth', ns)
        orth_text = orth_element.text if orth_element is not None else None

        # Find all 'def' elements and extract their text and role
        defs = {}
        for def_element in entry.findall('tei:def', ns):
            role = def_element.get('role')
            defs[role] = def_element.text

        # Store the extracted data in the lexicon dictionary
        lexicon[entry_id] = {
            'orth': orth_text,
            'definitions': defs
        }

    return lexicon


def perform_commentary_search(commentary_db, search_query):
    search_results = []

    for author in CHURCH_FATHERS:
        try:
            results = commentary_db.similarity_search_with_relevance_scores(
                search_query,
                k=1,
                score_function=SCORE_FUNCTION,
                filter={FATHER_NAME: author},
            )
            if results:
                search_results.extend(results)
        except Exception as exc:
            print(f"Author search generated an exception for {author}: {exc}")

    return search_results


def initialize_session_state(default_queries):
    if "initialized" not in st.session_state:
        st.session_state.search_query = random.choice(list(default_queries))
        st.session_state.initialized = True


def update_author_selection(select_all=True):
    for author in CHURCH_FATHERS:
        st.session_state[author] = select_all


def create_author_filters(church_fathers, columns):
    author_filters = {}
    for i, author in enumerate(church_fathers):
        col = columns[(i % 2) + 1]
        if author not in st.session_state:
            st.session_state[author] = True
        author_filters[author] = col.checkbox(author, value=st.session_state[author])
    return author_filters


def select_options():
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        ot = st.checkbox("Old Testament", value=True)
    with col2:
        nt = st.checkbox("New Testament", value=True)
    with col3:
        fc = st.checkbox("Full Chapter", value=True)
    with col4:
        st.session_state.enable_commentary = st.checkbox("Church Fathers", value=False)
    with col5:
        gk = st.checkbox("Greek NT", value=False)
    with col6:
        count = st.slider(
            "Number of Bible Results", min_value=1, max_value=15, value=4, step=1
        )
    return ot, nt, fc, count, gk


def get_selected_bible_filters(ot, nt):
    if ot != nt:
        return {"testament": "OT"} if ot else {"testament": "NT"}
    return {}



def highlight_text(full_text, search_text):
    highlighted_text = full_text.replace(search_text, f"<span style='background-color:gold; color:black;'>{search_text}</span>")
    return highlighted_text


def search_greek_texts(greek_texts, book_code, chapter=None):
    paragraph = ""
    target_text = greek_texts.get(book_code, [])
    for line in target_text:
        if chapter:
            if line.startswith(f"{book_code} {chapter}:"):
                text_part = line.split('\t', 1)[1] if '\t' in line else ""
                paragraph += text_part + " "
    return paragraph.strip()


def extract_greek_word_from_result(result):
    greek_word_regex = r'[\u0370-\u03FF\u1F00-\u1FFF]+' 
    matches = re.findall(greek_word_regex, result)
    if matches:
        return matches 
    return ""

def display_bible_results(results, bible_xml, greek_texts, nt_book_mapping):
    for i, r in enumerate(results):
        content = r[0].page_content
        book = r[0].metadata[BOOK]
        chapter = r[0].metadata[CHAPTER]
        score = r[1]

        if fc:
            with st.expander(f"**{book} {chapter}**", expanded=True):
                query = f".//v[@b='{book}'][@c='{chapter}']"
                full_chapter_content = ""
                for verse in bible_xml.findall(query):
                    text = verse.text
                    full_chapter_content += f"{text}\n"

                highlighted_content = highlight_text(full_chapter_content, content)
                st.markdown(highlighted_content, unsafe_allow_html=True)
                st.write(f"Score: {score}")
        else:
            with st.expander(f"**{book} {chapter}**", expanded=True):
                st.write(f"{content}")
                st.write(SCORE_RESULT.format(value=score))
                
        if gk:
            with st.expander(f"**{book} {chapter}** - SBL Greek New Testament", expanded=True):
                greek_book_code = nt_book_mapping.get(book, "")
                if greek_book_code:
                    greek_paragraph = search_greek_texts(greek_texts, greek_book_code, chapter)
                    if greek_paragraph:
                        st.write(greek_paragraph)
            with st.expander(f"**Dodson Greek Lexicon**", expanded=True):
                greek_words = extract_greek_word_from_result(greek_paragraph)
                lexicon_results = set()
                for greek_word in greek_words:
                    definition = search_lexicon(greek_word)
                    if definition:
                        lexicon_results.add(f"**{greek_word}**: {definition}")
                for definition in lexicon_results:
                    st.write(definition)

@st.cache_resource
def get_nt_book_mapping():
    nt_book_mapping = {
        "1CO": "1Cor",
        "1PE": "1Pet",
        "1TI": "1Tim",
        "2JN": "2John",
        "2TH": "2Thess",
        "3JN": "3John",
        "COL": "Col",
        "GAL": "Gal",
        "JAS": "Jas",
        "JUD": "Jude",
        "MRK": "Mark",
        "PHP": "Phil",
        "REV": "Rev",
        "TIT": "Titus",
        "1JN": "1John",
        "1TH": "1Thess",
        "2CO": "2Cor",
        "2PE": "2Pet",
        "2TI": "2Tim",
        "ACT": "Acts",
        "EPH": "Eph",
        "HEB": "Heb",
        "JHN": "John",
        "LUK": "Luke",
        "MAT": "Matt",
        "PHM": "Phlm",
        "ROM": "Rom"
    }
    return nt_book_mapping

def load_greek_texts(directory):
    greek_texts = {}
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            book_code = filename.split('.')[0]
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                greek_texts[book_code] = file.readlines()
    return greek_texts


greek_texts = load_greek_texts('./data/sblgnt')
dodson_lexicon = load_lexicon_xml(LEXICON_XML_FILE)

def search_lexicon(greek_word):
    for entry_id, entry_data in dodson_lexicon.items():
        if entry_data['orth'].startswith(greek_word):
            return entry_data['definitions'].get('full', None)
    return None


def display_commentary_results(results):
    # cols = st.columns(3)
    results = sorted(results, key=lambda x: x[1], reverse=True)
    results = [r for r in results if r[1] >= 0.81 and len(r[0].page_content) >= 450]
    for i, r in enumerate(results):
        # with cols[i % 3]:
        content, metadata = r[0].page_content, r[0].metadata
        father_name = metadata[FATHER_NAME]
        source_title = metadata[SOURCE_TITLE]
        book = metadata[BOOK]
        append_to_author_name = metadata[APPEND_TO_AUTHOR_NAME]
        score = r[1]

        with st.expander(f"**{father_name.title()}**", expanded=True):
            st.write(f"{content}")
            if append_to_author_name:
                st.write(f"{append_to_author_name.title()}")
            st.write(f"**{source_title.title()}**")
            st.write(SCORE_RESULT.format(value=score))


def format_commentary_results(commentary_results):
    return [
        f"Source: {r[0].metadata[FATHER_NAME]}{r[0].metadata[BOOK]}{r[0].metadata[SOURCE_TITLE]}\nContent: {r[0].page_content}"
        for r in commentary_results
    ]


def format_bible_results(bible_search_results):
    formatted_results = [
        f"Source: {r[0].metadata[BOOK]}\nContent: {r[0].page_content}"
        for r in bible_search_results
    ]
    return formatted_results


st.title(TITLE)

with st.expander("Search Options"):
    ot_checkbox, nt_checkbox, fc, count, gk = select_options()

bible_db = setup_db(DB_DIR, DB_QUERY)
commentary_db = setup_db(COMMENTARY_DB_DIR, COMMENTARY_DB_QUERY)
bible_xml = load_bible_xml(BIBLE_XML_FILE)

initialize_session_state(DEFAULT_QUERIES)

search_query = st.text_input(SEARCH_LABEL, st.session_state.search_query)

bible_search_results = bible_db.similarity_search_with_relevance_scores(
    search_query,
    k=count,
    score_function=SCORE_FUNCTION,
    filter=get_selected_bible_filters(ot_checkbox, nt_checkbox),
)


display_bible_results(bible_search_results, bible_xml, greek_texts, get_nt_book_mapping())


if st.session_state.enable_commentary:
    st.divider()
    commentary_results = perform_commentary_search(commentary_db, search_query)
    display_commentary_results(commentary_results)

streamlit_analytics.stop_tracking(
    save_to_json=ANALYTICS_JSON_PATH, unsafe_password=UNSAFE_PASSWORD
)
