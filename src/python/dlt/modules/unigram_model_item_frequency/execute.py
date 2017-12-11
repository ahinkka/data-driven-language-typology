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
import os
from pimlico.core.modules.base import BaseModuleExecutor

from dlt.utils import working_directory
from ngram.models import UnigramModel


def log_linear_fit_plot_r_output(stream, item_frequencies):
    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=5, height=5, pointsize=12)', file=stream)
    print(u'sorted_frequencies <- sort(c({}), decreasing=TRUE)\n'
          .format(u', '.join(str(i) for i in item_frequencies)), file=stream)
    print(u'ranks <- seq_along(sorted_frequencies)', file=stream)

    print(u'linear_estimate = lm(sorted_frequencies ~ ranks)', file=stream)
    print(u'log_linear_estimate = lm(sorted_frequencies ~ log(ranks))', file=stream)
    #print(u'log_log_estimate = lm(log(sorted_frequencies) ~ log(ranks))', file=stream)

    print(u'plot(sorted_frequencies, ylab="log(frequency)", xlab="log(rank)", main="Item frequency as function of rank", log="xy")',
          file=stream)
    print(u'lines(ranks, predict(linear_estimate), col="lightgray")', file=stream)
    print(u'lines(ranks, predict(log_linear_estimate), col="darkgray")', file=stream)
    #print(u'lines(ranks, predict(log_log_estimate), col="black")', file=stream)


def zipf_plot_r_output(stream, item_frequencies):
    print(u'library(zipfR)', file=stream)
    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=5, height=5, pointsize=12)', file=stream)
    print(u'observed_tfl <- tfl(c({}))\n'.format(u', '.join(str(i) for i in item_frequencies)), file=stream)

    print(u'plot(sort(observed_tfl$f, decreasing=TRUE), log="y", xlab="rank", ylab="frequency")', file=stream)

    print(u'''plotZipf <- function(observed) {
    observed_zm <- lnre("zm", tfl2spc(observed))
    k <- 1:length(observed$f)
    f <- tqlnre(observed_zm, k) * N(observed)
    lines(k, f, lwd=2, col="gray")
}

tryCatch(plotZipf(observed_tfl), error = function(e) { print("Zipf line not drawn") })
''', file=stream)


def other_zipf_plot_r_output(stream, item_frequencies):
    freq_sum = sum(item_frequencies)

    def zipf(n, count):
        return count * (1.0 / float(n))

    nums = None
    multiplier = 1.0
    while nums is None or sum(nums) > freq_sum:
        nums = [zipf(i, multiplier * freq_sum) for i in xrange(1, len(item_frequencies) + 1)]
        multiplier -= 0.01

    estimated_counts = [str(int(n)) for n in nums]

    if len(item_frequencies) != len(estimated_counts):
        raise Exception("Actual and simulated lengths differ")

    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=5, height=5, pointsize=12)', file=stream)
    print(u'sorted_frequencies <- sort(c({}), decreasing=TRUE)\n'
          .format(u', '.join(estimated_counts)), file=stream)
    print(u'ranks <- seq_along(sorted_frequencies)', file=stream)

    print(u'linear_estimate = lm(sorted_frequencies ~ ranks)', file=stream)
    print(u'log_linear_estimate = lm(sorted_frequencies ~ log(ranks))', file=stream)
    #print(u'log_log_estimate = lm(log(sorted_frequencies) ~ log(ranks))', file=stream)

    print(u'plot(sorted_frequencies, ylab="log(frequency)", xlab="log(rank)", main="Item frequency as function of rank", log="xy")',
          file=stream)
    print(u'lines(ranks, predict(linear_estimate), col="lightgray")', file=stream)
    print(u'lines(ranks, predict(log_linear_estimate), col="darkgray")', file=stream)


def _make_plot(plot_type, plot_function, model):
    r_filename = u'{}_plot.R'.format(plot_type)
    svg_filename = u'{}_plot.svg'.format(plot_type)
    try:
        os.remove(r_filename)
    except:
        pass
    with codecs.open(r_filename, 'w', encoding='utf-8') as f:
        plot_function(f, list([v for k, v in model.token_counts.iteritems() if k != u'WB']))

        try:
            os.remove(svg_filename)
        except:
            pass
        subprocess.check_call('cat {} | Rscript - {}'.format(r_filename, svg_filename), shell=True)
        return svg_filename


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        # https://stat.ethz.ch/pipermail/r-help/2010-October/256608.html
        model = self.info.get_input("model")

        with codecs.open(model.absolute_path, 'r', encoding='utf-8') as f:
            unigram_model = UnigramModel.read_from_file(f)

        model_language = model.module.module_variables["lang_code"]

        output_dir = self.info.get_absolute_output_dir("plot")
        try:
            os.mkdir(output_dir)
        except:
            pass
        with working_directory(output_dir):
            out_file = _make_plot("zipf", zipf_plot_r_output, unigram_model)
            self.log.info(u'Zipf plot written to {}'.format(os.path.join(output_dir, out_file)))

            out_file = _make_plot("log_linear_fit", log_linear_fit_plot_r_output, unigram_model)
            self.log.info(u'Log linear fit plot written to {}'.format(os.path.join(output_dir, out_file)))

            out_file = _make_plot("other_zipf", other_zipf_plot_r_output, unigram_model)
            self.log.info(u'Other Zipf plot written to {}'.format(os.path.join(output_dir, out_file)))
