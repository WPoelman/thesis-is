# Support
## Contents
### Configuration
- `config.py`: stores file paths for the scripts (does *not* include the corpus path)

### General preprocessing
- `create_wiki_lookup_table.py`: converts DBPedia URI's to valid Wikipedia links / titles, creates `WIKI_LOOKUP_PICKLE`
- `create_entity_count.py`: uses Spacy to count all named entities in the corpus, creates `ENTITY_COUNTS_PICKLE`
- `export_entity_count_to_csv.py`: creates a `ENTITY_COUNTS_CSV` using `ENTITY_COUNTS_PICKLE`
- `create_entity_blacklist.py`: creates `ENTITY_BLACKLIST_RAW` and `ENTITY_BLACKLIST_PICKLE` using `ENTITY_COUNTS_PICKLE`
 
### Validation API
- `select_data_for_validation.py`: creates sqlite database using `OUTPUT_RAW` with all items needed for validating the output
- `api.py`: simple Flask api for storing and retrieving the annotations for validating, uses sqlite db from previous point
- `validation.html`: skeleton html that can be used to access the api

A compressed version of `OUTPUT_RAW` is included in the `data` folder.

The server for the api is hosted at: [https://wpoelman.pythonanywhere.com/validation](https://wpoelman.pythonanywhere.com/validation)

The page for validation is hosted at: [https://wesselpoelman.nl/validation.html](https://wesselpoelman.nl/validation.html)

## Usage
In general the usage is as follows:

`python <script_name> <optional_path_to_raw_corpus_files>`

Detailed information is available at the top in the scripts. The order of the list above is the order that should be followed because `ENTITY_COUNTS_PICKLE` is used by others for example. The csv is optional, but might be helpful to see what is going on. The config can be changed so a different folder with all the data can be used. Be warned that `create_entity_count.py` takes a *long* time and uses a *lot* of system resources.
