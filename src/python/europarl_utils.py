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
"""
Contents of this module are from Mark's europarl.py. These are intended to be used for the phonetic transcription
'pipeline' so that documents that are dropped by the text pipeline are likewise dropped without transcribing them."""
import codecs
import re

language_indicator_re = re.compile(r"\([A-Z]{2}\) ")


def filter_document(lines):
    lines = [filter_line(line) for line in lines]
    lines = [line for line in lines if line is not None]
    # If a document has only a couple of lines in it, it's not a debate transcript, but just a heading
    # Better to skip these
    if len(lines) < 4:
        return None
    return lines


def filter_line(line):
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


def is_empty_doc(absolute_path):
    with codecs.open(absolute_path, 'r', encoding='utf-8') as i_f:
        lines = i_f.read().split('\n')
        filtered = filter_document(lines)
    return filtered is None or len(filtered) == 0
