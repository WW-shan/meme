* [GitHub](https://github.com/skfolio/skfolio "GitHub")

# skfolio.model\_selection.CombinatorialPurgedCV[#](#skfolio-model-selection-combinatorialpurgedcv "Link to this heading")

class skfolio.model\_selection.CombinatorialPurgedCV(*n\_folds=10*, *n\_test\_folds=8*, *purged\_size=0*, *embargo\_size=0*)[[source]](../_modules/skfolio/model_selection/_combinatorial.html#CombinatorialPurgedCV)[#](#skfolio.model_selection.CombinatorialPurgedCV "Link to this definition")
:   Combinatorial Purged Cross-Validation.

    Provides train/test indices to split time series data samples based on Combinatorial Purged Cross-Validation [[1]](#re93330c75414-1).

    Compared to `KFold`, which splits the data into `k` folds with `1` fold for the test set and `k - 1` folds for the training set, `CombinatorialPurgedCV` uses `k - p` folds for the training set with `p> 1` being the number of test folds.

    `KFold` can recombine one single testing path while `CombinatorialPurgedCV` can recombine multiple testing paths from the combinations of the train/test sets.

    To avoid data leakage, purging and embargoing can be performed.

    Purging consist of removing from the training set all observations whose labels overlapped in time with those labels included in the testing set.

    Embargoing consist of removing from the training set all observations that immediately follow an observation in the testing set, since financial features often incorporate series that exhibit serial correlation (like ARMA processes).

    Parameters:
    :   **n\_folds**int, default=10
        :   Number of folds. Must be at least 3.

        **n\_test\_folds**int, default=8
        :   Number of test folds. Must be at least 2. For only one test fold, use `sklearn.model_validation.KFold`.

        **purged\_size**int, default=0
        :   Number of observations to exclude from the start of each train set that are after a test set **and** the number of observations to exclude from the end of each training set that are before a test set.

        **embargo\_size**int, default=0
        :   Number of observations to exclude from the start of each training set that are after a test set.

    Attributes:
    :   **index\_train\_test\_**ndarray of shape (n\_observations, n\_splits)

    Methods

    |  |  |
    | --- | --- |
    | [`get_n_splits`](#skfolio.model_selection.CombinatorialPurgedCV.get_n_splits "skfolio.model_selection.CombinatorialPurgedCV.get_n_splits")([X, y, groups]) | Return the number of splitting iterations in the cross-validator. |
    | [`get_path_ids`](#skfolio.model_selection.CombinatorialPurgedCV.get_path_ids "skfolio.model_selection.CombinatorialPurgedCV.get_path_ids")() | Return the path id of each test sets in each split. |
    | [`plot_train_test_folds`](#skfolio.model_selection.CombinatorialPurgedCV.plot_train_test_folds "skfolio.model_selection.CombinatorialPurgedCV.plot_train_test_folds")() | Plot the train/test fold locations. |
    | [`plot_train_test_index`](#skfolio.model_selection.CombinatorialPurgedCV.plot_train_test_index "skfolio.model_selection.CombinatorialPurgedCV.plot_train_test_index")(X) | Plot the training and test indices for each combinations by assigning `0` to training, `1` to test and `-1` to both purge and embargo indices. |
    | [`split`](#skfolio.model_selection.CombinatorialPurgedCV.split "skfolio.model_selection.CombinatorialPurgedCV.split")(X[, y, groups]) | Generate indices to split data into training and test set. |

    |  |
    | --- |
    | **summary** |

    References

    [[1](#id1)]

    “Advances in Financial Machine Learning”, Marcos López de Prado (2018)

    Examples

    Tutorials using `CombinatorialPurgedCV`:
    :   * [Drop Highly Correlated Assets](../auto_examples/pre_selection/plot_1_drop_correlated.html#sphx-glr-auto-examples-pre-selection-plot-1-drop-correlated-py)
        * [HRP vs HERC](../auto_examples/clustering/plot_3_hrp_vs_herc.html#sphx-glr-auto-examples-clustering-plot-3-hrp-vs-herc-py)
        * [NCO - Combinatorial Purged CV](../auto_examples/clustering/plot_5_nco_grid_search.html#sphx-glr-auto-examples-clustering-plot-5-nco-grid-search-py)

    ```
    >>> import  numpy  as  np>>> from  skfolio.model_selection  import CombinatorialPurgedCV>>> X = np. random. randn(12, 2)>>> cv = CombinatorialPurgedCV(n_folds = 3, n_test_folds = 2)>>> for i,(train_index, tests) in enumerate(cv. split(X)):... print(f "Split {i}:")... print(f" Train: index={train_index} ")... for j, test_index in enumerate(tests):... print(f " Test {j}: index={test_index} ")Split 0: Train: index=[ 8 9 10 11] Test 0: index=[0 1 2 3] Test 1: index=[4 5 6 7]Split 1: Train: index=[4 5 6 7] Test 0: index=[0 1 2 3] Test 1: index=[ 8 9 10 11]Split 2: Train: index=[0 1 2 3] Test 0: index=[4 5 6 7] Test 1: index=[ 8 9 10 11]>>> cv = CombinatorialPurgedCV(n_folds = 3, n_test_folds = 2, purged_size = 1)>>> for i,(train_index, tests) in enumerate(cv. split(X)):... print(f "Split {i}:")... print(f" Train: index={train_index} ")... for j, test_index in enumerate(tests):... print(f " Test {j}: index={test_index} ")Split 0: Train: index=[ 9 10 11] Test 0: index=[0 1 2 3] Test 1: index=[4 5 6 7]Split 1: Train: index=[5 6] Test 0: index=[0 1 2 3] Test 1: index=[ 8 9 10 11]Split 2: Train: index=[0 1 2] Test 0: index=[4 5 6 7] Test 1: index=[ 8 9 10 11]>>> cv = CombinatorialPurgedCV(n_folds = 3, n_test_folds = 2, embargo_size = 1)>>> for i,(train_index, tests) in enumerate(cv. split(X)):... print(f "Split {i}:")... print(f" Train: index={train_index} ")... for j, test_index in enumerate(tests):... print(f " Test {j}: index={test_index} ")Split 0: Train: index=[ 9 10 11] Test 0: index=[0 1 2 3] Test 1: index=[4 5 6 7]Split 1: Train: index=[5 6 7] Test 0: index=[0 1 2 3] Test 1: index=[ 8 9 10 11]Split 2: Train: index=[0 1 2 3] Test 0: index=[4 5 6 7] Test 1: index=[ 8 9 10 11]
    ```

    property binary\_train\_test\_sets[#](#skfolio.model_selection.CombinatorialPurgedCV.binary_train_test_sets "Link to this definition")
    :   Identify training and test folds for each combinations by assigning `0` to training folds and `1` to test folds.

    get\_n\_splits(*X=None*, *y=None*, *groups=None*)[[source]](../_modules/skfolio/model_selection/_combinatorial.html#CombinatorialPurgedCV.get_n_splits)[#](#skfolio.model_selection.CombinatorialPurgedCV.get_n_splits "Link to this definition")
    :   Return the number of splitting iterations in the cross-validator.

        Parameters:
        :   **X**object
            :   Always ignored, exists for compatibility.

            **y**object
            :   Always ignored, exists for compatibility.

            **groups**object
            :   Always ignored, exists for compatibility.

        Returns:
        :   **n\_splits**int
            :   Number of splitting iterations in the cross-validator.

    get\_path\_ids()[[source]](../_modules/skfolio/model_selection/_combinatorial.html#CombinatorialPurgedCV.get_path_ids)[#](#skfolio.model_selection.CombinatorialPurgedCV.get_path_ids "Link to this definition")
    :   Return the path id of each test sets in each split.

    property n\_splits[#](#skfolio.model_selection.CombinatorialPurgedCV.n_splits "Link to this definition")
    :   Number of splits.

    property n\_test\_paths[#](#skfolio.model_selection.CombinatorialPurgedCV.n_test_paths "Link to this definition")
    :   Number of test paths that can be reconstructed from the train/test combinations.

    plot\_train\_test\_folds()[[source]](../_modules/skfolio/model_selection/_combinatorial.html#CombinatorialPurgedCV.plot_train_test_folds)[#](#skfolio.model_selection.CombinatorialPurgedCV.plot_train_test_folds "Link to this definition")
    :   Plot the train/test fold locations.

    plot\_train\_test\_index(*X*)[[source]](../_modules/skfolio/model_selection/_combinatorial.html#CombinatorialPurgedCV.plot_train_test_index)[#](#skfolio.model_selection.CombinatorialPurgedCV.plot_train_test_index "Link to this definition")
    :   Plot the training and test indices for each combinations by assigning `0` to training, `1` to test and `-1` to both purge and embargo indices.

    property recombined\_paths[#](#skfolio.model_selection.CombinatorialPurgedCV.recombined_paths "Link to this definition")
    :   Recombine each test path by returning the test set location in each split.

    split(*X*, *y=None*, *groups=None*)[[source]](../_modules/skfolio/model_selection/_combinatorial.html#CombinatorialPurgedCV.split)[#](#skfolio.model_selection.CombinatorialPurgedCV.split "Link to this definition")
    :   Generate indices to split data into training and test set.

        Parameters:
        :   **X**array-like of shape (n\_samples, n\_features)
            :   Training data, where `n_samples` is the number of samples and `n_features` is the number of features.

            **y**array-like of shape (n\_samples,), optional
            :   The (multi-)target variable

            **groups**array-like of shape (n\_samples,), optional
            :   Group labels for the samples used while splitting the dataset into train/test set.

        Yields:
        :   **train**ndarray
            :   The training set indices for that split.

            **test**ndarray
            :   The testing set indices for that split.

    property test\_set\_index[#](#skfolio.model_selection.CombinatorialPurgedCV.test_set_index "Link to this definition")
    :   Location of each test set.
