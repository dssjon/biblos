# File paths
ANALYTICS_JSON_PATH = "./data/analytics.json"
BIBLE_DB_PERSIST_DIRECTORY = "./data/db"
COMMENTARY_DB_PERSIST_DIRECTORY = "./data/commentary_db"

# URLs
HELP_URL = "https://www.github.com/dssjon"
BUG_REPORT_URL = "https://www.github.com/dssjon"
ABOUT_URL = "Made with <3 by https://www.github.com/dssjon"

# Model names
HUGGINGFACE_INSTRUCT_MODEL_NAME = "hkunlp/instructor-large"
LLM_MODEL_NAME = "claude-2.1"

# Query Instructions
BIBLE_DB_QUERY_INSTRUCTION = "Represent the Religious Bible verse text for semantic search:"
COMMENTARY_DB_QUERY_INSTRUCTION = "Represent the Religious bible commentary text for semantic search:"

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
    "What is the fruit of the spirit?",
    "How to handle pain and suffering",
    "What will happen during the end times?",
    "What is love?",
    "What is the Holy Spirit?",
    "The importance of faith",
    "Living a Christian life",
    "Understanding salvation",
    "Overcoming temptation",
]

# Other constants
MAX_TOKENS = 200000
UNSAFE_PASSWORD = "x"
LLM_ERROR = "No API token found, so LLM support is disabled."

FATHER_NAME = "father_name"
SOURCE_TITLE = "source_title"
BOOK = "book"
CHAPTER = "chapter"

