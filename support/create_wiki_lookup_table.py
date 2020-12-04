#!/usr/bin/python3
'''
File name:      create_wiki_lookup_table.py
Author:         Wessel Poelman (S2976129)
Date:           06-11-2020
Description:    This script creates an efficient cache for looking up
                a Wikipedia link for a given DBPedia resource / entity.
                For an example file see:
                    https://wiki.dbpedia.org/services-resources
                    /datasets/previous-releases/data-set-30

                See 'Links to Wikipedia Article'. This is either a txt or csv.

Usage:          python create_wiki_lookup_table.py
'''


import csv
import pickle
import sys

from config import Config


def main():
    filepath = Config.DBPEDIA_TO_WIKI

    lookup = {}

    # The first column in the csv is the resource string,
    # the second the Wikipedia origin
    # the third is the link to that entity
    if filepath.endswith('.csv'):
        with open(filepath, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                lookup[row[0]] = row[2]

    # The first 'column' in textfile is the resource string,
    # the second the Wikipedia origin (which I assume is always wikipage-nl)
    # the third is the link to that entity
    if filepath.endswith('.txt'):
        with open(filepath, 'r', encoding='utf8') as f:
            for line in f.readlines():
                row = line.strip().split()
                row[0] = row[0].replace('<http://', '<http://nl.')
                lookup[row[0]] = row[2]

    with open(Config.WIKI_LOOKUP_PICKLE, 'wb') as o:
        pickle.dump(lookup, o)

    print(
        f'Created DBPedia to Wikipedia lookup table with \
        {len(lookup)} entries'
    )


if __name__ == "__main__":
    main()
