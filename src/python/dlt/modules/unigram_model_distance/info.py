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

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import choose_from_list, str_to_bool
from pimlico.datatypes.results import NumericResult
from pimlico.datatypes.tar import TarredCorpusType

from dlt.datatypes.ngram import UnigramFrequencyType, TokenMappingType
from langsim.datatypes.raw_lines import RawTextLinesDocumentType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "unigram_model_distance"
    module_inputs = [("unigram_model", UnigramFrequencyType),
                     ("corpus", TarredCorpusType(RawTextLinesDocumentType)),
                     ("corpus_unigram_model", UnigramFrequencyType),
                     ("token_mapping", TokenMappingType)]
    module_outputs = [("distance", NumericResult)]
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
        "additive_smoothing": {
            "help": "Use additive (Laplace) smoothing",
            "required": False,
            "default": False,
            "type": str_to_bool
        },
        "additive_smoothing_a": {
            "help": "Alpha parameter for additive smoothing",
            "required": False,
            "default": 0.1,
            "type": float
        },
        "distance_measure": {
            "help": "Type of distance measure to use: either 'perplexity' or 'kita'.",
            "required": False,
            "type": choose_from_list(["perplexity", "kita"]),
            "default": "perplexity"
        }
    }
