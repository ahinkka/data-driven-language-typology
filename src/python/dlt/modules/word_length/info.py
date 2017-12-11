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
from pimlico.datatypes.files import NamedFile
from pimlico.datatypes.tar import TarredCorpusType

from langsim.datatypes.raw_lines import RawTextLinesDocumentType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "word_length"
    module_inputs = [("corpus", TarredCorpusType(RawTextLinesDocumentType))]
    module_outputs = [("word_length", NamedFile("word_length.txt"))]

    module_options = {
        "token_type": {
            "help": "Type of token: either 'text', 'phonemes' or 'kita'.",
            "required": True,
            "type": choose_from_list(["text", "phonemes", "kita"]),
        },
        "count": {
            "help": "How many tokens to process",
            "required": True,
            "type": int,
        },
    }
