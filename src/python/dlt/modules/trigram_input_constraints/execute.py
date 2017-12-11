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
from pimlico.core.modules.base import BaseModuleExecutor

from dlt.datatypes.ngram import SetSizeAndStatisticsTypeWriter
from dlt.phonetic_transcript_tokenizer import token_gen as phoneme_token_gen
from dlt.text_tokenizer import token_gen as text_token_gen
from dlt.utils import read_tokens, calculate_statistics_with_callable, random_range, next_size
from ngram.models import TrigramModelBuilderTokenSink, TrigramModel, UnigramModelBuilderTokenSink, \
    BigramModelBuilderTokenSink, UnigramModel, BigramModel, \
    DeletedInterpolationTrigramModel, calculate_perplexity


def make_trigram_model(tokens, logger):
    ug_sink = UnigramModelBuilderTokenSink(logger)
    bg_sink = BigramModelBuilderTokenSink(logger)
    tg_sink = TrigramModelBuilderTokenSink(logger)
    for token in tokens:
        ug_sink.handle(token)
        bg_sink.handle(token)
        tg_sink.handle(token)

    ug_model = UnigramModel(ug_sink.token_counts, additive_smoothing=True)
    bg_model = BigramModel(bg_sink.transition_counts)
    tg_model = TrigramModel(tg_sink.transition_counts)

    return DeletedInterpolationTrigramModel(tg_model, bg_model, ug_model)


def calculate_statistics_for_learning_set_size(expected_value, learning_tokens, learning_set_size,
                                               test_tokens, test_set_size, iterations, logger):
    def perplexity_calc():
        learning_sample = random_range(learning_tokens, learning_set_size)
        language_model = make_trigram_model(learning_sample, logger)
        test_sample = random_range(test_tokens, test_set_size)
        return calculate_perplexity(language_model, test_sample)
    return calculate_statistics_with_callable(expected_value, perplexity_calc, iterations, logger)


def calculate_statistics_for_test_set_size(desired_perplexity, language_model, test_tokens, size, sample_count, logger):
    def perplexity_calc():
        test_sample = random_range(test_tokens, size)
        return calculate_perplexity(language_model, test_sample)
    return calculate_statistics_with_callable(desired_perplexity, perplexity_calc, sample_count, logger)


def calculate_probability(measurements, desired_value, diff_threshold):
    successes = 0
    for observation in measurements:
        if abs(observation - desired_value) <= diff_threshold:
            successes += 1
    return successes / float(len(measurements))


def stop_condition(statistics, diff_threshold, desired_value, p_threshold):
    if len(statistics) < 1:
        return False, 0.0

    p = calculate_probability(statistics[-1].measurements, desired_value, diff_threshold)
    if p >= p_threshold:
        return True, p
    else:
        return False, p


def optimal_test_set_size(logger, language_model, test_tokens, desired_perplexity,
                          diff_threshold, cutoff_probability, sample_count):
    logger.info("Finding minimum test set size, expected value is {}...".format(desired_perplexity))
    keys = ["SET SIZE", "MEDIAN", "MEAN", "STD DEV", "PROB"]
    logger.info(u'\t'.join([u'{:<10}'.format(k) for k in keys]))

    size = None
    prev_size = size
    all_stats = []
    while True:
        if size is None:
            size = 20
        else:
            size = next_size(size)

        if size > len(test_tokens):
            raise Exception("Good enough test set size not reached")

        stats = calculate_statistics_for_test_set_size(desired_perplexity, language_model, test_tokens, size,
                                                       sample_count, logger)
        all_stats.append((size, stats))
        should_stop, prob = stop_condition([s[1] for s in all_stats],
                                           diff_threshold, desired_perplexity, cutoff_probability)
        logger.info(u'\t'.join([u'{:<10}'.format(i)
                                for i in [size, stats.median, stats.mean, stats.std_dev, prob]]))

        if should_stop:
            # Recalculate previous size with double the sample size
            logger.info("Recalculating previous test set size with double the sample count")
            prev_stats = calculate_statistics_for_test_set_size(desired_perplexity, language_model, test_tokens, prev_size,
                                                                sample_count * 2, logger)
            should_stop_prev, prob_prev = stop_condition([prev_stats],
                                                         diff_threshold, desired_perplexity, cutoff_probability)
            logger.info(u'\t'.join([u'{:<10}'.format(i)
                                    for i in [prev_size, prev_stats.median, prev_stats.mean, prev_stats.std_dev, prob_prev]]))

            if should_stop_prev:
                all_stats = all_stats[:-1]
                size = prev_size
                all_stats.append((size, prev_stats))
                should_stop = should_stop_prev

        if should_stop:
            return size, all_stats
        prev_size = size


