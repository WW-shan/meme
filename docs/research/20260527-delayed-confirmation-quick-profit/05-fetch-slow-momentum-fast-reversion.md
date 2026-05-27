\ul

# Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection

###### Abstract

Momentum strategies are an important part of alternative investments and are at the heart of commodity trading advisors (CTAs). These strategies have, however, been found to have difficulties adjusting to rapid changes in market conditions, such as during the 2020 market crash. In particular, immediately after momentum turning points, where a trend reverses from an uptrend (downtrend) to a downtrend (uptrend), time-series momentum (TSMOM) strategies are prone to making bad bets. To improve the response to regime change, we introduce a novel approach, where we insert an online changepoint detection (CPD) module into a Deep Momentum Network (DMN) [[1](#bib.bib1)] pipeline, which uses an LSTM deep-learning architecture to simultaneously learn both trend estimation and position sizing. Furthermore, our model is able to optimise the way in which it balances 1) a slow momentum strategy which exploits persisting trends, but does not overreact to localised price moves, and 2) a fast mean-reversion strategy regime by quickly flipping its position, then swapping it back again to exploit localised price moves. Our CPD module outputs a changepoint location and severity score, allowing our model to learn to respond to varying degrees of disequilibrium, or smaller and more localised changepoints, in a data driven manner. Back-testing our model over the period 1995–2020, the addition of the CPD module leads to an improvement in Sharpe ratio of one-third. The module is especially beneficial in periods of significant nonstationarity, and in particular, over the most recent years tested (2015–2020) the performance boost is approximately two-thirds. This is interesting as traditional momentum strategies have been underperforming in this period.

## I Introduction

Time-series (TS) momentum [[2](#bib.bib2)] strategies are derived from the philosophy that strong price trends have a tendency to persist. These trends have been observed to hold across a range of timescales, asset classes and time periods [[3](#bib.bib3), [4](#bib.bib4), [5](#bib.bib5)]. Momentum strategies are often referred to as ‘follow the winner’, because it is assumed that winners will continue to be winners in the subsequent period. Momentum strategies are an important part of alternative investments and are at the heart of commodity trading advisors (CTAs). Much effort goes into quantifying the magnitude of trends [[5](#bib.bib5), [6](#bib.bib6), [7](#bib.bib7)] and sizing traded positions accordingly [[8](#bib.bib8), [9](#bib.bib9), [10](#bib.bib10)]. Rather than using handcrafted techniques to identify trends and select positions, [[1](#bib.bib1)] introduces Deep Momentum Networks (DMNs), where a Long Short-Term Memory (LSTM) [[11](#bib.bib11)] deep learning architecture achieves this by directly optimising on the Sharpe ratio of the signal. Deep Learning has been widely utilised for time-series forecasting [[12](#bib.bib12)], achieving a high level of accuracy across various fields, including the field of finance for both daily data [[1](#bib.bib1), [13](#bib.bib13), [14](#bib.bib14), [15](#bib.bib15), [16](#bib.bib16)] and in a high frequency setting, using limit order book data [[17](#bib.bib17), [18](#bib.bib18)]. In recent years, implementation of such deep learning models has been made accessible via extensive open source frameworks such as TensorFlow [[19](#bib.bib19)] and PyTorch [[20](#bib.bib20)].

Momentum strategies aim to capitalise on persisting price trends, however occasionally these trends break down, which we label momentum turning points. At these turning points, momentum strategies are prone to performing poorly because they are unable to adapt quickly to this abrupt change in regime. This concept is explored in [[21](#bib.bib21)] where a slow momentum signal based on a long lookback window, such as 12 months, is blended with a fast momentum signal which is based on a short lookback window, such as 1 month. This approach is a balancing act between reducing noise and being quick enough to respond to turning points. Adopting the terminology from [[21](#bib.bib21)], a Bull or Bear market is when the two momentum signals agree on a long or short position respectively. If slow momentum suggests a long (short) position, and fast momentum a short (long) position, we term this a Correction (Rebound) phase.

Correction and Rebound phases, where the momentum assumption breaks down, are examples of mean-reversion [[22](#bib.bib22), [23](#bib.bib23), [24](#bib.bib24)] regimes. Mean-reversion trading strategies, often referred to as ‘follow the loser’ strategies, assume losers (winners) over some lookback window will be winners (losers) in the subsequent period. If we observe the positions taken by a DMN, alongside exploiting persisting trends, the model also exploits fluctuations in returns data at a shorter time horizon by regularly flipping its position then quickly changing back again. We argue that the high Sharpe ratio achieved by DMNs can be largely attributed to its fast mean-reversion property.

Changepoint detection (CPD) is a field which involves the identification of abrupt changes in sequential data, where the generative parameters for our model after the changepoint are independent of those which come before. The nonstationarity of real world time-series in fields such as finance, robotics and sensor data has led to a plethora of research in this field. To enable us to respond to CPD in real time we require an ‘online’ algorithm, which processes each data point as it becomes available, as opposed to ‘offline’ algorithms which consider the entire data set at once and detect changepoints retrospectively. First introduced by [[25](#bib.bib25)], Bayesian approaches to online CPD, which naturally accommodate to noisy, uncertain and incomplete time-series data, have proven to be very successful. Assuming a changepoint model of the parameters, the Bayesian approach integrates out the uncertainty for these parameters as opposed to using a point estimate. Gaussian Processes (GPs) [[26](#bib.bib26), [27](#bib.bib27)], which are collections of random variables where any finite number of which have joint Gaussian distributions, are well suited to time-series modelling [[28](#bib.bib28)]. GPs are often referred to as a Bayesian non-parametric model and have the ability to handle changepoints [[29](#bib.bib29), [30](#bib.bib30), [31](#bib.bib31)]. Rather than comparing a slow and fast momentum signals to detect regime change, we utilise GPs as a more principled method for detecting momentum turning points. For our experiments, we use the Python package GPflow [[32](#bib.bib32)] to build Gaussian process models, which leverage the TensorFlow framework.

In this paper, we introduce a novel approach, where we add an online CPD module to a DMN pipeline, to improve overall strategy returns. By incorporating the CPD module, we optimise our response to momentum turning points in a data-driven manner by passing outputs from the module as inputs to a DMN, which in turn learns trading rules and optimises position based on some finance value function such as Sharpe Ratio [[33](#bib.bib33)]. This approach helps to correctly identify when we are in a Bull or Bear market and select the momentum strategy accordingly. With the addition of the CPD module, the new model learns how to exploit, but not overreact, to noise at a shorter timescale. Our strategy is able to exploit the fast reversion we observe in DMNs but effectively balance this with a slow momentum strategy and improve returns across an entire Bull or Bear regime. Effectively the new pipeline has more knowledge on how to respond to abrupt changes, or lack of changes in a data driven way.

We argue that the concept of CPD is an artificial construct which can occur at varying degrees of severity and is dependent on decisions such as length of the lookback horizon for CPD. Rather than specifying regimes based on some criteria or threshold, we use our CPD module to quantify, or score, the level of disequilibrium, allowing the model to consider smaller or more localised ‘regime changes’. The length of the lookback window is the most sensitive design choice for the CPD module, for if the lookback horizon is too long, we miss smaller, but still potentially significant regime changes. If the horizon is too short, the data becomes too noisy and is of little value. We introduce the lookback window length (LBW) as a structural hyperparameter which we optimise using the outer optimisation loop of our model. This allows the module to be more tightly coupled with our LSTM module, helping us to maximise the efficiency of the CPD, and allowing us to tweak the LSTM hyperparamters in conjunction with the LBW.

It can be noted that the performance of DMNs, without CPD, deteriorates in more recent years. The deterioration in performance is especially notable in the period 2015–2020, which exhibits a greater degree of turbulence, or disequilibrium, than the preceding years. One possible explanation of deterioration in momentum strategies in recent years is the concept of ‘factor crowding’, which is discussed in depth in [[34](#bib.bib34)], where it is argued that arbitrageurs inflict negative externalities on one another. By using the same models, and hence taking the same positions, a coordination problem is created, pushing the price away from fundamentals. It is argued that momentum strategies are susceptible to this scenario. Impressively, the addition of a CPD module helps to alleviate the deterioration in performance and our model significantly outperforms the standard DMN model during the 2015–2020 period. A similar phenomenon can be observed from around 2003, when electronic trading was becoming more common, where the deep learning based strategies start to significantly outperform classic TSMOM strategies.

## II Changepoint Detection Using Gaussian Processes

A classic univariate regression problem, of the form y​(x)=f​(x)+ϵ𝑦𝑥𝑓𝑥italic-ϵy(x)=f(x)+\epsilon, where ϵitalic-ϵ\epsilon is an additive noise process, has the goal of evaluating the function f𝑓f and the probability distribution p​(y∗|x∗)𝑝conditionalsubscript𝑦subscript𝑥p(y\_{\*}|x\_{\*}) of some point y∗subscript𝑦y\_{\*} given some x∗subscript𝑥x\_{\*}. Our daily time-series data, for asset i𝑖i, consists of a sequence of observations for (closing) price {pt(i)}t=1Tsuperscriptsubscriptsuperscriptsubscript𝑝𝑡𝑖𝑡1𝑇\{p\_{t}^{(i)}\}\_{t=1}^{T}, up to time T𝑇T. Since financial time-series are nonstationary in the mean, for each time t𝑡t we take the first difference of the time-series, otherwise known as the arithmetic returns,

|  |  |  |  |
| --- | --- | --- | --- |
|  | rt−1,t(i)=pt(i)−pt−1(i)pt−1(i),superscriptsubscript𝑟  𝑡1𝑡𝑖superscriptsubscript𝑝𝑡𝑖superscriptsubscript𝑝𝑡1𝑖superscriptsubscript𝑝𝑡1𝑖r\_{t-1,t}^{(i)}=\frac{p\_{t}^{(i)}-p\_{t-1}^{(i)}}{p\_{t-1}^{(i)}}, |  | (1) |

in an attempt to remove linear trend in the mean. Throughout this paper, for brevity, we will refer to rt−1,tsubscript𝑟

𝑡1𝑡r\_{t-1,t} simply as rtsubscript𝑟𝑡r\_{t}. For the purposes of CPD, it is not computationally feasible, nor is it necessary, to consider the entire time-series, hence we consider the series {rt(i)}t=T−lTsubscriptsuperscriptsubscriptsuperscript𝑟𝑖𝑡𝑇𝑡𝑇𝑙\{r^{(i)}\_{t}\}^{T}\_{t=T-l}, with lookback horizon l𝑙l from time T𝑇T. For every CPD window, where 𝒯={T−l,T−l+1,…,T}𝒯𝑇𝑙𝑇𝑙1…𝑇\mathcal{T}=\{T-l,T-l+1,\ldots,T\}, we standardise our returns as,

|  |  |  |  |
| --- | --- | --- | --- |
|  | rt^(i)=rt(i)−𝔼𝒯​[rt(i)]Var𝒯​[rt(i)].superscript^subscript𝑟𝑡𝑖superscriptsubscript𝑟𝑡𝑖subscript𝔼𝒯delimited-[]superscriptsubscript𝑟𝑡𝑖subscriptVar𝒯delimited-[]superscriptsubscript𝑟𝑡𝑖\hat{r\_{t}}^{(i)}=\frac{r\_{t}^{(i)}-\mathbb{E}\_{\mathcal{T}}\left[r\_{t}^{(i)}\right]}{\sqrt{\mathrm{Var}\_{\mathcal{T}}\left[r\_{t}^{(i)}\right]}}. |  | (2) |

This step is taken for two reasons, we can assume that the mean over our window is zero and, with unit variance, we have more consistency across all windows when we run our CPD module.

Our approach to changepoint detection, involves a curve fitting approach for input-output pairs (t,r^t(i))𝑡subscriptsuperscript^𝑟𝑖𝑡(t,\hat{r}^{(i)}\_{t}) via the use of Gaussian Process (GP) regression [[27](#bib.bib27)]. GP regression is a probabilistic, non-parametric method, popular in the fields of machine learning and time-series analysis [[28](#bib.bib28)]. It is a kernel based technique where the Gaussian Process 𝒢​𝒫𝒢𝒫\mathcal{GP} is specified by a covariance function kξ​(⋅)subscript𝑘𝜉⋅k\_{\xi}(\cdot), which is in turn parameterised by a set of hyperparameters ξ𝜉\xi. In its common guise, the GP has a stationary kernel; however, it should be noted that GPs can readily work well even when the time-series is nonstationary [[35](#bib.bib35)]. We define the GP as a distribution over functions where,

|  |  |  |  |
| --- | --- | --- | --- |
|  | r^t(i)=f​(t)+ϵt,f∼𝒢​𝒫​(0,kξ),ϵt∼𝒩​(0,σn2),formulae-sequencesuperscriptsubscript^𝑟𝑡𝑖𝑓𝑡subscriptitalic-ϵ𝑡formulae-sequencesimilar-to𝑓𝒢𝒫0subscript𝑘𝜉similar-tosubscriptitalic-ϵ𝑡𝒩0subscriptsuperscript𝜎2𝑛\hat{r}\_{t}^{(i)}=f(t)+\epsilon\_{t},f\sim\mathcal{GP}(0,k\_{\xi}),\epsilon\_{t}\sim\mathcal{N}(0,\sigma^{2}\_{n}), |  | (3) |

given noise variance σnsubscript𝜎𝑛\sigma\_{n}, which helps to deal with noisy outputs which are uncorrelated.

It has been demonstrated in [[36](#bib.bib36), [37](#bib.bib37)] that a Matérn 3/2 kernel is a good choice of covariance function for noisy financial data, which tends to be highly non-smooth and not infinitely differentiable. This problem setting favours the least smooth of the Matérn family of kernels which is the 3/2 kernel. We parametrise our Matérn 3/2 kernel as,

|  |  |  |  |
| --- | --- | --- | --- |
|  | k​(x,x′)=σh2​(1+3​|x−x′|λ)​e(−3​|x−x′|λ),𝑘𝑥superscript𝑥′superscriptsubscript𝜎ℎ213𝑥superscript𝑥′𝜆superscript𝑒3𝑥superscript𝑥′𝜆k(x,x^{\prime})=\sigma\_{h}^{2}\left(1+\frac{\sqrt{3}|x-x^{\prime}|}{\lambda}\right)e^{\left(-\frac{\sqrt{3}|x-x^{\prime}|}{\lambda}\right)}, |  | (4) |

with kernel hyperparameters ξM=(λ,σh,σn)subscript𝜉𝑀𝜆subscript𝜎ℎsubscript𝜎𝑛\xi\_{M}=(\lambda,\sigma\_{h},\sigma\_{n}), where λ𝜆\lambda is the input scale and σhsubscript𝜎ℎ\sigma\_{h} the output scale. We define our covariance matrix, for a set of locations 𝐱=[x1,x2,…​xn]𝐱

subscript𝑥1subscript𝑥2…subscript𝑥𝑛\mathbf{x}=[x\_{1},x\_{2},\ldots x\_{n}] as,

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝐊​(𝐱,𝐱)=(k​(x1,x1)⋯k​(x1,xn)⋮⋱⋮k​(xn,x1)⋯k​(xn,xn)).𝐊𝐱𝐱𝑘subscript𝑥1subscript𝑥1⋯𝑘subscript𝑥1subscript𝑥𝑛missing-subexpression⋮⋱⋮missing-subexpression𝑘subscript𝑥𝑛subscript𝑥1⋯𝑘subscript𝑥𝑛subscript𝑥𝑛missing-subexpression\mathbf{K}(\mathbf{x},\mathbf{x})=\left(\begin{array}[]{cccc}k(x\_{1},x\_{1})&\cdots&k(x\_{1},x\_{n})\\ \vdots&\ddots&\vdots\\ k(x\_{n},x\_{1})&\cdots&k(x\_{n},x\_{n})\end{array}\right). |  | (5) |

Using 𝐫^=[r^t−l,…,r^t]^𝐫

subscript^𝑟𝑡𝑙…subscript^𝑟𝑡\mathbf{\hat{r}}=[\hat{r}\_{t-l},...,\hat{r}\_{t}], we integrate out the function variables to give p​(𝐫^|ξ)=𝒩​(𝟎,𝐕)𝑝conditional^𝐫𝜉𝒩0𝐕p(\mathbf{\hat{r}}|\xi)=\mathcal{N}(\mathbf{0},\mathbf{V}), with 𝐕=𝐊+σn2​𝐈𝐕𝐊superscriptsubscript𝜎𝑛2𝐈\mathbf{V}=\mathbf{K}+\sigma\_{n}^{2}\mathbf{I}. Since p​(ξ|𝐫^)𝑝conditional𝜉^𝐫p(\xi|\mathbf{\hat{r}}) is intractable, we instead apply Bayes’ rule,

|  |  |  |  |
| --- | --- | --- | --- |
|  | p​(ξ|𝐫^)=p​(𝐫^|ξ)​p​(ξ)p​(𝐫^)𝑝conditional𝜉^𝐫𝑝conditional^𝐫𝜉𝑝𝜉𝑝^𝐫p(\xi|\mathbf{\hat{r}})=\frac{p(\mathbf{\hat{r}}|\xi)p(\xi)}{p(\mathbf{\hat{r}})} |  | (6) |

and perform type II maximum likelihood on p​(𝐫^|ξ)𝑝conditional^𝐫𝜉p(\mathbf{\hat{r}}|\xi). We minimise the negative log marginal likelihood,

|  |  |  |  |
| --- | --- | --- | --- |
|  | nlmlξ=minξ⁡(12​𝐫^𝖳​𝐕−1​𝐫^+12​log⁡|𝐕|+l+12​log⁡2​π).subscriptnlml𝜉subscript𝜉12superscript^𝐫𝖳superscript𝐕1^𝐫12𝐕𝑙122𝜋\mathrm{nlml}\_{\xi}=\min\_{\xi}\left(\frac{1}{2}\mathbf{\hat{r}}^{\mathsf{T}}\mathbf{V}^{-1}\mathbf{\hat{r}}+\frac{1}{2}\log|\mathbf{V}|+\frac{l+1}{2}\log 2\pi\right). |  | (7) |

We use the GPflow framework to compute the hyperparameters ξ𝜉\xi, which in turn uses the L-BFGS-B [[38](#bib.bib38)] optimisation algorithm via the scipy.optimize.minimize package.

In [[29](#bib.bib29), [28](#bib.bib28)] it is assumed that our function of interest is well behaved, except there is a drastic change, or changepoint, at c∈{t−l+1,t−l+2,…,t−1}𝑐𝑡𝑙1𝑡𝑙2…𝑡1c\in\{t-l+1,t-l+2,\ldots,t-1\}, after which all observations before c𝑐c are completely uninformative about the observations after this point. It is important to note that the lookback window (LBW) l𝑙l for this approach needs to be prespecified and it is assumed that it contains a single changepoint. Each of the two regions are described by different covariance functions kξ1subscript𝑘subscript𝜉1k\_{\xi\_{1}}, kξ2subscript𝑘subscript𝜉2k\_{\xi\_{2}}, in our case Matérn 3/2 kernels, which are parameterised by hyperparameters ξ1subscript𝜉1\xi\_{1} and ξ2subscript𝜉2\xi\_{2} respectively. The Region-switching kernel is,

|  |  |  |  |
| --- | --- | --- | --- |
|  | kξR​(x,x′)={kξ1​(x,x′)x,x′<ckξ2​(x,x′)x,x′≥c0otherwise,subscript𝑘subscript𝜉𝑅𝑥superscript𝑥′casessubscript𝑘subscript𝜉1𝑥superscript𝑥′  𝑥superscript𝑥′ 𝑐subscript𝑘subscript𝜉2𝑥superscript𝑥′  𝑥superscript𝑥′ 𝑐0otherwisek\_{\xi\_{R}}(x,x^{\prime})=\left\{\begin{array}[]{cc}k\_{\xi\_{1}}(x,x^{\prime})&x,x^{\prime}<c\\ k\_{\xi\_{2}}(x,x^{\prime})&x,x^{\prime}\geq c\\ 0&\mathrm{otherwise,}\\ \end{array}\right. |  | (8) |

with full set of hyperparameters ξR={ξ1,ξ2,c,σn}subscript𝜉𝑅subscript𝜉1subscript𝜉2𝑐subscript𝜎𝑛\xi\_{R}=\{\xi\_{1},\xi\_{2},c,\sigma\_{n}\}. Here, a changepoint can take multiple forms, with these cases being either a drastic change in covariance, a sudden change in the input scale, or a sudden change in the output scale. In the context of financial time-series we can think of these cases as either a change in correlation length, a change in mean-reversion length or a change in volatility.

It is computationally inefficient to fit 2​(l−1)2𝑙12(l-1) GPs, to minimise nlmlξRsubscriptnlmlsubscript𝜉𝑅\mathrm{nlml}\_{\xi\_{R}} as in ([7](#S2.E7 "In II Changepoint Detection Using Gaussian Processes ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection")), due to the introduction the discrete hyperparameter c𝑐c. We instead borrow an idea from [[31](#bib.bib31)] and approximate the abrupt change of covariance in ([8](#S2.E8 "In II Changepoint Detection Using Gaussian Processes ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection")) using a sigmmoid function σ​(x)=1/(1+e−s​(x−c))𝜎𝑥11superscript𝑒𝑠𝑥𝑐\sigma(x)=1/\left(1+e^{-s(x-c)}\right) which has the properties σ​(x,x′)=σ​(x)​σ​(x′)𝜎𝑥superscript𝑥′𝜎𝑥𝜎superscript𝑥′\sigma(x,x^{\prime})=\sigma(x)\sigma(x^{\prime}) and σ¯​(x,x′)​(1−σ​(x))​(1−σ​(x′))¯𝜎𝑥superscript𝑥′1𝜎𝑥1𝜎superscript𝑥′\bar{\sigma}(x,x^{\prime})(1-\sigma(x))(1-\sigma(x^{\prime})). Here, c∈(t−l,t)𝑐𝑡𝑙𝑡c\in(t-l,t) is the changepoint location and s>0𝑠0s>0 is the steepness parameter. Our Changepoint kernel is,

|  |  |  |  |
| --- | --- | --- | --- |
|  | kξC​(x,x′)=kξ1​(x,x′)​σ​(x,x′)+kξ2​(x,x′)​σ¯​(x,x′),subscript𝑘subscript𝜉𝐶𝑥superscript𝑥′subscript𝑘subscript𝜉1𝑥superscript𝑥′𝜎𝑥superscript𝑥′subscript𝑘subscript𝜉2𝑥superscript𝑥′¯𝜎𝑥superscript𝑥′k\_{\xi\_{C}}(x,x^{\prime})=k\_{\xi\_{1}}(x,x^{\prime})\sigma(x,x^{\prime})+k\_{\xi\_{2}}(x,x^{\prime})\bar{\sigma}(x,x^{\prime}), |  | (9) |

with full set of hyperparameters ξC={ξ1,ξ2,c,s,σn}subscript𝜉𝐶subscript𝜉1subscript𝜉2𝑐𝑠subscript𝜎𝑛\xi\_{C}=\{\xi\_{1},\xi\_{2},c,s,\sigma\_{n}\}. We can compute nlmlξCsubscriptnlmlsubscript𝜉𝐶\mathrm{nlml}\_{\xi\_{C}} by optimising the parameters a single GP, which is significantly more efficient than computing nlmlξRsubscriptnlmlsubscript𝜉𝑅\mathrm{nlml}\_{\xi\_{R}}, despite having additional hyperparameters. This new kernel has the added benefit of capturing more gradual transitions from one covariance function to another, due to the additional of the steepness parameter s𝑠s. We implement ([9](#S2.E9 "In II Changepoint Detection Using Gaussian Processes ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection")) in GPflow via the gpflow.kernels.ChangePoints class, adding the constraint c∈(t−l,t)𝑐𝑡𝑙𝑡c\in(t-l,t), which is not enforced by default.

![Refer to caption](/html/2105.13727/assets/Images/CPD.png)

To quantify the level of disequilibrium, we look at the reduction in negative log marginal likelihood achieved via the introduction of the changepoint kernel hyperparameters, through comparison to nlmlξMsubscriptnlmlsubscript𝜉𝑀\textrm{nlml}\_{\xi\_{M}}. If the introduction of additional hyperparameters leads to no reduction in negative log marginal likelihood, then the level of disequilibrium is low. Conversely, if the reduction is large, this indicates significant disequilibrium, or a stronger changepoint, because the data is better described by two covariance functions. Our changepoint score νt(i)∈(0,1)subscriptsuperscript𝜈𝑖𝑡01\nu^{(i)}\_{t}\in(0,1) and location γt(i)∈(0,1)subscriptsuperscript𝛾𝑖𝑡01\gamma^{(i)}\_{t}\in(0,1) are,

|  |  |  |  |
| --- | --- | --- | --- |
|  | νt(i)=1−11+e−(nlmnξC−nlmnξM),γt(i)=c−(t−l)l,formulae-sequencesubscriptsuperscript𝜈𝑖𝑡111superscriptesubscriptnlmnsubscript𝜉𝐶subscriptnlmnsubscript𝜉𝑀subscriptsuperscript𝛾𝑖𝑡𝑐𝑡𝑙𝑙\nu^{(i)}\_{t}=1-\frac{1}{1+\mathrm{e}^{-(\mathrm{nlmn}\_{\xi\_{C}}-\mathrm{nlmn}\_{\xi\_{M}})}},\quad\gamma^{(i)}\_{t}=\frac{c-(t-l)}{l}, |  | (10) |

which are both normalised values which helps to improve stability and performance of our LSTM module.

## III Momentum Strategies Review

### III-A Classical Strategies

In this paper we focus on univariate time-series approaches [[2](#bib.bib2)], as opposed to cross-sectional [[39](#bib.bib39)] strategies, which trade assets against each other and select a portfolio based on relative ranking. Volatility scaling [[10](#bib.bib10), [8](#bib.bib8)] has been proven to play a crucial role in the positive performance of TSMOM strategies, including deep learning strategies [[1](#bib.bib1)]. We scale the returns of each asset by its volatility, so that each asset has a similar contribution to the overall portfolio returns, ensuring that our strategy targets a consistent amount of risk. The consistency over time and across assets has the added benefit of allowing us us to benchmark strategies. Targeting an annualised volatility σtgtsubscript𝜎tgt\sigma\_{\mathrm{tgt}}, which we take to be 15%percent1515\% in this paper, the realised return of our strategy from day t𝑡t to t+1𝑡1t+1 is,

|  |  |  |  |
| --- | --- | --- | --- |
|  | Rt+1TSMOM=1N​∑i=1NRt+1(i),Rt+1(i)=Xt(i)​σtgtσt(i)​rt+1(i),formulae-sequencesuperscriptsubscript𝑅𝑡1TSMOM1𝑁superscriptsubscript𝑖1𝑁superscriptsubscript𝑅𝑡1𝑖superscriptsubscript𝑅𝑡1𝑖superscriptsubscript𝑋𝑡𝑖subscript𝜎tgtsuperscriptsubscript𝜎𝑡𝑖superscriptsubscript𝑟𝑡1𝑖R\_{t+1}^{\mathrm{TSMOM}}=\frac{1}{N}\sum\_{i=1}^{N}R\_{t+1}^{(i)},\quad R\_{t+1}^{(i)}=X\_{t}^{(i)}~{}\frac{\sigma\_{\mathrm{tgt}}}{\sigma\_{t}^{(i)}}~{}r\_{t+1}^{(i)}, |  | (11) |

where Xtsubscript𝑋𝑡X\_{t} is our position size, N𝑁N the number of assets in our portfolio and σt(i)superscriptsubscript𝜎𝑡𝑖\sigma\_{t}^{(i)} the ex-ante volatility estimate of the i𝑖i-th asset. We compute σt(i)superscriptsubscript𝜎𝑡𝑖\sigma\_{t}^{(i)} using a 60-day exponentially weighted moving standard deviation.

The simplest trading strategy, for which we benchmark performance is Long Only, where we always select the maximum position Xt(i)=1subscriptsuperscript𝑋𝑖𝑡1X^{(i)}\_{t}=1. The original paper on time-series momentum [[2](#bib.bib2)], which we will refer to as Moskowitz, selects position as Xt(i)=sgn​(rt−252,t)subscriptsuperscript𝑋𝑖𝑡sgnsubscript𝑟

𝑡252𝑡X^{(i)}\_{t}=\mathrm{sgn}(r\_{t-252,t}), where we are using the volatility scaling framework and rt−252,tsubscript𝑟

𝑡252𝑡r\_{t-252,t} is annual return. In attempt to react quicker to momentum turning points, [[21](#bib.bib21)] blends a slow signal based on annual returns and a fast signal based on monthly returns, to give and Intermediate strategy,

|  |  |  |  |
| --- | --- | --- | --- |
|  | Xt=(1−w)​sgn​(rt−252,t)+w​sgn​(rt−21,t).subscript𝑋𝑡1𝑤sgnsubscript𝑟  𝑡252𝑡𝑤sgnsubscript𝑟  𝑡21𝑡X\_{t}=(1-w)\,\text{sgn}(r\_{t-252,t})+w\,\text{sgn}(r\_{t-21,t}). |  | (12) |

We control the relative contribution of the fast and slow signal via w∈[0,1]𝑤01w\in[0,1], with the case w=0𝑤0w=0 corresponding to the Moskowitz strategy. We additionally use MACD [[5](#bib.bib5)] as a benchmark, and for details of the implementation we invite the reader to see [[1](#bib.bib1)].

### III-B Deep Learning

We adopt a number of key choices which lead to the improved performance of DMNs.

#### LSTM Architecture

Of the deep-learning architectures assessed in [[1](#bib.bib1)], the Long Short-Term Memory (LSTM) [[11](#bib.bib11)] architecture yields the best results. LSTM is a special kind of Recurent Neural Network (RNN) [[40](#bib.bib40)], initially proposed to address the vanishing and exploding gradient problem [[41](#bib.bib41)]. An RNN takes an input sequence and, through the use of a looping mechanism where information can flow from one step to another, can be used to transform this into an output sequence while taking into account contextual information in a flexible way. An LSTM operates with cells, which store both short-term memory and long-term memories, using gating mechanisms to summarise and filter information. Internal memory states are sequentially updated with new observations at each step. The resulting model has fewer trainable parameters, is able to learn representations of long-term relationships and typically achieves better generalisation results.

#### Trading Signal and Position Sizing

Trading signals are learnt directly by DMNs, removing the need to manually specify both the trend estimator and maps this into a position. The output of the LSTM is followed by a time distributed, fully-connected layer with a activation function tanh⁡(⋅)⋅\tanh(\cdot), which is a squashing function that directly outputs positions Xt(i)∈(−1,1)subscriptsuperscript𝑋𝑖𝑡11X^{(i)}\_{t}\in(-1,1). The advantage of this approach is that we learn trading rules and positions sizing directly from the data itself. Once our hyperparameters θ𝜃\theta have been trained via backpropagation [[42](#bib.bib42)], our LSTM architecture g​(⋅;θ)𝑔

⋅𝜃g(\cdot;\theta) takes input features uT−τ+1:T(i)subscriptsuperscriptu𝑖:𝑇𝜏1𝑇\textbf{u}^{(i)}\_{T-\tau+1:T} for all timesteps in the LSTM looking back from time T𝑇T with τ𝜏\tau steps, and directly outputs a sequence of positions,

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝐗T−τ+1:T(i)=g​(𝐮T−τ+1:T(i);θ).subscriptsuperscript𝐗𝑖:𝑇𝜏1𝑇𝑔  subscriptsuperscript𝐮𝑖:𝑇𝜏1𝑇𝜃\mathbf{X}^{(i)}\_{T-\tau+1:T}=g(\mathbf{u}^{(i)}\_{T-\tau+1:T};\theta). |  | (13) |

In an online prediction setting, only the final position in the sequence XT(i)subscriptsuperscript𝑋𝑖𝑇X^{(i)}\_{T} is of relevance to our strategy.

#### Loss Function

It has been observed [[43](#bib.bib43)], that correctly predicting the direction of a stock moves, does not translate directly into a positive strategy return, since the driving moves can often be large but infrequent. Furthermore, we want to account for trade-offs between risk and reward, hence we explicitly optimise networks for risk-adjusted performance metrics. One such metric, used by DMNs is the Sharpe ratio [[33](#bib.bib33)], which calculates the return per unit of volatility. Our Sharpe loss function is,

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℒsharpe​(𝜽)=−252​𝔼Ω​[Rt(i)]VarΩ​[Rt(i)],subscriptℒsharpe𝜽252subscript𝔼Ωdelimited-[]superscriptsubscript𝑅𝑡𝑖subscriptVarΩdelimited-[]superscriptsubscript𝑅𝑡𝑖\mathcal{L}\_{\mathrm{sharpe}}(\boldsymbol{\theta})=-\frac{\sqrt{252}\,\mathbb{E}\_{\Omega}\left[R\_{t}^{(i)}\right]}{\sqrt{\mathrm{Var}\_{\Omega}\left[R\_{t}^{(i)}\right]}}, |  | (14) |

where ΩΩ\Omega is the set of all asset-time pairs {(i,t)|i∈{1,2,…​N},t∈{T−τ+1,…,T}}conditional-set𝑖𝑡formulae-sequence𝑖12…𝑁𝑡𝑇𝜏1…𝑇\{(i,t)|i\in\{1,2,\ldots N\},t\in\{T-\tau+1,\ldots,T\}\}. Automatic differentiation is used to compute gradients for backpropagation [[40](#bib.bib40)], which explicitly optimises networks for our chosen performance metric.

#### Model Inputs

For each timestep, our model can benefit from inputting signals from various timescales. We normalise returns to be rt−t′,t(i)/σt(i)​t′subscriptsuperscript𝑟𝑖

𝑡superscript𝑡′𝑡superscriptsubscript𝜎𝑡𝑖superscript𝑡′r^{(i)}\_{t-t^{\prime},t}/\sigma\_{t}^{(i)}\sqrt{t^{\prime}}, given a time offset of t′superscript𝑡′t^{\prime} days. We use offsets t′∈{1,21,63,126,256}superscript𝑡′12163126256t^{\prime}\in\{1,21,63,126,256\}, corresponding to daily, monthly, quarterly, biannual and annual returns. We also encode additional information by inputting MACD indicators [[5](#bib.bib5)]. MACD is a volatility normalised moving average convergence divergence signal, defining the relationship between a short and long signal. For implementation details, please refer to [[1](#bib.bib1)]. We use pairs in {(8,24),(16,28),(32,96)}82416283296\{(8,24),(16,28),(32,96)\}. We can think of these indicators preforming a similar function to a convolutional layer.

## IV Trading Strategy

### IV-A Strategy Definition

As we are using a data-driven approach, we split our training data as a first step, setting aside the first 90% for training and the last 10% for validation, for each asset. We calibrate our model using the training data by optimising on the Sharpe loss function ([14](#S3.E14 "In Loss Function ‣ III-B Deep Learning ‣ III Momentum Strategies Review ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection")) via minibatch Stochastic Gradient Descent (SGD), using the Adam [[44](#bib.bib44)] optimiser. We observe validation loss after each epoch, which is a full pass of the data, to determine convergence. We also use the validation set for the outer optimisation loop, where we tune our model hyperparameters. The hyperparameter optimisation process is detailed in Appendix [-B](#A0.SS2 "-B Experiment Details ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection"). It is necessary to precompute the CPD location γt(i)subscriptsuperscript𝛾𝑖𝑡\gamma^{(i)}\_{t} and severity νt(i)subscriptsuperscript𝜈𝑖𝑡\nu^{(i)}\_{t} parameters as detailed by ([10](#S2.E10 "In II Changepoint Detection Using Gaussian Processes ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection")). We do this for each times-asset pair in our training and validation set. It is necessary to do this for a chosen l∈{10,21,63,126,252}𝑙102163126252l\in\{10,21,63,126,252\}, corresponding to two weeks, a month, a quarter, half a year and a full year. We selected these LBW sizes to correspond to input returns timescales, with the exception of the 10 day LBW, which was selected to be as close to daily returns data as reasonably possible. We reinitialise our Matérn 3/2 kernel for each timestep, with all hyperparameters set to 111. This approach was found to be more stable than borrowing parameters from the previous timestep. For our Changepoint kernel, we initialise the hyperparameters as c=t−l2𝑐𝑡𝑙2c=t-\frac{l}{2} and s=1𝑠1s=1. All other parameters are initialised as the equivalent parameter from fitting the Matérn 3/2 kernel, initialising kξ1subscript𝑘subscript𝜉1k\_{\xi\_{1}} and kξ2subscript𝑘subscript𝜉2k\_{\xi\_{2}} with the same values. In the rare case this process fails, we try again by reinitialising all Changepoint kernel parameters to 111, with the exception of setting c=t−l2𝑐𝑡𝑙2c=t-\frac{l}{2}. In the event the module still fails for a given timestep, we fill the outputs νt(i)subscriptsuperscript𝜈𝑖𝑡\nu^{(i)}\_{t} and γt(i)subscriptsuperscript𝛾𝑖𝑡\gamma^{(i)}\_{t} using the outputs from the previous timestep, noting that we need to increment the changepoint location by an additional step.

For each LSTM input, we pass in the normalised returns from the different timescales, our MACD indicators, alongside CPD severity and location, for a chosen l𝑙l. We can either fix l𝑙l for our strategy or introduce it as a structural hyperparameter, which is tuned by the outer optimisation loop. By doing this, we have information exchange from our CPD Module all the way through to our Sharpe ratio loss function and traded positions. Once our model has been fully trained, we can run it online by computing the CPD module for the most recent data points, then using our LSTM module to select positions to hold for the next day, for each asset.

### IV-B Experiments via Back-testing

For all of our experiments, we used a portfolio of 50, liquid, continuous futures contracts over the period 1990–2020. The combination of commodities, equities, fixed income and FX futures were selected to make up a well balanced portfolio. The data was extracted from the Pinnacle Data Corp CLC database [[45](#bib.bib45)], and the selected futures contracts are listed in Appendix [-A](#A0.SS1 "-A Dataset Details ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection"). All of the selected assets have less than 10% of data missing.

In order to back-test our model, we use an expanding window approach, where we start by using 1990–1995 for training/validation, then test out-of-sample on the period 1995–2000. With each successive iteration, we expand the training/validation window by an additional five years, preform the hyperparameter optimisation again, and test on the subsequent five year period. Data was not available from 1990 for every asset and we only use an asset if there is enough data available in the validation set for one at least one LSTM sequence. All of our results are recorded as an average of the test windows. We test our LSTM with CPD strategy using a LBW l∈{10,21,63,126,252}𝑙102163126252l\in\{10,21,63,126,252\}, then with the optimised l𝑙l for each window, based on validation loss.

![Refer to caption](/html/2105.13727/assets/Images/CPD-window-size.png)

We benchmark our strategy against those discussed in Section [III](#S3 "III Momentum Strategies Review ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection"), where we choose w∈{0,0.5,1}𝑤00.51w\in\{0,0.5,1\} for the Intermediate strategy. We also compare our strategy to a DMN which does not have the CPD module. To maintain consistency with the previous work from [[1](#bib.bib1)] we benchmark strategy,

profitability through annualised returns and percentage of positive captured returns,

risk through annualised volatility, annualised downside deviation and maximum drawdown (MDD), and

risk adjusted performance through annualised Sharpe, Sortino and Calmar Ratios.

We provide results for both the raw signal output and then with an additional layer of volatility rescaling to the target of 15%, for ease of comparison between strategies. It should be noted that this paper selects a more realistic 50 asset portfolio instead of the full 88 assets previously selected in [[1](#bib.bib1)]. We focus on raw predictive power of the model and do not account for transaction costs at this stage; however this is a simple adjustment and can easily be incorporated into the loss function. We have included some details and analysis of transaction costs in Appendix [-C](#A0.SS3 "-C Transaction costs ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection"). For further information on the implementation and the effects of transaction costs, please refer to [[1](#bib.bib1)].

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | Returns | Vol. | Sharpe | |  | | --- | | Downside | | Deviation | | Sortino | MDD | Calmar | |  | | --- | | % of ++ve | | Returns | | Ave. PAve. LAve. PAve. L\mathbf{\frac{\text{Ave. P}}{\text{Ave. L}}} |
| \ulReference |  |  |  |  |  |  |  |  |  |
| Long Only | 2.30% | 5.22% | 0.44 | 3.59% | 0.64 | 3.12% | 0.79 | 52.45% | 0.975 |
| MACD | 2.65% | 3.58% | 0.77 | 2.57% | 1.09 | 2.56% | 0.95 | 53.34% | 1.002 |
| \ulTSMOM |  |  |  |  |  |  |  |  |  |
| w=0𝑤0w=0 | 4.41% | 4.80% | 0.94 | 3.44% | 1.32 | 3.22% | 1.35 | 54.28% | 0.990 |
| w=0.5𝑤0.5w=0.5 | 3.29% | 3.78% | 0.89 | 2.80% | 1.23 | 2.70% | 1.16 | 53.88% | 0.998 |
| w=1𝑤1w=1 | 2.17% | 4.71% | 0.48 | 3.29% | 0.68 | 3.24% | 0.67 | 51.48% | 1.026 |
| \ulLSTM | 3.53% | 2.52% | 1.62 | 1.71% | 2.46 | 1.72% | 2.79 | 55.23% | 1.075 |
| \ulLSTM w/ CPD |  |  |  |  |  |  |  |  |  |
| 10-day LBW | 3.04% | 1.57% | 1.77 | 1.07% | 2.74 | 1.09% | 2.78 | 55.50% | 1.096 |
| 21-day LBW | 3.68% | 1.81% | 2.04 | 1.21% | 3.07 | 1.08% | 3.75 | 56.43% | 1.095 |
| 63-day LBW | 3.51% | 1.72% | 2.08 | 1.10% | 3.27 | 1.06% | 3.58 | 55.61% | 1.140 |
| 126-day LBW | 3.37% | 2.28% | 1.75 | 1.59% | 2.66 | 1.52% | 2.88 | 54.95% | 1.117 |
| 252-day LBW | 2.81% | 2.24% | 1.45 | 1.57% | 2.19 | 1.54% | 2.32 | 54.00% | 1.101 |
| LBW Optimised | 3.64% | 1.73% | 2.16 | 1.17% | 3.33 | 1.14% | 3.50 | 56.22% | 1.133 |

|  |
| --- |
| Downside |
| Deviation |

|  |
| --- |
| % of ++ve |
| Returns |

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | Returns | Vol. | Sharpe | |  | | --- | | Downside | | Deviation | | Sortino | MDD | Calmar | |  | | --- | | % of ++ve | | Returns | | Ave. PAve. LAve. PAve. L\mathbf{\frac{\text{Ave. P}}{\text{Ave. L}}} |
| \ulReference |  |  |  |  |  |  |  |  |  |
| Long Only | 6.62% | 15.00% | 0.44 | 10.32% | 0.64 | 8.96% | 0.79 | 52.45% | 0.975 |
| MACD | 11.08% | 15.00% | 0.77 | 10.74% | 1.09 | 10.72% | 0.95 | 53.34% | 1.002 |
| \ulTSMOM |  |  |  |  |  |  |  |  |  |
| w=0𝑤0w=0 | 13.79% | 15.00% | 0.94 | 10.74% | 1.32 | 10.05% | 1.35 | 54.28% | 0.990 |
| w=0.5𝑤0.5w=0.5 | 13.06% | 15.00% | 0.89 | 11.10% | 1.23 | 10.72% | 1.16 | 53.88% | 0.998 |
| w=1𝑤1w=1 | 6.89% | 15.00% | 0.48 | 10.46% | 0.68 | 10.32% | 0.67 | 51.48% | 1.026 |
| \ulLSTM | 21.03% | 15.00% | 1.62 | 10.15% | 2.46 | 10.24% | 2.79 | 55.23% | 1.075 |
| \ulLSTM w/ CPD |  |  |  |  |  |  |  |  |  |
| 10-day LBW | 29.01% | 15.00% | 1.77 | 10.18% | 2.74 | 10.39% | 2.78 | 55.50% | 1.096 |
| 21-day LBW | 30.57% | 15.00% | 2.04 | 10.06% | 3.07 | 9.01% | 3.75 | 56.43% | 1.095 |
| 63-day LBW | 30.71% | 15.00% | 2.08 | 9.65% | 3.27 | 9.22% | 3.58 | 55.61% | 1.140 |
| 126-day LBW | 22.16% | 15.00% | 1.75 | 10.44% | 2.66 | 9.99% | 2.88 | 54.95% | 1.117 |
| 252-day LBW | 18.82% | 15.00% | 1.45 | 10.54% | 2.19 | 10.32% | 2.32 | 54.00% | 1.101 |
| LBW Optimised | 31.52% | 15.00% | 2.16 | 10.10% | 3.33 | 9.88% | 3.50 | 56.22% | 1.133 |

|  |
| --- |
| Downside |
| Deviation |

|  |
| --- |
| % of ++ve |
| Returns |

### IV-C Results and Discussion

Our aggregated out-of-sample prediction results, averaged across all five-year windows from 1995–2020, are recorded in Exhibit [4](#S4.T4 "TABLE 4 ‣ IV-B Experiments via Back-testing ‣ IV Trading Strategy ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection") and again in Exhibit [4](#S4.T4 "TABLE 4 ‣ IV-B Experiments via Back-testing ‣ IV Trading Strategy ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection") using volatility rescaling. We plot the effect of CPD LBW size on average Sharpe ratio in Exhibit [2](#S4.F2 "Figure 2 ‣ IV-B Experiments via Back-testing ‣ IV Trading Strategy ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection") and demonstrate how optimising on this as a hyperparameter can improve overall performance. We note that the CPD computation becomes more intensive for l∈{126,252}𝑙126252l\in\{126,252\}, however we find that performance gains diminish by this point and l=252𝑙252l=252 especially provides no benefit. Impressively, due to our GP framework for CPD, we are able to achieve superior results with very small LBWs, with a notable performance boost from only a two week LBW and performance almost maxes out after only one month.

Another idea involved passing in outputs from multiple CPD modules with different LBWs in parallel, as inputs to the LSTM. This was not found to improve the model and actually resulted in a degraded performance. It is proposed that multiple LBWs could be useful if using a more complex deep learning architecture than LSTM.

![Refer to caption](/html/2105.13727/assets/Images/FTSE-GBP-fast-slow.png)
![Refer to caption](/html/2105.13727/assets/Images/cumulative-returns-benchmark.png)

In Exhibit [5](#S4.F5 "Figure 5 ‣ IV-C Results and Discussion ‣ IV Trading Strategy ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection") we observe how we have slow momentum and fast reversion strategies happening simultaneously. By introducing CPD, we are able to achieve superior returns because we are better able to learn the timing of these strategies and when to place more emphasis on one of these, using a data-driven approach. In our results we can see the difficulties of trying to address regime change with handcrafted techniques such as the Intermediate w=0.5𝑤0.5w=0.5, which in our experiments actually fails to outperform the w=0𝑤0w=0 Moskowitz strategy on all risk adjusted performance ratios.

Our results demonstrate that via the introduction of the CPD module, we outperform the standard DMN in every single performance metric. Our model correctly classifies the direction of the return more often and in addition has a higher average profit to loss ratio. We can see that the CPD module helps to reduce the risk, reducing volatility, downside deviation and MDD, whilst still achieving slightly higher raw returns. This translates to an improvement in risk adjusted performance, improving Sortino ratio by 35% and Calmar ratio by 25%. These metrics suggest that the CPD module makes our model more robust to market crashes. We observe an improvement of Sharpe ratio, our target metric, of 33% which translates to an improvement of 130% when comparing to the best performing TSMOM strategy. We plot the raw and rescaled signals to benchmark strategies in Exhibit [6](#S4.F6 "Figure 6 ‣ IV-C Results and Discussion ‣ IV Trading Strategy ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection"). We note that up until about 2003, when the uptake of electronic trading was becoming much more widespread, the traditional TSMOM and MACD strategies are comparable to the results achieved via the LSTM DMN architecture. At this point the LSTM starts to significantly outperform these traditional strategies, until more recent years where we see volatility increase and performance, especially risk-adjusted performance, drop significantly. This drop in performance can be largely attributed to increased market nonstationarity. Impressively, with the addition of the CPD module, our DMN pipeline continues to perform well even during the market nonstationarity of the 2015–2020 period. Using five repeated trials of the entire experiment, with and without CPD, the average improvement for Sharpe ratio in this period is 70%, for LBW l=21𝑙21l=21.

## V Conclusions

We have demonstrated that the introduction of an online changepoint detection (CPD) module is a simple, yet effective, way to significantly improve model performance, specifically Deep Momentum Networks (DMNs). Our model is able blend different strategies at different timescales, learning to do so in a data-driven manner, directly based on our desired risk-adjusted performance metric. In periods of stability, our model is able to achieve superior returns by focusing on slow momentum whilst exploiting but not overreacting to local mean-reversion. The impressive performance increase in periods of nonstationarity, such as recent years, can be attributed to the fact that we 1) can effectively incorporate CPD online with a very short lookback window due to the fact we do so using Gaussian Processes, and 2) pass changepoint score νt(i)superscriptsubscript𝜈𝑡𝑖\nu\_{t}^{(i)} from our CPD module to the DMN, helping our model learn how to respond to varying degrees of disequilibrium. As a result, we enhance performance in such conditions where we observe a more conservative slow momentum strategy with a focus on fast mean-reversion.

Future work includes incorporating a CPD module into other deep learning architectures or performing CPD on a model representation as opposed to model inputs. The work in this paper has natural parallels to the field of Continual Learning (CL), which is a paradigm whereby an agent sequentially learns new tasks. Another direction of work will involve utilising CL for momentum trading, where CPD is used to determine task boundaries.

## VI Acknowledgements

We would like to thank the Oxford-Man Institute of Quantitative Finance for financial and computing support.

## References

### -A Dataset Details

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| Identifier | Description | |  | | --- | | Back-test | | From | |
| \ulCommodities |  |  |
| CC | COCOA | 1995 |
| DA | MILK III, composite | 2000 |
| GI | GOLDMAN SAKS C. I. | 1995 |
| JO | ORANGE JUICE | 1995 |
| KC | COFFEE | 1995 |
| KW | WHEAT, KC | 1995 |
| LB | LUMBER | 1995 |
| NR | ROUGH RICE | 1995 |
| SB | SUGAR #11 | 1995 |
| ZA | PALLADIUM, electronic | 1995 |
| ZC | CORN, electronic | 1995 |
| ZF | FEEDER CATTLE, electronic | 1995 |
| ZG | GOLD, electronic | 1995 |
| ZH | HEATING OIL, electronic | 1995 |
| ZI | SILVER, electronic | 1995 |
| ZK | COPPER, electronic | 1995 |
| ZL | SOYBEAN OIL, electronic | 1995 |
| ZN | NATURAL GAS, electronic | 1995 |
| ZO | OATS, electronic | 1995 |
| ZP | PLATINUM, electronic | 1995 |
| ZR | ROUGH RICE, electronic | 1995 |
| ZT | LIVE CATTLE, electronic | 1995 |
| ZU | CRUDE OIL, electronic | 1995 |
| ZW | WHEAT, electronic | 1995 |
| ZZ | LEAN HOGS, electronic | 1995 |
| \ulEquities |  |  |
| CA | CAC40 INDEX | 2000 |
| EN | NASDAQ, MINI | 2005 |
| ER | RUSSELL 2000, MINI | 2005 |
| ES | S & P 500, MINI | 2000 |
| LX | FTSE 100 INDEX | 1995 |
| MD | S&P 400 (Mini electronic) | 1995 |
| SC | S & P 500, composite | 2000 |
| SP | S & P 500, day session | 1995 |
| XU | DOW JONES EUROSTOXX50 | 2005 |
| XX | DOW JONES STOXX 50 | 2005 |
| YM | Mini Dow Jones ($5.00) | 2005 |
| \ulFixed Income |  |  |
| DT | EURO BOND (BUND) | 1995 |
| FB | T-NOTE, 5yr composite | 1995 |
| TY | T-NOTE, 10yr composite | 1995 |
| UB | EURO BOBL | 2005 |
| US | T-BONDS, composite | 1995 |
| \ulFX |  |  |
| AN | AUSTRALIAN $$, composite | 1995 |
| BN | BRITISH POUND, composite | 1995 |
| CN | CANADIAN $$, composite | 1995 |
| DX | US DOLLAR INDEX | 1995 |
| FN | EURO, composite | 1995 |
| JN | JAPANESE YEN, composite | 1995 |
| MP | MEXICAN PESO | 2000 |
| NK | NIKKEI INDEX | 1995 |
| SN | SWISS FRANC, composite | 1995 |

|  |
| --- |
| Back-test |
| From |

### -B Experiment Details

We split our data into training and validation datasets using a 90%, 10% split. We winsorise our data by limiting it to be within 5 times its exponentially weighted moving (EWM) standard deviations from its EWM average, using a 252-day half life. We calibrate our model using the training data by optimising on the Sharpe loss function via minibatch Stochastic Gradient Descent (SGD), using the Adam [[44](#bib.bib44)] optimiser. We limit our training to 300 epochs, with an early stopping patience of 25 epochs, meaning training is terminated if there is no decrease in validation loss during this time period. The model is implemented via the Keras API in TensorFlow. Our LSTM sequence length was set to 63 for all experiments. For training and validation, in attempt to prevent overfitting, we split our data into non-overlapping sequences, rather than using a sliding window approach. A stateless LSTM is used, meaning the last state from the previous batch is not used as the initial state for the subsequent batch. Keeping the order of each individual sequence in tact, we shuffle the order which each sequence appears in an epoch. We employ dropout regularisation [[46](#bib.bib46)] as another technique to avoid overfitting, applying it to LSTM inputs and outputs.

We tune our hyperparameters, with options listed in Exhibit [7](#A0.T7 "TABLE 7 ‣ -B Experiment Details ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection"), using an outer optimisation loop. We achieve this via 50 iterations of random grid search to identify the optimal model. We perform the full experiment for each choice of CPD LBW length and then use the model which achieved the lowest validation loss for the optimised CPD model.

|  |  |
| --- | --- |
| Hyperparameters | Random Search Grid |
| Dropout Rate | 0.1, 0.2, 0.3, 0.4, 0.5 |
| Hidden Layer Size | 5, 10, 20, 40, 80, 160 |
| Minibatch Size | 64, 128, 256 |
| Learning Rate | 10−4,10−3,10−2,10−1  superscript104superscript103superscript102superscript10110^{-4},~{}10^{-3},~{}10^{-2},~{}10^{-1} |
| Max Gradient Norm | 10−2,100,102  superscript102superscript100superscript10210^{-2},~{}10^{0},~{}10^{2} |
| ∗CPD LBW Length | 10, 21, 63, 126, 252 |

∗\,\,{}^{\*}CPD LBW length can be either a hyperparameter or fixed.

### -C Transaction costs

![Refer to caption](/html/2105.13727/assets/Images/transaction-cost.png)

Assuming an average transaction cost of C𝐶C, we calculate turnover adjusted returns as,

|  |  |  |  |
| --- | --- | --- | --- |
|  | R¯t+1(i)=Rt+1(i)+−Cσtgt|Xt(i)σt(i)−Xt−1(i)σt−1(i)|\bar{R}\_{t+1}^{(i)}=R\_{t+1}^{(i)}+-C\sigma\_{\mathrm{tgt}}\left|\frac{X\_{t}^{(i)}}{\sigma\_{t}^{(i)}}-\frac{X\_{t-1}^{(i)}}{\sigma\_{t-1}^{(i)}}\right| |  | (15) |

In Exhibit [8](#A0.F8 "Figure 8 ‣ -C Transaction costs ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection") we demonstrate the effects of transaction cost on our raw signal. Our strategy outperforms classical strategies for transaction costs of up to 2 basis points, at which point it rapidly deteriorates, due to the fast reverting component. We note that the a larger CPD LBW window size becomes favourable as we increase C𝐶C. We suspect this is because the model focuses on larger long term changepoints and favours slow momentum over fast reversion. For larger average transaction costs greater than 1bps we suggest incorporating turnover adjusted returns into the loss function ([14](#S3.E14 "In Loss Function ‣ III-B Deep Learning ‣ III Momentum Strategies Review ‣ Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection")). This adjustment is detailed in [[1](#bib.bib1)], where it is demonstrated to work well when transaction costs are high.

![ar5iv homepage](/assets/ar5iv.png)
![Mascot Sammy](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)
