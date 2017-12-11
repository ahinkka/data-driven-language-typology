# -*- coding: utf-8 -*-

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
import collections
import math

from datetime import datetime
from operator import itemgetter


class TokenHandlingProgressReporter(object):
    def __init__(self, logger):
        self.logger = logger
        self.last_print = datetime.now()
        self.total_transitions = 0

    def token_handled(self):
        self.total_transitions += 1
        every_nth = 1000000
        if self.total_transitions % every_nth == 0:
            now = datetime.now()
            secs_between = (now - self.last_print).total_seconds()
            transitions_per_sec = int(every_nth / secs_between)
            self.logger.debug(u"{:,} tokens handled; {:,} t/s"
                              .format(self.total_transitions, transitions_per_sec))
            self.last_print = now


class UnigramModelBuilderTokenSink(object):
    def __init__(self, logger):
        self.progress_reporter = TokenHandlingProgressReporter(logger)
        self.previous = None
        self.token_counts = collections.defaultdict(int)

    def handle(self, token):
        # print(token.letter, token.is_beginning, token.is_ending, sep='\t')
        self.progress_reporter.token_handled()

        if self.previous != u"WB":
            if token.is_beginning:
                self.token_counts[u"WB"] += 1
            if token.is_ending:
                self.token_counts[u"WB"] += 1

        self.token_counts[token.letter] += 1

        if not token.is_ending:
            self.previous = token.letter
        else:
            self.previous = u"WB"


class UnigramModel(object):
    def __init__(self, token_counts, additional_vocabulary=None, additive_smoothing=False, additive_smoothing_a=0.1):
        self.token_counts = token_counts
        total_count = float(sum(token_counts.itervalues()))

        # Prepare vocabulary
        self.vocabulary = set(token_counts.keys())
        if additional_vocabulary is not None:
            self.vocabulary.update(additional_vocabulary)

        # Finish with populating transition_probabilities
        if additive_smoothing:
            # https://en.wikipedia.org/wiki/Additive_smoothing
            vocabulary_size = len(self.vocabulary)
            vocab_times_a = vocabulary_size * float(additive_smoothing_a)

            self.token_probabilities = {k: (token_counts[k] + additive_smoothing_a) / (total_count + vocab_times_a)
                                        for k, v in token_counts.iteritems()}
            self.additive_default = additive_smoothing_a / (total_count + vocab_times_a)
        else:
            self.additive_default = None
            self.token_probabilities = {k: token_counts[k] / total_count
                                        for k, v in token_counts.iteritems()}

    def probability(self, key, missing_value=None, log_fn=None):
        tmp = self.token_probabilities.get(key, None)
        if tmp is None and self.additive_default is not None:
            if key not in self.vocabulary and log_fn is not None:
                log_fn(u"Token {} not part of model's vocabulary".format(key))
            return self.additive_default
        elif tmp is None:
            return missing_value
        else:
            return tmp

    def top_n(self, key, n):
        return sorted(self.token_probabilities.items(), key=itemgetter(1), reverse=True)[:n]

    @classmethod
    def _read_frequency_dist(cls, stream):
        probability = {}
        for line in stream:
            line = line.replace('\n', '')
            state, tmp = line.split('\t')
            probability[state] = int(tmp)
        return probability

    @classmethod
    def read_from_file(cls, file, *args, **kwargs):
        return UnigramModel(UnigramModel._read_frequency_dist(file), *args, **kwargs)

    def write_to_file(self, file):
        for k, v in self.token_counts.iteritems():
            file.write(u"{}\t{}\n".format(k, v))


class UnigramModelPerplexitySink(object):
    def __init__(self, model, substitution_map=None):
        assert isinstance(model, UnigramModel)
        self.model = model

        if substitution_map is None:
            self.substitution_map = {}
        else:
            assert isinstance(substitution_map, dict)
            self.substitution_map = substitution_map

        self.log_sum = 0

        self.transitions_handled = 0
        self.transition_count = collections.defaultdict(int)

        if substitution_map is None:
            self.substitution_map = {}
        else:
            self.substitution_map = substitution_map

    def handle(self, token):
        substituted_letter = self.substitution_map.get(token.letter, token.letter)
        probability = self.model.probability(substituted_letter, None)
        if probability is not None:
            contribution = math.log(probability, 2)
            self.log_sum += contribution
            self.transitions_handled += 1
            self.transition_count[token.letter] += 1

    def distance(self):
        return math.pow(2, - 1 * self.log_sum / float(self.transitions_handled))


