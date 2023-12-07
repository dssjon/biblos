import xml.etree.ElementTree as ET
import collections
import sys
import argparse
from datetime import datetime

from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain.embeddings import HuggingFaceInstructEmbeddings

# Accept the following arguments:
#  -input_file (-i) : path to input VPL file (default: "./engwebp_vpl.xml")
#  -model_name (-m) : name of the HuggingFace model to use (default: "hkunlp/instructor-large")
#  -query_instruction (-q) : query instruction to use (default: "Represent the religious Bible verse text for semantic search:")
#  -output_dir (-o) : path to base output directory (default: "./db")

input_file = "./engwebp_vpl.xml"
model_name = "hkunlp/instructor-large"
query_instruction = "Represent the Religious Bible verse text for semantic search:"
output_dir = "./output_db"

# Parse the command-line arguments

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input_file", default=input_file, help=f"path to input VPL fil (expected .xml format, default {input_file})")
parser.add_argument("-m", "--model_name", default=model_name, help=f"name of the HuggingFace model to use (default: {model_name})")
parser.add_argument("-q", "--query_instruction", default=query_instruction, help=f"query instruction to use (default: \"{query_instruction}\")")
parser.add_argument("-o", "--output_dir", default=output_dir, help="path to base output directory. The output directory will be modified to reflect the input_file and model_name parameters if they are different from their defaults.")
args = parser.parse_args()

output_dir = args.output_dir

# If any of the arguemnts are not at their default, then modify the output_dir to reflect the arguments
if args.input_file != input_file:
    input_file = args.input_file
    output_dir = output_dir + "_" + input_file.split('/')[-1].split('.')[0]
if args.model_name != model_name:
    model_name = args.model_name
    output_dir = output_dir + "_" + model_name.replace("/", "_")
if args.query_instruction != query_instruction:
    query_instruction = args.query_instruction
    # TODO: Should we include the query instruction in the output_dir?

print(f"input_file: {input_file}")
print(f"model_name: {model_name}")
print(f"query_instruction: {query_instruction}")
print(f"output_dir: {output_dir}")

# Load XML
tree = ET.parse(input_file)
root = tree.getroot()

then = datetime.now()

print()
print("Parsing XML, grouping verses by chapter...")
# Group verses by chapter
verses_by_chapter = collections.defaultdict(list)
for verse in root.findall("v"):
    book = verse.attrib["b"]
    chapter = int(verse.attrib["c"])
    verse_num = int(verse.attrib["v"])
    text = verse.text

    verses_by_chapter[(book, chapter)].append((verse_num, text))

print(f' {sum(len(verses) for verses in verses_by_chapter.values())} verses found')
print(f' {len(verses_by_chapter)} chapters found')

print(f'Creating documents for each chapter...')
# Create document for each chapter
documents = []
testament="OT"

for (book, chapter), verses in verses_by_chapter.items():
    chapter_text = ""
    for verse_num, text in verses:
        chapter_text += f"{text}\n"

    if book.lower().startswith("mat"):
        testament = "NT"

    verse_nums_as_string = ",".join(str(verse_num) for verse_num, text in verses)
    doc = Document(page_content=chapter_text)
    doc.metadata = {
        "book": book,
        "chapter": chapter,
        "verse_nums": verse_nums_as_string,
        "testament": testament,
    }
    documents.append(doc)

# TODO: Try out alternative splitters and test results
# RecursiveCharacterTextSplitter: This splitter divides the text into fragments based on characters, starting with the first character. If the fragments turn out to be too large, it moves on to the next character. It offers flexibility by allowing you to define the division characters and fragment size

# RecursiveTextSplitter: This splitter divides text into fragments based on words or tokens instead of characters. This provides a more semantic view and is ideal for content analysis rather than structure

# Split into chunks
chunk_size = 1000
chunk_overlap = 0
verse_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
)
bible = verse_splitter.split_documents(documents)

print(f' {len(bible)} documents created from {len(documents)} chapters')

# Load embeddings
print(f"Loading embeddings from model {model_name}...")
embedding_function = HuggingFaceInstructEmbeddings(
    model_name=model_name,
    query_instruction=query_instruction,
    encode_kwargs = {'normalize_embeddings': True},
    model_kwargs = {"device": "mps"}
)

# Create Chroma database
print(f"Initializing db and creating embeddings to {output_dir} (please be patient, this will take a while)...")
db = Chroma.from_documents(
    bible,
    embedding_function,
    persist_directory=output_dir,
    collection_metadata={"hnsw:space": "cosine"},
)

print("Saving database...")
db.persist()

completed_at = datetime.now()
elapsed_time_s = (completed_at - then).total_seconds()

print(f"Completed in {elapsed_time_s} seconds")
exit()
