[![scikit-learn homepage](../../_static/scikit-learn-logo-without-subtitle.svg) ![scikit-learn homepage](../../_static/scikit-learn-logo-without-subtitle.svg)](../../index.html)

* [GitHub](https://github.com/scikit-learn/scikit-learn "GitHub")

[Go to the end](#sphx-glr-download-auto-examples-model-selection-plot-cost-sensitive-learning-py) to download the full example code or to run this example in your browser via JupyterLite or Binder.

# Post-tuning the decision threshold for cost-sensitive learning[#](#post-tuning-the-decision-threshold-for-cost-sensitive-learning "Link to this heading")

Once a classifier is trained, the output of the [predict](../../glossary.html#term-predict) method outputs class label predictions corresponding to a thresholding of either the [decision\_function](../../glossary.html#term-decision_function) or the [predict\_proba](../../glossary.html#term-predict_proba) output. For a binary classifier, the default threshold is defined as a posterior probability estimate of 0.5 or a decision score of 0.0.

However, this default strategy is most likely not optimal for the task at hand. Here, we use the “Statlog” German credit dataset [[1]](#id2) to illustrate a use case. In this dataset, the task is to predict whether a person has a “good” or “bad” credit. In addition, a cost-matrix is provided that specifies the cost of misclassification. Specifically, misclassifying a “bad” credit as “good” is five times more costly on average than misclassifying a “good” credit as “bad”.

We use the [`TunedThresholdClassifierCV`](../../modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#sklearn.model_selection.TunedThresholdClassifierCV "sklearn.model_selection.TunedThresholdClassifierCV") to select the cut-off point of the decision function that minimizes the provided business cost.

In the second part of the example, we further extend this approach by considering the problem of fraud detection in credit card transactions: in this case, the business metric depends on the amount of each individual transaction.

```
# Authors: The scikit-learn developers# SPDX-License-Identifier: BSD-3-Clause
```

## Cost-sensitive learning with constant gains and costs[#](#cost-sensitive-learning-with-constant-gains-and-costs "Link to this heading")

In this first section, we illustrate the use of the [`TunedThresholdClassifierCV`](../../modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#sklearn.model_selection.TunedThresholdClassifierCV "sklearn.model_selection.TunedThresholdClassifierCV") in a setting of cost-sensitive learning when the gains and costs associated to each entry of the confusion matrix are constant. We use the problematic presented in [[2]](#id3) using the “Statlog” German credit dataset [[1]](#id2).

### “Statlog” German credit dataset[#](#statlog-german-credit-dataset "Link to this heading")

We fetch the German credit dataset from OpenML.

```
 import  sklearn from  sklearn.datasets  import fetch_openml sklearn. set_config(transform_output = "pandas") german_credit = fetch_openml(data_id = 31, as_frame = True, parser = "pandas") X, y = german_credit. data, german_credit. target
```

We check the feature types available in `X`.

```
 X. info()
```

Many features are categorical and usually string-encoded. We need to encode these categories when we develop our predictive model. Let’s check the targets.

```
 y. value_counts()
```

Another observation is that the dataset is imbalanced. We would need to be careful when evaluating our predictive model and use a family of metrics that are adapted to this setting.

In addition, we observe that the target is string-encoded. Some metrics (e.g. precision and recall) require to provide the label of interest also called the “positive label”. Here, we define that our goal is to predict whether or not a sample is a “bad” credit.

```
 pos_label, neg_label = "bad", "good"
```

To carry our analysis, we split our dataset using a single stratified split.

```
 from  sklearn.model_selection  import train_test_split X_train, X_test, y_train, y_test = train_test_split(X, y, stratify = y, random_state = 0)
```

We are ready to design our predictive model and the associated evaluation strategy.

### Evaluation metrics[#](#evaluation-metrics "Link to this heading")

In this section, we define a set of metrics that we use later. To see the effect of tuning the cut-off point, we evaluate the predictive model using the Receiver Operating Characteristic (ROC) curve and the Precision-Recall curve. The values reported on these plots are therefore the true positive rate (TPR), also known as the recall or the sensitivity, and the false positive rate (FPR), also known as the specificity, for the ROC curve and the precision and recall for the Precision-Recall curve.

From these four metrics, scikit-learn does not provide a scorer for the FPR. We therefore need to define a small custom function to compute it.

```
 from  sklearn.metrics  import confusion_matrix def  fpr_score(y, y_pred, neg_label, pos_label): cm = confusion_matrix(y, y_pred, labels =[neg_label, pos_label]) tn, fp, _, _ = cm. ravel() tnr = tn/(tn + fp) return 1 - tnr
```

As previously stated, the “positive label” is not defined as the value “1” and calling some of the metrics with this non-standard value raise an error. We need to provide the indication of the “positive label” to the metrics.

We therefore need to define a scikit-learn scorer using [`make_scorer`](../../modules/generated/sklearn.metrics.make_scorer.html#sklearn.metrics.make_scorer "sklearn.metrics.make_scorer") where the information is passed. We store all the custom scorers in a dictionary. To use them, we need to pass the fitted model, the data and the target on which we want to evaluate the predictive model.

```
 from  sklearn.metrics  import make_scorer, precision_score, recall_score tpr_score = recall_score # TPR and recall are the same metric scoring ={"precision": make_scorer(precision_score, pos_label = pos_label), "recall": make_scorer(recall_score, pos_label = pos_label), "fpr": make_scorer(fpr_score, neg_label = neg_label, pos_label = pos_label), "tpr": make_scorer(tpr_score, pos_label = pos_label),}
```

In addition, the original research [[1]](#id2) defines a custom business metric. We call a “business metric” any metric function that aims at quantifying how the predictions (correct or wrong) might impact the business value of deploying a given machine learning model in a specific application context. For our credit prediction task, the authors provide a custom cost-matrix which encodes that classifying a “bad” credit as “good” is 5 times more costly on average than the opposite: it is less costly for the financing institution to not grant a credit to a potential customer that will not default (and therefore miss a good customer that would have otherwise both reimbursed the credit and paid interests) than to grant a credit to a customer that will default.

We define a python function that weighs the confusion matrix and returns the overall cost. The rows of the confusion matrix hold the counts of observed classes while the columns hold counts of predicted classes. Recall that here we consider “bad” as the positive class (second row and column). Scikit-learn model selection tools expect that we follow a convention that “higher” means “better”, hence the following gain matrix assigns negative gains (costs) to the two kinds of prediction errors:

* a gain of `-1` for each false positive (“good” credit labeled as “bad”),
* a gain of `-5` for each false negative (“bad” credit labeled as “good”),
* a `0` gain for true positives and true negatives.

Note that theoretically, given that our model is calibrated and our data set representative and large enough, we do not need to tune the threshold, but can safely set it to 1/5 of the cost ratio, as stated by Eq. (2) in Elkan’s paper [[2]](#id3).

```
 import  numpy  as  np def  credit_gain_score(y, y_pred, neg_label, pos_label): cm = confusion_matrix(y, y_pred, labels =[neg_label, pos_label]) gain_matrix = np. array([[0, - 1],# -1 gain for false positives[- 5, 0],# -5 gain for false negatives]) return np. sum(cm* gain_matrix) scoring["credit_gain"] = make_scorer(credit_gain_score, neg_label = neg_label, pos_label = pos_label)
```

### Vanilla predictive model[#](#vanilla-predictive-model "Link to this heading")

We use [`HistGradientBoostingClassifier`](../../modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#sklearn.ensemble.HistGradientBoostingClassifier "sklearn.ensemble.HistGradientBoostingClassifier") as a predictive model that natively handles categorical features and missing values.

```
 from  sklearn.ensemble  import HistGradientBoostingClassifier model = HistGradientBoostingClassifier(categorical_features = "from_dtype", random_state = 0). fit(X_train, y_train) model
```

```
HistGradientBoostingClassifier(random_state=0)
```

**In a Jupyter environment, please rerun this cell to show the HTML representation or trust the notebook.   
On GitHub, the HTML representation is unable to render, please try loading this page with nbviewer.org.**

Parameters

|  |  |
| --- | --- |
| [loss loss: {'log\_loss'}, default='log\_loss'  The loss function to use in the boosting process.  For binary classification problems, 'log\_loss' is also known as logistic loss, binomial deviance or binary crossentropy. Internally, the model fits one tree per boosting iteration and uses the logistic sigmoid function (expit) as inverse link function to compute the predicted positive class probability.  For multiclass classification problems, 'log\_loss' is also known as multinomial deviance or categorical crossentropy. Internally, the model fits one tree per boosting iteration and per class and uses the softmax function as inverse link function to compute the predicted probabilities of the classes.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=loss,-%7B%27log_loss%27%7D%2C%20default%3D%27log_loss%27) | 'log\_loss' |
| [learning\_rate learning\_rate: float, default=0.1  The learning rate, also known as \*shrinkage\*. This is used as a multiplicative factor for the leaves values. Use ``1`` for no shrinkage.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=learning_rate,-float%2C%20default%3D0.1) | 0.1 |
| [max\_iter max\_iter: int, default=100  The maximum number of iterations of the boosting process, i.e. the maximum number of trees for binary classification. For multiclass classification, `n\_classes` trees per iteration are built.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=max_iter,-int%2C%20default%3D100) | 100 |
| [max\_leaf\_nodes max\_leaf\_nodes: int or None, default=31  The maximum number of leaves for each tree. Must be strictly greater than 1. If None, there is no maximum limit.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=max_leaf_nodes,-int%20or%20None%2C%20default%3D31) | 31 |
| [max\_depth max\_depth: int or None, default=None  The maximum depth of each tree. The depth of a tree is the number of edges to go from the root to the deepest leaf. Depth isn't constrained by default.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=max_depth,-int%20or%20None%2C%20default%3DNone) | None |
| [min\_samples\_leaf min\_samples\_leaf: int, default=20  The minimum number of samples per leaf. For small datasets with less than a few hundred samples, it is recommended to lower this value since only very shallow trees would be built.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=min_samples_leaf,-int%2C%20default%3D20) | 20 |
| [l2\_regularization l2\_regularization: float, default=0  The L2 regularization parameter penalizing leaves with small hessians. Use ``0`` for no regularization (default).](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=l2_regularization,-float%2C%20default%3D0) | 0.0 |
| [max\_features max\_features: float, default=1.0  Proportion of randomly chosen features in each and every node split. This is a form of regularization, smaller values make the trees weaker learners and might prevent overfitting. If interaction constraints from `interaction\_cst` are present, only allowed features are taken into account for the subsampling.  .. versionadded:: 1.4](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=max_features,-float%2C%20default%3D1.0) | 1.0 |
| [max\_bins max\_bins: int, default=255  The maximum number of bins to use for non-missing values. Before training, each feature of the input array `X` is binned into integer-valued bins, which allows for a much faster training stage. Features with a small number of unique values may use less than ``max\_bins`` bins. In addition to the ``max\_bins`` bins, one more bin is always reserved for missing values. Must be no larger than 255.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=max_bins,-int%2C%20default%3D255) | 255 |
| [categorical\_features categorical\_features: array-like of {bool, int, str} of shape (n\_features) or shape (n\_categorical\_features,), default='from\_dtype'  Indicates the categorical features.  - None : no feature will be considered categorical. - boolean array-like : boolean mask indicating categorical features. - integer array-like : integer indices indicating categorical  features. - str array-like: names of categorical features (assuming the training  data has feature names). - `"from\_dtype"`: dataframe columns with dtype "category" are  considered to be categorical features. The input must be an object  exposing a ``\_\_dataframe\_\_`` method such as pandas or polars  DataFrames to use this feature.  For each categorical feature, there must be at most `max\_bins` unique categories. Negative values for categorical features encoded as numeric dtypes are treated as missing values. All categorical values are converted to floating point numbers. This means that categorical values of 1.0 and 1 are treated as the same category.  Read more in the :ref:`User Guide `.  .. versionadded:: 0.24  .. versionchanged:: 1.2  Added support for feature names.  .. versionchanged:: 1.4  Added `"from\_dtype"` option.  .. versionchanged:: 1.6  The default value changed from `None` to `"from\_dtype"`.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=categorical_features,-array-like%20of%20%7Bbool%2C%20int%2C%20str%7D%20of%20shape%20%28n_features%29%20%20%20%20%20%20%20%20%20%20%20%20%20or%20shape%20%28n_categorical_features%2C%29%2C%20default%3D%27from_dtype%27) | 'from\_dtype' |
| [monotonic\_cst monotonic\_cst: array-like of int of shape (n\_features) or dict, default=None  Monotonic constraint to enforce on each feature are specified using the following integer values:  - 1: monotonic increase - 0: no constraint - -1: monotonic decrease  If a dict with str keys, map feature to monotonic constraints by name. If an array, the features are mapped to constraints by position. See :ref:`monotonic\_cst\_features\_names` for a usage example.  The constraints are only valid for binary classifications and hold over the probability of the positive class. Read more in the :ref:`User Guide `.  .. versionadded:: 0.23  .. versionchanged:: 1.2  Accept dict of constraints with feature names as keys.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=monotonic_cst,-array-like%20of%20int%20of%20shape%20%28n_features%29%20or%20dict%2C%20default%3DNone) | None |
| [interaction\_cst interaction\_cst: {"pairwise", "no\_interactions"} or sequence of lists/tuples/sets of int, default=None  Specify interaction constraints, the sets of features which can interact with each other in child node splits.  Each item specifies the set of feature indices that are allowed to interact with each other. If there are more features than specified in these constraints, they are treated as if they were specified as an additional set.  The strings "pairwise" and "no\_interactions" are shorthands for allowing only pairwise or no interactions, respectively.  For instance, with 5 features in total, `interaction\_cst=[{0, 1}]` is equivalent to `interaction\_cst=[{0, 1}, {2, 3, 4}]`, and specifies that each branch of a tree will either only split on features 0 and 1 or only split on features 2, 3 and 4.  See :ref:`this example` on how to use `interaction\_cst`.  .. versionadded:: 1.2](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=interaction_cst,-%7B%22pairwise%22%2C%20%22no_interactions%22%7D%20or%20sequence%20of%20lists/tuples/sets%20%20%20%20%20%20%20%20%20%20%20%20%20of%20int%2C%20default%3DNone) | None |
| [warm\_start warm\_start: bool, default=False  When set to ``True``, reuse the solution of the previous call to fit and add more estimators to the ensemble. For results to be valid, the estimator should be re-trained on the same data only. See :term:`the Glossary `.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=warm_start,-bool%2C%20default%3DFalse) | False |
| [early\_stopping early\_stopping: 'auto' or bool, default='auto'  If 'auto', early stopping is enabled if the sample size is larger than 10000 or if `X\_val` and `y\_val` are passed to `fit`. If True, early stopping is enabled, otherwise early stopping is disabled.  .. versionadded:: 0.23](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=early_stopping,-%27auto%27%20or%20bool%2C%20default%3D%27auto%27) | 'auto' |
| [scoring scoring: str or callable or None, default='loss'  Scoring method to use for early stopping. Only used if `early\_stopping` is enabled. Options:  - str: see :ref:`scoring\_string\_names` for options. - callable: a scorer callable object (e.g., function) with signature  ``scorer(estimator, X, y)``. See :ref:`scoring\_callable` for details. - `None`: :ref:`accuracy ` is used. - 'loss': early stopping is checked w.r.t the loss value.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=scoring,-str%20or%20callable%20or%20None%2C%20default%3D%27loss%27) | 'loss' |
| [validation\_fraction validation\_fraction: int or float or None, default=0.1  Proportion (or absolute size) of training data to set aside as validation data for early stopping. If None, early stopping is done on the training data. The value is ignored if either early stopping is not performed, e.g. `early\_stopping=False`, or if `X\_val` and `y\_val` are passed to fit.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=validation_fraction,-int%20or%20float%20or%20None%2C%20default%3D0.1) | 0.1 |
| [n\_iter\_no\_change n\_iter\_no\_change: int, default=10  Used to determine when to "early stop". The fitting process is stopped when none of the last ``n\_iter\_no\_change`` scores are better than the ``n\_iter\_no\_change - 1`` -th-to-last one, up to some tolerance. Only used if early stopping is performed.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=n_iter_no_change,-int%2C%20default%3D10) | 10 |
| [tol tol: float, default=1e-7  The absolute tolerance to use when comparing scores. The higher the tolerance, the more likely we are to early stop: higher tolerance means that it will be harder for subsequent iterations to be considered an improvement upon the reference score.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=tol,-float%2C%20default%3D1e-7) | 1e-07 |
| [verbose verbose: int, default=0  The verbosity level. If not zero, print some information about the fitting process. ``1`` prints only summary info, ``2`` prints info per iteration.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=verbose,-int%2C%20default%3D0) | 0 |
| [random\_state random\_state: int, RandomState instance or None, default=None  Pseudo-random number generator to control the subsampling in the binning process, and the train/validation data split if early stopping is enabled. Pass an int for reproducible output across multiple function calls. See :term:`Glossary `.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=random_state,-int%2C%20RandomState%20instance%20or%20None%2C%20default%3DNone) | 0 |
| [class\_weight class\_weight: dict or 'balanced', default=None  Weights associated with classes in the form `{class\_label: weight}`. If not given, all classes are supposed to have weight one. The "balanced" mode uses the values of y to automatically adjust weights inversely proportional to class frequencies in the input data as `n\_samples / (n\_classes \* np.bincount(y))`. Note that these weights will be multiplied with sample\_weight (passed through the fit method) if `sample\_weight` is specified.  .. versionadded:: 1.2](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=class_weight,-dict%20or%20%27balanced%27%2C%20default%3DNone) | None |

  
   

We evaluate the performance of our predictive model using the ROC and Precision-Recall curves.

```
 import  matplotlib.pyplot  as  plt from  sklearn.metrics  import PrecisionRecallDisplay, RocCurveDisplay fig, axs = plt. subplots(nrows = 1, ncols = 2, figsize =(14, 6)) PrecisionRecallDisplay. from_estimator(model, X_test, y_test, pos_label = pos_label, ax = axs[0], name = "GBDT") axs[0]. plot(scoring["recall"](model, X_test, y_test), scoring["precision"](model, X_test, y_test), marker = "o", markersize = 10, color ="tab:blue", label ="Default cut-off point at a probability of 0.5",) axs[0]. set_title("Precision-Recall curve") axs[0]. legend() RocCurveDisplay. from_estimator(model, X_test, y_test, pos_label = pos_label, ax = axs[1], name = "GBDT", plot_chance_level = True,) axs[1]. plot(scoring["fpr"](model, X_test, y_test), scoring["tpr"](model, X_test, y_test), marker = "o", markersize = 10, color ="tab:blue", label ="Default cut-off point at a probability of 0.5",) axs[1]. set_title("ROC curve") axs[1]. legend() _ = fig. suptitle("Evaluation of the vanilla GBDT model")
```

![Evaluation of the vanilla GBDT model, Precision-Recall curve, ROC curve](../../_images/sphx_glr_plot_cost_sensitive_learning_001.png)

We recall that these curves give insights on the statistical performance of the predictive model for different cut-off points. For the Precision-Recall curve, the reported metrics are the precision and recall and for the ROC curve, the reported metrics are the TPR (same as recall) and FPR.

Here, the different cut-off points correspond to different levels of posterior probability estimates ranging between 0 and 1. By default, `model.predict` uses a cut-off point at a probability estimate of 0.5. The metrics for such a cut-off point are reported with the blue dot on the curves: it corresponds to the statistical performance of the model when using `model.predict`.

However, we recall that the original aim was to minimize the cost (or maximize the gain) as defined by the business metric. We can compute the value of the business metric:

```
 print(f"Business defined metric: {scoring['credit_gain'](model,  X_test,  y_test)} ")
```

At this stage we don’t know if any other cut-off can lead to a greater gain. To find the optimal one, we need to compute the cost-gain using the business metric for all possible cut-off points and choose the best. This strategy can be quite tedious to implement by hand, but the [`TunedThresholdClassifierCV`](../../modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#sklearn.model_selection.TunedThresholdClassifierCV "sklearn.model_selection.TunedThresholdClassifierCV") class is here to help us. It automatically computes the cost-gain for all possible cut-off points and optimizes for the `scoring`.

### Tuning the cut-off point[#](#tuning-the-cut-off-point "Link to this heading")

We use [`TunedThresholdClassifierCV`](../../modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#sklearn.model_selection.TunedThresholdClassifierCV "sklearn.model_selection.TunedThresholdClassifierCV") to tune the cut-off point. We need to provide the business metric to optimize as well as the positive label. Internally, the optimum cut-off point is chosen such that it maximizes the business metric via cross-validation. By default a 5-fold stratified cross-validation is used.

```
 from  sklearn.model_selection  import TunedThresholdClassifierCV tuned_model = TunedThresholdClassifierCV(estimator = model, scoring = scoring["credit_gain"], store_cv_results = True, # necessary to inspect all results) tuned_model. fit(X_train, y_train) print(f "{tuned_model. best_threshold_ =:0.2f} ")
```

We plot the ROC and Precision-Recall curves for the vanilla model and the tuned model. Also we plot the cut-off points that would be used by each model. Because, we are reusing the same code later, we define a function that generates the plots.

```
 def  plot_roc_pr_curves(vanilla_model, tuned_model,*, title): fig, axs = plt. subplots(nrows = 1, ncols = 3, figsize =(21, 6)) linestyles =("dashed", "dotted") markerstyles =("o",">") colors =("tab:blue","tab:orange") names =("Vanilla GBDT", "Tuned GBDT") for idx,(est, linestyle, marker, color, name) in enumerate(zip((vanilla_model, tuned_model), linestyles, markerstyles, colors, names)): decision_threshold = getattr(est, "best_threshold_",0.5) PrecisionRecallDisplay. from_estimator(est, X_test, y_test, pos_label = pos_label, linestyle = linestyle, color = color, ax = axs[0], name = name,) axs[0]. plot(scoring["recall"](est, X_test, y_test), scoring["precision"](est, X_test, y_test), marker, markersize = 10, color = color, label = f"Cut-off point at probability of {decision_threshold:.2f} ",) RocCurveDisplay. from_estimator(est, X_test, y_test, pos_label = pos_label, curve_kwargs = dict(linestyle = linestyle, color = color), ax = axs[1], name = name, plot_chance_level = idx == 1,) axs[1]. plot(scoring["fpr"](est, X_test, y_test), scoring["tpr"](est, X_test, y_test), marker, markersize = 10, color = color, label = f"Cut-off point at probability of {decision_threshold:.2f} ",) axs[0]. set_title("Precision-Recall curve") axs[0]. legend() axs[1]. set_title("ROC curve") axs[1]. legend() axs[2]. plot(tuned_model. cv_results_["thresholds"], tuned_model. cv_results_["scores"], color ="tab:orange",) axs[2]. plot(tuned_model. best_threshold_, tuned_model. best_score_, "o", markersize = 10, color ="tab:orange", label ="Optimal cut-off point for the business metric",) axs[2]. legend() axs[2]. set_xlabel("Decision threshold (probability)") axs[2]. set_ylabel("Objective score (using cost-matrix)") axs[2]. set_title("Objective score as a function of the decision threshold") fig. suptitle(title)
```

```
 title ="Comparison of the cut-off point for the vanilla and tuned GBDT model" plot_roc_pr_curves(model, tuned_model, title = title)
```

![Comparison of the cut-off point for the vanilla and tuned GBDT model, Precision-Recall curve, ROC curve, Objective score as a function of the decision threshold](../../_images/sphx_glr_plot_cost_sensitive_learning_002.png)

The first remark is that both classifiers have exactly the same ROC and Precision-Recall curves. It is expected because by default, the classifier is fitted on the same training data. In a later section, we discuss more in detail the available options regarding model refitting and cross-validation.

The second remark is that the cut-off points of the vanilla and tuned model are different. To understand why the tuned model has chosen this cut-off point, we can look at the right-hand side plot that plots the objective score that is our exactly the same as our business metric. We see that the optimum threshold corresponds to the maximum of the objective score. This maximum is reached for a decision threshold much lower than 0.5: the tuned model enjoys a much higher recall at the cost of of significantly lower precision: the tuned model is much more eager to predict the “bad” class label to larger fraction of individuals.

We can now check if choosing this cut-off point leads to a better score on the testing set:

```
 print(f"Business defined metric: {scoring['credit_gain'](tuned_model,  X_test,  y_test)} ")
```

We observe that tuning the decision threshold almost improves our business gains by factor of 2.

### Consideration regarding model refitting and cross-validation[#](#consideration-regarding-model-refitting-and-cross-validation "Link to this heading")

In the above experiment, we used the default setting of the [`TunedThresholdClassifierCV`](../../modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#sklearn.model_selection.TunedThresholdClassifierCV "sklearn.model_selection.TunedThresholdClassifierCV"). In particular, the cut-off point is tuned using a 5-fold stratified cross-validation. Also, the underlying predictive model is refitted on the entire training data once the cut-off point is chosen.

These two strategies can be changed by providing the `refit` and `cv` parameters. For instance, one could provide a fitted `estimator` and set `cv="prefit"`, in which case the cut-off point is found on the entire dataset provided at fitting time. Also, the underlying classifier is not be refitted by setting `refit=False`. Here, we can try to do such experiment.

```
 model. fit(X_train, y_train) tuned_model. set_params(cv = "prefit", refit = False). fit(X_train, y_train) print(f "{tuned_model. best_threshold_ =:0.2f} ")
```

Then, we evaluate our model with the same approach as before:

```
 title = "Tuned GBDT model without refitting and using the entire dataset" plot_roc_pr_curves(model, tuned_model, title = title)
```

![Tuned GBDT model without refitting and using the entire dataset, Precision-Recall curve, ROC curve, Objective score as a function of the decision threshold](../../_images/sphx_glr_plot_cost_sensitive_learning_003.png)

We observe the that the optimum cut-off point is different from the one found in the previous experiment. If we look at the right-hand side plot, we observe that the business gain has large plateau of near-optimal 0 gain for a large span of decision thresholds. This behavior is symptomatic of an overfitting. Because we disable cross-validation, we tuned the cut-off point on the same set as the model was trained on, and this is the reason for the observed overfitting.

This option should therefore be used with caution. One needs to make sure that the data provided at fitting time to the [`TunedThresholdClassifierCV`](../../modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#sklearn.model_selection.TunedThresholdClassifierCV "sklearn.model_selection.TunedThresholdClassifierCV") is not the same as the data used to train the underlying classifier. This could happen sometimes when the idea is just to tune the predictive model on a completely new validation set without a costly complete refit.

When cross-validation is too costly, a potential alternative is to use a single train-test split by providing a floating number in range `[0,1]` to the `cv` parameter. It splits the data into a training and testing set. Let’s explore this option:

```
 tuned_model. set_params(cv =0.75). fit(X_train, y_train)
```

```
TunedThresholdClassifierCV(cv=0.75, estimator=HistGradientBoostingClassifier(random_state=0), refit=False, scoring=make_scorer(credit_gain_score, response_method='predict', neg_label=good, pos_label=bad), store_cv_results=True)
```

**In a Jupyter environment, please rerun this cell to show the HTML representation or trust the notebook.   
On GitHub, the HTML representation is unable to render, please try loading this page with nbviewer.org.**

Parameters

|  |  |
| --- | --- |
| [estimator estimator: estimator instance  The classifier, fitted or not, for which we want to optimize the decision threshold used during `predict`.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=estimator,-estimator%20instance) | HistGradientB...andom\_state=0) |
| [scoring scoring: str or callable, default="balanced\_accuracy"  The objective metric to be optimized. Can be one of:  - str: string associated to a scoring function for binary classification,  see :ref:`scoring\_string\_names` for options. - callable: a scorer callable object (e.g., function) with signature  ``scorer(estimator, X, y)``. See :ref:`scoring\_callable` for details.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=scoring,-str%20or%20callable%2C%20default%3D%22balanced_accuracy%22) | make\_scorer(c...pos\_label=bad) |
| [response\_method response\_method: {"auto", "decision\_function", "predict\_proba"}, default="auto"  Methods by the classifier `estimator` corresponding to the decision function for which we want to find a threshold. It can be:  \* if `"auto"`, it will try to invoke, for each classifier,  `"predict\_proba"` or `"decision\_function"` in that order. \* otherwise, one of `"predict\_proba"` or `"decision\_function"`.  If the method is not implemented by the classifier, it will raise an  error.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=response_method,-%7B%22auto%22%2C%20%22decision_function%22%2C%20%22predict_proba%22%7D%2C%20default%3D%22auto%22) | 'auto' |
| [thresholds thresholds: int or array-like, default=100  The number of decision threshold to use when discretizing the output of the classifier `method`. Pass an array-like to manually specify the thresholds to use.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=thresholds,-int%20or%20array-like%2C%20default%3D100) | 100 |
| [cv cv: int, float, cross-validation generator, iterable or "prefit", default=None  Determines the cross-validation splitting strategy to train classifier. Possible inputs for cv are:  \* `None`, to use the default 5-fold stratified K-fold cross validation; \* An integer number, to specify the number of folds in a stratified k-fold; \* A float number, to specify a single shuffle split. The floating number should  be in (0, 1) and represent the size of the validation set; \* An object to be used as a cross-validation generator; \* An iterable yielding train, test splits; \* `"prefit"`, to bypass the cross-validation.  Refer :ref:`User Guide ` for the various cross-validation strategies that can be used here.  .. warning::  Using `cv="prefit"` and passing the same dataset for fitting `estimator`  and tuning the cut-off point is subject to undesired overfitting. You can  refer to :ref:`TunedThresholdClassifierCV\_no\_cv` for an example.   This option should only be used when the set used to fit `estimator` is  different from the one used to tune the cut-off point (by calling  :meth:`TunedThresholdClassifierCV.fit`).](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=cv,-int%2C%20float%2C%20cross-validation%20generator%2C%20iterable%20or%20%22prefit%22%2C%20default%3DNone) | 0.75 |
| [refit refit: bool, default=True  Whether or not to refit the classifier on the entire training set once the decision threshold has been found. Note that forcing `refit=False` on cross-validation having more than a single split will raise an error. Similarly, `refit=True` in conjunction with `cv="prefit"` will raise an error.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=refit,-bool%2C%20default%3DTrue) | False |
| [n\_jobs n\_jobs: int, default=None  The number of jobs to run in parallel. When `cv` represents a cross-validation strategy, the fitting and scoring on each data split is done in parallel. ``None`` means 1 unless in a :obj:`joblib.parallel\_backend` context. ``-1`` means using all processors. See :term:`Glossary ` for more details.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=n_jobs,-int%2C%20default%3DNone) | None |
| [random\_state random\_state: int, RandomState instance or None, default=None  Controls the randomness of cross-validation when `cv` is a float. See :term:`Glossary `.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=random_state,-int%2C%20RandomState%20instance%20or%20None%2C%20default%3DNone) | None |
| [store\_cv\_results store\_cv\_results: bool, default=False  Whether to store all scores and thresholds computed during the cross-validation process.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=store_cv_results,-bool%2C%20default%3DFalse) | True |

```
HistGradientBoostingClassifier(random_state=0)
```

Parameters

|  |  |
| --- | --- |
| [loss loss: {'log\_loss'}, default='log\_loss'  The loss function to use in the boosting process.  For binary classification problems, 'log\_loss' is also known as logistic loss, binomial deviance or binary crossentropy. Internally, the model fits one tree per boosting iteration and uses the logistic sigmoid function (expit) as inverse link function to compute the predicted positive class probability.  For multiclass classification problems, 'log\_loss' is also known as multinomial deviance or categorical crossentropy. Internally, the model fits one tree per boosting iteration and per class and uses the softmax function as inverse link function to compute the predicted probabilities of the classes.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=loss,-%7B%27log_loss%27%7D%2C%20default%3D%27log_loss%27) | 'log\_loss' |
| [learning\_rate learning\_rate: float, default=0.1  The learning rate, also known as \*shrinkage\*. This is used as a multiplicative factor for the leaves values. Use ``1`` for no shrinkage.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=learning_rate,-float%2C%20default%3D0.1) | 0.1 |
| [max\_iter max\_iter: int, default=100  The maximum number of iterations of the boosting process, i.e. the maximum number of trees for binary classification. For multiclass classification, `n\_classes` trees per iteration are built.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=max_iter,-int%2C%20default%3D100) | 100 |
| [max\_leaf\_nodes max\_leaf\_nodes: int or None, default=31  The maximum number of leaves for each tree. Must be strictly greater than 1. If None, there is no maximum limit.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=max_leaf_nodes,-int%20or%20None%2C%20default%3D31) | 31 |
| [max\_depth max\_depth: int or None, default=None  The maximum depth of each tree. The depth of a tree is the number of edges to go from the root to the deepest leaf. Depth isn't constrained by default.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=max_depth,-int%20or%20None%2C%20default%3DNone) | None |
| [min\_samples\_leaf min\_samples\_leaf: int, default=20  The minimum number of samples per leaf. For small datasets with less than a few hundred samples, it is recommended to lower this value since only very shallow trees would be built.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=min_samples_leaf,-int%2C%20default%3D20) | 20 |
| [l2\_regularization l2\_regularization: float, default=0  The L2 regularization parameter penalizing leaves with small hessians. Use ``0`` for no regularization (default).](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=l2_regularization,-float%2C%20default%3D0) | 0.0 |
| [max\_features max\_features: float, default=1.0  Proportion of randomly chosen features in each and every node split. This is a form of regularization, smaller values make the trees weaker learners and might prevent overfitting. If interaction constraints from `interaction\_cst` are present, only allowed features are taken into account for the subsampling.  .. versionadded:: 1.4](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=max_features,-float%2C%20default%3D1.0) | 1.0 |
| [max\_bins max\_bins: int, default=255  The maximum number of bins to use for non-missing values. Before training, each feature of the input array `X` is binned into integer-valued bins, which allows for a much faster training stage. Features with a small number of unique values may use less than ``max\_bins`` bins. In addition to the ``max\_bins`` bins, one more bin is always reserved for missing values. Must be no larger than 255.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=max_bins,-int%2C%20default%3D255) | 255 |
| [categorical\_features categorical\_features: array-like of {bool, int, str} of shape (n\_features) or shape (n\_categorical\_features,), default='from\_dtype'  Indicates the categorical features.  - None : no feature will be considered categorical. - boolean array-like : boolean mask indicating categorical features. - integer array-like : integer indices indicating categorical  features. - str array-like: names of categorical features (assuming the training  data has feature names). - `"from\_dtype"`: dataframe columns with dtype "category" are  considered to be categorical features. The input must be an object  exposing a ``\_\_dataframe\_\_`` method such as pandas or polars  DataFrames to use this feature.  For each categorical feature, there must be at most `max\_bins` unique categories. Negative values for categorical features encoded as numeric dtypes are treated as missing values. All categorical values are converted to floating point numbers. This means that categorical values of 1.0 and 1 are treated as the same category.  Read more in the :ref:`User Guide `.  .. versionadded:: 0.24  .. versionchanged:: 1.2  Added support for feature names.  .. versionchanged:: 1.4  Added `"from\_dtype"` option.  .. versionchanged:: 1.6  The default value changed from `None` to `"from\_dtype"`.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=categorical_features,-array-like%20of%20%7Bbool%2C%20int%2C%20str%7D%20of%20shape%20%28n_features%29%20%20%20%20%20%20%20%20%20%20%20%20%20or%20shape%20%28n_categorical_features%2C%29%2C%20default%3D%27from_dtype%27) | 'from\_dtype' |
| [monotonic\_cst monotonic\_cst: array-like of int of shape (n\_features) or dict, default=None  Monotonic constraint to enforce on each feature are specified using the following integer values:  - 1: monotonic increase - 0: no constraint - -1: monotonic decrease  If a dict with str keys, map feature to monotonic constraints by name. If an array, the features are mapped to constraints by position. See :ref:`monotonic\_cst\_features\_names` for a usage example.  The constraints are only valid for binary classifications and hold over the probability of the positive class. Read more in the :ref:`User Guide `.  .. versionadded:: 0.23  .. versionchanged:: 1.2  Accept dict of constraints with feature names as keys.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=monotonic_cst,-array-like%20of%20int%20of%20shape%20%28n_features%29%20or%20dict%2C%20default%3DNone) | None |
| [interaction\_cst interaction\_cst: {"pairwise", "no\_interactions"} or sequence of lists/tuples/sets of int, default=None  Specify interaction constraints, the sets of features which can interact with each other in child node splits.  Each item specifies the set of feature indices that are allowed to interact with each other. If there are more features than specified in these constraints, they are treated as if they were specified as an additional set.  The strings "pairwise" and "no\_interactions" are shorthands for allowing only pairwise or no interactions, respectively.  For instance, with 5 features in total, `interaction\_cst=[{0, 1}]` is equivalent to `interaction\_cst=[{0, 1}, {2, 3, 4}]`, and specifies that each branch of a tree will either only split on features 0 and 1 or only split on features 2, 3 and 4.  See :ref:`this example` on how to use `interaction\_cst`.  .. versionadded:: 1.2](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=interaction_cst,-%7B%22pairwise%22%2C%20%22no_interactions%22%7D%20or%20sequence%20of%20lists/tuples/sets%20%20%20%20%20%20%20%20%20%20%20%20%20of%20int%2C%20default%3DNone) | None |
| [warm\_start warm\_start: bool, default=False  When set to ``True``, reuse the solution of the previous call to fit and add more estimators to the ensemble. For results to be valid, the estimator should be re-trained on the same data only. See :term:`the Glossary `.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=warm_start,-bool%2C%20default%3DFalse) | False |
| [early\_stopping early\_stopping: 'auto' or bool, default='auto'  If 'auto', early stopping is enabled if the sample size is larger than 10000 or if `X\_val` and `y\_val` are passed to `fit`. If True, early stopping is enabled, otherwise early stopping is disabled.  .. versionadded:: 0.23](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=early_stopping,-%27auto%27%20or%20bool%2C%20default%3D%27auto%27) | 'auto' |
| [scoring scoring: str or callable or None, default='loss'  Scoring method to use for early stopping. Only used if `early\_stopping` is enabled. Options:  - str: see :ref:`scoring\_string\_names` for options. - callable: a scorer callable object (e.g., function) with signature  ``scorer(estimator, X, y)``. See :ref:`scoring\_callable` for details. - `None`: :ref:`accuracy ` is used. - 'loss': early stopping is checked w.r.t the loss value.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=scoring,-str%20or%20callable%20or%20None%2C%20default%3D%27loss%27) | 'loss' |
| [validation\_fraction validation\_fraction: int or float or None, default=0.1  Proportion (or absolute size) of training data to set aside as validation data for early stopping. If None, early stopping is done on the training data. The value is ignored if either early stopping is not performed, e.g. `early\_stopping=False`, or if `X\_val` and `y\_val` are passed to fit.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=validation_fraction,-int%20or%20float%20or%20None%2C%20default%3D0.1) | 0.1 |
| [n\_iter\_no\_change n\_iter\_no\_change: int, default=10  Used to determine when to "early stop". The fitting process is stopped when none of the last ``n\_iter\_no\_change`` scores are better than the ``n\_iter\_no\_change - 1`` -th-to-last one, up to some tolerance. Only used if early stopping is performed.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=n_iter_no_change,-int%2C%20default%3D10) | 10 |
| [tol tol: float, default=1e-7  The absolute tolerance to use when comparing scores. The higher the tolerance, the more likely we are to early stop: higher tolerance means that it will be harder for subsequent iterations to be considered an improvement upon the reference score.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=tol,-float%2C%20default%3D1e-7) | 1e-07 |
| [verbose verbose: int, default=0  The verbosity level. If not zero, print some information about the fitting process. ``1`` prints only summary info, ``2`` prints info per iteration.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=verbose,-int%2C%20default%3D0) | 0 |
| [random\_state random\_state: int, RandomState instance or None, default=None  Pseudo-random number generator to control the subsampling in the binning process, and the train/validation data split if early stopping is enabled. Pass an int for reproducible output across multiple function calls. See :term:`Glossary `.](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=random_state,-int%2C%20RandomState%20instance%20or%20None%2C%20default%3DNone) | 0 |
| [class\_weight class\_weight: dict or 'balanced', default=None  Weights associated with classes in the form `{class\_label: weight}`. If not given, all classes are supposed to have weight one. The "balanced" mode uses the values of y to automatically adjust weights inversely proportional to class frequencies in the input data as `n\_samples / (n\_classes \* np.bincount(y))`. Note that these weights will be multiplied with sample\_weight (passed through the fit method) if `sample\_weight` is specified.  .. versionadded:: 1.2](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html#:~:text=class_weight,-dict%20or%20%27balanced%27%2C%20default%3DNone) | None |

  
   

```
 title = "Tuned GBDT model without refitting and using the entire dataset" plot_roc_pr_curves(model, tuned_model, title = title)
```

![Tuned GBDT model without refitting and using the entire dataset, Precision-Recall curve, ROC curve, Objective score as a function of the decision threshold](../../_images/sphx_glr_plot_cost_sensitive_learning_004.png)

Regarding the cut-off point, we observe that the optimum is similar to the multiple repeated cross-validation case. However, be aware that a single split does not account for the variability of the fit/predict process and thus we are unable to know if there is any variance in the cut-off point. The repeated cross-validation averages out this effect.

Another observation concerns the ROC and Precision-Recall curves of the tuned model. As expected, these curves differ from those of the vanilla model, given that we trained the underlying classifier on a subset of the data provided during fitting and reserved a validation set for tuning the cut-off point.

## Cost-sensitive learning when gains and costs are not constant[#](#cost-sensitive-learning-when-gains-and-costs-are-not-constant "Link to this heading")

As stated in [[2]](#id3), gains and costs are generally not constant in real-world problems. In this section, we use a similar example as in [[2]](#id3) for the problem of detecting fraud in credit card transaction records.

### The credit card dataset[#](#the-credit-card-dataset "Link to this heading")

```
 credit_card = fetch_openml(data_id = 1597, as_frame = True, parser = "pandas") credit_card. frame. info()
```

The dataset contains information about credit card records from which some are fraudulent and others are legitimate. The goal is therefore to predict whether or not a credit card record is fraudulent.

```
 columns_to_drop =["Class"] data = credit_card. frame. drop(columns = columns_to_drop) target = credit_card. frame["Class"]. astype(int)
```

First, we check the class distribution of the datasets.

```
 target. value_counts(normalize = True)
```

The dataset is highly imbalanced with fraudulent transaction representing only 0.17% of the data. Since we are interested in training a machine learning model, we should also make sure that we have enough samples in the minority class to train the model.

```
 target. value_counts()
```

We observe that we have around 500 samples that is on the low end of the number of samples required to train a machine learning model. In addition of the target distribution, we check the distribution of the amount of the fraudulent transactions.

```
 fraud = target == 1 amount_fraud = data["Amount"][fraud] _, ax = plt. subplots() ax. hist(amount_fraud, bins = 30) ax. set_title("Amount of fraud transaction") _ = ax. set_xlabel("Amount (€)")
```

![Amount of fraud transaction](../../_images/sphx_glr_plot_cost_sensitive_learning_005.png)

### Addressing the problem with a business metric[#](#addressing-the-problem-with-a-business-metric "Link to this heading")

Now, we create the business metric that depends on the amount of each transaction. We define the cost matrix similarly to [[2]](#id3). Accepting a legitimate transaction provides a gain of 2% of the amount of the transaction. However, accepting a fraudulent transaction result in a loss of the amount of the transaction. As stated in [[2]](#id3), the gain and loss related to refusals (of fraudulent and legitimate transactions) are not trivial to define. Here, we define that a refusal of a legitimate transaction is estimated to a loss of 5€ while the refusal of a fraudulent transaction is estimated to a gain of 50€. Therefore, we define the following function to compute the total benefit of a given decision:

```
 def  business_metric(y_true, y_pred, amount): mask_true_positive =(y_true == 1) &(y_pred == 1) mask_true_negative =(y_true == 0) &(y_pred == 0) mask_false_positive =(y_true == 0) &(y_pred == 1) mask_false_negative =(y_true == 1) &(y_pred == 0) fraudulent_refuse = mask_true_positive. sum()* 50 fraudulent_accept = - amount[mask_false_negative]. sum() legitimate_refuse = mask_false_positive. sum()* - 5 legitimate_accept =(amount[mask_true_negative]*0.02). sum() return fraudulent_refuse + fraudulent_accept + legitimate_refuse + legitimate_accept
```

From this business metric, we create a scikit-learn scorer that given a fitted classifier and a test set compute the business metric. In this regard, we use the [`make_scorer`](../../modules/generated/sklearn.metrics.make_scorer.html#sklearn.metrics.make_scorer "sklearn.metrics.make_scorer") factory. The variable `amount` is an additional metadata to be passed to the scorer and we need to use [metadata routing](../../metadata_routing.html#metadata-routing) to take into account this information.

```
 sklearn. set_config(enable_metadata_routing = True) business_scorer = make_scorer(business_metric). set_score_request(amount = True)
```

So at this stage, we observe that the amount of the transaction is used twice: once as a feature to train our predictive model and once as a metadata to compute the the business metric and thus the statistical performance of our model. When used as a feature, we are only required to have a column in `data` that contains the amount of each transaction. To use this information as metadata, we need to have an external variable that we can pass to the scorer or the model that internally routes this metadata to the scorer. So let’s create this variable.

```
 amount = credit_card. frame["Amount"]. to_numpy()
```

```
 from  sklearn.model_selection  import train_test_split data_train, data_test, target_train, target_test, amount_train, amount_test =(train_test_split(data, target, amount, stratify = target, test_size =0.5, random_state = 42))
```

We first evaluate some baseline policies to serve as reference. Recall that class “0” is the legitimate class and class “1” is the fraudulent class.

```
 from  sklearn.dummy  import DummyClassifier always_accept_policy = DummyClassifier(strategy = "constant", constant = 0) always_accept_policy. fit(data_train, target_train) benefit = business_scorer(always_accept_policy, data_test, target_test, amount = amount_test) print(f"Benefit of the 'always accept' policy: {benefit:,.2f} €")
```

A policy that considers all transactions as legitimate would create a profit of around 220,000€. We make the same evaluation for a classifier that predicts all transactions as fraudulent.

```
 always_reject_policy = DummyClassifier(strategy = "constant", constant = 1) always_reject_policy. fit(data_train, target_train) benefit = business_scorer(always_reject_policy, data_test, target_test, amount = amount_test) print(f"Benefit of the 'always reject' policy: {benefit:,.2f} €")
```

Such a policy would entail a catastrophic loss: around 670,000€. This is expected since the vast majority of the transactions are legitimate and the policy would refuse them at a non-trivial cost.

A predictive model that adapts the accept/reject decisions on a per transaction basis should ideally allow us to make a profit larger than the 220,000€ of the best of our constant baseline policies.

We start with a logistic regression model with the default decision threshold at 0.5. Here we tune the hyperparameter `C` of the logistic regression with a proper scoring rule (the log loss) to ensure that the model’s probabilistic predictions returned by its `predict_proba` method are as accurate as possible, irrespectively of the choice of the value of the decision threshold.

```
 from  sklearn.linear_model  import LogisticRegression from  sklearn.model_selection  import GridSearchCV from  sklearn.pipeline  import make_pipeline from  sklearn.preprocessing  import StandardScaler logistic_regression = make_pipeline(StandardScaler(), LogisticRegression()) param_grid ={"logisticregression__C": np. logspace(- 6, 6, 13)} model = GridSearchCV(logistic_regression, param_grid, scoring = "neg_log_loss"). fit(data_train, target_train) model
```

```
GridSearchCV(estimator=Pipeline(steps=[('standardscaler', StandardScaler()), ('logisticregression', LogisticRegression())]), param_grid={'logisticregression__C': array([1.e-06, 1.e-05, 1.e-04, 1.e-03, 1.e-02, 1.e-01, 1.e+00, 1.e+01, 1.e+02, 1.e+03, 1.e+04, 1.e+05, 1.e+06])}, scoring='neg_log_loss')
```

**In a Jupyter environment, please rerun this cell to show the HTML representation or trust the notebook.   
On GitHub, the HTML representation is unable to render, please try loading this page with nbviewer.org.**

Parameters

|  |  |
| --- | --- |
| [estimator estimator: estimator object  This is assumed to implement the scikit-learn estimator interface. Either estimator needs to provide a ``score`` function, or ``scoring`` must be passed.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GridSearchCV.html#:~:text=estimator,-estimator%20object) | Pipeline(step...egression())]) |
| [param\_grid param\_grid: dict or list of dictionaries  Dictionary with parameters names (`str`) as keys and lists of parameter settings to try as values, or a list of such dictionaries, in which case the grids spanned by each dictionary in the list are explored. This enables searching over any sequence of parameter settings.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GridSearchCV.html#:~:text=param_grid,-dict%20or%20list%20of%20dictionaries) | {'logisticregression\_\_C': array([1.e-06...e+05, 1.e+06])} |
| [scoring scoring: str, callable, list, tuple or dict, default=None  Strategy to evaluate the performance of the cross-validated model on the test set.  If `scoring` represents a single score, one can use:  - a single string (see :ref:`scoring\_string\_names`); - a callable (see :ref:`scoring\_callable`) that returns a single value; - `None`, the `estimator`'s  :ref:`default evaluation criterion ` is used.  If `scoring` represents multiple scores, one can use:  - a list or tuple of unique strings; - a callable returning a dictionary where the keys are the metric  names and the values are the metric scores; - a dictionary with metric names as keys and callables as values.  See :ref:`multimetric\_grid\_search` for an example.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GridSearchCV.html#:~:text=scoring,-str%2C%20callable%2C%20list%2C%20tuple%20or%20dict%2C%20default%3DNone) | 'neg\_log\_loss' |
| [n\_jobs n\_jobs: int, default=None  Number of jobs to run in parallel. ``None`` means 1 unless in a :obj:`joblib.parallel\_backend` context. ``-1`` means using all processors. See :term:`Glossary ` for more details.  .. versionchanged:: v0.20  `n\_jobs` default changed from 1 to None](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GridSearchCV.html#:~:text=n_jobs,-int%2C%20default%3DNone) | None |
| [refit refit: bool, str, or callable, default=True  Refit an estimator using the best found parameters on the whole dataset.  For multiple metric evaluation, this needs to be a `str` denoting the scorer that would be used to find the best parameters for refitting the estimator at the end.  Where there are considerations other than maximum score in choosing a best estimator, ``refit`` can be set to a function which returns the selected ``best\_index\_`` given ``cv\_results\_``. In that case, the ``best\_estimator\_`` and ``best\_params\_`` will be set according to the returned ``best\_index\_`` while the ``best\_score\_`` attribute will not be available.  The refitted estimator is made available at the ``best\_estimator\_`` attribute and permits using ``predict`` directly on this ``GridSearchCV`` instance.  Also for multiple metric evaluation, the attributes ``best\_index\_``, ``best\_score\_`` and ``best\_params\_`` will only be available if ``refit`` is set and all of them will be determined w.r.t this specific scorer.  See ``scoring`` parameter to know more about multiple metric evaluation.  See :ref:`sphx\_glr\_auto\_examples\_model\_selection\_plot\_grid\_search\_digits.py` to see how to design a custom selection strategy using a callable via `refit`.  See :ref:`this example ` for an example of how to use ``refit=callable`` to balance model complexity and cross-validated score.  .. versionchanged:: 0.20  Support for callable added.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GridSearchCV.html#:~:text=refit,-bool%2C%20str%2C%20or%20callable%2C%20default%3DTrue) | True |
| [cv cv: int, cross-validation generator or an iterable, default=None  Determines the cross-validation splitting strategy. Possible inputs for cv are:  - None, to use the default 5-fold cross validation, - integer, to specify the number of folds in a `(Stratified)KFold`, - :term:`CV splitter`, - An iterable yielding (train, test) splits as arrays of indices.  For integer/None inputs, if the estimator is a classifier and ``y`` is either binary or multiclass, :class:`StratifiedKFold` is used. In all other cases, :class:`KFold` is used. These splitters are instantiated with `shuffle=False` so the splits will be the same across calls.  Refer :ref:`User Guide ` for the various cross-validation strategies that can be used here.  .. versionchanged:: 0.22  ``cv`` default value if None changed from 3-fold to 5-fold.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GridSearchCV.html#:~:text=cv,-int%2C%20cross-validation%20generator%20or%20an%20iterable%2C%20default%3DNone) | None |
| [verbose verbose: int  Controls the verbosity: the higher, the more messages.  - >1 : the computation time for each fold and parameter candidate is  displayed; - >2 : the score is also displayed; - >3 : the fold and candidate parameter indexes are also displayed  together with the starting time of the computation.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GridSearchCV.html#:~:text=verbose,-int) | 0 |
| [pre\_dispatch pre\_dispatch: int, or str, default='2\*n\_jobs'  Controls the number of jobs that get dispatched during parallel execution. Reducing this number can be useful to avoid an explosion of memory consumption when more jobs get dispatched than CPUs can process. This parameter can be:  - None, in which case all the jobs are immediately created and spawned. Use  this for lightweight and fast-running jobs, to avoid delays due to on-demand  spawning of the jobs - An int, giving the exact number of total jobs that are spawned - A str, giving an expression as a function of n\_jobs, as in '2\*n\_jobs'](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GridSearchCV.html#:~:text=pre_dispatch,-int%2C%20or%20str%2C%20default%3D%272%2An_jobs%27) | '2\*n\_jobs' |
| [error\_score error\_score: 'raise' or numeric, default=np.nan  Value to assign to the score if an error occurs in estimator fitting. If set to 'raise', the error is raised. If a numeric value is given, FitFailedWarning is raised. This parameter does not affect the refit step, which will always raise the error.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GridSearchCV.html#:~:text=error_score,-%27raise%27%20or%20numeric%2C%20default%3Dnp.nan) | nan |
| [return\_train\_score return\_train\_score: bool, default=False  If ``False``, the ``cv\_results\_`` attribute will not include training scores. Computing training scores is used to get insights on how different parameter settings impact the overfitting/underfitting trade-off. However computing the scores on the training set can be computationally expensive and is not strictly required to select the parameters that yield the best generalization performance.  .. versionadded:: 0.19  .. versionchanged:: 0.21  Default value was changed from ``True`` to ``False``](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GridSearchCV.html#:~:text=return_train_score,-bool%2C%20default%3DFalse) | False |

Parameters

|  |  |
| --- | --- |
| [copy copy: bool, default=True  If False, try to avoid a copy and do inplace scaling instead. This is not guaranteed to always work inplace; e.g. if the data is not a NumPy array or scipy.sparse CSR matrix, a copy may still be returned.](https://scikit-learn.org/1.8/modules/generated/sklearn.preprocessing.StandardScaler.html#:~:text=copy,-bool%2C%20default%3DTrue) | True |
| [with\_mean with\_mean: bool, default=True  If True, center the data before scaling. This does not work (and will raise an exception) when attempted on sparse matrices, because centering them entails building a dense matrix which in common use cases is likely to be too large to fit in memory.](https://scikit-learn.org/1.8/modules/generated/sklearn.preprocessing.StandardScaler.html#:~:text=with_mean,-bool%2C%20default%3DTrue) | True |
| [with\_std with\_std: bool, default=True  If True, scale the data to unit variance (or equivalently, unit standard deviation).](https://scikit-learn.org/1.8/modules/generated/sklearn.preprocessing.StandardScaler.html#:~:text=with_std,-bool%2C%20default%3DTrue) | True |

Parameters

|  |  |
| --- | --- |
| [penalty penalty: {'l1', 'l2', 'elasticnet', None}, default='l2'  Specify the norm of the penalty:  - `None`: no penalty is added; - `'l2'`: add a L2 penalty term and it is the default choice; - `'l1'`: add a L1 penalty term; - `'elasticnet'`: both L1 and L2 penalty terms are added.  .. warning::  Some penalties may not work with some solvers. See the parameter  `solver` below, to know the compatibility between the penalty and  solver.  .. versionadded:: 0.19  l1 penalty with SAGA solver (allowing 'multinomial' + L1)  .. deprecated:: 1.8  `penalty` was deprecated in version 1.8 and will be removed in 1.10.  Use `l1\_ratio` instead. `l1\_ratio=0` for `penalty='l2'`, `l1\_ratio=1` for  `penalty='l1'` and `l1\_ratio` set to any float between 0 and 1 for  `'penalty='elasticnet'`.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=penalty,-%7B%27l1%27%2C%20%27l2%27%2C%20%27elasticnet%27%2C%20None%7D%2C%20default%3D%27l2%27) | 'deprecated' |
| [C C: float, default=1.0  Inverse of regularization strength; must be a positive float. Like in support vector machines, smaller values specify stronger regularization. `C=np.inf` results in unpenalized logistic regression. For a visual example on the effect of tuning the `C` parameter with an L1 penalty, see: :ref:`sphx\_glr\_auto\_examples\_linear\_model\_plot\_logistic\_path.py`.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=C,-float%2C%20default%3D1.0) | np.float64(100.0) |
| [l1\_ratio l1\_ratio: float, default=0.0  The Elastic-Net mixing parameter, with `0 <= l1\_ratio <= 1`. Setting `l1\_ratio=1` gives a pure L1-penalty, setting `l1\_ratio=0` a pure L2-penalty. Any value between 0 and 1 gives an Elastic-Net penalty of the form `l1\_ratio \* L1 + (1 - l1\_ratio) \* L2`.  .. warning::  Certain values of `l1\_ratio`, i.e. some penalties, may not work with some  solvers. See the parameter `solver` below, to know the compatibility between  the penalty and solver.  .. versionchanged:: 1.8  Default value changed from None to 0.0.  .. deprecated:: 1.8  `None` is deprecated and will be removed in version 1.10. Always use  `l1\_ratio` to specify the penalty type.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=l1_ratio,-float%2C%20default%3D0.0) | 0.0 |
| [dual dual: bool, default=False  Dual (constrained) or primal (regularized, see also :ref:`this equation `) formulation. Dual formulation is only implemented for l2 penalty with liblinear solver. Prefer `dual=False` when n\_samples > n\_features.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=dual,-bool%2C%20default%3DFalse) | False |
| [tol tol: float, default=1e-4  Tolerance for stopping criteria.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=tol,-float%2C%20default%3D1e-4) | 0.0001 |
| [fit\_intercept fit\_intercept: bool, default=True  Specifies if a constant (a.k.a. bias or intercept) should be added to the decision function.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=fit_intercept,-bool%2C%20default%3DTrue) | True |
| [intercept\_scaling intercept\_scaling: float, default=1  Useful only when the solver `liblinear` is used and `self.fit\_intercept` is set to `True`. In this case, `x` becomes `[x, self.intercept\_scaling]`, i.e. a "synthetic" feature with constant value equal to `intercept\_scaling` is appended to the instance vector. The intercept becomes ``intercept\_scaling \* synthetic\_feature\_weight``.  .. note::  The synthetic feature weight is subject to L1 or L2  regularization as all other features.  To lessen the effect of regularization on synthetic feature weight  (and therefore on the intercept) `intercept\_scaling` has to be increased.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=intercept_scaling,-float%2C%20default%3D1) | 1 |
| [class\_weight class\_weight: dict or 'balanced', default=None  Weights associated with classes in the form ``{class\_label: weight}``. If not given, all classes are supposed to have weight one.  The "balanced" mode uses the values of y to automatically adjust weights inversely proportional to class frequencies in the input data as ``n\_samples / (n\_classes \* np.bincount(y))``.  Note that these weights will be multiplied with sample\_weight (passed through the fit method) if sample\_weight is specified.  .. versionadded:: 0.17  \*class\_weight='balanced'\*](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=class_weight,-dict%20or%20%27balanced%27%2C%20default%3DNone) | None |
| [random\_state random\_state: int, RandomState instance, default=None  Used when ``solver`` == 'sag', 'saga' or 'liblinear' to shuffle the data. See :term:`Glossary ` for details.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=random_state,-int%2C%20RandomState%20instance%2C%20default%3DNone) | None |
| [solver solver: {'lbfgs', 'liblinear', 'newton-cg', 'newton-cholesky', 'sag', 'saga'}, default='lbfgs'  Algorithm to use in the optimization problem. Default is 'lbfgs'. To choose a solver, you might want to consider the following aspects:  - 'lbfgs' is a good default solver because it works reasonably well for a wide  class of problems. - For :term:`multiclass` problems (`n\_classes >= 3`), all solvers except  'liblinear' minimize the full multinomial loss, 'liblinear' will raise an  error. - 'newton-cholesky' is a good choice for  `n\_samples` >> `n\_features \* n\_classes`, especially with one-hot encoded  categorical features with rare categories. Be aware that the memory usage  of this solver has a quadratic dependency on `n\_features \* n\_classes`  because it explicitly computes the full Hessian matrix. - For small datasets, 'liblinear' is a good choice, whereas 'sag'  and 'saga' are faster for large ones; - 'liblinear' can only handle binary classification by default. To apply a  one-versus-rest scheme for the multiclass setting one can wrap it with the  :class:`~sklearn.multiclass.OneVsRestClassifier`.  .. warning::  The choice of the algorithm depends on the penalty chosen (`l1\_ratio=0`  for L2-penalty, `l1\_ratio=1` for L1-penalty and `0 < l1\_ratio < 1` for  Elastic-Net) and on (multinomial) multiclass support:   ================= ======================== ======================  solver l1\_ratio multinomial multiclass  ================= ======================== ======================  'lbfgs' l1\_ratio=0 yes  'liblinear' l1\_ratio=1 or l1\_ratio=0 no  'newton-cg' l1\_ratio=0 yes  'newton-cholesky' l1\_ratio=0 yes  'sag' l1\_ratio=0 yes  'saga' 0<=l1\_ratio<=1 yes  ================= ======================== ======================  .. note::  'sag' and 'saga' fast convergence is only guaranteed on features  with approximately the same scale. You can preprocess the data with  a scaler from :mod:`sklearn.preprocessing`.  .. seealso::  Refer to the :ref:`User Guide ` for more  information regarding :class:`LogisticRegression` and more specifically the  :ref:`Table `  summarizing solver/penalty supports.  .. versionadded:: 0.17  Stochastic Average Gradient (SAG) descent solver. Multinomial support in  version 0.18. .. versionadded:: 0.19  SAGA solver. .. versionchanged:: 0.22  The default solver changed from 'liblinear' to 'lbfgs' in 0.22. .. versionadded:: 1.2  newton-cholesky solver. Multinomial support in version 1.6.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=solver,-%7B%27lbfgs%27%2C%20%27liblinear%27%2C%20%27newton-cg%27%2C%20%27newton-cholesky%27%2C%20%27sag%27%2C%20%27saga%27%7D%2C%20%20%20%20%20%20%20%20%20%20%20%20%20default%3D%27lbfgs%27) | 'lbfgs' |
| [max\_iter max\_iter: int, default=100  Maximum number of iterations taken for the solvers to converge.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=max_iter,-int%2C%20default%3D100) | 100 |
| [verbose verbose: int, default=0  For the liblinear and lbfgs solvers set verbose to any positive number for verbosity.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=verbose,-int%2C%20default%3D0) | 0 |
| [warm\_start warm\_start: bool, default=False  When set to True, reuse the solution of the previous call to fit as initialization, otherwise, just erase the previous solution. Useless for liblinear solver. See :term:`the Glossary `.  .. versionadded:: 0.17  \*warm\_start\* to support \*lbfgs\*, \*newton-cg\*, \*sag\*, \*saga\* solvers.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=warm_start,-bool%2C%20default%3DFalse) | False |
| [n\_jobs n\_jobs: int, default=None  Does not have any effect.  .. deprecated:: 1.8  `n\_jobs` is deprecated in version 1.8 and will be removed in 1.10.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=n_jobs,-int%2C%20default%3DNone) | None |

  
   

```
 print("Benefit of logistic regression with default threshold: " f "{business_scorer(model,  data_test,  target_test,  amount = amount_test):,.2f} €")
```

The business metric shows that our predictive model with a default decision threshold is already winning over the baseline in terms of profit and it would be already beneficial to use it to accept or reject transactions instead of accepting all transactions.

### Tuning the decision threshold[#](#tuning-the-decision-threshold "Link to this heading")

Now the question is: is our model optimum for the type of decision that we want to do? Up to now, we did not optimize the decision threshold. We use the [`TunedThresholdClassifierCV`](../../modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#sklearn.model_selection.TunedThresholdClassifierCV "sklearn.model_selection.TunedThresholdClassifierCV") to optimize the decision given our business scorer. To avoid a nested cross-validation, we will use the best estimator found during the previous grid-search.

```
 tuned_model = TunedThresholdClassifierCV(estimator = model. best_estimator_, scoring = business_scorer, thresholds = 100, n_jobs = 2,)
```

Since our business scorer requires the amount of each transaction, we need to pass this information in the `fit` method. The [`TunedThresholdClassifierCV`](../../modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#sklearn.model_selection.TunedThresholdClassifierCV "sklearn.model_selection.TunedThresholdClassifierCV") is in charge of automatically dispatching this metadata to the underlying scorer.

```
 tuned_model. fit(data_train, target_train, amount = amount_train)
```

```
TunedThresholdClassifierCV(estimator=Pipeline(steps=[('standardscaler', StandardScaler()), ('logisticregression', LogisticRegression(C=np.float64(100.0)))]), n_jobs=2, scoring=make_scorer(business_metric, response_method='predict'))
```

**In a Jupyter environment, please rerun this cell to show the HTML representation or trust the notebook.   
On GitHub, the HTML representation is unable to render, please try loading this page with nbviewer.org.**

Parameters

|  |  |
| --- | --- |
| [estimator estimator: estimator instance  The classifier, fitted or not, for which we want to optimize the decision threshold used during `predict`.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=estimator,-estimator%20instance) | Pipeline(step...t64(100.0)))]) |
| [scoring scoring: str or callable, default="balanced\_accuracy"  The objective metric to be optimized. Can be one of:  - str: string associated to a scoring function for binary classification,  see :ref:`scoring\_string\_names` for options. - callable: a scorer callable object (e.g., function) with signature  ``scorer(estimator, X, y)``. See :ref:`scoring\_callable` for details.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=scoring,-str%20or%20callable%2C%20default%3D%22balanced_accuracy%22) | make\_scorer(b...hod='predict') |
| [response\_method response\_method: {"auto", "decision\_function", "predict\_proba"}, default="auto"  Methods by the classifier `estimator` corresponding to the decision function for which we want to find a threshold. It can be:  \* if `"auto"`, it will try to invoke, for each classifier,  `"predict\_proba"` or `"decision\_function"` in that order. \* otherwise, one of `"predict\_proba"` or `"decision\_function"`.  If the method is not implemented by the classifier, it will raise an  error.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=response_method,-%7B%22auto%22%2C%20%22decision_function%22%2C%20%22predict_proba%22%7D%2C%20default%3D%22auto%22) | 'auto' |
| [thresholds thresholds: int or array-like, default=100  The number of decision threshold to use when discretizing the output of the classifier `method`. Pass an array-like to manually specify the thresholds to use.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=thresholds,-int%20or%20array-like%2C%20default%3D100) | 100 |
| [cv cv: int, float, cross-validation generator, iterable or "prefit", default=None  Determines the cross-validation splitting strategy to train classifier. Possible inputs for cv are:  \* `None`, to use the default 5-fold stratified K-fold cross validation; \* An integer number, to specify the number of folds in a stratified k-fold; \* A float number, to specify a single shuffle split. The floating number should  be in (0, 1) and represent the size of the validation set; \* An object to be used as a cross-validation generator; \* An iterable yielding train, test splits; \* `"prefit"`, to bypass the cross-validation.  Refer :ref:`User Guide ` for the various cross-validation strategies that can be used here.  .. warning::  Using `cv="prefit"` and passing the same dataset for fitting `estimator`  and tuning the cut-off point is subject to undesired overfitting. You can  refer to :ref:`TunedThresholdClassifierCV\_no\_cv` for an example.   This option should only be used when the set used to fit `estimator` is  different from the one used to tune the cut-off point (by calling  :meth:`TunedThresholdClassifierCV.fit`).](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=cv,-int%2C%20float%2C%20cross-validation%20generator%2C%20iterable%20or%20%22prefit%22%2C%20default%3DNone) | None |
| [refit refit: bool, default=True  Whether or not to refit the classifier on the entire training set once the decision threshold has been found. Note that forcing `refit=False` on cross-validation having more than a single split will raise an error. Similarly, `refit=True` in conjunction with `cv="prefit"` will raise an error.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=refit,-bool%2C%20default%3DTrue) | True |
| [n\_jobs n\_jobs: int, default=None  The number of jobs to run in parallel. When `cv` represents a cross-validation strategy, the fitting and scoring on each data split is done in parallel. ``None`` means 1 unless in a :obj:`joblib.parallel\_backend` context. ``-1`` means using all processors. See :term:`Glossary ` for more details.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=n_jobs,-int%2C%20default%3DNone) | 2 |
| [random\_state random\_state: int, RandomState instance or None, default=None  Controls the randomness of cross-validation when `cv` is a float. See :term:`Glossary `.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=random_state,-int%2C%20RandomState%20instance%20or%20None%2C%20default%3DNone) | None |
| [store\_cv\_results store\_cv\_results: bool, default=False  Whether to store all scores and thresholds computed during the cross-validation process.](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#:~:text=store_cv_results,-bool%2C%20default%3DFalse) | False |

Parameters

|  |  |
| --- | --- |
| [copy copy: bool, default=True  If False, try to avoid a copy and do inplace scaling instead. This is not guaranteed to always work inplace; e.g. if the data is not a NumPy array or scipy.sparse CSR matrix, a copy may still be returned.](https://scikit-learn.org/1.8/modules/generated/sklearn.preprocessing.StandardScaler.html#:~:text=copy,-bool%2C%20default%3DTrue) | True |
| [with\_mean with\_mean: bool, default=True  If True, center the data before scaling. This does not work (and will raise an exception) when attempted on sparse matrices, because centering them entails building a dense matrix which in common use cases is likely to be too large to fit in memory.](https://scikit-learn.org/1.8/modules/generated/sklearn.preprocessing.StandardScaler.html#:~:text=with_mean,-bool%2C%20default%3DTrue) | True |
| [with\_std with\_std: bool, default=True  If True, scale the data to unit variance (or equivalently, unit standard deviation).](https://scikit-learn.org/1.8/modules/generated/sklearn.preprocessing.StandardScaler.html#:~:text=with_std,-bool%2C%20default%3DTrue) | True |

Parameters

|  |  |
| --- | --- |
| [penalty penalty: {'l1', 'l2', 'elasticnet', None}, default='l2'  Specify the norm of the penalty:  - `None`: no penalty is added; - `'l2'`: add a L2 penalty term and it is the default choice; - `'l1'`: add a L1 penalty term; - `'elasticnet'`: both L1 and L2 penalty terms are added.  .. warning::  Some penalties may not work with some solvers. See the parameter  `solver` below, to know the compatibility between the penalty and  solver.  .. versionadded:: 0.19  l1 penalty with SAGA solver (allowing 'multinomial' + L1)  .. deprecated:: 1.8  `penalty` was deprecated in version 1.8 and will be removed in 1.10.  Use `l1\_ratio` instead. `l1\_ratio=0` for `penalty='l2'`, `l1\_ratio=1` for  `penalty='l1'` and `l1\_ratio` set to any float between 0 and 1 for  `'penalty='elasticnet'`.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=penalty,-%7B%27l1%27%2C%20%27l2%27%2C%20%27elasticnet%27%2C%20None%7D%2C%20default%3D%27l2%27) | 'deprecated' |
| [C C: float, default=1.0  Inverse of regularization strength; must be a positive float. Like in support vector machines, smaller values specify stronger regularization. `C=np.inf` results in unpenalized logistic regression. For a visual example on the effect of tuning the `C` parameter with an L1 penalty, see: :ref:`sphx\_glr\_auto\_examples\_linear\_model\_plot\_logistic\_path.py`.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=C,-float%2C%20default%3D1.0) | np.float64(100.0) |
| [l1\_ratio l1\_ratio: float, default=0.0  The Elastic-Net mixing parameter, with `0 <= l1\_ratio <= 1`. Setting `l1\_ratio=1` gives a pure L1-penalty, setting `l1\_ratio=0` a pure L2-penalty. Any value between 0 and 1 gives an Elastic-Net penalty of the form `l1\_ratio \* L1 + (1 - l1\_ratio) \* L2`.  .. warning::  Certain values of `l1\_ratio`, i.e. some penalties, may not work with some  solvers. See the parameter `solver` below, to know the compatibility between  the penalty and solver.  .. versionchanged:: 1.8  Default value changed from None to 0.0.  .. deprecated:: 1.8  `None` is deprecated and will be removed in version 1.10. Always use  `l1\_ratio` to specify the penalty type.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=l1_ratio,-float%2C%20default%3D0.0) | 0.0 |
| [dual dual: bool, default=False  Dual (constrained) or primal (regularized, see also :ref:`this equation `) formulation. Dual formulation is only implemented for l2 penalty with liblinear solver. Prefer `dual=False` when n\_samples > n\_features.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=dual,-bool%2C%20default%3DFalse) | False |
| [tol tol: float, default=1e-4  Tolerance for stopping criteria.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=tol,-float%2C%20default%3D1e-4) | 0.0001 |
| [fit\_intercept fit\_intercept: bool, default=True  Specifies if a constant (a.k.a. bias or intercept) should be added to the decision function.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=fit_intercept,-bool%2C%20default%3DTrue) | True |
| [intercept\_scaling intercept\_scaling: float, default=1  Useful only when the solver `liblinear` is used and `self.fit\_intercept` is set to `True`. In this case, `x` becomes `[x, self.intercept\_scaling]`, i.e. a "synthetic" feature with constant value equal to `intercept\_scaling` is appended to the instance vector. The intercept becomes ``intercept\_scaling \* synthetic\_feature\_weight``.  .. note::  The synthetic feature weight is subject to L1 or L2  regularization as all other features.  To lessen the effect of regularization on synthetic feature weight  (and therefore on the intercept) `intercept\_scaling` has to be increased.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=intercept_scaling,-float%2C%20default%3D1) | 1 |
| [class\_weight class\_weight: dict or 'balanced', default=None  Weights associated with classes in the form ``{class\_label: weight}``. If not given, all classes are supposed to have weight one.  The "balanced" mode uses the values of y to automatically adjust weights inversely proportional to class frequencies in the input data as ``n\_samples / (n\_classes \* np.bincount(y))``.  Note that these weights will be multiplied with sample\_weight (passed through the fit method) if sample\_weight is specified.  .. versionadded:: 0.17  \*class\_weight='balanced'\*](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=class_weight,-dict%20or%20%27balanced%27%2C%20default%3DNone) | None |
| [random\_state random\_state: int, RandomState instance, default=None  Used when ``solver`` == 'sag', 'saga' or 'liblinear' to shuffle the data. See :term:`Glossary ` for details.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=random_state,-int%2C%20RandomState%20instance%2C%20default%3DNone) | None |
| [solver solver: {'lbfgs', 'liblinear', 'newton-cg', 'newton-cholesky', 'sag', 'saga'}, default='lbfgs'  Algorithm to use in the optimization problem. Default is 'lbfgs'. To choose a solver, you might want to consider the following aspects:  - 'lbfgs' is a good default solver because it works reasonably well for a wide  class of problems. - For :term:`multiclass` problems (`n\_classes >= 3`), all solvers except  'liblinear' minimize the full multinomial loss, 'liblinear' will raise an  error. - 'newton-cholesky' is a good choice for  `n\_samples` >> `n\_features \* n\_classes`, especially with one-hot encoded  categorical features with rare categories. Be aware that the memory usage  of this solver has a quadratic dependency on `n\_features \* n\_classes`  because it explicitly computes the full Hessian matrix. - For small datasets, 'liblinear' is a good choice, whereas 'sag'  and 'saga' are faster for large ones; - 'liblinear' can only handle binary classification by default. To apply a  one-versus-rest scheme for the multiclass setting one can wrap it with the  :class:`~sklearn.multiclass.OneVsRestClassifier`.  .. warning::  The choice of the algorithm depends on the penalty chosen (`l1\_ratio=0`  for L2-penalty, `l1\_ratio=1` for L1-penalty and `0 < l1\_ratio < 1` for  Elastic-Net) and on (multinomial) multiclass support:   ================= ======================== ======================  solver l1\_ratio multinomial multiclass  ================= ======================== ======================  'lbfgs' l1\_ratio=0 yes  'liblinear' l1\_ratio=1 or l1\_ratio=0 no  'newton-cg' l1\_ratio=0 yes  'newton-cholesky' l1\_ratio=0 yes  'sag' l1\_ratio=0 yes  'saga' 0<=l1\_ratio<=1 yes  ================= ======================== ======================  .. note::  'sag' and 'saga' fast convergence is only guaranteed on features  with approximately the same scale. You can preprocess the data with  a scaler from :mod:`sklearn.preprocessing`.  .. seealso::  Refer to the :ref:`User Guide ` for more  information regarding :class:`LogisticRegression` and more specifically the  :ref:`Table `  summarizing solver/penalty supports.  .. versionadded:: 0.17  Stochastic Average Gradient (SAG) descent solver. Multinomial support in  version 0.18. .. versionadded:: 0.19  SAGA solver. .. versionchanged:: 0.22  The default solver changed from 'liblinear' to 'lbfgs' in 0.22. .. versionadded:: 1.2  newton-cholesky solver. Multinomial support in version 1.6.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=solver,-%7B%27lbfgs%27%2C%20%27liblinear%27%2C%20%27newton-cg%27%2C%20%27newton-cholesky%27%2C%20%27sag%27%2C%20%27saga%27%7D%2C%20%20%20%20%20%20%20%20%20%20%20%20%20default%3D%27lbfgs%27) | 'lbfgs' |
| [max\_iter max\_iter: int, default=100  Maximum number of iterations taken for the solvers to converge.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=max_iter,-int%2C%20default%3D100) | 100 |
| [verbose verbose: int, default=0  For the liblinear and lbfgs solvers set verbose to any positive number for verbosity.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=verbose,-int%2C%20default%3D0) | 0 |
| [warm\_start warm\_start: bool, default=False  When set to True, reuse the solution of the previous call to fit as initialization, otherwise, just erase the previous solution. Useless for liblinear solver. See :term:`the Glossary `.  .. versionadded:: 0.17  \*warm\_start\* to support \*lbfgs\*, \*newton-cg\*, \*sag\*, \*saga\* solvers.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=warm_start,-bool%2C%20default%3DFalse) | False |
| [n\_jobs n\_jobs: int, default=None  Does not have any effect.  .. deprecated:: 1.8  `n\_jobs` is deprecated in version 1.8 and will be removed in 1.10.](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html#:~:text=n_jobs,-int%2C%20default%3DNone) | None |

  
   

We observe that the tuned decision threshold is far away from the default 0.5:

```
 print(f"Tuned decision threshold: {tuned_model. best_threshold_:.2f} ")
```

```
 print("Benefit of logistic regression with a tuned threshold: " f "{business_scorer(tuned_model,  data_test,  target_test,  amount = amount_test):,.2f} €")
```

We observe that tuning the decision threshold increases the expected profit when deploying our model - as indicated by the business metric. It is therefore valuable, whenever possible, to optimize the decision threshold with respect to the business metric.

### Manually setting the decision threshold instead of tuning it[#](#manually-setting-the-decision-threshold-instead-of-tuning-it "Link to this heading")

In the previous example, we used the [`TunedThresholdClassifierCV`](../../modules/generated/sklearn.model_selection.TunedThresholdClassifierCV.html#sklearn.model_selection.TunedThresholdClassifierCV "sklearn.model_selection.TunedThresholdClassifierCV") to find the optimal decision threshold. However, in some cases, we might have some prior knowledge about the problem at hand and we might be happy to set the decision threshold manually.

The class [`FixedThresholdClassifier`](../../modules/generated/sklearn.model_selection.FixedThresholdClassifier.html#sklearn.model_selection.FixedThresholdClassifier "sklearn.model_selection.FixedThresholdClassifier") allows us to manually set the decision threshold. At prediction time, it behave as the previous tuned model but no search is performed during the fitting process. Note that here we use [`FrozenEstimator`](../../modules/generated/sklearn.frozen.FrozenEstimator.html#sklearn.frozen.FrozenEstimator "sklearn.frozen.FrozenEstimator") to wrap the predictive model to avoid any refitting.

Here, we will reuse the decision threshold found in the previous section to create a new model and check that it gives the same results.

```
 from  sklearn.frozen  import FrozenEstimator from  sklearn.model_selection  import FixedThresholdClassifier model_fixed_threshold = FixedThresholdClassifier(estimator = FrozenEstimator(model), threshold = tuned_model. best_threshold_)
```

```
 business_score = business_scorer(model_fixed_threshold, data_test, target_test, amount = amount_test) print(f"Benefit of logistic regression with a tuned threshold: {business_score:,.2f} €")
```

We observe that we obtained the exact same results but the fitting process was much faster since we did not perform any hyper-parameter search.

Finally, the estimate of the (average) business metric itself can be unreliable, in particular when the number of data points in the minority class is very small. Any business impact estimated by cross-validation of a business metric on historical data (offline evaluation) should ideally be confirmed by A/B testing on live data (online evaluation). Note however that A/B testing models is beyond the scope of the scikit-learn library itself.

At the end, we disable the configuration flag for metadata routing:

```
.. GENERATED FROM PYTHON SOURCE LINES 694 - 695
```

```
 sklearn. set_config(enable_metadata_routing = False)
```

**Total running time of the script:** (0 minutes 35.825 seconds)

[![Launch binder](../../_images/binder_badge_logo22.svg)](https://mybinder.org/v2/gh/scikit-learn/scikit-learn/1.8.X?urlpath=lab/tree/notebooks/auto_examples/model_selection/plot_cost_sensitive_learning.ipynb)

[![Launch JupyterLite](../../_images/jupyterlite_badge_logo22.svg)](../../lite/lab/index.html?path=auto_examples/model_selection/plot_cost_sensitive_learning.ipynb)

[`Download Jupyternotebook:plot_cost_sensitive_learning.ipynb`](../../_downloads/133f2198d3ab792c75b39a63b0a99872/plot_cost_sensitive_learning.ipynb)

[`Download Python sourcecode:plot_cost_sensitive_learning.py`](../../_downloads/9ca7cbe47e4cace7242fe4c5c43dfa52/plot_cost_sensitive_learning.py)

Related examples

![](../../_images/sphx_glr_plot_tuned_decision_threshold_thumb.png)

[Post-hoc tuning the cut-off point of decision function](plot_tuned_decision_threshold.html)

Post-hoc tuning the cut-off point of decision function

![](../../_images/sphx_glr_plot_release_highlights_1_5_0_thumb.png)

[Release Highlights for scikit-learn 1.5](../release_highlights/plot_release_highlights_1_5_0.html)

Release Highlights for scikit-learn 1.5

![](../../_images/sphx_glr_plot_precision_recall_thumb.png)

Precision-Recall

![](../../_images/sphx_glr_plot_grid_search_digits_thumb.png)

[Custom refit strategy of a grid search with cross-validation](plot_grid_search_digits.html)

Custom refit strategy of a grid search with cross-validation

[Gallery generated by Sphinx-Gallery](https://sphinx-gallery.github.io)

On this page

### This Page

* [Show Source](../../_sources/auto_examples/model_selection/plot_cost_sensitive_learning.rst.txt)

[Download source code](../../_downloads/9ca7cbe47e4cace7242fe4c5c43dfa52/plot_cost_sensitive_learning.py)

[Download Jupyter notebook](../../_downloads/133f2198d3ab792c75b39a63b0a99872/plot_cost_sensitive_learning.ipynb)

[Download zipped](../../_downloads/c75a28fb9c5813c4fe15345695d1bdcf/plot_cost_sensitive_learning.zip)

[![Launch JupyterLite](../../_images/jupyterlite_badge_logo22.svg)](../../lite/lab/index.html?path=auto_examples/model_selection/plot_cost_sensitive_learning.ipynb)

[![Launch binder](../../_images/binder_badge_logo22.svg)](https://mybinder.org/v2/gh/scikit-learn/scikit-learn/1.8.X?urlpath=lab/tree/notebooks/auto_examples/model_selection/plot_cost_sensitive_learning.ipynb)

 
