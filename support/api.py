#!/usr/bin/python3
'''
File name:      api.py
Author:         Wessel Poelman (S2976129)
Date:           21-11-2020
Description:    This is the web api used for annotating / validating
                the decisions of the system. If you want to use this,
                make sure to edit the config values (or insert the
                info directly into the code), set debug to false and
                upload this file with a prefilled db file. The db can
                be created using 'select_data_for_validation.py'.

                A skeleton html file is provided. You need to add the
                API url to that file and (optionally) add some styling.

Usage:          python3 api.py
'''

import os

from flask import Flask
from flask_cors import CORS
from flask_restful import (Api, Resource, abort, fields, marshal_with,
                           reqparse, request)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func

from config import Config

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{Config.VALIDATION_DB}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
api = Api(app)
db = SQLAlchemy(app)

if not os.path.isfile(Config.VALIDATION_DB):
    raise FileNotFoundError(
        f'Database not found at {Config.VALIDATION_DB}. \
        This db can be created with \'select_data_for_validation.py\''
    )


class ValidationModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Output from the system
    entity = db.Column(db.String(255), nullable=False)
    extract = db.Column(db.Text)
    score = db.Column(db.Numeric)
    with_explanation = db.Column(db.Text, nullable=False)
    with_explanation_raw = db.Column(db.Text, nullable=False)
    without_explanation = db.Column(db.Text, nullable=False)
    system_decision = db.Column(db.String(20), nullable=False)
    system_choice = db.Column(db.String(20), nullable=False)

    # Validation counts
    total_with_explanation = db.Column(db.Integer, default=0)
    total_without_explanation = db.Column(db.Integer, default=0)
    total_validations = db.Column(db.Integer, default=0)


validation_put_args = reqparse.RequestParser()
validation_put_args.add_argument(
    'id',
    type=int,
    help='The id of the validation is required',
    required=True,
)
validation_put_args.add_argument(
    'choice',
    type=str,
    help='The choice for the validation is required',
    required=True,
)

validation_fields = {
    'id': fields.Integer,
    'with_explanation': fields.String,
    'without_explanation': fields.String,
}


class Validation(Resource):
    @marshal_with(validation_fields)
    def get(self):
        # This makes sure someone doesn't get the same validation
        # two times in a row and IAA can be calculated.
        last_id = request.args.get('last', default=None, type=int)

        result = ValidationModel \
            .query \
            .filter(
                ValidationModel.total_validations < 2,
                ValidationModel.id != last_id
            ) \
            .order_by(func.random()) \
            .first()

        return result

    def post(self):
        values = validation_put_args.parse_args()
        validation = ValidationModel \
            .query \
            .filter_by(id=values['id']) \
            .first()

        if not validation:
            abort(404, message='The validation id is invalid')

        if values['choice'] not in ['with', 'without']:
            abort(422, message='The provided choice is invalid')

        if values['choice'] == 'with':
            validation.total_with_explanation += 1

        if values['choice'] == 'without':
            validation.total_without_explanation += 1

        validation.total_validations += 1

        db.session.commit()


api.add_resource(Validation, '/validation')

if __name__ == "__main__":
    app.run(debug=True)
