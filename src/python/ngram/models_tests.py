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
import unittest

import collections

from ngram.models import UnigramModel, BigramModel, DeletedInterpolationBigramModel, TrigramModel, \
    DeletedInterpolationTrigramModel


def unigram_test_scaffold():
    common_vocabulary = {u'a', u'b', u'c', u'd'}
    vocabulary_a = common_vocabulary | {u'i', u'j', u'k'}
    vocabulary_b = common_vocabulary | {u'x', u'y', u'z'}

    frequencies = {}
    for order, item in enumerate(sorted(vocabulary_a | vocabulary_b), start=1):
        frequencies[item] = order * 31

    token_counts_a = {v: frequencies[v] for v in vocabulary_a}
    token_counts_b = {v: frequencies[v] for v in vocabulary_b}

    return vocabulary_a, vocabulary_b, token_counts_a, token_counts_b


class UnigramModelProbabilityMassTest(unittest.TestCase):
    def setUp(self):
        self.vocabulary_a, self.vocabulary_b, self.token_counts_a, self.token_counts_b = unigram_test_scaffold()

    def test_with_smoothing(self):
        model_a = UnigramModel(self.token_counts_a, additive_smoothing=True, additional_vocabulary=self.vocabulary_b)
        model_b = UnigramModel(self.token_counts_b, additive_smoothing=True, additional_vocabulary=self.vocabulary_a)
        model_a_100 = UnigramModel(self.token_counts_a, additive_smoothing=True, additive_smoothing_a=100,
                                   additional_vocabulary=self.vocabulary_b)
        model_b_100 = UnigramModel(self.token_counts_b, additive_smoothing=True, additive_smoothing_a=100,
                                   additional_vocabulary=self.vocabulary_a)

        sum_from_model_a = 0
        sum_from_model_b = 0
        sum_from_model_a_100 = 0
        sum_from_model_b_100 = 0
        for v in self.vocabulary_a | self.vocabulary_b:
            sum_from_model_a += model_a.probability(v)
            sum_from_model_b += model_b.probability(v)
            sum_from_model_a_100 += model_a_100.probability(v)
            sum_from_model_b_100 += model_b_100.probability(v)
        self.assertAlmostEqual(sum_from_model_a, 1.0, 15)
        self.assertAlmostEqual(sum_from_model_b, 1.0, 15)
        self.assertAlmostEqual(sum_from_model_a_100, 1.0, 15)
        self.assertAlmostEqual(sum_from_model_b_100, 1.0, 15)


def bigram_test_scaffold():
    common_vocabulary = {u'a', u'b', u'c', u'd'}
    vocabulary_a = common_vocabulary | {u'i', u'j', u'k'}
    vocabulary_b = common_vocabulary | {u'x', u'y', u'z'}

    numbers = {}
    for order, item in enumerate(sorted(vocabulary_a | vocabulary_b), start=1):
        numbers[item] = order * 31

    transitions_a = {}
    for v1 in vocabulary_a:
        for v2 in vocabulary_a:
            transitions_a[(v1, v2)] = numbers[v1] + numbers[v2]

    transitions_b = {}
    for v1 in vocabulary_b:
        for v2 in vocabulary_b:
            transitions_b[(v1, v2)] = numbers[v1] + numbers[v2]

    return vocabulary_a, vocabulary_b, transitions_a, transitions_b


class BigramModelProbabilityMassTest(unittest.TestCase):
    def setUp(self):
        self.vocabulary_a, self.vocabulary_b, self.transitions_a, self.transitions_b = bigram_test_scaffold()

    def test_with_smoothing(self):
        model_a = BigramModel(self.transitions_a, additive_smoothing=True, additional_vocabulary=self.vocabulary_b)
        model_b = BigramModel(self.transitions_b, additive_smoothing=True, additional_vocabulary=self.vocabulary_a)
        model_a_100 = BigramModel(self.transitions_a, additive_smoothing=True, additive_smoothing_a=100,
                                  additional_vocabulary=self.vocabulary_b)
        model_b_100 = BigramModel(self.transitions_b, additive_smoothing=True, additive_smoothing_a=100,
                                  additional_vocabulary=self.vocabulary_a)

        sum_from_model_a = collections.defaultdict(float)
        sum_from_model_b = collections.defaultdict(float)
        sum_from_model_a_100 = collections.defaultdict(float)
        sum_from_model_b_100 = collections.defaultdict(float)
        for v1 in self.vocabulary_a | self.vocabulary_b:
            for v2 in self.vocabulary_a | self.vocabulary_b:
                sum_from_model_a[v1] += model_a.probability((v1, v2))
                sum_from_model_b[v1] += model_b.probability((v1, v2))
                sum_from_model_a_100[v1] += model_a_100.probability((v1, v2))
                sum_from_model_b_100[v1] += model_b_100.probability((v1, v2))

        def test_sum_from_model(model):
            for k, v in model.iteritems():
                self.assertAlmostEqual(v, 1.0, 15)

        test_sum_from_model(sum_from_model_a)
        test_sum_from_model(sum_from_model_a_100)
        test_sum_from_model(sum_from_model_b)
        test_sum_from_model(sum_from_model_b_100)


