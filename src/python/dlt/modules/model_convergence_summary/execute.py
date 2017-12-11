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

import codecs
import subprocess

import shutil

import os
import sys

from dlt.utils import working_directory
from pimlico.core.modules.base import BaseModuleExecutor


def _read_stats(path):
    with open(path, 'r') as f:
        return json.load(f)[u'statistics']


def _stabilization_plot(output_dir, pairs, diff_threshold):
    r_filename = u'stabilization.R'
    svg_filename = u'stabilization.svg'
    with working_directory(output_dir):
        if os.path.isfile(r_filename):
            os.remove(r_filename)
        with codecs.open(r_filename, 'w', encoding='utf-8') as f:
            sizes = [size for size, _ in pairs]
            probabilities = []

            desired = pairs[0][1]["expected_value"]
            attrs = []
            for _, stats in pairs:
                within_threshold = 0
                for measurement in stats["measurements"]:
                    if abs(measurement - desired) <= diff_threshold:
                        within_threshold += 1
                p = within_threshold / float(len(stats["measurements"]))
                probabilities.append(p)

            print(u'temp_matrix <- matrix(c({}, {}), nrow={}, ncol=2)'.format(
                u', '.join([str(s) for s in sizes]),
                u', '.join([str(s) for s in probabilities]),
                len(sizes)
            ), file=f)
            print(u'colnames(temp_matrix) <- c("Size", "Probability")', file=f)
            print(u'temp_frame <- as.data.frame(temp_matrix)', file=f)
            print(u'svg("{}", width=5, height=5, pointsize=12)'.format(svg_filename), file=f)

            print(u'plot(temp_frame, ylim=c(0, 1), xlim=c(100, max(temp_frame$Size)), log="x", ylab="Within threshold probability", xlab="Sample size")', file=f)
            print(u'lines(temp_frame)', file=f)
            print(u'grid()', file=f)

        subprocess.check_call(u'cat {} | Rscript -'.format(r_filename), shell=True)


def _size_stats_pairs_to_plot_r(pairs, stat_attribute, attr_name, filename, stream,
                                extra_plot_attrs={}, extra_data_attrs={}):
    print(u'temp_matrix <- matrix(c(', end='', file=stream)

    sizes = [size for size, _ in pairs]

    if stat_attribute == 'p':
        desired = pairs[0][1]["expected_value"]
        diff_threshold = extra_data_attrs["diff_threshold"],
        cutoff_probability = extra_data_attrs["cutoff_probability"]

        attrs = []
        for _, stats in pairs:
            within_threshold = 0
            for measurement in stats["measurements"]:
                if abs(measurement - desired) <= diff_threshold[0]:
                    within_threshold += 1
            p = within_threshold / float(len(stats["measurements"]))
            attrs.append(p)
    else:
        attrs = [stats[stat_attribute] for _, stats in pairs]

    print(u'{}, {}), nrow={}, ncol=2)'.format(
        ', '.join([str(i) for i in sizes]),
        ', '.join([str(i) for i in attrs]),
        len(sizes)),
        file=stream)

    print(u'colnames(temp_matrix) <- c("{}", "{}")'.format("Size", attr_name), file=stream)
    print(u'temp_frame <- as.data.frame(temp_matrix)', file=stream)
    print(u'svg("{}", width=5, height=5, pointsize=12)'.format(filename), file=stream)

    plot_params = ["temp_frame"]
    for k, v in extra_plot_attrs.iteritems():
        plot_params.append(u'{}={}'.format(k, v))
    print(u'plot({})'.format(u', '.join(plot_params)), file=stream)


def _measurements_to_plot_r(pairs, variable_name, variable_human_readable, distance_measure, filename, stream):
    size_vector_names = []
    for size, stats in pairs:
        vector_name = u'C{}'.format(size)
        size_vector_names.append(vector_name)
        print(u'{} <- c({})'.format(vector_name, u', '.join([u'{}'.format(i) for i in stats["measurements"]])),
              file=stream)

    print(u'f <- data.frame({})'.format(u', '.join([u'{}={}'.format(n, n) for n in size_vector_names])), file=stream)
    print(u'colnames(f) <- c({})'.format(u', '.join([u'"{}"'.format(n[1:]) for n in size_vector_names])), file=stream)
    print(u'svg("{}", width=10, height=5, pointsize=12)'.format(filename), file=stream)
    print(u'sample_sizes <- c({})'.format(u', '.join([u'{}'.format(n[1:]) for n in size_vector_names])), file=stream)
    print(u'boxplot(f, log="y", xaxt="n", outpch=1, outcex=.7, ylab="Distance", xlab="{} set size")'
          .format(variable_human_readable), file=stream)
    print(u'abline(h={}, lty="dashed", cex=.7)'.format(pairs[0][1]["expected_value"]), file=stream)
    print(u'axis(side=1, at=seq(1, length(sample_sizes)), labels=sample_sizes)', file=stream)
    print(u'mtext("Distance measure = {}", side=1, adj=0, padj=6, cex=.5)'.format(distance_measure), file=stream)


