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
import codecs
import operator
import os
import subprocess

from pimlico.datatypes.files import NamedFileWriter

from dlt.utils import working_directory, collect_distances_names
from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        distances_a = self.info.get_input("distances_a")
        model_corpus_distances_a, lang_names = collect_distances_names(distances_a)
        distances_b = self.info.get_input("distances_b")
        model_corpus_distances_b, _ = collect_distances_names(distances_b)

        all_languages = set()
        for a, b in model_corpus_distances_a.iterkeys():
            all_languages.add(a)
            all_languages.add(b)
        all_languages = sorted(all_languages)

        deltas = {}
        for lang_i in all_languages:
            for lang_j in all_languages:
                a_dist = model_corpus_distances_a[(lang_i, lang_j)]
                b_dist = model_corpus_distances_b[(lang_i, lang_j)]
                deltas[(lang_i, lang_j)] = (a_dist - b_dist, a_dist, b_dist)

        self.improvements(deltas)

    def improvements(self, deltas):
        filename = u'improvements.txt'

        _d, _f = self.info.get_absolute_output_dir("improvements"), self.info.get_output("improvements").filenames[0]

        try:
            os.unlink(os.path.join(_d, _f))
        except:
            pass
        with NamedFileWriter(_d, _f) as writer:
            lines = []

            lines.append(u'# Self included')
            lines.append(u'# I\tJ\tDELTA\tD_a\tD_b')
            improvement_ordered = sorted(deltas.iteritems(), cmp=lambda x, y: cmp(x[1][0], y[1][0]),
                                         reverse=True)
            for k, v in improvement_ordered:
                i, j = k
                d, ad, bd = v
                lines.append(u'{}\t{}\t{:.2f}\t{:.2f}\t{:.2f}'.format(i, j, d, ad, bd))
            lines.append(u'')

            lines.append(u'# Self excluded')
            lines.append(u'# I\tJ\tDELTA\tD_a\tD_b')
            improvement_ordered = sorted(deltas.iteritems(), cmp=lambda x, y: cmp(x[1][0], y[1][0]),
                                         reverse=True)
            for k, v in improvement_ordered:
                i, j = k
                if i == j:
                    continue
                d, ad, bd = v
                lines.append(u'{}\t{}\t{:.2f}\t{:.2f}\t{:.2f}'.format(i, j, d, ad, bd))
            lines.append(u'')

            writer.write_data(u'\n'.join(lines))
