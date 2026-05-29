# Quantifying Uncertainty: All We Need is the Bootstrap?

###### Abstract

{A critical literature review and comprehensive simulation study is used to show that (a) non-parametric bootstrap is a viable alternative to commonly taught and used methods in basic estimation tasks (mean, variance, quartiles, correlation) and (b), contrary to recommendations in most related work, double bootstrap performs better than BCa.} Quantifying uncertainty through standard errors, confidence intervals, hypothesis tests, and related measures is a fundamental aspect of statistical practice. However, these techniques involve a variety of methods, mathematical formulas, and underlying concepts, which can be complex. Could the non-parametric bootstrap, known for its simplicity and general applicability, serve as a universal alternative? This paper addresses this question through a review of the existing literature and a simulation analysis of one- and two-sided confidence intervals across varying sample sizes, confidence levels, data-generating processes, and statistical functionals. Results show that the double bootstrap consistently performs best and is a promising alternative to traditional methods used for common statistical tasks. These results suggest that the bootstrap, particularly the double bootstrap, could simplify statistical education and practice without compromising effectiveness.

###### keywords:

## 1 Introduction

University curricula in fields such as the social sciences, medicine, and life sciences, which heavily rely on statistical methodology, typically include only one or two applied statistics courses. However, it is practitioners in these fields, rather than professional statisticians, who perform the majority of statistical analyses. The mismatch between the level of training provided and the practical demand for statistical analysis often results in an over-reliance on rote memorization and formulaic application of methods, contributing to challenges such as the replication crisis in science. This underscores the importance of exploring ways to simplify current statistical practices. Simplification could not only enhance comprehension and reduce errors but also create opportunities to incorporate other aspects of statistical methodology into curricula.

