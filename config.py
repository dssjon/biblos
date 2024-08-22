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
API_URL = "https://api.anthropic.com/v1/messages"
LLM_MODEL_NAME = "claude-3-5-sonnet-20240620"
MAX_TOKENS = 500

# Query Instructions
DB_QUERY = "Represent the Religious Bible verse text for semantic search:"
COMMENTARY_DB_QUERY = "Represent the Religious bible commentary text for semantic search:"

# Prompts
BIBLE_SUMMARY_PROMPT_ORIG = """
The topic for analysis is {topic}. Here are the Bible passages: {passages}.  Please provide the following:

* **Key Insights:** Summarize the main points made about the topic within these specific verses.
* **Connections:** How do the verses reinforce, complement, or potentially challenge each other's perspective on the topic?
* **Theological Significance:** How do these insights connect to the broader story of God's redemption (as seen in the gospel message) across the Old and New Testaments?
* **Practical Application:** What actions or changes in understanding might be inspired by reflecting on these passages together?
"""


BIBLE_SUMMARY_PROMPT = """You are a concise Biblical scholar assisting a seeker with their query: "{topic}"  Given these relevant passages: {passages} Provide a brief, focused response on the central theme or teaching from these verses related to the query. Keep your response under 200 words, grounded in conservative theology.
"""


COMMENTARY_SUMMARY_PROMPT = """You are a concise Biblical scholar assisting a seeker with their query: {topic} Given these relevant church fathers commentary search results: {content}
Provide a brief summary of the key insights and interpretations of the Church Fathers' thoughts. Keep your response under 200 words, grounded in conservative theology.
"""


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
    #"Divine agape and  God's love for humanity",
    #"What will happen during the end times?",
    #"What is the work and nature of the Holy Spirit in our life?",
    #"Experiencing God's presence: Comfort and renewal in the Christian life",
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
SEARCH_LABEL = "Semantic Search:"
SCORE_RESULT = """**Similarity Score**: {value}"""
SCORE_FUNCTION = "cosine"

HEADER_LABEL = """
    <div class="title-container" style="display: flex; justify-content: space-between; align-items: center; margin-top: 0rem; padding-top: 0rem; margin-bottom: 0rem; padding-bottom: 0rem; flex-wrap: wrap;">
        <h1 style="font-size: 2rem; font-weight: 800; color: #3b3b3b; margin-top: 0rem; padding-top: 0rem; margin-bottom: 0rem;">
            Explore the Bible
        </h1>
        <div class="search-label-container" style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0rem; padding-bottom: 0.5rem;">
            <p style="font-size: 1.125rem; color: #6b7280; font-style: italic; text-align: right; margin-bottom: 0rem;">
                Semantic Search & Summary Insights
            </p>
            <a href="https://www.github.com/dssjon" target="_blank" rel="noopener noreferrer" style="color: #6b7280; text-decoration: none;">
                <svg height="24" aria-hidden="true" viewBox="0 0 16 16" version="1.1" width="24" data-view-component="true" class="octicon octicon-mark-github v-align-middle">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            </a>
        </div>
    </div>
"""

BIBLE_BOOK_NAMES = {
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus", "NUM": "Numbers", "DEU": "Deuteronomy",
    "JOS": "Joshua", "JDG": "Judges", "RUT": "Ruth", "1SA": "1 Samuel", "2SA": "2 Samuel",
    "1KI": "1 Kings", "2KI": "2 Kings", "1CH": "1 Chronicles", "2CH": "2 Chronicles", "EZR": "Ezra",
    "NEH": "Nehemiah", "EST": "Esther", "JOB": "Job", "PSA": "Psalms", "PRO": "Proverbs",
    "ECC": "Ecclesiastes", "SNG": "Song of Solomon", "ISA": "Isaiah", "JER": "Jeremiah", "LAM": "Lamentations",
    "EZK": "Ezekiel", "DAN": "Daniel", "HOS": "Hosea", "JOL": "Joel", "AMO": "Amos",
    "OBA": "Obadiah", "JON": "Jonah", "MIC": "Micah", "NAM": "Nahum", "HAB": "Habakkuk",
    "ZEP": "Zephaniah", "HAG": "Haggai", "ZEC": "Zechariah", "MAL": "Malachi",
    "MAT": "Matthew", "MRK": "Mark", "LUK": "Luke", "JHN": "John", "ACT": "Acts",
    "ROM": "Romans", "1CO": "1 Corinthians", "2CO": "2 Corinthians", "GAL": "Galatians", "EPH": "Ephesians",
    "PHP": "Philippians", "COL": "Colossians", "1TH": "1 Thessalonians", "2TH": "2 Thessalonians", "1TI": "1 Timothy",
    "2TI": "2 Timothy", "TIT": "Titus", "PHM": "Philemon", "HEB": "Hebrews", "JAS": "James",
    "1PE": "1 Peter", "2PE": "2 Peter", "1JN": "1 John", "2JN": "2 John", "3JN": "3 John",
    "JUD": "Jude", "REV": "Revelation"
}

NT_BOOK_MAPPING = {
    "1CO": "1Cor", "1PE": "1Pet", "1TI": "1Tim", "2JN": "2John", "2TH": "2Thess",
    "3JN": "3John", "COL": "Col", "GAL": "Gal", "JAS": "Jas", "JUD": "Jude",
    "MRK": "Mark", "PHP": "Phil", "REV": "Rev", "TIT": "Titus", "1JN": "1John",
    "1TH": "1Thess", "2CO": "2Cor", "2PE": "2Pet", "2TI": "2Tim", "ACT": "Acts",
    "EPH": "Eph", "HEB": "Heb", "JHN": "John", "LUK": "Luke", "MAT": "Matt",
    "PHM": "Phlm", "ROM": "Rom"
}