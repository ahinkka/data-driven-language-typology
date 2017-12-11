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

import re


class Token(object):
    def __init__(self, letter, is_beginning, is_ending):
        self.letter = letter
        self.is_beginning = is_beginning
        self.is_ending = is_ending

    def __str__(self):
        return self.letter


def token_gen(text, token_delimiter=None, retain_token=None):
    words = text.split()

    for word in words:
        if len(word) == 0 or re.match(ur"\d+", word) or word in [u'-', '"']:
            continue

        if token_delimiter is None:
            for index, letter in enumerate(word):
                is_beginning = index == 0
                is_ending = index == len(word) - 1

                yield Token(unicode(letter.lower()), is_beginning, is_ending)
        else:
            # Prune out empty tokens
            parts = [part
                     for part in word.split(token_delimiter)
                     if part != u'']

            # If retain_token function is passed in, only retain the ones
            # which the function accepts, i.e. returns True for.
            if retain_token is not None:
                parts = [part for part in parts if retain_token(part)]

            for index, letter in enumerate(parts):
                is_beginning = index == 0
                is_ending = index == len(parts) - 1

                yield Token(unicode(letter.lower()), is_beginning, is_ending)


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
