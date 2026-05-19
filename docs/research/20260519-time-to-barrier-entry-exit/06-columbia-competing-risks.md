[Skip to content](#cb-content__main)

![Columbia University Mailman School of Public Health](https://www.publichealth.columbia.edu/sites/default/files/logo-mailman-blue-horizontal.svg?td2hfs)

## [About Us](/about-us)

## [Events](/about-us/events)

## News

![](data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)

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

![](data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)

Meet the faculty of the Mailman School of Public Health.

## [Become a Student](/become-student)

## [Life and Community](/become-student/life-community)

## How to Apply

![](data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)

Learn how to apply to the Mailman School of Public Health.

## [Info For](/info)

# Competing Risk Analysis

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

## Overview

Competing risk analysis refers to a special type of survival analysis that aims to correctly estimate marginal probability of an event in the presence of competing events. Traditional methods to describe survival process, such Kaplan Meier product-limit method, are not designed to accommodate the competing nature of multiple causes to the same event, therefore they tend to produce inaccurate estimates when analyzing the marginal probability for cause-specific events. As an work-around, Cumulative Incidence Function (CIF) was proposed to solve this particular issue by estimating the marginal probability of a certain event as a function of its cause-specific probability and overall survival probability. This method hybridizes the idea of product-limit approach and the idea of competing causal pathways, which provides a more interpretable estimate for the survival experience of multiple competing events for a group of subjects. Like many analyses, the competing risk analysis includes a non-parametric method which involves the use of a modified Chi-squared test to compare CIF curves between groups, and a parametric approach which model the CIF based on a subdistribution hazard function.

## Description

**1. What is “competing event” and “competing risk”?**

In standard survival data, subjects are supposed to experience only one type of event over follow-up, such as death from breast cancer. On the contrary, in real life, subjects can potentially experience more than one type of a certain event. For instance, if mortality is of research interest, then our observations – senior patients at an oncology department, could possibly die from heart attack or breast cancer, or even traffic accident. When only one of these different types of event can occur, we refers to these events as “competing events”, in a sense that they compete with each other to deliver the event of interest, and the occurrence of one type of event will prevent the occurrence of the others. As a result, we call the probability of these events as “competing risks”, in a sense that the probability of each competing event is somehow regulated by the other competing events, which has an interpretation suitable to describe the survival process determined by multiple types of events.

To better understand the competing event scenario, consider the following examples:

1) A patient can die from breast cancer or from stroke, but he cannot die from both;
2) A breast cancer patient may die after surgery before they can develop hospital infection;
3) A soldier may die during a combat or in a traffic accident.

In the examples above, there are more than one pathway that a subject can fail, but the failure, either death or infection, can only occur once for each subject (without considering recurring event). Therefore, the failures caused by different pathways are mutually exclusive and hence called competing events. Analysis of such data requires special considerations.

**2. Why shouldn’t we use Kaplan Meier estimator?**

Like in standard survival analysis, the analytical object for competing event data is to estimate the probability of one event among the many possible events over time, allowing the subjects to fail from competing events. In the above examples, we might want to estimate the breast cancer mortality rate over time, and want to know whether the mortality rate of breast cancer differ between two or more treatment groups, with or without adjustment of covariates. In standard survival analysis these questions can be answered by using Kaplan Meier product limit method to obtain event probability over time, and Cox proportional hazard model to predict such probability. Likewise, in competing event data, the typical approach involves the use of KM estimator to separately estimate probability for each type of event, while treating the other competing events as censored in addition to those who are censored from loss to follow-up or withdrawal. This method of estimating event probability is called cause-specific hazard function, which is mathematically expressed as:

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAFCAYAAAA3zK6FAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACAUlEQVQokZ2Sv4vaYBzGv8YQBDUoJioqWIOWog7lPKoiSCnB0a2jo7uDYCGu4qyD/4BugQPRSZyKi6AHOkhsNeAPpEiMx6W8r1z07HpDodhnfB4e+MDzGOA/xPN8OBaL3bMsK6uqSnEcN5Jl+X0qlZI7nQ4fCAR2pVJp0Gg0PBhjcj6f0+l0ek/TNJPNZmeiKLr7/X6UYRjQdf28Wq1onudnDodjN51Ow3a7fbHf7++v16tKCILgAQBotVq+drttq9Vqzrcw1WrVU6/Xmbcey7Kc1+vtIYQIq9Vq2u12FMuyn7fbLYEQejEajajX69koigqTJAk0TdMMw7zOZrNoLpezjUajj8fjMWw2m02SJO3tdjupaRpDEARJEMQdxthisVgojDFpKBaL3xKJRGMwGIQB4J2maT8QQmtd1z0cx0miKHKCIHySZdkdCAQW+Xz+AQA8AEDF43HbcDh8AgCgaZoMhUKm8Xj8Ox6PM8vl8klRlPO/1nC5XDZVVZ+TyaRT07TnzWZzVhTlBQAgk8k4DYIg3Pl8vg+Xy0WiKOqEEKKGw6Gk67qF4zj1cDhEI5GIe7lcnoLBIGEwGKRCofDrlkuIoujsdrtMKBR6LZfL0i1dslKpPALA41+y02KxIJrN5tf1ev3T7/d/RwhlMcYEANwEOJlMvmCMufP5rADATYB/AMrK6FCS4yLWAAAAAElFTkSuQmCC)

