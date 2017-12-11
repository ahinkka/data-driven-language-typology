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

import os
import cPickle as pickle
from StringIO import StringIO
from collections import OrderedDict

from pimlico.core.dependencies.python import numpy_dependency
from pimlico.datatypes.arrays import NumpyArray
from pimlico.datatypes.base import PimlicoDatatype, PimlicoDatatypeWriter
from pimlico.datatypes.dictionary import Dictionary


class ConfusionMatrix(PimlicoDatatype):
    def __init__(self, base_dir, pipeline, **kwargs):
        super(ConfusionMatrix, self).__init__(base_dir, pipeline, **kwargs)

        self._vocab = None
        self._matrix = None
        self._id2token = None

    def data_ready(self):
        return super(ConfusionMatrix, self).data_ready() and os.path.exists(os.path.join(self.data_dir, "array.npy")) \
            and os.path.exists(os.path.join(self.data_dir, "dictionary"))

    def get_software_dependencies(self):
        return super(ConfusionMatrix, self).get_software_dependencies() + [numpy_dependency]

    @property
    def id2token(self):
        if self._id2token is None:
            self._id2token = dict(self.vocab.id2token)
            self._id2token[len(self.vocab)] = "OOV"
            self._id2token[len(self.vocab)+1] = "STOP"
        return self._id2token

    @property
    def vocab(self):
        if self._vocab is None:
            self._vocab = Dictionary(self.base_dir, self.pipeline).get_data()
        return self._vocab

    @property
    def matrix(self):
        if self._matrix is None:
            self._matrix = NumpyArray(self.base_dir, self.pipeline).array
        return self._matrix

    def summary_for_target(self, char, out=None):
        data = self.summary_data_for_target(char, out=out)

        if out is None:
            out = StringIO()
        print >>out, data["heading"]
        print >>out, "Total counts:    %.2f" % data["total_counts"]
        if "accuracy" in data:
            print >>out, "Accuracy/share:  %.3f%%" % data["accuracy"]
            print >>out, u"Top confusions: %s" % u", ".join(
                u"'%s' (%.2f)" % (conf_char, weight) for (conf_char, weight) in data["confusions"][:8]
            )
        return out

    def summary_data_for_target(self, char, out=None):
        if char not in self.vocab.token2id:
            raise ValueError(u"target char '%s' not in vocab" % char)
        char_id = self.vocab.token2id[char]
        counts = self.matrix[char_id]
        dist = counts / counts.sum()

        data = OrderedDict()
        data["heading"] = u"Target character: %s" % char
        data["char"] = char
        data["total_counts"] = counts.sum()
        if counts.sum() > 0.:
            data["accuracy"] = dist[char_id] * 100.
            data["confusions"] = [
                (self.id2token[i], dist[i]) for i in reversed(dist.argsort())
            ]
        return data

    def summary(self, out=None):
        if out is None:
            out = StringIO()

        for char_id in range(len(self.vocab)):
            self.summary_for_target(self.vocab[char_id], out=out)
            print >>out
        return out

    def top_confusions(self, min_target_freq=0.01):
        import numpy
        # We're not interested in targets that occur very rarely
        # Apply a cutoff in terms of the relative frequency of the target
        target_freq = self.matrix.sum(axis=1)
        target_freq /= target_freq.sum()
        rare_targets = numpy.where(target_freq < min_target_freq)[0]
        # Normalize the rows of the matrix to get the consistency of confusions for each target
        conf_freqs = self.matrix / self.matrix.sum(axis=1)[:, numpy.newaxis]
        # Sort 2D array indices by the consistency of the confusion they represent
        top_targets, top_confs = numpy.unravel_index((-conf_freqs).argsort(axis=None), self.matrix.shape)
        # Exclude rare targets from the returned index pairs
        return [
            (trg, conf) for (trg, conf) in zip(top_targets, top_confs)
            if trg not in rare_targets and trg != conf
        ]


class ConfusionMatrixWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir, **kwargs):
        super(ConfusionMatrixWriter, self).__init__(base_dir, **kwargs)
        self.require_tasks("vocab", "matrix")

    def store_matrix(self, matrix):
        import numpy
        numpy.save(os.path.join(self.data_dir, "array.npy"), matrix)
        self.task_complete("matrix")

    def store_vocab(self, vocab):
        with open(os.path.join(self.data_dir, "dictionary"), "w") as f:
            pickle.dump(vocab, f, -1)
        self.task_complete("vocab")