This paper focuses on the quantification of uncertainty. Standard errors, confidence intervals, and hypothesis tests are integral components of statistical practice, yet they typically involve advanced concepts—such as test statistics and sampling distributions—and encompass a wide array of methods. Among these, one method stands out: the bootstrap. The bootstrap offers several advantages over traditional techniques for quantifying uncertainty. It is conceptually straightforward, reinforces the fundamental role of sampling in statistics, allows direct interaction with estimates and their distributions, and can be applied to a wide range of practical tasks without requiring the mastery of new concepts or complex mathematical formulas. These characteristics give the bootstrap significant pedagogical value [[1](https://arxiv.org/html/2403.20182v3#bib.bib1)], positioning it as a strong candidate for a one-size-fits-all approach to quantifying uncertainty, particularly for practitioners with limited statistical training.

Historically, the use of the bootstrap was constrained by computational limitations. With advancements in computing power, this is no longer a concern, yet introductory applied statistics textbooks and courses rarely place the bootstrap at the forefront. This is largely due to the inertia of established practices, which are supported by more extensive instructional resources and software tools—resources that bootstrapping has historically lacked [[1](https://arxiv.org/html/2403.20182v3#bib.bib1)], and to some extent still does. Moreover, there is currently insufficient empirical evidence to convincingly establish the bootstrap as a comprehensive, one-size-fits-all solution for quantifying uncertainty.

### 1.1 Related work

Theoretical cases where bootstrap fails are pathological with limited implications for practice (see [[2](https://arxiv.org/html/2403.20182v3#bib.bib2)] and [[3](https://arxiv.org/html/2403.20182v3#bib.bib3), Ch.2.6]). Large sample properties of common bootstrap approaches have also been established (see [[2](https://arxiv.org/html/2403.20182v3#bib.bib2)] for a summary). Unfortunately, large sample theory is not always a reliable predictor of finite sample performance, so empirical work is required.

Tables [1.1](https://arxiv.org/html/2403.20182v3#S1.SS1 "1.1 Related work ‣ 1 Introduction ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") and [1.1](https://arxiv.org/html/2403.20182v3#S1.SS1 "1.1 Related work ‣ 1 Introduction ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") summarize empirical studies on bootstrap methods. Early research primarily focused on the Pearson correlation and the sample mean, with subsequent work extending to other functionals, particularly quantiles and regression parameters. In this review, the focus is on non-parametric bootstrap techniques and methods that are widely taught and applied in practice, referred to hereafter as baseline methods. These include, for example, Fisher confidence intervals (CIs) for the Pearson correlation and t-intervals for the sample mean.

While most, though not all, related studies include a baseline comparison, there are only three instances—aside from an early study where the 1st-order accurate percentile bootstrap (PB) was the best-performing method [[4](https://arxiv.org/html/2403.20182v3#bib.bib4)]—in which the baseline outperforms the top-performing bootstrap approach. For example, [[5](https://arxiv.org/html/2403.20182v3#bib.bib5)] demonstrated that Fieller and Taylor series-based confidence intervals for elasticities and flexibilities marginally outperformed the bias-corrected and accelerated (BCa), bias-corrected (BC), and PB methods, though this result was observed with relatively small sample sizes (n=13,15n=13,15). Similarly, [[6](https://arxiv.org/html/2403.20182v3#bib.bib6)] showed that for Pearson correlation under a bivariate normal distribution with varying correlation coefficients, Fisher intervals achieved coverage close to the nominal 95%, while BCa intervals yielded coverage rates around 93% and 94% for sample sizes of 20 and 10, respectively. Furthermore, [[7](https://arxiv.org/html/2403.20182v3#bib.bib7)] found that for the log-normal distribution, baseline methods attained nominal coverage with smaller sample sizes than BCa, though this was contingent on assuming log-normality.

The most common recommendation propagated through literature is to use BCa, based mostly on theoretical results. Empirical results also often recommend BCa, with the exception of the mean, where studentized bootstrap (also bootstrap-t, B-t) is better. However, some studies suggest that BCa does not perform well with small sample sizes [[2](https://arxiv.org/html/2403.20182v3#bib.bib2), [8](https://arxiv.org/html/2403.20182v3#bib.bib8), [9](https://arxiv.org/html/2403.20182v3#bib.bib9)]. Double or iterated (also calibrated) bootstrap (DB) appears in only 7 studies. When it does, it performs as well as or better than other methods.

In summary, much of the related research is confined to a single functional, a single data-generating process (DGP), and/or a single confidence level. Additionally, the most commonly used methods are not always included as baselines for comparison. DB also warrants greater attention. While the findings are promising, it remains challenging to fully assess the practical implications of relying exclusively on bootstrap methods.

A summary of simulation studies in related work (1981-1999). Ordered by year of publication.

Ref.


DGP


n


nrep{}\_{\text{rep}}


Functional


Evaluating


Methods


Summary of results




[[10](https://arxiv.org/html/2403.20182v3#bib.bib10)]


normal


14


200


mean


SE


PB, SB (B = 128, 512)


SB better than PB



[[11](https://arxiv.org/html/2403.20182v3#bib.bib11)]


normal


20-100


1600


variance


90% CI


BC, PB (B = 1000)


bootstrap coverage below nominal



[[12](https://arxiv.org/html/2403.20182v3#bib.bib12)]


normal, exponential


15


200


trimmed mean


SE


PB (B = 200)


PB better than jackknife



[[4](https://arxiv.org/html/2403.20182v3#bib.bib4)]


normal, non-normal


5-60


1000


mean


95%, 99% CI


baseline; PB (B = 500)


baseline better than PB



[[13](https://arxiv.org/html/2403.20182v3#bib.bib13)]


normal


14-100


200


mean


SE


PB, SB (B = 200)


SB better than PB



[[14](https://arxiv.org/html/2403.20182v3#bib.bib14)]


exponential


5


1


corr


95% CI


BC, BCa, PB (B = ?)


BCa good; PB and BC poor




bivariate non-normal


5


1


ratio


95% CI


BC, BCa, PB (B = ?)


BCa good; PB and BC poor




normal


8


1


mean


95% CI


B-t, BC, PB (B = ?)


BC and PB perform similarly, B-t is worse



[[15](https://arxiv.org/html/2403.20182v3#bib.bib15)]


normal


100


100


mean


several CI


baseline; PB, SB (B = 2000)


PB similar to baseline; SB better than PB



[[9](https://arxiv.org/html/2403.20182v3#bib.bib9)]


chi-squared


20


1000


corr


90% CI


baseline; hybrid, B-t, BC, BCa, PB (B = 1000)


hybrid, B-t, and PB perform similarly; BC and BCa have lower than nominal coverage



[[5](https://arxiv.org/html/2403.20182v3#bib.bib5)]


(see paper)


13, 15


500


regression


90% CI


baseline; BC, BCa, PB (B = 500)


baseline better than bootstrap; bootstrap methods similar to each other



[[16](https://arxiv.org/html/2403.20182v3#bib.bib16)]


normal, exponential


10, 20


1000


corr


several CI


PB (B = 50000)


PB is biased



[[17](https://arxiv.org/html/2403.20182v3#bib.bib17)]


7 distributions (see paper)


3-20


1000


corr


95% CI


baseline; B-t, BCa, PB (B = 1000)


B-t performs well



[[18](https://arxiv.org/html/2403.20182v3#bib.bib18)]


chi-squared, mixture of normal


20


10000


corr


several CI


baseline; B-t, PB (B = 1000)


bootstrap similar to baseline; B-t is best



[[19](https://arxiv.org/html/2403.20182v3#bib.bib19)]


normal, Poisson, t, Weibull


20


500


corr


90% CI


baseline; B-t, BCa, DB, PB (B = 500)


DB and B-t perform best



[[20](https://arxiv.org/html/2403.20182v3#bib.bib20)]


normal, exponential


5-25


1000


corr


95% CI


baseline; DB, PB (B = 1000)


DB as good or better than baseline, except for n=5n=5; PB is worst



[[21](https://arxiv.org/html/2403.20182v3#bib.bib21)]


normal, exponential, beta, gamma, t


10, 100


500


median


SE


PB, SB (B = 200)


smoothing improves performance



[[22](https://arxiv.org/html/2403.20182v3#bib.bib22)]


normal


20


1


mean


90% CI


baseline; ABC, BCa, B-t (B = 2000)


bootstrap better than baseline



[[23](https://arxiv.org/html/2403.20182v3#bib.bib23)]


normal, folded normal, exponential, log-normal


15, 30


1600


corr


90% CI


ABC, DB, DB-ABC, PB (B = 1000)


DB better than ABC and calibrated ABC



[[24](https://arxiv.org/html/2403.20182v3#bib.bib24)]


(see paper)


13, 15


500


regression


90% CI


DB, PB (B = 1999)


DB better than PB
\tabnoten = sample size or range, if more than two;  nrep{}\_{\text{rep}} = number of Monte Carlo replications; B = number of bootstrap replications; ? indicates information that could not be discerned from the paper

A summary of simulation studies in related work (2000-2023). Ordered by year of publication.

Ref.


DGP


n


nrep{}\_{\text{rep}}


Functional


Evaluating


Methods


Summary of results




[[2](https://arxiv.org/html/2403.20182v3#bib.bib2)]


inverse exponential


20


10000


corr


99% CI


baseline; B-t, BC, BCa, PB (B = 4999)


baseline, B-t, and BCa perform similarly; BCa poor for small n



[[25](https://arxiv.org/html/2403.20182v3#bib.bib25)]


normal


15


1


mean


90% CI


baseline; ABC


bootstrap better than baseline



[[26](https://arxiv.org/html/2403.20182v3#bib.bib26)]


log-normal, gamma


10-50


10000


diff. in means


95% CI


baseline; B-t, BCa (B = 1000)


B-t performs well and better than BCa



[[27](https://arxiv.org/html/2403.20182v3#bib.bib27)]


bivariate normal (censored)


25-400


2000


(see paper)


90%, 95% CI


B-t, BCa, PB (B = 520)


jackknife performs best; PB performs worst



[[8](https://arxiv.org/html/2403.20182v3#bib.bib8)]


normal, log-normal, gamma, t, uniform


10-3600


1000-64000


variance


several CI


baseline; ABC, BC, BCa, PB (B = 1000, 16000)


2nd order accurate methods can converge slowly and perform worse than PB



[[28](https://arxiv.org/html/2403.20182v3#bib.bib28)]


(see paper)


50-500


5000


regression


95% CI


baseline; BC, PB (B = 2000)


BC and PB perform well



[[29](https://arxiv.org/html/2403.20182v3#bib.bib29)]


exponential, Pareto


10-25


2000


extrema


80%, 90% CI


baseline; PB, DB (B = 699)


DB is best



[[30](https://arxiv.org/html/2403.20182v3#bib.bib30)]


(see paper)


50-500


5000


regression


95% CI


baseline; BCa, PB (B = 10000)


BCa and PB perform well



[[31](https://arxiv.org/html/2403.20182v3#bib.bib31)]


(see paper)


10-50


1000


capture-recapture


95% CI


baseline; B-t, PB (B = 100, 250)


B-t performs best



[[32](https://arxiv.org/html/2403.20182v3#bib.bib32)]


log-logistic with censored data


25-50


1000


(see paper)


90%, 95% CI


baseline; B-t, DB, DB-t, PB (B = ?)


PB poor; other bootstrap methods good and similar to each other



[[33](https://arxiv.org/html/2403.20182v3#bib.bib33)]


normal, uniform, triangular, beta, Laplace, Pareto


50?-300?


1000


mean


95% CI


BCa, PB (B = 2000)


BCa slightly better than PB; good coverage except on Pareto



[[1](https://arxiv.org/html/2403.20182v3#bib.bib1)]


normal, exponential


5-4000


10000


corr


95% CI


baseline; B-t, PB, reverse PB (B = 10000)


bootstrapped CI narrow, especially for small n; PB worse than baseline for small n; reverse PB poor; B-t best



[[34](https://arxiv.org/html/2403.20182v3#bib.bib34)]


log-logistic with censored data


25-60


1000


(see paper)


90%, 95% CI


baseline, JK; DB, PB (B = 1000)


DB best; PB poor



[[6](https://arxiv.org/html/2403.20182v3#bib.bib6)]


normal


10-100


10000


mean


95% CI


baseline; B-n, B-t, BC, BCa, PB (B = 10000)


baseline better than bootstrap on small n; BCa performs well



[[35](https://arxiv.org/html/2403.20182v3#bib.bib35)]


(see paper)


?


1000


quantiles


95% CI


modified B-n, BC, BCa, PB (B = 1999)


bootstrap methods perform similarly



[[36](https://arxiv.org/html/2403.20182v3#bib.bib36)]


log-normal


20-120


100


quantiles


95% CI


baseline; BCa, PB (B = 10000)


baseline better than bootstrap for small n



[[37](https://arxiv.org/html/2403.20182v3#bib.bib37)]


26 pairs


20-600


1000


corr


95% CI


baseline; BCa, PB (B = 2000)


BCa better than PB on small n; PB better than BCa for large n; poor coverage for uniform-chi-squared
\tabnoten = sample size or range, if more than two;  nrep{}\_{\text{rep}} = number of Monte Carlo replications; B = number of bootstrap replications; ? indicates information that could not be discerned from the paper

## 2 Simulation Study

The experiment runs across each possible combination of sample size nn from {4, 8, 16, 32, 64, 128, 256}, intervals (−∞,α)(-\infty,\alpha) with endpoints α\alpha from {0.025, 0.05, 0.25, 0.75, 0.95, 0.975}, statistical functional from {mean, median, standard deviation, 5t​h5^{th} and 95t​h95^{th} percentile, and Pearson correlation}, and data generating process from

normal with μ=0\mu=0 and σ=1\sigma=1,

exponential with λ=1\lambda=1,

uniform from 0 to 1,

beta with α=10\alpha=10 and β=2\beta=2,

log-normal with μ=0\mu=0 and σ=1\sigma=1,

Laplace with μ=0\mu=0 and b=1b=1,

Bernoulli with p=0.5p=0.5,

Bernoulli with p=0.9p=0.9, and

bivariate normal with μ=[11]\mu=\begin{bmatrix}1\\
1\end{bmatrix}
and Σ=[20.50.51]\Sigma=\begin{bmatrix}2&0.5\\
0.5&1\end{bmatrix}.

Note that the bivariate normal and Pearson correlation appear only in combination with each other and the two Bernoulli distributions appear only in combination with the mean.

The experimental design was informed by a combination of related simulation studies, theoretical considerations, and computational constraints. The selected range of sample sizes is consistent with those commonly used in similar studies. However, sample sizes of 4 and 8, which are rarely examined, are included. Although such small samples are uncommon in most statistical practice, they may hold practical relevance in fields where data is limited (for example, gene expression studies). For sample sizes of 256 and above, all methods should perform well from a practical standpoint, though these larger sample sizes can also become computationally prohibitive.

The selected range of endpoints includes the 5% and 95% confidence levels and enables the construction of symmetric two-sided confidence intervals at 95% and 90% levels by combining the 0.025 and 0.975, or 0.05 and 0.95 endpoints. These levels are the most commonly used in practice and almost all simulation studies. However, this choice of endpoints also permits the exploration of other confidence levels. It is important to note, from an evaluation standpoint, that considering one-sided coverage is crucial, as relying solely on two-sided coverage can be misleading (see Section [2.2](https://arxiv.org/html/2403.20182v3#S2.SS2 "2.2 Measuring the quality of confidence intervals ‣ 2 Simulation Study ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") for details).

The selected statistical functionals include the most commonly used functionals (mean, median, standard deviation, and correlation) and two extreme percentiles, which are less widely used in practice but are known to pose challenges in quantifying uncertainty. A notable omission is the inclusion of model coefficients, such as those from the family of generalized linear mixed-effects models. However, for many of these models, and most more complex models, the bootstrap is not only a viable alternative but the only option for quantifying uncertainty.

Every experiment is replicated nrep=10000n\_{\text{rep}}=10000 times, to limit coverage standard error to 0.0050.005 in the worst case, and B={10,100,1000}B=\{10,100,1000\} bootstrap replications. More bootstrap replications is better, so BB is not considered as a dimension of the experiment. Results are only reported for B=1000B=1000, but B=100B=100 would result in the same main conclusions. For B=10B=10 the performance of bootstrap methods is noticeably worse. Recommendations [[3](https://arxiv.org/html/2403.20182v3#bib.bib3), [8](https://arxiv.org/html/2403.20182v3#bib.bib8), [38](https://arxiv.org/html/2403.20182v3#bib.bib38)] and choices of BB in simulation studies also suggest that B=1000B=1000 is sufficient.

### 2.1 Methods

CIs produced by the methods that are most commonly used in practice for that statistical functional are included as a baseline for comparison. For the mean, the t-based CIs from the commonly used t-test (t-test). For the mean of the two Bernoulli distributions, the Clopper-Pearson (c-p) [[39](https://arxiv.org/html/2403.20182v3#bib.bib39)] and Agresti-Coull (a-c) [[40](https://arxiv.org/html/2403.20182v3#bib.bib40)] intervals. For the median, CIs from the Wilcoxon signed rank test (wilcoxon) [[41](https://arxiv.org/html/2403.20182v3#bib.bib41)]. For standard deviation, chi-squared CIs (chi-sq) [[42](https://arxiv.org/html/2403.20182v3#bib.bib42)]. For Pearson correlation Fisher CIs (fisher) [[43](https://arxiv.org/html/2403.20182v3#bib.bib43)]. For quantiles, parametric CIs based on normal assumption (q-par), non-parametric CI (q-nonpar) (see [[7](https://arxiv.org/html/2403.20182v3#bib.bib7)] for both), and the Maritz-Jarrett method (m-j) [[44](https://arxiv.org/html/2403.20182v3#bib.bib44)].

The bootstrap procedure can be divided into two primary steps. First, *bootstrap sampling* to generate the bootstrap distribution, which serves as an approximation of the sampling distribution of the functional of interest. And second, applying a *bootstrap method* to construct a confidence interval.

Bootstrap sampling can be further categorized into parametric and non-parametric approaches. The parametric bootstrap assumes a specific distribution for the underlying population, FF, and estimates the associated parameters from the observed data, X=(x1,x2,…,xn)X=(x\_{1},x\_{2},\dots,x\_{n}). In contrast, the non-parametric bootstrap infers properties of FF by resampling directly from XX without imposing distributional assumptions. Given that there are nnn^{n} possible samples from resampling, the process is typically restricted to BB independent bootstrap samples to maintain computational feasibility. This yields BB bootstrap samples X1∗,X2∗,…,XB∗X^{\*}\_{1},X^{\*}\_{2},\dots,X^{\*}\_{B} and the bootstrap distribution of the parameter θ^∗=(θ^1∗,θ^2∗,…,θ^B∗)\hat{\theta}^{\*}=(\hat{\theta}^{\*}\_{1},\hat{\theta}^{\*}\_{2},\dots,\hat{\theta}^{\*}\_{B}).

The assumptions underlying parametric bootstrap methods restrict their applicability or require additional user input, making them less suitable as a universal approach. Therefore, the experiments focus exclusively on non-parametric bootstrap methods. Below is a brief overview of the bootstrap methods used for CI construction, along with references for further details. The source code is also available (see Section [3](https://arxiv.org/html/2403.20182v3#S3 "3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?")).

#### 2.1.1 Percentile Bootstrap (PB)

The percentile method is the original method proposed by Efron in [[45](https://arxiv.org/html/2403.20182v3#bib.bib45)] (for details, also see [[38](https://arxiv.org/html/2403.20182v3#bib.bib38), chap. 13]). Multiple improvements have been made since, but percentile remains one of the most popular bootstrap methods. The percentile CI for confidence level α\alpha is obtained by taking the α\alpha-quantile of the bootstrap distribution:

|  |  |  |
| --- | --- | --- |
|  | θ^PB​[α]=θ^α∗.\hat{\theta}\_{\text{PB}}[\alpha]=\hat{\theta}^{\*}\_{\alpha}. |  |

All implementations of methods that use quantiles, use the median-unbiased version of quantile calculation, recommended in [[46](https://arxiv.org/html/2403.20182v3#bib.bib46)].

#### 2.1.2 Standard Bootstrap (B-n)

The standard method (sometimes the normal method), assumes that the bootstrap distribution is normal [[38](https://arxiv.org/html/2403.20182v3#bib.bib38), chap. 13]:

|  |  |  |
| --- | --- | --- |
|  | θ^B-n​[α]=θ^+σ^​zα,\hat{\theta}\_{\text{B-n}}[\alpha]=\hat{\theta}+\hat{\sigma}z\_{\alpha}, |  |

where θ^\hat{\theta} is the plug-in estimator of the functional, σ^\hat{\sigma} is the standard deviation estimate from the bootstrap distribution and zαz\_{\alpha} is the z-score.

#### 2.1.3 Basic Bootstrap (BB)

In the basic bootstrap [[38](https://arxiv.org/html/2403.20182v3#bib.bib38), chap. 13.4], sometimes called the reverse percentile method, the observed bootstrap distribution θ∗\theta^{\*} is replaced with W∗=θ∗−θ^W^{\*}=\theta^{\*}-\hat{\theta}. This results in

|  |  |  |
| --- | --- | --- |
|  | θ^BB​[α]=2​θ^−θ^1−α∗.\hat{\theta}\_{\text{BB}}[\alpha]=2\hat{\theta}-\hat{\theta}^{\*}\_{1-\alpha}. |  |

Davison and Hinkley [[3](https://arxiv.org/html/2403.20182v3#bib.bib3)] show that it provides an accurate confidence interval for the sample median, but it can have a substantial coverage error because of errors in quantile calculation of W∗W^{\*}. It can also give us invalid parameter values, when there are constraints on θ\theta.

#### 2.1.4 Smoothed Bootstrap (SB)

The smoothed bootstrap [[3](https://arxiv.org/html/2403.20182v3#bib.bib3)] gets its name from smoothing the bootstrap distribution. Smoothing is implemented with a normal kernel centered on 0 and kernel size is determined with

|  |  |  |
| --- | --- | --- |
|  | h=0.9​min⁡(σ^,IQR1.34),h=0.9\min\big(\hat{\sigma},\frac{\text{IQR}}{1.34}\big), |  |

where IQR is the inter-quartile range of the bootstrap distribution, respectively. The CI estimate is then obtained by taking the α\alpha quantile of the smoothed bootstrap distribution θ~∗\tilde{\theta}^{\*}:

|  |  |  |
| --- | --- | --- |
|  | θ^SB​[α]=θ~α∗.\hat{\theta}\_{\text{SB}}[\alpha]=\tilde{\theta}^{\*}\_{\alpha}. |  |

#### 2.1.5 Bias Corrected Bootstrap (BC)

The bias corrected bootstrap corrects the bias of the percentile CI [[38](https://arxiv.org/html/2403.20182v3#bib.bib38), chap. 14]. The CI estimate is:

|  |  |  |  |
| --- | --- | --- | --- |
|  | θ^BC​[α]\displaystyle\hat{\theta}\_{\text{BC}}[\alpha] | =θ^αB​C∗,\displaystyle=\hat{\theta}^{\*}\_{\alpha\_{BC}}, |  |
|  |  |  |  |
| --- | --- | --- | --- |
|  | αBC\displaystyle\alpha\_{\text{BC}} | =Φ​(2​Φ−1​(b^)+zα),\displaystyle=\Phi\big(2\Phi^{-1}(\hat{b})+z\_{\alpha}\big), |  |

where Φ\Phi is the standard normal CDF b^\hat{b} is the bias, calculated as the percentage of values from the bootstrap distribution that are lower than the value of the functional on the data.

#### 2.1.6 Bias Corrected and Accelerated Bootstrap (BCa)

The bias corrected and accelerated bootstrap [[38](https://arxiv.org/html/2403.20182v3#bib.bib38), chap. 14] further corrects the B​CBC interval by computing acceleration aa, which accounts for the skewness of the bootstrap distribution:

|  |  |  |  |
| --- | --- | --- | --- |
|  | θ^B​C​a​[α]\displaystyle\hat{\theta}\_{BCa}[\alpha] | =θ^αBCa∗,\displaystyle=\hat{\theta}^{\*}\_{\alpha\_{\text{BCa}}}, |  |
|  |  |  |  |
| --- | --- | --- | --- |
|  | αBCa\displaystyle\alpha\_{\text{BCa}} | =Φ​(Φ−1​(b)+Φ−1​(b^)+zα1+a^​(Φ−1​(b^)+zα)),\displaystyle=\Phi\Big(\Phi^{-1}(b)+\frac{\Phi^{-1}(\hat{b})+z\_{\alpha}}{1+\hat{a}(\Phi^{-1}(\hat{b})+z\_{\alpha})}\Big), |  |

where a^\hat{a} is the leave-one-out jackknife approximation of the acceleration constant.

#### 2.1.7 Studentized Bootstrap (B-t)

The studentized bootstrap [[38](https://arxiv.org/html/2403.20182v3#bib.bib38), chap. 14], also known as bootstrap-t, generalizes the Student’s t method, using the distribution of T=(θ^−θ)/σ^T=(\hat{\theta}-\theta)/\hat{\sigma} to estimate the CI:

|  |  |  |
| --- | --- | --- |
|  | θ^B-t​[α]=θ^−σ^​T1−α.\hat{\theta}\_{\text{B-t}}[\alpha]=\hat{\theta}-\hat{\sigma}T\_{1-\alpha}. |  |

But since the distribution of TT is not known, its percentiles have to be approximated from the bootstrap distribution. That is done by defining T∗=(θ^∗−θ^)/σ^∗T^{\*}=(\hat{\theta}^{\*}-\hat{\theta})/\hat{\sigma}^{\*}, where σ^∗\hat{\sigma}^{\*} is obtained by doing another inner bootstrap sampling on each of the outer samples.

#### 2.1.8 Double Bootstrap (DB)

The double bootstrap [[47](https://arxiv.org/html/2403.20182v3#bib.bib47), chap. 3.11] corrects bias with another level of inner of bootstraps. The bootstrap procedure is repeated on each of the bootstrap samples to calculate the the percentage of times that the inner bootstrap functional is smaller than on the original sample. A limit is required such that P​{θ^∈(−∞,θ^d​o​u​b​l​e​[α])}=αP\{\hat{\theta}\in(-\infty,\hat{\theta}\_{double}[\alpha])\}=\alpha, which is why the α\alpha-th quantile of biases b^∗\hat{b}^{\*} is selected for the adjusted level αDB\alpha\_{\text{DB}}. This leads to

|  |  |  |  |
| --- | --- | --- | --- |
|  | θ^DB​[α]\displaystyle\hat{\theta}\_{\text{DB}}[\alpha] | =θ^αd​o​u​b​l​e∗,\displaystyle=\hat{\theta}^{\*}\_{\alpha\_{double}}, |  |
|  |  |  |  |
| --- | --- | --- | --- |
|  | αDB\displaystyle\alpha\_{\text{DB}} | =b^α∗.\displaystyle=\hat{b}^{\*}\_{\alpha}. |  |

Note that percentile bootstrap is used on the inner and outer bootstrap, but the double (iterated) bootstrap allows for any bootstrap method.

### 2.2 Measuring the quality of confidence intervals

Most related work measures only coverage, with only a few studies measuring interval length [[2](https://arxiv.org/html/2403.20182v3#bib.bib2), [37](https://arxiv.org/html/2403.20182v3#bib.bib37), [25](https://arxiv.org/html/2403.20182v3#bib.bib25), [35](https://arxiv.org/html/2403.20182v3#bib.bib35), [36](https://arxiv.org/html/2403.20182v3#bib.bib36), [17](https://arxiv.org/html/2403.20182v3#bib.bib17), [6](https://arxiv.org/html/2403.20182v3#bib.bib6)] or comparing CIs with exact intervals [[22](https://arxiv.org/html/2403.20182v3#bib.bib22), [14](https://arxiv.org/html/2403.20182v3#bib.bib14), [25](https://arxiv.org/html/2403.20182v3#bib.bib25)].

This study also focuses on coverage, but also measures and reports results for interval length for two-sided CIs and the absolute distance from exact intervals for one-sided intervals. The exact interval for endpoint α\alpha and parameter θ\theta is defined as θ^e​x​a​c​t​[α]=θ^−σ^​K−1​(1−α)\hat{\theta}\_{exact}[\alpha]=\hat{\theta}-\hat{\sigma}K^{-1}(1-\alpha), where KK is the cumulative distribution function of θ\theta [[48](https://arxiv.org/html/2403.20182v3#bib.bib48)]. Note that σ^​K−1​(1−α)\hat{\sigma}K^{-1}(1-\alpha) is approximated with 100000 samples.

Note that two-sided coverage can be misleading regarding a method’s coverage because good two-sided coverage can be, and in practice often is, a result of substantial, but opposite errors in the two one-sided intervals (see [[48](https://arxiv.org/html/2403.20182v3#bib.bib48)] for an example). That is, while two-sided error can be studied from one-sided CIs, the converse is not true.

The practical meaning of coverage error depends on nominal coverage and is not symmetric. For example, 51% coverage at 50% nominal coverage is not the same as 96% coverage at 95% nominal coverage. And 85% coverage is not the same as 95% coverage at 90% nominal coverage. To aggregate results and for a threshold-based criterion that can be applied to all confidence levels, a novel criterion is proposed, based on the Kullback-Leibler divergence. That is, it is based on measuring information loss if nominal coverage π\pi is assumed when actual coverage is pp:

|  |  |  |
| --- | --- | --- |
|  | KL​(p,π)=p​log2⁡(pπ)+(1−p)​log2⁡(1−p1−π).\text{KL}(p,\pi)=p\log\_{2}(\frac{p}{\pi})+(1-p)\log\_{2}(\frac{1-p}{1-\pi}). |  |

For a threshold-based criterion of what is considered *good enough* Bradley’s criterion |p−π|<min⁡(π,1−π)k|p-\pi|<\frac{\min(\pi,1-\pi)}{k} is modified, where π\pi is the nominal coverage [[49](https://arxiv.org/html/2403.20182v3#bib.bib49)]. Common choices for kk are 10 (stringent), 4 (intermediate), 2 (liberal), and 0.75 (very liberal). Note that the intermediate and very liberal were introduced by [[50](https://arxiv.org/html/2403.20182v3#bib.bib50)]. In related work on the bootstrap, only [[37](https://arxiv.org/html/2403.20182v3#bib.bib37)] uses a *good enough* criterion - that actual coverage should lie between 92.5% and 97.5% when nominal coverage is 95% (this is based on the work of [[49](https://arxiv.org/html/2403.20182v3#bib.bib49)]).

At 95%95\% nominal coverage, the KL divergences for the Bradley lower bounds 94.5%94.5\% (k=10k=10), 93.8%93.8\% (k=4k=4), 92.5%92.5\% (k=2k=2), and 88.3%88.3\% (k=0.75k=0.75) are approximately 0.00040.0004, 0.00200.0020, 0.00830.0083, and 0.05030.0503. The value KL​(0.945,0.95)\text{KL}(0.945,0.95) is adopted as the stringent criterion and a factor of 5 as an *order of magnitude* worse/better performance. For nominal coverage 95% this leads to criteria very similar to Bradley’s: (93.8,96.2)(93.8,96.2) vs (93.9,96.1)(93.9,96.1) (intermediate), (92.5,97.5)(92.5,97.5) vs (92.4,97.3)(92.4,97.3) (liberal), and (88.3,101.7)(88.3,101.7) vs (88.6,99.4)(88.6,99.4) (very liberal). However, for nominal coverage further away from 95%, the proposed approach gives produces sensible criteria and does not produce endpoints outside of the unit interval.

## 3 Results

The simulation study consists of 1386 combinations of sample size, endpoint, and functional, and it is infeasible to list all of the results. The results first focus on identifying if a bootstrap method is a viable one-size-fits-all approach. Inevitably, some details that are relevant to the reader might be left out. A visualization tool is available to browse all of the results of the experiments zrimseku.github.io/bootstrap-simulation/ (see Figure [2](https://arxiv.org/html/2403.20182v3#S3.F2 "Figure 2 ‣ 3.4 Absolute distance from exact CIs ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?")).

The raw results (aggregated over 10000 replications) and the source code for the tool, simulation framework, pre-processing, and analysis can be found here: github.com/zrimseku/bootstrap-simulation. The source code can be used to generate the full non-aggregated results. The library with all the methods can be found here: github.com/zrimseku/bootstrap-ci.

### 3.1 When methods fail to produce a CI

There are only a few cases where a method fails to produce a CI. All bootstrap methods fail to produce a CI for Pearson correlation for n=4n=4, due to division by zero variance. It can also happen for n=8n=8, but rarely. BC and BCa do not produce a CI for the 5t​h5^{th} percentile for n≤8n\leq 8. For the 95t​h95^{th} percentile, B-t does not produce an interval in most cases when n=4n=4 for the Laplace distribution. m-j is unable to produce CIs for small sample sizes and extreme percentiles (5t​h5^{th} percentile for n≤16n\leq 16 and the 95t​h95^{th} percentile for n≤8n\leq 8). Method q-nonpar fails to produce the 95t​h95^{th} percentile for n=4n=4 and α≤0.75\alpha\leq 0.75, for n∈{8,16}n\in\{8,16\} and α≤0.25\alpha\leq 0.25, for n=32n=32 and α≤0.05\alpha\leq 0.05 and for n=64n=64 and a​l​p​h​a=0.025alpha=0.025. When predicting CIs for the median, it fails at n=4n=4 and α≤0.05\alpha\leq 0.05. And, although wilcoxon returns CIs for asymmetric distributions, they are not useful CIs for location. Also note that all cases for Bernoulli, where all nn had the same value, are removed, because most methods fail if there is no variability in the data.

### 3.2 Coverage of bootstrap methods

Table [3.2](https://arxiv.org/html/2403.20182v3#S3.SS2 "3.2 Coverage of bootstrap methods ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") shows a comparison of bootstrap methods in mean KL. As expected, coverage improves with sample size and the two extreme percentiles and standard deviation are the most difficult functionals. For Pearson correlation, mean, and median, DB is best. For the percentiles, B-n is best. And for standard deviation, B-t is best. B-n and B-t perform the best overall. Because coverage gets wors with smaller sample size, the overall results are biased towards methods that perform well on small nn. DB and BCa, which are expected to perform best, perform relatively poorly for small nn, but are best and second best for sample sizes n≥64n\geq 64.

Mean KL coverage performance of bootstrap methods for one-sided CIs. The all column is across all combinations, while the remaining results are grouped by sample size or statistical functional. The best performing method for each column is underlined.

all
4
8
16
32
64
128
256
corr
mean
Q0.5
Q0.05
Q0.95
std


B-n
0.078¯\underline{0.078}
0.3170.317
0.174¯\underline{0.174}
0.087¯\underline{0.087}
0.037¯\underline{0.037}
0.0210.021
0.0140.014
0.0090.009
0.0060.006
0.0260.026
0.0040.004
0.024¯\underline{0.024}
0.145¯\underline{0.145}
0.2080.208

B-t
0.0840.084
0.196¯\underline{0.196}
0.2690.269
0.1070.107
0.0490.049
0.0230.023
0.0190.019
0.0140.014
0.0080.008
0.013¯\underline{0.013}
0.0120.012
0.0780.078
0.2640.264
0.084¯\underline{0.084}

BB
0.1120.112
0.2490.249
0.1890.189
0.2180.218
0.1010.101
0.0460.046
0.0330.033
0.0220.022
0.0170.017
0.0310.031
0.0450.045
0.1590.159
0.2340.234
0.1450.145

SB
0.1180.118
0.4520.452
0.2670.267
0.1520.152
0.0600.060
0.0270.027
0.0170.017
0.0110.011
0.0020.002
0.0220.022
0.0030.003
0.0640.064
0.2300.230
0.3080.308

DB
0.1340.134
0.5360.536
0.3400.340
0.1930.193
0.0570.057
0.008¯\underline{0.008}
0.005¯\underline{0.005}
0.003¯\underline{0.003}
0.000¯\underline{0.000}
0.013¯\underline{0.013}
0.002¯\underline{0.002}
0.1250.125
0.4010.401
0.1880.188

PB
0.1570.157
0.6100.610
0.3640.364
0.2190.219
0.0730.073
0.0280.028
0.0180.018
0.0110.011
0.0020.002
0.0250.025
0.0030.003
0.1090.109
0.3770.377
0.3300.330

BC
0.1610.161
0.6280.628
0.3590.359
0.2280.228
0.0920.092
0.0220.022
0.0130.013
0.0080.008
0.0010.001
0.0490.049
0.0170.017
0.1690.169
0.3870.387
0.2460.246

BCa
0.1610.161
0.6320.632
0.3590.359
0.2360.236
0.0920.092
0.0180.018
0.0100.010
0.0050.005
0.0010.001
0.0580.058
0.0170.017
0.2010.201
0.3790.379
0.2180.218

Threshold-based coverage performance of bootstrapping on one-sided CIs. The table shows the percentage of experiments where a method does not meet the liberal criterion 25×KL​(0.945,0.95)25\times\text{KL}(0.945,0.95). The all column is across all experiments, while the remaining results are grouped by sample size or statistical functional. The best performing method for each column is underlined.

all
4
8
16
32
64
128
256
corr
mean
Q0.5
Q0.05
Q0.95
std


DB
0.30¯\underline{0.30}
0.670.67
0.49¯\underline{0.49}
0.46¯\underline{0.46}
0.440.44
0.12¯\underline{0.12}
0.07¯\underline{0.07}
0.03¯\underline{0.03}
0.00¯\underline{0.00}
0.18¯\underline{0.18}
0.05¯\underline{0.05}
0.460.46
0.500.50
0.42¯\underline{0.42}

B-n
0.400.40
0.780.78
0.650.65
0.560.56
0.36¯\underline{0.36}
0.280.28
0.200.20
0.130.13
0.200.20
0.340.34
0.110.11
0.28¯\underline{0.28}
0.460.46
0.800.80

BCa
0.410.41
0.890.89
0.700.70
0.620.62
0.410.41
0.230.23
0.210.21
0.060.06
0.00¯\underline{0.00}
0.320.32
0.330.33
0.680.68
0.41¯\underline{0.41}
0.470.47

SB
0.450.45
0.830.83
0.630.63
0.570.57
0.490.49
0.400.40
0.280.28
0.140.14
0.070.07
0.280.28
0.120.12
0.490.49
0.570.57
0.940.94

BC
0.460.46
0.890.89
0.720.72
0.680.68
0.500.50
0.340.34
0.240.24
0.110.11
0.00¯\underline{0.00}
0.310.31
0.330.33
0.570.57
0.730.73
0.540.54

PB
0.470.47
0.820.82
0.660.66
0.630.63
0.510.51
0.390.39
0.280.28
0.160.16
0.070.07
0.320.32
0.100.10
0.490.49
0.590.59
0.940.94

B-t
0.470.47
0.54¯\underline{0.54}
0.620.62
0.550.55
0.510.51
0.430.43
0.410.41
0.320.32
0.230.23
0.300.30
0.350.35
0.590.59
0.670.67
0.570.57

BB
0.570.57
0.800.80
0.750.75
0.640.64
0.600.60
0.500.50
0.460.46
0.410.41
0.270.27
0.370.37
0.590.59
0.760.76
0.810.81
0.500.50

Threshold-based coverage performance of bootstrapping on two-sided CIs. The table shows the percentage of experiments where a method does not meet the liberal criterion 25×KL​(0.945,0.95)25\times\text{KL}(0.945,0.95). The all column is across all experiments, while the remaining results are grouped by sample size or statistical functional. The best performing method for each column is underlined.

all
4
8
16
32
64
128
256
corr
mean
Q0.5
Q0.05
Q0.95
std


DB
0.33¯\underline{0.33}
0.820.82
0.53¯\underline{0.53}
0.58¯\underline{0.58}
0.53¯\underline{0.53}
0.11¯\underline{0.11}
0.03¯\underline{0.03}
0.03¯\underline{0.03}
0.00¯\underline{0.00}
0.290.29
0.07¯\underline{0.07}
0.430.43
0.40¯\underline{0.40}
0.57¯\underline{0.57}

SB
0.440.44
1.001.00
0.680.68
0.710.71
0.620.62
0.230.23
0.120.12
0.080.08
0.100.10
0.440.44
0.140.14
0.430.43
0.420.42
0.820.82

B-n
0.460.46
0.970.97
0.820.82
0.760.76
0.560.56
0.290.29
0.120.12
0.080.08
0.400.40
0.460.46
0.230.23
0.35¯\underline{0.35}
0.430.43
0.800.80

BCa
0.470.47
1.001.00
0.890.89
0.680.68
0.590.59
0.330.33
0.110.11
0.060.06
0.00¯\underline{0.00}
0.420.42
0.250.25
0.620.62
0.40¯\underline{0.40}
0.740.74

PB
0.470.47
1.001.00
0.760.76
0.760.76
0.620.62
0.300.30
0.120.12
0.080.08
0.200.20
0.440.44
0.190.19
0.470.47
0.470.47
0.820.82

BC
0.480.48
1.001.00
0.920.92
0.730.73
0.580.58
0.360.36
0.090.09
0.060.06
0.00¯\underline{0.00}
0.430.43
0.250.25
0.570.57
0.450.45
0.770.77

B-t
0.660.66
0.53¯\underline{0.53}
0.740.74
0.800.80
0.740.74
0.620.62
0.580.58
0.560.56
0.400.40
0.21¯\underline{0.21}
0.760.76
1.001.00
1.001.00
0.650.65

BB
0.800.80
1.001.00
1.001.00
0.920.92
0.830.83
0.760.76
0.640.64
0.590.59
0.600.60
0.470.47
0.950.95
1.001.00
1.001.00
0.790.79

Table [3.2](https://arxiv.org/html/2403.20182v3#S3.SS2 "3.2 Coverage of bootstrap methods ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") shows how often methods fail to meet the stringent criterion. DB outperforms other methods overall and on all sample sizes except n=4n=4. It is the best method or relatively close to the best on all functionals, except on one of the two extreme percentiles. BCa is second-best overall. The results so far suggest that overall DB is best, but can have very poor coverage in some cases, especially for the two extreme percentiles at small sample sizes. While a more liberal criterion will result in fewer failures for all methods, the ordering does not change.

Four of the six confidence levels in the experiments can be used to derive results for the two most common two-sided CIs (95%, 90%). Table [3.2](https://arxiv.org/html/2403.20182v3#S3.SS2 "3.2 Coverage of bootstrap methods ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") shows how often the methods fail to meet the liberal criterion for these two-sided intervals. These and results for other thresholds and KL are similar for one-sided and two-sided intervals. Most bootstrap methods meet the liberal criterion in almost all cases when n≥128n\geq 128 (n≥64n\geq 64 for DB), but even at n=256n=256 there are still two cases where even DB does not (standard deviation for log-normal). Excluding these, DB meets the very liberal criterion for all experiments for n≥64n\geq 64.

### 3.3 Coverage comparison with baseline methods

All of the results in this section are for one-sided CIs. Results for two-sided CIs are similar. Starting with the premise that when limited to a single method, DB is the best choice, this section takes a closer look at where DB is clearly outperformed by another method. The criterion used is that method A outperforms method B if B does not meet the liberal criterion and A is at least an order of magnitude better than method B. If a method is not able to produce CIs, it is outperformed by any method that can.

Cases where DB and baseline outperform each other. The number in the parentheses is the number of combinations where a method outperforms. There are a total of 36 combinations for every pair of nn and functional, except Pearson correlation, where there are 6, and the mean, where there are 48.

n
functional
baseline ≫\gg DB
DB ≫\gg baseline


4
corr
fisher (6)

4
mean
a-c (2); c-p (1); t-test (11); wilcoxon (1)
DB (2)

4
median
m-j (5); q-par (3)

4
Q(0.05)
q-nonpar (12); q-par (22)

4
Q(0.95)
q-par (21)
DB (4)

4
std
chi-sq (14)
DB (5)

8
corr
fisher (6)

8
mean
a-c (7); c-p (5); t-test (10); wilcoxon (3)
DB (3)

8
Q(0.05)
q-nonpar (12); q-par (22)
DB (3)

8
Q(0.95)
q-nonpar (12); q-par (21)

8
std
chi-sq (7)
DB (9)

16
mean
a-c (4); c-p (3); t-test (4)
DB (9)

16
Q(0.05)
q-nonpar (17); q-par (15)

16
Q(0.95)
m-j (10); q-par (11)
DB (4)

16
std
chi-sq (2)
DB (9)

32
mean
a-c (1); c-p (1); t-test (3)
DB (8)

32
Q(0.05)
m-j (6); q-nonpar (17); q-par (5)

32
Q(0.95)
m-j (17); q-par (6)

32
std

DB (12)

64
mean
a-c (1); c-p (1)
DB (7)

64
Q(0.05)
m-j (1); q-nonpar (3)

64
Q(0.95)

DB (5)

64
std
chi-sq (1)
DB (18)

128
mean
a-c (2); c-p (1); t-test (1)
DB (6)

128
Q(0.05)
m-j (2)
DB (1)

128
std

DB (24)

256
mean

DB (4)

256
std

DB (27)

Table [3.3](https://arxiv.org/html/2403.20182v3#S3.SS3 "3.3 Coverage comparison with baseline methods ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") adds detail to the results from Section [3.2](https://arxiv.org/html/2403.20182v3#S3.SS2 "3.2 Coverage of bootstrap methods ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?"). For Pearson correlation DB does not produce CIs for n=4n=4 and performs poorly for n=8n=8. It performs poorly on the two extreme percentiles for n≤32n\leq 32 and in some cases on the other functionals, mostly for n≤8n\leq 8. For Q(0.05) and Q(0.95), a better choice is q-par for the smaller sample sizes and m-j for sample size n=32n=32. For the other functionals and n≥8n\geq 8 (n≥16n\geq 16 for Pearson correlation) there is no clear advantage of using baseline methods. Note that for Q(0.05) and Q(0.95) and n=16,32n=16,32 B-n is as good as or better than baseline. Table [3.3](https://arxiv.org/html/2403.20182v3#S3.SS3 "3.3 Coverage comparison with baseline methods ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") shows the advantage of using B-n instead of DB for Q(0.05) and Q(0.95) for n≤32n\leq 32.

Cases where B-n and baseline outperform each other. Results are for the two extreme percentiles and n≤32n\leq 32. The number in the parentheses is the number of combinations where a method outperforms. There are a total of 36 combinations for every pair of nn and functional.

n
functional
baseline ≫\gg B-n
B-n ≫\gg baseline


4
Q(0.05)
q-nonpar (11); q-par (14)

4
Q(0.95)
q-par (14)

8
Q(0.05)
q-par (11)
B-n (1)

8
Q(0.95)
q-nonpar (4); q-par (10)
B-n (3)

16
Q(0.05)
q-nonpar (5); q-par (6)
B-n (5)

16
Q(0.95)
m-j (1); q-par (6)

32
Q(0.05)

B-n (4)

32
Q(0.95)
m-j (2); q-par (1)
B-n (6)

Note that BCa behaves similarly to DB, but DB is the better choice. For example, DB is at least an order of magnitude better than BCa in 17% of all cases while BCa is better than DB in 4% of the cases.

### 3.4 Absolute distance from exact CIs

Coverage by itself is not sufficient, as CI endpoints should also match the exact endpoints. An extreme example would be to generate a very large endpoint (wide two-sided interval) with probability α\alpha and a very small endpoint (narrow two-sided interval) with probability α\alpha. This would result in nominal coverage but useless CIs.

Table [3.4](https://arxiv.org/html/2403.20182v3#S3.SS4 "3.4 Absolute distance from exact CIs ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") shows that B-n has lowest distance from exact, while DB and BCa perform relatively poorly across all groups. This result cannot be interpreted in isolation, because there is typically a trade-off between coverage and distance (see Figure [1](https://arxiv.org/html/2403.20182v3#S3.F1 "Figure 1 ‣ 3.4 Absolute distance from exact CIs ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") for an illustrative example).

Mean absolute distance from exact for one-sided CIs. For each combination, the value is normalized with two standard deviations of exact intervals. The all column is across all experiments, while the remaining results are grouped by sample size or statistical functional. The best performing method for each column is underlined.

all
4
8
16
32
64
128
256
corr
mean
Q0.5
Q0.05
Q0.95
std


B-n
0.240¯\underline{0.240}
0.4230.423
0.333¯\underline{0.333}
0.269¯\underline{0.269}
0.221¯\underline{0.221}
0.180¯\underline{0.180}
0.145¯\underline{0.145}
0.118¯\underline{0.118}
0.095¯\underline{0.095}
0.146¯\underline{0.146}
0.201¯\underline{0.201}
0.329¯\underline{0.329}
0.330¯\underline{0.330}
0.2440.244

BB
0.2640.264
0.395¯\underline{0.395}
0.3460.346
0.3170.317
0.2610.261
0.2060.206
0.1780.178
0.1530.153
0.095¯\underline{0.095}
0.146¯\underline{0.146}
0.2620.262
0.3620.362
0.3830.383
0.227¯\underline{0.227}

SB
0.3180.318
0.5440.544
0.4390.439
0.3520.352
0.2950.295
0.2430.243
0.1990.199
0.1650.165
0.1250.125
0.1610.161
0.2760.276
0.4790.479
0.4410.441
0.3080.308

BC
0.3320.332
0.6200.620
0.4610.461
0.3820.382
0.3160.316
0.2530.253
0.2080.208
0.1730.173
0.1360.136
0.2420.242
0.2860.286
0.4160.416
0.5360.536
0.2580.258

BCa
0.3400.340
0.6000.600
0.4580.458
0.3920.392
0.3290.329
0.2750.275
0.2220.222
0.1830.183
0.1360.136
0.2680.268
0.2860.286
0.4320.432
0.5210.521
0.2680.268

PB
0.3500.350
0.6420.642
0.4990.499
0.3860.386
0.3130.313
0.2490.249
0.2050.205
0.1700.170
0.1240.124
0.1660.166
0.2950.295
0.5540.554
0.5020.502
0.3200.320

DB
0.3600.360
0.5970.597
0.5060.506
0.3940.394
0.3290.329
0.2860.286
0.2340.234
0.1880.188
0.1590.159
0.2840.284
0.2990.299
0.4880.488
0.5010.501
0.2790.279

B-t
0.9660.966
4.3764.376
0.6730.673
0.6680.668
0.5240.524
0.3000.300
0.2310.231
0.1880.188
0.1160.116
0.6240.624
1.7511.751
0.9120.912
1.1271.127
0.6360.636

Table [3.4](https://arxiv.org/html/2403.20182v3#S3.SS4 "3.4 Absolute distance from exact CIs ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") shows where a baseline method has better distance from exact than DB, but only for cases where its coverage is not an order of magnitude worse. B-n is included as the bootstrap method that performs best in distance from exact. Results are similar to those in Table [3.3](https://arxiv.org/html/2403.20182v3#S3.SS3 "3.3 Coverage comparison with baseline methods ‣ 3 Results ‣ Quantifying Uncertainty: All We Need is the Bootstrap?") - baseline methods and B-n outperform DB for the two extreme percentiles. That is, in most cases, lower distance from exact comes at the expense of worse coverage.

Cases where baseline (with B-n included) outperforms DB in absolute distance from exact intervals. The number in the parentheses is the number of combinations where a method outperforms. Note that there are a total of 36 combinations for every pair of nn and functional, except Pearson correlation, where there are 6, and the mean, where there are 48.

n
functional
baseline and B-n ≫\gg DB

4
corr
fisher (6)

4
mean
a-c (2); B-n (7); c-p (1); t-test (3); wilcoxon (1)

4
median
B-n (2); m-j (2); q-par (2)

4
Q(0.05)
B-n (19); q-nonpar (3); q-par (17)

4
Q(0.95)
B-n (17); q-par (15)

4
std
B-n (6)

8
corr
fisher (6)

8
mean
a-c (2); B-n (6); c-p (1); t-test (8); wilcoxon (2)

8
Q(0.05)
B-n (21); q-nonpar (6); q-par (18)

8
Q(0.95)
B-n (19); q-nonpar (7); q-par (19)

16
corr
fisher (1)

16
mean
B-n (4); t-test (3)

16
Q(0.05)
B-n (11); q-nonpar (3); q-par (6)

16
Q(0.95)
B-n (8); m-j (6); q-par (6)

32
mean
a-c (1); B-n (3); c-p (1); t-test (5)

32
Q(0.05)
B-n (8); m-j (5); q-par (9)

32
Q(0.95)
B-n (8); m-j (4); q-par (11)

32
std
chi-sq (1)

64
mean
B-n (1); t-test (1)

64
Q(0.05)
B-n (3); m-j (1); q-par (1)

64
Q(0.95)
B-n (1); m-j (6); q-par (1)

64
std
chi-sq (2)

128
mean
B-n (1); t-test (1)

128
Q(0.05)
B-n (1); m-j (1); q-nonpar (1)

128
Q(0.95)
B-n (2); m-j (3)

![Refer to caption](x1.png)
![Refer to caption](application_example.png)

## 4 Conclusion

This paper is the most comprehensive review of empirical results for bootstrap methods to date, along with an extensive empirical comparison. The simulation study encompasses not only the most widely used non-parametric bootstrap methods but also the most common techniques for quantifying uncertainty in general. Furthermore, a novel criterion for assessing confidence interval quality is introduced, which improves on existing evaluation approaches.

DB is identified as the overall best method, contrary to some recommendations of BCa for general cases [[2](https://arxiv.org/html/2403.20182v3#bib.bib2)], but in line with other recommendations [[51](https://arxiv.org/html/2403.20182v3#bib.bib51), [23](https://arxiv.org/html/2403.20182v3#bib.bib23)] and the few empirical studies that included DB. These results are also in line with related work: PB performs relatively poorly. For small nn B-t performs best for the mean and BCa best for Pearson correlation, although DB performs similarly. B-t relies on an estimate of variance and can produce very long CIs. Bootstrapping can perform poorly compared do chi-squared CIs on variance for small nn and normal distribution, however, as demonstrated, chi-squared performs poorly on non-normal distributions and DB is comparable or better for n≥32n\geq 32.

DB has two weaknesses. It can perform relatively poorly when n=4,8n=4,8 and on extreme percentiles for n≤32n\leq 32. The latter can be mitigated by using B-n but also raises the question if DB can be modified to deal with these cases, while still preserving most of its simplicity. This leaves us with n=4,8n=4,8, where it has to be acknowledged that a non-parametric approach is often worse than a parametric approach even when the assumptions of the parametric method are violated. It was not investigated to what extent bootstrap diagnostics (see [[52](https://arxiv.org/html/2403.20182v3#bib.bib52)] and [[3](https://arxiv.org/html/2403.20182v3#bib.bib3), Ch.3.10]) could further mitigate these issues.

The dimensions of the experiment can be improved, as it only includes one DGP for Pearson correlation, which is not nearly as comprehensive as the recent study by [[37](https://arxiv.org/html/2403.20182v3#bib.bib37)], who did not include DB. Other commonly used functionals could also be included, such as regression model coefficients, non-parametric correlation, and distances between distributions. Furthermore, the study focuses on independent data. Related work on hierarchical, temporal, spatial, and other dependencies is sparse, but mostly in favor of bootstrapping. And in more complex problems bootstrapping is often the only viable approach.

### 4.1 Practical implications

One general implication of these results for practitioners is that DB is superior to BCa. Considering that the DB is also conceptually simpler and easier to implement than the BCa, it should be a standard feature in every bootstrap library. This is currently not the case. For example, SPSS and popular bootstrap libraries from Python (scipy.stats.bootstrap, bootstrapping) and R (boot) do not implement any form of iterated bootstrap. While the boot package does implement the studentized bootstrap, which involves inner bootstrap sampling, this method performed poorly in our simulation study.

The underutilization of the double bootstrap could be attributed to the misconception that BCa is superior or to the DB being more computationally intensive. Due to its quadratic time complexity, the double bootstrap will not scale to large sample sizes as well as BCa. However, with advances in computation, this is no longer a significant issue. It can also be argued that once a sample size is large enough to make the double bootstrap prohibitive, the choice of method becomes moot, as even the percentile bootstrap will likely perform well enough. Additionally, the double bootstrap is easy to parallelize, and efficient approximations have been developed, such as [[53](https://arxiv.org/html/2403.20182v3#bib.bib53), [54](https://arxiv.org/html/2403.20182v3#bib.bib54)].

In critical applications of statistics, there is no substitute for thoroughly understanding the statistical task at hand, carefully choosing the most appropriate method, and applying it correctly. However, if a single method had to be recommended, the double bootstrap appears to be the best choice. The two scenarios where particular care should be taken are with very small sample sizes and when estimating extreme quantiles, both of which are arguably less common in practice.

The double bootstrap can also play an important role in the teaching of applied statistics. In particular, it can be a valuable tool in a bootstrap-centric introduction to applied statistics for a broad audience of individuals who will use statistics but will only receive one or two courses of formal statistical training. For example, in most empirical sciences.

A basic understanding of standard statistical functionals is required, regardless of what method is used to quantify uncertainty. For example, the mean (average) has to be understood, before bootstrapping, t-distribution-based, or any other approach to constructing CIs can be used. Once functionals are understood, percentile bootstrap is conceptually very simple, can be implemented in a few lines of code, and then applied in the same way to any functional. This is an order of magnitude less complex and time-consuming than teaching a different approach for every functional.

The main disadvantage of the percentile bootstrap is its suboptimal performance in practice. Consequently, a student transitioning into a practitioner must either switch to more complicated bootstrap approaches, such as BCa, or apply parametric approaches. The double bootstrap alleviates this issue, similar to the percentile bootstrap. With just a few more lines of code, we can achieve excellent performance, often surpassing methods that are more complex to understand and implement.

This bootstrap-centric approach is less pedagogically complex than learning several different approaches, and it is computationally not an issue on modern hardware. Lack of software support might be an issue, but a minor one, because percentile and double bootstrap are easy to implement. We agree with [[1](https://arxiv.org/html/2403.20182v3#bib.bib1)] that the main reasons that such a shift has not occurred is the lack of teaching materials and legitimate concerns for backwards compatibility. That is, the concern with not teaching the students the methods that are currently dominant statistical practice. This study contributes to alleviating those concerns, showing that bootstrapping, in particular double bootstrap, is overall at least as good as, if not superior to, standard parametric approaches. However, the logical next step is to develop and test an introductory course in applied statistics that relies solely on the bootstrap.

## Acknowledgment

We thank Gregor Sočan for his helpful comments.

## Funding

This work was supported by the Slovenian Research and Innovation Agency under Grants P2-0442 and J5-60084.

## Data Availability Statement

The authors confirm that the data supporting the findings of this study are available within the article and its supplementary materials.

## References

![Mascot Sammy](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)
