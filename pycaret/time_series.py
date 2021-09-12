# Module: Time Series
# Author: Antoni Baum <antoni.baum@protonmail.com>
# License: MIT
# Release: PyCaret 2.2.0
# Last modified : 25/10/2020

import time
import logging

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from pycaret.internal.pycaret_experiment import TimeSeriesExperiment
from pycaret.internal.utils import check_if_global_is_not_none

from typing import List, Tuple, Any, Union, Optional, Dict
import warnings
import time

warnings.filterwarnings("ignore")

_CURRENT_EXPERIMENT = None
_CURRENT_EXPERIMENT_EXCEPTION = (
    "_CURRENT_EXPERIMENT global variable is not set. Please run setup() first."
)
_CURRENT_EXPERIMENT_DECORATOR_DICT = {
    "_CURRENT_EXPERIMENT": _CURRENT_EXPERIMENT_EXCEPTION
}


def setup(
    data: Union[pd.Series, pd.DataFrame],
    preprocess: bool = True,
    imputation_type: str = "simple",
    #        transform_target: bool = False,
    #        transform_target_method: str = "box-cox",
    fold_strategy: Union[str, Any] = "expanding",
    fold: int = 3,
    fh: Union[List[int], int, np.array] = 1,
    seasonal_period: Optional[Union[int, str]] = None,
    n_jobs: Optional[int] = -1,
    use_gpu: bool = False,
    custom_pipeline: Union[Any] = None,
    html: bool = True,
    session_id: Optional[int] = None,
    system_log: Union[bool, logging.Logger] = True,
    log_experiment: bool = False,
    experiment_name: Optional[str] = None,
    log_plots: Union[bool, list] = False,
    log_profile: bool = False,
    log_data: bool = False,
    verbose: bool = True,
    profile: bool = False,
    profile_kwargs: Dict[str, Any] = None,
):
    """
    This function initializes the training environment and creates the transformation
    pipeline. Setup function must be called before executing any other function. It takes
    two mandatory parameters: ``data`` and ``target``. All the other parameters are
    optional.

    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.time_series import *
    >>> exp_name = setup(data = boston,  target = 'medv')


    data : pandas.Series or pandas.DataFrame
        Shape (n_samples, 1), where n_samples is the number of samples.


    fh: np.array, default = None
        The forecast horizon to be used for forecasting. User must specify a value.
        The values of the array must be integers specifying the lookahead points that
        must be forecasted. e.g. np.array([2, 5]) will forecast 2 and 5 points ahead.
        Default value of None will result in an error.


    preprocess: bool, default = True
        When set to False, no transformations are applied except for train_test_split
        and custom transformations passed in ``custom_pipeline`` param. Data must be
        ready for modeling (no missing values, no dates, categorical data encoding),
        when preprocess is set to False.


    imputation_type: str, default = 'simple'
        The type of imputation to use. Can be either 'simple' or 'iterative'.


    fold_strategy: str or sklearn CV generator object, default = 'expanding'
        Choice of cross validation strategy. Possible values are:

        * 'expanding'
        * 'rolling' (same as/aliased to 'expanding')
        * 'sliding'

        You can also pass an sktime compatible cross validation object such
        as SlidingWindowSplitter or ExpandingWindowSplitter. In this case,
        the `fold` and `fh` parameters will be ignored and these values will
        be extracted from the fold_strategy object directly.


    fold: int, default = 3
        Number of folds to be used in cross validation. Must be at least 2. This is
        a global setting that can be over-written at function level by using ``fold``
        parameter. Ignored when ``fold_strategy`` is a custom object.


    fh: int, list or np.array, default = 1
        Number of steps ahead to take to evaluate forecast.


    seasonal_period: int or str, default = None
        Seasonal periods in timeseries data. If not provided the frequency of the data
        index is map to a seasonal period as follows:

        * "S": 60
        * "T": 60
        * 'H': 24
        * 'D': 7
        * 'W': 52
        * 'M': 12
        * 'Q': 4
        * 'A': 1
        * 'Y': 1

        Alternatively you can provide a custom `seasonal_parameter` by passing
        it as an integer.

        NOTE: If data index is not of type pd.core.indexes.period.PeriodIndex,
        then seasonal_period MUST be passed. Refer to the mapping above for
        a guide of what values to use depending on the frequency of the data.
        If your data does not have any seasonality, then set seasonal_period = 1.


    n_jobs: int, default = -1
        The number of jobs to run in parallel (for functions that supports parallel
        processing) -1 means using all processors. To run all functions on single
        processor set n_jobs to None.


    use_gpu: bool or str, default = False
        When set to True, it will use GPU for training with algorithms that support it,
        and fall back to CPU if they are unavailable. When set to 'force', it will only
        use GPU-enabled algorithms and raise exceptions when they are unavailable. When
        False, all algorithms are trained using CPU only.

        GPU enabled algorithms:

        - Extreme Gradient Boosting, requires no further installation

        - CatBoost Regressor, requires no further installation
        (GPU is only enabled when data > 50,000 rows)

        - Light Gradient Boosting Machine, requires GPU installation
        https://lightgbm.readthedocs.io/en/latest/GPU-Tutorial.html

        - Linear Regression, Lasso Regression, Ridge Regression, K Neighbors Regressor,
        Random Forest, Support Vector Regression, Elastic Net requires cuML >= 0.15
        https://github.com/rapidsai/cuml


    custom_pipeline: (str, transformer) or list of (str, transformer), default = None
        When passed, will append the custom transformers in the preprocessing pipeline
        and are applied on each CV fold separately and on the final fit. All the custom
        transformations are applied after 'train_test_split' and before pycaret's internal
        transformations.


    html: bool, default = True
        When set to False, prevents runtime display of monitor. This must be set to False
        when the environment does not support IPython. For example, command line terminal,
        Databricks Notebook, Spyder and other similar IDEs.


    session_id: int, default = None
        Controls the randomness of experiment. It is equivalent to 'random_state' in
        scikit-learn. When None, a pseudo random number is generated. This can be used
        for later reproducibility of the entire experiment.


    system_log: bool or logging.Logger, default = True
        Whether to save the system logging file (as logs.log). If the input
        already is a logger object, that one is used instead.


    log_experiment: bool, default = False
        When set to True, all metrics and parameters are logged on the ``MLFlow`` server.


    experiment_name: str, default = None
        Name of the experiment for logging. Ignored when ``log_experiment`` is not True.


    log_plots: bool or list, default = False
        When set to True, certain plots are logged automatically in the ``MLFlow`` server.
        To change the type of plots to be logged, pass a list containing plot IDs. Refer
        to documentation of ``plot_model``. Ignored when ``log_experiment`` is not True.


    log_profile: bool, default = False
        When set to True, data profile is logged on the ``MLflow`` server as a html file.
        Ignored when ``log_experiment`` is not True.


    log_data: bool, default = False
        When set to True, dataset is logged on the ``MLflow`` server as a csv file.
        Ignored when ``log_experiment`` is not True.


    verbose: bool, default = True
        When set to False, Information grid is not printed.


    profile: bool, default = False
        When set to True, an interactive EDA report is displayed.


    profile_kwargs: dict, default = {} (empty dict)
        Dictionary of arguments passed to the ProfileReport method used
        to create the EDA report. Ignored if ``profile`` is False.


    Returns:
        Global variables that can be changed using the ``set_config`` function.

    """

    exp = TimeSeriesExperiment()
    set_current_experiment(exp)
    return exp.setup(
        data=data,
        preprocess=preprocess,
        imputation_type=imputation_type,
        fold_strategy=fold_strategy,
        fold=fold,
        fh=fh,
        seasonal_period=seasonal_period,
        n_jobs=n_jobs,
        use_gpu=use_gpu,
        custom_pipeline=custom_pipeline,
        html=html,
        session_id=session_id,
        system_log=system_log,
        log_experiment=log_experiment,
        experiment_name=experiment_name,
        log_plots=log_plots,
        log_profile=log_profile,
        log_data=log_data,
        verbose=verbose,
        profile=profile,
        profile_kwargs=profile_kwargs,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def compare_models(
    include: Optional[List[Union[str, Any]]] = None,
    exclude: Optional[List[str]] = None,
    fold: Optional[Union[int, Any]] = None,
    round: int = 4,
    cross_validation: bool = True,
    sort: str = "smape",
    n_select: int = 1,
    budget_time: Optional[float] = None,
    turbo: bool = True,
    errors: str = "ignore",
    fit_kwargs: Optional[dict] = None,
    verbose: bool = True,
):

    """
    This function trains and evaluates performance of all estimators available in the
    model library using cross validation. The output of this function is a score grid
    with average cross validated scores. Metrics evaluated during CV can be accessed
    using the ``get_metrics`` function. Custom metrics can be added or removed using
    ``add_metric`` and ``remove_metric`` function.


    Example
    --------
    >>> from pycaret.datasets import get_data
    >>> from pycaret.internal.pycaret_experiment import TimeSeriesExperiment
    >>> airline = get_data('airline', verbose=False)
    >>> fh, fold = np.arange(1,13), 3
    >>> exp = TimeSeriesExperiment()
    >>> exp.setup(data=airline, fh=fh, fold=fold)
    >>> master_display_exp = exp.compare_models(fold=fold, sort='mape')


    include: list of str or scikit-learn compatible object, default = None
        To train and evaluate select models, list containing model ID or scikit-learn
        compatible object can be passed in include param. To see a list of all models
        available in the model library use the ``models`` function.


    exclude: list of str, default = None
        To omit certain models from training and evaluation, pass a list containing
        model id in the exclude parameter. To see a list of all models available
        in the model library use the ``models`` function.


    fold: int or scikit-learn compatible CV generator, default = None
        Controls cross-validation. If None, the CV generator in the ``fold_strategy``
        parameter of the ``setup`` function is used. When an integer is passed,
        it is interpreted as the 'n_splits' parameter of the CV generator in the
        ``setup`` function.


    round: int, default = 4
        Number of decimal places the metrics in the score grid will be rounded to.


    cross_validation: bool, default = True
        When set to False, metrics are evaluated on holdout set. ``fold`` param
        is ignored when cross_validation is set to False.


    sort: str, default = 'smape'
        The sort order of the score grid. It also accepts custom metrics that are
        added through the ``add_metric`` function.


    n_select: int, default = 1
        Number of top_n models to return. For example, to select top 3 models use
        n_select = 3.


    budget_time: int or float, default = None
        If not None, will terminate execution of the function after budget_time
        minutes have passed and return results up to that point.


    turbo: bool, default = True
        When set to True, it excludes estimators with longer training times. To
        see which algorithms are excluded use the ``models`` function.


    errors: str, default = 'ignore'
        When set to 'ignore', will skip the model with exceptions and continue.
        If 'raise', will break the function when exceptions are raised.


    fit_kwargs: dict, default = {} (empty dict)
        Dictionary of arguments passed to the fit method of the model.


    verbose: bool, default = True
        Score grid is not printed when verbose is set to False.


    Returns:
        Trained model or list of trained models, depending on the ``n_select`` param.


    Warnings
    --------
    - Changing turbo parameter to False may result in very high training times with
      datasets exceeding 10,000 rows.

    - No models are logged in ``MLFlow`` when ``cross_validation`` parameter is False.

    """

    return _CURRENT_EXPERIMENT.compare_models(
        include=include,
        exclude=exclude,
        fold=fold,
        round=round,
        cross_validation=cross_validation,
        sort=sort,
        n_select=n_select,
        budget_time=budget_time,
        turbo=turbo,
        errors=errors,
        fit_kwargs=fit_kwargs,
        verbose=verbose,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def create_model(
    estimator: Union[str, Any],
    fold: Optional[Union[int, Any]] = None,
    round: int = 4,
    cross_validation: bool = True,
    fit_kwargs: Optional[dict] = None,
    verbose: bool = True,
    **kwargs,
):

    """
    This function trains and evaluates the performance of a given estimator
    using cross validation. The output of this function is a score grid with
    CV scores by fold. Metrics evaluated during CV can be accessed using the
    ``get_metrics`` function. Custom metrics can be added or removed using
    ``add_metric`` and ``remove_metric`` function. All the available models
    can be accessed using the ``models`` function.


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> airline = get_data('airline')
    >>> from pycaret.internal.pycaret_experiment import TimeSeriesExperiment
    >>> exp = TimeSeriesExperiment()
    >>> exp.setup(data=airline, fh=12)
    >>> model = exp.create_model("naive")

    TODO: Update
    estimator: str or scikit-learn compatible object
        ID of an estimator available in model library or pass an untrained
        model object consistent with scikit-learn API. Estimators available
        in the model library (ID - Name):

        * 'arima' - ARIMA
        * 'naive' - Naive
        * 'poly_trend' - PolyTrend
        * 'exp_smooth' - ExponentialSmoothing
        * 'theta' - Theta


    fold: int or scikit-learn compatible CV generator, default = None
        Controls cross-validation. If None, the CV generator in the ``fold_strategy``
        parameter of the ``setup`` function is used. When an integer is passed,
        it is interpreted as the 'n_splits' parameter of the CV generator in the
        ``setup`` function.


    round: int, default = 4
        Number of decimal places the metrics in the score grid will be rounded to.


    cross_validation: bool, default = True
        When set to False, metrics are evaluated on holdout set. ``fold`` param
        is ignored when cross_validation is set to False.


    fit_kwargs: dict, default = {} (empty dict)
        Dictionary of arguments passed to the fit method of the model.


    verbose: bool, default = True
        Score grid is not printed when verbose is set to False.


    **kwargs:
        Additional keyword arguments to pass to the estimator.


    Returns:
        Trained Model


    Warnings
    --------
    - Models are not logged on the ``MLFlow`` server when ``cross_validation`` param
      is set to False.

    """

    return _CURRENT_EXPERIMENT.create_model(
        estimator=estimator,
        fold=fold,
        round=round,
        cross_validation=cross_validation,
        fit_kwargs=fit_kwargs,
        verbose=verbose,
        **kwargs,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def tune_model(
    estimator,
    fold: Optional[Union[int, Any]] = None,
    round: int = 4,
    n_iter: int = 10,
    custom_grid: Optional[Union[Dict[str, list], Any]] = None,
    optimize: str = "smape",
    custom_scorer=None,
    search_algorithm: Optional[str] = None,
    choose_better: bool = False,
    fit_kwargs: Optional[dict] = None,
    return_tuner: bool = False,
    verbose: bool = True,
    tuner_verbose: Union[int, bool] = True,
    **kwargs,
):

    """
    This function tunes the hyperparameters of a given estimator. The output of
    this function is a score grid with CV scores by fold of the best selected
    model based on ``optimize`` parameter. Metrics evaluated during CV can be
    accessed using the ``get_metrics`` function. Custom metrics can be added
    or removed using ``add_metric`` and ``remove_metric`` function.


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> lr = create_model('lr')
    >>> tuned_lr = tune_model(lr)


    estimator: scikit-learn compatible object
        Trained model object


    fold: int or scikit-learn compatible CV generator, default = None
        Controls cross-validation. If None, the CV generator in the ``fold_strategy``
        parameter of the ``setup`` function is used. When an integer is passed,
        it is interpreted as the 'n_splits' parameter of the CV generator in the
        ``setup`` function.


    round: int, default = 4
        Number of decimal places the metrics in the score grid will be rounded to.


    n_iter: int, default = 10
        Number of iterations in the grid search. Increasing 'n_iter' may improve
        model performance but also increases the training time.


    custom_grid: dictionary, default = None
        To define custom search space for hyperparameters, pass a dictionary with
        parameter name and values to be iterated. Custom grids must be in a format
        supported by the defined ``search_library``.


    optimize: str, default = 'R2'
        Metric name to be evaluated for hyperparameter tuning. It also accepts custom
        metrics that are added through the ``add_metric`` function.


    custom_scorer: object, default = None
        custom scoring strategy can be passed to tune hyperparameters of the model.
        It must be created using ``sklearn.make_scorer``. It is equivalent of adding
        custom metric using the ``add_metric`` function and passing the name of the
        custom metric in the ``optimize`` parameter.
        Will be deprecated in future.


    search_algorithm: str, default = None
        The search algorithm depends on the ``search_library`` parameter.
        Some search algorithms require additional libraries to be installed.
        If None, will use search library-specific default algorithm.

        - 'scikit-learn' possible values:
            - 'random' : random grid search (default)
            - 'grid' : grid search

        - 'scikit-optimize' possible values:
            - 'bayesian' : Bayesian search (default)

        - 'tune-sklearn' possible values:
            - 'random' : random grid search (default)
            - 'grid' : grid search
            - 'bayesian' : ``pip install scikit-optimize``
            - 'hyperopt' : ``pip install hyperopt``
            - 'optuna' : ``pip install optuna``
            - 'bohb' : ``pip install hpbandster ConfigSpace``

        - 'optuna' possible values:
            - 'random' : randomized search
            - 'tpe' : Tree-structured Parzen Estimator search (default)


    choose_better: bool, default = False
        When set to True, the returned object is always better performing. The
        metric used for comparison is defined by the ``optimize`` parameter.


    fit_kwargs: dict, default = {} (empty dict)
        Dictionary of arguments passed to the fit method of the tuner.


    return_tuner: bool, default = False
        When set to True, will return a tuple of (model, tuner_object).


    verbose: bool, default = True
        Score grid is not printed when verbose is set to False.


    tuner_verbose: bool or in, default = True
        If True or above 0, will print messages from the tuner. Higher values
        print more messages. Ignored when ``verbose`` param is False.


    **kwargs:
        Additional keyword arguments to pass to the optimizer.


    Returns:
        Trained Model and Optional Tuner Object when ``return_tuner`` is True.


    Warnings
    --------
    - Using 'grid' as ``search_algorithm`` may result in very long computation.
      Only recommended with smaller search spaces that can be defined in the
      ``custom_grid`` parameter.

    - ``search_library`` 'tune-sklearn' does not support GPU models.

    """

    return _CURRENT_EXPERIMENT.tune_model(
        estimator=estimator,
        fold=fold,
        round=round,
        n_iter=n_iter,
        custom_grid=custom_grid,
        optimize=optimize,
        custom_scorer=custom_scorer,
        search_algorithm=search_algorithm,
        choose_better=choose_better,
        fit_kwargs=fit_kwargs,
        return_tuner=return_tuner,
        verbose=verbose,
        tuner_verbose=tuner_verbose,
        **kwargs,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def ensemble_model(
    estimator,
    method: str = "Bagging",
    fold: Optional[Union[int, Any]] = None,
    n_estimators: int = 10,
    round: int = 4,
    choose_better: bool = False,
    optimize: str = "R2",
    fit_kwargs: Optional[dict] = None,
    verbose: bool = True,
) -> Any:

    """
    This function ensembles a given estimator. The output of this function is
    a score grid with CV scores by fold. Metrics evaluated during CV can be
    accessed using the ``get_metrics`` function. Custom metrics can be added
    or removed using ``add_metric`` and ``remove_metric`` function.


    Example
    --------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> dt = create_model('dt')
    >>> bagged_dt = ensemble_model(dt, method = 'Bagging')


    estimator: scikit-learn compatible object
        Trained model object


    method: str, default = 'Bagging'
        Method for ensembling base estimator. It can be 'Bagging' or 'Boosting'.


    fold: int or scikit-learn compatible CV generator, default = None
        Controls cross-validation. If None, the CV generator in the ``fold_strategy``
        parameter of the ``setup`` function is used. When an integer is passed,
        it is interpreted as the 'n_splits' parameter of the CV generator in the
        ``setup`` function.


    n_estimators: int, default = 10
        The number of base estimators in the ensemble. In case of perfect fit, the
        learning procedure is stopped early.


    round: int, default = 4
        Number of decimal places the metrics in the score grid will be rounded to.


    choose_better: bool, default = False
        When set to True, the returned object is always better performing. The
        metric used for comparison is defined by the ``optimize`` parameter.


    optimize: str, default = 'R2'
        Metric to compare for model selection when ``choose_better`` is True.


    fit_kwargs: dict, default = {} (empty dict)
        Dictionary of arguments passed to the fit method of the model.


    verbose: bool, default = True
        Score grid is not printed when verbose is set to False.


    Returns:
        Trained Model

    """

    return _CURRENT_EXPERIMENT.ensemble_model(
        estimator=estimator,
        method=method,
        fold=fold,
        n_estimators=n_estimators,
        round=round,
        choose_better=choose_better,
        optimize=optimize,
        fit_kwargs=fit_kwargs,
        verbose=verbose,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def blend_models(
    estimator_list: list,
    method: str = "mean",
    fold: Optional[Union[int, Any]] = None,
    round: int = 4,
    choose_better: bool = False,
    optimize: str = "SMAPE",
    weights: Optional[List[float]] = None,
    fit_kwargs: Optional[dict] = None,
    verbose: bool = True,
):

    """
    This function trains a EnsembleForecaster for select models passed in the
    ``estimator_list`` param. The output of this function is a score grid with
    CV scores by fold. Metrics evaluated during CV can be accessed using the
    ``get_metrics`` function. Custom metrics can be added or removed using
    ``add_metric`` and ``remove_metric`` function.


    Example
    --------
    >>> from pycaret.datasets import get_data
    >>> from pycaret.internal.pycaret_experiment import TimeSeriesExperiment
    >>> import numpy as np
    >>> airline_data = get_data('airline', verbose=False)
    >>> fh = np.arange(1,13)
    >>> fold = 3
    >>> exp = TimeSeriesExperiment()
    >>> exp.setup(data=y, fh=fh, fold=fold)
    >>> arima_model = exp.create_model("arima")
    >>> naive_model = exp.create_model("naive")
    >>> ts_blender = exp.blend_models([arima_model, naive_model], optimize='MAPE_ts')


    estimator_list: list of sktime compatible estimators
        List of model objects


    method: str, default = 'mean'
        Method to average the individual predictions to form a final prediction.
        Available Methods:

        * 'mean' - Mean of individual predictions
        * 'median' - Median of individual predictions
        * 'voting' - Vote individual predictions based on the provided weights.


    fold: int or scikit-learn compatible CV generator, default = None
        Controls cross-validation. If None, the CV generator in the ``fold_strategy``
        parameter of the ``setup`` function is used. When an integer is passed,
        it is interpreted as the 'n_splits' parameter of the CV generator in the
        ``setup`` function.


    round: int, default = 4
        Number of decimal places the metrics in the score grid will be rounded to.


    choose_better: bool, default = False
        When set to True, the returned object is always better performing. The
        metric used for comparison is defined by the ``optimize`` parameter.


    optimize: str, default = 'MAPE_ts'
        Metric to compare for model selection when ``choose_better`` is True.


    weights: list, default = None
        Sequence of weights (float or int) to weight the occurrences of predicted class
        labels (hard voting) or class probabilities before averaging (soft voting). Uses
        uniform weights when None.


    fit_kwargs: dict, default = {} (empty dict)
        Dictionary of arguments passed to the fit method of the model.


    verbose: bool, default = True
        Score grid is not printed when verbose is set to False.


    Returns:
        Trained Model


    """

    return _CURRENT_EXPERIMENT.blend_models(
        estimator_list=estimator_list,
        fold=fold,
        round=round,
        choose_better=choose_better,
        optimize=optimize,
        weights=weights,
        fit_kwargs=fit_kwargs,
        verbose=verbose,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def stack_models(
    estimator_list: list,
    meta_model=None,
    fold: Optional[Union[int, Any]] = None,
    round: int = 4,
    restack: bool = True,
    choose_better: bool = False,
    optimize: str = "R2",
    fit_kwargs: Optional[dict] = None,
    verbose: bool = True,
):

    """
    This function trains a meta model over select estimators passed in
    the ``estimator_list`` parameter. The output of this function is a
    score grid with CV scores by fold. Metrics evaluated during CV can
    be accessed using the ``get_metrics`` function. Custom metrics
    can be added or removed using ``add_metric`` and ``remove_metric``
    function.


    Example
    --------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> top3 = compare_models(n_select = 3)
    >>> stacker = stack_models(top3)


    estimator_list: list of scikit-learn compatible objects
        List of trained model objects


    meta_model: scikit-learn compatible object, default = None
        When None, Linear Regression is trained as a meta model.


    fold: int or scikit-learn compatible CV generator, default = None
        Controls cross-validation. If None, the CV generator in the ``fold_strategy``
        parameter of the ``setup`` function is used. When an integer is passed,
        it is interpreted as the 'n_splits' parameter of the CV generator in the
        ``setup`` function.


    round: int, default = 4
        Number of decimal places the metrics in the score grid will be rounded to.


    restack: bool, default = True
        When set to False, only the predictions of estimators will be used as
        training data for the ``meta_model``.


    choose_better: bool, default = False
        When set to True, the returned object is always better performing. The
        metric used for comparison is defined by the ``optimize`` parameter.


    optimize: str, default = 'R2'
        Metric to compare for model selection when ``choose_better`` is True.


    fit_kwargs: dict, default = {} (empty dict)
        Dictionary of arguments passed to the fit method of the model.


    verbose: bool, default = True
        Score grid is not printed when verbose is set to False.


    Returns:
        Trained Model

    """

    return _CURRENT_EXPERIMENT.stack_models(
        estimator_list=estimator_list,
        meta_model=meta_model,
        fold=fold,
        round=round,
        restack=restack,
        choose_better=choose_better,
        optimize=optimize,
        fit_kwargs=fit_kwargs,
        verbose=verbose,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def plot_model(
    estimator,
    plot: str = "residuals",
    scale: float = 1,
    save: bool = False,
    fold: Optional[Union[int, Any]] = None,
    fit_kwargs: Optional[dict] = None,
    use_train_data: bool = False,
    verbose: bool = True,
    display_format: Optional[str] = None,
) -> str:

    """
    This function analyzes the performance of a trained model on holdout set.
    It may require re-training the model in certain cases.


    Example
    --------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> lr = create_model('lr')
    >>> plot_model(lr, plot = 'residual')


    estimator: scikit-learn compatible object
        Trained model object


    plot: str, default = 'residual'
        List of available plots (ID - Name):

        * 'residuals' - Residuals Plot
        * 'error' - Prediction Error Plot
        * 'cooks' - Cooks Distance Plot
        * 'rfe' - Recursive Feat. Selection
        * 'learning' - Learning Curve
        * 'vc' - Validation Curve
        * 'manifold' - Manifold Learning
        * 'feature' - Feature Importance
        * 'feature_all' - Feature Importance (All)
        * 'parameter' - Model Hyperparameter
        * 'tree' - Decision Tree


    scale: float, default = 1
        The resolution scale of the figure.


    save: bool, default = False
        When set to True, plot is saved in the current working directory.


    fold: int or scikit-learn compatible CV generator, default = None
        Controls cross-validation. If None, the CV generator in the ``fold_strategy``
        parameter of the ``setup`` function is used. When an integer is passed,
        it is interpreted as the 'n_splits' parameter of the CV generator in the
        ``setup`` function.


    fit_kwargs: dict, default = {} (empty dict)
        Dictionary of arguments passed to the fit method of the model.


    use_train_data: bool, default = False
        When set to true, train data will be used for plots, instead
        of test data.


    verbose: bool, default = True
        When set to False, progress bar is not displayed.


    display_format: str, default = None
        To display plots in Streamlit (https://www.streamlit.io/), set this to 'streamlit'.
        Currently, not all plots are supported.


    Returns:
        None

    """

    return _CURRENT_EXPERIMENT.plot_model(
        estimator=estimator,
        plot=plot,
        scale=scale,
        save=save,
        fold=fold,
        fit_kwargs=fit_kwargs,
        verbose=verbose,
        use_train_data=use_train_data,
        display_format=display_format,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def evaluate_model(
    estimator,
    fold: Optional[Union[int, Any]] = None,
    fit_kwargs: Optional[dict] = None,
    use_train_data: bool = False,
):

    """
    This function displays a user interface for analyzing performance of a trained
    model. It calls the ``plot_model`` function internally.

    Example
    --------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> lr = create_model('lr')
    >>> evaluate_model(lr)


    estimator: scikit-learn compatible object
        Trained model object


    fold: int or scikit-learn compatible CV generator, default = None
        Controls cross-validation. If None, the CV generator in the ``fold_strategy``
        parameter of the ``setup`` function is used. When an integer is passed,
        it is interpreted as the 'n_splits' parameter of the CV generator in the
        ``setup`` function.


    fit_kwargs: dict, default = {} (empty dict)
        Dictionary of arguments passed to the fit method of the model.


    use_train_data: bool, default = False
        When set to true, train data will be used for plots, instead
        of test data.


    Returns:
        None


    Warnings
    --------
    -   This function only works in IPython enabled Notebook.

    """

    return _CURRENT_EXPERIMENT.evaluate_model(
        estimator=estimator,
        fold=fold,
        fit_kwargs=fit_kwargs,
        use_train_data=use_train_data,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def interpret_model(
    estimator,
    plot: str = "summary",
    feature: Optional[str] = None,
    observation: Optional[int] = None,
    use_train_data: bool = False,
    save: bool = False,
    **kwargs,
):

    """
    This function analyzes the predictions generated from a trained model. Most plots
    in this function are implemented based on the SHAP (SHapley Additive exPlanations).
    For more info on this, please see https://shap.readthedocs.io/en/latest/


    Example
    --------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp = setup(data = boston,  target = 'medv')
    >>> xgboost = create_model('xgboost')
    >>> interpret_model(xgboost)


    estimator: scikit-learn compatible object
        Trained model object


    plot: str, default = 'summary'
        List of available plots (ID - Name):
        * 'summary' - Summary Plot using SHAP
        * 'correlation' - Dependence Plot using SHAP
        * 'reason' - Force Plot using SHAP
        * 'pdp' - Partial Dependence Plot


    feature: str, default = None
        Feature to check correlation with. This parameter is only required when ``plot``
        type is 'correlation' or 'pdp'. When set to None, it uses the first column from 
        the dataset.


    observation: int, default = None
        Observation index number in holdout set to explain. When ``plot`` is not
        'reason', this parameter is ignored.


    use_train_data: bool, default = False
        When set to true, train data will be used for plots, instead
        of test data.


    save: bool, default = False
        When set to True, Plot is saved as a 'png' file in current working directory.


    **kwargs:
        Additional keyword arguments to pass to the plot.


    Returns:
        None

    """

    return _CURRENT_EXPERIMENT.interpret_model(
        estimator=estimator,
        plot=plot,
        feature=feature,
        observation=observation,
        use_train_data=use_train_data,
        save=save,
        **kwargs,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def predict_model(
    estimator,
    # data: Optional[pd.DataFrame] = None,
    fh=None,
    return_pred_int=False,
    alpha=0.05,
    round: int = 4,
    verbose: bool = True,
) -> pd.DataFrame:

    """
    This function predicts ``Label`` using a trained model. When ``data`` is
    None, it predicts label on the holdout set.


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> lr = create_model('lr')
    >>> pred_holdout = predict_model(lr)
    >>> pred_unseen = predict_model(lr, data = unseen_dataframe)


    estimator: scikit-learn compatible object
        Trained model object


    data : pandas.DataFrame
        Shape (n_samples, n_features). All features used during training
        must be available in the unseen dataset.


    round: int, default = 4
        Number of decimal places to round predictions to.


    verbose: bool, default = True
        When set to False, holdout score grid is not printed.


    Returns:
        pandas.DataFrame


    Warnings
    --------
    - The behavior of the ``predict_model`` is changed in version 2.1 without backward
      compatibility. As such, the pipelines trained using the version (<= 2.0), may not
      work for inference with version >= 2.1. You can either retrain your models with a
      newer version or downgrade the version for inference.


    """

    return _CURRENT_EXPERIMENT.predict_model(
        estimator=estimator,
        # data=data,
        fh=fh,
        return_pred_int=return_pred_int,
        alpha=alpha,
        round=round,
        verbose=verbose,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def finalize_model(
    estimator,
    fit_kwargs: Optional[dict] = None,
    model_only: bool = True,
) -> Any:

    """
    This function trains a given estimator on the entire dataset including the
    holdout set.


    Example
    --------
    >>> from pycaret.datasets import get_data
    >>> data = get_data('airline')
    >>> from pycaret.time_series import *
    >>> exp_name = setup(data = data, fh = 12)
    >>> model = create_model('naive')
    >>> final_model = finalize_model(model)


    estimator: sktime compatible object
        Trained model object


    fit_kwargs: dict, default = {} (empty dict)
        Dictionary of arguments passed to the fit method of the model.


    model_only: bool, default = True
        When set to False, only model object is re-trained and all the
        transformations in Pipeline are ignored.


    Returns:
        Trained Model


    """

    return _CURRENT_EXPERIMENT.finalize_model(
        estimator=estimator,
        fit_kwargs=fit_kwargs,
        model_only=model_only,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def deploy_model(
    model,
    model_name: str,
    authentication: dict,
    platform: str = "aws",
):

    """
    This function deploys the transformation pipeline and trained model on cloud.


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> lr = create_model('lr')
    >>> deploy_model(model = lr, model_name = 'lr-for-deployment', platform = 'aws', authentication = {'bucket' : 'S3-bucket-name'})


    Amazon Web Service (AWS) users:
        To deploy a model on AWS S3 ('aws'), environment variables must be set in your
        local environment. To configure AWS environment variables, type ``aws configure``
        in the command line. Following information from the IAM portal of amazon console
        account is required:

        - AWS Access Key ID
        - AWS Secret Key Access
        - Default Region Name (can be seen under Global settings on your AWS console)

        More info: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html


    Google Cloud Platform (GCP) users:
        To deploy a model on Google Cloud Platform ('gcp'), project must be created
        using command line or GCP console. Once project is created, you must create
        a service account and download the service account key as a JSON file to set
        environment variables in your local environment.

        More info: https://cloud.google.com/docs/authentication/production


    Microsoft Azure (Azure) users:
        To deploy a model on Microsoft Azure ('azure'), environment variables for connection
        string must be set in your local environment. Go to settings of storage account on
        Azure portal to access the connection string required.

        More info: https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python?toc=%2Fpython%2Fazure%2FTOC.json


    model: scikit-learn compatible object
        Trained model object


    model_name: str
        Name of model.


    authentication: dict
        Dictionary of applicable authentication tokens.

        When platform = 'aws':
        {'bucket' : 'S3-bucket-name'}

        When platform = 'gcp':
        {'project': 'gcp-project-name', 'bucket' : 'gcp-bucket-name'}

        When platform = 'azure':
        {'container': 'azure-container-name'}


    platform: str, default = 'aws'
        Name of the platform. Currently supported platforms: 'aws', 'gcp' and 'azure'.


    Returns:
        None

    """

    return _CURRENT_EXPERIMENT.deploy_model(
        model=model,
        model_name=model_name,
        authentication=authentication,
        platform=platform,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def save_model(model, model_name: str, model_only: bool = True, verbose: bool = True):

    """
    This function saves the transformation pipeline and trained model object
    into the current working directory as a pickle file for later use.

    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> lr = create_model('lr')
    >>> save_model(lr, 'saved_lr_model')


    model: scikit-learn compatible object
        Trained model object


    model_name: str
        Name of the model.


    model_only: bool, default = True
        When set to True, only trained model object is saved instead of the
        entire pipeline.


    verbose: bool, default = True
        Success message is not printed when verbose is set to False.


    Returns:
        Tuple of the model object and the filename.

    """

    return _CURRENT_EXPERIMENT.save_model(
        model=model, model_name=model_name, model_only=model_only, verbose=verbose
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def load_model(
    model_name,
    platform: Optional[str] = None,
    authentication: Optional[Dict[str, str]] = None,
    verbose: bool = True,
):

    """
    This function loads a previously saved pipeline.

    Example
    -------
    >>> from pycaret.regression import load_model
    >>> saved_lr = load_model('saved_lr_model')


    model_name: str
        Name of the model.


    platform: str, default = None
        Name of the cloud platform. Currently supported platforms:
        'aws', 'gcp' and 'azure'.


    authentication: dict, default = None
        dictionary of applicable authentication tokens.

        when platform = 'aws':
        {'bucket' : 'S3-bucket-name'}

        when platform = 'gcp':
        {'project': 'gcp-project-name', 'bucket' : 'gcp-bucket-name'}

        when platform = 'azure':
        {'container': 'azure-container-name'}


    verbose: bool, default = True
        Success message is not printed when verbose is set to False.


    Returns:
        Trained Model

    """

    return _CURRENT_EXPERIMENT.load_model(
        model_name=model_name,
        platform=platform,
        authentication=authentication,
        verbose=verbose,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def automl(optimize: str = "R2", use_holdout: bool = False, turbo: bool = True) -> Any:

    """
    This function returns the best model out of all trained models in
    current session based on the ``optimize`` parameter. Metrics
    evaluated can be accessed using the ``get_metrics`` function.


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> top3 = compare_models(n_select = 3)
    >>> tuned_top3 = [tune_model(i) for i in top3]
    >>> blender = blend_models(tuned_top3)
    >>> stacker = stack_models(tuned_top3)
    >>> best_mae_model = automl(optimize = 'MAE')


    optimize: str, default = 'R2'
        Metric to use for model selection. It also accepts custom metrics
        added using the ``add_metric`` function.


    use_holdout: bool, default = False
        When set to True, metrics are evaluated on holdout set instead of CV.


    turbo: bool, default = True
        When set to True and use_holdout is False, only models created with default fold
        parameter will be considered. If set to False, models created with a non-default
        fold parameter will be scored again using default fold settings, so that they can be
        compared.


    Returns:
        Trained Model


    """

    return _CURRENT_EXPERIMENT.automl(
        optimize=optimize, use_holdout=use_holdout, turbo=turbo
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def pull(pop: bool = False) -> pd.DataFrame:
    """
    Returns last printed score grid. Use ``pull`` function after
    any training function to store the score grid in pandas.DataFrame.


    pop: bool, default = False
        If True, will pop (remove) the returned dataframe from the
        display container.


    Returns:
        pandas.DataFrame

    """
    return _CURRENT_EXPERIMENT.pull(pop=pop)


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def models(
    type: Optional[str] = None,
    internal: bool = False,
    raise_errors: bool = True,
) -> pd.DataFrame:

    """
    Returns table of models available in the model library.

    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> all_models = models()


    type: str, default = None
        - linear : filters and only return linear models
        - tree : filters and only return tree based models
        - ensemble : filters and only return ensemble models


    internal: bool, default = False
        When True, will return extra columns and rows used internally.


    raise_errors: bool, default = True
        When False, will suppress all exceptions, ignoring models
        that couldn't be created.


    Returns:
        pandas.DataFrame

    """
    return _CURRENT_EXPERIMENT.models(
        type=type, internal=internal, raise_errors=raise_errors
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def get_metrics(
    reset: bool = False,
    include_custom: bool = True,
    raise_errors: bool = True,
) -> pd.DataFrame:

    """
    Returns table of available metrics used for CV.


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> all_metrics = get_metrics()


    reset: bool, default = False
        When True, will reset all changes made using the ``add_metric``
        and ``remove_metric`` function.


    include_custom: bool, default = True
        Whether to include user added (custom) metrics or not.


    raise_errors: bool, default = True
        If False, will suppress all exceptions, ignoring models that
        couldn't be created.


    Returns:
        pandas.DataFrame

    """

    return _CURRENT_EXPERIMENT.get_metrics(
        reset=reset,
        include_custom=include_custom,
        raise_errors=raise_errors,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def add_metric(
    id: str,
    name: str,
    score_func: type,
    greater_is_better: bool = True,
    **kwargs,
) -> pd.Series:

    """
    Adds a custom metric to be used for CV.


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> from sklearn.metrics import explained_variance_score
    >>> add_metric('evs', 'EVS', explained_variance_score)


    id: str
        Unique id for the metric.


    name: str
        Display name of the metric.


    score_func: type
        Score function (or loss function) with signature ``score_func(y, y_pred, **kwargs)``.


    greater_is_better: bool, default = True
        Whether ``score_func`` is higher the better or not.


    **kwargs:
        Arguments to be passed to score function.


    Returns:
        pandas.Series

    """

    return _CURRENT_EXPERIMENT.add_metric(
        id=id,
        name=name,
        score_func=score_func,
        target="pred",
        greater_is_better=greater_is_better,
        **kwargs,
    )


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def remove_metric(name_or_id: str):

    """
    Removes a metric from CV.


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'mredv')
    >>> remove_metric('MAPE')


    name_or_id: str
        Display name or ID of the metric.


    Returns:
        None

    """
    return _CURRENT_EXPERIMENT.remove_metric(name_or_id=name_or_id)


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def get_logs(experiment_name: Optional[str] = None, save: bool = False) -> pd.DataFrame:

    """
    Returns a table of experiment logs. Only works when ``log_experiment``
    is True when initializing the ``setup`` function.


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv', log_experiment = True)
    >>> best = compare_models()
    >>> exp_logs = get_logs()


    experiment_name: str, default = None
        When None current active run is used.


    save: bool, default = False
        When set to True, csv file is saved in current working directory.


    Returns:
        pandas.DataFrame

    """

    return _CURRENT_EXPERIMENT.get_logs(experiment_name=experiment_name, save=save)


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def get_config(variable: str):

    """
    This function retrieves the global variables created when initializing the
    ``setup`` function. Following variables are accessible:

    - X: Transformed dataset (X)
    - y: Transformed dataset (y)
    - X_train: Transformed train dataset (X)
    - X_test: Transformed test/holdout dataset (X)
    - y_train: Transformed train dataset (y)
    - y_test: Transformed test/holdout dataset (y)
    - seed: random state set through session_id
    - prep_pipe: Transformation pipeline
    - fold_shuffle_param: shuffle parameter used in Kfolds
    - n_jobs_param: n_jobs parameter used in model training
    - html_param: html_param configured through setup
    - create_model_container: results grid storage container
    - master_model_container: model storage container
    - display_container: results display container
    - exp_name_log: Name of experiment
    - logging_param: log_experiment param
    - log_plots_param: log_plots param
    - USI: Unique session ID parameter
    - fix_imbalance_param: fix_imbalance param
    - fix_imbalance_method_param: fix_imbalance_method param
    - data_before_preprocess: data before preprocessing
    - target_param: name of target variable
    - gpu_param: use_gpu param configured through setup
    - fold_generator: CV splitter configured in fold_strategy
    - fold_param: fold params defined in the setup
    - fold_groups_param: fold groups defined in the setup
    - stratify_param: stratify parameter defined in the setup
    - transform_target_param: transform_target_param in setup
    - transform_target_method_param: transform_target_method_param in setup


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> X_train = get_config('X_train')


    Returns:
        Global variable


    """

    return _CURRENT_EXPERIMENT.get_config(variable=variable)


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def set_config(variable: str, value):

    """
    This function resets the global variables. Following variables are
    accessible:

    - X: Transformed dataset (X)
    - y: Transformed dataset (y)
    - X_train: Transformed train dataset (X)
    - X_test: Transformed test/holdout dataset (X)
    - y_train: Transformed train dataset (y)
    - y_test: Transformed test/holdout dataset (y)
    - seed: random state set through session_id
    - prep_pipe: Transformation pipeline
    - fold_shuffle_param: shuffle parameter used in Kfolds
    - n_jobs_param: n_jobs parameter used in model training
    - html_param: html_param configured through setup
    - create_model_container: results grid storage container
    - master_model_container: model storage container
    - display_container: results display container
    - exp_name_log: Name of experiment
    - logging_param: log_experiment param
    - log_plots_param: log_plots param
    - USI: Unique session ID parameter
    - fix_imbalance_param: fix_imbalance param
    - fix_imbalance_method_param: fix_imbalance_method param
    - data_before_preprocess: data before preprocessing
    - target_param: name of target variable
    - gpu_param: use_gpu param configured through setup
    - fold_generator: CV splitter configured in fold_strategy
    - fold_param: fold params defined in the setup
    - fold_groups_param: fold groups defined in the setup
    - stratify_param: stratify parameter defined in the setup
    - transform_target_param: transform_target_param in setup
    - transform_target_method_param: transform_target_method_param in setup


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> set_config('seed', 123)


    Returns:
        None

    """

    return _CURRENT_EXPERIMENT.set_config(variable=variable, value=value)


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def save_config(file_name: str):

    """
    This function save all global variables to a pickle file, allowing to
    later resume without rerunning the ``setup``.


    Example
    -------
    >>> from pycaret.datasets import get_data
    >>> boston = get_data('boston')
    >>> from pycaret.regression import *
    >>> exp_name = setup(data = boston,  target = 'medv')
    >>> save_config('myvars.pkl')


    Returns:
        None

    """

    return _CURRENT_EXPERIMENT.save_config(file_name=file_name)


@check_if_global_is_not_none(globals(), _CURRENT_EXPERIMENT_DECORATOR_DICT)
def load_config(file_name: str):

    """
    This function loads global variables from a pickle file into Python
    environment.


    Example
    -------
    >>> from pycaret.regression import load_config
    >>> load_config('myvars.pkl')


    Returns:
        Global variables

    """

    return _CURRENT_EXPERIMENT.load_config(file_name=file_name)


def set_current_experiment(experiment: TimeSeriesExperiment):
    global _CURRENT_EXPERIMENT

    if not isinstance(experiment, TimeSeriesExperiment):
        raise TypeError(
            f"experiment must be a PyCaret TimeSeriesExperiment object, got {type(experiment)}."
        )
    _CURRENT_EXPERIMENT = experiment