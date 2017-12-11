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
from __future__ import print_function

import operator
import os
import shutil

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

        with codecs.open(model_a_input.absolute_path, 'r', encoding='utf-8') as f:
            model_a = UnigramModel.read_from_file(f)
        with codecs.open(model_b_input.absolute_path, 'r', encoding='utf-8') as f:
            model_b = UnigramModel.read_from_file(f)

        model_a_language = model_a_input.module.module_variables["lang"]
        model_b_language = model_b_input.module.module_variables["lang"]

        assert model_a_language is not None and model_b_language is not None

        output_dir = self.info.get_absolute_output_dir("phoneme_set_diff")
        shutil.rmtree(output_dir, ignore_errors=True)
        os.mkdir(output_dir)

        all_phonemes = sorted(set(model_a.token_probabilities.keys()) | set(model_b.token_probabilities.keys()))
        rows = []
        for p in all_phonemes:
            a_prob = model_a.token_probabilities.get(p, None)
            b_prob = model_b.token_probabilities.get(p, None)
            a_eff_prob = model_a.token_probabilities.get(p, 0.00000000000000000001)
            b_eff_prob = model_b.token_probabilities.get(p, 0.00000000000000000001)
            x_e = a_eff_prob * math.log(b_eff_prob, 2)

            is_a = u'_'
            if a_prob is not None:
                is_a = u'X'
            is_b = u'_'
            if b_prob is not None:
                is_b = u'X'

            rows.append((p, is_a, is_b, a_eff_prob, b_eff_prob, abs(x_e)))

        with codecs.open(os.path.join(output_dir, 'by_xe.txt'), 'w', encoding='utf-8') as f:
            print(u'{} vs {}, sorted by {}\n----'.format(model_a_language, model_b_language, 'cross entropy'), file=f)

            for row in sorted(rows, key=operator.itemgetter(5), reverse=True):
                print(*row, sep='\t', file=f)

        with codecs.open(os.path.join(output_dir, 'by_a_prob.txt'), 'w', encoding='utf-8') as f:
            print(u'{} vs {}, sorted by {}\n----'.format(model_a_language, model_b_language, 'cross entropy'), file=f)

            for row in sorted(rows, key=operator.itemgetter(3), reverse=True):
                print(*row, sep='\t', file=f)

        with codecs.open(os.path.join(output_dir, 'missing.txt'), 'w', encoding='utf-8') as f:
            missing_accumulator = 0.0
            for row in rows:
                if row[2] == u'_':
                    missing_accumulator += row[3]

            print(u'{} vs {}, sorted by {}; missing percentage: {}\n----'
                  .format(model_a_language, model_b_language, 'cross entropy', missing_accumulator * 100), file=f)

            for row in sorted(rows, key=operator.itemgetter(5), reverse=True):
                if row[2] == u'_':
                    print(*row, sep='\t', file=f)
