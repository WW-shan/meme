# Conformal Predictive Portfolio Selection

###### Abstract

This study explores portfolio selection using predictive models for portfolio returns. Portfolio selection is a fundamental task in finance, and various methods have been developed to achieve this goal. For example, the mean-variance approach constructs portfolios by balancing the trade-off between the mean and variance of asset returns, while the quantile-based approach optimizes portfolios by accounting for tail risk. These traditional methods often rely on distributional information estimated from historical data. However, a key concern is the uncertainty of future portfolio returns, which may not be fully captured by simple reliance on historical data, such as using the sample average. To address this, we propose a framework for predictive portfolio selection using conformal inference, called *Conformal Predictive Portfolio Selection* (CPPS). Our approach predicts future portfolio returns, computes corresponding prediction intervals, and selects the desirable portfolio based on these intervals. The framework is flexible and can accommodate a variety of predictive models, including autoregressive (AR) models, random forests, and neural networks. We demonstrate the effectiveness of our CPPS framework using an AR model and validate its performance through empirical studies, showing that it provides superior returns compared to simpler strategies.

## 1 Introduction

Portfolio selection is a fundamental problem in finance, and numerous approaches have been developed to help investors select desirable portfolios. A key aspect of constructing better portfolios is utilizing estimated distributional information of future asset returns. In this study, given predictive models, including conventional autoregressive (AR) models and modern machine learning methods, we aim to develop a general framework for portfolio selection based on prediction intervals obtained through conformal inference.

