![[Uncertainty in Artificial Intelligence Logo]](/v180/assets/images/logo-pmlr.svg)
![RSS Feed](https://proceedings.mlr.press/v180/assets/images/RSS.gif)

[[edit](https://github.com/mlresearch/v180/edit/gh-pages/_posts/2022-08-17-liu22d.md)]

# Offline policy optimization with eligible actions

#### Abstract

#### Cite this Paper

`@InProceedings{pmlr-v180-liu22d,
title = {Offline policy optimization with eligible actions},
author = {Liu, Yao and Flet-Berliac, Yannis and Brunskill, Emma},
booktitle = {Proceedings of the Thirty-Eighth Conference on Uncertainty in Artificial Intelligence},
pages = {1253--1263},
year = {2022},
editor = {Cussens, James and Zhang, Kun},
volume = {180},
series = {Proceedings of Machine Learning Research},
month = {01--05 Aug},
publisher = {PMLR},
pdf = {https://proceedings.mlr.press/v180/liu22d/liu22d.pdf},
url = {https://proceedings.mlr.press/v180/liu22d.html},
abstract = {Offline policy optimization could have a large impact on many real-world decision-making problems, as online learning may be infeasible in many applications. Importance sampling and its variants are a common used type of estimator in offline policy evaluation, and such estimators typically do not require assumptions on the properties and representational capabilities of value function or decision process model function classes. In this paper, we identify an important overfitting phenomenon in optimizing the importance weighted return, in which it may be possible for the learned policy to essentially avoid making aligned decisions for part of the initial state space. We propose an algorithm to avoid this overfitting through a new per-state-neighborhood normalization constraint, and provide a theoretical justification of the proposed algorithm. We also show the limitations of previous attempts to this approach. We test our algorithm in a healthcare-inspired simulator, a logged dataset collected from real hospitals and continuous control tasks. These experiments show the proposed method yields less overfitting and better test performance compared to state-of-the-art batch reinforcement learning algorithms.}
}`
`%0 Conference Paper
%T Offline policy optimization with eligible actions
%A Yao Liu
%A Yannis Flet-Berliac
%A Emma Brunskill
%B Proceedings of the Thirty-Eighth Conference on Uncertainty in Artificial Intelligence
%C Proceedings of Machine Learning Research
%D 2022
%E James Cussens
%E Kun Zhang
%F pmlr-v180-liu22d
%I PMLR
%P 1253--1263
%U https://proceedings.mlr.press/v180/liu22d.html
%V 180
%X Offline policy optimization could have a large impact on many real-world decision-making problems, as online learning may be infeasible in many applications. Importance sampling and its variants are a common used type of estimator in offline policy evaluation, and such estimators typically do not require assumptions on the properties and representational capabilities of value function or decision process model function classes. In this paper, we identify an important overfitting phenomenon in optimizing the importance weighted return, in which it may be possible for the learned policy to essentially avoid making aligned decisions for part of the initial state space. We propose an algorithm to avoid this overfitting through a new per-state-neighborhood normalization constraint, and provide a theoretical justification of the proposed algorithm. We also show the limitations of previous attempts to this approach. We test our algorithm in a healthcare-inspired simulator, a logged dataset collected from real hospitals and continuous control tasks. These experiments show the proposed method yields less overfitting and better test performance compared to state-of-the-art batch reinforcement learning algorithms.`
`Liu, Y., Flet-Berliac, Y. & Brunskill, E.. (2022). Offline policy optimization with eligible actions. Proceedings of the Thirty-Eighth Conference on Uncertainty in Artificial Intelligence, in Proceedings of Machine Learning Research 180:1253-1263 Available from https://proceedings.mlr.press/v180/liu22d.html.`

#### Related Material

This site last compiled Wed, 08 Feb 2023 10:38:37 +0000
