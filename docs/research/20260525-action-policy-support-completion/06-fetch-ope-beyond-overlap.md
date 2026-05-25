![[International Conference on Machine Learning Logo]](/v235/assets/images/logo-pmlr.svg)
![RSS Feed](https://proceedings.mlr.press/v235/assets/images/RSS.gif)

[[edit](https://github.com/mlresearch/v235/edit/gh-pages/_posts/2024-07-08-khan24b.md)]

# Off-policy Evaluation Beyond Overlap: Sharp Partial Identification Under Smoothness

#### Abstract

#### Cite this Paper

`@InProceedings{pmlr-v235-khan24b,
title = {Off-policy Evaluation Beyond Overlap: Sharp Partial Identification Under Smoothness},
author = {Khan, Samir and Saveski, Martin and Ugander, Johan},
booktitle = {Proceedings of the 41st International Conference on Machine Learning},
pages = {23734--23757},
year = {2024},
editor = {Salakhutdinov, Ruslan and Kolter, Zico and Heller, Katherine and Weller, Adrian and Oliver, Nuria and Scarlett, Jonathan and Berkenkamp, Felix},
volume = {235},
series = {Proceedings of Machine Learning Research},
month = {21--27 Jul},
publisher = {PMLR},
pdf = {https://raw.githubusercontent.com/mlresearch/v235/main/assets/khan24b/khan24b.pdf},
url = {https://proceedings.mlr.press/v235/khan24b.html},
abstract = {Off-policy evaluation, and the complementary problem of policy learning, use historical data collected under a logging policy to estimate and/or optimize the value of a target policy. Methods for these tasks typically assume overlap between the target and logging policy, enabling solutions based on importance weighting and/or imputation. Absent such an overlap assumption, existing work either relies on a well-specified model or optimizes needlessly conservative bounds. In this work, we develop methods for no-overlap policy evaluation without a well-specified model, relying instead on non-parametric assumptions on the expected outcome, with a particular focus on Lipschitz smoothness. Under such assumptions we are able to provide sharp bounds on the off-policy value, along with optimal estimators of those bounds. For Lipschitz smoothness, we construct a pair of linear programs that upper and lower bound the contribution of the no-overlap region to the off-policy value. We show that these programs have a concise closed form solution, and that their solutions converge under the Lipschitz assumption to the sharp partial identification bounds at a minimax optimal rate, up to log factors. We demonstrate the effectiveness our methods on two semi-synthetic examples, and obtain informative and valid bounds that are tighter than those possible without smoothness assumptions.}
}`
`%0 Conference Paper
%T Off-policy Evaluation Beyond Overlap: Sharp Partial Identification Under Smoothness
%A Samir Khan
%A Martin Saveski
%A Johan Ugander
%B Proceedings of the 41st International Conference on Machine Learning
%C Proceedings of Machine Learning Research
%D 2024
%E Ruslan Salakhutdinov
%E Zico Kolter
%E Katherine Heller
%E Adrian Weller
%E Nuria Oliver
%E Jonathan Scarlett
%E Felix Berkenkamp
%F pmlr-v235-khan24b
%I PMLR
%P 23734--23757
%U https://proceedings.mlr.press/v235/khan24b.html
%V 235
%X Off-policy evaluation, and the complementary problem of policy learning, use historical data collected under a logging policy to estimate and/or optimize the value of a target policy. Methods for these tasks typically assume overlap between the target and logging policy, enabling solutions based on importance weighting and/or imputation. Absent such an overlap assumption, existing work either relies on a well-specified model or optimizes needlessly conservative bounds. In this work, we develop methods for no-overlap policy evaluation without a well-specified model, relying instead on non-parametric assumptions on the expected outcome, with a particular focus on Lipschitz smoothness. Under such assumptions we are able to provide sharp bounds on the off-policy value, along with optimal estimators of those bounds. For Lipschitz smoothness, we construct a pair of linear programs that upper and lower bound the contribution of the no-overlap region to the off-policy value. We show that these programs have a concise closed form solution, and that their solutions converge under the Lipschitz assumption to the sharp partial identification bounds at a minimax optimal rate, up to log factors. We demonstrate the effectiveness our methods on two semi-synthetic examples, and obtain informative and valid bounds that are tighter than those possible without smoothness assumptions.`
`Khan, S., Saveski, M. & Ugander, J.. (2024). Off-policy Evaluation Beyond Overlap: Sharp Partial Identification Under Smoothness. Proceedings of the 41st International Conference on Machine Learning, in Proceedings of Machine Learning Research 235:23734-23757 Available from https://proceedings.mlr.press/v235/khan24b.html.`

#### Related Material

This site last compiled Wed, 09 Jul 2025 15:10:10 +0000