The random variable Tc denotes the time to failure from event type c, therefore the cause-specific hazard function hc(t) gives the instantaneous failure rate at time t from event type c, given not failing from event c by time t.

Correspondingly, there is a cause-specific hazard model based on the Cox proportional hazard model which has the form of:

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAJCAYAAABADm7+AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACoElEQVQ4jb2ST0jbYBiH33Yx1dmEEEqsYZZsk0GzHGapsolD28ModDIPO0iFDmGnXAZjsxTEg8UKFimIsGN3KttBpA1K8A9KCb1sbjJRKU0Ve7BFWqmzXWsbw06OMUQ9OH+nj5fnefnx8gHccGZnZ42jo6Ofr8pr/2eZ8yLLMpLL5d5fWYhGo8jZe3l52XAeEwqF9P/OhoaGtGtra3/cWCyGz8zMIOexZ7vb2tp8LMv2YRjG2e321xMTE9aLuoVCIf0ts9n8trm5eX1jY6NmNpvt7e3tXZIkfY9EIjhN036Hw1HJ5XJ3Y7FY6m+5s7PzRaFQ0IqieAAA0NLS8nR3d/cRiqIMRVFZj8dzp7e3l3Y4HKTT6SQSiQTLMEw4k8m8CwaDH8fHx78sLi7uS5LEmkymV6urq3EAgIGBAZ7n+Yf9/f07yWTyCZLJZBSO49yiKK6PjY3td3d3m+bm5gwnJyfo8fFxkeO4r6IoWg4PDxGe5+2KopA0TS+Vy+XbhULh+cjISF9TU9PS9vY2gqJo/d7e3jej0eglSTIZj8cNFEWpiUQCAODH9PT0L6fTKUQikVYA2AIAKJVKeENDQ2FycvKZwWCQT09PdwRBIG02G5tOp6sIhmGftFptBwBkBwcHWxEEmc/n8+zKykq2Wq1+CIfD9S6Xq54kSQUAFs4uODw8PE9RFJnNZl9WKhXKYrH8VBRF0ul0rTqdLlgulwmGYdDNzc3HNptt6ejo6J7X62UIggCPx7MVCAT0GIYxGo0Gb2xsjJZKpTd1dXVZQRDWa7Uarqrqg56enormoj9w3XG73a5UKqXSNE0Ui8X7Vqs14PP5Di5ybrTg1NQUoaoqIcvyAY7jXX6/f+EyB7kMuM7k83mTXq/vAIB9FEXJqzi/ARx6EsYQ9QOpAAAAAElFTkSuQmCC)

This proportional hazard model of event type c at time t allows effects of the covariates to differ by event types, as the subscripted beta coefficient suggests.

Using these methods, one can separately estimate failure rate for each one of competing events. For instance, in our breast cancer mortality example, when death from breast cancer is the event of interest, the death from heart attack and all other causes should be treated as censored in addition to conventional censored observations. This would allow us to estimate the cause-specific hazard for breast cancer mortality rate, and go on to fit a cause-specific hazard model on breast cancer mortality. The same procedure can apply to death from heart attack when it becomes event of interest.

A major caveat of the cause-specific approach is that it still assumes independent censoringfor subjects who are not actually censored but failed from competing events, as for standard censorship such as loss to follow up. Suppose this assumption is true, when focusing on cause-specific death rate from breast cancer, then any censored subject at time t would have the same death rate from breast cancer, regardless of whether the reason for censoring is either CVD or other cause of death, or loss to follow-up. This assumption is equivalent to sayingcompeting events are independent, which is the foundation for the KM type of analysis to be valid. However, there is no way to explicitly test whether this assumption is satisfied for any given dataset. For instance, we can never determine whether a subject who died from heart attack would have died from breast cancer if he did not die from heart attack, since the possible death from cancer is unobservable for subjects died from heart attack. Therefore, estimates from cause-specific hazard function do not have an informative interpretation since it relies heavily on the independence censoring assumption.

