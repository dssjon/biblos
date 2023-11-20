from langchain.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
import xml.etree.ElementTree as ET
import collections
import streamlit as st
import pandas as pd

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

def query_databases(dbs, test_queries, k, score_function):
    results = []
    for idx, db in enumerate(dbs):
        db_results = []
        for query, validating_verses in test_queries.items():
            search_results = db.similarity_search_with_relevance_scores(
                query, k=k, score_function=score_function
            )

            # Check if the returned verses match the expected validating verses
            returned_verses = [f"{doc[0].metadata['book']} {doc[0].metadata['chapter']}" for doc in search_results]
            print("validating:" , validating_verses)
            print("returned: ", returned_verses)
            matches = sum(verse in validating_verses for verse in returned_verses)
            print("matches: ", matches)
            
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
#query_instruction = "Analyze and encapsulate the theological doctrines, historical context, narrative structure, and ethical teachings present in this biblical verse for in-depth semantic search and understanding:"
query_instruction = "Represent the Religious question for retrieving related passages: "
query_instruction2 = "Conduct a detailed semantic search to find biblical verses closely related to the theological, historical, and ethical aspects of the following query, focusing on direct scriptural relevance and doctrinal accuracy: "
query_instruction3 = "Analyze and encapsulate the theological doctrines, historical context, narrative structure, and ethical teachings present in this biblical verse for in-depth semantic search and understanding:"
query_instruction4 = "Represent the Religious Bible verse text for semantic search:"

db_configs = [
    {
        "model_name": "BAAI/bge-large-en-v1.5",
        "persist_directory": "./test_data/bge_large_1k_db",
        "embedding_class": HuggingFaceBgeEmbeddings,
    },
    {
        "model_name": "hkunlp/instructor-large",
        "model_kwargs": {"query_instruction": query_instruction},
        # create_db -> query_instruction: "Represent the Religious passage for retrieval: "
        "persist_directory": "./test_data/instructor_large_1K_db_new_instruction",
        "embedding_class": HuggingFaceInstructEmbeddings,
    },
    {
        "model_name": "hkunlp/instructor-large",
        "model_kwargs": {"query_instruction": query_instruction}, 
        "persist_directory": "./test_data/instructor_large_1K_db",
        "embedding_class": HuggingFaceInstructEmbeddings,
    },
    {
        "model_name": "hkunlp/instructor-large",
        "model_kwargs": {"query_instruction": query_instruction2}, 
        "persist_directory": "./test_data/instructor_large_1K_db",
        "embedding_class": HuggingFaceInstructEmbeddings,
    },
    {
        "model_name": "hkunlp/instructor-large",
        "model_kwargs": {"query_instruction": query_instruction3},
        "persist_directory": "./test_data/instructor_large_1K_db",
        "embedding_class": HuggingFaceInstructEmbeddings,
    },
        {
        "model_name": "hkunlp/instructor-large",
        "model_kwargs": {"query_instruction": query_instruction4},
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
    "How is faith described in the New Testament?": ["HEB 11", "ROM 4", "JAS 2"],
    "What are the Beatitudes and what do they teach about Christian life?": ["MAT 5"],
    "What does Psalm 23 reflect about God's guidance and protection?": ["PSA 23"],
    "How does the book of Revelation describe the end times?": ["REV 21", "REV 22", "REV 20"],
    "What lessons can be learned from the story of David and Goliath?": ["1SA 17"],
    "What does Paul say about love in his letters to the Corinthians?": ["1CO 13"],
    "What teachings are given in the Sermon on the Mount?": ["MAT 5", "MAT 6", "MAT 7"],
    "How does the book of Genesis describe the creation?": ["GEN 1", "GEN 2"]
    # ... [add more test queries as needed]
}


results = query_databases(dbs, test_queries, 4, "cosine")
# below has no effect on scoring
#results2 = query_databases(dbs, test_queries, 4, "l2")
#results3 = query_databases(dbs, test_queries, 4, "ip")

st.title("Test results")

st.subheader(f"Total word count of engwebp_vpl_xml: {get_count_of_words_in_engwebp_vpl_xml()}")

def results_to_dataframe(results):
    data = {
        "Database": [],
        "Query": [],
        "Validating Verses": [],
        "Returned Verses": [],
        "Matches": [],
        "Total Similarity Scores": [],
        "Total Word Count": []
    }

    for result in results:
        data["Database"].append(f"Database {result['idx'] + 1}")
        data["Query"].append(result["query"])
        data["Validating Verses"].append(", ".join(result.get("validating_verses", [])))
        data["Returned Verses"].append(", ".join(result.get("returned_verses", [])))
        data["Matches"].append(result.get("matches", 'N/A'))
        data["Total Similarity Scores"].append(result.get("total_similarity_scores", 'N/A'))
        data["Total Word Count"].append(result.get("total_word_count", 'N/A'))

    return pd.DataFrame(data)

df_results = results_to_dataframe(results)
st.dataframe(df_results)
