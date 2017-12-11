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
from operator import itemgetter

from dlt import thresholded_phoneme_map
from dlt.datatypes.ngram import TokenMappingTypeWriter
from dlt.phonetic_transcript_tokenizer import token_gen as phoneme_tokenizer
from ngram.models import UnigramModel, BigramModel, BigramModelPerplexitySink, UnigramModelPerplexitySink, \
    TrigramModelPerplexitySink, TrigramModel
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes import InvalidDocument


def find_missing_from_b(dist_a, dist_b, logger, lang_a_name='A', lang_b_name='B'):
    diff_threshold = 0.01

    result = []
    for phoneme, pa in dist_a.token_probabilities.iteritems():
        if phoneme == u'WB':
            continue
        pb = dist_b.token_probabilities.get(phoneme, 0.0)
        p_diff = abs(pa - pb)
        if pb < 0.0000000001 and pa > pb and p_diff > diff_threshold:
            result.append(phoneme)
            logger.info(u'Phoneme {} is missing from language {}; rel. frequency in {}: {} vs {}: {}'
                        .format(phoneme, lang_b_name, lang_a_name, pa, lang_b_name, pb))

    return result


def bigram_perplexity(bigram_model, sub_map, corpus):
    sink = BigramModelPerplexitySink(bigram_model, substitution_map=sub_map)
    for token in corpus:
        sink.handle(token)
    return sink.perplexity()


def unigram_perplexity(unigram_model, sub_map, corpus):
    sink = UnigramModelPerplexitySink(unigram_model, substitution_map=sub_map)
    for token in corpus:
        sink.handle(token)
    return sink.perplexity()


def trigram_perplexity(trigram_model, sub_map, corpus):
    sink = TrigramModelPerplexitySink(trigram_model, substitution_map=sub_map)
    for token in corpus:
        sink.handle(token)
    return sink.perplexity()


def unigram_frequency_distance(original, unigram_model_a, candidate, unigram_model_b):
    ordered_a = [i[0] for i in sorted(unigram_model_a.token_counts.items(), key=itemgetter(1), reverse=True)]
    ordered_b = [i[0] for i in sorted(unigram_model_b.token_counts.items(), key=itemgetter(1), reverse=True)]

    original_index = ordered_a.index(original)
    candidate_index = ordered_b.index(candidate)

    return abs(original_index - candidate_index)


def find_best_candidate(original, unigram_model_a, unigram_model_b, bigram_model, trigram_model, corpus, phoneme_similarities, candidates, substitution_map,
                        logger):
    perplexity_with_candidate = {} # candidate => (bigram perp, trigram perp)

    original_bigram_perplexity = bigram_perplexity(bigram_model, substitution_map, corpus)
    original_trigram_perplexity = trigram_perplexity(trigram_model, substitution_map, corpus)
    logger.info(u'Original perplexity: {}'.format(original_bigram_perplexity))
    logger.info(u'Original trigram perplexity: {}'.format(original_trigram_perplexity))

    for candidate in candidates:
        sub_map = substitution_map.copy()
        sub_map[candidate] = original
        bg_perplexity = bigram_perplexity(bigram_model, sub_map, corpus)
        tg_perplexity = trigram_perplexity(trigram_model, sub_map, corpus)
        # logger.info(u'Perplexity with substitution: {} => {}: bg: {} / tg: {})'
        #             .format(original, candidate, bg_perplexity, tg_perplexity))

        perplexity_with_candidate[candidate] = (bg_perplexity, tg_perplexity,
                                                phoneme_similarities[(original, candidate)])

    best_candidate = None
    best_phoneme_similarity = None
    for candidate, values in perplexity_with_candidate.iteritems():
        bg_perplexity, tg_perplexity, phoneme_similarity = values
        bg_improvement = original_bigram_perplexity - bg_perplexity
        tg_improvement = original_trigram_perplexity - tg_perplexity
        average_perplexity = (bg_perplexity + tg_perplexity) / 2.0
        aggregate_improvement = (bg_improvement + tg_improvement) / 2.0
        proportional_improvement = aggregate_improvement / average_perplexity
        ug_order_distance = unigram_frequency_distance(original, unigram_model_a, candidate, unigram_model_b)

        logger.info(u'{} => {}; prop. improv: {}; phonem. sim: {}; order dist: {}'
                    .format(original, candidate,
                            proportional_improvement, phoneme_similarity,
                            ug_order_distance))

        if best_candidate is None or best_phoneme_similarity < phoneme_similarity:
            if ug_order_distance < 4:
                best_candidate = candidate
                best_phoneme_similarity = phoneme_similarity

    if best_candidate is not None and best_phoneme_similarity > 0:
        return best_candidate
    else:
        return None


