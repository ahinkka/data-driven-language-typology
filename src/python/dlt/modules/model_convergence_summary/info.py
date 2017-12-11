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
from dlt.datatypes.ngram import SetSizeAndStatistics
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes import PimlicoDatatype, MultipleInputs


class ModuleInfo(BaseModuleInfo):
    module_type_name = "model_convergence_summary"
    module_inputs = [("test_set_size", SetSizeAndStatistics),
                     ("learning_set_size", SetSizeAndStatistics)]
    module_outputs = [("test_set_convergence", PimlicoDatatype),
                      ("test_set_stabilization", PimlicoDatatype),
                      ("learning_set_convergence", PimlicoDatatype),
                      ("learning_set_stabilization", PimlicoDatatype)]
    module_options = {
        "title": {
            "help": "Title of the summary.",
            "required": True,
            "type": str,
        },
        "distance_measure": {
            "help": "Distance measure used.",
            "required": True,
            "type": str,
        },
        "train_diff_threshold": {
            "help": "What is the standard deviation we have to reach",
            "required": True,
            "type": float,
        },
        "train_cutoff_probability": {
            "help": "What is the cutoff probability we have to reach",
            "required": True,
            "type": float,
        },
        "train_sample_count": {
            "help": "How many sample calculations to execute.",
            "required": True,
            "type": int,
        },
        "test_diff_threshold": {
            "help": "What is the standard deviation we have to reach",
            "required": True,
            "type": float,
        },
        "test_cutoff_probability": {
            "help": "What is the cutoff probability we have to reach",
            "required": True,
            "type": float,
        },
        "test_sample_count": {
            "help": "How many sample calculations to execute.",
            "required": True,
            "type": int,
        },
    }
