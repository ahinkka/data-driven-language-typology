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
import unicodedata as ud

from text_tokenizer import token_gen as _tg


def _rmdiacritics(char):
    desc = ud.name(unicode(char))
    cutoff = desc.find(' WITH ')
    if cutoff != -1:
        desc = desc[:cutoff]
    return ud.lookup(desc)


def token_gen(text):
    for token in _tg(text):
        token.letter = _rmdiacritics(token.letter)
        yield token


if __name__ == '__main__':
    import sys
    import codecs
    stdin8 = codecs.getwriter('utf-8')(sys.stdin)
    stdout8 = codecs.getwriter('utf-8')(sys.stdout)

    for line in stdin8:
        line = unicode(line, 'utf-8')
        for token in token_gen(line):
            if token.is_beginning:
                stdout8.write("<S>")
            stdout8.write(unicode(token))
            stdout8.write(u' ')
            if token.is_ending:
                stdout8.write("<E>\n")
