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
from dlt.utils import read_token_mapping
from ngram.models import UnigramModel, BigramModel, BigramModelPerplexitySink, UnigramModelPerplexitySink, \
    TrigramModelPerplexitySink, TrigramModel, DeletedInterpolationBigramModel, DeletedInterpolationTrigramModel
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes import InvalidDocument


def find_missing_from_b(dist_a, dist_b, existing_mapping, logger, lang_a_name='A', lang_b_name='B'):
    diff_threshold = 0.01

    result = []
    for phoneme, pa in dist_a.token_probabilities.iteritems():
        if phoneme == u'WB' or phoneme in existing_mapping:
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
    return sink.distance()


def unigram_perplexity(unigram_model, sub_map, corpus):
    sink = UnigramModelPerplexitySink(unigram_model, substitution_map=sub_map)
    for token in corpus:
        sink.handle(token)
    return sink.distance()


def trigram_perplexity(trigram_model, sub_map, corpus):
    sink = TrigramModelPerplexitySink(trigram_model, substitution_map=sub_map)
    for token in corpus:
        sink.handle(token)
    return sink.distance()


def find_best_candidate(original, bigram_model, trigram_model, corpus, phoneme_similarities, candidates,
                        substitution_map, logger):
    perplexity_with_candidate = {}

    original_bigram_perplexity = bigram_perplexity(bigram_model, substitution_map, corpus)
    original_trigram_perplexity = trigram_perplexity(trigram_model, substitution_map, corpus)
    logger.info(u'Original perplexity (bg / tg): {} / {}'.format(original_bigram_perplexity,
                                                                 original_trigram_perplexity))

    for candidate in candidates:
        sub_map = substitution_map.copy()
        sub_map[candidate] = original
        bg_perplexity = bigram_perplexity(bigram_model, sub_map, corpus)
        tg_perplexity = trigram_perplexity(trigram_model, sub_map, corpus)
        phoneme_similarity = phoneme_similarities[(original, candidate)]
        logger.info(u' {} => {}: bg: {} / tg: {}; impr. {} / {}; p-s: {}'
                    .format(original, candidate, bg_perplexity, tg_perplexity,
                            original_bigram_perplexity - bg_perplexity,
                            original_trigram_perplexity - tg_perplexity,
                            phoneme_similarity))

        perplexity_with_candidate[candidate] = (bg_perplexity, tg_perplexity, phoneme_similarity)

    best_candidate = None
    best_perplexity_improvement = None
    for candidate, values in perplexity_with_candidate.iteritems():
        bg_perplexity, tg_perplexity, phoneme_similarity = values
        bg_improvement = original_bigram_perplexity - bg_perplexity
        tg_improvement = original_trigram_perplexity - tg_perplexity
        average_perplexity = (bg_perplexity + tg_perplexity) / 2.0
        aggregate_improvement = (bg_improvement + tg_improvement) / 2.0
        proportional_improvement = aggregate_improvement / average_perplexity

        if best_candidate is None or best_perplexity_improvement < proportional_improvement:
            best_candidate = candidate
            best_perplexity_improvement = proportional_improvement

    if best_candidate is not None and best_perplexity_improvement > 0:
        return best_candidate
    else:
        return None


