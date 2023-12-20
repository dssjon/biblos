# File paths
ANALYTICS_JSON_PATH = "./data/analytics.json"
DB_DIR = "./data/db"
COMMENTARY_DB_DIR = "./data/commentary_db"
BIBLE_XML_FILE = "./data/engwebp_vpl.xml"
LEXICON_XML_FILE = "./data/dodson.xml"

# URLs
HELP_URL = "https://www.github.com/dssjon"
BUG_REPORT_URL = "https://www.github.com/dssjon"
ABOUT_URL = "Made with <3 by https://www.github.com/dssjon"

# Model names
EMBEDDING_MODEL_NAME = "hkunlp/instructor-large"
#LLM_MODEL_NAME = "claude-2.1"
#MAX_TOKENS = 200000
#LLM_MODEL_NAME = "claude-2.0"
LLM_MODEL_NAME = "claude-instant-1.2"
MAX_TOKENS = 100000

# Query Instructions
DB_QUERY = "Represent the Religious Bible verse text for semantic search:"
COMMENTARY_DB_QUERY = "Represent the Religious bible commentary text for semantic search:"

# Prompts
BIBLE_SUMMARY_PROMPT = """Based on the user's search query, the topic is: {topic}
Please provide a concise summary of the key points made in the following Bible passages about the topic above, including chapter and verse references. Focus only on the content found in these specific verses. Explain connections between the passages and how they theologically relate to the overarching biblical meta narrative across both Old and New Testaments.
{content}"""

COMMENTARY_SUMMARY_PROMPT = """Based on the user's search query, the topic is: {topic}
Please provide a concise summary of the key insights and interpretations offered in the following Church Fathers' commentaries on the topic above. Focus only on the content in these specific commentaries, highlighting how they contribute to understanding the scriptural texts. Include the church father and source text.
{content}"""

# Church Fathers
CHURCH_FATHERS = [
    "Augustine of Hippo",
    "Athanasius of Alexandria",
    "Basil of Caesarea",
    "Gregory of Nazianzus",
    "Gregory of Nyssa",
    "Cyril of Alexandria",
    "Irenaeus",
    "Cyprian",
    "Origen of Alexandria"
]

# Test Queries
DEFAULT_QUERIES = [
    "What did Jesus say about eternal life?",
    "Divine agape and  God's love for humanity",
    "What will happen during the end times?",
    "What is the work and nature of the Holy Spirit in our life?",
    "Experiencing God's presence: Comfort and renewal in the Christian life",
]

# Other constants
UNSAFE_PASSWORD = "x"
LLM_ERROR = "No API token found, so LLM support is disabled."
LLM_NOT_FOUND = "No API token found, so LLM support is disabled."

FATHER_NAME = "father_name"
APPEND_TO_AUTHOR_NAME = "append_to_author_name="
SOURCE_TITLE = "source_title"
BOOK = "book"
CHAPTER = "chapter"
TITLE = "Biblos: Exploration Tool"
SEARCH_LABEL = "Search:"
SCORE_RESULT = """**Similarity Score**: {value}"""
SCORE_FUNCTION = "cosine"

