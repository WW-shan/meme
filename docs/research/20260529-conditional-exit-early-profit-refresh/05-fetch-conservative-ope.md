![[Uncertainty in Artificial Intelligence Logo]](/v216/assets/images/logo-pmlr.svg)
![RSS Feed](https://proceedings.mlr.press/v216/assets/images/RSS.gif)

[[edit](https://github.com/mlresearch/v216/edit/gh-pages/_posts/2023-07-02-rothfuss23a.md)]

# Hallucinated adversarial control for conservative offline policy evaluation

#### Abstract

#### Cite this Paper

`@InProceedings{pmlr-v216-rothfuss23a,
title = {Hallucinated adversarial control for conservative offline policy evaluation},
author = {Rothfuss, Jonas and Sukhija, Bhavya and Birchler, Tobias and Kassraie, Parnian and Krause, Andreas},
booktitle = {Proceedings of the Thirty-Ninth Conference on Uncertainty in Artificial Intelligence},
pages = {1774--1784},
year = {2023},
editor = {Evans, Robin J. and Shpitser, Ilya},
volume = {216},
series = {Proceedings of Machine Learning Research},
month = {31 Jul--04 Aug},
publisher = {PMLR},
pdf = {https://proceedings.mlr.press/v216/rothfuss23a/rothfuss23a.pdf},
url = {https://proceedings.mlr.press/v216/rothfuss23a.html},
abstract = {We study the problem of conservative off-policy evaluation (COPE) where given an offline dataset of environment interactions, collected by other agents, we seek to obtain a (tight) lower bound on a policy’s performance. This is crucial when deciding whether a given policy satisfies certain minimal performance/safety criteria before it can be deployed in the real world. To this end, we introduce HAMBO, which builds on an uncertainty-aware learned model of the transition dynamics. To form a conservative estimate of the policy’s performance, HAMBO hallucinates worst-case trajectories that the policy may take, within the margin of the models’ epistemic confidence regions. We prove that the resulting COPE estimates are valid lower bounds, and, under regularity conditions, show their convergence to the true expected return. Finally, we discuss scalable variants of our approach based on Bayesian Neural Networks and empirically demonstrate that they yield reliable and tight lower bounds in various continuous control environments.}
}`
`%0 Conference Paper
%T Hallucinated adversarial control for conservative offline policy evaluation
%A Jonas Rothfuss
%A Bhavya Sukhija
%A Tobias Birchler
%A Parnian Kassraie
%A Andreas Krause
%B Proceedings of the Thirty-Ninth Conference on Uncertainty in Artificial Intelligence
%C Proceedings of Machine Learning Research
%D 2023
%E Robin J. Evans
%E Ilya Shpitser
%F pmlr-v216-rothfuss23a
%I PMLR
%P 1774--1784
%U https://proceedings.mlr.press/v216/rothfuss23a.html
%V 216
%X We study the problem of conservative off-policy evaluation (COPE) where given an offline dataset of environment interactions, collected by other agents, we seek to obtain a (tight) lower bound on a policy’s performance. This is crucial when deciding whether a given policy satisfies certain minimal performance/safety criteria before it can be deployed in the real world. To this end, we introduce HAMBO, which builds on an uncertainty-aware learned model of the transition dynamics. To form a conservative estimate of the policy’s performance, HAMBO hallucinates worst-case trajectories that the policy may take, within the margin of the models’ epistemic confidence regions. We prove that the resulting COPE estimates are valid lower bounds, and, under regularity conditions, show their convergence to the true expected return. Finally, we discuss scalable variants of our approach based on Bayesian Neural Networks and empirically demonstrate that they yield reliable and tight lower bounds in various continuous control environments.`
`Rothfuss, J., Sukhija, B., Birchler, T., Kassraie, P. & Krause, A.. (2023). Hallucinated adversarial control for conservative offline policy evaluation. Proceedings of the Thirty-Ninth Conference on Uncertainty in Artificial Intelligence, in Proceedings of Machine Learning Research 216:1774-1784 Available from https://proceedings.mlr.press/v216/rothfuss23a.html.`

#### Related Material

This site last compiled Thu, 21 Aug 2025 05:44:21 +0000