**3. What’s the solution?**

Up to date, the most popular alternative approach to analyze competing event data is called theCumulative Incidence Function (CIF), which estimates the marginal probability for each competing event. Marginal probability is defined as the probability of subjects who actually developed the event of interest, regardless of whether they were censored or failed from other competing events. In the simplest case, when there is only one event of interest, the CIF should equal the (1-KM) estimate. When there are competing events, however, the marginal probability of each competing events can be estimated from CIF, which is derived from the cause-specific hazard as we discussed previously. By definition, the marginal probability does not assume the independence of competing events, and it has an interpretation that is more relevant to clinician in cost-effectiveness analyses in which risk probability is used to assess treatment utility.

**3.1 Cumulative Incidence Function (CIF)**

The construction of a CIF is as straight forward as the KM estimate. It is a product of two estimates:

1) The estimate of hazard at ordered failure time tf for event-type of interest, expressed as:

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAICAYAAACLUr1bAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABR0lEQVQ4jc3TzUtbQRQF8B+vMUgqMUi/kKAhlhCkuLGVYotIliLBlX9xF8Wlq6CbLopIKYGWIkXa0sU7wWdI2lI3HhjenXPv3I8z8+A5XrrHaGZN48mc+Hn8XdCd5yjQw4spfgWPYg+nfIt/SvifmDv0A7zFJzzEOPw2zvEUA5zgZ3xf8AZn2e9gA+t4jIvwu1hGP98FfJ3RQxtXaOBVal7iF6WCrSTtVA418Q01vMO1UrV+/LVK7AinWaNwBZ5l8F64qkpL2I+9hg/J2ci+UN7UoMB3bKXrHeV1XydgNXYtinxM0h+VYqsZrhNbpq9FmXGa/IzX2EydC7fRw/vUbaWn8WSaxXyHyvfXzoF6eDioKLHp71iKEo2sJg6Tf5CabaViEiPNFdgz4+etu7m+ToXvZ2pJWvxDg7MwUeco+67bz6Uadwy/AeWpLPUuCyL3AAAAAElFTkSuQmCC)

where the mcf denotes the number of events for risk c at time tf and nf is the number of subjects at that time.

2) The estimate of overall probability of surviving previous time (td-1):

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAQCAYAAABk1z2tAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACOklEQVRIic3Wz4uNURgH8E/v3KTpdo3bJCSmyWKS0PiRhZWFJElSIiu/FtZSysaSDX+IsmKFBaOsJGExCylM40d+XGOMwWXxnNs993Vxy4hvvZ3znOe853zP83zP8759OjGCQ3iDl/4D9GX9xViF6xjCW3z8B5z+CCsx7y/vUcXyllHJHDVsSW0F46l/NflXYxCPS+9AYw4JzmIzmniaEz0hNEhE6Sz2JLuO4xgoLXYSe+eQXAv9OI1qkQZGsFBEjTjFNdxL9jJMC13m2IhHf4HgNCYw2iLYL9K7OZt0WzvE2/Ew863DMaHJDeKCzTWeYlXrFj/HIhzBUSzBGGaS/wAuiZPBK6xI9gW8x7c5JrgAGwoUQpDnsB+nROq2ZpMH8Dqzv2A9bgk5NDNfRUR3Rw8kClHStqV+jin0F0J/y9ImL0TkLou05wvldh3DuKOzEsDBdJi7PRBcjF3Y1IVggWaBnViaOWrJvpGNNbRLSovgdHpGM5JD2JfGeyk9EyIg3VDDy4rQ27BIY5HaiyKaLTwQF2Ii2bOpP4pJ7RS/FuK+kuxBrNFZ3JuiOkz+hnwNkxWcEZqqJseMH8vJmEjDmHYBPZ/6jYzg0tLGDdz3Y/rK63fDEG5XsslTv5g8LkpQXdzgZmrLWIRnmT2rMxNlDIosrBVfqpZu6yKT4z95ryuWC72WLwURoWHsFjWzVxQicwPaMpgvvk5VOv9mfod3Itqf8LXk68NhfMZNfOhxzW8iyjPZmvPwJO3nO/Xoe+g3saxPAAAAAElFTkSuQmCC)

