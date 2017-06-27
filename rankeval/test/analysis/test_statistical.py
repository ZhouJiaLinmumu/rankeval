import os
import unittest
import logging

import numpy as np
from numpy.testing import assert_array_almost_equal, assert_almost_equal

from rankeval.analysis.statistical import statistical_significance
from rankeval.analysis.statistical import _randomization

from rankeval.core.model import RTEnsemble
from rankeval.core.scoring.scorer import Scorer
from rankeval.core.dataset import Dataset
from rankeval.core.metrics.ndcg import NDCG

from rankeval.test.base import data_dir



class StatisticalSignificanceTestCase(unittest.TestCase):

    def setUp(self):
        self.model_a = RTEnsemble(os.path.join(data_dir, "quickrank.model.xml"), format="quickrank")
        self.model_b = RTEnsemble(os.path.join(data_dir, "quickrank.model.v2.xml"), format="quickrank")
        self.dataset = Dataset.load(os.path.join(data_dir, "msn1.fold1.test.5k.txt"), format="svmlight")
        self.metric = NDCG()

    def tearDown(self):
        del self.model_a
        self.model_a = None
        del self.model_b
        self.model_b = None
        del self.dataset
        self.dataset = None
        del self.metric
        self.metric = None
 
    def test_statistical_significance(self):
    	data = statistical_significance([self.dataset], self.model_a, self.model_b, [self.metric], n_perm=100)


    def test_randomization(self):
        A = np.array([1,1,1,1,1,1,1,0,0,0])
        B = np.array([0,0,0,0,0,0,0,1,1,1])
        n_perm = 10000
        p1,p2 = _randomization( A, B, n_perm)
        assert_almost_equal(p2, .34195, decimal=2) # compute with https://github.com/searchivarius/PermTest


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
    unittest.main()
