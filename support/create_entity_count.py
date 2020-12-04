#!/usr/bin/python3
'''
File name:      create_entity_count.py
Author:         Wessel Poelman (S2976129)
Date:           19-11-2020
Description:    This script counts all entities recognized by spacy.
                This is used to create the blacklist in
                'create_entity_blacklist.py'

                As a default it assumes the usage of the 'raw' txt files
                from the DutchWebCorpus. It loops trough all txt files
                in the folder.

Usage:          python create_entity_count.py <path_to_raw_folder>
'''


import os
import pickle
import sys
from collections import Counter
from multiprocessing import cpu_count

import spacy

from config import Config


def main():
    try:
        folder_path = sys.argv[1]
    except ValueError:
        print(__doc__)
        exit()

    # I experienced some memory errors occasionally
    # this can help with manually trying again without
    # repeating the same file.
    # seen = set([
    #     '0.txt',
    #     '1.txt',
    #     '2.txt',
    #     '3.txt',
    #     '4.txt',
    #     '5.txt',
    #     '6.txt',
    #     '7.txt',
    #     '8.txt',
    #     '9.txt',
    #     '10.txt',
    #     '11.txt',
    #     '12.txt',
    #     '13.txt',
    #     '14.txt',
    #     '15.txt',
    #     '16.txt',
    #     '17.txt',
    #     '18.txt',
    #     '19.txt',
    # ])
    seen = set()

    total_files = [
        x for x in list(os.scandir(folder_path))
        if x.is_file() and
        x.path.endswith('.txt') and
        x.name not in seen
    ]
    total_files_count = len(total_files)

    print(
        f'Found {total_files_count} text \
        files: {[x.name for x in total_files]}'
    )

    print('Loading spacy...')

    # We only need the NER tagger, with everything enabled it is much slower
    nlp = spacy.load(Config.SPACY_MODEL, disable=['parser', 'tagger'])

    entity_counts = Counter()

    if not os.path.isfile(Config.ENTITY_COUNTS_PICKLE):
        with open(Config.ENTITY_COUNTS_PICKLE, 'wb') as f:
            pickle.dump(entity_counts, f)

    for i, raw_file in enumerate(total_files):
        print(
            f'Counting entities in file {raw_file.name} \
            ({i + 1} / {total_files_count})'
        )
        # Because this process takes a long time (about 1.5 hours on
        # a 6 core 12 thread 16GB machine) we save the progress per file,
        # so if something goes wrong, we have not lost all progress.
        with open(Config.ENTITY_COUNTS_PICKLE, 'rb') as o:
            entity_counts = pickle.load(o)

        # We need to process the files using the pipe() to batch chunks,
        # otherwise it gets loaded into memory and with an average size
        # of 100mb combined with the already high memory usage of spacy
        # this is way too much.
        with open(raw_file.path, 'r', encoding='utf8') as f:
            for j, doc in enumerate(nlp.pipe(f, n_process=cpu_count() - 1)):
                for entity in doc.ents:
                    entity_counts[entity.text.lower()] += 1

                j % 500 == 0 and print(f'Processing line {j}', end='\r')

        print(f'\rFound {len(entity_counts.keys())} so far')

        with open(Config.ENTITY_COUNTS_PICKLE, 'wb') as o:
            pickle.dump(entity_counts, o)

        # This again just helps with the occasional crashes
        seen.add(raw_file.name)
        print(f'Seen files: {seen}')

    print(
        f'Counted all entities in corpus, totalling \
        {len(entity_counts.keys())}'
    )


if __name__ == '__main__':
    main()
