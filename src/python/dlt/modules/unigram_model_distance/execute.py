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

from ngram.models import UnigramModel, UnigramModelPerplexitySink
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.results import NumericResultWriter
from pimlico.core.modules.base import BaseModuleExecutor

from dlt.utils import read_token_mapping
from dlt.text_tokenizer import token_gen as text_token_gen
from dlt.phonetic_transcript_tokenizer import token_gen as phoneme_token_gen
from dlt.kita_tokenizer import token_gen as kita_token_gen


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        ug_model = self.info.get_input("unigram_model")
        corpus_ug_model = self.info.get_input("corpus_unigram_model")
        corpus = self.info.get_input("corpus")
        token_mapping = self.info.get_input("token_mapping")
        token_type = self.info.options["token_type"]
        token_count = self.info.options["count"]
        additive_smoothing = self.info.options["additive_smoothing"]
        additive_smoothing_a = self.info.options["additive_smoothing_a"]
        distance_measure = self.info.options["distance_measure"]

        with codecs.open(corpus_ug_model.absolute_path, 'r', encoding='utf-8') as f:
            corpus_unigram_model = UnigramModel.read_from_file(f)

        with codecs.open(ug_model.absolute_path, 'r', encoding='utf-8') as f:
            unigram_model = UnigramModel.read_from_file(f, additive_smoothing=additive_smoothing,
                                                        additive_smoothing_a=additive_smoothing_a,
                                                        additional_vocabulary=corpus_unigram_model.vocabulary)

        model_language = ug_model.module.module_variables["lang_code"]
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

        if distance_measure == "perplexity":
            sink = UnigramModelPerplexitySink(unigram_model, substitution_map=token_map)
        elif distance_measure == "kita":
            raise Exception("kita measure and unigrams not implemented")
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
