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
from pimlico.datatypes.tar import TarredCorpusType
from pimlico.core.modules.options import choose_from_list, comma_separated_list

from langsim.datatypes.raw_lines import RawTextLinesDocumentType
from dlt.datatypes.ngram import SetSizeAndStatistics


class ModuleInfo(BaseModuleInfo):
    module_type_name = "unigram_input_constraints"
    module_inputs = [("corpus", TarredCorpusType(RawTextLinesDocumentType))]
    module_outputs = [("test_set_size_and_statistics", SetSizeAndStatistics),
                      ("learning_set_size_and_statistics", SetSizeAndStatistics)]
    module_options = {
        "token_type": {
            "help": "Type of token: either 'text' or 'phonemes'.",
            "required": True,
            "type": choose_from_list(["text", "phonemes"]),
        },
        "max_token_count": {
            "help": "How many tokens to use for training and testing from the input.\n" + \
                    "Useful if one of the input sets is smaller or if one wants to set the upper limit for tests.",
            "required": True,
            "type": int,
        },
        "held_out_set_size": {
            "help": "How many tokens to reserve only for testing; these are included in the max_token_count",
            "required": True,
            "type": int,
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
