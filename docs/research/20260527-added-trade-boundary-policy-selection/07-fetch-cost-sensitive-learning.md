### [Navigation](#navigation)

![MachineLearningMastery.com](https://machinelearningmastery.com/wp-content/uploads/2024/10/mlm-logo.svg)

Making developers awesome at machine learning

![](https://machinelearningmastery.com/wp-content/uploads/2024/10/mlm-logo.svg)

Making Developers Awesome at Machine Learning

Making developers awesome at machine learning

![](https://machinelearningmastery.com/wp-content/uploads/2024/10/mlm-logo.svg)

Making Developers Awesome at Machine Learning

# Cost-Sensitive Learning for Imbalanced Classification

Most machine learning algorithms assume that all misclassification errors made by a model are equal.

This is often not the case for imbalanced classification problems where missing a positive or minority class case is worse than incorrectly classifying an example from the negative or majority class. There are many real-world examples, such as detecting spam email, diagnosing a medical condition, or identifying fraud. In all of these cases, a false negative (missing a case) is worse or more costly than a false positive.

**Cost-sensitive learning** is a subfield of machine learning that takes the costs of prediction errors (and potentially other costs) into account when training a machine learning model. It is a field of study that is closely related to the field of imbalanced learning that is concerned with classification on datasets with a skewed class distribution. As such, many conceptualizations and techniques developed and used for cost-sensitive learning can be adopted for imbalanced classification problems.

In this tutorial, you will discover a gentle introduction to cost-sensitive learning for imbalanced classification.

After completing this tutorial, you will know:

**Kick-start your project** with my new book [Imbalanced Classification with Python](https://machinelearningmastery.com/imbalanced-classification-with-python/), including *step-by-step tutorials* and the *Python source code* files for all examples.

Let’s get started.

![Cost-Sensitive Learning for Imbalanced Classification](https://machinelearningmastery.com/wp-content/uploads/2020/02/Cost-Sensitive-Learning-for-Imbalanced-Classification.jpg)

Cost-Sensitive Learning for Imbalanced Classification
Photo by [bvi4092](https://flickr.com/photos/bvi4092/33035819163/), some rights reserved.

## Tutorial Overview

This tutorial is divided into four parts; they are:

## Not All Classification Errors Are Equal

Classification is a predictive modeling problem that involves predicting the class label for an observation.

There may be many class labels, so-called multi-class classification problems, although the simplest and perhaps most common type of classification problem has two classes and is referred to as binary classification.

Most machine learning algorithms designed for classification assume that there is an equal number of examples for each observed class.

This is not always the case in practice, and datasets that have a skewed class distribution are referred to as imbalanced classification problems.

In cost-sensitive learning instead of each instance being either correctly or incorrectly classified, each class (or instance) is given a misclassification cost. Thus, instead of trying to optimize the accuracy, the problem is then to minimize the total misclassification cost.

— Page 50, [Imbalanced Learning: Foundations, Algorithms, and Applications](https://amzn.to/32K9K6d), 2013.

In addition to assuming that the class distribution is balanced, most machine learning algorithms also assume that the prediction errors made by a classifier are the same, so-called miss-classifications.

This is typically not the case for binary classification problems, especially those that have an imbalanced class distribution.

Most classifiers assume that the misclassification costs (false negative and false positive cost) are the same. In most real-world applications, this assumption is not true.

— [Cost-sensitive Learning Methods For Imbalanced Data](https://ieeexplore.ieee.org/document/5596486), 2010.

For imbalanced classification problems, the examples from the majority class are referred to as the negative class and assigned the class label 0. Those examples from the minority class are referred to as the positive class and are assigned the class label 1.

The reason for this negative vs. positive naming convention is because the examples from the majority class typically represent a normal or no-event case, whereas examples from the minority class represent the exceptional or event case.

Real-world imbalanced binary classification problems typically have a different interpretation for each of the classification errors that can be made. For example, classifying a negative case as a positive case is typically far less of a problem than classifying a positive case as a negative case.

This makes sense if we consider the goal of a classifier on imbalanced binary classification problems is to detect the positive cases correctly and positive cases represent an exceptional or event that we are most interested in.

We can make this clear with some examples.

**Bank Loan Problem**: Consider a problem where a bank wants to determine whether to give a loan to a customer or not. Denying a loan to a good customer is not as bad as giving a loan to a bad customer that may never repay it.

**Cancer Diagnosis Problem**: Consider a problem where a doctor wants to determine whether a patient has cancer or not. It is better to diagnose a healthy patient with cancer and follow-up with more medical tests than it is to discharge a patient that has cancer.

… in medical diagnosis of a certain cancer, if the cancer is regarded as the positive class, and non-cancer (healthy) as negative, then missing a cancer (the patient is actually positive but is classified as negative; thus it is also called “false negative”) is much more serious (thus expensive) than the false-positive error.

— [Cost-Sensitive Learning, Encyclopedia of Machine Learning](https://amzn.to/2PamKhX), 2010.

**Fraud Detection Problem**: Consider the problem of an insurance company wants to determine whether a claim is fraudulent. Identifying good claims as fraudulent and following up with the customer is better than honoring fraudulent insurance claims.

We can see with these examples that misclassification errors are not desirable in general, but one type of misclassification is much worse than the other. Specifically predicting positive cases as a negative case is more harmful, more expensive, or worse in whatever way we want to measure the context of the target domain.

… it is often more expensive to misclassify an actual positive example into negative, than an actual negative example into positive.

— [Cost-Sensitive Learning, Encyclopedia of Machine Learning](https://amzn.to/2PamKhX), 2010.

Machine learning algorithms that treat each type of misclassification error as the same are unable to meet the needs of these types of problems.

As such, both the underrepresentation of the minority class in the training data and the increased importance on correctly identifying examples from the minority class make imbalanced classification one of the most challenging problems in applied machine learning.

Class imbalance is one of the challenging problems for machine learning algorithms.

— [Cost-sensitive Learning Methods For Imbalanced Data](https://ieeexplore.ieee.org/document/5596486), 2010.

### Want to Get Started With Imbalance Classification?

Take my free 7-day email crash course now (with sample code).

Click to sign-up and also get a free PDF Ebook version of the course.

Download Your FREE Mini-Course

## Cost-Sensitive Learning

There is a subfield of machine learning that is focused on learning and using models on data that have uneven penalties or costs when making predictions and more.

This field is generally referred to as Cost-Sensitive Machine Learning, or more simply Cost-Sensitive Learning.

… the machine learning algorithm needs to be sensitive to the cost that it is dealing with, and in the better case take the cost into account in the model fitting process. This leads to cost-sensitive machine learning, a relatively new research topic in machine learning.

— Page xiii, [Cost-Sensitive Machine Learning](https://amzn.to/2qFgswK), 2011.

Traditionally, machine learning algorithms are trained on a dataset and seek to minimize error. Fitting a model on data solves an optimization problem where we explicitly seek to minimize error. A range of functions can be used to calculate the error of a model on training data, and the more general term is referred to as loss. We seek to minimize the loss of a model on the training data, which is the same as talking about error minimization.

In cost-sensitive learning, a penalty associated with an incorrect prediction and is referred to as a “*cost*.” We could alternately refer to the inverse of the penalty as the “*benefit*“, although this framing is rarely used.

The goal of cost-sensitive learning is to minimize the cost of a model on the training dataset, where it is assumed that different types of prediction errors have a different and known associated cost.

Cost-Sensitive Learning is a type of learning that takes the misclassification costs (and possibly other types of cost) into consideration. The goal of this type of learning is to minimize the total cost.

— [Cost-Sensitive Learning, Encyclopedia of Machine Learning](https://amzn.to/2PamKhX), 2010.

There is a tight-coupling between imbalanced classification and cost-sensitive learning. Specifically, an imbalanced learning problem can be addressed using cost-sensitive learning.

Nevertheless, cost-sensitive learning is a separate subfield of study and cost may be defined more broadly than prediction error or classification error. This means that although some methods from cost-sensitive learning can be helpful on imbalanced classification, not all cost-sensitive learning techniques are imbalanced-learning techniques, and conversely, not all methods used to address imbalanced learning are appropriate for cost-sensitive learning.

To make this concrete, we can consider a wide range of other ways we might wish to consider or measure cost when training a model on a dataset. For example, [Peter Turney](https://www.apperceptual.com) lists nine types of costs that might be considered in machine learning in his 2000 paper titled “[Types of Cost in Inductive Concept Learning](https://arxiv.org/abs/cs/0212034).”

In summary, they are:

Although critical to many real-world problems, the idea of costs and cost-sensitive learning is a new topic that was largely ignored up until recently.

In real-world applications of concept learning, there are many different types of cost involved. The majority of the machine learning literature ignores all types of cost …

— [Types of Cost in Inductive Concept Learning](https://arxiv.org/abs/cs/0212034), 2000.

The above list highlights that the cost we are interested in for imbalanced-classification is just one type of the range of costs that the broader field of cost-sensitive learning might consider.

In the next section, we will take a closer look at how we can harness ideas of misclassification cost-sensitive learning to help with imbalanced classification.

## Cost-Sensitive Imbalanced Classification

Cost-sensitive learning for imbalanced classification is focused on first assigning different costs to the types of misclassification errors that can be made, then using specialized methods to take those costs into account.

The varying misclassification costs are best understood using the idea of a cost matrix.

Let’s start by reviewing the confusion matrix.

A [confusion matrix](https://machinelearningmastery.com/ufaqs/what-is-a-confusion-matrix/) is a summary of the predictions made by a model on classification tasks. It is a table that summarizes the number of predictions made for each class, separated by the actual class to which each example belongs.

It is best understood using a binary classification problem with negative and positive classes, typically assigned 0 and 1 class labels respectively. The columns of the table represent the actual class to which examples belong, and the rows represent the predicted class (although the meaning of rows and columns can and often are interchanged with no loss of meaning). A cell in the table is the count of the number of examples that meet the conditions of the row and column, and each cell has a specific common name.

An example of a confusion matrix for a binary classification task is listed below showing the common names for the values in each of the four cells of the table.

|  |  |
| --- | --- |
| 1  2  3 | | Actual Negative | Actual Positive  Predicted Negative | True Negative   | False Negative  Predicted Positive | False Positive  | True Positive |

We can see that we are most interested in the errors, the so-called False Positives and False Negatives, and it is the False Negatives that probably interest us the most on many imbalanced classification tasks.

Now, we can consider the same table with the same rows and columns and assign a cost to each of the cells. This is called a cost matrix.

The example below is a cost matrix where we use the notation *C()* to indicate the cost, the first value represented as the predicted class and the second value represents the actual class. The names of each cell from the confusion matrix are also listed as acronyms, e.g. False Positive is FP.

|  |  |
| --- | --- |
| 1  2  3 | | Actual Negative | Actual Positive  Predicted Negative | C(0,0), TN      | C(0,1), FN  Predicted Positive | C(1,0), FP      | C(1,1), TP |

We can see that the cost of a False Positive is C(1,0) and the cost of a False Negative is C(0,1).

This formulation and notation of the cost matrix comes from [Charles Elkan’s](https://www.linkedin.com/in/celkan/) seminal 2001 paper on the topic titled “[The Foundations of Cost-Sensitive Learning](https://dl.acm.org/citation.cfm?id=1642224).”

An intuition from this matrix is that the cost of misclassification is always higher than correct classification, otherwise, cost can be minimized by predicting one class.

Conceptually, the cost of labeling an example incorrectly should always be greater than the cost of labeling it correctly.

— [The Foundations Of Cost-sensitive Learning](https://dl.acm.org/citation.cfm?id=1642224), 2001.

For example, we might assign no cost to correct predictions in each class, a cost of 5 for False Positives and a cost of 88 for False Negatives.

|  |  |
| --- | --- |
| 1  2  3 | | Actual Negative | Actual Positive  Predicted Negative | 0               | 88  Predicted Positive | 5               | 0 |

We can define the total cost of a classifier using this framework as the cost-weighted sum of the False Negatives and False Positives.

This is the value that we seek to minimize in cost-sensitive learning, at least conceptually.

The purpose of CSL is to build a model with minimum misclassification costs (total cost)

— [Cost-sensitive Learning Methods For Imbalanced Data](https://ieeexplore.ieee.org/document/5596486), 2010.

The values of the cost matrix must be carefully defined. Like the choice of error function for traditional machine learning models, the choice of costs or cost function will determine the quality and utility of the model that is fit on the training data.

The effectiveness of cost-sensitive learning relies strongly on the supplied cost matrix. Parameters provided there will be of crucial importance to both training and predictions steps.

— Page 66, [Learning from Imbalanced Data Sets](https://amzn.to/307Xlva), 2018.

In some problem domains, defining the cost matrix might be obvious. In an insurance claim example, the costs for a false positive might be the monetary cost of follow-up with the customer to the company and the cost of a false negative might be the cost of the insurance claim.

In other domains, defining the cost matrix might be challenging. For example, in a cancer diagnostic test example, the cost of a false positive might be the monetary cost of performing subsequent tests, whereas what is the equivalent dollar cost for letting a sick patient go home and get sicker? A cost matrix might be able to be defined by a domain expert or economist in such cases, or not.

Further, the cost might be a complex multi-dimensional function, including monetary costs, reputation costs, and more.

A good starting point for imbalanced classification tasks is to assign costs based on the inverse class distribution.

In many cases we do not have access to a domain expert and no a priori information on cost matrix is available during classifier training. This is a common scenario when we want to apply cost-sensitive learning as a method for solving imbalanced problems …

— Page 67, [Learning from Imbalanced Data Sets](https://amzn.to/307Xlva), 2018.

For example, we may have a dataset with a 1 to 100 (1:100) ratio of examples in the minority class to examples in the majority class. This ratio can be inverted and used as the cost of misclassification errors, where the cost of a False Negative is 100 and the cost of a False Positive is 1.

|  |  |
| --- | --- |
| 1  2  3 | | Actual Negative | Actual Positive  Predicted Negative | 0               | 100  Predicted Positive | 1               | 0 |

This is an effective heuristic for setting costs in general, although it assumes that the class distribution observed in the training data is representative of the broader problem and is appropriate for the chosen cost-sensitive method being used.

As such, it is a good idea to use this heuristic as a starting point, then test a range of similar related costs or ratios to confirm it is sensible.

## Cost-Sensitive Methods

Cost-sensitive machine learning methods are those that explicitly use the cost matrix.

Given our focus on imbalanced classification, we are specifically interested in those cost-sensitive techniques that focus on using varying misclassification costs in some way.

Cost-sensitive learning methods target the problem of imbalanced learning by using different cost matrices that describe the costs for misclassifying any particular data example.

— Page 3-4, [Imbalanced Learning: Foundations, Algorithms, and Applications](https://amzn.to/32K9K6d), 2013.

There are perhaps three main groups of cost-sensitive methods that are most relevant for imbalanced learning; they are:

Let’s take a closer look at each in turn.

### Cost-Sensitive Resampling

In imbalanced classification, data resampling refers to techniques that transform the training dataset to better balance the class distribution.

This may involve selectively deleting examples from the majority class, referred to as undersampling. More commonly, it refers to duplicating or synthesizing new examples in the minority class, referred to as oversampling, or combinations of both undersampling and oversampling.

Data resampling is a technique that can be used for cost-sensitive learning directly. Instead of resampling with a focus on balancing the skewed class distribution, the focus is on changing the composition of the training dataset to meet the expectations of the cost matrix.

This might involve directly resampling the data distribution or using a method to weight examples in the dataset. Such methods may be referred to as cost-proportionate weighing of the training dataset or cost-proportionate resampling.

We propose and evaluate a family of methods […] based on cost-proportionate weighting of the training examples, which can be realized either by feeding the weights to the classification algorithm (as often done in boosting), or (in a black box manner) by careful subsampling.

— [Cost-Sensitive Learning by Cost-Proportionate Example Weighting](https://dl.acm.org/citation.cfm?id=952181), 2003.

For imbalanced classification where the cost matrix is defined using the class distribution, then there is no difference in the data resampling technique.

### Cost-Sensitive Algorithms

Machine learning algorithms are rarely developed specifically for cost-sensitive learning.

Instead, the wealth of existing machine learning algorithms can be modified to make use of the cost matrix.

This might involve a modification that is unique to each algorithm and which can be quite time consuming to develop and test. Many such algorithm-specific augmentations have been proposed for popular algorithms, like decision trees and support vector machines.

Among all of the classifiers, induction of cost-sensitive decision trees has arguably gained the most attention.

— Page 69, [Learning from Imbalanced Data Sets](https://amzn.to/307Xlva), 2018.

The scikit-learn Python machine learning library provides examples of these cost-sensitive extensions via the *class\_weight* argument on the following classifiers:

Another more general approach to modifying existing algorithms is to use the costs as a penalty for misclassification when the algorithms are trained. Given that most machine learning algorithms are trained to minimize error, cost for misclassification is added to the error or used to weigh the error during the training process.

This approach can be used for iteratively trained algorithms, such as logistic regression and artificial neural networks.

The scikit-learn library provides examples of these cost-sensitive extensions via the *class\_weight* argument on the following classifiers:

The [Keras Python Deep Learning library](https://machinelearningmastery.com/tutorial-first-neural-network-python-keras/) also provides access to this use of cost-sensitive augmentation for neural networks via the *class\_weight* argument on the [fit() function](https://keras.io/models/sequential/) when training models.

Again, the line is blurred between cost-sensitive augmentations to algorithms vs. imbalanced classification augmentations to algorithms when the inverse class distribution is used as the cost matrix.

In the domain of cost-sensitive machine learning, these algorithms are referred to with the “*Cost-Sensitive*” prefix, e.g. Cost-Sensitive Logistic Regression, whereas in imbalanced-learning, such algorithms are referred to with a “*Class-Weighted*” prefix, e.g. Class-Weighted Logistic Regression or simply Weighted Logistic Regression.

### Cost-Sensitive Ensembles

A second distinct group of methods is techniques designed to filter or combine the predictions from traditional machine learning models in order to take misclassification costs into account.

These methods are referred to as “*wrapper methods*” as they wrap a standard machine learning classifier. They are also referred to as “*meta-learners*” or “*ensembles*” as they learn how to use or combine predictions from other models.

Cost-sensitive meta-learning converts existing cost-insensitive classifiers into cost-sensitive ones without modifying them. Thus, it can be regarded as a middleware component that pre-processes the training data, or post-processes the output, from the cost-insensitive learning algorithms.

— [Cost-Sensitive Learning, Encyclopedia of Machine Learning](https://amzn.to/2PamKhX), 2010.

Perhaps the simplest approach is the use of a machine learning model to predict the probability of class membership, then using a line search on the threshold at which examples are assigned to each crisp class label that minimizes the cost of misclassification.

This is often referred to as “*thresholding*” or threshold optimization and is used more generally for binary classification tasks, although it can easily be modified to minimize cost instead of a specific type of classification error metric.

MetaCost is a data preprocessing technique that relabels examples in the training dataset in order to minimize cost.

… we propose a principled method for making an arbitrary classifier cost-sensitive by wrapping a cost-minimizing procedure around it.

— [MetaCost: A General Method for Making Classifiers Cost-Sensitive](https://dl.acm.org/citation.cfm?id=312220), 1999.

In MetaCost, first a bagged ensemble of classifiers is fit on the training dataset in order to identify those examples that need to be relabeled, a transformed version of the dataset with relabeled examples is created, then the ensemble is discarded and the transformed dataset is used to train a classifier model.

Another important area is modifications to decision tree ensembles that take the cost matrix into account, such as bagging and boosting algorithms, most notably cost-sensitive versions of AdaBoost such as AdaCost.

AdaCost, a variant of AdaBoost, is a misclassification cost-sensitive boosting method. It uses the cost of misclassifications to update the training distribution on successive boosting rounds.

— [AdaCost: Misclassification Cost-Sensitive Boosting](https://dl.acm.org/citation.cfm?id=657651), 1999.

## Further Reading

This section provides more resources on the topic if you are looking to go deeper.

### Papers

### Books

### Articles

## Summary

In this tutorial, you discovered cost-sensitive learning for imbalanced classification.

Specifically, you learned:

Do you have any questions?
Ask your questions in the comments below and I will do my best to answer.

## Get a Handle on Imbalanced Classification!

![Imbalanced Classification with Python](/wp-content/uploads/2022/11/ICP-220.png)

#### Develop Imbalanced Learning Models in Minutes

...with just a few lines of python code

Discover how in my new Ebook:
[Imbalanced Classification with Python](/imbalanced-classification-with-python/)

It provides **self-study tutorials** and **end-to-end projects** on:
*Performance Metrics*, *Undersampling Methods*, *SMOTE*, *Threshold Moving*, *Probability Calibration*, *Cost-Sensitive Algorithms*
and much more...

#### Bring Imbalanced Classification Methods to Your Machine Learning Projects

[See What's Inside](/imbalanced-classification-with-python/)

### More On This Topic

![Standard Machine Learning Datasets for Imbalanced Classification](https://machinelearningmastery.com/wp-content/uploads/2019/12/Standard-Machine-Learning-Datasets-for-Imbalanced-Classification.jpg "Standard Machine Learning Datasets for Imbalanced Classification")
![A Gentle Introduction to Imbalanced Classification](https://machinelearningmastery.com/wp-content/uploads/2019/12/A-Gentle-Introduction-to-Imbalanced-Classification.jpg "A Gentle Introduction to Imbalanced Classification")
![Best Resources for Imbalanced Classification](https://machinelearningmastery.com/wp-content/uploads/2019/12/Best-Resources-for-Imbalanced-Classification.jpg "Best Resources for Imbalanced Classification")
![Scatter Plot of Binary Classification Dataset With 1 to 100 Class Distribution](https://machinelearningmastery.com/wp-content/uploads/2019/10/Scatter-Plot-of-Binary-Classification-Dataset-With-1-to-100-Class-Distribution.png "Failure of Classification Accuracy for Imbalanced Class Distributions")
![How to Calculate Precision, Recall, and F-Measure for Imbalanced Classification](https://machinelearningmastery.com/wp-content/uploads/2020/01/How-to-Calculate-Precision-Recall-and-F-Measure-for-Imbalanced-Classification.jpg "How to Calculate Precision, Recall, and F-Measure for Imbalanced Classification")
![Precision-Recall Curve of a Logistic Regression Model and a No Skill Classifier](https://machinelearningmastery.com/wp-content/uploads/2020/01/Precision-Recall-Curve-of-a-Logistic-Regression-Model-and-a-No-Skill-Classifier2.png "ROC Curves and Precision-Recall Curves for Imbalanced Classification")
![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=80&d=mm&r=g)

#### About Jason Brownlee

### 39 Responses to *Cost-Sensitive Learning for Imbalanced Classification*

![](https://secure.gravatar.com/avatar/3a4b3d6973165d33b6ac124195a359b72bb7975e465909ebab9d2c8c9289eaa3?s=40&d=mm&r=g)

Hello Jason,
I have a classification problem.
I’m wondering whether Accuracy and AUC have the similar meaning and I have to use BOTH to evaluate one model?
In case of imbalanced dataset what is the best metric to use?

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Not at all.

Accuracy:
<https://machinelearningmastery.com/failure-of-accuracy-for-imbalanced-class-distributions/>

AUC:
<https://machinelearningmastery.com/roc-curves-and-precision-recall-curves-for-imbalanced-classification/>

How to choose a metric:
<https://machinelearningmastery.com/tour-of-evaluation-metrics-for-imbalanced-classification/>

![](https://secure.gravatar.com/avatar/3a4b3d6973165d33b6ac124195a359b72bb7975e465909ebab9d2c8c9289eaa3?s=40&d=mm&r=g)

Hello Jason,
One more question is about overfiitting.
Is it only a classification issue or it is also a regression issue?
Thanks

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Both for sure!

![](https://secure.gravatar.com/avatar/3a4b3d6973165d33b6ac124195a359b72bb7975e465909ebab9d2c8c9289eaa3?s=40&d=mm&r=g)

Hello Jason,
techniques to address overfitting in regression are the same of classification problems?
Thanks

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Yes, the same techniques can be used for both classification and regression.

![](https://secure.gravatar.com/avatar/fb23dee69887b5c6e07dd97da61807bd9e65212fb2e80c45a8ce2541dd4c8d82?s=40&d=mm&r=g)

I was looking for this subject a few weeks ago. As usual, your tutorial gives a broad and simple explication.
Thanks a lot.

My question: is there any connection between boosting techniques such as Adaboost and cost-sensitive learning?
Tanks in advance.

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Thanks!

Not really. Maybe from a “weight the instances” vs “weight the classes” perspective.

![](https://secure.gravatar.com/avatar/b136285fc8a40eed14d7671e1f9da18aa4c456dbbd4fb7640839a3a61844dcd1?s=40&d=mm&r=g)

Thanks for the wonderful tutorial.

I have one question if we have a multi-class classification model then how to interparate the cost for it to know the penalty of missclassification. As we are giving in binary classification based on FP and FN.

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

You can specify a cost for each class as a dictionary.

Perhaps experiment with different penalty values to see what works.

![](https://secure.gravatar.com/avatar/b136285fc8a40eed14d7671e1f9da18aa4c456dbbd4fb7640839a3a61844dcd1?s=40&d=mm&r=g)

Thank you sir,

Is it possible to get any of the solved example for this then it is easy to understandable?

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Yes, this tutorial gives an example of multi-class cost sensitive learning:
<https://machinelearningmastery.com/imbalanced-multiclass-classification-with-the-glass-identification-dataset/>

![](https://secure.gravatar.com/avatar/b136285fc8a40eed14d7671e1f9da18aa4c456dbbd4fb7640839a3a61844dcd1?s=40&d=mm&r=g)

thank you sir,

For your reference, I’ll go through this document.

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

You’re welcome.

![](https://secure.gravatar.com/avatar/b136285fc8a40eed14d7671e1f9da18aa4c456dbbd4fb7640839a3a61844dcd1?s=40&d=mm&r=g)

Thanks for the link and it helps me to clear many doubts related to model development and selection for the imbalanced multiclass dataset.

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

You’re welcome.

![](https://secure.gravatar.com/avatar/372e0a87138e9660d5afec1001028b1105cdadc496721fe032e7a9c5ab5acfff?s=40&d=mm&r=g)

Hi, is there a way I can create a custom loss function using a pre-defined penalty matrix for a multiclassification problem? I not only have an imbalanced dataset, but I also want to use penalty matrix in the training of my model.

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Yes, the weighting specified to the cost-sensitive model can be based on any design you like, e.g. a penalty or a reweighing, or a combination.

Ensure to select or devise a performance metric that takes the goals of the project into account.

![](https://secure.gravatar.com/avatar/9b847379c46fbfaf1e07c796fd0be05acd8958195b6cf0ec2fc1df32bdb8b488?s=40&d=mm&r=g)

Hi Jason,
First, thanks for your wonderful courses: whenever I have difficulties understanding something in Machine Learning, my first idea is to go to MachineLearningMastery. You have a rare ability to explain things.

\*\*My question is : are there cost sensitive learning method/algorithms for regression ?\*\*

( My example is : suppose you want to predict next week sales for each product category, but accuracy for category A is critical to you while accuracy for category B is less critical. )

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Thanks!

Yes, you are describing a time series classification problem, and cost-sensitive algorithms for classification can be used for this problem type directly, after you restructure your data to be an supervised learning problem:
<https://machinelearningmastery.com/time-series-forecasting-supervised-learning/>

![](https://secure.gravatar.com/avatar/eefc2d017973b745999bc51143f45cc8f19fec2c73b16a4027d88c93e10c49d2?s=40&d=mm&r=g)

Hi Jason! Your work is amazing! Is it possible to buy hard copies of your books to go with the electronic versions?

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Good question, I answer it here:
<https://machinelearningmastery.com/faq/single-faq/can-i-get-a-hard-copy-of-your-book>

![](https://secure.gravatar.com/avatar/efe114cc44d0c56dfd1a828462865bc783ab1f9c96d567f8f69112d82f476ab7?s=40&d=mm&r=g)

hello jason,
im wondering how can i make ID3 a missclasifaction sensitive?
what i want to do is to improve ID3 such that it minimize my loss func
loss(c)=(0.1\*Falsenegative+falsepositive)/(number of test examples)

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Good question, perhaps there is a cost sensitive version described in the literature, I recommend performing a lit review.

![](https://secure.gravatar.com/avatar/f0429df65759e9e78f975f260c6d8d2d6d932f1748177edd426825d00e5835bd?s=40&d=mm&r=g)

can i have a link?

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

<https://machinelearningmastery.com/faq/single-faq/where-can-i-get-a-research-paper-on-___>

![](https://secure.gravatar.com/avatar/1f07549150da0d0bf54240fa5cafd15f1c1b7f33d984303ebd19c3eddcd766d8?s=40&d=mm&r=g)

Another great article.
I have a question:
I have a multiclass classification (output 0 1 2 3 4 5) problem.

For my problem, zero is the important most class. Is there a way I can add extra weight/cost for class zero during training phase?

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Thanks!

Yes, you can assign a weight of 1 to class=0 and a weight of 0.5 to all other classes. Or something like that.

![](https://secure.gravatar.com/avatar/d64e8b2fe5c7de6af58d7ade7e29a21940d0a16d1ddbdc09b39009a190db2fe4?s=40&d=mm&r=g)

This is a great article,

i’have some questions for this part,

so the usual resampling of imbalanced data that we’ve used to balancing the data is actually one of the part of cost-sensitive classification?

and if I understand correctly, we should choose one of 3 method (resampling, algorithm, ensembles) to make the cost-sensitive model, not choose two or all of them. (for example, resampling with cost-weight and after, applying this same cost-weight in algorithm makes another imbalanced data?)

thank you so much,

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Typically you would choose a resampling algorithm or a cost-sensitive algorithm. Not both. But, it is possible that using both may give you better results, so test and confirm.

![](https://secure.gravatar.com/avatar/e7ebcfd93ca7c83f62ccdaac02739a8e658de658a2b7bc74337879df1a17dbdc?s=40&d=mm&r=g)

Great article.
I have a small question for you…
I have a multiclass document classification task based on the text(7 types)…
Problem is whatever document i am passing its showing the type from the above 7 types…
I dont know how to handle misclassifiaction…what can i do so that my model will predict the otger documents as NAN OR NONE..something like that and how to handle misclassification??

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

Perhaps you need to tune the performance of your model, e.g. these suggestions:
<https://machinelearningmastery.com/improve-deep-learning-performance/>

![](https://secure.gravatar.com/avatar/8140c272d973349b97406365ecc2158ad2c14f030766edbbecf8a5161f94e2ae?s=40&d=mm&r=g)

Hi Jason,

I have a multi-class imbalanced classification problem, where certain types of misclassification are more problematic than others. For example, misclassifying 0 as a 1, is much worse than misclassifying a 0 as a 2.

Is there any way you can recommend implementing this in Python?

I have thought about balancing the weights of each class in order to compensate for classes of different sizes, before then altering the weights again to reward the classifier for correctly predicting key classes. However, this does not solve my differential misclassification costs issue.

Thanks

![](https://secure.gravatar.com/avatar/5f1c8e7a708d04b1bd173e9120107d3fd43d8fad5be7c94796b877515b6d0357?s=40&d=mm&r=g)

I recommend selecting a metric first (this might be the hardest part of the project), then explore a suite of methods in order to discover what works well or best.

This might help:
<https://machinelearningmastery.com/framework-for-imbalanced-classification-projects/>

![](https://secure.gravatar.com/avatar/8140c272d973349b97406365ecc2158ad2c14f030766edbbecf8a5161f94e2ae?s=40&d=mm&r=g)

PS I would like to implement this cost sensitivity in a random forest, and I have been trying to implement what I mentioned above via the class\_weight parameter in sklearn.

![](https://secure.gravatar.com/avatar/3e252d54c3fbed87c131f170e3d9a578b0245a3cb646005d07532c0cc4b0bfbd?s=40&d=mm&r=g)

Hi Jason,

Thanks for your article. It is very useful. How to apply cost sensitive learning for timeseries forecasting problem. How to include cost matrix for timeseries forecasting? Any timeseries forecasting method currently supports cost matrix?

waiting for your response.

![](https://secure.gravatar.com/avatar/9489ebe21e231593130db8f6494ec78291a6c9dee89713b86d2001f54ee1698a?s=40&d=mm&r=g)

Hi Raj…The following resource is a great starting point for application of cost-sensitive learning:

<http://www.dabi.temple.edu/external/zoran/papers/shoumikecml2017.pdf>

![](https://secure.gravatar.com/avatar/23902a538df8e66b385ecfe35690e9629c921c52088f1f0f5fe0ac02d11ae11e?s=40&d=mm&r=g)

Hi Jason,

I’m working on an imbalanced regression problem (but with a continuous target domain) I use Density weight, I have a question, to measure the error in my test set, should I use the same estimated density of the training or recalculate the density for test set?

![](https://secure.gravatar.com/avatar/9489ebe21e231593130db8f6494ec78291a6c9dee89713b86d2001f54ee1698a?s=40&d=mm&r=g)

Hi Diana…The following resource may be of interest to you:

<https://link.springer.com/article/10.1007/s10994-021-06023-5>

### Leave a Reply [Click here to cancel reply.](/cost-sensitive-learning-for-imbalanced-classification/#respond)

Comment \*

Name (required)

Email (will not be published) (required)

Δ

![](https://secure.gravatar.com/avatar/f35a3fae3b273cf95005f8b005808f43039fd77f2440fdf889ddeb4e135e062d?s=88&d=mm&r=g)

**Welcome!**
I'm *Jason Brownlee* PhD
and I **help developers** get results with **machine learning**.
[Read more](/about)

#### Never miss a tutorial:

![LinkedIn](/wp-content/uploads/2019/12/small_icon_blue_linkedin3.png)
![Twitter](/wp-content/uploads/2019/12/small_icon_blue_twitter3.png)
![Facebook](/wp-content/uploads/2019/12/small_icon_blue_facebook3.png)
![Email Newsletter](/wp-content/uploads/2019/12/small_icon_blue_email3.png)
![RSS Feed](/wp-content/uploads/2019/12/small_icon_blue_rss3.png)

#### Picked for you:

![Scatter Plot of Imbalanced Dataset Transformed by SMOTE and Random Undersampling](https://machinelearningmastery.com/wp-content/uploads/2019/10/Scatter-Plot-of-Imbalanced-Dataset-Transformed-by-SMOTE-and-Random-Undersampling-150x150.png)
![A Gentle Introduction to Threshold-Moving for Imbalanced Classification](https://machinelearningmastery.com/wp-content/uploads/2020/02/A-Gentle-Introduction-to-Threshold-Moving-for-Imbalanced-Classification-150x150.jpg)
![Imbalanced Classification With Python (7-Day Mini-Course)](https://machinelearningmastery.com/wp-content/uploads/2020/01/Imbalanced-Classification-With-Python-7-Day-Mini-Course-150x150.jpg)
![How to Choose a Metric for Imbalanced Classification](https://machinelearningmastery.com/wp-content/uploads/2019/12/How-to-Choose-a-Metric-for-Imbalanced-Classification-latest-150x150.png)
![Scatter Plot of a Binary Classification Problem With a 1 to 1000 Class Imbalance](https://machinelearningmastery.com/wp-content/uploads/2019/11/Scatter-Plot-of-a-Binary-Classification-Problem-with-a-1-to-1000-Class-Imbalance-150x150.png)

#### Loving the Tutorials?

#### Loving the Tutorials?

The [Imbalanced Classification](/imbalanced-classification-with-python/) EBook is
where you'll find the ***Really Good*** stuff.

[>> See What's Inside](/imbalanced-classification-with-python/)

![](https://machinelearningmastery.com/wp-content/uploads/2014/11/machine_learning_mastery_logo.png)

Machine Learning Mastery is part of Guiding Tech Media, a leading digital media publisher focused on helping people figure out technology. [Visit our corporate website](https://www.guidingtechmedia.com) to learn more about our mission and team.

© 2026 Guiding Tech Media All Rights Reserved
