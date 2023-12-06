import streamlit as st
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceInstructEmbeddings
import sqlite3
import random

@st.cache_resource
def setup_commentary_db():
    embeddings = HuggingFaceInstructEmbeddings(
        model_name="hkunlp/instructor-large",
        query_instruction="Represent the Religious bible commentary text for semantic search:",
    )
    commentary_db = Chroma(
        persist_directory="./",
        embedding_function=embeddings,
    )
    return commentary_db

db = setup_commentary_db()

# deleting data to target < 100 MB db size
ids = db.get(where={"father_name": "Jerome"})['ids']
print(ids)
# db.delete(ids=ids)

def vacuum_sqlite_db(db_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute the VACUUM command
    cursor.execute("VACUUM")

    # Close the connection
    conn.close()

# Replace 'your_database_file.db' with the path to your database file
vacuum_sqlite_db('./chroma.sqlite3')
