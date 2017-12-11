#!/usr/bin/env python
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
from __future__ import print_function

import codecs
import collections

from operator import itemgetter


try:
    from ipapy import UNICODE_TO_IPA as ipa_name
except:
    def ipa_name(*args):
        return "IPA mapper not in use"


def resolve_ipa_desc(char):
    try:
        return ipa_name[char].name
    except:
        return 'no description for IPA character'


def find_percentile_phonemes(dist, percentile_threshold):
    result = set()
    current_percentile = 0.0

    items = sorted(dist.items(), key=itemgetter(1), reverse=True)
    for phoneme, probability in items:
        result.add(phoneme)
        current_percentile += probability
        if current_percentile * 100.0 >= percentile_threshold:
            break
    result.remove(u'WB')
    return result


def find_most_probable_mappings(dist_a, dist_b, phoneme_similarities,
                                diff_threshold, min_replacement_p, similarity_threshold,
                                logger, lang_a_name='A', lang_b_name='B'):
    def is_missing(phoneme):
        pb = dist_b.get(phoneme, 0.0)
        p_diff = abs(pa - pb)
        if pb < 0.0000000001 and pa > pb and p_diff > diff_threshold:
            logger.info(u'Phoneme {} is missing from language {}; rel. frequency in {}: {} vs {}: {}'
                        .format(phoneme, lang_b_name, lang_a_name, pa, lang_b_name, pb))
            return True, p_diff
        else:
            return False, p_diff

    missing_candidates = collections.defaultdict(list)
    result = []
    for phoneme_a, pa in dist_a.iteritems():
        if phoneme_a == u'WB':
            continue

        phoneme_missing, p_diff = is_missing(phoneme_a)
        candidates = []
        for phoneme_b, probability in dist_b.iteritems():
            if phoneme_b == u'WB':
                continue
            if probability > min_replacement_p:
                similarity = phoneme_similarities.get((phoneme_a, phoneme_b), 0)
                if similarity > 0:
                    candidates.append((phoneme_b, similarity))

        candidates = sorted(candidates, key=itemgetter(1), reverse=True)

        if phoneme_missing:
            logger.info(u'Candidates in {} for {} ({})'.format(lang_b_name, phoneme_a, resolve_ipa_desc(phoneme_a)))
        for candidate in candidates:
            if phoneme_missing:
                logger.info(u'  Phoneme {} with similarity of {} ({})'
                            .format(candidate[0], candidate[1], resolve_ipa_desc(candidate[0])))
            missing_candidates[phoneme_a].append((phoneme_missing, p_diff, candidate[0], candidate[1],
                                                  dist_a.get(phoneme_a, 0), dist_b.get(phoneme_a, 0),
                                                  dist_a.get(candidate[0], 0), dist_b.get(candidate[0], 0)))

        suitable_candidates = [c for c in candidates if c[1] >= similarity_threshold]
        if phoneme_missing:
            if len(suitable_candidates) > 0:
                result.append((phoneme_a, suitable_candidates[0][0]))
            else:
                logger.info(u'No suitable candidates (similarity must not be less than {})'.format(similarity_threshold))

    return result, missing_candidates


def read_phoneme_similarities(mapping_file_path):
    result = {}
    with codecs.open(mapping_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.replace('\n', '').split('\t')
            result[(parts[0], parts[1])] = float(parts[2])
    return result