def find_mappings(unigram_a, unigram_b, bigram_a, trigram_a, corpus_b, existing_mapping, phoneme_similarities,
                  min_phoneme_similarity, logger, lang_a_name='A', lang_b_name='B'):
    min_replacement_p = 0.01

    logger.info(u'Finding mappings from {} to {}...'.format(lang_a_name, lang_b_name))
    missing = find_missing_from_b(unigram_a, unigram_b, existing_mapping, logger,
                                  lang_a_name=lang_a_name, lang_b_name=lang_b_name)

    b_probs = sorted({k: v for k, v in unigram_b.token_probabilities.iteritems() if k != u'WB'}.items(),
                     key=itemgetter(1),
                     reverse=True)

    result = []
    substitution_map = dict(existing_mapping)
    already_mapped = set(existing_mapping.values())
    for m in missing:
        candidates = []
        for phoneme, probability in b_probs:
            if probability > min_replacement_p:
                try:
                    similarity = phoneme_similarities[(m, phoneme)]
                except:
                    similarity = 0
                if similarity >= min_phoneme_similarity and phoneme not in already_mapped:
                    candidates.append((phoneme, similarity))

        candidates = sorted(candidates, key=itemgetter(1), reverse=True)

        # logger.info(u'Candidates in {} for {}'.format(lang_b_name, m))
        # for candidate in candidates:
        #     logger.info(u'  Phoneme {} with similarity of {}'.format(candidate[0], candidate[1]))

        best_candidate = find_best_candidate(m, bigram_a, trigram_a, corpus_b, phoneme_similarities, [c[0] for c in candidates], substitution_map, logger)
        if best_candidate is not None:
            logger.info(u'Best candidate was: {}, phonological similarity was: {}'
                        .format(best_candidate, phoneme_similarities[(m, best_candidate)]))
            substitution_map[best_candidate] = m
            result.append((m, best_candidate))
            already_mapped.add(best_candidate)
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
        interpolation_method = self.info.options["interpolation_method"]
        additive_smoothing = self.info.options["additive_smoothing"]
        corpora_inputs = self.info.get_input("corpora")
        unigram_model_inputs = self.info.get_input("unigram_models")
        bigram_model_inputs = self.info.get_input("bigram_models")
        trigram_model_inputs = self.info.get_input("trigram_models")

        with codecs.open(self.info.get_input("previous_mappings").absolute_path, 'r', encoding='utf-8') as f:
            token_mapping = read_token_mapping(f)

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
                unigram_models[language] = UnigramModel.read_from_file(f, additive_smoothing=additive_smoothing)

        self.log.info(u'Read in {} unigram distributions, languages: {}'
                      .format(len(unigram_models.keys()), u', '.join(unigram_models.keys())))

        bigram_models = {}
        for model_input in bigram_model_inputs:
            language = model_input.module.module_variables["lang"]
            with codecs.open(model_input.absolute_path, 'r', encoding='utf-8') as f:
                bigram_models[language] = BigramModel.read_from_file(f, additive_smoothing=additive_smoothing)

        self.log.info(u'Read in {} bigram distributions, languages: {}'
                      .format(len(bigram_models.keys()), u', '.join(bigram_models.keys())))

        trigram_models = {}
        for model_input in trigram_model_inputs:
            language = model_input.module.module_variables["lang"]
            with codecs.open(model_input.absolute_path, 'r', encoding='utf-8') as f:
                trigram_models[language] = TrigramModel.read_from_file(f, additive_smoothing=additive_smoothing)

        self.log.info(u'Read in {} trigram distributions, languages: {}'
                      .format(len(bigram_models.keys()), u', '.join(bigram_models.keys())))

        self.log.info(u'Reading in phoneme mappings...')
        phoneme_similarities = thresholded_phoneme_map.read_phoneme_similarities(
            self.info.options["phoneme_similarity_mapping_path"])
        self.log.info(u'Read in {} phoneme mappings'.format(len(phoneme_similarities)))

        lang_pair_mappings = {} # key: (l1, l2), values: (char, char)
        pair_count = 0
        for l1, m1 in unigram_models.iteritems():
            for l2, m2 in unigram_models.iteritems():
                if l1 == l2:
                    continue
                pair_count += 1

        # Effective interpolation model instantiation
        eff_bg_models = {}
        eff_tg_models = {}
        for language, tg_model in trigram_models.iteritems():
            ug_model = unigram_models[language]
            bg_model = bigram_models[language]
            if interpolation_method == "deleted":
                eff_bg_models[language] = DeletedInterpolationBigramModel(bg_model, ug_model)
                eff_tg_models[language] = DeletedInterpolationTrigramModel(tg_model, bg_model, ug_model)
            elif interpolation_method == "none":
                eff_bg_models[language] = bg_model
                eff_tg_models[language] = tg_model

        pairs_done = 0
        for l1, m1 in unigram_models.iteritems():
            for l2, m2 in unigram_models.iteritems():
                if l1 == l2:
                    continue

                existing_mapping = token_mapping.get((l1, l2), {})
                pair_mappings = find_mappings(m1, m2,
                                              eff_bg_models[l1], eff_tg_models[l1],
                                              corpora[l2],
                                              existing_mapping,
                                              phoneme_similarities,
                                              self.info.options["min_phoneme_similarity"],
                                              self.log, lang_a_name=l1, lang_b_name=l2)
                lang_pair_mappings[(l1, l2)] = pair_mappings
                pairs_done += 1

                self.log.info(u'Mapping progress {}/{}'.format(pairs_done, pair_count))

        with TokenMappingTypeWriter(self.info.get_absolute_output_dir("mappings")) as writer:
            writer.mappings = lang_pair_mappings
