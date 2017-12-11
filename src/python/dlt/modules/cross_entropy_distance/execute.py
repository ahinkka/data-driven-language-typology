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
import codecs
import math

from dlt.utils import read_token_mapping
from ngram.models import UnigramModel
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.results import NumericResultWriter


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        model_a_input = self.info.get_input("model_a")
        model_b_input = self.info.get_input("model_b")
        token_mapping = self.info.get_input("token_mapping")
        min_frequency = self.info.options["min_frequency"]

        with codecs.open(model_a_input.absolute_path, 'r', encoding='utf-8') as f:
            model_a = UnigramModel.read_from_file(f)
        with codecs.open(model_b_input.absolute_path, 'r', encoding='utf-8') as f:
            model_b = UnigramModel.read_from_file(f)

        model_a_language = model_a_input.module.module_variables["lang"]
        model_b_language = model_b_input.module.module_variables["lang"]

        assert model_a_language is not None and model_b_language is not None

        with codecs.open(token_mapping.absolute_path, 'r', encoding='utf-8') as f:
            token_map = {v: k
                         for k, v in read_token_mapping(f).get((model_a_language, model_b_language), {}).iteritems()}

        # https://en.wikipedia.org/wiki/Cross_entropy
        #  See "for discrete random variable".

        x_e_sum = 0.0
        for item, probability in model_a.token_probabilities.iteritems():
            if probability < min_frequency:
                continue

            b_prob = model_b.token_probabilities.get(item, 0.00000000000000000001)
            x_e_sum += probability * math.log(b_prob, 2)

        distance = -x_e_sum

        with NumericResultWriter(self.info.get_absolute_output_dir("distance")) as writer:
            writer.result = distance
            writer.label = "cross_entropy"
