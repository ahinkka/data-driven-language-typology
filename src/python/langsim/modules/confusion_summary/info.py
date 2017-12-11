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
from langsim.datatypes.confusion import ConfusionMatrix
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import MultipleInputs
from pimlico.datatypes.files import NamedFile


class ModuleInfo(BaseModuleInfo):
    module_type_name = "confusion_summary"
    module_readable_name = "Collect confusion matrices and output a big summary into one document"
    module_inputs = [("matrix", MultipleInputs(ConfusionMatrix))]
    module_outputs = [("latex", NamedFile("perplexities.tex"))]
