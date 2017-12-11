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

import argparse
import codecs
import datetime
import os
import subprocess
import sys
import tempfile


stdin8 = codecs.getwriter('utf-8')(sys.stdin)
stdout8 = codecs.getwriter('utf-8')(sys.stdout)
stderr8 = codecs.getwriter('utf-8')(sys.stderr)


BATCH_LINES = 1000


def espeak_transcribe(language, line_buffer, output):
    # Hack to pass in DYLD_LIBRARY_PATH environment variable on Mac (equivalent to LD_LIBRARY_PATH on Linux).
    if "USE_DYLD_LIBRARY_PATH" in os.environ:
        os.environ["DYLD_LIBRARY_PATH"] = os.environ["USE_DYLD_LIBRARY_PATH"]

    with tempfile.NamedTemporaryFile(prefix=__file__.replace(".py", ""), delete=True) as i_f:
        utf8_i_f = codecs.getwriter('utf-8')(i_f)
        for line in line_buffer:
            try:
                i_f.write(line)
            except:
                utf8_i_f.write(line)
        i_f.flush()

        cmd = ["espeak", "-v", language, "--ipa=3", "-q", "-f", i_f.name]
        # print("# Calling {}".format(" ".join(cmd), file=stderr8))
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        espeak_output = unicode(p.communicate()[0], 'utf-8')
        # print("# Transcribed {} to {}".format(os.path.getsize(i_f.name), len(espeak_output)),
        #       file=stderr8)
        output.write(espeak_output)


def main(input_file, output_file, language):
    reading_from_stdin = 'stdin' in repr(input_file)

    line_count = None
    if not reading_from_stdin:
        line_count = 0
        for line in input_file:
            line_count += 1
        input_file.seek(0)

    line_buffer = []
    lines_done = 0
    lines_done_total = 0
    first_started = datetime.datetime.now()
    started = first_started
    handled_lines = 0
    for line in input_file:
        if lines_done < BATCH_LINES:
            line_buffer.append(line)
            lines_done += 1
        elif lines_done == BATCH_LINES:
            espeak_transcribe(language, line_buffer, output_file)
            took_secs = (datetime.datetime.now() - started).total_seconds()
            print("# {} lines per sec".format(BATCH_LINES / took_secs),
                  file=stderr8)
            if line_count is not None:
                took_total_secs = (datetime.datetime.now() - first_started).total_seconds()
                speed_overall = lines_done_total / took_total_secs
                to_go = line_count - lines_done_total
                secs_to_go = int(to_go * speed_overall)
                hours_to_go = secs_to_go / float(3600)
                print("# {:.2f}% done; {} hours to complete"
                      .format(lines_done_total / float(line_count),
                              hours_to_go), file=stderr8)
            started = datetime.datetime.now()
            lines_done_total += lines_done
            lines_done = 0
            line_buffer = []

    if len(line_buffer) > 0:
        espeak_transcribe(language, line_buffer, output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Wrap espeak IPA transcription into a thing that works')

    parser.add_argument('input', nargs='?', type=argparse.FileType('r'),
                        default=stdin8)
    parser.add_argument('output', nargs='?', type=argparse.FileType('w'),
                        default=stdout8)
    parser.add_argument('--language', type=str, required=True)
    args = parser.parse_args()
    main(args.input, args.output, args.language)
