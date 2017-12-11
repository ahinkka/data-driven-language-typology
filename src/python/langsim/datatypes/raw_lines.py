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

from pimlico.datatypes.documents import RawTextDocumentType


class RawTextLinesDocumentType(RawTextDocumentType):
    """
    Like a raw-text document, but the data is assumed to have been split up in some way into subtexts,
    each consisting of a line. The subtexts may not include line breaks.

    """
    def process_document(self, doc):
        return doc.split(u"\n")
