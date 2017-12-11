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

import re

from langsim.datatypes.raw_lines import RawTextLinesDocumentType
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.files import RawTextDirectory


class EuroparlText(RawTextDirectory):
    """
    Read raw text from Europarl documents in a directory, filtering out the XML info.

    """
    data_point_type = RawTextLinesDocumentType
    datatype_name = "europarl_raw_text"

    def filter_document(self, doc):
        lines = [self.filter_line(line) for line in doc]
        lines = [line for line in lines if line is not None]
        # If a document has only a couple of lines in it, it's not a debate transcript, but just a heading
        # Better to skip these
        if len(lines) < 4:
            return InvalidDocument("reader:%s" % self.datatype_name,
                                   error_info="Too few lines in document: not a debate transcript")
        return lines

    def filter_line(self, line):
        """
        Filter applied to each line. It either returns an updated version of the line, or None, in which
        case the line is left out altogether.

        """
        if line.startswith("<"):
            # Simply filter out all lines beginning with '<', which are metadata
            return None

        # Some metadata-like text is also included at the start of lines, followed by ". - "
        if u". - " in line:
            __, __, line = line.partition(u". - ")

        # Remove -s and spaces from the start of lines
        # Not sure why they're often there, but it's just how the transcripts were formatted
        line = line.lstrip(u"- ")

        # Skip lines that are fully surrounded by brackets: they're typically descriptions of what happened
        # E.g. (Applause)
        if line.startswith(u"(") and line.endswith(u")"):
            return None

        # It's common for a speaker's first utterance to start with a marker indicating the original language
        line = language_indicator_re.sub(u"", line)
        return line


language_indicator_re = re.compile(r"\([A-Z]{2}\) ")
