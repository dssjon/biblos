import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_community.chat_models import ChatAnthropic
import streamlit_analytics
import random
from constants import *
import xml.etree.ElementTree as ET
import os 
import re
import requests

streamlit_analytics.start_tracking(load_from_json=ANALYTICS_JSON_PATH)

st.set_page_config(
    layout="wide",
    menu_items={
        "Get Help": HELP_URL,
        "Report a bug": BUG_REPORT_URL,
        "About": ABOUT_URL,
    },
)
def select_options():
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        ot = st.checkbox("Old Testament", value=True)
    with col2:
        nt = st.checkbox("New Testament", value=True)
    with col3:
        fc = st.checkbox("Full Chapter", value=False)
    with col4:
        st.session_state.enable_commentary = st.checkbox("Church Fathers", value=False)
    with col5:
        gk = st.checkbox("Greek NT", value=False)
    with col6:
        count = st.slider(
            "Number of Bible Results", min_value=1, max_value=8, value=2, step=1
        )
    return ot, nt, fc, count, gk

st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0rem; padding-bottom: 0rem; flex-wrap: wrap;">
        <h1 style="font-size: 2rem; font-weight: 800; color: #3b3b3b; margin-bottom: 0rem;">
            Explore the Bible
        </h1>
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0rem; padding-bottom: 0rem;">
            <p style="font-size: 1.125rem; color: #6b7280; font-style: italic; text-align: right; margin-bottom: 0rem; padding-bottom: 0rem;">
                Semantic Search & Summary Insights
            </p>
            <a href="https://www.github.com/dssjon" target="_blank" rel="noopener noreferrer" style="color: #6b7280; text-decoration: none;">
                <svg height="24" aria-hidden="true" viewBox="0 0 16 16" version="1.1" width="24" data-view-component="true" class="octicon octicon-mark-github v-align-middle">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            </a>
        </div>
    </div>
