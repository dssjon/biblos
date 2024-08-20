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
import json

streamlit_analytics.start_tracking(load_from_json=ANALYTICS_JSON_PATH)

st.set_page_config(
    layout="wide",
    menu_items={
        "Get Help": HELP_URL,
        "Report a bug": BUG_REPORT_URL,
        "About": ABOUT_URL,
    },
    initial_sidebar_state="expanded",
)

def select_options():
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        ot = st.checkbox("Old Testament", value=True)
    with col2:
        nt = st.checkbox("New Testament", value=True)
    with col3:
        st.session_state.enable_commentary = st.checkbox("Church Fathers", value=True)
    with col4:
        gk = st.checkbox("Greek NT", value=False)
    with col5:
        summarize = st.checkbox("Summarize", value=False)
    with col6:
        count = st.slider(
            "Number of Bible Results", min_value=1, max_value=8, value=4, step=1
        )
    return ot, nt, count, gk, summarize



st.markdown(HEADER_LABEL, unsafe_allow_html=True)

with st.expander("Search Options"):
    ot_checkbox, nt_checkbox, count, gk, summarize = select_options()

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


def display_bible_results(results, bible_xml):
    for i, r in enumerate(results):
        content = r[0].page_content
        book_abbr = r[0].metadata[BOOK]
        book = BIBLE_BOOK_NAMES.get(book_abbr, book_abbr)
        chapter = r[0].metadata[CHAPTER]
        score = r[1]

        with st.expander(f"**{book}** - Chapter {chapter}", expanded=True):
            full_chapter_key = f"full_chapter_{i}"
            if full_chapter_key not in st.session_state:
                st.session_state[full_chapter_key] = False

            if not st.session_state[full_chapter_key]:
                st.markdown(content)
                st.write(SCORE_RESULT.format(value=round(score, 4)))
                if st.button("View Full Chapter", key=f"view_{i}"):
                    st.session_state[full_chapter_key] = True
                    st.rerun()
            else:
                query = f".//v[@b='{book_abbr}'][@c='{chapter}']"
                full_chapter_content = ""
                for verse in bible_xml.findall(query):
                    text = verse.text
                    full_chapter_content += f"{text}\n"
                
                highlighted_content = highlight_text(full_chapter_content, content)
                st.markdown(highlighted_content, unsafe_allow_html=True)
                st.write(SCORE_RESULT.format(value=round(score, 4)))
                if st.button("Show Search Result", key=f"back_{i}"):
                    st.session_state[full_chapter_key] = False
                    st.rerun()

def display_results(bible_results, commentary_results, bible_xml, greek_texts):
    num_columns = 1
    if st.session_state.enable_commentary:
        num_columns += 1
    if gk:
        num_columns += 1
    
    columns = st.columns(num_columns)
    
    with columns[0]:
        st.subheader("Bible Results")
        display_bible_results(bible_results, bible_xml)
    
    column_index = 1
    
    if gk:
        with columns[column_index]:
            st.subheader("Greek New Testament")
            display_greek_results(bible_results, greek_texts)
        column_index += 1
    
    if st.session_state.enable_commentary:
        with columns[column_index]:
            st.subheader("Church Fathers' Commentary")
            display_commentary_results(commentary_results)

def display_greek_results(results, greek_texts):
    for i, r in enumerate(results):
        book_abbr = r[0].metadata[BOOK]
        book = BIBLE_BOOK_NAMES.get(book_abbr, book_abbr)
        chapter = r[0].metadata[CHAPTER]
        
        greek_book_code = NT_BOOK_MAPPING.get(book_abbr, "")
        if greek_book_code:
            with st.expander(f"**{book} {chapter}** - SBL Greek New Testament", expanded=True):
                greek_paragraph = search_greek_texts(greek_texts, greek_book_code, chapter)
                if greek_paragraph:
                    st.write(greek_paragraph)
                    
                    st.subheader("Dodson Greek Lexicon")
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
                else:
                    st.write("No Greek text available for this passage.")
        else:
            st.write("This book is not part of the Greek New Testament.")

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

@st.cache_resource
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

def generate_summaries(llm, search_query, bible_search_results, commentary_results):
    summaries = {}
    
    # Generate Bible summary
    bible_results = format_bible_results(bible_search_results)
    if bible_results:
        all_results = "\n".join(bible_results)
        llm_query = BIBLE_SUMMARY_PROMPT.format(topic=search_query, passages=all_results)
        bible_summary = invoke_llm(llm, llm_query)
        if bible_summary:
            summaries['bible'] = bible_summary
    
    # Generate Commentary summary if enabled
    if st.session_state.enable_commentary:
        formatted_results = format_commentary_results(commentary_results)
        if formatted_results:
            all_results = "\n".join(formatted_results)
            llm_query = COMMENTARY_SUMMARY_PROMPT.format(topic=search_query, content=all_results)
            commentary_summary = invoke_llm(llm, llm_query)
            if commentary_summary:
                summaries['commentary'] = commentary_summary
    
    return summaries

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

commentary_results = []
if st.session_state.enable_commentary:
    commentary_results = perform_commentary_search(commentary_db, search_query)

# Generate summaries if the checkbox is checked
if summarize:
    if llm is None:
        st.error("No API token found, so LLM support is disabled.")
    else:
        with st.spinner("Generating summaries..."):
            summaries = generate_summaries(llm, search_query, bible_search_results, commentary_results)
            
            if 'bible' in summaries:
                st.subheader("Summary")
                st.success(summaries['bible'])
            
            if 'commentary' in summaries:
                st.subheader("Church Fathers' Summary")
                st.success(summaries['commentary'])


display_results(bible_search_results, commentary_results, bible_xml, greek_texts)

# Modify the summary buttons and display logic
num_summary_columns = 1 + int(st.session_state.enable_commentary)
summary_columns = st.columns(num_summary_columns)

# Display summaries
if 'bible_summary' in st.session_state:
    num_summary_display_columns = 1 + int(st.session_state.enable_commentary)
    summary_display_columns = st.columns(num_summary_display_columns)
    
    with summary_display_columns[0]:
        st.subheader("Bible Summary")
        st.success(st.session_state.bible_summary)
    
    if st.session_state.enable_commentary and 'commentary_summary' in st.session_state:
        with summary_display_columns[1]:
            st.subheader("Church Fathers' Summary")
            st.success(st.session_state.commentary_summary)

streamlit_analytics.stop_tracking(
    save_to_json=ANALYTICS_JSON_PATH, unsafe_password=UNSAFE_PASSWORD
)