def _plot_size_and_variable(output_dir, variable_name, variable_human_readable, size_stat_pairs,
                            extra_plot_attrs={}, extra_data_attrs={}):
    r_filename = u'{}.R'.format(variable_name)
    svg_filename = u'{}.svg'.format(variable_name)
    with working_directory(output_dir):
        if os.path.isfile(r_filename):
            os.remove(r_filename)
        with codecs.open(r_filename, 'w', encoding='utf-8') as f:
            _size_stats_pairs_to_plot_r(size_stat_pairs, variable_name, variable_human_readable, svg_filename, f,
                                        extra_plot_attrs=extra_plot_attrs, extra_data_attrs=extra_data_attrs)
        subprocess.check_call(u'cat {} | Rscript -'.format(r_filename), shell=True)


def _plot_measurements_as_boxplot(output_dir, variable_name, variable_human_readable, distance_measure, size_stat_pairs):
    r_filename = u'{}.R'.format(variable_name)
    svg_filename = u'{}.svg'.format(variable_name)
    with working_directory(output_dir):
        if os.path.isfile(r_filename):
            os.remove(r_filename)
        with codecs.open(r_filename, 'w', encoding='utf-8') as f:
            _measurements_to_plot_r(size_stat_pairs, variable_name, variable_human_readable, distance_measure,
                                    svg_filename, f)
        subprocess.check_call(u'cat {} | Rscript -'.format(r_filename), shell=True)


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        figure_title = self.info.options["title"]
        test_set_input = self.info.get_input("test_set_size")
        learning_set_input = self.info.get_input("learning_set_size")
        lang = test_set_input.module.module_variables["lang"]
        distance_measure = self.info.options["distance_measure"]

        test_sizes = _read_stats(test_set_input.absolute_path)
        learn_sizes = _read_stats(learning_set_input.absolute_path)

        test_set_output_dir = self.info.get_absolute_output_dir("test_set_convergence")
        learning_set_output_dir = self.info.get_absolute_output_dir("learning_set_convergence")
        if not os.path.isdir(test_set_output_dir):
            os.makedirs(test_set_output_dir)
        if not os.path.isdir(learning_set_output_dir):
            os.makedirs(learning_set_output_dir)

        _plot_size_and_variable(test_set_output_dir, u'std_dev', "Standard deviation", test_sizes,
                                extra_plot_attrs={"log": '"y"'}) #, "ylim": "c(0, 25)"})
        _plot_size_and_variable(learning_set_output_dir, u'std_dev', "Standard deviation", learn_sizes,
                                extra_plot_attrs={"log": '"y"'}) #, "ylim": "c(1, 25)"})

        _plot_size_and_variable(test_set_output_dir, u'p', "Probability", test_sizes,
                                extra_plot_attrs={"ylim": 'c(0, 1)'},
                                extra_data_attrs={
                                    "diff_threshold": self.info.options["test_diff_threshold"],
                                    "cutoff_probability": self.info.options["test_cutoff_probability"]
                                })
        _plot_size_and_variable(learning_set_output_dir, u'p', "Probability", learn_sizes,
                                extra_plot_attrs={"ylim": 'c(0, 1)'},
                                extra_data_attrs={
                                    "diff_threshold": self.info.options["train_diff_threshold"],
                                    "cutoff_probability": self.info.options["train_cutoff_probability"]
                                })

        _plot_size_and_variable(test_set_output_dir, u'mean', "Mean", test_sizes,
                                extra_plot_attrs={"log": '"y"'})
        _plot_size_and_variable(learning_set_output_dir, u'mean', "Mean", learn_sizes,
                                extra_plot_attrs={"log": '"y"'})

        _plot_measurements_as_boxplot(learning_set_output_dir, "learn", "Learn", distance_measure, learn_sizes)
        _plot_measurements_as_boxplot(test_set_output_dir, "test", "Test", distance_measure, test_sizes)

        test_set_stabilization_output_dir = self.info.get_absolute_output_dir("test_set_stabilization")
        learning_set_stabilization_output_dir = self.info.get_absolute_output_dir("learning_set_stabilization")
        if not os.path.isdir(test_set_stabilization_output_dir):
            os.makedirs(test_set_stabilization_output_dir)
        if not os.path.isdir(learning_set_stabilization_output_dir):
            os.makedirs(learning_set_stabilization_output_dir)

        _stabilization_plot(learning_set_stabilization_output_dir, learn_sizes, self.info.options["train_diff_threshold"])
        _stabilization_plot(test_set_stabilization_output_dir, test_sizes, self.info.options["test_diff_threshold"])