class DeletedInterpolationBigramModelProbabilityMassTest(unittest.TestCase):
    def setUp(self):
        self.ug_vocab_a, self.ug_vocab_b, self.ug_token_counts_a, self.ug_token_counts_b = unigram_test_scaffold()
        self.bg_vocab_a, self.bg_vocab_b, self.bg_transitions_a, self.bg_transitions_b = bigram_test_scaffold()

    def test_smoothed(self):
        ug_model_a = UnigramModel(self.ug_token_counts_a, additive_smoothing=True,
                                  additional_vocabulary=self.ug_vocab_b | self.bg_vocab_a | self.bg_vocab_b)
        ug_model_b = UnigramModel(self.ug_token_counts_b, additive_smoothing=True,
                                  additional_vocabulary=self.ug_vocab_a | self.bg_vocab_a | self.bg_vocab_b)
        bg_model_a = BigramModel(self.bg_transitions_a, additive_smoothing=True,
                                 additional_vocabulary=self.bg_vocab_b | self.ug_vocab_a | self.ug_vocab_b)
        bg_model_b = BigramModel(self.bg_transitions_b, additive_smoothing=True,
                                 additional_vocabulary=self.bg_vocab_a | self.ug_vocab_a | self.ug_vocab_b)

        interp_model_a = DeletedInterpolationBigramModel(bg_model_a, ug_model_a)
        interp_model_b = DeletedInterpolationBigramModel(bg_model_b, ug_model_b)

        sum_from_model_a = collections.defaultdict(float)
        sum_from_model_b = collections.defaultdict(float)
        for v1 in self.bg_vocab_a | self.bg_vocab_b:
            for v2 in self.bg_vocab_a | self.bg_vocab_b:
                sum_from_model_a[v1] += interp_model_a.probability((v1, v2))
                sum_from_model_b[v1] += interp_model_b.probability((v1, v2))

        def test_sum_from_model(model):
            for k, v in model.iteritems():
                self.assertAlmostEqual(v, 1.0, 15)

        test_sum_from_model(sum_from_model_a)
        test_sum_from_model(sum_from_model_b)


def trigram_test_scaffold():
    common_vocabulary = {u'a', u'b', u'c', u'd'}
    vocabulary_a = common_vocabulary | {u'i', u'j', u'k'}
    vocabulary_b = common_vocabulary | {u'x', u'y', u'z'}

    numbers = {}
    for order, item in enumerate(sorted(vocabulary_a | vocabulary_b), start=1):
        numbers[item] = order * 31

    transitions_a = {}
    for v1 in vocabulary_a:
        for v2 in vocabulary_a:
            for v3 in vocabulary_a:
                transitions_a[(v1, v2, v3)] = numbers[v1] + numbers[v2] + numbers[v3]

    transitions_b = {}
    for v1 in vocabulary_b:
        for v2 in vocabulary_b:
            for v3 in vocabulary_b:
                transitions_b[(v1, v2, v3)] = numbers[v1] + numbers[v2] + numbers[v3]

    return vocabulary_a, vocabulary_b, transitions_a, transitions_b


