from langchain.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import Chroma
import streamlit as st


def query_databases(dbs, queries):

    results = []
    for idx, db in enumerate(dbs):
        db_results = []
        for query in queries:

            # TODO: configure k and score function
            search_results = db.similarity_search_with_relevance_scores(
                query, k=4, score_function="cosine"
            )
            query_words = query.lower().split()

            page_contents = [doc[0].page_content.replace("\n", " ") for doc in search_results]

            # TODO: Find semantic matches
            match_count = sum(
                any(word in content.lower() for word in query_words)
                for content in page_contents
            )
            total_similarity_scores = sum(match[1] for match in search_results)
            
            db_results.append(
                {
                    "idx": idx,
                    "query": query,
                    "matches": match_count,
                    "search_results": search_results,
                    "total_similarity_scores": total_similarity_scores,
                }
            )

        total_matches = sum(result["matches"] for result in db_results)
        total_scores = sum(result["total_similarity_scores"] for result in db_results)
        
        db_results.append(
            {
                "idx": idx,
                "query": "total",
                "matches": total_matches,
                "total_similarity_scores": total_scores,
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

# TODO: Expand to include additional instructor models, with query instruction params, trained on varying instruction prompts
# TODO: Allow for creation of db from scratch, instead of including pre-built dbs
db_configs = [
    {
        "model_name": "BAAI/bge-large-en-v1.5",
        "persist_directory": "./test_data/bge_large_1k_db",
        "embedding_class": HuggingFaceBgeEmbeddings,
    },
    {
        "model_name": "hkunlp/instructor-large",
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

# TODO: Add queries and implement better scoring considering the number semantic matches & target verses desired
queries = [
    "three days nights",
    "Keys Kingdom Heaven",
    "Sign Jonah",
    "Doeg Edomite",
    "What did Jesus say about eternal life?",
]

results = query_databases(dbs, queries)

st.title("Test results")

columns = st.columns(len(dbs))
for idx, col in enumerate(columns):
    # TODO: Return db name and render instead of idx
    col.header(f"Database {idx + 1}")

for query in queries + ["total"]:
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
