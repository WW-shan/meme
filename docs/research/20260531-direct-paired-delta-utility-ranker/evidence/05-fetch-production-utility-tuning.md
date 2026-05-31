##### Report GitHub Issue

Content selection saved. Describe the issue below:

![arXiv logo](/static/browse/0.3.4/images/arxiv-logo-one-color-white.svg)

# A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems

###### Abstract.

Large-scale recommenders encode multi-objective trade-offs by combining multiple predicted outcomes into a single utility score. Although this utility layer can be updated independently of the ranker, weight tuning remains largely manual, globally applied, slow to adapt to changing environments and business needs, and hard to govern as priorities shift. We propose PRL-PUTS, a Production-ready, ranker independent RL framework for Personalized Utility-weight Tuning with Pareto Sweeping.
We cast utility tuning as a one-step, value-based RL problem: given request context, an agent selects a utility-weight vector that re-weights ranker predictions to maximize request-level engagement rewards.
To visualize performance across the trade-off spectrum and allow decision makers to update the deployed operating policy instantly, we adopt an inference-time Pareto frontier sweeping via a scalarization parameter, producing a family of policies and an empirical Pareto frontier used as a governance artifact for operating policy selection. PRL-PUTS runs in parallel with ranking inference without adding serving latency. We validate PRL-PUTS with offline analysis using unbiased exploration logs and online experiments on Pinterest Homefeed where PRL-PUTS showed significant increases in engagement compared to baseline such as +0.13% increase in successful session, a core metric for user engagement.

## 1. Introduction

