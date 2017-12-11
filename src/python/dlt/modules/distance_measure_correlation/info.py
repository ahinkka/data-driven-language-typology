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
from pimlico.datatypes import PimlicoDatatype, MultipleInputs
from pimlico.datatypes.results import NumericResult


class ModuleInfo(BaseModuleInfo):
    module_type_name = "distance_measure_correlation"
    module_inputs = [("distances_a", MultipleInputs(NumericResult)),
                     ("distances_b", MultipleInputs(NumericResult))]
    module_outputs = [("correlation_plot", PimlicoDatatype)]
    module_options = {
        "distance_measure_a": {
            "help": "Distance measure name for A.",
            "required": True,
            "type": str,
        },
        "distance_measure_b": {
            "help": "Distance measure name for B.",
            "required": True,
            "type": str,
        },
        "upper_threshold_a": {
            "help": "Filter out all values above this threshold for A.",
            "required": True,
            "type": int,
            "default": -1,
        },
        "upper_threshold_b": {
            "help": "Filter out all values above this threshold for B.",
            "required": True,
            "type": int,
            "default": -1,
        },
    }
