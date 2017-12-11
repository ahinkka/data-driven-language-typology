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

from dlt.datatypes.ngram import TrigramModelTypeWriter
from dlt.phonetic_transcript_tokenizer import token_gen as phoneme_token_gen
from dlt.text_tokenizer import token_gen as text_token_gen
from dlt.kita_tokenizer import token_gen as kita_token_gen
from ngram.models import TrigramModelBuilderTokenSink, TrigramModel
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.base import InvalidDocument


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        corpus = self.info.get_input("corpus")
        token_type = self.info.options["token_type"]
        token_count = self.info.options["count"]

        if token_type == "text":
            tokenizer = text_token_gen
        elif token_type == "phonemes":
            tokenizer = phoneme_token_gen
        elif token_type == "kita":
            tokenizer = kita_token_gen
        else:
            raise Exception("Unknown token type: {}".format(token_type))

        sink = TrigramModelBuilderTokenSink(self.log)
        docs_processed = 0
        lines_processed = 0
        tokens_processed = 0
        docs_skipped = 0
        for doc_name, doc_text in corpus:
            self.log.debug(u"Processing {}".format(doc_name))
            if isinstance(doc_text, InvalidDocument):
                self.log.debug(u"Skipping document {}: {}".format(doc_name, doc_text))
                docs_skipped += 1
                continue

            for line in doc_text:
                for token in tokenizer(line):
                    sink.handle(token)
                    tokens_processed += 1
                    if tokens_processed >= token_count:
                        break
                if tokens_processed >= token_count:
                    break
                lines_processed += 1
            if tokens_processed >= token_count:
                break
            docs_processed += 1

        self.log.info(u"{} documents skipped".format(docs_skipped))
        self.log.info(u"{} documents, {} lines and {} tokens processed"
                      .format(docs_processed, lines_processed, tokens_processed))

        if tokens_processed < token_count:
            raise Exception("Not enough tokens found")

        with TrigramModelTypeWriter(self.info.get_absolute_output_dir("trigram_model")) as writer:
            with codecs.open(writer.absolute_path, 'w', encoding='utf-8') as f:
                model = TrigramModel(sink.transition_counts)
                model.write_to_file(f)
