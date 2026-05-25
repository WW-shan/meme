![Cornell University](https://static.arxiv.org/static/base/1.0.0a5/images/cornell-reduced-white-SMALL.svg)

We gratefully acknowledge support from
 the Simons Foundation, [member institutions](https://info.arxiv.org/about/ourmembers.html), and all contributors. [Donate](https://info.arxiv.org/about/donate.html)

![arxiv logo](https://static.arxiv.org/static/base/1.0.0a5/images/arxiv-logo-one-color-white.svg)

[Help](https://info.arxiv.org/help) | [Advanced Search](https://arxiv.org/search/advanced)

# Showing 1–5 of 5 results for all: "High Confidence Off-Policy Evaluation"

[arXiv:2510.07635](https://arxiv.org/abs/2510.07635)
 [[pdf](https://arxiv.org/pdf/2510.07635), [ps](https://arxiv.org/ps/2510.07635), [other](https://arxiv.org/format/2510.07635)] 

Safely Exploring Novel Actions in Recommender Systems via Deployment-Efficient Policy Learning

Authors:
[Haruka Kiyohara](/search/?searchtype=author&query=Kiyohara%2C+H),
[Yusuke Narita](/search/?searchtype=author&query=Narita%2C+Y),
[Yuta Saito](/search/?searchtype=author&query=Saito%2C+Y),
[Kei Tateno](/search/?searchtype=author&query=Tateno%2C+K),
[Takuma Udagawa](/search/?searchtype=author&query=Udagawa%2C+T)

Abstract:
…of novel actions with a guarantee for safety. To this end, we first develop Safe Off-Policy Policy Gradient (Safe OPG), which is a model-free safe OPL method based on a high…
▽ More

In many real recommender systems, novel items are added frequently over time. The importance of sufficiently presenting novel actions has widely been acknowledged for improving long-term user engagement. A recent work builds on Off-Policy Learning (OPL), which trains a policy from only logged data, however, the existing methods can be unsafe in the presence of novel actions. Our goal is to develop a framework to enforce exploration of novel actions with a guarantee for safety. To this end, we first develop Safe Off-Policy Policy Gradient (Safe OPG), which is a model-free safe OPL method based on a high confidence off-policy evaluation. In our first experiment, we observe that Safe OPG almost always satisfies a safety requirement, even when existing methods violate it greatly. However, the result also reveals that Safe OPG tends to be too conservative, suggesting a difficult tradeoff between guaranteeing safety and exploring novel actions. To overcome this tradeoff, we also propose a novel framework called Deployment-Efficient Policy Learning for Safe User Exploration, which leverages safety margin and gradually relaxes safety regularization during multiple (not many) deployments. Our framework thus enables exploration of novel actions while guaranteeing safe implementation of recommender systems.
△ Less

Submitted 8 October, 2025;
originally announced October 2025.

[arXiv:2309.13278](https://arxiv.org/abs/2309.13278)
 [[pdf](https://arxiv.org/pdf/2309.13278), [other](https://arxiv.org/format/2309.13278)] 

Distributional Shift-Aware Off-Policy Interval Estimation: A Unified Error Quantification Framework

Authors:
[Wenzhuo Zhou](/search/?searchtype=author&query=Zhou%2C+W),
[Yuhan Li](/search/?searchtype=author&query=Li%2C+Y),
[Ruoqing Zhu](/search/?searchtype=author&query=Zhu%2C+R),
[Annie Qu](/search/?searchtype=author&query=Qu%2C+A)

Abstract:
We study high-confidence off-policy evaluation in the context of infinite-horizon Markov decision processes, where the objective is to establish a confidence interval (CI) for the target policy value…
▽ More

We study high-confidence off-policy evaluation in the context of infinite-horizon Markov decision processes, where the objective is to establish a confidence interval (CI) for the target policy value using only offline data pre-collected from unknown behavior policies. This task faces two primary challenges: providing a comprehensive and rigorous error quantification in CI estimation, and addressing the distributional shift that results from discrepancies between the distribution induced by the target policy and the offline data-generating process. Motivated by an innovative unified error analysis, we jointly quantify the two sources of estimation errors: the misspecification error on modeling marginalized importance weights and the statistical uncertainty due to sampling, within a single interval. This unified framework reveals a previously hidden tradeoff between the errors, which undermines the tightness of the CI. Relying on a carefully designed discriminator function, the proposed estimator achieves a dual purpose: breaking the curse of the tradeoff to attain the tightest possible CI, and adapting the CI to ensure robustness against distributional shifts. Our method is applicable to time-dependent data without assuming any weak dependence conditions via leveraging a local supermartingale/martingale structure. Theoretically, we show that our algorithm is sample-efficient, error-robust, and provably convergent even in non-linear function approximation settings. The numerical performance of the proposed method is examined in synthetic datasets and an OhioT1DM mobile health study.
△ Less

Submitted 1 October, 2023; v1 submitted 23 September, 2023;
originally announced September 2023.

[arXiv:2212.08302](https://arxiv.org/abs/2212.08302)
 [[pdf](https://arxiv.org/pdf/2212.08302), [other](https://arxiv.org/format/2212.08302)] 

Safe Evaluation For Offline Learning: Are We Ready To Deploy?

Authors:
[Hager Radi](/search/?searchtype=author&query=Radi%2C+H),
[Josiah P. Hanna](/search/?searchtype=author&query=Hanna%2C+J+P),
[Peter Stone](/search/?searchtype=author&query=Stone%2C+P),
[Matthew E. Taylor](/search/?searchtype=author&query=Taylor%2C+M+E)

Abstract:
…deploying it and without the risk of overestimating its true performance. To achieve this, we introduce a framework for safe evaluation of offline learning using approximate high-…
▽ More

The world currently offers an abundance of data in multiple domains, from which we can learn reinforcement learning (RL) policies without further interaction with the environment. RL agents learning offline from such data is possible but deploying them while learning might be dangerous in domains where safety is critical. Therefore, it is essential to find a way to estimate how a newly-learned agent will perform if deployed in the target environment before actually deploying it and without the risk of overestimating its true performance. To achieve this, we introduce a framework for safe evaluation of offline learning using approximate high-confidence off-policy evaluation (HCOPE) to estimate the performance of offline policies during learning. In our setting, we assume a source of data, which we split into a train-set, to learn an offline policy, and a test-set, to estimate a lower-bound on the offline policy using off-policy evaluation with bootstrapping. A lower-bound estimate tells us how good a newly-learned target policy would perform before it is deployed in the real environment, and therefore allows us to decide when to deploy our learned policy.
△ Less

Submitted 16 December, 2022;
originally announced December 2022.

Comments:
NeurIPS 2021 Workshop on Deployable Decision Making in Embodied Systems [Spotlight]

[arXiv:2002.00467](https://arxiv.org/abs/2002.00467)
 [[pdf](https://arxiv.org/pdf/2002.00467), [other](https://arxiv.org/format/2002.00467)] 

Safe Exploration for Optimizing Contextual Bandits

Authors:
[Rolf Jagerman](/search/?searchtype=author&query=Jagerman%2C+R),
[Ilya Markov](/search/?searchtype=author&query=Markov%2C+I),
[Maarten de Rijke](/search/?searchtype=author&query=de+Rijke%2C+M)

Abstract:
…suboptimal performance and, thus, needs to be improved. Then SEA uses counterfactual learning to learn a new policy based on the behavior of the baseline policy. SEA also uses high-…
▽ More

Contextual bandit problems are a natural fit for many information retrieval tasks, such as learning to rank, text classification, recommendation, etc. However, existing learning methods for contextual bandit problems have one of two drawbacks: they either do not explore the space of all possible document rankings (i.e., actions) and, thus, may miss the optimal ranking, or they present suboptimal rankings to a user and, thus, may harm the user experience. We introduce a new learning method for contextual bandit problems, Safe Exploration Algorithm (SEA), which overcomes the above drawbacks. SEA starts by using a baseline (or production) ranking system (i.e., policy), which does not harm the user experience and, thus, is safe to execute, but has suboptimal performance and, thus, needs to be improved. Then SEA uses counterfactual learning to learn a new policy based on the behavior of the baseline policy. SEA also uses high-confidence off-policy evaluation to estimate the performance of the newly learned policy. Once the performance of the newly learned policy is at least as good as the performance of the baseline policy, SEA starts using the new policy to execute new actions, allowing it to actively explore favorable regions of the action space. This way, SEA never performs worse than the baseline policy and, thus, does not harm the user experience, while still exploring the action space and, thus, being able to find an optimal policy. Our experiments using text classification and document retrieval confirm the above by comparing SEA (and a boundless variant called BSEA) to online and offline learning methods for contextual bandit problems.
△ Less

Submitted 2 February, 2020;
originally announced February 2020.

Comments:
23 pages, 3 figures

[arXiv:1606.06126](https://arxiv.org/abs/1606.06126)
 [[pdf](https://arxiv.org/pdf/1606.06126), [other](https://arxiv.org/format/1606.06126)] 

Bootstrapping with Models: Confidence Intervals for Off-Policy Evaluation

Authors:
[Josiah P. Hanna](/search/?searchtype=author&query=Hanna%2C+J+P),
[Peter Stone](/search/?searchtype=author&query=Stone%2C+P),
[Scott Niekum](/search/?searchtype=author&query=Niekum%2C+S)

Abstract:
…For such agents, it is desirable to determine confidence interval lower bounds on the performance of any given policy without executing said policy. Current methods for exact high…
▽ More

For an autonomous agent, executing a poor policy may be costly or even dangerous. For such agents, it is desirable to determine confidence interval lower bounds on the performance of any given policy without executing said policy. Current methods for exact high confidence off-policy evaluation that use importance sampling require a substantial amount of data to achieve a tight lower bound. Existing model-based methods only address the problem in discrete state spaces. Since exact bounds are intractable for many domains we trade off strict guarantees of safety for more data-efficient approximate bounds. In this context, we propose two bootstrapping off-policy evaluation methods which use learned MDP transition models in order to estimate lower confidence bounds on policy performance with limited data in both continuous and discrete state spaces. Since direct use of a model may introduce bias, we derive a theoretical upper bound on model bias for when the model transition function is estimated with i.i.d. trajectories. This bound broadens our understanding of the conditions under which model-based methods have high bias. Finally, we empirically evaluate our proposed methods and analyze the settings in which different bootstrapping off-policy confidence interval methods succeed and fail.
△ Less

Submitted 24 September, 2018; v1 submitted 20 June, 2016;
originally announced June 2016.

Comments:
Published in proceedings of the 16th International Conference on Autonomous Agents and Multi-agent Systems

[arXiv Operational Status](https://status.arxiv.org)
Get status notifications via
[email](https://subscribe.sorryapp.com/24846f03/email/new)
or [slack](https://subscribe.sorryapp.com/24846f03/slack/new)
