![](/static/images/icons/enwiki-25.svg)
![Wikipedia](/static/images/mobile/copyright/wikipedia-wordmark-en-25.svg)
![The Free Encyclopedia](/static/images/mobile/copyright/wikipedia-tagline-en-25.svg)

## Contents

# Purged cross-validation

|  |  |
| --- | --- |
|  | **A major contributor to this article appears to have a [close connection](/wiki/Wikipedia:Conflict_of_interest "Wikipedia:Conflict of interest") with its subject.** It may require cleanup to comply with Wikipedia's content policies, particularly [neutral point of view](/wiki/Wikipedia:Neutral_point_of_view "Wikipedia:Neutral point of view"). Please discuss further on the [talk page](/wiki/Talk:Purged_cross-validation "Talk:Purged cross-validation").  See our [advice if the article is about you](/wiki/Wikipedia:About_you "Wikipedia:About you") and read our [scam warning](/wiki/Wikipedia:Scam_warning "Wikipedia:Scam warning") in case someone asks for money to edit this article. *(December 2025)* *([Learn how and when to remove this message](/wiki/Help:Maintenance_template_removal "Help:Maintenance template removal"))* |

![](//upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Unbalanced_scales.svg/60px-Unbalanced_scales.svg.png)

**Purged cross-validation** is a variant of *k*-fold [cross-validation](/wiki/Cross-validation_(statistics) "Cross-validation (statistics)") designed to prevent look-ahead bias in time series and other structured data, developed in 2017 by Marcos López de Prado at [Guggenheim Partners](/wiki/Guggenheim_Partners "Guggenheim Partners") and [Cornell University](/wiki/Cornell_University "Cornell University").[[1]](#cite_note-1) It is primarily used in financial [machine learning](/wiki/Machine_learning "Machine learning") to ensure the independence of training and testing samples when labels depend on future events. It provides an alternative to conventional cross-validation and walk-forward [backtesting](/wiki/Backtesting "Backtesting") methods, which often yield overly optimistic performance estimates due to information leakage and [overfitting](/wiki/Overfitting "Overfitting").[[2]](#cite_note-JPM-2)[[3]](#cite_note-JCF-3)

## Motivation

Standard cross-validation assumes that observations are independently and identically distributed (IID), which often does not hold in time series or financial datasets. If the label of a test sample overlaps in time with the features or labels in the training set, the result may be [data leakage](/wiki/Data_leakage "Data leakage") and overfitting. Purged cross-validation addresses this issue by removing overlapping observations and, optionally, adding a temporal buffer ("embargo") around the test set to further reduce the risk of leakage.[[4]](#cite_note-The10-4)[[3]](#cite_note-JCF-3)[[5]](#cite_note-5)[[6]](#cite_note-Cambridge-6)

The figure below illustrates standard 5 Fold Cross-Validation[[7]](#cite_note-7)

![Visualization of KFold Cross-Validation](//upload.wikimedia.org/wikipedia/commons/thumb/c/c9/KFold_Cross-Validation.png/500px-KFold_Cross-Validation.png)

## Purging

Purging removes from the training set any observation whose timestamp falls within the time range of formation of a label in the test set. This can be the case for train set observations before and after the test set. Their removal ensures that the algorithm cannot learn during train time information that will be used to assess the performance of the algorithm. See the figure below for an illustration of purging.[[8]](#cite_note-AFML-8)

![Purging Overlapping Samples in Finance](//upload.wikimedia.org/wikipedia/commons/thumb/3/33/Purging_Overlapping_Samples_in_Finance.png/500px-Purging_Overlapping_Samples_in_Finance.png)

## Embargoing

Embargoing addresses a more subtle form of leakage: even if an observation does not directly overlap the test set, it may still be affected by test events due to market reaction lag or downstream dependencies. To guard against this, a percentage-based embargo is imposed after each test fold. For example, with a 5% embargo and 1000 observations, the 50 observations following each test fold are excluded from training.

Unlike purging, embargoing can only occur *after* the test set. The figure below illustrates the application of embargo:[[8]](#cite_note-AFML-8)

![Embargo of post-test train observations](//upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Embargo_of_post-test_train_observations.png/500px-Embargo_of_post-test_train_observations.png)

## Applications

Purged and embargoed cross-validation has been useful in:

## Example

To illustrate the effect of purging and embargoing, consider the figures below. Both diagrams show the structure of 5-fold cross-validation over a 20-day period. In each row, blue squares indicate training samples and red squares denote test samples. Each label is defined based on the value of the next two observations, hence creating an overlap. If this overlap is left untreated, test set information leaks into the train set.

![](//upload.wikimedia.org/wikipedia/en/thumb/f/f0/KFCV.png/960px-KFCV.png)

The second figure applies the Purged CV procedure. Notice how purging removes overlapping observations from the training set and the embargo widens the gap between test and training data. This approach ensures that the evaluation more closely resembles a true out-of-sample test and reduces the risk of backtest overfitting.

![](//upload.wikimedia.org/wikipedia/en/thumb/3/38/CPCV.png/960px-CPCV.png)

## Combinatorial Purged Cross-Validation

Walk-forward [backtesting](/wiki/Backtesting "Backtesting") analysis, another common cross-validation technique in finance, preserves temporal order but evaluates the model on a single sequence of test sets. This leads to high variance in performance estimation, as results are contingent on a specific historical path.[[2]](#cite_note-JPM-2)

Combinatorial Purged Cross-Validation (CPCV) addresses this limitation by systematically constructing multiple train-test splits, purging overlapping samples, and enforcing an embargo period to prevent information leakage. The result is a distribution of out-of-sample performance estimates, enabling robust statistical inference and more realistic assessment of a model's predictive power.[[8]](#cite_note-AFML-8)

### Methodology

CPCV divides a time-series dataset into *N* sequential, non-overlapping groups. These groups preserve the temporal order of observations. Then, all combinations of *k* groups (where *k < N*) are selected as test sets, with the remaining *N − k* groups used for training. For each combination, the model is trained and evaluated under strict controls to prevent leakage.[[8]](#cite_note-AFML-8)

To eliminate potential contamination between training and test sets, CPCV introduces two additional mechanisms:

Each data point appears in multiple test sets across different combinations. Because test groups are drawn combinatorially, this process produces multiple backtest "paths," each of which simulates a plausible market scenario. From these paths, practitioners can compute a distribution of performance statistics such as the [Sharpe ratio](/wiki/Sharpe_ratio "Sharpe ratio"), [drawdown](/wiki/Drawdown "Drawdown"), or classification accuracy.

### Formal definition

Let *N* be the number of sequential groups into which the dataset is divided, and let *k* be the number of groups selected as the test set for each split. Then:

![{\displaystyle {\binom {N}{k}}}](https://wikimedia.org/api/rest_v1/media/math/render/svg/3c26606aa34e6988cead40d7adfbf706827a42a6)
![{\displaystyle k}](https://wikimedia.org/api/rest_v1/media/math/render/svg/c3c9a2c7b599b37105512c5d570edc034056dd40)
![{\displaystyle \varphi [N,k]}](https://wikimedia.org/api/rest_v1/media/math/render/svg/97dff09e23496784945d0da0c54922545b3dbada)
![{\displaystyle \varphi [N,k]={\frac {k}{N}}{\binom {N}{k}}}](https://wikimedia.org/api/rest_v1/media/math/render/svg/916aba1000f1d187f9b7cb3a5b12ac791d49176d)

This yields a distribution of performance metrics rather than a single point estimate, making it possible to apply [Monte Carlo-based](/wiki/Monte_Carlo_method "Monte Carlo method") or probabilistic techniques to assess model robustness.

### Illustrative example

Consider the case where *N = 6* and *k = 2*. The number of possible test set combinations is






(

6
2

)
=
15
{\displaystyle {\binom {6}{2}}=15}
![{\displaystyle {\binom {6}{2}}=15}](https://wikimedia.org/api/rest_v1/media/math/render/svg/200454cd65cb81e71e211242e93d1d4e78bf5f4a). Each of the six groups appears in five test splits. Consequently, five distinct backtest paths can be constructed, each incorporating one appearance from every group.

![{\displaystyle {\binom {6}{2}}=15}](https://wikimedia.org/api/rest_v1/media/math/render/svg/200454cd65cb81e71e211242e93d1d4e78bf5f4a)

#### Test group assignment matrix

This table shows the 15 test combinations. An "x" indicates that the corresponding group is included in the test set for that split.

Paths generated for *N = 6*, *k = 2*

| Group | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 | S11 | S12 | S13 | S14 | S15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | x | x | x | x | x |  |  |  |  |  |  |  |  |  |  |
| G2 | x |  |  |  |  | x | x | x | x |  |  |  |  |  |  |
| G3 |  | x |  |  |  | x |  |  |  | x | x | x |  |  |  |
| G4 |  |  | x |  |  |  | x |  |  | x |  |  | x | x |  |
| G5 |  |  |  | x |  |  |  | x |  |  | x |  | x |  | x |
| G6 |  |  |  |  | x |  |  |  | x |  |  | x |  | x | x |

#### Backtest path assignment

Each group contributes to five different backtest paths. The number in each cell indicates the path to which the group's result is assigned for that split.

Path assignments for each group

| Group | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 | S11 | S12 | S13 | S14 | S15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 1 | 2 | 3 | 4 | 5 |  |  |  |  |  |  |  |  |  |  |
| G2 | 1 |  |  |  |  | 2 | 3 | 4 | 5 |  |  |  |  |  |  |
| G3 |  | 1 |  |  |  | 2 |  |  |  | 3 | 4 | 5 |  |  |  |
| G4 |  |  | 1 |  |  |  | 2 |  |  | 3 |  |  | 4 | 5 |  |
| G5 |  |  |  | 1 |  |  |  | 2 |  |  | 3 |  | 4 |  | 5 |
| G6 |  |  |  |  | 1 |  |  |  | 2 |  |  | 3 |  | 4 | 5 |

### Advantages

Combinatorial Purged Cross-Validation offers several key benefits over conventional methods:

CPCV is commonly used in quantitative strategy research, especially for evaluating predictive models such as classifiers, regressors, and portfolio optimizers.[[4]](#cite_note-The10-4) It has been applied to estimate realistic Sharpe ratios, assess the risk of overfitting, and support the use of statistical tools such as the [Deflated Sharpe Ratio](/wiki/Deflated_Sharpe_Ratio "Deflated Sharpe Ratio") (DSR).[[10]](#cite_note-Factor-10)[[6]](#cite_note-Cambridge-6)

### Limitations

The main limitation of CPCV stems from its high computational cost. However, this cost can be managed by sampling a finite number of splits from the space of all possible combinations.

## See also

## References

![](https://en.wikipedia.org/wiki/Special:CentralAutoLogin/start?useformat=desktop&type=1x1&usesul3=1)
![Wikimedia Foundation](/static/images/footer/wikimedia.svg)
![Powered by MediaWiki](/w/resources/assets/mediawiki_compact.svg)
