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
from dlt.datatypes.ngram import UnigramFrequencyType, TokenMappingType, TokenMappingMissingCandidatesType
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import MultipleInputs


class ModuleInfo(BaseModuleInfo):
    module_type_name = "token_mapping"
    module_inputs = [("models", MultipleInputs(UnigramFrequencyType))]
    module_outputs = [("mappings", TokenMappingType),
                      ("missing_candidates", TokenMappingMissingCandidatesType)]
    module_options = {
        "phoneme_similarity_mapping_path": {
            "help": "Path to the ipa.bitdist.table file (incl. filename).",
            "required": True,
            "type": str,
        },
        "p_diff_threshold": {
            "help": "Probability difference threshold between languages for a unigram; the lower the higher chance " +
                    "of replacement.",
            "required": False,
            "type": float,
            "default": 0.05
        },
        "min_replacement_p": {
            "help": "Probability of the replacement in B; if set to low, very uncommon unigrams can be used as " +
                    "substitutes.",
            "required": False,
            "type": float,
            "default": 0.04
        },
        "min_phoneme_similarity": {
            "help": "Minimum phonetic similarity for replacement candidate",
            "required": False,
            "type": float,
            "default": 0.01
        }
    }
