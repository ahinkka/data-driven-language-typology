# -*- coding: utf-8 -*-
#
# Copyright 2016-2017 University of Helsinki.
#
# This file is part of data-driven-language-typology distribution.
#
# data-driven-language-typology is free software: you can
# redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# data-driven-language-typology is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with data-driven-language-typology.  If not, see
# <http://www.gnu.org/licenses/>.
#
import codecs
import sys

import numpy as np

from pimlico.datatypes.dictionary import DictionaryData
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.results import NumericResultWriter
from langsim.datatypes.confusion import ConfusionMatrixWriter
from dlt.phonetic_transcript_tokenizer import token_gen as phoneme_token_gen
from dlt.text_tokenizer import token_gen as text_token_gen
from dlt.kita_tokenizer import token_gen as kita_token_gen
from dlt.utils import read_token_mapping
from ngram.models import TrigramModel, TrigramModelPerplexitySink, BigramModel, UnigramModel, \
    DeletedInterpolationTrigramModel, TrigramModelKitaDistanceSink


_is_pypy = '__pypy__' in sys.builtin_module_names


def model_pimlico_vocabulary(model):
    token2id = {}
    for index, item in enumerate(sorted(model.vocabulary)):
        token2id[item] = index
    result = DictionaryData()
    result.token2id = token2id
    return result


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        ug_model = self.info.get_input("unigram_model")
        bg_model = self.info.get_input("bigram_model")
        tg_model = self.info.get_input("trigram_model")
        corpus = self.info.get_input("corpus")
        corpus_ug_model = self.info.get_input("corpus_unigram_model")
        corpus_bg_model = self.info.get_input("corpus_bigram_model")
        corpus_tg_model = self.info.get_input("corpus_trigram_model")
        token_mapping = self.info.get_input("token_mapping")
        token_type = self.info.options["token_type"]
        token_count = self.info.options["count"]
        interpolation_method = self.info.options["interpolation_method"]
        additive_smoothing = self.info.options["additive_smoothing"]
        additive_smoothing_a = self.info.options["additive_smoothing_a"]
        distance_measure = self.info.options["distance_measure"]

        with codecs.open(corpus_ug_model.absolute_path, 'r', encoding='utf-8') as f:
            corpus_vocabulary = UnigramModel.read_from_file(f).vocabulary
        with codecs.open(ug_model.absolute_path, 'r', encoding='utf-8') as f:
            original_unigram_model = UnigramModel.read_from_file(f)
            model_vocabulary = original_unigram_model.vocabulary
        shared_vocabulary = corpus_vocabulary | model_vocabulary

        with codecs.open(ug_model.absolute_path, 'r', encoding='utf-8') as f:
            unigram_model = UnigramModel.read_from_file(f, additional_vocabulary=shared_vocabulary,
                                                        additive_smoothing=additive_smoothing,
                                                        additive_smoothing_a=additive_smoothing_a)

        with codecs.open(corpus_ug_model.absolute_path, 'r', encoding='utf-8') as f:
            corpus_unigram_model = UnigramModel.read_from_file(f, additional_vocabulary=shared_vocabulary,
                                                               additive_smoothing=additive_smoothing,
                                                               additive_smoothing_a=additive_smoothing_a)

        with codecs.open(bg_model.absolute_path, 'r', encoding='utf-8') as f:
            bigram_model = BigramModel.read_from_file(f, additional_vocabulary=shared_vocabulary)

        with codecs.open(corpus_bg_model.absolute_path, 'r', encoding='utf-8') as f:
            corpus_bigram_model = BigramModel.read_from_file(f, additional_vocabulary=shared_vocabulary)

        with codecs.open(tg_model.absolute_path, 'r', encoding='utf-8') as f:
            trigram_model = TrigramModel.read_from_file(f, additional_vocabulary=shared_vocabulary)

        with codecs.open(corpus_tg_model.absolute_path, 'r', encoding='utf-8') as f:
            corpus_trigram_model = TrigramModel.read_from_file(f, additional_vocabulary=shared_vocabulary)

        model_language = tg_model.module.module_variables["lang_code"]

        corpus_language = corpus.module.module_variables["lang_code"]
        with codecs.open(token_mapping.absolute_path, 'r', encoding='utf-8') as f:
            token_map = {v: k
                         for k, v in read_token_mapping(f).get((model_language, corpus_language), {}).iteritems()}

        if token_type == "text":
            tokenizer = text_token_gen
        elif token_type == "phonemes":
            tokenizer = phoneme_token_gen
        elif token_type == "kita":
            tokenizer = kita_token_gen
        else:
            raise Exception("Unknown token type: {}".format(token_type))

        if interpolation_method == "deleted":
            eff_tg_model = DeletedInterpolationTrigramModel(trigram_model, bigram_model, unigram_model)
            eff_corpus_tg_model = DeletedInterpolationTrigramModel(corpus_trigram_model, corpus_bigram_model,
                                                                   corpus_unigram_model)
        else:
            eff_tg_model = trigram_model
            eff_corpus_tg_model = corpus_trigram_model

        if distance_measure == "perplexity":
            sink = TrigramModelPerplexitySink(eff_tg_model, substitution_map=token_map)
        elif distance_measure == "kita":
            sink = TrigramModelKitaDistanceSink(eff_tg_model, eff_corpus_tg_model, substitution_map=token_map)

        docs_processed = 0
        lines_processed = 0
        tokens_processed = 0
        docs_skipped = 0
        for doc_name, doc_text in corpus:
            self.log.debug(u"Processing {}".format(doc_name))
            if isinstance(doc_text, InvalidDocument):
                self.log.debug(u"Skipping document {}: {}".format(doc_name, doc_text))
                docs_skipped += 1
                continue

            for line in doc_text:
                for token in tokenizer(line):
                    sink.handle(token)
                    tokens_processed += 1
                    if tokens_processed >= token_count:
                        break
                if tokens_processed >= token_count:
                    break
                lines_processed += 1
            if tokens_processed >= token_count:
                break
            docs_processed += 1

        self.log.info(u"{} documents skipped".format(docs_skipped))
        self.log.info(u"{} documents, {} lines and {} tokens processed"
                      .format(docs_processed, lines_processed, tokens_processed))

        if tokens_processed < token_count:
            raise Exception("Not enough tokens found")

        distance = sink.distance()
        self.log.info(u"Distance ({}): {}".format(distance_measure, distance))

        with NumericResultWriter(self.info.get_absolute_output_dir("distance")) as writer:
            writer.result = distance
            writer.label = distance_measure

        # Confusion matrix
        with ConfusionMatrixWriter(self.info.get_absolute_output_dir("confusion_matrix")) as writer:
            model_vocab = model_pimlico_vocabulary(original_unigram_model)
            writer.store_vocab(model_vocab)

            # Initialize a regular Python list of lists for PyPy, numpy array for CPython. Numpy array access is
            # significantly slower in PyPy than regular Python lists. This results in a speedup of about 5x.
            rows = len(model_vocab) + 1
            cols = len(model_vocab) + 2
            if _is_pypy:
                conf_mat = []
                for i in xrange(rows):
                    row = []
                    for j in xrange(cols):
                        row.append(0.0)
                    conf_mat.append(row)

            else:
                conf_mat = np.zeros((rows, cols), dtype=np.float32)
            oov = len(model_vocab)

            for transition, count in sink.transition_count.iteritems():
                ctx1, ctx2, target = transition
                ctx1 = token_map.get(ctx1, ctx1)
                ctx2 = token_map.get(ctx2, ctx2)
                target = token_map.get(target, target)
                target_id = model_vocab.token2id.get(target, oov)
                for item, id in model_vocab.token2id.iteritems():
                    probability = eff_tg_model.probability((ctx1, ctx2, item), missing_value=None)
                    if probability is None:
                        probability = eff_tg_model.probability((ctx1, ctx2, item))
                        # conf_mat[target_id, oov] += count * probability
                        conf_mat[target_id][oov] += count * probability
                    else:
                        # self.log.info(u'{}\t{}\t{}\t{}\t{}'.format(target, target_id, id, count, probability))
                        # conf_mat[target_id, id] += count * probability
                        conf_mat[target_id][id] += count * probability

            if _is_pypy:
                _conf_mat = np.zeros((rows, cols), dtype=np.float32)
                for i, row in enumerate(conf_mat):
                    for j, item in enumerate(row):
                        _conf_mat[i, j] = item
            else:
                _conf_mat = conf_mat

            writer.store_matrix(_conf_mat)
