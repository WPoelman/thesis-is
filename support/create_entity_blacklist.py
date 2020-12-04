#!/usr/bin/python3
'''
File name:      create_entity_blacklist.py
Author:         Wessel Poelman (S2976129)
Date:           19-11-2020
Description:    This script creates a blacklist of very common
                named entities. This list tries to capture
                'common knowledge' and is used in the decision
                of when an explanation is needed.

                The script 'create_entity_counts.py' produces a
                pickle file that this script needs.

Usage:          python create_entity_blacklist.py
'''


import pickle
import sys
from collections import Counter

from config import Config


def main():
    # The entity counts file consists of a Counter
    # which means tuples of (<entity string>, <count>)
    with open(Config.ENTITY_COUNTS_PICKLE, 'rb') as f:
        entity_counts = pickle.load(f)

    # This makes a blacklist of the top 1% entities.
    # On the DutchWebCorpus this means roughly a
    # cutoff at 118 mentions of that entity in the
    # corpus. This captures a lot of obvious cases
    # such as 'Amsterdam' with a huge 135706 mentions.
    top_counts = entity_counts.most_common(
        int(len(entity_counts.keys()) * 0.01)
    )

    top_entities = {e[0] for e in top_counts}

    # We dump this as a set of strings because we only
    # want to know (fast) membership and the counts do not matter
    # in the linking itself, only here.
    with open(Config.ENTITY_BLACKLIST_PICKLE, 'wb') as f:
        pickle.dump(top_entities, f)

    # For debugging and to see what is happening, we also
    # create a raw txt file of the blacklist
    with open(Config.ENTITY_BLACKLIST_RAW, 'w', encoding='utf8') as f:
        f.writelines([f'{e}\n' for e in top_entities])

    print(
        f'Created blacklist pickle and txt file with \
        {len(top_entities)} entities.'
    )


if __name__ == '__main__':
    main()
