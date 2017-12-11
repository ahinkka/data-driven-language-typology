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
import collections
import os
import shutil
import subprocess

import sys
from operator import itemgetter

import numpy

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.files import NamedFileWriter

from dlt.utils import read_token_mapping

DOC_TEMPLATE = u"""\
\\documentclass{article}

\\usepackage[T1]{fontenc}
\\usepackage[utf8]{inputenc}
\\usepackage{textcomp}
\\usepackage{longtable}

\\usepackage{fullpage}
\\usepackage{hyperref}

\\usepackage{fontspec}
\\setmainfont{DoulosSIL-R.ttf}

\\usepackage{multicol}

\\title{Phonetic mapping summary}
\\author{data-driven-language-typology}
\\date{\\today}

\\begin{document}
\\maketitle

\\begin{multicols*}{2}
\\tableofcontents
\\end{multicols*}

%s

\\end{document}
"""


# All the mappings should probably be per pair so we could get the language name without hardcoding them here. But it's
# just slow because reading in the IPA similarity table is slow. To overcome that, reading in the table would also need
# to be refactored. Not doing that now.
LANG_NAMES = {
    "en": "English",
    "fi": "Finnish",
    "et": "Estonian",
    "sv": "Swedish",
    "da": "Danish",
    "nl": "Dutch",
    "fr": "French",
    "lt": "Lithuanian",
    "sl": "Slovene",
    "bg": "Bulgarian",
    "cs": "Czech",
    "de": "German",
    "el": "Greek",
    "es": "Spanish",
    "hu": "Hungarian",
    "it": "Italian",
    "lv": "Latvian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "sk": "Slovak"
}


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        token_mapping = self.info.get_input("mappings")
        with codecs.open(token_mapping.absolute_path, 'r', encoding='utf-8') as f:
            token_map = read_token_mapping(f)

        sections = collections.defaultdict(dict)
        for lang_a, lang_b in token_map.iterkeys():
            sections[LANG_NAMES[lang_a]][LANG_NAMES[lang_b]] = u"""
\\subsection{%s to %s}

Phoneme mappings:

\\begin{longtable}{l l r r r}
\\textbf{From} & \\textbf{To} \\\\\\hline
%s
\\end{longtable}
""" % (
                LANG_NAMES[lang_a], LANG_NAMES[lang_b],
                u" \\\\\n".join(
                    u"%s & %s" % (latex_ipa(latexify(a)), latex_ipa(latexify(b)))
                    for a, b in token_map[(lang_a, lang_b)].iteritems()))

        self.log.info(sections)
        self.log.info(type(sections))

        try:
            os.unlink(os.path.join(self.info.get_absolute_output_dir("latex"),
                                   self.info.get_output("latex").filenames[0]))
        except:
            pass
        with NamedFileWriter(self.info.get_absolute_output_dir("latex"),
                             self.info.get_output("latex").filenames[0]) as writer:
            latex_path = writer.absolute_path
            latex_dir = writer.data_dir
            latex_filename = writer.filename

            self.log.info("Outputting Latex to %s" % latex_path)
            writer.write_data((DOC_TEMPLATE % u"\n\n".join(
                u"\\section{%s model}\n%s" % (model,
                                              u"\n".join(
                                                  section_text for corpus, section_text in
                                                  sorted(section.items(), key=itemgetter(0))
                                              ))
                for model, section in sorted(sections.items(), key=itemgetter(0))
            )).encode("utf-8"))

        # Copy he Doulos SIL font file to the output dir
        shutil.copy2(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "DoulosSIL-R.ttf"),
            latex_dir
        )

        # Try compiling
        try:
            subprocess.check_call(["xelatex", latex_filename], cwd=latex_dir)
            subprocess.check_call(["xelatex", latex_filename], cwd=latex_dir)
        except subprocess.CalledProcessError, e:
            self.log.info("Could not compile latex document: %s" % e)
            self.log.info("Latex file is ready to be compiled: %s" % latex_path)
        else:
            self.log.info("Compiled latex document")


def latexify(s):
    return s.replace(u"_", u"\\_").replace(u"&", u"\\&")


def latex_ipa(s):
    return s.replace(u"^", u"\^{}")
