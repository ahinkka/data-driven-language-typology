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
import sys

from dlt.model_corpus_distance_utils import read_model_corpus_distance, round_to_base
from dlt.model_corpus_distance_utils import averaged_language_distances

stdin8 = codecs.getwriter('utf-8')(sys.stdin)
stdout8 = codecs.getwriter('utf-8')(sys.stdout)
stderr8 = codecs.getwriter('utf-8')(sys.stderr)


def find_best_pair(distance_map):
    return min(distance_map.items(), key=lambda x: x[1])


def dist_dict_with_pair_merged(dist, pair):
    nodes = set([k[0] for k in dist.keys()]) | \
            set([k[1] for k in dist.keys()])

    member_a = pair[0]
    member_b = pair[1]

    def other_one(pair, not_this):
        if pair[0] == not_this:
            return pair[1]
        else:
            return pair[0]

    result = {}
    language_distances = collections.defaultdict(list)
    for k, v in dist.iteritems():
        if k == pair:
            continue
        if member_a in k:
            other = other_one(k, member_a)
            language_distances[other].append(v)
        elif member_b in k:
            other = other_one(k, member_b)
            language_distances[other].append(v)
        else:
            result[k] = v

    merged_key = tuple(sorted([member_a, member_b]))
    for other, distances in language_distances.iteritems():
        key = tuple(sorted([other, merged_key]))
        result[key] = sum(distances) / float(len(distances))

    return result


def cluster(dist):
    result = []
    distances = {}
    current_dist = dist
    while len(current_dist) > 0:
        best_pair = find_best_pair(current_dist)
        result.append(best_pair[0])
        distances[best_pair[0]] = best_pair[1]
        current_dist = dist_dict_with_pair_merged(current_dist, best_pair[0])
    # result.append(tuple(sorted(current_dist.keys()[0])))
    return result, distances