class TrigramModelProbabilityMassTest(unittest.TestCase):
    def setUp(self):
        self.vocabulary_a, self.vocabulary_b, self.transitions_a, self.transitions_b = trigram_test_scaffold()

    def test_with_smoothing(self):
        model_a = TrigramModel(self.transitions_a, additive_smoothing=True, additional_vocabulary=self.vocabulary_b)
        model_b = TrigramModel(self.transitions_b, additive_smoothing=True, additional_vocabulary=self.vocabulary_a)
        model_a_100 = TrigramModel(self.transitions_a, additive_smoothing=True, additive_smoothing_a=100,
                                   additional_vocabulary=self.vocabulary_b)
        model_b_100 = TrigramModel(self.transitions_b, additive_smoothing=True, additive_smoothing_a=100,
                                   additional_vocabulary=self.vocabulary_a)

        sum_from_model_a = collections.defaultdict(float)
        sum_from_model_b = collections.defaultdict(float)
        sum_from_model_a_100 = collections.defaultdict(float)
        sum_from_model_b_100 = collections.defaultdict(float)
        for v1 in self.vocabulary_a | self.vocabulary_b:
            for v2 in self.vocabulary_a | self.vocabulary_b:
                for v3 in self.vocabulary_a | self.vocabulary_b:
                    sum_from_model_a[(v1, v2)] += model_a.probability((v1, v2, v3))
                    sum_from_model_b[(v1, v2)] += model_b.probability((v1, v2, v3))
                    sum_from_model_a_100[(v1, v2)] += model_a_100.probability((v1, v2, v3))
                    sum_from_model_b_100[(v1, v2)] += model_b_100.probability((v1, v2, v3))

        def test_sum_from_model(model):
            for k, v in model.iteritems():
                self.assertAlmostEqual(v, 1.0, 15)

        test_sum_from_model(sum_from_model_a)
        test_sum_from_model(sum_from_model_a_100)
        test_sum_from_model(sum_from_model_b)
        test_sum_from_model(sum_from_model_b_100)


class DeletedInterpolationTrigramModelProbabilityMassTest(unittest.TestCase):
    def setUp(self):
        self.ug_vocab_a, self.ug_vocab_b, self.ug_token_counts_a, self.ug_token_counts_b = unigram_test_scaffold()
        self.bg_vocab_a, self.bg_vocab_b, self.bg_transitions_a, self.bg_transitions_b = bigram_test_scaffold()
        self.tg_vocab_a, self.tg_vocab_b, self.tg_transitions_a, self.tg_transitions_b = trigram_test_scaffold()

    def test_smoothed(self):
        ug_model_a = UnigramModel(self.ug_token_counts_a, additive_smoothing=True,
                                  additional_vocabulary=self.ug_vocab_b | self.bg_vocab_a | self.bg_vocab_b)
        ug_model_b = UnigramModel(self.ug_token_counts_b, additive_smoothing=True,
                                  additional_vocabulary=self.ug_vocab_a | self.bg_vocab_a | self.bg_vocab_b)
        bg_model_a = BigramModel(self.bg_transitions_a, additive_smoothing=True,
                                 additional_vocabulary=self.bg_vocab_b | self.ug_vocab_a | self.ug_vocab_b)
        bg_model_b = BigramModel(self.bg_transitions_b, additive_smoothing=True,
                                 additional_vocabulary=self.bg_vocab_a | self.ug_vocab_a | self.ug_vocab_b)
        tg_model_a = TrigramModel(self.tg_transitions_a, additive_smoothing=True,
                                  additional_vocabulary=self.tg_vocab_b
                                                        | self.bg_vocab_a | self.bg_vocab_b
                                                        | self.ug_vocab_a | self.ug_vocab_b)
        tg_model_b = TrigramModel(self.tg_transitions_b, additive_smoothing=True,
                                  additional_vocabulary=self.tg_vocab_a
                                                        | self.bg_vocab_a | self.bg_vocab_b
                                                        | self.ug_vocab_a | self.ug_vocab_b)

        interp_model_a = DeletedInterpolationTrigramModel(tg_model_a, bg_model_a, ug_model_a)
        interp_model_b = DeletedInterpolationTrigramModel(tg_model_b, bg_model_b, ug_model_b)

        sum_from_model_a = collections.defaultdict(float)
        sum_from_model_b = collections.defaultdict(float)
        for v1 in self.bg_vocab_a | self.bg_vocab_b:
            for v2 in self.bg_vocab_a | self.bg_vocab_b:
                for v3 in self.bg_vocab_a | self.bg_vocab_b:
                    sum_from_model_a[(v1, v2)] += interp_model_a.probability((v1, v2, v3))
                    sum_from_model_b[(v1, v2)] += interp_model_b.probability((v1, v2, v3))

        def test_sum_from_model(model):
            for k, v in model.iteritems():
                self.assertAlmostEqual(v, 1.0, 15)

        test_sum_from_model(sum_from_model_a)
        test_sum_from_model(sum_from_model_b)
