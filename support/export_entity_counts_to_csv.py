#!/usr/bin/python3
'''
File name:      export_entity_counts_to_csv.py
Author:         Wessel Poelman (S2976129)
Date:           19-11-2020
Description:    Creates a sorted csv of all entity counts
                to see what is going on.

Usage:          python export_entity_counts_to_csv.py
'''


import csv
import os
import pickle
import sys
from collections import Counter

from config import Config


def main():
    # The entity counts file consists of a Counter
    # which means tuples of (<entity string>, <count>)
    with open(Config.ENTITY_COUNTS_PICKLE, 'rb') as f:
        entity_counts = pickle.load(f)

    with open(Config.ENTITY_COUNTS_CSV, 'w') as csvfile:
        writer = csv.writer(csvfile,
                            delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)

        # Header row
        writer.writerow(['entity', 'count'])

        for entity in entity_counts.most_common(len(entity_counts)):
            writer.writerow([entity[0], entity[1]])

    print(f'Created csv with {len(entity_counts)} rows')


if __name__ == '__main__':
    main()
