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

import shutil

import codecs
import operator
import os
import subprocess

from pimlico.datatypes.files import NamedFileWriter

from dlt.model_corpus_distance_utils import distance_dict_to_r_matrix, distance_dict_to_r_distance_vector
from dlt.utils import working_directory, collect_distances_names
from pimlico.core.modules.base import BaseModuleExecutor


def neighbor_distance_plot_r_output(stream, neighbor_distances, figure_title, language, distance_measure, clusters=None):
    closest_first_neighbors = sorted(neighbor_distances.items(), key=operator.itemgetter(1))

    print(u'neighbors <- c({})'.format(u','.join([u'"{}"'.format(n[0]) for n in closest_first_neighbors])), file=stream)
    print(u'distances <- c({})'.format(u','.join([u'{}'.format(n[1]) for n in closest_first_neighbors])), file=stream)

    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=5, height=5, pointsize=12)', file=stream)

    # If the title begins with "R ", treat it as a legal R expression, otherwise escape the title
    if figure_title[0:2] == u'R ':
        figure_title = figure_title[2:]
    else:
        figure_title = u"'" + figure_title + u"'"

    clusters_part = u''
    if clusters is not None:
        print(u'fit <- kmeans(distances, {})'.format(clusters), file=stream)
        clusters_part = u', pch=fit$cluster'

    # First plot without any limits to get a proper values for graphical parameters
    print(u'plot(distances)', file=stream)
    print(u'char_height <- par("cxy")[2]', file=stream)
    print(u'y_min <- par("usr")[3]', file=stream)

    print(u'plot(distances, main={}, ylab="Distance", xlab="Neighbor languages for {}", xaxt="n", ylim=c(y_min, max(distances) + 1.5 * char_height){})'
          .format(figure_title, language, clusters_part), file=stream)

    print(u'text(seq(neighbors), distances + char_height, labels=neighbors, cex=0.8)', file=stream)

    print(u'mtext("Distance measure: {}", side=1, adj=0, cex=.5)'.format(distance_measure), file=stream)
    if clusters is not None:
        print(u'mtext("Cluster count: {}", side=1, adj=0, padj=1.2, cex=.5)'.format(clusters), file=stream)

    padj = 0
    for i in xrange(len(closest_first_neighbors)):
        if i == 5:
            break
        print(u'mtext(paste("Distance to {}:", format({}, digits=2, nsmall=2)), side=1, adj=1, padj={}, cex=.5)'
              .format(closest_first_neighbors[i][0], closest_first_neighbors[i][1], padj), file=stream)
        padj += 1.5

    print(u"dev.off()", file=stream)


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        distances = self.info.get_input("distances")
        model_corpus_distances, lang_names = collect_distances_names(distances)

        all_languages = set()
        for a, b in model_corpus_distances.iterkeys():
            all_languages.add(a)
            all_languages.add(b)
        all_languages = sorted(all_languages)

        self.self_distance(all_languages, model_corpus_distances)
        self.proximity_ranking(all_languages, model_corpus_distances)
        self.distance_histogram([v
                                 for k, v in sorted(model_corpus_distances.items(), key=operator.itemgetter(0))
                                 if k[0] != k[1]], "hist_self_excluded")
        self.distance_histogram([v
                                 for k, v in sorted(model_corpus_distances.items(), key=operator.itemgetter(0))
                                 if k[0] == k[1]], "hist_self_only")
        self.distance_histogram([v
                                 for k, v in sorted(model_corpus_distances.items(), key=operator.itemgetter(0))],
                                "hist_all")
        self.r_exports(model_corpus_distances, lang_names)

        # per language histogram of distances

        total_min = 10000
        for language in all_languages:
            self.neighbor_distance_plot(language, lang_names[language], model_corpus_distances)

            for i in xrange(2, 6):
                self.neighbor_distance_plot(language, lang_names[language], model_corpus_distances, clusters=i)

            minimum = self.neighbor_distance_minimum_change_needed(language, model_corpus_distances)
            if minimum < total_min:
                total_min = minimum

        output_dir = self.info.get_absolute_output_dir("minimum_distance")
        with working_directory(output_dir):
            try:
                os.remove(u'minimum_distance')
            except:
                pass
            with codecs.open(u'minimum_distance', 'w', encoding='utf-8') as f:
                print(u'{}'.format(total_min), file=f)

    def self_distance(self, languages, distances):
        with NamedFileWriter(self.info.get_absolute_output_dir("self_distance"),
                             self.info.get_output("self_distance").filenames[0]) as writer:
            out = u''
            tmp = []
            for language in languages:
                distance = distances[(language, language)]
                out += u'{}\t{}\n'.format(language, distance)
                tmp.append(distance)
            out += u'\n{}'.format(', '.join([str(i) for i in tmp]))
            writer.write_data(out)

    def proximity_ranking(self, languages, distances):
        max_distances = {}
        min_distances = {}
        mean_distances = {}

        for lang_a in languages:
            for lang_b in languages:
                if lang_a == lang_b:
                    continue
                key1 = tuple(sorted([lang_a, lang_b]))
                key2 = tuple(sorted([lang_a, lang_b], reverse=True))
                d1, d2 = distances[key1], distances[key2]
                max_distances[key1] = max([d1, d2])
                min_distances[key1] = min([d1, d2])
                mean_distances[key1] = sum([d1, d2]) / 2.0

        sorted_distances = sorted(max_distances.items(), key=operator.itemgetter(1))

        with NamedFileWriter(self.info.get_absolute_output_dir("proximity_ranking"),
                             self.info.get_output("proximity_ranking").filenames[0]) as writer:
            out = u''
            out += u'A\tB\tA->B\tB->A\tMEAN\tMAX\tMIN\n'
            for pair, _ in sorted_distances:
                ab = distances[pair]
                ba = distances[(pair[1], pair[0])]

                out += u'{}\t{}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\n'\
                    .format(pair[0], pair[1], ab, ba, mean_distances[pair], max_distances[pair], min_distances[pair])
            writer.write_data(out)

    def neighbor_distance_minimum_change_needed(self, language, dist):
        distance_measure = self.info.options["distance_measure"]
        output_dir = self.info.get_absolute_output_dir("minimum_distance")

        distances = {a_b[1]: distance
                     for a_b, distance in dist.iteritems()
                     if a_b[0] == language and a_b[1] != language}

        try:
            os.mkdir(output_dir)
        except:
            pass

        with working_directory(output_dir):
            report_filename = u'distances_{}'.format(language)
            try:
                os.remove(report_filename)
            except:
                pass

            with codecs.open(report_filename, 'w', encoding='utf-8') as f:
                print("# Language: {}".format(language), file=f)
                print("# Distance measure: {}".format(distance_measure), file=f)
                print("", file=f)

                for neighbor, distance in sorted(distances.items(), key=operator.itemgetter(1), reverse=False):
                    print(u'{}\t{}'.format(neighbor, distance), file=f)

        return min(distances.values())

    def neighbor_distance_plot(self, language, language_human_readable, dist, clusters=None):
        figure_title = self.info.options["title"]
        distance_measure = self.info.options["distance_measure"]
        output_dir = self.info.get_absolute_output_dir("neighbor_distance_plot")

        distances = {a_b[1]: distance
                     for a_b, distance in dist.iteritems()
                     if a_b[0] == language}

        if clusters is not None and len(distances) <= clusters:
            self.log.info(u'Not clustering with as many neighbors')
            return

        try:
            os.mkdir(output_dir)
        except:
            pass
        with working_directory(output_dir):
            if clusters is None:
                clusters_part = u''
            else:
                clusters_part = u'_{}'.format(clusters)
            r_filename = u'neighbor_distance_plot_{}{}.R'.format(language, clusters_part)
            svg_filename = u'neighbor_distance_plot_{}{}.svg'.format(language, clusters_part)
            try:
                os.remove(r_filename)
            except:
                pass
            with codecs.open(r_filename, 'w', encoding='utf-8') as f:
                neighbor_distance_plot_r_output(f, distances, figure_title, language_human_readable, distance_measure,
                                                clusters=clusters)

                try:
                    os.remove(svg_filename)
                except:
                    pass
                subprocess.check_call('cat {} | Rscript - {}'.format(r_filename, svg_filename), shell=True)
                self.log.info(u'Neighbor distance plot with {} clusters written to {}'
                              .format(clusters, os.path.join(output_dir, svg_filename)))

    def distance_histogram(self, distances, filename):
        output_dir = self.info.get_absolute_output_dir("distance_histogram")
        try:
            os.mkdir(output_dir)
        except:
            pass
        with working_directory(output_dir):
            r_filename = u'{}.R'.format(filename)
            svg_filename = u'{}.svg'.format(filename)
            try:
                os.remove(r_filename)
            except:
                pass
            with codecs.open(r_filename, 'w', encoding='utf-8') as f:
                print(u'args <- commandArgs(trailingOnly = TRUE)', file=f)
                print(u'svg(filename=args[1], width=10, height=8, pointsize=12)', file=f)

                print(u'distances <- c({})'.format(', '.join([str(i) for i in distances])), file=f)
                print(u'par(mfrow=c(3,3))', file=f)
                print(u'hist(distances, main="All distances")', file=f)
                print(u'hist(distances[which(distances < 5000)], main="Distances under 5000")', file=f)
                #print(u'hist(distances[which(distances < 2000)], main="Distances under 2000")', file=f)
                print(u'hist(distances[which(distances < 1000)], main="Distances under 1000")', file=f)
                print(u'hist(distances[which(distances < 500)], main="Distances under 500")', file=f)
                print(u'hist(distances[which(distances < 200)], main="Distances under 200")', file=f)
                print(u'hist(distances[which(distances < 100)], main="Distances under 100")', file=f)
                print(u'hist(distances, breaks=4, main="Distances")', file=f)
                print(u'hist(distances[which(distances < 5000)], breaks=4, main="Distances under 5000")', file=f)
                print(u'hist(distances[which(distances < 1000)], breaks=9, main="Distances under 1000")', file=f)

                print(u"dev.off()", file=f)

                try:
                    os.remove(svg_filename)
                except:
                    pass
                subprocess.check_call('cat {} | Rscript - {}'.format(r_filename, svg_filename), shell=True)
                self.log.info(u'Distance histogram written to {}'.format(os.path.join(output_dir, svg_filename)))

    def r_exports(self, model_corpus_distances, lang_names):
        output_dir = self.info.get_absolute_output_dir("r_exports")
        try:
            os.mkdir(output_dir)
        except:
            pass
        with working_directory(output_dir):
            matrix_filename = 'distance_matrix.R'
            vector_filename = 'distance_vector.R'
            no_self_vector_filename = 'distance_vector_no_self.R'

            shutil.rmtree(matrix_filename, ignore_errors=True)
            shutil.rmtree(vector_filename, ignore_errors=True)
            shutil.rmtree(no_self_vector_filename, ignore_errors=True)

            with codecs.open(matrix_filename, 'w', encoding='utf-8') as f:
                print(distance_dict_to_r_matrix(model_corpus_distances, 'distance_matrix'),
                      file=f)
                self.log.info(u'R distance matrix written to {}'.format(os.path.join(output_dir, matrix_filename)))

            with codecs.open(vector_filename, 'w', encoding='utf-8') as f:
                print(distance_dict_to_r_distance_vector(model_corpus_distances, 'distance_vector'),
                      file=f)
                self.log.info(u'R distance vector written to {}'.format(os.path.join(output_dir, vector_filename)))

            with codecs.open(no_self_vector_filename, 'w', encoding='utf-8') as f:
                print(distance_dict_to_r_distance_vector({k: v
                                                          for k, v in model_corpus_distances.iteritems()
                                                          if k[0] != k[1]}, 'distance_vector'),
                      file=f)
                self.log.info(u'R distance vector (no self distances) written to {}'
                              .format(os.path.join(output_dir, no_self_vector_filename)))
