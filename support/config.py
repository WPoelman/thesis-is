from pathlib import Path


class Config():
    '''
    Config used by scripts to locate files and constants.
    '''
    # --- General ---
    SPACY_MODEL = 'nl_core_news_lg'

    WIKI_API_URL = 'https://nl.wikipedia.org/api/rest_v1/page/summary/'

    # Default local url for Dutch Model
    SPOTLIGHT_API_URL = 'http://0.0.0.0:2232/rest/annotate'

    # --- Filepaths ---
    DATA_FOLDER = Path(f'{__file__}').parent.parent / 'data'

    OUTPUT_RAW = DATA_FOLDER / 'out.txt'

    # Credits stopwords: https://eikhart.com/nl/blog/moderne-stopwoorden-lijst
    STOP_WORDS_RAW = DATA_FOLDER / 'stopwoorden.txt'

    EXPLANATION_CACHE = DATA_FOLDER / 'explanation_cache.pickle'

    DBPEDIA_TO_WIKI = DATA_FOLDER / 'dbpedia_to_wiki.txt'

    WIKI_LOOKUP_PICKLE = DATA_FOLDER / 'wiki_lookup_table.pickle'

    ENTITY_COUNTS_PICKLE = DATA_FOLDER / 'all_entity_counts.pickle'

    ENTITY_COUNTS_CSV = DATA_FOLDER / 'all_entity_counts.csv'

    ENTITY_BLACKLIST_RAW = DATA_FOLDER / 'entity_blacklist.txt'

    ENTITY_BLACKLIST_PICKLE = DATA_FOLDER / 'entity_blacklist.pickle'

    # --- API ---
    VALIDATION_DB = DATA_FOLDER / 'database.db'
