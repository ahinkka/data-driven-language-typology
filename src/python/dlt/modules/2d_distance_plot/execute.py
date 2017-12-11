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
import subprocess

import codecs
import os

from dlt.model_corpus_distance_utils import averaged_language_distances
from dlt.utils import working_directory, collect_distances_names
from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        distances = self.info.get_input("distances")
        figure_title = self.info.options["title"]
        distance_measure = self.info.options["distance_measure"]

        model_corpus_distances, lang_names = collect_distances_names(distances)
        dist = averaged_language_distances(model_corpus_distances)
        import dlt.model_corpus_distance_2d_plot as mod_plot

        output_dir = self.info.get_absolute_output_dir("2d_plot")
        try:
            os.mkdir(output_dir)
        except:
            pass

        with working_directory(output_dir):
            try:
                os.remove('2d_plot.R')
            except:
                pass
            with codecs.open('2d_plot.R', 'w', encoding='utf-8') as f:
                mod_plot.r_output(f, dist, figure_title, distance_measure)
                subprocess.check_call('cat 2d_plot.R | Rscript - 2d_plot.svg', shell=True)
                self.log.info(u'2d plot written to {}'
                              .format(os.path.join(output_dir, u'2d_plot.svg')))
