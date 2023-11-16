from langchain.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
import xml.etree.ElementTree as ET
import collections
import streamlit as st

def get_count_of_words_in_engwebp_vpl_xml():
    tree = ET.parse("../data/engwebp_vpl.xml")
    root = tree.getroot()

    verses_by_chapter = collections.defaultdict(list)
    for verse in root.findall("v"):
        book = verse.attrib["b"]
        chapter = int(verse.attrib["c"])
        verse_num = int(verse.attrib["v"])
        text = verse.text

        verses_by_chapter[(book, chapter)].append((verse_num, text))

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

    total_count = 0
    for doc in documents:
        chapter_text = doc.page_content
        chapter_words = chapter_text.split()
        chapter_word_count = len(chapter_words)
        total_count += chapter_word_count

    return total_count

def get_count_of_words_in_db(db):
    total_word_count = 0
    docs = db._collection.get()["documents"]
    for item in docs:
        total_word_count += len(item.split())
    return total_word_count

def query_databases(dbs, test_queries):
    results = []
    for idx, db in enumerate(dbs):
        db_results = []
        for query, validating_verses in test_queries.items():
            search_results = db.similarity_search_with_relevance_scores(
                query, k=4, score_function="cosine"
            )
            query_words = query.lower().split()

            # Check if the returned verses match the expected validating verses
            returned_verses = [f"{doc[0].metadata['book']} {doc[0].metadata['chapter']}" for doc in search_results]
            print(returned_verses)
            matches = sum(verse in validating_verses for verse in returned_verses)
            print(matches)
            
            total_similarity_scores = sum(match[1] for match in search_results)

            db_results.append(
                {
                    "idx": idx,
                    "query": query,
                    "matches": matches,
                    "validating_verses": validating_verses,
                    "returned_verses": returned_verses,
                    "total_similarity_scores": total_similarity_scores,
                }
            )

        total_matches = sum(result["matches"] for result in db_results)
        total_scores = sum(result["total_similarity_scores"] for result in db_results)
        total_word_count = get_count_of_words_in_db(db)

        db_results.append(
            {
                "idx": idx,
                "query": "total",
                "matches": total_matches,
                "total_similarity_scores": total_scores,
                "total_word_count": total_word_count,
            }
        )
        results.extend(db_results)
    return results


def get_chroma_db(embedding_function, persist_directory):
    return Chroma(
        persist_directory=persist_directory, embedding_function=embedding_function
    )

def get_embedding_function(model_name, model_kwargs, encode_kwargs, embedding_class):
    return embedding_class(
        model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
    )

model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": True}

# Refined query instruction
query_instruction = "Analyze and encapsulate the theological doctrines, historical context, narrative structure, and ethical teachings present in this biblical verse for in-depth semantic search and understanding:"

db_configs = [
    {
        "model_name": "BAAI/bge-large-en-v1.5",
        "persist_directory": "./test_data/bge_large_1k_db",
        "embedding_class": HuggingFaceBgeEmbeddings,
    },
    {
        "model_name": "hkunlp/instructor-large",
        "model_kwargs": {"query_instruction": query_instruction},  # Pass the refined query instruction
        "persist_directory": "./test_data/instructor_large_1K_db",
        "embedding_class": HuggingFaceInstructEmbeddings,
    },
]

dbs = [
    get_chroma_db(
        get_embedding_function(
            config["model_name"], model_kwargs, encode_kwargs, config["embedding_class"]
        ),
        config["persist_directory"],
    )
    for config in db_configs
]

test_queries = {
    "What did Jesus say about eternal life?": ["JHN 3", "JHN 17", "MAT 19"],
    "What does the parable of the Prodigal Son reveal about forgiveness and family relationships?": ["LUK 15"],
    "How is faith described in the New Testament?": ["HEB 11"],
    "What are the Beatitudes and what do they teach about Christian life?": ["MAT 5"],
    "What does Psalm 23 reflect about God's guidance and protection?": ["PSA 23"],
    "How does the book of Revelation describe the end times?": ["REV 21", "REV 22"],
    "What lessons can be learned from the story of David and Goliath?": ["1SA 17"],
    "What does Paul say about love in his letters to the Corinthians?": ["1CO 13"],
    "What teachings are given in the Sermon on the Mount?": ["MAT 5", "MAT 6", "MAT 7"],
    "How does the book of Genesis describe the creation?": ["GEN 1", "GEN 2"]
    # ... [add more test queries as needed]
}


results = query_databases(dbs, test_queries)

st.title("Test results")

st.subheader(f"Total word count of engwebp_vpl_xml: {get_count_of_words_in_engwebp_vpl_xml()}")

columns = st.columns(len(dbs))
for idx, col in enumerate(columns):
    col.header(f"Database {idx + 1}")

for query in list(test_queries.keys()) + ["total"]:
    for idx, col in enumerate(columns):
        res = next(
            (item for item in results if item["query"] == query and item["idx"] == idx),
            None,
        )
        col.write(f"Query: {query}")
        col.write(f"Matches: {res['matches'] if res else 'N/A'}")
        if res and "search_results" in res:
            expander = col.expander("Search results")
            expander.write(f"{res['search_results']}")
        col.write(
            f"Total Similarity Scores: {res['total_similarity_scores'] if res else 'N/A'}"
        )
        if res and "total_word_count" in res:
            col.write(
                f"Total Word Count: {res['total_word_count'] if res else 'N/A'}"
            )
