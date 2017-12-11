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
import contextlib

import collections
import random

import math
import os

from pimlico.datatypes import InvalidDocument


@contextlib.contextmanager
def working_directory(path):
    """A context manager which changes the working directory to the given
    path, and then changes it back to its previous value on exit.

    """
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def read_token_mapping(stream):
    result = {}
    for line in stream:
        parts = line.replace('\n', '').split('\t')
        lang_key = parts[0], parts[1]
        if lang_key not in result:
            result[lang_key] = {}
        result[lang_key][parts[2]] = parts[3]
    return result


def read_tokens(corpus, max_token_count, tokenizer, logger):
    all_tokens = []
    tokens_processed = 0
    for doc_name, doc_text in corpus:
        logger.debug(u"Processing {}".format(doc_name))
        if isinstance(doc_text, InvalidDocument):
            logger.debug(u"Skipping document {}: {}".format(doc_name, doc_text))
            continue

        for line in doc_text:
            for token in tokenizer(line):
                all_tokens.append(token)
                tokens_processed += 1
                if tokens_processed >= max_token_count:
                    break
            if tokens_processed >= max_token_count:
                break
        if tokens_processed >= max_token_count:
            break

    return all_tokens, tokens_processed


Statistics = collections.namedtuple('Statistics', ['expected_value', 'min', 'median', 'max', 'mean',
                                                   'std_dev', 'variance', 'measurements'])


def calculate_statistics_with_callable(expected_value, callable_, iterations, logger):
    values = []
    for i in xrange(iterations):
        value = callable_()
        values.append(value)

    min_ = min(values)
    median = sorted(values)[int(math.ceil(len(values) * 0.5))]
    max_ = max(values)

    deviations = [p - expected_value for p in values]
    deviations_squared = [d * d for d in deviations]
    unbiased_sample_variance = (1 / float((len(deviations_squared) - 1))) * sum(deviations_squared)
    std_dev = math.sqrt(unbiased_sample_variance)
    mean = sum(values) / float(len(values))

    return Statistics(expected_value=expected_value, min=min_, median=median, max=max_, mean=mean,
                      std_dev=std_dev, variance=unbiased_sample_variance,
                      measurements=values)


def random_range(sequence, range_length, random_int_generator=random.randint):
    """Takes a random range from a sequence given range length. Returns an iterator."""
    seq_len = len(sequence)
    if range_length == seq_len:
        for item in sequence:
            yield item
    elif range_length > seq_len:
        raise ValueError("sample size is greater than sequence length: {} vs {}".format(range_length, seq_len))
    else:
        start_index = random_int_generator(0, seq_len - range_length)
        end_index = start_index + range_length
        for item in sequence[start_index:end_index]:
            yield item


def collect_distances_names(input_distances):
    distances = {}
    lang_names = {}
    for d in input_distances:
        model_lang = d.module.module_variables["model_lang_code"]
        corpus_lang = d.module.module_variables["corpus_lang_code"]

        lang_names[model_lang] = d.module.module_variables["model_lang"]
        lang_names[corpus_lang] = d.module.module_variables["corpus_lang"]

        distances[(model_lang, corpus_lang)] = d.result

    return distances, lang_names


def next_size(previous):
    if previous < 20:
        raise Exception("Unsupported size: {}".format(previous))
    elif previous < 200:
        tens = previous / 10
        return (tens + 2) * 10
    elif previous < 1000:
        hundreds = previous / 100
        return (hundreds + 1) * 100
    elif previous < 10000:
        thousands = previous / 1000
        return (thousands + 1) * 1000
    elif previous < 20000:
        thousands = previous / 1000
        return (thousands + 2) * 1000
    elif previous < 50000:
        thousands = previous / 1000
        return (thousands + 5) * 1000
    else:
        ten_thousands = previous / 10000
        return (ten_thousands + 1) * 10000