def r_output(stream, clusters, distances, figure_title, ylab):
    """
http://stackoverflow.com/questions/2310913/how-do-i-manually-create-a-dendrogram-or-hclust-object-in-r

a <- list()  # initialize empty object
# define merging pattern: 
#    negative numbers are leaves, 
#    positive are merged clusters (defined by row number in $merge)
a$merge <- matrix(c(-1, -2,
                    -3, -4,
                     1,  2), nc=2, byrow=TRUE ) 
a$height <- c(1, 1.5, 3)    # define merge heights
a$order <- 1:4              # order of leaves(trivial if hand-entered)
a$labels <- LETTERS[1:4]    # labels of leaves
class(a) <- "hclust"        # make it an hclust object
plot(a)                     # look at the result   

#convert to a dendrogram object if needed
ad <- as.dendrogram(a)
    """
    current_node_number = 1
    node_numbers = {}
    print(u"a <- list()", file=stream)
    #    negative numbers are leaves, 
    #    positive are merged clusters (defined by row number in $merge)
    print(u"a$merge <- matrix(c(", file=stream)
    for cluster in clusters:
        left, right = cluster

        if not isinstance(left, tuple) and left not in node_numbers:
            node_numbers[left] = current_node_number
            current_node_number += 1

        if not isinstance(right, tuple) and right not in node_numbers:
            node_numbers[right] = current_node_number
            current_node_number += 1

    printable_pairs = []
    cluster_rows = {}
    current_row = 1
    labels = []
    ordered_distances = []
    for cluster in clusters:
        left, right = cluster

        print("Cluster: {}, distance {}".format(cluster, distances[left, right]), file=stderr8)
        ordered_distances.append(distances[left, right])
        if isinstance(left, tuple) and isinstance(right, tuple):
            left_row = cluster_rows[left]
            right_row = cluster_rows[right]
            printable_pairs.append((left_row, right_row))

            print("  Trunk row: {}".format(current_row), file=stderr8)
            print("    Left leaf: {}".format(left_row), file=stderr8)
            print("    Right leaf: {}".format(right_row), file=stderr8)

            cluster_rows[cluster] = current_row
            current_row += 1
        elif isinstance(left, tuple) and not isinstance(right, tuple):
            if right not in labels:
                labels.append(right)
                print("    Right label number: {}".format(len(labels)), file=stderr8)
            left_row = cluster_rows[left]
            right_num = node_numbers[right]
            print("  Trunk-leaf row: {}".format(current_row), file=stderr8)
            print("    Left trunk: {}".format(left_row), file=stderr8)
            print("    Right leaf: {}".format(-right_num), file=stderr8)
            printable_pairs.append((left_row, -right_num))
            cluster_rows[cluster] = current_row
            current_row += 1
        elif not isinstance(left, tuple) and isinstance(right, tuple):
            if left not in labels:
                labels.append(left)
                print("    Left label number: {}".format(len(labels)), file=stderr8)
            right_row = cluster_rows[right]
            left_num = node_numbers[left]
            print("  Trunk-leaf row: {}".format(current_row), file=stderr8)
            print("    Left leaf: {}".format(-left_num), file=stderr8)
            print("    Right trunk: {}".format(right_row), file=stderr8)
            printable_pairs.append((-left_num, right_row))
            cluster_rows[cluster] = current_row
            current_row += 1
        else:
            left_num = node_numbers[left]
            right_num = node_numbers[right]
            print("  Leaf row: {}".format(current_row), file=stderr8)
            print("    Left number: {}".format(-left_num), file=stderr8)
            print("    Right number: {}".format(-right_num), file=stderr8)

            if left not in labels:
                labels.append(left)
                print("    Left label number: {}".format(len(labels)), file=stderr8)
            if right not in labels:
                labels.append(right)
                print("    Right label number: {}".format(len(labels)), file=stderr8)
            printable_pairs.append((-left_num, -right_num))
            cluster_rows[cluster] = current_row
            current_row += 1

    print(u", \n".join([u"{}, {}".format(a, b) for a, b in printable_pairs]),
          file=stream)
    print("), nc=2, byrow=TRUE)", file=stream)

    # print(u"a$order <- 1:{}".format(len(printable_pairs) + 1), file=stream)
    print(u"a$height <- c({})".format(", ".join((str(d) for d in ordered_distances))), file=stream)
    # a$order <- 1:4              # order of leaves(trivial if hand-entered)
    print(u"a$labels <- c({})".format(", ".join([u'"{}"'.format(lab) for lab in labels])),
          file=stream)
    print(u'class(a) <- "hclust"', file=stream)
    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=5, height=4, pointsize=12)', file=stream)
    # print(u'plot(as.dendrogram(a), main="Language clusters", ' +

    # If the title begins with "R ", treat it as a legal R expression, otherwise escape the title
    if figure_title[0:2] == u'R ':
        figure_title = figure_title[2:]
    else:
        figure_title = u"'" + figure_title + u"'"

    ylim_padding = 5
    if max(ordered_distances) < ylim_padding:
        ylim_padding = max(ordered_distances) + 1
    print(u"plot(as.dendrogram(a), main={}, ".format(figure_title) +
          u'ylab="{}", '.format(ylab) +
          'ylim=c(0, {}))'.format(round_to_base(max(ordered_distances)) + ylim_padding), file=stream)
    print(u"dev.off()", file=stream)


def main(input_file, figure_title):
    model_corpus_distance = read_model_corpus_distance(input_file)
    dist = averaged_language_distances(model_corpus_distance)
    clusters, distances = cluster(dist)
    # print(clusters, file=stderr8)
    r_output(stdout8, clusters, distances, figure_title, 'Distance')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Make a dendrogram from a model's distance on a corpus")
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'),
                        default=stdin8)
    parser.add_argument('--title', type=str, metavar='FIGURE_TITLE',
                        help='Main title for figure', default="Distance dendrogram")
    args = parser.parse_args()
    main(args.input, args.title)
