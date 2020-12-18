#!/usr/bin/python3
'''
File name:      select_data_for_validation.py
Author:         Wessel Poelman (S2976129)
Date:           21-11-2020
Description:    Creates a selection of output from the
                system to validate and fills the sqlite
                db with entries to validate (used by 'api.py').

                Warning: This will overwrite any db that is stored
                in the data folder specified in config.py.

Usage:          python select_data_for_validation.py
'''

import json
import os

from api import ValidationModel, db
from config import Config


def main():
    # We are going to select:
    #   500 decided not to explain
    #   500 decided to explain
    #
    # NOTE: this was the initial target, but proved to be way too high.
    # The final database contains a lot less, both to increase the chance
    # of two annotations for the same sample and because a lot more people
    # were needed to annotate this many!
    target = 500
    with_explanation = 0
    without_explanation = 0

    # We are going to overwrite any existing db, so watch out!
    db.create_all()

    # The output lists need to be mapped to the label used in the validation
    db_mapping = {'annotated_entities': 'with', 'ignored_entities': 'without'}

    with open(Config.OUTPUT_RAW, 'r') as output:
        for line in output:
            if with_explanation >= target and without_explanation >= target:
                break

            data = json.loads(line)

            for key, decision in db_mapping.items():
                for ann in data[key]:
                    model = ValidationModel(
                        entity=ann['entity'],
                        extract=ann['extract'],
                        score=ann['score'],
                        with_explanation_raw=ann['context_with_explanation'],
                        with_explanation=ann['context_highlighted'],
                        without_explanation=ann['context_without_explanation'],
                        system_decision=decision,
                        system_choice=ann['choice'],
                    )

                    if (len(data['annotated_entities']) > 0
                            and with_explanation < target):
                        with_explanation += 1
                        db.session.add(model)
                        continue

                    if (len(data['ignored_entities']) > 0
                            and without_explanation < target):
                        without_explanation += 1
                        db.session.add(model)

    db.session.commit()

    print(f'Created sqlite db')


if __name__ == '__main__':
    main()