class BigramModelBuilderTokenSink(object):
    def __init__(self, logger):
        self.progress_reporter = TokenHandlingProgressReporter(logger)
        self.previous = u"WB"
        self.transition_counts = collections.defaultdict(int)

    def handle(self, token):
        self.progress_reporter.token_handled()

        self.transition_counts[(self.previous, token.letter)] += 1
        self.previous = token.letter

        if token.is_ending:
            self.transition_counts[(token.letter, u"WB")] += 1
            self.previous = u"WB"


class BigramModel(object):
    def __init__(self, transition_counts, additional_vocabulary=None,
                 additive_smoothing=False, additive_smoothing_a=0.1):
        self.transition_counts = transition_counts

        self._per_from_transition_count = collections.defaultdict(int)
        for key, count in transition_counts.iteritems():
            self._per_from_transition_count[key[0]] += count

        # Prepare vocabulary
        self.vocabulary = set()
        for key in transition_counts.iterkeys():
            a, b = key
            self.vocabulary.add(a)
            self.vocabulary.add(b)
        if additional_vocabulary is not None:
            self.vocabulary.update(additional_vocabulary)

        # Finish with populating transition_probabilities
        if additive_smoothing:
            # https://en.wikipedia.org/wiki/Additive_smoothing
            vocabulary_size = len(self.vocabulary)
            vocab_times_a = vocabulary_size * float(additive_smoothing_a)

            self.transition_probabilities =\
                {k: (v + additive_smoothing_a) / (float(self._per_from_transition_count[k[0]]) + vocab_times_a)
                 for k, v in transition_counts.iteritems()}
            self._additive_smoothing_a = additive_smoothing_a
            self._vocab_times_a = vocab_times_a
        else:
            self._vocab_times_a = None
            self.transition_probabilities =\
                {k: v / float(self._per_from_transition_count[k[0]])
                 for k, v in transition_counts.iteritems()}

    def probability(self, key, missing_value=None, log_fn=None):
        tmp = self.transition_probabilities.get(key, None)
        if tmp is None and self._vocab_times_a is not None:
            if key[0] not in self.vocabulary and log_fn is not None:
                log_fn(u"Token {} not part of model's vocabulary".format(key[0]))
            elif key[1] not in self.vocabulary and log_fn is not None:
                log_fn(u"Token {} not part of model's vocabulary".format(key[1]))
            return self._additive_smoothing_a / \
                   float(self._per_from_transition_count[key[0]] + self._vocab_times_a)
        elif tmp is None:
            return missing_value
        else:
            return tmp

    @classmethod
    def _read_transition_counts(cls, stream):
        probability = {}
        for line in stream:
            line = line.replace('\n', '')
            frm, to, tmp = line.split('\t')
            probability[(frm, to)] = int(tmp)
        return probability

    @classmethod
    def read_from_file(cls, file, *args, **kwargs):
        return BigramModel(BigramModel._read_transition_counts(file), *args, **kwargs)

    def write_to_file(self, file):
        for k, v in self.transition_counts.iteritems():
            file.write(u"{}\t{}\t{}\n".format(k[0], k[1], v))


class BigramModelPerplexitySink(object):
    def __init__(self, bigram_model, substitution_map=None):
        self.model = bigram_model

        if substitution_map is not None:
            self.substitution_map = substitution_map
        else:
            self.substitution_map = {}

        self.previous = None

        self.log_sum = 0
        self.transitions_handled = 0

        self.transition_count = collections.defaultdict(int)

    def _handle_transition(self, context, token):
        substituted_context = self.substitution_map.get(context, context)
        substituted_token = self.substitution_map.get(token, token)

        key = (substituted_context, substituted_token)
        probability = self.model.probability(key, None)

        self.transition_count[key] += 1
        if probability is None:
            pass
        else:
            contribution = math.log(probability, 2)
            self.log_sum += contribution
            self.transitions_handled += 1

    def handle(self, token):
        if self.previous is None:
            previous = u"WB"
        else:
            previous = self.previous.letter

        self._handle_transition(previous, token.letter)
        self.previous = token

        if token.is_ending:
            self._handle_transition(token.letter, u"WB")
            self.previous = None

    def distance(self):
        return math.pow(2, - 1 * self.log_sum / float(self.transitions_handled))


class BigramModelKitaDistanceSink(object):
    def __init__(self, bigram_model, corpus_bigram_model, substitution_map=None):
        self.model = bigram_model
        self.corpus_model = corpus_bigram_model

        if substitution_map is not None:
            self.substitution_map = substitution_map
        else:
            self.substitution_map = {}

        self.previous = None

        self.log_sum = 0
        self.transitions_handled = 0

        self.transition_count = collections.defaultdict(int)

    def _handle_transition(self, context, token):
        substituted_context = self.substitution_map.get(context, context)
        substituted_token = self.substitution_map.get(token, token)

        key = (substituted_context, substituted_token)
        corpus_probability = self.corpus_model.probability(key, None)
        probability = self.model.probability(key, None)

        self.transition_count[key] += 1
        if corpus_probability is None or probability is None:
            pass
        else:
            contribution = abs(math.log(corpus_probability, 2) - math.log(probability, 2))
            self.log_sum += contribution
            self.transitions_handled += 1

    def handle(self, token):
        if self.previous is None:
            previous = u"WB"
        else:
            previous = self.previous.letter

        self._handle_transition(previous, token.letter)
        self.previous = token

        if token.is_ending:
            self._handle_transition(token.letter, u"WB")
            self.previous = None

    def distance(self):
        return self.log_sum / float(self.transitions_handled)


