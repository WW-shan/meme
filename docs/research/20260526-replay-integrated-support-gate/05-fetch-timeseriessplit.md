[![scikit-learn homepage](../../_static/scikit-learn-logo-without-subtitle.svg) ![scikit-learn homepage](../../_static/scikit-learn-logo-without-subtitle.svg)](../../index.html)

* [GitHub](https://github.com/scikit-learn/scikit-learn "GitHub")

# TimeSeriesSplit[#](#timeseriessplit "Link to this heading")

*class* sklearn.model\_selection.TimeSeriesSplit(*n\_splits=5*, *\**, *max\_train\_size=None*, *test\_size=None*, *gap=0*)[[source]](https://github.com/scikit-learn/scikit-learn/blob/fe2edb3cd/sklearn/model_selection/_split.py#L1109)[#](#sklearn.model_selection.TimeSeriesSplit "Link to this definition")
:   Time Series cross-validator.

    Provides train/test indices to split time-ordered data, where other cross-validation methods are inappropriate, as they would lead to training on future data and evaluating on past data. To ensure comparable metrics across folds, samples must be equally spaced. Once this condition is met, each test set covers the same time duration, while the train set size accumulates data from previous splits.

    This cross-validation object is a variation of [`KFold`](sklearn.model_selection.KFold.html#sklearn.model_selection.KFold "sklearn.model_selection.KFold"). In the k-th split, it returns the first k folds as the train set and the (k+1)-th fold as the test set.

    Note that, unlike standard cross-validation methods, successive training sets are supersets of those that come before them.

    Read more in the [User Guide](../cross_validation.html#time-series-split).

    For visualisation of cross-validation behaviour and comparison between common scikit-learn split methods refer to [Visualizing cross-validation behavior in scikit-learn](../../auto_examples/model_selection/plot_cv_indices.html#sphx-glr-auto-examples-model-selection-plot-cv-indices-py)

    Added in version 0.18.

    Parameters:
    :   **n\_splits**int, default=5
        :   Number of splits. Must be at least 2.

            Changed in version 0.22: `n_splits` default value changed from 3 to 5.

        **max\_train\_size**int, default=None
        :   Maximum size for a single training set.

        **test\_size**int, default=None
        :   Used to limit the size of the test set. Defaults to `n_samples//(n_splits +1)`, which is the maximum allowed value with `gap=0`.

            Added in version 0.24.

        **gap**int, default=0
        :   Number of samples to exclude from the end of each train set before the test set.

            Added in version 0.24.

    Notes

    The training set has size `i* n_samples//(n_splits +1) + n_samples %(n_splits +1)` in the `i` th split, with a test set of size `n_samples//(n_splits +1)` by default, where `n_samples` is the number of samples. Note that this formula is only valid when `test_size` and `max_train_size` are left to their default values.

    Examples

    ```
    >>> import  numpy  as  np>>> from  sklearn.model_selection  import TimeSeriesSplit>>> X = np. array([[1, 2],[3, 4],[1, 2],[3, 4],[1, 2],[3, 4]])>>> y = np. array([1, 2, 3, 4, 5, 6])>>> tscv = TimeSeriesSplit()>>> print(tscv)TimeSeriesSplit(gap=0, max_train_size=None, n_splits=5, test_size=None)>>> for i,(train_index, test_index) in enumerate(tscv. split(X)):... print(f "Fold {i}:")... print(f" Train: index={train_index} ")... print(f" Test: index={test_index} ")Fold 0: Train: index=[0] Test: index=[1]Fold 1: Train: index=[0 1] Test: index=[2]Fold 2: Train: index=[0 1 2] Test: index=[3]Fold 3: Train: index=[0 1 2 3] Test: index=[4]Fold 4: Train: index=[0 1 2 3 4] Test: index=[5]>>> # Fix test_size to 2 with 12 samples>>> X = np. random. randn(12, 2)>>> y = np. random. randint(0, 2, 12)>>> tscv = TimeSeriesSplit(n_splits = 3, test_size = 2)>>> for i,(train_index, test_index) in enumerate(tscv. split(X)):... print(f "Fold {i}:")... print(f" Train: index={train_index} ")... print(f" Test: index={test_index} ")Fold 0: Train: index=[0 1 2 3 4 5] Test: index=[6 7]Fold 1: Train: index=[0 1 2 3 4 5 6 7] Test: index=[8 9]Fold 2: Train: index=[0 1 2 3 4 5 6 7 8 9] Test: index=[10 11]>>> # Add in a 2 period gap>>> tscv = TimeSeriesSplit(n_splits = 3, test_size = 2, gap = 2)>>> for i,(train_index, test_index) in enumerate(tscv. split(X)):... print(f "Fold {i}:")... print(f" Train: index={train_index} ")... print(f" Test: index={test_index} ")Fold 0: Train: index=[0 1 2 3] Test: index=[6 7]Fold 1: Train: index=[0 1 2 3 4 5] Test: index=[8 9]Fold 2: Train: index=[0 1 2 3 4 5 6 7] Test: index=[10 11]
    ```

    For a more extended example see [Time-related feature engineering](../../auto_examples/applications/plot_cyclical_feature_engineering.html#sphx-glr-auto-examples-applications-plot-cyclical-feature-engineering-py).

    get\_metadata\_routing()[[source]](https://github.com/scikit-learn/scikit-learn/blob/fe2edb3cd/sklearn/utils/_metadata_requests.py#L1550)[#](#sklearn.model_selection.TimeSeriesSplit.get_metadata_routing "Link to this definition")
    :   Get metadata routing of this object.

        Please check [User Guide](../../metadata_routing.html#metadata-routing) on how the routing mechanism works.

        Returns:
        :   **routing**MetadataRequest
            :   A [`MetadataRequest`](sklearn.utils.metadata_routing.MetadataRequest.html#sklearn.utils.metadata_routing.MetadataRequest "sklearn.utils.metadata_routing.MetadataRequest") encapsulating routing information.

    get\_n\_splits(*X=None*, *y=None*, *groups=None*)[[source]](https://github.com/scikit-learn/scikit-learn/blob/fe2edb3cd/sklearn/model_selection/_split.py#L415)[#](#sklearn.model_selection.TimeSeriesSplit.get_n_splits "Link to this definition")
    :   Returns the number of splitting iterations as set with the `n_splits` param when instantiating the cross-validator.

        Parameters:
        :   **X**array-like of shape (n\_samples, n\_features), default=None
            :   Always ignored, exists for API compatibility.

            **y**array-like of shape (n\_samples,), default=None
            :   Always ignored, exists for API compatibility.

            **groups**array-like of shape (n\_samples,), default=None
            :   Always ignored, exists for API compatibility.

        Returns:
        :   **n\_splits**int
            :   Returns the number of splitting iterations in the cross-validator.

    split(*X*, *y=None*, *groups=None*)[[source]](https://github.com/scikit-learn/scikit-learn/blob/fe2edb3cd/sklearn/model_selection/_split.py#L1238)[#](#sklearn.model_selection.TimeSeriesSplit.split "Link to this definition")
    :   Generate indices to split data into training and test set.

        Parameters:
        :   **X**array-like of shape (n\_samples, n\_features)
            :   Training data, where `n_samples` is the number of samples and `n_features` is the number of features.

            **y**array-like of shape (n\_samples,), default=None
            :   Always ignored, exists for API compatibility.

            **groups**array-like of shape (n\_samples,), default=None
            :   Always ignored, exists for API compatibility.

        Yields:
        :   **train**ndarray
            :   The training set indices for that split.

            **test**ndarray
            :   The testing set indices for that split.

## Gallery examples[#](#gallery-examples "Link to this heading")

![](../../_images/sphx_glr_plot_cyclical_feature_engineering_thumb.png)

[Time-related feature engineering](../../auto_examples/applications/plot_cyclical_feature_engineering.html)

Time-related feature engineering

![](../../_images/sphx_glr_plot_time_series_lagged_features_thumb.png)

[Lagged features for time series forecasting](../../auto_examples/applications/plot_time_series_lagged_features.html)

Lagged features for time series forecasting

![](../../_images/sphx_glr_plot_hgbt_regression_thumb.png)

[Features in Histogram Gradient Boosting Trees](../../auto_examples/ensemble/plot_hgbt_regression.html)

Features in Histogram Gradient Boosting Trees

![](../../_images/sphx_glr_plot_lasso_and_elasticnet_thumb.png)

[L1-based models for Sparse Signals](../../auto_examples/linear_model/plot_lasso_and_elasticnet.html)

L1-based models for Sparse Signals

![](../../_images/sphx_glr_plot_cv_indices_thumb.png)

[Visualizing cross-validation behavior in scikit-learn](../../auto_examples/model_selection/plot_cv_indices.html)

Visualizing cross-validation behavior in scikit-learn

On this page

### This Page

* [Show Source](../../_sources/modules/generated/sklearn.model_selection.TimeSeriesSplit.rst.txt)
