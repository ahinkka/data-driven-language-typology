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
    module_type_name = "model_constraint_summary"
    module_inputs = [("test_set_size", MultipleInputs(SetSizeAndStatistics)),
                     ("learning_set_size", MultipleInputs(SetSizeAndStatistics))]
    module_outputs = [("summary", PimlicoDatatype),
                      ("r_output", PimlicoDatatype)]
    module_options = {
        "title": {
            "help": "Title of the summary.",
            "required": True,
            "type": str,
        },
    }
