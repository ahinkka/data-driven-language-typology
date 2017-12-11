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

from dlt import thresholded_phoneme_map
from dlt.datatypes.ngram import TokenMappingTypeWriter, TokenMappingMissingCandidatesTypeWriter
from ngram.models import UnigramModel
from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        model_inputs = self.info.get_input("models")

        models = {}
        lang_names = {}
        for model_input in model_inputs:
            language = model_input.module.module_variables["lang_code"]
            lang_names[language] = model_input.module.module_variables["lang"]
            with codecs.open(model_input.absolute_path, 'r', encoding='utf-8') as f:
                models[language] = UnigramModel.read_from_file(f)

        self.log.info(u'Read in {} unigram distributions, languages: {}'
                      .format(len(models.keys()), u', '.join(models.keys())))

        self.log.info(u'Reading in phoneme mappings...')
        phoneme_similarities = thresholded_phoneme_map.read_phoneme_similarities(
            self.info.options["phoneme_similarity_mapping_path"])
        self.log.info(u'Read in {} phoneme mappings'.format(len(phoneme_similarities)))

        lang_pair_mappings = {} # key: (l1, l2), values: (char, char)
        lang_pair_missing_candidates = {} # key: (l1, l2), values: (char, (char, phon. sim, a_freq, b_freq))
        for l1, m1 in models.iteritems():
            for l2, m2 in models.iteritems():
                if l1 == l2:
                    continue

                self.log.info(u'Finding mappings from {} to {}...'.format(lang_names[l1], lang_names[l2]))

                mappings, missing_candidates = thresholded_phoneme_map.find_most_probable_mappings(
                    m1.token_probabilities, m2.token_probabilities,
                    phoneme_similarities,
                    self.info.options["p_diff_threshold"],
                    self.info.options["min_replacement_p"],
                    self.info.options["min_phoneme_similarity"],
                    self.log,
                    lang_a_name=l1, lang_b_name=l2)

                if len(mappings) == 0:
                    self.log.info('No mappings from {} to {}'.format(l1, l2))
                for mapping in mappings:
                    self.log.info(u'{} in {} mapped to {} in {}'
                                  .format(mapping[0], lang_names[l1], mapping[1], lang_names[l2]))
                lang_pair_mappings[(l1, l2)] = mappings
                lang_pair_missing_candidates[(l1, l2)] = missing_candidates

        with TokenMappingTypeWriter(self.info.get_absolute_output_dir("mappings")) as writer:
            writer.mappings = lang_pair_mappings

        with TokenMappingMissingCandidatesTypeWriter(self.info.get_absolute_output_dir("missing_candidates")) as writer:
            writer.missing_candidates = lang_pair_missing_candidates
