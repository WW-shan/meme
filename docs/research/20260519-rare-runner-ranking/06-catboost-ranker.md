# CatBoostRanker

* [Purpose](en/concepts/python-reference_catboostranker#purpose)
* [Parameters](en/concepts/python-reference_catboostranker#parameters)
  + [metadata](en/concepts/python-reference_catboostranker#metadata)
  + [cat\_features](en/concepts/python-reference_catboostranker#cat_features)
* [Attributes](en/concepts/python-reference_catboostranker#attributes)
  + [tree\_count\_](en/concepts/python-reference_catboostranker#tree_count_)
  + [feature\_importances\_](en/concepts/python-reference_catboostranker#feature_importances_)
  + [random\_seed\_](en/concepts/python-reference_catboostranker#random_seed_)
  + [learning\_rate\_](en/concepts/python-reference_catboostranker#learning_rate_)
  + [feature\_names\_](en/concepts/python-reference_catboostranker#feature_names_)
  + [evals\_result\_](en/concepts/python-reference_catboostranker#evals_result_)
  + [best\_score\_](en/concepts/python-reference_catboostranker#best_score_)
  + [best\_iteration\_](en/concepts/python-reference_catboostranker#best_iteration_)
* [Methods](en/concepts/python-reference_catboostranker#methods)
  + [fit](en/concepts/python-reference_catboostranker#fit)
  + [predict](en/concepts/python-reference_catboostranker#predict)
  + [calc\_leaf\_indexes](en/concepts/python-reference_catboostranker#calc_leaf_indexes)
  + [calc\_feature\_statistics](en/concepts/python-reference_catboostranker#calc_feature_statistics)
  + [copy](en/concepts/python-reference_catboostranker#copy)
  + [compare](en/concepts/python-reference_catboostranker#compare)
  + [eval\_metrics](en/concepts/python-reference_catboostranker#eval_metrics)
  + [get\_all\_params](en/concepts/python-reference_catboostranker#get_all_params)
  + [get\_best\_iteration](en/concepts/python-reference_catboostranker#get_best_iteration)
  + [get\_best\_score](en/concepts/python-reference_catboostranker#get_best_score)
  + [get\_borders](en/concepts/python-reference_catboostranker#get_borders)
  + [get\_evals\_result](en/concepts/python-reference_catboostranker#get_evals_result)
  + [get\_feature\_importance](en/concepts/python-reference_catboostranker#get_feature_importance)
  + [get\_metadata](en/concepts/python-reference_catboostranker#get_metadata)
  + [get\_object\_importance](en/concepts/python-reference_catboostranker#get_object_importance)
  + [get\_param](en/concepts/python-reference_catboostranker#get_param)
  + [get\_params](en/concepts/python-reference_catboostranker#get_params)
  + [get\_scale\_and\_bias](en/concepts/python-reference_catboostranker#get_scale_and_bias)
  + [get\_test\_eval](en/concepts/python-reference_catboostranker#get_test_eval)
  + [grid\_search](en/concepts/python-reference_catboostranker#grid_search)
  + [is\_fitted](en/concepts/python-reference_catboostranker#is_fitted)
  + [load\_model](en/concepts/python-reference_catboostranker#load_model)
  + [plot\_predictions](en/concepts/python-reference_catboostranker#plot_predictions)
  + [plot\_tree](en/concepts/python-reference_catboostranker#plot_tree)
  + [randomized\_search](en/concepts/python-reference_catboostranker#randomized_search)
  + [save\_borders](en/concepts/python-reference_catboostranker#save_borders)
  + [save\_model](en/concepts/python-reference_catboostranker#save_model)
  + [score](en/concepts/python-reference_catboostranker#score)
  + [select\_features](en/concepts/python-reference_catboostranker#select_features)
  + [set\_feature\_names](en/concepts/python-reference_catboostranker#set_feature_names)
  + [set\_params](en/concepts/python-reference_catboostranker#set_params)
  + [set\_scale\_and\_bias](en/concepts/python-reference_catboostranker#set_scale_and_bias)
  + [shrink](en/concepts/python-reference_catboostranker#shrink)
  + [staged\_predict](en/concepts/python-reference_catboostranker#staged_predict)

```
class CatBoostRanker None None None None None None 'YetiRank' None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None None
```

## Purpose

Implementation of [the scikit-learn estimator API](https://scikit-learn.org/stable/developers/develop.html) for CatBoost ranking.

Supports model training, inference and auxiliary calculations like feature importance.

## Parameters

### metadata

#### Description

The key-value string pairs to store in the model's metadata storage after the training.

**Default value**

None

### cat\_features

#### Description

A one-dimensional array of categorical columns indices (specified as integers) or names (specified as strings).

This array can contain both indices and names for different elements.

If any features in the `cat_features` parameter are specified as names instead of indices, feature names must be provided for the training dataset. Therefore, the type of the `X` parameter in the future calls of the `fit` function must be either [catboost.Pool](en/concepts/python-reference_pool) with defined feature names data or pandas.DataFrame or [polars.DataFrame](https://docs.pola.rs/api/python/stable/reference/dataframe/index.html).

Note

* If this parameter is not None and the training dataset passed as the value of the X parameter to the fit function of this class has the [catboost.Pool](en/concepts/python-reference_pool) type, CatBoost checks the equivalence of the categorical features indices specification in this object and the one in the [catboost.Pool](en/concepts/python-reference_pool) object.
* If this parameter is not None, passing objects of the [catboost.FeaturesData](en/concepts/python-features-data__desc) type as the X parameter to the fit function of this class is prohibited.

**Default value**

None (all features are either considered numerical or of other types if specified precisely)

See [Python package training parameters](en/references/training-parameters/) for the full list of parameters.

Note

Some parameters duplicate the ones specified for the [fit](en/concepts/python-reference_catboostranker_fit) method. In these cases the values specified for the [fit](en/concepts/python-reference_catboostranker_fit) method take precedence.

## Attributes

### tree\_count\_

Return the number of trees in the model.

This number can differ from the value specified in the `--iterations` training parameter in the following cases:

* The training is stopped by the [overfitting detector](en/concepts/overfitting-detector).
* The `--use-best-model` training parameter is set to True.

### feature\_importances\_

Return the calculated [feature importances](en/concepts/fstr). The output data depends on the type of the model's loss function:

* Non-ranking loss functions — [PredictionValuesChange](en/concepts/fstr#regular-feature-importance)
* Ranking loss functions — [LossFunctionChange](en/concepts/fstr#regular-feature-importances__lossfunctionchange)

### random\_seed\_

The random seed used for training.

### learning\_rate\_

The learning rate used for training.

### feature\_names\_

The names of features in the dataset.

### evals\_result\_

Return the values of metrics calculated during the training.

### best\_score\_

Return the best result for each metric calculated on each validation dataset.

### best\_iteration\_

Return the identifier of the iteration with the best result of the evaluation metric or loss function on the last validation set.

## Methods

### [fit](en/concepts/python-reference_catboostranker_fit)

Train a model.

### [predict](en/concepts/python-reference_catboostranker_predict)

Apply the model to the given dataset.

### [calc\_leaf\_indexes](en/concepts/python-reference_catboostranker_calc_leaf_indexes)

Returns indexes of leafs to which objects from pool are mapped by model trees.

### [calc\_feature\_statistics](en/concepts/python-reference_catboostranker_calc_feature_statistics)

Calculate and plot a set of statistics for the chosen feature.

### [copy](en/concepts/python-reference_catboostranker_copy)

Copy the CatBoost object.

### [compare](en/concepts/python-reference_catboostranker_modelcompare)

Draw train and evaluation metrics in [Jupyter Notebook](en/features/visualization_jupyter-notebook) for two trained models.

### [eval\_metrics](en/concepts/python-reference_catboostranker_eval-metrics)

Calculate the specified metrics for the specified dataset.

### [get\_all\_params](en/concepts/python-reference_catboostranker_get_all_params)

Return the values of all training parameters (including the ones that are not explicitly specified by users).

### [get\_best\_iteration](en/concepts/python-reference_catboostranker_get_best_iteration)

Return the identifier of the iteration with the best result of the evaluation metric or loss function on the last validation set.

### [get\_best\_score](en/concepts/python-reference_catboostranker_get_best_score)

Return the best result for each metric calculated on each validation dataset.

### [get\_borders](en/concepts/python-reference_catboostranker_get_borders)

Return the list of borders for numerical features.

### [get\_evals\_result](en/concepts/python-reference_catboostranker_get_evals_result)

Return the values of metrics calculated during the training.

### [get\_feature\_importance](en/concepts/python-reference_catboostranker_get_feature_importance)

Calculate and return the [feature importances](en/concepts/fstr).

### [get\_metadata](en/concepts/python-reference_catboostranker_metadata)

Return a proxy object with metadata from the model's internal key-value string storage.

### [get\_object\_importance](en/concepts/python-reference_catboostranker_get_object_importance)

Calculate the effect of objects from the train dataset on the optimized metric values for the objects from the input dataset:

* Positive values reflect that the optimized metric increases.
* Negative values reflect that the optimized metric decreases.

### [get\_param](en/concepts/python-reference_catboostranker_get_param)

Return the value of the given parameter if it is explicitly by the user before starting the training. If this parameter is used with the default value, this function returns None.

### [get\_params](en/concepts/python-reference_catboostranker_get_params)

Return the values of training parameters that are explicitly specified by the user. If all parameters are used with their default values, this function returns an empty dict.

### [get\_scale\_and\_bias](en/concepts/python-reference_catboostranker_get_scale_and_bias)

Return the scale and bias of the model.

These values affect the results of applying the model, since the model prediction results are calculated as follows:
 ∑leaf\_values⋅scale+bias

### [get\_test\_eval](en/concepts/python-reference_catboostranker_get_test_eval)

Return the formula values that were calculated for the objects from the validation dataset provided for training.

### [grid\_search](en/concepts/python-reference_catboostranker_grid_search)

A simple grid search over specified parameter values for a model.

### [is\_fitted](en/concepts/python-reference_catboostranker_is_fitted)

Check whether the model is trained.

### [load\_model](en/concepts/python-reference_catboostranker_load_model)

Load the model from a file.

### [plot\_predictions](en/concepts/python-reference_catboostranker_plot_predictions)

Sequentially vary the value of the specified features to put them into all buckets and calculate predictions for the input objects accordingly.

### [plot\_tree](en/concepts/python-reference_catboostranker_plot_tree)

Visualize the CatBoost decision trees.

### [randomized\_search](en/concepts/python-reference_catboostranker_randomized_search)

A simple randomized search on hyperparameters.

### [save\_borders](en/concepts/python-reference_catboostranker_save_borders)

Save the model borders to a file.

### [save\_model](en/concepts/python-reference_catboostranker_save_model)

Save the model to a file.

### [score](en/concepts/python-reference_catboostranker_score)

Calculate the R2 [metric](en/concepts/loss-functions) for the objects in the given dataset.

### [select\_features](en/concepts/python-reference_catboostranker_select_features)

Select the best features from the dataset using the [Recursive Feature Elimination](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.RFE.html) algorithm.

### [set\_feature\_names](en/concepts/python-reference_catboostranker_set_feature_names)

Set names for all features in the model.

### [set\_params](en/concepts/python-reference_catboostranker_set_params)

Set the training parameters.

### [set\_scale\_and\_bias](en/concepts/python-reference_catboostranker_set_scale_and_bias)

Set the scale and bias.

### [shrink](en/concepts/python-reference_catboostranker_shrink)

Shrink the model. Only trees with indices from the range `[ntree_start, ntree_end)` are kept.

### [staged\_predict](en/concepts/python-reference_catboostranker_staged_predict)

Apply the model to the given dataset and calculate the results taking into consideration only the trees in the range [0; i).

### Was the article helpful?

[fit](en/concepts/python-reference_catboostranker_fit)
