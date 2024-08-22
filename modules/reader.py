# reader.py

import streamlit as st
import xml.etree.ElementTree as ET
from config import BIBLE_BOOK_NAMES, BIBLE_XML_FILE

@st.cache_resource
def load_bible_xml(input_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    return root

@st.cache_data
def get_full_chapter_text(book_abbr, chapter):
    bible_xml = load_bible_xml(BIBLE_XML_FILE)
    query = f".//v[@b='{book_abbr}'][@c='{chapter}']"
    full_chapter_content = ""
    for verse in bible_xml.findall(query):
        verse_num = verse.get('v')
        text = verse.text
        full_chapter_content += f"{verse_num} {text}\n"
    return full_chapter_content.strip()

@st.cache_data
def split_content_into_paragraphs(content, lines_per_paragraph=5):
    paragraphs = []
    lines = content.split('\n')
    current_paragraph = []
    span_open = False
    for line in lines:
        if "<span" in line and "</span>" not in line:
            span_open = True
        current_paragraph.append(line)
        if len(current_paragraph) >= lines_per_paragraph and not span_open:
            paragraphs.append("\n".join(current_paragraph))
            current_paragraph = []
        if "</span>" in line:
            span_open = False
    if current_paragraph:
        paragraphs.append("\n".join(current_paragraph))
    return paragraphs

def update_chapter():
    st.session_state.current_chapter = st.session_state.chapter_select

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
        chapter = st.number_input("Chapter", min_value=1, max_value=max_chapters, value=st.session_state.current_chapter, key="chapter_select", on_change=update_chapter)