where S(t) denotes the overall survival function rather than the cause specific survival function. The reason why we have to take overall survival into consideration is simple yet important: a subject must have survived all other competing events in order to fail from event type c at timetf.

With these two estimates, we can compute the estimated incidence probability of failing from event-type c at time tf as:

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAFCAYAAAA3zK6FAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA4UlEQVQokY3RMUsDQRAF4I8lhCMEkRAkhHDIISFYiIWI+P9/hJW1RYogFiIiFnlH1oMLvmZnZue9eTsLU7ROKCPxEAXdP/rOoc38sXmlYIL7FDYh7JI3/pqvscIPtjG6G+kr6akN9GeHr8SXWAx0tgVrvKRwFYNdzE1Tg+uQV8kneMiwPW4H/TIQLqr8ucrn0ej1D9Ep0ZkX3FUXMMNr6p/4Hq4kWOZhH3nMW0x3efQycak0Ct7TJ5yZ4w/2tb3jrzX17CabWYQAT4n7LZzDJudNjPVoo7E+wy3hN07bf+zrv5MpGA8x/PxvAAAAAElFTkSuQmCC)

The equation is self-explanatory: the probability of failing from event type c at time tf is simply the product of surviving the previous time periods and the cause specific hazard at time tf.

The CIF for event type c at time tf is then the cumulative sum up to time tf (i.e., from f’=1 to f’=f) of these incidence probabilities over all event type c failure times, which is expressed as:

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAGCAYAAACxWNwrAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA9UlEQVQokZXSO08CURCG4QfxhhoUg6jRGC8FhY2Fra1/3d6foMbCkKDiiiywWuyYbFCW7DRnd+Y9M9/MGarZMo4r8KcV8/+xegV2F12MsIopMnz/wzZxiSHWkaIW/DxbwhomswJvcRZnhgQXGKAdvk30cYM7fIbYYYHtYBziXgtsgnPsYTvu/grqxP9+NHoS/kN84KgegT7ecI+DCLZiWmk08hUCemjEvWYU2In4CCshvMhmkSeJ/IM4p+FrxHdd/jrv0VBaWzDy4pNs4SoEveCphN3AdTTaw0MJW1q/bAdnd6uNR/mOTKL4PLaFZ/kUxwvY0vo/jM5KxACmUGEAAAAASUVORK5CYII=)

As we mentioned before, the CIF is equivalent to 1-KM estimator when there is no competing event. When there is competing event, the CIF differs from 1-KM estimator in that it uses overall survival function S(t) that counts failures from competing events in addition to the event of interest, whereas the 1-KM estimator uses the event-type specific survival function Sc(t), which treats failures from competing events as censored.

By using the overall survival function, CIF bypasses the need to make unverifiable assumptions of independence of censoring on competing events. Since the S(t) is always less than Sc(t), in competing event data, the CIF is always smaller than 1-KM estimates, which means the 1-KM tends to overestimate the probability of failure from the event type of interest. Another advantage is that, by definition, the CIF of each competing event is a fraction of the S(t), therefore the sum of each individual hazard for all competing events should equal the overall hazard. This property of CIF makes it possible to dissect overall hazard, which has more practical interpretations.

**3.2 Non-parametric analysis**