""", unsafe_allow_html=True)


with st.expander("Search Options"):
    ot_checkbox, nt_checkbox, fc, count, gk = select_options()

API_KEY = os.getenv("ANTHROPIC_API_KEY")

@st.cache_resource
def setup_llm():
    if not API_KEY:
        print("No API token found, so LLM support is disabled.")
        return None
    
    return {
        "api_url": API_URL,
        "headers": {
            "x-api-key": API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        },
        "model": LLM_MODEL_NAME,
    }

def invoke_llm(llm, prompt):
    data = {
        "model": llm["model"],
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post(llm["api_url"], headers=llm["headers"], json=data)
    if response.status_code == 200:
        return response.json()["content"][0]["text"]
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

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
    tree = ET.parse(input_file)
    root = tree.getroot()

    ns = {'tei': 'http://www.crosswire.org/2008/TEIOSIS/namespace'}

    for entry in root.findall('tei:entry', ns):
        entry_id = entry.get('n')
        orth_element = entry.find('tei:orth', ns)
        orth_text = orth_element.text if orth_element is not None else None

        defs = {}
        for def_element in entry.findall('tei:def', ns):
            role = def_element.get('role')
            defs[role] = def_element.text

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
                filter={FATHER_NAME: author},
            )
            if results and results[0][1] >= 0.80:
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

BIBLE_BOOK_NAMES = {
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus", "NUM": "Numbers", "DEU": "Deuteronomy",
    "JOS": "Joshua", "JDG": "Judges", "RUT": "Ruth", "1SA": "1 Samuel", "2SA": "2 Samuel",
    "1KI": "1 Kings", "2KI": "2 Kings", "1CH": "1 Chronicles", "2CH": "2 Chronicles", "EZR": "Ezra",
    "NEH": "Nehemiah", "EST": "Esther", "JOB": "Job", "PSA": "Psalms", "PRO": "Proverbs",
    "ECC": "Ecclesiastes", "SNG": "Song of Solomon", "ISA": "Isaiah", "JER": "Jeremiah", "LAM": "Lamentations",
    "EZK": "Ezekiel", "DAN": "Daniel", "HOS": "Hosea", "JOL": "Joel", "AMO": "Amos",
    "OBA": "Obadiah", "JON": "Jonah", "MIC": "Micah", "NAM": "Nahum", "HAB": "Habakkuk",
    "ZEP": "Zephaniah", "HAG": "Haggai", "ZEC": "Zechariah", "MAL": "Malachi",
    "MAT": "Matthew", "MRK": "Mark", "LUK": "Luke", "JHN": "John", "ACT": "Acts",
    "ROM": "Romans", "1CO": "1 Corinthians", "2CO": "2 Corinthians", "GAL": "Galatians", "EPH": "Ephesians",
    "PHP": "Philippians", "COL": "Colossians", "1TH": "1 Thessalonians", "2TH": "2 Thessalonians", "1TI": "1 Timothy",
    "2TI": "2 Timothy", "TIT": "Titus", "PHM": "Philemon", "HEB": "Hebrews", "JAS": "James",
    "1PE": "1 Peter", "2PE": "2 Peter", "1JN": "1 John", "2JN": "2 John", "3JN": "3 John",
    "JUD": "Jude", "REV": "Revelation"
}

def display_bible_results(results, bible_xml, greek_texts, nt_book_mapping):
    for i, r in enumerate(results):
        content = r[0].page_content
        book_abbr = r[0].metadata[BOOK]
        book = BIBLE_BOOK_NAMES.get(book_abbr, book_abbr)
        chapter = r[0].metadata[CHAPTER]
        score = r[1]

        if fc:
            with st.expander(f"**{book} {chapter}**", expanded=True):
                query = f".//v[@b='{book_abbr}'][@c='{chapter}']"
                full_chapter_content = ""
                for verse in bible_xml.findall(query):
                    text = verse.text
                    full_chapter_content += f"{text}\n"

                highlighted_content = highlight_text(full_chapter_content, content)
                st.markdown(highlighted_content, unsafe_allow_html=True)
                st.write(SCORE_RESULT.format(value=round(score, 4)))
        else:
            with st.expander(f"**{book} {chapter}**", expanded=True):
                st.write(f"{content}")
                st.write(SCORE_RESULT.format(value=round(score, 4)))
                
        if gk:
            greek_paragraph = ""
            with st.expander(f"**{book} {chapter}** - SBL Greek New Testament", expanded=True):
                greek_book_code = nt_book_mapping.get(book_abbr, "")
                if greek_book_code:
                    greek_paragraph = search_greek_texts(greek_texts, greek_book_code, chapter)
                    if greek_paragraph:
                        st.write(greek_paragraph)
                    else:
                        st.write("No Greek text available for this passage.")
                else:
                    st.write("This book is not part of the Greek New Testament.")
            
            if greek_paragraph:
                with st.expander(f"**Dodson Greek Lexicon**", expanded=True):
                    greek_words = extract_greek_word_from_result(greek_paragraph)
                    lexicon_results = set()
                    for greek_word in greek_words:
                        definition = search_lexicon(greek_word)
                        if definition:
                            lexicon_results.add(f"**{greek_word}**: {definition}")
                    if lexicon_results:
                        for definition in lexicon_results:
                            st.write(definition)
                    else:
                        st.write("No definitions found for the Greek words in this passage.")

@st.cache_resource
def get_nt_book_mapping():
    nt_book_mapping = {
        "1CO": "1Cor", "1PE": "1Pet", "1TI": "1Tim", "2JN": "2John", "2TH": "2Thess",
        "3JN": "3John", "COL": "Col", "GAL": "Gal", "JAS": "Jas", "JUD": "Jude",
        "MRK": "Mark", "PHP": "Phil", "REV": "Rev", "TIT": "Titus", "1JN": "1John",
        "1TH": "1Thess", "2CO": "2Cor", "2PE": "2Pet", "2TI": "2Tim", "ACT": "Acts",
        "EPH": "Eph", "HEB": "Heb", "JHN": "John", "LUK": "Luke", "MAT": "Matt",
        "PHM": "Phlm", "ROM": "Rom"
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
    results = sorted(results, key=lambda x: x[1], reverse=True)
    results = [r for r in results if r[1] >= 0.81 and len(r[0].page_content) >= 450]
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

def format_bible_results(bible_search_results):
    formatted_results = [
        f"Source: {BIBLE_BOOK_NAMES.get(r[0].metadata[BOOK], r[0].metadata[BOOK])}\nContent: {r[0].page_content}"
        for r in bible_search_results
    ]
    return formatted_results



llm = setup_llm()
bible_db = setup_db(DB_DIR, DB_QUERY)
commentary_db = setup_db(COMMENTARY_DB_DIR, COMMENTARY_DB_QUERY)
bible_xml = load_bible_xml(BIBLE_XML_FILE)

initialize_session_state(DEFAULT_QUERIES)

search_query = st.text_input(SEARCH_LABEL, st.session_state.search_query)

bible_search_results = bible_db.similarity_search_with_relevance_scores(
    search_query,
    k=count,
    filter=get_selected_bible_filters(ot_checkbox, nt_checkbox),
)

display_bible_results(bible_search_results, bible_xml, greek_texts, get_nt_book_mapping())

if st.button("Summarize"):
    if llm is None:
        st.error("No API token found, so LLM support is disabled.")
        st.stop()
    else:
        with st.spinner("Summarizing passages..."):
            results = format_bible_results(bible_search_results)
            if not results:
                st.error("No results found")
                st.stop()

            all_results = "\n".join(results)
            llm_query = BIBLE_SUMMARY_PROMPT.format(topic=search_query, passages=all_results)
            llm_response = invoke_llm(llm, llm_query)
            if llm_response:
                st.success(llm_response)
            else:
                st.error("Failed to get a response from the LLM.")

if st.session_state.enable_commentary:
    st.divider()
    commentary_results = perform_commentary_search(commentary_db, search_query)
    display_commentary_results(commentary_results)
    
    if st.button("Summarize Church Fathers"):
        if llm is None:
            st.error("No API token found, so LLM support is disabled.")
            st.stop()
        else:
            with st.spinner("Summarizing Church Fathers'..."):
                formatted_results = format_commentary_results(commentary_results)
                if not formatted_results:
                    st.error("No Church Fathers' commentaries found")
                    st.stop()

                all_results = "\n".join(formatted_results)
                llm_query = COMMENTARY_SUMMARY_PROMPT.format(topic=search_query, content=all_results)
                llm_response = invoke_llm(llm, llm_query)
                if llm_response:
                    st.success(llm_response)
                else:
                    st.error("Failed to get a response from the LLM.")

streamlit_analytics.stop_tracking(
    save_to_json=ANALYTICS_JSON_PATH, unsafe_password=UNSAFE_PASSWORD
)
