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

from dlt.model_corpus_distance_utils import distance_dict_to_r_matrix
from dlt.utils import working_directory, collect_distances_names


def heatmap_r_output(stream, distances, low_threshold, lang_names):
    model_corpus_distances, lang_names = collect_distances_names(distances)

    print(u'library(gplots)', file=stream)

    def family_comparator(a, b):
        order = [
            # Finno-Ugrig
            'fi', 'et', 'hu',
            # Slavic
            'bg', 'sl',
            'cs', 'sk',
            'pl',
            # Germanic
            'de', 'nl', 'da', 'sv', 'en',
            # Romance
            'es', 'pt', 'fr', 'it', 'ro',
            # Baltic
            'lt', 'lv',
            # Greek
            'el'
        ]

        return order.index(a) - order.index(b)

    print(distance_dict_to_r_matrix(model_corpus_distances, 'distance_matrix',
                                    language_comparator=family_comparator),
          file=stream)

    print(u'args <- commandArgs(trailingOnly = TRUE)', file=stream)
    print(u'svg(filename=args[1], width=5, height=5, pointsize=12)', file=stream)

    dark_threshold = low_threshold

    print(u'dark_threshold <- {}'.format(dark_threshold), file=stream)
    print(u'dark_breaks <- pretty(c(0, dark_threshold), 4)', file=stream)
    print(u'light_breaks <- pretty(c(dark_threshold, max(distance_matrix)), 4)', file=stream)
    print(u'col_breaks <- unique(c(dark_breaks, light_breaks))', file=stream)
    print(u'col_breaks', file=stream)
    print(u'cols <- c(gray.colors(n=4, start=0.25, 0.7), gray.colors(n=length(col_breaks) - 5, start=0.8, end=0.95))',
          file=stream)
    print(u'cols', file=stream)

    # https://www.rdocumentation.org/packages/gplots/versions/3.0.1/topics/heatmap.2
    print(u'''heatmap.2(distance_matrix, Rowv=NA, Colv=NA, revC=FALSE, symm=FALSE,
              col=cols, breaks=col_breaks, key=TRUE)''', file=stream)

    print(u"dev.off()", file=stream)


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        distances = self.info.get_input("distances")
        model_corpus_distances, lang_names = collect_distances_names(distances)

        all_languages = set()
        for a, b in model_corpus_distances.iterkeys():
            all_languages.add(a)
            all_languages.add(b)

        # per language histogram of distances
        # histogram for all distances

        output_dir = self.info.get_absolute_output_dir("heatmap")
        try:
            os.mkdir(output_dir)
        except:
            pass
        with working_directory(output_dir):
            r_filename = u'heatmap.R'
            svg_filename = u'heatmap.svg'
            try:
                os.remove(r_filename)
            except:
                pass
            with codecs.open(r_filename, 'w', encoding='utf-8') as f:
                heatmap_r_output(f, distances, self.info.options["low_threshold"], lang_names)

                try:
                    os.remove(svg_filename)
                except:
                    pass
                subprocess.check_call('cat {} | Rscript - {}'.format(r_filename, svg_filename), shell=True)
                self.log.info(u'Family ordered heatmap written to {}'.format(os.path.join(output_dir, svg_filename)))
