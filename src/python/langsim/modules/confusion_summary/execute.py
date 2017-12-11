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
import shutil
import subprocess
from operator import itemgetter

import numpy
import os
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.files import NamedFileWriter

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

\\title{Confusion matrix summary}
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


MIN_RELEVANT_FREQ = 0.02


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        # We've got lots of confusion matrices and accompanying vocabularies, which we need to understand them
        matrices = self.info.get_input("matrix")

        # Produce a section for every language pair
        sections = {}
        for conf_mat in matrices:
            # Get the language names from modvars
            model_lang = conf_mat.module.module_variables["model_lang"]
            corpus_lang = conf_mat.module.module_variables["corpus_lang"]
            # Find the most consistently confused target-prediction pairs
            top_confs = conf_mat.top_confusions(min_target_freq=MIN_RELEVANT_FREQ)
            conf_dist = conf_mat.matrix / conf_mat.matrix.sum(axis=1)[:, None]

            # Compute PMI, to account for commonly predicted chars
            prediction_counts = conf_mat.matrix.sum(axis=0)
            prediction_dist = prediction_counts / prediction_counts.sum()
            pmi = numpy.log(conf_dist) - numpy.log(prediction_dist)

            # Reorder the confusions by PMI
            # Filter out things that get predicted infrequently, since they're not relevant
            top_confs = sorted(((t, c) for (t, c) in top_confs
                                if prediction_dist[c] > MIN_RELEVANT_FREQ and conf_dist[t, c] > MIN_RELEVANT_FREQ),
                               key=lambda (trg, conf): -pmi[trg, conf])

            # Compute chi2 for each confusion
            #prediction_counts = conf_mat.matrix.sum(axis=0)
            #prediction_dist = prediction_counts / prediction_counts.sum()
            #((conf_dist - prediction_dist[:, numpy.newaxis]) ** 2.) / prediction_dist[:, numpy.newaxis]

            sections.setdefault(model_lang, {})[corpus_lang] = u"""
\\subsection{%s model on %s corpus}

Top confusions:

\\begin{longtable}{l l r r r}
\\textbf{Target} & \\textbf{Predicted} & \\textbf{Count} & \\textbf{Confusion freq} & \\textbf{PMI} \\\\\\hline
%s
\\end{longtable}
""" % (
                model_lang, corpus_lang,
                u" \\\\\n".join(
                    u"%s & %s & %.2f & %.2f\\%% & %.2f" % (
                        latex_ipa(latexify(conf_mat.id2token[trg])),
                        latex_ipa(latexify(conf_mat.id2token[conf])),
                        conf_mat.matrix[trg, conf] * 100.,
                        conf_dist[trg, conf] * 100.,
                        pmi[trg, conf]
                    ) for (trg, conf) in top_confs[:20]
                )
            )

        with NamedFileWriter(self.info.get_absolute_output_dir("latex"),
                             self.info.get_output("latex").filenames[0]) \
                as writer:
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
