[Skip to content](#cb-content__main)

![Columbia University Mailman School of Public Health](https://www.publichealth.columbia.edu/sites/default/files/logo-mailman-blue-horizontal.svg?tfg526)

## [About Us](/about-us)

## [Events](/about-us/events)

## News

![Joseph L. Mailman School of Public Health entrance sign.](data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)

Read the latest news stories about Mailman faculty, research, and events.

[Explore Our News](https://www.publichealth.columbia.edu/about-us/news)

Read the latest news stories about Mailman faculty, research, and events.

## [Academics](/academics)

## [Degrees](/academics/degrees)

## Departments

![Professor discussing a diagram with three students in front of a whiteboard](data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)

We integrate an innovative skills-based curriculum, research collaborations, and hands-on field experience to prepare students.

## [Research](/research)

## Centers

![](data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)

Learn more about our research centers, which focus on critical issues in public health.

## [People](/people)

## Our Faculty

![Joseph L. Mailman School of Public Health building entrance.](data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)

Meet the faculty of the Mailman School of Public Health.

## [Become a Student](/become-student)

## [Life and Community](/become-student/life-community)

## How to Apply

![](data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)

Learn how to apply to the Mailman School of Public Health.

## [Info For](/info)

# Time-To-Event Data Analysis

|  |  |
| --- | --- |
| [Overview](#Overview) | Software |
| [Description](#Description) | Websites |
| [Readings](#readings) | [Courses](#courses) |

[Overview](#Overview)

Software

[Description](#Description)

Websites

[Readings](#readings)

[Courses](#courses)

## 

## Overview

This page briefly describes a series of questions that should be considered when analyzing time-to-event data and provides an annotated resource list for more information.

## Description

**What is unique about time-to-event (TTE) data?**

Time-to-event (TTE) data is unique because the outcome of interest is not only whether or not an event occurred, but also when that event occurred. Traditional methods of logistic and linear regression are not suited to be able to include both the event and time aspects as the outcome in the model. Traditional regression methods also are not equipped to handle censoring, a special type of missing data that occurs in time-to-event analyses when subjects do not experience the event of interest during the follow-up time. In the presence of censoring, the true time to event is underestimated. Special techniques for TTE data, as will be discussed below, have been developed to utilize the partial information on each subject with censored data and provide unbiased survival estimates. These techniques incorporate data from multiple time points across subjects and can be used to directly calculate rates, time ratios, and hazard ratios.

**What are important methodological considerations of time-to-event data?**

There are 4 main methodological considerations in the analysis of time to event or survival data. It is important to have a clear definition of the target event, the time origin, the time scale, and to describe how participants will exit the study. Once these are well-defined, then the analysis becomes more straight-forward. Typically there is a single target event, but there are extensions of survival analyses that allow for multiple events or repeated events.

**What is the time origin?**

The time origin is the point at which follow-up time starts. TTE data can employ a variety of time origins that are largely determined by study design, each having associated benefits and drawbacks. Examples include baseline time or baseline age. Time origins can also be determined by a defining characteristic, such as onset of exposure or diagnosis. This is often a natural choice if the outcome is related to that characteristic. Other examples include birth and calendar year. For cohort studies, the time-scale is most commonly time on study.

**Is there another option for time-scale other than time on study?**

Age is another commonly used time-scale, where baseline age is the time origin and individuals exit at their event or censoring age. Models with age as the time scale can be adjusted for calendar effects. Some authors recommend that age rather than time on study be used as the time-scale as it may provide less biased estimates.

**What is censoring?**

One of the challenges specific to survival analysis is that only some individuals will have experienced the event by the end of the study, and therefore survival times will be unknown for a subset of the study group. This phenomenon is called censoring and may arise in the following ways: the study participant has not yet experienced the relevant outcome, such as relapse or death, by the close of the study; the study participant is lost to follow-up during the study period; or, the study participant experiences a different event that makes further follow-up impossible. Such censored interval times underestimate the true but unknown time to event. For most analytic approaches, censoring is assumed to be random or non-informative.

There are three main types of censoring, right, left, and interval. If the events occur beyond the end of the study, then the data is right-censored. Left-censored data occurs when the event is observed, but exact event time is unknown. Interval-censored data occurs when the event is observed, but participants come in and out of observation, so the exact event time is unknown. Most survival analytic methods are designed for right-censored observations, but methods for interval and left-censored data are available.

**What is the question of interest?**

The choice of analytical tool should be guided by the research question of interest. With TTE data, the research question can take several forms, which influences which survival function is the most relevant to the research question. Three different types of research questions that may be of interest for TTE data include:

What proportion of individuals will remain free of the event after a certain time?

What proportion of individuals will have the event after a certain time?

What is the risk of the event at a particular point in time, among those who have survived until that point?

Each of these questions corresponds with a different type of function used in survival analysis:

Survival Function, S(t): the probability that an individual will survive beyond time t [Pr(T>t)]

Probability Density Function, F(t), or the Cumulative Incidence Function, R(t): the probability that that an individual will have a survival time less than or equal to t [Pr(T≤t)]

Hazard Function, h(t): the instantaneous potential of experiencing an event at time t, conditional on having survived to that time

Cumulative Hazard Function, H(t): the integral of the hazard function from time 0 to time t, which equals the area under the curve h(t) between time 0 and time t

If one of these functions is known, the other functions can be calculated using the following formulas:

S(t) = 1 – F(t)  The survival function and the probability density function sum to 1

h(t)=f(t)/S(t)  The instantaneous hazard equals the unconditional probability of

experiencing the event at time t, scaled by the fraction alive at time t

H(t) = -log[S(t)] The cumulative hazard function equals the negative log of the survival

function

S(t) = e –H(t) The survival function equals the exponentiated negative cumulative hazard

function

These conversions are used often in survival analysis methods, as will be discussed below. Generally, an increase in h(t), the instantaneous hazard, will lead to an increase in H(t), the cumulative hazard, which translates into a decrease in S(t), the survival function.

**What assumptions must be made to use standard techniques for time-to-event data?**

The main assumption in analyzing TTE data is that of non-informative censoring: individuals that are censored have the same probability of experiencing a subsequent event as individuals that remain in the study. Informative censoring is analogous to non-ignorable missing data, which will bias the analysis. There is no definitive way to test whether censoring is non-informative, though exploring patterns of censoring may indicate whether an assumption of non-informative censoring is reasonable. If informative censoring is suspected, sensitivity analyses, such as best-case and worst-case scenarios, can be used to try to quantify the effect that informative censoring has on the analysis.

Another assumption when analyzing TTE data is that there is sufficient follow-up time and number of events for adequate statistical power. This needs to be considered in the study design phase, as most survival analyses are based on cohort studies.

Additional simplifying assumptions are worth mentioning, as they are often made in overviews of survival analysis. While these assumptions simplify survival models, they are not necessary to conduct analyses with TTE data. Advanced techniques can be used if these assumptions are violated:

No cohort effect on survival: for a cohort with a long recruitment period, assume that individuals that join early have the same survival probabilities as those than join late

Right censoring only in the data

Events are independent of each other

**What types of approaches can be used for survival analysis?**

There are three main approaches to analyzing TTE data: non-parametric, semi-parametric and parametric approaches. The choice of which approach to use should be driven by the research question of interest. Often, more than one approach can be appropriately utilized in the same analysis.

What are non-parametric approaches to survival analysis and when are they appropriate?

Non-parametric approaches do not rely on assumptions about the shape or form of parameters in the underlying population. In survival analysis, non-parametric approaches are used to describe the data by estimating the survival function, S(t), along with the median and quartiles of survival time. These descriptive statistics cannot be calculated directly from the data due to censoring, which underestimates the true survival time in censored subjects, leading to skewed estimates of the mean, median and other descriptives. Non-parametric approaches are often used as the first step in an analysis to generate unbiased descriptive statistics, and are often used in conjunction with semi-parametric or parametric approaches.

**Kaplan-Meier Estimator**

The most common non-parametric approach in the literature is the Kaplan-Meier (or product limit) estimator. The Kaplan-Meier estimator works by breaking up the estimation of S(t) into a series of steps/intervals based on observed event times. Observations contribute to the estimation of S(t) until the event occurs or until they are censored. For each interval, the probability of surviving until the end of the interval is calculated, given that subjects are at risk at the beginning of the interval (this is commonly notated as pj =( nj – dj)/nj). The estimated S(t)for every value of t equals the product of surviving each interval up to and including time t. The main assumptions of this method, in addition to non-informative censoring, is that censoring occurs after failures and that there is no cohort effect on survival, so subjects have the same survival probability regardless of when they came under study.

The estimated S(t) from the Kaplan-Meier method can be plotted as a stepwise function with time on the X-axis. This plot is a nice way to visualize the survival experience of the cohort, and can also be used to estimate the median (when S(t)≤0.5) or quartiles of survival time. These descriptive statistics can also be calculated directly using the Kaplan-Meier estimator. 95% confidence intervals (CI) for S(t) rely on transformations of S(t) to ensure that the 95% CI is within 0 and 1. The most common method in the literature is the Greenwood estimator.

**Life Table Estimator**

The life table estimator of the survival function is one of the earliest examples of applied statistical methods, having been used for over 100 years to describe mortality in large populations. The life table estimator is similar to the Kaplan-Meier method, except that intervals are based on calendar time instead of observed events. Since life table methods are based on these calendar intervals, and not based on individual events/censoring times, these methods use the average risk set size per interval to estimate S(t) and must assume that censoring occurred uniformly over the calendar time interval. For this reason, the life table estimator is not as precise as the Kaplan-Meier estimator, but results will be similar in very large samples.

**Nelson-Aalen Estimator**

Another alternative to Kaplan-Meier is the Nelson-Aalen estimator, which is based on using a counting process approach to estimate the cumulative hazard function, H(t). The estimate of H(t)can then be used to estimate S(t). Estimates of S(t) derived using this method will always be greater than the K-M estimate, but the difference will be small between the two methods in large samples.

Can non-parametric approaches be used for univariable or multivariable analyses?

Non-parametric approaches like the Kaplan-Meier estimator can be used to conduct univariable analyses for categorical factors of interest. Factors must be categorical (either in nature or a continuous variable broken into categories) because the survival function, S(t), is estimated for each level of the categorical variable and then compared across these groups. The estimatedS(t) for each group can be plotted and visually compared.

Rank-based tests can also be used to statistically test the difference between the survival curves. These tests compare observed and expected number of events at each time point across groups, under the null hypothesis that the survival functions are equal across groups. There are several versions of these rank-based tests, which differ in the weight given to each time point in the calculation of the test statistic. Two of the most common rank-based tests seen in the literature are the log rank test, which gives each time point equal weight, and the Wilcoxon test, which weights each time point by the number of subjects at risk. Based on this weight, the Wilcoxon test is more sensitive to differences between curves early in the follow-up, when more subjects are at risk. Other tests, like the Peto-Prentice test, use weights in between those of the log rank and Wilcoxon tests. Rank-based tests are subject to the additional assumption that censoring is independent of group, and all are limited by little power to detect differences between groups when survival curves cross. Although these tests provide a p-value of the difference between curves, they cannot be used to estimate effect sizes (the log rank test p-value, however, is equivalent to the p-value for a categorical factor of interest in a univariable Cox model).

Non-parametric models are limited in that they do not provide effect estimates and cannot generally be used to assess the effect of multiple factors of interest (multivariable models). For this reason, non-parametric approaches are often used in conjunction with semi- or fully parametric models in epidemiology, where multivariable models are typically used to control for confounders.

**Can Kaplan-Meier curves be adjusted?**

It is a common myth that Kaplan-Meier curves cannot be adjusted, and this is often cited as a reason to use a parametric model that can generate covariate-adjusted survival curves. A method has been developed, however, to create adjusted survival curves using inverse probability weighting (IPW). In the case of only one covariate, IPWs can be non-parametrically estimated and are equivalent to direct standardization of the survival curves to the study population. In the case of multiple covariates, semi- or fully parametric models must be used to estimate the weights, which are then used to create multiple-covariate adjusted survival curves. Advantages of this method are that it is not subject to the proportional hazards assumption, it can be used for time-varying covariates, and it can also be used for continuous covariates.

**Why do we need parametric approaches for analyzing time-to-event data?**

A non-parametric approach to the analysis of TTE data is used to simply describe the survival data with respect to the factor under investigation. Models utilizing this approach are also referred to as univariable models. More commonly, investigators are interested in the relationship between several covariates and the time to event. The use of semi- and fully-parametric models allow the time to event to be analyzed with respect to many factors simultaneously, and provides estimates of the strength of the effect for each constituent factor.

**What is a semi-parametric approach, and why is it so commonly used?**

The Cox Proportional model is the most commonly used multivariable approach for analyzing survival data in medical research. It is essentially a time-to-event regression model, which describes the relation between the event incidence, as expressed by the hazard function, and a set of covariates. The Cox model is written as follows:

hazard function, h(t) = h0(t)exp{β1X1 + β2X2 + … + βpXp}

It is considered a semi-parametric approach because the model contains a non-parametric component and a parametric component. The non-parametric component is the baseline hazard, h0(t). This is the value of the hazard when all covariates are equal to 0, which highlights the importance of centering the covariates in the model for interpretability. Do not confuse the baseline hazard to be the hazard at time 0. The baseline hazard function is estimated non-parametrically, and so unlike most other statistical models, the survival times are not assumed to follow a particular statistical distribution and the shape of the baseline hazard is arbitrary. The baseline hazard function doesn’t need to be estimated in order to make inferences about the relative hazard or the hazard ratio. This feature makes the Cox model more robust than parametric approaches because it is not vulnerable to misspecification of the baseline hazard.

The parametric component is comprised of the covariate vector. The covariate vector multiples the baseline hazard by the same amount regardless of time, so the effect of any covariate is the same at any time during follow-up, and this is the basis for the proportional hazards assumption.

**What is the proportional hazards assumption?**

The proportional hazards assumption is vital to the use and interpretation of a Cox model.

Under this assumption, there is a constant relationship between the outcome or the dependent variable and the covariate vector. The implications of this assumption are that the hazard functions for any two individuals are proportional at any point in time and the hazard ratio does not vary with time. In other words, if an individual has a risk of death at some initial time point that is twice as high as that of another individual, then at all later time points the risk of death remains twice as high. This assumption implies that the hazard curves for the groups should be proportional and shouldn’t cross. Because this assumption is so important, it should definitely be tested.

**How do you test the proportional hazards assumption?**

There are a variety of techniques, both graphical and test-based, for assessing the validity of the proportional hazards assumption. One technique is to simply plot Kaplan–Meier survival curves if you are comparing two groups with no covariates. If the curves cross, the proportional hazards assumption may be violated. An important caveat to this approach must be kept in mind for small studies. There may be a large amount of error associated with the estimation of survival curves for studies with a small sample size, therefore the curves may cross even when the proportional hazards assumption is met. The complementary log-log plot is a more robust test that plots the logarithm of the negative logarithm of the estimated survivor function against the logarithm of survival time. If the hazards are proportional across groups, this plot will yield parallel curves. Another common method for testing the proportional hazards assumption is to include a time interaction term to determine if the HR changes over time, since time is often the culprit for non-proportionality of the hazards. Evidence that the group\*time interaction term is not zero is evidence against proportional hazards.

**What if the proportional hazards assumption doesn’t hold?**

If you find that the PH assumption doesn’t hold, you don’t necessarily need to abandon the use of the Cox model. There are options for improving the non-proportionality in the model. For example, you can include other covariates in the model, either new covariates, non-linear terms for existing covariates, or interactions among covariates. Or you can stratify the analysis on one or more variables. This estimates a model in which the baseline hazard is allowed to be different within each stratum, but the covariates effects are equal across strata. Other options include dividing time into categories and use indicator variables to allow hazard ratios to vary across time, and changing the analysis time variable (e.g, from elapsed time to age or vice versa).

**How do you examine semi-parametric model fit?**

In addition to checking for violations of the proportionality assumption, there are other aspects of model fit that should be examined. Statistics similar to those used in linear and logistic regression can be applied to perform these tasks for Cox models with some differences, but the essential ideas are the same in all three settings. It is important to check the linearity of the covariate vector, which can be done by examining the residuals, just as we do in linear regression. However, residuals in TTE data are not quite as straightforward as they are in linear regression, partly because the value of the outcome is unknown for some of the data, and the residuals are often skewed. Several different types of residuals have been developed in order to assess Cox model fit for TTE data. Examples include Martingale and Schoenfeld, among others. You can also look at the residuals to identify highly influential and poorly fit observations. There are also goodness-of-fit tests that are specific to Cox models, such as the Gronnesby and Borgan test, and the Hosmer and Lemeshow prognostic index. You can also use the AIC to compare different models, although use of R2 is problematic.

**Why use a parametric approach?**

One of the main advantages of semi-parametric models is that the baseline hazard does not need to be specified in order to estimate hazard ratios that describe differences in the relative hazard between groups. It may be, however, that the estimation of the baseline hazard itself is of interest. In this case, a parametric approach is necessary. In parametric approaches, both the hazard function and the effect of the covariates are specified. The hazard function is estimated based on an assumed distribution in the underlying population.

Advantages of using a parametric approach to survival analysis are:

Parametric approaches are more informative than non- and semi-parametric approaches. In addition to calculating relative effect estimates, they can also be used to predict survival time, hazard rates and mean and median survival times. They can also be used to make absolute risk predictions over time and to plot covariate-adjusted survival curves.

When the parametric form is correctly specified, parametric models have more power than semi-parametric models. They are also more efficient, leading to smaller standard errors and more precise estimates.

Parametric approaches rely on full maximum likelihood to estimate parameters.

Residuals of parametric models take the familiar form of the difference in the observed versus expected.

The main disadvantage of using a parametric approach is that is relies on the assumption that the underlying population distribution has been correctly specified. Parametric models are not robust to misspecification, which is why semi-parametric models are more common in the literature and are less risky to use when there is uncertainty about the underlying population distribution.

**How do you choose the parametric form?**

The choice of the appropriate parametric form is the most difficult part of parametric survival analysis. The specification of the parametric form should be driven by the study hypothesis, along with prior knowledge and biologic plausibility of the shape of the baseline hazard. For example, if it is known that the risk of death increases dramatically right after surgery and then decreases and flattens out, it would be inappropriate to specify the exponential distribution, which assumes a constant hazard over time. The data can be used to assess whether the specified form appears to fit the data, but these data-driven methods should complement, not replace, hypothesis-driven selections.

**What is the difference between a proportional hazards model and an accelerated failure time model?**

Although the Cox proportional hazards model is semi-parametric, proportional hazards models can also be parametric. Parametric proportional hazards models can be written as:

h(t,X) = h0(t)exp(Xi β) = h0(t)λ

where the baseline hazard, h0(t), depends only on time, t, but not on X, and λ is a unit-specific function of covariates, which does not depend on t, that scales the baseline hazard function up or down. λ cannot be negative. In this model, the hazard rate is a multiplicative function of the baseline hazard and the hazard ratios can be interpreted the same way as in the semi-parametric proportional hazards model.

Accelerated Failure Time (AFT) models are a class of parametric survival models that can be linearized by taking the natural log of the survival time model. The simplest example of an AFT model is the exponential model, which is written as:

ln(T) = β0 + β1X1+….+ βpXp + ε\*

The main difference between AFT models and PH models is that AFT models assumes that effects of covariates are multiplicative on time scale, while Cox models use the hazard scale as shown above. Parameter estimates from AFT models are interpreted as effects on the time scale, which can either accelerate or decelerate survival time. Exp(β)>1 from an AFT model means that the factor accelerates survival time, or leads to longer survival. Exp(β)<1 decelerates survival time (shorter survival). AFT models assume that estimated time ratios are constant across the time scale. A time ratio of 2, for example, can be interpreted as the median time to death in group 1 is double the median time to death in group 2 (indicated longer survival for group 1).

Some error distributions can be written and interpreted as both PH and AFT models (ie. exponential, Weibull), others are only PH (ie. Gompertz) or only AFT models (ie. log-logistic) and others are neither PH or AFT models (ie. fitting a spline).

**What forms can parametric models assume?**

The hazard function can take any form as long as h(t)>0 for all values of t. While the primary consideration for the parametric form should be prior knowledge of the shape of the baseline hazard, each distribution has its own advantages and disadvantages. Some of the more common forms will be briefly explained, with more information available in the resource list.

**Exponential Distribution**

The exponential distribution assumes that h(t) depends only on model coefficients and covariates and is constant over time. The main advantage of this model is that it is both a proportional hazards model and an accelerated failure time model, so that effect estimates can be interpreted as either hazard ratios or time ratios. The main drawback of this model is that it is often implausible to assume a constant hazard over time.

**Weibull Distribution**

The Weibull distribution is similar to the exponential distribution. While the exponential distribution assumes a constant hazard, the Weibull distribution assumes a monotonic hazard that can either be increasing or decreasing but not both. It has two parameters. The shape parameter (σ ) controls whether hazard increases (σ<1 ) or decreases (σ>1 ) (in the exponential distribution, this parameter is set to 1). The scale parameter, (1/σ)exp(-β0/σ), determines the scale of this increase/decrease. Since the Weibull distribution simplifies to the exponential distribution when σ=1, the null hypothesis that σ=1 can be tested using a Wald test. The main advantage of this model is that it is both a PH and AFT model, so both hazard ratios and time ratios can be estimated. Again, the main drawback is that the assumption of monotonicity of the baseline hazard may be implausible in some cases.

**Gompertz Distribution**

The Gompertz distribution is a PH model that is equal to the log-Weibull distribution, so the log of the hazard function is linear in t. This distribution has an exponentially increasing failure rate, and is often appropriate for actuarial data, as the risk of mortality also increases exponentially over time.

**Log-Logistic Distribution**

The log-logistic distribution is an AFT model with an error term that follows the standard logistic distribution. It can fit non-monotonic hazards, and generally fits best when the underlying hazard rises to a peak and then falls, which may be plausible for certain diseases like tuberculosis. The log-logistic distribution is not a PH model, but it is a proportional odds model. This means that it is subject to the proportional odds assumption, but the advantage is that slope coefficients can be interpreted as time ratios and also as odds ratios. An odds ratio of 2 from a parametric log-logistic model, for example, would be interpreted as the odds of survival beyond time t among subjects with x=1 is twice the odds among subjects with x=0.

**Generalized Gamma (GG) Distribution**

The generalized gamma (GG) distribution is actually a family of distributions that contains nearly all of the most commonly used distributions, including the exponential, Weibull, log normal and gamma distributions. This allows for comparisons among the different distributions. The GG family also includes all four of the most common types of hazard functions, which makes the GG distribution particularly useful since the shape of the hazard function may help optimize model selection.

**Splines Approach**

Since the only general limitation of the specification of the baseline hazard function is thath(t)>0 for all values of t, splines can be used for maximum flexibility in modeling the shape of the baseline hazard. Restricted cubic splines are one method that has recently been recommended in the literature for parametric survival analysis since this method allows for flexibility in the shape, but restricts the function to be linear on ends where data is sparse. Splines can be used to improve estimation and are also advantageous for extrapolation, since they maximize fit to the observed data. If correctly specified, effect estimates from models fit using splines should not be biased. Like in other regression analyses, challenges in fitting splines can include choosing the number and location of the knots and issues with over-fitting.

**How do you examine parametric model fit?**

The most important component of assessing parametric model fit is to check whether the data supports the specified parametric form. This can be assessed visually by graphing the model-based cumulative hazard against the Kaplan-Meier estimated cumulative hazard function. If the specified form is correct, the graph should go through the origin with a slope of 1. The Grønnesby-Borgan goodness-of-fit test can also be used to whether the observed number of events is significantly different from the expected number of events in groups differentiated by risk scores. This test is highly sensitive to the number of groups chosen, and tends to reject the null hypothesis of adequate fit too liberally if many groups are chosen, especially in small data sets. The test lacks power to detect model violations, however, if too few groups are chosen. For this reason, it seems ill-advised to rely on a goodness-of-fit test alone in determining if the specified parametric form is reasonable.

AIC can also be used to compare models run with different parametric forms, with the lowest AIC indicative of the best fit. AIC cannot be used to compare parametric and semi-parametric models, however, since parametric models are based on observed event times and semi-parametric models are based on the order of event times. Again, these tools should be used to examine whether the specified form fits the data, but plausibility of the specified underlying hazard is still the most important aspect of choosing a parametric form.

Once the specified parametric form has been determined to fit the data well, similar methods to those previously described for semi-proportional hazard models can be used to choose between different models, such as residual plots and goodness-of-fit tests.

**What if predictors change over time?**

In the model statements written above, we have assumed that exposures are constant over the course of follow-up. Exposures with values that change over time, or time-varying covariates, can be included in survival models by changing the unit of the analysis from the individual to the period of time when the exposure is constant. This breaks up the person-time of individuals into intervals that each person contributes to the risk set of “exposed” and “unexposed” for that covariate. The main assumption of including a time-varying covariate in this way is that theeffect of the time-varying covariate does not depend on time.

For a Cox proportional hazard model, the inclusion of a time-varying covariate would take the form of: h(t) = h0(t)e^β1x1(t). Time-varying covariates can also be included in parametric models, though it is a little more complicated and difficult to interpret. Parametric models can also model time-varying covariates using splines for greater flexibility.

Generally time-varying covariates should be used when it is hypothesized that the hazard depends more on later values of the covariate than the value of the covariate at baseline. Challenges that arise with time-varying covariates are missing data on the covariate at different time points, and a potential bias in estimation of the hazard if the time-varying covariate is actually a mediator.

**What is competing risks analysis?**

Traditional survival analysis methods assume that only one type of event of interest occurs. However, more advanced methods exist to allow the investigation of several types of events in the same study, such as death from multiple causes. Competing risks analysis is used for these studies in which the survival duration is ended by the first of several events. Special methods are needed because analyzing the time to each event separately can be biased. Specifically in this context, the KM method tends to overestimate the proportion of subjects experiencing events. Competing risks analysis utilizes the cumulative incidence method, in which the overall event probability at any time is the sum of the event-specific probabilities. The models are generally implemented by entering each study participant several times – one per event type. For each study participant, the time to any event is censored on the time at which the patient experienced the first event. For more information, please see the advancedepidemiology.org page on [competing risks](http://www.advancedepidemiology.org/?p=331).

**What are frailty models and why are they useful for correlated data?**

Correlated survival data can arise due to recurrent events experienced by an individual or when observations are clustered into groups. Either due to lack of knowledge or for feasibility, some covariates related to the event of interest may not be measured. Frailty models account for the heterogeneity caused by unmeasured covariates by adding random effects, which act multiplicatively on the hazard function. Frailty models are essentially extensions of the Cox model with the addition of random effects. Although there are various classification schemes and nomenclature used to describe these models, four common types of frailty models include shared, nested, joint, and additive frailty.

**Are there other approaches to analyzing recurrent event data?**

Recurrent event data are correlated since multiple events may occur within the same subject. While frailty models are one method to account for this correlation in recurrent event analyses, a more simple approach that can also account for this correlation is the use of robust standard errors (SE). With the addition of robust SEs, recurrent event analysis can be done as a simple extension of either semi-parametric or parametric models.

Although simple to implement, there are multiple ways to model recurrent event data using robust SEs. These approaches differ in how they define the risk set for each recurrence. In this way, they answer slightly different study questions, so the choice of which modeling approach to use should be based on the study hypothesis and the validity of the modeling assumptions.

The counting process, or Andersen-Gill, approach to recurrent event modeling assumes that each recurrence is an independent event, and does not take the order or type of event into account. In this model, follow-up time for each subject starts at the beginning of the study and is broken into segments defined by events (recurrences). Subjects contribute to the risk set for an event as long as they are under observation at that time (not censored). These models are simple to fit as a Cox model with the addition of a robust SE estimator, and hazard ratios are interpreted as the effect of the covariate on the recurrence rate over the follow-up period. This model would be inappropriate, however, if the independence assumption is not reasonable.

Conditional approaches assume that a subject is not at risk for a subsequent event until a prior event occurs, and hence take the order of events into account. They are fit using a stratified model, with the event number (or number of recurrence, in this case), as the strata variable and including robust SEs. There are two different conditional approaches that use different time scales, and hence have different risk sets. The conditional probability approach uses the time since the beginning of the study to define the time intervals, and is appropriate when the interest is in the full course of the recurrent event process. The gap time approach essentially “resets the clock” for each recurrence by using the time since the previous event to define time intervals, and is more appropriate when event (or recurrence)-specific effect estimates are of interest.

Finally, marginal approaches (also known as the WLW – Wei, Lin and Weissfeld – approach) consider each event to be a separate process, so subjects are at risk for all events from the start of follow-up, regardless of whether they experienced a prior event. This model is appropriate when the events are thought to result from different underlying processes, so that a subject could experience a 3rd event, for example, without experiencing the 1st. Although this assumption seems implausible with some types of data, like cancer recurrences, it could be used to model injury recurrences over a period of time, when subjects could experience different types of injuries over the time period that have no natural order. Marginal models can also be fit using stratified models with robust SEs.

## Readings

This project aimed to describe the methodological and analytic decisions that one may face when working with time-to-event data, but it is by no means exhaustive. Resources are provided below to delve deeper into these topics.

### Textbooks & Chapters

Vittinghoff E, Glidden DV, Shiboski SC, McCulloch CE (2012). Regression Methods in Biostatistics, 2nd New York, NY: Springer.

Introductory text to linear, logistic, survival, and repeated measures models, best for those who want a basic starting point.

Survival analysis chapter provides a good overview but not depth. Examples are STATA-based.

Hosmer DW, Lemeshow S, May S. (2008) Applied Survival Analysis: Regression Modeling of Time-to-Event Data, 2nd ed. Hoboken, NJ: John Wiley & Sons, Inc.

In-depth overview of non-parametric, semi-parametric and parametric Cox models, best for those that are knowledgeable in other areas of statistics. Advanced techniques are not covered in depth, but references to other specialty textbooks are provided.

Kleinbaum DG, Klein M (2012). Survival Analysis: A Self-Learning Text, 3rd ed. New York, NY: Springer Science + Business Media, LLC

Excellent introductory text

Klein JP, Moeschberger ML (2005). Survival Analysis: Techniques for Censored and Truncated Data, 2nd ed. New York, NY: Springer Science + Business Media, LLC

designed for graduate students, this book provides many practical examples

Therneau TM, Grambsch PM (2000). Modeling Survival Data: Extending the Cox Model. New York, NY: Springer Science + Business Media, LLC

Good introduction to counting process approach and analyzing correlated survival data. The author also wrote the “survival” package in R

Allison PD (2010). Survival Analysis Using SAS: A Practice Guide, 2nd ed. Cary, NC: SAS Institute

A great applied text for SAS users

Bagdonavicius V, Nikulin M (2002). Accelerated Life Models: Modeling and Statistical Analysis.Boca Raton, FL: Chapman & Hall/CRC Press.

Good resource for more information on parametric and semi-parametric accelerated failure time models and how they compare to proportional hazard models

### Methodological Articles

**Introductory/Overview Articles**

Hougaard P (1999). Fundamentals of Survival Data. Biometrics 55(1): 13-22. PMID:[11318147](http://www.ncbi.nlm.nih.gov/pubmed/11318147).

Clark TG, Bradburn MJ, Love SB, Altman DG (2003). Survival analysis part I: basic concepts and first analyses. Br J Cancer 89(2): 232-8. PMID: [12865907](http://www.ncbi.nlm.nih.gov/pubmed/?term=12865907)

Clark TG, Bradburn MJ, Love SB, Altman DG (2003). Survival analysis part II: multivariate data analysis–an introduction to concepts and methods. Br J Cancer 89(3): 431-6. PMID:[1288808](http://www.ncbi.nlm.nih.gov/pubmed/?term=12888808)

Clark TG, Bradburn MJ, Love SB, Altman DG (2003). Survival analysis part II: multivariate data analysis–choosing a model and assessing its adequacy and fit. Br J Cancer 89(4): 605-11. PMID: [12951864](http://www.ncbi.nlm.nih.gov/pubmed/?term=12915864)

Clark TG, Bradburn MJ, Love SB, Altman DG (2003). Survival analysis part IV: further concepts and methods in survival analysis. Br J Cancer 89(5): 781-6. PMID: [12942105](http://www.ncbi.nlm.nih.gov/pubmed/?term=12942105)

The series of four articles above is an excellent introductory overview of methods in survival analysis that is extremely well-written and easy to understand – it’s highly recommended.

**Age as time scale**

Korn EL, Graubard BI, Midthune D (1997). Time-to-event analysis of longitudinal follow-up of a survey: choice of the time-scale. Am J Epidemiol 145(1):72-80. PMID: [8982025](http://www.ncbi.nlm.nih.gov/pubmed/?term=8982025)

Paper advocating the use of age as the time scale rather than time on study.

Ingram DD, Makuc DM, Feldman JJ (1997). Re: “Time-to-event analysis of longitudinal follow-up of a survey: choice of the time-scale”. Am J Epidemiol 146(6):528-9. PMID:[9290515](http://www.ncbi.nlm.nih.gov/pubmed/?term=9290515).

Comment on the Korn paper describing precautions to take when using age as the time scale.

Thiébaut AC, Bénichou J (2004). Choice of time-scale in Cox’s model analysis of epidemiologic cohort data: a simulation study. Stat Med 30;23(24):3803-20. PMID:[15580597](http://www.ncbi.nlm.nih.gov/pubmed/?term=15580597)

Simulation study showing the magnitude of bias for different degrees of association between age and the covariate of interest when using time on study as the time scale.

Canchola AJ, Stewart SL, Bernstein L, et al. Cox regression using different time-scales. Available at: <http://www.lexjansen.com/wuss/2003/DataAnalysis/i-cox_time_scales.pdf>.

A nice paper comparing 5 Cox regression models with variations on either time on study or age as the time-scale with SAS code.

**Censoring**

Huang CY, Ning J, Qin J (2015). Semiparametric likelihood inference for left-truncated and right-censored data. Biostatistics [epub] PMID: [25796430](http://www.ncbi.nlm.nih.gov/pubmed/?term=25796430).

This paper has a nice introduction to the analysis of censored data and provides a new estimation procedure for the survival time distribution with left-truncated and right-censored data. It is very dense and has an advanced statistical focus.

Cain KC, Harlow SD, Little RJ, Nan B, Yosef M, Taffe JR, Elliott MR (2011). Bias due to left truncation and left censoring in longitudinal studies of developmental and disease processes. Am J Epidemiol 173(9):1078-84. PMID: [21422059](http://www.ncbi.nlm.nih.gov/pubmed/?term=21422059).

An excellent resource that explains the bias inherent in left-censored data from an epidemiologic perspective.

Sun J, Sun L, Zhu C (2007). Testing the proportional odds model for interval-censored data.Lifetime Data Anal 13:37–50. PMID [17160547](http://www.ncbi.nlm.nih.gov/pubmed/?term=17160547).

Another statistically dense article on a nuanced aspect of TTE data analysis, but provides a good explanation of interval-censored data.

Robins JM (1995a) An analytic method for randomized trials with informative censoring: Part I. Lifetime Data Anal 1: 241–254. PMID [9385104](http://www.ncbi.nlm.nih.gov/pubmed/?term=9385104).

Robins JM (1995b) An analytic method for randomized trials with informative censoring: Part II. Lifetime Data Anal 1: 417–434. PMID [9385113](http://www.ncbi.nlm.nih.gov/pubmed/?term=9385113).

Two papers that discuss methods for dealing with informative censoring.

**Non-parametric survival methods**

Borgan Ø (2005) Kaplan-Meier Estimator. Encyclopedia of Biostatistics DOI: 10.1002/0470011815.b2a11042

Excellent overview of the Kaplan-Meier estimator and its relationship to the Nelson-Aalen estimator

Rodríguez G (2005). Non-Parametric Estimation in Survival Models. Available from:<http://data.princeton.edu/pop509/NonParametricSurvival.pdf>

Introduction to non-parametric methods and the Cox proportional hazard model that explains the relationships between methods with the mathematical formulas

Cole SR, Hernan MA (2004). Adjusted survival curves with inverse probability weights.Comput Methods Programs Biomed 75(1): 35-9. PMID: [15158046](http://www.ncbi.nlm.nih.gov/pubmed/15158046)

Describes the use of IPW to create adjusted Kaplan-Meier curves. Includes an example and SAS macro.

Zhang M (2015). Robust methods to improve efficiency and reduce bias in estimating survival curves in randomized clinical trials. Lifetime Data Anal 21(1): 119-37. PMID:[24522498](http://www.ncbi.nlm.nih.gov/pubmed/24522498)

Proposed method for covariate-adjusted survival curves in RCTs

**Semi-parametric survival methods**

Cox DR (1972) Regression models and life tables (with discussion). J R Statist Soc B 34: 187–220.

The classic reference.

Christensen E (1987) Multivariate survival analysis using Cox’s regression model.Hepatology 7: 1346–1358. PMID [3679094](http://www.ncbi.nlm.nih.gov/pubmed/?term=3679094).

Describes the use of the Cox model using a motivating example. Excellent review of the key aspects of Cox model analysis, including how to fit a Cox model and checking of model assumptions.

Grambsch PM, Therneau TM (1994) Proportional hazards tests and diagnostics based on weighted residuals. Biometrika 81: 515–526.

An in-depth paper on testing the proportional hazards assumption. Good mix of theory and advanced statistical explanation.

Ng’andu NH (1997) An empirical comparison of statistical tests for assessing the proportional hazards assumption of Cox’s model. Stat Med 16: 611–626. PMID [9131751](http://www.ncbi.nlm.nih.gov/pubmed/?term=9131751).

Another in-depth paper on testing the proportional hazards assumption, this one includes discussion of checking residuals and effects of censoring.

**Parametric survival methods**

Rodrίguez, G (2010). Parametric Survival Models. Available from:<http://data.princeton.edu/pop509/ParametricSurvival.pdf>

brief introduction to the most common distributions used in parametric survival analysis

Nardi A, Schemper M (2003). Comparing Cox and parametric models in clinical studies.Stat Med 22 (23): 2597-610. PMID: [14652863](http://www.ncbi.nlm.nih.gov/pubmed/14652863)

Provides good examples comparing semi-parametric models with models using common parametric distributions and focuses on assessing model fit

Royston P, Parmar MK (2002). Flexible parametric proportional-hazards and proportional-odds models for censored survival data, with application to prognostic modelling and estimation of treatment effects. Stat Med 21(15): 2175-97. PMID: [12210632](http://www.ncbi.nlm.nih.gov/pubmed/?term=12210632)

Good explanation for basics of proportional hazards and odds models and comparisons with cubic splines

Cox C, Chu H, Schneider MF, Muñoz A (2007). Parametric survival analysis and taxonomy of hazard functions for the generalized gamma distribution. Statist Med 26:4352–4374. PMID [17342754](http://www.ncbi.nlm.nih.gov/pubmed/?term=17342754).

Provides an excellent overview of parametric survival methods, including a taxonomy of the hazard functions and an in-depth discussion of the generalized gamma distribution family.

Crowther MJ, Lambert PC (2014). A general framework for parametric survival analysis.Stat Med 33(30): 5280-97. PMID: [25220693](http://www.ncbi.nlm.nih.gov/pubmed/?term=25220693)

Describes restrictive assumptions of commonly used parametric distributions and explains restricted cubic spline methodology

Sparling YH, Younes N, Lachin JM, Bautista OM (2006). Parametric survival models for interval-censored data with time-dependent covariates. Biometrics 7 (4): 599-614. PMID:[16597670](http://www.ncbi.nlm.nih.gov/pubmed/16597670)

Extension and example of how to use parametric models with interval-censored data

**Time-Varying Covariates**

Fisher LD, Lin DY (1999). Time-dependent covariates in the Cox proportional-hazards regression model. Annu Rev Public Health 20: 145-57. PMID: [10352854](http://www.ncbi.nlm.nih.gov/pubmed/10352854)

Thorough and easy to understand explanation of time-varying covariates in Cox models, with a mathematical appendix

Petersen T (1986). Fitting parametric survival models with time-dependent covariates. Appl Statist 35(3): 281-88.

Dense article, but with a useful applied example

**Competing risk analysis**

See [Competing Risks](/research/population-health-methods/competing-risk-analysis)

Tai B, Machin D, White I, Gebski V (2001) Competing risks analysis of patients with osteosarcoma: a comparison of four different approaches. Stat Med 20: 661–684. PMID[11241570](http://www.ncbi.nlm.nih.gov/pubmed/?term=11241570).

Good in-depth paper that describes four different methods of analysing competing risks data, and uses data from a randomized trial of patients with osteosarcoma to compare these four approaches.

Checkley W, Brower RG, Muñoz A (2010). Inference for mutually exclusive competing events through a mixture of generalized gamma distributions. Epidemiology 21(4): 557–565. PMID [20502337](http://www.ncbi.nlm.nih.gov/pubmed/?term=20502337).

Paper on competing risks using the generalized gamma distribution.

**Analysis of clustered data and frailty models**

Yamaguchi T, Ohashi Y, Matsuyama Y (2002) Proportional hazards models with random effects to examine centre effects in multicentre cancer clinical trials. Stat Methods Med Res 11: 221–236. PMID [12094756](http://www.ncbi.nlm.nih.gov/pubmed/?term=12094756).

A paper with excellent theoretical and mathematical explanation of taking clustering into account when analyzing survival data from multi-center clinical trials.

O’Quigley J, Stare J (2002) Proportional hazards models with frailties and random effects. Stat Med 21: 3219–3233. PMID [12375300](http://www.ncbi.nlm.nih.gov/pubmed/?term=12375300).

A head-to-head comparison of frailty models and random effects models.

Balakrishnan N, Peng Y (2006). Generalized gamma frailty model. Statist Med 25:2797–2816. PMID

A paper on frailty models using the generalized gamma distribution as the frailty distribution.

Rondeau V, Mazroui Y, Gonzalez JR (2012). frailtypack: An R Package for the Analysis of Correlated Survival Data with Frailty Models Using Penalized Likelihood Estimation or Parametrical Estimation. Journal of Statistical Software 47(4): 1-28.

R package vignette with good background information on frailty models.

Schaubel DE, Cai J (2005). Analysis of clustered recurrent event data with application to hospitalization rates among renal failure patients. Biostatistics 6(3):404-19. PMID[15831581](http://www.ncbi.nlm.nih.gov/pubmed/?term=15831581).

Excellent paper in which the authors present two methods to analyze clustered recurrent event data, and then they compare results from the proposed models to those based on a frailty model.

Gharibvand L, Liu L (2009). Analysis of Survival Data with Clustered Events. SAS Global Forum 2009 Paper 237-2009.

Succinct and easy to understand source for analysis of time to event data with clustered events with SAS procedures.

**Recurrent Event Analysis**

Twisk JW, Smidt N, de Vente W (2005). Applied analysis of recurrent events: a practical overview. J Epidemiol Community Health 59(8): 706-10. PMID: [16020650](http://www.ncbi.nlm.nih.gov/pubmed/?term=16020650)

Very easy to understand introduction to recurrent event modeling and the concept of risk sets

Villegas R, Juliá O, Ocaña J (2013). Empirical study of correlated survival times for recurrent events with proportional hazards margins and the effect of correlation and censoring.BMC Med Res Methodol 13:95. PMID: [23883000](http://www.ncbi.nlm.nih.gov/pubmed/?term=23883000)

Uses simulations to test the robustness of different models for recurrent event data

Kelly PJ, Lim LL (2000). Survival analysis for recurrent event data: an application to childhood infectious diseases. Stat Med 19 (1): 13-33. PMID: [10623190](http://www.ncbi.nlm.nih.gov/pubmed/10623910)

Applied examples of the four main approaches for modeling recurrent event data

Wei LJ, Lin DY, Weissfeld L (1989). Regression analysis of multivariate incomplete failure time data by modeling marginal distributions. Journal of the American Statistical Association84 (108): 1065-1073

The original article describing marginal models for recurrent event analysis

## Courses

Epidemiology and Population Health Summer Institute at Columbia University (EPIC)

An [online course on survival analysis](http://reg.abcsignup.com/reg/event_page.aspx?ek=0013-0020-16bba0bbf094486ca786f0e95954df00) is offered in June

Statistical Horizons, private provider of speciality statistical seminars taught by experts in the field

5-day seminar on event history and survival analysis offered July 15-19, 2015 in Philadelphia, taught by Paul Allison. No previous knowledge of survival analysis is necessary. For more information, see <http://statisticalhorizons.com/seminars/public-seminars/eventhistory13>

Inter-university Consortium for Political and Social Research (ICPSR) Summer Program in Quantitative Methods of Social Research, part of the Institute for Social Research at the University of Michigan

3-day seminar on survival analysis, event history modeling and duration analysis offered June 22-24, 2015 in Berkeley, CA, taught by Tenko Raykov of Michigan State University. Comprehensive overview of survival methods across disciplines (not solely public health): <http://www.icpsr.umich.edu/icpsrweb/sumprog/courses/0200>

Institute for Statistics Research offers two online courses for survival analysis, offered multiple times a year. These courses are based from the Applied analysis textbook by Klein and Kleinbaum (see below) and can be taken a la carte or as part of a certificate program in Statistics:

Introduction to survival analysis, with a focus on semi-parametric Cox models, taught by David Kleinbaum or Matt Strickland: <http://www.statistics.com/survival/>

Advanced survival analysis, including parametric models, recurrence analysis and frailty models, taught by Matt Strickland: <http://www.statistics.com/survival2/>

The Institute for Digital Research and Education at UCLA offer what they call seminars through their website for survival analysis in different statistical software. These seminars demonstrate how to conduct applied survival analysis, focusing more on code than theory.

Survival analysis in SAS:<http://www.ats.ucla.edu/stat/sas/seminars/sas_survival/default.htm>

Survival analysis in STATA:<http://www.ats.ucla.edu/stat/stata/seminars/stata_survival/>

The UCLA website also provides examples from the Hosmer, Lemeshow & May survival analysis textbook (see below) in SAS, STATA, SPSS and R:<http://www.ats.ucla.edu/stat/spss/examples/asa2/>

## Join the Conversation

Have a question about methods? Join us on Facebook

## Columbia University Mailman School of Public Health

## Follow Us

We are committed to the well-being and success of all community members. Columbia complies with all applicable civil rights laws and does not engage in illegal preferences or discrimination.
