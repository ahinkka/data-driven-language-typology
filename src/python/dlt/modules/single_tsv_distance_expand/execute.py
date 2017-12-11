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

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.results import NumericResultWriter


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        ug_model = self.info.get_input("unigram_model")
        corpus = self.info.get_input("corpus")

        model_language = ug_model.module.module_variables["lang_code"]
        corpus_language = corpus.module.module_variables["lang_code"]

        result = None
        with codecs.open(self.info.options["single_tsv_path"], 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.replace(u'\n', '').split('\t')
                model, corpus, distance = parts
                if model == model_language and corpus == corpus_language:
                    result = float(distance)

        if result is None:
            raise Exception(u"Couldn't find {} {}".format(model_language, corpus_language))

        self.log.info(u"Distance: {}".format(result))

        with NumericResultWriter(self.info.get_absolute_output_dir("distance")) as writer:
            writer.result = result
            writer.label = "perplexity"
