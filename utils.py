import os
import pickle

from support.config import Config


def insert(in_string, to_be_inserted, i):
    return f'{in_string[:i]}{to_be_inserted}{in_string[i:]}'


def load_stop_words(path=Config.STOP_WORDS_RAW):
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Stop words not found at {path}"
        )

    with open(path, 'r', encoding="utf8") as f:
        # Using a Set here is faster than a list because we
        # only want to know membership
        stop_words = {w.strip() for w in f.readlines()}
    return stop_words


def load_entity_blacklist(path=Config.ENTITY_BLACKLIST_PICKLE):
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Entity blacklist not found at {path}"
        )

    with open(path, 'rb') as f:
        blacklist = pickle.load(f)
    return blacklist


def load_or_create_expl_cache(path=Config.EXPLANATION_CACHE):
    # Create an empty cache if it is not present
    if not os.path.isfile(path):
        print(
            f'Warning, no explanation cache was found at {path}\
            \nCreating a new one..'
        )
        with open(path, 'wb') as f:
            pickle.dump({}, f)
        return {}

    # Otherwise load the cache and return it
    with open(path, 'rb') as f:
        cache = pickle.load(f)
    return cache


def load_wiki_lookup(path=Config.WIKI_LOOKUP_PICKLE):
    # We need this file to get the correct titles
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Wiki lookup file not found at {path}.\n \
            This file can be created with *create_wiki_lookup_table.py*"
        )

    with open(path, 'rb') as f:
        lookup = pickle.load(f)
    return lookup


def extract_wiki_title(link):
    return link.replace('<http://nl.wikipedia.org/wiki/', '') \
               .replace('>', '')