class TrigramModelBuilderTokenSink(object):
    def __init__(self, logger):
        self.progress_reporter = TokenHandlingProgressReporter(logger)
        self.context = (u"WB", u"WB")
        self.transition_counts = collections.defaultdict(int)

    def push_context(self, item):
        self.context = (self.context[-1], item)

    def handle(self, token):
        self.progress_reporter.token_handled()

        self.transition_counts[(self.context[0], self.context[1], token.letter)] += 1
        self.push_context(token.letter)

        if token.is_ending:
            self.transition_counts[(self.context[0], self.context[1], u"WB")] += 1
            self.push_context(u"WB")


class TrigramModel(object):
    def __init__(self, transition_counts, additional_vocabulary=None,
                 additive_smoothing=False, additive_smoothing_a=0.1):
        self.transition_counts = transition_counts

        self._per_from_transition_count = collections.defaultdict(int)
        for key, count in transition_counts.iteritems():
            self._per_from_transition_count[(key[0], key[1])] += count

        # Prepare vocabulary
        self.vocabulary = set()
        for key in transition_counts.iterkeys():
            a, b, c = key
            self.vocabulary.add(a)
            self.vocabulary.add(b)
            self.vocabulary.add(c)
        if additional_vocabulary is not None:
            self.vocabulary.update(additional_vocabulary)

        # Finish with populating transition_probabilities
        if additive_smoothing:
            # https://en.wikipedia.org/wiki/Additive_smoothing
            vocabulary_size = len(self.vocabulary)
            self._vocab_times_a = vocabulary_size * float(additive_smoothing_a)
            self._additive_smoothing_a = additive_smoothing_a

            self.transition_probabilities =\
                {k: (v + additive_smoothing_a) /
                    (float(self._per_from_transition_count[(k[0], k[1])]) + self._vocab_times_a)
                 for k, v in transition_counts.iteritems()}
        else:
            self._vocab_times_a = None
            self.transition_probabilities =\
                {k: v / float(self._per_from_transition_count[(k[0], k[1])])
                 for k, v in transition_counts.iteritems()}

    def probability(self, key, missing_value=None, log_fn=None):
        tmp = self.transition_probabilities.get(key, None)
        if tmp is None and self._vocab_times_a is not None:
            if key[0] not in self.vocabulary and log_fn is not None:
                log_fn(u"Token {} not part of model's vocabulary".format(key[0]))
            elif key[1] not in self.vocabulary and log_fn is not None:
                log_fn(u"Token {} not part of model's vocabulary".format(key[1]))
            elif key[2] not in self.vocabulary and log_fn is not None:
                log_fn(u"Token {} not part of model's vocabulary".format(key[2]))
            return self._additive_smoothing_a /\
                   float(self._per_from_transition_count[(key[0], key[1])] + self._vocab_times_a)
        elif tmp is None:
            return missing_value
        else:
            return tmp

    @classmethod
    def _read_transition_counts(cls, stream):
        probability = {}
        for line in stream:
            line = line.replace('\n', '')
            frm1, frm2, to, tmp = line.split('\t')
            probability[(frm1, frm2, to)] = int(tmp)
        return probability

    @classmethod
    def read_from_file(cls, file, *args, **kwargs):
        return TrigramModel(TrigramModel._read_transition_counts(file), *args, **kwargs)

    def write_to_file(self, file):
        for k, v in self.transition_counts.iteritems():
            file.write(u"{}\t{}\t{}\t{}\n".format(k[0], k[1], k[2], v))


