# Biblos - Bible Exploration with Vector Search and Summarization

Biblos allows semantic search and summarization of Bible passages using state-of-the-art NLP techniques:

- Vector search over the entire Bible text using [Chroma](https://github.com/chroma-core/chroma) and instructor-large embeddings
- Summarization of search results using [Anthropic's Claude](https://www.anthropic.com/) large language model

This enables powerful semantic search over biblical texts to find related passages, along with high quality summaries of the relationships between verses on a given topic.

## Features

- Semantic search over the entire Bible text
- Summarization of search results using Claude LLM
- Web UI built with Streamlit for easy exploration
- Leverages Chroma for vector search over instructor-large embeddings
- Modular design allowing swapping of components like DB, embeddings, LLM etc.

## Architecture

Biblos follows a RAG (Retrieval Augmented Generation) architecture:

1. Bible text is indexed in a Chroma vector database using sentence embeddings
2. User searches for a topic, and relevant passages are retrieved by semantic similarity
3. Top results are collated and passed to Claude to generate a summarization

This enables combining the strengths of dense vector search for retrieval with a powerful LLM for summarization.

The UI is built using Streamlit for easy exploration, with Python code modularized for maintainability.

## Running Biblos

To run Biblos locally:

1. Install requirements

```
pip install -r requirements.txt
```

2. Download embedding model and preprocess Bible text into a Chroma database (optional -- if you don't recreate this, you can use the default embedding database that comes with the application)

```
cd data
python create_db.py
cd ..
```
_Note: This can take a long time (approx 18 minutes on an M1 Macbook Pro)_

3. Obtain an [Anthropic API Key](https://docs.anthropic.com/claude/reference/getting-started-with-the-api) and set it to environment variable `ANTHROPIC_API_KEY`

```
export ANTHROPIC_API_KEY ***your_api_key***
```

4. Launch the Streamlit app:

```
streamlit run app.py
```

## Credits

Biblos leverages the following open source projects:

- [Langchain](https://github.com/langchain-ai/langchain) - Building LLMs through composability
- [Chroma](https://github.com/chroma-core/chroma) - Vector similarity search
- [Anthropic](https://www.anthropic.com/) - Claude summarization model
- [instructor-large Embeddings](https://huggingface.co/hkunlp/instructor-large) - Text embeddings
- [Streamlit](https://streamlit.io/) - Web UI