[Gray (1988)](https://www.jstor.org/stable/2241622)proposed a non-parametric test to compare two or more CIFs. The test is analogous to the log-rank test comparing KM curves, using a modified Chi-squared test statistic. This test does not require the independent censoring assumption. Please read the [original article](https://www.jstor.org/stable/2241622)for details on how this test statistics is constructed.

**3.3 Parametric analysis**

[Fine and Gray (1999)](https://www.jstor.org/stable/2670170)proposed a proportional hazards model aims at modeling the CIF with covariates, by treating the CIF curve as a subdistribution function. The subdistribution function is analogous to the Cox proportional hazard model, except that it models a hazard function (as known as subdistribution hazard) derived from a CIF. The Fine and Gray subdistribution hazard function for event type c can be expressed as:

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAADCAYAAADhlU2YAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAlUlEQVQYlZXQzQqBYRAF4MfnwxeSLCRZWkouwf1fhqRYWEhKfjdHbCSnpnd+zpyZd2r+wwx79LDGHROskoMDKvQTD7BJvpnaHWXq+w/uCQWG2KGqY4EjuuhgHL8em2eJbUQueW8fwypcUUtPI1rn8M9Z7hHOyy+i1Up/lfxrRinkLtohNGMiMM2PRl+u+gsDLL0v/BeeZWAatFocP88AAAAASUVORK5CYII=)

The above function estimates the hazard rate for event type c at time t based on the risk set that remains at time t after accounting for all previously occurring event types, which includes competing events.

The CIF based proportional hazard model is then defined as:

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAICAYAAACLUr1bAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABE0lEQVQ4jcXTS0pDUQzG8V97a22ropWKRVRUxIEOBcFNuB7X58glCIoLECs+a63PQb9C8TmzgXBIvuTkf3O4hfHaHgrcjJnjR5v7q6DAPB5/0CvxOvqftN/6htbA8ze5Jg5ximUs4GKkZgmTqBbYxS16qAWoitkUtvAaoFLiHrbxjqfoZUylt4F29HaAmgGZTv05tnAUuFVMZBH7OEOzCEQFL9jItiaxjm5grpPrB+AhQDtYxB02k1/BGjoBvQ1YPXe9ZVYnH3eZrd1kfgX3Bs8/U4pYjb8kfhs5y/Ger1ZO3/CO7kjcNXiRYV8rMLVs8SBbbOAKx9H6I3Pnv5n5b1bJOWcA82vROGzDYNtlnPj6E4IPzKI5MUnwwM0AAAAASUVORK5CYII=)

This model satisfied the proportional hazard assumption for the subpopulation hazard being modeled, which means the general hazard ratio formula is essentially the same as for the Cox model, except a minor cosmetic difference that the betas in the Cox model is replaced by gammas in Fine and Gray’s model. Consequently, we should interpret the gammas in a similar way as we do for the betas estimated from a Cox model, except that it estimates the effect of certain covariates in the presence of competing events. The Fine and Gray model can also be extended to allow for time-dependent covariates.

Today, analysis of competing data using either non-parametric or parametric method is available in the major statistical packages including R, STATA and SAS.

## Readings

### Textbooks & Chapters

J. D. Kalbfleisch, and Ross L. Prentice, ‘Competing Risks and Multistate Models’, in The Statistical Analysis of Failure Time Data (Hoboken, N.J.: J. Wiley, 2002), pp. 247-77.
The idea of CIF was first proposed in this book. It gives you a convincing rationale as to why you can’t analyze competing data using Kaplan Meier method.

David G. Kleinbaum, and Mitchel Klein, ‘Competing Risks Survival Analysis’, in Survival Analysis : A Self-Learning Text (New York: Springer, 2012), pp. 425-95.
This entire page borrowed heavily from this awesome chapter by Kleinbaum & Klein, I highly recommend it! P.S. I highly recommend all statistical textbooks by Kleinbaum in general.

Bob Gray (2013). cmprsk: Subdistribution Analysis of Competing Risks. R package version 2.2-6. <https://cran.r-project.org/web/packages/cmprsk/index.html>
This is the R package “cmprsk” user manual, it provides human being friendly guidance on how to implement those functions.

“stcrreg — Competing-risks regression”, StataCorp. 2013. Stata 13 Base Reference Manual. College Station, TX: Stata Press.
This is the STATA user manual, I know very little about it but seems to be informative to skilled STATA users.

“Proportional Subdistribution Hazards Model for Competing-Risks Data”, SAS Institute Inc. 2013. SAS/STAT® 13.1 User’s Guide: pp5991-5995. Cary, NC: SAS Institute Inc.
This is one of those SAS forum papers that describes how to analyze competing risk using PROC PHREG in SAS. Very detailed and useful.

### Methodological Articles

Prentice, Ross L., et al. “The analysis of failure times in the presence of competing risks.” Biometrics (1978): 541-554.
This paper is very similar to the book chapter by Kalbfleisch and Prentice, probably they are the same paper.

Gray, Robert J. “A class of K-sample tests for comparing the cumulative incidence of a competing risk.” The Annals of statistics (1988): 1141-1154.
This is the paper that proposed the modified Chi-squared test to compare two or more CIFs. Epic!

Fine, Jason P., and Robert J. Gray. “A proportional hazards model for the subdistribution of a competing risk.” Journal of the American Statistical Association 94.446 (1999): 496-509.
This is the paper that proposed the subdistribution hazard function and the proportional hazard model for CIF. Epic!

