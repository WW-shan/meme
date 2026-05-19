[![NannyML Blog](https://imagedelivery.net/gLgcD68SxSCB7eEUDDEJXQ/80c96c1b294735fc2fd66882838b30ac_8470d039-f086-4057-4bf2-1b95fed06200/square)](https://nannyml.com/)

[Docs](https://docs.nannyml.com/cloud)[Blog](/blog/all)[Pricing](https://www.nannyml.com/pricing)[About](https://www.nannyml.com/about)[Contact](https://www.nannyml.com/contact-us)

[GitHub 🌟](https://github.com/NannyML/nannyml)

Open main menu

[Docs](https://docs.nannyml.com/cloud)[Blog](/blog/all)[Pricing](https://www.nannyml.com/pricing)[About](https://www.nannyml.com/about)[Contact](https://www.nannyml.com/contact-us)

[GitHub 🌟](https://github.com/NannyML/nannyml)



# Bad Machine Learning models can still be well-calibrated

You don’t need a perfect oracle to get your probabilities right.

[Data Science](/blog/tags/ai-data-science)

•

[![ Michal Oleszak](https://api-prod.usenotioncms.com/v1/proxy-2/block/d6b6fac9-46f8-420d-91ff-0aed1fa97e9c%2F5fa8f37b-3cc4-467f-b803-bbd304828677%2F63f5e555b6a4b3d5503c7fe8_michal-p-500.jpeg)](/blog/authors/michal-oleszak) [Michal Oleszak](/blog/authors/michal-oleszak)

ML Engineer & Data Science Instructor | Top Writer in AI & Statistics

Table of Contents

* [What is Probability Calibration?](/blog/probability-calibration#what-is-probability-calibration)
* [Do you even need calibration?](/blog/probability-calibration#do-you-even-need-calibration)
* [Calibration is everything](/blog/probability-calibration#calibration-is-everything)
* [Credit Line Assignment](/blog/probability-calibration#credit-line-assignment)
* [Model Performance Estimation](/blog/probability-calibration#model-performance-estimation)
* [We don’t need calibration](/blog/probability-calibration#we-don-t-need-calibration)
* [Ranking Problems](/blog/probability-calibration#ranking-problems)
* [A story of a poor, well-calibrated model](/blog/probability-calibration#a-story-of-a-poor-well-calibrated-model)
* [When it’s hard to get a good performance](/blog/probability-calibration#when-it-s-hard-to-get-a-good-performance)
* [When it’s impossible to get a good performance](/blog/probability-calibration#when-it-s-impossible-to-get-a-good-performance)
* [Takeaways](/blog/probability-calibration#takeaways)

Table of Contents

* [What is Probability Calibration?](/blog/probability-calibration#what-is-probability-calibration)
* [Do you even need calibration?](/blog/probability-calibration#do-you-even-need-calibration)
* [Calibration is everything](/blog/probability-calibration#calibration-is-everything)
* [Credit Line Assignment](/blog/probability-calibration#credit-line-assignment)
* [Model Performance Estimation](/blog/probability-calibration#model-performance-estimation)
* [We don’t need calibration](/blog/probability-calibration#we-don-t-need-calibration)
* [Ranking Problems](/blog/probability-calibration#ranking-problems)
* [A story of a poor, well-calibrated model](/blog/probability-calibration#a-story-of-a-poor-well-calibrated-model)
* [When it’s hard to get a good performance](/blog/probability-calibration#when-it-s-hard-to-get-a-good-performance)
* [When it’s impossible to get a good performance](/blog/probability-calibration#when-it-s-impossible-to-get-a-good-performance)
* [Takeaways](/blog/probability-calibration#takeaways)

* [Twitter](https://twitter.com/share?url=https://www.nannyml.com/blog/probability-calibration&text=Bad%20Machine%20Learning%20models%20can%20still%20be%20well-calibrated)
* [Facebook](https://www.facebook.com/sharer/sharer.php?u=https://www.nannyml.com/blog/probability-calibration)
* [LinkedIn](https://www.linkedin.com/share?url=https://www.nannyml.com/blog/probability-calibration)

![Bad Machine Learning models can still be well-calibrated](https://api-prod.usenotioncms.com/v1/proxy-2/block/b5c73b1f-c259-4179-b8f3-6ba762e05926%2F4e52ff98-6582-4e7e-b6ae-882a1da6aeb7%2F63e7c888037f3b12bdbe9a45_michal.png)

Do not index

Canonical URL

Machine learning models are often evaluated based on their performance, measured by how close some metric is to zero or one (depending on the metric), but this is not the only factor that determines their usefulness. In some cases, a model that is not very accurate overall can still be well-calibrated and find a useful application. In this article, we will explore the difference between good calibration and good performance and when one might be preferred over the other. Let’s dive in!

## What is Probability Calibration?

Probability calibration, in its strong definition, is the degree to which the probabilities predicted by a classification model match the true frequencies of the target classes in a dataset. A [well-calibrated model](https://medium.com/towards-data-science/calibrating-classifiers-559abc30711a) produces predictions that are, on aggregate, closely aligned with the actual outcomes.

What this means in practice is that if we make a lot of predictions with a perfectly calibrated binary classification model, and then consider only those for which the model predicted a 70% probability of the positive class, then the model should be correct 70% of the time. Similarly, if we only consider the examples for which our model predicted a 10% probability of the positive class, the ground truth will turn out to indeed be positive in one-tenth of the cases.

A well-calibrated model produces predictions that are closely aligned with the actual outcomes on aggregate.

A model with strong calibration guarantees that its predictions satisfy the frequentist definition of probability ([as opposed to the Bayesian one](https://towardsdatascience.com/the-gentlest-of-introductions-to-bayesian-data-analysis-74df448da25)), which states that *an event’s probability is the limit of its relative frequency in many trials.*

Why is the probability of rolling a six with a dice 1/6? Because if you rolled it 6 000 000 times, you’d get approximately 1 000 000 sixes. And if you rolled it infinitely many times, then exactly 1/6 rolls will come up six. In this context, what does it *mean*when a binary classification model outputs a probability of 90% for an event? It means that if it does this many times, in approximately 9 out of 10 cases, the event will indeed occur.

Most machine learning models are ill-calibrated, and the reasons depend on the learning algorithm. Tree-based ensembles such as random forests generate their predictions by averaging individual trees, which makes it unlikely to obtain probabilities near zero and one since there is always some variance in the trees’ predictions. As a result, we see probabilistic overestimates near zero and underestimates near one. Many other models optimize for and are scored by binary metrics. Accuracy only looks at whether we are right or wrong, disregarding certainty. Gini-impurity used by decision trees to decide on splits optimizes for being as accurate as possible as quickly as possible.

The consequence of this is that while the scores produced by most machine learning models preserve order (the higher the number, the more likely the positive class), they cannot be interpreted as frequentist probabilities.

[There are simple methods to calibrate them](https://medium.com/towards-data-science/calibrating-classifiers-559abc30711a), and good calibration is undoubtedly a desired trait for a model to feature, but as we will soon see, it is not a required condition for the model to be useful, and sometimes we might even want the model not to be calibrated!

## Do you even need calibration?

When training a classification model, you need to ask yourself a crucial question: do you actually *need* the model to be well-calibrated? The answer will depend on how the model will be used. Let’s take a look at some examples.

### Calibration is everything

#### Credit Line Assignment

In some scenarios, good calibration is indispensable. Think about a bank deciding how much credit to grant a customer. Let’s assume here that we are only considering loan applicants who have already been screened and assessed as low-risk and eligible for a loan (we will talk more about this screening process in a second). It is decided that the loans will be granted to them. The question is, how much money can we lend each of them?

To answer it, the bank would need to know the exact probability of default for each customer, for different loan amounts. Knowing how likely different scenarios are, the bank will be able to predict the monetary impact from all loans, both paid back and defaulted and make the optimal decision. To achieve their goal, they need a very well-calibrated model.

Notice how we don’t really care about the model’s accuracy *per se*. Accuracy is all about being on the correct side of the prediction threshold; from its point of view, there is no difference between predicting 51% and 99% as long as the loan defaults; the prediction is just as correct in both cases. But for the bank, and for the loan applicant themselves, this is a huge difference. Getting the probability right is what’s important here.

#### Model Performance Estimation

Sometimes, good model calibration is a prerequisite for a given application. Think about estimating the model’s performance in production without knowing the ground truth targets. One approach to solve this challenging task for classification models is NannyML’s [Confidence-Based Performance Estimation (CBPE) algorithm](https://medium.com/towards-artificial-intelligence/estimating-model-performance-without-ground-truth-453b850dad9a). In a nutshell, the idea behind this approach is to estimate the elements of the confusion matrix based on the expected error rates, which we know, assuming the model is well-calibrated.

So, if we want to monitor the model’s performance in production and we don’t immediately have ground truth targets, we need our model to be calibrated. And yet again, the model does not need to be of great accuracy. As long as its predictions are well-calibrated, it is good to go.

### We don’t need calibration

#### Ranking Problems

There are situations, however, in which the model’s calibration does not really matter much. These include all sorts of ranking problems, for instance.

Think about models that rank news article titles in terms of quality or relevance to the user’s search query. If the goal is to select one or more articles to show the user, we don’t really care about the exact probability that each of them is high-quality and relevant; rather, we care about the order of scores produced by the model. That is, we want to be sure that what we show the user is better than what we don’t show, and that the best news sit on top of the results list. In this setting, calibrating the model does not make much sense.

> Depending on how the model will be used, good calibration may be either indispensable or rather unnecessary.

Let’s now take a look at some models that are poor in terms of performance, but their good calibration renders them very useful for their intended purposes.

## A story of a poor, well-calibrated model

Let’s consider two different models. First, we will look at one where good performance is hard to get, but good calibration ensures the model provides value. Second, we will consider a model theoretically incapable of good performance, but well-calibrated and thus useful.

### When it’s hard to get a good performance

Some time ago, I was been training models to predict the results of football (a.k.a. soccer) matches with the goal of getting rich quickly and effortlessly by betting at a bookie. Predicting a match result accurately is an impossible task — there are too many hidden factors involved, such as luck and the players’ disposition of the day. But guess what, getting accurate predictions is not what we need! Just like in the credit line assignment and performance estimation examples, here too, the game is all about getting the probabilities right.

Consider this binary random forest classifier trained to predict whether the home team will win the game. It was trained on a couple of seasons of the English Premier League matches, and the feature set included the [ELO ratings](https://en.wikipedia.org/wiki/Elo_rating_system) of both teams as well as many different statistics summing up how good each team was in the recent games with respect to attack and defense.

The model’s test accuracy was 63%. This is certainly better than a dummy model, which always predicts the home team to win; such a model would score 46% as the hosts tend to win almost half of the games. That said, 63% does not seem to be a great result.

Let’s take a look at the model’s calibration plot. The horizontal axis shows the probabilities produced by the model for the test set, binned into 10 equal-width bins. For each, the actual frequency of home wins is shown on the vertical axis. A perfectly calibrated model would produce a straight diagonal line.

Football predictor’s calibration curves.

![Image by the author.](https://www.notion.so/image/https:%2F%2Fassets.website-files.com%2F6099466f98d9383d91745b9e%2F63e7cbeb5b939f263d8c6860_michale2.png%3FspaceId=35376f8c-46c5-49d2-914f-cd4491e5ac90?table=block&id=ec8c81b0-fb53-4401-a7ae-6cde3451441c&cache=v2)

Image by the author.

The original model, shown in blue, is very poorly calibrated at more extreme probabilities: a prediction of 90% has only a 30% chance of being correct! Hence, I decided to calibrate it using one of the most popular techniques: [fitting a logistic regressor on top of the model’s outputs](https://towardsdatascience.com/calibrating-classifiers-559abc30711a).

The resulting model, shown in green, seems to be much better calibrated. You will surely notice, too, that it does not produce extreme probabilities anymore. As far as accuracy is concerned, it dropped by one percentage point, to 62%. So, we managed to improve the model’s calibration at the cost of accuracy. How is this useful?

Consider the following strategy: we will only bet on matches in which the model is the most certain that the home team will win, so the ones for which it produces a prediction of 70%. Thanks to reasonably good calibration, we know the model will be correct in 70% of such cases. For simplicity, assume we are betting $100 on each game separately.

Out of 100 games, we will miss 30, which will yield us a loss of $3000. But we will win the remaining 70 bets, and the cash prize will be (we subtract 1 to take into account that we need to spend $7000 on the coupons in the first place). We can solve this equation to find such bookie’s odds for which we break even:

There we go! We can bet on all matches for which the model produces a 70% prediction and for which the bookie offers odds higher than 1.42 (disregarding the tax). We can, of course, compute the odds for other predicted probabilities in a similar fashion. Assuming the model’s calibration will stay good in the future (and this is a strong assumption!), this strategy should yield quite profitable in the long run. And all that despite the poor 62% accuracy!

### When it’s impossible to get a good performance

Now consider an attempt to predict dice rolls. Our model should produce a probability of the die facing up to six after it has been rolled. We assume that the die is just a regular, board game-type, six-sided, fair die.

Rolling such a die is a completely stochastic process, and the chance of each side facing up is the same: ⅙. In other words, the data classes are completely inseparable: it is not feasible to build an accurate model. What model can we have then?

Consider these two competing approaches. Model A is a dummy binary classifier that always predicts with full confidence that the rolled number is not a six;  that is, it predicts a six 0% of the time and a not-six 100% of the time. Model B also never predicts a six, but the probabilities it outputs are different: it always predicts a six with the probability of  ⅙ and a not-six with the probability of  ⅚.

In the long run, both models feature the same accuracy: they are correct 5 out of 6 times. And this is as good as any model can get. However, an important fact differentiates between the two models: model B is perfectly calibrated while Model A is not calibrated at all.

As far as calibration is concerned, the two models couldn’t be more different. How about the usefulness of the two models? Model A doesn’t really deliver any value. Model B, on the other hand, allows us to accurately predict the target frequency in the long run. It also allows us to run simulations to answer more complex questions such as: what is the probability of rolling four not-six and seven sixes in 11 rolls? Once again, despite the poor predictive performance, good calibration yields the model useful!

## Takeaways

Well-calibrated models produce predictions that are closely aligned with the frequency of the actual outcomes on aggregate. Most models are ill-calibrated because of the way they learn, but there are simple methods to fix this. For some applications, like assigning credit lines or CBPE estimation, good calibration is essential (in fact, more important than the performance metrics themselves). For others, such as granting loans or ranking problems, not very much so; here, correct rank ordering and performance are what matters. Inaccurate models can be pretty useful provided they are well-calibrated; sometimes, getting the probabilities right is all we can do.

Share this post

* [Twitter](https://twitter.com/share?url=https://www.nannyml.com/blog/probability-calibration&text=Bad%20Machine%20Learning%20models%20can%20still%20be%20well-calibrated)
* [Facebook](https://www.facebook.com/sharer/sharer.php?u=https://www.nannyml.com/blog/probability-calibration)
* [LinkedIn](https://www.linkedin.com/share?url=https://www.nannyml.com/blog/probability-calibration)

Ready to learn how well are your ML models working?

### Join other 1100+ data scientists now!

[Subscribe](/blog/probability-calibration#newsletter-in-footer-wrapper)

Written by

[![ Michal Oleszak](https://api-prod.usenotioncms.com/v1/proxy-2/block/d6b6fac9-46f8-420d-91ff-0aed1fa97e9c%2F5fa8f37b-3cc4-467f-b803-bbd304828677%2F63f5e555b6a4b3d5503c7fe8_michal-p-500.jpeg)](/blog/authors/michal-oleszak)

[Michal Oleszak](/blog/authors/michal-oleszak)

ML Engineer & Data Science Instructor | Top Writer in AI & Statistics

* [LinkedIn](https://www.linkedin.com/in/michal-oleszak/)

Ready to learn how well are your ML models working?

### Join other 1100+ data scientists now!

No spam. Unsubscribe at any time.
