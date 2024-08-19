# Biblos - Advanced Bible Exploration with Vector Search and Multi-Layered Analysis

Biblos is a sophisticated tool for semantic search and in-depth analysis of Biblical texts, leveraging state-of-the-art NLP techniques and historical commentaries:

- Semantic search over the entire Bible text using [Chroma](https://github.com/chroma-core/chroma) and instructor-large embeddings
- Summarization of search results using [Anthropic's Claude](https://www.anthropic.com/) large language model
- Full chapter view for comprehensive context
- Integration of Greek New Testament text and Dodson Greek Lexicon for original language insights
- Incorporation of Church Fathers' commentaries for historical theological perspectives

This powerful combination enables not just semantic search over biblical texts to find related passages, but also provides a multi-layered analysis including original language study and historical interpretations.

## Features

- Semantic search over the entire Bible text
- Full chapter view option for broader context
- Greek New Testament text display for relevant passages
- Greek word definitions from Dodson Greek Lexicon
- Church Fathers' commentary integration for historical insights
- Summarization of search results using Claude LLM
- Web UI built with Streamlit for easy exploration
- Leverages Chroma for vector search over instructor-large embeddings
- Modular design allowing swapping of components like DB, embeddings, LLM etc.

## Architecture

Biblos follows an enhanced RAG (Retrieval Augmented Generation) architecture:

1. Bible text is indexed in a Chroma vector database using sentence embeddings
2. User searches for a topic, and relevant passages are retrieved by semantic similarity
3. Top results are displayed with options for full chapter view and Greek text (for NT passages)
4. Greek words are linked to definitions from the Dodson Greek Lexicon
5. Relevant Church Fathers' commentaries are retrieved and displayed
6. Selected results are collated and passed to Claude to generate a summarization

This architecture combines dense vector search for retrieval with multiple layers of contextual information and a powerful LLM for summarization.

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
python create_commentary_db.py
cd ..
```
_Note: This can take a long time (approx 18 minutes on an M1 Macbook Pro for the Bible text, and additional time for commentaries)_

3. Obtain an [Anthropic API Key](https://docs.anthropic.com/claude/reference/getting-started-with-the-api) and set it to environment variable `ANTHROPIC_API_KEY`

```
export ANTHROPIC_API_KEY ***your_api_key***
```

4. Launch the Streamlit app:

```
streamlit run app.py
```

## Usage

1. Enter a search query in the text input field
2. Adjust search options:
   - Select Old Testament and/or New Testament
   - Toggle Full Chapter view
   - Enable Church Fathers commentaries
   - Enable Greek NT and Lexicon display
   - Adjust the number of Bible results
3. View search results, expanding sections for more details
4. For New Testament results, view the Greek text and word definitions
5. Explore Church Fathers' commentaries if enabled
6. Generate a summary of the results using the "Summary" button

## Credits

Biblos leverages the following open source projects and resources:

- [Langchain](https://github.com/langchain-ai/langchain) - Building LLMs through composability
- [Chroma](https://github.com/chroma-core/chroma) - Vector similarity search
- [Anthropic](https://www.anthropic.com/) - Claude summarization model
- [instructor-large Embeddings](https://huggingface.co/hkunlp/instructor-large) - Text embeddings
- [Streamlit](https://streamlit.io/) - Python Web UI
- [SBL Greek New Testament](https://www.sblgnt.com/) - Greek text of the New Testament
- [Dodson Greek Lexicon](https://github.com/biblicalhumanities/Dodson-Greek-Lexicon) - Greek word definitions
- [Historical Christian Faith Commentaries Database](https://github.com/HistoricalChristianFaith/Commentaries-Database) - Church Fathers' commentaries

