import sqlite3
import argparse
from datetime import datetime
from langchain.schema import Document
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter

# Parse the command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-db", "--db_file", default="./data.sqlite", help="path to SQLite database file")
parser.add_argument("-m", "--model_name", default="hkunlp/instructor-large", help="name of the HuggingFace model to use")
parser.add_argument("-o", "--output_dir", default="./output_db", help="path to output directory")
args = parser.parse_args()

# Update variables with user input
db_file = args.db_file
model_name = args.model_name
output_dir = args.output_dir

# db file from https://github.com/HistoricalChristianFaith/Commentaries-Database

# subset of the authors in the DB
top_authors = [
    "Augustine of Hippo", "Thomas Aquinas", "John Chrysostom", "Jerome", "Athanasius of Alexandria"
]

# New Testament book commentaries found in the db file
new_testament_books = [
    'matthew', 'mark', 'luke', 'john', 'acts', 'romans', '1corinthians', '2corinthians',
    'galatians', 'ephesians', 'philippians', 'colossians', '1thessalonians', '2thessalonians',
    '1timothy', '2timothy', 'titus', 'philemon', 'hebrews', 'james', '1peter',
    '2peter', '1john', '2john', '3john', 'jude', 'revelation'
]

# Connect to SQLite database and handle potential errors
try:
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    query = "SELECT id, father_name, file_name, append_to_author_name, ts, book, location_start, location_end, txt, source_url, source_title FROM commentary"
    query = query + " WHERE father_name IN ('" + "','".join(top_authors) + "')"
    query += " AND book IN ('" + "','".join(new_testament_books) + "')"

    print("running query", query)
    cursor.execute(query)
    rows = cursor.fetchall()
    
except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
    sys.exit(1)

# Create documents
documents = []
for row in rows:
    id, father_name, file_name, append_to_author_name, ts, book, location_start, location_end, txt, source_url, source_title = row
    
    # skipping smaller commentaries
    if len(txt) < 1000:
        continue
    
    if source_title == None or source_title == "":
        continue
    doc = Document(page_content=txt)
    doc.metadata = {
        "id": id,
        "father_name": father_name,
        "book": book,
        "location_start": location_start,
        "location_end": location_end,
        "source_url": source_url,
        "source_title": source_title
    }
    
    documents.append(doc)

# Close the database connection
cursor.close()
connection.close()

#Split into chunks
chunk_size = 2000
chunk_overlap = 0
text_splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    length_function = len,
    is_separator_regex = True,
)

split_documents = text_splitter.split_documents(documents)
print(f' {len(split_documents)} documents created from {len(documents)} entries')

# Load embeddings
print(f"Loading embeddings from model {model_name}...")
embedding_function = HuggingFaceInstructEmbeddings(
    model_name=model_name,
    query_instruction="Represent the Religious bible commentary text for semantic search:",
    encode_kwargs={'normalize_embeddings': True},
    model_kwargs={"device": "mps"}
)

# Create Chroma database
print(f"Initializing db and creating embeddings to {output_dir} (please be patient, this will take a while)...")
db = Chroma.from_documents(
    split_documents,
    embedding_function,
    persist_directory=output_dir,
    collection_metadata={"hnsw:space": "cosine"},
)

print("Saving database...")
db.persist()

then = datetime.now()
completed_at = datetime.now()
elapsed_time_s = (completed_at - then).total_seconds()

print(f"Completed in {elapsed_time_s} seconds")
exit()
