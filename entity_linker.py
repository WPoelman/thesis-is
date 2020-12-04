import json
import os
import pickle

import requests
import spacy
import spotlight

from support.config import Config
from utils import *


class EntityLinkerStatus():
    ''' Status used for EntityLinker class'''
    OK = 'OK'
    NO_ENTITIES = 'NO_ENTITIES'


class EntityLinkerChoice():
    ''' Reason for a giving an "is needed" score '''
    CONTEXT = 'CONTEXT'
    COMMON_KNOWLEDGE = 'COMMON_KNOWLEDGE'
    ERROR = 'ERROR'


class EntityLinkerException(Exception):
    ''' Base exception used for EntityLinker class '''
    pass


class EntityLinker:
    """
    A class used to get DBPedia and Wikipedia info about entities
    recognized by Spotlight in a text and maybe annotate them with
    explanations if needed.
    """

    def __init__(
        self,
        verbose=False,  # Print progress and debug info
        url=Config.SPOTLIGHT_API_URL,  # Default local url
        types=['DBpedia:Name', 'DBpedia:Organisation',
               'DBpedia:Person', 'DBpedia:Place'],  # Best for named entities
    ):
        self.verbose = verbose
        self.verbose and print(
            "Loading caches, spacy and testing connection...", end="\r"
        )

        # --- Spotlight settings ---
        self.url = url
        self.types = ','.join(types)

        # --- Text processing ---
        self.stop_words = load_stop_words()
        self.nlp = spacy.load(Config.SPACY_MODEL, disable=['tagger', 'ner'])

        # --- Cache files ---
        # This is the file used to look up wiki links with a given
        # DBpedia URI, see 'create_wiki_lookup_table.py' for more info
        self.wiki_lookup = load_wiki_lookup()

        self.entity_blacklist = load_entity_blacklist()

        # There are a lot of entities that occur multiple times in the texts
        # because of this and because we don't want to 'abuse' the wikipedia
        # api, we chache the responses. It is also considerably faster!
        self.explanation_cache = load_or_create_expl_cache()

        # Highlight tags for the explanation used in validation
        self.h_start = '<span class="annotation">'
        self.h_end = '</span>'

        # --- After setup ---
        self.__test_connection()

    def find(self, text, confidence=0.4):
        '''
        Finds entities in a given text using DBpedia Spotlight and returns
        a dictionary with information about the entity from Spotlight and
        Wikipedia. The dictionary is structured as follows:

            response = {
                'entities': {
                    <surface form entity>: {
                        'dbpedia': <spotlight annotation json response>,
                        'wikipedia': <wikipedia api summary json response>,
                    }
                }
                'status': <EntityLinkerStatus>,
            }
        '''
        response = {
            'entities': {},
            'status': EntityLinkerStatus.NO_ENTITIES,
        }

        try:
            # This small wrapper library cleans the json keys we
            # get back from spotlight, but it also throws an exception
            # when no entities are found
            result = spotlight.annotate(
                self.url,
                text,
                filters={
                    # The default confidence might seem low, but Spotlight
                    # is pretty strict with high confidences and there were
                    # not that many errors.
                    'confidence': confidence,
                    'types': self.types,
                }
            )
        except (spotlight.SpotlightException, requests.exceptions.HTTPError):
            return response

        seen = set()

        for entity_data in result:
            try:
                link = self.wiki_lookup[f'<{entity_data["URI"]}>']

                # We only want to find information about an entity once
                if link in seen:
                    continue

                seen.add(link)
            except KeyError:
                continue

            wiki_title = extract_wiki_title(link)

            if wiki_title in self.explanation_cache.keys():
                wiki_data = self.explanation_cache[wiki_title]

                self.verbose and print(
                    f'FROM CHACHE {wiki_title}', end='\r'
                )
            else:
                wiki_data = requests.get(
                    f"{Config.WIKI_API_URL}{wiki_title}"
                ).json()

                self.verbose and print(
                    f'FROM WIKI {wiki_title}', end='\r'
                )

                self.explanation_cache[wiki_title] = wiki_data
                self.__update_explanation_cache()

            response['entities'][entity_data['surfaceForm']] = {
                'dbpedia': entity_data,
                'wikipedia': wiki_data,
            }

        return {**response, 'status': EntityLinkerStatus.OK}

    def annotate(self, result, raw_text, threshold=0.5):
        '''
            Annotates the given text with all entities that get a score
            *below* the given threshold. It also creates some metadata
            about the descision process wich gives insight in how the
            system works, just from the output data. Metadata is used for
            humnan validation of the system.

            Returns the following dictionary structure:

            {
                'input_text': <raw input text>,
                'output_text': <raw annotated output text,
                                possibly with explanations>,
                'annotated_entities': <entity_list>,
                'ignored_entities': <entity_list>,
            }

            entity_list = [
                {
                    'entity': <surface form of the entity>,
                    'explanation': <raw explanation used>,
                    'extract': <raw fist sentence of extract used>,
                    'score': <score given for needed or not>,
                    'choice': <EntityLinkerChoice>,
                    'context_with_explanation':
                        <sentence with entity,
                         possibly with surrounding context>,
                    'context_with_explanation':
                        <sentence with entity,
                         possibly with surrounding context>,
                    'context_highlighted':
                        <sentence with entity and highlighted
                         explanation, possibly with surrounding context>,
                },
                ...
            ]
        '''
        doc_sents = list(self.nlp(raw_text).sents)

        explanation_needed = []
        explanation_not_needed = []

        annotated_text = raw_text
        shift = 0

        for entity, entity_result in result['entities'].items():
            # Wikipedia sometimes returns other stuff than listed in the
            # api documentation, to go on with the rest we need to be sure
            # the important fields are present.
            if ('description' not in entity_result['wikipedia'].keys()
                    or 'extract' not in entity_result['wikipedia'].keys()):
                continue

            # Sometimes the fields are present, but empty
            if (len(entity_result['wikipedia']['description']) == 0
                    or len(entity_result['wikipedia']['extract']) == 0):
                continue

            # The first sentence of a Wikipedia article is the most direct
            # explanation of the entity, so we use that one for similarity
            extract = list(
                self.nlp(entity_result['wikipedia']['extract']).sents
            )[0]
            explanation = self.nlp(entity_result['wikipedia']['description'])
            explanation_formatted = f" ({explanation.text})"

            context_dict = self.__get_context(entity, doc_sents)

            context_with_explanation = insert(
                context_dict['context_raw'],
                explanation_formatted,
                context_dict['context_raw'].find(entity) + len(entity)
            )

            # This is a bit hacky, but if we let the front end do it, we run
            # into trouble when there are multiple brackets in the sentence.
            # We could do some fancy regex or string manipulation, this is
            # the most straightforward method.
            context_highlighted = insert(
                context_dict['context_raw'],
                f' {self.h_start}{explanation_formatted.strip()}{self.h_end}',
                context_dict['context_raw'].find(entity) + len(entity)
            )

            (score, choice) = self.get_is_needed_score(
                entity,
                context_dict,
                extract,
                explanation
            )

            full_entity_data = {
                'entity': entity,
                'explanation': explanation.text,
                'extract': extract.text,
                'score': score,
                'choice': choice,
                'context_with_explanation': context_with_explanation,
                'context_without_explanation': context_dict['context_raw'],
                'context_highlighted': context_highlighted,
            }

            if (score > threshold):
                explanation_not_needed.append(full_entity_data)
                continue

            explanation_needed.append(full_entity_data)

            # Account for previous entities and the current for
            # the right position (just after the entity)
            offset = entity_result['dbpedia']['offset']
            annotated_text = insert(annotated_text, explanation_formatted,
                                    (offset + shift + len(entity)))

            shift += len(explanation_formatted)

        self.verbose and print(
            f"'\x1b[2K\r'Needed: {len(explanation_needed)} \
            Not needed: {len(explanation_not_needed)}",
            end='\r'
        )

        return {
            'input_text': raw_text,
            'output_text': annotated_text,
            'annotated_entities': explanation_needed,
            'ignored_entities': explanation_not_needed,
        }

    def get_is_needed_score(
        self,
        entity,  # Raw string of entity
        context,  # Dict with spacy spans of context info
        extract,  # Raw string of first wiki extract sentence
        explanation,  # Raw string of explanation
        explanation_weight=0.7,
        extract_weight=0.3,
    ):
        '''
            Calculates a score with a max of 1. 1 being not needed and 0,
            or in rare occasions < 0, definitely needed. Uses the
            'common knowledge' blacklist or the entity context combined with
            the explanation and first sentence of the wiki summary to determine
            the score.

            Returns a tuple with:
                (score<float>, choice<EntityLinkerChoice>)
        '''
        # This happens when spacy makes a mistake with the sentence
        # boundaries it only happens once every 3000 articles or so
        # so we just skip it to avoid mistakes
        if len(context['sentence']) == 0:
            return (1.0, EntityLinkerChoice.ERROR)

        if entity.lower() in self.entity_blacklist:
            return (1.0, EntityLinkerChoice.COMMON_KNOWLEDGE)

        clean_sentences = [
            self.__clean_sentence(context[context_type], entity)
            for context_type in ['left', 'sentence', 'right']
            if len(context[context_type]) > 0
        ]

        extract = self.__clean_sentence(extract, entity)
        explanation = self.__clean_sentence(explanation, entity)

        explanation_sum = sum([
            s.similarity(explanation)
            for s in clean_sentences]) if len(explanation.text) > 0 else 0

        extract_sum = sum([
            s.similarity(extract)
            for s in clean_sentences]) if len(extract.text) > 0 else 0

        # In all the hundres of thousands of articles I never saw 0
        # clean sentences so a theoretical divide by zero should not happen.
        avg_explanation_sim = explanation_sum / len(clean_sentences)
        avg_extract_sim = extract_sum / len(clean_sentences)

        # The default weights are somewhat arbitrary, but since the
        # explanation is inserted into the text, we want to avoid
        # a high similarity there. The extract is a lot more detailed
        # and thus more prone to noise affecting the similarity,
        # which is why the weight is decreased for that one.
        score = (avg_explanation_sim * explanation_weight) + \
                (avg_extract_sim * extract_weight)

        return (score, EntityLinkerChoice.CONTEXT)

    def __clean_sentence(self, sentence, entity):
        ''' Cleans stop words, unknown words and the entity itself '''
        return self.nlp(
            ' '.join([
                w.text for w in sentence
                if w.text.lower() not in self.stop_words
                and w.text != entity
                and w.has_vector
            ])
        )

    def __get_context(self, entity, doc_sents):
        '''
            Gets the context of a given entity in the text. In this case
            that is 1 sentence left and one right if they exist.
        '''
        # We want to find the sentence the entity occurs in for the first time.
        # This is a bit inefficient because we theoretically need to loop
        # through all the sentences every time. However, we do not know where
        # the entity is in the parsed sentences. Could be better, but this does
        # ensure the entity is only evaluated the first time it is seen,
        # which is what we want.
        sentence, left, right = '', '', ''

        for i, sent in enumerate(doc_sents):
            if entity in sent.text:
                sentence = sent
                left = '' if i == 0 else doc_sents[i - 1]
                right = '' if i + 1 == len(doc_sents) \
                    else doc_sents[i + 1]
                break

        context_raw = f'{left} {sentence} {right}'.strip()

        return {
            'left': left,
            'sentence': sentence,
            'right': right,
            'context_raw': context_raw,
        }

    def __test_connection(self):
        ''' Checks if Spotlight is running '''
        response = requests.get(self.url, params={'text': "test"})

        if response.status_code != 200:
            raise EntityLinkerException(
                f'Spotlight appears to be unreachable. \
                Is the server running and is the url \'{self.url}\' correct?'
            )

        self.verbose and print(f"Spotlight found at {self.url}")

    def __update_explanation_cache(self):
        ''' Updates the wiki explanations cache if needed '''
        with open(Config.EXPLANATION_CACHE, 'wb') as o:
            pickle.dump(self.explanation_cache, o)
