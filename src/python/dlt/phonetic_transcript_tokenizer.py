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
from text_tokenizer import token_gen as _tg, Token


def _retain_token(token):
    # Skip items such as (en) and (el) in the Greek transcript
    if len(token) > 2 and token[0] == u'(' and token[-1] == u')':
        return False
    return True


def token_gen(text):
    for token in _tg(text, token_delimiter=u"_", retain_token=_retain_token):
        if token.letter.startswith(u'ˈ') or token.letter.startswith(u'ˌ'):
            token.letter = token.letter[1:]

        # Glottal stop compound phoneme handling
        #  This handles cases like ʔe where the glottal stop is placed together
        #  with the following vowel sound by eSpeak.
        if token.letter.startswith(u'ʔ') and len(token.letter) > 1:
            glottal_stop_token = Token(token.letter[0], token.is_beginning, False)
            yield glottal_stop_token
            next_token = Token(token.letter[1:], False, token.is_ending)
            token = next_token

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
