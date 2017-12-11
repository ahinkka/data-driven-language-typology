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

import json
import shutil
import subprocess

import codecs
import operator
import os
from pimlico.core.modules.base import BaseModuleExecutor

from dlt.utils import working_directory


def _read_size(path):
    with open(path, 'r') as f:
        return int(json.load(f)[u'size'])


def _r_vector_export_output(stream, variable_name, values, labels):
    print(u'{} <- c({})'
          .format(variable_name,
                  ", ".join([str(i) for i in values])),
          file=stream)
    print(u'names({}) <- c({})'
          .format(variable_name, ", ".join([u"\"{}\"".format(label) for label in labels])),
          file=stream)


def _r_single_plot_output(stream, figure_title, language_labels, values):
    print(u"sizes <- c({})"
          .format(", ".join([str(i) for i in values])),
          file=stream)
    print(u"names(sizes) <- c({})"
          .format(", ".join([u"\"{}\"".format(lab) for lab in language_labels])),
          file=stream)
    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=8, height=4, pointsize=12)', file=stream)
    #print(u'par(mar = c(7, 4, 4, 2) + 0.1)', file=stream)
    print(u'barplot(sizes, main="{}", las=2)'.format(figure_title), file=stream)
    print(u'grid()', file=stream)


def _r_dual_plot_output(stream, figure_title, language_labels, values):
    print(u"d <- data.frame({})"
          .format(", ".join([u"c({}, {})".format(t, l) for t, l in values])),
          file=stream)
    print(u"colnames(d) <- c({})"
          .format(", ".join([u"\"{}\"".format(lab) for lab in language_labels])),
          file=stream)
    print(u"rownames(d) <- c(\"test\", \"learn\")", file=stream)
    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=8, height=4, pointsize=12)', file=stream)
    # https://cran.r-project.org/doc/FAQ/R-FAQ.html#How-can-I-create-rotated-axis-labels_003f
    print(u'par(mar = c(7, 4, 4, 2) + 0.1)', file=stream)
    print(u'barplot(as.matrix(d), main="{}", beside = TRUE, xaxt = "n", xlab = "", legend = rownames(d))'
          .format(figure_title), file=stream)
    print(u'indices <- seq(1:(3 * length(d)))[seq(1, 3 * length(d), 3)]', file=stream)
    print(u'text(indices + 1, par("usr")[3] - 0.25, srt = 45, adj = 1, labels = colnames(d), xpd = TRUE)',
          file=stream)
    print(u'grid()', file=stream)


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        figure_title = self.info.options["title"]
        test_set_sizes = {}
        learning_set_sizes = {}
        lang_names = {}

        for s in self.info.get_input("test_set_size"):
            lang = s.module.module_variables["lang_code"]
            lang_names[lang] = s.module.module_variables["lang"]
            s = _read_size(s.absolute_path)
            test_set_sizes[lang] = s

        for s in self.info.get_input("learning_set_size"):
            lang = s.module.module_variables["lang_code"]
            lang_names[lang] = s.module.module_variables["lang"]
            s = _read_size(s.absolute_path)
            learning_set_sizes[lang] = s

        output_dir = self.info.get_absolute_output_dir("summary")
        try:
            shutil.rmtree(output_dir)
            os.makedirs(output_dir)
        except:
            pass

        # Alphabetical
        labels = []
        values = []
        for lang in sorted(lang_names.keys()):
            t, l = test_set_sizes[lang], learning_set_sizes[lang]
            labels.append(lang_names[lang])
            values.append((t, l))
        self.generate_barplot(figure_title, 'alphabetical', labels, output_dir, values, dual=True)

        # By test
        labels = []
        values = []
        for lang in [i[0] for i in sorted(test_set_sizes.items(), key=operator.itemgetter(1))]:
            t, l = test_set_sizes[lang], learning_set_sizes[lang]
            labels.append(lang_names[lang])
            values.append((t, l))
        self.generate_barplot(figure_title, 'single_test_sorted', labels, output_dir, [v[0] for v in values])
        self.generate_barplot(figure_title, 'both_test_sorted', labels, output_dir, values, dual=True)

        # By learn
        labels = []
        values = []
        for lang in [i[0] for i in sorted(learning_set_sizes.items(), key=operator.itemgetter(1))]:
            t, l = test_set_sizes[lang], learning_set_sizes[lang]
            labels.append(lang_names[lang])
            values.append((t, l))
        self.generate_barplot(figure_title, 'single_learn_sorted', labels, output_dir, [v[1] for v in values])
        self.generate_barplot(figure_title, 'both_learn_sorted', labels, output_dir, values, dual=True)

        # R export output
        output_dir = self.info.get_absolute_output_dir("r_output")
        shutil.rmtree(output_dir, ignore_errors=True)
        os.makedirs(output_dir)

        with codecs.open(os.path.join(output_dir, "learn.R"), 'w', encoding='utf-8') as f:
            labels = []
            values = []
            for lang in sorted(lang_names.keys()):
                labels.append(lang_names[lang])
                values.append(learning_set_sizes[lang])
            _r_vector_export_output(f, "learn", values, labels)

        with codecs.open(os.path.join(output_dir, "test.R"), 'w', encoding='utf-8') as f:
            labels = []
            values = []
            for lang in sorted(lang_names.keys()):
                labels.append(lang_names[lang])
                values.append(test_set_sizes[lang])
            _r_vector_export_output(f, "test", values, labels)

    def generate_barplot(self, figure_title, sorting_order, labels, output_dir, values, dual=False):
        barplot_file_name = u'barplot_{}.R'.format(sorting_order)
        barplot_path = os.path.join(output_dir, barplot_file_name)
        try:
            os.mkdir(output_dir)
        except:
            pass
        try:
            os.remove(barplot_path)
        except:
            pass
        with codecs.open(barplot_path, 'w', encoding='utf-8') as f:
            if dual:
                _r_dual_plot_output(f, figure_title, labels, values)
            else:
                _r_single_plot_output(f, figure_title, labels, values)

            with working_directory(output_dir):
                subprocess.check_call(u'cat {} | Rscript - barplot_{}.svg'.format(barplot_file_name, sorting_order),
                                      shell=True)

