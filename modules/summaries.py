# summaries.py

import streamlit as st
from config import BIBLE_SUMMARY_PROMPT, COMMENTARY_SUMMARY_PROMPT, LLM_ERROR
from modules.search import format_bible_results, format_commentary_results
from config import *
import requests
import os 

@st.cache_resource
def setup_llm():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("No API token found, so LLM support is disabled.")
        return None
    
    return {
        "api_url": API_URL,
        "headers": {
            "x-api-key": api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        },
        "model": LLM_MODEL_NAME,
    }

def invoke_llm(llm, prompt):
    if not llm:
        st.error(LLM_ERROR)
        return None
    
    data = {
        "model": llm["model"],
        "max_tokens": 256,
        "temperature": 0.0,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(llm["api_url"], headers=llm["headers"], json=data)
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except requests.RequestException as e:
        st.error(f"Error invoking LLM: {str(e)}")
        return None

def generate_summaries(search_query, bible_search_results, commentary_results):
    llm = setup_llm()
    if not llm:
        st.error(LLM_ERROR)
        return {}

    summaries = {}
    
    # Generate Bible summary
    if bible_search_results:
        bible_passages = []
        for result in bible_search_results:
            content = result[0].page_content
            book = BIBLE_BOOK_NAMES.get(result[0].metadata['book'], result[0].metadata['book'])
            chapter = result[0].metadata['chapter']
            bible_passages.append(f"Source: {book} {chapter}\nContent: {content}")
        
        all_results = "\n\n".join(bible_passages)
        llm_query = BIBLE_SUMMARY_PROMPT.format(topic=search_query, passages=all_results)
        bible_summary = invoke_llm(llm, llm_query)
        if bible_summary:
            summaries['bible'] = bible_summary
    
    # Generate Commentary summary if enabled
    if st.session_state.enable_commentary and commentary_results:
        commentary_passages = []
        for result in commentary_results:
            content = result[0].page_content
            author = result[0].metadata['father_name']
            source = result[0].metadata['source_title']
            commentary_passages.append(f"Source: {author} - {source}\nContent: {content}")
        
        all_results = "\n\n".join(commentary_passages)
        llm_query = COMMENTARY_SUMMARY_PROMPT.format(topic=search_query, content=all_results)
        commentary_summary = invoke_llm(llm, llm_query)
        if commentary_summary:
            summaries['commentary'] = commentary_summary
    
    return summaries

def display_summaries(search_query, bible_results, commentary_results):
    summaries = generate_summaries(search_query, bible_results, commentary_results)

    if 'bible' in summaries:
        st.subheader("Summary")
        st.success(summaries['bible'])

    if 'commentary' in summaries:
        st.subheader("Church Fathers' Summary")
        st.success(summaries['commentary'])