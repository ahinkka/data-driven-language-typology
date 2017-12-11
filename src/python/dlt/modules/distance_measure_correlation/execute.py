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

import subprocess

import codecs
import operator
import os
from pimlico.core.modules.base import BaseModuleExecutor

from dlt.model_corpus_distance_utils import distance_dict_to_r_matrix
from dlt.utils import working_directory, collect_distances_names


def correlation_plot_r_output(stream, a_distances, b_distances, a_label, b_label):
    print(u'a <- c({})'.format(', '.join([str(d) for d in a_distances])), file=stream)
    print(u'b <- c({})'.format(', '.join([str(d) for d in b_distances])), file=stream)

    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=5, height=5, pointsize=12)', file=stream)

    """ print(u'plot(a, pch=1)', file=stream)
    print(u'par(new = TRUE)', file=stream)
    print(u'plot(b, axes = FALSE, bty = "n", xlab = "", ylab = "", pch=2)', file=stream)
    print(u'axis(side=4, at = pretty(range(b)))', file=stream)
    print(u'mtext("z", side=4, line=3)', file=stream) """

    log_parts = []
    if 'perplexity' in b_label.lower():
        log_parts.append('x')
    if 'perplexity' in a_label.lower():
        log_parts.append('y')

    print(u'plot(a ~ b, log="{}", ylab="{}", xlab="{}")'
          .format(''.join(log_parts), a_label, b_label), file=stream)
    print(u'grid()', file=stream)

    # Another model, from https://datascienceplus.com/fitting-polynomial-regression-r/
    #print(u'set.seed(20)', file=stream)
    #print(u'model <- lm(a ~ poly(b, 3))', file=stream)
    #print(u"predicted.intervals <- predict(model, data.frame(x=b),interval='confidence', level=0.99)", file=stream)
    #print(u"lines(b,predicted.intervals[,1],col='deepskyblue4',lwd=3)", file=stream)
    #print(u"lines(b,predicted.intervals[,2],col='red',lwd=1)", file=stream)
    #print(u"lines(b,predicted.intervals[,3],col='green',lwd=1)", file=stream)
    #print(u'legend("bottomright",c("Observ.","Signal","Predicted"), col=c("deepskyblue4","red","green"), lwd=3)', file=stream)

    # Bog standard linear regression model
    print(u'model <- lm(a ~ b)', file=stream)
    print(u'r_squared <- summary(model)$adj.r.squared', file=stream)
    print(u'abline(model, untf=TRUE)', file=stream)
    print(u'mtext(bquote(R^2 == .(format(r_squared, digits=3))), side=1, adj=0, padj=5)', file=stream)

    print(u"dev.off()", file=stream)


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        distances_a = self.info.get_input("distances_a")
        distances_b = self.info.get_input("distances_b")
        model_corpus_distances_a, lang_names = collect_distances_names(distances_a)
        model_corpus_distances_b, _ = collect_distances_names(distances_b)

        model_corpus_distances_a = {k: v for k, v in model_corpus_distances_a.items() if k[0] != k[1]}
        model_corpus_distances_b = {k:v for k, v in model_corpus_distances_b.items() if k[0] != k[1]}

        all_languages = set()
        for a, b in model_corpus_distances_a.iterkeys():
            all_languages.add(a)
            all_languages.add(b)

        sorted_a = sorted(model_corpus_distances_a.items(), key=operator.itemgetter(1))
        if self.info.options["upper_threshold_a"] > 0:
            sorted_a = [(i, j) for i, j in sorted_a if j <= self.info.options["upper_threshold_a"]]

        remove_from_a_indices = []
        ordered_b = []
        for idx, pair in enumerate(sorted_a):
            k, v = pair
            b_distance = model_corpus_distances_b[k]
            if self.info.options["upper_threshold_b"] > 0 and b_distance > self.info.options["upper_threshold_b"]:
                remove_from_a_indices.append(idx)
            else:
                ordered_b.append((k, b_distance))
        for idx in reversed(remove_from_a_indices):
            del sorted_a[idx]

        output_dir = self.info.get_absolute_output_dir("correlation_plot")
        try:
            os.mkdir(output_dir)
        except:
            pass
        with working_directory(output_dir):
            r_filename = u'correlation_plot.R'
            svg_filename = u'correlation_plot.svg'
            try:
                os.remove(r_filename)
            except:
                pass
            with codecs.open(r_filename, 'w', encoding='utf-8') as f:
                correlation_plot_r_output(f,
                                          [b for a, b in sorted_a],
                                          [b for a, b in ordered_b],
                                          self.info.options["distance_measure_a"],
                                          self.info.options["distance_measure_b"])

                try:
                    os.remove(svg_filename)
                except:
                    pass
                subprocess.check_call('cat {} | Rscript - {}'.format(r_filename, svg_filename), shell=True)
                self.log.info(u'Correlation plot written to {}'.format(os.path.join(output_dir, svg_filename)))
