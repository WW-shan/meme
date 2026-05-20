![](https://cdn.ncbi.nlm.nih.gov/pmc/pd-medc-pmc-cloudpmc-viewer/production/674d4f95/var/data/static/img/us_flag.svg)

An official website of the United States government

Here's how you know

![](https://cdn.ncbi.nlm.nih.gov/pmc/pd-medc-pmc-cloudpmc-viewer/production/674d4f95/var/data/static/img/icon-dot-gov.svg)

**Official websites use .gov**
 A **.gov** website belongs to an official government organization in the United States.

![](https://cdn.ncbi.nlm.nih.gov/pmc/pd-medc-pmc-cloudpmc-viewer/production/674d4f95/var/data/static/img/icon-https.svg)

**Secure .gov websites use HTTPS**
 A **lock** (  ) or **https://** means you've safely connected to the .gov website. Share sensitive information only on official, secure websites.

[![NCBI home page](https://cdn.ncbi.nlm.nih.gov/pmc/pd-medc-pmc-cloudpmc-viewer/production/674d4f95/var/data/static/img/ncbi-logos/nih-nlm-ncbi--white.svg)](https://www.ncbi.nlm.nih.gov/)

* [Dashboard](https://www.ncbi.nlm.nih.gov/myncbi/)
* [Publications](https://www.ncbi.nlm.nih.gov/myncbi/collections/bibliography/)
* [Account settings](https://www.ncbi.nlm.nih.gov/account/settings/)

* [Journal List](/journals/)
* [User Guide](/about/userguide/)

* [![Download PDF icon](https://cdn.ncbi.nlm.nih.gov/pmc/pd-medc-pmc-cloudpmc-viewer/production/674d4f95/var/data/static/img/file_download.svg)](pdf/nihms-2088989.pdf "Download PDF")

* ## PERMALINK

As a library, NLM provides access to scientific literature. Inclusion in an NLM database does not imply endorsement of, or agreement with, the contents by NLM or the National Institutes of Health.
 Learn more: [PMC Disclaimer](/about/disclaimer/) |  [PMC Copyright Notice](/about/copyright/)

. Author manuscript; available in PMC: 2025 Sep 27.

*Published in final edited form as:* Transact Mach Learn Res. 2024 Oct;2024:dmxMGW6J7N.

# Selective Classification Under Distribution Shifts

[Hengyue Liang](https://pubmed.ncbi.nlm.nih.gov/?term=)

### Hengyue Liang

1Department of Electrical and Computer Engineering, University of Minnesota

Find articles by [Hengyue Liang](https://pubmed.ncbi.nlm.nih.gov/?term=)

1, [Le Peng](https://pubmed.ncbi.nlm.nih.gov/?term=)

### Le Peng

2Department of Computer Science and Engineering, University of Minnesota

Find articles by [Le Peng](https://pubmed.ncbi.nlm.nih.gov/?term=)

2, [Ju Sun](https://pubmed.ncbi.nlm.nih.gov/?term=)

### Ju Sun

3Department of Computer Science and Engineering, University of Minnesota

Find articles by [Ju Sun](https://pubmed.ncbi.nlm.nih.gov/?term=)

3



1Department of Electrical and Computer Engineering, University of Minnesota

2Department of Computer Science and Engineering, University of Minnesota

3Department of Computer Science and Engineering, University of Minnesota

✉

Email: liang656@umn.edu

[PMC Copyright notice](/about/copyright/)

PMCID: PMC12470254  NIHMSID: NIHMS2088989  PMID: [41019465](https://pubmed.ncbi.nlm.nih.gov/41019465/)

## Abstract

In selective classification (SC), a classifier abstains from making predictions that are likely to be wrong to avoid excessive errors. To deploy imperfect classifiers—either due to intrinsic statistical noise of data or for robustness issue of the classifier or beyond—in high-stakes scenarios, SC appears to be an attractive and necessary path to follow. Despite decades of research in SC, most previous SC methods still focus on the ideal statistical setting only, i.e., the data distribution at deployment is the same as that of training, although practical data can come from the wild. To bridge this gap, in this paper, we propose an SC framework that takes into account distribution shifts, termed *generalized selective classification*, that covers label-shifted (or out-of-distribution) and covariate-shifted samples, in addition to typical in-distribution samples, *the first of its kind* in the SC literature. We focus on non-training-based confidence-score functions for generalized SC on deep learning (DL) classifiers, and propose two novel margin-based score functions. Through extensive analysis and experiments, we show that our proposed score functions are more effective and reliable than the existing ones for generalized SC on a variety of classification tasks and DL classifiers. The code is available at <https://github.com/sun-umn/sc_with_distshift>.

## 1. Introduction

In practice, classifiers almost never have perfect accuracy. Although modern classifiers powered by deep neural networks (DNNs) typically achieve higher accuracy than the classical ones, they are known to be unrobust: perturbations of inputs that are inconsequential to human decision making can easily alter DNN classifiers’ predictions ([Carlini et al., 2019](#R3); [Croce et al., 2020](#R9); [Hendrycks & Dietterich, 2018](#R30); [Liang et al., 2023](#R41)), and more generally, shifts in data distribution in deployment from that in training often cause systematic classification errors. These classification errors, regardless of their source, are rarely acceptable for high-stakes applications, such as disease diagnosis in healthcare.

To achieve minimal and controllable levels of classification error so that imperfect and unrobust classifiers can be deployed for high-stakes applications, a promising approach is *selective classification* (SC): samples that are likely to be misclassified are selected, excluded from prediction, and deferred to human decision makers, so that the classification performance on the remaining samples reaches the desired level ([Chow, 1970](#R5); [Franc et al., 2023a](#R17); [Geifman & El-Yaniv, 2017](#R22)). For example, by flagging and passing uncertain patient cases that it tends to mistake on to human doctors, an intelligent medical agent can make confident and correct diagnoses for the rest. This “conservative” classification framework not only saves doctors’ efforts, but also avoids liability due to the agent’s mistakes.

Consider a multiclass classification problem with input space , label space , and training distribution on . For any classifier , there are many potential causes of classification errors. In this paper, we focus on three types of errors that are commonly encountered in practice and are studied extensively, but mostly separately, in the literature.

* `Type A errors`: errors made on *in-distribution* (In-D) samples, i.e., those samples drawn from . These are classification errors discussed in typical statistical learning frameworks ([Mohri et al., 2018](#R47));
* `Type B errors`: errors made on *label-shifted* samples, i.e., those samples with groundtruth labels not from . Since assigns labels from only, it always errs on these samples;
* `Type C errors`: errors made on *covariate-shifted* samples, i.e., samples drawn from a different input distribution where but with groundtruth labels from .

It is clear that in practical deployment of classifiers, samples can come from the wild, and hence `Type A`, `Type B` and `Type C` errors can coexist. In order to ensure the reliable deployment of classifiers in high-stakes applications, we must control the three types of errors, *jointly*. Unfortunately, previous research falls short of a unified treatment of these errors. Classical SC ([Chow, 1970](#R5)) focuses on rejecting samples that cause In-D errors (`Type A`), whereas the current *out-of-distribution (OOD) detection* research ([Yang et al., 2021](#R65); [Park et al., 2023](#R51)) focuses on detecting label-shifted samples (`Type B`). Although [Hendrycks & Gimpel (2016)](#R31); [Granese et al. (2021)](#R28); [Xia & Bouganis (2022)](#R63); [Kim et al. (2023)](#R35) have advocated the simultaneous detection of samples that cause `Type A` and `Type B` errors, their approaches still treat the problem as consisting of two *separate* tasks, reflected in their *separate and independent* performance evaluation on OOD detection and SC. Regarding the challenge posed by `Type C` errors, existing work ([Hendrycks & Dietterich, 2018](#R30); [Croce et al., 2020](#R9)) focuses primarily on obtaining classifiers that are more robust to covariate shifts, not on rejecting potentially misclassified samples due to covariate shifts—the latter, to the best of our knowledge, has not yet been explicitly considered, not to mention joint rejection together with `Type A` and `Type B` errors.

In this paper, our goal is to close the gap and consider, *for the first time*, rejecting all three types of errors in a unified framework. For brevity, we use the umbrella term *distribution shifts* to cover both label shifts and covariate shifts, which are perhaps the most commonly seen types of distribution shifts, with the caveat that practical distribution shifts can also be induced by other sources. So, we call the unified framework considered in this paper *selective classification under distribution shifts, or generalized selective classification*. Another key desideratum is practicality. With the increasing popularity of foundation models and associated downstream few-shot learners ([Brown et al., 2020](#R2); [Radford et al., 2021](#R55); [Yuan et al., 2021](#R69)), accessing massive original training data becomes increasingly more difficult. Moreover, there are numerous high-stakes domains where training data are typically protected due to privacy concerns, such as healthcare and finance. These applied scenarios call for *SC strategies that can work with given pretrained classifiers and do not require access to the training data*, which will be our focus in this paper. **Our contributions** include:

* We advocate a new SC framework, *generalized selective classification*, which rejects samples that could cause `Type A`, `Type B` and `Type C` errors *jointly*, to improve classification performance over the nonrejected samples. With careful review and reasoning, we argue that generalized SC covers and unifies the scope of the existing OOD detection and SC, if *the goal is to achieve reliable classification on the selected samples*. ([Sections 2.3](#S7) and [2.4](#S11))
* Focused on non-training-based (or post-hoc) SC settings, we identify a critical scale-sensitivity issue of several SC confidence scores based on softmax responses ([Section 3.1](#S14)) which are popularly used and reported to be the state-of-the-art (SOTA) methods in the existing SC literature ([Geifman & El-Yaniv, 2017](#R22); [Feng et al., 2023](#R15)).
* We propose two confidence scores based on the raw logits (v.s. the normalized logits, i.e., softmax responses), inspired by the notion of margins ([Section 3.2](#S18)). Through careful analysis ([Section 3.3](#S22)) and extensive experiments ([Section 4](#S24)), we show that our margin-based confidence scores are more reliable for generalized SC on various dataset-classifier combinations, even under moderate distribution shifts.

## 2. Technical background and related work

### 2.1. Selective classification (SC)

Consider a multiclass classification problem with input space , label space , and data distribution on . A selective classifier consists of a predictor and a selector and works as follows:

|  |  |
| --- | --- |
|  | (1) |

for any input . Typical selectors take the form:

|  |  |
| --- | --- |
|  | (2) |

where is a *confidence-score* function, and is a tunable threshold for selection.

### 2.2. Prior work in SC

For a given selective classifier (), its SC performance is often characterized by two quantities:

|  |  |
| --- | --- |
|  | (3) |

Because a high coverage typically comes with a high selection risk, there is always a need for risk-coverage tradeoff in SC. Most of the existing work considers to be the standard 0/1 classification loss ([Chow, 1970](#R5); [El-Yaniv et al., 2010](#R13); [Geifman et al., 2018](#R24)), and we also follow this convention in this paper. A classical cost-based formulation is to optimize the risk-coverage (RC) tradeoff ([Chow, 1970](#R5))

|  |
| --- |
|  |

where is the cost of making a rejection. The optimal selective classifier for this formulation is ([Chow, 1970](#R5); [Franc et al., 2023a](#R17)):

|  |  |
| --- | --- |
|  | (5) |

where is the Bayes optimal classifier and depends on the posterior probabilities for all , which are hard to obtain in practice. Moreover, solutions to two constrained formulations for the RC tradeoff,

|  |  |
| --- | --- |
|  | (6) |

also depend on the posterior probabilities ([Pietraszek, 2005](#R52); [Geifman & El-Yaniv, 2017](#R22); [Franc et al., 2023a](#R17); [El-Yaniv et al., 2010](#R13)).

#### Training-based scores

Due to the intractability of true posterior probabilities in practice, many previous methods focus on learning effective confidence-score functions from training data. They require access to training data and learn parametric score functions, often under cost-based/constrained formulations and their variants for the RC tradeoff. This learning problem can be formulated together with ([Chow, 1970](#R5); [Pietraszek, 2005](#R52); [Grandvalet et al., 2008](#R27); [El-Yaniv et al., 2010](#R13); [Cortes et al., 2016](#R7); [Geifman & El-Yaniv, 2019](#R23); [Liu et al., 2019](#R45); [Huang et al., 2022](#R33); [Gal & Ghahramani, 2016](#R21); [Lakshminarayanan et al., 2017](#R38); [Geifman et al., 2018](#R24); [Maddox et al., 2019](#R46); [Dusenberry et al., 2020](#R12); [Lei, 2014](#R40); [Villmann et al., 2016](#R60); [Corbière et al., 2019](#R6)) or separately from training the classifier ([Jiang et al., 2018](#R34); [Fisch et al., 2022](#R16); [Franc et al., 2023a](#R17)). However, [Feng et al. (2023)](#R15) has recently shown that these training-based scores do not outperform simple non-training-based scores described below.

##### Algorithm 1.

Non-training-based selective classification

|  |
| --- |
| **Require:** A pretrained classifier ; a score function ; a small calibration dataset |
| 1: , compute and |
| 2: Determine a threshold according to the coverage or selection-risk target |
| 3: Deploy the selector based on [Eq. (2)](#FD2). |

[Open in a new tab](table/T1/)

#### Manually designed (non-training-based) scores

This family works with any given classifier and does not assume access to the training set. This is particularly attractive when it comes to modern pretrained large DNN models, e.g., CLIP ([Radford et al., 2021](#R55)), Florence ([Yuan et al., 2021](#R69)), and GPTs ([Brown et al., 2020](#R2)), for which obtaining the original training data and performing retraining are prohibitively expensive, if not impossible, to typical users. [Algorithm 1](#T1) shows a typical use case of SC with non-training-based scores. Different confidence scores have been proposed in the literature. For example, for support vector machines (SVMs), confidence margin (the difference of the top two raw logits) has been used as a confidence score ([Fumera & Roli, 2002](#R20); [Franc et al., 2023a](#R17)); see also [Section 3.2](#S18). For DNN models, *which is our focus*, confidence scores are popularly defined over the *softmax responses* (SRs). Assume that contains the raw logits (RLs) and is the softmax activation. The following three confidence-score functions

|  |  |
| --- | --- |
|  | (7) |

are popularly used in recent work, e.g., [Feng et al. (2023)](#R15); [Granese et al. (2021)](#R28); [Xia & Bouganis (2022)](#R63). Although simple, can easily beat existing training-based methods ([Feng et al., 2023](#R15)). On the other hand, these SR-based score functions generally follow the plug-in principle by assuming that SRs approximate posterior probabilities well ([Franc et al., 2023a](#R17)). Unfortunately, this assumption often does not hold in practice, and bridging this approximation gap is a major challenge for confidence calibration ([Guo et al., 2017](#R29); [Nixon et al., 2019](#R50)). However, [Zhu et al. (2022)](#R71) reveals that recent calibration methods may even degrade SC performance.

### 2.3. SC under distribution shifts: generalized SC

In this paper, we consider SC under distribution shifts, or *generalized selective classification*. Shifts between training and deployment distributions are common in practice and can often cause performance drops in deployment ([Quinonero-Candela et al., 2008](#R53); [Rabanser et al., 2019](#R54); [Koh et al., 2021](#R36)), raising reliability concerns for high-stakes applications in the real world. In this paper, we use the term *distribution shifts* to cover both covariate and label shifts—perhaps the most prevalent forms of distribution shifts (see the beginning of [Section 1](#S1) for their definitions)—jointly. Although the basic set-up for our generalized SC framework remains the same as that of [Eqs. (1)](#FD1) and [(2)](#FD2), we need to modify the definitions for selection risk and coverage in [Eq. (3)](#FD3) to take into account potential distribution shifts:

|  |  |
| --- | --- |
|  | (8) |

where is the original data distribution, is the shifted distribution— may not be the same as due to potential label shifts.[1](#FN1)

#### Out-of-distribution (OOD) detection as a weak form of generalized SC

The goal of OOD detection is to detect and exclude OOD samples ([Yang et al., 2021](#R65)). An ideal OOD detector should perfectly separate In-D and OOD samples:

|  |  |
| --- | --- |
|  | (9) |

##### Algorithm 2.

Typical OOD detection pipeline (e.g., [Sun et al. (2021)](#R58))

|  |
| --- |
| **Require:** An OOD score function ; an In-D calibration dataset and an OOD calibration dataset |
| 1: and , compute and . |
| 2: Compute a threshold using [Eq. (9)](#FD9) by problem-specific target requirements, e.g., a target TPR (true positive rate) value. |
| 3: Deploy the OOD detector according to [Eq. (9)](#FD9). |

[Open in a new tab](table/T2/)

Here, is a confidence-score function indicating the likelihood that the input is an In-D sample, and is again a tunable cutoff threshold. Although by the literal meaning of OOD both covariate and label shifts are covered by , the literature on OOD detection focuses mainly on detecting *label-shifted* samples, i.e., covariate-shifted induced by label shifts ([Liu et al., 2020](#R43); [Sun et al., 2021](#R58); [Wang et al., 2022](#R61); [Sun et al., 2022](#R59)). OOD detection is commonly motivated as an approach to achieving reliable predictions: under the assumption that is induced by label shifts only, any OOD samples will cause misclassification and hence should be excluded—clearly aligned with the goal of SC. [Algorithm 2](#T2) shows the typical use case of OOD (label-shift) detectors, and its similarity to SC shown in [Algorithm 1](#T1) is self-evident. However, OOD detection clearly aims for less than generalized SC in that: (1) even if the OOD detection is perfect, misclassified samples—either as In-D or due to distribution shifts—by imperfect classifiers are not rejected, and (2) practical OOD detectors may fail to perfectly separate In-D and OOD samples, OOD detected but correctly classified In-D samples are still rejected, hurting the classification performance on the selected samples; see [Appendix C](#APP3) for an illustrative example. Therefore, if we are to achieve reliable predictions by excluding samples that are likely to cause errors, we should directly follow the generalized SC instead of the OOD detection formulation.

#### Other related concepts

Besides OOD detection, OOD generalization focuses on correctly classifying In-D and covariate-shifted samples, without considering prediction confidence and selection to improve prediction reliability; open-set recognition (OSR) focuses on correctly classifying In-D samples, as well as flagging label-shifted samples; see [Geng et al. (2020)](#R25) for a comprehensive review. In contrast, generalized SC covers all In-D, label-shifted, and covariate-shifted samples, the widest coverage compared to these related concepts, and targets the most practical and pragmatic metric—classification performance on the selected samples.

#### Prior work on SC with distribution shifts

Although the existing literature on SC is rich ([Zhang et al., 2023](#R70)), research work that considers SC with potential distribution shifts is very recent and focuses only on *label shifts*: [Xia & Bouganis (2022)](#R63); [Kim et al. (2023)](#R35) perform In-D SC and OOD (label shift) detection together with a confidence score that combines an SC score and an OOD score, but they still evaluate the performance of In-D SC and OOD detection *separately*. [Müller et al. (2023)](#R48); Cattelan & Silva empirically show that existing OOD scores are not good enough for SC tasks with covariate/label-shifted samples; Cattelan & Silva proposes ways to refine these scores with the help of additional datasets to optimize performance. [Franc et al. (2024)](#R19) provides theoretical insights on SC with In-D and label-shifted samples. In contrast, we focus on identifying better confidence scores for generalized SC—that covers both In-D and covariate/label-shifted samples and maximizes the utility of the classifier, and unify the evaluation protocol (see [Section 2.4](#S11)).

### 2.4. Evaluation of generalized SC

Since the goal of generalized SC is to identify and exclude misclassified samples, for performance evaluation at a fixed cutoff threshold , it is natural to report the coverage—the portion of samples accepted, and the corresponding selection risk—”accuracy” (taken broadly) on accepted samples. It is clear from [Eqs. (1)](#FD1) and [(2)](#FD2) that for a given pair of classifier and confidence-score function , the threshold can be adjusted to achieve different risk-coverage (RC) tradeoffs. By continuously varying , we can plot a *risk-coverage (RC) curve* [El-Yaniv et al. (2010)](#R13); [Franc et al. (2023a)](#R17) to profile the SC performance of throughout the entire coverage range ; see [Fig. 1](#F1) for an example. Generally, the lower the RC curve, the better the SC performance. To obtain a summarizing metric, it is natural to use the *area under the RC curve* (AURC) ([El-Yaniv et al., 2010](#R13); [Franc et al., 2023a](#R17)). We note that the RC curve and the AURC are also the most widely used evaluation metrics for classical SC—which is not surprising, as the goal of classical SC aligns with that of generalized SC, although generalized SC also allows distribution shifts.

#### Figure 1:

[Open in a new tab](figure/F1/)

Visualization of the *normalized AURC-*—the area in blue divided by the coverage value .

For typical high-stakes applications, such as medical diagnosis, low selection risks are often prioritized over high coverage levels. So, in addition to RC curves and AURC, we also report several partial AURCs to account for potential different needs—*normalized* , where specifies the coverage level, and we normalize the partial area-under-the-curve by the corresponding so that different partial levels can be cross-compared; see [Fig. 1](#F1) for illustration.

Note that RC curves, and hence the associated AURCs and normalized AURC- also, depend on the pair. So, if the purpose is to *compare different confidence-score functions*, should be fixed. [Feng et al. (2023)](#R15) has recently pointed out the abuse of this crucial point in recent training-based SC methods. Thus, it is worth stressing that we *always take and fix pretrained* ‘s when making the comparison between different score functions.

### 2.5. Few words on implementing [Algorithm 1](#T1) in practice

In the practical implementation of generalized SC for high-stakes applications after [Algorithm 1](#T1), it is necessary to select a cutoff threshold based on a calibration set to meet the target coverage, or more likely the target risk level. However, in this paper, we follow most existing work on SC and do not touch on issues such as how the calibration set should be constructed and how the threshold should be selected—we leave these for future work. Our evaluation here, again, as most existing SC work, is only about the *potential* of specific confidence-score functions for generalized SC, measured by the RC curve, AUPC, and normalized AURC-’s, directly on test sets that consist of In-D, OOD, and covariate-shifted samples.

## 3. Our method—margins as confidence scores for generalized SC

Our goal is to design effective confidence-score functions for generalized SC. Again, our focus is on non-training-based scores that can work on any pretrained classifier without access to the training data.

### 3.1. Scale sensitivity of SR-based scores

As discussed in [Section 2.2](#S4), most manually designed confidence scores focus on DNN models and are based on softmax responses (SRs), assuming that SRs closely approximate true posterior probabilities—closing such approximation gaps is the goal of confidence calibration. However, effective confidence calibration remains elusive ([Guo et al., 2017](#R29); [Nixon et al., 2019](#R50)), and the performance of SR-based score functions is sensitive to the scale of raw logits and hence that of SRs, as explained below.

#### A quick numerical experiment

Consider a 4-component mixture-of-Gaussian distribution with means , equal variance , and equal weight 1/4. If we treat each component of the mixture as a class and consider the resulting 4-class classification problem, it is easy to see that the optimal 4-class linear classifier is , with the decision rule ; see [Fig. 2 (a)](#F2) for visualization of the data distribution and decision boundaries (i.e., the lines and ). Moreover, this is also a Bayes optimal classifier as well as the maximum a posterior (MAP) classifier, for our particular problem here. Now, given any input , we consider scaled raw logits for different scale factors and plot the resulting RC curves for , and , respectively; see [Fig. 2 (b)](#F2)–[(d)](#F2). For reference, we also include the RC curves based on the true posterior probabilities (denoted as ), which are available for our simple data model here. We can observe that for SR-based functions (, and ), their RC curves and hence the associated AURC’s vary as changes, and these curves approach a common curve (, which we will explain below) as becomes large.

##### Figure 2:

[Open in a new tab](figure/F2/)

RC curves for **(b)** , **(c)** , and **(d)** , calculated based on scaled (by factor 0.1, 1.0, 2.0, and 4.0, respectively) raw logits from the optimal 4-class linear classifier using data shown in **(a)**. The RC curves for and are also plotted for reference, where is one of our proposed confidence-score functions.

#### Why it happens?

The above observations are not incidental. To see why the curves change with respect to , note that for a given test set and a fixed classifier , the RC curve for any score function is fully determined by the ordering of ’s ([Franc et al., 2023a](#R17)). But this ordering is sensitive to the scale of the raw logits for all three SR-based score functions: , and . Take as an example and consider any sample with its corresponding raw logits sorted in descending order (i.e., ) without loss of generality. Then for any scale factor applied to , we have the score

|  |  |
| --- | --- |
|  | (10) |

This means that the score is determined by all the scaled *logit gaps* ’s. Moreover, due to the inner exponential function, small gaps gain more emphasis as increases, and all gaps receive increasingly more emphasis as decreases. Such a shifted emphasis can easily change the order of scores for two data samples, depending on how different their raw logits are distributed. Clearly, as . We can also make similar arguments for and . Next, for the common asymptotic curve as , we can show the following (proof is deferred to [Appendix B](#APP2)):

**Lemma 3.1.** *Consider the raw logits* , *and without loss of generality assume that they are ordered in descending order without any ties, i.e.*, . *We have that as* ,

|  |
| --- |
|  |

*where ~ means asymptotic equivalence. In particular, all the asymptotic functions increase monotonically with respect to* .

This implies that the asymptotic RC curve as for all three score functions is fully determined by the score function !

#### Implications

The sensitivity of the RC curves, and hence of the performance, of these SR-based scores to the scale of raw logits is disturbing. *It implies that one can simply change the overall scale of the raw logits*—*which does not alter the classification accuracy itself*—*to claim better or worse performance of an SR-based confidence-score function for selective classification, making the comparison of different SR-based scores shaky*. Unfortunately, between the limiting cases and , there is no canonical scaling.

### 3.2. Our method: margin-based confidence scores

To avoid the scale sensitivity caused by the softmax nonlinearity, it is natural to consider designing score functions directly over the raw logits. To this end, we revisit ideas in support vector machines (SVMs).

#### Margins in SVMs

In linear SVMs for binary classification, the classifier takes the form and the confidence in classifying a sample can be assessed by its distance from the supporting hyperplane ([Fumera & Roli, 2002](#R20); [Franc et al., 2023a](#R17)): , which is called the *geometric margin;* see [Appendix A](#APP1) for a detailed review. We can extend the idea to -class linear SVMs. Following the popular joint multiclass SVM formulation ([Crammer & Singer, 2001](#R8)), we consider a linear classifier . Here, and induce hyperplanes, and we can define the signed distance of any sample to the -th hyperplane as: denotes the -th column of and the -th element of ), generalizing the definition for the binary case. However, a single signed distance makes little sense for assessing the classification confidence in multiclass cases, given the typical `argmax` decision rule—e.g., the largest signed distance can be negative. Instead, comparing the distances to all decision hyperplanes seems more reasonable. Thus, we can consider the following *geometric margin* as a confidence-score function:

|  |  |
| --- | --- |
|  | (11) |

where . In other words, it is the difference between the top two signed distances of to all hyperplanes. Intuitively, the larger the geometric margin, the more confident the classifier is in classifying the sample following the largest signed distance—*a clearer winner earns more trust*. Although the interpretation is intuitive, the geometric margin is not popularly used in multiclass SVM formulations, likely due to its non-convexity. Instead, a popular proxy for the geometric margin is the convex *confidence margin:*

|  |  |
| --- | --- |
|  | (12) |

with the decision rule ; see [Appendix A](#APP1). Despite its numerical convenience, the confidence margin loses geometric interpretability compared to the geometric margin, and it can be sensitive to the scaling of . We study both margins in this paper.

#### Margins in DNNs

To extend the idea of margins to a DNN classifier parameterized by , we view all but the final linear layer as a feature extractor, denoted as . So, for each sample , the logit output takes the form , and thus the signed distance of the representation to each decision hyperplane in the representation space is: . Assume sorted signed distances and logits, i.e., and . The geometric margin and the *confidence margin* are defined as

|  |  |
| --- | --- |
|  | (13) |

Note that both and are computed using the *raw logits without softmax normalization;* ’s and ’s may not have the same ordering due to the scale of . In fact, is applied in [LeCun et al. (1989)](#R39) to formulate an empirical rejection rule for a handwritten recognition system, although no detailed analysis or discussion is given on why it is effective. Despite the simplicity of these two notions of margins, we have not found prior work that considers them for SC except for [LeCun et al. (1989)](#R39).

#### Scale-invariance property

An attractive property of margin-based score functions is that their SC performance is *invariant* w.r.t. the scale of raw logits. This is because changing the overall scale of the raw logits does not change the order of scores assigned by either the geometric or the confidence margin. In this regard, margin-based score functions are much more preferred and reliable than SR-based scores for SC. Another interesting point is that the limiting curve depicted in [Fig. 2 (b)](#F2)–[(d)](#F2) is induced by the confidence margin, as is clear from Lemma 3.1 and the discussion following it.

### 3.3. Analysis of rejection patterns

We continue with the toy example in [Section 3.1](#S14) to show another major difference between the SR-based and the margin-based score functions—they have *different rejection patterns for given coverage levels*. We will see that margin-based score functions induce favorable rejection patterns and can hence be used for reliable rejection even under moderate covariate shifts. For comparison, we also consider the maximum raw logit (denoted as ) to show that a single logit in multiclass classification is not a sensible confidence score.

**Case 1:** We use the same setup as in the numerical experiment in [Section 3.1](#S14) (see also [Fig. 2](#F2)), and plot in [Fig. 3 (a-1)](#F3) the RC curves induced by the various confidence-score functions[2](#FN2). It is clear that performs the best. To better understand the difference between and other score functions, we study their rejection patterns: we visualize in [Fig. 3 (b-1)](#F3)&[(c-1)](#F3) the samples rejected at 0.8 coverage for and , respectively; see visualization of other score functions in [Appendix D](#APP4), whose rejection patterns are similar to that of . *An iconic feature of is that it prioritizes rejecting samples closer to decision boundaries, whereas SR-based scores prioritize rejecting samples close to the origin*. Conceptually, the former rejection pattern is favorable, as the goal of SC is exactly to reject uncertain samples on which classifier’s decisions can be shaky. More precisely, the difference in rejection patterns implies at least two things: (1) could be advantageous when most classification errors occur near the decision boundaries; (2) may be superior even when test samples have a moderate level of distribution shifts with respect to training. For example, when the test set has a slightly different than the training set (see Cases 2 & 3 below), mistaken samples due to the shift tend to be close to the decision boundaries and thus can be successfully rejected. [Fig. 3 (d-1)](#F3) plots the histograms of the *robustness radii* (i.e., the distance of a sample to the closest decision boundary) of selected samples at 0.8 coverage, where the robustness radius quantitatively captures the extent of shift SC can tolerate: while the selected samples using uniformly have nonzero robust radii, all other score functions lead to zero robustness radii for the worst samples, implying sensitivity to shifts.[3](#FN3)

#### Figure 3:

[Open in a new tab](figure/F3/)

Further analysis of the numerical example in [Section 3.1](#S14). Case 1, Case 2, and Case 3 correspond to the original dataset in [Section 3.1](#S14), the dataset after small perturbations, and the dataset after substantial perturbations, respectively. Here, (**a-**)’s are the RC curves achieved by different selection scores; (**b-**)’s are visualizations of the samples (one color per class), decision boundaries (dashed blue line) and the rejected samples (black crosses) at coverage 0.8 by ; (**c-**)’s visualize the rejected samples (black crosses) at coverage 0.8 by ; and (**d-**)’s present the histogram of the robustness radius of the selected samples in by all score functions.

Case 2: We keep the same setup as Case 1, except that small perturbations are added on all samples. The perturbations are drawn from a uniform distribution within the interval [−0.5, 0.5] on each dimension of ; see [Fig. 3 (b-2)](#F3), where more samples of different classes are intermingled than before the perturbations are added. Although some misclassified samples have moved far into the bulks of other classes, most of them are still close to the decision boundaries. Therefore, still outperforms other SR-based score functions, as in [Fig. 3 (a-2)](#F3).

Case 3: We continue to increase the magnitudes of perturbations and [Fig. 3 (b-3)](#F3) illustrates the case where the perturbations are drawn from a uniform distribution within the interval [−2, 2]. Now that samples from different classes are well mixed in the 2D space, is no longer superior when the coverage level is high, as shown in [Fig. 3 (a-3)](#F3). However, we argue that Case 3 is less concerning in practice—we probably will never consider deploying a classifier that does not work well at all before SC; see the risk achieved at coverage level 1. Instead of relying on an SC strategy, it is more urgent to improve the base classifier in this case.

#### Summary:

Using the above examples, we have shown that our proposed margin-based score functions are not sensitive to the scale of the raw logits. When the base classifier is reasonable in classifying in-distribution data samples (i.e., achieving low risks at full coverage), margin-based scores are expected to result in good SC performance, even when test samples have low or moderate distribution shifts, as we show empirically in [Section 4](#S24) below.

## 4. Experiments

In this section, we experiment with various multiclass classification tasks and recent DNN classifiers to verify the effectiveness of our margin-based score functions for generalized SC.

### 4.1. Comparison with nontraining-based score functions using pretrained models

#### Setups

We take different pretrained DNN models in various classification tasks and evaluate SC performance on test datasets composed of In-D and distribution-shifted samples jointly. Specifically, our evaluation tasks include (i) `ImageNet` ([Russakovsky et al., 2015](#R56)), the most widely used testbed for image classification, with a covariate-shifted version `ImageNet-C` ([Hendrycks & Dietterich, 2018](#R30)) composed of synthetic perturbations, and `OpenImage-O` ([Wang et al., 2022](#R61)) composed of natural images similar to `ImageNet` but with disjoint labels, i.e., label-shifted samples; (ii) `iWIldCam` ([Beery et al., 2020](#R1)) test set provides two subsets of animal images taken at different geo-locations, where one is the same as the training set serving as In-D and the other at different locations as a natural covariate-shifted version; (iii) `Amazon` ([Ni et al., 2019](#R49)) test set provides two subsets of review comments by different users, producing In-D and natural covariate-shifted test samples for a language sentiment classification task; (iv) `CIFAR-10` ([Krizhevsky et al., 2009](#R37)), a small image classification dataset commonly used in previous training-based SC works, together with `CIFAR-10-C` (perturbed `CIFAR-10`) and `CIFAR-100` (with disjoint labels from `CIFAR-10`), popularly used covariate-shifted and label-shifted versions of `CIFAR-10`. [Tables 1](#T7) and [2](#T8) summarize the pretrained models and datasets.

##### Table 1:

Summary of the pretrained classifiers used for the various classification tasks

| Task | Model Name | Source | Note |
| `ImageNet` | EVA ([Fang et al., 2023](#R14)) | `timm`  [6](#FN6) | Top-1 acc. 88.76 % |
| ConvNext ([Liu et al., 2022](#R44)) | Top-1 acc. 86.25 % |
| VOLO ([Yuan et al., 2022](#R68)) | Top-1 acc. 85.56 % |
| ResNext ([Xie et al., 2017](#R64)) | Top-1 acc. 85.54 % |
| `iWildCam` | FLYP ([Goyal et al., 2023](#R26)) | Official source code[7](#FN7) | Ranked on `WILDS` ([Koh et al., 2021](#R36)) |
| `Amazon` | LISA ([Yao et al., 2022](#R67)) | Official source code[8](#FN8) | Ranked on `WILDS` |
| `CIFAR & ImageNet` | ScNet ([Geifman & El-Yaniv, 2019](#R23)) | `PyTorch re-implementation`  [9](#FN9) | Training-based SC. |

[Open in a new tab](table/T7/)

##### Table 2:

Summary of In-D and distribution-shifted datasets used for our SC evaluation

| Task | In-D (split) | classes - samples | Shift-Cov | samples | Shift-Label | samples |
| `ImageNet` | `ILSVRC-2012` (’val’) | 1000 – 50,000 | `ImageNet-C` (severity 3) \*All types of corruptions | 50,000 × 19 | `OpenImage-O` | 17,256 |
| `iWildCam` | `iWildCam` (’id\_test’) | 178 – 8154 | `iWildCam` (’ood\_test’) | 42791 | N/A | N/A |
| `Amazon` | `Amazon` (’id\_test’) | 5 – 46,950 | `Amazon` (’test’) | 100,050 | N/A | N/A |
| `CIFAR` | `CIFAR-10` (’val’) | 10 – 10,000 | `CIFAR-10-C` (severity 3) \*All types of corruptions | 10,000 × 19 | `CIFAR-100` | 10,000 |

[Open in a new tab](table/T8/)

#### Confidence-score functions for comparison

In addition to and introduced in [Eq. (7)](#FD7) and our proposed margin-based scores and in [Eq. (13)](#FD14), we also consider several recent post-hoc OOD detection scores[4](#FN4): (i) : the maximum raw logit ([Hendrycks et al., 2019](#R32)); (ii) Energy: log-sum-exponential aggregation (i.e., smooth approximation to the maximum raw logit) of the raw logits ([Liu et al., 2020](#R43)); (iii) KNN: a score composed of the distances from a test data point to the nearest neighbors of the training set in the raw logit space ([Sun et al., 2022](#R59)); (iv) ViM—a score composed of the residual of a test sample from the principal components estimated in the feature space prior to the raw logits using training data ([Wang et al., 2022](#R61)); and (v) SIRC—a composite score of the softmax response and OOD detection scores ([Xia & Bouganis, 2022](#R63)). **We note that** KNN, ViM, and SIRC all contain hyperparameters that are determined by the training data. To minimize the gap with our ‘nontraining-based’ setup, we randomly sample a small number of data points[5](#FN5) from the In-D test set to tune their hyperparameters, respectively. Also, note that KNN has an additional hyperparameter that is independent of the statistics of the dataset. Empirically, we find KNN’s performance is very sensitive to the choice of , the task, and the classifier. Therefore, in this paper, we use (the empirical best) by default for KNN and provide an ablation analysis for KNN for each experiment in [Appendix H](#APP8).

#### Evaluation metrics

We report both the RC curves and the AURC- where as discussed in [Section 2.4](#S11). Note that when plotting the RC curves, we omit because it almost overlaps with , which is also observed by [Xia & Bouganis (2022)](#R63).

#### Results on ImageNet

We show in [Fig. 4](#F4) the RC curves of the various score functions on the pretrained model **EVA**, for different combinations of subsets of test data, as summarized in [Table 3](#T9). The most striking is in [Fig. 4(c)](#F4), which collects the results for evaluation on mixup of In-D and label-shifted samples: except for and KNN, the selection risks of other score functions do not follow a monotonic decreasing trend as coverage decreases. As coverage approaches zero, their selection risks spike up, almost to the risk level at full coverage (i.e., error rate on the whole set). This is because the other score functions do not indicate prediction confidence well in this setting and hence fail to sufficiently separate right and wrong predictions—during rejection, both right and wrong predictions are rejected indiscriminately. On the other hand, are better than KNN in separating correct and wrong predictions when there are no label-shifted samples, as shown in [Fig. 4 (a)](#F4)&[(b)](#F4). As a result, and have the best overall performance when In-D, covariate-shifted and label-shifted samples coexist, as shown in [Fig. 4 (d)](#F4). Also, see [Table 3](#T9) for numerical confirmation of the above observations, where in all cases and are the best or comparable to the best-performing among all score functions. We present the SC results of other `ImageNet` models in [Appendix G](#APP7); our margin-based score functions still stand as the best-performing among all.

##### Figure 4:

[Open in a new tab](figure/F4/)

RC curves of different confidence-score functions on the model **EVA** for `ImageNet`. **(a)-(d)** are RC curves evaluated using samples from **(a)** In-D samples only, **(b)** In-D and covariate-shifted samples only, **(c)** In-D and label-shifted samples only, and **(d)** all samples, respectively. We group the curves by whether they are originally proposed for SC setups (solid lines) or for OOD detection (dashed lines).

##### Table 3:

Summary of AURC- for [Fig. 4](#F4). The AURC numbers are *on the* 10−2 *scale—the lower, the better*. The score functions proposed for SC are highlighted in gray, and the rest are originally for OOD detection. The best AURC numbers for each coverage level are highlighted in bold, and the and best scores are underlined.

| `ImageNet` - EVA | In-D | In-D + Shift (Cov) | In-D + Shift (Label) | In-D + Shift (both) |
|  | 0.1 | 0.5 | 1 | 0.1 | 0.5 | 1 | 0.1 | 0.5 | 1 | 0.1 | 0.5 | 1 |
|  | **0.16** | **0.53** | **2.39** | **0.24** | **0.96** | **4.77** | **1.04** | 3.34 | 11.7 | **0.34** | **1.20** | **5.43** |
|  | 0.27 | 0.59 | 2.43 | 0.37 | 1.02 | 4.78 | 1.20 | 3.35 | 11.6 | 0.48 | 1.26 | **5.43** |
| SIRC | 2.23 | 2.07 | 3.36 | 3.71 | 3.06 | 5.83 | 15.8 | 8.88 | 13.7 | 4.61 | 3.53 | 6.52 |
|  | 3.20 | 2.36 | 3.38 | 4.52 | 3.66 | 5.93 | 13.1 | 7.52 | 12.6 | 5.21 | 3.75 | 6.56 |
|  | 4.28 | 3.13 | 4.04 | 6.24 | 4.66 | 7.00 | 16.0 | 9.19 | 13.4 | 7.04 | 5.10 | 7.61 |
|  | 3.22 | 2.38 | 3.40 | 4.55 | 3.40 | 6.00 | 13.2 | 7.55 | 12.6 | 5.24 | 3.78 | 6.61 |
|  | 5.53 | 4.05 | 4.57 | 8.48 | 6.04 | 7.64 | 21.1 | 11.9 | 14.9 | 9.53 | 6.59 | 8.33 |
| Energy | 8.13 | 6.60 | 6.90 | 12.8 | 10.3 | 11.1 | 27.3 | 16.6 | 18.1 | 14.1 | 11.0 | 11.8 |
| KNN | 0.99 | 2.27 | 4.58 | 1.22 | 2.89 | 6.78 | 1.18 | **3.23** | **10.8** | 1.24 | 2.98 | 7.16 |
| ViM | 5.48 | 7.11 | 8.31 | 5.31 | 8.05 | 10.4 | 5.83 | 7.89 | 13.4 | 5.35 | 8.12 | 10.7 |

[Open in a new tab](table/T9/)

#### Results on iWildCam & Amazon

We report in [Fig. 5](#F5) and [Table 4](#T10) the SC performance of different score functions on `iWildCam` and `Amazon`. Similar to the `ImageNet` experiment above, scores designed for OOD detection (, Energy, KNN and ViM) do not have satisfactory performance in SC. By contrast, existing SR-based scores ( and ) all demonstrate better SC potential than OOD score functions, and our margin-based score functions ( and ) perform on par with the SR-based scores.

##### Figure 5:

[Open in a new tab](figure/F5/)

RC curves of different confidence-score functions on the model **FLYP** for iWildCam and the model **LISA** for Amazon. **(a)&(c)** are RC curves evaluated using In-D samples only and **(b)&(d)** are RC curves evaluated using both In-D and covariate-shifted samples.

##### Table 4:

Summary of AURC- for [Fig. 5](#F5). The AURC numbers are *on the scale—the lower, the better*. The score functions proposed for SC are highlighted in gray, and the rest are originally for OOD detection. The best AURC numbers for each coverage level are highlighted in bold, and the and best scores are underlined.

| `iWildCam`- FYLP | `Amazon` - LISA |
| In-D | In-D + Shift (Cov) | In-D | In-D + Shift (Cov) |
|  | 0.1 | 0.5 | 1 | 0.1 | 0.5 | 1 | 0.1 | 0.5 | 1 | 0.1 | 0.5 | 1 |
|  | 1.63 | 3.88 | 10.2 | 1.84 | **3.21** | 10.0 | **1.11** | 5.31 | 12.5 | **1.83** | 6.91 | 14.2 |
|  | 1.63 | 3.88 | 10.1 | 1.84 | **3.21** | 10.0 | 1.13 | 5.51 | 12.8 | 1.86 | 7.15 | 14.6 |
| SIRC | **1.45** | **3.72** | **9.84** | 1.38 | 3.5 | **9.94** | 1.14 | 5.09 | 12.2 | 1.88 | 6.66 | 13.9 |
|  | **1.45** | 3.87 | 10.0 | 1.38 | 3.61 | 10.1 | 1.14 | 5.13 | 12.3 | 1.88 | 6.70 | 14.0 |
|  | 1.46 | 4.03 | 10.6 | **1.34** | 3.94 | 10.6 | 1.15 | **5.06** | **12.1** | 1.89 | **6.61** | **13.8** |
|  | **1.45** | 3.87 | 10.1 | 1.38 | 3.62 | 10.1 | 1.14 | 5.13 | 12.2 | 1.88 | 6.70 | 13.9 |
|  | 29.1 | 21.4 | 24.7 | 25.5 | 24.8 | 27.9 | 1.26 | 5.21 | 12.5 | 1.98 | 6.88 | 14.4 |
| Energy | 35.2 | 28.3 | 29.9 | 36.1 | 33.2 | 34.4 | 1.26 | 5.37 | 12.8 | 1.98 | 6.88 | 14.4 |
| KNN | 6.40 | 11.1 | 15.3 | 8.16 | 5.10 | 10.7 | 12.1 | 14.3 | 18.2 | 16.1 | 16.5 | 20.1 |
| ViM | 13.4 | 10.7 | 15.7 | 6.98 | 6.47 | 12.2 | 2.33 | 8.72 | 15.0 | 3.55 | 10.4 | 16.7 |

[Open in a new tab](table/T10/)

### 4.2. Comparison with a training-based confidence-score function

We also compare with a training-based method, ScNet ([Geifman & El-Yaniv, 2019](#R23)). ScNet consists of a selection network and a classifier that are structurally *decoupled* and trained together, allowing us to perform a faithful comparison of selection scores with a fixed classifier[10](#FN10). As shown above, score functions designed for OOD detection perform poorly for generalized SC, so here we focus on comparing our margin-based and SR-based score functions with ScNet. We first train ScNet using the training set of `CIFAR-10` and `ImageNet`, respectively; see [Appendix F](#APP6) for training details. After training, we fix both the classification and the selection heads and compute the scores and selection risks using the test setup shown in [Table 2](#T8): (i) the ScNet selection score is taken directly from the selection head, and (ii) the margin-based and SR-based scores are computed using the classification head.

#### Results

We show in [Fig. 6](#F6) the RC curves achieved using ScNet, SR-based, and margin-based scores. For the `CIFAR` experiment shown in [Fig. 6 (a)](#F6)&[(b)](#F6), ScNet and perform comparably and are better than and SIRC, whereas for the `ImageNet` experiment in [Fig. 6 (c)](#F6)&[(d)](#F6), and SIRC perform comparably and are better than ScNet.[11](#FN11) Surprisingly, ScNet does not always lead to the best performance, even if it has access to training data. However, our margin-based scores consistently exhibit good SC performance.

##### Figure 6:

[Open in a new tab](figure/F6/)

RC curves of different confidence-score functions on the model **ScNet** for CIFAR and `ImageNet`. **(a)&(c)** are RC curves evaluated using In-D samples only and **(b)&(d)** are RC curves evaluated using both In-D and covariate-shifted samples.

### 4.3. Summary of experimental results

From all above experiments, we can conclude that (i) existing nontraining-based score functions for OOD detection do not perform well for generalized SC, not helping achieve reliable classification performance after rejecting low-confidence samples, and (ii) our proposed margin-based score functions and consistently perform comparably to or better than existing SR-based scores on all DL models we have tested, especially in the low-risk regime, which is of particular interest for high-stakes problems. These confirm the superiority of and as effective confidence-score functions for SC even under moderate distribution shifts for risk-sensitive applications.

In most of our experiments, and perform similarly; only in rare cases, e.g. [Fig. 5 (a)](#F5) and [Fig. 6 (b)](#F6), slightly outperforms . However, we do not think it is sufficient to conclude that is better than , or vise versa. Recall how and are defined in [Eqs. (11)](#FD12) and [(12)](#FD13) and their associated decision rules, the current practice of training DL classifiers is in favor of [12](#FN12). Thus, understanding the difference in behavior of and is likely to also involve investigation of the training process, which we will leave for future work.

## 5. Conclusion and discussion

In this paper, we have proposed *generalized selective classification*, a new selective classification (SC) framework that allows distribution shifts. This is motivated by the pressing need to achieve reliable classification for real-world, risk-sensitive applications where data can come from the wild in deployment. Generalized SC *covers* and *unifies* existing selective classification and out-of-distribution (OOD) detection, and we have proposed two margin-based score functions for generalized SC, and , which are not based on training: they are compatible for any given pretrained classifiers. Through our extensive analysis and experiments, we have shown the superiority of and over numerous recently proposed non-training-based score functions for SC and OOD detection. As the first work that touches on generalized SC, our paper can inspire several lines of future research, including at least: (i) to further improve the SC performance, one can try to align the training objective with our SC confidence-score functions here, i.e., promoting large margins; (ii) in this paper, we only consider the case where all classes are treated equally, while practical generalized SC might entail different rejection weights and costs for different classes, e.g., medical diagnosis of diseases with different levels of health implications; (iii) last but not least, finding better confidence-score functions. We hope that our small step here stimulates further research on generalized SC, bridging the widespread gaps between exploratory AI development and reliable AI deployment for practical high-stakes applications.

## Acknowledgments

Liang H. and Sun J. are partially supported by NIH fund R01NS131314. Peng L. and Sun J. are partially supported by NIH fund R01CA287413. The authors acknowledge the Minnesota Supercomputing Institute (MSI) at the University of Minnesota for providing resources that contributed to the research results reported in this article. The content is solely the responsibility of the authors and does not necessarily represent the official views of the National Institutes of Health. This research is also part of AI-CLIMATE: “AI Institute for Climate-Land Interactions, Mitigation, Adaptation, Tradeoffs and Economy,” and is supported by USDA National Institute of Food and Agriculture (NIFA) and the National Science Foundation (NSF) National AI Research Institutes Competitive Award no. 2023-67021-39829.

## A. Linear SVM and margins

We first consider binary classification. Assume training set , where and for notational simplicity, we assume that an extra 1 has been appended to the original feature vectors so that we only need to consider the homogeneous form of the predictor: . The basic idea of SVM is to maximize the worst signed geometric margin, *which makes sense no matter whether the data are separable or not:*

|  |  |
| --- | --- |
|  | (14) |

Note that the problem is non-convex due to the fractional form . Moreover, is invariant to the rescaling of which is bad for numerical computation (as this implies that there exist global solutions arbitrarily close to and ).

If the training set is separable, i.e., there exists a such that , there also exists a so that by a simple rescaling argument. Then [Eq. (14)](#FD15) becomes

|  |  |
| --- | --- |
|  | (15) |

|  |  |
| --- | --- |
|  | (16) |

|  |  |
| --- | --- |
|  | (17) |

where [Eq. (17)](#FD18) is our textbook hard-margin SVM (except for the squared norm often used in the objective). A problem with [Eq. (17)](#FD18) is that the constraint set is infeasible for inseparable training data. To fix this issue, we can allow slight violations in the constraint and penalize these violations in the objective of [Eq. (17)](#FD18), arriving at

|  |  |
| --- | --- |
|  | (18) |

which is our textbook soft-margin SVM.

Now for multiclass classification, let us assume the data space: with . The classifier takes the form , where . We note that from binary SVM, people create the notion of *confidence margin:*

|  |  |
| --- | --- |
|  | (19) |

which for the binary case is simply the signed geometric margin rescaled by . The standard multiclass decision rule is[13](#FN13)

|  |  |
| --- | --- |
|  | (20) |

where is the -th column of . To correctly classify all points, we need

|  |  |
| --- | --- |
|  | (21) |

This motivates the multiclass hard-margin SVM, separability assumed:

|  |  |
| --- | --- |
|  | (22) |

where terms can be viewed as *multiclass confidence margins*, natural generalizations of confidence margins for the binary case. The corresponding soft-margin version is

|  |  |
| --- | --- |
|  | (23) |

Both hard- and soft-margin versions are convex and thus more convenient for numerical optimization.

On the other hand, if we strictly follow the geometric margin interpretation, it seems more natural to formulate multiclass SVM as follows. Consider the decision rule:

|  |  |
| --- | --- |
|  | (24) |

which would classify all points correctly provided that there exists a satisfying

|  |  |
| --- | --- |
|  | (25) |

This motivates an optimization problem on the worst *geometric margins:*

|  |  |
| --- | --- |
|  | (26) |

However, this problem is non-convex and thus not popularly adopted.

## B. Asymptotic behaviors of

Recall from mathematical analysis that two functions and *are asymptotically equivalent as* , written as as , if and only if as , where is the standard small-o notation. Note that .

**Lemma B.1.** *Consider the raw logits* , *and without loss of generality assume that they are ordered in descending order without any ties, i.e.,* . *We have that as* ,

|  |
| --- |
|  |

*Moreover, all of the asymptotic functions are monotonically increasing with respect to* .

*Proof*. First, for , we have

|  |  |
| --- | --- |
|  | (27) |

as , because as . Moreover, as ,

|  |  |
| --- | --- |
|  | (28) |

as when . So we conclude that

|  |  |
| --- | --- |
|  | (29) |

Now consider . Applying a similar argument as above, we have

|  |  |
| --- | --- |
|  | (30) |

|  |  |
| --- | --- |
|  | (31) |

|  |  |
| --- | --- |
|  | (32) |

|  |  |
| --- | --- |
|  | (33) |

as , where [Eq. (33)](#FD35) holds as is lower order than when so that . Therefore, as ,

|  |  |
| --- | --- |
|  | (34) |

Finally, for , we have that when ,

|  |  |
| --- | --- |
|  | (35) |

|  |  |
| --- | --- |
|  | (36) |

|  |  |
| --- | --- |
|  | (37) |

|  |  |
| --- | --- |
|  | (38) |

where [Eq. (38)](#FD40) holds because as . Continuing the above argument, we further have that as ,

|  |  |
| --- | --- |
|  | (39) |

Let’s write . The last two terms in [Eq. (39)](#FD41) can be re-written as . Since , we thus have as , and hense by the definition of the asymptotic equivalence. Therefore, we have:

|  |  |
| --- | --- |
|  | (40) |

|  |  |
| --- | --- |
|  | (41) |

So we conclude that

|  |  |
| --- | --- |
|  | (42) |

completing the proof. □

## C. Evaluation metrics for OOD detection vs. evaluation metrics for generalized SC

The commonly used evaluation metrics for OOD detection do not reflect the classification performance ([Franc et al., 2023b](#R18)). Here we provide a quantitative supporting example, in comparison with the RC curve for generalized SC.

### Table 5:

Evaluation of and using popular OOD metrics. The better numbers are highlighted in bold.

| OOD metric |  |  |
| AUROC (↑) | 0.765 | **0.944** |
| AUPR (↑) | 0.987 | **0.997** |
| FPR@TPR=0.95 (↓) | 0.816 | **0.279** |

[Open in a new tab](table/T3/)

OOD (mostly label-shift) detection as formulated in [Eq. (9)](#FD9) can be viewed as a binary classification problem: selected and rejected samples form the two classes. So pioneer work on OOD detection, such as [Hendrycks & Gimpel (2016)](#R31), proposes to evaluate OOD detection in a manner similar to that of binary classification, e.g., using the Area Under the Receiver Operating Characteristic (AUROC) curve ([Davis & Goadrich, 2006](#R10)) and Area Under the Precision-Recall curve (AUPR) ([Saito & Rehmsmeier, 2015](#R57)) to measure the separability of In-D and OOD samples.[14](#FN14) However, two important aspects are missing in OOD detection, and hence also its performance evaluation, if we are to focus on the performance on the accepted samples:

1. Pretrained classifiers do not always make wrong predictions on label-shifted samples, and hence these OOD samples should not be blindly rejected;
2. In-D samples that might have been correctly classified can be rejected due to poor separation of In-D and OOD samples, leading to worse classification performance on the selected part.

To demonstrate our points quantitatively, we take the pretrained model **EVA**[15](#FN15) from `timm` ([Wightman, 2019](#R62)) that achieves > 88% top 1 accuracy on the `ImageNet` validation set. We then mix `ImageNet` validation set (In-D samples) with ImageNet-0 (OOD samples, label shifted) ([Hendrycks & Dietterich, 2018](#R30)), and evaluate two score functions and [16](#FN16) using both generalized SC formulation (via RC curves) and OOD detection (via AUROC and AUPR).

According to [Table 5](#T3), is considered superior to by all metrics for OOD detection. Correspondingly, from [Fig. 7(a)](#F7) and [(b)](#F7), we observe that the scores of the label-shifted samples (green) and those of the In-D samples (blue and orange) are more separated by than by . However, we can also quickly notice one issue: In-D samples are not completely separated from OOD samples—a threshold intended to reject label-shifted samples will inevitably reject a portion of In-D samples at the same time, even though a large portion of In-D samples have been correctly classified (blue); In-D samples that can be correctly classified (blue) are less separated from those misclassified ones (orange) by than by . This problem cannot be revealed by the OOD metrics in [Table 5](#T3), but is captured by the RC curves in [Fig. 7(c)](#F7) where the selection risk of (blue) increases as more OOD samples are rejected (TPR from 0.95 to 0.1 as indicated by the vertical dashed lines). In contrast, the more samples rejected by (smaller coverage), the lower the selection risk, implying that serves SC better.

### Figure 7:

[Open in a new tab](figure/F7/)

Score distributions of and (a)-(b) and their RC curves (c). In (a) and (b), In-D samples that are *correctly* classified by **EVA** are shown in blue, while In-D samples that are *incorrectly* classified are shown in orange; OOD samples (label-shifted) are shown in green. The vertical dashed lines in (a)-(c) corresponds to different True-Positive-Rate cutoffs in the AUROC metric in OOD detection.

## D. Rejection patterns of different score functions

We plot in [Fig. 8](#F8) the heatmap of the score values for each score function. During SC, samples located in the darker areas (with low score values) will be rejected before those located in the brighter areas (with high score values).

### Figure 8:

[Open in a new tab](figure/F8/)

Heatmaps of rejection patterns (distribution of scores). Note that because we rescale the scores for good visualization, the colors are not cross-comparable between different score functions.

## E. Timm model cards

### Table 6:

Names of model cards in library `timm` to retrieve the models for `ImageNet`

| Dataset | Model name | Model card name | Top-1 Acc. (%) |
| `ImageNet` | EVA (ViT) | eva\_giant\_\_patch14\_224.clip\_ft\_in1k | 88.76 |
| ConvNext | convnextv2\_base.fcmae\_ft\_in22k\_in1k | 86.25 |
| VOLO | volo\_d4\_224.sail\_in1k | 85.56 |
| ResNext | seresnextaa101d\_\_32×8d.sw\_in12k\_ft\_in1k | 85.94 |

[Open in a new tab](table/T4/)

[Table 6](#T4) shows the names of the model cards used to retrieve the pretrained models for `ImageNet` from the timm library. Our considerations for choosing these models are as follows: **(i)** the models should cover a wide range of recent and popular architectures, and **(ii)** they should achieve high top-1 accuracy to represent recent advances of image classification.

## F. Training details for ScNet

We use the unofficial `PyTorch` implementation[17](#FN17) of the original SelectiveNet ([Geifman & El-Yaniv, 2019](#R23)) due to the out-of-date `Keras` environment of the original repository[18](#FN18). The `PyTorch` implementation follows the training method proposed in [Geifman & El-Yaniv (2019)](#R23) and faithfully reproduces the results of `CIFAR-10` experiment reported in the original paper. We add the `ImageNet` experiment on top of the `PyTorch` code, as it is not included in the original code or the paper. [Table 7](#T5) summarizes the key hyperparameters to produce the results reported in this paper.

### Table 7:

Key hyperparameters for the ScNet training used in this paper

| Dataset | Model architecture | Dropout prob. | Target coverage | Batch size | Total epochs | Lr (base) | Scheduler |
| `CIFAR-10` | VGG | 0.3 | 0.7 | 128 | 300 | 0.1 | StepLR |
| `ImaegNet-1k` | resnet34 | N/A | 0.7 | 768 | 250 | 0.1 | CosineAnnealingLR |

[Open in a new tab](table/T5/)

## G. Additional `ImageNet` experiments

We report in [Fig. 9](#F9) the RC curves of different score functions on models `ConvNext`, `ResNext`, and `VOLO` for `ImageNet`, and summarize their AURC statistics in [Table 8](#T6).

## H. Ablation experiments for the KNN score

We show in [Fig. 10](#F10) the SC performance of the KNN score on models `EVA`, `ConvNext`, `ResNext`, and `VOLO`, respectively, on `ImageNet` with all In-D and distribution-shifted samples. We can observe that (i) the SC performance of KNN is sensitive to the choice of hyperparameter , and (ii) our selection achieves the best SC performance for KNN score on our `ImageNet` task.

### Figure 9:

[Open in a new tab](figure/F9/)

RC curves of different confidence-score functions on models `ConvNext`, `ResNext` and `VOLO` from `timm` for ImageNet. The four columns are RC curves evaluated using samples from In-D only, In-D and covariate-shifted only, In-D and label-shifted only, and all, respectively. We group the curves by whether they are originally proposed for SC (solid lines) or for OOD detection (dashed lines).

### Figure 10:

[Open in a new tab](figure/F10/)

RC curves achieved by the KNN score with different on `ImageNet`

### Table 8:

Summary of AURC- for [Fig. 9](#F9). The AURC numbers are *on the* 10−2 *scale—the lower, the better*. The score functions proposed for SC are highlighted in gray, and the rest are originally for OOD detection. The best AURC numbers for each coverage level are highlighted in bold, and the and best scores are underlined.

| `ImageNet` - ConvNext | In-D | In-D + Shift (Cov) | In-D + Shift (Label) | In-D + Shift (both) |
|  | 0.1 | 0.5 | 1 | 0.1 | 0.5 | 1 | 0.1 | 0.5 | 1 | 0.1 | 0.5 | 1 |
|  | **0.10** | **0.53** | **3.02** | **0.26** | 1.76 | 8.20 | **0.58** | **2.51** | 11.8 | **0.34** | 1.99 | 8.88 |
|  | 0.15 | 0.59 | 3.10 | 0.31 | **1.75** | **8.14** | 0.75 | 2.54 | 11.8 | 0.38 | **1.97** | **8.81** |
| SIRC | 1.96 | 1.70 | 3.59 | 3.44 | 3.23 | 8.60 | 5.94 | 4.03 | 11.5 | 3.76 | 3.46 | 9.18 |
|  | 2.26 | 1.86 | 3.66 | 3.73 | 3.40 | 8.70 | 5.86 | 4.05 | 11.4 | 4.04 | 3.62 | 9.26 |
|  | 2.77 | 2.44 | 4.19 | 4.78 | 4.33 | 9.54 | 6.83 | 4.85 | 11.6 | 5.13 | 4.56 | 10.1 |
|  | 2.26 | 1.86 | 3.67 | 3.73 | 3.41 | 8.74 | 5.86 | 4.06 | **11.3** | 4.04 | 3.63 | 9.29 |
|  | 5.43 | 4.77 | 5.81 | 9.05 | 7.89 | 11.6 | 10.5 | 7.73 | 13.2 | 9.45 | 8.13 | 12.1 |
| Energy | 6.66 | 6.70 | 7.54 | 10.9 | 10.7 | 13.9 | 11.9 | 9.78 | 14.6 | 11.3 | 10.9 | 14.3 |
| KNN | 1.01 | 2.37 | 5.72 | 1.29 | 4.54 | 10.6 | 1.11 | 3.66 | 12.0 | 1.31 | 4.59 | 11.0 |
| ViM | 15.1 | 9.84 | 9.49 | 16.2 | 11.9 | 14.3 | 14.1 | 9.57 | 14.5 | 16.2 | 11.9 | 14.7 |
| `ImageNet` - ResNext |
|  | **0.12** | **0.59** | **3.17** | **0.29** | 2.15 | 9.38 | **0.59** | 3.22 | 12.8 | **0.38** | 2.50 | 10.2 |
|  | 0.17 | 0.60 | 3.18 | 0.34 | **2.14** | **9.33** | 0.65 | **3.16** | 12.7 | 0.43 | **2.49** | **10.1** |
| SIRC | 1.71 | 1.91 | 3.94 | 3.96 | 4.18 | 9.99 | 7.77 | 5.88 | 13.1 | 4.47 | 4.57 | 10.7 |
|  | 2.28 | 2.26 | 4.11 | 4.88 | 4.69 | 10.3 | 7.44 | 5.88 | 12.9 | 5.36 | 5.06 | 11.0 |
|  | 3.38 | 3.42 | 5.37 | 6.92 | 6.94 | 12.2 | 9.46 | 7.70 | 13.9 | 7.47 | 7.36 | 12.8 |
|  | 2.29 | 2.28 | 4.17 | 4.92 | 4.75 | 10.4 | 7.47 | 5.92 | 12.8 | 5.39 | 5.12 | 11.1 |
|  | 1.57 | 2.34 | 4.79 | 2.98 | 4.82 | 10.9 | 2.37 | 3.83 | **11.9** | 3.06 | 5.00 | 11.4 |
| Energy | 3.08 | 3.90 | 6.17 | 5.13 | 7.20 | 12.7 | 3.68 | 5.34 | 13.2 | 5.19 | 7.37 | 13.2 |
| KNN | 3.23 | 4.84 | 7.61 | 4.12 | 7.65 | 13.6 | 3.40 | 5.85 | 13.5 | 4.14 | 7.77 | 14.0 |
| ViM | 4.68 | 6.13 | 7.79 | 6.18 | 8.81 | 13.6 | 5.09 | 6.82 | 13.6 | 6.23 | 8.92 | 14.1 |
| `ImageNet` - VOLO |
|  | **0.31** | **0.79** | **3.44** | **0.46** | 2.24 | 9.72 | 1.30 | 3.79 | 13.3 | 0.68 | 2.67 | 10.6 |
|  | 0.37 | 0.81 | 3.46 | 0.50 | **2.23** | 9.73 | **0.94** | **3.56** | 13.1 | **0.66** | **2.64** | 10.6 |
| SIRC | 1.27 | 1.44 | 3.74 | 1.35 | 2.82 | 9.56 | 2.68 | 3.97 | 12.9 | 1.90 | 3.37 | 10.5 |
|  | 1.31 | 1.42 | 3.72 | 1.33 | 2.82 | 9.59 | 2.54 | 3.78 | 12.7 | 1.86 | 3.36 | 10.5 |
|  | 1.47 | 1.59 | 3.83 | 1.58 | 3.13 | 9.72 | 2.71 | 3.87 | **12.4** | 2.13 | 3.69 | 10.6 |
|  | 1.31 | 1.42 | 3.71 | 1.33 | 2.82 | **9.55** | 2.54 | 3.78 | 12.7 | 1.86 | 3.36 | **10.4** |
|  | 4.92 | 4.51 | 6.18 | 6.32 | 7.13 | 12.5 | 6.37 | 6.82 | 13.8 | 7.07 | 7.84 | 13.4 |
| Energy | 5.21 | 4.99 | 6.84 | 6.88 | 8.24 | 13.5 | 6.70 | 7.37 | 14.3 | 7.62 | 8.95 | 14.4 |
| KNN | 2.18 | 3.29 | 6.23 | 2.10 | 5.03 | 11.7 | 2.27 | 4.85 | 13.7 | 2.15 | 5.26 | 12.3 |
| ViM | 9.38 | 10.7 | 11.9 | 9.04 | 12.0 | 16.5 | 10.4 | 13.5 | 21.1 | 9.22 | 12.4 | 17.3 |

[Open in a new tab](table/T6/)

## Footnotes

1

We assume no *outliers* in generalized SC—samples that do not follow any specific statistical patterns—during deployment, i.e., they are already detected and removed after separate data preprocessing steps. This allows us to properly define the coverage and selection risk.

2

For the classifier consideblue, and have the same SC performance as .

3

The intuition on why our notions of margins work for Type B errors is different: there since assumes a label outside the known set, we expect no clear winner in the raw logits.

4

In OOD detection, scores are usually dependent on the training data. However, these post-hoc scores can also be applied as nontraining-based SC scores as [Algorithm 1](#T1), by replacing and in [Algorithm 2](#T2) with .

5

Five times the number of classes in each task from [Table 2](#T8). We do not sample five points per class, as in practice the calibration set may be imbalanced.

6

See [Table 6](#T4) in [Appendix E](#APP5) for the model card information to retrieve these `timm` models.

7

<https://github.com/locuslab/FLYP>

8

<https://github.com/huaxiuyao/LISA.git>

9

<https://github.com/gatheluck/pytorch-SelectiveNet>

10

We do not consider training-based score functions such as [Liu et al. (2019)](#R45); [Huang et al. (2022)](#R33) due to the ambiguity in calculating their SR responses. During their training, a virtual class “abstention” is added and the softmax normalization is applied on all logits—including that of the virtual class, so it is unfair either simply dropping the abstention logit during test for score calculation or keeping the abstention logit but modifying the score calculation procedure. Retraining a classifier with the same settings but without the abstention logit is also unfair due to the requirement of a fixed classifier. Furthermore, [Feng et al. (2023)](#R15) reports that the above selection methods ([Liu et al., 2019](#R45); [Huang et al., 2022](#R33)) are not as effective as they claim.

11

Existing training-based SC works so far have only reported SC (In-D) performance on `CIFAR-10` dataset and have not experimented with `ImageNet` using the full training set. Our results on `CIFAR-10` dataset faithfully reproduce the result originally reported in [Geifman & El-Yaniv (2019)](#R23).

12

The cross-entropy loss is the most commonly used and minimizing it can be viewed as approximating maximizing the confidence margin. To see this, without loss of generality, assume that the magnitudes of the raw logits are ordered and that the true label of the current sample is class 1. Then the cross-entropy loss for the current sample is , so , where the last minimization problem can be approximated by min , i.e., maximizing the confidence margin, when .

13

The decision rule for the binary case is . Therefore, we do not need to worry about the ’s scaling

14

A single-point metric, False Positive Rate (FPR) at 0.95 True Positive Rate (TPR), is also popularly used as a companion ([Liang et al., 2017](#R42); [Wang et al., 2022](#R61); [Liu et al., 2020](#R43); [Djurisic et al., 2022](#R11); [Sun et al., 2022](#R59); [Yang et al., 2022](#R66)).

15

See [Appendix E](#APP5) for model card information. This model is also used in the experiments of [Section 4](#S24).

16

is our proposed and is ViM.

17

<https://github.com/gatheluck/pytorch-SelectiveNet>

18

## Contributor Information

Hengyue Liang, Department of Electrical and Computer Engineering, University of Minnesota.

Le Peng, Department of Computer Science and Engineering, University of Minnesota.

Ju Sun, Department of Computer Science and Engineering, University of Minnesota.

## References

1. Beery Sara, Cole Elijah, and Gjoka Arvi. The iwildcam 2020 competition dataset. arXiv preprint arXiv:2004.10340, 2020. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=The%20iwildcam%202020%20competition%20dataset&author=Sara%20Beery&author=Elijah%20Cole&author=Arvi%20Gjoka&publication_year=2020&)]
2. Brown Tom B., Mann Benjamin, Ryder Nick, Subbiah Melanie, Kaplan Jared, Dhariwal Prafulla, Neelakantan Arvind, Shyam Pranav, Sastry Girish, Askell Amanda, Agarwal Sandhini, Herbert-Voss Ariel, Krueger Gretchen, Henighan Tom, Child Rewon, Ramesh Aditya, Ziegler Daniel M., Wu Jeffrey, Winter Clemens, Hesse Christopher, Chen Mark, Sigler Eric, Litwin Mateusz, Gray Scott, Chess Benjamin, Clark Jack, Berner Christopher, McCandlish Sam,Radford Alec, Sutskever Ilya, and Amodei Dario. Language models are few-shot learners. arXiv preprint arXiv:2005.14165, 2020. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Language%20models%20are%20few-shot%20learners&author=Tom%20B.%20Brown&author=Benjamin%20Mann&author=Nick%20Ryder&author=Melanie%20Subbiah&author=Jared%20Kaplan&publication_year=2020&)]
3. Carlini Nicholas, Athalye Anish, Papernot Nicolas, Brendel Wieland, Rauber Jonas, Tsipras Dimitris, Goodfellow Ian, Madry Aleksander, and Kurakin Alexey. On evaluating adversarial robustness. arXiv preprint arXiv:1902.06705, 2019. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=On%20evaluating%20adversarial%20robustness&author=Nicholas%20Carlini&author=Anish%20Athalye&author=Nicolas%20Papernot&author=Wieland%20Brendel&author=Jonas%20Rauber&publication_year=2019&)]
4. Cattelan Luís Felipe Prates and Silva Danilo. On selective classification under distribution shift. In NeurIPS 2023 Workshop on Distribution Shifts: New Frontiers with Foundation Models. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=NeurIPS%202023%20Workshop%20on%20Distribution%20Shifts:%20New%20Frontiers%20with%20Foundation%20Models&title=On%20selective%20classification%20under%20distribution%20shift&author=Lu%C3%ADs%20Felipe%20Prates%20Cattelan&author=Danilo%20Silva&)]
5. Chow C. On optimum recognition error and reject tradeoff. IEEE Transactions on information theory, 16 (1):41–46, 1970. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=IEEE%20Transactions%20on%20information%20theory&title=On%20optimum%20recognition%20error%20and%20reject%20tradeoff&author=C%20Chow&volume=16&issue=1&publication_year=1970&pages=41-46&)]
6. Corbière Charles, Thome Nicolas, Bar-Hen Avner, Cord Matthieu, and Pérez Patrick. Addressing failure prediction by learning model confidence. Advances in Neural Information Processing Systems, 32, 2019. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20Neural%20Information%20Processing%20Systems&title=Addressing%20failure%20prediction%20by%20learning%20model%20confidence&author=Charles%20Corbi%C3%A8re&author=Nicolas%20Thome&author=Avner%20Bar-Hen&author=Matthieu%20Cord&author=Patrick%20P%C3%A9rez&volume=32&publication_year=2019&)]
7. Cortes Corinna, DeSalvo Giulia, and Mohri Mehryar. Boosting with abstention. Advances in Neural Information Processing Systems, 29, 2016. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20Neural%20Information%20Processing%20Systems&title=Boosting%20with%20abstention&author=Corinna%20Cortes&author=Giulia%20DeSalvo&author=Mehryar%20Mohri&volume=29&publication_year=2016&)]
8. Crammer Koby and Singer Yoram. On the algorithmic implementation of multiclass kernel-based vector machines. Journal of machine learning research, 2(Dec):265–292, 2001. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Journal%20of%20machine%20learning%20research&title=On%20the%20algorithmic%20implementation%20of%20multiclass%20kernel-based%20vector%20machines&author=Koby%20Crammer&author=Yoram%20Singer&volume=2&issue=Dec&publication_year=2001&pages=265-292&)]
9. Croce Francesco, Andriushchenko Maksym, Sehwag Vikash, Debenedetti Edoardo, Flammarion Nicolas, Chiang Mung, Mittal Prateek, and Hein Matthias. Robustbench: a standardized adversarial robustness benchmark. arXiv preprint arXiv:2010.09670, 2020. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Robustbench:%20a%20standardized%20adversarial%20robustness%20benchmark&author=Francesco%20Croce&author=Maksym%20Andriushchenko&author=Vikash%20Sehwag&author=Edoardo%20Debenedetti&author=Nicolas%20Flammarion&publication_year=2020&)]
10. Davis Jesse and Goadrich Mark. The relationship between precision-recall and roc curves. In Proceedings of the 23rd international conference on Machine learning, pp. 233–240, 2006. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%2023rd%20international%20conference%20on%20Machine%20learning&title=The%20relationship%20between%20precision-recall%20and%20roc%20curves&author=Jesse%20Davis&author=Mark%20Goadrich&publication_year=2006&pages=233-240&)]
11. Djurisic Andrija, Bozanic Nebojsa, Ashok Arjun, and Liu Rosanne. Extremely simple activation shaping for out-of-distribution detection. arXiv preprint arXiv:2209.09858, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Extremely%20simple%20activation%20shaping%20for%20out-of-distribution%20detection&author=Andrija%20Djurisic&author=Nebojsa%20Bozanic&author=Arjun%20Ashok&author=Rosanne%20Liu&publication_year=2022&)]
12. Dusenberry Michael, Jerfel Ghassen, Wen Yeming, Ma Yian, Snoek Jasper, Heller Katherine, Lakshminarayanan Balaji, and Tran Dustin. Efficient and scalable bayesian neural nets with rank-1 factors. In International conference on machine learning, pp. 2782–2792. PMLR, 2020. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=International%20conference%20on%20machine%20learning&author=Michael%20Dusenberry&author=Ghassen%20Jerfel&author=Yeming%20Wen&author=Yian%20Ma&author=Jasper%20Snoek&publication_year=2020&)]
13. El-Yaniv Ran et al. On the foundations of noise-free selective classification. Journal of Machine Learning Research, 11(5), 2010. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Journal%20of%20Machine%20Learning%20Research&title=On%20the%20foundations%20of%20noise-free%20selective%20classification&author=Ran%20El-Yaniv&volume=11&issue=5&publication_year=2010&)]
14. Fang Yuxin, Wang Wen, Xie Binhui, Sun Quan, Wu Ledell, Wang Xinggang, Huang Tiejun, Wang Xinlong, and Cao Yue. Eva: Exploring the limits of masked visual representation learning at scale. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 19358–19369, 2023. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%20IEEE/CVF%20Conference%20on%20Computer%20Vision%20and%20Pattern%20Recognition&title=Eva:%20Exploring%20the%20limits%20of%20masked%20visual%20representation%20learning%20at%20scale&author=Yuxin%20Fang&author=Wen%20Wang&author=Binhui%20Xie&author=Quan%20Sun&author=Ledell%20Wu&publication_year=2023&pages=19358-19369&)]
15. Feng Leo, Ahmed Mohamed Osama, Hajimirsadeghi Hossein, and Abdi Amir H. Towards better selective classification. In The Eleventh International Conference on Learning Representations, 2023. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=The%20Eleventh%20International%20Conference%20on%20Learning%20Representations&title=Towards%20better%20selective%20classification&author=Leo%20Feng&author=Mohamed%20Osama%20Ahmed&author=Hossein%20Hajimirsadeghi&author=Amir%20H%20Abdi&publication_year=2023&)]
16. Fisch Adam, Jaakkola Tommi S, and Barzilay Regina. Calibrated selective classification. Transactions on Machine Learning Research, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Transactions%20on%20Machine%20Learning%20Research&title=Calibrated%20selective%20classification&author=Adam%20Fisch&author=Tommi%20S%20Jaakkola&author=Regina%20Barzilay&publication_year=2022&)]
17. Franc Vaclav Voracek Vojtech, Prusa Daniel, and Voracek Vaclav. Optimal strategies for reject option classifiers. Journal of Machine Learning Research, 24(11):1–49, 2023a. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Journal%20of%20Machine%20Learning%20Research&title=Optimal%20strategies%20for%20reject%20option%20classifiers&author=Vaclav%20Voracek%20Vojtech%20Franc&author=Daniel%20Prusa&author=Vaclav%20Voracek&volume=24&issue=11&publication_year=2023a&pages=1-49&)]
18. Franc Vojtech, Prusa Daniel, and Paplham Jakub. Reject option models comprising out-of-distribution detection. arXiv preprint arXiv:2307.05199, 2023b. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Reject%20option%20models%20comprising%20out-of-distribution%20detection&author=Vojtech%20Franc&author=Daniel%20Prusa&author=Jakub%20Paplham&publication_year=2023b&)]
19. Franc Vojtech, Paplham Jakub, and Prusa Daniel. Scod: From heuristics to theory. arXiv preprint arXiv:2403.16916, 2024. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Scod:%20From%20heuristics%20to%20theory&author=Vojtech%20Franc&author=Jakub%20Paplham&author=Daniel%20Prusa&publication_year=2024&)]
20. Fumera Giorgio and Roli Fabio. Support vector machines with embedded reject option. In Pattern Recognition with Support Vector Machines: First International Workshop, SVM 2002 Niagara Falls, Canada, August 10, 2002 Proceedings, pp. 68–82. Springer, 2002. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=Pattern%20Recognition%20with%20Support%20Vector%20Machines:%20First%20International%20Workshop,%20SVM%202002%20Niagara%20Falls,%20Canada,%20August%2010,%202002%20Proceedings&author=Giorgio%20Fumera&author=Fabio%20Roli&publication_year=2002&)]
21. Gal Yarin and Ghahramani Zoubin. Dropout as a bayesian approximation: Representing model uncertainty in deep learning. In international conference on machine learning, pp. 1050–1059. PMLR, 2016. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=international%20conference%20on%20machine%20learning&author=Yarin%20Gal&author=Zoubin%20Ghahramani&publication_year=2016&)]
22. Geifman Yonatan and El-Yaniv Ran. Selective classification for deep neural networks. Advances in neural information processing systems, 30, 2017. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20neural%20information%20processing%20systems&title=Selective%20classification%20for%20deep%20neural%20networks&author=Yonatan%20Geifman&author=Ran%20El-Yaniv&volume=30&publication_year=2017&)]
23. Geifman Yonatan and El-Yaniv Ran. Selectivenet: A deep neural network with an integrated reject option. In International conference on machine learning, pp. 2151–2159. PMLR, 2019. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=International%20conference%20on%20machine%20learning&author=Yonatan%20Geifman&author=Ran%20El-Yaniv&publication_year=2019&)]
24. Geifman Yonatan, Uziel Guy, and El-Yaniv Ran. Bias-reduced uncertainty estimation for deep neural classifiers. arXiv preprint arXiv:1805.08206, 2018. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Bias-reduced%20uncertainty%20estimation%20for%20deep%20neural%20classifiers&author=Yonatan%20Geifman&author=Guy%20Uziel&author=Ran%20El-Yaniv&publication_year=2018&)]
25. Geng Chuanxing, Huang Sheng-jun, and Chen Songcan. Recent advances in open set recognition: A survey. IEEE transactions on pattern analysis and machine intelligence, 43(10):3614–3631, 2020. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=IEEE%20transactions%20on%20pattern%20analysis%20and%20machine%20intelligence&title=Recent%20advances%20in%20open%20set%20recognition:%20A%20survey&author=Chuanxing%20Geng&author=Sheng-jun%20Huang&author=Songcan%20Chen&volume=43&issue=10&publication_year=2020&pages=3614-3631&)]
26. Goyal Sachin, Kumar Ananya, Garg Sankalp, Kolter Zico, and Raghunathan Aditi. Finetune like you pretrain: Improved finetuning of zero-shot vision models. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 19338–19347, 2023. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%20IEEE/CVF%20Conference%20on%20Computer%20Vision%20and%20Pattern%20Recognition&title=Finetune%20like%20you%20pretrain:%20Improved%20finetuning%20of%20zero-shot%20vision%20models&author=Sachin%20Goyal&author=Ananya%20Kumar&author=Sankalp%20Garg&author=Zico%20Kolter&author=Aditi%20Raghunathan&publication_year=2023&pages=19338-19347&)]
27. Grandvalet Yves, Rakotomamonjy Alain, Keshet Joseph, and Canu Stéphane. Support vector machines with a reject option. Advances in neural information processing systems, 21, 2008. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20neural%20information%20processing%20systems&title=Support%20vector%20machines%20with%20a%20reject%20option&author=Yves%20Grandvalet&author=Alain%20Rakotomamonjy&author=Joseph%20Keshet&author=St%C3%A9phane%20Canu&volume=21&publication_year=2008&)]
28. Granese Federica, Romanelli Marco, Gorla Daniele, Palamidessi Catuscia, and Piantanida Pablo. Doctor: A simple method for detecting misclassification errors. Advances in Neural Information Processing Systems, 34:5669–5681, 2021. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20Neural%20Information%20Processing%20Systems&title=Doctor:%20A%20simple%20method%20for%20detecting%20misclassification%20errors&author=Federica%20Granese&author=Marco%20Romanelli&author=Daniele%20Gorla&author=Catuscia%20Palamidessi&author=Pablo%20Piantanida&volume=34&publication_year=2021&pages=5669-5681&)]
29. Guo Chuan, Pleiss Geoff, Sun Yu, and Weinberger Kilian Q. On calibration of modern neural networks. In International conference on machine learning, pp. 1321–1330. PMLR, 2017. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=International%20conference%20on%20machine%20learning&author=Chuan%20Guo&author=Geoff%20Pleiss&author=Yu%20Sun&author=Kilian%20Q%20Weinberger&publication_year=2017&)]
30. Hendrycks Dan and Dietterich Thomas. Benchmarking neural network robustness to common corruptions and perturbations. In International Conference on Learning Representations, 2018. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=International%20Conference%20on%20Learning%20Representations&title=Benchmarking%20neural%20network%20robustness%20to%20common%20corruptions%20and%20perturbations&author=Dan%20Hendrycks&author=Thomas%20Dietterich&publication_year=2018&)]
31. Hendrycks Dan and Gimpel Kevin. A baseline for detecting misclassified and out-of-distribution examples in neural networks. arXiv preprint arXiv:1610.02136, 2016. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=A%20baseline%20for%20detecting%20misclassified%20and%20out-of-distribution%20examples%20in%20neural%20networks&author=Dan%20Hendrycks&author=Kevin%20Gimpel&publication_year=2016&)]
32. Hendrycks Dan, Basart Steven, Mazeika Mantas, Zou Andy, Kwon Joe, Mostajabi Mohammadreza, Steinhardt Jacob, and Song Dawn. Scaling out-of-distribution detection for real-world settings. arXiv preprint arXiv:1911.11132, 2019. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Scaling%20out-of-distribution%20detection%20for%20real-world%20settings&author=Dan%20Hendrycks&author=Steven%20Basart&author=Mantas%20Mazeika&author=Andy%20Zou&author=Joe%20Kwon&publication_year=2019&)]
33. Huang Lang, Zhang Chao, and Zhang Hongyang. Self-adaptive training: Bridging supervised and self-supervised learning. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=IEEE%20Transactions%20on%20Pattern%20Analysis%20and%20Machine%20Intelligence&title=Self-adaptive%20training:%20Bridging%20supervised%20and%20self-supervised%20learning&author=Lang%20Huang&author=Chao%20Zhang&author=Hongyang%20Zhang&publication_year=2022&)]
34. Jiang Heinrich, Kim Been, Guan Melody, and Gupta Maya. To trust or not to trust a classifier. Advances in neural information processing systems, 31, 2018. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20neural%20information%20processing%20systems&title=To%20trust%20or%20not%20to%20trust%20a%20classifier&author=Heinrich%20Jiang&author=Been%20Kim&author=Melody%20Guan&author=Maya%20Gupta&volume=31&publication_year=2018&)]
35. Kim Jihyo, Koo Jiin, and Hwang Sangheum. A unified benchmark for the unknown detection capability of deep neural networks. Expert Systems with Applications, 229:120461, 2023. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Expert%20Systems%20with%20Applications&title=A%20unified%20benchmark%20for%20the%20unknown%20detection%20capability%20of%20deep%20neural%20networks&author=Jihyo%20Kim&author=Jiin%20Koo&author=Sangheum%20Hwang&volume=229&publication_year=2023&pages=120461&)]
36. Koh Pang Wei, Sagawa Shiori, Marklund Henrik, Xie Sang Michael, Zhang Marvin, Balsubramani Akshay, Hu Weihua, Yasunaga Michihiro, Phillips Richard Lanas, Gao Irena, et al. Wilds: A benchmark of in-the-wild distribution shifts. In International Conference on Machine Learning, pp. 5637–5664. PMLR, 2021. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=International%20Conference%20on%20Machine%20Learning&author=Pang%20Wei%20Koh&author=Shiori%20Sagawa&author=Henrik%20Marklund&author=Sang%20Michael%20Xie&author=Marvin%20Zhang&publication_year=2021&)]
37. Krizhevsky Alex, Hinton Geoffrey, et al. Learning multiple layers of features from tiny images. 2009. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Learning%20multiple%20layers%20of%20features%20from%20tiny%20images&author=Alex%20Krizhevsky&author=Geoffrey%20Hinton&publication_year=2009&)]
38. Lakshminarayanan Balaji, Pritzel Alexander, and Blundell Charles. Simple and scalable predictive uncertainty estimation using deep ensembles. Advances in neural information processing systems, 30, 2017. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20neural%20information%20processing%20systems&title=Simple%20and%20scalable%20predictive%20uncertainty%20estimation%20using%20deep%20ensembles&author=Balaji%20Lakshminarayanan&author=Alexander%20Pritzel&author=Charles%20Blundell&volume=30&publication_year=2017&)]
39. LeCun Yann, Boser Bernhard, Denker John, Henderson Donnie, Howard Richard, Hubbard Wayne, and Jackel Lawrence. Handwritten digit recognition with a back-propagation network. Advances in neural information processing systems, 2, 1989. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20neural%20information%20processing%20systems&title=Handwritten%20digit%20recognition%20with%20a%20back-propagation%20network&author=Yann%20LeCun&author=Bernhard%20Boser&author=John%20Denker&author=Donnie%20Henderson&author=Richard%20Howard&volume=2&publication_year=1989&)]
40. Lei Jing. Classification with confidence. Biometrika, 101(4):755–769, 2014. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Biometrika&title=Classification%20with%20confidence&author=Jing%20Lei&volume=101&issue=4&publication_year=2014&pages=755-769&)]
41. Liang Hengyue, Liang Buyun, Peng Le, Cui Ying, Mitchell Tim, and Sun Ju. Optimization and optimizers for adversarial robustness. arXiv preprint arXiv:2303.13401, 2023. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Optimization%20and%20optimizers%20for%20adversarial%20robustness&author=Hengyue%20Liang&author=Buyun%20Liang&author=Le%20Peng&author=Ying%20Cui&author=Tim%20Mitchell&publication_year=2023&)]
42. Liang Shiyu, Li Yixuan, and Srikant Rayadurgam. Enhancing the reliability of out-of-distribution image detection in neural networks. arXiv preprint arXiv:1706.02690, 2017. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Enhancing%20the%20reliability%20of%20out-of-distribution%20image%20detection%20in%20neural%20networks&author=Shiyu%20Liang&author=Yixuan%20Li&author=Rayadurgam%20Srikant&publication_year=2017&)]
43. Liu Weitang, Wang Xiaoyun, Owens John, and Li Yixuan. Energy-based out-of-distribution detection. Advances in neural information processing systems, 33:21464–21475, 2020. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20neural%20information%20processing%20systems&title=Energy-based%20out-of-distribution%20detection&author=Weitang%20Liu&author=Xiaoyun%20Wang&author=John%20Owens&author=Yixuan%20Li&volume=33&publication_year=2020&pages=21464-21475&)]
44. Liu Zhuang, Mao Hanzi, Wu Chao-Yuan, Feichtenhofer Christoph, Darrell Trevor, and Xie Saining. A convnet for the 2020s. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 11976–11986, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%20IEEE/CVF%20Conference%20on%20Computer%20Vision%20and%20Pattern%20Recognition&title=A%20convnet%20for%20the%202020s&author=Zhuang%20Liu&author=Hanzi%20Mao&author=Chao-Yuan%20Wu&author=Christoph%20Feichtenhofer&author=Trevor%20Darrell&publication_year=2022&pages=11976-11986&)]
45. Liu Ziyin, Wang Zhikang, Liang Paul Pu, Salakhutdinov Russ R, Morency Louis-Philippe, and Ueda Masahito. Deep gamblers: Learning to abstain with portfolio theory. Advances in Neural Information Processing Systems, 32, 2019. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20Neural%20Information%20Processing%20Systems&title=Deep%20gamblers:%20Learning%20to%20abstain%20with%20portfolio%20theory&author=Ziyin%20Liu&author=Zhikang%20Wang&author=Paul%20Pu%20Liang&author=Russ%20R%20Salakhutdinov&author=Louis-Philippe%20Morency&volume=32&publication_year=2019&)]
46. Maddox Wesley J, Izmailov Pavel, Garipov Timur, Vetrov Dmitry P, and Wilson Andrew Gordon. A simple baseline for bayesian uncertainty in deep learning. Advances in neural information processing systems, 32, 2019. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20neural%20information%20processing%20systems&title=A%20simple%20baseline%20for%20bayesian%20uncertainty%20in%20deep%20learning&author=Wesley%20J%20Maddox&author=Pavel%20Izmailov&author=Timur%20Garipov&author=Dmitry%20P%20Vetrov&author=Andrew%20Gordon%20Wilson&volume=32&publication_year=2019&)]
47. Mohri Mehryar, Rostamizadeh Afshin, and Talwalkar Ameet. Foundations of machine learning. MIT press, 2018. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=Foundations%20of%20machine%20learning&author=Mehryar%20Mohri&author=Afshin%20Rostamizadeh&author=Ameet%20Talwalkar&publication_year=2018&)]
48. Müller Jens, Radev Stefan T, Schmier Robert, Draxler Felix, Rother Carsten, and Köthe Ullrich. Finding competence regions in domain generalization. arXiv preprint arXiv:2303.09989, 2023. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Finding%20competence%20regions%20in%20domain%20generalization&author=Jens%20M%C3%BCller&author=Stefan%20T%20Radev&author=Robert%20Schmier&author=Felix%20Draxler&author=Carsten%20Rother&publication_year=2023&)]
49. Ni Jianmo, Li Jiacheng, and McAuley Julian. Justifying recommendations using distantly-labeled reviews and fine-grained aspects. In Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP), 2019. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%202019%20Conference%20on%20Empirical%20Methods%20in%20Natural%20Language%20Processing%20and%20the%209th%20International%20Joint%20Conference%20on%20Natural%20Language%20Processing%20(EMNLP-IJCNLP)&title=Justifying%20recommendations%20using%20distantly-labeled%20reviews%20and%20fine-grained%20aspects&author=Jianmo%20Ni&author=Jiacheng%20Li&author=Julian%20McAuley&publication_year=2019&)]
50. Nixon Jeremy, Dusenberry Michael W, Zhang Linchuan, Jerfel Ghassen, and Tran Dustin. Measuring calibration in deep learning. In CVPR workshops, volume 2, 2019. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=CVPR%20workshops&title=Measuring%20calibration%20in%20deep%20learning&author=Jeremy%20Nixon&author=Michael%20W%20Dusenberry&author=Linchuan%20Zhang&author=Ghassen%20Jerfel&author=Dustin%20Tran&volume=2&publication_year=2019&)]
51. Park Jaewoo, Jung Yoon Gyo, and Teoh Andrew Beng Jin. Nearest neighbor guidance for out-of-distribution detection. In Proceedings of the IEEE/CVF International Conference on Computer Vision, pp. 1686–1695, 2023. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%20IEEE/CVF%20International%20Conference%20on%20Computer%20Vision&title=Nearest%20neighbor%20guidance%20for%20out-of-distribution%20detection&author=Jaewoo%20Park&author=Yoon%20Gyo%20Jung&author=Andrew%20Beng%20Jin%20Teoh&publication_year=2023&pages=1686-1695&)]
52. Pietraszek Tadeusz. Optimizing abstaining classifiers using roc analysis. In Proceedings of the 22nd international conference on Machine learning, pp. 665–672, 2005. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%2022nd%20international%20conference%20on%20Machine%20learning&title=Optimizing%20abstaining%20classifiers%20using%20roc%20analysis&author=Tadeusz%20Pietraszek&publication_year=2005&pages=665-672&)]
53. Quinonero-Candela Joaquin, Sugiyama Masashi, Schwaighofer Anton, and Lawrence Neil D. Dataset shift in machine learning. Mit Press, 2008. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=Dataset%20shift%20in%20machine%20learning&author=Joaquin%20Quinonero-Candela&author=Masashi%20Sugiyama&author=Anton%20Schwaighofer&author=Neil%20D%20Lawrence&publication_year=2008&)]
54. Rabanser Stephan, Günnemann Stephan, and Lipton Zachary. Failing loudly: An empirical study of methods for detecting dataset shift. Advances in Neural Information Processing Systems, 32, 2019. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20Neural%20Information%20Processing%20Systems&title=Failing%20loudly:%20An%20empirical%20study%20of%20methods%20for%20detecting%20dataset%20shift&author=Stephan%20Rabanser&author=Stephan%20G%C3%BCnnemann&author=Zachary%20Lipton&volume=32&publication_year=2019&)]
55. Radford Alec, Kim Jong Wook, Hallacy Chris, Ramesh Aditya, Goh Gabriel, Agarwal Sandhini, Sastry Girish, Askell Amanda, Mishkin Pamela, Clark Jack, et al. Learning transferable visual models from natural language supervision. In International conference on machine learning, pp. 8748–8763. PMLR, 2021. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=International%20conference%20on%20machine%20learning&author=Alec%20Radford&author=Jong%20Wook%20Kim&author=Chris%20Hallacy&author=Aditya%20Ramesh&author=Gabriel%20Goh&publication_year=2021&)]
56. Russakovsky Olga, Deng Jia, Su Hao, Krause Jonathan, Satheesh Sanjeev, Ma Sean, Huang Zhiheng, Karpathy Andrej, Khosla Aditya, Bernstein Michael, et al. Imagenet large scale visual recognition challenge. International journal of computer vision, 115:211–252, 2015. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=International%20journal%20of%20computer%20vision&title=Imagenet%20large%20scale%20visual%20recognition%20challenge&author=Olga%20Russakovsky&author=Jia%20Deng&author=Hao%20Su&author=Jonathan%20Krause&author=Sanjeev%20Satheesh&volume=115&publication_year=2015&pages=211-252&)]
57. Saito Takaya and Rehmsmeier Marc. The precision-recall plot is more informative than the roc plot when evaluating binary classifiers on imbalanced datasets. PloS one, 10(3):e0118432, 2015. [[DOI](https://doi.org/10.1371/journal.pone.0118432)] [[PMC free article](/articles/PMC4349800/)] [[PubMed](https://pubmed.ncbi.nlm.nih.gov/25738806/)] [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=PloS%20one&title=The%20precision-recall%20plot%20is%20more%20informative%20than%20the%20roc%20plot%20when%20evaluating%20binary%20classifiers%20on%20imbalanced%20datasets&author=Takaya%20Saito&author=Marc%20Rehmsmeier&volume=10&issue=3&publication_year=2015&pages=e0118432&pmid=25738806&doi=10.1371/journal.pone.0118432&)]
58. Sun Yiyou, Guo Chuan, and Li Yixuan. React: Out-of-distribution detection with rectified activations. Advances in Neural Information Processing Systems, 34:144–157, 2021. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20Neural%20Information%20Processing%20Systems&title=React:%20Out-of-distribution%20detection%20with%20rectified%20activations&author=Yiyou%20Sun&author=Chuan%20Guo&author=Yixuan%20Li&volume=34&publication_year=2021&pages=144-157&)]
59. Sun Yiyou, Ming Yifei, Zhu Xiaojin, and Li Yixuan. Out-of-distribution detection with deep nearest neighbors. In International Conference on Machine Learning, pp. 20827–20840. PMLR, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=International%20Conference%20on%20Machine%20Learning&author=Yiyou%20Sun&author=Yifei%20Ming&author=Xiaojin%20Zhu&author=Yixuan%20Li&publication_year=2022&)]
60. Villmann Thomas, Kaden Marika, Bohnsack Andrea, Villmann J-M, Drogies T, Saralajew Sascha, and Hammer Barbara. Self-adjusting reject options in prototype based classification. In Advances in Self-Organizing Maps and Learning Vector Quantization: Proceedings of the 11th International Workshop WSOM 2016, Houston, Texas, USA, January 6-8, 2016, pp. 269–279. Springer, 2016. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=Advances%20in%20Self-Organizing%20Maps%20and%20Learning%20Vector%20Quantization:%20Proceedings%20of%20the%2011th%20International%20Workshop%20WSOM%202016,%20Houston,%20Texas,%20USA&author=Thomas%20Villmann&author=Marika%20Kaden&author=Andrea%20Bohnsack&author=J-M%20Villmann&author=T%20Drogies&publication_year=2016&)]
61. Wang Haoqi, Li Zhizhong, Feng Litong, and Zhang Wayne. Vim: Out-of-distribution with virtual-logit matching. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pp. 4921–4930, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%20IEEE/CVF%20conference%20on%20computer%20vision%20and%20pattern%20recognition&title=Vim:%20Out-of-distribution%20with%20virtual-logit%20matching&author=Haoqi%20Wang&author=Zhizhong%20Li&author=Litong%20Feng&author=Wayne%20Zhang&publication_year=2022&pages=4921-4930&)]
62. Wightman Ross. Pytorch image models. <https://github.com/rwightman/pytorch-image-models>, 2019.
63. Xia Guoxuan and Bouganis Christos-Savvas. Augmenting softmax information for selective classification with out-of-distribution data. In Proceedings of the Asian Conference on Computer Vision, pp. 1995–2012, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%20Asian%20Conference%20on%20Computer%20Vision&title=Augmenting%20softmax%20information%20for%20selective%20classification%20with%20out-of-distribution%20data&author=Guoxuan%20Xia&author=Christos-Savvas%20Bouganis&publication_year=2022&pages=1995-2012&)]
64. Xie Saining, Girshick Ross, Piotr Dollár Zhuowen Tu, and He Kaiming. Aggregated residual transformations for deep neural networks. In Proceedings of the IEEE conference on computer vision and pattern recognition, pp. 1492–1500, 2017. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%20IEEE%20conference%20on%20computer%20vision%20and%20pattern%20recognition&title=Aggregated%20residual%20transformations%20for%20deep%20neural%20networks&author=Saining%20Xie&author=Ross%20Girshick&author=Zhuowen%20Tu%20Piotr%20Doll%C3%A1r&author=Kaiming%20He&publication_year=2017&pages=1492-1500&)]
65. Yang Jingkang, Zhou Kaiyang, Li Yixuan, and Liu Ziwei. Generalized out-of-distribution detection: A survey. arXiv preprint arXiv:2110.11334, 2021. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Generalized%20out-of-distribution%20detection:%20A%20survey&author=Jingkang%20Yang&author=Kaiyang%20Zhou&author=Yixuan%20Li&author=Ziwei%20Liu&publication_year=2021&)]
66. Yang Jingkang, Wang Pengyun, Zou Dejian, Zhou Zitang, Ding Kunyuan, Peng Wenxuan, Wang Haoqi, Chen Guangyao, Li Bo, Sun Yiyou, et al. Openood: Benchmarking generalized out-of-distribution detection. Advances in Neural Information Processing Systems, 35:32598–32611, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Advances%20in%20Neural%20Information%20Processing%20Systems&title=Openood:%20Benchmarking%20generalized%20out-of-distribution%20detection&author=Jingkang%20Yang&author=Pengyun%20Wang&author=Dejian%20Zou&author=Zitang%20Zhou&author=Kunyuan%20Ding&volume=35&publication_year=2022&pages=32598-32611&)]
67. Yao Huaxiu, Wang Yu, Li Sai, Zhang Linjun, Liang Weixin, Zou James, and Finn Chelsea. Improving out-of-distribution robustness via selective augmentation. In International Conference on Machine Learning, pp. 25407–25437. PMLR, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=International%20Conference%20on%20Machine%20Learning&author=Huaxiu%20Yao&author=Yu%20Wang&author=Sai%20Li&author=Linjun%20Zhang&author=Weixin%20Liang&publication_year=2022&)]
68. Yuan Li, Hou Qibin, Jiang Zihang, Feng Jiashi, and Yan Shuicheng. Volo: Vision outlooker for visual recognition. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=IEEE%20Transactions%20on%20Pattern%20Analysis%20and%20Machine%20Intelligence&title=Volo:%20Vision%20outlooker%20for%20visual%20recognition&author=Li%20Yuan&author=Qibin%20Hou&author=Zihang%20Jiang&author=Jiashi%20Feng&author=Shuicheng%20Yan&publication_year=2022&)]
69. Yuan Lu, Chen Dongdong, Chen Yi-Ling, Codella Noel, Dai Xiyang, Gao Jianfeng, Hu Houdong, Huang Xuedong, Li Boxin, Li Chunyuan, et al. Florence: A new foundation model for computer vision. arXiv preprint arXiv:2111.11432, 2021. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=arXiv&title=Florence:%20A%20new%20foundation%20model%20for%20computer%20vision&author=Lu%20Yuan&author=Dongdong%20Chen&author=Yi-Ling%20Chen&author=Noel%20Codella&author=Xiyang%20Dai&publication_year=2021&)]
70. Zhang Xu-Yao, Xie Guo-Sen, Li Xiuli, Mei Tao, and Liu Cheng-Lin. A survey on learning to reject. Proceedings of the IEEE, 111(2):185–215, 2023. [[Google Scholar](https://scholar.google.com/scholar_lookup?journal=Proceedings%20of%20the%20IEEE&title=A%20survey%20on%20learning%20to%20reject&author=Xu-Yao%20Zhang&author=Guo-Sen%20Xie&author=Xiuli%20Li&author=Tao%20Mei&author=Cheng-Lin%20Liu&volume=111&issue=2&publication_year=2023&pages=185-215&)]
71. Zhu Fei, Cheng Zhen, Zhang Xu-Yao, and Liu Cheng-Lin. Rethinking confidence calibration for failure prediction. In Computer Vision–ECCV 2022: 17th European Conference, Tel Aviv, Israel, October 23–27, 2022, Proceedings, Part XXV, pp. 518–536. Springer, 2022. [[Google Scholar](https://scholar.google.com/scholar_lookup?title=Computer%20Vision%E2%80%93ECCV%202022:%2017th%20European%20Conference,%20Tel%20Aviv,%20Israel,%20October%2023%E2%80%9327,%202022,%20Proceedings,%20Part%20XXV&author=Fei%20Zhu&author=Zhen%20Cheng&author=Xu-Yao%20Zhang&author=Cheng-Lin%20Liu&publication_year=2022&)]

## ACTIONS

* [![Download PDF icon](https://cdn.ncbi.nlm.nih.gov/pmc/pd-medc-pmc-cloudpmc-viewer/production/674d4f95/var/data/static/img/file_download.svg) PDF (2.4 MB)](pdf/nihms-2088989.pdf)

* ## PERMALINK

## RESOURCES

###

###

###

* [![Download icon](https://cdn.ncbi.nlm.nih.gov/pmc/pd-medc-pmc-cloudpmc-viewer/production/674d4f95/var/data/static/img/file_download.svg) Download .nbib .nbib](# "Download a file for external citation management software")

## Add to Collections