Large-scale recommender systems predict multiple objectives simultaneously (e.g., clicks, saves) (Jannach and Abdollahpouri, [2023](#bib.bib51 "A survey on multi-objective recommender systems"); Zhao et al., [2019b](#bib.bib47 "Recommending what video to watch next: a multitask ranking system")), and a downstream *utility layer* aggregates the per-objective predictions into a single score used for ranking. A common implementation is a linear utility: a weighted sum of the predicted outcomes, where the weights encode the desired balance among business goals. This design is attractive because the utility layer is simple, debuggable, and can be updated without retraining the ranker. In practice, this makes the utility layer the primary control surface for responding quickly to shifting priorities, while keeping ranker retraining on a different cycle.

However, the same simplicity creates persistent operational and product debt. Operationally, utility weights are typically selected through ad hoc offline analyses and repeated online experiments, after which decision makers choose among competing metric movements without clear visibility into the set of feasible trade-offs. This process is slow (often taking weeks to months from ideation to launch), hard to reproduce, and difficult to revisit as the environment or priorities change. Technically, the ranker itself is frequently refreshed (e.g. data, features, and calibration), while global utility weights are often treated as long-lived constants; as a result, weights tuned on an earlier distribution can become stale relative to the current ranker and traffic. From a product perspective, global weights are fundamentally non-personalized: they impose the same objective trade-off across heterogeneous user intents and contexts, not because this is optimal, but because manually enumerating and validating context-dependent trade-offs is intractable at production scale.

This paper asks a practical question: *how can we make multi-objective trade-offs fast to update, context-sensitive, and governable while respecting production constraints that limit model retraining frequency and serving-time complexity?* We propose PRL-PUTS, a Production-ready ranker-independent RL framework for Personalized Utiliy-weight Tuning with Pareto Sweeping. PRL-PUTS selects a *utility-weight vector* per request and applies it to the ranker’s existing predictions. We cast this as a one-step, value-based RL problem: given request context, the agent chooses weights to maximize request-level engagement rewards. By restricting actions to utility weights, PRL-PUTS provides a small, reviewable control surface that supports fast operating-policy changes and safe rollback, allowing the ranker and control layer to iterate on different cadences.

Beyond learning a single policy, real world deployments require *governance*: stakeholders must be able to select among achievable trade-offs and update the operating policy as priorities shift (Chen et al., [2023](#bib.bib52 "Controllable multi-objective re-ranking with policy hypernetworks")). We therefore adopt *inference-time Pareto frontier sweeping* (Roijers et al., [2013](#bib.bib55 "A survey of multi-objective sequential decision-making"); Hayes et al., [2021](#bib.bib56 "A practical guide to multi-objective reinforcement learning and planning"); Mossalam et al., [2016](#bib.bib57 "Multi-objective deep reinforcement learning")). PRL-PUTS learns objective-specific value functions for the tasks of interest and exposes a scalarization hyperparameter α\alpha at inference time to control their relative importance. Sweeping α\alpha offline induces a family of policies from the same trained model and yields an empirical Pareto frontier that stakeholders can use to choose an operating policy aligned with current business priorities.

We integrate the proposed control layer into Pinterest Homefeed, where it adjusts only the utility aggregation step and adds no serving latency. We evaluate it offline using unbiased exploration logs from randomized production traffic (Bottou et al., [2013](#bib.bib45 "Counterfactual reasoning and learning systems: the example of computational advertising"); Zhao et al., [2019a](#bib.bib21 "” Deep reinforcement learning for search, recommendation, and online advertising: a survey” by xiangyu zhao, long xia, jiliang tang, and dawei yin with martin vesely as coordinator")) and validate it with online experiments. We quantify trade-offs between Repin (saves) and P2P impressions (impressions under related-Pin context) while tracking Successful Sessions, and show strong offline-to-online agreement, with gains attributable to contextual (request-dependent) weight selection rather than a single shifted global weight vector.

This work makes the following contributions:

Ranker-independent, one-step RL formulation: We cast utility-weight selection as a one-step, value-based RL problem whose actions are utility-weight vectors applied to ranker predictions, enabling request-time contextual control.

Actionable multi-objective governance via Pareto sweeping: We adopt inference-time sweeping with a scalarization hyperparameter α\alpha to induce a family of policies from a single trained model and construct an empirical Pareto frontier for deployment-time operating policy selection.

Production integration and deployment: We present a design that runs alongside ranking inference, adds no serving latency, and is deployed in production on Pinterest Homefeed.

End-to-end evidence: We show that offline Pareto-swept trade-off estimates reliably predict online metric movements, with gains driven by weight personalization rather than shifts in global weights.

## 2. Related Work

Utility Weights in Production Ranking.
Production recommender systems typically aggregate multiple engagement predictions into a single ranking score using a linear utility function with manually tuned weights  (Zhao et al., [2019b](#bib.bib47 "Recommending what video to watch next: a multitask ranking system"); Milli et al., [2023](#bib.bib48 "Choosing the right weights: balancing value, strategy, and noise in recommender systems")).
In practice, these weights are iterated through offline analysis and A/B tests and then deployed as a largely global, static configuration, which can misspecify trade-offs across heterogeneous users and request contexts (Jeunen et al., [2024](#bib.bib50 "Multi-objective recommendation via multivariate policy learning"); Jannach and Abdollahpouri, [2023](#bib.bib51 "A survey on multi-objective recommender systems"); Chen et al., [2023](#bib.bib52 "Controllable multi-objective re-ranking with policy hypernetworks")). Recent work argues that fixed scalarization enforces a one-size-fits-all trade-off and explores learning context-dependent preferences/dynamic weighting (Yang et al., [2025](#bib.bib49 "Deep reinforcement learning for ranking utility tuning in the ad recommender system at pinterest"); Jeunen et al., [2024](#bib.bib50 "Multi-objective recommendation via multivariate policy learning"); Wanigasekara et al., [2019](#bib.bib53 "Learning multi-objective rewards and user utility function in contextual bandits for personalized ranking."); Cunha and Marchini, [2024](#bib.bib54 "A hybrid meta-learning and multi-armed bandit approach for context-specific multi-objective recommendation optimization")). Most closely related, Yang et al. ([2025](#bib.bib49 "Deep reinforcement learning for ranking utility tuning in the ad recommender system at pinterest")) learns a *policy-based* RL controller that selects utility weights for ranking utility tuning in Pinterest ads, illustrating the promise of contextual weight control; in contrast, we use a *value-based* formulation that supports inference-time Pareto sweeping from a single trained model and yields an empirical Pareto frontier for stakeholder-governed operating policy selection.

RL for Recommender Systems: End-to-end Ranking vs. Control-layer RL.
RL has been studied extensively for recommendation and ranking, particularly for sequential/session objectives and large decision spaces. Representative examples include RL-to-rank for e-commerce search sessions  (Hu et al., [2018](#bib.bib26 "Reinforcement learning to rank in e-commerce search engine: formalization, analysis, and application")), page-wise and whole-chain recommendation formulations  (Zhao et al., [2018b](#bib.bib22 "Deep reinforcement learning for page-wise recommendations"), [2020](#bib.bib25 "Whole-chain recommendations")), hierarchical RL for integrated recommendation  (Xie et al., [2021](#bib.bib19 "Hierarchical reinforcement learning for integrated recommendation")), and web-scale in-session optimization frameworks  (Ayed et al., [2025](#bib.bib16 "RecoMind: a reinforcement learning framework for optimizing in-session user satisfaction in recommendation systems")). Across these lines of work, RL is typically embedded in the core recommendation decision (e.g., selecting items/slates or optimizing multi-step trajectories), which often couples the policy tightly to candidate generation, ranking models, and the broader serving pipeline (Ge et al., [2022](#bib.bib64 "Toward pareto efficient fairness-utility trade-off in recommendation through reinforcement learning")). In contrast, our RL agent operates as a production-friendly control layer: the action is a utility weight vector applied to existing per-objective predictions, rather than replacing the ranker or choosing items directly. This design reduces coupling with ranking model iteration and better matches stringent serving constraints in web-scale systems, since the policy can be evaluated at request time independently of item-level scoring (consistent with real-time infrastructure considerations discussed in systems work such as  (Liu et al., [2022](#bib.bib37 "Monolith: real time recommendation system with collisionless embedding table"))).

Multi-objective Control and Pareto-style Operating-policy Selection.
Multi-objective optimization is inherent in production recommenders, where stakeholders frequently need to trade off competing engagement goals. RL foundations and practical RL surveys emphasize that preference specifications and reward design strongly shape learned behavior, and that changing preferences can be operationally costly if it requires retraining  (Roijers et al., [2013](#bib.bib55 "A survey of multi-objective sequential decision-making"); Sutton, [2018](#bib.bib6 "Reinforcement learning: an introduction"); Zhao et al., [2019a](#bib.bib21 "” Deep reinforcement learning for search, recommendation, and online advertising: a survey” by xiangyu zhao, long xia, jiliang tang, and dawei yin with martin vesely as coordinator")). We focus on enabling post hoc trade-off selection: we learn objective-specific value estimates and then expose a family of trade-off policies at inference time by sweeping a preference parameter, constructing an empirical frontier from which stakeholders can choose an operating policy (Roijers et al., [2013](#bib.bib55 "A survey of multi-objective sequential decision-making"); Hayes et al., [2021](#bib.bib56 "A practical guide to multi-objective reinforcement learning and planning"); Mossalam et al., [2016](#bib.bib57 "Multi-objective deep reinforcement learning")).

Production Learning Loop: Exploration Logging and Offline Evaluation.
A core challenge in production control is that the “correct” action (here, utility weights) is unlabeled; outcomes are only observed under the deployed action, motivating careful exploration and evaluation from logged data. Counterfactual learning provides a standard framing for this setting  (Bottou et al., [2013](#bib.bib45 "Counterfactual reasoning and learning systems: the example of computational advertising")), and off-policy RL emphasizes learning/evaluating from data generated by a different behavior policy  (Degris et al., [2012](#bib.bib8 "Off-policy actor-critic")). In our setup, we collect logs via constrained randomized exploration over a discrete set of utility-weight actions, and screen policies offline using Reward@HIT, an action-matching (rejection-style) estimator that evaluates only requests where the policy action matches the logged action (Li et al., [2011](#bib.bib58 "Unbiased offline evaluation of contextual-bandit-based news article recommendation algorithms"), [2012](#bib.bib59 "An unbiased offline evaluation of contextual bandit algorithms with generalized linear models"); Dudík et al., [2012](#bib.bib60 "Sample-efficient nonstationary policy evaluation for contextual bandits")). Industrial RL for ads/allocation provides precedents for constrained exploration and learning from interaction feedback (e.g., bidding/exposure control  (Cai et al., [2017](#bib.bib1 "Real-time bidding by reinforcement learning in display advertising"); Jin et al., [2018](#bib.bib15 "Real-time bidding with multi-agent reinforcement learning in display advertising"); Wu et al., [2018](#bib.bib2 "Budget constrained bidding by model-free reinforcement learning in display advertising"); Zhao et al., [2018a](#bib.bib27 "Deep reinforcement learning for sponsored search real-time bidding")) and pacing/exposure approaches  (Wang et al., [2019](#bib.bib18 "Learning adaptive display exposure for real-time advertising"); Wei et al., [2023](#bib.bib4 "RLTP: reinforcement learning to pace for delayed impression modeling in preloaded ads"); Zhao et al., [2021](#bib.bib3 "Dear: deep reinforcement learning for online advertising impression in recommender systems"))), reinforcing the same production pattern: limited exploration, offline screening, online A/B confirmation (Garcıa and Fernández, [2015](#bib.bib61 "A comprehensive survey on safe reinforcement learning"); Brunke et al., [2022](#bib.bib62 "Safe learning in robotics: from learning-based control to safe reinforcement learning"); Wachi et al., [2024](#bib.bib63 "A survey of constraint formulations in safe reinforcement learning")).

## 3. Problem Formulation

In this section, we formalize ranker-independent utility-weight tuning as a one-step, multi-objective decision problem at the request level. We first define the multi-task ranker and the utility aggregation used for ranking, then specify the one-step RL tuple (s,a,r)(s,a,r) together with the state, action, and reward definitions.

### 3.1. Utility Tuning for Ranking

Modern recommender systems commonly use multi-task ranking models that estimate the likelihood of different user engagement outcomes (e.g., clicks, saves). At serving time, these per-objective predictions are aggregated into a single utility score, typically via a weighted linear combination of the model head scores.

##### Request-level ranking.

For each request ss, the system retrieves a candidate set (e.g., ≈2,000\approx 2{,}000 items). A multi-task ranker hh then produces, for every candidate item xx, a vector of predicted scores over mm objectives (one score per prediction head).
A utility-weight vector w∈ℝmw\in\mathbb{R}^{m} defines a per-item utility score uu:

|  |  |  |  |
| --- | --- | --- | --- |
| (1) |  | u​(s,x;w)=∑i=1mwi​hi​(s,x)u(s,x;w)=\sum\limits\_{i=1}^{m}w\_{i}h\_{i}(s,x) |  |

where hi​(s,x)h\_{i}(s,x) is the predicted i-th objective from the ranker hh based on the request ss and item xx.
The system serves the top-kk ranked list based on u​(s,x;w)u(s,x;w).

In many production systems, utility weights ww are selected through offline analysis and repeated online experiments, and are typically applied globally (one weight for all requests) for extended periods. We recast this manual configuration process as a request-level decision problem that selects utility weights, enabling personalization and faster updates as environments and priorities change.

### 3.2. One-step RL / Contextual Bandit Formulation

We model utility-weight tuning as a one-step MDP at the request level. Each logged interaction is a tuple(s,a,r)(s,a,r), where ss is the request context, aa is the selected utility-weight action, and 𝐫∈ℝM\mathbf{r}\in\mathbb{R}^{M} is a vector of request-level rewards. Since aa affects only the current request and we optimize immediate engagement, we set γ=0\gamma=0 and do not model state transitions. To enable learning and offline evaluation from logged production data, we collect exploration traffic under a random policy and record action propensities.

### 3.3. State Representation

We define the state at the granularity of a single user request. For each request, ss comprises serving-time features summarizing the user and request context. Specifically, ss includes:

User information. Profile signals and long-term preference summaries (e.g., User embeddings).

User action history. A sequence of the last NN user actions, including embeddings of the engaged items and engagement timestamps/action types.

Context information. Serving-time context features (e.g., device type, surface, and request time).

We restrict ss to features available at serving time to ensure the learned policy is deployable and that training/evaluation match online inference. We study sensitivity to the state feature set via ablations in Appendix [Section A.4](#A1.SS4 "A.4. Feature Ablation Study ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems").

### 3.4. Action Space

Given a request-level state ss, the agent selects an action aa that specifies the utility weights for the prediction heads. The selected weights are applied only in the utility aggregation step (Eq. [1](#S3.E1 "Equation 1 ‣ Request-level ranking. ‣ 3.1. Utility Tuning for Ranking ‣ 3. Problem Formulation ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")); the upstream ranker and its per-item predictions remain unchanged.

##### Controlling a subset of utility weights.

Our framework supports tuning an arbitrary subset (or all) utility weights. In practice, jointly varying many weights in a production serving stack increases complexity and confounding: objectives interact through aggregation and downstream post-processing, making effects harder to attribute and govern. As an initial deployment step, we therefore tune only the two utility heads with the largest contribution to the production utility score, while fixing all other weights to their production values. This reduces action dimensionality, improves interpretability of learned trade-offs, and enables incremental rollout. A breakdown of per-head utility contributions is provided in Appendix [Section A.1](#A1.SS1 "A.1. Head Contribution Analysis ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems"). The two controlled objectives are *Repin*, the number of Pins a user saves to a board, and *P2P impressions*, the number of impression events in which a user is shown a Pin in a related-Pin context.

##### Discretizing the action values.

There is no ground-truth “correct” setting of utility weights; their effects are only observable through online outcomes under a complex serving pipeline. We therefore restrict actions to a compact discrete set to (i) bound exploration risk, (ii) make the control surface reviewable, and (iii) support stable offline policy evaluation from logs. To select candidate weight values, we analyze the distribution of each controlled head’s *contribution* to the overall utility score under the production configuration. This informs weight ranges that cover practically meaningful regimes—from near-negligible influence to strong emphasis—while remaining within operationally safe bounds (Appendix [Section A.2](#A1.SS2 "A.2. Action Values Selection ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")). We then discretize each range by selecting KK linearly spaced values.
Finally, we collect training data by running a randomized exploration policy over the resulting discrete action space.

Let 𝒲repin\mathcal{W}^{\text{repin}} and 𝒲p2p\mathcal{W}^{\text{p2p}} denote the discrete candidate sets for the Repin and P2P impression weights, respectively. The action space is:

|  |  |  |  |
| --- | --- | --- | --- |
| (2) |  | 𝒜={(wrepin,wp2p)∣wrepin∈𝒲repin,wp2p∈𝒲p2p},\mathcal{A}=\{(w^{\text{repin}},w^{\text{p2p}})\mid w^{\text{repin}}\in\mathcal{W}^{\text{repin}},\;w^{\text{p2p}}\in\mathcal{W}^{\text{p2p}}\}, |  |

where |𝒲repin|=|𝒲p2p|=K|\mathcal{W}^{\text{repin}}|=|\mathcal{W}^{\text{p2p}}|=K. In this work, we set K=7K=7.

### 3.5. Multi-objective Rewards

We use vector-valued rewards 𝐫∈ℝM\mathbf{r}\in\mathbb{R}^{M}. In our Homefeed instantiation, we align rewards with the two controlled objectives and set 𝐫=[rr​e​p​i​n,rp​2​p]\mathbf{r}=[r^{repin},r^{p2p}]. We learn objective-specific value estimates and expose a scalarization parameter α\alpha at inference time to induce a *family* of policies (Section [4.2](#S4.SS2 "4.2. Inference-time Pareto Sweeping for Governance ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")); evaluating this family yields an empirical Pareto frontier that stakeholders can use for operating-policy selection.

Let nr​e​p​i​nn^{repin} and np​2​pn^{p2p} denote the resulting request-level counts of Repin and P2P impression events, respectively. To reduce the influence of rare heavy-tail events and stabilize offline estimation and learning, we use clipped binary rewards (Appendix [Section A.3](#A1.SS3 "A.3. Engagement Distribution Analysis ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")):

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| (3) |  | 𝐫\displaystyle\mathbf{r} | =[rr​e​p​i​n,rp​2​p]\displaystyle=[r^{repin},r^{p2p}] |  |
|  | rr​e​p​i​n\displaystyle r^{repin} | =min⁡(nr​e​p​i​n,1)\displaystyle=\min(n^{repin},1) |  |
|  | rp​2​p\displaystyle r^{p2p} | =min⁡(np​2​p,1).\displaystyle=\min(n^{p2p},1). |  |

## 4. Proposed Methods: PRL-PUTS

In this section, we describe the high-level design of PRL-PUTS, our inference-time Pareto sweeping procedure for actionable operating-policy selection, and the model architecture used to predict objective-specific values for utility-weight actions.

### 4.1. Agent Design (One-step RL / Contextual Bandit)

PRL-PUTS operates in the one-step decision setting formalized in [Section 3](#S3 "3. Problem Formulation ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems"). For each request context (state) s∈𝒮s\in\mathcal{S}, the agent selects an action a∈𝒜a\in\mathcal{A}, where each action corresponds to a *utility-weight vector* ww applied on top of a fixed multi-task ranker’s head predictions (Eq. [1](#S3.E1 "Equation 1 ‣ Request-level ranking. ‣ 3.1. Utility Tuning for Ranking ‣ 3. Problem Formulation ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")). The environment returns immediate request-level rewards 𝐫=[rr​e​p​i​n,rp​2​p]\mathbf{r}=[r^{repin},r^{p2p}]. Because the action affects only the ranked list shown for the current request and we optimize immediate engagement outcomes, we use a one-step RL formulation where discount factor γ=0\gamma=0.

In a one-step setting, the objective-specific action-value functions reduce to conditional expected rewards:

|  |  |  |  |
| --- | --- | --- | --- |
| (4) |  | Qr​e​p​i​n​(s,a)=𝔼​[rr​e​p​i​n∣s,a],Qp​2​p​(s,a)=𝔼​[rp​2​p∣s,a].Q^{repin}(s,a)=\mathbb{E}[r^{repin}\mid s,a],\quad Q^{p2p}(s,a)=\mathbb{E}[r^{p2p}\mid s,a]. |  |

We therefore learn a MM-head value function (with MM=2 in our instantiation) that predicts these conditional expectations from logged exploration data. This design (i) decouples value estimation across objectives for clearer credit assignment and (ii) together with a restricted action space, exposes a small, reviewable control surface: the policy selects only from pre-defined utility-weight actions, enabling fast and safe iteration.

Training data support.
We train PRL-PUTS using unbiased exploration logs collected under a known randomized logging policy μ​(a∣s)\mu(a\mid s) (uniform over 𝒜\mathcal{A} in our deployment; [Section 6.1](#S6.SS1 "6.1. Data Collection ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")). Uniform exploration provides broad action coverage and simplifies offline evaluation, since propensities are constant ([Section 6.2](#S6.SS2 "6.2. Offline Policy Evaluation ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")).

### 4.2. Inference-time Pareto Sweeping for Governance

In production, stakeholders often need to *update multi-objective trade-offs quickly* as priorities shift. In standard multi-objective RL, one fixes a scalarization of the objectives during training, which yields a single policy; changing the trade-off typically requires retraining. PRL-PUTS instead separates learning from selection: we learn objective-specific value functions once, and at serving time choose the operating policy by varying a scalarization parameter α\alpha, which induces a family of deterministic policies (a Pareto sweep) without retraining. Given a request context ss and a scalarization parameter α∈[0,1]\alpha\in[0,1], we select the utility-weight action that maximizes a linear scalarization of the two predicted values:

|  |  |  |  |
| --- | --- | --- | --- |
| (5) |  | a⋆=arg⁡maxa∈𝒜⁡(α​Qθp​2​p​(s,a)+(1−α)​Qθr​e​p​i​n​(s,a))a^{\star}=\arg\max\limits\_{a\in\mathcal{A}}\left(\alpha Q\_{\theta}^{p2p}(s,a)+(1-\alpha)Q\_{\theta}^{repin}(s,a)\right) |  |

Sweeping α\alpha over a finite grid 𝒢⊂[0,1]\mathcal{G}\subset[0,1] yields a set of candidate policies {πα}α∈𝒢\{\pi\_{\alpha}\}\_{\alpha\in\mathcal{G}} representing different *supported* trade-offs between objectives.

##### Empirical Pareto frontier construction.

For governance and deployment planning, we evaluate each πα\pi\_{\alpha} offline on held-out exploration logs using off-policy evaluation ([Section 6.2](#S6.SS2 "6.2. Offline Policy Evaluation ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")). This yields a vector of offline lift estimates Δ​(α)∈ℝM\Delta(\alpha)\in\mathbb{R}^{M} relative to the production baseline, one per objective. We then retain the non-dominated evaluated policies to form an empirical Pareto frontier ([Section 6.3](#S6.SS3 "6.3. Empirical Pareto Frontier for Governance ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")), which stakeholders use to (i) visualize feasible trade-offs (one example is showed in [Figure 1](#S4.F1 "In Operating-policy control in production. ‣ 4.2. Inference-time Pareto Sweeping for Governance ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")) and (ii) select a small set of operating policies for online A/B tests.

##### Operating-policy control in production.

Selecting an operating policy requires only setting α\alpha via configuration; no model retraining is needed. This makes multi-objective tuning fast to update and easy to roll back.

![Refer to caption](2605.16344v1/content/resources/frontier.png)

Algorithm [1](#alg1 "Algorithm 1 ‣ Operating-policy control in production. ‣ 4.2. Inference-time Pareto Sweeping for Governance ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") summarizes our end-to-end training and serving-time control loop for the two-objective instantiation.

### 4.3. Two-head Value Model Architecture

![Refer to caption](2605.16344v1/x1.png)

Our model predicts objective-specific values for a given state-action pair (s,a)(s,a), i.e., estimates of 𝔼​[rr​e​p​i​n∣s,a]\mathbb{E}[r^{repin}\mid s,a] and 𝔼​[rp​2​p∣s,a]\mathbb{E}[r^{p2p}\mid s,a]. [Figure 2](#S4.F2 "In 4.3. Two-head Value Model Architecture ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") summarizes the architecture.

#### 4.3.1. State Module

The state module constructs a request-level representation from features available at serving time. Categorical features (e.g., device type) are mapped to dense vectors using embedding tables. Sequential features are encoded by a Transformer (Vaswani et al., [2017](#bib.bib65 "Attention is all you need")), followed by average pooling to obtain a fixed-length sequence representation. These are concatenated with a user embedding produced by internal Pinterest models and passed through an MLP to produce the final state representation.

#### 4.3.2. Encoding Actions

We encode actions as model inputs (rather than enumerating a separate output neuron per action) to keep the design extensible and to facilitate future extensions beyond the current discrete action set. For each action a=(wr​e​p​i​n,wp​2​p)a=(w^{repin},w^{p2p}), we min–max normalize each weight within its candidate set:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| (6) |  | wn​o​r​mr​e​p​i​n\displaystyle w^{repin}\_{norm} | =wr​e​p​i​n−min⁡(𝒲r​e​p​i​n)max⁡(𝒲r​e​p​i​n)−min⁡(𝒲r​e​p​i​n),\displaystyle=\frac{w^{repin}-\min(\mathcal{W}^{repin})}{\max(\mathcal{W}^{repin})-\min(\mathcal{W}^{repin})}, |  |
|  | wn​o​r​mp​2​p\displaystyle w^{p2p}\_{norm} | =wp​2​p−min⁡(𝒲p​2​p)max⁡(𝒲p​2​p)−min⁡(𝒲p​2​p)\displaystyle=\frac{w^{p2p}-\min(\mathcal{W}^{p2p})}{\max(\mathcal{W}^{p2p})-\min(\mathcal{W}^{p2p})} |  |

We first apply min–max normalization to the utility weights and then embed the normalized vector [wn​o​r​mr​e​p​i​n,wn​o​r​mp​2​p][w^{repin}\_{norm},w^{p2p}\_{norm}] with a one-layer MLP to obtain a dense action representation. Normalization maps weights to a consistent scale, improving training stability and enabling generalization to other weight values within the same range. At serving time, because |𝒜||\mathcal{A}| is small (e.g., K2K^{2}), we can efficiently score all actions and take an argmax under Eq. [5](#S4.E5 "Equation 5 ‣ 4.2. Inference-time Pareto Sweeping for Governance ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems"), which keeps inference simple and reliable.

#### 4.3.3. Backbone Module

We concatenate the state and action embeddings and feed them into a shared backbone implemented as a three-layer MLP. Each layer consists of batch normalization, a linear projection, and a ReLU nonlinearity, as illustrated in [Figure 2](#S4.F2 "In 4.3. Two-head Value Model Architecture ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems").

#### 4.3.4. Objective-specific Output Heads

The model has two output heads sharing the same backbone: one for Repin and one for P2P. Each head is a one-layer MLP producing a scalar value estimate. Since the rewards are clipped to {0,1}\{0,1\}, we bound the predicted values to [0,1][0,1] with a sigmoid so they can be interpreted as estimated conditional success probabilities:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| (7) |  | Qθr​e​p​i​n​(s,a)\displaystyle Q^{repin}\_{\theta}(s,a) | ≈𝔼​[rr​e​p​i​n∣s,a]∈[0,1],\displaystyle\approx\mathbb{E}\!\left[r^{repin}\mid s,a\right]\in[0,1], |  |
|  | Qθp​2​p​(s,a)\displaystyle Q^{p2p}\_{\theta}(s,a) | ≈𝔼​[rp​2​p∣s,a]∈[0,1]\displaystyle\approx\mathbb{E}\!\left[r^{p2p}\mid s,a\right]\in[0,1] |  |

#### 4.3.5. Training Objective

Given logged exploration examples {(si,ai)}\{(s\_{i},a\_{i})\}, we train the two heads with a sum of per-objective regression losses:

|  |  |  |  |
| --- | --- | --- | --- |
| (8) |  | L​(θ)=1N​∑i=1N((Qθp​2​p​(si,ai)−rip​2​p)2+(Qθr​e​p​i​n​(si,ai)−rir​e​p​i​n)2)L(\theta)=\frac{1}{N}\sum\_{i=1}^{N}\left((Q\_{\theta}^{p2p}(s\_{i},a\_{i})-r\_{i}^{p2p})^{2}+(Q\_{\theta}^{repin}(s\_{i},a\_{i})-r\_{i}^{repin})^{2}\right) |  |

where θ\theta is the parameters of the model and rir​e​p​i​nr\_{i}^{repin} and rip​2​pr\_{i}^{p2p} are the i-th Repin rewards and P2P rewards, NN is the total number of examples.
We also experimented with binary cross-entropy (BCE) losses; in our setting BCE did not improve offline or online performance relative to MSE, so we report results with the MSE objective.

## 5. Integration into Production

![Refer to caption](2605.16344v1/content/resources/production_structure.png)

Our goal is not only to develop an algorithmic approach to utility-weight tuning, but also to demonstrate a practical deployment path in a large-scale production recommender system. In this section, we describe how PRL-PUTS is integrated into Pinterest Homefeed’s serving stack (Figure [3](#S5.F3 "Figure 3 ‣ 5. Integration into Production ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")) and how the integration enables (i) ranker-independent control, (ii) negligible serving overhead with robust fallback behavior, and (iii) actionable governance via inference-time operating policy selection.

### 5.1. Decoupling Ranking Models

A central design goal of PRL-PUTS is to support deployment with minimal disruption to existing ranking infrastructure. We implement PRL-PUTS as a decoupled utility-control layer on top of the existing multi-task ranker: the ranker continues to produce per-objective predictions, while PRL-PUTS selects a request-level utility-weight configuration that is applied only in the downstream utility aggregation step. Both modules run in parallel. This separation makes the framework ranking model-agnostic which enables independent iteration: PRL-PUTS can be enabled, ramped, reconfigured (e.g., changing α\alpha), or reverted via configuration without changes to the deployed ranker.

### 5.2. Serving Latency Overhead

PRL-PUTS adds no measurable end-to-end serving latency. During serving, the ranker computes per-item predictions while PRL-PUTS runs in parallel to infer a request-level utility-weight vector from request context only. PRL-PUTS does not depend on item-level features or intermediate ranker computations; once per-item predictions are available, the blending layer applies the selected weights to form the final utility score (alongside existing post-processing). For reliability, we enforce a fixed inference budget and fall back to the production static weights on timeout, missing features, or inference failures.

### 5.3. Operating Policy Control and Rollback

PRL-PUTS exposes inference-time control through the scalarization parameter α\alpha (Section [4.2](#S4.SS2 "4.2. Inference-time Pareto Sweeping for Governance ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")). In production, the deployed operating policy is selected by setting α\alpha via serving configuration, allowing stakeholders to switch operating policy (or revert to static weights) without retraining the ranker or the RL model. To make this selection actionable, we operationalize the offline Pareto sweep results as a finite set of candidate operating policies reviewed (e.g., a table and graph over the evaluated grid of α\alpha values) with associated offline lift estimates on the primary objectives and key guardrails. We also continuously monitor online key metrics and guardrails (e.g., negative feedback and latency) during ramps and experiments.

### 5.4. Ranker refreshes and distribution shift

The integration remains stable under routine ranker iteration as long as the serving contract is preserved: the controlled objective heads retain consistent semantics and remain available at serving time. Because PRL-PUTS operates only on request features and selects among utility-weight configurations, ranker retraining does not require changes in PRL-PUTS. Retraining PRL-PUTS is required only when its contract materially changes (e.g., adding/removing a head controlled by PRL-PUTS) or when substantial distribution shifts in the controlled head predictions invalidate learned context-to-weight mappings. In these cases, the system can safely continue serving the production static utility while collecting fresh exploration data and retraining PRL-PUTS.

## 6. Experiments

### 6.1. Data Collection

We log training data from live Pinterest Homefeed traffic with per-request randomization. A capped 1.25% of requests is used for exploration, where the logging policy μ\mu samples uniformly from a discrete action set 𝒜\mathcal{A} (μ​(a∣s)=1|𝒜|\mu(a\mid s)=\frac{1}{|\mathcal{A}|}) and logs the chosen action and its propensity. Each action a∈𝒜a\in\mathcal{A} specifies a utility-weight vector applied to the fixed multi-task ranker’s per-objective predictions. We discretize each tunable weight into KK candidate values and form 𝒜\mathcal{A} as their Cartesian product (all other utility weights are held fixed). For each request, we log the context ss, action aa, and request-level rewards for each objective measured from user engagement on the top-kk items returned for that request (Repins and P2P impressions).

### 6.2. Offline Policy Evaluation

We evaluate candidate policies offline on held-out exploration logs using an off-policy evaluation (OPE) protocol. Exploration traffic samples actions uniformly at random from a discrete action set 𝒜\mathcal{A} (Section [6.1](#S6.SS1 "6.1. Data Collection ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")), so action propensities are constant (μ​(a∣s)=1/|𝒜|\mu(a\mid s)=1/|\mathcal{A}|) and require no clipping. We consider deterministic target policies derived from our two-head Q-network via argmax action selection.

##### Hold-out split.

We train the Q-network on 14 days of exploration logs and evaluate policies on a disjoint 7-day hold-out period to mitigate temporal leakage and to better reflect generalization under live traffic.

##### Hit-based OPE / Reward@HIT

Let the hold-out dataset consist of NN logged requests:

|  |  |  |
| --- | --- | --- |
|  | D={(si,ai,rip​2​p,rir​e​p​i​n)}i=1N,D=\{(s\_{i},a\_{i},r\_{i}^{p2p},r\_{i}^{repin})\}\_{i=1}^{N}, |  |

where sis\_{i} is the request context, aia\_{i} is the logged action, and rip​2​pr\_{i}^{p2p} and rir​e​p​i​nr\_{i}^{repin} are the observed request-level rewards. Given a learned Q-network and a scalarization parameter α\alpha, we derive a deterministic policy πα\pi\_{\alpha} and its predicted action ai⋆=πα​(si)a\_{i}^{\star}=\pi\_{\alpha}(s\_{i}) using [Equation 5](#S4.E5 "In 4.2. Inference-time Pareto Sweeping for Governance ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems"). We define a *hit* event when ai⋆=aia\_{i}^{\star}=a\_{i} and estimate each objective’s expected reward by averaging observed outcomes over hit events:

|  |  |  |  |
| --- | --- | --- | --- |
| (9) |  | V^hit​(πα;r)=∑i=1N𝟙​[ai⋆=ai]⋅ri∑i=1N𝟙​[ai⋆=ai],\widehat{V}\_{\text{hit}}(\pi\_{\alpha};r)=\frac{\sum\_{i=1}^{N}\mathbbm{1}[a\_{i}^{\star}=a\_{i}]\cdot r\_{i}}{\sum\_{i=1}^{N}\mathbbm{1}[a\_{i}^{\star}=a\_{i}]}, |  |

where r∈{rp​2​p,rr​e​p​i​n}r\in\{r^{p2p},r^{repin}\} and 𝟙​[⋅]\mathbbm{1}[\cdot] is an indicator. Because μ​(a∣s)\mu(a\mid s) is constant under uniform exploration, the inverse-propensity weights cancel in the self-normalized estimator, yielding the hit-based form in Eq. [9](#S6.E9 "Equation 9 ‣ Hit-based OPE / Reward@HIT ‣ 6.2. Offline Policy Evaluation ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems").

We choose Reward@HIT for its simplicity and auditability under uniform randomization; we leave more sample-efficient OPE estimators to future work.

##### Offline lift relative to production.

For each objective rr, we report offline lift relative to the production policy πprod\pi\_{\text{prod}} (which uses a static weight vector) by evaluating both policies on the same hold-out data:

|  |  |  |  |
| --- | --- | --- | --- |
| (10) |  | Δoffline​(πα;r)=V^hit​(πα;r)−V^hit​(πprod;r).\Delta\_{\text{offline}}(\pi\_{\alpha};r)=\widehat{V}\_{\text{hit}}(\pi\_{\alpha};r)-\widehat{V}\_{\text{hit}}(\pi\_{\text{prod}};r). |  |

This yields paired offline lift estimates for Repin and P2P impression for each evaluated α\alpha, which we use for model selection and trade-off characterization. Estimator reliability and variance depends on the number of hit events; in our setting, a relatively small action space coupled with the large exploration log and a 7-day hold-out provide sufficient support for stable policy comparisons across α\alpha.

### 6.3. Empirical Pareto Frontier for Governance

Section [4.2](#S4.SS2 "4.2. Inference-time Pareto Sweeping for Governance ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") describes how inference-time sweeping over the scalarization parameter α\alpha induces a family of deterministic policies from a single trained two-head Q-network. In this section we describe how we *evaluate* that policy family and convert it into an empirical Pareto frontier that can be used as a governance artifact for deployment decisions.

##### Discrete sweep and offline evaluation.

In practice, we evaluate a finite grid of α\alpha values, 𝒢⊂[0,1]\mathcal{G}\subset[0,1] with |𝒢|=25|\mathcal{G}|=25, and for each α∈𝒢\alpha\in\mathcal{G} we derive a deterministic policy πα\pi\_{\alpha} via argmax action selection using [Equation 5](#S4.E5 "In 4.2. Inference-time Pareto Sweeping for Governance ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems"). We evaluate each πα\pi\_{\alpha} on the same 7-day hold-out exploration log using the hit-based OPE estimator in Section  [6.2](#S6.SS2 "6.2. Offline Policy Evaluation ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems"), yielding paired offline lifts relative to production:

|  |  |  |
| --- | --- | --- |
|  | Δoffline​(πα)=(Δoffline​(πα;rr​e​p​i​n),Δoffline​(πα;rp​2​p)).\Delta\_{\text{offline}}(\pi\_{\alpha})=\big(\Delta\_{\text{offline}}(\pi\_{\alpha};r^{repin}),\,\Delta\_{\text{offline}}(\pi\_{\alpha};r^{p2p})\big). |  |

Each evaluated α\alpha therefore corresponds to one point in the Repin–P2P impression objective space (Repin lift vs. P2P impression lift).

##### Frontier construction.

We construct an empirical Pareto frontier by retaining only the non-dominated evaluated policies. Specifically, an evaluated policy is dominated if there exists another evaluated policy with at least as large offline lift on both objectives and strictly larger lift on at least one objective. The remaining non-dominated policies form the empirical frontier as shown in [Figure 1](#S4.F1 "In Operating-policy control in production. ‣ 4.2. Inference-time Pareto Sweeping for Governance ‣ 4. Proposed Methods: PRL-PUTS ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems").

##### Selecting operating policies for online tests.

We use the offline frontier to select a small number of representative operating policies spanning different regions of the Repin–P2P impression trade-off curve for online A/B tests. Concretely, we select (i) a Repin-leaning policy near the frontier extreme, (ii) a P2P impression-leaning policy near the opposite extreme, and (iii) a “knee” policy that provides a balanced trade-off. To reduce deployment risk and align with stakeholder requirements, we restrict online candidates to operating policies that are predicted offline to be non-degrading on both objectives (i.e., non-negative lift in both Repin and P2P impression).

### 6.4. Online Experiments

We validate PRL-PUTS through online experiments in a production setting. The goals are (i) to measure the real-world impact of policies selected from the offline Pareto frontier, and (ii) to test whether offline trade-off estimates reliably predict online metric movements under live traffic.

#### 6.4.1. Experiment Setup

We conduct controlled A/B tests by randomly splitting Homefeed traffic at the user level between the production baseline and three treatment policies derived from the same trained two-head Q-network. The baseline uses the current production utility with global static Repin and P2P impression weights. Each treatment reuses the same trained model and serving stack, and differs only in the inference-time policy configuration (i.e., the choice of α\alpha selected from the offline Pareto frontier), enabling evaluation of multiple Repin–P2P impression operating policies.

All experiment arms share the same serving infrastructure; the only variation across arms is the action-selection policy applied at serving time. Experiments run for two weeks, with each arm allocated 1% of total Pinterest Homefeed traffic. We report relative percentage lifts for Repin and P2P impression, and also report Successful Sessions (SS), defined as sessions with at least one key positive action, as a composite engagement metric. Bolded metrics in the tables indicates a statistically significant lift relative to the production baseline.

#### 6.4.2. Global operating policies from the offline frontier

In the first setting, we deploy a global operating policy where a single trade-off parameter α\alpha is applied uniformly across all users receiving a treatment. We select three representative operating policies from the offline Pareto frontier (Repin-leaning, balanced/knee, and P2P impression-leaning). [Table 1](#S6.T1 "In 6.4.2. Global operating policies from the offline frontier ‣ 6.4. Online Experiments ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") reports the corresponding offline estimates and online lifts.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| Policy | α\alpha | Repin | P2P | SS |
|  |  | Online | |  |
| Repin-leaning | 0.17 | +2.26% | -0.21% | -0.09% |
| balanced | 0.21 | +1.35% | -0.04% | -0.02% |
| P2P-leaning | 0.24 | +0.66% | +0.30% | +0.13% |
|  |  | Offline | |  |
| Repin-leaning | 0.17 | +2.77% | -0.30% | - |
| balanced | 0.21 | +1.46% | +0.41% | - |
| P2P-leaning | 0.24 | +0.31% | +1.18% | - |
|  |  | Correlation | |  |
| Correlation |  | 0.999 | 0.986 |  |

As shown in [Table 1](#S6.T1 "In 6.4.2. Global operating policies from the offline frontier ‣ 6.4. Online Experiments ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems"), online metric movements follow the expected trade-off pattern: Repin-leaning configurations achieve larger Repin lift with some P2P impression reduction, while P2P impression-leaning configurations increase P2P impressions with reduced Repin lift. The balanced operating policy provides a more even trade-off. Across these operating policies, SS is non-degrading and shows a small improvement for the P2P impression-leaning policy.

#### 6.4.3. Cohort-conditioned operating policies

In the second setting, we allow α\alpha to vary as a function of a coarse user-context signal (user cohort), enabling different cohorts to adopt different operating policies while remaining interpretable and easy to govern. We define three cohorts:

CORE: users who saved on at least 4 days out of the last 28 days.

CASUAL: users who were active on at least 4 days out of the last 28 days.

REST: all remaining users.

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Policy | α\alpha | | | Repin | | | | P2P impression | | | | Successful Session (SS) | | | |
|  | CORE | CAUSAL | REST | CORE | CAUSAL | REST | TOTAL | CORE | CAUSAL | REST | TOTAL | CORE | CAUSAL | REST | TOTAL |
|  |  |  |  | Online | | | | | | | | | | | |
| repin-leaning | 0.28 | 0.07 | 0.17 | -0.09% | +7.62% | +1.70% | +0.65% | -0.30% | +0.10% | +0.13% | -0.03% | +0.02% | -0.03% | -0.11% | -0.01% |
| balanced | 0.28 | 0.14 | 0.31 | +0.36% | +3.36% | -1.42% | +0.36% | -0.20% | +0.58% | +0.55% | +0.28% | -0.01% | +0.09% | -0.09% | +0.02% |
| p2p-leaning | 0.28 | 0.18 | 0.35 | -0.11% | +1.90% | -2.44% | -2.19% | -0.33% | +1.02% | +0.73% | +0.48% | +0.04% | +0.32% | -0.03% | +0.17% |
|  |  |  |  | Offline | | | | | | | | | | | |
| repin-leaning | 0.28 | 0.07 | 0.17 | +0.02% | +10.34% | +4.87% | +1.20% | +0.75% | +0.49% | +0.50% | +0.58% | - | - | - | - |
| balanced | 0.28 | 0.14 | 0.31 | +0.02% | +5.04% | +3.12% | +0.31% | +0.75% | +2.53% | +2.23% | +1.62% | - | - | - | - |
| p2p-leaning | 0.28 | 0.18 | 0.35 | +0.02% | +2.36% | +0.70% | 0.00% | +0.75% | +3.26% | +3.23% | +2.02% | - | - | - | - |
|  |  |  |  | Correlation | | | | | | | | | | | |
|  |  |  |  | - | 0.996 | 0.929 | 0.763 | - | 0.971 | 0.997 | 0.992 | - | - | - | - |

Operationally, for each request we select α\alpha based on the user’s cohort category and apply the corresponding policy. [Table 2](#S6.T2 "In 6.4.3. Cohort-conditioned operating policies ‣ 6.4. Online Experiments ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") summarizes online results (offline frontiers for each cohort are provided in Appendix [Section A.5](#A1.SS5 "A.5. Offline Pareto Frontier for User Cohorts ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")). The CASUAL and REST cohorts respond to α\alpha as expected, exhibiting controllable shifts along the Repin–P2P impression trade-off curve (e.g., Repin-leaning increases Repin while P2P impression-leaning increases P2P impression). For the CORE cohort, offline evaluation indicates only one operating policy is non-degrading on both objectives; therefore we reuse that same α\alpha value across the three variants.

#### 6.4.4. Offline-to-online consistency

To quantify whether offline trade-off estimates are decision-useful for selecting online operating policies, we compare offline-predicted lifts to online observed lifts across the evaluated three operating policies and compute Pearson correlation for each objective. We find strong offline-to-online consistency (reported in the final rows of [Table 1](#S6.T1 "In 6.4.2. Global operating policies from the offline frontier ‣ 6.4. Online Experiments ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") and [Table 2](#S6.T2 "In 6.4.3. Cohort-conditioned operating policies ‣ 6.4. Online Experiments ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")), indicating that the offline Pareto frontier is actionable for choosing among operating policies prior to online testing.

|  | Repin | P2P | SS |
| --- | --- | --- | --- |
| matched static weights | -0.24% | +0.07% | +0.02% |
| PRL-PUTS | +0.12% | +0.21% | +0.11% |

#### 6.4.5. Personalization vs. global weight tuning

A natural question is whether observed gains are driven primarily by global utility reweighting or by contextual personalization. To disentangle these effects, we construct a static baseline by setting Repin and P2P impression utility weights to match the traffic-level averages produced by PRL-PUTS. For example, the learned policy yields an average P2P impression weight of 11.83 (vs. the production default of 9.1); we therefore increase the static production weight to 11.83. Results are reported in [Table 3](#S6.T3 "In 6.4.4. Offline-to-online consistency ‣ 6.4. Online Experiments ‣ 6. Experiments ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems"). The static-tuned variant is neutral or negative online and does not reproduce PRL-PUTS gains, indicating that improvements are driven by context-dependent weight selection rather than a single globally retuned weight vector.

## 7. Discussion

Known limitations.
PRL-PUTS is intentionally designed around a constrained, production-compatible abstraction, and that abstraction has clear limits. First, the one-step RL (contextual bandit) formulation optimizes immediate, request-level outcomes and does not explicitly capture longer-horizon effects such as future engagement or retention; it is therefore best suited to objectives with fast feedback and short-window attribution. Second, our instantiation focuses on two controlled objectives, which keeps trade-offs interpretable and governable (a single α\alpha sweep), but does not directly address cases with three or more goals. Third, we restrict the controller to a compact discrete action set to bound exploration risk and to ensure adequate action support in logged data for stable offline comparison;
this improves safety and evaluation but reduces expressivity and may miss fine-grained operating policies.

Longer-horizon decision making.
A natural extension is to move beyond the one-step assumption when business objectives require delayed credit assignment. Doing so would require additional instrumentation (e.g., longer attribution windows and trajectory-style logging) and learning methods that incorporate bootstrapping over future value rather than regressing only immediate rewards. In large-scale recommenders, longer horizons also increase sensitivity to confounding and non-stationarity, so an important direction is pairing longer-horizon learning with production-suitable safeguards such as conservative deployment constraints and periodic validation of offline-to-online consistency.

Scaling objectives and improving efficiency.
Future work can broaden the control surface while improving sample efficiency. For more than two objectives, a single scalarization knob is insufficient; promising directions include constrained selection or exposing a small number of auditable preference parameters. On the action side, moving from discrete grids to continuous weights can improve expressivity, but it raises new challenges in both exploration and off-policy evaluation. A practical path is to combine continuous actions with adaptive, policy-based exploration that concentrates data on high-value regions while maintaining coverage/uncertainty controls needed for trustworthy counterfactual validation.

## 8. Conclusions and Future Work

We presented PRL-PUTS, a production-ready RL control layer for request-level utility-weight tuning on top of a fixed multi-task ranker. PRL-PUTS enables fast, ranker-independent, and governable multi-objective control by exposing inference-time Pareto sweeping via a scalarization parameter α\alpha. Deployed in Pinterest Homefeed with negligible serving overhead, PRL-PUTS delivers controllable Repin–P2P trade-offs and demonstrates strong offline-to-online consistency using unbiased exploration logs and online experiments. Future work will explore extending PRL-PUTS to richer action spaces and longer-horizon objectives.

###### Acknowledgements.

## References

## Appendix A Appendix

### A.1. Head Contribution Analysis

We compute the utiliy score based on the [Equation 1](#S3.E1 "In Request-level ranking. ‣ 3.1. Utility Tuning for Ranking ‣ 3. Problem Formulation ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems"). The contribution of each head (cic\_{i}) is computed as:

|  |  |  |  |
| --- | --- | --- | --- |
| (11) |  | ci​(s,x;w)=‖wi​hi​(s,x)‖∑im‖wi​hi​(s,x)‖c\_{i}(s,x;w)=\frac{\|w\_{i}h\_{i}(s,x)\|}{\sum\limits\_{i}^{m}\|w\_{i}h\_{i}(s,x)\|}\\ |  |

where hi​(s,x)h\_{i}(s,x) is the predicted i-th objective from the ranker hh based on the request context ss and item xx.
[Figure 4](#A1.F4 "In A.1. Head Contribution Analysis ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") shows the contribution of each head using the static prodution weight wp​r​o​dw\_{prod}. We observe that Repin and P2P impression head are the top 2 heads that contribute almost 90%90\% to the final utility score. We tune these two heads as the first step.

![Refer to caption](2605.16344v1/content/resources/head_dist.png)

### A.2. Action Values Selection

We select a set of candidate values for the Repin and P2P impression utility weights from the following ranges:

Repin: [10,200][10,200]

P2P impression: [1,30][1,30]

These ranges are chosen to provide broad coverage of the trade-off space. [Figure 6](#A1.F6 "In A.2. Action Values Selection ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") and [Figure 5](#A1.F5 "In A.2. Action Values Selection ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") illustrate how each head’s contribution to the overall utility score varies as its corresponding weight changes while holding the other weight fixed. In both cases, the selected ranges span from low to high emphasis, enabling exploration from near-negligible influence to dominant contribution. For example, increasing the P2P impression weight from 1 to 30 changes its contribution from below 1% to nearly 50% of the total utility score (see [Figure 5](#A1.F5 "In A.2. Action Values Selection ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems")). For reference, the production baseline uses a Repin weight of 91.6 and a P2P impression weight of 9.1.

![Refer to caption](2605.16344v1/content/resources/p2p_weight_ranges.png)
![Refer to caption](2605.16344v1/content/resources/repin_weight_ranges.png)

### A.3. Engagement Distribution Analysis

![Refer to caption](2605.16344v1/x2.png)
![Refer to caption](2605.16344v1/x3.png)

We partition examples into engagement deciles and compute the mean engagement within each decile to summarize how engagement volume is distributed across the population. [Figure 7](#A1.F7 "In A.3. Engagement Distribution Analysis ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") and [Figure 8](#A1.F8 "In A.3. Engagement Distribution Analysis ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") show the percentile distributions of P2P impressions and Repin, respectively. Both metrics exhibit a pronounced long-tailed distribution: more than 80% of examples receive at most one engagement. To mitigate the influence of extreme values, we define the reward as a clipped version of engagement, mapping counts to the interval [0,1][0,1].

This clipping improves robustness but discards information about engagement intensity beyond the first event (e.g., it treats 2 and 200 engagements identically), which may remove useful signal for distinguishing highly engaging content and may limit the agent’s ability to optimize for the upper tail. In future work, we plan to incorporate richer reward shaping that preserves magnitude information—e.g., log-scaled or quantile-normalized rewards, multi-level bins, or separate objectives for occurrence vs. volume—while maintaining training stability.

### A.4. Feature Ablation Study

![Refer to caption](2605.16344v1/content/resources/feature_ablation.png)

We conduct a feature ablation study to quantify the contribution of major feature groups to offline policy performance and to identify which signals are most informative for learning accurate action-value estimates. Unlike a standard leave-one-group-out protocol, our study adopts a *feature-group isolation* setting: starting from a common experimental setup, we train a series of models where each variant is provided with *only one* feature group at a time. This design enables a clearer attribution of performance to individual feature families and highlights the standalone predictive strength of each group under identical training conditions.

#### A.4.1. Ablation Setup

We partition input signals into semantically coherent feature groups (e.g., user features, user action history, and context information). For each ablation variant, we retain exactly one feature group as input and remove all other groups. We keep the remainder of the training and evaluation pipeline unchanged across variants, including data sampling, training schedule, hyperparameters, and model capacity (except for the corresponding input dimensionality change). As a result, differences in offline performance across variants primarily reflect the marginal value of the retained feature group rather than confounding factors introduced by changes in training procedure.

#### A.4.2. Ablation Results

Each ablated variant is evaluated on the same hold-out dataset using Reward@HIT for the policy induced by the corresponding model. For visualization and comparison, we construct and plot the Pareto frontier of each ablation variant alongside the full-feature baseline within a single figure. [Figure 9](#A1.F9 "In A.4. Feature Ablation Study ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") shows the results.
When evaluating feature groups in isolation, we find that user information provides the strongest contribution to offline performance. Sequence-based features exhibit trends that are highly consistent with those observed for user features, suggesting they capture complementary signals of similar predictive value. In contrast, models trained using context-only features perform substantially worse, indicating that contextual signals alone are insufficient to support accurate action-value estimation.

### A.5. Offline Pareto Frontier for User Cohorts

![Refer to caption](2605.16344v1/content/resources/user_cohorts.png)

[Figure 10](#A1.F10 "In A.5. Offline Pareto Frontier for User Cohorts ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems") presents the offline Pareto frontiers for different user cohorts. We observe that the CASUAL and REST cohorts are more sensitive to the trade-off parameter α\alpha than the CORE cohort. With appropriate tuning of α\alpha, we achieve up to a 10% offline lift in Repin for CASUAL users and up to a 5% offline lift in Repin for REST users. In contrast, CORE users exhibit a more constrained trade-off: it is difficult to identify operating points that simultaneously improve both Repin and P2P relative to the production baseline. As shown in [Figure 10](#A1.F10 "In A.5. Offline Pareto Frontier for User Cohorts ‣ Appendix A Appendix ‣ A Production-Ready RL Framework for Personalized Utility Tuning with Pareto Sweeping in Pinterest Recommender Systems"), only a single α\alpha value yields a positive lift on both metrics for the CORE cohort.

![[LOGO]](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)

## Instructions for reporting errors

We are continuing to improve HTML versions of papers, and your feedback helps enhance accessibility and mobile
support. To report errors in the HTML that will help us improve conversion and rendering, choose any of the
methods listed below:

**Tip:** You can select the relevant text first, to include it in your report.

Our team has already identified [the following issues](https://github.com/arXiv/html_feedback/issues). We appreciate your time reviewing and reporting rendering errors we
may not have found yet. Your efforts will help us improve the HTML versions for all readers, because disability
should not be a barrier to accessing research. Thank you for your continued support in championing open access for
all.

Have a free development cycle? Help support accessibility at arXiv! Our collaborators at LaTeXML maintain a [list of packages that need conversion](https://github.com/brucemiller/LaTeXML/wiki/Porting-LaTeX-packages-for-LaTeXML), and welcome [developer contributions](https://github.com/brucemiller/LaTeXML/issues).