One of the primary approaches in portfolio selection is Markowitz’s mean-variance portfolio theory, which optimizes portfolios by balancing the trade-off between the mean and variance of asset returns (Markowitz, [1952](https://arxiv.org/html/2410.16333v1#bib.bib10), [1959](https://arxiv.org/html/2410.16333v1#bib.bib11); Markowitz & Todd, [2000](https://arxiv.org/html/2410.16333v1#bib.bib12)). Although widely adopted, the mean-variance approach has been criticized for its use of variance as a risk measure. Specifically, variance increases with returns, despite higher returns generally being desirable for investors. Additionally, variance considers the entire distribution of returns, including outcomes that may not reflect true risk from the investor’s perspective. In response to these critiques, quantile-based approaches have gained traction. For instance, Rockafellar & Uryasev ([2000](https://arxiv.org/html/2410.16333v1#bib.bib13)) propose minimizing Conditional Value at Risk (CVaR) through linear programming, while Bodnar et al. ([2021](https://arxiv.org/html/2410.16333v1#bib.bib3)) introduce a different quantile-based portfolio selection method that incorporates quantiles of both returns and risks.

Despite the introduction of various methods that utilize distributional information, there remains a common challenge: relying solely on historical data may not yield effective prediction. For example, the historical sample mean can be a poor predictor of future asset returns. As the ultimate goal is to optimize future returns, we may need to utilize predictive models including AR models and machine learning methods. In fact, recent studies have employed machine learning models to predict asset returns, including stocks, currencies, and real estate. However, both AR models and machine learning models often introduce challenges in assessing prediction uncertainty. In traditional methods such as linear regression models, confidence intervals are more easily computed in low-dimensional regression models. In contrast, machine learning models typically involve high-dimensional parameters, making the application of classical statistical inference more difficult. Additionally, under dependent data, obtaining prediction interval is difficult without making strong assumptions on the error term in the regression model, such as normality.

This challenge of uncertainty evaluation is particularly pressing in finance. Conformal inference addresses this issue by providing valid prediction intervals without relying on specific model assumptions (Vovk et al., [2005](https://arxiv.org/html/2410.16333v1#bib.bib15); Chernozhukov et al., [2018](https://arxiv.org/html/2410.16333v1#bib.bib5)). For this model-free property, we consider that conformal inference is an attractive option for uncertainty evaluation in portfolio selection.

Building on this body of work, we develop a portfolio selection framework that uses prediction intervals. In our framework, the objective is based on the confidence intervals of future asset returns generated by machine learning models and conformal inference. Our framework provides a model-free, prediction-interval-based framework for portfolio selection, allowing for flexible definition of objective functions without requiring a predefined structure.

As an example, given a certain error level, we select a portfolio with the highest predicted return from a confidence interval, ensuring that the lowest return in the set is sufficiently high under the given error threshold. In this process, we predict future returns for each portfolio candidate, compute prediction intervals using conformal inference, and then select portfolios based on their predicted returns at a specified error rate. This approach is proposed for improving the worst-case performance of our portfolio.

Important related work includes research on portfolio selection within a Bayesian framework, which allows for the measurement of future asset return uncertainty (Barry, [1974](https://arxiv.org/html/2410.16333v1#bib.bib1); Brown, [1976](https://arxiv.org/html/2410.16333v1#bib.bib4); Winkler & Barry, [1975](https://arxiv.org/html/2410.16333v1#bib.bib16)). The Bayesian approach has been applied to mean-variance portfolio by David Bauder & Schmid ([2021](https://arxiv.org/html/2410.16333v1#bib.bib6)) and to quantile-based portfolio by Bodnar et al. ([2020](https://arxiv.org/html/2410.16333v1#bib.bib2)). Recent studies, such as Tallman & West ([2023](https://arxiv.org/html/2410.16333v1#bib.bib14)) and Kato et al. ([2024](https://arxiv.org/html/2410.16333v1#bib.bib9)); Kato ([2024](https://arxiv.org/html/2410.16333v1#bib.bib8)), explore Bayesian ensemble methods for portfolio selection.

## 2 Problem Setting

Let T,K≥2

𝑇𝐾
2T,K\geq 2italic\_T , italic\_K ≥ 2 be positive integers. Consider a time series with T+1𝑇1T+1italic\_T + 1 periods denoted by 1,2,…,T,T+1

12…𝑇𝑇11,2,\dots,T,T+11 , 2 , … , italic\_T , italic\_T + 1. There are K𝐾Kitalic\_K financial assets, and each asset a∈[K]≔{1,2,…,K}𝑎delimited-[]𝐾≔12…𝐾a\in[K]\coloneqq\{1,2,\dots,K\}italic\_a ∈ [ italic\_K ] ≔ { 1 , 2 , … , italic\_K } yields a return Ya,tsubscript𝑌

𝑎𝑡Y\_{a,t}italic\_Y start\_POSTSUBSCRIPT italic\_a , italic\_t end\_POSTSUBSCRIPT in each period t∈[T+1]𝑡delimited-[]𝑇1t\in[T+1]italic\_t ∈ [ italic\_T + 1 ]. Additionally, for each period t∈[T+1]𝑡delimited-[]𝑇1t\in[T+1]italic\_t ∈ [ italic\_T + 1 ], there exists a d𝑑ditalic\_d-dimensional feature vector Xa,t∈𝒳⊆ℝdsubscript𝑋

𝑎𝑡𝒳superscriptℝ𝑑X\_{a,t}\in\mathcal{X}\subseteq\mathbb{R}^{d}italic\_X start\_POSTSUBSCRIPT italic\_a , italic\_t end\_POSTSUBSCRIPT ∈ caligraphic\_X ⊆ blackboard\_R start\_POSTSUPERSCRIPT italic\_d end\_POSTSUPERSCRIPT, where 𝒳𝒳\mathcal{X}caligraphic\_X is a space of feature vectors. These feature vectors are used to predict future asset returns or portfolio returns. The feature vector Xtsubscript𝑋𝑡X\_{t}italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT can include both endogenously given variables and historical target variables observed up to that period, such as Y1,Y2,…,Yt−1

subscript𝑌1subscript𝑌2…subscript𝑌𝑡1Y\_{1},Y\_{2},\dots,Y\_{t-1}italic\_Y start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_Y start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT , … , italic\_Y start\_POSTSUBSCRIPT italic\_t - 1 end\_POSTSUBSCRIPT.

The goal of this study is to select a desirable portfolio in period T+1𝑇1T+1italic\_T + 1. We assume that the dataset {(Yt,Xt)}t=1Tsuperscriptsubscriptsubscript𝑌𝑡subscript𝑋𝑡𝑡1𝑇\{(Y\_{t},X\_{t})\}\_{t=1}^{T}{ ( italic\_Y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT and feature vector XT+1subscript𝑋𝑇1X\_{T+1}italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT is observable in period T+1𝑇1T+1italic\_T + 1. In period T+1𝑇1T+1italic\_T + 1, given this dataset and the feature vector XT+1subscript𝑋𝑇1X\_{T+1}italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT, we aim to select a portfolio 𝒘T+1∈𝒲≔{𝒘≔{wa}a∈[K]∈[0,1]K∣∑a∈[K]wa=1}subscript𝒘𝑇1𝒲≔conditional-set≔𝒘subscriptsubscript𝑤𝑎𝑎delimited-[]𝐾superscript01𝐾subscript𝑎delimited-[]𝐾subscript𝑤𝑎1\bm{w}\_{T+1}\in\mathcal{W}\coloneqq\{\bm{w}\coloneqq\{w\_{a}\}\_{a\in[K]}\in[0,1%
]^{K}\mid\sum\_{a\in[K]}w\_{a}=1\}bold\_italic\_w start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ∈ caligraphic\_W ≔ { bold\_italic\_w ≔ { italic\_w start\_POSTSUBSCRIPT italic\_a end\_POSTSUBSCRIPT } start\_POSTSUBSCRIPT italic\_a ∈ [ italic\_K ] end\_POSTSUBSCRIPT ∈ [ 0 , 1 ] start\_POSTSUPERSCRIPT italic\_K end\_POSTSUPERSCRIPT ∣ ∑ start\_POSTSUBSCRIPT italic\_a ∈ [ italic\_K ] end\_POSTSUBSCRIPT italic\_w start\_POSTSUBSCRIPT italic\_a end\_POSTSUBSCRIPT = 1 }, which will yield a return RT+1⁢(𝒘T+1)subscript𝑅𝑇1subscript𝒘𝑇1R\_{T+1}(\bm{w}\_{T+1})italic\_R start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ( bold\_italic\_w start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) after the portfolio is selected. Our objective is to select a portfolio to satisfy some criterion.

In portfolio selection, investors typically account for both the uncertainty of asset returns and their risk preferences. Simply maximizing RT+1⁢(𝒘T+1)subscript𝑅𝑇1subscript𝒘𝑇1R\_{T+1}(\bm{w}\_{T+1})italic\_R start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ( bold\_italic\_w start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) may not be desirable. Well-known portfolio objectives include the mean-variance portfolio, risk-parity portfolio, and quantile-risk-based portfolio. In this study, we propose a method for constructing portfolios using prediction intervals.

### 2.1 Predictive Models

Our focus is on portfolio selection in period T+1𝑇1T+1italic\_T + 1, given {(Yt,Xt)}t=1Tsuperscriptsubscriptsubscript𝑌𝑡subscript𝑋𝑡𝑡1𝑇\{(Y\_{t},X\_{t})\}\_{t=1}^{T}{ ( italic\_Y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT and XT+1subscript𝑋𝑇1X\_{T+1}italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT. Since the portfolio return RT+1⁢(𝒘T+1)subscript𝑅𝑇1subscript𝒘𝑇1R\_{T+1}(\bm{w}\_{T+1})italic\_R start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ( bold\_italic\_w start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) is an unrealized and unobserved future value, we predict it using various predictive models.

We formalize the problem as follows. Given {(Yt,Xt)}t=1Tsuperscriptsubscriptsubscript𝑌𝑡subscript𝑋𝑡𝑡1𝑇\{(Y\_{t},X\_{t})\}\_{t=1}^{T}{ ( italic\_Y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT and XT+1subscript𝑋𝑇1X\_{T+1}italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT, for each 𝒘∈𝒲𝒘𝒲\bm{w}\in\mathcal{W}bold\_italic\_w ∈ caligraphic\_W, we predict the portfolio return RT+1⁢(𝒘T+1)subscript𝑅𝑇1subscript𝒘𝑇1R\_{T+1}(\bm{w}\_{T+1})italic\_R start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ( bold\_italic\_w start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) using models such as linear regression, random forests, and neural networks. We can train (or estimate) such predictive models using the given dataset {(Yt,Xt)}t=1Tsuperscriptsubscriptsubscript𝑌𝑡subscript𝑋𝑡𝑡1𝑇\{(Y\_{t},X\_{t})\}\_{t=1}^{T}{ ( italic\_Y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT and XT+1subscript𝑋𝑇1X\_{T+1}italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT. In time series analysis, standard methods include AR models and moving-average (MA) models (Hamilton, [1994](https://arxiv.org/html/2410.16333v1#bib.bib7)).

### 2.2 Conformal Inference of Portfolio Return

We construct portfolios based on the predictions generated by predictive models. To measure the uncertainty of these predictions, we employ conformal inference. Conformal inference is flexible, as it does not impose restrictions on the choice of predictive models, provided certain conditions, such as estimation error rates, are met.

Let α∈(0,1)𝛼01\alpha\in(0,1)italic\_α ∈ ( 0 , 1 ) be an error rate. Using conformal inference, given the dataset {(Yt,Xt)}t=1Tsuperscriptsubscriptsubscript𝑌𝑡subscript𝑋𝑡𝑡1𝑇\{(Y\_{t},X\_{t})\}\_{t=1}^{T}{ ( italic\_Y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT and a portfolio 𝒘∈𝒲𝒘𝒲\bm{w}\in\mathcal{W}bold\_italic\_w ∈ caligraphic\_W, we construct a prediction interval C^T𝒘⁢(XT+1)subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇1\widehat{C}^{\bm{w}}\_{T}(X\_{T+1})over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ), which satisfies

|  |  |  |
| --- | --- | --- |
|  | ℙ⁢(RT+1⁢(𝒘)∈C^T𝒘⁢(XT+1))≥1−α,ℙsubscript𝑅𝑇1𝒘subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇11𝛼\displaystyle\mathbb{P}\left(R\_{T+1}(\bm{w})\in\widehat{C}^{\bm{w}}\_{T}(X\_{T+1% })\right)\geq 1-\alpha,blackboard\_P ( italic\_R start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ( bold\_italic\_w ) ∈ over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) ) ≥ 1 - italic\_α , |  |

where the probability ℙℙ\mathbb{P}blackboard\_P is taken over {(Yt,Xt)}t=1T+1superscriptsubscriptsubscript𝑌𝑡subscript𝑋𝑡𝑡1𝑇1\{(Y\_{t},X\_{t})\}\_{t=1}^{T+1}{ ( italic\_Y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T + 1 end\_POSTSUPERSCRIPT.

## 3 Conformal Predictive Portfolio Selection

This study employs prediction intervals of future asset returns to guide portfolio selection. While predictive asset returns provide insights into future performance, they often fail to reflect the associated uncertainty. In portfolio selection, when investors are not risk-neutral, this uncertainty plays a crucial role in determining the desirable portfolio. Therefore, it is essential to incorporate a method that accounts for the uncertainty in predicted portfolio returns.

To address this, we utilize conformal inference, which offers a formal way to measure the uncertainty of predictions. Conformal inference provides prediction intervals C^T𝒘⁢(XT+1)subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇1\widehat{C}^{\bm{w}}\_{T}(X\_{T+1})over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) such that ℙ⁢(Rt⁢(𝒘)∈C^T𝒘⁢(XT+1))=1−αℙsubscript𝑅𝑡𝒘subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇11𝛼\mathbb{P}\left(R\_{t}\left({\bm{w}}\right)\in\widehat{C}^{\bm{w}}\_{T}(X\_{T+1})%
\right)=1-\alphablackboard\_P ( italic\_R start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ( bold\_italic\_w ) ∈ over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) ) = 1 - italic\_α. For each 𝒘∈𝒲𝒘𝒲\bm{w}\in\mathcal{W}bold\_italic\_w ∈ caligraphic\_W, we calculate the prediction interval C^T𝒘⁢(XT+1)subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇1\widehat{C}^{\bm{w}}\_{T}(X\_{T+1})over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) using conformal inference and optimize an objective based on these intervals. We denote the mechanism that receives prediction intervals and returns a portfolio 𝒘^T+1subscript^𝒘𝑇1\widehat{\bm{w}}\_{T+1}over^ start\_ARG bold\_italic\_w end\_ARG start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT as

|  |  |  |
| --- | --- | --- |
|  | PI⁢({C^T𝒘⁢(XT+1)}𝒘∈𝒲)=𝒘^T+1.PIsubscriptsubscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇1𝒘𝒲subscript^𝒘𝑇1\displaystyle\mathrm{PI}\left(\{\widehat{C}^{\bm{w}}\_{T}(X\_{T+1})\}\_{\bm{w}\in% \mathcal{W}}\right)=\widehat{\bm{w}}\_{T+1}.roman\_PI ( { over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) } start\_POSTSUBSCRIPT bold\_italic\_w ∈ caligraphic\_W end\_POSTSUBSCRIPT ) = over^ start\_ARG bold\_italic\_w end\_ARG start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT . |  |

We refer to such a portfolio as a prediction-interval-based portfolio.

Our framework is general and can accommodate various objectives for portfolio selection, allowing flexibility in both the choice of predictive models and conformal inference methods. We do not impose specific choices for these, as different methods may be suitable depending on the data-generating process. For example, for conformal inference with dependent data, methods proposed by Chernozhukov et al. ([2018](https://arxiv.org/html/2410.16333v1#bib.bib5)) can be employed, and appropriate methods should be selected based on the data at hand.

We refer to our framework as *conformal predictive portfolio selection* (CPPS), where conformal inference is used to generate prediction intervals, and these intervals are then leveraged to construct the prediction-interval-based portfolios. Our CPPS method is composed of the following core steps:

For each portfolio 𝒘∈𝒲𝒘𝒲\bm{w}\in\mathcal{W}bold\_italic\_w ∈ caligraphic\_W, compute a prediction interval C^T𝒘⁢(XT+1)subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇1\widehat{C}^{\bm{w}}\_{T}(X\_{T+1})over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) using a conformal inference method, and calculate the portfolio value.

Select the desirable portfolio by choosing the one that provides the best portfolio value based on the prediction intervals.

We provide the pseudo-code for this procedure in Algorithm [1](https://arxiv.org/html/2410.16333v1#alg1 "Algorithm 1 ‣ 3 Conformal Predictive Portfolio Selection ‣ Conformal Predictive Portfolio Selection").

An important practical consideration is that computing prediction intervals for every 𝒘∈𝒲𝒘𝒲\bm{w}\in\mathcal{W}bold\_italic\_w ∈ caligraphic\_W can be computationally expensive. To address this, it may be necessary to restrict the portfolio class 𝒲𝒲\mathcal{W}caligraphic\_W to a finite set. Reducing computational costs is a key direction for future research.

### 3.1 Example: HR-LR CPPS

While our CPPS framework does not require specific predictive models and conformal inference, it is helpful to provide a concrete example to illustrate the procedure. Here, we present an example of CPPS, where we select a portfolio that maximizes returns at a given error rate α𝛼\alphaitalic\_α, while limiting risk. We refer to this as the High-Return-from-Low-Risk (HR-LR) portfolio. Although this example is simple, it provides an intuitive understanding of the CPPS framework. We also include the procedure and corresponding pseudo-code. For the conformal inference, we use the method proposed by Chernozhukov et al. ([2018](https://arxiv.org/html/2410.16333v1#bib.bib5)).

Let ℰ⊂𝒲ℰ𝒲\mathcal{E}\subset\mathcal{W}caligraphic\_E ⊂ caligraphic\_W be the set of portfolio candidates, α∈(0,1)𝛼01\alpha\in(0,1)italic\_α ∈ ( 0 , 1 ) the error rate, and ℋℋ\mathcal{H}caligraphic\_H the hypothetical values of RT+1⁢(𝒘)subscript𝑅𝑇1𝒘R\_{T+1}(\bm{w})italic\_R start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ( bold\_italic\_w ). For simplicity, assume that ℋℋ\mathcal{H}caligraphic\_H is a discrete set, such as ℋ={−0.3,−0.2,0.0,0.1,0.2,0.3}ℋ0.30.20.00.10.20.3\mathcal{H}=\{-0.3,-0.2,0.0,0.1,0.2,0.3\}caligraphic\_H = { - 0.3 , - 0.2 , 0.0 , 0.1 , 0.2 , 0.3 }. It is important to note that ℰℰ\mathcal{E}caligraphic\_E is not required to span the entire space 𝒲𝒲\mathcal{W}caligraphic\_W; rather, it can consist of portfolio candidates provided by an investor.

We begin by defining a finite set of portfolio candidates ℰℰ\mathcal{E}caligraphic\_E. For each 𝒘∈ℰ𝒘ℰ\bm{w}\in\mathcal{E}bold\_italic\_w ∈ caligraphic\_E, we use conformal inference to obtain a prediction interval C^T𝒘⁢(XT+1)⊆ℋsubscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇1ℋ\widehat{C}^{\bm{w}}\_{T}(X\_{T+1})\subseteq\mathcal{H}over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) ⊆ caligraphic\_H that satisfies

|  |  |  |
| --- | --- | --- |
|  | ℙ⁢(RT+1⁢(𝒘)∈C^T𝒘⁢(XT+1))≥1−α.ℙsubscript𝑅𝑇1𝒘subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇11𝛼\mathbb{P}\left(R\_{T+1}(\bm{w})\in\widehat{C}^{\bm{w}}\_{T}(X\_{T+1})\right)\geq 1% -\alpha.blackboard\_P ( italic\_R start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ( bold\_italic\_w ) ∈ over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) ) ≥ 1 - italic\_α . |  |

Let m≥1𝑚1m\geq 1italic\_m ≥ 1 be a positive integer. For each portfolio 𝒘∈ℰ𝒘ℰ\bm{w}\in\mathcal{E}bold\_italic\_w ∈ caligraphic\_E, define the lowest and highest returns in C^T𝒘⁢(XT+1)subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇1\widehat{C}^{\bm{w}}\_{T}(X\_{T+1})over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) as r¯T+1𝒘,αsubscriptsuperscript¯𝑟

𝒘𝛼𝑇1\underline{r}^{\bm{w},\alpha}\_{T+1}under¯ start\_ARG italic\_r end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w , italic\_α end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT and r¯T+1𝒘,αsubscriptsuperscript¯𝑟

𝒘𝛼𝑇1\overline{r}^{\bm{w},\alpha}\_{T+1}over¯ start\_ARG italic\_r end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w , italic\_α end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT, respectively. We select m𝑚mitalic\_m portfolios 𝒘∈ℰ~⊂ℰ𝒘~ℰℰ\bm{w}\in\widetilde{\mathcal{E}}\subset\mathcal{E}bold\_italic\_w ∈ over~ start\_ARG caligraphic\_E end\_ARG ⊂ caligraphic\_E from the candidates with the lowest r¯T+1𝒘,αsubscriptsuperscript¯𝑟

𝒘𝛼𝑇1\underline{r}^{\bm{w},\alpha}\_{T+1}under¯ start\_ARG italic\_r end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w , italic\_α end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT up to the m𝑚mitalic\_m-th lowest. Then, we choose the portfolio with the highest r¯T+1𝒘,αsubscriptsuperscript¯𝑟

𝒘𝛼𝑇1\overline{r}^{\bm{w},\alpha}\_{T+1}over¯ start\_ARG italic\_r end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w , italic\_α end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT. This portfolio, denoted as 𝒘HR−LRsuperscript𝒘HRLR\bm{w}^{\mathrm{HR}\mathchar 45\relax\mathrm{LR}}bold\_italic\_w start\_POSTSUPERSCRIPT roman\_HR - roman\_LR end\_POSTSUPERSCRIPT, is defined by

|  |  |  |
| --- | --- | --- |
|  | 𝒘HR−LR=arg⁢max𝒘∈ℰ~⁡r¯T+1𝒘,α.superscript𝒘HRLRsubscriptargmax𝒘~ℰsubscriptsuperscript¯𝑟  𝒘𝛼𝑇1\displaystyle\bm{w}^{\mathrm{HR}\mathchar 45\relax\mathrm{LR}}=\operatorname\*{% arg\,max}\_{\bm{w}\in\widetilde{\mathcal{E}}}\overline{r}^{\bm{w},\alpha}\_{T+1}.bold\_italic\_w start\_POSTSUPERSCRIPT roman\_HR - roman\_LR end\_POSTSUPERSCRIPT = start\_OPERATOR roman\_arg roman\_max end\_OPERATOR start\_POSTSUBSCRIPT bold\_italic\_w ∈ over~ start\_ARG caligraphic\_E end\_ARG end\_POSTSUBSCRIPT over¯ start\_ARG italic\_r end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w , italic\_α end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT . |  |

This portfolio is expected to have the highest return among a set of portfolios whose lowest return within the confidence interval is relatively high compared to other portfolios.

### 3.2 HR-LR CPPS with AR Models

As a more concrete example, we demonstrate the CPPS framework using AR models as a predictive model. For the conformal inference, we apply the method proposed by Chernozhukov et al. ([2018](https://arxiv.org/html/2410.16333v1#bib.bib5)).

#### Step 1: Data Augmentation

Let hypothetical values ℋ={r(1),r(2),…,r(H)}ℋsuperscript𝑟1superscript𝑟2…superscript𝑟𝐻\mathcal{H}=\{r^{(1)},r^{(2)},\dots,r^{(H)}\}caligraphic\_H = { italic\_r start\_POSTSUPERSCRIPT ( 1 ) end\_POSTSUPERSCRIPT , italic\_r start\_POSTSUPERSCRIPT ( 2 ) end\_POSTSUPERSCRIPT , … , italic\_r start\_POSTSUPERSCRIPT ( italic\_H ) end\_POSTSUPERSCRIPT } be given. For each 𝒘∈𝒲𝒘𝒲\bm{w}\in\mathcal{W}bold\_italic\_w ∈ caligraphic\_W and r∈ℋ𝑟ℋr\in\mathcal{H}italic\_r ∈ caligraphic\_H, we define an augmented dataset 𝒟(r)={Zt}t=1T+1subscript𝒟𝑟superscriptsubscriptsubscript𝑍𝑡𝑡1𝑇1\mathcal{D}\_{(r)}=\{Z\_{t}\}\_{t=1}^{T+1}caligraphic\_D start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT = { italic\_Z start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T + 1 end\_POSTSUPERSCRIPT, where

|  |  |  |  |
| --- | --- | --- | --- |
|  | Zt=(R~t,Xt)={(Rt⁢(𝒘),Xt)if⁢ 1≤t≤T,(r,Xt)if⁢t=T+1.subscript𝑍𝑡subscript~𝑅𝑡subscript𝑋𝑡casessubscript𝑅𝑡𝒘subscript𝑋𝑡if1𝑡𝑇𝑟subscript𝑋𝑡if𝑡𝑇1\displaystyle Z\_{t}=\left(\widetilde{R}\_{t},X\_{t}\right)=\begin{cases}(R\_{t}(% \bm{w}),X\_{t})&\textrm{if}\ 1\leq t\leq T,\\ (r,X\_{t})&\textrm{if}\ t=T+1.\end{cases}italic\_Z start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT = ( over~ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) = { start\_ROW start\_CELL ( italic\_R start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ( bold\_italic\_w ) , italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) end\_CELL start\_CELL if 1 ≤ italic\_t ≤ italic\_T , end\_CELL end\_ROW start\_ROW start\_CELL ( italic\_r , italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) end\_CELL start\_CELL if italic\_t = italic\_T + 1 . end\_CELL end\_ROW |  | (1) |

Let π𝜋\piitalic\_π be a permutation of the set {1,2,…,T}12…𝑇\{1,2,\dots,T\}{ 1 , 2 , … , italic\_T }. Denote the permuted dataset as 𝒟(r)π={Zπ⁢(t)}t=1Tsubscriptsuperscript𝒟𝜋𝑟superscriptsubscriptsubscript𝑍𝜋𝑡𝑡1𝑇\mathcal{D}^{\pi}\_{(r)}=\{Z\_{\pi(t)}\}\_{t=1}^{T}caligraphic\_D start\_POSTSUPERSCRIPT italic\_π end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT = { italic\_Z start\_POSTSUBSCRIPT italic\_π ( italic\_t ) end\_POSTSUBSCRIPT } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT. We assume that the identity permutation 𝕀𝕀\mathbb{I}blackboard\_I is included in the set of permutations, so that 𝒟(r)=𝒟(r)𝕀subscript𝒟𝑟subscriptsuperscript𝒟𝕀𝑟\mathcal{D}\_{(r)}=\mathcal{D}^{\mathbb{I}}\_{(r)}caligraphic\_D start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT = caligraphic\_D start\_POSTSUPERSCRIPT blackboard\_I end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT. Specifically, following Chernozhukov et al. ([2018](https://arxiv.org/html/2410.16333v1#bib.bib5)), we consider the following blocking permutation; that is, we define Π={πj}j=1TΠsubscriptsuperscriptsubscript𝜋𝑗𝑇𝑗1\Pi=\{\pi\_{j}\}^{T}\_{j=1}roman\_Π = { italic\_π start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT } start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_j = 1 end\_POSTSUBSCRIPT as

|  |  |  |
| --- | --- | --- |
|  | t↦πj⁢(t)={t+(j−1)if⁢ 1≤t≤T−(j−1)t+(j−1)−Tif⁢T−(j−1)+1≤t≤Tmaps-to𝑡subscript𝜋𝑗𝑡cases𝑡𝑗1if1𝑡𝑇𝑗1𝑡𝑗1𝑇if𝑇𝑗11𝑡𝑇\displaystyle t\mapsto\pi\_{j}(t)=\begin{cases}t+(j-1)&\mathrm{if}\ 1\leq t\leq T% -(j-1)\\ t+(j-1)-T&\mathrm{if}\ T-(j-1)+1\leq t\leq T\end{cases}italic\_t ↦ italic\_π start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ( italic\_t ) = { start\_ROW start\_CELL italic\_t + ( italic\_j - 1 ) end\_CELL start\_CELL roman\_if 1 ≤ italic\_t ≤ italic\_T - ( italic\_j - 1 ) end\_CELL end\_ROW start\_ROW start\_CELL italic\_t + ( italic\_j - 1 ) - italic\_T end\_CELL start\_CELL roman\_if italic\_T - ( italic\_j - 1 ) + 1 ≤ italic\_t ≤ italic\_T end\_CELL end\_ROW |  |

for t=1,…,T𝑡

1…𝑇t=1,\dots,Titalic\_t = 1 , … , italic\_T.

#### Step 2: Training a Predictive Model

For each dataset 𝒟(r)π={(R~π⁢(t),Xπ⁢(t))}t=1T+1subscriptsuperscript𝒟𝜋𝑟superscriptsubscriptsubscript~𝑅𝜋𝑡subscript𝑋𝜋𝑡𝑡1𝑇1\mathcal{D}^{\pi}\_{(r)}=\left\{\left(\widetilde{R}\_{\pi(t)},X\_{\pi(t)}\right)%
\right\}\_{t=1}^{T+1}caligraphic\_D start\_POSTSUPERSCRIPT italic\_π end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT = { ( over~ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_π ( italic\_t ) end\_POSTSUBSCRIPT , italic\_X start\_POSTSUBSCRIPT italic\_π ( italic\_t ) end\_POSTSUBSCRIPT ) } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T + 1 end\_POSTSUPERSCRIPT, including the original data 𝒟(r)subscript𝒟𝑟\mathcal{D}\_{(r)}caligraphic\_D start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT, we train an AR model using {(R~π⁢(t),Xπ⁢(t))}t=1Tsuperscriptsubscriptsubscript~𝑅𝜋𝑡subscript𝑋𝜋𝑡𝑡1𝑇\left\{\left(\widetilde{R}\_{\pi(t)},X\_{\pi(t)}\right)\right\}\_{t=1}^{T}{ ( over~ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_π ( italic\_t ) end\_POSTSUBSCRIPT , italic\_X start\_POSTSUBSCRIPT italic\_π ( italic\_t ) end\_POSTSUBSCRIPT ) } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT. Denote the trained model by fTπsubscriptsuperscript𝑓𝜋𝑇f^{\pi}\_{T}italic\_f start\_POSTSUPERSCRIPT italic\_π end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT, with fTsubscript𝑓𝑇f\_{T}italic\_f start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT corresponding to the model trained using the original dataset 𝒟(r)subscript𝒟𝑟\mathcal{D}\_{(r)}caligraphic\_D start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT.

#### Step 3: conformal inference

We define the p𝑝pitalic\_p-value as

|  |  |  |  |
| --- | --- | --- | --- |
|  | p^⁢(r):=1|Π|⁢∑π∈Π𝟏⁢[S⁢(𝒟(r)π)≥S⁢(𝒟(r))],assign^𝑝𝑟1Πsubscript𝜋Π1delimited-[]𝑆subscriptsuperscript𝒟𝜋𝑟𝑆subscript𝒟𝑟\displaystyle\widehat{p}(r):=\frac{1}{|\Pi|}\sum\_{\pi\in\Pi}\mathbf{1}[S(% \mathcal{D}^{\pi}\_{(r)})\geq S(\mathcal{D}\_{(r)})],over^ start\_ARG italic\_p end\_ARG ( italic\_r ) := divide start\_ARG 1 end\_ARG start\_ARG | roman\_Π | end\_ARG ∑ start\_POSTSUBSCRIPT italic\_π ∈ roman\_Π end\_POSTSUBSCRIPT bold\_1 [ italic\_S ( caligraphic\_D start\_POSTSUPERSCRIPT italic\_π end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT ) ≥ italic\_S ( caligraphic\_D start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT ) ] , |  | (2) |

where S⁢(⋅)𝑆⋅S(\cdot)italic\_S ( ⋅ ) is the nonconformity score. In this case, S⁢(⋅)𝑆⋅S(\cdot)italic\_S ( ⋅ ) is defined as the (empirical) mean squared error between the predicted values and R~π⁢(t)subscript~𝑅𝜋𝑡\widetilde{R}\_{\pi(t)}over~ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_π ( italic\_t ) end\_POSTSUBSCRIPT:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  |  | S⁢(𝒟(r))=1T+1⁢∑t=1T+1(R~t−fT⁢(Xt))2,𝑆subscript𝒟𝑟1𝑇1subscriptsuperscript𝑇1𝑡1superscriptsubscript~𝑅𝑡subscript𝑓𝑇subscript𝑋𝑡2\displaystyle S(\mathcal{D}\_{(r)})=\frac{1}{T+1}\sum^{T+1}\_{t=1}\left(% \widetilde{R}\_{t}-f\_{T}(X\_{t})\right)^{2},italic\_S ( caligraphic\_D start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT ) = divide start\_ARG 1 end\_ARG start\_ARG italic\_T + 1 end\_ARG ∑ start\_POSTSUPERSCRIPT italic\_T + 1 end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT ( over~ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT - italic\_f start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) ) start\_POSTSUPERSCRIPT 2 end\_POSTSUPERSCRIPT , |  | (3) |
|  |  |  |  |
| --- | --- | --- | --- |
|  |  | S⁢(𝒟(r)π)=1T+1⁢∑t=1T+1(R~π⁢(t)−fTπ⁢(Xπ⁢(t)))2.𝑆subscriptsuperscript𝒟𝜋𝑟1𝑇1subscriptsuperscript𝑇1𝑡1superscriptsubscript~𝑅𝜋𝑡subscriptsuperscript𝑓𝜋𝑇subscript𝑋𝜋𝑡2\displaystyle S(\mathcal{D}^{\pi}\_{(r)})=\frac{1}{T+1}\sum^{T+1}\_{t=1}\left(% \widetilde{R}\_{\pi(t)}-f^{\pi}\_{T}(X\_{\pi(t)})\right)^{2}.italic\_S ( caligraphic\_D start\_POSTSUPERSCRIPT italic\_π end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT ( italic\_r ) end\_POSTSUBSCRIPT ) = divide start\_ARG 1 end\_ARG start\_ARG italic\_T + 1 end\_ARG ∑ start\_POSTSUPERSCRIPT italic\_T + 1 end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT ( over~ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_π ( italic\_t ) end\_POSTSUBSCRIPT - italic\_f start\_POSTSUPERSCRIPT italic\_π end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_π ( italic\_t ) end\_POSTSUBSCRIPT ) ) start\_POSTSUPERSCRIPT 2 end\_POSTSUPERSCRIPT . |  |

For a given α∈(0,1)𝛼01\alpha\in(0,1)italic\_α ∈ ( 0 , 1 ), the prediction set is defined as

|  |  |  |
| --- | --- | --- |
|  | 𝒞Tw⁢(XT+1)={r:p^⁢(r)>α}.subscriptsuperscript𝒞𝑤𝑇subscript𝑋𝑇1conditional-set𝑟^𝑝𝑟𝛼\displaystyle\mathcal{C}^{w}\_{T}(X\_{T+1})=\left\{r:\widehat{p}(r)>\alpha\right\}.caligraphic\_C start\_POSTSUPERSCRIPT italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) = { italic\_r : over^ start\_ARG italic\_p end\_ARG ( italic\_r ) > italic\_α } . |  |

We consider a grid of candidate values for ℋℋ\mathcal{H}caligraphic\_H. The pseudo-code for this conformal inference method, based on Chernozhukov et al. ([2018](https://arxiv.org/html/2410.16333v1#bib.bib5)), is shown in Algorithm [3](https://arxiv.org/html/2410.16333v1#alg3 "Algorithm 3 ‣ Step 5: HR-LR CPPS ‣ 3.2 HR-LR CPPS with AR Models ‣ 3 Conformal Predictive Portfolio Selection ‣ Conformal Predictive Portfolio Selection").

#### Step 4: Defining Highest Return and Lowest Risk

For each 𝒘𝒘\bm{w}bold\_italic\_w, define r¯T+1𝒘,α=maxr∈C^T𝒘⁢(XT+1)⁡rsubscriptsuperscript¯𝑟

𝒘𝛼𝑇1subscript𝑟subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇1𝑟\overline{r}^{\bm{w},\alpha}\_{T+1}=\max\_{r\in\widehat{C}^{\bm{w}}\_{T}(X\_{T+1})}rover¯ start\_ARG italic\_r end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w , italic\_α end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT = roman\_max start\_POSTSUBSCRIPT italic\_r ∈ over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) end\_POSTSUBSCRIPT italic\_r and r¯T+1𝒘,α=minr∈C^T𝒘⁢(XT+1)⁡rsubscriptsuperscript¯𝑟

𝒘𝛼𝑇1subscript𝑟subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇1𝑟\underline{r}^{\bm{w},\alpha}\_{T+1}=\min\_{r\in\widehat{C}^{\bm{w}}\_{T}(X\_{T+1}%
)}runder¯ start\_ARG italic\_r end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w , italic\_α end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT = roman\_min start\_POSTSUBSCRIPT italic\_r ∈ over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) end\_POSTSUBSCRIPT italic\_r
we select m𝑚mitalic\_m portfolios with the highest r¯T+1𝒘,αsubscriptsuperscript¯𝑟

𝒘𝛼𝑇1\underline{r}^{\bm{w},\alpha}\_{T+1}under¯ start\_ARG italic\_r end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w , italic\_α end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT, and denote this set as ℰ~⊂𝒲~ℰ𝒲\widetilde{\mathcal{E}}\subset\mathcal{W}over~ start\_ARG caligraphic\_E end\_ARG ⊂ caligraphic\_W.

#### Step 5: HR-LR CPPS

Finally, from the set ℰ~~ℰ\widetilde{\mathcal{E}}over~ start\_ARG caligraphic\_E end\_ARG, we select the portfolio with the highest return as

|  |  |  |
| --- | --- | --- |
|  | 𝒘^T+1=arg⁢max𝒘∈ℰ~⁡r¯T+1𝒘,α.subscript^𝒘𝑇1subscriptargmax𝒘~ℰsubscriptsuperscript¯𝑟  𝒘𝛼𝑇1\widehat{\bm{w}}\_{T+1}=\operatorname\*{arg\,max}\_{\bm{w}\in\widetilde{\mathcal{% E}}}\overline{r}^{\bm{w},\alpha}\_{T+1}.over^ start\_ARG bold\_italic\_w end\_ARG start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT = start\_OPERATOR roman\_arg roman\_max end\_OPERATOR start\_POSTSUBSCRIPT bold\_italic\_w ∈ over~ start\_ARG caligraphic\_E end\_ARG end\_POSTSUBSCRIPT over¯ start\_ARG italic\_r end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w , italic\_α end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT . |  |

### 3.3 Theoretical Analysis

We now turn to the justification of conformal inference for dependent data, following the results presented in Chernozhukov et al. ([2018](https://arxiv.org/html/2410.16333v1#bib.bib5)).

To introduce this justification, we define an unknown oracle score function S∗subscript𝑆S\_{\*}italic\_S start\_POSTSUBSCRIPT ∗ end\_POSTSUBSCRIPT. The validity of conformal inference for dependent data depends on how well the score S𝑆Sitalic\_S, defined in ([3](https://arxiv.org/html/2410.16333v1#S3.E3 "Equation 3 ‣ Step 3: conformal inference ‣ 3.2 HR-LR CPPS with AR Models ‣ 3 Conformal Predictive Portfolio Selection ‣ Conformal Predictive Portfolio Selection")), approximates the oracle score S∗subscript𝑆S\_{\*}italic\_S start\_POSTSUBSCRIPT ∗ end\_POSTSUBSCRIPT.

When using AR models and the blocking permutation ΠΠ\Piroman\_Π, under certain regularity conditions, the following results hold for a set of sequences {δ1,t,δ2,t,γ1,t,γ2,t}t=1Tsuperscriptsubscriptsubscript𝛿

1𝑡subscript𝛿

2𝑡subscript𝛾

1𝑡subscript𝛾

2𝑡𝑡1𝑇\{\delta\_{1,t},\delta\_{2,t},\gamma\_{1,t},\gamma\_{2,t}\}\_{t=1}^{T}{ italic\_δ start\_POSTSUBSCRIPT 1 , italic\_t end\_POSTSUBSCRIPT , italic\_δ start\_POSTSUBSCRIPT 2 , italic\_t end\_POSTSUBSCRIPT , italic\_γ start\_POSTSUBSCRIPT 1 , italic\_t end\_POSTSUBSCRIPT , italic\_γ start\_POSTSUBSCRIPT 2 , italic\_t end\_POSTSUBSCRIPT } start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT, where each element approaches zero as t→∞→𝑡t\to\inftyitalic\_t → ∞ (Chernozhukov et al., [2018](https://arxiv.org/html/2410.16333v1#bib.bib5)):

With probability 1−γ11subscript𝛾11-\gamma\_{1}1 - italic\_γ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT, the randomization distribution

|  |  |  |
| --- | --- | --- |
|  | F~⁢(x)≔1T⁢∑π∈Π𝟙⁢[S∗⁢(Zπ)<x]≔~𝐹𝑥1𝑇subscript𝜋Π1delimited-[]subscript𝑆superscript𝑍𝜋𝑥\widetilde{F}(x)\coloneqq\frac{1}{T}\sum\_{\pi\in\Pi}\mathbbm{1}\left[S\_{\*}% \left(Z^{\pi}\right)<x\right]over~ start\_ARG italic\_F end\_ARG ( italic\_x ) ≔ divide start\_ARG 1 end\_ARG start\_ARG italic\_T end\_ARG ∑ start\_POSTSUBSCRIPT italic\_π ∈ roman\_Π end\_POSTSUBSCRIPT blackboard\_1 [ italic\_S start\_POSTSUBSCRIPT ∗ end\_POSTSUBSCRIPT ( italic\_Z start\_POSTSUPERSCRIPT italic\_π end\_POSTSUPERSCRIPT ) < italic\_x ] |  |

satisfies

|  |  |  |
| --- | --- | --- |
|  | |F~⁢(x)−F⁢(x)|≤δ1,T,~𝐹𝑥𝐹𝑥subscript𝛿  1𝑇|\widetilde{F}(x)-F(x)|\leq\delta\_{1,T},| over~ start\_ARG italic\_F end\_ARG ( italic\_x ) - italic\_F ( italic\_x ) | ≤ italic\_δ start\_POSTSUBSCRIPT 1 , italic\_T end\_POSTSUBSCRIPT , |  |

where F⁢(x)=P⁢(S∗⁢(Z)<x)𝐹𝑥𝑃subscript𝑆𝑍𝑥F(x)=P\left(S\_{\*}(Z)<x\right)italic\_F ( italic\_x ) = italic\_P ( italic\_S start\_POSTSUBSCRIPT ∗ end\_POSTSUBSCRIPT ( italic\_Z ) < italic\_x ). When this inequality holds, we say that F~⁢(x)~𝐹𝑥\widetilde{F}(x)over~ start\_ARG italic\_F end\_ARG ( italic\_x ) is approximately ergodic for F⁢(x)𝐹𝑥F(x)italic\_F ( italic\_x ).

With probability 1−γ21subscript𝛾21-\gamma\_{2}1 - italic\_γ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT, the estimation errors are small:

The mean squared error satisfies 1T⁢∑π∈Π(S⁢(Zπ)−S∗⁢(Zπ))2≤δ2,T21𝑇subscript𝜋Πsuperscript𝑆superscript𝑍𝜋subscript𝑆superscript𝑍𝜋2subscriptsuperscript𝛿2

2𝑇\frac{1}{T}\sum\_{\pi\in\Pi}\left(S\left(Z^{\pi}\right)-S\_{\*}\left(Z^{\pi}%
\right)\right)^{2}\leq\delta^{2}\_{2,T}divide start\_ARG 1 end\_ARG start\_ARG italic\_T end\_ARG ∑ start\_POSTSUBSCRIPT italic\_π ∈ roman\_Π end\_POSTSUBSCRIPT ( italic\_S ( italic\_Z start\_POSTSUPERSCRIPT italic\_π end\_POSTSUPERSCRIPT ) - italic\_S start\_POSTSUBSCRIPT ∗ end\_POSTSUBSCRIPT ( italic\_Z start\_POSTSUPERSCRIPT italic\_π end\_POSTSUPERSCRIPT ) ) start\_POSTSUPERSCRIPT 2 end\_POSTSUPERSCRIPT ≤ italic\_δ start\_POSTSUPERSCRIPT 2 end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT 2 , italic\_T end\_POSTSUBSCRIPT;

The pointwise error at π=Identity𝜋Identity\pi=\mathrm{Identity}italic\_π = roman\_Identity is small: |S⁢(Z)−S∗⁢(Z)|≤δ2,T𝑆𝑍subscript𝑆𝑍subscript𝛿

2𝑇\left|S(Z)-S\_{\*}(Z)\right|\leq\delta\_{2,T}| italic\_S ( italic\_Z ) - italic\_S start\_POSTSUBSCRIPT ∗ end\_POSTSUBSCRIPT ( italic\_Z ) | ≤ italic\_δ start\_POSTSUBSCRIPT 2 , italic\_T end\_POSTSUBSCRIPT;

The probability density function of S∗⁢(Z)subscript𝑆𝑍S\_{\*}(Z)italic\_S start\_POSTSUBSCRIPT ∗ end\_POSTSUBSCRIPT ( italic\_Z ) is bounded above by a constant D𝐷Ditalic\_D.

Note that the number of permutations |Π|=TΠ𝑇|\Pi|=T| roman\_Π | = italic\_T.

Thus, the confidence interval obtained from conformal inference has approximate coverage of 1−α1𝛼1-\alpha1 - italic\_α. Specifically, it holds that

|  |  |  |
| --- | --- | --- |
|  | |ℙ⁢(RT+1⁢(𝒘)∈C^T𝒘⁢(XT+1))−(1−α)|ℙsubscript𝑅𝑇1𝒘subscriptsuperscript^𝐶𝒘𝑇subscript𝑋𝑇11𝛼\displaystyle\left|\mathbb{P}\left(R\_{T+1}(\bm{w})\in\widehat{C}^{\bm{w}}\_{T}(% X\_{T+1})\right)-(1-\alpha)\right|| blackboard\_P ( italic\_R start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ( bold\_italic\_w ) ∈ over^ start\_ARG italic\_C end\_ARG start\_POSTSUPERSCRIPT bold\_italic\_w end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_X start\_POSTSUBSCRIPT italic\_T + 1 end\_POSTSUBSCRIPT ) ) - ( 1 - italic\_α ) | |  |
|  |  |  |
| --- | --- | --- |
|  | ≤6⁢δ1,T+4⁢δ2,T+2⁢D⁢(δ2,T+2⁢δ2,T)+γ1,T+γ2,T.absent6subscript𝛿  1𝑇4subscript𝛿  2𝑇2𝐷subscript𝛿  2𝑇2subscript𝛿  2𝑇subscript𝛾  1𝑇subscript𝛾  2𝑇\displaystyle\leq 6\delta\_{1,T}+4\delta\_{2,T}+2D\left(\delta\_{2,T}+2\sqrt{% \delta\_{2,T}}\right)+\gamma\_{1,T}+\gamma\_{2,T}.≤ 6 italic\_δ start\_POSTSUBSCRIPT 1 , italic\_T end\_POSTSUBSCRIPT + 4 italic\_δ start\_POSTSUBSCRIPT 2 , italic\_T end\_POSTSUBSCRIPT + 2 italic\_D ( italic\_δ start\_POSTSUBSCRIPT 2 , italic\_T end\_POSTSUBSCRIPT + 2 square-root start\_ARG italic\_δ start\_POSTSUBSCRIPT 2 , italic\_T end\_POSTSUBSCRIPT end\_ARG ) + italic\_γ start\_POSTSUBSCRIPT 1 , italic\_T end\_POSTSUBSCRIPT + italic\_γ start\_POSTSUBSCRIPT 2 , italic\_T end\_POSTSUBSCRIPT . |  |

This result implies that under our setup, the confidence interval provided by conformal inference is approximately valid, thereby justifying our proposed HR-LR CPPS framework with AR models.

## 4 Experiments

In this section, we investigate the empirical performance of our proposed CPPS framework. Specifically, we focus on the HR-LR CPPS and conduct empirical studies in the US and Japanese markets. In each market, we use three stocks listed in Tables [1](https://arxiv.org/html/2410.16333v1#S4.T1 "Table 1 ‣ 4 Experiments ‣ Conformal Predictive Portfolio Selection") and [2](https://arxiv.org/html/2410.16333v1#S4.T2 "Table 2 ‣ 4 Experiments ‣ Conformal Predictive Portfolio Selection").

The stock price data spans from January 1, 2008, to December 31, 2019, and returns are calculated on a monthly basis. Data from 2008 to 2010 is used solely for parameter learning, while the performance of the portfolio is tested using data from 2011 to 2019. The parameter estimation is updated sequentially after 2011.

| Company | Industry |
| --- | --- |
| Apple Inc. | Technology |
| Microsoft Corp. | Technology |
| Amazon.com Inc. | Consumer Discretionary |

| Company | Industry |
| --- | --- |
| Toyota Motor | Automotive |
| SoftBank Group | Telecommunication & IT |
| Keyence | Electronic Equipment |

![Refer to caption](x1.png)
![Refer to caption](x2.png)

### 4.1 Alternative Methods

In this study, for comparison, we also construct portfolios with the following methods:

The sample mean of the past 1 year (M⁢e⁢a⁢nt⁢[1]𝑀𝑒𝑎subscript𝑛𝑡delimited-[]1Mean\_{t}[1]italic\_M italic\_e italic\_a italic\_n start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT [ 1 ]).

The sample mean of the past 3 years (M⁢e⁢a⁢nt⁢[3]𝑀𝑒𝑎subscript𝑛𝑡delimited-[]3Mean\_{t}[3]italic\_M italic\_e italic\_a italic\_n start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT [ 3 ]).

An AR(1)1(1)( 1 ) regression model using samples from the past 3 years (A⁢Rt⁢(1)𝐴subscript𝑅𝑡1AR\_{t}(1)italic\_A italic\_R start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ( 1 )).

An AR(2)2(2)( 2 ) regression model using samples from the past 3 years (A⁢Rt⁢(2)𝐴subscript𝑅𝑡2AR\_{t}(2)italic\_A italic\_R start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ( 2 )).

An AR(3)3(3)( 3 ) regression model using samples from the past 3 years (A⁢Rt⁢(3)𝐴subscript𝑅𝑡3AR\_{t}(3)italic\_A italic\_R start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ( 3 )).

### 4.2 Experimental Results

We run each method on the dataset from January 1, 2008, to December 31, 2019, and report their cumulative returns. We assume that investors can adjust their portfolio composition without incurring additional costs.

Figures [2](https://arxiv.org/html/2410.16333v1#S4.F2 "Figure 2 ‣ 4 Experiments ‣ Conformal Predictive Portfolio Selection") and [2](https://arxiv.org/html/2410.16333v1#S4.F2 "Figure 2 ‣ 4 Experiments ‣ Conformal Predictive Portfolio Selection") present the results for US and Japanese stocks, respectively. We denote the HR-LR CPPS by Conformal in our figures. From these results, we observe that our CPPS method performs well compared to alternative methods. We attribute this success to the HR-LR CPPS’s ability to avoid sudden drops in portfolio value. As shown in the figures, alternative methods sometimes experience significant losses, while the HR-LR method successfully mitigates these downturns. These losses contribute to the performance gap between our proposed CPPS and other methods.

## 5 Conclusion

In this study, we developed a general framework for portfolio selection using prediction intervals derived from conformal inference. As a concrete example, we introduced the HR-LR CPPS, which selects the portfolio with the highest return among those with the lowest risk. Our empirical studies, conducted using datasets from both the US and Japanese stock markets, demonstrated the effectiveness of the proposed method. The HR-LR CPPS showed its ability to mitigate significant losses and maintain consistent performance compared to alternative methods, highlighting the potential of conformal inference in portfolio selection.

## References

![Mascot Sammy](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)
