#!/usr/bin/python3
'''
File name:      main.py
Author:         Wessel Poelman (S2976129)
Date:           10-11-2020
Description:    This script is the entry point for annotating named
                entities in a text with explanations.

Usage:          python3 main.py <text> -v(erbose) -
'''


import argparse
import csv
import json
import pickle
import sys

import spacy

from entity_linker import EntityLinker, EntityLinkerStatus
from support.config import Config


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-v",
            "--verbose",
            help="Shows detailed process and debug info",
            action="store_true"
        )
        parser.add_argument(
            "-t",
            "--target",
            type=int,
            default=500,
            help="Target of how many 'interesting items' to output. \
                  The choice outputs <target> per explanation needed and \
                  not needed. Default is 500."
        )
        parser.add_argument(
            "path",
            help="Path to corpus file"
        )
        args = parser.parse_args()
    except ValueError:
        print(__doc__)
        exit()

    with open(args.path, 'r', encoding='utf8') as f:
        # This particular splitting assumes the use of a raw
        # DutchWebCorpus txt file!
        test_corpus = [s.replace('\n', ' ') for s in f.read().split('\n\n')]

    e = EntityLinker(verbose=args.verbose)

    # This can help with letting the system create a certain amount of
    # interesing results for validation for example
    count_with, count_without = 0, 0
    target = args.target

    # This writes a JSON string per line to a txt file, not the prettiest
    # but allows for appending, which is hard with plain JSON.
    # To rebuild (part of) the txt file, just read it per line and
    # parse the JSON.
    with open(Config.OUTPUT_RAW, 'a', encoding="utf8") as f:
        for i, text in enumerate(test_corpus):
            if (count_with >= target and count_without >= target):
                args.verbose and print(f'Target of {target} reached.')
                break

            args.verbose and i % 100 == 0 and print(
                f"\rDoc {i} from {len(test_corpus)}"
            )

            found_entities = e.find(text)

            # If we have a file without entities or with other errors
            # we will skip it so the program does not crash
            if found_entities['status'] != EntityLinkerStatus.OK:
                continue

            res = e.annotate(found_entities, text)

            # We only want to find some interesting examples to validate
            if (len(res['ignored_entities']) == 0 and
                    len(res['annotated_entities']) == 0):
                continue

            if len(res['annotated_entities']) != 0:
                count_with += 1
                f.write(f'{json.dumps(res)}\n')
                continue

            if len(res['ignored_entities']) != 0:
                count_without += 1
                f.write(f'{json.dumps(res)}\n')


if __name__ == "__main__":
    main()
