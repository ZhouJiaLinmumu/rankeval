# Copyright (c) 2017, All Contributors (see CONTRIBUTORS file)
# Authors: Salvatore Trani <salvatore.trani@isti.cnr.it>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
This package implements several effectiveness analysis focused on assessing
the performance of the models in terms of accuracy. These functionalities can
be applied to several models at the same time, so to have a direct comparison
of the analysis performed.
"""

# Authors: Salvatore Trani <salvatore.trani@isti.cnr.it>, Franco Maria Nardini <francomaria.nardini@isti.cnr.it>
# License: <TO DEFINE>

import numpy as np
import xarray as xr

from rankeval.core.dataset import Dataset
from rankeval.core.model import RTEnsemble
from rankeval.core.metrics import Metric


def model_performance(datasets=[], models=[], metrics=[], display=False):
    """
    This method implements the model performance analysis (part of the effectiveness analysis category).

    Parameters
    ----------
    datasets : list of Dataset
        The datasets to use for analyzing the behaviour of the model using the given metrics and models
    models : list of RTEnsemble
        The models to analyze
    metrics : list of Metric
        The metrics to use for the analysis
    display : bool
        True if the method has to display interestingly insights using inline plots/tables
        These additional information will be displayed only if working inside a ipython notebook.

    Returns
    -------
    metric_scores : xarray.DataArray
        A DataArray containing the metric scores of the models using the given metrics on the given datasets.
    """
    data = np.zeros(shape=(len(datasets), len(models), len(metrics)), dtype=np.float32)
    for idx_dataset, dataset in enumerate(datasets):
        for idx_model, model in enumerate(models):
            scorer = model.score(dataset, detailed=False)
            for idx_metric, metric in enumerate(metrics):
                data[idx_dataset][idx_model][idx_metric] = metric.eval(dataset, scorer.y_pred)[0]

    performance = xr.DataArray(data,
                               name='Model Performance',
                               coords=[datasets, models, metrics],
                               dims=['dataset', 'model', 'metric'])

    if display:
        try:
            from IPython.display import display, HTML
            for dataset in performance.coords['dataset'].values:
                display(HTML("<h3>Dateset: %s</h3>" % dataset))
                display(performance.sel(dataset=dataset).to_pandas())
        except ImportError:
            pass

    return performance


def tree_wise_performance(datasets=[], models=[], metrics=[], step=10, display=False):
    """
    This method implements the analysis of the model on a tree-wise basis (part of the effectiveness analysis category).

    Parameters
    ----------
    datasets : list of Dataset
        The datasets to use for analyzing the behaviour of the model using the given metrics and models
    models : list of RTEnsemble
        The models to analyze
    metrics : list of Metric
        The metrics to use for the analysis
    step : int
        Step-size identifying evenly spaced number of trees for evaluating the top=k model performance.
        (e.g., step=100 means the method will evaluate the model performance at 100, 200, 300, etc trees).
    display : bool
        True if the method has to display interestingly insights using inline plots/tables
        These additional information will be displayed only if working inside a ipython notebook.

    Returns
    -------
    metric_scores : xarray.DataArray
        A DataArray containing the metric scores of each model using the given metrics on the given datasets.
        The metric scores are cumulatively reported tree by tree, i.e., top 10 trees, top 20, etc., with a step-size
        between the number of trees as highlighted by the step parameter.

    """
    def get_tree_steps(model_trees):
        trees = range(step-1, model_trees, step)
        # Add last tree to the steps
        if trees[-1] != model_trees-1:
            trees.append(model_trees-1)
        return np.array(trees)

    max_num_trees = 0
    for model in models:
        if model.n_trees > max_num_trees:
            max_num_trees = model.n_trees

    tree_steps = get_tree_steps(max_num_trees)

    data = np.empty(shape=(len(datasets), len(models), len(tree_steps), len(metrics)), dtype=np.float32)
    data.fill(np.nan)

    for idx_dataset, dataset in enumerate(datasets):
        for idx_model, model in enumerate(models):
            scorer = model.score(dataset, detailed=True)

            # the document scores are accumulated along for the various top-k (in order to avoid useless re-scoring)
            y_pred = np.zeros(dataset.n_instances)

            for idx_top_k, top_k in enumerate(get_tree_steps(model.n_trees)):

                # compute the document scores using only top-k trees of the model on the given dataset
                for idx_tree in np.arange(start=idx_top_k*step, stop=top_k+1):
                    for idx_instance in np.arange(dataset.n_instances):
                        y_pred[idx_instance] += scorer.partial_y_pred[idx_instance][idx_tree]

                # compute the metric score using the predicted document scores
                for idx_metric, metric in enumerate(metrics):
                    metric_score, _ = metric.eval(dataset, y_pred)
                    data[idx_dataset][idx_model][idx_top_k][idx_metric] = metric_score

    performance = xr.DataArray(data,
                               name='Tree-Wise Performance',
                               coords=[datasets, models, tree_steps+1, metrics],
                               dims=['dataset', 'model', 'k', 'metric'])
    return performance


def tree_wise_average_contribution(datasets=[], models=[], display=False):
    """
    This method provides the average contribution given by each tree of each model to the scoring of the datasets.

    Parameters
    ----------
    datasets : list of Dataset
        The datasets to use for analyzing the behaviour of the model using the given metrics and models
    models : list of RTEnsemble
        The models to analyze
    display : bool
        True if the method has to display interestingly insights using inline plots/tables
        These additional information will be displayed only if working inside a ipython notebook.

    Returns
    -------
    average_contribution : xarray.DataArray
        A DataArray containing the average contribution given by each tree of
        each model to the scoring of the given datasets. The average
        contribution are reported tree by tree.
    """

    max_num_trees = 0
    for model in models:
        if model.n_trees > max_num_trees:
            max_num_trees = model.n_trees

    data = np.empty(shape=(len(datasets), len(models), max_num_trees), dtype=np.float32)
    data.fill(np.nan)

    for idx_dataset, dataset in enumerate(datasets):
        for idx_model, model in enumerate(models):
            scorer = model.score(dataset, detailed=True)

            # the document scores are accumulated along for the various top-k (in order to avoid useless re-scoring)
            y_contributes = np.empty(max_num_trees, dtype=np.float32)
            y_contributes.fill(np.nan)
            y_contributes[:model.n_trees] = np.average(np.abs(scorer.partial_y_pred), axis=0)

            data[idx_dataset][idx_model] = y_contributes

    performance = xr.DataArray(data,
                               name='Tree-Wise Average Contribution',
                               coords=[datasets, models, np.arange(max_num_trees)],
                               dims=['dataset', 'model', 'trees'])
    return performance


def query_wise_performance(datasets=[], models=[], metrics=[], bins=None, start=None, end=None, display=False):
    """
    This method implements the analysis of the model on a query-wise basis, i.e., it compute the cumulative distribution
    of a given performance metric. For example, the fraction of queries with a NDCG score smaller that any given
    threshold, over the set of queries described in the dataset.

    Parameters
    ----------
    datasets : list of Dataset
        The datasets to use for analyzing the behaviour of the model using the given metrics and models
    models : list of RTEnsemble
        The models to analyze
    metrics : list of Metric
        The metrics to use for the analysis
    bins : int or None
        Number of equi-spaced bins for which to computer the cumulative distribution of the given metric.
        if bin is None, it will use the maximum number of queries across all the datasets as bins value.
    start : int or None
        The start point of the range for which we will compute the cumulative distribution of the given metric.
        if start is None, it will use the minimum metric score as starting point for the range.
    end : int or None
        The end point of the range for which we will compute the cumulative distribution of the given metric
        if end is None, it will use the maximum metric score as starting point for the range.
    display : bool
        True if the method has to display interestingly insights using inline plots/tables
        These additional information will be displayed only if working inside a ipython notebook.

    Returns
    -------
    metric_scores : xarray.DataArray
        A DataArray containing the metric scores of each model using the given metrics on the given datasets.
        The metric scores are cumulatively reported tree by tree, i.e., top 10 trees, top 20, etc., with a step-size
        between the number of trees as highlighted by the step parameter.
    """
    glob_metric_scores = np.empty(shape=(len(datasets), len(models), len(metrics)), dtype=object)
    glob_metric_scores.fill(np.nan)

    min_metric_score = max_metric_score = np.nan
    for idx_dataset, dataset in enumerate(datasets):
        for idx_model, model in enumerate(models):
            scorer = model.score(dataset, detailed=False)
            for idx_metric, metric in enumerate(metrics):
                _, metric_scores = metric.eval(dataset, scorer.y_pred)
                glob_metric_scores[idx_dataset][idx_model][idx_metric] = metric_scores
                min_metric_score = np.nanmin([min_metric_score, metric_scores.min()])
                max_metric_score = np.nanmax([max_metric_score, metric_scores.max()])

    if start is None:
        start = min_metric_score
    if end is None:
        end = max_metric_score
    if bins is None:
        bins = np.max([dataset.n_queries for dataset in datasets])

    bin_values = np.linspace(start=start, stop=end, num=bins+1)

    data = np.empty(shape=(len(datasets), len(models), len(metrics), bins), dtype=np.float32)
    data.fill(np.nan)

    for idx_dataset, dataset in enumerate(datasets):
        for idx_model, model in enumerate(models):
            for idx_metric, metric in enumerate(metrics):
                metric_scores = glob_metric_scores[idx_dataset][idx_model][idx_metric]
                # evaluate the histogram
                values, base = np.histogram(metric_scores, bins=bin_values)
                # evaluate the cumulative
                cumulative = np.cumsum(values, dtype=float) / bins

                data[idx_dataset][idx_model][idx_metric] = cumulative

    performance = xr.DataArray(data,
                               name='Query-Wise Performance',
                               coords=[datasets, models, metrics, bin_values[:-1] + 1.0 / bins],
                               dims=['dataset', 'model', 'metric', 'bin'])
    return performance


def query_class_performance(datasets=[], models=[], metrics=[], query_classes=[], display=False):
    """
    This method implements the analysis of the effectiveness of a given model by providing a breakdown of the 
    performance over query class. Whenever a query classification is provided, e.g., navigational, informational,
    transactional, number of terms composing the query, etc., it provides the model effectiveness over such classes.
    This analysis is important especially in a production environment, as it allows to calibrate the ranking
    infrastructure w.r.t. a specific context.
    
    
    Parameters
    ----------
    datasets : list of Dataset
        The datasets to use for analyzing the behaviour of the model using the given metrics and models
    models : list of RTEnsemble
        The models to analyze
    metrics : list of Metric
        The metrics to use for the analysis
    query_classes : list of lists
        A list containing lists of classes each one for a specific Dataset. The i-th item in the j-th list identifies
        the class of the i-th query of the j-th Dataset.
    display : bool
        True if the method has to display interestingly insights using inline plots/tables
        These additional information will be displayed only if working inside a ipython notebook. 
    
    Returns
    -------
    query_class_performance : xarray.DataArray
        A DataArray containing the per-class metric scores of each model using the given metrics on the given datasets.
    """

    glob_metric_scores = np.empty(shape=(len(datasets), len(models), len(metrics)), dtype=object)
    glob_metric_scores.fill(np.nan)

    for idx_dataset, dataset in enumerate(datasets):
        for idx_model, model in enumerate(models):
            scorer = model.score(dataset, detailed=False)
            for idx_metric, metric in enumerate(metrics):
                _, metric_scores = metric.eval(dataset, scorer.y_pred)
                glob_metric_scores[idx_dataset][idx_model][idx_metric] = metric_scores

    # computing unique elements for each list of query class
    unique_query_classes = [np.unique(query_class) for query_class in query_classes]
    unique_classes = np.unique([c for d in unique_query_classes for c in d])

    # defining destination array now saving values of the specific metric directly
    query_class_metric_scores = np.empty(shape=(len(datasets), len(models), len(metrics), len(unique_classes)),
                                         dtype=np.float32)
    query_class_metric_scores.fill(np.nan)

    # computing the average metric over the specific categorization
    for idx_dataset, dataset in enumerate(datasets):
        for idx_model, model in enumerate(models):
            for idx_metric, metric in enumerate(metrics):
                for idx_query_class, query_class in enumerate(unique_classes):

                    indices = np.where(query_classes[idx_dataset] == query_class)
                    # If this query class is not present in this dataset, skip it
                    if not len(indices):
                        continue

                    query_class_metric_scores[idx_dataset][idx_model][idx_metric][idx_query_class] = \
                        glob_metric_scores[idx_dataset][idx_model][idx_metric][indices].mean()

    performance = xr.DataArray(query_class_metric_scores,
                               name='Query Class Performance',
                               coords=[datasets, models, metrics, unique_classes],
                               dims=['dataset', 'model', 'metric', 'classes'])

    return performance


def document_graded_relevance(datasets=[], models=[], bins=100, start=None, end=None, display=False):
    """
    This method implements the analysis of the model on a per-label basis,
    i.e., it allows the evaluation of the cumulative predicted score
    distribution. For example, for each relevance label available in each
    dataset, it provides the fraction of documents with a predicted score
    smaller than a given score (the latter are binned among start and end).
    By plotting this fractions it is possible to obtains a curve for each
    relevance label. The bigger the distance amongst curves the larger the
    model's discriminative power.

    Parameters
    ----------
    datasets : list of Dataset
        The datasets to use for analyzing the behaviour of the model using the given models
    models : list of RTEnsemble
        The models to analyze
    bins : int or None
        Number of equi-spaced bins for which to computer the cumulative distribution of the predicted scores.
        if bin is None, it will use the maximum number of queries across all the datasets as bins value.
    start : int or None
        The start point of the range for which we will compute the cumulative distribution of the predicted scores.
        if start is None, it will use the minimum metric score as starting point for the range.
    end : int or None
        The end point of the range for which we will compute the cumulative distribution of the predicted scores
        if end is None, it will use the maximum metric score as starting point for the range.
    display : bool
        True if the method has to display interestingly insights using inline plots/tables
        These additional information will be displayed only if working inside a ipython notebook.

    Returns
    -------
    graded_relevance : xarray.DataArray
        A DataArray containing the fraction of documents with a predicted score
        smaller than a given score, for each model and each dataset.
    """

    glob_doc_scores = np.empty(shape=(len(datasets), len(models)), dtype=object)
    glob_doc_scores.fill(np.nan)

    min_doc_score = max_doc_score = np.nan
    for idx_dataset, dataset in enumerate(datasets):
        for idx_model, model in enumerate(models):
            scorer = model.score(dataset, detailed=True)
            glob_doc_scores[idx_dataset][idx_model] = scorer.y_pred
            min_doc_score = np.nanmin([min_doc_score, scorer.y_pred.min()])
            max_doc_score = np.nanmax([max_doc_score, scorer.y_pred.max()])

    if start is None:
        start = min_doc_score
    if end is None:
        end = max_doc_score

    bin_values = np.linspace(start=start, stop=end, num=bins+1)

    rel_labels = np.sort(np.unique([dataset.y for dataset in datasets]))

    data = np.empty(shape=(len(datasets), len(models), len(rel_labels), bins), dtype=np.float32)
    data.fill(np.nan)

    for idx_dataset, dataset in enumerate(datasets):
        for idx_model, model in enumerate(models):
            for idx_label, graded_rel in enumerate(rel_labels):
                indices = np.where(dataset.y == graded_rel)
                # If this graded relevance is not present in this dataset, skip it
                if not len(indices):
                    continue
                scorer = model.score(dataset, detailed=False)
                y_pred = scorer.y_pred[indices]
                # evaluate the histogram
                values, base = np.histogram(y_pred, bins=bin_values)
                # evaluate the cumulative
                cumulative = np.cumsum(values, dtype=float) / len(y_pred)
                data[idx_dataset][idx_model][idx_label] = cumulative

    performance = xr.DataArray(data,
                               name='Document Graded Relevance',
                               coords=[datasets, models, rel_labels, bin_values[:-1] + 1.0 / bins],
                               dims=['dataset', 'model', 'label', 'bin'])
    return performance


def rank_confusion_matrix(datasets=[], models=[], skip_same_label=False, display=False):
    """
    RankEval allows for a novel rank-oriented confusion matrix by reporting for
    any given relevance label  l_i, the number of document with a predicted
    score smaller than documents with label l_j. When  l_i > l_j this
    corresponds to the number of mis-ranked document pairs. This can be
    considered as a breakdown over the relevance labels of the ranking
    effectiveness of the model.

    Parameters
    ----------
    datasets : list of Dataset
        The datasets to use for analyzing the behaviour of the model using the given models
    models : list of RTEnsemble
        The models to analyze

    display : bool
        True if the method has to display interestingly insights using inline plots/tables
        These additional information will be displayed only if working inside a ipython notebook.
    skip_same_label : bool
        True if the method has to skip the pair with the same labels, False otherwise

    Returns
    -------
    ranked_matrix: xarray.DataArray
        A DataArray reporting for any given relevance label  l_i, the number of
        documents with a predicted score smaller than documents with label l_j
    """

    rel_labels = np.sort(np.unique([dataset.y for dataset in datasets])).astype(np.int32)

    data = np.zeros(shape=(len(datasets), len(models), len(rel_labels), len(rel_labels)), dtype=np.int32)

    for idx_dataset, dataset in enumerate(datasets):
        for idx_model, model in enumerate(models):
            scorer = model.score(dataset, detailed=True)
            for query_id, (start_offset, end_offset) in enumerate(dataset.query_offset_iterator()):
                for i in np.arange(start_offset, end_offset):
                    for j in np.arange(i, end_offset):
                        # check if the two documents have the same label and skip them
                        if skip_same_label and dataset.y[i] == dataset.y[j]:
                            continue
                        y_i = dataset.y[i].astype(np.int32)
                        y_j = dataset.y[j].astype(np.int32)
                        if scorer.y_pred[i] < scorer.y_pred[j]:
                            data[idx_dataset][idx_model][y_i, y_j] += 1
                        else:
                            data[idx_dataset][idx_model][y_j, y_i] += 1

    performance = xr.DataArray(data,
                               name='Rank Confusion Matrix',
                               coords=[datasets, models, rel_labels, rel_labels],
                               dims=['dataset', 'model', 'label_i', 'label_j'])
    return performance
