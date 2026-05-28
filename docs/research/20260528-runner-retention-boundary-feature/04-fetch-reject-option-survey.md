HTML conversions [sometimes display errors](https://info.dev.arxiv.org/about/accessibility_html_error_messages.html) due to content that did not convert correctly from the source. This paper uses the following packages that are not yet supported by the HTML conversion tool. Feedback on these issues are not necessary; they are known and are being worked on.

Authors: achieve the best HTML results from your LaTeX submissions by following these [best practices](https://info.arxiv.org/help/submit_latex_best_practices.html).

# Machine Learning with a Reject Option: A survey

###### Abstract

Machine learning models always make a prediction, even when it is likely to be inaccurate. This behavior should be avoided in many decision support applications, where mistakes can have severe consequences. Albeit already studied in 1970, machine learning with rejection recently gained interest. This machine learning subfield enables machine learning models to abstain from making a prediction when likely to make a mistake.

This survey aims to provide an overview on machine learning with rejection. We introduce the conditions leading to two types of rejection, ambiguity and novelty rejection, which we carefully formalize. Moreover, we review and categorize strategies to evaluate a model’s predictive and rejective quality. Additionally, we define the existing architectures for models with rejection and describe the standard techniques for learning such models. Finally, we provide examples of relevant application domains and show how machine learning with rejection relates to other machine learning research areas.

###### Keywords:

###### MSC:

###### Contents

## 1 Introduction

The canonical task in machine learning is to learn a predictive model that captures the relationship between a set of input variables and a target variable on the basis of training data. Machine-learned models are powerful because, after training, they offer the ability to make accurate predictions about future examples. Since this enables automating a number of tasks that are difficult and/or time-consuming, such models are ubiquitously deployed.

However, their key functionality of always returning a prediction for a given novel input is also a drawback. While the model may produce accurate predictions in general, in certain circumstances this may not be the case. For instance, there could be certain regions of the feature space where the model struggles to differentiate among the different classes. Or the current test example could be highly dissimilar to the data used to train the model. In certain application domains, such as medical diagnostics (Kotropoulos and Arce,, [2009](https://arxiv.org/html/2107.11277v3#bib.bib121)) and engineering (Zou et al.,, [2011](https://arxiv.org/html/2107.11277v3#bib.bib230)), mispredictions can have serious consequences. Therefore, it would be beneficial for a model to be cautious in situations where it is uncertain about its predictions. The prediction task could be deferred to a human expert in these situations.

One way to accomplish this is to use machine learning models with rejection. Such models assess their confidence in each prediction and have the option to abstain from making a prediction when they are likely to make a mistake. This ability to abstain from making a prediction has several benefits. First, by only making predictions when it is confident, it can result in improved performance for the retained examples (Pudil et al.,, [1992](https://arxiv.org/html/2107.11277v3#bib.bib173)). Second, avoiding mispredictions can increase a user’s trust in the system (El-Yaniv and Wiener,, [2010](https://arxiv.org/html/2107.11277v3#bib.bib52)). Third, it can still result in time savings by only requiring human interventions to make decisions in a small number of cases. Fourth, avoiding strongly biased predictions helps build a more fair model (Lee et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib131); Ruggieri et al.,, [2023](https://arxiv.org/html/2107.11277v3#bib.bib178)).
This machine learning sub-field was already studied in 1970 by Chow, ([1970](https://arxiv.org/html/2107.11277v3#bib.bib23)) and Hellman, ([1970](https://arxiv.org/html/2107.11277v3#bib.bib101)). However, the proliferation of applications has resulted in renewed interest in this area.

This survey aims to provide an overview of the subfield of machine learning with rejection, which we structure around eight key research questions.

How can we formalize the conditions for which a model should abstain from making a prediction?

How can we evaluate the performance of a model with rejection?

What architectures are possible for operationalizing (i.e., putting this into practice) the ability to abstain from making a prediction?

How do we learn models with rejection?

What are the main pros and cons of using a specific architecture?

How can we combine multiple rejectors?

Where does the need for machine learning with rejection methods arise in real-world applications?

How does machine learning with rejection relate to other research areas?

In addition to the individual contributions of addressing each of these research questions, our major contribution is that we identify the main characteristics of machine learning models with rejection, allowing us to structure the methods in this research field.
By providing an overview of the research field as well as deeper insights into the various techniques, we aid in further advance this research area, as well as its adaptation to real-world applications.

The remainder of this paper is structured as follows. In Section [2](https://arxiv.org/html/2107.11277v3#S2 "2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey"), we formalize the setting in which machine learning with rejection operates and identify the two main motivations to abstain from making a prediction (Q1). Section [3](https://arxiv.org/html/2107.11277v3#S3 "3 Evaluating models with rejection ‣ Machine Learning with a Reject Option: A survey") introduces the means to evaluate the performance of models with rejection (Q2).
Sections [4](https://arxiv.org/html/2107.11277v3#S4 "4 Separated rejector ‣ Machine Learning with a Reject Option: A survey"), [5](https://arxiv.org/html/2107.11277v3#S5 "5 Dependent rejector ‣ Machine Learning with a Reject Option: A survey"), and [6](https://arxiv.org/html/2107.11277v3#S6 "6 Integrated rejector ‣ Machine Learning with a Reject Option: A survey") provide a structured overview of the actionable techniques to reject based on the relevant literature. In these sections, we focus on describing the architecture (Q3), the rejector’s learning (Q4), and the key pros and cons (Q5). In Section [7](https://arxiv.org/html/2107.11277v3#S7 "7 Combining multiple rejectors ‣ Machine Learning with a Reject Option: A survey") we explore how to combine multiple rejectors to allow different types of rejection (Q6)
Section [8](https://arxiv.org/html/2107.11277v3#S8 "8 Applications of machine learning models with rejection ‣ Machine Learning with a Reject Option: A survey") discusses the main application fields (Q7), while Section [9](https://arxiv.org/html/2107.11277v3#S9 "9 Link to other research areas ‣ Machine Learning with a Reject Option: A survey") explores the relation of machine learning with rejection with other research areas (Q8).
Finally, Section [10](https://arxiv.org/html/2107.11277v3#S10 "10 Conclusions and perspectives ‣ Machine Learning with a Reject Option: A survey") summarizes our conclusions and lists the main open research questions.

## 2 The learning with reject problem setting

In the standard supervised setting, a learner has access to a training set D={(x1,y1),…,(xn,yn)}𝐷subscript𝑥1subscript𝑦1…subscript𝑥𝑛subscript𝑦𝑛D=\{(x\_{1},y\_{1}),\ldots,(x\_{n},y\_{n})\}italic\_D = { ( italic\_x start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_y start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ) , … , ( italic\_x start\_POSTSUBSCRIPT italic\_n end\_POSTSUBSCRIPT , italic\_y start\_POSTSUBSCRIPT italic\_n end\_POSTSUBSCRIPT ) }, where each xisubscript𝑥𝑖x\_{i}italic\_x start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT is a d𝑑ditalic\_d dimensional vector and yisubscript𝑦𝑖y\_{i}italic\_y start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT is the target. The training data is assumed to be independent and identically distributed (i.i.d.) according to some unknown probability measure P𝑃Pitalic\_P (with density p⁢(X,Y)𝑝𝑋𝑌p(X,Y)italic\_p ( italic\_X , italic\_Y )).
More generally, we denote the feature space as 𝒳𝒳\mathcal{X}caligraphic\_X and the target space as 𝒴𝒴\mathcal{Y}caligraphic\_Y, which could be discrete 𝒴={1,2,…,K}𝒴12…𝐾\mathcal{Y}=\{1,2,\ldots,K\}caligraphic\_Y = { 1 , 2 , … , italic\_K }, continuous 𝒴=ℝ𝒴ℝ\mathcal{Y}=\mathbb{R}caligraphic\_Y = blackboard\_R, or even probabilistic 𝒴=[0,1]𝒴01\mathcal{Y}=[0,1]caligraphic\_Y = [ 0 , 1 ].

The assumption is that there is an unknown, non-deterministic function f:𝒳→𝒴:𝑓→𝒳𝒴f\colon\mathcal{X}\to\mathcal{Y}italic\_f : caligraphic\_X → caligraphic\_Y that maps the examples to their target value. Given a hypothesis space ℋℋ\mathcal{H}caligraphic\_H of functions h:𝒳→𝒴:ℎ→𝒳𝒴h\colon\mathcal{X}\to\mathcal{Y}italic\_h : caligraphic\_X → caligraphic\_Y, the goal of a learner is to find a good approximation to f𝑓fitalic\_f. Typically, this can be done by finding a model h∈ℋℎℋh\in\mathcal{H}italic\_h ∈ caligraphic\_H with a small expected risk R𝑅Ritalic\_R which is usually approximated using the training data

|  |  |  |  |
| --- | --- | --- | --- |
|  | R⁢(h)≔∫𝒳×𝒴L⁢(h⁢(x),y)⁢𝑑P⁢(x,y)≈∑i=1nL⁢(h⁢(xi),yi)n,≔𝑅ℎsubscript𝒳𝒴𝐿ℎ𝑥𝑦differential-d𝑃𝑥𝑦superscriptsubscript𝑖1𝑛𝐿ℎsubscript𝑥𝑖subscript𝑦𝑖𝑛R(h)\coloneqq\int\_{\mathcal{X}\times\mathcal{Y}}L(h(x),y)dP(x,y)\approx\sum\_{i% =1}^{n}\frac{L(h(x\_{i}),y\_{i})}{n},italic\_R ( italic\_h ) ≔ ∫ start\_POSTSUBSCRIPT caligraphic\_X × caligraphic\_Y end\_POSTSUBSCRIPT italic\_L ( italic\_h ( italic\_x ) , italic\_y ) italic\_d italic\_P ( italic\_x , italic\_y ) ≈ ∑ start\_POSTSUBSCRIPT italic\_i = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_n end\_POSTSUPERSCRIPT divide start\_ARG italic\_L ( italic\_h ( italic\_x start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ) , italic\_y start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ) end\_ARG start\_ARG italic\_n end\_ARG , |  | (1) |

where L𝐿Litalic\_L is a suitable loss function such as the squared or zero-one loss.

### 2.1 Models with a reject option

In learning with rejection, the output space of the model is extended to include a new value ® ([Cortes et al., 2016a,](https://arxiv.org/html/2107.11277v3#bib.bib39) ; Cortes et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib38); [Gamelas Sousa et al., 2014a,](https://arxiv.org/html/2107.11277v3#bib.bib80) ). This new symbol means that the model abstains from making a prediction. When performing classification with rejection, which is also called cautious classification, this new output ® can be seen as an additional class (Ferri and Hernández-Orallo,, [2004](https://arxiv.org/html/2107.11277v3#bib.bib56)).

Conceptually, since hℎhitalic\_h only approximates the true underlying model, there are likely regions of 𝒳𝒳\mathcal{X}caligraphic\_X where hℎhitalic\_h systematically differs from f𝑓fitalic\_f.
Specifically, discrepancies between hℎhitalic\_h and f𝑓fitalic\_f can be due to inconsistent data (e.g., classes overlapping), insufficient data (e.g., unexplored regions), or even incorrect model assumptions (e.g., hℎhitalic\_h must be linear while f𝑓fitalic\_f is not).
Therefore, the goal of rejection is to determine such regions in order to abstain from making likely inaccurate predictions.

Formally, a model with rejection m:𝒳→𝒴∪{®}:𝑚→𝒳𝒴®m\colon\mathcal{X}\to\mathcal{Y}\cup\{\text{\textregistered}\}italic\_m : caligraphic\_X → caligraphic\_Y ∪ { ® } is represented by a pair (h,r)ℎ𝑟(h,r)( italic\_h , italic\_r ), where h:𝒳→𝒴:ℎ→𝒳𝒴h\colon\mathcal{X}\to\mathcal{Y}italic\_h : caligraphic\_X → caligraphic\_Y is the predictor and r:ℛ→ℝ:𝑟→ℛℝr\colon\mathcal{R}\to\mathbb{R}italic\_r : caligraphic\_R → blackboard\_R is the rejector. Note that the rejector may use a variety of different inputs such as examples (ℛ=𝒳ℛ𝒳\mathcal{R}=\mathcal{X}caligraphic\_R = caligraphic\_X), confidence or probability values (ℛ=[0,1]ℛ01\mathcal{R}=[0,1]caligraphic\_R = [ 0 , 1 ]), or even both (ℛ=𝒳×[0,1]ℛ𝒳01\mathcal{R}=\mathcal{X}\times[0,1]caligraphic\_R = caligraphic\_X × [ 0 , 1 ]).
At prediction time, m𝑚mitalic\_m outputs the symbol ® and abstains from making predictions when the rejector r𝑟ritalic\_r determines that the predictor is at a heightened risk of making a misprediction and otherwise returns the predictor’s output:

|  |  |  |  |
| --- | --- | --- | --- |
|  | m⁢(x)={®if the prediction is 𝑟𝑒𝑗𝑒𝑐𝑡𝑒𝑑;h⁢(x)if the prediction is 𝑎𝑐𝑐𝑒𝑝𝑡𝑒𝑑.𝑚𝑥cases®if the prediction is 𝑟𝑒𝑗𝑒𝑐𝑡𝑒𝑑ℎ𝑥if the prediction is 𝑎𝑐𝑐𝑒𝑝𝑡𝑒𝑑m(x)=\begin{cases}\text{\textregistered}&\text{if the prediction is \emph{% rejected}};\\ h(x)&\text{if the prediction is \emph{accepted}}.\end{cases}italic\_m ( italic\_x ) = { start\_ROW start\_CELL ® end\_CELL start\_CELL if the prediction is italic\_rejected ; end\_CELL end\_ROW start\_ROW start\_CELL italic\_h ( italic\_x ) end\_CELL start\_CELL if the prediction is italic\_accepted . end\_CELL end\_ROW |  | (2) |

At prediction time, the key design decision for a model with rejection is how to structure the relationship between the predictor and rejector. Based on our analysis of the literature, we have identified three common architectural principles.

The rejector operates independently from the predictor. The most typical operationalization of this architecture lets the rejector serve as a filter that decides whether to pass a test example to the predictor.
Figure [1](https://arxiv.org/html/2107.11277v3#S2.F1 "Figure 1 ‣ 2.1 Models with a reject option ‣ 2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey") shows the test time data flow of a separated rejector.

Here, the rejector bases its decision on the output of the predictor. For instance, the dependent rejector can look at how close a prediction is to the predictor’s decision boundary and abstain if it is too close. Figure [2](https://arxiv.org/html/2107.11277v3#S2.F2 "Figure 2 ‣ 2.1 Models with a reject option ‣ 2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey") shows the data flow for the dependent rejector.

This principle involves integrating the rejector and predictor into a single model m𝑚mitalic\_m by treating rejection as an additional class that can be returned by the model m𝑚mitalic\_m. Thus, it is impossible to distinguish between the role of the predictor hℎhitalic\_h and the rejector r𝑟ritalic\_r.
Figure [3](https://arxiv.org/html/2107.11277v3#S2.F3 "Figure 3 ‣ 2.1 Models with a reject option ‣ 2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey") illustrates this scenario.

![Refer to caption](extracted/5422438/level_1.png)
![Refer to caption](extracted/5422438/level_2.png)
![Refer to caption](extracted/5422438/level_3.png)

### 2.2 Types of rejection

At a high-level, a learned predictor can exhibit (high) uncertainty in its predictions for four reasons:

There can be cases where a vector xi∈𝒳subscript𝑥𝑖𝒳x\_{i}\in\mathcal{X}italic\_x start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ∈ caligraphic\_X is associated with multiple values from the target space 𝒴𝒴\mathcal{Y}caligraphic\_Y. This can arise in situations such as when classes overlap in classification tasks.

Some instances in the training data are incorrect (e.g., the values of certain features were recorded incorrectly, labeling errors).

P⁢(X,Y)𝑃𝑋𝑌P(X,Y)italic\_P ( italic\_X , italic\_Y ) might differ between the training phase and deployment (e.g., concept drift). Consequently, the training data is no longer representative.

Some examples x𝑥xitalic\_x could simply not be acquired due to their inherent rarity (anomalies, out-of-distribution).

Based on this intuition, two types of rejections can be performed:

occurs if x𝑥xitalic\_x falls in a region where the target y𝑦yitalic\_y is ambiguous (R1 and R2). This often occurs in regions that are close to the decision boundary in classification tasks;

occurs if x𝑥xitalic\_x falls in a region where there was little (or no) training data. Hence, the predictor may struggle to make accurate predictions because it did not see enough data to accurately model the relationship between X𝑋Xitalic\_X and Y𝑌Yitalic\_Y (R3 and R4).

#### 2.2.1 Ambiguity Rejection

Ambiguity rejection allows a model to abstain from making a prediction for an example x𝑥xitalic\_x in regions where, despite having access to some training examples, the model hℎhitalic\_h fails to capture the correct relationship f𝑓fitalic\_f between X𝑋Xitalic\_X and Y𝑌Yitalic\_Y (Flores,, [1958](https://arxiv.org/html/2107.11277v3#bib.bib64); Hellman,, [1970](https://arxiv.org/html/2107.11277v3#bib.bib101); Fukunaga and Kessell,, [1972](https://arxiv.org/html/2107.11277v3#bib.bib72)). This can happen for two reasons.

First, the observed relationship between X𝑋Xitalic\_X and Y𝑌Yitalic\_Y is not deterministic. This can arise due to the intrinsic probabilistic nature of Y|Xconditional𝑌𝑋Y|Xitalic\_Y | italic\_X, which a deterministic predictor hℎhitalic\_h cannot handle (e.g., coin toss), or the training data containing too many errors (e.g., incorrectly labeled examples), which would make it difficult for hℎhitalic\_h to approximate f𝑓fitalic\_f.
In classification, this can arise due to classes overlapping in certain regions of the instance-space (Figure [4](https://arxiv.org/html/2107.11277v3#S2.F4 "Figure 4 ‣ 2.2.2 Novelty Rejection ‣ 2.2 Types of rejection ‣ 2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey")a), while in regression, it leads to high variance in the target variable in certain regions (Figure [5](https://arxiv.org/html/2107.11277v3#S2.F5 "Figure 5 ‣ 2.2.2 Novelty Rejection ‣ 2.2 Types of rejection ‣ 2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey")a). One way to interpret this issue is that the chosen feature space does not allow for accurately determining the target value (e.g., missing features might cause examples with different predictions to be projected onto the same example (Van Craenendonck et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib203), Figure 2)).

Second, a poor choice of the predictor’s hypothesis space makes it impossible to learn the relationship between X𝑋Xitalic\_X and Y𝑌Yitalic\_Y.
This occurs when the chosen hypothesis space ℋℋ\mathcal{H}caligraphic\_H does not include f𝑓fitalic\_f. Figure [4](https://arxiv.org/html/2107.11277v3#S2.F4 "Figure 4 ‣ 2.2.2 Novelty Rejection ‣ 2.2 Types of rejection ‣ 2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey")b illustrates this error in binary classification, where only linear models (e.g., perceptron) are considered for ℋℋ\mathcal{H}caligraphic\_H while the true target concept f𝑓fitalic\_f is non-linear. Similarly, Figure [5](https://arxiv.org/html/2107.11277v3#S2.F5 "Figure 5 ‣ 2.2.2 Novelty Rejection ‣ 2.2 Types of rejection ‣ 2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey")b shows a regression problem with ℋℋ\mathcal{H}caligraphic\_H as the family of quadratic models, while f𝑓fitalic\_f is non-quadratic. In both cases, the expected prediction error is large for certain examples because f∉ℋ𝑓ℋf\not\in\mathcal{H}italic\_f ∉ caligraphic\_H.

#### 2.2.2 Novelty Rejection

Many machine learning models struggle when forced to extrapolate to regions of the feature space that were not (sufficiently) present in the training data ([Cordella et al., 1995a,](https://arxiv.org/html/2107.11277v3#bib.bib36) ; Sambu Seo et al.,, [2000](https://arxiv.org/html/2107.11277v3#bib.bib179); Vailaya and Jain,, [2000](https://arxiv.org/html/2107.11277v3#bib.bib202)).

Novelty rejection allows a model to abstain from making predictions for examples that are sufficiently different from the training data (Dubuisson and Masson,, [1993](https://arxiv.org/html/2107.11277v3#bib.bib50)). For such examples, the predictor hℎhitalic\_h is likely to make mistakes because the absence of training data similar to x𝑥xitalic\_x prevents hℎhitalic\_h from learning the correct target y𝑦yitalic\_y.

In practice, this arises when one of the following assumptions of the training procedure is violated. First, the sampling distribution differs from the true distribution. Thus, parts of the feature space are not represented in the data (e.g., the data does not contain any examples of patients suffering from a particular rare disease) (Van der Plas et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib204)) or one cannot generate data for all imaginable situations (e.g., a sensor can break in many different ways) (Hendrickx et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib102); Urahama and Furukawa,, [1995](https://arxiv.org/html/2107.11277v3#bib.bib201); Hsu et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib108)). Second, the skew in the class distribution is too large that the model ignores parts of the feature space. Thus, the predictor may choose to ignore these examples in its objective to optimize the accuracy model-complexity trade-off. Third, a new distribution appears after training and these new examples are out-of-distribution. For instance, this can arise due to drift that leads to new classes (Landgrebe et al.,, [2004](https://arxiv.org/html/2107.11277v3#bib.bib128)) or an adversarial agent that deliberately tries to mislead (Wang and Yiu,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib215); Corbière et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib33)).

Figures [4](https://arxiv.org/html/2107.11277v3#S2.F4 "Figure 4 ‣ 2.2.2 Novelty Rejection ‣ 2.2 Types of rejection ‣ 2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey")c and [5](https://arxiv.org/html/2107.11277v3#S2.F5 "Figure 5 ‣ 2.2.2 Novelty Rejection ‣ 2.2 Types of rejection ‣ 2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey")c illustrate this rejection type for a classification and a regression problem. In both cases, the three black stars represent test examples that are far away from the training examples.
The learned model hℎhitalic\_h may be inaccurate in these regions due to the lack of training data, which increases the chance of making a misprediction for these test examples.

The importance of novelty rejection often becomes particularly apparent in medical applications since in many of these applications, it is challenging or expensive to get an exhaustive training set. Therefore, the training set might only include patients from specific age groups or with particular medical conditions.
For instance, Van der Plas et al., ([2021](https://arxiv.org/html/2107.11277v3#bib.bib204)) learned a sleep stage classifier but only had access to a training set containing adult patients. Consequently, the model may not perform well when applied in practice to patients that are different than those encountered during training such as children or people suffering from extremely rare disorders. However, this information and the assumptions made during data collection might not be available to the user of the model.
Therefore, adding a novelty rejector is crucial to avoid poor prediction performance on these patients. In this case, a rejector based on a LOF outlier detector can reject the predictions from children as they have a different morphology than the adults in the training set (Figure [6](https://arxiv.org/html/2107.11277v3#S2.F6 "Figure 6 ‣ 2.2.2 Novelty Rejection ‣ 2.2 Types of rejection ‣ 2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey")). This mitigates the risk of incorrect predictions.

![Refer to caption](x1.png)
![Refer to caption](x2.png)
![Refer to caption](extracted/5422438/example_sleep_2.png)

## 3 Evaluating models with rejection

|  | | Rejection | |
| --- | --- | --- | --- |
| Prediction |  | *No* | *Yes* |
| *Correct* | True accept (TA) | False reject (FR) |
|  | *Incorrect* | False accept (FA) | True reject (TR) |

Prediction

Conceptually, a model with a reject option involves evaluating the outputs of both the predictor and the rejector. Thus, its performance can be viewed through the prism of the confusion matrix shown in Table [1](https://arxiv.org/html/2107.11277v3#S3.T1 "Table 1 ‣ 3 Evaluating models with rejection ‣ Machine Learning with a Reject Option: A survey"), where the columns represent the rejector’s decision and the rows whether the predictor’s output is correct or not.
Intuitively, the learning-to-reject model is “correct” if a correct prediction is returned to the user (a true accept) or an example is rejected when the model’s prediction was wrong (a true reject). It is considered to have made a “mistake” if the model provides the user with an incorrect prediction (false accept) or rejects an example for which the model’s prediction was correct.

Viewed through this lens, a model with rejection has two goals. On the one hand, it wants to have high accuracy 𝒜𝒜\mathcal{A}caligraphic\_A on examples for which it makes a prediction:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | 𝒜𝒜\displaystyle\mathcal{A}caligraphic\_A | =\displaystyle== | T⁢AT⁢A+F⁢A.𝑇𝐴𝑇𝐴𝐹𝐴\displaystyle\frac{TA}{TA+FA}.divide start\_ARG italic\_T italic\_A end\_ARG start\_ARG italic\_T italic\_A + italic\_F italic\_A end\_ARG . |  |

This makes the model reliable as practitioners can trust its outputs. On the other hand, it wants to have high coverage:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | ϕitalic-ϕ\displaystyle\phiitalic\_ϕ | =\displaystyle== | T⁢A+F⁢AT⁢A+F⁢A+F⁢R+T⁢R.𝑇𝐴𝐹𝐴𝑇𝐴𝐹𝐴𝐹𝑅𝑇𝑅\displaystyle\frac{TA+FA}{TA+FA+FR+TR}.divide start\_ARG italic\_T italic\_A + italic\_F italic\_A end\_ARG start\_ARG italic\_T italic\_A + italic\_F italic\_A + italic\_F italic\_R + italic\_T italic\_R end\_ARG . |  |

That is, it should make a prediction for as many test examples as possible (De Stefano et al.,, [2000](https://arxiv.org/html/2107.11277v3#bib.bib44); El-Yaniv and Wiener,, [2010](https://arxiv.org/html/2107.11277v3#bib.bib52); Lei,, [2014](https://arxiv.org/html/2107.11277v3#bib.bib132)). This can alternatively be viewed as having a low rejection rate, defined as 1−ϕ1italic-ϕ1-\phi1 - italic\_ϕ.
This makes the model useful in practice as its predictions can be utilized for decision-making. Unfortunately, these two goals are competing as the accuracy can be increased by limiting the predictions to the most confident cases, i.e., reducing the coverage (Hansen et al.,, [1997](https://arxiv.org/html/2107.11277v3#bib.bib99); Homenda et al.,, [2016](https://arxiv.org/html/2107.11277v3#bib.bib106)). As a result, metrics specifically tailored to learning to reject must capture this trade-off (Cordelia et al.,, [1998](https://arxiv.org/html/2107.11277v3#bib.bib34)).

Broadly speaking, three categories of metrics exist that evaluate different aspects of a model with rejection:

This entails having a fixed rejection rate provided by the user. In this case, one only needs to evaluate performance on the non-rejected examples and it is possible to use the standard evaluations (e.g., accuracy (Golfarelli et al.,, [1997](https://arxiv.org/html/2107.11277v3#bib.bib90)));

One can plot the rejection rate on the x-axis and the predictor’s performance obtained on a representative test set on the y-axis, similar to Receiver Operating Characteristic (ROC) analysis;

This case only requires knowing the model’s output and the costs for (mis)predictions and rejections.

### 3.1 Evaluating models with a fixed rejection rate.

Given a dataset and a fixed rejection rate, Condessa et al., ([2017](https://arxiv.org/html/2107.11277v3#bib.bib31)) argue that a good evaluation metric should meet four main criteria: given a fixed predictor, such metric should: (p1) depend on the model’s rejection rate; (p2) be able to compare two models with different rejectors for a given rejection rate (and for the same predictor); (p3) be able to compare two models with different rejectors with different rejection rates when one clearly outperforms the other; (p4) reach its maximum value for a perfect rejector (i.e., a rejector that rejects all misclassified examples) and its minimum value for a rejector that rejects all accurate predictions. In addition, Condessa et al., ([2017](https://arxiv.org/html/2107.11277v3#bib.bib31)) propose three types of evaluation metrics that meet the required conditions:

Prediction quality. The model’s prediction quality (PQ) measures the predictor’s performance on the non-rejected examples. For instance, one can use classical evaluation metrics on the accepted examples such as the accuracy

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | P⁢Qacc𝑃subscript𝑄acc\displaystyle PQ\_{\textsc{acc}}italic\_P italic\_Q start\_POSTSUBSCRIPT acc end\_POSTSUBSCRIPT | =\displaystyle== | T⁢AT⁢A+F⁢A,𝑇𝐴𝑇𝐴𝐹𝐴\displaystyle\frac{TA}{TA+FA},divide start\_ARG italic\_T italic\_A end\_ARG start\_ARG italic\_T italic\_A + italic\_F italic\_A end\_ARG , |  |

the F-scores (Pillai et al.,, [2011](https://arxiv.org/html/2107.11277v3#bib.bib167); Mesquita et al.,, [2016](https://arxiv.org/html/2107.11277v3#bib.bib147)) or any other evaluation metric, including fairness metrics (Madras et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib142)).
While this allows comparing models with different rejectors, looking only at the prediction quality will tend to favor the model with the highest rejection rate. By being more conservative (i.e., having a lower coverage), the model tends only to offer predictions for the subset of examples for which it is most confident.

Rejection quality. The rejection quality (RQ) indicates the rejector’s ability to reject misclassified examples.
One way to do this is by comparing the ratio of misclassified examples on the rejected subset (T⁢RF⁢R𝑇𝑅𝐹𝑅\frac{TR}{FR}divide start\_ARG italic\_T italic\_R end\_ARG start\_ARG italic\_F italic\_R end\_ARG) to the ratio on the complete dataset (F⁢A+T⁢RT⁢A+F⁢R𝐹𝐴𝑇𝑅𝑇𝐴𝐹𝑅\frac{FA+TR}{TA+FR}divide start\_ARG italic\_F italic\_A + italic\_T italic\_R end\_ARG start\_ARG italic\_T italic\_A + italic\_F italic\_R end\_ARG), i.e.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | R⁢Qratio𝑅subscript𝑄ratio\displaystyle RQ\_{\textsc{ratio}}italic\_R italic\_Q start\_POSTSUBSCRIPT ratio end\_POSTSUBSCRIPT | =\displaystyle== | T⁢RF⁢R/F⁢A+T⁢RT⁢A+F⁢R.𝑇𝑅𝐹𝑅𝐹𝐴𝑇𝑅𝑇𝐴𝐹𝑅\displaystyle\frac{TR}{FR}\Big{/}\frac{FA+TR}{TA+FR}.divide start\_ARG italic\_T italic\_R end\_ARG start\_ARG italic\_F italic\_R end\_ARG / divide start\_ARG italic\_F italic\_A + italic\_T italic\_R end\_ARG start\_ARG italic\_T italic\_A + italic\_F italic\_R end\_ARG . |  |

Looking only at the rejection quality will favor models with the lowest rejection rate. The lower the rejection rate is, the more likely the rejector is to abstain only on those few examples for which it is most confident that the predictor will make a mistake.

Combined quality. The combined quality (CQ) evaluates the model with a reject option as a whole.
One way to accomplish this is by combining the predictor’s performance on the non-rejected examples (prediction quality) with the rejector’s performance on the misclassified examples (rejection quality). For instance, using P⁢Qacc𝑃subscript𝑄accPQ\_{\textsc{acc}}italic\_P italic\_Q start\_POSTSUBSCRIPT acc end\_POSTSUBSCRIPT and R⁢Qratio𝑅subscript𝑄ratioRQ\_{\textsc{ratio}}italic\_R italic\_Q start\_POSTSUBSCRIPT ratio end\_POSTSUBSCRIPT yields to

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | C⁢Qacc-ratio𝐶subscript𝑄acc-ratio\displaystyle CQ\_{\textsc{acc-ratio}}italic\_C italic\_Q start\_POSTSUBSCRIPT acc-ratio end\_POSTSUBSCRIPT | =\displaystyle== | T⁢A+T⁢RT⁢A+F⁢A+F⁢R+T⁢R.𝑇𝐴𝑇𝑅𝑇𝐴𝐹𝐴𝐹𝑅𝑇𝑅\displaystyle\frac{TA+TR}{TA+FA+FR+TR}.divide start\_ARG italic\_T italic\_A + italic\_T italic\_R end\_ARG start\_ARG italic\_T italic\_A + italic\_F italic\_A + italic\_F italic\_R + italic\_T italic\_R end\_ARG . |  |

Overall, the combined quality offers a more holistic assessment of the model’s overall performance as it measures both the predictor’s and the rejector’s quality (Lin et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib135)).
The downside is that aggregating the two metrics yields a less fine-grained characterization of the model performance. Specifically, in case a model has low CQ, it is hard to ascertain which component, the predictor or rejector, is contributing the most to the model’s poor performance.

##### Pros and Cons.

The main advantage of this category is that the metrics clearly measure the fine-grained model performance in the given setting. However, using one of these types of metrics may be limiting in some cases. For instance, theoretical research may not care about evaluating the model with rejection for a specific rejection rate, as it is usually specified based on domain knowledge. Moreover, given a rejection rate, not all performance metrics can be always used, as some may suffer from task-related issues. For instance, rejecting a whole class would not allow utilizing metrics like F1-score and AUC for the prediction quality as they need both classes’ labels.

### 3.2 Evaluating the model performance/rejection trade-off.

![Refer to caption](x3.png)

To assess the performance-rejection trade-off, a common approach is to evaluate the prediction quality (for non-rejected examples) by varying the rejection rate from 0%percent00\%0 % to 100%percent100100\%100 %, which is known as the Accuracy-Reject Curve (ARC) (Nadeem et al.,, [2010](https://arxiv.org/html/2107.11277v3#bib.bib150)). This involves plotting the rejection rate on the x-axis and the prediction quality (e.g., accuracy) on the y-axis (Hanczar and Sebag,, [2014](https://arxiv.org/html/2107.11277v3#bib.bib98)). Higher curves indicate better performance. Alternatively, risk-based metrics like mean squared error can be plotted, with lower curves indicating better performance (Sambu Seo et al.,, [2000](https://arxiv.org/html/2107.11277v3#bib.bib179)). Sometimes the predictor’s performance on the rejected examples is also shown with the intuition that it should be worse on this subset of the data than on the accepted ones (Zou et al.,, [2011](https://arxiv.org/html/2107.11277v3#bib.bib230); [Condessa et al., 2015c,](https://arxiv.org/html/2107.11277v3#bib.bib30) ; [Condessa et al., 2015b,](https://arxiv.org/html/2107.11277v3#bib.bib29) ).

When comparing two models using the ARC method, two scenarios arise. First, one model clearly outperforms the other in terms of prediction quality for all rejection rates. Second, the models show varying prediction quality across different rejection rates. To illustrate this, consider Figure [7](https://arxiv.org/html/2107.11277v3#S3.F7 "Figure 7 ‣ 3.2 Evaluating the model performance/rejection trade-off. ‣ 3 Evaluating models with rejection ‣ Machine Learning with a Reject Option: A survey") where the light blue curve only outperforms the black curves if the rejection rate is lower than 0.010.010.010.01. When it is not clear which model performs best, the overall performance can be assessed using the Area Under the ARC Curve (AURC), similar to the AUC in standard machine learning ([Vanderlooy et al., 2006a,](https://arxiv.org/html/2107.11277v3#bib.bib206) ; [Vanderlooy et al., 2006b,](https://arxiv.org/html/2107.11277v3#bib.bib207) ; Landgrebe et al.,, [2006](https://arxiv.org/html/2107.11277v3#bib.bib127)). In this example, the AURC of the light blue curve will be higher than the AURC of the black curves, indicating that it performs better overall than the black curves.

##### Pros and Cons.

The main advantage of this category is that any prediction quality metric can be used on the y-axis. Moreover, they provide a high-level overview of how the model works for different rejection rates. However, generating these curves can be challenging for two reasons.
First, some rejectors do not allow directly setting the rejection rate (Wu et al.,, [2007](https://arxiv.org/html/2107.11277v3#bib.bib218); Homenda et al.,, [2014](https://arxiv.org/html/2107.11277v3#bib.bib105)), but they might have other hyperparameters (e.g., rejection threshold).
Mapping these to rejection rates may be challenging and may not be possible to achieve all possible rejection rates.
Second, altering the rejection rate of a model with rejection can require completely retraining the whole model. This may be too computationally demanding to perform a fine-grained analysis (Condessa et al.,, [2017](https://arxiv.org/html/2107.11277v3#bib.bib31)).

### 3.3 Evaluating models through a cost function.

For classification tasks, one can ask the user to specify the costs for (mis)predictions as well as for rejection and evaluate a model by its (expected) total cost at test time.
Although the costs can be designed as a continuous function of the examples (Mozannar and Sontag,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib148); De et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib43)), the cost function typically accounts only for three constant costs: the cost of correct prediction Ccsubscript𝐶𝑐C\_{c}italic\_C start\_POSTSUBSCRIPT italic\_c end\_POSTSUBSCRIPT, the cost of a prediction error Cesubscript𝐶𝑒C\_{e}italic\_C start\_POSTSUBSCRIPT italic\_e end\_POSTSUBSCRIPT, and the cost of rejection Crsubscript𝐶𝑟C\_{r}italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT such that Cc<Cr<Cesubscript𝐶𝑐subscript𝐶𝑟subscript𝐶𝑒C\_{c}<C\_{r}<C\_{e}italic\_C start\_POSTSUBSCRIPT italic\_c end\_POSTSUBSCRIPT < italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT < italic\_C start\_POSTSUBSCRIPT italic\_e end\_POSTSUBSCRIPT (De Stefano et al.,, [2000](https://arxiv.org/html/2107.11277v3#bib.bib44); Balsubramani,, [2016](https://arxiv.org/html/2107.11277v3#bib.bib8); Condessa et al.,, [2013](https://arxiv.org/html/2107.11277v3#bib.bib27)). Without loss of generality, usually one assumes normalized costs, i.e., Cc=0subscript𝐶𝑐0C\_{c}=0italic\_C start\_POSTSUBSCRIPT italic\_c end\_POSTSUBSCRIPT = 0, Ce=1subscript𝐶𝑒1C\_{e}=1italic\_C start\_POSTSUBSCRIPT italic\_e end\_POSTSUBSCRIPT = 1 and Cr∈[0,1]subscript𝐶𝑟01C\_{r}\in[0,1]italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT ∈ [ 0 , 1 ] in which the normalized value for Crsubscript𝐶𝑟C\_{r}italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT can be obtained from the initial values as Cr−CcCe−Ccsubscript𝐶𝑟subscript𝐶𝑐subscript𝐶𝑒subscript𝐶𝑐\frac{C\_{r}-C\_{c}}{C\_{e}-C\_{c}}divide start\_ARG italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT - italic\_C start\_POSTSUBSCRIPT italic\_c end\_POSTSUBSCRIPT end\_ARG start\_ARG italic\_C start\_POSTSUBSCRIPT italic\_e end\_POSTSUBSCRIPT - italic\_C start\_POSTSUBSCRIPT italic\_c end\_POSTSUBSCRIPT end\_ARG. Although the costs need to be set based on some domain knowledge, there are two constraints for setting the rejection cost properly. First, it must be lower than a random predictor’s average cost for a classification task with K𝐾Kitalic\_K classes, i.e. Cr≤1Ksubscript𝐶𝑟1𝐾C\_{r}\leq\frac{1}{K}italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT ≤ divide start\_ARG 1 end\_ARG start\_ARG italic\_K end\_ARG ([Cordella et al., 1995b,](https://arxiv.org/html/2107.11277v3#bib.bib37) ; Herbei and Wegkamp,, [2006](https://arxiv.org/html/2107.11277v3#bib.bib104)). Otherwise, the expected cost of always making a random prediction would be lower than the rejection cost, which nullifies the task of rejection. Second, one should account for possible imbalance classes by setting Cr≤1−maxk≤K⁡P⁢(Y=k)subscript𝐶𝑟1subscript𝑘𝐾𝑃𝑌𝑘C\_{r}\leq 1-\max\_{k\leq K}P(Y=k)italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT ≤ 1 - roman\_max start\_POSTSUBSCRIPT italic\_k ≤ italic\_K end\_POSTSUBSCRIPT italic\_P ( italic\_Y = italic\_k ), where P⁢(Y=k)𝑃𝑌𝑘P(Y=k)italic\_P ( italic\_Y = italic\_k ) is the class frequency (Perini et al.,, [2023](https://arxiv.org/html/2107.11277v3#bib.bib162)). In fact, for higher Crsubscript𝐶𝑟C\_{r}italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT, a naive model that always predicts the most frequent class k¯¯𝑘\bar{k}over¯ start\_ARG italic\_k end\_ARG would obtain a cost equal to 1−P⁢(Y=k¯)1𝑃𝑌¯𝑘1-P(Y=\bar{k})1 - italic\_P ( italic\_Y = over¯ start\_ARG italic\_k end\_ARG ) and rejecting examples would not be worth it for higher rejection costs.

##### Pros and Cons.

The main benefit of this category is its high interpretability: given a final cost, we can easily go back to the causes that yield such a cost. Moreover, one can use the same cost function to optimize the model parameters during the learning phase. This ensures coherence between learning the optimal model at training time and measuring its performance at test time. However, this category has the key drawback that the user must set the cost function based on domain knowledge, which is not always easy to obtain. Setting different costs changes the quality of the models, which may end up ranking several compared models differently.
A way to alleviate this would be to make the Cost-Reject plot (Hanczar,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib96)), where, similar to the ARC, the x-axis and y-axis represent respectively the normalized rejection cost and the normalized prediction cost (Friedel et al.,, [2006](https://arxiv.org/html/2107.11277v3#bib.bib70); Abbas et al.,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib1)).

## 4 Separated rejector

Separated rejectors operate by filtering out unlikely examples. They are typically used for novelty rejection though there are some examples of using them for ambiguity rejection (Asif and Minhas,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib7)).
Because the rejector does not use the predictor’s output in any way, it is typically a function of the examples: r:𝒳→ℝ:𝑟→𝒳ℝr\colon\mathcal{X}\to\mathbb{R}italic\_r : caligraphic\_X → blackboard\_R. Formally, the separated architecture yields the following model:

|  |  |  |  |
| --- | --- | --- | --- |
|  | m⁢(x)={®if ⁢r⁢(x)<τh⁢(x)otherwise.𝑚𝑥cases®if 𝑟𝑥𝜏ℎ𝑥otherwise.m(x)=\begin{cases}\text{\textregistered}&\text{if }r(x)<\tau\\ h(x)&\text{otherwise.}\end{cases}italic\_m ( italic\_x ) = { start\_ROW start\_CELL ® end\_CELL start\_CELL if italic\_r ( italic\_x ) < italic\_τ end\_CELL end\_ROW start\_ROW start\_CELL italic\_h ( italic\_x ) end\_CELL start\_CELL otherwise. end\_CELL end\_ROW |  | (3) |

If the rejector r𝑟ritalic\_r outputs a value less than τ𝜏\tauitalic\_τ, then the model m𝑚mitalic\_m rejects the example (®). Otherwise, m𝑚mitalic\_m uses the predictor hℎhitalic\_h to make a prediction.

The separation between predictor and rejector means that the rejector is learned independently of the predictor. The learning task involves learning the rejector itself as well as setting the threshold τ𝜏\tauitalic\_τ. To align with its goal of identifying unlikely or unexpected examples, a common choice is to use anomaly/outlier, out-of-distribution, or novelty detection algorithms. Three categories of methods can be used for this goal: models that 1) estimate p⁢(X)𝑝𝑋p(X)italic\_p ( italic\_X ), 2) are one-class classifiers, and 3) quantify the degree of novelty using a data-driven score function.

##### Learning a separated rejector.

A first option to learn a separated rejector is to use a probabilistic model that estimates the marginal density p⁢(X)𝑝𝑋p(X)italic\_p ( italic\_X ) and to reject a test example x𝑥xitalic\_x if p⁢(x)<τ𝑝𝑥𝜏p(x)<\tauitalic\_p ( italic\_x ) < italic\_τ. These probabilistic models often make assumptions about the distribution of the examples and are trained to maximize the likelihood of the training dataset (Vasconcelos et al.,, [1993](https://arxiv.org/html/2107.11277v3#bib.bib211)). For instance, Landgrebe et al., ([2004](https://arxiv.org/html/2107.11277v3#bib.bib128)) proposes a locally normal distribution assumption and uses a Gaussian Mixture Model (GMM) to estimate p⁢(X)𝑝𝑋p(X)italic\_p ( italic\_X ) with a specified number of components whereas others have considered Variational Autoencoders (Wang and Yiu,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib215)) and Normalizing Flows (Nalisnick et al.,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib151)).

Another option to learn a separated rejector is by employing a one-class classification model. Generally, they enclose the dataset into a specific surface and flag any example that falls outside such region as novelty. For instance, a typical approach is to use a One-Class Support Vector Machine (OCSVM) to encapsulate the training data through a hypersphere (Coenen et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib25); Homenda et al.,, [2014](https://arxiv.org/html/2107.11277v3#bib.bib105)). By adjusting the size of the hypersphere, the proportion of non-rejected examples can be increased (Wu et al.,, [2007](https://arxiv.org/html/2107.11277v3#bib.bib218)).

Alternatively, some models assign scores that represent the degree of novelty of each example (i.e., the higher the more novel), such as L⁢O⁢F𝐿𝑂𝐹LOFitalic\_L italic\_O italic\_F (Van der Plas et al.,, [2023](https://arxiv.org/html/2107.11277v3#bib.bib205)) or Neural Networks (Hsu et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib108)). When dealing with these methods, one often initially transforms the scores into novelty probabilities using heuristic functions, such as sigmoid and squashing (Vercruyssen et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib213)), or Gaussian Processes (Martens et al.,, [2023](https://arxiv.org/html/2107.11277v3#bib.bib145)). Then, the rejection threshold can be set to reject examples with high novelty probability.

##### Learning the rejection threshold τ𝜏\tauitalic\_τ.

The rejection threshold τ𝜏\tauitalic\_τ is a crucial parameter that determines whether an example is rejected or not. In many cases, the threshold is set based on domain knowledge. For instance, one can introduce adversarial examples and set a threshold to reject them all (Hosseini et al.,, [2017](https://arxiv.org/html/2107.11277v3#bib.bib107)). In case the number of novelties is unknown, one can use existing methods to estimate the contamination factor, i.e. the proportion of novelties, and set the threshold accordingly ([Perini et al., 2022b,](https://arxiv.org/html/2107.11277v3#bib.bib164) ; [Perini et al., 2022a,](https://arxiv.org/html/2107.11277v3#bib.bib160) ). Otherwise, heuristics can be employed, such as rejecting examples falling within the first or second percentiles of correctly classified training examples (Wang and Yiu,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib215)).

##### Benefits and drawbacks of a separated rejector.

Using a separated rejector has several *benefits*. First, the rejector is predictor agnostic. Hence, it can be combined with any type of predictor. Second, because the rejector can be trained independently of the predictor, it is possible to augment an existing predictor with a reject option using this architecture.
Third, by serving as a filter, the predictor makes fewer predictions. This is particularly advantageous when there is a high computational cost associated with using the predictor.
Finally, this architecture is generally simpler to operationalize compared to rejectors that interact with the predictor.
However, there are two evident *drawbacks*. First, not sharing information between the predictor and the rejector results often in sub-optimal rejection performance (Homenda et al.,, [2014](https://arxiv.org/html/2107.11277v3#bib.bib105)).
Second, this architecture is typically only used for novelty rejection because it is naturally related to assessing whether x𝑥xitalic\_x is rare or not while ambiguity rejection requires information on p⁢(Y|X)𝑝conditional𝑌𝑋p(Y|X)italic\_p ( italic\_Y | italic\_X ), which is often estimated through the predictor’s output.

## 5 Dependent rejector

Dependent rejectors analyze the predictor’s output to identify examples that the predictor is likely to mispredict. The rejector is typically represented as a confidence function ch:𝒳→[0,1]:subscript𝑐ℎ→𝒳01c\_{h}\colon\mathcal{X}\to[0,1]italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT : caligraphic\_X → [ 0 , 1 ] that measures how likely the predictor is to make a correct prediction. Formally, the model for a dependent architecture has the form:

|  |  |  |  |
| --- | --- | --- | --- |
|  | m⁢(x)={®if ⁢r⁢(x;h)<τ;h⁢(x)otherwise.𝑚𝑥cases®if 𝑟  𝑥ℎ𝜏ℎ𝑥otherwise.m(x)=\begin{cases}\text{\textregistered}&\text{if }r(x;h)<\tau;\\ h(x)&\text{otherwise.}\end{cases}italic\_m ( italic\_x ) = { start\_ROW start\_CELL ® end\_CELL start\_CELL if italic\_r ( italic\_x ; italic\_h ) < italic\_τ ; end\_CELL end\_ROW start\_ROW start\_CELL italic\_h ( italic\_x ) end\_CELL start\_CELL otherwise. end\_CELL end\_ROW |  | (4) |

where r𝑟ritalic\_r may depend on the feature vector x𝑥xitalic\_x, and on the predictor hℎhitalic\_h through the confidence function chsubscript𝑐ℎc\_{h}italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT. Similar to the separated rejector, the model rejects the example (®) only if the rejector outputs a value lower than τ𝜏\tauitalic\_τ. Without loss of generality, we assume the confidence values ch⁢(x)∈[0,1]subscript𝑐ℎ𝑥01c\_{h}(x)\in[0,1]italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) ∈ [ 0 , 1 ], as one can always transform a score function into this range.

The learning task for a dependent rejector usually entails (1) selecting a confidence function that measures how confident the predictor is in its predictions, and (2) setting the rejection threshold τ𝜏\tauitalic\_τ.

##### Learning a dependent rejector: types of confidence function chsubscript𝑐ℎc\_{h}italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT.

The form of the confidence function depends on the desired rejection type. For *ambiguity rejection*, the metric should indicate the variability of the target variable or the potential predictor bias. For *novelty rejection*, the confidence should capture the example’s similarity to the training data.
We distinguish among four ways to derive the confidence scores: i) estimating the conditional probability P⁢(Y|X)𝑃conditional𝑌𝑋P(Y|X)italic\_P ( italic\_Y | italic\_X ), ii) estimating the class conditional density p⁢(X|Y)𝑝conditional𝑋𝑌p(X|Y)italic\_p ( italic\_X | italic\_Y ), iii) performing a sensitivity analysis, and iv) exploiting the predictor’s properties.

The *conditional probability* approaches allow for ambiguity rejections by using the maximum of the class conditional probability as confidence function (Pazzani et al.,, [1994](https://arxiv.org/html/2107.11277v3#bib.bib158); Fumera et al.,, [2004](https://arxiv.org/html/2107.11277v3#bib.bib74); Lam and Suen,, [1995](https://arxiv.org/html/2107.11277v3#bib.bib126))

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
|  | ch⁢(x)subscript𝑐ℎ𝑥\displaystyle c\_{h}(x)italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) | =\displaystyle== | maxk∈𝒴⁡P⁢(Y=k|X=x)subscript𝑘𝒴𝑃𝑌conditional𝑘𝑋𝑥\displaystyle\max\_{k\in\mathcal{Y}}P(Y=k|X=x)roman\_max start\_POSTSUBSCRIPT italic\_k ∈ caligraphic\_Y end\_POSTSUBSCRIPT italic\_P ( italic\_Y = italic\_k | italic\_X = italic\_x ) |  | (5) |

where k𝑘kitalic\_k is either the true target value or the predictor’s output. Low P⁢(Y|X)𝑃conditional𝑌𝑋P(Y|X)italic\_P ( italic\_Y | italic\_X ) values for two or more targets k1,k2∈𝒴

subscript𝑘1subscript𝑘2
𝒴k\_{1},k\_{2}\in\mathcal{Y}italic\_k start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_k start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT ∈ caligraphic\_Y indicate high randomness of the data or proximity to the decision boundary (Arlandis et al.,, [2002](https://arxiv.org/html/2107.11277v3#bib.bib6)). Deriving the conditional probabilities from the predictor’s outputs can be done by post-processing the predictor’s output using techniques such as sigmoid calibration for binary classification tasks (Cordella et al.,, [2014](https://arxiv.org/html/2107.11277v3#bib.bib35); Brinkrolf and Hammer,, [2017](https://arxiv.org/html/2107.11277v3#bib.bib16))

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | P⁢(Y=1|X=x)𝑃𝑌conditional1𝑋𝑥\displaystyle P(Y=1|X=x)italic\_P ( italic\_Y = 1 | italic\_X = italic\_x ) | ≈\displaystyle\approx≈ | 11+exp⁡(A⁢h⁢(x)+B),11𝐴ℎ𝑥𝐵\displaystyle\frac{1}{1+\exp(Ah(x)+B)},divide start\_ARG 1 end\_ARG start\_ARG 1 + roman\_exp ( italic\_A italic\_h ( italic\_x ) + italic\_B ) end\_ARG , |  |

with parameters A𝐴Aitalic\_A and B𝐵Bitalic\_B learned during the training (Brinkrolf and Hammer,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib17)), softmax transformation for multi-class classification tasks (Kwok,, [1999](https://arxiv.org/html/2107.11277v3#bib.bib125))

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | P⁢(Y=k|X=x)𝑃𝑌conditional𝑘𝑋𝑥\displaystyle P(Y=k|X=x)italic\_P ( italic\_Y = italic\_k | italic\_X = italic\_x ) | ≈\displaystyle\approx≈ | exp⁡(hk⁢(x))∑j∈𝒴exp⁡(hj⁢(x)),subscriptℎ𝑘𝑥subscript𝑗𝒴subscriptℎ𝑗𝑥\displaystyle\frac{\exp{(h\_{k}(x))}}{\sum\_{j\in\mathcal{Y}}\exp{(h\_{j}(x))}},divide start\_ARG roman\_exp ( italic\_h start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ( italic\_x ) ) end\_ARG start\_ARG ∑ start\_POSTSUBSCRIPT italic\_j ∈ caligraphic\_Y end\_POSTSUBSCRIPT roman\_exp ( italic\_h start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ( italic\_x ) ) end\_ARG , |  |

where hj⁢(x)subscriptℎ𝑗𝑥h\_{j}(x)italic\_h start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ( italic\_x ) is the predictor’s output for x𝑥xitalic\_x related to class j𝑗jitalic\_j, or by fitting Gaussian Processes for regression tasks (Sambu Seo et al.,, [2000](https://arxiv.org/html/2107.11277v3#bib.bib179)). In case of multiple predictors h1,…,hV

subscriptℎ1…subscriptℎ𝑉h\_{1},\dots,h\_{V}italic\_h start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , … , italic\_h start\_POSTSUBSCRIPT italic\_V end\_POSTSUBSCRIPT, one can also measure the ensemble agreement as the conditional probability (Glodek et al.,, [2012](https://arxiv.org/html/2107.11277v3#bib.bib89); Zhang,, [2013](https://arxiv.org/html/2107.11277v3#bib.bib221))

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | P⁢(Y=k|X=x)𝑃𝑌conditional𝑘𝑋𝑥\displaystyle P(Y=k|X=x)italic\_P ( italic\_Y = italic\_k | italic\_X = italic\_x ) | ≈\displaystyle\approx≈ | ∑v=1V𝟙⁢[hv⁢(x)=k]V.superscriptsubscript𝑣1𝑉1delimited-[]subscriptℎ𝑣𝑥𝑘𝑉\displaystyle\frac{\sum\_{v=1}^{V}\mathbbm{1}[h\_{v}(x)=k]}{V}.divide start\_ARG ∑ start\_POSTSUBSCRIPT italic\_v = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_V end\_POSTSUPERSCRIPT blackboard\_1 [ italic\_h start\_POSTSUBSCRIPT italic\_v end\_POSTSUBSCRIPT ( italic\_x ) = italic\_k ] end\_ARG start\_ARG italic\_V end\_ARG . |  |

On the other hand, the *class conditional density* approaches perform novelty rejection putting (Dubuisson and Masson,, [1993](https://arxiv.org/html/2107.11277v3#bib.bib50); Dübuisson et al.,, [1985](https://arxiv.org/html/2107.11277v3#bib.bib51))

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
|  | ch⁢(x)subscript𝑐ℎ𝑥\displaystyle c\_{h}(x)italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) | =\displaystyle== | maxk∈𝒴⁡p⁢(X=x|Y=k).subscript𝑘𝒴𝑝𝑋conditional𝑥𝑌𝑘\displaystyle\max\_{k\in\mathcal{Y}}p(X=x|Y=k).roman\_max start\_POSTSUBSCRIPT italic\_k ∈ caligraphic\_Y end\_POSTSUBSCRIPT italic\_p ( italic\_X = italic\_x | italic\_Y = italic\_k ) . |  | (6) |

Intuitively, a low density p⁢(X|Y)𝑝conditional𝑋𝑌p(X|Y)italic\_p ( italic\_X | italic\_Y ) expresses that a sample is rare ([Condessa et al., 2015b,](https://arxiv.org/html/2107.11277v3#bib.bib29) ). Common methods to estimate the confidence in Eq. [6](https://arxiv.org/html/2107.11277v3#S5.E6 "6 ‣ Learning a dependent rejector: types of confidence function 𝑐_ℎ. ‣ 5 Dependent rejector ‣ Machine Learning with a Reject Option: A survey") employ generative predictors that directly measure the data density such as Gaussian Mixture Models (GMMs) (Vailaya and Jain,, [2000](https://arxiv.org/html/2107.11277v3#bib.bib202)). It is also possible to employ heuristic approaches such as normalizing the class distance between the example x𝑥xitalic\_x and its v−limit-from𝑣v-italic\_v -th nearest neighbor x′superscript𝑥′x^{\prime}italic\_x start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT (Conte et al.,, [2012](https://arxiv.org/html/2107.11277v3#bib.bib32); Villmann et al.,, [2015](https://arxiv.org/html/2107.11277v3#bib.bib214); [Fischer et al., 2014b,](https://arxiv.org/html/2107.11277v3#bib.bib62) ), i.e.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | p⁢(X=x|Y=k)𝑝𝑋conditional𝑥𝑌𝑘\displaystyle p(X=x|Y=k)italic\_p ( italic\_X = italic\_x | italic\_Y = italic\_k ) | ≈\displaystyle\approx≈ | d⁢(x,x′)∑{(x\*,y\*)∈D:y\*=k}d⁢(x\*,x\*′)𝑑𝑥superscript𝑥′subscriptconditional-setsubscript𝑥subscript𝑦𝐷subscript𝑦𝑘𝑑subscript𝑥subscriptsuperscript𝑥′\displaystyle\frac{d(x,x^{\prime})}{\sum\_{\{(x\_{\*},y\_{\*})\in D\colon y\_{\*}=k\}% }d(x\_{\*},x^{\prime}\_{\*})}divide start\_ARG italic\_d ( italic\_x , italic\_x start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT ) end\_ARG start\_ARG ∑ start\_POSTSUBSCRIPT { ( italic\_x start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT , italic\_y start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT ) ∈ italic\_D : italic\_y start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT = italic\_k } end\_POSTSUBSCRIPT italic\_d ( italic\_x start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT , italic\_x start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT ) end\_ARG |  |

and computing the proportion of neighbors within a specified radius R𝑅Ritalic\_R (Berlemont et al.,, [2015](https://arxiv.org/html/2107.11277v3#bib.bib11)) as

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | p⁢(X=x|Y=k)𝑝𝑋conditional𝑥𝑌𝑘\displaystyle p(X=x|Y=k)italic\_p ( italic\_X = italic\_x | italic\_Y = italic\_k ) | ≈\displaystyle\approx≈ | |{x′:d⁢(x,x′)≤R,(x′,y′)∈D,y′=k}|∑(x′,y′)∈D|{x\*:d⁢(x′,x\*)≤R,(x\*,y\*)∈D,y\*=k}|.conditional-setsuperscript𝑥′formulae-sequence𝑑𝑥superscript𝑥′𝑅formulae-sequencesuperscript𝑥′superscript𝑦′𝐷superscript𝑦′𝑘subscriptsuperscript𝑥′superscript𝑦′𝐷conditional-setsubscript𝑥formulae-sequence𝑑superscript𝑥′subscript𝑥𝑅formulae-sequencesubscript𝑥subscript𝑦𝐷subscript𝑦𝑘\displaystyle\frac{|\{x^{\prime}\colon d(x,x^{\prime})\leq R,(x^{\prime},y^{% \prime})\in D,y^{\prime}=k\}|}{\sum\_{(x^{\prime},y^{\prime})\in D}|\{x\_{\*}% \colon d(x^{\prime},x\_{\*})\leq R,(x\_{\*},y\_{\*})\in D,y\_{\*}=k\}|}.divide start\_ARG | { italic\_x start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT : italic\_d ( italic\_x , italic\_x start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT ) ≤ italic\_R , ( italic\_x start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT , italic\_y start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT ) ∈ italic\_D , italic\_y start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT = italic\_k } | end\_ARG start\_ARG ∑ start\_POSTSUBSCRIPT ( italic\_x start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT , italic\_y start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT ) ∈ italic\_D end\_POSTSUBSCRIPT | { italic\_x start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT : italic\_d ( italic\_x start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT , italic\_x start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT ) ≤ italic\_R , ( italic\_x start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT , italic\_y start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT ) ∈ italic\_D , italic\_y start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT = italic\_k } | end\_ARG . |  |

The *sensitivity analysis line* allows only *ambiguity rejection*, as it measures the robustness of the predictor under perturbation of either (a) its parameters or (b) the examples (Lewicke et al.,, [2008](https://arxiv.org/html/2107.11277v3#bib.bib133); Hellman,, [1970](https://arxiv.org/html/2107.11277v3#bib.bib101)).
Intuitively, slightly perturbing the predictor’s parameters has major effects on the predictions only for examples that fall in the proximity of the decision boundary: slight variations of the parameters yield slight changes in the decision boundary, which, in turn, may end up flipping the predictions for some examples. Examples of employed perturbations involve adding some noise to the model’s parameter values (e.g., adding a random sample from a normal distribution with null mean and small variance to the weights of a neural network), employing neural networks with a dropout layer (Geifman and El-Yaniv,, [2017](https://arxiv.org/html/2107.11277v3#bib.bib86)), or using a Bayesian simulation ([Perini et al., 2020b,](https://arxiv.org/html/2107.11277v3#bib.bib163) ).
In the case of constructing multiple predictors, a common and simple confidence metric is

|  |  |  |
| --- | --- | --- |
|  | c{h1,…,hM}⁢(x)=1−Var⁢{h1⁢(x),…,hM⁢(x)}subscript𝑐subscriptℎ1…subscriptℎ𝑀𝑥1Varsubscriptℎ1𝑥…subscriptℎ𝑀𝑥c\_{\{h\_{1},\dots,h\_{M}\}}(x)=1-\mathrm{Var}\{h\_{1}(x),\dots,h\_{M}(x)\}italic\_c start\_POSTSUBSCRIPT { italic\_h start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , … , italic\_h start\_POSTSUBSCRIPT italic\_M end\_POSTSUBSCRIPT } end\_POSTSUBSCRIPT ( italic\_x ) = 1 - roman\_Var { italic\_h start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ( italic\_x ) , … , italic\_h start\_POSTSUBSCRIPT italic\_M end\_POSTSUBSCRIPT ( italic\_x ) } |  |

where h1,…,hM

subscriptℎ1…subscriptℎ𝑀h\_{1},\dots,h\_{M}italic\_h start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , … , italic\_h start\_POSTSUBSCRIPT italic\_M end\_POSTSUBSCRIPT are the M𝑀Mitalic\_M predictors constructed by perturbing the parameters, and the variance is scaled to be in [0,1]01[0,1][ 0 , 1 ]. In some cases, one can directly employ an ensemble of M𝑀Mitalic\_M similar predictors and measure the variance of their predictions (Fumera and Roli,, [2004](https://arxiv.org/html/2107.11277v3#bib.bib76); Jiang et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib111)).

Alternatively, one can perturb the test example x𝑥xitalic\_x to be x+ε𝑥𝜀x+\varepsilonitalic\_x + italic\_ε, where ε𝜀\varepsilonitalic\_ε is a random noise such that ‖ε‖norm𝜀\|\varepsilon\|∥ italic\_ε ∥ is small. Intuitively, we want a predictor’s output to remain the same when the example is only slightly perturbed. Thus, the confidence metric should reflect the robustness of hℎhitalic\_h (Mena et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib146); Denis and Hebiri,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib45); Kühne et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib123)), such as

|  |  |  |
| --- | --- | --- |
|  | ch⁢(x)=P⁢(h⁢(x+ε)=h⁢(x)),subscript𝑐ℎ𝑥𝑃ℎ𝑥𝜀ℎ𝑥c\_{h}(x)=P(h(x+\varepsilon)=h(x)),italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) = italic\_P ( italic\_h ( italic\_x + italic\_ε ) = italic\_h ( italic\_x ) ) , |  |

which measures how likely it is that the prediction does not change when the example is perturbed. More generally, we can apply transformations such as rotations and symmetries to the examples (Chen et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib22)). Finally, because choosing a specific value for ε𝜀\varepsilonitalic\_ε is hard, one can use existing approaches to find each example’s minimum ε𝜀\varepsilonitalic\_ε that will alter its predicted label (Devos et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib46)) and derive a confidence metric as a function of the training ε𝜀\varepsilonitalic\_ε.

The *property-based* methods consist of learning the confidence based on some of the predictor’s properties, such as using the leaf configurations of a tree ensemble or the neural network’s weight of specific neurons. This line allows both ambiguity and novelty rejection, depending on the utilized property. These methods tend to exploit heuristic and data-driven intuitions and there are no overarching themes that connect these intuitions.
For instance, Devos et al., ([2023](https://arxiv.org/html/2107.11277v3#bib.bib47)) present a method to detect evasion attacks in tree ensembles. By enumerating the leaves of each tree as oisubscript𝑜𝑖o\_{i}italic\_o start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT, they map each example x𝑥xitalic\_x to the configuration o=(o1,…,oV)∈ℕV𝑜subscript𝑜1…subscript𝑜𝑉superscriptℕ𝑉o=(o\_{1},\dots,o\_{V})\in\mathbb{N}^{V}italic\_o = ( italic\_o start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , … , italic\_o start\_POSTSUBSCRIPT italic\_V end\_POSTSUBSCRIPT ) ∈ blackboard\_N start\_POSTSUPERSCRIPT italic\_V end\_POSTSUPERSCRIPT of the V𝑉Vitalic\_V activated leaves (one per tree) when passing x𝑥xitalic\_x as input to the ensemble. In such output configuration space, they quantify the proximity to the decision boundary by measuring the Hamming distance between the configuration o𝑜oitalic\_o of a test example with ensemble’s prediction y𝑦yitalic\_y and the closest training example’s configuration o′superscript𝑜′o^{\prime}italic\_o start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT with flipped prediction y^≠y^𝑦𝑦\hat{y}\neq yover^ start\_ARG italic\_y end\_ARG ≠ italic\_y:

|  |  |  |
| --- | --- | --- |
|  | OC-score⁢(x)=mino′∈Ry^⁡(∑v=1V𝟙⁢[ov≠ov′])OC-score𝑥subscriptsuperscript𝑜′subscript𝑅^𝑦superscriptsubscript𝑣1𝑉1delimited-[]subscript𝑜𝑣subscriptsuperscript𝑜′𝑣\textsc{OC-score}(x)=\min\_{o^{\prime}\in R\_{\hat{y}}}\left(\sum\_{v=1}^{V}% \mathbbm{1}\left[o\_{v}\neq o^{\prime}\_{v}\right]\right)OC-score ( italic\_x ) = roman\_min start\_POSTSUBSCRIPT italic\_o start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT ∈ italic\_R start\_POSTSUBSCRIPT over^ start\_ARG italic\_y end\_ARG end\_POSTSUBSCRIPT end\_POSTSUBSCRIPT ( ∑ start\_POSTSUBSCRIPT italic\_v = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_V end\_POSTSUPERSCRIPT blackboard\_1 [ italic\_o start\_POSTSUBSCRIPT italic\_v end\_POSTSUBSCRIPT ≠ italic\_o start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_v end\_POSTSUBSCRIPT ] ) |  |

where Ry^subscript𝑅^𝑦R\_{\hat{y}}italic\_R start\_POSTSUBSCRIPT over^ start\_ARG italic\_y end\_ARG end\_POSTSUBSCRIPT is the set of training configurations with flipped predictions. One can derive a confidence metric chsubscript𝑐ℎc\_{h}italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT by, for instance, min-max normalizing the OC-score.
On the other hand, confidence values can also be derived from the weight vectors of a Self-Organizing Map (SOM) ([Gamelas Sousa et al., 2014b,](https://arxiv.org/html/2107.11277v3#bib.bib81) ; Gamelas Sousa et al.,, [2015](https://arxiv.org/html/2107.11277v3#bib.bib79)). Because SOM ’s can approximate the input data density, they approximate p⁢(X=x|Y=k)𝑝𝑋conditional𝑥𝑌𝑘p(X=x|Y=k)italic\_p ( italic\_X = italic\_x | italic\_Y = italic\_k ) with p⁢(w|Y=k,X=x)𝑝formulae-sequenceconditional𝑤𝑌𝑘𝑋𝑥p(w|Y=k,X=x)italic\_p ( italic\_w | italic\_Y = italic\_k , italic\_X = italic\_x ), where w𝑤witalic\_w are the weights of the neural network, using standard statistical techniques, such as the Parzen Windows (Alhoniemi et al.,, [1999](https://arxiv.org/html/2107.11277v3#bib.bib4)).
Moreover, El-Yaniv and Wiener, ([2011](https://arxiv.org/html/2107.11277v3#bib.bib53)) propose a disbelief principle, which computes the confidence function by measuring how much the predictor hℎhitalic\_h deteriorates if retrained with the constraint to predict a specific example x𝑥xitalic\_x differently (i.e., hxsubscriptℎ𝑥h\_{x}italic\_h start\_POSTSUBSCRIPT italic\_x end\_POSTSUBSCRIPT)

|  |  |  |
| --- | --- | --- |
|  | ch⁢(x)=1R⁢(hx)−R⁢(h),subscript𝑐ℎ𝑥1𝑅subscriptℎ𝑥𝑅ℎ\displaystyle c\_{h}(x)=\frac{1}{R(h\_{x})-R(h)},italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) = divide start\_ARG 1 end\_ARG start\_ARG italic\_R ( italic\_h start\_POSTSUBSCRIPT italic\_x end\_POSTSUBSCRIPT ) - italic\_R ( italic\_h ) end\_ARG , |  |

where R⁢(hx)>R⁢(h)>0𝑅subscriptℎ𝑥𝑅ℎ0R(h\_{x})>R(h)>0italic\_R ( italic\_h start\_POSTSUBSCRIPT italic\_x end\_POSTSUBSCRIPT ) > italic\_R ( italic\_h ) > 0.
Finally, the literature presents additional ad-hoc confidence metrics for k𝑘kitalic\_k-NN and Random Forest (Göpfert et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib91); Dalitz,, [2009](https://arxiv.org/html/2107.11277v3#bib.bib42)).

##### Learning the rejection threshold τ𝜏\tauitalic\_τ.

Setting an appropriate rejection threshold τ𝜏\tauitalic\_τ is crucial for having an accurate dependent rejector. At a high level, the threshold is set in three main ways: using domain knowledge, adhering to user-provided constraints, or tuning it empirically based on some objective function.

In some situations, users possess *domain knowledge* that enables setting τ𝜏\tauitalic\_τ to achieve a desired rejection rate ρ𝜌\rhoitalic\_ρ (Le Capitaine and Frélicot,, [2012](https://arxiv.org/html/2107.11277v3#bib.bib130); Pang et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib156)). Setting τ𝜏\tauitalic\_τ in this situation entails (1) ranking training examples based on their confidence level, and (2) setting τ𝜏\tauitalic\_τ such that the desired percentage of predictions are rejected (Sotgiu et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib192)), that is, at

|  |  |  |
| --- | --- | --- |
|  | PX⁢(ch⁢(x)<τ)=ρ.subscript𝑃𝑋subscript𝑐ℎ𝑥𝜏𝜌P\_{X}(c\_{h}(x)<\tau)=\rho.italic\_P start\_POSTSUBSCRIPT italic\_X end\_POSTSUBSCRIPT ( italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) < italic\_τ ) = italic\_ρ . |  |

Note that this approach is also used when evaluating the model performance/rejection trade-off, which needs to measure the model performance for a fixed rejection rate (see Sec. [3.2](https://arxiv.org/html/2107.11277v3#S3.SS2 "3.2 Evaluating the model performance/rejection trade-off. ‣ 3 Evaluating models with rejection ‣ Machine Learning with a Reject Option: A survey")) (Ma et al.,, [2001](https://arxiv.org/html/2107.11277v3#bib.bib141); Heo et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib103); Fumera et al.,, [2003](https://arxiv.org/html/2107.11277v3#bib.bib73)).

In other cases, users provide knowledge as *specific constraints* that should be satisfied (Pietraszek,, [2005](https://arxiv.org/html/2107.11277v3#bib.bib165)). On the one hand, the user may provide an upper bound ℜℜ\mathfrak{R}fraktur\_R for the rejection rate and aim to limit the number of rejections. This results in learning the appropriate τ𝜏\tauitalic\_τ by minimizing the model misclassification risk while adhering to the rejection rate constraint (Zhou et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib226); Pugnana and Ruggieri,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib174), [2023](https://arxiv.org/html/2107.11277v3#bib.bib175))

|  |  |  |
| --- | --- | --- |
|  | τ=arg⁢mint∈[0,1]⁡PX⁢Y⁢(h⁢(x)≠y,ch⁢(x)≥t) subject to PX⁢(ch⁢(x)<t)≤ℜ.formulae-sequence𝜏  subscriptargmin𝑡01subscript𝑃𝑋𝑌formulae-sequenceℎ𝑥𝑦subscript𝑐ℎ𝑥𝑡 subject to subscript𝑃𝑋subscript𝑐ℎ𝑥𝑡ℜ\tau=\operatorname\*{arg\,min}\_{t\in[0,1]}P\_{XY}(h(x)\neq y,c\_{h}(x)\geq t)% \quad\text{ subject to }\quad P\_{X}(c\_{h}(x)<t)\leq\mathfrak{R}.italic\_τ = start\_OPERATOR roman\_arg roman\_min end\_OPERATOR start\_POSTSUBSCRIPT italic\_t ∈ [ 0 , 1 ] end\_POSTSUBSCRIPT italic\_P start\_POSTSUBSCRIPT italic\_X italic\_Y end\_POSTSUBSCRIPT ( italic\_h ( italic\_x ) ≠ italic\_y , italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) ≥ italic\_t ) subject to italic\_P start\_POSTSUBSCRIPT italic\_X end\_POSTSUBSCRIPT ( italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) < italic\_t ) ≤ fraktur\_R . |  |

On the other hand, the user may provide an upper bound 𝔐𝔐\mathfrak{M}fraktur\_M for the proportion of mispredictions, and aim to control the allowable error (Varshney,, [2011](https://arxiv.org/html/2107.11277v3#bib.bib210); Sayedi et al.,, [2010](https://arxiv.org/html/2107.11277v3#bib.bib182)). Thus, one needs to learn τ𝜏\tauitalic\_τ by setting up the complementary problem as before, namely by minimizing the model rejection rate while satisfying the constraints on error (Li and Sethi,, [2006](https://arxiv.org/html/2107.11277v3#bib.bib134); Franc and Prusa,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib65); Franc et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib66))

|  |  |  |
| --- | --- | --- |
|  | τ=arg⁢mint∈[0,1]⁡PX⁢(ch⁢(x)<t) subject to PX⁢Y⁢(h⁢(x)≠y,ch⁢(x)≥t)≤𝔐.formulae-sequence𝜏  subscriptargmin𝑡01subscript𝑃𝑋subscript𝑐ℎ𝑥𝑡 subject to subscript𝑃𝑋𝑌formulae-sequenceℎ𝑥𝑦subscript𝑐ℎ𝑥𝑡𝔐\tau=\operatorname\*{arg\,min}\_{t\in[0,1]}P\_{X}(c\_{h}(x)<t)\quad\text{ subject % to }\quad P\_{XY}(h(x)\neq y,c\_{h}(x)\geq t)\leq\mathfrak{M}.italic\_τ = start\_OPERATOR roman\_arg roman\_min end\_OPERATOR start\_POSTSUBSCRIPT italic\_t ∈ [ 0 , 1 ] end\_POSTSUBSCRIPT italic\_P start\_POSTSUBSCRIPT italic\_X end\_POSTSUBSCRIPT ( italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) < italic\_t ) subject to italic\_P start\_POSTSUBSCRIPT italic\_X italic\_Y end\_POSTSUBSCRIPT ( italic\_h ( italic\_x ) ≠ italic\_y , italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) ≥ italic\_t ) ≤ fraktur\_M . |  |

Moreover, one can generalize this problem by finding the threshold τ𝜏\tauitalic\_τ such that the predictor’s misclassification risk at test time is guaranteed to be bounded with high probability (Geifman and El-Yaniv,, [2017](https://arxiv.org/html/2107.11277v3#bib.bib86)).

Finally, it is possible to set τ𝜏\tauitalic\_τ empirically according to some objective function.
The most common approach is to set a *single global threshold* τ𝜏\tauitalic\_τ, which makes the rejection both simple and transparent, yet usually effective (Fukunaga and Kessell,, [1972](https://arxiv.org/html/2107.11277v3#bib.bib72)).
This is the case for Chow’s rule (Chow,, [1970](https://arxiv.org/html/2107.11277v3#bib.bib23)) which involves learning the optimal τ𝜏\tauitalic\_τ by minimizing the risk function that includes the expected error rate and the rejection rate

|  |  |  |  |
| --- | --- | --- | --- |
|  | τ=arg⁢mint∈[0,1]⁡[∫{x∈𝒳:ch⁢(x)≥t}(1−ch⁢(x))⁢p⁢(x)⁢𝑑x⏟Error rate+t⁢∫{x∈𝒳:ch⁢(x)<t}p⁢(x)⁢𝑑x⏟Rejection rate].𝜏subscriptargmin𝑡01subscript⏟subscriptconditional-set𝑥𝒳subscript𝑐ℎ𝑥𝑡1subscript𝑐ℎ𝑥𝑝𝑥differential-d𝑥Error rate𝑡subscript⏟subscriptconditional-set𝑥𝒳subscript𝑐ℎ𝑥𝑡𝑝𝑥differential-d𝑥Rejection rate\tau=\operatorname\*{arg\,min}\_{t\in[0,1]}\left[{\underbrace{\int\_{\{x\in% \mathcal{X}\colon c\_{h}(x)\geq t\}}(1-c\_{h}(x))\,p(x)\,dx}\_{\textsc{Error rate% }}}+t{\underbrace{\int\_{\{x\in\mathcal{X}\colon c\_{h}(x)<t\}}p(x)\,dx}\_{% \textsc{Rejection rate}}}\right].italic\_τ = start\_OPERATOR roman\_arg roman\_min end\_OPERATOR start\_POSTSUBSCRIPT italic\_t ∈ [ 0 , 1 ] end\_POSTSUBSCRIPT [ under⏟ start\_ARG ∫ start\_POSTSUBSCRIPT { italic\_x ∈ caligraphic\_X : italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) ≥ italic\_t } end\_POSTSUBSCRIPT ( 1 - italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) ) italic\_p ( italic\_x ) italic\_d italic\_x end\_ARG start\_POSTSUBSCRIPT Error rate end\_POSTSUBSCRIPT + italic\_t under⏟ start\_ARG ∫ start\_POSTSUBSCRIPT { italic\_x ∈ caligraphic\_X : italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) < italic\_t } end\_POSTSUBSCRIPT italic\_p ( italic\_x ) italic\_d italic\_x end\_ARG start\_POSTSUBSCRIPT Rejection rate end\_POSTSUBSCRIPT ] . |  | (7) |

However, in real-world scenarios, obtaining complete knowledge of class distributions is challenging, limiting the applicability of Chow’s rule (Shekhar et al.,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib186)).
Thus, in a binary classification case, Tortorella, ([2000](https://arxiv.org/html/2107.11277v3#bib.bib198)) proposes to use two rejection thresholds τ1subscript𝜏1\tau\_{1}italic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT and τ2subscript𝜏2\tau\_{2}italic\_τ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT such that

|  |  |  |  |
| --- | --- | --- | --- |
|  | h⁢(x)={0if ⁢ch⁢(x)<τ1;1if ⁢ch⁢(x)>τ2;®if ⁢τ1≤ch⁢(x)≤τ2ℎ𝑥cases0if subscript𝑐ℎ𝑥subscript𝜏11if subscript𝑐ℎ𝑥subscript𝜏2®if subscript𝜏1subscript𝑐ℎ𝑥subscript𝜏2h(x)=\begin{cases}0&\text{if }c\_{h}(x)<\tau\_{1};\\ 1&\text{if }c\_{h}(x)>\tau\_{2};\\ \text{\textregistered}&\text{if }\tau\_{1}\leq c\_{h}(x)\leq\tau\_{2}\end{cases}italic\_h ( italic\_x ) = { start\_ROW start\_CELL 0 end\_CELL start\_CELL if italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) < italic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ; end\_CELL end\_ROW start\_ROW start\_CELL 1 end\_CELL start\_CELL if italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) > italic\_τ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT ; end\_CELL end\_ROW start\_ROW start\_CELL ® end\_CELL start\_CELL if italic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ≤ italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) ≤ italic\_τ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT end\_CELL end\_ROW |  | (8) |

with ch⁢(x)=P⁢(Y=1|X=x)subscript𝑐ℎ𝑥𝑃𝑌conditional1𝑋𝑥c\_{h}(x)=P(Y=1|X=x)italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) = italic\_P ( italic\_Y = 1 | italic\_X = italic\_x ).
He proposes to learn τ1subscript𝜏1\tau\_{1}italic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT, τ2subscript𝜏2\tau\_{2}italic\_τ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT by optimizing a cost function that is identical to finding the intersection between the cost function and the convex hull of the ROC curve

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
|  | τ1subscript𝜏1\displaystyle\tau\_{1}italic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT | =\displaystyle== | arg⁢mint∈[0,1]⁡P⁢(Y=1)⁢(Cf⁢n−Cr)⁢F⁢N⁢R⁢(t)+P⁢(Y=0)⁢(Ct⁢n−Cr)⁢T⁢N⁢R⁢(t)subscriptargmin𝑡01𝑃𝑌1subscript𝐶𝑓𝑛subscript𝐶𝑟𝐹𝑁𝑅𝑡𝑃𝑌0subscript𝐶𝑡𝑛subscript𝐶𝑟𝑇𝑁𝑅𝑡\displaystyle\operatorname\*{arg\,min}\_{t\in[0,1]}P(Y=1)(C\_{fn}-C\_{r})FNR(t)+P(% Y=0)(C\_{tn}-C\_{r})TNR(t)start\_OPERATOR roman\_arg roman\_min end\_OPERATOR start\_POSTSUBSCRIPT italic\_t ∈ [ 0 , 1 ] end\_POSTSUBSCRIPT italic\_P ( italic\_Y = 1 ) ( italic\_C start\_POSTSUBSCRIPT italic\_f italic\_n end\_POSTSUBSCRIPT - italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT ) italic\_F italic\_N italic\_R ( italic\_t ) + italic\_P ( italic\_Y = 0 ) ( italic\_C start\_POSTSUBSCRIPT italic\_t italic\_n end\_POSTSUBSCRIPT - italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT ) italic\_T italic\_N italic\_R ( italic\_t ) |  | (9) |
|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
|  | τ2subscript𝜏2\displaystyle\tau\_{2}italic\_τ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT | =\displaystyle== | arg⁢mint∈[0,1]⁡P⁢(Y=1)⁢(Ct⁢p−Cr)⁢T⁢P⁢R⁢(t)+P⁢(Y=0)⁢(Cf⁢p−Cr)⁢F⁢P⁢R⁢(t)subscriptargmin𝑡01𝑃𝑌1subscript𝐶𝑡𝑝subscript𝐶𝑟𝑇𝑃𝑅𝑡𝑃𝑌0subscript𝐶𝑓𝑝subscript𝐶𝑟𝐹𝑃𝑅𝑡\displaystyle\operatorname\*{arg\,min}\_{t\in[0,1]}P(Y=1)(C\_{tp}-C\_{r})TPR(t)+P(% Y=0)(C\_{fp}-C\_{r})FPR(t)start\_OPERATOR roman\_arg roman\_min end\_OPERATOR start\_POSTSUBSCRIPT italic\_t ∈ [ 0 , 1 ] end\_POSTSUBSCRIPT italic\_P ( italic\_Y = 1 ) ( italic\_C start\_POSTSUBSCRIPT italic\_t italic\_p end\_POSTSUBSCRIPT - italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT ) italic\_T italic\_P italic\_R ( italic\_t ) + italic\_P ( italic\_Y = 0 ) ( italic\_C start\_POSTSUBSCRIPT italic\_f italic\_p end\_POSTSUBSCRIPT - italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT ) italic\_F italic\_P italic\_R ( italic\_t ) |  | (10) |

where Cf⁢nsubscript𝐶𝑓𝑛C\_{fn}italic\_C start\_POSTSUBSCRIPT italic\_f italic\_n end\_POSTSUBSCRIPT, Cf⁢psubscript𝐶𝑓𝑝C\_{fp}italic\_C start\_POSTSUBSCRIPT italic\_f italic\_p end\_POSTSUBSCRIPT, Ct⁢nsubscript𝐶𝑡𝑛C\_{tn}italic\_C start\_POSTSUBSCRIPT italic\_t italic\_n end\_POSTSUBSCRIPT, and Ct⁢psubscript𝐶𝑡𝑝C\_{tp}italic\_C start\_POSTSUBSCRIPT italic\_t italic\_p end\_POSTSUBSCRIPT are the costs for false negatives, false positives, true negatives, and true positives, while F⁢N⁢R⁢(t)𝐹𝑁𝑅𝑡FNR(t)italic\_F italic\_N italic\_R ( italic\_t ), T⁢N⁢R⁢(t)𝑇𝑁𝑅𝑡TNR(t)italic\_T italic\_N italic\_R ( italic\_t ), T⁢P⁢R⁢(t)𝑇𝑃𝑅𝑡TPR(t)italic\_T italic\_P italic\_R ( italic\_t ) and F⁢P⁢R⁢(t)𝐹𝑃𝑅𝑡FPR(t)italic\_F italic\_P italic\_R ( italic\_t ) are the false negative, false positive, true negative and true positive rates obtained by evaluating the models with the thresholds set to t𝑡titalic\_t.
This approach is theoretically equivalent to Chow’s rule under the Bayesian optimality assumption (Santos-Pereira and Pires,, [2005](https://arxiv.org/html/2107.11277v3#bib.bib181); Du et al.,, [2010](https://arxiv.org/html/2107.11277v3#bib.bib48)). However, when estimating posterior probabilities, Chow’s rule is not suitable, and τ𝜏\tauitalic\_τ should be learned using a cost-based approach (Marrocco et al.,, [2007](https://arxiv.org/html/2107.11277v3#bib.bib144); Kotropoulos and Arce,, [2009](https://arxiv.org/html/2107.11277v3#bib.bib121)).
Different approaches have extended [Tortorella,](https://arxiv.org/html/2107.11277v3#bib.bib198)’s method to address other scenarios (Sansone et al.,, [2001](https://arxiv.org/html/2107.11277v3#bib.bib180)), such as stable formulations of ROC curves for small datasets (Jigang et al.,, [2006](https://arxiv.org/html/2107.11277v3#bib.bib112)), robust and fast-to-retrain rejections for cost-sensitive situations (Dubos et al.,, [2016](https://arxiv.org/html/2107.11277v3#bib.bib49); [Fischer et al., 2015b,](https://arxiv.org/html/2107.11277v3#bib.bib60) ), and tailored solutions for learning meta-classifiers or handling multiple classes (Pietraszek,, [2007](https://arxiv.org/html/2107.11277v3#bib.bib166); Cecotti and Vajda,, [2013](https://arxiv.org/html/2107.11277v3#bib.bib20)).

For tasks requiring a more fine-grained rejection capability, considering *multiple local thresholds* τ1,τ2,…

subscript𝜏1subscript𝜏2…\tau\_{1},\tau\_{2},\ldotsitalic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_τ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT , … (up to a finite number) may be beneficial (Muzzolini et al.,, [1998](https://arxiv.org/html/2107.11277v3#bib.bib149); Kummert et al.,, [2016](https://arxiv.org/html/2107.11277v3#bib.bib124); Krawczyk and Cano,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib122)). Normally, setting local thresholds requires dividing the feature space into J𝐽Jitalic\_J regions 𝒥isubscript𝒥𝑖\mathcal{J}\_{i}caligraphic\_J start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT and setting a (local) threshold in each region. For instance, one can design regions and thresholds by

constructing one region for each class, i.e. 𝒥i={x\*|y\*=i}subscript𝒥𝑖conditional-setsubscript𝑥subscript𝑦𝑖\mathcal{J}\_{i}=\{x\_{\*}\ |\ y\_{\*}=i\}caligraphic\_J start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT = { italic\_x start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT | italic\_y start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT = italic\_i }, which means that the number of regions J𝐽Jitalic\_J equals the number of classes K𝐾Kitalic\_K (Fumera et al.,, [2000](https://arxiv.org/html/2107.11277v3#bib.bib77)); then, one often finds the local threshold by using for each 𝒥isubscript𝒥𝑖\mathcal{J}\_{i}caligraphic\_J start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT the same approach as for global thresholds;

using the Voronoi-cell decomposition, which requires J𝐽Jitalic\_J prototypes wisubscript𝑤𝑖w\_{i}italic\_w start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT to have 𝒥i={x\*|d⁢(x\*,wj)≤d⁢(x\*,wk)⁢∀k≠i}subscript𝒥𝑖conditional-setsubscript𝑥𝑑subscript𝑥subscript𝑤𝑗𝑑subscript𝑥subscript𝑤𝑘for-all𝑘𝑖\mathcal{J}\_{i}=\{x\_{\*}\ |\ d(x\_{\*},w\_{j})\leq d(x\_{\*},w\_{k})\ \forall k\neq i\}caligraphic\_J start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT = { italic\_x start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT | italic\_d ( italic\_x start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT , italic\_w start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ) ≤ italic\_d ( italic\_x start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT , italic\_w start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ) ∀ italic\_k ≠ italic\_i }, for i≤J𝑖𝐽i\leq Jitalic\_i ≤ italic\_J (Villmann et al.,, [2015](https://arxiv.org/html/2107.11277v3#bib.bib214); [Fischer et al., 2015a,](https://arxiv.org/html/2107.11277v3#bib.bib59) ; [Fischer et al., 2015b,](https://arxiv.org/html/2107.11277v3#bib.bib60) ; Fischer and Villmann,, [2016](https://arxiv.org/html/2107.11277v3#bib.bib63)); then, [Fischer et al., 2014a](https://arxiv.org/html/2107.11277v3#bib.bib58)  present a greedy optimization method to adaptively determine local thresholds using a heuristic principle;

setting up an optimization problem that finds the optimal thresholds by assigning different class rejection costs; for instance, in binary classification, Zheng et al., ([2011](https://arxiv.org/html/2107.11277v3#bib.bib225)) proposes to find

|  |  |  |
| --- | --- | --- |
|  | τ1,τ2=arg⁢min0≤t1,t2≤1[PX⁢Y⁢(ch⁢(x)⁢<t1|⁢y=0)⁢Cr,0+PX⁢Y⁢(ch⁢(x)⁢<t2|⁢y=1)⁢Cr,1+PX⁢Y(m(x)≠y)Ce]  subscript𝜏1subscript𝜏2 subscriptargminformulae-sequence0subscript𝑡1subscript𝑡21subscript𝑃𝑋𝑌subscript𝑐ℎ𝑥brasubscript𝑡1𝑦0subscript𝐶  𝑟0subscript𝑃𝑋𝑌subscript𝑐ℎ𝑥brasubscript𝑡2𝑦1subscript𝐶  𝑟1subscript𝑃𝑋𝑌𝑚𝑥𝑦subscript𝐶𝑒\begin{split}\tau\_{1},\tau\_{2}=\operatorname\*{arg\,min}\_{0\leq t\_{1},t\_{2}\leq 1% }\Big{[}&P\_{XY}(c\_{h}(x)<t\_{1}|y=0)C\_{r,0}+P\_{XY}(c\_{h}(x)<t\_{2}|y=1)C\_{r,1}\\ &+P\_{XY}(m(x)\neq y)C\_{e}\Big{]}\end{split}start\_ROW start\_CELL italic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_τ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT = start\_OPERATOR roman\_arg roman\_min end\_OPERATOR start\_POSTSUBSCRIPT 0 ≤ italic\_t start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_t start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT ≤ 1 end\_POSTSUBSCRIPT [ end\_CELL start\_CELL italic\_P start\_POSTSUBSCRIPT italic\_X italic\_Y end\_POSTSUBSCRIPT ( italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) < italic\_t start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT | italic\_y = 0 ) italic\_C start\_POSTSUBSCRIPT italic\_r , 0 end\_POSTSUBSCRIPT + italic\_P start\_POSTSUBSCRIPT italic\_X italic\_Y end\_POSTSUBSCRIPT ( italic\_c start\_POSTSUBSCRIPT italic\_h end\_POSTSUBSCRIPT ( italic\_x ) < italic\_t start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT | italic\_y = 1 ) italic\_C start\_POSTSUBSCRIPT italic\_r , 1 end\_POSTSUBSCRIPT end\_CELL end\_ROW start\_ROW start\_CELL end\_CELL start\_CELL + italic\_P start\_POSTSUBSCRIPT italic\_X italic\_Y end\_POSTSUBSCRIPT ( italic\_m ( italic\_x ) ≠ italic\_y ) italic\_C start\_POSTSUBSCRIPT italic\_e end\_POSTSUBSCRIPT ] end\_CELL end\_ROW |  |

where Cr,0subscript𝐶

𝑟0C\_{r,0}italic\_C start\_POSTSUBSCRIPT italic\_r , 0 end\_POSTSUBSCRIPT and Cr,1subscript𝐶

𝑟1C\_{r,1}italic\_C start\_POSTSUBSCRIPT italic\_r , 1 end\_POSTSUBSCRIPT are the costs for rejecting examples from the negative and positive classes;

optimizing an objective function that accounts for different user-specified class misclassification risks 𝔐1,…,𝔐K

subscript𝔐1…subscript𝔐𝐾\mathfrak{M}\_{1},\dots,\mathfrak{M}\_{K}fraktur\_M start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , … , fraktur\_M start\_POSTSUBSCRIPT italic\_K end\_POSTSUBSCRIPT; Lin et al., ([2022](https://arxiv.org/html/2107.11277v3#bib.bib136)) treat each class independently, setting

|  |  |  |
| --- | --- | --- |
|  | L⁢(tk)=A^⁢(tk)+∑jKλj⁢(𝔐^j−𝔐j)2𝐿subscript𝑡𝑘^𝐴subscript𝑡𝑘superscriptsubscript𝑗𝐾subscript𝜆𝑗superscriptsubscript^𝔐𝑗subscript𝔐𝑗2L(t\_{k})=\hat{A}(t\_{k})+\sum\_{j}^{K}\lambda\_{j}(\hat{\mathfrak{M}}\_{j}-% \mathfrak{M}\_{j})^{2}italic\_L ( italic\_t start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ) = over^ start\_ARG italic\_A end\_ARG ( italic\_t start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ) + ∑ start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_K end\_POSTSUPERSCRIPT italic\_λ start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ( over^ start\_ARG fraktur\_M end\_ARG start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT - fraktur\_M start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ) start\_POSTSUPERSCRIPT 2 end\_POSTSUPERSCRIPT |  |

where A^⁢(tk)^𝐴subscript𝑡𝑘\hat{A}(t\_{k})over^ start\_ARG italic\_A end\_ARG ( italic\_t start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ) is any ambiguity metric, λjsubscript𝜆𝑗\lambda\_{j}italic\_λ start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT is a penalization term that needs to be set to high values to penalize high differences between the model’s misclassification risk 𝔐^^𝔐\hat{\mathfrak{M}}over^ start\_ARG fraktur\_M end\_ARG and the user-specified target.

Although multiple thresholds give more fine-grained control over a rejector’s performance (Laroui et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib129); [Gangrade et al., 2021a,](https://arxiv.org/html/2107.11277v3#bib.bib83) ), this is usually more computationally expensive. However, Fischer et al., ([2016](https://arxiv.org/html/2107.11277v3#bib.bib61)) propose efficient schemes for optimizing local thresholds and show that the computation time can be reduced to polynomial (Boulegane et al.,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib13)).

##### Benefits and drawbacks of a dependent rejector.

Designing a dependent rejector has several *benefits*.
First, the interaction between the predictor and rejector enables both types of rejection, because the rejector learns from the predictor’s output the regions of the feature space where examples are mispredicted or unlikely to fall.
Second, a dependent rejector can extend an existing predictor (including black-box) by simply setting a proper threshold on a confidence measure. Third, it allows the reuse of previously learned models, eliminating the need for costly retraining (Zou et al.,, [2011](https://arxiv.org/html/2107.11277v3#bib.bib230); Tang and Sazonov,, [2014](https://arxiv.org/html/2107.11277v3#bib.bib194)). Fourth, a confidence-based rejection could be improved by considering multiple confidence metrics where each one captures different aspects of the underlying uncertainty (Tax and Duin,, [2008](https://arxiv.org/html/2107.11277v3#bib.bib195)). However, this architecture has potential *drawbacks* as well. First, the quality of the dependent rejector is highly influenced by the quality of the confidence metric, which is usually hard to evaluate. Second, typically a dependent rejector does not affect the predictor’s learning phase. This results in possible sub-optimal predictions of the model with a reject option.

## 6 Integrated rejector

The integrated rejector combines the rejector and predictor into a single model where it is impossible to distinguish between the role of the hℎhitalic\_h and the r𝑟ritalic\_r.
Formally, the model with integrated reject option acts as

|  |  |  |  |
| --- | --- | --- | --- |
|  | m⁢(x)∈𝒴∪{®}.𝑚𝑥𝒴®m(x)\in\mathcal{Y}\cup\{\text{\textregistered}\}.italic\_m ( italic\_x ) ∈ caligraphic\_Y ∪ { ® } . |  | (11) |

Conceptually, this model simply includes ® as an additional output.

This architecture usually needs a unique algorithm for learning predictor and rejector in tandem ([Cortes et al., 2016a,](https://arxiv.org/html/2107.11277v3#bib.bib39) ; [Cortes et al., 2016b,](https://arxiv.org/html/2107.11277v3#bib.bib40) ).
There are two distinct approaches to learning an integrated rejector. The first approach is model-agnostic and involves designing an objective function that penalizes (mis)predictions as well as rejections. The second approach is model-specific and entails integrating a rejector into an existing predictor, where rejection becomes part of the decision-making process.

##### Learning a model-agnostic integrated rejector.

Typically, learning a model that simultaneously makes accurate predictions and rejects the examples that will be otherwise mispredicted can be done by simply designing a specialized objective function (Mozannar and Sontag,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib148)). Then, such a function can be minimized using potentially any existing optimizer, which makes it model-agnostic.
For instance, for classification, a simple cost-based objective for any hypothesis m𝑚mitalic\_m can be expressed as

|  |  |  |
| --- | --- | --- |
|  | L=𝔼p⁢(X,Y)⁢[Cr⁢𝟙m⁢(x)=®⁢(x)+𝟙m⁢(x)∉{y,®}⁢(x)]𝐿subscript𝔼𝑝𝑋𝑌delimited-[]subscript𝐶𝑟subscript1𝑚𝑥®𝑥subscript1𝑚𝑥𝑦®𝑥L=\mathbb{E}\_{p(X,Y)}\left[C\_{r}\mathbbm{1}\_{m(x)=\text{\textregistered}}(x)+% \mathbbm{1}\_{m(x)\not\in\{y,\text{\textregistered}\}}(x)\right]italic\_L = blackboard\_E start\_POSTSUBSCRIPT italic\_p ( italic\_X , italic\_Y ) end\_POSTSUBSCRIPT [ italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT blackboard\_1 start\_POSTSUBSCRIPT italic\_m ( italic\_x ) = ® end\_POSTSUBSCRIPT ( italic\_x ) + blackboard\_1 start\_POSTSUBSCRIPT italic\_m ( italic\_x ) ∉ { italic\_y , ® } end\_POSTSUBSCRIPT ( italic\_x ) ] |  |

with Cr∈(0,1/2]subscript𝐶𝑟012C\_{r}\in(0,1/2]italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT ∈ ( 0 , 1 / 2 ].
For tasks other than classification, ad-hoc loss functions are used, such as those for multilabel classification (Pillai et al.,, [2013](https://arxiv.org/html/2107.11277v3#bib.bib168); Nguyen and Hüllermeier,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib153), [2021](https://arxiv.org/html/2107.11277v3#bib.bib154)), regression (Asif and Minhas,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib7); Kalai and Kanade,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib113)), online learning (Cortes et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib38); Kocak et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib117)), and multi-instance learning (Zhang and Metaxas,, [2006](https://arxiv.org/html/2107.11277v3#bib.bib224)). However, in many cases, surrogate losses are employed to enable efficient optimization, as learning from discrete losses is computationally impractical (Wegkamp,, [2007](https://arxiv.org/html/2107.11277v3#bib.bib216); Grandvalet et al.,, [2009](https://arxiv.org/html/2107.11277v3#bib.bib92); Cao et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib18)). Consequently, the original loss L𝐿Litalic\_L is converted into a convex loss by utilizing surrogate functions ψ:ℝ→ℝ:𝜓→ℝℝ\psi\colon\mathbb{R}\to\mathbb{R}italic\_ψ : blackboard\_R → blackboard\_R, such as the logistic and hinge functions (Ramaswamy et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib177); Zhang et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib223); Bartlett and Wegkamp,, [2008](https://arxiv.org/html/2107.11277v3#bib.bib10)):

|  |  |  |
| --- | --- | --- |
|  | Logistic: ⁢ψ⁢(L)=11+exp⁡(L),Hinge: ⁢ψ⁢(L)={1−1−CrCr⁢L if ⁢L<01−L if ⁢0≤L<10 otherwiseformulae-sequenceLogistic: 𝜓𝐿11𝐿Hinge: 𝜓𝐿cases11subscript𝐶𝑟subscript𝐶𝑟𝐿 if 𝐿01𝐿 if 0𝐿10 otherwise\text{Logistic: }\psi(L)=\frac{1}{1+\exp(L)},\qquad\text{Hinge: }\psi(L)=% \begin{cases}1-\frac{1-C\_{r}}{C\_{r}}L&\text{ if }L<0\\ 1-L&\text{ if }0\leq L<1\\ 0&\text{ otherwise}\end{cases}Logistic: italic\_ψ ( italic\_L ) = divide start\_ARG 1 end\_ARG start\_ARG 1 + roman\_exp ( italic\_L ) end\_ARG , Hinge: italic\_ψ ( italic\_L ) = { start\_ROW start\_CELL 1 - divide start\_ARG 1 - italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT end\_ARG start\_ARG italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT end\_ARG italic\_L end\_CELL start\_CELL if italic\_L < 0 end\_CELL end\_ROW start\_ROW start\_CELL 1 - italic\_L end\_CELL start\_CELL if 0 ≤ italic\_L < 1 end\_CELL end\_ROW start\_ROW start\_CELL 0 end\_CELL start\_CELL otherwise end\_CELL end\_ROW |  |

For the hinge loss to be convex, it is required that Cr≤1/2subscript𝐶𝑟12C\_{r}\leq 1/2italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT ≤ 1 / 2 which is the case for classification as otherwise the cost of rejection would be higher than the cost of random guessing.
Numerous studies in the literature have explored the properties of surrogate loss functions (Yuan and Wegkamp,, [2010](https://arxiv.org/html/2107.11277v3#bib.bib220)), including calibration effects (Ni et al.,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib155); Charoenphakdee et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib21)), estimates of bounds for misclassification risk (Shekhar et al.,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib186); Kato et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib115)), penalization effects in high-dimensional spaces (Wegkamp and Yuan,, [2012](https://arxiv.org/html/2107.11277v3#bib.bib217)), proximity to the optimal Bayes solution (Bounsiar et al.,, [2008](https://arxiv.org/html/2107.11277v3#bib.bib14); [Shen et al., 2020a,](https://arxiv.org/html/2107.11277v3#bib.bib188) ), and convergence rate analysis (Denis and Hebiri,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib45)).

Lastly, one can allocate an extra class K+1𝐾1K+1italic\_K + 1 (commonly known as the *reject class*) for rejection and assign a specific penalization cost Crsubscript𝐶𝑟C\_{r}italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT for predicting such a class. With this setting, there are two main alternatives. In the first case, there are no actual examples belonging to this class. Thus, these approaches design loss functions to enable the classifier to assign on its own a positive score to ambiguous examples (Huang et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib109); Feng et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib54)). For instance, Ziyin et al., ([2019](https://arxiv.org/html/2107.11277v3#bib.bib228)) propose to measure the expected loss as

|  |  |  |
| --- | --- | --- |
|  | L=𝔼p⁢(X,Y)⁢[log⁡(sk⁢(x)+1Cr⁢sK+1⁢(x))],𝐿subscript𝔼𝑝𝑋𝑌delimited-[]subscript𝑠𝑘𝑥1subscript𝐶𝑟subscript𝑠𝐾1𝑥L=\mathbb{E}\_{p(X,Y)}\left[\log(s\_{k}(x)+\frac{1}{C\_{r}}s\_{K+1}(x))\right],italic\_L = blackboard\_E start\_POSTSUBSCRIPT italic\_p ( italic\_X , italic\_Y ) end\_POSTSUBSCRIPT [ roman\_log ( italic\_s start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ( italic\_x ) + divide start\_ARG 1 end\_ARG start\_ARG italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT end\_ARG italic\_s start\_POSTSUBSCRIPT italic\_K + 1 end\_POSTSUBSCRIPT ( italic\_x ) ) ] , |  |

where sk⁢(x)subscript𝑠𝑘𝑥s\_{k}(x)italic\_s start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ( italic\_x ) and sK+1⁢(x)subscript𝑠𝐾1𝑥s\_{K+1}(x)italic\_s start\_POSTSUBSCRIPT italic\_K + 1 end\_POSTSUBSCRIPT ( italic\_x ) are probabilities, respectively, for the class y=k𝑦𝑘y=kitalic\_y = italic\_k and K+1𝐾1K+1italic\_K + 1 (rejection). At a high level, decreasing the rejection cost Crsubscript𝐶𝑟C\_{r}italic\_C start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT results in higher chances of rejection. In the second case, one artificially generates examples xn+1,…,xN

subscript𝑥𝑛1…subscript𝑥𝑁{x\_{n+1},\dots,x\_{N}}italic\_x start\_POSTSUBSCRIPT italic\_n + 1 end\_POSTSUBSCRIPT , … , italic\_x start\_POSTSUBSCRIPT italic\_N end\_POSTSUBSCRIPT (e.g., adversarial examples) and assigns them to the rejection class K+1𝐾1K+1italic\_K + 1. By training a predictor with K+1𝐾1K+1italic\_K + 1 classes, the reject option is naturally incorporated as output, and any (multi-class) predictor can be used for novelty (Vasconcelos et al.,, [1995](https://arxiv.org/html/2107.11277v3#bib.bib212); Singh and Markou,, [2004](https://arxiv.org/html/2107.11277v3#bib.bib191); Urahama and Furukawa,, [1995](https://arxiv.org/html/2107.11277v3#bib.bib201)) or ambiguity rejection (Thulasidasan et al.,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib197); Pang et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib157)).

##### Learning a model-specific integrated rejector.

![Refer to caption](extracted/5422438/svms.png)

In many practical use cases, one may already know that a specific class of models works well within the given context, such as SVM models in medical applications (Hanczar and Dougherty,, [2008](https://arxiv.org/html/2107.11277v3#bib.bib97); Hamid et al.,, [2017](https://arxiv.org/html/2107.11277v3#bib.bib95)). Given a specific predictor, its learning algorithm can be slightly adapted to include the reject option.
For instance, *integrated SVMs* set two (or more) hyperplanes on the feature space and reject all the examples located in between them (Pillai et al.,, [2011](https://arxiv.org/html/2107.11277v3#bib.bib167); Lin et al.,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib135); Zidelmal et al.,, [2012](https://arxiv.org/html/2107.11277v3#bib.bib227)).
Figure [8](https://arxiv.org/html/2107.11277v3#S6.F8 "Figure 8 ‣ Learning a model-specific integrated rejector. ‣ 6 Integrated rejector ‣ Machine Learning with a Reject Option: A survey") shows two common cases to learn the hyperplanes. First, one can parametrize the hyperplane as w⋅x+b±ε=0plus-or-minus⋅𝑤𝑥𝑏𝜀0w\cdot x+b\pm\varepsilon=0italic\_w ⋅ italic\_x + italic\_b ± italic\_ε = 0, with ε≥0𝜀0\varepsilon\geq 0italic\_ε ≥ 0, which results in parallel and equidistant hyperplanes from the decision boundary, where ε𝜀\varepsilonitalic\_ε indicates the distance (Fumera and Roli,, [2002](https://arxiv.org/html/2107.11277v3#bib.bib75)). Learning such hyperplanes requires minimizing the empirical loss

|  |  |  |
| --- | --- | --- |
|  | L=12⁢w⋅w+C⁢∑i=1nl⁢(ξi,ε)−∑i=1nαi⁢[yi⁢(w⋅xi+b)−1+ξi]𝐿⋅12𝑤𝑤𝐶superscriptsubscript𝑖1𝑛𝑙subscript𝜉𝑖𝜀superscriptsubscript𝑖1𝑛subscript𝛼𝑖delimited-[]subscript𝑦𝑖⋅𝑤subscript𝑥𝑖𝑏1subscript𝜉𝑖L=\frac{1}{2}w\cdot w+C\sum\_{i=1}^{n}l(\xi\_{i},\varepsilon)-\sum\_{i=1}^{n}% \alpha\_{i}\left[y\_{i}(w\cdot x\_{i}+b)-1+\xi\_{i}\right]italic\_L = divide start\_ARG 1 end\_ARG start\_ARG 2 end\_ARG italic\_w ⋅ italic\_w + italic\_C ∑ start\_POSTSUBSCRIPT italic\_i = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_n end\_POSTSUPERSCRIPT italic\_l ( italic\_ξ start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT , italic\_ε ) - ∑ start\_POSTSUBSCRIPT italic\_i = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_n end\_POSTSUPERSCRIPT italic\_α start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT [ italic\_y start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ( italic\_w ⋅ italic\_x start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT + italic\_b ) - 1 + italic\_ξ start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ] |  |

where w𝑤witalic\_w is the weight vector, b𝑏bitalic\_b is the intercept of the hyperplane, C𝐶Citalic\_C is a (large) hyperparameter that regulates the importance of the performance/rejection trade-off expressed inside the function l⁢(ξi,ε)𝑙subscript𝜉𝑖𝜀l(\xi\_{i},\varepsilon)italic\_l ( italic\_ξ start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT , italic\_ε ), and αisubscript𝛼𝑖\alpha\_{i}italic\_α start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT are the Lagrangian multipliers. Second, the two hyperplanes can be parametrized as

|  |  |  |
| --- | --- | --- |
|  | w′⋅x+b′=0andw′′⋅x+b′′=0.formulae-sequence⋅superscript𝑤′𝑥superscript𝑏′  0and⋅superscript𝑤′′𝑥superscript𝑏′′0w^{\prime}\cdot x+b^{\prime}=0\quad\text{and}\quad w^{\prime\prime}\cdot x+b^{% \prime\prime}=0.italic\_w start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT ⋅ italic\_x + italic\_b start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT = 0 and italic\_w start\_POSTSUPERSCRIPT ′ ′ end\_POSTSUPERSCRIPT ⋅ italic\_x + italic\_b start\_POSTSUPERSCRIPT ′ ′ end\_POSTSUPERSCRIPT = 0 . |  |

By formulating two distinct optimization problems, one can learn the parameters of these hyperplanes. In this approach, one hyperplane is highly penalized for mispredicting the positive class, while the other one is for the negative class. Essentially, this technique yields two SVMs that have few mispredictions on either class, and examples falling in between the hyperplanes can be naturally rejected (Varshney,, [2006](https://arxiv.org/html/2107.11277v3#bib.bib209)).
With the same approach, one can also learn a OCSVM for each class to reject test examples that lie outside any learned hypersphere (novelty) or within two overlapping hyperspheres (ambiguity) (Lotte et al.,, [2008](https://arxiv.org/html/2107.11277v3#bib.bib139); Loeffel et al.,, [2015](https://arxiv.org/html/2107.11277v3#bib.bib138); Wu et al.,, [2007](https://arxiv.org/html/2107.11277v3#bib.bib218)). Finally, [Gamelas Sousa et al., 2014a](https://arxiv.org/html/2107.11277v3#bib.bib80)  shows that limiting the number of support vectors reduces the computational cost, while still ensuring high performance in most cases.

However, in several cases, more than two SVMs are used. For instance, in multi-label classification one can exploit as many SVMs as the number of labels and fit each hyperplane to discriminate between one class and all the others (Pillai et al.,, [2011](https://arxiv.org/html/2107.11277v3#bib.bib167)). This raises the issue of defining rejection in the regions of intersection between some, but not all, of the hyperplanes. To address this, a natural solution is to utilize a data-replication method (Gamelas Sousa et al.,, [2009](https://arxiv.org/html/2107.11277v3#bib.bib82)). This approach involves replicating the complete dataset for each class k∈𝒴𝑘𝒴k\in\mathcal{Y}italic\_k ∈ caligraphic\_Y, adding a new dimension z𝑧zitalic\_z with the class number, changing the target variable of each replica to a discrete one-vs-all label, and discriminating class k𝑘kitalic\_k from the other classes (Cardoso and Pinto Da Costa,, [2007](https://arxiv.org/html/2107.11277v3#bib.bib19); da Rocha Neto et al.,, [2011](https://arxiv.org/html/2107.11277v3#bib.bib41)).

Finally, *Neural Network models* allow integrating the rejector and predictor into the same structure by modifying their output layers ([Gangrade et al., 2021b,](https://arxiv.org/html/2107.11277v3#bib.bib84) ; Ziyin et al.,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib228)). Geifman and El-Yaniv, ([2019](https://arxiv.org/html/2107.11277v3#bib.bib87)) propose to introduce an additional head mrsubscript𝑚𝑟m\_{r}italic\_m start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT into the network that is dedicated to rejection. Specifically, mrsubscript𝑚𝑟m\_{r}italic\_m start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT is set as a sigmoid function and used such that

|  |  |  |
| --- | --- | --- |
|  | m⁢(x)=® if ⁢mr⁢(x)<0.5.formulae-sequence𝑚𝑥® if subscript𝑚𝑟𝑥0.5m(x)=\text{\textregistered}\quad\text{ if }m\_{r}(x)<0.5.italic\_m ( italic\_x ) = ® if italic\_m start\_POSTSUBSCRIPT italic\_r end\_POSTSUBSCRIPT ( italic\_x ) < 0.5 . |  |

Similar to the SVM case, Gasca A. et al., ([2011](https://arxiv.org/html/2107.11277v3#bib.bib85)) and Mesquita et al., ([2016](https://arxiv.org/html/2107.11277v3#bib.bib147)) measure the disagreement of two Neural Networks trained to prioritize the classes differently. Specifically, they assume a binary classification task and use the output of two neural networks h1subscriptℎ1h\_{1}italic\_h start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT, h2subscriptℎ2h\_{2}italic\_h start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT to predict the positive class if h1⁢(x),h2⁢(x)≥0

subscriptℎ1𝑥subscriptℎ2𝑥
0h\_{1}(x),h\_{2}(x)\geq 0italic\_h start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ( italic\_x ) , italic\_h start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT ( italic\_x ) ≥ 0, the negative class if h1⁢(x),h2⁢(x)<0

subscriptℎ1𝑥subscriptℎ2𝑥
0h\_{1}(x),h\_{2}(x)<0italic\_h start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ( italic\_x ) , italic\_h start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT ( italic\_x ) < 0 and rejection if they disagree on the sign. For this task, they use two weighted Extreme Learning Machines (wELM) (Zong et al.,, [2013](https://arxiv.org/html/2107.11277v3#bib.bib229)), namely two neural networks with Q𝑄Qitalic\_Q hidden neurons that output

|  |  |  |
| --- | --- | --- |
|  | h\*⁢(x)=∑q=1Qwy⁢βq⁢g⁢(aq⋅x+bq)subscriptℎ𝑥superscriptsubscript𝑞1𝑄subscript𝑤𝑦subscript𝛽𝑞𝑔⋅subscript𝑎𝑞𝑥subscript𝑏𝑞h\_{\*}(x)=\sum\_{q=1}^{Q}w\_{y}\beta\_{q}g(a\_{q}\cdot x+b\_{q})italic\_h start\_POSTSUBSCRIPT \* end\_POSTSUBSCRIPT ( italic\_x ) = ∑ start\_POSTSUBSCRIPT italic\_q = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_Q end\_POSTSUPERSCRIPT italic\_w start\_POSTSUBSCRIPT italic\_y end\_POSTSUBSCRIPT italic\_β start\_POSTSUBSCRIPT italic\_q end\_POSTSUBSCRIPT italic\_g ( italic\_a start\_POSTSUBSCRIPT italic\_q end\_POSTSUBSCRIPT ⋅ italic\_x + italic\_b start\_POSTSUBSCRIPT italic\_q end\_POSTSUBSCRIPT ) |  |

where wysubscript𝑤𝑦w\_{y}italic\_w start\_POSTSUBSCRIPT italic\_y end\_POSTSUBSCRIPT is the cost related to the example x𝑥xitalic\_x that belongs to the class y𝑦yitalic\_y, aqsubscript𝑎𝑞a\_{q}italic\_a start\_POSTSUBSCRIPT italic\_q end\_POSTSUBSCRIPT is the weight vector connecting the q𝑞qitalic\_q-th hidden node and the input nodes, bqsubscript𝑏𝑞b\_{q}italic\_b start\_POSTSUBSCRIPT italic\_q end\_POSTSUBSCRIPT is the bias of the q𝑞qitalic\_q-th hidden node and g𝑔gitalic\_g is the activation function. By setting the class misprediction costs, learning the parameters β=(β1,…,βQ)𝛽subscript𝛽1…subscript𝛽𝑄\beta=(\beta\_{1},\dots,\beta\_{Q})italic\_β = ( italic\_β start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , … , italic\_β start\_POSTSUBSCRIPT italic\_Q end\_POSTSUBSCRIPT ) requires using the traditional weighted least square formulation min⁡‖H⁢β−Y‖2superscriptnorm𝐻𝛽𝑌2\min\|H\beta-Y\|^{2}roman\_min ∥ italic\_H italic\_β - italic\_Y ∥ start\_POSTSUPERSCRIPT 2 end\_POSTSUPERSCRIPT so that

|  |  |  |
| --- | --- | --- |
|  | β=(HT⁢W⁢H)−1⁢HT⁢W⁢Y𝛽superscriptsuperscript𝐻𝑇𝑊𝐻1superscript𝐻𝑇𝑊𝑌\beta=(H^{T}WH)^{-1}H^{T}WYitalic\_β = ( italic\_H start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT italic\_W italic\_H ) start\_POSTSUPERSCRIPT - 1 end\_POSTSUPERSCRIPT italic\_H start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT italic\_W italic\_Y |  |

where H𝐻Hitalic\_H is the n×Q𝑛𝑄n\times Qitalic\_n × italic\_Q matrix of activation functions hi⁢q=g⁢(aq⋅xi+bq)subscriptℎ𝑖𝑞𝑔⋅subscript𝑎𝑞subscript𝑥𝑖subscript𝑏𝑞h\_{iq}=g(a\_{q}\cdot x\_{i}+b\_{q})italic\_h start\_POSTSUBSCRIPT italic\_i italic\_q end\_POSTSUBSCRIPT = italic\_g ( italic\_a start\_POSTSUBSCRIPT italic\_q end\_POSTSUBSCRIPT ⋅ italic\_x start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT + italic\_b start\_POSTSUBSCRIPT italic\_q end\_POSTSUBSCRIPT ), W𝑊Witalic\_W is the n×1𝑛1n\times 1italic\_n × 1 matrix of class costs (one per example) and Y𝑌Yitalic\_Y is the target vector. Thus, each network limits one class mispredictions and the region of disagreement is designed to be the rejection region.

##### Benefits and drawbacks of an integrated rejector.

This architecture has two key *benefits*.
First, integrating the predictor and rejector means that both aspects of the model are optimized toward the task at hand.
This can improve the performance of the model with rejection when compared to using other architectures because the predictor’s and the rejector’s components can affect each other.
Second, because it is a unique model, the bias introduced by the model with rejection is potentially less than in the scenario where the predictor and rejector are two different models.
However, this architecture has potential *drawbacks*, as designing such a rejector might not be trivial. First, it requires extensive knowledge about the predictor in order to integrate the reject option. Second, it may require developing a novel algorithm to learn the model with a reject option from data. Finally, it is computationally more expensive than the other architectures, as any changes to the rejector require retraining the entire model, which can be time-consuming (Clertant et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib24); Shpakova and Sokolovska,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib190)).

## 7 Combining multiple rejectors

Most rejectors are tailored towards a single rejection type. However, by combining multiple rejectors one can enable multiple rejections, such as performing both ambiguity and novelty rejection. We distinguish between two types of combinations of rejectors based on whether the rejectors’ rejection regions overlap or not because examples in overlapping regions require deeper analysis (e.g., to specify the underlying rejection type).

First, when rejectors do not overlap (or when we are not interested in the example’s rejection type), one can simply combine the rejection sets by a logical o⁢r𝑜𝑟oritalic\_o italic\_r-rule: reject the example if any of the rejectors rejects it and assign such rejection type (Frélicot,, [1997](https://arxiv.org/html/2107.11277v3#bib.bib67); Suutala et al.,, [2004](https://arxiv.org/html/2107.11277v3#bib.bib193)). For instance, given 𝒵𝒵\mathcal{Z}caligraphic\_Z rejectors r1,r2,…,r𝒵

subscript𝑟1subscript𝑟2…subscript𝑟𝒵r\_{1},r\_{2},\dots,r\_{\mathcal{Z}}italic\_r start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_r start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT , … , italic\_r start\_POSTSUBSCRIPT caligraphic\_Z end\_POSTSUBSCRIPT with thresholds τ1,τ2,…,τ𝒵

subscript𝜏1subscript𝜏2…subscript𝜏𝒵\tau\_{1},\tau\_{2},\dots,\tau\_{\mathcal{Z}}italic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_τ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT , … , italic\_τ start\_POSTSUBSCRIPT caligraphic\_Z end\_POSTSUBSCRIPT, one can combine them into m𝑚mitalic\_m as

|  |  |  |
| --- | --- | --- |
|  | m⁢(x)={®if ⁢∃i≤𝒵:ri⁢(x;h)<τih⁢(x)otherwise𝑚𝑥cases®:if 𝑖𝒵subscript𝑟𝑖  𝑥ℎsubscript𝜏𝑖ℎ𝑥otherwisem(x)=\begin{cases}\text{\textregistered}\quad&\text{if }\exists\,i\leq\mathcal% {Z}\,\colon r\_{i}(x;h)<\tau\_{i}\\ h(x)\quad&\text{otherwise}\end{cases}italic\_m ( italic\_x ) = { start\_ROW start\_CELL ® end\_CELL start\_CELL if ∃ italic\_i ≤ caligraphic\_Z : italic\_r start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ( italic\_x ; italic\_h ) < italic\_τ start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT end\_CELL end\_ROW start\_ROW start\_CELL italic\_h ( italic\_x ) end\_CELL start\_CELL otherwise end\_CELL end\_ROW |  |

Second, when rejectors overlap in some regions a simple o⁢r𝑜𝑟oritalic\_o italic\_r-rule can be insufficient to determine the reason for rejection because each rejector may decide to abstain for a different reason. Typically, existing works carefully select the order to evaluate the rejectors. This is usually done in a multi-step architecture: either by stacking only the rejectors (Frélicot,, [1998](https://arxiv.org/html/2107.11277v3#bib.bib68); Frélicot and Mascarilla,, [2002](https://arxiv.org/html/2107.11277v3#bib.bib69)), or even using multiple models with rejection (Pudil et al.,, [1992](https://arxiv.org/html/2107.11277v3#bib.bib173); Barandas et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib9)). For instance, given 𝒵𝒵\mathcal{Z}caligraphic\_Z rejectors r1,r2,…,r𝒵

subscript𝑟1subscript𝑟2…subscript𝑟𝒵r\_{1},r\_{2},\dots,r\_{\mathcal{Z}}italic\_r start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_r start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT , … , italic\_r start\_POSTSUBSCRIPT caligraphic\_Z end\_POSTSUBSCRIPT with thresholds τ1,τ2,…,τ𝒵

subscript𝜏1subscript𝜏2…subscript𝜏𝒵\tau\_{1},\tau\_{2},\dots,\tau\_{\mathcal{Z}}italic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_τ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT , … , italic\_τ start\_POSTSUBSCRIPT caligraphic\_Z end\_POSTSUBSCRIPT, one can order rejectors by importance and combine them as

|  |  |  |
| --- | --- | --- |
|  | m⁢(x)={®1if ⁢r1⁢(x;h)<τ1;®2if ⁢r1⁢(x;h)≥τ1⁢ and ⁢r2⁢(x;h)<τ2;⋮h⁢(x)if ⁢ri⁢(x;h)≥τi⁢∀i≤𝒵;𝑚𝑥casessubscript®1if subscript𝑟1  𝑥ℎsubscript𝜏1subscript®2if subscript𝑟1  𝑥ℎsubscript𝜏1 and subscript𝑟2  𝑥ℎsubscript𝜏2⋮𝑜𝑡ℎ𝑒𝑟𝑤𝑖𝑠𝑒ℎ𝑥if subscript𝑟𝑖  𝑥ℎsubscript𝜏𝑖for-all𝑖𝒵m(x)=\begin{cases}\text{\textregistered}\_{1}\quad&\text{if }r\_{1}(x;h)<\tau\_{1% };\\ \text{\textregistered}\_{2}\quad&\text{if }r\_{1}(x;h)\geq\tau\_{1}\text{ and }r\_% {2}(x;h)<\tau\_{2};\\ \vdots\\ h(x)\quad&\text{if }r\_{i}(x;h)\geq\tau\_{i}\ \forall\,i\leq\mathcal{Z};\\ \end{cases}italic\_m ( italic\_x ) = { start\_ROW start\_CELL ® start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT end\_CELL start\_CELL if italic\_r start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ( italic\_x ; italic\_h ) < italic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ; end\_CELL end\_ROW start\_ROW start\_CELL ® start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT end\_CELL start\_CELL if italic\_r start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ( italic\_x ; italic\_h ) ≥ italic\_τ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT and italic\_r start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT ( italic\_x ; italic\_h ) < italic\_τ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT ; end\_CELL end\_ROW start\_ROW start\_CELL ⋮ end\_CELL start\_CELL end\_CELL end\_ROW start\_ROW start\_CELL italic\_h ( italic\_x ) end\_CELL start\_CELL if italic\_r start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ( italic\_x ; italic\_h ) ≥ italic\_τ start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ∀ italic\_i ≤ caligraphic\_Z ; end\_CELL end\_ROW |  |

where ®isubscript®𝑖\text{\textregistered}\_{i}® start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT indicates the rejector risubscript𝑟𝑖r\_{i}italic\_r start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT’s type of rejection.

## 8 Applications of machine learning models with rejection

In safety-sensitive domains, making the wrong decision can have serious consequences such as fatal accidents with self-driving cars, major breakdowns in industrial settings or incorrect diagnoses in medical applications. In these domains, rejection can be used to make cautious predictions. However, the number of papers discussing machine learning with rejection in practical applications is still limited. In this section, an overview of these papers is given.

##### Biomedical applications.

Machine learning with rejection is primarily explored in medical applications due to the potential consequences of incorrect decisions (Liu et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib137)). The main focus is on ambiguity rejection for medical diagnosing, specifically the detection and classification of diseases. If the model is confident enough, the detection results are automatically translated into a diagnosis. Otherwise, a medical expert verifies the detection (Kompa et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib118)). For instance, vocal pathologies are detected using voice recording data, where a linear classifier is trained and uncertain predictions are rejected based on a threshold of the derived posterior probability (Kotropoulos and Arce,, [2009](https://arxiv.org/html/2107.11277v3#bib.bib121)). Spine disease diagnosis employs the data-replication method, which predicts only when two biased classifiers agree (Gamelas Sousa et al.,, [2009](https://arxiv.org/html/2107.11277v3#bib.bib82)). Cancer detection, particularly breast tumor detection, benefits from a reject option implemented with an SVM classifier using confidence-based rejection (Guan et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib94)). The rejection thresholds are chosen to limit the rejection rate and reduce manual effort.

Other biomedical applications have also adopted the use of a reject option. Lotte et al., ([2008](https://arxiv.org/html/2107.11277v3#bib.bib139)) conduct an experiment on distinguishing hand movements using brain activity. They employ a separate novelty rejector trained in a supervised manner to discard brain activity associated with other activities. Lewicke et al., ([2008](https://arxiv.org/html/2107.11277v3#bib.bib133)) explore sleep stage scoring with both types of rejection, utilizing confidence metrics derived from a Neural Network classifier’s neural activities. Another sleep stage scoring application utilizes a separate rejector based on Local Outlier Factor (LOF) anomaly scores for novelty rejection, identifying patients who deviate from the training data (Van der Plas et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib204)). Some papers compare the performance of multiple models with rejection to determine the optimal approach for specific biomedical applications. For instance, Kang et al., ([2017](https://arxiv.org/html/2107.11277v3#bib.bib114)) predict the effectiveness of a diabetes drug for individual patients, while Tang and Sazonov, ([2014](https://arxiv.org/html/2107.11277v3#bib.bib194)) investigate the classification of body positions using sensors placed in patients’ shoes. Lastly, a medical application focuses on the analysis of tissue examples, aiming to classify each pixel of tissue images into categories such as bone, fat, or muscle (Condessa et al.,, [2013](https://arxiv.org/html/2107.11277v3#bib.bib27); [Condessa et al., 2015a,](https://arxiv.org/html/2107.11277v3#bib.bib28) ).

##### Engineering applications.

Applications in engineering can also benefit from a reject option. For instance, in the chemical identification of gases, time-series data is processed by two classifiers to classify the observed gas. Classification occurs only when there is agreement between the classifiers, and ambiguous predictions are rejected until consensus is reached (Hatami and Chira,, [2013](https://arxiv.org/html/2107.11277v3#bib.bib100)). A similar ambiguity rejection technique, rejecting when two classifiers disagree, is employed in defect detection in software applications (Mesquita et al.,, [2016](https://arxiv.org/html/2107.11277v3#bib.bib147)). Fault detection in steam generators utilizes a set of one against all SVM classifiers, and rejection is based on the distance to the decision boundary of these classifiers, allowing for both rejection types (Zou et al.,, [2011](https://arxiv.org/html/2107.11277v3#bib.bib230)). Finally, Hendrickx et al., ([2022](https://arxiv.org/html/2107.11277v3#bib.bib102)) employs a separated novelty rejector for vehicle usage profiling.

##### Economics applications.

In the domain of economics, two applications of machine learning with rejection have been proposed, both focused on ambiguity rejection and novelty rejection. The first application uses a Learning Vector Quantization (LVQ) to classify dollar bills by value (Ahmadi et al.,, [2004](https://arxiv.org/html/2107.11277v3#bib.bib3)). Confidence metrics are obtained from the classifier for both types of rejection. The second application investigates a few rejection techniques on top of a predictor to decide whether to grant a loan (Coenen et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib25))

##### Image recognition applications.

Reject options are usually available for analyzing text styles and reading handwritten numbers (Fumera and Roli,, [2004](https://arxiv.org/html/2107.11277v3#bib.bib76)), used for both ambiguity rejection (Xu et al.,, [1992](https://arxiv.org/html/2107.11277v3#bib.bib219); Huang and Suen,, [1995](https://arxiv.org/html/2107.11277v3#bib.bib110); Rahman and Fairhurst,, [1998](https://arxiv.org/html/2107.11277v3#bib.bib176)) and novelty rejection (Lou et al.,, [1999](https://arxiv.org/html/2107.11277v3#bib.bib140); Arlandis et al.,, [2002](https://arxiv.org/html/2107.11277v3#bib.bib6)). These methods employ a confidence-based dependent rejector. Additionally, there is a paper focused on identifying walkers based on their footprints (Suutala et al.,, [2004](https://arxiv.org/html/2107.11277v3#bib.bib193)). Initially, each footprint is individually predicted or rejected, and then the information from three consecutive footprints is combined for the final decision.

## 9 Link to other research areas

This section briefly discusses the fields related to learning with rejection.

### 9.1 Uncertainty quantification

The field of uncertainty quantification (UQ) aims to measure how uncertain a learned model’s predictions are (Gal et al.,, [2017](https://arxiv.org/html/2107.11277v3#bib.bib78)). It distinguishes between two types of uncertainties: aleatoric uncertainty, which is the randomness in the data, and epistemic uncertainty, which is the lack of knowledge. Aleatoric uncertainty arises from non-deterministic relations between features and the target, while epistemic uncertainty can be caused by a small training set or incorrect model bias. For instance, when predicting the outcome of tossing an unfair coin, initially we lack historical data, resulting in high data-epistemic uncertainty. As we observe more coin tosses, data-epistemic uncertainty decreases, but aleatoric uncertainty remains due to the stochastic nature of the coin flip (Senge et al.,, [2014](https://arxiv.org/html/2107.11277v3#bib.bib183)).

These uncertainties are inherently related to rejection. Rejecting examples due to high aleatoric uncertainty falls into the ambiguity rejection scenario. On the other hand, high epistemic uncertainty due to the lack of data may cause either ambiguity or novelty rejection. That is, if an example is similar to the training set but its prediction strongly depends on the choice of the dataset (e.g., close to the predictor’s decision boundary for classification tasks), then this gives rise to an ambiguity rejection.
Alternatively, if an example is dissimilar to any of the training examples, this leads to a novelty rejection.

Methods for UQ can be applied within learning with rejection.
UQ focuses on obtaining (calibrated) estimates that meaningfully convey the level of uncertainty (Kotelevskii et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib120)), which learning with rejection can leverage to allow the model to abstain when the uncertainty is high (Perello-Nieto et al.,, [2017](https://arxiv.org/html/2107.11277v3#bib.bib159); Kompa et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib118)). While calibrated uncertainty estimates are not always necessary for learning with rejection, they can be important. For instance, calibrated uncertainty estimates enable setting an optimal threshold that minimizes the empirical risks (Chow,, [1970](https://arxiv.org/html/2107.11277v3#bib.bib23)).

### 9.2 Anomaly detection

Anomaly detection (Prasad et al.,, [2009](https://arxiv.org/html/2107.11277v3#bib.bib171)) is a Data Mining task aimed at identifying examples that deviate from expected behavior in a dataset. It is closely linked to novelty rejection because anomalies, being rare and substantially different from the training data, fall under the category of novelties (Ulmer and Cinà,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib200); Pimentel et al.,, [2014](https://arxiv.org/html/2107.11277v3#bib.bib169); Markou and Singh,, [2003](https://arxiv.org/html/2107.11277v3#bib.bib143)). Anomaly detectors are often utilized for novelty rejection within a separate rejector architecture.

Adding a reject option to anomaly detectors allows them to abstain from processing examples when a clear decision cannot be made ([Perini et al., 2020b,](https://arxiv.org/html/2107.11277v3#bib.bib163) ; Perini et al.,, [2023](https://arxiv.org/html/2107.11277v3#bib.bib162)). However, enabling this option in unsupervised anomaly detection poses two challenges. First, most confidence metrics assume a supervised setting, relying on measuring the distance to a decision surface. However, in anomaly detection, a hard decision surface may not always exist, necessitating specialized metrics that consider the model bias of the detector ([Perini et al., 2020b,](https://arxiv.org/html/2107.11277v3#bib.bib163) ). Second, the lack of labeled data makes it difficult to train a rejector using standard performance metrics. Instead, unsupervised techniques are employed, leveraging performance metrics that measure the stability of the anomaly detector itself ([Perini et al., 2020a,](https://arxiv.org/html/2107.11277v3#bib.bib161) ).

### 9.3 Active learning

Active learning (Settles,, [2009](https://arxiv.org/html/2107.11277v3#bib.bib184); Fu et al.,, [2013](https://arxiv.org/html/2107.11277v3#bib.bib71); Zhang and Chaudhuri,, [2014](https://arxiv.org/html/2107.11277v3#bib.bib222); Nguyen et al.,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib152)) involves the interaction between a learning algorithm and an oracle who provides feedback to guide the learner. Its purpose is to reduce the need for labeling large amounts of data while still achieving high predictive performance. The algorithms focus on identifying the examples that would be most beneficial for the learner to label, thus minimizing the associated labeling costs.

Active learning and learning with rejection share the focus on uncertain examples (Amin et al.,, [2021](https://arxiv.org/html/2107.11277v3#bib.bib5)). However, they differ in their motivations for addressing uncertainty. In active learning, uncertainty is crucial during training to improve efficiency by minimizing the amount of labeled data required for an accurate model. In contrast, learning with rejection aims to capture uncertainty at test time to prevent mispredictions. Its focus is on avoiding unreliable predictions based on uncertain examples.

Another difference is that outliers are not always considered. For instance, methods based on discriminative learning cannot express low-density regions. Sharma and Bilgic, ([2017](https://arxiv.org/html/2107.11277v3#bib.bib185)) determine uncertain examples based on evidence measures that support the positive (E+1subscript𝐸1E\_{+1}italic\_E start\_POSTSUBSCRIPT + 1 end\_POSTSUBSCRIPT) or negative class (E−1subscript𝐸1E\_{-1}italic\_E start\_POSTSUBSCRIPT - 1 end\_POSTSUBSCRIPT) in binary classification. An example x𝑥xitalic\_x has an uncertain class if E+1⁢(x)≈E−1⁢(x)subscript𝐸1𝑥subscript𝐸1𝑥E\_{+1}(x)\approx E\_{-1}(x)italic\_E start\_POSTSUBSCRIPT + 1 end\_POSTSUBSCRIPT ( italic\_x ) ≈ italic\_E start\_POSTSUBSCRIPT - 1 end\_POSTSUBSCRIPT ( italic\_x ). Two cases are distinguished based on the magnitude of the evidence: if both E+1subscript𝐸1E\_{+1}italic\_E start\_POSTSUBSCRIPT + 1 end\_POSTSUBSCRIPT and E−1subscript𝐸1E\_{-1}italic\_E start\_POSTSUBSCRIPT - 1 end\_POSTSUBSCRIPT are large, the model is uncertain because of strong, but conflicting evidence for both classes, while if both E+1subscript𝐸1E\_{+1}italic\_E start\_POSTSUBSCRIPT + 1 end\_POSTSUBSCRIPT and E−1subscript𝐸1E\_{-1}italic\_E start\_POSTSUBSCRIPT - 1 end\_POSTSUBSCRIPT are small, the model is uncertain because of insufficient evidence for either class. Because both cases assume that a model is uncertain if P⁢(Y|X)≈0.5𝑃conditional𝑌𝑋0.5P(Y|X)\approx 0.5italic\_P ( italic\_Y | italic\_X ) ≈ 0.5 when using a uniform prior, they both correspond to our ambiguity rejection scenario.

Combining active learning with machine learning with rejection could be of great use (Korycki et al.,, [2019](https://arxiv.org/html/2107.11277v3#bib.bib119); Puchkin and Zhivotovskiy,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib172); Shekhar et al.,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib187)). When the interaction with an oracle is possible, it may be of interest to query the rejected test examples. New data types could be identified by novelty rejection, while ambiguity rejection may fine-tune the decision boundary.

### 9.4 Class-incremental / incomplete learning

Typically, learned models assume knowledge of all possible classes during training. However, class-incremental learning focuses on models that adapt during deployment to detect and predict novel classes that were not seen during training.

Novelty rejection and class-incremental learning both operate under an open-world assumption and aim to detect novel examples compared to the training set. However, there are two key differences. First, class-incremental learning specifically targets examples belonging to novel classes, distinguishing them from outliers. In contrast, novelty rejection techniques do not prioritize this distinction. Second, class-incremental learning involves detecting novel class examples and retraining the model to recognize them.

Novelty rejection techniques can be considered in class-incremental learning. Moreover, both techniques can be combined into a single pipeline, by adapting incremental models with novelty rejected examples. For instance, such examples can be used as prototypes in a k-Nearest Neighbors (k-NN) model.

### 9.5 Delegating classifiers

Similar to learning with rejection, the approach of delegation involves the use of a classifier, which only classifies examples with high confidence and delegates the prediction for the remaining examples (Temanni and Nadeem,, [2007](https://arxiv.org/html/2107.11277v3#bib.bib196); Khodra,, [2016](https://arxiv.org/html/2107.11277v3#bib.bib116)). The delegated examples are given to another, more specialized, classifier which makes a prediction (Ferri et al.,, [2004](https://arxiv.org/html/2107.11277v3#bib.bib55); Prasad and Sowmya,, [2008](https://arxiv.org/html/2107.11277v3#bib.bib170)). In contrast, learning with rejection usually assumes that the user will inspect any rejected examples. Furthermore, delegation can be developed as a chain, where the next classifier makes a prediction for the examples for which the previous model was too uncertain (Giraud-Carrier,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib88)).

### 9.6 Meta-learning

Meta-learning, also known as “learning to learn”, explores methods and techniques for automatically learning the characteristics, behaviors, and performance of machine learning models (Bock,, [1988](https://arxiv.org/html/2107.11277v3#bib.bib12); Vanschoren,, [2018](https://arxiv.org/html/2107.11277v3#bib.bib208)). It aims to develop higher-level knowledge that guides the learning process itself (Brazdil et al.,, [2009](https://arxiv.org/html/2107.11277v3#bib.bib15); Gridin,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib93)).

Despite having different goals and levels of abstraction, meta-learning can provide valuable insights and approaches for the context of learning with rejection. For instance, meta-learning algorithms analyze the behavior and performance of classifiers on different datasets to derive general knowledge about their strengths, weaknesses, and limitations (Abbasi et al.,, [2012](https://arxiv.org/html/2107.11277v3#bib.bib2); Tremmel et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib199); Cohen et al.,, [2022](https://arxiv.org/html/2107.11277v3#bib.bib26)). This knowledge can then be used to make informed decisions about when to reject predictions. Moreover, meta-learning algorithms can identify relevant features or attributes that are informative for determining when to reject predictions (Filchenkov and Pendryak,, [2016](https://arxiv.org/html/2107.11277v3#bib.bib57); [Shen et al., 2020b,](https://arxiv.org/html/2107.11277v3#bib.bib189) ). By focusing on important features, rejectors can make more accurate decisions.

## 10 Conclusions and perspectives

We have studied the subfield of machine learning with rejection and provided a higher-level overview of existing research. To conclude, we revisit our key research questions and point to new directions that future research might take.

### 10.1 Research questions revisited

This survey paper is built around eight key research questions, introduced in the introduction. In this section, we revisit each of these questions and briefly summarize our findings.

##### How can we formalize the conditions for which a model should abstain from making a prediction?

In Section [2](https://arxiv.org/html/2107.11277v3#S2 "2 The learning with reject problem setting ‣ Machine Learning with a Reject Option: A survey"), we identify two types of rejections: ambiguity rejection and novelty rejection.
Ambiguity rejection abstains from making a prediction an example falls in a region where the target value is ambiguous (e.g., close to the decision boundary in classification tasks).
This could be due to a non-deterministic true relation between the features and target variable, or due to a hypothesis space that is not able to capture the true relation.
Novelty rejection abstains from making a prediction on examples that are rare with respect to the given training set. For such an example, there is no guarantee that the model correctly extrapolates to this untrained region, making it likely that the model mispredicts the example.

##### How can we evaluate the performance of a model with rejection?

Standard machine learning evaluation is focused on a model’s predictive quality. However, in machine learning with rejection, there exists a trade-off between the predictive quality and the proportion of rejected examples.

In Section [3](https://arxiv.org/html/2107.11277v3#S3 "3 Evaluating models with rejection ‣ Machine Learning with a Reject Option: A survey"), we provide an overview of techniques evaluating both the prediction and rejection quality of models with rejection. We identify three categories: metrics evaluating models with a given rejection rate, metrics evaluating the overall model performance/rejection trade-off, and metrics evaluating models through a cost function.

##### What architectures are possible for operationalizing (i.e., putting this into practice) the ability to abstain from making a prediction?

We categorize machine learning methodologies with rejection in three different architectures, depending on the relationship between the predictor and the rejector: separated, dependent and integrated rejector. These categories are introduced and mapped to the existing literature in Sections [4](https://arxiv.org/html/2107.11277v3#S4 "4 Separated rejector ‣ Machine Learning with a Reject Option: A survey"), [5](https://arxiv.org/html/2107.11277v3#S5 "5 Dependent rejector ‣ Machine Learning with a Reject Option: A survey") and [6](https://arxiv.org/html/2107.11277v3#S6 "6 Integrated rejector ‣ Machine Learning with a Reject Option: A survey").

##### How do we learn models with rejection?

For each architecture, we discuss the main techniques to learn a model with rejection and related these to the existing literature in Sections [4](https://arxiv.org/html/2107.11277v3#S4 "4 Separated rejector ‣ Machine Learning with a Reject Option: A survey"), [5](https://arxiv.org/html/2107.11277v3#S5 "5 Dependent rejector ‣ Machine Learning with a Reject Option: A survey") and [6](https://arxiv.org/html/2107.11277v3#S6 "6 Integrated rejector ‣ Machine Learning with a Reject Option: A survey").
First, the separated rejector is usually learned independently of the predictor.
Second, learning the dependent rejector entails learning for which examples the predictor is likely to mispredict using a confidence function. Both architectures need setting a rejection threshold.
Third, integrated rejector needs a unique algorithm for learning predictor and rejector in tandem. Usually, this architecture relies on designing an objective function.

##### What are the main pros and cons of using a specific architecture?

Each architecture, discussed in Sections [4](https://arxiv.org/html/2107.11277v3#S4 "4 Separated rejector ‣ Machine Learning with a Reject Option: A survey"),[5](https://arxiv.org/html/2107.11277v3#S5 "5 Dependent rejector ‣ Machine Learning with a Reject Option: A survey"), and [6](https://arxiv.org/html/2107.11277v3#S6 "6 Integrated rejector ‣ Machine Learning with a Reject Option: A survey"), offers distinct benefits and drawbacks. Separated rejectors show broad applicability, as they can be combined with any predictor. However, they often yield sub-optimal rejection performance since they do not learn from the predictor’s mispredictions. On the other hand, dependent rejectors have reduced, yet still high, applicability, relying on a specific confidence function learned from the predictor’s output, but they can enhance the rejection quality by leveraging the predictor’s mispredictions. Finally, integrated rejectors necessitate joint design with the predictor, but learning a single model for prediction and rejection improves the overall performance for both prediction and rejection tasks.

##### How can we combine multiple rejectors?

We discuss the combination of multiple rejectors for enabling various types of rejections within a unique model. There are two approaches for combining rejectors. First, when rejectors do not overlap, a logical “or” rule is applied, rejecting an example if any of the rejectors rejects it. Second, when rejectors overlap in some regions and disagree on the type of rejection, a multi-step architecture is used, ordering rejectors by importance to make decisions based on the most relevant rejector.

##### Where does the need for machine learning with rejection methods arise in real-world applications?

On a high level, machine learning with rejection is typically used in applications where incorrect decisions can have severe consequences, both financially and safety-related. These consequences motivate the need for robust and trustworthy machine learning. In Section [8](https://arxiv.org/html/2107.11277v3#S8 "8 Applications of machine learning models with rejection ‣ Machine Learning with a Reject Option: A survey"), we provide an overview of application areas in which machine learning with rejection is already used.

##### How does machine learning with rejection relate to other research areas?

Section [9](https://arxiv.org/html/2107.11277v3#S9 "9 Link to other research areas ‣ Machine Learning with a Reject Option: A survey") shows that machine learning with rejection is closely related to several other subfields of machine learning. This relation sometimes leads to terminology and techniques overlapping or inspired by these other domains. In contrast, other cases show machine learning with rejection from a broader perspective. In this survey, we related machine learning with rejection to uncertainty quantification, anomaly detection, active learning, class-incremental learning, delegating classifiers, and meta-learning.

### 10.2 Future directions

Given its significance for the usage of machine learning in real-world problems and the growing attention for trustworthy AI, we expect machine learning with rejection to remain an active research field. In this section, we briefly discuss three key research directions for which we see a strong need.

##### Standard settings to compare different models with rejection.

A large number of machine learning models with rejection already exist. However, these are typically evaluated on custom or even proprietary data. This makes it difficult to benchmark and compare the different approaches. While some papers use publicly available datasets, there is no standard benchmark set for machine learning with rejection.
Additionally, applying multiple strategies to evaluate the rejector offers a better view of an algorithm’s performance and improves comparability.

##### Partial rejection for machine learning models.

A promising avenue for further exploration is the concept of partial abstention.
Nowadays, machine learning problems often involve seeking elaborated predictions rather than simple scalar or class values as in classification and regression tasks. For instance, in multi-label classification, a prediction for an instance is a subset of possible class labels.
In such cases, the idea of abstaining from a complete prediction can be extended to partial abstention, where the learner delivers predictions on *some but not necessarily all*
class labels, according to its level of certainty (Nguyen and Hüllermeier,, [2020](https://arxiv.org/html/2107.11277v3#bib.bib153)).
This has the key benefit of providing a middle ground between making predictions for the entire structure and completely abstaining from making any predictions.

##### Algorithms enabling models with rejection in domains other than classification.

Most papers on machine learning with rejection study supervised classification problems. Modern machine learning tackles numerous other tasks such as regression, forecasting, and clustering, or even semi-supervised and self-supervised feedback loops. We believe that the rejection can also be of use in such areas. However, since only a handful of relevant studies exist, this requires more attention from the research community.
Future research can also focus on integrating rejection-related variables into statistical frameworks utilized in educational measurement, such as Item Response Theory (IRT). This integration has the potential to improve the precision of item calibration, trait estimation, and the interpretation of test scores. Furthermore, it can provide valuable insights into the psychological aspects of learning, enabling the development of more precise instructional strategies and interventions.

## Declarations

### Funding

Kilian Hendrickx and Dries Van der Plas received funding from VLAIO (Flemish Innovation & Entrepreneurship) through the Baekeland PhD mandates [HBC.2017.0226] (KH) and [HBC.2019.2615] (DV).
Lorenzo Perini received funding from FWO-Vlaanderen, aspirant grant 1166222N.
Jesse Davis is partially supported by the KU Leuven research funds [C14/17/070].
Lorenzo Perini, Jesse Davis and Wannes Meert received funding from the Flemish Government under the “Onderzoeksprogramma Artificiële Intelligentie (AI) Vlaanderen” programme.

### Conflict of interest

The authors declare that they have no conflict of interest.

### Ethics approval

Not applicable

### Consent to participate

Not applicable

### Availability of data and material

Not applicable

### Code availability

Not applicable

### Authors’ contributions

Concept: JD, WM;
Literature Study: KH, LP, DVdP;
Categorization: KH, LP, DVdP, WM, JD;
Writing - original draft preparation: KH, LP, DVdP;
Writing - review and editing: WM, JD;
Writing - revision: LP, WM, JD, DVdP, KH;
Funding acquisition: WM, JD;
Supervision: WM, JD.

## References

![[LOGO]](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)