def optimal_learning_set_size(logger, learning_tokens, test_tokens, test_set_size,
                              desired_perplexity, diff_threshold, cutoff_probability, sample_count):
    logger.info("Finding minimum learning set size, expected value is {}...".format(desired_perplexity))
    keys = ["SET SIZE", "MEDIAN", "MEAN", "STD DEV", "PROB"]
    logger.info(u'\t'.join([u'{:<10}'.format(k) for k in keys]))

    size = None
    prev_size = size
    all_stats = []
    while True:
        if size is None:
            size = 100
        else:
            size = next_size(size)

        if size > len(learning_tokens):
            raise Exception("Good enough learning set size not reached")

        stats = calculate_statistics_for_learning_set_size(
            desired_perplexity, learning_tokens, size, test_tokens, test_set_size, sample_count, logger)
        all_stats.append((size, stats))

        should_stop, prob = stop_condition([s[1] for s in all_stats],
                                           diff_threshold, desired_perplexity, cutoff_probability)
        logger.info(u'\t'.join([u'{:<10}'.format(i)
                                for i in [size, stats.median, stats.mean, stats.std_dev, prob]]))

        if should_stop:
            # Recalculate previous size with double the sample size
            logger.info("Recalculating previous learning set size with double the sample count")
            prev_stats = calculate_statistics_for_learning_set_size(
                desired_perplexity, learning_tokens, prev_size, test_tokens, test_set_size, sample_count * 2, logger)
            should_stop_prev, prob_prev = stop_condition([prev_stats],
                                                         diff_threshold, desired_perplexity, cutoff_probability)
            logger.info(u'\t'.join([u'{:<10}'.format(i)
                                    for i in [prev_size, prev_stats.median, prev_stats.mean, prev_stats.std_dev, prob_prev]]))

            if should_stop_prev:
                all_stats = all_stats[:-1]
                size = prev_size
                all_stats.append((size, prev_stats))
                should_stop = should_stop_prev

        if should_stop:
            return size, all_stats
        prev_size = size


def optimal_set_sizes(logger, learning_tokens, test_tokens, diff_threshold, cutoff_probability, sample_count):
    pass


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        corpus = self.info.get_input("corpus")
        token_type = self.info.options["token_type"]
        max_token_count = self.info.options["max_token_count"]
        held_out_set_size = self.info.options["held_out_set_size"]
        train_diff_threshold = self.info.options["train_diff_threshold"]
        train_cutoff_probability = self.info.options["train_cutoff_probability"]
        train_sample_count = self.info.options["train_sample_count"]
        test_diff_threshold = self.info.options["test_diff_threshold"]
        test_cutoff_probability = self.info.options["test_cutoff_probability"]
        test_sample_count = self.info.options["test_sample_count"]

        if held_out_set_size < 10000:
            raise Exception("Please provide a sane held out set size")

        start_test_token = max_token_count - held_out_set_size
        if start_test_token < 0:
            raise Exception("Start token is less than zero")

        if token_type == "text":
            tokenizer = text_token_gen
        elif token_type == "phonemes":
            tokenizer = phoneme_token_gen

        tokens, tokens_processed = read_tokens(corpus, max_token_count, tokenizer, self.log)
        self.log.info(u"{} tokens read".format(tokens_processed))

        held_out_tokens = tokens[0:held_out_set_size]
        learning_tokens = tokens[held_out_set_size:]

        full_model = make_trigram_model(learning_tokens, self.log)

        desired_perplexity = calculate_perplexity(full_model, held_out_tokens)
        self.log.info(u"Desired perplexity is {}".format(desired_perplexity))

        test_set_size, statistics = optimal_test_set_size(self.log, full_model, held_out_tokens, desired_perplexity,
                                                          test_diff_threshold, test_cutoff_probability, test_sample_count)
        self.log.info(u"Optimal test set size is {}".format(test_set_size))

        with SetSizeAndStatisticsTypeWriter(
                self.info.get_absolute_output_dir("test_set_size_and_statistics")) as writer:
            writer.set_size = test_set_size
            writer.statistics = statistics

        learning_set_size, statistics = optimal_learning_set_size(self.log, learning_tokens, held_out_tokens,
                                                                  test_set_size, desired_perplexity, train_diff_threshold,
                                                                  train_cutoff_probability, train_sample_count)
        with SetSizeAndStatisticsTypeWriter(
                self.info.get_absolute_output_dir("learning_set_size_and_statistics")) as writer:
            writer.set_size = learning_set_size
            writer.statistics = statistics
        self.log.info(u"Optimal learning set size is {}".format(learning_set_size))
