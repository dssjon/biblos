# greek.py

import streamlit as st
import os
import re
from config import NT_BOOK_MAPPING, BIBLE_BOOK_NAMES, LEXICON_XML_FILE
import xml.etree.ElementTree as ET

@st.cache_resource
def load_greek_texts(directory):
    greek_texts = {}
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            book_code = filename.split('.')[0]
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                greek_texts[book_code] = file.readlines()
    return greek_texts

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

greek_texts = load_greek_texts('./data/sblgnt')
dodson_lexicon = load_lexicon_xml(LEXICON_XML_FILE)

@st.cache_data
def search_greek_texts(book_code, chapter=None):
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
    return matches if matches else []

@st.cache_data
def search_lexicon(greek_word):
    for entry_id, entry_data in dodson_lexicon.items():
        if entry_data['orth'].startswith(greek_word):
            return entry_data['definitions'].get('full', None)
    return None

def display_greek_results(results):
    for r in results:
        book_abbr = r[0].metadata['book']
        book = BIBLE_BOOK_NAMES.get(book_abbr, book_abbr)
        chapter = r[0].metadata['chapter']
        
        greek_book_code = NT_BOOK_MAPPING.get(book_abbr, "")
        if greek_book_code:
            with st.expander(f"**{book} {chapter}** - SBL Greek New Testament", expanded=True):
                greek_paragraph = search_greek_texts(greek_book_code, chapter)
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