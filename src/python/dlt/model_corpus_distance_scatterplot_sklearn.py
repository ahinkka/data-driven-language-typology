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

import argparse
import codecs
import collections
import math
import operator
import sys

import numpy as np

from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection

from sklearn import manifold
from sklearn.metrics import euclidean_distances, r2_score
from sklearn.decomposition import PCA

from dlt.model_corpus_distance_utils import read_model_corpus_distance

stdin8 = codecs.getwriter('utf-8')(sys.stdin)
stdout8 = codecs.getwriter('utf-8')(sys.stdout)
stderr8 = codecs.getwriter('utf-8')(sys.stderr)


def per_language_distances(model_corpus_distance):
    languages = set()
    for a, b in model_corpus_distance.iterkeys():
        languages.add(a)
        languages.add(b)

    result = collections.defaultdict(list)
    for k, distance in model_corpus_distance.iteritems():
        a, b = k
        result[a].append((b, distance))

    return {k: sorted(v, key=operator.itemgetter(1)) for k, v in result.iteritems()}


def language_distance_avg(model_corpus_distance):
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


def main(input_file, interactive, output, title):
    model_corpus_distance = read_model_corpus_distance(input_file)
    per_lang = per_language_distances(model_corpus_distance)

    langs = sorted(per_lang.keys())
    lang_indices = {v: k for k, v in enumerate(langs)}
    weights = np.zeros((len(langs), len(langs) + 1), np.float)
    for lang_a in langs:
        ai = lang_indices[lang_a]
        for lang_b in langs:
            if lang_a == lang_b:
                continue
            bi = lang_indices[lang_b]
            weights[ai, bi] = model_corpus_distance[(lang_a, lang_b)]

    seed = np.random.RandomState(seed=3)
    mds = manifold.MDS(n_components=2, max_iter=3000, eps=1e-9, random_state=seed,
                       dissimilarity="precomputed", n_jobs=1)
    nmds = manifold.MDS(n_components=2, metric=False, max_iter=3000, eps=1e-12,
                        dissimilarity="precomputed", random_state=seed, n_jobs=1,
                        n_init=1)
    similarities = euclidean_distances(weights)

    mds_fit = mds.fit(similarities)
    pos = mds_fit.embedding_
    npos = nmds.fit_transform(similarities, init=pos)
    stress = mds_fit.stress_

    # R²: http://scikit-learn.org/stable/modules/generated/sklearn.metrics.r2_score.html
    #  1. calculate distances between all nodes in the end result
    #  2. feed them into sklearn.metrics.r2_score
    expected_distances = []
    mds_distances = []
    for lang1 in langs:
        idx1 = lang_indices[lang1]
        x1, y1 = pos[idx1]
        for lang2 in langs:
            idx2 = lang_indices[lang2]
            # x2, y2 = pos[idx2]
            x2, y2 = npos[idx2]
            euclidean_dist = math.sqrt(math.exp(x1 - x2) + math.exp(y1 - y2))

            expected_distances.append(weights[idx1, idx2])
            mds_distances.append(euclidean_dist)

    expected_distances = [i * (1 / float(max(expected_distances)))
                          for i in expected_distances]
    mds_distances = [i * (1 / float(max(mds_distances)))
                     for i in mds_distances]

    r2 = r2_score(expected_distances, mds_distances, sample_weight=None, multioutput=None)
    print(u"Stress: {}\nR²: {}".format(stress, r2), file=stderr8)
    # End of R² calculation

    # Rescale data
    # pos *= np.sqrt((weights ** 2).sum()) / np.sqrt((pos ** 2).sum())
    npos *= np.sqrt((weights ** 2).sum()) / np.sqrt((npos ** 2).sum())

    clf = PCA(n_components=2)
    pos_orig = clf.fit_transform(weights)
    # pos = clf.fit_transform(pos)
    npos = clf.fit_transform(npos)

    fig = plt.figure(1)
    ax = plt.axes([0., 0., 1., 1.])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    s = 100
    plt.scatter(npos[:, 0], npos[:, 1], color='black', s=s, lw=0, label='MDS')
    # plt.legend(scatterpoints=1, loc='best', shadow=False)

    similarities = similarities.max() / similarities * 100
    similarities[np.isinf(similarities)] = 0

    start_idx, end_idx = np.where(npos)
    segments = [[npos[i, :], npos[j, :]]
                for i in range(len(npos)) for j in range(len(npos))]
    values = np.abs(similarities)
    lc = LineCollection(segments,
                        zorder=0, cmap=plt.cm.Blues,
                        norm=plt.Normalize(0, values.max()))
    lc.set_array(similarities.flatten())
    lc.set_linewidths(0.5 * np.ones(len(segments)))
    ax.add_collection(lc)
    ax.margins(0.11)

    for label, x, y in zip(langs, npos[:, 0], npos[:, 1]):
        plt.annotate(
            label, 
            xy = (x, y), xytext = (-20, 5),
            textcoords = 'offset points', ha='right', va='top',
            bbox = dict(boxstyle='circle, pad=0.6', fc='white', alpha=0.5),
            arrowprops = dict(arrowstyle='-', connectionstyle='arc3,rad=0'))

    fig.suptitle(title, fontsize=14, fontweight='bold')

    if interactive:
        plt.show()
    else:
        plt.savefig(output, dpi=600)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Make a scatter plot from languages")
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'),
                        default=stdin8)
    parser.add_argument('output', nargs='?', type=str)
    parser.add_argument('--title', default="", type=str,
                        help="Title for plot.")
    parser.add_argument('--interactive', default=False, action="store_true",
                        help="Show the interactive Matplotlib viewer")

    args = parser.parse_args()

    if not args.interactive and not args.output:
        parser.error("In non-interactive use output file is required.")
    main(args.input, args.interactive, args.output, args.title)
