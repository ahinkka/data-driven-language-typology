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
from __future__ import print_function

import json

import codecs
import collections
import os
from pimlico.datatypes.files import File
from pimlico.datatypes.base import PimlicoDatatypeWriter


class UnigramFrequencyType(File):
    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "unigram_frequency")


class UnigramFrequencyTypeWriter(PimlicoDatatypeWriter):
    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "unigram_frequency")


class BigramModelType(File):
    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "bigram_model")


class BigramModelTypeWriter(PimlicoDatatypeWriter):
    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "bigram_model")


class TrigramModelType(File):
    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "trigram_model")


class TrigramModelTypeWriter(PimlicoDatatypeWriter):
    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "trigram_model")


class DecimalDistancesType(File):
    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "decimal_distances")


class DecimalDistancesTypeWriter(PimlicoDatatypeWriter):
    def __init__(self, *args, **kwargs):
        super(DecimalDistancesTypeWriter, self).__init__(*args, **kwargs)
        self.model_corpus_distances = {}

    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "decimal_distances")

    def __exit__(self, *args, **kwargs):
        if self.model_corpus_distances is None or len(self.model_corpus_distances) == 0:
            raise Exception("'model_corpus_distances' attribute must be set and populated for the writer within the context")

        with codecs.open(self.absolute_path, 'w', encoding='utf-8') as f:
            for k, v in self.model_corpus_distances.iteritems():
                print(k[0], k[1], v, sep="\t", file=f)

        super(DecimalDistancesTypeWriter, self).__exit__(*args, **kwargs)


class SetSizeAndStatistics(File):
    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "set_size_and_statistics")


class SetSizeAndStatisticsTypeWriter(PimlicoDatatypeWriter):
    def __init__(self, *args, **kwargs):
        super(SetSizeAndStatisticsTypeWriter, self).__init__(*args, **kwargs)
        self.set_size = None
        self.statistics = None

    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "set_size_and_statistics")

    def __exit__(self, *args, **kwargs):
        if self.set_size is None or self.statistics is None:
            raise Exception(
                "'set_size' and 'statistics' attributes must be set for the writer within the context")

        with codecs.open(self.absolute_path, 'w', encoding='utf-8') as f:
            json.dump({'size': self.set_size, 'statistics': [(s[0], s[1]._asdict()) for s in self.statistics]}, f)

        super(SetSizeAndStatisticsTypeWriter, self).__exit__(*args, **kwargs)


class TokenMappingType(File):
    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "token_mapping")


class TokenMappingTypeWriter(PimlicoDatatypeWriter):
    def __init__(self, *args, **kwargs):
        super(TokenMappingTypeWriter, self).__init__(*args, **kwargs)
        # Contains (lang_a, lang_b) => mapping_dict, where languages are two-letter acronyms and mapping_dict a dict
        # with lang_a tokens as keys and lang_b replacements as values.
        self.mappings = collections.defaultdict(dict)

    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "token_mapping")

    def __exit__(self, *args, **kwargs):
        if len(self.mappings) == 0:
            pass

        with codecs.open(self.absolute_path, 'w', encoding='utf-8') as f:
            for languages, mappings in self.mappings.iteritems():
                lang_a, lang_b = languages
                for original_token, replacement_token in mappings:
                    print(u'{}\t{}\t{}\t{}'.format(lang_a, lang_b, original_token, replacement_token),
                          file=f)

        super(TokenMappingTypeWriter, self).__exit__(*args, **kwargs)


class TokenMappingMissingCandidatesType(File):
    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "missing_candidates")


class TokenMappingMissingCandidatesTypeWriter(PimlicoDatatypeWriter):
    def __init__(self, *args, **kwargs):
        super(TokenMappingMissingCandidatesTypeWriter, self).__init__(*args, **kwargs)
        # Contains (lang_a, lang_b) => { char_a => (char_b, phon. sim, char_b_a_freq, char_b_b_freq) }
        self.missing_candidates = collections.defaultdict(dict)

    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "missing_candidates")

    def __exit__(self, *args, **kwargs):
        if len(self.missing_candidates) == 0:
            pass

        with codecs.open(self.absolute_path, 'w', encoding='utf-8') as f:
            for languages, missing_candidates in self.missing_candidates.iteritems():
                lang_a, lang_b = languages
                for missing_token, candidate_tuples in missing_candidates.iteritems():
                    for (really_missing, p_diff, candidate_token, phon_similarity,
                         orig_a_freq, orig_b_freq,\
                         cand_a_freq, cand_b_freq) in candidate_tuples:
                        print(u'{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'
                              .format(lang_a, lang_b, missing_token, p_diff, really_missing, orig_a_freq, orig_b_freq,
                                      candidate_token, phon_similarity, cand_a_freq, cand_b_freq),
                              file=f)

        super(TokenMappingMissingCandidatesTypeWriter, self).__exit__(*args, **kwargs)