Latouche, Aurélien, et al. “Misspecified regression model for the subdistribution hazard of a competing risk.” Statistics in medicine 26.5 (2007): 965-974.
This paper criticized the misuse of subdistribution hazard function in published papers. It’s kind of helpful since it pointed out some common mistakes in using this method.

Lau, Bryan, Stephen R. Cole, and Stephen J. Gange. “Competing risk regression models for epidemiologic data.” American journal of epidemiology 170.2 (2009): 244-256.
This paper gives an excellent summary of the CIF and competing risk regression, with vivid graphs. It also has an application of this method in real world data. Very useful for epidemiologists.

Zhou, Bingqing, et al. “Competing risks regression for stratified data.” Biometrics 67.2 (2011): 661-670.
The paper extended Gray’s methods to analyze stratified data.

Zhou, Bingqing, et al. “Competing risks regression for clustered data.” Biostatistics 13.3 (2012): 371-383.
The paper extended Gray’s methods to analyze clustered data.

Andersen, Per Kragh, et al. “Competing risks in epidemiology: possibilities and pitfalls.” International journal of epidemiology 41.3 (2012): 861-870.
A good summary and critique of Gray’s methods.

### Application Articles

Wolbers, Marcel, et al. “Prognostic models with competing risks: methods and application to coronary risk prediction.” Epidemiology 20.4 (2009): 555-561.
This paper compared Fine and Gray’s model to standard Cox model in analyzing coronary heart disease mortality and showed Cox model overestimated the hazard.

Wolbers, Marcel, et al. “Competing risks analyses: objectives and approaches.” European Heart Journal (2014): ehu131.
This paper is also by Wolbers et al. but gives a more extensive review of Gray’s method and an example analysis of implantable cardioverter-defibrillators effectiveness.

Grover, Gurprit, Prafulla Kumar Swain, and Vajala Ravi. “A Competing Risk Approach with Censoring to Estimate the Probability of Death of HIV/AIDS Patients on Antiretroviral Therapy in the Presence of Covariates.” Statistics Research Letters 3.1 (2014).
A classic application in HIV treatment research.

Dignam, James J., Qiang Zhang, and Masha Kocherginsky. “The use and interpretation of competing risks regression models.” Clinical Cancer Research 18.8 (2012): 2301-2308.
This paper used an example data from a radiation therapy oncology group clinical trial for prostate cancer to show that different model of hazard can lead to very different conclusions about the same predictor.

**R Tutorials**

Scrucca, L., A. Santucci, and F. Aversa. “Competing risk analysis using R: an easy guide for clinicians.” Bone marrow transplantation 40.4 (2007): 381-387.
A very nice tutorial of estimating CIF in R for non-statsitical people.

Scrucca, L., A. Santucci, and F. Aversa. “Regression modeling of competing risk using R: an in depth guide for clinicians.” Bone marrow transplantation 45.9 (2010): 1388-1395.
A very nice tutorial of fitting competing risk regression in R for non-statsitical people.

Scheike, Thomas H., and Mei-Jie Zhang. “Analyzing competing risk data using the R timereg package.” Journal of statistical software 38.2 (2011).
An intro to an R package “timereg” other than the “cmprsk” package for competing data analysis.

**STATA tutorials**

Coviello, Vincenzo, and May Boggess. “Cumulative incidence estimation in the presence of competing risks.” STATA journal 4 (2004): 103-112.

**SAS tutorials**

Lin, Guixian, Ying So, and Gordon Johnston. “Analyzing survival data with competing risks using SAS software.” SAS Global Forum. Vol. 2102. 2012.

## Courses

Sally R. Hinchlie. “Competing Risks – What, Why, When and How?” Survival Analysis for Junior Researchers, Department of Health Sciences, University of Leicester, 2012
An awesome lecture on competing risk analysis with lots of graphs to understand the method.

Bernhard Haller. “Analysis of competing risks data and simulation of data following predened subdistribution hazards”, Research Seminar, Institut für Medizinische Statistik und Epidemiologie, Technische Universität München, 2013
Teach you how to simulate competing data, a little bit hard to follow.

Roberto G. Gutierrez. “Competing-risks regression”, 2009 Australian and New Zealand Stata Users Group Meeting. StataCorp LP, 2009
A lecture about using STATA to analyze competing risk data.

## Join the Conversation

Have a question about methods? Join us on Facebook

## Columbia University Mailman School of Public Health

## Follow Us

We are committed to the well-being and success of all community members. Columbia complies with all applicable civil rights laws and does not engage in illegal preferences or discrimination.
