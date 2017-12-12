#!/usr/bin/env python
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
import argparse

import collections

import logging

import codecs
import os
import random
import sqlite3

import europarl_utils
from espeak_transcript import espeak_transcribe
from patharg import PathType


Document = collections.namedtuple('Document', ['language', 'relative_path'])


def collect_files(root_dir):
    for directory, _, files in os.walk(root_dir, topdown=False):
        for item in files:
            language = [part for part in directory.split(os.sep) if len(part) == 2][0]
            yield Document(language=language, relative_path=os.path.relpath(os.path.join(directory, item), root_dir))


def init(args, logger):
    input_dir = args.input_directory
    output_dir = args.output_directory

    logger.info("Initializing transcription process...")

    conn = sqlite3.connect(args.database)
    c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE documents
                 (language TEXT,
                  input_dir TEXT,
                  output_dir TEXT,
                  relative_path TEXT,
                  started BOOLEAN,
                  finished BOOLEAN,
                  empty_doc BOOLEAN,
                  token_count INT)''')

    for idx, f in enumerate(collect_files(input_dir)):
        try:
            empty_doc = europarl_utils.is_empty_doc(os.path.join(input_dir, f.relative_path))
        except:
            logger.warn(u"Couldn't determine if document {} is empty or not; skipping"
                        .format(f.relative_path))
            empty_doc = True
        c.execute("INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (f.language, input_dir, output_dir, f.relative_path, False, False, empty_doc, 0))
        if idx % 1000 == 0:
            conn.commit()
            logger.info("{} added".format(idx))
    conn.commit()
    conn.close()


def transcribe(args, logger):
    logger.info("Transcriber started")

    documents_done = 0
    while True:
        conn = sqlite3.connect(args.database)
        c = conn.cursor()
        c.row_factory = sqlite3.Row

        # Pick a random language
        c.execute("SELECT DISTINCT language FROM documents")
        lang = random.choice(c.fetchall())[0]

        # Start work on a document
        c.execute("SELECT * FROM documents WHERE language=? AND started=0 AND empty_doc=0", (lang,))
        row = c.fetchone()
        relative_path = row["relative_path"]
        c.execute("UPDATE documents SET started=1 WHERE relative_path=?", (relative_path,))
        conn.commit()
        logger.info("Transcribing {}".format(relative_path))

        # c.execute("SELECT * FROM documents WHERE relative_path=?", (relative_path,))
        # print(c.fetchone())

        from_path = os.path.join(row["input_dir"], relative_path)
        to_path = os.path.join(row["output_dir"], relative_path)
        logger.info("{} => {}".format(from_path, to_path))

        with codecs.open(from_path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
            filtered = europarl_utils.filter_document(lines)

            try:
                os.makedirs(os.path.split(to_path)[0])
            except:
                pass
            with codecs.open(to_path, 'w', encoding='utf-8') as of:
                espeak_transcribe(row["language"], filtered, of)
            with codecs.open(to_path, 'r', encoding='utf-8') as of:
                token_count = 0
                for line in of:
                    line = line.strip().replace('\n', '')
                    words = line.split(" ")
                    for word in words:
                        tokens = word.split("_")
                        token_count += len(tokens)
                c.execute("UPDATE documents SET token_count=? WHERE relative_path=?",
                          (token_count, relative_path))
                conn.commit()

        c.execute("UPDATE documents SET finished=1 WHERE relative_path=?", (relative_path,))
        conn.commit()
        documents_done += 1
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Phonetically transcribe a directory of text files')
    parser.add_argument('database')

    subparsers = parser.add_subparsers()
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument('input_directory', type=PathType(exists=True, type='dir'))
    init_parser.add_argument('output_directory')
    init_parser.set_defaults(func=init)

    transcribe_parser = subparsers.add_parser("transcribe")
    transcribe_parser.set_defaults(func=transcribe)

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("transcribe_europarl")
    # logger.setLevel(logging.INFO)
    args.func(args, logger)
