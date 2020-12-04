#!/usr/bin/python3
'''
File name:      analysis.py
Author:         Wessel Poelman (S2976129)
Date:           02-12-2020
Description:    This script generates an txt file with measures
                using the (filled) sqlite database from 'api.py'.

Usage:          python analysis.py <path_to_database>
'''

import random
import sqlite3
import sys
from datetime import datetime

import pandas as pd
from sklearn.metrics import cohen_kappa_score


def split_items(items):
    '''
    Not the prettiest, but we need to transform counts to labels:
        - 0 means both chose *the other label*
        - 1 means both chose another label
        - 2 means both chose *this* label

    Since it is Cohens Kappa, the labels do not matter, but when
    provided with the 'with' list, this generates the correct labels
    for all double annotations.
    '''
    x, y = [], []

    for i in items:
        if i == 0:
            x.append('without')
            y.append('without')

        if i == 1:
            x.append('with')
            y.append('without')

        if i == 2:
            x.append('with')
            y.append('with')

    return x, y


def main():
    try:
        database_path = sys.argv[1]
    except ValueError:
        print(__doc__)
        exit()

    connection = sqlite3.connect(database_path)
    df = pd.read_sql_query(
        "SELECT * FROM validation_model WHERE total_validations != 0",
        connection
    )
    connection.close()

    # 'm' means 'mask', these help with the readability of the boolean indexing
    m_context = (df.system_choice == 'CONTEXT')
    m_knowledge = (df.system_choice == 'COMMON_KNOWLEDGE')
    m_with = (df.system_decision == 'with')
    m_without = (df.system_decision == 'without')

    total_sentences = df.shape[0]
    total_with = df[m_with].shape[0]
    total_without = df[m_without].shape[0]
    total_context_with = df[m_context & m_with].shape[0]
    total_context_without = df[m_context & m_without].shape[0]
    total_knowledge_with = df[m_knowledge & m_with].shape[0]
    total_knowledge_without = df[m_knowledge & m_without].shape[0]

    total_annotations = df.total_validations.sum()
    total_ann_with = df.total_with_explanation.sum()
    total_ann_without = df.total_without_explanation.sum()

    # These are the annotations grouped by the system decisions (a)ll
    total_ann_with_a = df[m_with].total_with_explanation.sum()
    total_ann_without_a = df[m_without].total_without_explanation.sum()
    per_with_agree_a = total_ann_with_a / total_with
    per_without_agree_a = total_ann_without_a / total_without

    # These are the annotations grouped by the system decisions AND choices
    # with (c)ontext and (k)nowledge
    total_ann_with_c = df[m_with & m_context].total_with_explanation.sum()
    total_ann_without_c = df[m_without &
                             m_context].total_without_explanation.sum()
    per_with_agree_c = total_ann_with_c / total_context_with
    per_without_agree_c = total_ann_without_c / total_context_without

    total_ann_with_k = df[m_with & m_knowledge].total_with_explanation.sum()
    total_ann_without_k = df[m_without &
                             m_knowledge].total_without_explanation.sum()
    per_with_agree_k = total_ann_with_k / total_knowledge_with
    per_without_agree_k = total_ann_without_k / total_knowledge_without

    all_double_with = list(
        df[df.total_validations > 1].total_with_explanation
    )

    a, b = split_items(all_double_with)

    output = f'''
{{
    'database_used': {database_path},
    'created_measures_at': {datetime.now()},
    'system_counts': {{
        'total_sentences': {total_sentences},
        'total_with': {total_with},
        'total_without': {total_without},
        'total_context_with': {total_context_with},
        'total_context_without': {total_context_without},
        'total_knowledge_with': {total_knowledge_with},
        'total_knowledge_without': {total_knowledge_without},
    }},
    'annotation_counts': {{
        'total_annotations': {total_annotations},
        'total_ann_with': {total_ann_with},
        'total_ann_without': {total_ann_without},
        'total_ann_with_a': {total_ann_with_a},
        'total_ann_without_a': {total_ann_without_a}
        'total_ann_with_c': {total_ann_with_c},
        'total_ann_without_c': {total_ann_without_c}
        'total_ann_with_k': {total_ann_with_k}
        'total_ann_without_k': {total_ann_without_k}
    }},
    'percentage_agree_all': {{
        'per_with_agree_a': {per_with_agree_a},
        'per_without_agree_a': {per_without_agree_a},
    }},
    'percentage_agree_context': {{
        'per_with_agree_c': {per_with_agree_c},
        'per_without_agree_c': {per_without_agree_c},
    }},
    'percentage_agree_knowledge': {{
        'per_with_agree_k': {per_with_agree_k},
        'per_without_agree_k': {per_without_agree_k},
    }},
    'cohens_kappa': {cohen_kappa_score(a, b)}
}}
    '''

    with open(f'measures{random.randint(0, 100000)}.txt', 'w') as f:
        f.write(output)

    print(output)


if __name__ == '__main__':
    main()
