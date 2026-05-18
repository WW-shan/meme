 Selective Conformal Risk Control




##### Report GitHub Issue

×

Title:

Content selection saved. Describe the issue below:

Description:

Submit without GitHub Submit in GitHub


[![arXiv logo](/static/browse/0.3.4/images/arxiv-logo-one-color-white.svg) Back to arXiv](/)

[Why HTML?](https://info.arxiv.org/about/accessible_HTML.html)  [Report Issue](# "Report an Issue")  [Back to Abstract](/abs/2512.12844v2 "Back to abstract page")   [Download PDF](/pdf/2512.12844v2 "Download PDF")



1. [Abstract](#abstract1 "In Selective Conformal Risk Control")
2. [1 Introduction](#S1 "In Selective Conformal Risk Control")
3. [2 Problem Formulation](#S2 "In Selective Conformal Risk Control")
   1. [Selective Conformal Risk Control.](#S2.SS0.SSS0.Px1 "In 2 Problem Formulation ‣ Selective Conformal Risk Control")
4. [3 Related Work](#S3 "In Selective Conformal Risk Control")
   1. [Conformal Prediction.](#S3.SS0.SSS0.Px1 "In 3 Related Work ‣ Selective Conformal Risk Control")
   2. [Selective Classification.](#S3.SS0.SSS0.Px2 "In 3 Related Work ‣ Selective Conformal Risk Control")
   3. [Conformal Prediction and Selective Classification.](#S3.SS0.SSS0.Px3 "In 3 Related Work ‣ Selective Conformal Risk Control")
5. [4 Method](#S4 "In Selective Conformal Risk Control")
   1. [4.1 Conditional Exchangeability](#S4.SS1 "In 4 Method ‣ Selective Conformal Risk Control")
   2. [4.2 First Stage Control](#S4.SS2 "In 4 Method ‣ Selective Conformal Risk Control")
   3. [4.3 Second Stage Control](#S4.SS3 "In 4 Method ‣ Selective Conformal Risk Control")
   4. [4.4 Set-Size Refinement](#S4.SS4 "In 4 Method ‣ Selective Conformal Risk Control")
   5. [4.5 Calibration-only Variant](#S4.SS5 "In 4 Method ‣ Selective Conformal Risk Control")
6. [5 Experiments](#S5 "In Selective Conformal Risk Control")
   1. [5.1 Experiment Setup](#S5.SS1 "In 5 Experiments ‣ Selective Conformal Risk Control")
      1. [Model and score preparation.](#S5.SS1.SSS0.Px1 "In 5.1 Experiment Setup ‣ 5 Experiments ‣ Selective Conformal Risk Control")
      2. [Compared Methods](#S5.SS1.SSS0.Px2 "In 5.1 Experiment Setup ‣ 5 Experiments ‣ Selective Conformal Risk Control")
      3. [Evaluation protocol.](#S5.SS1.SSS0.Px3 "In 5.1 Experiment Setup ‣ 5 Experiments ‣ Selective Conformal Risk Control")
   2. [5.2 CIFAR-10 Dataset](#S5.SS2 "In 5 Experiments ‣ Selective Conformal Risk Control")
      1. [Coverage control.](#S5.SS2.SSS0.Px1 "In 5.2 CIFAR-10 Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control")
      2. [Risk control.](#S5.SS2.SSS0.Px2 "In 5.2 CIFAR-10 Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control")
      3. [Comparison of SCRC-T and SCRC-I.](#S5.SS2.SSS0.Px3 "In 5.2 CIFAR-10 Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control")
      4. [Effect of score functions.](#S5.SS2.SSS0.Px4 "In 5.2 CIFAR-10 Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control")
      5. [Effect of δ\delta for SCRC-I.](#S5.SS2.SSS0.Px5 "In 5.2 CIFAR-10 Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control")
   3. [5.3 Diabetic Retinopathy Detection Dataset](#S5.SS3 "In 5 Experiments ‣ Selective Conformal Risk Control")
      1. [Coverage and risk control.](#S5.SS3.SSS0.Px1 "In 5.3 Diabetic Retinopathy Detection Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control")
      2. [Comparison of methods.](#S5.SS3.SSS0.Px2 "In 5.3 Diabetic Retinopathy Detection Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control")
      3. [Effect of score functions and δ\delta.](#S5.SS3.SSS0.Px3 "In 5.3 Diabetic Retinopathy Detection Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control")
7. [6 Conclusions](#S6 "In Selective Conformal Risk Control")
8. [References](#bib "In Selective Conformal Risk Control")


[License: CC BY 4.0](https://info.arxiv.org/help/license/index.html#licenses-available)

arXiv:2512.12844v2 [cs.LG] 27 Apr 2026

# Selective Conformal Risk Control

Yunpeng Xu1     Wenge Guo2     Zhi Wei1
 1Department of Computer Science, New Jersey Institute of Technology
2Department of Mathematical Sciences, New Jersey Institute of Technology

###### Abstract

Reliable uncertainty quantification is essential for deploying machine learning systems in high-stakes domains. Conformal prediction provides distribution-free coverage guarantees but often yields overly large prediction sets, limiting its practical utility. To address this limitation, we propose Selective Conformal Risk Control (SCRC), a unified framework that integrates conformal prediction with selective classification. SCRC operates in a selective setting: it abstains on low-confidence inputs and applies conformal risk control only to the accepted subset, where compact and informative prediction sets are most valuable. The framework formulates uncertainty control as a two-stage procedure. The first stage selects confident samples, while the second stage constructs calibrated prediction sets via conformal risk control. We develop two variants: SCRC-T, a transductive method that preserves exchangeability and achieves exact finite-sample guarantees at the cost of per-test recomputation, and SCRC-I, an inductive alternative that reuses calibration thresholds to provide PAC-style guarantees with improved computational efficiency. Experiments on two benchmark datasets demonstrate that both methods achieve the desired coverage and risk levels with nearly identical performance. SCRC-I is slightly more conservative but substantially more practical for deployment. Overall, SCRC improves the efficiency of uncertainty quantification on accepted samples while explicitly deferring uncertain cases for abstention or downstream handling.

## 1 Introduction

Despite growing research on uncertainty quantification, many real-world machine learning systems still provide predictions without transparent confidence assessments. In high-stakes domains such as medical diagnosis, autonomous driving, or financial decision-making, this absence of uncertainty information makes it difficult to assess how much one can trust a given prediction, potentially leading to critical failures. Therefore, quantifying and controlling predictive uncertainty has become a key requirement for building reliable machine learning systems.

To address this need, a wide range of methods have been developed to estimate and communicate predictive uncertainty, spanning both Bayesian approaches such as [[5](#bib.bib15 "Weight uncertainty in neural networks"), [10](#bib.bib12 "Dropout as a bayesian approximation: representing model uncertainty in deep learning")], and calibration-based techniques such as [[14](#bib.bib14 "On calibration of modern neural networks"), [19](#bib.bib16 "Accurate uncertainties for deep learning using calibrated regression"), [27](#bib.bib17 "Evaluating model calibration in classification")].

As a popular uncertain quantization method, conformal prediction [[2](#bib.bib6 "A gentle introduction to conformal prediction and distribution-free uncertainty quantification"), [1](#bib.bib9 "Conformal risk control"), [8](#bib.bib18 "Conformal prediction sets with limited false positives")] received a lot of attention in recent years. The method produces a prediction set by post-processing the model output such that a bigger prediction size corresponds to a less confident inference and vice versa. It is distribution-free, with finite-sample and model-agnostic coverage guarantees.

On the other hand, however, conformal prediction often suffers from inefficiency in practice: to meet the desired coverage level, the resulting prediction sets can be excessively large, sometimes including most or all possible labels. This greatly limits its usefulness in real-world applications, for example medical diagnosis, where compact and actionable prediction sets are critical. Reducing the prediction set size without compromising the risk guarantee is therefore a central challenge in improving the practicality of conformal prediction.

A related and complementary approach is selective classification [[6](#bib.bib1 "An optimum character recognition system using decision functions"), [16](#bib.bib2 "The nearest neighbor classification rule with a reject option"), [12](#bib.bib3 "Selective classification for deep neural networks"), [13](#bib.bib4 "SelectiveNet: a deep neural network with an integrated reject option")], which has been well studied in machine learning field for several decades. It introduces a reject option: the model abstains from making a prediction when it is uncertain. By adjusting the rejection threshold, the model can trade off coverage (fraction of predictions made) against accuracy (risk).

Selective classification provides a natural mechanism to improve the efficiency of conformal prediction. Instead of producing large prediction sets for all samples and attempting to provide improved uncertainty quantification uniformly, the model can abstain on uncertain inputs and focus on the accepted subset. This allows for smaller average prediction set sizes on the selected (high-confidence) samples while maintaining overall risk control. Combining the coverage guarantee of conformal prediction with the flexibility of selective classification can thus yield more efficient and practically useful uncertainty quantification.

In this work, we propose a unified framework, Selective Conformal Risk Control (SCRC), that integrates conformal prediction with selective classification. The proposed method introduces a two-stage risk control procedure: the first stage determines which samples to accept for prediction (selection control), and the second stage constructs conformal prediction sets for the accepted samples (risk control). This combination allows the model to produce informative prediction sets only when confident and to abstain otherwise, leading to a more compact and interpretable uncertainty representation. Accordingly, the guarantees in our framework are selective: they apply to the accepted subpopulation, while rejected cases are intentionally deferred rather than assigned a possibly uninformative prediction set.

We further develop two algorithmic variants to serve complementary roles: SCRC-T, a transductive method that computes thresholds symmetrically over calibration and test data, with strict exchangeability guarantees; SCRC-I, a more computationally efficient variant that reuses calibration thresholds across test samples, with PAC-style high-probability guarantees. Both methods ensure risk and coverage control, with theoretical guarantees derived under the conformal risk control framework. Empirical evaluations demonstrate that our proposed methods achieve the desired risk and coverage levels while significantly reducing prediction set sizes compared to standard conformal prediction.

To summarize, this paper makes the following contributions:

* •

  We propose Selective Conformal Risk Control, by combining conformal risk control and selective classification into a unified two-stage uncertainty quantification framework.
* •

  We develop two practical algorithms: SCRC-T and SCRC-I, which ensure valid risk and coverage control under different computational trade-offs.
* •

  We establish theoretical results for the proposed methods.
* •

  We provide extensive experiments to validate the proposed methods.

## 2 Problem Formulation

Selective classification provides a mechanism for models to abstain from making uncertain predictions, allowing a trade-off between coverage and accuracy. Given an input space 𝒳\mathcal{X} and label space 𝒴={1,…,K}\mathcal{Y}=\{1,\dots,K\}, let f:𝒳→[0,1]Kf:\mathcal{X}\rightarrow[0,1]^{K} denote a base classifier producing class scores for KK classes, and g:𝒳→[0,1]g:\mathcal{X}\rightarrow[0,1] denote a selection function that measures confidence. For a selection threshold λ∈[0,1]\lambda\in[0,1], the model outputs

|  |  |
| --- | --- |
| y^​(x)={f​(x),if ​g​(x)≥1−λ,®,otherwise,\hat{y}(x)=\begin{cases}f(x),&\text{if }g(x)\geq 1-\lambda,\\ \circledR,&\text{otherwise,}\end{cases} | (1) |

where ®\circledR indicates rejection. The overall prediction coverage and conditional classification risk are defined respectively as

|  |  |  |
| --- | --- | --- |
| ϕ​(f,g)\displaystyle\phi(f,g) | =ℙ​(g​(X)≥1−λ),\displaystyle=\mathbb{P}(g(X)\geq 1-\lambda), | (2) |
|  |  |  |
| --- | --- | --- |
| R​(f,g)\displaystyle R(f,g) | =𝔼​[l​(f​(X),Y)∣g​(X)≥1−λ],\displaystyle=\mathbb{E}[\,l(f(X),Y)\mid g(X)\geq 1-\lambda\,], | (3) |

where ll is a bounded loss function measuring the classification error. A conventional selective classifier often seeks an optimal g​(x)g(x) that minimizes the conditional risk under a coverage constraint:

|  |  |
| --- | --- |
| ming⁡R​(f,g)s.t. ​ϕ​(f,g)≥ξ.\min\_{g}\;R(f,g)\quad\text{s.t. }\phi(f,g)\geq\xi. | (4) |

In this work, we are not concerned with learning ff or gg directly. Instead, we assume both are fixed and focus on calibrating their outputs to guarantee the desired risk and coverage levels under the conformal prediction framework. To that end, we introduce the Selective Conformal Risk Control problem.

#### Selective Conformal Risk Control.

Let 𝐙={(xi,yi)}i=1n\mathbf{Z}=\{(x\_{i},y\_{i})\}\_{i=1}^{n} be an exchangeable calibration dataset, where each sample is associated with model outputs (fi,gi)(f\_{i},g\_{i}). For a new test instance Xn+1X\_{n+1} and its corresponding score pair (fn+1,gn+1)(f\_{n+1},g\_{n+1}), we determine its selective prediction 𝒞​(Xn+1)∈{®}∪2𝒴\mathcal{C}(X\_{n+1})\in\{\circledR\}\cup 2^{\mathcal{Y}}, by post-processing the model score pair (fn+1,gn+1)(f\_{n+1},g\_{n+1}) using calibration data, where 𝒞\mathcal{C} is a function of the models as well as the calibration set.

Specifically, we introduce two calibration thresholds λ=(λ1,λ2)\lambda=(\lambda\_{1},\lambda\_{2}), and decide the output of Xn+1X\_{n+1} as:

|  |  |
| --- | --- |
| 𝒞​(Xn+1)={®,g​(Xn+1)<1−λ1,Cλ2​(Xn+1),otherwise.\mathcal{C}(X\_{n+1})=\begin{cases}\circledR,&g(X\_{n+1})<1-\lambda\_{1},\\ C\_{\lambda\_{2}}(X\_{n+1}),&\text{otherwise.}\end{cases} | (5) |

where Cλ2​(Xn+1)C\_{\lambda\_{2}}(X\_{n+1}) denotes a prediction set constructed according to threshold λ2\lambda\_{2}. In this work we use

|  |
| --- |
| Cλ2​(Xn+1)={k∈{1,…,K}:f​(Xn+1)k≥1−λ2},C\_{\lambda\_{2}}(X\_{n+1})=\{k\in\{1,\dots,K\}:f(X\_{n+1})\_{k}\geq 1-\lambda\_{2}\}, |

although other set-construction rules could also be employed.

The first-stage threshold λ1\lambda\_{1} controls which examples are accepted for prediction, while the second-stage threshold λ2\lambda\_{2} determines the size of the prediction set for the accepted cases. We evaluate selective performance using

|  |  |  |
| --- | --- | --- |
| R​(f,g)\displaystyle R(f,g) | =𝔼​[l​(𝒞λ2​(Xn+1),Yn+1)∣g​(Xn+1)≥1−λ1],\displaystyle=\mathbb{E}\big[l(\mathcal{C}\_{\lambda\_{2}}(X\_{n+1}),Y\_{n+1})\mid g(X\_{n+1})\geq 1-\lambda\_{1}\big], | (6) |
|  |  |  |
| --- | --- | --- |
| ϕ​(f,g)\displaystyle\phi(f,g) | =ℙ​(g​(Xn+1)≥1−λ1),\displaystyle=\mathbb{P}(g(X\_{n+1})\geq 1-\lambda\_{1}), | (7) |

where l​(𝒞λ2​(Xn+1),Yn+1)∈[0,1]l(\mathcal{C}\_{\lambda\_{2}}(X\_{n+1}),Y\_{n+1})\in[0,1] is a bounded, monotonically decreasing loss function that diminishes as the prediction set 𝒞λ2​(Xn+1)\mathcal{C}\_{\lambda\_{2}}(X\_{n+1}) expands.

Since the expected set size conditional on acceptance is an indicator of prediction efficiency, our goal is therefore to find calibration parameters (λ1,λ2)(\lambda\_{1},\lambda\_{2}) that satisfy the selective coverage ξ\xi and risk α\alpha requirements, while minimizing the expected prediction set size:

|  |  |  |
| --- | --- | --- |
| min(λ1,λ2)\displaystyle\min\_{(\lambda\_{1},\lambda\_{2})} | 𝔼​[|𝒞λ2​(Xn+1)|∣g​(Xn+1)≥1−λ1]\displaystyle\mathbb{E}\big[|\mathcal{C}\_{\lambda\_{2}}(X\_{n+1})|\mid g(X\_{n+1})\geq 1-\lambda\_{1}\big] | (8) |
| s.t. | R​(f,g)≤α,ϕ​(f,g)≥ξ.\displaystyle R(f,g)\leq\alpha,\quad\phi(f,g)\geq\xi. |

This defines the Selective Conformal Classification Problem. The minimization of the conditional prediction set size prevents trivial solutions (e.g., always predict or include all labels), ensuring an efficient and informative prediction.

## 3 Related Work

#### Conformal Prediction.

Conformal prediction (CP), originally developed by Vovk and colleagues [[28](#bib.bib7 "Machine-learning applications of algorithmic randomness"), [29](#bib.bib8 "Algorithmic learning in a random world")], is a foundational framework for distribution-free uncertainty quantification in machine learning. It provides finite-sample coverage guarantees under the assumption of data exchangeability, enabling rigorous uncertainty calibration without relying on parametric assumptions. A wide range of CP variants have been developed, including inductive and split conformal prediction [[22](#bib.bib20 "Inductive confidence machines for regression"), [20](#bib.bib21 "Distribution-free predictive inference for regression")], conformalized quantile regression [[24](#bib.bib22 "Conformalized quantile regression")], and covariate-shift adaptation [[26](#bib.bib23 "Conformal prediction under covariate shift")], as well as limited false positives control [[8](#bib.bib18 "Conformal prediction sets with limited false positives")]. Comprehensive overviews of this field can be found in [[2](#bib.bib6 "A gentle introduction to conformal prediction and distribution-free uncertainty quantification"), [25](#bib.bib19 "A tutorial on conformal prediction")], which review both theoretical foundations and practical applications across regression, classification, and structured prediction tasks.

Recent research has reframed CP through the lens of *risk control*[[1](#bib.bib9 "Conformal risk control")]: instead of targeting a coverage guarantee, conformal risk control (CRC) directly constrains the expected loss of the prediction at a target level α\alpha. This generalization extends the scope of the classical CP and enables it for many new applications. Our work is conceptually aligned with this framework.

#### Selective Classification.

Selective classification (also known as classification with a reject option) has received extensive studies in the past few decades. The foundational studies by [[6](#bib.bib1 "An optimum character recognition system using decision functions"), [16](#bib.bib2 "The nearest neighbor classification rule with a reject option")] established optimal decision rules under the reject option. Since then, numerous selective classification methods have been introduced, including [[4](#bib.bib27 "Classification with a reject option using a hinge loss"), [12](#bib.bib3 "Selective classification for deep neural networks"), [13](#bib.bib4 "SelectiveNet: a deep neural network with an integrated reject option"), [9](#bib.bib25 "Optimal strategies for reject option classifiers"), [23](#bib.bib26 "AUC-based selective classification")]. These methods provide a principled trade-off between accuracy and coverage, by allowing models to abstain from making a prediction when it is uncertain. A comprehensive survey of machine learning approaches with rejection is provided by [[17](#bib.bib24 "Machine learning with a reject option: a survey")].

#### Conformal Prediction and Selective Classification.

A small but growing body of research integrates conformal prediction or calibration with selective classification principles. [[7](#bib.bib5 "Calibrated selective classification")] developed a calibrated selective classification framework that trains a selection model to ensure that accepted predictions remain probability-calibrated. [[3](#bib.bib28 "Selective conformal inference with false coverage-statement rate control")] introduced selective conditional conformal prediction with false coverage rate (FCR) control. [[11](#bib.bib29 "Selecting informative conformal prediction sets with false coverage rate control")] further developed two informative selective CP procedures that guarantee FCR while constraining informativeness. In contrast, our method addresses a distinct but complementary problem: we formulate a two-stage selective conformal risk-control framework that simultaneously enforces coverage and conditional risk guarantees on accepted samples, while minimizing the expected prediction set size to improve efficiency.

## 4 Method

The problem naturally involves two stages, selection and classification, each targeting a distinct risk control objective. This formulation is conceptually related to the two-stage risk control framework introduced in [[31](#bib.bib31 "Two-stage risk control with application to ranked retrieval")]. However, the selective setting presents a critical challenge: the act of selection disrupts exchangeability between calibration and test samples, a key condition for applying the conformal risk control (CRC) framework. As a result, the existing two-stage method cannot be directly applied without modification. We therefore develop a new approach tailored to selective classification.

### 4.1 Conditional Exchangeability

To invoke standard results from the CRC framework, we first need to address the question of exchangeability after selection.

###### Lemma 1.

Suppose (X1,Y1),…,(Xn+1,Yn+1)\left(X\_{1},Y\_{1}\right),\ldots,\left(X\_{n+1},Y\_{n+1}\right) are exchangeable, and let ℐ\mathcal{I} be a symmetric selection rule, meaning that for any dataset 𝒟\mathcal{D}, any permutation σ\sigma of [n+1][n+1], and any index i∈[n+1]i\in[n+1],

|  |
| --- |
| σ​(i)∈ℐ​(𝒟)⟺i∈ℐ​(𝒟σ),\sigma(i)\in\mathcal{I}(\mathcal{D})\Longleftrightarrow i\in\mathcal{I}\left(\mathcal{D}^{\sigma}\right), |

where 𝒟σ={(Xσ​(i),Yσ​(i))}i=1n+1\mathcal{D}^{\sigma}=\{(X\_{\sigma(i)},Y\_{\sigma(i)})\}\_{i=1}^{n+1} denotes the permutated dataset. Let ℰI\mathcal{E}\_{I} denote the event that ℐ​(𝒟)=I\mathcal{I}\left(\mathcal{D}\right)=I, for some fixed nonempty subset I⊆[n+I\subseteq[n+ 1]1], and assume ℙ​(ℰI)>0\mathbb{P}\left(\mathcal{E}\_{I}\right)>0. Then, conditional on ℰI\mathcal{E}\_{I}, the subcollection {(Xi,Yi)}i∈I\left\{\left(X\_{i},Y\_{i}\right)\right\}\_{i\in I} is exchangeable.

###### Proof.

Let A⊂(𝒳×𝒴)|I|A\subset(\mathcal{X}\times\mathcal{Y})^{|I|} be a measurable set of values for the data pairs. Let π\pi be any permutation of the index set II, and extend it to a permutation σ\sigma on the full set of indices [n+1][n+1] as follows,

|  |
| --- |
| σ​(i)={π​(i)for i∈Iifor i∉I\sigma(i)=\begin{cases}\pi(i)&\text{for $i\in I$}\\ i&\text{for $i\notin I$}\end{cases} |

Since II is a set, we have σ​(I)=I\sigma(I)=I. We aim to show that

|  |
| --- |
| P​((Xi,Yi)i∈I∈A|ℰI)=P​((Xπ​(i),Yπ​(i))i∈I∈A|ℰI).P((X\_{i},Y\_{i})\_{i\in I}\in A|\mathcal{E}\_{I})=P((X\_{\pi(i)},Y\_{\pi(i)})\_{i\in I}\in A|\mathcal{E}\_{I}). |

Start from the numerator of the conditional probability, and write it as an expectation of an indicator:

|  |
| --- |
| P​((Xi,Yi)i∈I∈A,ℰI)=E​[𝟏{(Xi,Yi)i∈I∈A}​𝟏ℰI].P((X\_{i},Y\_{i})\_{i\in I}\in A,\mathcal{E}\_{I})=E[\mathbf{1}\_{\{(X\_{i},Y\_{i})\_{i\in I}\in A\}}\mathbf{1}\_{\mathcal{E}\_{I}}]. |

By exchangeability of the full dataset, we have

|  |
| --- |
| E​[𝟏{(Xi,Yi)i∈I∈A}​𝟏ℰI]=E​[𝟏{(Xσ​(i),Yσ​(i))i∈I∈A}​𝟏ℰIσ],E[\mathbf{1}\_{\{(X\_{i},Y\_{i})\_{i\in I}\in A\}}\mathbf{1}\_{\mathcal{E}\_{I}}]=E[\mathbf{1}\_{\{(X\_{\sigma(i)},Y\_{\sigma(i)})\_{i\in I}\in A\}}\mathbf{1}\_{\mathcal{E}\_{I\_{\sigma}}}], |

where ℰIσ\mathcal{E}\_{I\_{\sigma}} is the event that ℐ​(Dσ)=I\mathcal{I}(D^{\sigma})=I. By symmetry of the selection rule ℐ\mathcal{I}, we have ℐ​(Dσ)=σ​(ℐ​(D))\mathcal{I}(D^{\sigma})=\sigma(\mathcal{I}(D)). Since σ​(I)=I\sigma(I)=I, it follows that 𝟏​(ℰIσ)=𝟏​(ℰI)\mathbf{1}(\mathcal{E}\_{I\_{\sigma}})=\mathbf{1}(\mathcal{E}\_{I}), therefore,

|  |
| --- |
| P​((Xi,Yi)i∈I∈A,ℰI)=P​((Xσ​(i),Yσ​(i))i∈I∈A,ℰI)=P​((Xπ​(i),Yπ​(i))i∈I∈A,ℰI).P((X\_{i},Y\_{i})\_{i\in I}\in A,{\mathcal{E}\_{I}})=P((X\_{\sigma(i)},Y\_{\sigma(i)})\_{i\in I}\in A,{\mathcal{E}\_{I}})=P((X\_{\pi(i)},Y\_{\pi(i)})\_{i\in I}\in A,{\mathcal{E}\_{I}}). |

∎

### 4.2 First Stage Control

Lemma [1](#Thmtheorem1 "Lemma 1. ‣ 4.1 Conditional Exchangeability ‣ 4 Method ‣ Selective Conformal Risk Control") says that to preserve exchangeability, the selection rule employed in the first stage must be symmetric. This requirement motivates a modification to the standard first-stage risk control procedure.

In the first stage, the loss function depends solely on the feature XX, rather than on the full data pair (X,Y)(X,Y). The threshold λ1\lambda\_{1} is determined by computing the empirical quantile of the feature-dependent loss values over both calibration and test samples, yielding the estimator λ^1\hat{\lambda}\_{1}. Because this construction treats all features symmetrically, λ^1\hat{\lambda}\_{1} is a symmetric function of (X1,…,Xn+1)(X\_{1},\ldots,X\_{n+1}). This design contrasts with the standard CRC method, where the threshold is estimated using only the calibration data and is independent of the test data, thus breaking symmetry and invalidating exchangeability in the selective setting.

Formally, define the first-stage loss function as

|  |  |
| --- | --- |
| L(1)​(X;λ1)=𝟏​{g​(X)<1−λ1}.L^{(1)}(X;\lambda\_{1})=\mathbf{1}\{g(X)<1-\lambda\_{1}\}. | (9) |

Given calibration features (X1,…,Xn)(X\_{1},\dots,X\_{n}) and test feature Xn+1X\_{n+1}, the empirical first stage risk is

|  |  |
| --- | --- |
| R^n+1(1)​(λ1)=1n+1​∑i=1n+1L(1)​(Xi,λ1).\widehat{R}\_{n+1}^{(1)}(\lambda\_{1})=\frac{1}{n+1}\sum\_{i=1}^{n+1}L^{(1)}(X\_{i},\lambda\_{1}). | (10) |

The data-driven threshold is then defined by

|  |  |
| --- | --- |
| λ^1=inf{λ1∈Λ1:R^n+1(1)​(λ1)≤1−ξ}.\hat{\lambda}\_{1}=\inf\left\{\lambda\_{1}\in\Lambda\_{1}:\widehat{R}\_{n+1}^{(1)}(\lambda\_{1})\leq 1-\xi\right\}. | (11) |

By this construction, λ^1\hat{\lambda}\_{1} is a symmetric function of the feature values (X1,…,Xn+1)(X\_{1},\ldots,X\_{n+1}). Therefore, under the exchangeability assumption on (X1,…,Xn+1)(X\_{1},\ldots,X\_{n+1}) and by Lemma [1](#Thmtheorem1 "Lemma 1. ‣ 4.1 Conditional Exchangeability ‣ 4 Method ‣ Selective Conformal Risk Control"), the selection event defined through λ^1\hat{\lambda}\_{1} preserves exchangeability, ensuring that ℙ​(g​(Xn+1)≥1−λ^1)≥ξ\mathbb{P}(g(X\_{n+1})\geq 1-\hat{\lambda}\_{1})\geq\xi. This establishes valid first-stage risk control while maintaining the symmetry required for the second-stage analysis.

### 4.3 Second Stage Control

Once λ^1\hat{\lambda}\_{1} is determined, the selection rule ℐ\mathcal{I} is defined as

|  |  |
| --- | --- |
| ℐ​(X1,…,Xn+1)={i∈[n+1]:g​(Xi)≥1−λ^1}.\mathcal{I}\left(X\_{1},\ldots,X\_{n+1}\right)=\left\{i\in[n+1]:g\left(X\_{i}\right)\geq 1-\hat{\lambda}\_{1}\right\}. | (12) |

This rule is symmetric with respect to the inputs (X1,…,Xn+1)(X\_{1},\ldots,X\_{n+1}), since it depends only on the symmetric threshold λ^1\hat{\lambda}\_{1} and applies the same elementwise comparison to each feature.

By Lemma [1](#Thmtheorem1 "Lemma 1. ‣ 4.1 Conditional Exchangeability ‣ 4 Method ‣ Selective Conformal Risk Control"), let ℰI\mathcal{E}\_{I} denote the event that ℐ​(X1,…,Xn+1)=I\mathcal{I}(X\_{1},\ldots,X\_{n+1})=I for some fixed nonempty subset I⊆[n+1]I\subseteq[n+1] with n+1∈In+1\in I, and assume ℙ​(ℰI)>0\mathbb{P}(\mathcal{E}\_{I})>0. Then, conditional on ℰI\mathcal{E}\_{I}, the subcollection {(Xi,Yi)}i∈I\left\{(X\_{i},Y\_{i})\right\}\_{i\in I} is exchangeable. Therefore, the standard CRC procedure can be applied to this selected subset to estimate the second-stage threshold λ^2\hat{\lambda}\_{2}, ensuring conditional risk control at level α\alpha.

Formally, for a fixed candidate value λ¯1∈[0,1]\bar{\lambda}\_{1}\in[0,1], define the selected calibration subset

|  |  |
| --- | --- |
| Zλ¯1={(Xi,Yi):g​(Xi)≥1−λ¯1,i∈[n]}.Z\_{\bar{\lambda}\_{1}}=\{(X\_{i},Y\_{i}):g(X\_{i})\geq 1-\bar{\lambda}\_{1},\;i\in[n]\}. | (13) |

We denote its cardinality by m=|Zλ¯1|\quad m=|Z\_{\bar{\lambda}\_{1}}|. In practice, the search over λ¯1\bar{\lambda}\_{1} is restricted to the interval [λ^1,1][\hat{\lambda}\_{1},1] to reduce computation.

Define the second-stage loss as

|  |  |
| --- | --- |
| L(2)​(X,Y;λ2)=l​(Cλ2​(X),Y),L^{(2)}(X,Y;\lambda\_{2})=l(C\_{\lambda\_{2}}(X),Y), | (14) |

which is assumed to be bounded in [0,1][0,1] and non-increasing in λ2\lambda\_{2}.

The conformal risk control (CRC) rule chooses the largest feasible threshold

|  |  |
| --- | --- |
| λ^2=i​n​f​{λ2∈[0,1]:∑(Xi,Yi)∈Zλ¯1l​(𝒞λ2​(Xi),Yi)≤⌈(m+1)​α⌉−1}.\hat{\lambda}\_{2}=inf\{\lambda\_{2}\in[0,1]:\sum\_{(X\_{i},Y\_{i})\in Z\_{\bar{\lambda}\_{1}}}l(\mathcal{C}\_{\lambda\_{2}}(X\_{i}),Y\_{i})\leq\lceil(m+1)\alpha\rceil-1\}. | (15) |

This construction guarantees that

|  |  |
| --- | --- |
| 𝔼​[l​(Cλ^2​(X),Y)∣g​(X)≥1−λ¯1]≤α.\mathbb{E}[l(C\_{\hat{\lambda}\_{2}}(X),Y)\mid g(X)\geq 1-\bar{\lambda}\_{1}]\leq\alpha. | (16) |

###### Theorem 2 (Selective CRC Guarantee).

Assume (Xi,Yi)i=1n+1(X\_{i},Y\_{i})\_{i=1}^{n+1} are exchangeable. Let λ^1\hat{\lambda}\_{1} be obtained by Equation ([11](#S4.E11 "In 4.2 First Stage Control ‣ 4 Method ‣ Selective Conformal Risk Control")), let λ¯1\bar{\lambda}\_{1} be a *symmetric* function of the n+1n{+}1 points such that λ¯1≥λ^1\bar{\lambda}\_{1}\geq\hat{\lambda}\_{1} almost surely, and let λ^2\hat{\lambda}\_{2} be obtained by Equation ([15](#S4.E15 "In 4.3 Second Stage Control ‣ 4 Method ‣ Selective Conformal Risk Control")). Then the resulting selective classifier satisfies

|  |
| --- |
| 𝔼​[l​(Cλ^2​(Xn+1),Yn+1)∣g​(Xn+1)≥1−λ¯1]≤α,{\mathbb{E}[l(C\_{\hat{\lambda}\_{2}}(X\_{n+1}),Y\_{n+1})\mid g(X\_{n+1})\geq 1-\bar{\lambda}\_{1}]\leq\alpha,} |

and the selection coverage satisfies

|  |
| --- |
| ℙ​(g​(Xn+1)≥1−λ¯1)≥ξ.{\mathbb{P}\!\left(g(X\_{n+1})\geq 1-\bar{\lambda}\_{1}\right)\ \geq\ \xi.} |

###### Proof.

(Coverage) Because λ^1\hat{\lambda}\_{1} is a symmetric functional of (X1,…,Xn+1)(X\_{1},\dots,X\_{n+1}), hence by exchangeability

|  |
| --- |
| 𝔼​[𝟏​{g​(Xn+1)<1−λ^1}]=𝔼​[R^n+1(1)​(λ^1)]≤1−ξ.{\mathbb{E}[\mathbf{1}\{g(X\_{n+1})<1-\hat{\lambda}\_{1}\}]=\mathbb{E}[\hat{R}^{(1)}\_{n+1}(\hat{\lambda}\_{1})]\leq 1-\xi.} |

Since λ¯1≥λ^1\bar{\lambda}\_{1}\geq\hat{\lambda}\_{1} almost surely, monotonicity in λ1\lambda\_{1} yields

|  |
| --- |
| ℙ​(g​(Xn+1)≥1−λ¯1)≥ℙ​(g​(Xn+1)≥1−λ^1)≥ξ.{\mathbb{P}(g(X\_{n+1})\geq 1-\bar{\lambda}\_{1})\geq\mathbb{P}(g(X\_{n+1})\geq 1-\hat{\lambda}\_{1})\geq\xi.} |

(Risk) Let I={i:g​(Xi)≥1−λ¯1}I=\{i:g(X\_{i})\geq 1-\bar{\lambda}\_{1}\} and m=|I∩[n]|m=|I\cap[n]|. Since λ¯1\bar{\lambda}\_{1} is symmetric, conditioning on EI={I​(Dn+1)=I,n+1∈I}E\_{I}=\{I(D\_{n+1})=I,\ n{+}1\in I\}, Lemma [1](#Thmtheorem1 "Lemma 1. ‣ 4.1 Conditional Exchangeability ‣ 4 Method ‣ Selective Conformal Risk Control") ensures that {(Xi,Yi)}i∈I\{(X\_{i},Y\_{i})\}\_{i\in I} are exchangeable. Applying the CRC counting rule to the bounded, non-increasing loss l​(Cλ2,⋅)l(C\_{\lambda\_{2}},\cdot) and Equation ([15](#S4.E15 "In 4.3 Second Stage Control ‣ 4 Method ‣ Selective Conformal Risk Control")) yields

|  |
| --- |
| 𝔼​[l​(Cλ^2​(Xn+1),Yn+1)∣g​(Xn+1)≥1−λ¯1]≤α.{\mathbb{E}[l(C\_{\hat{\lambda}\_{2}}(X\_{n+1}),Y\_{n+1})\mid g(X\_{n+1})\geq 1-\bar{\lambda}\_{1}]\leq\alpha.} |

∎

###### Remark (Feasibility check).

To ensure a valid solution of Equation ([15](#S4.E15 "In 4.3 Second Stage Control ‣ 4 Method ‣ Selective Conformal Risk Control")), we requier ⌈(m+1)​α⌉−1>0\lceil(m+1)\alpha\rceil-1>0, which holds whenever m≥mm​i​n=⌈1/α⌉−1m\geq m\_{min}=\lceil 1/\alpha\rceil-1. In practice, candidates with m<mm​i​nm are skipped, or λ¯1\bar{\lambda}\_{1} is increased, to ensure feasible risk control at level α\alpha in the second stage.

### 4.4 Set-Size Refinement

Theorem [2](#Thmtheorem2 "Theorem 2 (Selective CRC Guarantee). ‣ 4.3 Second Stage Control ‣ 4 Method ‣ Selective Conformal Risk Control") establishes the selective validity of the base construction for a fixed admissible first-stage threshold. In practice, one may further reduce the prediction set size by searching over candidate values of λ1\lambda\_{1} whenever a family of feasible candidates are available.

For a fixed λ1∈[λ^1,1]\lambda\_{1}\in[\hat{\lambda}\_{1},1], let λ2​(λ1)\lambda\_{2}(\lambda\_{1}) be the maximal value of λ2\lambda\_{2} that satisfies Equation [15](#S4.E15 "In 4.3 Second Stage Control ‣ 4 Method ‣ Selective Conformal Risk Control"). By the monotonicity of the loss L(2)​(X,Y;λ2)L^{(2)}(X,Y;\lambda\_{2}) in λ2\lambda\_{2}, the corresponding prediction set size |Cλ2​(λ1)​(X)||C\_{\lambda\_{2}(\lambda\_{1})}(X)| is the smallest among all feasible λ2∈[λ2​(λ1),1]\lambda\_{2}\in[\lambda\_{2}(\lambda\_{1}),1].

The first-stage threshold λ^1\hat{\lambda}\_{1} is the minimal threshold that guarantees the target selection coverage, but it need not minimize the conditional prediction set size. Moreover, the second-stage risk need not be monotone in λ1\lambda\_{1} for fixed λ2\lambda\_{2}, so restricting attention to λ^1\hat{\lambda}\_{1} alone may be suboptimal from an efficiency standpoint. This motivates a practical search over a finite grid of candidate first-stage thresholds.

Accordingly, we consider the following heuristic: for each candidate λ1\lambda\_{1} in a user-specified grid, construct the corresponding selected calibration subset, compute the feasible second-stage threshold, and then choose the candidate that yields the smallest empirical prediction set size. The resulting procedure is summarized in Algorithm [1](#alg1 "Algorithm 1 ‣ 4.4 Set-Size Refinement ‣ 4 Method ‣ Selective Conformal Risk Control"), and its *efficiency* aspect is formalized in Theorem [3](#Thmtheorem3 "Theorem 3 (Finite-Grid Selection Efficiency). ‣ 4.4 Set-Size Refinement ‣ 4 Method ‣ Selective Conformal Risk Control"). We emphasize that this procedure is intended as a practical refinement to improve set size; moreover, its output is not covered by Theorem [2](#Thmtheorem2 "Theorem 2 (Selective CRC Guarantee). ‣ 4.3 Second Stage Control ‣ 4 Method ‣ Selective Conformal Risk Control").



Algorithm 1  Heuristic Search for Efficient SCRC Thresholds

Input: Calibration data {(Xi,Yi)}i=1n\{(X\_{i},Y\_{i})\}\_{i=1}^{n}, test feature Xn+1X\_{n+1}, coverage level ξ\xi, classification risk level α\alpha, candidate grid Λ⊆[0,1]\Lambda\subseteq[0,1]
Output: A practically chosen pair (λ¯1,λ¯2)(\bar{\lambda}\_{1},\bar{\lambda}\_{2})



1:Compute the theorem-backed threshold λ^1\hat{\lambda}\_{1} using Equation [11](#S4.E11 "In 4.2 First Stage Control ‣ 4 Method ‣ Selective Conformal Risk Control").

2:Initialize (λ¯1,λ¯2)←(λ^1,+∞)(\bar{\lambda}\_{1},\bar{\lambda}\_{2})\leftarrow(\hat{\lambda}\_{1},+\infty).

3:for each λ1∈Λ\lambda\_{1}\in\Lambda such that λ1≥λ^1\lambda\_{1}\geq\hat{\lambda}\_{1} do

4:  Construct the selected calibration subset Zλ1Z\_{\lambda\_{1}} using Equation [13](#S4.E13 "In 4.3 Second Stage Control ‣ 4 Method ‣ Selective Conformal Risk Control").

5:  m←|Zλ1|m\leftarrow|Z\_{\lambda\_{1}}|.

6:  if m>mminm>m\_{\min} then

7:   Compute the feasible second-stage threshold λ^2​(λ1)\hat{\lambda}\_{2}(\lambda\_{1}) using Equation [15](#S4.E15 "In 4.3 Second Stage Control ‣ 4 Method ‣ Selective Conformal Risk Control").

8:   Evaluate the empirical conditional prediction set size S^​(λ1)\widehat{S}(\lambda\_{1}).

9:   if S^​(λ1)<S^​(λ¯1)\widehat{S}(\lambda\_{1})<\widehat{S}(\bar{\lambda}\_{1}) then

10:     (λ¯1,λ¯2)←(λ1,λ^2​(λ1))(\bar{\lambda}\_{1},\bar{\lambda}\_{2})\leftarrow(\lambda\_{1},\hat{\lambda}\_{2}(\lambda\_{1})).

11:   end if

12:  end if

13:end for

14:return (λ¯1,λ¯2)(\bar{\lambda}\_{1},\bar{\lambda}\_{2})

###### Theorem 3 (Finite-Grid Selection Efficiency).

Assume the calibration sample (Xi,Yi)i=1n(X\_{i},Y\_{i})\_{i=1}^{n} is i.i.d. Let Λ⊂[0,1]\Lambda\subset[0,1] be a finite, data-independent grid and define λ^1ERM∈arg⁡minλ1∈Λ,λ1≥λ^1⁡S^​(λ1)\hat{\lambda}\_{1}^{\mathrm{ERM}}\in{\arg\min}\_{\lambda\_{1}\in\Lambda,\lambda\_{1}\geq\hat{\lambda}\_{1}}\widehat{S}(\lambda\_{1}), where S^​(λ1)\widehat{S}(\lambda\_{1}) denotes the empirical mean prediction set size for parameter λ1\lambda\_{1}. If the prediction set sizes are bounded by BB and mmin=minλ1∈Λ,λ1≥λ^1⁡m​(λ1)m\_{\min}=\min\_{\lambda\_{1}\in\Lambda,\lambda\_{1}\geq\hat{\lambda}\_{1}}m(\lambda\_{1}), then for any δ∈(0,1)\delta\in(0,1), with probability at least 1−δ1-\delta,

|  |
| --- |
| S​(λ^1ERM)≤minλ1∈Λ,λ1≥λ^1⁡S​(λ1)+ 2​B​log⁡(2​|Λ|/δ)2​mmin.S(\hat{\lambda}\_{1}^{\mathrm{ERM}})\;\leq\;\min\_{\lambda\_{1}\in\Lambda,\,\lambda\_{1}\geq\hat{\lambda}\_{1}}S(\lambda\_{1})\;+\;2B\sqrt{\tfrac{\log(2|\Lambda|/\delta)}{2\,m\_{\min}}}. |

###### Proof.

For a fixed λ1∈Λ\lambda\_{1}\in\Lambda, under the i.i.d. assumption, the selected calibration subset Zλ1Z\_{\lambda\_{1}} consists of m​(λ1)m(\lambda\_{1}) i.i.d. samples drawn from the conditional distribution (X,Y)∣g​(X)≥1−λ1(X,Y)\mid g(X)\geq 1-\lambda\_{1}. Hence S^​(λ1)\widehat{S}(\lambda\_{1}) is the empirical mean of m​(λ1)m(\lambda\_{1}) independent bounded random variables with expectation S​(λ1)S(\lambda\_{1}).

By Hoeffding’s inequality,

|  |
| --- |
| Pr⁡(|S^​(λ1)−S​(λ1)|>ε)≤2​exp⁡(−2​m​(λ1)​ε2B2).\Pr\!\left(\big|\widehat{S}(\lambda\_{1})-S(\lambda\_{1})\big|>\varepsilon\right)\leq 2\exp\!\Big(-\tfrac{2m(\lambda\_{1})\varepsilon^{2}}{B^{2}}\Big). |

Because the grid Λ\Lambda is deterministic, applying a union bound over Λ\Lambda and using m​(λ1)≥mminm(\lambda\_{1})\geq m\_{\min} yields

|  |
| --- |
| supλ1∈Λ|S^​(λ1)−S​(λ1)|≤B​log⁡(2​|Λ|/δ)2​mmin\sup\_{\lambda\_{1}\in\Lambda}\big|\widehat{S}(\lambda\_{1})-S(\lambda\_{1})\big|\leq B\sqrt{\tfrac{\log(2|\Lambda|/\delta)}{2m\_{\min}}} |

with probability at least 1−δ1-\delta. On this event, the empirical minimizer satisfies

|  |
| --- |
| S​(λ^1ERM)≤S^​(λ^1ERM)+ε≤S^​(λ1⋆)+ε≤S​(λ1⋆)+2​ε,S(\hat{\lambda}\_{1}^{\mathrm{ERM}})\leq\widehat{S}(\hat{\lambda}\_{1}^{\mathrm{ERM}})+\varepsilon\leq\widehat{S}(\lambda\_{1}^{\star})+\varepsilon\leq S(\lambda\_{1}^{\star})+2\varepsilon, |

where

|  |
| --- |
| λ1⋆=arg⁡minλ1∈Λ,λ1≥λ^1⁡S​(λ1).\lambda\_{1}^{\star}=\arg\min\_{\lambda\_{1}\in\Lambda,\ \lambda\_{1}\geq\hat{\lambda}\_{1}}S(\lambda\_{1}). |

Substituting ε\varepsilon gives the claim. ∎

###### Remark.

In practice, when the selection score g​(x)g(x) and the prediction score f​(x)f(x) are derived from the same underlying logits (as is common in deep classifiers), the two stages are strongly coupled: smaller g​(x)g(x) values also tend to have lower classification confidence under f​(x)f(x). Consequently, as λ1\lambda\_{1} increases, the selected subset gradually includes more low-confidence and hence more difficult instances, often resulting in a monotone increase of the mean prediction set size.

However, this monotonic relationship is not guaranteed in general. When g​(x)g(x) and f​(x)f(x) are decoupled—for instance, if g​(x)g(x) measures some auxiliary notion of “informativeness” unrelated to the posterior confidence used in f​(x)f(x)—the subsets selected by different λ1\lambda\_{1} values may not correspond to strictly increasing difficulty levels. In such cases, the mapping between λ1\lambda\_{1} and the mean set size can become non-monotone, justifying the need to perform a grid search over λ1\lambda\_{1} rather than assuming monotonicity.

### 4.5 Calibration-only Variant

In the transductive construction, the first-stage threshold depends symmetrically on both the calibration data and the test feature. This preserves exchangeability but requires recomputing the threshold for each new test point. For deployment, it is desirable to determine the first-stage threshold once from calibration data and reuse it for all future test points. We therefore introduce an inductive variant, SCRC-I, with a high-probability PAC-style guarantee.

Specifically, for any candidate first-stage threshold λ1\lambda\_{1}, define the selection indicator

|  |
| --- |
| Sλ1​(x)=𝟏​{g​(x)≥1−λ1}.S\_{\lambda\_{1}}(x)=\mathbf{1}\{g(x)\geq 1-\lambda\_{1}\}. |

Its population selection probability is

|  |
| --- |
| q​(λ1)=ℙ​(Sλ1​(X)=1),q(\lambda\_{1})=\mathbb{P}\big(S\_{\lambda\_{1}}(X)=1\big), |

and its empirical counterpart on the calibration sample is

|  |
| --- |
| q^n​(λ1)=1n​∑i=1nSλ1​(Xi).\widehat{q}\_{n}(\lambda\_{1})=\frac{1}{n}\sum\_{i=1}^{n}S\_{\lambda\_{1}}(X\_{i}). |

We choose the calibration-only first-stage threshold by

|  |  |
| --- | --- |
| λ^1′=inf{λ1∈Λ1:q^n​(λ1)≥ξ}.\hat{\lambda}\_{1}^{\prime}=\inf\left\{\lambda\_{1}\in\Lambda\_{1}:\widehat{q}\_{n}(\lambda\_{1})\geq\xi\right\}. | (17) |

To lower-bound the true selection probability induced by the data-dependent threshold λ^1′\hat{\lambda}\_{1}^{\prime}, we apply the Dvoretzky–Kiefer–Wolfowitz inequality with confidence level δ/2\delta/2. Define

|  |  |
| --- | --- |
| εn(q)=12​n​log⁡4δ,ξLCB=max⁡{q^n​(λ^1′)−εn(q), 0}.\varepsilon\_{n}^{(q)}=\sqrt{\frac{1}{2n}\log\frac{4}{\delta}},\qquad\xi\_{\mathrm{LCB}}=\max\big\{\widehat{q}\_{n}(\hat{\lambda}\_{1}^{\prime})-\varepsilon\_{n}^{(q)},\,0\big\}. | (18) |

Next, for any candidate pair (λ1,λ2)(\lambda\_{1},\lambda\_{2}), define the augmented population quantity

|  |  |
| --- | --- |
| N​(λ1,λ2)=𝔼​[Sλ1​(X)​ℓ​(Cλ2​(X),Y)],N(\lambda\_{1},\lambda\_{2})=\mathbb{E}\!\left[S\_{\lambda\_{1}}(X)\,\ell(C\_{\lambda\_{2}}(X),Y)\right], | (19) |

and its empirical version

|  |  |
| --- | --- |
| N^n​(λ1,λ2)=1n​∑i=1nSλ1​(Xi)​ℓ​(Cλ2​(Xi),Yi).\widehat{N}\_{n}(\lambda\_{1},\lambda\_{2})=\frac{1}{n}\sum\_{i=1}^{n}S\_{\lambda\_{1}}(X\_{i})\,\ell(C\_{\lambda\_{2}}(X\_{i}),Y\_{i}). | (20) |

Since the loss is bounded in [0,1][0,1], each summand in ([20](#S4.E20 "In 4.5 Calibration-only Variant ‣ 4 Method ‣ Selective Conformal Risk Control")) is also bounded in [0,1][0,1]. Over a finite candidate grid Λ1×Λ2\Lambda\_{1}\times\Lambda\_{2}, a uniform Hoeffding inequality with confidence level δ/2\delta/2 yields

|  |  |
| --- | --- |
| εn(N)=12​n​log⁡4​|Λ1|​|Λ2|δ.\varepsilon\_{n}^{(N)}=\sqrt{\frac{1}{2n}\log\frac{4|\Lambda\_{1}||\Lambda\_{2}|}{\delta}}. | (21) |

We then choose the second-stage threshold by the PAC-feasibility rule

|  |  |
| --- | --- |
| λ^2=inf{λ2∈Λ2:N^n​(λ^1′,λ2)+εn(N)≤α​ξLCB}.\hat{\lambda}\_{2}=\inf\left\{\lambda\_{2}\in\Lambda\_{2}:\widehat{N}\_{n}(\hat{\lambda}\_{1}^{\prime},\lambda\_{2})+\varepsilon\_{n}^{(N)}\leq\alpha\,\xi\_{\mathrm{LCB}}\right\}. | (22) |

The selective conditional risk admits the decomposition

|  |  |
| --- | --- |
| R​(λ1,λ2)=𝔼​[ℓ​(Cλ2​(X),Y)∣g​(X)≥1−λ1]=N​(λ1,λ2)q​(λ1),R(\lambda\_{1},\lambda\_{2})=\mathbb{E}\!\left[\ell(C\_{\lambda\_{2}}(X),Y)\mid g(X)\geq 1-\lambda\_{1}\right]=\frac{N(\lambda\_{1},\lambda\_{2})}{q(\lambda\_{1})}, | (23) |

whenever q​(λ1)>0q(\lambda\_{1})>0. The following proposition shows that the above construction yields a valid inductive guarantee.

###### Proposition 4 (Calibration-only variant).

Assume (Xi,Yi)i=1n(X\_{i},Y\_{i})\_{i=1}^{n} are i.i.d., let Λ1,Λ2⊂[0,1]\Lambda\_{1},\Lambda\_{2}\subset[0,1] be finite grids, and construct λ^1′\hat{\lambda}\_{1}^{\prime} and λ^2\hat{\lambda}\_{2} according to ([17](#S4.E17 "In 4.5 Calibration-only Variant ‣ 4 Method ‣ Selective Conformal Risk Control")) and ([22](#S4.E22 "In 4.5 Calibration-only Variant ‣ 4 Method ‣ Selective Conformal Risk Control")). Then for any δ∈(0,1)\delta\in(0,1), with probability at least 1−δ1-\delta over the calibration sample,

|  |
| --- |
| 𝔼​[ℓ​(Cλ^2​(X),Y)∣g​(X)≥1−λ^1′]≤α,\mathbb{E}\!\left[\ell(C\_{\hat{\lambda}\_{2}}(X),Y)\mid g(X)\geq 1-\hat{\lambda}\_{1}^{\prime}\right]\leq\alpha, |

provided ξLCB>0\xi\_{\mathrm{LCB}}>0.

###### Proof.

Apply the DKW inequality with confidence level δ/2\delta/2. Then with probability at least 1−δ/21-\delta/2,

|  |
| --- |
| supλ1∈Λ1|q^n​(λ1)−q​(λ1)|≤εn(q).\sup\_{\lambda\_{1}\in\Lambda\_{1}}\big|\widehat{q}\_{n}(\lambda\_{1})-q(\lambda\_{1})\big|\leq\varepsilon\_{n}^{(q)}. |

In particular,

|  |
| --- |
| q​(λ^1′)≥q^n​(λ^1′)−εn(q)=ξLCB.q(\hat{\lambda}\_{1}^{\prime})\geq\widehat{q}\_{n}(\hat{\lambda}\_{1}^{\prime})-\varepsilon\_{n}^{(q)}=\xi\_{\mathrm{LCB}}. |

Next, for each fixed pair (λ1,λ2)∈Λ1×Λ2(\lambda\_{1},\lambda\_{2})\in\Lambda\_{1}\times\Lambda\_{2}, the variables Sλ1​(Xi)​ℓ​(Cλ2​(Xi),Yi)S\_{\lambda\_{1}}(X\_{i})\,\ell(C\_{\lambda\_{2}}(X\_{i}),Y\_{i}) are i.i.d. and bounded in [0,1][0,1]. Hence Hoeffding’s inequality and a union bound imply that, with probability at least 1−δ/21-\delta/2,

|  |
| --- |
| sup(λ1,λ2)∈Λ1×Λ2|N^n​(λ1,λ2)−N​(λ1,λ2)|≤εn(N).\sup\_{(\lambda\_{1},\lambda\_{2})\in\Lambda\_{1}\times\Lambda\_{2}}\left|\widehat{N}\_{n}(\lambda\_{1},\lambda\_{2})-N(\lambda\_{1},\lambda\_{2})\right|\leq\varepsilon\_{n}^{(N)}. |

On the intersection of these two events, the PAC-feasibility condition in ([22](#S4.E22 "In 4.5 Calibration-only Variant ‣ 4 Method ‣ Selective Conformal Risk Control")) gives

|  |
| --- |
| N​(λ^1′,λ^2)≤N^n​(λ^1′,λ^2)+εn(N)≤α​ξLCB≤α​q​(λ^1′).N(\hat{\lambda}\_{1}^{\prime},\hat{\lambda}\_{2})\leq\widehat{N}\_{n}(\hat{\lambda}\_{1}^{\prime},\hat{\lambda}\_{2})+\varepsilon\_{n}^{(N)}\leq\alpha\,\xi\_{\mathrm{LCB}}\leq\alpha\,q(\hat{\lambda}\_{1}^{\prime}). |

Dividing both sides by q​(λ^1′)q(\hat{\lambda}\_{1}^{\prime}) and using ([23](#S4.E23 "In 4.5 Calibration-only Variant ‣ 4 Method ‣ Selective Conformal Risk Control")) yields

|  |
| --- |
| 𝔼​[ℓ​(Cλ^2​(X),Y)∣g​(X)≥1−λ^1′]≤α.\mathbb{E}\!\left[\ell(C\_{\hat{\lambda}\_{2}}(X),Y)\mid g(X)\geq 1-\hat{\lambda}\_{1}^{\prime}\right]\leq\alpha. |

A final union bound shows that this holds with probability at least 1−δ1-\delta. ∎

###### Remark.

SCRC-I is an inductive variant with a reusable calibration rule: both λ^1′\hat{\lambda}\_{1}^{\prime} and λ^2\hat{\lambda}\_{2} are computed once from the calibration sample and then reused for future test points. Its analysis does not require exchangeability after selection; instead, it controls the selection probability and the selected numerator risk separately via uniform concentration arguments. Relative to the transductive SCRC-T procedure, SCRC-I trades some statistical efficiency (due to concentration slack) for computational efficiency, avoiding per-test recomputation and making it more practical for deployment.

## 5 Experiments

### 5.1 Experiment Setup

We adopt the following setup for all experiments presented in this section.

#### Model and score preparation.

Since model optimization is not the focus of this work, we use pretrained or standard models without additional hyperparameter tuning. The raw model logits are converted into calibrated class probabilities f​(x)f(x) via a temperature-scaled softmax transformation. For the selection function g​(x)g(x), we evaluate four commonly used confidence or uncertainty scores, all derived from the model logits:

* •

  Maximum Softmax Probability (MSP) [[18](#bib.bib10 "A baseline for detecting misclassified and out-of-distribution examples in neural networks")]: the highest predicted class probability, gMSP​(x)=maxk⁡p​(y=k∣x).g\_{\text{MSP}}(x)=\max\_{k}p(y=k\mid x).
* •

  Margin [[18](#bib.bib10 "A baseline for detecting misclassified and out-of-distribution examples in neural networks")]: the difference between the top two predicted probabilities, gmargin​(x)=p(1)−p(2).g\_{\text{margin}}(x)=p\_{(1)}-p\_{(2)}.
* •

  Entropy [[10](#bib.bib12 "Dropout as a bayesian approximation: representing model uncertainty in deep learning")]: the entropy of the predictive distribution, representing overall uncertainty, gentropy​(x)=−∑kp​(y=k|x)​log⁡p​(y=k|x)g\_{\text{entropy}}(x)=-\sum\_{k}{p(y=k|x)\log{p(y=k|x)}}.
* •

  Energy [[21](#bib.bib11 "Energy-based out-of-distribution detection")]: an energy-based confidence score derived directly from unnormalized logits, genergy​(x)=−T​log​∑kexp⁡logitk​(x)Tg\_{\text{energy}}(x)=-T\log\sum\_{k}{{\exp{\frac{\text{logit}\_{k}(x)}{T}}}}.

#### Compared Methods

We compare four approaches for risk control:

* •

  SCRC-T: the transductive variant of our proposed method, which preserves full exchangeability.
* •

  SCRC-I: the calibration-only (inductive) variant of our proposed method, which provides PAC-style probabilistic guarantees.
* •

  CRC-ALL: a two-stage baseline that applies traditional conformal risk control (CRC) after selecting all data in the first stage.
* •

  RAND: a random selection baseline that samples data at the target coverage rate before applying CRC in the second stage.

#### Evaluation protocol.

To assess the validity of risk and coverage control, we conduct two complementary analyses. First, we fix the target risk level α\alpha and vary the desired coverage ξ\xi to evaluate selective coverage control. Then, we fix ξ\xi and vary α\alpha to evaluate risk control performance. For each setting, we report both the achieved coverage and empirical risk, as well as the average prediction set size. We further compare results for the subset of accepted (selected) samples and the rejected (unselected) samples to characterize efficiency.

Each experiment is repeated 100 times with random sampling, and we report the averaged results across runs.

All codes, including for both data generation and risk control, are publicly available at https://github.com/git4review/conformal\_selective\_classification.

### 5.2 CIFAR-10 Dataset

The CIFAR-10 dataset111<https://www.cs.toronto.edu/~kriz/cifar.html> consists of 60,000 color images of size 32×3232\times 32, evenly distributed across 10 mutually exclusive object classes. Following standard practice, we use the 50,000 training images and 10,000 test images, with approximately 5,000 and 1,000 images per class, respectively. We further split the 50,000 training images into training, validation, and calibration sets using a 7:1:2 ratio. A ResNet-18 classifier [[15](#bib.bib13 "Deep residual learning for image recognition")] is trained to produce logits for all experiments.

#### Coverage control.

Figure [1](#S5.F1 "Figure 1 ‣ Coverage control. ‣ 5.2 CIFAR-10 Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control") shows empirical coverage and prediction set sizes as functions of the target coverage ξ\xi, with the risk level fixed at α=0.1\alpha=0.1 and using the margin score as the selection function. All methods except CRC\_ALL successfully control coverage at the desired level. As expected, CRC\_ALL produces a coverage of 1.01.0 regardless of ξ\xi, since the first-stage selection always accepts all samples.

For both SCRC-T and SCRC-I, prediction set sizes for the selected subset increase with ξ\xi, reflecting the strong coupling between the selection score g​(x)g(x) and the predictive scores f​(x)f(x). Moreover, selected samples by these two methods consistently exhibit substantially smaller prediction sets than unselected samples, confirming that the selection mechanism can effectively reject uncertain examples for classification. The RAND and CRC\_ALL baselines, on the other hand, show prediction set sizes that remain unchanged across different values of ξ\xi, due to their lack of the selection process.

![Refer to caption](2512.12844v2/figures/cifar10_coverage_vs_xi_alpha0.1_scoremargin.png)

![Refer to caption](2512.12844v2/figures/cifar10_setsize_vs_xi_alpha0.1_scoremargin.png)

Figure 1: CIFAR-10: Coverage control at different values of ξ\xi with α=0.1\alpha=0.1 (margin score).

#### Risk control.

Figure [2](#S5.F2 "Figure 2 ‣ Risk control. ‣ 5.2 CIFAR-10 Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control") reports the empirical risk and prediction set sizes as functions of α\alpha, with the target coverage fixed at ξ=0.7\xi=0.7. All methods achieve the desired selective risk control. Prediction set sizes decrease as α\alpha increases, consistent with the fact that looser risk constraints permit smaller prediction sets. As in the coverage experiments, selected samples exhibit much smaller prediction sets than rejected samples for both SCRC-T and SCRC-I,.

![Refer to caption](2512.12844v2/figures/cifar10_risk_vs_alpha_xi0.7_scoremargin.png)

![Refer to caption](2512.12844v2/figures/cifar10_setsize_vs_alpha_xi0.7_scoremargin.png)

Figure 2: CIFAR-10: Risk control at different values of α\alpha with ξ=0.7\xi=0.7 (margin score).

#### Comparison of SCRC-T and SCRC-I.

Across both sets of experiments, SCRC-T and SCRC-I deliver nearly identical empirical performance. However, SCRC-I is slightly more conservative in risk control, leading to marginally larger prediction sets. This behavior follows directly from its PAC-style correction using the lower confidence bound ξLCB\xi\_{\mathrm{LCB}}, which trades a small amount of efficiency for a reusable, inductive calibration procedure with high-probability guarantees. In practice, the difference between the two methods is minor and decreases as the calibration set grows. SCRC-T, on the other hand, yields a more efficient prediction sets when a per-test recomputation is feasible, though it incurs a much higher computational cost. This empirical comparison reflects their intended roles: SCRC-T serves as the exact exchangeability-preserving benchmark, while SCRC-I is the practically deployable variant.

#### Effect of score functions.

To study the impact of different selection functions, we repeat the experiments using MSP, margin, entropy, and energy scores. As shown in Figure [3](#S5.F3 "Figure 3 ‣ Effect of score functions. ‣ 5.2 CIFAR-10 Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control"), all four choices achieve comparable coverage and risk control, but produce different prediction set sizes. Entropy and energy yield the smallest prediction sets, while margin produces the largest. This highlights an important distinction: the choice of g​(x)g(x) primarily affects *efficiency*—how many examples are accepted and how small the resulting prediction sets are—rather than the validity of the selective guarantees themselves.

![Refer to caption](2512.12844v2/figures/cifar10_score_comparison_selected_xi0.7_alpha0.1.png)

Figure 3: CIFAR-10: Comparison of different selection score functions.

#### Effect of δ\delta for SCRC-I.

Finally, we examine the impact of the confidence parameter δ\delta on SCRC-I, which determines the DKW half-width ϵn,δ\epsilon\_{n,\delta}. Fixing ξ=0.7\xi=0.7 and α=0.1\alpha=0.1, we vary δ\delta and report empirical results in Table [2](#S5.T2 "Table 2 ‣ Effect of score functions and 𝛿. ‣ 5.3 Diabetic Retinopathy Detection Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control"). Tighter values of δ\delta (i.e., stronger confidence guarantees) lead to slightly more conservative risk control and marginally larger prediction sets, both of which are expected behaviors. Overall, the effect is small but consistent.



Table 1: CIFAR-10: Impact of different values of δ\delta for SCRC-I.

| Metric | δ=0.01\delta=0.01 | δ=0.05\delta=0.05 | δ=0.10\delta=0.10 |
| --- | --- | --- | --- |
| Empirical risk | 0.0954 | 0.0960 | 0.0964 |
| Prediction set size | 2.460 | 2.451 | 2.446 |

### 5.3 Diabetic Retinopathy Detection Dataset

The Diabetic Retinopathy Detection (DRD) dataset222<https://www.kaggle.com/competitions/diabetic-retinopathy-detection> contains over 35,000 retinal fundus images captured under varying imaging conditions. Each image is manually graded by clinicians into one of five ordinal severity levels (0 to 4 where 4 is the most severe level), making the task clinically meaningful and well suited for uncertainty-aware evaluation. Compared to CIFAR-10, this dataset presents two notable differences: (i) it comes from a medical imaging domain where reliable uncertainty quantification is particularly critical, and (ii) the labels are *ordinal*, requiring a different notion of prediction-set loss. We therefore adopt the weighted ordinal loss from [[30](#bib.bib30 "Conformal risk control for ordinal classification")] when constructing prediction sets.

Following the same protocol as in the CIFAR-10 experiments, we randomly split the images into training/validation, calibration, and test sets in a 4:1:1 ratio and train a ResNet-34 [[15](#bib.bib13 "Deep residual learning for image recognition")] to obtain logits for the five severity levels.

#### Coverage and risk control.

Figures [4](#S5.F4 "Figure 4 ‣ Coverage and risk control. ‣ 5.3 Diabetic Retinopathy Detection Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control") and [5](#S5.F5 "Figure 5 ‣ Coverage and risk control. ‣ 5.3 Diabetic Retinopathy Detection Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control") show the selective coverage and risk as functions of ξ\xi and α\alpha. The overall behavior closely mirrors that of CIFAR-10: both SCRC-T and SCRC-I achieve the desired selective coverage and risk across all settings, with their selected samples exhibiting substantially smaller prediction sets than rejected samples. CRC\_ALL again maintains a fixed coverage of 1.01.0, and RAND remains insensitive to ξ\xi due to its uninformed selection step.

![Refer to caption](2512.12844v2/figures/drd_coverage_vs_xi_alpha0.1_scoremargin.png)

![Refer to caption](2512.12844v2/figures/drd_setsize_vs_xi_alpha0.1_scoremargin.png)

Figure 4: DR Detection: Coverage control at different values of ξ\xi with α=0.1\alpha=0.1 (margin score).



![Refer to caption](2512.12844v2/figures/drd_risk_vs_alpha_xi0.7_scoremargin.png)

![Refer to caption](2512.12844v2/figures/drd_setsize_vs_alpha_xi0.7_scoremargin.png)

Figure 5: DR Detection: Risk control at different values of α\alpha with ξ=0.7\xi=0.7 (margin score).

#### Comparison of methods.

As in the CIFAR-10 results, SCRC-T and SCRC-I perform almost identically, with SCRC-I being slightly more conservative due to its PAC-style correction. This conservativeness is more noticeable on smaller calibration sets, which are common in medical datasets, but the effect remains small in practice. Importantly, both methods maintain valid uncertainty control despite the ordinal structure of the labels. In this setting, abstention is especially useful because difficult cases can be deferred, while accepted cases still receive informative calibrated set-valued predictions.

#### Effect of score functions and δ\delta.

Figure [6](#S5.F6 "Figure 6 ‣ Effect of score functions and 𝛿. ‣ 5.3 Diabetic Retinopathy Detection Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control") shows prediction set sizes for various score functions; the relative ranking is consistent with CIFAR-10: entropy and energy yield the smallest sets, and margin is more conservative. Table [2](#S5.T2 "Table 2 ‣ Effect of score functions and 𝛿. ‣ 5.3 Diabetic Retinopathy Detection Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control") summarizes the effect of δ\delta in SCRC-I. Smaller δ\delta values (tighter confidence levels) lead to slightly larger prediction sets and marginal increases in conservativeness, as expected from the tighter DKW constraint.

![Refer to caption](2512.12844v2/figures/drd_score_comparison_selected_xi0.7_alpha0.1.png)

Figure 6: DR Detection: Comparison of different selection score functions.



Table 2: DR Detection: Impact of different values of δ\delta for SCRC-I.

| Metric | δ=0.01\delta=0.01 | δ=0.05\delta=0.05 | δ=0.10\delta=0.10 |
| --- | --- | --- | --- |
| Empirical risk | 0.0931 | 0.0935 | 0.0937 |
| Prediction set size | 2.569 | 2.567 | 2.566 |

## 6 Conclusions

In this paper, we introduced Selective Conformal Risk Control, a unified framework that integrates conformal prediction with selective classification to provide reliable, distribution-free uncertainty quantification while improving efficiency through selective abstention. The framework targets the selective setting: it produces calibrated prediction sets on accepted inputs and explicitly abstains on rejected ones, rather than attempting to force informative prediction sets on every sample. Our design enables simultaneous guarantees on selective coverage and conditional risk, and addresses the practical limitation of standard conformal methods that often yield excessively large prediction sets.

We developed two algorithmic variants within this framework: SCRC-T and SCRC-I. Empirical results demonstrate that both methods successfully achieve the target coverage and risk levels. Their performance is nearly identical across all tested configurations, with the SCRC-I variant exhibiting slightly more conservative risk control, an expected consequence of its PAC correction. Nevertheless, SCRC-I is more practical for real world deployment, as it avoids parameter recomputation while maintaining reliable uncertainty calibration. In contrast, SCRC-T serves as the exact exchangeability-preserving construction and provides a useful benchmark when per-test recomputation is acceptable.

A limitation of the current framework is that it does not provide a second-stage prediction-set guarantee for rejected samples; these cases are intentionally deferred and should be handled by a downstream fallback mechanism such as human review or a more specialized model. Future work may explore integrating such fallback mechanisms into a unified framework, as well as developing adaptive or learned selection functions. Additional directions include extending the approach to regression and ranking settings, and applying it to large-scale, high-stakes domains where both reliable uncertainty control and computational efficiency are critical.

## References

* [1] A. N. Angelopoulos, S. Bates, A. Fisch, L. Lei, and T. Schuster (2024)  Conformal risk control.  ICLR.  Cited by: [§1](#S1.p3.1 "1 Introduction ‣ Selective Conformal Risk Control"), [§3](#S3.SS0.SSS0.Px1.p2.1 "Conformal Prediction. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [2] A. N. Angelopoulos and S. Bates (”2021”)  A gentle introduction to conformal prediction and distribution-free uncertainty quantification.  ”arXiv:2107.07511”.  Cited by: [§1](#S1.p3.1 "1 Introduction ‣ Selective Conformal Risk Control"), [§3](#S3.SS0.SSS0.Px1.p1.1 "Conformal Prediction. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [3] Y. Bao, Y. Huo, H. Ren, and C. Zou (2024)  Selective conformal inference with false coverage-statement rate control.  Biometrika.  Cited by: [§3](#S3.SS0.SSS0.Px3.p1.1 "Conformal Prediction and Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [4] P. L. Bartlett and M. H. Wegkamp (2008)  Classification with a reject option using a hinge loss.  Journal of Machine Learning Research 9 (59),  pp. 1823–1840.  Cited by: [§3](#S3.SS0.SSS0.Px2.p1.1 "Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [5] C. Blundell, J. Cornebise, K. Kavukcuoglu, and D. Wierstra (2015)  Weight uncertainty in neural networks.  In Proceedings of the 32nd International Conference on Machine Learning,  Cited by: [§1](#S1.p2.1 "1 Introduction ‣ Selective Conformal Risk Control").
* [6] C. K. Chow (1957)  An optimum character recognition system using decision functions.  IRE Transactions on Electronic Computers.  Cited by: [§1](#S1.p5.1 "1 Introduction ‣ Selective Conformal Risk Control"), [§3](#S3.SS0.SSS0.Px2.p1.1 "Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [7] A. Fisch, T. Jaakkola, and R. Barzilay (2022)  Calibrated selective classification.  https://arxiv.org/abs/2208.12084.  Cited by: [§3](#S3.SS0.SSS0.Px3.p1.1 "Conformal Prediction and Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [8] A. Fisch, T. Jaakkola, and R. Barzilay (2022)  Conformal prediction sets with limited false positives.  In Proceedings of the 39 th International Conference on Machine Learning,  Cited by: [§1](#S1.p3.1 "1 Introduction ‣ Selective Conformal Risk Control"), [§3](#S3.SS0.SSS0.Px1.p1.1 "Conformal Prediction. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [9] V. Franc, D. Prusa, and V. Voracek (2023)  Optimal strategies for reject option classifiers.  Journal of Machine Learning Research 24,  pp. 1–49.  Cited by: [§3](#S3.SS0.SSS0.Px2.p1.1 "Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [10] Y. Gal and Z. Ghahramani (2016)  Dropout as a bayesian approximation: representing model uncertainty in deep learning.  In Proceedings of the 33rd International Conference on Machine Learning,  Cited by: [§1](#S1.p2.1 "1 Introduction ‣ Selective Conformal Risk Control"), [3rd item](#S5.I1.i3.p1.1 "In Model and score preparation. ‣ 5.1 Experiment Setup ‣ 5 Experiments ‣ Selective Conformal Risk Control").
* [11] U. Gazin, R. Heller, A. Marandon, and E. Roquain (2024)  Selecting informative conformal prediction sets with false coverage rate control.  arXiv preprint arXiv:2403.12295.  Cited by: [§3](#S3.SS0.SSS0.Px3.p1.1 "Conformal Prediction and Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [12] Y. Geifman and R. El-Yaniv (2017)  Selective classification for deep neural networks.  Proceedings of the 31st International Conference on Neural Information Processing Systems.  Cited by: [§1](#S1.p5.1 "1 Introduction ‣ Selective Conformal Risk Control"), [§3](#S3.SS0.SSS0.Px2.p1.1 "Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [13] Y. Geifman and R. El-Yaniv (2019)  SelectiveNet: a deep neural network with an integrated reject option.  Proceedings of the 36 th International Conference on Machine Learning.  Cited by: [§1](#S1.p5.1 "1 Introduction ‣ Selective Conformal Risk Control"), [§3](#S3.SS0.SSS0.Px2.p1.1 "Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [14] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger (2017)  On calibration of modern neural networks.  In Proceedings of the 34th International Conference on Machine Learning,  Cited by: [§1](#S1.p2.1 "1 Introduction ‣ Selective Conformal Risk Control").
* [15] K. He, X. Zhang, S. Ren, and J. Sun (2016)  Deep residual learning for image recognition.  In 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR),  Cited by: [§5.2](#S5.SS2.p1.1 "5.2 CIFAR-10 Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control"), [§5.3](#S5.SS3.p2.1 "5.3 Diabetic Retinopathy Detection Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control").
* [16] M. E. Hellman (1970)  The nearest neighbor classification rule with a reject option.  IEEE Transactions on Systems Science and Cybernetics.  Cited by: [§1](#S1.p5.1 "1 Introduction ‣ Selective Conformal Risk Control"), [§3](#S3.SS0.SSS0.Px2.p1.1 "Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [17] K. Hendrickx, L. Perini, D. Van der Plas, W. Meert, and J. Davis (2024)  Machine learning with a reject option: a survey.  Machine Learning 113,  pp. 3073 – 3110.  Cited by: [§3](#S3.SS0.SSS0.Px2.p1.1 "Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [18] D. Hendrycks and K. Gimpel (2017)  A baseline for detecting misclassified and out-of-distribution examples in neural networks.  Proceedings of International Conference on Learning Representations.  Cited by: [1st item](#S5.I1.i1.p1.1 "In Model and score preparation. ‣ 5.1 Experiment Setup ‣ 5 Experiments ‣ Selective Conformal Risk Control"), [2nd item](#S5.I1.i2.p1.1 "In Model and score preparation. ‣ 5.1 Experiment Setup ‣ 5 Experiments ‣ Selective Conformal Risk Control").
* [19] V. Kuleshov, N. Fenner, and S. Ermon (2018)  Accurate uncertainties for deep learning using calibrated regression.  In Proceedings of the 35th International Conference on Machine Learning,  Cited by: [§1](#S1.p2.1 "1 Introduction ‣ Selective Conformal Risk Control").
* [20] J. Lei, M. G’Sell, A. Rinaldo, R. J. Tibshirani, and L. Wasserman (2018)  Distribution-free predictive inference for regression.  Journal of the American Statistical Association.  Cited by: [§3](#S3.SS0.SSS0.Px1.p1.1 "Conformal Prediction. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [21] W. Liu, X. Wang, J. D. Owens, and Y. Li (2020)  Energy-based out-of-distribution detection.  34th Conference on Neural Information Processing Systems.  Cited by: [4th item](#S5.I1.i4.p1.1 "In Model and score preparation. ‣ 5.1 Experiment Setup ‣ 5 Experiments ‣ Selective Conformal Risk Control").
* [22] H. Papadopoulos, K. Proedrou, V. Vovk, and A. Gammerman (2002)  Inductive confidence machines for regression.  In ECML,  Cited by: [§3](#S3.SS0.SSS0.Px1.p1.1 "Conformal Prediction. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [23] A. Pugnana and S. Ruggieri (2023)  AUC-based selective classification.  Cited by: [§3](#S3.SS0.SSS0.Px2.p1.1 "Selective Classification. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [24] Y. Romano, E. Patterson, and E. J. Candès (2019)  Conformalized quantile regression.  In Advances in Neural Information Processing Systems,  Cited by: [§3](#S3.SS0.SSS0.Px1.p1.1 "Conformal Prediction. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [25] G. Shafer and V. Vovk (2008)  A tutorial on conformal prediction.  Journal of Machine Learning Research 9,  pp. 371–421.  Cited by: [§3](#S3.SS0.SSS0.Px1.p1.1 "Conformal Prediction. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [26] R. J. Tibshirani, R. Foygel Barber, E. J. Candès, and A. Ramdas (2019)  Conformal prediction under covariate shift.  In Advances in Neural Information Processing Systems (NeurIPS),  Cited by: [§3](#S3.SS0.SSS0.Px1.p1.1 "Conformal Prediction. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [27] J. Vaicenavicius, D. Widmann, C. Andersson, F. Lindsten, J. Roll, and T. B. Schon (2019)  Evaluating model calibration in classification.  In Proceedings of the 22nd International Conference on Artificial Intelligence and Statistics,  Cited by: [§1](#S1.p2.1 "1 Introduction ‣ Selective Conformal Risk Control").
* [28] V. Vovk, A. Gammerman, and C. Saunders (1999)  Machine-learning applications of algorithmic randomness.  Sixteenth International Conference on Machine Learning (ICML).  Cited by: [§3](#S3.SS0.SSS0.Px1.p1.1 "Conformal Prediction. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [29] V. Vovk, A. Gammerman, and G. Shafer (2005)  Algorithmic learning in a random world.  Vol. 29, Springer.  Cited by: [§3](#S3.SS0.SSS0.Px1.p1.1 "Conformal Prediction. ‣ 3 Related Work ‣ Selective Conformal Risk Control").
* [30] Y. Xu, W. Guo, and Z. Wei (2023)  Conformal risk control for ordinal classification.  Proceedings of the 39th Conference on Uncertainty in Artificial Intelligence (UAI).  Cited by: [§5.3](#S5.SS3.p1.1 "5.3 Diabetic Retinopathy Detection Dataset ‣ 5 Experiments ‣ Selective Conformal Risk Control").
* [31] Y. Xu, M. Ying, W. Guo, and Z. Wei (2025)  Two-stage risk control with application to ranked retrieval.  Proceedings of the Thirty-Fourth International Joint Conference on Artificial Intelligence (IJCAI).  Cited by: [§4](#S4.p1.1 "4 Method ‣ Selective Conformal Risk Control").

Experimental support, please [view the build logs](./2512.12844v2/__stdout.txt) for errors. Generated by  [L A T E  xml ![[LOGO]](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)](https://math.nist.gov/~BMiller/LaTeXML/) .

## Instructions for reporting errors

We are continuing to improve HTML versions of papers, and your feedback helps enhance accessibility and mobile support. To report errors in the HTML that will help us improve conversion and rendering, choose any of the methods listed below:

* Click the "Report Issue" ( ) button, located in the page header.

**Tip:** You can select the relevant text first, to include it in your report.

Our team has already identified [the following issues](https://github.com/arXiv/html_feedback/issues). We appreciate your time reviewing and reporting rendering errors we may not have found yet. Your efforts will help us improve the HTML versions for all readers, because disability should not be a barrier to accessing research. Thank you for your continued support in championing open access for all.

Have a free development cycle? Help support accessibility at arXiv! Our collaborators at LaTeXML maintain a [list of packages that need conversion](https://github.com/brucemiller/LaTeXML/wiki/Porting-LaTeX-packages-for-LaTeXML), and welcome [developer contributions](https://github.com/brucemiller/LaTeXML/issues).

BETA
