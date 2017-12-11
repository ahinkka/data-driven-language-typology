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
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import choose_from_list
from pimlico.datatypes import PimlicoDatatype, MultipleInputs
from pimlico.datatypes.results import NumericResult


class ModuleInfo(BaseModuleInfo):
    module_type_name = "distances_dendrogram"
    module_inputs = [("distances", MultipleInputs(NumericResult))]
    module_outputs = [("dendrogram", PimlicoDatatype)]
    module_options = {
        "title": {
            "help": "Title of the dendrogram.",
            "required": True,
            "type": str,
        },
        "distance_measure": {
            "help": "Distance measure used.",
            "required": True,
            "type": str,
        },
        "clustering_method": {
            "help": "Clustering method to use, see " + \
                    "https://stat.ethz.ch/R-manual/R-devel/library/stats/html/hclust.html for details.",
            "required": False,
            "default": "average",
            "type": choose_from_list(['ward.D', 'ward.D2', 'single', 'complete', 'average', 'mcquitty', 'median',
                                      'centroid']),
        }
    }
