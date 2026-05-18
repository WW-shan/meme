##### Report GitHub Issue

Content selection saved. Describe the issue below:

![arXiv logo](/static/browse/0.3.4/images/arxiv-logo-one-color-white.svg)

# A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification

###### Abstract

Black-box machine learning models are now routinely used in high-risk settings, like medical diagnostics, which demand uncertainty quantification to avoid consequential model failures.
Conformal prediction (a.k.a. conformal inference) is a user-friendly paradigm for creating statistically rigorous uncertainty sets/intervals for the predictions of such models.
Critically, the sets are valid in a *distribution-free* sense: they possess explicit, non-asymptotic guarantees even without distributional assumptions or model assumptions.
One can use conformal prediction with any pre-trained model, such as a neural network, to produce sets that are guaranteed to contain the ground truth with a user-specified probability, such as 90%90\%.
It is easy-to-understand, easy-to-use, and general, applying naturally to problems arising in the fields of computer vision, natural language processing, deep reinforcement learning, and so on.

This hands-on introduction is aimed to provide the reader a working understanding of conformal prediction and related distribution-free uncertainty quantification techniques with one self-contained document.
We lead the reader through practical theory for and examples of conformal prediction and describe its extensions to complex machine learning tasks involving structured outputs, distribution shift, time-series, outliers, models that abstain, and more.
Throughout, there are many explanatory illustrations, examples, and code samples in Python.
With each code sample comes a Jupyter notebook implementing the method on a real-data example; the notebooks can be accessed and easily run by clicking on the following icons: [![[Uncaptioned image]](2107.07511v6/x1.png)](https://github.com/aangelopoulos/conformal-prediction).

![[Uncaptioned image]](2107.07511v6/x1.png)

###### Contents

## 1 Conformal Prediction

![Refer to caption](2107.07511v6/x2.png)

Conformal prediction [vovk2005algorithmic, papadopoulos2002inductive, lei2014distribution] (a.k.a. conformal inference) is a straightforward way to generate prediction sets for any model.
We will introduce it with a short, pragmatic image classification example, and follow up in later paragraphs with a general explanation. The high-level outline of conformal prediction is as follows. First, we begin with a fitted predicted model (such as a neural network classifier) which we will call f^\hat{f}. Then, we will create prediction sets (a set of possible labels) for this classifier using a small amount of additional *calibration data*—we will sometimes call this the *calibration step*.

Formally, suppose we have images as input and they each contain one of KK classes.
We begin with a classifier that outputs estimated probabilities (softmax scores) for each class: f^​(x)∈[0,1]K\hat{f}(x)\in[0,1]^{K}.
Then, we reserve a moderate number (e.g., 500) of fresh i.i.d. pairs of images and classes unseen during training, (X1,Y1),…,(Xn,Yn)(X\_{1},Y\_{1}),\dots,(X\_{n},Y\_{n}), for use as calibration data.
Using f^\hat{f} and the calibration data, we seek to construct a *prediction set* of possible labels 𝒞​(Xtest)⊂{1,…,K}\mathcal{C}(X\_{\rm test})\subset\{1,\dots,K\} that is valid in the following sense:

|  |  |  |  |
| --- | --- | --- | --- |
|  | 1−α≤ℙ​(Ytest∈𝒞​(Xtest))≤1−α+1n+1,1-\alpha\leq\mathbb{P}(Y\_{\rm test}\in\mathcal{C}(X\_{\rm test}))\leq 1-\alpha+\frac{1}{n+1}, |  | (1) |

where (Xtest,Ytest)(X\_{\rm test},Y\_{\rm test}) is a fresh test point from the same distribution, and α∈[0,1]\alpha\in[0,1] is a user-chosen error rate.
In words, the probability that the prediction set contains the correct label is almost exactly 1−α1-\alpha; we call this property *marginal coverage*, since the probability is marginal (averaged) over the randomness in the calibration and test points.
See Figure [1](#S1.F1 "Figure 1 ‣ 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") for examples of prediction sets on the Imagenet dataset.

![Refer to caption](2107.07511v6/x3.png)
![Refer to caption](2107.07511v6/x5.png)

To construct 𝒞\mathcal{C} from f^\hat{f} and the calibration data, we will perform a simple calibration step that requires only a few lines of code; see the right panel of Figure [2](#S1.F2 "Figure 2 ‣ 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
We now describe the calibration step in more detail, introducing some terms that will be helpful later on.
First, we set the *conformal score* si=1−f^​(Xi)Yis\_{i}=1-\hat{f}(X\_{i})\_{Y\_{i}} to be one minus the softmax output of the true class.
The score is high when the softmax output of the true class is low, i.e., when the model is badly wrong.
Next comes the critical step: define q^\hat{q} to be the ⌈(n+1)​(1−α)⌉/n\lceil(n+1)(1-\alpha)\rceil/n empirical quantile of s1,…,sns\_{1},...,s\_{n}, where ⌈⋅⌉\lceil\cdot\rceil is the ceiling function
(q^\hat{q} is essentially the 1−α1-\alpha quantile, but with a small correction).
Finally, for a new test data point (where XtestX\_{\rm test} is known but YtestY\_{\rm test} is not), create a prediction set 𝒞​(Xtest)={y:f^​(Xtest)y≥1−q^}\mathcal{C}(X\_{\rm test})=\{y:\hat{f}(X\_{\rm test})\_{y}\geq 1-\hat{q}\} that includes all classes with a high enough softmax output (see Figure [2](#S1.F2 "Figure 2 ‣ 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).
Remarkably, this algorithm gives prediction sets that are guaranteed to satisfy ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")), no matter what (possibly incorrect) model is used or what the (unknown) distribution of the data is.

#### Remarks

Let us think about the interpretation of 𝒞\mathcal{C}.
The function 𝒞\mathcal{C} is *set-valued*—it takes in an image, and it outputs a set of classes as in Figure [1](#S1.F1 "Figure 1 ‣ 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
The model’s softmax outputs help to generate the set.
This method constructs a different output set *adaptively to each particular input*.
The sets become larger when the model is uncertain or the image is intrinsically hard.
This is a property we want, because the size of the set gives you an indicator of the model’s certainty.
Furthermore, 𝒞​(Xtest)\mathcal{C}(X\_{\rm test}) can be interpreted as a set of plausible classes that the image XtestX\_{\rm test} could be assigned to.
Finally, 𝒞\mathcal{C} is *valid*, meaning it satisfies ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).111Due to the discreteness of YY, a small modification involving tie-breaking is needed to additionally satisfy the upper bound (see [angelopoulos2020sets] for details; this randomization is usually ignored in practice). We will henceforth ignore such tie-breaking.
These properties of 𝒞\mathcal{C} translate naturally to other machine learning problems, like regression, as we will see.

With an eye towards generalization, let us review in detail what happened in our classification problem. To begin, we were handed a model that had an inbuilt, but heuristic, notion of uncertainty: softmax outputs.
The softmax outputs attempted to measure the conditional probability of each class; in other words, the jjth entry of the softmax vector estimated ℙ​(Y=j∣X=x)\mathbb{P}(Y=j\mid X=x), the probability of class jj conditionally on an input image xx.
However, we had no guarantee that the softmax outputs were any good; they may have been arbitrarily overfit or otherwise untrustworthy. Therefore, instead of taking the softmax outputs at face value, we used the holdout set to adjust for their deficiencies.

The holdout set contained n≈500n\approx 500 fresh data points that the model never saw during training, which allowed us to get an honest appraisal of its performance.
The adjustment involved computing conformal scores, which grow when the model is uncertain, but are not valid prediction intervals on their own.
In our case, the conformal score was one minus the softmax output of the true class, but in general, the score can be any function of xx and yy.
We then took q^\hat{q} to be roughly the 1−α1-\alpha quantile of the scores.
In this case, the quantile had a simple interpretation—when setting α=0.1\alpha=0.1, at least 90%90\% of ground truth softmax outputs are guaranteed to be above the level 1−q^1-\hat{q} (we prove this rigorously in Appendix LABEL:app:coverage-proof).
Taking advantage of this fact, at test-time, we got the softmax outputs of a new image XtestX\_{\rm test} and collected all classes with outputs above 1−q^1-\hat{q} into a prediction set 𝒞​(Xtest)\mathcal{C}(X\_{\rm test}).
Since the softmax output of the new true class YtestY\_{\rm test} is guaranteed to be above 1−q^1-\hat{q} with probability at least 90%90\%, we finally got the guarantee in Eq. ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).

### 1.1 Instructions for Conformal Prediction

As we said during the summary, conformal prediction is not specific to softmax outputs or classification problems.
In fact, conformal prediction can be seen as a method for taking any heuristic notion of uncertainty from any model and converting it to a rigorous one (see the diagram below).
Conformal prediction does not care if the underlying prediction problem is discrete/continuous or classification/regression.

![[Uncaptioned image]](2107.07511v6/x6.png)

We next outline conformal prediction for a general input xx and output yy (not necessarily discrete).

Identify a heuristic notion of uncertainty using the pre-trained model.

Define the score function s​(x,y)∈ℝs(x,y)\in\mathbb{R}. (Larger scores encode worse agreement between xx and yy.)

Compute q^\hat{q} as the ⌈(n+1)​(1−α)⌉n\frac{\lceil(n+1)(1-\alpha)\rceil}{n} quantile of the calibration scores s1=s​(X1,Y1),…,sn=s​(Xn,Yn)s\_{1}=s(X\_{1},Y\_{1}),...,s\_{n}=s(X\_{n},Y\_{n}).

Use this quantile to form the prediction sets for new examples:

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(Xtest)={y:s​(Xtest,y)≤q^}.\mathcal{C}(X\_{\rm test})=\left\{y:s(X\_{\rm test},y)\leq\hat{q}\right\}. |  | (2) |

As before, these sets satisfy the validity property in ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")), for any (possibly uninformative) score function and (possibly unknown) distribution of the data. We formally state the coverage guarantee next.

###### Theorem 1 (Conformal coverage guarantee; Vovk, Gammerman, and Saunders [vovk1999machine]).

Suppose (Xi,Yi)i=1,…,n(X\_{i},Y\_{i})\_{i=1,\dots,n} and (Xtest,Ytest)(X\_{\rm test},Y\_{\rm test}) are i.i.d. and define q^\hat{q} as in step 3 above and 𝒞​(Xtest)\mathcal{C}(X\_{\rm test}) as in step 4 above. Then the following holds:

|  |  |  |
| --- | --- | --- |
|  | P​(Ytest∈𝒞​(Xtest))≥1−α.P\Big(Y\_{\rm test}\in\mathcal{C}(X\_{\rm test})\Big)\geq 1-\alpha. |  |

See Appendix LABEL:app:coverage-proof for a proof and a statement that includes the upper bound in ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).
We note that the above is only a special case of conformal prediction, called *split conformal prediction*. This is the most widely-used version of conformal prediction, and it will be our primary focus.
To complete the picture, we describe conformal prediction in full generality later in Section [6](#S6 "6 Full conformal prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") and give an overview of the literature in Section [7](#S7 "7 Historical Notes on Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").

#### Choice of score function

Upon first glance, this seems too good to be true, and a skeptical reader might ask the following question:

*How is it possible to construct a statistically valid prediction set even if the heuristic notion of uncertainty of the underlying model is arbitrarily bad?*

Let’s give some intuition to supplement the mathematical understanding from the proof in Appendix LABEL:app:coverage-proof.
Roughly, if the scores sis\_{i} correctly rank the inputs from lowest to highest magnitude of model error, then the resulting sets will be smaller for easy inputs and bigger for hard ones.
If the scores are bad, in the sense that they do not approximate this ranking, then the sets will be useless.
For example, if the scores are random noise, then the sets will contain a random sample of the label space, where that random sample is large enough to provide valid marginal coverage.
This illustrates an important underlying fact about conformal prediction: although the guarantee always holds, the usefulness of the prediction sets is primarily determined by the score function.
This should be no surprise—the score function incorporates almost all the information we know about our problem and data, including the underlying model itself.
For example, the main difference between applying conformal prediction on classification problems versus regression problems is the choice of score.
There are also many possible score functions for a single underlying model, which have different properties. Therefore, constructing the right score function is an important engineering choice.
We will next show a few examples of good score functions.

## 2 Examples of Conformal Procedures

In this section we give examples of conformal prediction applied in many settings, with the goal of providing the reader a bank of techniques to practically deploy.
Note that we will focus only on one-dimensional YY in this section, and smaller conformal scores will correspond to more model confidence (such scores are called nonconformity scores).
Richer settings, such as high-dimensional YY, complicated (or multiple) notions of error, or where different mistakes cost different amounts, often require the language of *risk control*, outlined in Section LABEL:app:ltt.

### 2.1 Classification with Adaptive Prediction Sets

![Refer to caption](2107.07511v6/x8.png)

Let’s begin our sequence of examples with an improvement to the classification example in Section [1](#S1 "1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
The previous method produces prediction sets with the smallest average size [Sadinle2016LeastAS], but it tends to undercover hard subgroups and overcover easy ones.
Here we develop a different method called *adaptive prediction sets* (APS) that avoids this problem.
We will follow [romano2020classification] and [angelopoulos2020sets].

As motivation for this new procedure, note that if the softmax outputs f^​(Xtest)\hat{f}(X\_{\rm test}) were a perfect model of Ytest|XtestY\_{\rm test}|X\_{\rm test}, we would greedily include the top-scoring classes until their total mass just exceeded 1−α1-\alpha.
Formally, we can describe this oracle algorithm as

|  |  |  |  |
| --- | --- | --- | --- |
|  | {π1​(x),…,πk​(x)}​, where ​k=sup{k′:∑j=1k′f^​(Xtest)πj​(x)<1−α}+1,\left\{\pi\_{1}(x),...,\pi\_{k}(x)\right\}\text{, where }k=\sup\left\{k^{\prime}:\sum\limits\_{j=1}^{k^{\prime}}\hat{f}(X\_{\rm test})\_{\pi\_{j}(x)}<1-\alpha\right\}+1, |  | (3) |

and π​(x)\pi(x) is the permutation of {1,…,K}\{1,...,K\} that sorts f^​(Xtest)\hat{f}(X\_{\rm test}) from most likely to least likely.
In practice, however, this procedure fails to provide coverage, since f^​(Xtest)\hat{f}(X\_{\rm test}) is not perfect; it only provides us a heuristic notion of uncertainty. Therefore, we will use conformal prediction to turn this into a rigorous notion of uncertainty.

To proceed, we define a score function inspired by the oracle algorithm:

|  |  |  |  |
| --- | --- | --- | --- |
|  | s​(x,y)=∑j=1kf^​(x)πj​(x)​, where ​y=πk​(x).s(x,y)=\sum\limits\_{j=1}^{k}\hat{f}(x)\_{\pi\_{j}(x)}\text{, where }y=\pi\_{k}(x). |  | (4) |

In other words, we greedily include classes in our set until we reach the true label, then we stop.
Unlike the score from Section [1](#S1 "1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), this one utilizes the softmax outputs of all classes, not just the true class.

The next step, as in all conformal procedures, is to set q^=Quantile​(s1,…,sn;⌈(n+1)​(1−α)⌉n)\hat{q}=\mathrm{Quantile}(s\_{1},...,s\_{n}\;;\;\frac{\lceil(n+1)(1-\alpha)\rceil}{n}).
Having done so, we will form the prediction set {y:s​(x,y)≤q^}\{y:s(x,y)\leq\hat{q}\}, modified slightly to avoid zero-size sets:

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(x)={π1​(x),…,πk​(x)}​, where ​k=sup{k′:∑j=1k′f^​(x)πj​(x)<q^}+1.\mathcal{C}(x)=\left\{\pi\_{1}(x),...,\pi\_{k}(x)\right\}\text{, where }k=\sup\left\{k^{\prime}:\sum\limits\_{j=1}^{k^{\prime}}\hat{f}(x)\_{\pi\_{j}(x)}<\hat{q}\right\}+1. |  | (5) |

Figure [3](#S2.F3 "Figure 3 ‣ 2.1 Classification with Adaptive Prediction Sets ‣ 2 Examples of Conformal Procedures ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") shows Python code to implement this method.
As usual, these uncertainty sets (with tie-breaking) satisfy ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).
See [angelopoulos2020sets] for details and significant practical improvements, which we implemented here: [![[Uncaptioned image]](2107.07511v6/x9.png)](https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/imagenet-raps.ipynb).

![[Uncaptioned image]](2107.07511v6/x9.png)
![Refer to caption](2107.07511v6/x10.png)

### 2.2 Conformalized Quantile Regression

We will next show how to incorporate uncertainty into regression problems with a continuous output, following the algorithm in [romano2019conformalized].
We use quantile regression [koenker1978regression] as our base model.
As a reminder, the quantile regression algorithm attempts to learn the γ\gamma quantile of Ytest|Xtest=xY\_{\rm test}|X\_{\rm test}=x for each possible value of xx.
We will call the true quantile tγ​(x)t\_{\gamma}(x) and the fitted model t^γ​(x)\hat{t}\_{\gamma}(x).
Since by definition Ytest|Xtest=xY\_{\rm test}|X\_{\rm test}=x lands below t0.05​(x)t\_{0.05}(x) with 5%5\% probability and above t0.95​(x)t\_{0.95}(x) with 5%5\% probability, we would expect the interval [t^0.05​(x),t^0.95​(x)]\left[\hat{t}\_{0.05}(x),\hat{t}\_{0.95}(x)\right] to have approximately 90% coverage.
However, because the fitted quantiles may be inaccurate, we will conformalize them.
Python pseudocode for conformalized quantile regression is in Figure [5](#S2.F5 "Figure 5 ‣ 2.2 Conformalized Quantile Regression ‣ 2 Examples of Conformal Procedures ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").

After training an algorithm to output two such quantiles (this can be done with a standard loss function, see below), tα/2t\_{\alpha/2} and t1−α/2t\_{1-\alpha/2}, we can define the score to be the difference between yy and its nearest quantile,

|  |  |  |  |
| --- | --- | --- | --- |
|  | s​(x,y)=max⁡{t^α/2​(x)−y,y−t^1−α/2​(x)}.s(x,y)=\max\left\{\hat{t}\_{\alpha/2}(x)-y,y-\hat{t}\_{1-\alpha/2}(x)\right\}. |  | (6) |

After computing the scores on our calibration set and setting q^=Quantile​(s1,…,sn;⌈(n+1)​(1−α)⌉n)\hat{q}=\mathrm{Quantile}(s\_{1},...,s\_{n}\;;\;\frac{\lceil(n+1)(1-\alpha)\rceil}{n}), we can form valid prediction intervals by taking

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(x)=[t^α/2​(x)−q^,t^1−α/2​(x)+q^].\mathcal{C}(x)=\left[\hat{t}\_{\alpha/2}(x)-\hat{q},\hat{t}\_{1-\alpha/2}(x)+\hat{q}\right]. |  | (7) |

Intuitively, the set 𝒞​(x)\mathcal{C}(x) just grows or shrinks the distance between the quantiles by q^\hat{q} to achieve coverage.

![Refer to caption](2107.07511v6/x12.png)
![Refer to caption](2107.07511v6/x13.png)

As before, 𝒞\mathcal{C} satisfies the coverage property in Eq. ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).
However, unlike our previous example in Section [1](#S1 "1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), 𝒞\mathcal{C} is no longer a set of classes, but instead a *continuous interval* in ℝ\mathbb{R}.
Quantile regression is not the only way to get such continuous-valued intervals.
However, it is often the best way, especially if α\alpha is known in advance.
The reason is that the intervals generated via quantile regression even without conformal prediction, i.e. [t^α/2​(x),t^1−α/2​(x)][\hat{t}\_{\alpha/2}(x),\hat{t}\_{1-\alpha/2}(x)], have good coverage to begin with.
Furthermore, they have asymptotically valid conditional coverage (a concept we will explain in Section [3](#S3 "3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).
These properties propagate through the conformal procedure and lead to prediction sets with good performance.

One attractive feature of quantile regression is that it can easily be added on top of any base model simply by changing the loss function to a *quantile loss* (informally referred to as a *pinball loss*),

|  |  |  |  |
| --- | --- | --- | --- |
|  | Lγ​(t^γ,y)=(y−t^γ)​γ​𝟙​{y>t^γ}+(t^γ−y)​(1−γ)​𝟙​{y≤t^γ}.L\_{\gamma}(\hat{t}\_{\gamma},y)=(y-\hat{t}\_{\gamma})\gamma\mathbbm{1}\left\{y>\hat{t}\_{\gamma}\right\}+(\hat{t}\_{\gamma}-y)(1-\gamma)\mathbbm{1}\left\{y\leq\hat{t}\_{\gamma}\right\}. |  | (8) |

![[Uncaptioned image]](2107.07511v6/x14.png)

The reader can think of quantile regression as a generalization of L1-norm regression: when γ=0.5\gamma=0.5, the loss function reduces to L0.5=|t^γ​(x)−y|/2L\_{0.5}=|\hat{t}\_{\gamma}(x)-y|/2, which encourages t^0.5​(x)\hat{t}\_{0.5}(x) to converge to the conditional median.
Changing γ\gamma just modifies the L1 norm as in the illustration above to target other quantiles.
In practice, one can just use a quantile loss instead of MSE at the end of any algorithm, like a neural network, in order to regress to a quantile.

### 2.3 Conformalizing Scalar Uncertainty Estimates

#### 2.3.1 The Estimated Standard Deviation

As an alternative to quantile regression, our next example is a different way of constructing prediction sets for continuous yy with a less rich but more common notion of heuristic uncertainty: an estimate of the standard deviation σ^​(x)\hat{\sigma}(x). For example, one can produce uncertainty scalars by assuming Ytest∣Xtest=xY\_{\rm test}\mid X\_{\rm test}=x follows some parametric distribution—like a Gaussian distribution—and training a model to output the mean and variance of that distribution.
To be precise, in this setting we choose to model Ytest∣Xtest=x∼𝒩​(μ​(x),σ​(x))Y\_{\rm test}\mid X\_{\rm test}=x\sim\mathcal{N}(\mu(x),\sigma(x)), and we have models f^​(x)\hat{f}(x) and σ^​(x)\hat{\sigma}(x) trained to maximize the likelihood of the data with respect to 𝔼​[Ytest∣Xtest=x]\mathbb{E}\left[Y\_{\rm test}\mid X\_{\rm test=x}\right] and Var​[Ytest∣Xtest=x]\sqrt{\textrm{Var}\left[Y\_{\rm test}\mid X\_{\rm test}=x\right]} respectively.
Then, f^​(x)\hat{f}(x) gets used as the point prediction and σ^​(x)\hat{\sigma}(x) gets used as the uncertainty.
This strategy is so common that it is commoditized: there are inbuilt PyTorch losses, such as GaussianNLLLoss, that enable training a neural network this way.
However, we usually know Ytest∣XtestY\_{\rm test}\mid X\_{\rm test} isn’t Gaussian, so even if we had infinite data, σ^​(x)\hat{\sigma}(x) would not necessarily be reliable.
We can use conformal prediction to turn this heuristic uncertainty notion into rigorous prediction intervals of the form f^​(x)±q^​σ^​(x)\hat{f}(x)\pm\hat{q}\hat{\sigma}(x).

#### 2.3.2 Other 1-D Uncertainty Estimates

More generally, we assume there is a function u​(x)u(x) such that larger values encode more uncertainty.
This single number can have many interpretations beyond the standard deviation.
For example, one instance of an uncertainty scalar simply involves the user creating a model for the magnitude of the residual.
In that setting, the user would first fit a model f^\hat{f} that predicts yy from xx.
Then, they would fit a second model r^\hat{r} (possibly the same neural network), that predicts |y−f^​(x)|\left|y-\hat{f}(x)\right|.
If r^\hat{r} were perfect, we would expect the set [f^​(x)−r^​(x),f^​(x)+r^​(x)]\left[\hat{f}(x)-\hat{r}(x),\hat{f}(x)+\hat{r}(x)\right] to have perfect coverage.
However, our learned model of the error r^\hat{r} is often poor in practice.

There are many more such uncertainty scalars than we can discuss in this document in detail, including

measuring the variance of f^​(x)\hat{f}(x) across an ensemble of models,

measuring the variance of f^​(x)\hat{f}(x) when randomly dropping out a fraction of nodes in a neural net,

measuring the variance of f^​(x)\hat{f}(x) to small, random input perturbations,

measuring the variance of f^​(x)\hat{f}(x) over different noise samples input to a generative model,

measuring the magnitude of change in f^​(x)\hat{f}(x) when applying an adversarial perturbation, etc.

These cases will all be treated the same way.
There will be some point prediction f^​(x)\hat{f}(x), and some uncertainty scalar u​(x)u(x) that is large when the model is uncertain and small otherwise (in the residual setting, u​(x):=r^​(x)u(x):=\hat{r}(x), and in the Gaussian setting, u​(x):=σ^​(x)u(x):=\hat{\sigma}(x)).
We will proceed with this notation for the sake of generality, but the reader should understand that uu can be replaced with any function.

Now that we have our heuristic notion of uncertainty in hand, we can define a score function,

|  |  |  |  |
| --- | --- | --- | --- |
|  | s​(x,y)=|y−f^​(x)|u​(x).s(x,y)=\frac{\left|y-\hat{f}(x)\right|}{u(x)}. |  | (9) |

This score function has a natural interpretation: it is a multiplicative correction factor of the uncertainty scalar (i.e., s​(x,y)​u​(x)=|y−f^​(x)|s(x,y)u(x)=\left|y-\hat{f}(x)\right|).
As before, taking q^\hat{q} to be the ⌈(1−α)​(n+1)⌉n\frac{\lceil(1-\alpha)(n+1)\rceil}{n} quantile of the calibration scores guarantees us that for a new example,

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ​[s​(Xtest,Ytest)≤q^]≥1−α⟹ℙ​[|Ytest−f^​(Xtest)|≤u​(Xtest)​q^]≥1−α.\mathbb{P}\left[s(X\_{\rm test},Y\_{\rm test})\leq\hat{q}\right]\geq 1-\alpha\implies\mathbb{P}\left[\left|Y\_{\rm test}-\hat{f}(X\_{\rm test})\right|\leq u(X\_{\rm test})\hat{q}\right]\geq 1-\alpha. |  | (10) |

Naturally, we can then form prediction sets using the rule

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(x)=[f^​(x)−u​(x)​q^,f^​(x)+u​(x)​q^].\mathcal{C}(x)=\left[\hat{f}(x)-u(x)\hat{q},\hat{f}(x)+u(x)\hat{q}\right]. |  | (11) |

![Refer to caption](2107.07511v6/x16.png)
![Refer to caption](2107.07511v6/x17.png)

Let’s reflect a bit on the nature of these prediction sets.
The prediction sets are valid, as we desired.
Due to our construction, they are also symmetric about the prediction, f^​(x)\hat{f}(x), although symmetry could be relaxed with minor modifications.
However, uncertainty scalars do not necessarily scale properly with α\alpha.
In other words, there is no reason to believe that a quantity like σ^\hat{\sigma} would be directly related to quantiles of the label distribution.
We tend to prefer quantile regression when possible, since it directly estimates this quantity and thus should be a better heuristic (and in practice it usually is; see [angelopoulos2022image] for some evaluations).
Nonetheless, uncertainty scalars remain in use because they are easy to deploy and have been commoditized in popular machine learning libraries.
See Figure [7](#S2.F7 "Figure 7 ‣ 2.3.2 Other 1-D Uncertainty Estimates ‣ 2.3 Conformalizing Scalar Uncertainty Estimates ‣ 2 Examples of Conformal Procedures ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") for a Python implementation of this method.

### 2.4 Conformalizing Bayes

Our final example of conformal prediction will use a Bayesian model.
Bayesian predictors, like Bayesian neural networks, are commonly studied in the field of uncertainty quantification, but rely on many unverifiable and/or incorrect assumptions to provide coverage.
Nonetheless, we should incorporate any prior information we have into our prediction sets.
We will now show how to create valid prediction sets that are also Bayes optimal among all prediction sets that achieve 1−α1-\alpha coverage.
These prediction sets use the posterior predictive density as a conformal score.
The Bayes optimality of this procedure was first proven in [hoff2021bayes], and was previously studied in [wasserman2011frasian, melluish2001comparing].
Because our algorithm reduces to picking the labels with high posterior predictive density, the Python code will look exactly the same as in Figure [2](#S1.F2 "Figure 2 ‣ 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
The only difference is interpretation, since the softmax now represents an approximation of a continuous distribution rather than a categorical one.

Let us first describe what a Bayesian would do, given a Bayesian model f^​(y∣x)\hat{f}(y\mid x), which estimates the value of the posterior distribution of YtestY\_{\rm test} at label yy with input Xtest=xX\_{\rm test}=x.
If one believed all the necessary assumptions—mainly, a correctly specified model and asymptotically large nn—the following would be the optimal prediction set:

|  |  |  |  |
| --- | --- | --- | --- |
|  | S​(x)={y:f^​(y∣x)>t}​, where ​t​ is chosen so ​∫y∈S​(x)f^​(y∣x)​𝑑y=1−α.S(x)=\left\{y:\hat{f}(y\mid x)>t\right\}\text{, where }t\text{ is chosen so }\int\limits\_{y\in S(x)}\hat{f}(y\mid x)dy=1-\alpha. |  | (12) |

However, because we cannot make assumptions on the model and data, we can only consider f^​(y∣x)\hat{f}(y\mid x) to be a heuristic notion of uncertainty.

Following our now-familiar checklist, we can define a conformal score,

|  |  |  |  |
| --- | --- | --- | --- |
|  | s​(x,y)=−f^​(y∣x),s(x,y)=-\hat{f}(y\mid x), |  | (13) |

which is high when the model is uncertain and otherwise low.
After computing q^\hat{q} over the calibration data, we can then construct prediction sets:

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(x)={y:f^​(y∣x)>−q^}.\mathcal{C}(x)=\left\{y:\hat{f}(y\mid x)>-\hat{q}\right\}. |  | (14) |

![Refer to caption](2107.07511v6/x18.png)

This set is valid because we chose the threshold q^\hat{q} via conformal prediction.
Furthermore, when certain technical assumptions are satisfied, it has the best Bayes risk among all prediction sets with 1−α1-\alpha coverage.
To be more precise, under the assumptions in [hoff2021bayes], 𝒞​(Xtest)\mathcal{C}(X\_{\rm test}) has the smallest average size of any conformal procedure with 1−α1-\alpha coverage, where the average is taken over the data *and* the parameters.
This result should not be a surprise to those familiar with decision theory, as the argument we are making feels similar to that of the Neyman-Pearson lemma.
This concludes the final example.

#### Discussion

As our examples have shown, conformal prediction is a simple and pragmatic technique with many use cases.
It is also easy to implement and computationally trivial.
Additionally, the above four examples serve as roadmaps to the user for designing score functions with various notions of optimality, including average size, adaptivity, and Bayes risk.
Still more is yet to come—conformal prediction can be applied more broadly than it may first seem at this point.
We will outline extensions of conformal prediction to other prediction tasks such as outlier detection, image segmentation, serial time-series prediction, and so on in Section [4](#S4 "4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
Before addressing these extensions, we will take a deep dive into diagnostics for conformal prediction in the standard setting, including the important topic of conditional coverage.

## 3 Evaluating Conformal Prediction

We have spent the last two sections learning how to form valid prediction sets satisfying rigorous statistical guarantees.
Now we will discuss how to evaluate them.
Our evaluations will fall into one of two categories.

Evaluating adaptivity. It is extremely important to keep in mind that the conformal prediction procedure with the smallest average set size is not necessarily the best.
A good conformal prediction procedure will give small sets on easy inputs and large sets on hard inputs in a way that faithfully reflects the model’s uncertainty. This *adaptivity* is not implied by conformal prediction’s coverage guarantee, but it is non-negotiable in practical deployments of conformal prediction. We will formalize adaptivity, explore its consequences, and suggest practical algorithms for evaluating it.

Correctness checks. Correctness checks help you test whether you’ve implemented conformal prediction correctly. We will empirically check that the coverage satisfies Theorem [1](#Thmtheorem1 "Theorem 1 (Conformal coverage guarantee; Vovk, Gammerman, and Saunders [vovk1999machine]). ‣ 1.1 Instructions for Conformal Prediction ‣ 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"). Rigorously evaluating whether this property holds requires a careful accounting of the finite-sample variability present with real datasets. We develop explicit formulae for the size of the benign fluctuations—if one observes deviations from 1−α1-\alpha in coverage that are larger than these formulae dictate, then there is a problem with the implementation.

Many of the evaluations we suggest are computationally intensive, and require running the entire conformal procedure on different splits of data at least 100100 times.
Naïve implementations of these evaluations can be slow when the score takes a long time to compute.
With some simple computational tricks and strategic caching, we can speed this process up by orders of magnitude.
Therefore to aid the reader, we intersperse the mathematical descriptions with code to efficiently implement these computations.

### 3.1 Evaluating Adaptivity

Although any conformal procedure yields prediction intervals that satisfy ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")), there are many such procedures, and they differ in other important ways. In particular, a key design consideration for conformal prediction is *adaptivity*: we want the procedure to return larger sets for harder inputs and smaller sets for easier inputs. While most reasonable conformal procedures will satisfy this to some extent, we now discuss precise metrics for adaptivity that allow the user to check a conformal procedure and to compare multiple alternative conformal procedures.

##### Set size.

The first step is to plot histograms of set sizes.
This histogram helps us in two ways.
Firstly, a large average set size indicates the conformal procedure is not very precise, indicating a possible problem with the score or underlying model.
Secondly, the spread of the set sizes shows whether the prediction sets properly adapt to the difficulty of examples. A wider spread is generally desirable, since it means that the procedure is effectively distinguishing between easy and hard inputs.

![[Uncaptioned image]](2107.07511v6/x19.png)

It can be tempting to stop evaluations after plotting the coverage and set size, but certain important questions remain unanswered.
A good spread of set sizes is generally better, but it does not necessarily indicate that the sets adapt properly to the difficulty of XX. Above seeing that the set sizes have dynamic range, we will need to verify that large sets occur for hard examples. We next formalize this notion and give metrics for evaluating it.

##### Conditional coverage.

Adaptivity is typically formalized by asking for the *conditional coverage* [vovk2012conditional] property:

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ​[Ytest∈𝒞​(Xtest)∣Xtest]≥1−α.\mathbb{P}\left[Y\_{\rm test}\in\mathcal{C}(X\_{\rm test})\mid X\_{\rm test}\right]\geq 1-\alpha. |  | (15) |

That is, for every value of the input XtestX\_{\rm test}, we seek to return prediction sets with 1−α1-\alpha coverage.
This is a stronger property than the *marginal coverage* property in ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) that conformal prediction is guaranteed to achieve—indeed, in the most general case, conditional coverage is impossible to achieve [vovk2012conditional]. In other words, conformal procedures are not guaranteed to satisfy ([15](#S3.E15 "In Conditional coverage. ‣ 3.1 Evaluating Adaptivity ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")), so we must check how close our procedure comes to approximating it.

The difference between marginal and conditional coverage is subtle but of great practical importance, so we will spend some time think about the differences here.
Imagine there are two groups of people, group A and group B, with frequencies 90% and 10%.
The prediction sets always cover YY among people in group A and never cover YY when the person comes from group B.
Then the prediction sets have 90% coverage, but not conditional coverage.
Conditional coverage would imply that the prediction sets cover YY at least 90% of the time in both groups.
This is necessary, but not sufficient; conditional coverage is a very strong property that states the probability of the prediction set needs to be ≥90%\geq 90\% *for a particular person*.
In other words, for any subset of the population, the coverage should be ≥90%\geq 90\%.
See Figure [10](#S3.F10 "Figure 10 ‣ Conditional coverage. ‣ 3.1 Evaluating Adaptivity ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") for a visualization of the difference between conditional and marginal coverage.

![Refer to caption](2107.07511v6/x20.png)

##### Feature-stratified coverage metric.

As a first metric for conditional coverage, we will formalize the example we gave earlier, where coverage is unequal over some groups.
The reader can think of these groups as discrete categories, like race, or as a discretization of continuous features, like age ranges.
Formally, suppose we have features Xi,1(val)X\_{i,1}^{\rm(val)} that take values in {1,…,G}\{1,\dots,G\} for some GG.
(Here, i=1,…,nvali=1,\dots,n\_{\rm val} indexes the example in the validation set, and the first coordinate of each feature is the group.)
Let ℐg⊂{1,…,nval}\mathcal{I}\_{g}\subset\{1,\dots,n\_{\rm val}\} be the set of observations such that Xi,1(val)=gX\_{i,1}^{\rm(val)}=g for g=1,…,Gg=1,\dots,G.
Since conditional coverage implies that the procedure has the same coverage for all values of XtestX\_{\rm test}, we use the following measure:

|  |  |  |
| --- | --- | --- |
|  | FSC metric:ming∈{1,…,G}1|ℐg|∑i∈ℐg𝟙{Yi(val)∈𝒞(Xi(val))}\textbf{FSC metric}:\qquad\min\_{g\in\{1,\dots,G\}}\ \frac{1}{|\mathcal{I}\_{g}|}\ \sum\_{i\in\mathcal{I}\_{g}}\mathbbm{1}\left\{Y\_{i}^{\rm(val)}\in\mathcal{C}\Big(X\_{i}^{\rm(val)}\Big)\right\} |  |

In words, this is the observed coverage among all instances where the discrete feature takes the value gg.
If conditional coverage were achieved, this would be 1−α1-\alpha, and values farther below 1−α1-\alpha indicate a greater violation of conditional coverage.
Note that this metric can also be used with a continuous feature by binning the features into a finite number of categories.

##### Size-stratified coverage metric.

We next consider a more general-purpose metric for how close a conformal procedure comes to satisfying ([15](#S3.E15 "In Conditional coverage. ‣ 3.1 Evaluating Adaptivity ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")), introduced in [angelopoulos2020sets]. First, we discretize the possible cardinalities of 𝒞​(x)\mathcal{C}(x), into GG bins, B1,…,BGB\_{1},\dots,B\_{G}. For example, in classification we might divide the observations into three groups, depending on whether 𝒞​(x)\mathcal{C}(x) has one element, two elements, or more than two elements. Let ℐg⊂{1,…,nval}\mathcal{I}\_{g}\subset\{1,\dots,n\_{\rm val}\} be the set of observations falling in bin gg for g=1,…,Gg=1,\dots,G. Then we consider the following

|  |  |  |
| --- | --- | --- |
|  | SSC metric:ming∈{1,…,G}1|ℐg|∑i∈ℐg𝟙{Yi(val)∈𝒞(Xi(val))}\textbf{SSC metric}:\qquad\min\_{g\in\{1,\dots,G\}}\ \frac{1}{|\mathcal{I}\_{g}|}\ \sum\_{i\in\mathcal{I}\_{g}}\mathbbm{1}\left\{Y\_{i}^{\rm(val)}\in\mathcal{C}\Big(X\_{i}^{\rm(val)}\Big)\right\} |  |

In words, this is the observed coverage for all units for which the set size |𝒞​(x)||\mathcal{C}(x)| falls into bin gg. As before, if conditional coverage were achieved, this would be 1−α1-\alpha, and values farther below 1−α1-\alpha indicate a greater violation of conditional coverage. Note that this is the same expression as for the FSC metric, except that the definition of ℐg\mathcal{I}\_{g} has changed.
Unlike the FSC metric, the user does not have to define an important set of discrete features a-priori—it is a general metric that can apply to any example.

See [cauchois2020knowing] and [feldman2021improving] for additional metrics of conditional coverage.

### 3.2 The Effect of the Size of the Calibration Set

We first pause to discuss how the size of the calibration set affects conformal prediction.
We consider this question for two reasons.
First, the user must choose this for a practical deployment. Roughly speaking, our conclusion will that be choosing a calibration set of size n=1000n=1000 is sufficient for most purposes.
Second, the size of the calibration set is one source of finite-sample variability that we will need to analyze to correctly check the coverage.
We will build on the results here in the next section, where we give a complete description of how to check coverage in practice.

How does the size of the calibration set, nn, affect conformal prediction?
The coverage guarantee in ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) holds for any nn, so we can see that our prediction sets have coverage at least 1−α1-\alpha even with a very small calibration set.
Intuitively, however, it may seem that larger nn is better, and leads to more stable procedures. This intuition is correct, and it explains why using a larger calibration set is beneficial in practice. The details are subtle, so we carefully work through them here.

The key idea is that *the coverage of conformal prediction conditionally on the calibration set is a random quantity*.
That is, if we run the conformal prediction algorithm twice, each time sampling a new calibration dataset, then check the coverage on an infinite number of validation points, those two numbers will not be equal.
The coverage property in ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) says that coverage will be at least 1−α1-\alpha on average over the randomness in the calibration set, but with any one fixed calibration set, the coverage on an infinite validation set will be some number that is not exactly 1−α1-\alpha. Nonetheless, we can choose nn large enough to control these fluctuations in coverage by analyzing its distribution.

In particular, the distribution of coverage has an analytic form, first introduced by Vladimir Vovk in [vovk2012conditional], namely,

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ​(Ytest∈𝒞​(Xtest)|{(Xi,Yi)}i=1n)∼Beta​(n+1−l,l),\mathbb{P}\left(Y\_{\rm test}\in\mathcal{C}\left(X\_{\rm test}\right)\big|\>\{(X\_{i},Y\_{i})\}\_{i=1}^{n}\right)\sim\textrm{Beta}\left(n+1-l,l\right), |  | (16) |

where

|  |  |  |
| --- | --- | --- |
|  | l=⌊(n+1)​α⌋.l=\lfloor(n+1)\alpha\rfloor. |  |

Notice that the conditional expectation above is the coverage with an infinite validation data set, holding the calibration data fixed.
A simple proof of this fact is available in [vovk2012conditional].
We plot the distribution of coverage for several values of nn in Figure [11](#S3.F11 "Figure 11 ‣ 3.2 The Effect of the Size of the Calibration Set ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").

![Refer to caption](2107.07511v6/x21.png)

Inspecting Figure [11](#S3.F11 "Figure 11 ‣ 3.2 The Effect of the Size of the Calibration Set ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), we see that choosing n=1000n=1000 calibration points leads to coverage that is typically between .88.88 and .92.92, hence our rough guideline of choosing about 10001000 calibration points. More formally, we can compute exactly the number of calibration points nn needed to achieve a coverage of 1−α±ϵ1-\alpha\pm\epsilon with probability 1−δ1-\delta.
Again, the average coverage is always at least 1−α1-\alpha; the parameter δ\delta controls the tail probabilities of the coverage conditionally on the calibration data.
For any δ\delta, the required calibration set size nn can be explicitly computed from a simple expression, and we report on several values in Table [1](#S3.T1 "Table 1 ‣ 3.2 The Effect of the Size of the Calibration Set ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") for the reader’s reference.
Code allowing the user to produce results for any choice of nn and α\alpha accompanies the table.

| ϵ\mathbf{\epsilon} | 0.1 | 0.05 | 0.01 | 0.005 | 0.001 |
| --- | --- | --- | --- | --- | --- |
| n​(ϵ)n(\epsilon) | 22 | 102 | 2491 | 9812 | 244390 |

![[Uncaptioned image]](2107.07511v6/x23.png)

### 3.3 Checking for Correct Coverage

As an obvious diagnostic, the user will want to assess whether the conformal procedure has the correct coverage.
This can be accomplished by running the procedure over RR trials with new calibration and validation sets, and then calculating the empirical coverage for each,

|  |  |  |  |
| --- | --- | --- | --- |
|  | Cj=1nval​∑i=1nval𝟙​{Yi,j(val)∈𝒞j​(Xi,j(val))}​, for ​j=1,…,R,C\_{j}=\frac{1}{n\_{\textnormal{val}}}\sum\limits\_{i=1}^{n\_{\textnormal{val}}}\mathbbm{1}\left\{Y^{(\text{val})}\_{i,j}\in\mathcal{C}\_{j}\left(X^{(\text{val})}\_{i,j}\right)\right\}\text{, for }j=1,...,R, |  | (17) |

where nvaln\_{\textnormal{val}} is the size of the validation set, (Xi,j(val),Yi,j(val))(X^{(\text{val})}\_{i,j},Y^{(\text{val})}\_{i,j}) is the iith validation example in trial jj, and 𝒞j\mathcal{C}\_{j} is calibrated using the calibration data from the jjth trial.
A histogram of the CjC\_{j} should be centered at roughly 1−α1-\alpha, as in Figure [11](#S3.F11 "Figure 11 ‣ 3.2 The Effect of the Size of the Calibration Set ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
Likewise, the mean value,

|  |  |  |  |
| --- | --- | --- | --- |
|  | C¯=1R​∑j=1RCj,\overline{C}=\frac{1}{R}\sum\limits\_{j=1}^{R}C\_{j}, |  | (18) |

should be approximately 1−α1-\alpha.

With real datasets, we only have n+nvaln+n\_{\textnormal{val}} data points total to evaluate our conformal algorithm and therefore cannot draw new data for each of the RR rounds.
So, we compute the coverage values by randomly splitting the n+nvaln+n\_{\textnormal{val}} data points RR times into calibration and validation datasets, then running conformal.
Notice that rather than splitting the data points themselves many times, we can instead first cache all conformal scores and then compute the coverage values over many random splits, as in the code sample in Figure [12](#S3.F12 "Figure 12 ‣ 3.3 Checking for Correct Coverage ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").

![Refer to caption](2107.07511v6/x25.png)

If properly implemented, conformal prediction is guaranteed to satisfy the inequality in ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).
However, if the reader sees minor fluctuations in the observed coverage, they may not need to worry: the finiteness of nn, nvaln\_{\textnormal{val}}, and RR can lead to benign fluctuations in coverage which add some width to the Beta distribution in Figure [11](#S3.F11 "Figure 11 ‣ 3.2 The Effect of the Size of the Calibration Set ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
Appendix LABEL:app:empirical-coverage gives exact theory for analyzing the mean and standard deviation of C¯\overline{C}.
From this, we will be able to tell if any deviation from 1−α1-\alpha indicates a problem with the implementation, or if it is benign.
Code for checking the coverage at all different values of nn, nvaln\_{\textnormal{val}}, and RR is available in the accompanying Jupyter notebook of Figure [12](#S3.F12 "Figure 12 ‣ 3.3 Checking for Correct Coverage ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").

## 4 Extensions of Conformal Prediction

At this point, we have seen the core of the matter: how to construct prediction sets with coverage in any standard supervised prediction problem.
We now broaden our horizons towards prediction tasks with different structure, such as side information, covariate shift, and so on.
These more exotic problems arise quite frequently in the real world, so we present practical conformal algorithms to address them.

### 4.1 Group-Balanced Conformal Prediction

In certain settings, we might want prediction intervals that have equal error rates across certain subsets of the data.
For example, we may require our medical classifier to have coverage that is correct for all racial and ethnic groups.
To formalize this, we suppose that the first feature of our inputs, Xi,1X\_{i,1}, i=1,…,ni=1,...,n takes values in some discrete set {1,…,G}\{1,...,G\} corresponding to categorical groups.
We then ask for *group-balanced* coverage:

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ(Ytest∈𝒞(Xtest)|Xtest,1=g)≥1−α,\mathbb{P}\left(Y\_{\rm test}\in\mathcal{C}(X\_{\rm test})\;\rvert\;X\_{\rm test,1}=g\right)\geq 1-\alpha, |  | (19) |

for all groups g∈{1,…,G}g\in\{1,\dots,G\}.
In words, this means we have a 1−α1-\alpha coverage rate for all groups.
Notice that the group output could be a post-processing of the original features in the data.
For example, we might bin the values of XtestX\_{\rm test} into a discrete set.

Recall that a standard application of conformal prediction will not necessarily yield coverage within each group simultaneously—that is, ([19](#S4.E19 "In 4.1 Group-Balanced Conformal Prediction ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) may not be satisfied.
We saw an example in Figure [10](#S3.F10 "Figure 10 ‣ Conditional coverage. ‣ 3.1 Evaluating Adaptivity ‣ 3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"); the marginal guarantee from normal conformal prediction can still be satisfied even if all errors happen in one group.

In order to achieve group-balanced coverage, we will
simply run conformal prediction seperately for each
group, as visualized below.

![[Uncaptioned image]](2107.07511v6/x26.png)

Making this formal, given a conformal score function ss, we stratify the scores on the calibration set by group,

|  |  |  |  |
| --- | --- | --- | --- |
|  | si(g)=s​(Xj,Yj)​, where ​Xj,1​ is the ​i​th occurrence of group ​g.s\_{i}^{(g)}=s(X\_{j},Y\_{j})\text{, where }X\_{j,1}\text{ is the }i\text{th occurrence of group }g. |  | (20) |

Then, within each group, we calculate the conformal quantile

|  |  |  |  |
| --- | --- | --- | --- |
|  | q^(g)=Quantile​(s1,…,sn(g);⌈(n(g)+1)​(1−α)⌉n(g))​, where ​n(g)​ is the number of examples of group ​g.\hat{q}^{(g)}=\mathrm{Quantile}\left(s\_{1},...,s\_{n^{(g)}};\frac{\big\lceil(n^{(g)}+1)(1-\alpha)\big\rceil}{n^{(g)}}\right)\text{, where }n^{(g)}\text{ is the number of examples of group }g. |  | (21) |

Finally, we form prediction sets by first picking the relevant quantile,

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(x)={y:s​(x,y)≤q^(x1)}.\mathcal{C}(x)=\left\{y:s(x,y)\leq\hat{q}^{(x\_{1})}\right\}. |  | (22) |

That is, for a point xx that we see falls in group x1x\_{1}, we use the threshold q^(x1)\hat{q}^{(x\_{1})} to form the prediction set, and so on.
This choice of 𝒞\mathcal{C} satisfies ([19](#S4.E19 "In 4.1 Group-Balanced Conformal Prediction ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")), as was first documented by Vovk in [vovk2012conditional].

###### Proposition 1 (Error control guarantee for group-balanced conformal prediction).

Suppose (X1,Y1),…,(Xn,Yn),(Xtest,Yt​e​s​t)(X\_{1},Y\_{1}),\dots,\\
(X\_{n},Y\_{n}),(X\_{\text{test}},Y\_{test}) are an i.i.d. sample from some distribution.
Then the set 𝒞\mathcal{C} defined above satisfies the error control property in ([19](#S4.E19 "In 4.1 Group-Balanced Conformal Prediction ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).

### 4.2 Class-Conditional Conformal Prediction

In classification problems, we might similarly ask for coverage on *every* ground truth class.
For example, if we had a medical classifier assigning inputs to class normal or class cancer, we might ask that the prediction sets are 95% accurate both when the ground truth is class cancer and also when the ground truth is class normal.
Formally, we return to the classification setting, where 𝒴={1,…,K}\mathcal{Y}=\{1,...,K\}.
We seek to achieve *class-balanced* coverage,

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ(Ytest∈𝒞(Xtest)|Ytest=y)≥1−α,\mathbb{P}\left(Y\_{\rm test}\in\mathcal{C}(X\_{\rm test})\;\rvert\;Y\_{\rm test}=y\right)\geq 1-\alpha, |  | (23) |

for all classes y∈{1,…,K}y\in\{1,\dots,K\}.

To achieve class-balanced coverage, we will calibrate within each class separately.
The algorithm will be similar to the group-balanced coverage of Section [4.1](#S4.SS1 "4.1 Group-Balanced Conformal Prediction ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), but we must modify it because we do not know the correct class at test time.
(In contrast, in Section [4.1](#S4.SS1 "4.1 Group-Balanced Conformal Prediction ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), we observed the group information Xtest,1X\_{\mathrm{test},1} as an input feature.)
See the visualization below.

![[Uncaptioned image]](2107.07511v6/x27.png)

Turning to the algorithm, given a conformal score function ss, stratify the scores on the calibration set by class,

|  |  |  |  |
| --- | --- | --- | --- |
|  | si(k)=s​(Xj,Yj)​, where ​Yj​ is the ​i​th occurrence of class ​k.s\_{i}^{(k)}=s(X\_{j},Y\_{j})\text{, where }Y\_{j}\text{ is the }i\text{th occurrence of class }k. |  | (24) |

Then, within each class, we calculate the conformal quantile,

|  |  |  |  |
| --- | --- | --- | --- |
|  | q^(k)=Quantile​(s1,…,sn(k);⌈(n(k)+1)​(1−α)⌉n(k))​, where ​n(k)​ is the number of examples of class ​k.\hat{q}^{(k)}=\mathrm{Quantile}\left(s\_{1},...,s\_{n^{(k)}};\frac{\big\lceil(n^{(k)}+1)(1-\alpha)\big\rceil}{n^{(k)}}\right)\text{, where }n^{(k)}\text{ is the number of examples of class }k. |  | (25) |

Finally, we iterate through our classes and include them in the prediction set based on their quantiles:

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(x)={y:s​(x,y)≤q^(y)}.\mathcal{C}(x)=\left\{y:s(x,y)\leq\hat{q}^{(y)}\right\}. |  | (26) |

Notice that in the preceding display, we take a provisional value of the response, yy,
and then use the conformal threshold q^(y)\hat{q}^{(y)} to
determine if it is included in the prediction set.
This choice of 𝒞\mathcal{C} satisfies ([23](#S4.E23 "In 4.2 Class-Conditional Conformal Prediction ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")), as proven by Vovk in [vovk2012conditional]; another version can be found in [Sadinle2016LeastAS].

###### Proposition 2 (Error control guarantee for class-balanced conformal prediction).

Suppose (X1,Y1),…,(Xn,Yn),(Xtest,Yt​e​s​t)(X\_{1},Y\_{1}),\dots,\\
(X\_{n},Y\_{n}),(X\_{\text{test}},Y\_{test}) are an i.i.d. sample from some distribution.
Then the set 𝒞\mathcal{C} defined above satisfies the error control property in ([23](#S4.E23 "In 4.2 Class-Conditional Conformal Prediction ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).

### 4.3 Conformal Risk Control

So far, we have used conformal prediction to construct prediction sets that bound the *miscoverage*,

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ​(Ytest∉𝒞​(Xtest))≤α.\mathbb{P}\Big(Y\_{\rm test}\notin\mathcal{C}(X\_{\rm test})\Big)\leq\alpha. |  | (27) |

However, for many machine learning problems, the natural notion of error is not miscoverage.
Here we show that conformal prediction can also provide guarantees of the form

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝔼​[ℓ​(𝒞​(Xtest),Ytest)]≤α,\mathbb{E}\Big[\ell\big(\mathcal{C}(X\_{\rm test}),Y\_{\rm test}\big)\Big]\leq\alpha, |  | (28) |

for any bounded *loss function* ℓ\ell that shrinks as 𝒞\mathcal{C} grows.
This is called a *conformal risk control* guarantee.
Note that ([28](#S4.E28 "In 4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) recovers ([27](#S4.E27 "In 4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) when using the miscoverage loss, ℓ​(C​(Xtest),Ytest)=𝟙​{Ytest∉C​(Xtest)}\ell\big(C(X\_{\rm test}),Y\_{\rm test}\big)=\mathbbm{1}\left\{Y\_{\rm test}\notin C(X\_{\rm test})\right\}.
However, this algorithm also extends conformal prediction to situations where other loss functions, such as the false negative rate (FNR), are more appropriate.

As an example, consider multilabel classification. Here, the response Yi⊆{1,…,K}Y\_{i}\subseteq\{1,...,K\} a subset of KK classes.
Given a trained model f:𝒳→[0,1]Kf:\mathcal{X}\to[0,1]^{K}, we wish to output sets that include a large fraction of the true classes in YiY\_{i}.
To that end, we post-process the model’s raw outputs into the set of classes with sufficiently high scores, 𝒞λ​(x)={k:f​(X)k≥1−λ}\mathcal{C}\_{\lambda}(x)=\{k:f(X)\_{k}\geq 1-\lambda\}.
Note that as the threshold λ\lambda grows, we include more classes in 𝒞λ​(x)\mathcal{C}\_{\lambda}(x)—it becomes more conservative in that we are less likely to omit true classes.
Conformal risk control can be used to find a threshold value λ^\hat{\lambda} that controls the fraction of missed classes. That is, λ^\hat{\lambda} can be chosen so that the expected value of ℓ​(𝒞λ^​(Xtest),Ytest)=1−|Ytest∩𝒞λ​(Xtest)|/|Ytest|\ell\big(\mathcal{C}\_{\hat{\lambda}}(X\_{\rm test}),Y\_{\rm test}\big)=1-|Y\_{\rm test}\cap\mathcal{C}\_{\lambda}(X\_{\rm test})|/|Y\_{\rm test}| is guaranteed to fall below a user-specified error rate α\alpha.
For example, setting α=0.1\alpha=0.1 ensures that 𝒞λ^​(Xtest)\mathcal{C}\_{\hat{\lambda}}(X\_{\rm test}) contains 90%90\% of the true classes in YtestY\_{\rm test} on average. We will work through a multilabel classification example in detail in Section [5.1](#S5.SS1 "5.1 Multilabel Classification ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").

Formally, we will consider post-processing the predictions of the model ff to create a prediction set 𝒞λ​(⋅)\mathcal{C}\_{\lambda}(\cdot).
The prediction set has a parameter λ\lambda that
encodes its level of conservativeness: larger λ\lambda values yield more conservative outputs (e.g., larger prediction sets).
To measure the quality of the output of 𝒞λ\mathcal{C}\_{\lambda}, we consider a loss function ℓ​(𝒞λ​(x),y)∈(−∞,B]\ell(\mathcal{C}\_{\lambda}(x),y)\in(-\infty,B] for some B<∞B<\infty.
We require the loss function to be non-increasing as a function of λ\lambda.
The following algorithm picks λ^\hat{\lambda} so that risk control as in ([28](#S4.E28 "In 4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) holds:

|  |  |  |  |
| --- | --- | --- | --- |
|  | λ^=inf{λ:R^​(λ)≤α−B−αn},\hat{\lambda}=\inf\left\{\lambda:\widehat{R}(\lambda)\leq\alpha-\frac{B-\alpha}{n}\right\}, |  | (29) |

where R^​(λ)=(ℓ​(𝒞λ​(X1),Y1)+…+ℓ​(𝒞λ​(Xn),Yn))/n\widehat{R}(\lambda)=\big(\ell\big(\mathcal{C}\_{\lambda}(X\_{1}),Y\_{1}\big)+\ldots+\ell\big(\mathcal{C}\_{\lambda}(X\_{n}),Y\_{n}\big)\big)/n is the empirical risk on the calibration data.
Note that this algorithm simply corresponds to tuning based on the empirical risk at a slightly more conservative level than α\alpha.
For example, if B=1B=1, α=0.1\alpha=0.1, and we have n=1000n=1000 calibration points, then we select λ^\hat{\lambda} to be the value where empirical risk hits level λ^=0.0991\hat{\lambda}=0.0991 instead of 0.10.1.

![[Uncaptioned image]](2107.07511v6/x28.png)

Then the prediction set 𝒞λ^​(Xtest)\mathcal{C}\_{\hat{\lambda}}(X\_{\rm test}) satisfies ([28](#S4.E28 "In 4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).

###### Theorem 2 (Conformal Risk Control [angelopoulos2022conformal]).

Suppose (X1,Y1),…,(Xn,Yn),(Xtest,Yt​e​s​t)(X\_{1},Y\_{1}),\dots,(X\_{n},Y\_{n}),(X\_{\text{test}},Y\_{test}) are an i.i.d. sample from some distribution.
Further, suppose ℓ\ell is a monotone function of λ\lambda, i.e., one satisfying

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℓ​(𝒞λ1​(x),y)≥ℓ​(𝒞λ2​(x),y)\ell\big(\mathcal{C}\_{\lambda\_{1}}(x),y\big)\geq\ell\big(\mathcal{C}\_{\lambda\_{2}}(x),y\big) |  | (30) |

for all (x,y)(x,y) and λ1≤λ2\lambda\_{1}\leq\lambda\_{2}. Then

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝔼​[ℓ​(𝒞λ^​(Xtest),Ytest)]≤α,\mathbb{E}\left[\ell\big(\mathcal{C}\_{\hat{\lambda}}(X\_{\rm test}),Y\_{\rm test}\big)\right]\leq\alpha, |  | (31) |

where λ^\hat{\lambda} is picked as in ([29](#S4.E29 "In 4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).

Theory and worked examples of conformal risk control are presented in [angelopoulos2022conformal].
In Sections [5.1](#S5.SS1 "5.1 Multilabel Classification ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") and [5.2](#S5.SS2 "5.2 Tumor Segmentation ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") we show a worked example of conformal risk control applied to tumor segmentation.
Furthermore, Appendix LABEL:app:ltt describes a more powerful technique called Learn then Test [angelopoulos2021learn] capable of controlling general risks that do not satisfy ([30](#S4.E30 "In Theorem 2 (Conformal Risk Control [angelopoulos2022conformal]). ‣ 4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).

### 4.4 Outlier Detection

Conformal prediction can also be adapted to handle unsupervised outlier detection.
Here, we have access to a clean dataset X1,…,XnX\_{1},\dots,X\_{n} and wish to detect when test points do not come from the same distribution.
As before, we begin with a heuristic model that tries to identify outliers;
a larger score means that the model judges the point more likely to be an outlier.
We will then use a variant of conformal prediction to calibrate it
to have statistical guarantees. In particular, we will
guarantee that it does not return too many false positives.

Formally, we will construct a function that labels test points as outliers or inliers, 𝒞:𝒳→{outlier,inlier}\mathcal{C}:\mathcal{X}\to\{\text{outlier},\text{inlier}\}, such that

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ​(𝒞​(Xtest)=outlier)≤α,\mathbb{P}\left(\mathcal{C}(X\_{\text{test}})=\text{outlier}\right)\leq\alpha, |  | (32) |

where the probability is over XtestX\_{\rm test}, a fresh sample from the clean-data distribution.
The algorithm for achieving ([32](#S4.E32 "In 4.4 Outlier Detection ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) is similar to the
usual conformal algorithm. We start with a conformal score s:𝒳→ℝs:\mathcal{X}\to\mathbb{R} (note that
since we are in the unsupervised setting, the score only depends on the features).
Next, we compute the conformal score on the clean data: si=s​(Xi)s\_{i}=s(X\_{i}) for i=1,…,ni=1,\dots,n.
Then, we compute the conformal threshold in the usual way:

|  |  |  |
| --- | --- | --- |
|  | q^=quantile​(s1,…,sn;⌈(n+1)​(1−α)⌉n).\hat{q}=\text{quantile}\left(s\_{1},\ldots,s\_{n};\frac{\big\lceil(n+1)(1-\alpha)\big\rceil}{n}\right). |  |

Lastly, when we encounter a test point, we declare it to be an outlier if the
score exceeds q^\hat{q}:

|  |  |  |
| --- | --- | --- |
|  | 𝒞​(x)={inlier if ​s​(x)≤q^outlier if ​s​(x)>q^.\mathcal{C}(x)=\begin{cases}\text{inlier}&\text{ if }s(x)\leq\hat{q}\\ \text{outlier}&\text{ if }s(x)>\hat{q}\end{cases}. |  |

This construction guarantees error control, as we record next.

###### Proposition 3 (Error control guarantee for outlier detection).

Suppose X1,…,Xn,XtestX\_{1},\dots,X\_{n},X\_{\text{test}} are an i.i.d. sample from some distribution.
Then the set 𝒞\mathcal{C} defined above satisfies the error control property in ([32](#S4.E32 "In 4.4 Outlier Detection ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).

As with standard conformal prediction, the score function is very important for
the method to perform well—that is, to be effective at flagging outliers.
Here, we wish to
choose the score function to effectively distinguish the type of outliers that we expect
to see in the test data from the clean data.
The general problem of training models
to distinguish outliers is sometimes called *anomaly detection*, *novelty detection*, or *one-class classification*, and there are good out-of-the box methods for doing this; see [pimental2014review]
for an overview of outlier detection.
Conformal outlier detection can also be seen as a hypothesis testing problem; points that are rejected as outliers have a p-value less than a​l​p​h​aalpha for the null hypothesis of exchangeability with the calibration data.
This interpretation is closely related to the classical permutation test [fisher1936design, pitman1937significance].
See [vovk2003testing, guan2019prediction, bates2021multiple]
for more on this interpretation and other statistical properties of conformal outlier detection.

### 4.5 Conformal Prediction Under Covariate Shift

All previous conformal methods rely on Theorem [1](#Thmtheorem1 "Theorem 1 (Conformal coverage guarantee; Vovk, Gammerman, and Saunders [vovk1999machine]). ‣ 1.1 Instructions for Conformal Prediction ‣ 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), which assumes that the incoming test points come from the same distribution as the calibration points.
However, past data is not necessarily representative of future data in practice.

One type of distribution shift that conformal prediction can handle is *covariate shift*.
Covariate shift refers to the situation where the distribution of XtestX\_{\rm test} changes from 𝒫\mathcal{P} to 𝒫test\mathcal{P}\_{\rm test}, but the relationship between XtestX\_{\rm test} and YtestY\_{\rm test}, i.e. the distribution of Ytest|XtestY\_{\rm test}|X\_{\rm test}, stays fixed.

![[Uncaptioned image]](2107.07511v6/x29.png)

Imagine our calibration features {Xi}i=1n\{X\_{i}\}\_{i=1}^{n} are drawn independently from 𝒫\mathcal{P} but our test feature XtestX\_{\rm test} is drawn from 𝒫test\mathcal{P}\_{\rm test}.
Then, there has been a covariate shift, and the data are no longer i.i.d.
This problem is common in the real world.
For example,

You are trying to predict diseases from MRI scans.
You conformalized on a balanced dataset of 50% infants and 50% adults, but in reality, the frequency is 5% infants and 95% adults.
Deploying the model in the real world would invalidate coverage; the infants are over-represented in our sample, so diseases present during infancy will be over-predicted.
This was a covariate shift in age.

You are trying to do instance segmentation, i.e., to segment each object in an image from the background.
You collected your calibration images in the morning but seek to deploy your system in the afternoon.
The amount of sunlight has changed, and more people are eating lunch.
This was a covariate shift in the time of day.

To address the covariate shift from 𝒫\mathcal{P} to 𝒫test\mathcal{P}\_{\rm test}, one can form valid prediction sets with *weighted conformal prediction*, first developed in [tibshirani2019conformal].

In weighted conformal prediction, we account for covariate shift by upweighting conformal scores from calibration points that would be more likely under the new distribution.
We will be using the *likelihood ratio*

|  |  |  |  |
| --- | --- | --- | --- |
|  | w​(x)=d​𝒫test​(x)d​𝒫​(x);w(x)=\frac{\mathrm{d}\mathcal{P}\_{\rm test}(x)}{\mathrm{d}\mathcal{P}(x)}; |  | (33) |

usually this is just the ratio of the new PDF to the old PDF at the point xx.
Now we define our weights,

|  |  |  |  |
| --- | --- | --- | --- |
|  | piw​(x)=w​(Xi)∑j=1nw​(Xj)+w​(x)​ and ​ptestw​(x)=w​(x)∑j=1nw​(Xj)+w​(x).p\_{i}^{w}(x)=\frac{w(X\_{i})}{\sum\limits\_{j=1}^{n}w(X\_{j})+w(x)}\;\;\text{ and }\;\;p\_{\rm test}^{w}(x)=\frac{w(x)}{\sum\limits\_{j=1}^{n}w(X\_{j})+w(x)}. |  | (34) |

Intuitively, the weight piw​(x)p\_{i}^{w}(x) is large when XiX\_{i} is likely under the new distribution, and ptestw​(x)p\_{\rm test}^{w}(x) is large when the input xx is likely under the new distribution.
We can then express our conformal quantile as the 1−α1-\alpha quantile of a reweighted distribution,

|  |  |  |  |
| --- | --- | --- | --- |
|  | q^​(x)=inf{sj:∑i=1jpiw​(x)​𝟙​{si≤sj}≥1−α},\hat{q}(x)=\inf\left\{s\_{j}:\sum\limits\_{i=1}^{j}p\_{i}^{w}(x)\mathbbm{1}\left\{s\_{i}\leq s\_{j}\right\}\geq 1-\alpha\right\}, |  | (35) |

where above for notational convenience we assume that the scores are ordered from smallest to largest a-priori.
The choice of quantile is the key step in this algorithm, so we pause to parse it.
First of all, notice that the quantile is now a function of an input xx, although the dependence is only minor.
Choosing piw​(x)=ptestw​(x)=1n+1p\_{i}^{w}(x)=p\_{\rm test}^{w}(x)=\frac{1}{n+1} gives the familiar case of conformal prediction—all points are equally weighted, so we end up choosing the ⌈(n+1)​(1−α)⌉\big\lceil(n+1)(1-\alpha)\big\rceilth-smallest score as our quantile.
When there is covariate shift, we instead re-weight the calibration
points with non-equal weights to match the test distribution.
If the covariate shift makes easier values of xx more likely, it makes our quantile smaller.
This happens because the covariate shift puts more weight on small scores—see the diagram below.
Of course, the opposite holds the covariate shift upweights difficult values of xx: so the covariate-shift-adjusted quantile grows.

![[Uncaptioned image]](2107.07511v6/x30.png)
![[Uncaptioned image]](2107.07511v6/x31.png)

With this quantile function in hand, we form our prediction set in the standard way,

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(x)={y:s​(x,y)≤q^​(x)}.\mathcal{C}(x)=\left\{y:s(x,y)\leq\hat{q}(x)\right\}. |  | (36) |

By accounting for the covariate shift in our choice of q^\hat{q}, we were able to make our calibration data look exchangeable with the test point, achieving the following guarantee.

###### Theorem 3 (Conformal prediction under covariate shift [tibshirani2019conformal]).

Suppose (X1,Y1),…,(Xn,Yn)(X\_{1},Y\_{1}),...,(X\_{n},Y\_{n}) are drawn i.i.d. from 𝒫×𝒫Y|X\mathcal{P}\times\mathcal{P}\_{Y|X} and that (Xtest,Ytest)(X\_{\rm test},Y\_{\rm test}) is drawn independently from 𝒫test×𝒫Y|X\mathcal{P}\_{\rm test}\times\mathcal{P}\_{Y|X}.
Then the choice of 𝒞\mathcal{C} above satisfies

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ​(Ytest∈𝒞​(Xtest))≥1−α.\mathbb{P}\left(Y\_{\rm test}\in\mathcal{C}(X\_{\rm test})\right)\geq 1-\alpha. |  | (37) |

Conformal prediction under various distribution shifts is an active and important area of research with many open challenges.
This algorithm addresses a somewhat restricted case—that of a known covariate shift—but is nonetheless quite practical.

### 4.6 Conformal Prediction Under Distribution Drift

Another common form of distribution shift is *distribution drift*: slowly varying changes in the data distribution.
For example, when collecting time-series data, the data distribution may change—furthermore, it may change in a way that is unknown or difficult to estimate.
Here, one can imagine using weights that give more weight to recent conformal scores.
The following theory provides some justification for such *weighted conformal* procedures; in particular, they always satisfy marginal coverage, and are exact when the magnitude of the distribution shift is known.

More formally, suppose the calibration data {(Xi,Yi)}i=1n\{(X\_{i},Y\_{i})\}\_{i=1}^{n} are drawn independently from different distributions {𝒫i}i=1n\{\mathcal{P}\_{i}\}\_{i=1}^{n} and the test point (Xtest,Ytest)(X\_{\rm test},Y\_{\rm test}) is drawn from 𝒫test\mathcal{P}\_{\rm test}.
Given some weight schedule w1,…,wnw\_{1},...,w\_{n}, wi∈[0,1]w\_{i}\in[0,1], we will consider the calculation of weighted quantiles using the calibration data:

|  |  |  |  |
| --- | --- | --- | --- |
|  | q^=inf{q:∑i=1nw~i​𝟙​{si≤q}≥1−α},\hat{q}=\inf\left\{q:\sum\limits\_{i=1}^{n}\tilde{w}\_{i}\mathbbm{1}\left\{s\_{i}\leq q\right\}\geq 1-\alpha\right\}, |  | (38) |

where the w~i\tilde{w}\_{i} are normalized weights,

|  |  |  |  |
| --- | --- | --- | --- |
|  | w~i=wiw1+…+wn+1.\tilde{w}\_{i}=\frac{w\_{i}}{w\_{1}+\ldots+w\_{n}+1}. |  | (39) |

Then we can construct prediction sets in the usual way,

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(x)={y:s​(x,y)≤q^}.\mathcal{C}(x)=\left\{y:s(x,y)\leq\hat{q}\right\}. |  | (40) |

We now state a theorem showing that when the distribution is shifting, it is a good idea to apply a discount factor to old samples.
In particular, let ϵi=dTV​((Xi,Yi),(Xtest,Ytest))\epsilon\_{i}=\mathrm{d}\_{\rm TV}\big((X\_{i},Y\_{i}),(X\_{\rm test},Y\_{\rm test})\big) be the TV distance between the iith data point and the test data point.
The TV distance is a measure of how much the distribution has shifted—a large ϵi\epsilon\_{i} (close to 11) means the iith data point is not representative of the new test point.
The result states that if ww discounts those points with large shifts, the coverage remains close to 1−α1-\alpha.

###### Theorem 4 (Conformal prediction under distribution drift [barber2022conformal]).

Suppose ϵi=dTV​((Xi,Yi),(Xtest,Ytest))\epsilon\_{i}=\mathrm{d}\_{\rm TV}\big((X\_{i},Y\_{i}),(X\_{\rm test},Y\_{\rm test})\big).
Then the choice of 𝒞\mathcal{C} above satisfies

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ​(Ytest∈𝒞​(Xtest))≥1−α−2​∑i=1nw~i​ϵi.\mathbb{P}\left(Y\_{\rm test}\in\mathcal{C}(X\_{\rm test})\right)\geq 1-\alpha-2\sum\limits\_{i=1}^{n}\tilde{w}\_{i}\epsilon\_{i}. |  | (41) |

When either factor in the product w~i​ϵi\tilde{w}\_{i}\epsilon\_{i} is small, that means that the iith data point doesn’t result in loss of coverage.
In other words, if there isn’t much distribution shift, we can place a high weight on that data point without much penalty, and vice versa.
Setting ϵi=0\epsilon\_{i}=0 above, we can also see that when there is no distribution shift, there is no loss in coverage regardless of what choice of weights is used—this fact had been observed previously in [guan2020conformal, tibshirani2019conformal].

The ϵi\epsilon\_{i} are never known exactly in advance—we only have some heuristic sense of their size.
In practice, for time-series problems, it often suffices to pick either a rolling window of size KK or a smooth decay using some domain knowledge about the speed of the drift:

|  |  |  |  |
| --- | --- | --- | --- |
|  | wifixed=𝟙​{i≥n−K} or widecay=0.99n−i+1.w\_{i}^{\rm fixed}=\mathbbm{1}\left\{i\geq n-K\right\}\qquad\text{ or }\qquad w\_{i}^{\rm decay}=0.99^{n-i+1}. |  | (42) |

We give a worked example of this procedure for a distribution shifting over time in Section [5.3](#S5.SS3 "5.3 Weather Prediction with Time-Series Distribution Shift ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").

As a final point on this algorithm, we note that there is some cost to using this or any other weighted conformal procedure.
In particular, the weights determine the *effective sample size* of the distribution:

|  |  |  |  |
| --- | --- | --- | --- |
|  | neff​(w1,…,wn)=w1+…+wnw12+…+wn2.n^{\rm eff}(w\_{1},\ldots,w\_{n})=\frac{w\_{1}+\ldots+w\_{n}}{w\_{1}^{2}+\ldots+w\_{n}^{2}}. |  | (43) |

This is quite important in practice, since the variance of the weighted conformal procedure can explode when neffn^{\rm eff} is small; as in Section [3](#S3 "3 Evaluating Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), the variance of coverage scales as 1/neff1/\sqrt{n^{\rm eff}}, which can be large if too many of the wiw\_{i} are small.
To see more of the theory of weighted conformal prediction under distribution drift, see [barber2022conformal].

## 5 Worked Examples

We now show several worked examples of the techniques described in Section [4](#S4 "4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
For each example, we provide Jupyter notebooks that allow the results to be conveniently replicated and extended.

### 5.1 Multilabel Classification

![Refer to caption](2107.07511v6/x32.png)
![Refer to caption](2107.07511v6/x34.png)

In the multilabel classification setting, we receive an image and predict which of KK objects are in an image.
We have a pretrained model f^\hat{f} that outputs estimated probabilities for each of the KK classes.
We wish to report on the possible classes contained in the image, returning most of the true labels. To this end, we will threshold the model’s outputs to get the subset of KK classes that the model thinks is most likely, 𝒞λ​(x)={y:f^​(x)≥λ}\mathcal{C}\_{\lambda}(x)=\{y:\hat{f}(x)\geq\lambda\}, which we call the prediction.
We will use conformal risk control (Section [4.3](#S4.SS3 "4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) to pick the threshold value λ\lambda certifying a low *false negative rate* (FNR), i.e., to guarantee the average fraction of ground truth classes that the model missed is less than α\alpha.

More formally, our calibration set {(Xi,Yi)}i=1n\{(X\_{i},Y\_{i})\}\_{i=1}^{n} contains exchangeable images XiX\_{i} and sets of classes Yi⊆{1,…,K}Y\_{i}\subseteq\{1,...,K\}.
With the notation of Section [4.3](#S4.SS3 "4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), we set our loss function to be ℓFNR​(𝒞λ​(x),y)=1−|𝒞λ​(x)∩y|/|y|\ell\_{\rm FNR}(\mathcal{C}\_{\lambda}(x),y)=1-|\mathcal{C}\_{\lambda}(x)\cap y|/|y|.
Then, picking λ^\hat{\lambda} as in [29](#S4.E29 "In 4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") yields a bound on the false negative rate,

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝔼​[ℓFNR​(𝒞λ^​(Xtest),Ytest)]≤α.\mathbb{E}\left[\ell\_{\rm FNR}\big(\mathcal{C}\_{\hat{\lambda}}(X\_{\rm test}),Y\_{\rm test}\big)\right]\leq\alpha. |  | (44) |

Figure [13](#S5.F13 "Figure 13 ‣ 5.1 Multilabel Classification ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") gives results and code for FNR control on the Microsoft Common Objects in Context dataset [lin2014microsoft].

### 5.2 Tumor Segmentation

![Refer to caption](2107.07511v6/x35.png)
![Refer to caption](2107.07511v6/x37.png)

In the tumor segmentation setting, we receive an M×N×3M\times N\times 3 image of a tumor and predict an M×NM\times N binary mask, where ‘1’ indicates a tumor pixel.
We start with a pretrained segmentation model f^\hat{f} that outputs an M×NM\times N grid of the estimated probabilities that each pixel is a tumor pixel.
We will threshold the model’s outputs to get our predicted binary mask, 𝒞λ​(x)={(i,j):f^​(x)(i,j)≥λ}\mathcal{C}\_{\lambda}(x)=\{(i,j):\hat{f}(x)\_{(i,j)}\geq\lambda\}, which we call the prediction.
We will use conformal risk control (Section [4.3](#S4.SS3 "4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) to pick the threshold value λ\lambda certifying a low FNR, i.e., guaranteeing the average fraction of tumor pixels missed is less than α\alpha.

More formally, our calibration set {(Xi,Yi)}i=1n\{(X\_{i},Y\_{i})\}\_{i=1}^{n} contains exchangeable images XiX\_{i} and sets of tumor pixels Yi⊆{1,…,M}×{1,…,N}Y\_{i}\subseteq\{1,\ldots,M\}\times\{1,\ldots,N\}.
As in the previous example, we let the loss be the false negative proportion, ℓFNR\ell\_{\rm FNR}.
Then, picking λ^\hat{\lambda} as in [29](#S4.E29 "In 4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") yields the bound on the FNR in [44](#S5.E44 "In 5.1 Multilabel Classification ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
Figure [14](#S5.F14 "Figure 14 ‣ 5.2 Tumor Segmentation ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") gives results and code on a dataset of gut polyps.

### 5.3 Weather Prediction with Time-Series Distribution Shift

![Refer to caption](2107.07511v6/x38.png)
![Refer to caption](2107.07511v6/x40.png)

In this example we seek to predict the temperature of different locations on Earth given covariates such as the latitude, longitude, altitude, atmospheric pressure, and so on.
We will make these predictions serially in time.
Dependencies between adjacent data points induced by local and global weather changes violate the standard exchangeability assumption, so we will need to apply the method from Section [4.6](#S4.SS6 "4.6 Conformal Prediction Under Distribution Drift ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").

In this setting, we have a time series {(Xt,Yt)}t=1T\big\{(X\_{t},Y\_{t})\big\}\_{t=1}^{T}, where the XtX\_{t} are tabular covariates and the Yt∈ℝY\_{t}\in\mathbb{R} are temperatures in degrees Celsius.
Note that these data points are not exchangeable or i.i.d.; adjacent data points will be correlated.
We start with a pretrained model f^\hat{f} taking features and predicting temperature and an uncertainty model u^\hat{u} takes features and outputs a scalar notion of uncertainty.
Following Section [2.3](#S2.SS3 "2.3 Conformalizing Scalar Uncertainty Estimates ‣ 2 Examples of Conformal Procedures ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), we compute the conformal scores

|  |  |  |  |
| --- | --- | --- | --- |
|  | st=|Yt−f^​(Xt)|u^​(Xt).s\_{t}=\frac{\big|Y\_{t}-\hat{f}(X\_{t})\big|}{\hat{u}(X\_{t})}. |  | (45) |

Since we observe the data points sequentially, we also observe the scores sequentially, and we will need to pick a different conformal quantile for each incoming data point.
More formally, consider the task of predicting the temperature at time t≤Tt\leq T.
We use the weighted conformal technique in Section [5.3](#S5.SS3 "5.3 Weather Prediction with Time-Series Distribution Shift ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") with the fixed KK-sized window wt′=𝟙​{t′≥t−K}w\_{t^{\prime}}=\mathbbm{1}\left\{t^{\prime}\geq t-K\right\} for all t′<tt^{\prime}<t.
This yields the quantiles

|  |  |  |  |
| --- | --- | --- | --- |
|  | q^t=inf{q:1min⁡(K,t′−1)+1​∑t′=1t−1st′​𝟙​{t′≥t−K}≥1−α}.\hat{q}\_{t}=\inf\left\{q:\frac{1}{\min(K,t^{\prime}-1)+1}\sum\limits\_{t^{\prime}=1}^{t-1}s\_{t^{\prime}}\mathbbm{1}\left\{t^{\prime}\geq t-K\right\}\geq 1-\alpha\right\}. |  | (46) |

With these adjusted quantiles in hand, we form prediction sets at each time step in the usual way,

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(Xt)=[f^​(Xt)−q^t​u^​(Xt),f^​(Xt)+q^t​u^​(Xt)].\mathcal{C}(X\_{t})=\Big[\hat{f}(X\_{t})-\hat{q}\_{t}\hat{u}(X\_{t})\;,\;\hat{f}(X\_{t})+\hat{q}\_{t}\hat{u}(X\_{t})\Big]. |  | (47) |

We run this procedure on the Yandex Weather Prediction dataset.
This dataset is part of the Shifts Project [malinin2021shifts], which also provides an ensemble of 10 pretrained CatBoost [dorogush2018catboost] models for making the temperature predictions.
We take the average prediction of these models as our base model f^\hat{f}.
Each of the models has its own internal variance; we take the average of these variances as our uncertainty scalar u^\hat{u}.
The dataset includes an in-distribution split of fresh data from the same time frame that the base model was trained and an out-of-distribution split consisting of time windows the model has never seen.
We concatenate these datasets in time, leading to a large change point in the score distribution.
Results in Figure [15](#S5.F15 "Figure 15 ‣ 5.3 Weather Prediction with Time-Series Distribution Shift ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") show that the weighted method works better than a naive unweighted conformal baseline, achieving the desired coverage in steady-state and recovering quickly from the change point.
There is no hope of measuring the TV distance between adjacent data points in order to apply Theorem [4](#Thmtheorem4 "Theorem 4 (Conformal prediction under distribution drift [barber2022conformal]). ‣ 4.6 Conformal Prediction Under Distribution Drift ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), so we cannot get a formal coverage bound.
Nonetheless, the procedure is useful with this simple fixed window of weights, which we chose with only a heuristic understanding of the distribution drift speed.
It is worth noting that conformal prediction for time-series applications is a particularly active area of research currently, and the method we have presented is not clearly the best. See [gibbs2021adaptive, zaffran2022adaptive, gibbs2022conformal] and [xu2021conformal] for two differing perspectives.

### 5.4 Toxic Online Comment Identification via Outlier Detection

![Refer to caption](2107.07511v6/x41.png)
![Refer to caption](2107.07511v6/x43.png)

We provide a type-1 error guarantee on a model that flags toxic online comments, such as threats, obscenity, insults, and identity-based hate.
Suppose we are given nn non-toxic text samples X1,…,XnX\_{1},...,X\_{n} and asked whether a new text sample XtestX\_{\rm test} is toxic.
We also have a pre-trained toxicity prediction model f^​(x)∈[0,1]\hat{f}(x)\in[0,1], where values closer to 1 indicate a higher level of toxicity.
The goal is to flag as many toxic comments as possible while not flagging more than α\alpha proportion of non-toxic comments.

The outlier detection procedure in Section [4.4](#S4.SS4 "4.4 Outlier Detection ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") applies immediately.
First, we run the model on each calibration point, yielding conformal scores si=f^​(Xi)s\_{i}=\hat{f}(X\_{i}).
Taking the toxicity threshold q^\hat{q} to be the ⌈(n+1)​(1−α)⌉\lceil(n+1)(1-\alpha)\rceil-smallest of the sis\_{i}, we construct the function

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(x)={inlierf^​(x)≤q^outlierf^​(x)>q^.\mathcal{C}(x)=\begin{cases}\mathrm{inlier}&\hat{f}(x)\leq\hat{q}\\ \mathrm{outlier}&\hat{f}(x)>\hat{q}.\end{cases} |  | (48) |

This gives the guarantee in Proposition [3](#Thmprop3 "Proposition 3 (Error control guarantee for outlier detection). ‣ 4.4 Outlier Detection ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")—no more than α\alpha fraction of future nontoxic text will be classified as toxic.

Figure [16](#S5.F16 "Figure 16 ‣ 5.4 Toxic Online Comment Identification via Outlier Detection ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") shows results of this procedure using the Unitary Detoxify BERT-based model [hanu2020detoxify, devlin2018bert] on the Jigsaw Multilingual Toxic Comment Classification dataset from the WILDS benchmark [koh2021wilds].
It is composed of comments from the talk channels of Wikipedia pages.
With a type-1 error of α=10%\alpha=10\%, the system correctly flags 70%70\% of all toxic comments.

### 5.5 Selective Classification

![Refer to caption](2107.07511v6/x44.png)
![Refer to caption](2107.07511v6/x46.png)

In many situations, we only want to show a model’s predictions when it is confident.
For example, we may only want to make medical diagnoses when the model will be 95% accurate, and otherwise to say “I don’t know.”
We next demonstrate a system that strategically abstains in order to achieve a higher accuracy than the base model in the problem of image classification.

More formally, given image-class pairs {(Xi,Yi)}i=1n\{(X\_{i},Y\_{i})\}\_{i=1}^{n} and an image classifier f^\hat{f}, we seek to ensure

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ​(Ytest=Y^​(Xtest)|P^​(Xtest)≥λ^)≥1−α,\mathbb{P}\left(Y\_{\rm test}=\widehat{Y}(X\_{\rm test})\>\big|\widehat{P}(X\_{\rm test})\geq\hat{\lambda}\right)\geq 1-\alpha, |  | (49) |

where Y^​(x)=arg⁡maxy⁡f^​(x)y\widehat{Y}(x)=\arg\max\_{y}\,\hat{f}(x)\_{y}, P^​(Xtest)=maxy⁡f^​(x)y\widehat{P}(X\_{\rm test})=\max\_{y}\,\hat{f}(x)\_{y}, and λ^\hat{\lambda} is a threshold chosen using the calibration data.
This is called a *selective accuracy* guarantee, because the accuracy is only computed over a subset of high-confidence predictions. This quantity cannot be controlled with techniques we’ve seen so far, since we are not guaranteed that model accuracy is monotone in the cutoff λ\lambda.
Nonetheless, it can be handled with Learn then Test—a framework for controlling arbitrary risks (see Appendix LABEL:app:ltt).
We show only the special case of controlling selective classification accuracy here.

We pick the threshold using based on the empirical estimate of selective accuracy on the calibration set,

|  |  |  |  |
| --- | --- | --- | --- |
|  | R^​(λ)=1n​(λ)​∑i=1n𝟙​{Yi≠Y^​(Xi)​ and ​P^​(Xi)≥λ}, where ​n​(λ)=∑i=1n𝟙​{P^​(Xi)≥λ}.\widehat{R}(\lambda)=\frac{1}{n(\lambda)}\sum\limits\_{i=1}^{n}\mathbbm{1}\left\{Y\_{i}\neq\widehat{Y}(X\_{i})\text{ and }\widehat{P}(X\_{i})\geq\lambda\right\},\text{ where }n(\lambda)=\sum\limits\_{i=1}^{n}\mathbbm{1}\left\{\widehat{P}(X\_{i})\geq\lambda\right\}. |  | (50) |

Since this function is not monotone in λ\lambda, we will choose λ^\hat{\lambda} differently than in Section [4.3](#S4.SS3 "4.3 Conformal Risk Control ‣ 4 Extensions of Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"). In particular, we will scan across values of λ\lambda looking at a conservative upper bound for the true risk (i.e., the top end of a confidence interval for the selective misclassification rate).
Realizing that R^​(λ)\widehat{R}(\lambda) is a Binomial random variable with n​(λ)n(\lambda) trials, we upper-bound the misclassification error as

|  |  |  |  |
| --- | --- | --- | --- |
|  | R^+​(λ)=sup{r:BinomCDF​(R^​(λ);n​(λ),r)≥δ}\widehat{R}^{+}(\lambda)=\sup\left\{r\>:\>\text{BinomCDF}(\widehat{R}(\lambda);\>n(\lambda),r)\geq\delta\right\} |  | (51) |

for some user-specified failure rate δ∈[0,1]\delta\in[0,1].
Then, scan the upper bound until the last time the bound exceeds α\alpha,

|  |  |  |  |
| --- | --- | --- | --- |
|  | λ^=inf{λ:R^+​(λ′)≤α​ for all ​λ′≥λ}.\hat{\lambda}=\inf\left\{\lambda:\widehat{R}^{+}(\lambda^{\prime})\leq\alpha\text{ for all }\lambda^{\prime}\geq\lambda\right\}. |  | (52) |

Deploying the threshold λ^\hat{\lambda} will satisfy ([49](#S5.E49 "In 5.5 Selective Classification ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) with high probability.

###### Proposition 4.

Assume the {(Xi,Yi)}i=1n\{(X\_{i},Y\_{i})\}\_{i=1}^{n} and (Xtest,Ytest)(X\_{\rm test},Y\_{\rm test}) are i.i.d. and λ^\hat{\lambda} is chosen as above. Then ([49](#S5.E49 "In 5.5 Selective Classification ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) is satisfied with probability 1−δ1-\delta.

See results on Imagenet at level α=0.1\alpha=0.1 in Figure [17](#S5.F17 "Figure 17 ‣ 5.5 Selective Classification ‣ 5 Worked Examples ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
For a deeper dive into this procedure and techniques for controlling other non-monotone risks, see Appendix LABEL:app:ltt.

## 6 Full conformal prediction

Up to this point, we have only considered *split conformal prediction*, otherwise known as inductive conformal prediction.
This version of conformal prediction is computationally attractive, since it only requires fitting the model one time, but it sacrifices statistical efficiency because it requires splitting the data into training and calibration datasets.
Next, we consider *full conformal prediction*, or transductive conformal prediction, which avoids data splitting at the cost of many more model fits.
Historically, full conformal prediction was developed first, and then split conformal prediction was later recognized as an important special case.
Next, we describe full conformal prediction. This discussion is motivated from three points of view. First, full conformal prediction is an elegant, historically important idea in our field.
Second, the exposition will reveal a complimentary interpretation of conformal prediction as a hypothesis test.
Lastly, full conformal prediction is a useful algorithm when statistical efficiency is of paramount importance.

### 6.1 Full Conformal Prediction

This topic requires expanded notation.
Let (X1,Y1),…,(Xn+1,Yn+1)(X\_{1},Y\_{1}),\dots,(X\_{n+1},Y\_{n+1}) be n+1n+1 exchangeable data points.
As before, the user sees (X1,Y1),…,(Xn,Yn)(X\_{1},Y\_{1}),\dots,(X\_{n},Y\_{n}) and Xn+1X\_{n+1}, and wishes to make a prediction set that contains Yn+1Y\_{n+1}.
But unlike split conformal prediction, we allow the model to train on all the data points, so there is no separate calibration dataset.

The core idea of full conformal prediction is as follows.
We know that the true label, Yn+1Y\_{n+1}, lives somewhere in 𝒴\mathcal{Y} — so if we loop over all possible y∈𝒴y\in\mathcal{Y}, then we will eventually hit the data point (Xn+1,Yn+1)(X\_{n+1},Y\_{n+1}), which is exchangeable with the first nn data points.
Full conformal prediction is so-named because it directly computes this loop.
For each y∈𝒴y\in\mathcal{Y}, we fit a new model f^y\hat{f}^{y} to the augmented dataset (X1,Y1),…,(Xn+1,y)(X\_{1},Y\_{1}),\ldots,(X\_{n+1},y).
Importantly, the model fitting for f^\hat{f} must be invariant to permutations of the data.
Then, we compute a score function siy=s​(Xi,Yi,f^y)s\_{i}^{y}=s(X\_{i},Y\_{i},\hat{f}^{y}) for i = 1,…,n and sn+1y=s​(Xn+1,y,f^y)s\_{n+1}^{y}=s(X\_{n+1},y,\hat{f}^{y}).
This score function is exactly the same as those from Section [2](#S2 "2 Examples of Conformal Procedures ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), except that the model f^y\hat{f}^{y} is now given as an argument because it is no longer fixed.
Then, we calculate the conformal quantile,

|  |  |  |  |
| --- | --- | --- | --- |
|  | q^y=Quantile​(s1y,…,sny;⌈(n+1)​(1−α)⌉n).\hat{q}^{y}=\mathrm{Quantile}\left(s\_{1}^{y},\ldots,s\_{n}^{y};\frac{\lceil(n+1)(1-\alpha)\rceil}{n}\right). |  | (53) |

Then, we collect all values of yy that are sufficiently consistent with the previous data (X1,Y1),…,(Xn,Yn)(X\_{1},Y\_{1}),\dots,(X\_{n},Y\_{n}) are collected into a confidence set for the unknown value of Yn+1Y\_{n+1}:

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒞​(Xtest)={y:sn+1y≤q^y}.\mathcal{C}(X\_{\rm test})=\{y:s^{y}\_{n+1}\leq\hat{q}^{y}\}. |  | (54) |

This prediction set has the same validity guarantee as before:

###### Theorem 5 (Full conformal coverage guarantee [vovk2005algorithmic]).

Suppose (X1,Y1),…,(Xn+1,Yn+1)(X\_{1},Y\_{1}),...,(X\_{n+1},Y\_{n+1}) are drawn i.i.d. from 𝒫\mathcal{P}, and that f^\hat{f} is a symmetric algorithm.
Then the choice of 𝒞\mathcal{C} above satisfies

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℙ​(Yn+1∈𝒞​(Xn+1))≥1−α.\mathbb{P}\left(Y\_{n+1}\in\mathcal{C}(X\_{n+1})\right)\geq 1-\alpha. |  | (55) |

More generally, the above holds for exchangeable random variables (X1,Y1),…,(Xn+1,Yn+1)(X\_{1},Y\_{1}),...,(X\_{n+1},Y\_{n+1}); the proof of Theorem [5](#Thmtheorem5 "Theorem 5 (Full conformal coverage guarantee [vovk2005algorithmic]). ‣ 6.1 Full Conformal Prediction ‣ 6 Full conformal prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification") critically relies on the fact that the score sn+1Yn+1s\_{n+1}^{Y\_{n+1}} is exchangeable with s1Yn+1,…,snYn+1s\_{1}^{Y\_{n+1}},\ldots,s\_{n}^{Y\_{n+1}}. We defer the proof to [vovk2005algorithmic], and note that upper bound in ([1](#S1.E1 "In 1 Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) also holds when the score function is continuous.

What about computation?
In principle, to compute ([54](#S6.E54 "In 6.1 Full Conformal Prediction ‣ 6 Full conformal prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")), we must iterate over all y∈𝒴y\in\mathcal{Y}, which leads to a substantial computational burden.
(When 𝒴\mathcal{Y} is continuous, we would typically first discretize the space and then check each element in a finite set.)
For example, if |Y|=K|Y|=K, then computing ([54](#S6.E54 "In 6.1 Full Conformal Prediction ‣ 6 Full conformal prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) requires (n+1)⋅K(n+1)\cdot K model fits.
For some specific score functions, the set in ([54](#S6.E54 "In 6.1 Full Conformal Prediction ‣ 6 Full conformal prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")) can actually be computed exactly even for continuous YY, and we refer the reader to [vovk2005algorithmic] and [shafer2008tutorial] for a summary of such cases and [ndiaye2019, Ndiaye2022root-finding] for recent developments.
Still, full conformal prediction is generally computationally costly.

Lastly, we give a statistical interpretation for the prediction set in ([54](#S6.E54 "In 6.1 Full Conformal Prediction ‣ 6 Full conformal prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).
The condition

|  |  |  |  |
| --- | --- | --- | --- |
|  | sn+1y≤q^ys^{y}\_{n+1}\leq\hat{q}^{y} |  | (56) |

is equivalent to the acceptance condition of a certain permutation test.
To see this, consider a level α\alpha permutation test for the exchangeability of s1y,…,snys\_{1}^{y},\dots,s\_{n}^{y} and the test score sn+1ys\_{n+1}^{y}, rejecting when the score function is large.
The values of yy such that the test does not reject are exactly those in ([54](#S6.E54 "In 6.1 Full Conformal Prediction ‣ 6 Full conformal prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification")).
In words, the confidence set is all values of yy such that the hypothetical data point is consistent with the other data, as judged by this permutation test.
We again refer the reader to [vovk2005algorithmic] for more on this viewpoint on conformal prediction.

### 6.2 Cross-Conformal Prediction, CV+, and Jackknife+

Split conformal prediction requires only one model fitting step, but sacrifices statistical efficiency. On the other hand, full conformal prediction requires a very large number of model fitting steps, but has high statistical efficiency. These are not the only two achievable points on the spectrum—there are techniques that fall in between, trading off statistical efficiency and computational efficiency differently. In particular, cross-conformal prediction [vovk2015cross] and CV+/Jackknife+ [barber2021predictive] both use a small number of model fits, but still use all data for both model fitting and calibration. We refer the reader to those works for a precise description of the algorithms and corresponding statistical guarantees.

## 7 Historical Notes on Conformal Prediction

We hope the reader has enjoyed reading the technical content in our gentle introduction.
As a dénouement, we now pay homage to the history of conformal prediction. Specifically, we will trace the history of techniques related to conformal prediction that are distribution-free, i.e., (1) agnostic to the model, (2) agnostic to the data distribution, and (3) valid in finite samples.
There are other lines of work in statistics with equal claim to the term “distribution-free” especially when it is interpreted asymptotically, such as permutation tests [chung2013exact], quantile regression [koenker1978regression], rank tests [mann1947test, lehmann1953power, sidak1999theory], and even the bootstrap [efron1994introduction, chatterjee2009distribution]—the following is not a history of those topics.
Rather, we focus on the progenitors and progeny of conformal prediction.

### Origins

The story of conformal prediction begins sixty-three kilometers north of the seventh-largest city in Ukraine, in the mining town of Chervonohrad in the Oblast of Lviv, where Vladimir Vovk spent his childhood.
Vladimir’s parents were both medical professionals, of Ukrainian descent, although the Lviv region changed hands many times over the years.
During his early education, Vovk recalls having very few exams, with grades mostly based on oral answers.
He did well in school and eventually took first place in the Mathematics Olympiad in Ukraine; he also got a Gold Medal, meaning he was one of the top graduating secondary school students.
Perhaps because he was precocious, his math teacher would occupy him in class by giving him copies of a magazine formerly edited by Isaak Kikoin and Andrey Kolmogorov, [Kvant](https://archive.org/details/kvant-journal), where he learned about physics, mathematics, and engineering—see Figure [18](#S7.F18 "Figure 18 ‣ Origins ‣ 7 Historical Notes on Conformal Prediction ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
Vladimir originally attended the Moscow Second Medical Institute (now called the Russian National Research Medical University) studying Biological Cybernetics, but eventually became disillusioned with the program, which had too much of a medical emphasis and imposed requirements to take classes like anatomy and physiology (there were “too many bones with strange Latin names”).
Therefore, he sat the entrance exams a second time and restarted school at the Mekh-Mat (faculty of mechanics and mathematics) in Moscow State University.
In his third year there, he became the student of Andrey Kolmogorov.
This was when the seeds of conformal prediction were first laid.
Today, Vladimir Vovk is widely recognized for being the co-inventor of conformal prediction, along with collaborators Alexander Gammerman, Vladimir Vapnik, and others, whose contributions we will soon discuss.
First, we will relay some of the historical roots of conformal prediction, along with some oral history related by Vovk that may be forgotten if never written.

![Refer to caption](2107.07511v6/figures/volodya.jpg)
![Refer to caption](2107.07511v6/figures/quant.png)

Kolmogorov and Vovk met approximately once a week during his three remaining years as an undergraduate at MSU.
At that time, Kolmogorov took an interest in Vovk, and encouraged him to work on difficult mathematical problems.
Ultimately, Vovk settled on studying a topic of interest to Kolmogorov: algorithmically random sequences, then known as *collectives*, and which were modified into *Bernoulli sequences* by Kolmogorov.

Work on collectives began at the turn of the 20th century, with Gustav Fechner’s *Kollectivmasslehre* [fechner1897kollektivmasslehre], and was developed significantly by von Mises [mises1919grundlagen], Abraham Wald [wald1937widerspruchfreiheit], Alonzo Church [church1940concept], and so on.
A long debate ensued among these statisticians as to whether von Mises’ axioms formed a valid foundation for probability, with Jean Ville being a notable opponent [ville1939etude].
Although the theory of von Mises’ collectives is somewhat defunct, the mathematical ideas generated during this time continue to have a broad impact on statistics, as we will see.
More careful historical reviews of the original debate on collectives exist elsewhere [shafer2006sources, church1940concept, vovk2001kolmogorov, porter2014kolmogorov].
We focus on its connection to the development of conformal prediction.

Kolmogorov’s interest in *Bernoulli sequences* continued into the 1970s and 1980s, when Vovk was his student.
Vovk recalls that, on the way to the train station, Kolmogorov told him (not in these exact words),

“Look around you; you do not only see infinite sequences. There are finite sequences.”

Feeling that the finite case was practically important, Kolmogorov extended the idea of collectives via Bernoulli sequences.

###### Definition 1 (Bernoulli sequence, informal).

A deterministic binary sequence of length n with k 1s is Bernoulli if it is a “random” element of the set of all (nk)\binom{n}{k} sequences of the same length and with the same number of 1s. “Random” is defined as having a Kolmogorov complexity close to the maximum, log⁡(nk)\log\binom{n}{k}.

As is typical in the study of random sequences, the underlying object itself is not a sequence of random variables. Rather, Kolmogorov quantified the “typicality” of a sequence via Kolmogorov complexity: he asked how long a program we would need to write in order to distinguish it from other sequences in the same space [kolmogorov1965three, kolmogorov1968logical, kolmogorov1983combinatorial].
Vovk’s first work on random sequences modified Kolmogorov’s [vovk1986firstpaper] definition to better reflect the randomness in an event like a coin toss.
Vovk discusses the history of Bernoulli sequences, including the important work done by Martin-Löf and Levin, in the Appendix of [vovk2021testing].
Learning the theory of Bernoulli sequences brought Vovk closer to understanding finite-sample exchangeability and its role in prediction problems.

We will make a last note about the contributions of the early probabilists before moving to the modern day.
The concept of a nonconformity score came from the idea of (local) *randomness deficiency*.
Consider the sequence

|  |  |  |  |
| --- | --- | --- | --- |
|  | 00000000000000000000000000000000000000000000000000000000000000000001.00000000000000000000000000000000000000000000000000000000000000000001. |  | (57) |

With a computer, we could write a very short program to identify the ‘1’ in the sequence, since it is atypical — it has a *large* randomness deficiency.
But to identify any particular ‘0’ in the sequence, we must specify its location, because it is so typical — it has a *small* randomness deficiency.
A heuristic understanding suffices here, and we defer the formal definition of randomness deficiency to [mota2013sophistication], avoiding the notation of Turing machines and Kolmogorov complexity.
When randomness deficiency is large, a point is atypical, just like the scores we discussed in Section [2](#S2 "2 Examples of Conformal Procedures ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
These ideas, along with the existing statistical literature on tolerance intervals [wilks1941, wilks1942, wald1943, tukey1947] and works related to de Finetti’s theorems on exchangeability [diaconis1980finite, aldous1985exchangeability, de1929funzione, freedman1965bernard, hewitt1955symmetric, kingman1978uses] formed the seedcorn for conformal prediction: the rough notion of collectives eventually became exchangeability, and the idea of randomness deficiency eventually became nonconformity.
Furthermore, the early literature on tolerance intervals was quite close mathematically to conformal prediction—indeed, the fact that order statistics of a uniform distribution are Beta distributed was known at the time, and this was used to form prediction regions in high probability, much like [vovk2012conditional]; more on this connection is available in Edgar Dobriban’s lecture notes [dobriban2022topics].

### Enter Conformal Prediction

The framework we now call conformal prediction was hatched by Vladimir Vovk, Alexander Gammerman, Craig Saunders, and Vladimir Vapnik in the years 1996-1999, first using e-values [gammerman1998learning] and then with p-values [saunders1999transduction, vovk1999machine].
For decades, Vovk and collaborators developed the theory and applications of conformal prediction.
Key moments include:

the 2002 proof that in online conformal prediction, the probability of error is independent across time-steps [vovk2002line];

the 2002 development, along with Harris Papadopoulos and Kostas Proedrou, of split-conformal predictors [papadopoulos2002inductive];

Glenn Shafer coins the term “conformal predictor” on December 1, 2003 while writing *Algorithmic Learning in a Random World* with Vovk [vovk2005algorithmic].

the 2003 development of Venn Predictors [vovk2003self] (Vovk says this idea came to him on a bus in Germany during the Dagstuhl seminar “Kolmogorov Complexity & Applications”);

the 2012 founding of the Symposium on Conformal and Probabilistic Prediction and its Applications (COPA), hosted in Greece by Harris Papadopoulos and colleagues;

the 2012 creation of cross-conformal predictors [vovk2015cross] and Venn-Abers predictors [vovk2012venn];

The 2017 invention of conformal predictive distributions [vovk2017nonparametric].

[*Algorithmic Learning in a Random World*](http://alrw.net/) [vovk2005algorithmic], by Vovk, Gammerman, and Glenn Shafer, contains further perspective on the history described above in the bibliography of Chapter 2 and the main text of Chapter 10.
Also, the book’s website links to several dozen technical reports on conformal prediction and related topics.
We now help the reader understand some of these key developments.

Conformal prediction was recently popularized in the United States by the pioneering work of Jing Lei, Larry Wasserman, and colleagues [lei2011efficient, lei2014distribution, lei2013distribution, poczos2013distribution, lei2014distribution, lei2018distribution].
Vovk himself remembers Wasserman’s involvement as a landmark moment in the history of the field.
In particular, their general framework for distribution-free predictive inference in regression [lei2018distribution] has been a seminal work.
They have also, in the special cases of kernel density estimation and kernel regression, created efficient approximations to full conformal prediction [lei2013conformal, lei2014distribution].
Jing Lei also created a fast and exact conformalization of the Lasso and elastic net procedures [lei2019fast].
Another equally important contribution of theirs was to introduce conformal prediction to thousands of researchers, including the authors of this paper, and also Rina Barber, Emmanuel Candès, Aaditya Ramdas, Ryan Tibshirani who themselves have made recent fundamental contributions.
Some of these we have already touched upon in Section [2](#S2 "2 Examples of Conformal Procedures ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"), such as adaptive prediction sets, conformalized quantile regression, covariate-shift conformal, and the idea of conformal prediction as indexing nested sets [gupta2020nested].

This group also did fundamental work circumscribing the conditions under which distribution-free conditional guarantees can exist [foygel2021limits], building on previous works by Vovk, Lei, and Wasserman that showed for an arbitrary continuous distribution, conditional coverage is impossible [vovk2012conditional, lei2014distribution, lei2018distribution].
More fine-grained analysis of this fact has also recently been done in [lee2021distribution], showing that vanishing-width intervals are achievable if and only if the effective support size of the distribution of XtestX\_{\rm test} is smaller than the square of the sample size.

### Current Trends

We now discuss recent work in conformal prediction and distribution-free uncertainty quantification more generally, providing pointers to topics we did not discuss in earlier sections.
Many of the papers we cite here would be great starting points for novel research on distribution-free methods.

Many recent papers have focused on designing conformal procedures to have good practical performance according to specific desiderata like small set sizes [Sadinle2016LeastAS], coverage that is approximately balanced across regions of feature space [foygel2021limits, izbicki2019flexible, romano2020classification, cauchois2020knowing, guan2020conformal, angelopoulos2020sets], and errors balanced across classes [lei2014classification, Sadinle2016LeastAS, hechtlinger2018cautious, guan2019prediction].
This usually involves adjusting the conformal score; we gave many examples of such adjustments in Section [2](#S2 "2 Examples of Conformal Procedures ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
Good conformal scores can also be trained with data to optimize more complicated desiderata [stutz2021learning].

Many statistical extensions to conformal prediction have also emerged.
Such extensions include the ideas of risk control [angelopoulos2020sets, angelopoulos2021learn] and covariate shift [tibshirani2019conformal] that we previously discussed.
One important and continual area of work is distribution shift, where our test point has a different distribution from our calibration data.
For example, [cauchois2020robust] builds a conformal procedure robust to shifts of known ff-divergence in the score function, and adaptive conformal prediction [gibbs2021adaptive] forms prediction sets in a data stream where the distribution varies over time in an unknown fashion by constantly re-estimating the conformal quantile.
A weighted version of conformal prediction pioneered by [barber2022conformal] provides tools for addressing non-exchangeable data, most notably slowly changing time-series.
This same work develops techniques for applying full conformal prediction to asymmetric algorithms.
Beyond distribution shift, recent statistical extensions also address topics such as creating reliable conformal prediction intervals for counterfactuals and individual treatment effects [lei2020conformal, yin2021conformal, chernozhukov2021exact], covariate-dependent lower bounds on survival times [candes2021conformalized], prediction sets that preserve the privacy of the calibration data [angelopoulos2021private], handling dependent data [chernozhukov2018exact, dunn2018distribution, oliveira2022split], and achieving ‘multivalid’ coverage that is conditionally valid with respect to several possibly overlapping groups [bastani2022practical, jung2022batch].

Furthermore, prediction sets are not the only important form of distribution-free uncertainty quantification.
One alternative form is a *conformal predictive distribution*, which outputs a probability distribution over the response space 𝒴\mathcal{Y} in a regression problem [vovk2017nonparametric].
Recent work also addresses the issue of calibrating a scalar notion of uncertainty to have probabilistic meaning via histogram binning [gupta2021distribution, park2021pac]—this is like a rigorous version of Platt scaling or isotonic regression.
The tools from conformal prediction can also be used to identify times when the distribution of data has changed by examining the score function’s behavior on new data points.
For example, [bates2021multiple] performs outlier detection using conformal prediction, [vovk2021testing, volkhonskiy2017inductive] detect change points in time-series data, [hu2020distributionfree] tests for covariate shift between two datasets, and [podkopaev2021tracking] tracks the risk of a predictor on a data-stream to identify when harmful changes in its distribution (one that increases the risk) occur.

Developing better estimators of uncertainty improves the practical effectiveness of conformal prediction.
The literature on this topic is too wide to even begin discussing; instead, we point to quantile regression as an example of a fruitful line of work that mingled especially nicely with conformal prediction in Section [2.2](#S2.SS2 "2.2 Conformalized Quantile Regression ‣ 2 Examples of Conformal Procedures ‣ A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification").
Quantile regression was first proposed in [koenker1978regression] and extended to the locally polynomial case in [chaudhuri1991global].
Under sufficient regularity, quantile regression converges uniformly to the true quantile function [chaudhuri1991global, steinwart2011estimating, takeuchi2006nonparametric, zhou1996direct, zhou1998statistical].
Practical and accessible references for quantile regression have been written by Koenker and collaborators [koenker2005quantile, koenker2018handbook].
Active work continues today to analyze the statistical properties of quantile regression and its variants under different conditions, for example in additive models [koenker2011additive] or to improve conditional coverage when the size of the intervals may correlate with miscoverage events [feldman2021improving].
The Handbook of Quantile Regression [koenker2018handbook] includes more detail on such topics, and a memoir of quantile regression for the interested reader.
Since quantile regression provides intervals with near-conditional coverage asymptotically, the conformalized version inherits this good behavior as well.

Along with such statistical advances has come a recent wave of practical applications of conformal prediction.
Conformal prediction in large-scale deep learning was studied in [angelopoulos2020sets], focusing on image classification.
One compelling use-case of conformal prediction is speeding up and decreasing the computational cost of the test-time evaluation of complex models [fisch2020efficient, schuster2021consistent].
The same researchers pooled information across multiple tasks in a meta-learning setup to form tight prediction sets for few-shot prediction [fisch2021few].
There is also an earlier line of work, appearing slightly after that of Lei and Wasserman, applying conformal prediction to decision trees [johansson2014regression, linusson2017calibration, bostrom2017accelerating].
Closer to end-users, we are aware of several real applications of conformal prediction.
The Washington Post estimated the number of outstanding Democratic and Republican votes in the 2020 United States presidential election using conformal prediction [cherian2020washington].
Early clinical experiments in hospitals underscore the utility of conformal prediction in that setting as well, although real deployments are still to come [lu2021distribution, lu2021fair].
Fairness and reliability of algorithmic risk forecasts in the criminal justice system improves (on controlled datasets) when applying conformal prediction [Romano2020With, kuchibhotla2021nested, lu2021fair].
Conformal prediction was recently applied to create safe robotic planning algorithms that avoid bumping into objects [lindemann2022safe, dixit2022adaptive].
Recently a scikit-learn compatible open-source library, [MAPIE](https://github.com/scikit-learn-contrib/MAPIE), has been developed for constructing conformal prediction intervals.
There remains a mountain of future work in these applications of conformal prediction and many others.

Today, the field of distribution-free uncertainty quantification remains small, but grows rapidly year-on-year.
The promulgation of machine learning deployments has caused a reckoning that point predictions are not enough and shown that we still need rigorous statistical inference for reliable decision-making.
Many researchers around the world have keyed into this fact and have created new algorithms and software using distribution-free ideas like conformal prediction.
These developments are numerous and high-quality, so most reviews are out-of-date.
To keep track of what gets released, the reader may want to see the [Awesome Conformal Prediction](https://github.com/valeman/awesome-conformal-prediction) repository [acp], which provides a frequently-updated list of resources in this area.

We will end our Gentle Introduction with a personal note to the reader—you can be part of this story too.
The infant field of distribution-free uncertainty quantification has ample room for significant technical contributions.
Furthermore, the concepts are practical and approachable; they can easily be understood and implemented in code.
Thus, we encourage the reader to try their hand at distribution-free uncertainty quantification; there is a lot more to be done!

![[LOGO]](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)

## Instructions for reporting errors

We are continuing to improve HTML versions of papers, and your feedback helps enhance accessibility and mobile
support. To report errors in the HTML that will help us improve conversion and rendering, choose any of the
methods listed below:

**Tip:** You can select the relevant text first, to include it in your report.

Our team has already identified [the following issues](https://github.com/arXiv/html_feedback/issues). We appreciate your time reviewing and reporting rendering errors we
may not have found yet. Your efforts will help us improve the HTML versions for all readers, because disability
should not be a barrier to accessing research. Thank you for your continued support in championing open access for
all.

Have a free development cycle? Help support accessibility at arXiv! Our collaborators at LaTeXML maintain a [list of packages that need conversion](https://github.com/brucemiller/LaTeXML/wiki/Porting-LaTeX-packages-for-LaTeXML), and welcome [developer contributions](https://github.com/brucemiller/LaTeXML/issues).