def find_mappings(ug_a, ug_b, bg_a, bg_b, tr_a, tr_b, corpus_a, corpus_b, phoneme_similarities, logger,
                  lang_a_name='A', lang_b_name='B'):
    # TODO: Yule distribution
    min_replacement_p = 0.01

    logger.info(u'Finding mappings from {} to {}...'.format(lang_a_name, lang_b_name))
    missing = find_missing_from_b(ug_a, ug_b, logger,
                                  lang_a_name=lang_a_name, lang_b_name=lang_b_name)

    b_probs = sorted({k: v for k, v in ug_b.token_probabilities.iteritems() if k != u'WB'}.items(),
                     key=itemgetter(1),
                     reverse=True)

    result = []
    substitution_map = {}
    for m in missing:
        candidates = []
        for phoneme, probability in b_probs:
            if probability > min_replacement_p:
                try:
                    similarity = phoneme_similarities[(m, phoneme)]
                except:
                    similarity = 0
                if similarity > 0: # .000001:
                    candidates.append((phoneme, similarity))

        candidates = sorted(candidates, key=itemgetter(1), reverse=True)

        # logger.info(u'Candidates in {} for {}'.format(lang_b_name, m))
        # for candidate in candidates:
        #     logger.info(u'  Phoneme {} with similarity of {}'.format(candidate[0], candidate[1]))

        best_candidate = find_best_candidate(m, ug_a, ug_b, bg_a, tr_a, corpus_b, phoneme_similarities, [c[0] for c in candidates], substitution_map, logger)
        if best_candidate is not None:
            logger.info(u'Best candidate was: {}, phonological similarity was: {}'
                        .format(best_candidate, phoneme_similarities[(m, best_candidate)]))
            substitution_map[best_candidate] = m
            result.append((m, best_candidate))
        else:
            logger.warn(u'No replacement for {}'.format(m))

    return result


def _read_tokens(corpus, token_count, logger):
    result = []
    tokens_processed = 0
    for doc_name, doc_text in corpus:
        logger.debug(u"Processing {}".format(doc_name))
        if isinstance(doc_text, InvalidDocument):
            logger.debug(u"Skipping document {}: {}".format(doc_name, doc_text))
            continue

        for line in doc_text:
            for token in phoneme_tokenizer(line):
                result.append(token)
                tokens_processed += 1
                if tokens_processed >= token_count:
                    break
            if tokens_processed >= token_count:
                break
        if tokens_processed >= token_count:
            break

    if len(result) < token_count:
        raise Exception(u'Not enough tokens in input, expected at least {}, got {}'
                        .format(token_count, len(result)))

    return result


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        token_count = self.info.options["count"]
        corpora_inputs = self.info.get_input("corpora")
        unigram_model_inputs = self.info.get_input("unigram_models")
        bigram_model_inputs = self.info.get_input("bigram_models")
        trigram_model_inputs = self.info.get_input("trigram_models")

        corpora = {}
        for corpora_input in corpora_inputs:
            language = corpora_input.module.module_variables["lang"]
            self.log.info(u'Reading corpus for {}...'.format(language))
            corpora[language] = _read_tokens(corpora_input, token_count, self.log)
        self.log.info(u'Corpora read.')

        unigram_models = {}
        for model_input in unigram_model_inputs:
            language = model_input.module.module_variables["lang"]
            with codecs.open(model_input.absolute_path, 'r', encoding='utf-8') as f:
                unigram_models[language] = UnigramModel.read_from_file(f)

        self.log.info(u'Read in {} unigram distributions, languages: {}'
                      .format(len(unigram_models.keys()), u', '.join(unigram_models.keys())))

        bigram_models = {}
        for model_input in bigram_model_inputs:
            language = model_input.module.module_variables["lang"]
            with codecs.open(model_input.absolute_path, 'r', encoding='utf-8') as f:
                bigram_models[language] = BigramModel.read_from_file(f)

        self.log.info(u'Read in {} bigram distributions, languages: {}'
                      .format(len(bigram_models.keys()), u', '.join(bigram_models.keys())))

        trigram_models = {}
        for model_input in trigram_model_inputs:
            language = model_input.module.module_variables["lang"]
            with codecs.open(model_input.absolute_path, 'r', encoding='utf-8') as f:
                trigram_models[language] = TrigramModel.read_from_file(f)

        self.log.info(u'Read in {} trigram distributions, languages: {}'
                      .format(len(bigram_models.keys()), u', '.join(bigram_models.keys())))

        self.log.info(u'Reading in phoneme mappings...')
        phoneme_similarities = thresholded_phoneme_map.read_phoneme_similarities(
            self.info.options["phoneme_similarity_mapping_path"])
        self.log.info(u'Read in {} phoneme mappings'.format(len(phoneme_similarities)))

        lang_pair_mappings = {} # key: (l1, l2), values: (char, char)
        for l1, m1 in unigram_models.iteritems():
            for l2, m2 in unigram_models.iteritems():
                if l1 == l2:
                    continue

                bim1 = bigram_models[l1]
                bim2 = bigram_models[l2]
                trm1 = trigram_models[l1]
                trm2 = trigram_models[l2]

                pair_mappings = find_mappings(m1, m2,
                                              bim1, bim2, trm1, trm2,
                                              corpora[l1], corpora[l2],
                                              phoneme_similarities,
                                              self.log, lang_a_name=l1, lang_b_name=l2)
                lang_pair_mappings[(l1, l2)] = pair_mappings

        with TokenMappingTypeWriter(self.info.get_absolute_output_dir("mappings")) as writer:
            writer.mappings = lang_pair_mappings
