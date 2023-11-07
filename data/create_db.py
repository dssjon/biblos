import xml.etree.ElementTree as ET
import collections

from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain.embeddings import HuggingFaceInstructEmbeddings

# Load XML
tree = ET.parse("./engwebp_vpl.xml")
root = tree.getroot()

# Group verses by chapter
verses_by_chapter = collections.defaultdict(list)
for verse in root.findall("v"):
    book = verse.attrib["b"]
    chapter = int(verse.attrib["c"])
    verse_num = int(verse.attrib["v"])
    text = verse.text

    verses_by_chapter[(book, chapter)].append((verse_num, text))

# Create document for each chapter
documents = []
for (book, chapter), verses in verses_by_chapter.items():
    chapter_text = ""
    for verse_num, text in verses:
        chapter_text += f"{text}\n"

    verse_nums_as_string = ",".join(str(verse_num) for verse_num, text in verses)
    doc = Document(page_content=chapter_text)
    doc.metadata = {
        "book": book,
        "chapter": chapter,
        "verse_nums": verse_nums_as_string,
    }
    documents.append(doc)

# Split into chunks
chunk_size = 1000
chunk_overlap = 100
verse_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
)
bible = verse_splitter.split_documents(documents)

# Load embeddings
print("loading embeddings")
embedding_function = HuggingFaceInstructEmbeddings(
    model_name="hkunlp/instructor-xl",
    query_instruction="Represent the Religious Bible verse text for semantic search:",
    encode_kwargs = {'normalize_embeddings': True}
)

# Create Chroma database
print("initializing db")
db = Chroma.from_documents(
    bible,
    embedding_function,
    persist_directory="./output_db",
    collection_metadata={"hnsw:space": "cosine"},
)

print("persisting db")
db.persist()

print("done")
exit()
