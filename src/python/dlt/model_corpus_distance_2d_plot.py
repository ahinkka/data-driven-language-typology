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
import sys

from dlt.model_corpus_distance_utils import read_model_corpus_distance, averaged_language_distances, \
    distance_dict_to_r_dist

stdin8 = codecs.getwriter('utf-8')(sys.stdin)
stdout8 = codecs.getwriter('utf-8')(sys.stdout)
stderr8 = codecs.getwriter('utf-8')(sys.stderr)


def r_output(stream, distances, figure_title, distance_measure, method='isomds'):
    print(distance_dict_to_r_dist(distances, "distm", tmp_matrix_name='tmp'), file=stream)

    # Maybe at some point try 3d scatterplots... :D
    # https://statmethods.wordpress.com/2012/01/30/getting-fancy-with-3-d-scatterplots/

    if method == u'isomds':
        # https://stat.ethz.ch/R-manual/R-devel/library/MASS/html/isoMDS.html
        print(u'library(MASS)', file=stream)
        print(u'fit <- isoMDS(distm, k=2)', file=stream)
        print(u'stress <- fit$stress', file=stream)
    elif method == u'classicmds':
        # https://stat.ethz.ch/R-manual/R-devel/library/stats/html/cmdscale.html
        print(u'fit <- cmdscale(distm, eig=TRUE, k=2)', file=stream)
    else:
        raise Exception("Unknown argument for method: {}".format(method))

    print(u'x <- fit$points[,1]', file=stream)
    print(u'y <- fit$points[,2]', file=stream)

    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=5, height=5, pointsize=12)', file=stream)

    # If the title begins with "R ", treat it as a legal R expression, otherwise escape the title
    if figure_title[0:2] == u'R ':
        figure_title = figure_title[2:]
    else:
        figure_title = u"'" + figure_title + u"'"

    print(u'plot(x, y, xlab="", ylab="", main={}, type="n", axes=FALSE, asp=1)'
          .format(figure_title), file=stream)

    print(u"""for (i in 1:length(tmp)) {
  for (j in 1:length(tmp)) {
    if (i != j) {
      lines(c(x[i], x[j]), y=c(y[i], y[j]), cex=.7, lwd=.2, col="gray", type="l")
    }
  }
}""", file=stream)

    print(u'text(x, y, labels=row.names(tmp), cex=.7)', file=stream)

    if method == 'isomds':
        # https://stat.ethz.ch/R-manual/R-devel/library/graphics/html/mtext.html
        print(u'mtext(paste("MDS stress =", format(stress, digits=3)), side=1, adj=1, cex=.5)', file=stream)

    # http://cognitionandreality.blogspot.fi/2015/04/computing-fit-of-mds-solution-using-r.html
    print(u'mds_distances <- dist(fit$points, diag=TRUE, upper=TRUE)', file=stream)
    print(u'r <- cor(c(distm), c(mds_distances))', file=stream)
    print(u'r_squared <- r * r', file=stream)
    print(u'mtext(bquote(R^2 == .(format(r_squared, digits=3))), side=1, adj=0, cex=.5)', file=stream)
    print(u'mtext("Distance measure: {}", side=1, adj=0, padj=1.2, cex=.5)'.format(distance_measure), file=stream)

    #print(u'degrees_of_freedom = NROW(c(mds_distances)) - 2', file=stream)
    #print(u'f_value <- r_squared / ((1 - r_squared) / degrees_of_freedom)', file=stream)
    # print(u'pf(f_value, 1, degrees_of_freedom, lower.tail = FALSE)', file=stream)

    #print(u'mtext(paste("F:", format(f_value, digits=5)), side=1, cex=.5)', file=stream)


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