class TrigramModelPerplexitySink(object):
    def __init__(self, model, substitution_map=None):
        self.model = model

        if substitution_map is not None:
            self.substitution_map = substitution_map
        else:
            self.substitution_map = {}

        self.context = (u"WB", u"WB")

        self.log_sum = 0
        self.transitions_handled = 0

        self.transition_count = collections.defaultdict(int)

    def push_context(self, item):
        self.context = (self.context[-1], item)

    def _handle_transition(self, context, state):
        ctx1 = self.substitution_map.get(context[0], context[0])
        ctx2 = self.substitution_map.get(context[1], context[1])
        substituted_state = self.substitution_map.get(state, state)

        key = (ctx1, ctx2, substituted_state)
        probability = self.model.probability(key, None)

        self.transition_count[key] += 1
        if probability is None:
            pass
        else:
            contribution = math.log(probability, 2)
            self.log_sum += contribution
            self.transitions_handled += 1

    def handle(self, token):
        self._handle_transition(self.context, token.letter)
        self.push_context(token.letter)

        if token.is_ending:
            self._handle_transition(self.context, u"WB")
            self.push_context(u"WB")

    def distance(self):
        return math.pow(2, - 1 * self.log_sum / float(self.transitions_handled))


class TrigramModelKitaDistanceSink(object):
    def __init__(self, model, corpus_model, substitution_map=None):
        self.model = model
        self.corpus_model = corpus_model

        if substitution_map is not None:
            self.substitution_map = substitution_map
        else:
            self.substitution_map = {}

        self.context = (u"WB", u"WB")

        self.log_sum = 0
        self.transitions_handled = 0

        self.transition_count = collections.defaultdict(int)

    def push_context(self, item):
        self.context = (self.context[-1], item)

    def _handle_transition(self, context, state):
        ctx1 = self.substitution_map.get(context[0], context[0])
        ctx2 = self.substitution_map.get(context[1], context[1])
        substituted_state = self.substitution_map.get(state, state)

        key = (ctx1, ctx2, substituted_state)
        probability = self.model.probability(key, None)
        corpus_probability = self.corpus_model.probability(key, None)

        self.transition_count[key] += 1
        if corpus_probability is None or probability is None:
            pass
        else:
            contribution = abs(math.log(corpus_probability, 2) - math.log(probability, 2))
            self.log_sum += contribution
            self.transitions_handled += 1

    def handle(self, token):
        self._handle_transition(self.context, token.letter)
        self.push_context(token.letter)

        if token.is_ending:
            self._handle_transition(self.context, u"WB")
            self.push_context(u"WB")

    def distance(self):
        return self.log_sum / float(self.transitions_handled)


class DeletedInterpolationBigramModel(object):
    def __init__(self, bigram_model, unigram_model):
        self.bigram_model = bigram_model
        self.unigram_model = unigram_model

        # weight bigram model; unigram is rest
        self.lambda1 = 0.8 # 0.3

        self.bigram_model_weight = self.lambda1
        self.unigram_model_weight = 1.0 - self.lambda1

    def probability(self, key, missing_value=None):
        bg_key = key

        bg_p = self.bigram_model.probability(bg_key, None)
        ug_p = self.unigram_model.probability(key[1], None)

        if bg_p is None and ug_p is None:
            return missing_value
        else:
            if bg_p is None:
                bg_p = 0.0
            if ug_p is None:
                ug_p = 0.0

        return \
            bg_p * self.bigram_model_weight + \
            ug_p * self.unigram_model_weight


class DeletedInterpolationTrigramModel(object):
    def __init__(self, trigram_model, bigram_model, unigram_model):
        self.trigram_model = trigram_model
        self.bigram_model = bigram_model
        self.unigram_model = unigram_model

        # weight of trigram model
        self.lambda1 = 0.7
        # weight bigram model; unigram is rest
        self.lambda2 = 0.2

        self.trigram_model_weight = self.lambda1
        self.bigram_model_weight = self.lambda2
        self.unigram_model_weight = 1.0 - self.lambda1 - self.lambda2

    def probability(self, key, missing_value=None):
        tg_key = key
        bg_key = (key[1], key[2])

        tg_p = self.trigram_model.probability(tg_key, None)
        bg_p = self.bigram_model.probability(bg_key, None)
        ug_p = self.unigram_model.probability(key[2], None)

        if tg_p is None and bg_p is None and ug_p is None:
            return missing_value
        else:
            if tg_p is None:
                tg_p = 0.0
            if bg_p is None:
                bg_p = 0.0
            if ug_p is None:
                ug_p = 0.0

        return \
            tg_p * self.trigram_model_weight + \
            bg_p * self.bigram_model_weight + \
            ug_p * self.unigram_model_weight


def calculate_perplexity(model, tokens):
    if isinstance(model, UnigramModel):
        sink = UnigramModelPerplexitySink(model)
    elif isinstance(model, BigramModel) or isinstance(model, DeletedInterpolationBigramModel):
        sink = BigramModelPerplexitySink(model)
    elif isinstance(model, TrigramModel) or isinstance(model, DeletedInterpolationTrigramModel):
        sink = TrigramModelPerplexitySink(model)
    else:
        raise Exception(u'No sink defined for {}'.format(type(model)))

    for token in tokens:
        sink.handle(token)
    return sink.distance()
