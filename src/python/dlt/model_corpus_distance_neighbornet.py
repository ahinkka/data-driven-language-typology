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
import sys

import codecs

from dlt.model_corpus_distance_utils import distance_dict_to_r_dist, read_model_corpus_distance, \
    averaged_language_distances

stdin8 = codecs.getwriter('utf-8')(sys.stdin)
stdout8 = codecs.getwriter('utf-8')(sys.stdout)
stderr8 = codecs.getwriter('utf-8')(sys.stderr)


def r_output(stream, distances, figure_title, distance_measure):
    """
    Page 35 of:
    https://cran.r-project.org/web/packages/phangorn/phangorn.pdf
    """
    print(u'rm(list=ls())', file=stream)
    print(u'library(phangorn)', file=stream)
    print(distance_dict_to_r_dist(distances, "distm"), file=stream)
    print(u'nnet <- neighborNet(distm)', file=stream)
    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=5, height=5, pointsize=12)', file=stream)

    # If the title begins with "R ", treat it as a legal R expression, otherwise escape the title
    if figure_title[0:2] == u'R ':
        figure_title = figure_title[2:]
    else:
        figure_title = u"'" + figure_title + u"'"

    print(u'plot(nnet, "2D")', file=stream) #, main={}, '.format(figure_title), file=stream)
    print(u'title(main={})'.format(figure_title), file=stream)
    print(u'mtext("Distance measure: {}", side=1, adj=0, cex=.5)'.format(distance_measure), file=stream)
    print(u"dev.off()", file=stream)


def main(input_file, figure_title):
    model_corpus_distance = read_model_corpus_distance(input_file)
    dist = averaged_language_distances(model_corpus_distance)
    r_output(stdout8, dist, figure_title)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Make a NeighborNet from a model's distance on a corpus")
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'),
                        default=stdin8)
    parser.add_argument('--title', type=str, metavar='FIGURE_TITLE',
                        help='Main title for figure', default="Distance dendrogram")
    args = parser.parse_args()
    main(args.input, args.title)
