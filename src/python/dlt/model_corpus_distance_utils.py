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


import collections


def round_to_base(x, base=5):
    return int(base * round(float(x) / base))


def read_model_corpus_distance(input_file):
    result = {}
    for line in input_file:
        model, corpus, distance = line.strip().split('\t')
        distance = float(distance)
        result[(model, corpus)] = distance
    return result


def averaged_language_distances(model_corpus_distance):
    language_distances = collections.defaultdict(list)
    for k, v in model_corpus_distance.iteritems():
        key = tuple(sorted([k[0], k[1]]))
        language_distances[key].append(v)
    result = {}
    for k, v in language_distances.iteritems():
        if k[0] == k[1]:
            continue
        result[k] = sum(v) / float(len(v))

    return result


def distance_dict_to_r_matrix(distances, result_r_variable_name, language_comparator=None,
                              for_dist=False):
    result = u''
    all_languages = set()
    for a, b in distances.iterkeys():
        all_languages.add(a)
        all_languages.add(b)

    if language_comparator is None:
        ordered_languages = sorted(all_languages)
    else:
        ordered_languages = sorted(all_languages, cmp=language_comparator)

    result += u'{} <- matrix(c('.format(result_r_variable_name)
    values = []
    for l1 in ordered_languages:
        for l2 in ordered_languages:
            if l1 == l2:
                if for_dist:
                    values.append(0.0)
                else:
                    values.append(distances[(l1, l2)])
            elif l2 > l1:
                key = tuple(sorted([l1, l2]))
                values.append(distances[key])
            elif l1 > l2:
                if for_dist:
                    values.append('NA')
                else:
                    values.append(distances[(l1, l2)])

    result += u', '.join([str(i) for i in values])
    result += '), nrow={}, ncol={})\n'.format(len(ordered_languages), len(ordered_languages))

    result += u'colnames({}) <- c({})\n'\
        .format(result_r_variable_name, u', '.join([u'"{}"'.format(i) for i in ordered_languages]))
    result += u'rownames({}) <- c({})\n'\
          .format(result_r_variable_name, u', '.join([u'"{}"'.format(i) for i in ordered_languages]))

    return result


def distance_dict_to_r_distance_vector(distances, result_r_variable_name, language_comparator=None):
    result = u''
    all_languages = set()
    for a, b in distances.iterkeys():
        all_languages.add(a)
        all_languages.add(b)

    if language_comparator is None:
        ordered_languages = sorted(all_languages)
    else:
        ordered_languages = sorted(all_languages, cmp=language_comparator)

    result += u'{} <- c('.format(result_r_variable_name)
    values = []
    language_pairs = []
    for l1 in ordered_languages:
        for l2 in ordered_languages:
            if l1 == l2:
                key = (l1, l2)
                if key not in distances:
                    continue
                values.append(distances[key])
                language_pairs.append(u"{}-{}".format(l1, l2))
            elif l2 > l1:
                key = tuple(sorted([l1, l2]))
                values.append(distances[key])
                language_pairs.append(u"{}-{}".format(*key))
            elif l1 > l2:
                values.append(distances[(l1, l2)])
                language_pairs.append(u"{}-{}".format(l1, l2))

    result += u', '.join([str(i) for i in values])
    result += ')\n'

    result += u'names({}) <- c({})\n'\
        .format(result_r_variable_name, u', '.join([u'"{}"'.format(i) for i in language_pairs]))

    return result


def distance_dict_to_r_dist(distances, result_r_variable_name, tmp_matrix_name='tmp_distance_matrix'):
    result = u''

    result += distance_dict_to_r_matrix(distances, tmp_matrix_name, for_dist=True)
    result += u'{} <- as.dist({})'.format(result_r_variable_name, tmp_matrix_name)

    return result