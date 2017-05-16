import numpy as np
import os

from numpy.testing import assert_equal, assert_array_equal
from nose.tools import raises

from svmlight_loader import (load_svmlight_file, load_svmlight_files,
                             dump_svmlight_file)
from sklearn.datasets import load_svmlight_file as sk_load_svmlight_file

currdir = os.path.dirname(os.path.abspath(__file__))
datafile = os.path.join(currdir, "data", "svmlight_classification.txt")
invalidfile = os.path.join(currdir, "data", "svmlight_invalid.txt")

qid_datafile = os.path.join(currdir, "data", "svmlight_classification_qid.txt")

def test_load_svmlight_qid_file():
    X, y, q = load_svmlight_file(qid_datafile, query_id=True)

    # test X's shape
    assert_equal(X.shape[0], 6)
    print X

    # test X's non-zero values
    # tests X's zero values
    # test can change X's values

    # test y
    assert_array_equal(y, [1, 2, 3])

    # test q
    assert_array_equal(q, [1, 37, 12])


def test_load_svmlight_file_empty_qid():
    X, y, q = load_svmlight_file(datafile, query_id=True)

    # test X's shape
    assert_equal(X.shape[0], 6)

    # test X's non-zero values
    # tests X's zero values
    # test can change X's values

    # test y
    assert_array_equal(y, [1, 2, 3])

    # test q
    assert_equal(q.shape[0], 0)

def test_load_svmlight_file():
    X, y = load_svmlight_file(datafile)

    # test X's shape
    assert_equal(X.shape[0], 6)


    # test X's non-zero values
    # tests X's zero values
    # test can change X's values

    # test y
    assert_array_equal(y, [1, 2, 3])

def test_load_svmlight_files_comment_qid():
    X_train, y_train, q_train, X_test, y_test, q_test = load_svmlight_files([datafile] * 2,
                                                           dtype=np.float32, query_id=True)
    assert_array_equal(X_train, X_test)
    assert_array_equal(y_train, y_test)
    assert_equal(X_train.dtype, np.float32)
    assert_equal(X_test.dtype, np.float32)

    X1, y1, q1, X2, y2, q2, X3, y3, q3 = load_svmlight_files([datafile] * 3,
                                                 dtype=np.float64, query_id=True)
    assert_equal(X1.dtype, X2.dtype)
    assert_equal(X2.dtype, X3.dtype)
    assert_equal(X3.dtype, np.float64)
#
def test_load_svmlight_files():
    X_train, y_train, X_test, y_test = load_svmlight_files([datafile] * 2,
                                                           dtype=np.float32)
    assert_array_equal(X_train, X_test)
    assert_array_equal(y_train, y_test)
    assert_equal(X_train.dtype, np.float32)
    assert_equal(X_test.dtype, np.float32)

    X1, y1, X2, y2, X3, y3 = load_svmlight_files([datafile] * 3,
                                                 dtype=np.float64)
    assert_equal(X1.dtype, X2.dtype)
    assert_equal(X2.dtype, X3.dtype)
    assert_equal(X3.dtype, np.float64)


@raises(ValueError)
def test_load_invalid_file():
    load_svmlight_file(invalidfile)


@raises(ValueError)
def test_load_invalid_file2():
    load_svmlight_files([datafile, invalidfile, datafile])


@raises(TypeError)
def test_not_a_filename():
    load_svmlight_file(1)


@raises(IOError)
def test_invalid_filename():
    load_svmlight_file("trou pic nic douille")


def test_dump():
    try:
        # loads from file
        Xs, y, = load_svmlight_file(datafile)
        print Xs.shape

        # dumps to file
        tmpfile = "tmp_dump.txt"
        dump_svmlight_file(Xs, y, tmpfile, zero_based=False)

        # loads them as CSR MATRIX
        X2, y2 = sk_load_svmlight_file(tmpfile)
        print X2.shape

        # make CSR matrix 1darray like our data
        X3 = X2.toarray().flatten()
        print X3.shape

        # check assetions
        assert_array_equal(Xs, X3)
        assert_array_equal(y, y2)
    finally:
        os.remove(tmpfile)

def test_dump_qid():
    try:
        # loads from file
        Xs, y, q = load_svmlight_file(qid_datafile, query_id=True)

        # dumps to file
        tmpfile = "tmp_dump.txt"
        dump_svmlight_file(Xs, y, tmpfile, query_id=list(q), zero_based=False)

        # loads them as CSR MATRIX with scikit-learn
        X2, y2, q2 = sk_load_svmlight_file(tmpfile, query_id=True)

        # make CSR matrix 1darray like our data
        X3 = X2.toarray().flatten()
        print X3.shape

        # check assertions
        assert_array_equal(Xs, X3)
        assert_array_equal(y, y2)
        assert_array_equal(q, q2)
    finally:
        os.remove(tmpfile)
