# RewardRank: Optimizing True Learning-to-Rank Utility

###### Abstract

Traditional ranking systems optimize offline proxy objectives that rely on oversimplified assumptions about user behavior, often neglecting factors such as position bias and item diversity. Consequently, these models fail to improve true counterfactual utilities such as such as click-through rate or purchase probability, when evaluated in online A/B tests.
We introduce RewardRank, a data-driven learning-to-rank (LTR) framework for counterfactual utility maximization. RewardRank first learns a reward model that predicts the utility of any ranking directly from logged user interactions, and then trains a ranker to maximize this reward using a differentiable soft permutation operator.
To enable rigorous and reproducible evaluation, we further propose two benchmark suites: (i) Parametric Oracle Evaluation (PO-Eval), which employs an open-source click model as a counterfactual oracle on the Baidu-ULTR dataset, and (ii) LLM-as-User Evaluation (LAU-Eval), which simulates realistic user behavior via large language models on the Amazon-KDD-Cup dataset. RewardRank achieves the highest counterfactual utility across both benchmarks and demonstrates that optimizing classical metrics such as NDCG is sub-optimal for maximizing true user utility. Finally, using real user feedback from the Baidu-ULTR dataset, RewardRank establishes a new state of the art in offline relevance performance. Overall, our results show that learning-to-rank can be reformulated as direct optimization of counterfactual utility, achieved in a purely data-driven manner without relying on explicit modeling assumptions such as position bias.
Our code is available at: <https://github.com/GauravBh1010tt/RewardRank>

## 1 Introduction

The goal of any ranking system is to model human decision-making in a way that maximizes user engagement and utility. However, real-world user behavior is shaped by subtle, context-dependent cognitive biases that traditional ranking losses fail to capture. Engagement often drops when users are presented with redundant or overly similar items, whereas introducing diversity or strategically positioning items can significantly enhance interest. For example, the decoy effect—where the presence of a less-attractive item increases preference for a similar alternative—has been observed in search interactions and shown to meaningfully influence user choices (Wang et al., [2025a](https://arxiv.org/html/2508.14180v2#bib.bib39)). Other well-documented biases include position bias (Chen et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib7); Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17); Zou et al., [2022](https://arxiv.org/html/2508.14180v2#bib.bib46)), brand bias (Li et al., [2025](https://arxiv.org/html/2508.14180v2#bib.bib24)), and similarity aversion (Tversky & Simonson, [2004](https://arxiv.org/html/2508.14180v2#bib.bib37)). In online advertising, the goal is often to maximize the probability that a user clicks on any item in the list, rather than just the top-ranked one. If data shows that users tend to click on the second position, it may be optimal to place the most engaging ad there to improve overall performance. Likewise, in recommendation scenarios, users may prefer a diverse mix of product styles or brands over a cluster of nearly identical, albeit highly relevant, items. Traditional ranking losses, which emphasize relevance at individual positions (typically the top), are ill-suited for modeling such list-level behaviors (Figure [1](https://arxiv.org/html/2508.14180v2#S1.F1 "Figure 1 ‣ 1 Introduction ‣ RewardRank: Optimizing True Learning-to-Rank Utility")). They overlook the fact that user utility depends not just on which items are shown, but how they are arranged, highlighting the limitations of handcrafted objectives in capturing the interactive and comparative nature of real user decision-making.

A natural way to model user behavior is by learning preferences over full permutations of items within a query group (i.e., a query and its associated items). The ideal objective is to identify and rank those permutations that are most likely to drive user engagement, which can be formulated as a likelihood maximization problem: maximizing the probability of observing high-engagement permutations while minimizing that of unengaged ones. However, the combinatorial explosion of the permutation space quickly renders this approach intractable; for instance, ranking 10 items results in 10!10! (over 3.6 million) possible arrangements. To address this, recent approaches adopt a utility-based framework (Feng et al., [2021](https://arxiv.org/html/2508.14180v2#bib.bib11); Shi et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib35); Xi et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib44); Ren et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib34); Wang et al., [2025b](https://arxiv.org/html/2508.14180v2#bib.bib40)), where a utility model is trained to score permutations based on user preferences, and a ranker is subsequently optimized to generate item orders that maximize the predicted utility. While this framework reduces the combinatorial burden, it introduces two key challenges. First is the classic exploration–exploitation dilemma: the ranker must leverage known high-utility arrangements while also exploring novel permutations that may yield higher engagement.

![Refer to caption](fig/illus.png)

Second is utility model misspecification (akin to reward misspecification Clark & Amodei ([2016](https://arxiv.org/html/2508.14180v2#bib.bib8)); Coste et al. ([2023](https://arxiv.org/html/2508.14180v2#bib.bib9))): if the learned reward model fails to accurately reflect true user preferences, the ranker may be misled, resulting in poor exploration and degraded overall performance.

In operational ranking systems, user interactions are logged for only a small fraction of the total permutation space. For example, in Figure [1](https://arxiv.org/html/2508.14180v2#S1.F1 "Figure 1 ‣ 1 Introduction ‣ RewardRank: Optimizing True Learning-to-Rank Utility"), only 3 out of the 120 possible arrangements of 5 items for the query "laptop bag" are observed, constituting the factual space. These observed interactions define the factual/observed space, whereas the vast majority of unexposed, yet potentially high-utility, permutations form the counterfactual/unobserved space. The optimal arrangement that maximizes user engagement may exist anywhere within the full permutation space of 120 arrangements. One of the major challenges in counterfactual ranking lies in reliably evaluating unobserved permutations. Even if the full permutation space is modeled, evaluating ranking strategies under counterfactual settings remains challenging due to the lack of explicit supervision (Agarwal et al., [2019](https://arxiv.org/html/2508.14180v2#bib.bib1); Gupta et al., [2024b](https://arxiv.org/html/2508.14180v2#bib.bib16); [a](https://arxiv.org/html/2508.14180v2#bib.bib15); Buchholz et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib2)). For instance, in Figure [1](https://arxiv.org/html/2508.14180v2#S1.F1 "Figure 1 ‣ 1 Introduction ‣ RewardRank: Optimizing True Learning-to-Rank Utility"), 117 out of 120 possible arrangements remain unobserved, making their evaluation inherently counterfactual. Existing approaches, such as offline A/B testing, inverse propensity scoring, or other debiasing techniques, are often costly, statistically unstable, or difficult to scale, making counterfactual evaluation a central bottleneck in listwise utility optimization.

To address these challenges, we propose RewardRank, a counterfactual utility maximization framework that models user behavior over full item permutations. Rather than scoring items in isolation, we learn a permutation-aware utility function that captures user preferences at the list level. To enable differentiable optimization over permutations, we employ the SoftSort operator (Prillo & Eisenschlos, [2020](https://arxiv.org/html/2508.14180v2#bib.bib30)) to construct soft item embeddings, allowing end-to-end training of the ranking model with respect to utility gradients. To mitigate the effects of reward model misspecification—where the learned utility may diverge from actual user preferences—we introduce a correction term in the ranker’s training objective that improves robustness during optimization. For evaluation, we present two scalable, fully automated protocols that assess counterfactual performance without requiring human labels. Parametric Oracle Evaluation (PO-Eval) uses a pretrained, position-aware oracle to provide soft supervision and serve as a proxy for user behavior. LLM-As-User Evaluation (LAU-Eval) leverages large language models to simulate user preferences and assess ranking quality across unobserved permutations. Together, these methods enable efficient benchmarking of counterfactual ranking strategies and help align learned rankings with actual or simulated user utility.

Our key contributions can be summarized as:

We introduce RewardRank, a framework for counterfactual utility maximization that learns a permutation-aware reward model, capturing human list-level preferences and behavioral biases without any explicit modeling assumptions such as position bias.

We enable end-to-end ranking optimization using differentiable soft permutation operators, and incorporating a per-item auxiliary loss along with a misspecified reward correction term to aid counterfactual space exploration.

We propose two large-scale automated evaluation protocols: PO-Eval (parametric oracle) and LAU-Eval (LLM-as-user), and construct reproducible testbeds for scalable counterfactual ranking evaluation. Experiments on these testbeds reveal that optimizing standard offline ranking metrics such as NDCG do not reliably maximize true user utility.

In both proposed counterfactual testbeds, RewardRank consistently achieves the highest learning-to-rank (LTR) utility compared to existing and widely adopted ranking methods. When trained on real click signals from an industry-scale dataset, RewardRank further establishes a new state-of-the-art in relevance performance.

## 2 Related Work

Traditional ranking methods. Traditional learning-to-rank (LTR) methods are typically categorized into three classes: point-wise, pair-wise, and list-wise approaches. Point-wise methods treat ranking as a regression or classification problem by independently assigning relevance scores to each item (Burges et al., [2005a](https://arxiv.org/html/2508.14180v2#bib.bib4); [b](https://arxiv.org/html/2508.14180v2#bib.bib5)). While computationally efficient, they neglect interactions among items in the ranked list. Pair-wise approaches, including RankSVM (Joachims, [2002](https://arxiv.org/html/2508.14180v2#bib.bib21)), RankBoost (Freund et al., [2003](https://arxiv.org/html/2508.14180v2#bib.bib12)), and LambdaMART (Burges, [2006](https://arxiv.org/html/2508.14180v2#bib.bib3); Wu et al., [2010](https://arxiv.org/html/2508.14180v2#bib.bib43)), aim to learn relative preferences between item pairs, improving over point-wise methods but still failing to capture full list-level dependencies. In contrast, list-wise methods optimize objectives over the entire ranking, such as NDCG (Cao et al., [2007](https://arxiv.org/html/2508.14180v2#bib.bib6); Xia et al., [2008](https://arxiv.org/html/2508.14180v2#bib.bib45)), offering better alignment with evaluation metrics.

Recent large-scale datasets such as Baidu-ULTR (Zou et al., [2022](https://arxiv.org/html/2508.14180v2#bib.bib46)) have enabled realistic benchmarking of ranking algorithms under user-interaction-driven settings, facilitating systematic studies on position bias, distribution shift, and counterfactual evaluation in LTR (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)). Building on these advances, modern approaches have expanded beyond purely supervised objectives toward *data-driven* and *representation-rich* formulations. Pretraining-based LTR models leverage large language or multimodal corpora to learn transferable ranking priors (Hou et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib18)), while latent cross-encoding methods (Luo et al., [2022](https://arxiv.org/html/2508.14180v2#bib.bib26)) and set-aware transformers Qin et al. ([2021](https://arxiv.org/html/2508.14180v2#bib.bib32)) jointly embed queries and items to capture fine-grained contextual dependencies.

Counterfactual Learning-to-Rank.
Prior work in counterfactual learning-to-rank (CLTR) primarily addresses position bias in implicit feedback using methods such as inverse propensity scoring (IPS) (Joachims et al., [2017](https://arxiv.org/html/2508.14180v2#bib.bib22)) and doubly robust estimation (Oosterhuis, [2023](https://arxiv.org/html/2508.14180v2#bib.bib28)). Extensions include modeling trust bias (Agarwal et al., [2019](https://arxiv.org/html/2508.14180v2#bib.bib1)) and jointly correcting for both position and trust biases (Vardasbi et al., [2020](https://arxiv.org/html/2508.14180v2#bib.bib38)). Recent approaches explore policy optimization via proximal updates (Gupta et al., [2024b](https://arxiv.org/html/2508.14180v2#bib.bib16)) and extend this to trust-aware CLTR through proximal ranking objectives (Gupta et al., [2024a](https://arxiv.org/html/2508.14180v2#bib.bib15)). While effective, these methods often focus narrowly on position bias or make strong assumptions, underscoring the need for broader utility-driven ranking frameworks, as pursued in this work.

Utility-oriented counterfactual reranking.
Reranking methods enhance an initial ranked list by applying a secondary model to better optimize downstream objectives such as user utility, fairness, or diversity (Xi et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib44); Wang et al., [2025b](https://arxiv.org/html/2508.14180v2#bib.bib40)). Recent work in counterfactual ranking predominantly follows a two-stage framework consisting of a generator and an evaluator (Xi et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib44); Shi et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib35); Ren et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib34); Wang et al., [2025b](https://arxiv.org/html/2508.14180v2#bib.bib40)). For example, URCC (Xi et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib44)) trains a set-aware utility model and employs a context-sensitive pairwise LambdaLoss to guide the ranker. NLGR (Wang et al., [2025b](https://arxiv.org/html/2508.14180v2#bib.bib40)) leverages neighboring lists within a generator-evaluator setup for utility optimization. PRS (Feng et al., [2021](https://arxiv.org/html/2508.14180v2#bib.bib11)) adopts beam search to generate candidate permutations and evaluates them using a permutation-wise scoring model, while PIER (Shi et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib35)) uses SimHash to select top-K candidates from the full permutation space efficiently.

Reranking approaches rely on a strong base ranker trained on logged data and typically explore counterfactuals around its initial permutations Xi et al. ([2024](https://arxiv.org/html/2508.14180v2#bib.bib44)); Wang et al. ([2025b](https://arxiv.org/html/2508.14180v2#bib.bib40)), which constrains exploration and limits discovery of globally optimal rankings. Importantly, these methods do not learn an explicit reward model; instead, they assume a predefined metric such as NDCG to serve as the counterfactual reward (Joachims et al., [2017](https://arxiv.org/html/2508.14180v2#bib.bib22); Agarwal et al., [2019](https://arxiv.org/html/2508.14180v2#bib.bib1)). While effective in certain settings, this reliance on a fixed evaluation metric can hinder adaptability to more general or task-specific reward signals.

Differential approximation to ranking.
A key challenge in learning-to-rank is the mismatch between evaluation metrics (e.g., NDCG, MAP) and surrogate loss functions amenable to gradient-based optimization, due to the non-differentiable nature of sorting operations. To address this, prior work has either proposed smooth approximations to the rank function (e.g., ApproxNDCG (Qin et al., [2010](https://arxiv.org/html/2508.14180v2#bib.bib31))) or introduced differentiable approximations to argsort using soft permutation matrices (Grover et al., [2019](https://arxiv.org/html/2508.14180v2#bib.bib14); Prillo & Eisenschlos, [2020](https://arxiv.org/html/2508.14180v2#bib.bib30)); for instance, PiRank (Swezey et al., [2021](https://arxiv.org/html/2508.14180v2#bib.bib36)) and NeuralNDCG (Pobrotyn & Białobrzeski, [2021](https://arxiv.org/html/2508.14180v2#bib.bib29)) utilize NeuralSort as a temperature-controlled surrogate. Another line of work leverages the Plackett–Luce distribution to model ranking policies in a differentiable manner (Oosterhuis, [2021](https://arxiv.org/html/2508.14180v2#bib.bib27)). Methods like PG-RANK (Gao et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib13)) use policy gradients to optimize the expected reward over the Plackett–Luce distribution based on REINFORCE, while ListNet (Cao et al., [2007](https://arxiv.org/html/2508.14180v2#bib.bib6)) and ListMLE (Xia et al., [2008](https://arxiv.org/html/2508.14180v2#bib.bib45)) employ the Plackett–Luce framework to derive smooth list-wise objectives.

## 3 Learning-To-Rank Problem: Utility Maximization vs Sorting

A data sample of an LTR problem is a *query group* (QG) consisting of a query, qq, and a set of LL items, {xℓ}ℓ=1L\{x\_{\ell}\}\_{\ell=1}^{L}, where LL may vary. The *query* may represent, for example, a search string, a user profile, or other contextual information like device type and page layout. The *items* are candidate entities like webpages, songs, or products retrieved by an upstream system. We assume that the QGs are drawn i.i.d. from a distribution 𝒫{\mathcal{P}}, i.e. (q,{xℓ})∼𝒫(q,\{x\_{\ell}\})\sim{\mathcal{P}}. When a user is presented with a ranking/arrangement (permutation), π:[L]→[L]\pi:[L]\to[L], of the items of a QG, i.e. (xπ​(1),…,xπ​(L))x\_{\pi(1)},\ldots,x\_{\pi(L)}), they interact with the ranked items, yielding a stochastic utility U​(q,{xℓ},π)∈ℝU(q,\{x\_{\ell}\},\pi)\in{\mathbb{R}}, which is a hidden function of the QG and the ranking. In typical internet systems, the utility can represent outcomes such as whether a user clicks or purchases any item, or continuous measures such as the total minutes of media consumed. Our objective is to learn a ranking policy, ff, mapping the QGs to permutations, that maximizes the expected utility return, i.e.

|  |  |  |  |
| --- | --- | --- | --- |
|  | f∗=argmaxf𝔼(q,{xℓ})∼𝒫[U(q,{xℓ},π=f(q,{xℓ})]\displaystyle f^{\*}=\operatorname\*{argmax}\_{f}\mathbb{E}\_{(q,\{x\_{\ell}\})\sim{\mathcal{P}}}[U(q,\{x\_{\ell}\},\pi=f(q,\{x\_{\ell}\})] |  | (1) |

Based on the choice of the utility, this objective corresponds to business metrics like click-through rate, units sold, or streamed minutes.
The main challenge here is that the hidden stochastic utility function UU is not directly observable. Instead we are given a training dataset, 𝒟{\mathcal{D}}, consisting of NN QGs (indexed by ii) and their observed utility {ui}\{u\_{i}\} under some logged rankings {πi}\{\pi\_{i}\}, i.e. 𝒟={(qi,{xi,ℓ}ℓ=1Li,πi,ui)}i∈[N]{\mathcal{D}}=\{(q\_{i},\{x\_{i,\ell}\}\_{\ell=1}^{L\_{i}},\pi\_{i},u\_{i})\}\_{i\in[N]}. We assume that similar hold-out test and validation dataset are also available.
This setting can be viewed as an offline one-step reinforcement-learning problem in which the state space is comprised of all possible QGs in the support of 𝒫{\mathcal{P}}, the action space is comprised of all item permutations, and the reward is the observed utility.

In practice, most QGs are unique, so we observe only one out of L!L! possible rankings for each. Consequently, even if we propose a better alternative ranking for a given QG, the *counterfactual* utility it would have obtained remains unknown.
To address this, traditional LTR algorithms optimize heuristic offline ranking metrics like Normalized Discounted Cumulative Gain (NDCG)
(Järvelin & Kekäläinen, [2002](https://arxiv.org/html/2508.14180v2#bib.bib19); Burges, [2006](https://arxiv.org/html/2508.14180v2#bib.bib3)), averaged over a test set. When a user interacts with a ranked QG, we also obtain per-item feedback signals {yℓ≥0}\{y\_{\ell}\geq 0\} (e.g. whether an item was clicked or purchase, or how many minutes it was streamed). Usually, the overall QG-level utility uu is some function of these per-item signals. Then, the NDCG of any new ranking π^\widehat{\pi}, on a QG with feedbacks {yℓ}\{y\_{\ell}\} can be defined as

|  |  |  |  |
| --- | --- | --- | --- |
|  | NDCG​(π^,{yℓ})=△DCG​(π^,{yℓ})DCG​(π∗,{yℓ})∈[0,1], where ​DCG​(r,{yℓ})=△∑ℓ=1L2yℓ−1log2⁡(1+r−1​(ℓ)).\displaystyle\mathrm{NDCG}(\widehat{\pi},\{y\_{\ell}\})\mathrel{\overset{\triangle}{=}}\frac{\mathrm{DCG}(\widehat{\pi},\{y\_{\ell}\})}{\mathrm{DCG}(\pi^{\*},\{y\_{\ell}\})}\in[0,1]\,,\textrm{ where }\mathrm{DCG}(r,\{y\_{\ell}\})\mathrel{\overset{\triangle}{=}}\sum\_{\ell=1}^{L}\frac{2^{y\_{\ell}}-1}{\log\_{2}(1+r^{-1}(\ell))}\,. |  | (2) |

DCG assigns a gain 2yℓ−12^{y\_{\ell}}-1 for the item xℓx\_{\ell} in a test QG, but its contribution to the metric is discounted by its position r−1​(ℓ)r^{-1}(\ell) under the ranking rr. Thus, NDCG is maximized when the items are ranked in the descending order of their feedback values, i.e., under the optimal ranking π∗\pi^{\*}. Traditional LTR methods (Burges, [2006](https://arxiv.org/html/2508.14180v2#bib.bib3); Swezey et al., [2021](https://arxiv.org/html/2508.14180v2#bib.bib36)), aim to maximize NDCG by optimizing various continuous relaxations of it.
This heuristic of learning to move items with higher feedback signal to the top of list have been highly successful, potentially because (i) items with positive feedback are usually relevant, and (ii) users tend to focus their attention on the top of the list. However, such offline metrics are now well-known to be sub-optimal as they do not perfectly align with the true (hidden) utility ([1](https://arxiv.org/html/2508.14180v2#S3.E1 "In 3 Learning-To-Rank Problem: Utility Maximization vs Sorting ‣ RewardRank: Optimizing True Learning-to-Rank Utility")) we aim to maximize (Wang et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib41); Jeunen et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib20)). A key advantage of RewardRank over traditional LTR methods is its ability to *leverage data without click/purchase labels*. Whereas standard pipelines often discard sessions with no purchases/clicks (or treat them as uninformative negatives), our approach can still extract signal from these interactions via its utility modeling and preference estimation. This aligns with recent evidence that leveraging unlabeled or weakly labeled interaction data—e.g., through pretraining or preference modeling—improves ranking quality (Hou et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib18)). In the next section, we introduce RewardRank, a data-driven ranking framework that directly maximizes the true LTR utility without relying on heuristics or specific user-behavior assumptions.

## 4 RewardRank: Data-driven LTR Utility Maximization

In this section, we present the RewardRank framework, which aims to maximize the true (hidden) LTR utility defined in ([2](https://arxiv.org/html/2508.14180v2#S3.E2 "In 3 Learning-To-Rank Problem: Utility Maximization vs Sorting ‣ RewardRank: Optimizing True Learning-to-Rank Utility")). At a high level, RewardRank proceeds in two stages. First, using the logged training data 𝒟{\mathcal{D}}, it learns a reward model that predicts the counterfactual utility for any QG and permutation. Then it trains a ranker using the reward model’s predictions as supervision, so as to maximize the expected counterfactual LTR utility of the ranker’s item arrangement (ranking) policy.

### 4.1 Stage 1: Learning the Utility Using a Reward Model

Let g​(q,{xℓ},π;ϕ)g(q,\{x\_{\ell}\},\pi;\phi) denote the reward model (parameterized with ϕ\phi) to predict the scalar utility for the QG (q,{xℓ})(q,\{x\_{\ell}\}) and a ranking π\pi. It is trained solely on the logged query groups, rankings and observed utilities in the training dataset 𝒟{\mathcal{D}}. When the utility U∈{0,1}U\in\{0,1\} is a binary random variable (e.g. click, purchase), we train g∈[0,1]g\in[0,1] by minimizing the average binary cross-entropy loss between the observed uiu\_{i} and the predicted utilities u^i​(ϕ):=g​(qi,{xi​ℓ},πi;ϕ)\widehat{u}\_{i}(\phi):=g(q\_{i},\{x\_{i\ell}\},\pi\_{i};\phi) over all i∈[N]i\in[N]:

|  |  |  |  |
| --- | --- | --- | --- |
|  | minϕ⁡[RewardLoss​(ϕ)=△−1N​∑i=1N[ui​log⁡(u^​(ϕ))+(1−ui)​log⁡(1−u^​(ϕ))]].\displaystyle\min\_{\phi}\bigg[\textrm{RewardLoss}(\phi)\mathrel{\overset{\triangle}{=}}-\frac{1}{N}\sum\_{i=1}^{N}[u\_{i}\log(\widehat{u}(\phi))+(1-u\_{i})\log(1-\widehat{u}(\phi))]\bigg]\,. |  | (3) |

When the true utility is a continuous random variable (e.g. minutes a song is streamed) we can use regression losses such mean squared error (MSE) minϕ⁡(1/N)​∑i=1N‖ui−u^i​(ϕ)‖2\min\_{\phi}(1/N)\sum\_{i=1}^{N}\|u\_{i}-\widehat{u}\_{i}(\phi)\|^{2}.
In our experiments, the reward model is instantiated with a transformer encoder, Enc, due to its ability to model functions over sequences (ranked list of items). Before passing a QG into Enc each query-item pair [q,xℓ][q,x\_{\ell}] is embedded using a text encoder to create the token embedding 𝐞ℓ\mathbf{e}\_{\ell}. Next, the ranking of the items π\pi is encoded through position encodings {𝐩k}\{\mathbf{p}\_{k}\}. Then the position encoded tokens are passed to the transformer Enc. Finally, the predicted utility is computed as the sigmoid of a linear function of the [CLS] token output. This can be succinctly represented as:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | g​(q,{xℓ}ℓ=1L,π;ϕ)\displaystyle g(q,\{x\_{\ell}\}\_{\ell=1}^{L},\pi;\phi) | =σ​[𝐯⊤​Encreward[CLS]​({𝐞π​(k)+𝐩k}k=1L)],\displaystyle=\sigma\bigg[\mathbf{v}^{\top}\texttt{Enc}\_{\text{reward}}^{\texttt{[CLS]}}\left(\left\{\mathbf{e}\_{\pi(k)}+\mathbf{p}\_{k}\right\}\_{k=1}^{L}\right)\bigg]\,, |  | (4) |

where 𝐞π​(k)\mathbf{e}\_{\pi(k)} is the token embedding of the query and the kk-th ranked item. During the second stage of training the ranker, we freeze the reward model parameters ϕ\phi.

![Refer to caption](fig/main_final.png)

Auxiliary per-item predictor: Typically the observed utility uu is a byproduct of user’s interaction with the items. So, we hypothesize that predicting the per-item feedback signals {yℓ}\{y\_{\ell}\} as an auxiliary task would improve the overall quality of the LTR utility prediction. Thus we include an auxiliary prediction head on the item tokens’ outputs to predict the feedback signal observed at each ranked position k∈[L]k\in[L]. When yℓ∈{0,1}y\_{\ell}\in\{0,1\} is binary, the predictions can be instantiated as

|  |  |  |  |
| --- | --- | --- | --- |
|  | y^k​(ϕ)=△σ​[𝐯~⊤​Encreward(k)​({𝐞π​(k)+𝐩k}k=1L)],∀k∈[L],\displaystyle\widehat{y}\_{k}(\phi)\mathrel{\overset{\triangle}{=}}\sigma\Big[\mathbf{\widetilde{v}}^{\top}\texttt{Enc}\_{\text{reward}}^{(k)}\left(\left\{\mathbf{e}\_{\pi(k)}+\mathbf{p}\_{k}\right\}\_{k=1}^{L}\right)\Big]\,,\;\;\;\forall\,k\in[L]\,, |  | (5) |

where Encreward(k)\texttt{Enc}\_{\text{reward}}^{(k)} is the output token at the kk-th position and σ\sigma is the sigmoid function. We can learn y^k​(ϕ)\widehat{y}\_{k}(\phi) alongside u^​(ϕ)\widehat{u}(\phi) by adding the average cross-entropy loss between y^k\widehat{y}\_{k} and yπ​(k){y}\_{\pi(k)},

|  |  |  |  |
| --- | --- | --- | --- |
|  | ItemLoss​(ϕ)=△−1∑iLi​∑i=1N∑k=1Li[yi​π​(k)​log⁡(y^i​k​(ϕ))+(1−yi​π​(k))​log⁡(1−y^i​k​(ϕ))].\displaystyle\textrm{ItemLoss}(\phi)\mathrel{\overset{\triangle}{=}}-\frac{1}{\sum\_{i}L\_{i}}\sum\_{i=1}^{N}\sum\_{k=1}^{L\_{i}}[y\_{i\pi(k)}\log(\widehat{y}\_{ik}(\phi))+(1-y\_{i\pi(k)})\log(1-\widehat{y}\_{ik}(\phi))]\,. |  | (6) |

as an additional regularizer to RewardLoss\mathrm{RewardLoss} ([3](https://arxiv.org/html/2508.14180v2#S4.E3 "In 4.1 Stage 1: Learning the Utility Using a Reward Model ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility")). Note that during the training of the ranker in the next stage, these auxiliary predictions can be discarded. Our ablation in Section [5.1](https://arxiv.org/html/2508.14180v2#S5.SS1 "5.1 Large-Scale Reproducible Testbenches for Counterfactual LTR ‣ 5 Experimental Results ‣ RewardRank: Optimizing True Learning-to-Rank Utility") shows that the per-item loss provides a moderate boost in performance. We also apply the per-item loss to query groups (QGs) with no purchases (i.e., no positive labels). This enables us to exploit otherwise discarded sessions and stabilize learning in sparse-feedback regimes by providing item-level signals even when list-level purchase supervision is absent.

### 4.2 Stage 2: Ranker Reward Maximization through Soft Sorting

Typically, rankers are modeled as scoring functions that assign a score to each item in a QG. Then the items are ordered in the descending order of their scores to obtain the final ranking. We follow the same pattern and define f​(q,{xℓ};θ)f(q,\{x\_{\ell}\};\theta) as a scoring-based ranker which maps a QG (q,{xℓ})(q,\{x\_{\ell}\}) to a set of item scores {sℓ}\{s\_{\ell}\}. Following our reward model design, we instantiate ff using the same transformer backbone architecture. Since QG has an unordered set of items, we do not use position encoding. Finally the score is computed as the linear function of the output item tokens, i.e.

|  |  |  |  |
| --- | --- | --- | --- |
|  | sℓ=△fℓ​(q,{xℓ};θ)=△𝐰⊤​Encranker(ℓ)​({𝐞ℓ}ℓ=1L),∀ℓ∈[L],\displaystyle s\_{\ell}\mathrel{\overset{\triangle}{=}}f\_{\ell}(q,\{x\_{\ell}\};\theta)\mathrel{\overset{\triangle}{=}}\mathbf{w}^{\top}\text{Enc}\_{\text{ranker}}^{(\ell)}\left(\left\{\mathbf{e}\_{\ell}\right\}\_{\ell=1}^{L}\right)\,,\;\;\forall\ell\in[L]\,, |  | (7) |

where Encranker(ℓ)\text{Enc}\_{\text{ranker}}^{(\ell)} is the output token of the ℓ\ell-th item.
Our goal is to optimize the effective ranking π^\widehat{\pi} induced by these scores so that it maximizes the expected counterfactual utility, which is a hidden from us. This is where the reward model comes in handy, as it helps us predict the counterfactual utility as u^:=g​(q,{xℓ},π^)\widehat{u}:=g(q,\{x\_{\ell}\},\widehat{\pi}).
However, since sorting (of the scores) is a discontinuous operation, it is challenging to optimize the scores to maximize the reward.
To enable an end-to-end optimization of the scorer ff, we resort to a continuous relaxation of the sorting operation.

##### Soft Permutation via SoftSort.

*SoftSort* (Prillo & Eisenschlos, [2020](https://arxiv.org/html/2508.14180v2#bib.bib30)) is a continuous relaxation of sorting operation. It defines a *unimodal row-stochastic* matrix (Swezey et al., [2021](https://arxiv.org/html/2508.14180v2#bib.bib36)) as the *soft* permutation matrix Π^(τ)∈[0,1]L×L\widehat{\Pi}^{(\tau)}\in[0,1]^{L\times L}. Row kk of this matrix corresponds to a probability distribution of the kk-the ranked item over the set of all items. Formally, we define

|  |  |  |  |
| --- | --- | --- | --- |
|  | Π^k,ℓ(τ)=△exp⁡(−1τ​|sℓ−sπ^​(k)|)∑ℓ′=1Lexp⁡(−1τ​|sℓ′−sπ^​(k)|),∀k,ℓ∈[L],\displaystyle\widehat{\Pi}^{(\tau)}\_{k,\ell}\mathrel{\overset{\triangle}{=}}\frac{\exp\left(-\frac{1}{\tau}\left|s\_{\ell}-s\_{\widehat{\pi}(k)}\right|\right)}{\sum\_{\ell^{\prime}=1}^{L}\exp\left(-\frac{1}{\tau}\left|s\_{\ell^{\prime}}-s\_{\widehat{\pi}(k)}\right|\right)}\,,\;\;\forall\,k,\ell\in[L]\,, |  | (8) |

where τ\tau is a temperature parameter and π^​(k)\widehat{\pi}(k) is the kk-th ranked items when (hard) sorting by the scores {sℓ}\{s\_{\ell}\}.
Π^(τ)\widehat{\Pi}^{(\tau)} is a continuous function of the scores {sℓ}\{s\_{\ell}\} and when τ→0\tau\to 0, Π^(τ)\widehat{\Pi}^{(\tau)} tends to the binary hard-permutation matrix Π^\widehat{\Pi}, where

|  |  |  |  |
| --- | --- | --- | --- |
|  | limτ→0Π^k,ℓ(τ)=Π^k,ℓ=△𝕀​{π^​(k)=ℓ},∀k,ℓ∈[L],\displaystyle\lim\_{\tau\to 0}\widehat{\Pi}^{(\tau)}\_{k,\ell}=\widehat{\Pi}\_{k,\ell}\mathrel{\overset{\triangle}{=}}\mathbb{I}\{\widehat{\pi}(k)=\ell\}\,,\;\;\forall\,k,\ell\in[L]\,, |  | (9) |

assuming the scores are unique.
Using this soft permutation matrix, we can compute a soft item embedding e^k(τ)\widehat{e}^{(\tau)}\_{k} at position kk as the following convex combination of the true item embeddings

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝐞^k(τ)=△∑ℓ∈[L]Π^k,ℓ(τ)​𝐞ℓ.\displaystyle\widehat{\mathbf{e}}\_{k}^{(\tau)}\mathrel{\overset{\triangle}{=}}\sum\_{\ell\in[L]}\widehat{\Pi}^{(\tau)}\_{k,\ell}\mathbf{e}\_{\ell}\,. |  | (10) |

It is easy to verify that 𝐞^k(τ)→𝐞π^​(k)\widehat{\mathbf{e}}\_{k}^{(\tau)}\to\mathbf{e}\_{\widehat{\pi}(k)} when τ→0\tau\to 0. Note that there are alternate soft permutation matrices like NeuralSort (Grover et al., [2019](https://arxiv.org/html/2508.14180v2#bib.bib14)), but we adopt SoftSort for its simplicity and state of the art performance (Prillo & Eisenschlos, [2020](https://arxiv.org/html/2508.14180v2#bib.bib30)). We then compute a soft reward for these soft item embeddings using

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | g^​(θ)=△g​(q,{xℓ},Π^(τ))\displaystyle\widehat{g}(\theta)\mathrel{\overset{\triangle}{=}}g(q,\{x\_{\ell}\},\widehat{\Pi}^{(\tau)}) | =△σ​[𝐯⊤​Encreward[CLS]​({𝐞^k(τ)+𝐩k}k=1L)],\displaystyle\mathrel{\overset{\triangle}{=}}\sigma\bigg[\mathbf{v}^{\top}\texttt{Enc}\_{\text{reward}}^{\texttt{[CLS]}}\left(\left\{\widehat{\mathbf{e}}^{(\tau)}\_{k}+\mathbf{p}\_{k}\right\}\_{k=1}^{L}\right)\bigg]\,, |  | (11) |

This allows us to compute an approximate predicted reward ([11](https://arxiv.org/html/2508.14180v2#S4.E11 "In Soft Permutation via SoftSort. ‣ 4.2 Stage 2: Ranker Reward Maximization through Soft Sorting ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility")) as a continuous function over the ranker scores {sℓ}\{s\_{\ell}\} through the SoftSort matrix. Finally, we optimize the parameters of scorer ff to maximize the average approximate reward over the training set in an end-to-end manner:

|  |  |  |  |
| --- | --- | --- | --- |
|  | minθ⁡[RankerLoss​(θ)=△−1N​∑i=1Ng^i​(θ)].\displaystyle\min\_{\theta}\bigg[\mathrm{RankerLoss}(\theta)\mathrel{\overset{\triangle}{=}}-\frac{1}{N}\sum\_{i=1}^{N}\widehat{g}\_{i}(\theta)\bigg]\,. |  | (12) |

Even though RewardRank is maximizing the predicted utility of the soft ranking, we hypothesize that it generalizes well and produces rankings with higher expected counterfactual utility than prior LTR methods.

An alternative to soft-permutation matrices is the Plackett–Luce (PL) model, which offers efficient, closed-form gradients for ranking. However, counterfactual learning with PL requires Monte Carlo sampling, leading to high-variance estimates in large action spaces. While variance reduction helps (Gao et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib13)), unbiased learning fundamentally depends on stochastic logging, which is incompatible with real-world deterministic rankers designed for stability and trust. Soft permutation relaxations like SoftSort (Prillo & Eisenschlos, [2020](https://arxiv.org/html/2508.14180v2#bib.bib30)) approximate permutations in continuous space, enabling gradient-based optimization without sampling. Though computationally more expensive, they reduce variance and support end-to-end utility maximization. We pair SoftSort with a learned reward model that generalizes over logged data, enabling scalable training under deterministic logs. This approach trades unbiasedness for stability and practicality in real-world ranking systems.

##### Mitigating reward misspecification.

One challenge of reward modeling the hidden counterfactual utility is model misspecification, i.e. a gap between the predicted and the true utilities. A misspecified reward can misguide the ranker into wrong ranking policies Coste et al. ([2023](https://arxiv.org/html/2508.14180v2#bib.bib9)); Clark & Amodei ([2016](https://arxiv.org/html/2508.14180v2#bib.bib8)). To mitigate this issue we propose a sample reweighting scheme which modifies the ranker loss as

|  |  |  |  |
| --- | --- | --- | --- |
|  | RankerLoss(λ)​(θ)=△−1N​∑i=1Nwi⋅g^i​(θ), where ​wi=1−λ​|ui−u^i|∈[0,1]​ and ​λ∈[0,1],∀i.\displaystyle\mathrm{RankerLoss}^{(\lambda)}(\theta)\mathrel{\overset{\triangle}{=}}-\frac{1}{N}\sum\_{i=1}^{N}w\_{i}\cdot\widehat{g}\_{i}(\theta)\,,\textrm{ where }w\_{i}=1-\lambda|u\_{i}-\widehat{u}\_{i}|\in[0,1]\text{ and }\lambda\in[0,1]\,,\;\;\forall\,i\,. |  | (13) |

Above loss is a pessimistic upperbound to RankerLoss​(θ)\mathrm{RankerLoss}(\theta) ([12](https://arxiv.org/html/2508.14180v2#S4.E12 "In Soft Permutation via SoftSort. ‣ 4.2 Stage 2: Ranker Reward Maximization through Soft Sorting ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility")). This reward down-weighting scheme is motivated by a conjecture that when the observed utility uiu\_{i} for the ii-th training QG and the corresponding prediction u^i​(θ)\widehat{u}\_{i}(\theta) are different, the utility prediction on new ranking of this QG would also be less reliable. Through an ablation in Section [5.1](https://arxiv.org/html/2508.14180v2#S5.SS1 "5.1 Large-Scale Reproducible Testbenches for Counterfactual LTR ‣ 5 Experimental Results ‣ RewardRank: Optimizing True Learning-to-Rank Utility") we show that reward misspecification correction slightly improves the RewardRank performance.

## 5 Experimental Results

Datasets. Public large-scale datasets for learning-to-rank (LTR), especially in counterfactual settings, are scarce. To the best of our knowledge, we propose the first reproducible testbeds for counterfactual ranking evaluation. We utilize two existing large-scale LTR datasets: Baidu-ULTR (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17); Zou et al., [2022](https://arxiv.org/html/2508.14180v2#bib.bib46)) and Amazon KDD-Cup (Reddy et al., [2022](https://arxiv.org/html/2508.14180v2#bib.bib33)), to construct these testbenches, enabling rigorous evaluation of permutation-aware ranking policies.
Baidu-ULTR contains 1.8M query groups (11.7M query-document pairs) and 590K validation/test sessions. Amazon KDD-Cup comprises 130K queries and 2.6M annotated query-product pairs with rich textual metadata. We generate 400K training and 50K validation/test query groups by sampling permutations of products per query. See Appendix [B.1](https://arxiv.org/html/2508.14180v2#A2.SS1 "B.1 Datasets ‣ Appendix B Experimentation details ‣ RewardRank: Optimizing True Learning-to-Rank Utility") for further details.

##### Implementation Details and Baselines.

Our reward models and rankers are based on a transformer architecture with 12 layers, 768 hidden dimensions, 12 attention heads, and roughly 110M parameters. We set τ=0.5\tau=0.5 and λ=0.7\lambda=0.7 for all RewardRank experiments, based on tuning over a held-out set. Ablations with varying values and further implementation details are provided in Appendix [B.2](https://arxiv.org/html/2508.14180v2#A2.SS2 "B.2 Implementation details ‣ Appendix B Experimentation details ‣ RewardRank: Optimizing True Learning-to-Rank Utility").
For comparison, we implement two utility-based counterfactual ranking methods: URCC (Xi et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib44)), which uses a LambdaLoss-based pairwise objective, and PG-rank (Gao et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib13)), which applies Plackett–Luce modeling with policy gradients. Our variants, URCC∗ and PG-rank∗, replace their offline metric utility (e.g. NDCG) with our transformer-based reward model for improved counterfactual performance.
Additionally, we train standard LTR baselines: ListNet (Cao et al., [2007](https://arxiv.org/html/2508.14180v2#bib.bib6)), ListMLE (Xia et al., [2008](https://arxiv.org/html/2508.14180v2#bib.bib45)), LambdaRank (Wang et al., [2018](https://arxiv.org/html/2508.14180v2#bib.bib42)), and PiRank (Swezey et al., [2021](https://arxiv.org/html/2508.14180v2#bib.bib36)), all using the same transformer architecture for fair comparison across supervision methods.

### 5.1 Large-Scale Reproducible Testbenches for Counterfactual LTR

To enable reproducible evaluation of ranking policies without online A/B testing, we introduce two complementary testbeds: PO-Eval, which leverages a parametric click model, and LAU-Eval, which simulates human-like shopping behavior via LLM reasoning. Together, they enable holistic, counterfactual assessment of ranking algorithms under both statistical and behavioral lenses.

##### Parametric Oracle Evaluation (PO-Eval).

To simulate a click-based counterfactual recommendation setting, we build a testbed from the Baidu-ULTR dataset (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)), employing a *pretrained parametric IPS model* as the oracle for supervision. This model estimates the click probability at position ℓ\ell as P​(C)=P​(Eℓ)⋅P​(Rq,i)P(C)=P(E\_{\ell})\cdot P(R\_{q,i}), where P​(Eℓ)P(E\_{\ell}) is the position-dependent examination probability and P​(Rq,i)P(R\_{q,i}) is the click probability given examination We use this oracle to sample binary clicks for training and later reuse it for counterfactual evaluation of new ranking policies. For each ranked query group (QG), we compute the expected utility as the probability of at least one click and the observed utility as a binary indicator of at least one sampled click. This setup provides a realistic and repeatable framework for evaluating how well learned rankers align with user behavior modeled by the IPS-oracle. See Appendix [A.1](https://arxiv.org/html/2508.14180v2#A1.SS1 "A.1 Click-based Utility for PO-Eval. ‣ Appendix A Proofs and conceptual details ‣ RewardRank: Optimizing True Learning-to-Rank Utility") for details on the parametric model and the derivation of utility metrics.

Table [7](https://arxiv.org/html/2508.14180v2#A3.T7 "Table 7 ‣ Ranking Evaluations. ‣ C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility") reports counterfactual evaluation results using PO-Eval, where we leverage a pre-trained parametric IPS-Oracle to simulate user clicks and assess ranking quality. The IPS-based utility P​r​(#​C​l​i​c​k​s≥1)Pr(\#Clicks\geq 1) captures the expected probability of at least one click per ranked list, while NDCGclick\text{NDCG}\_{\text{click}} measures how high are the originally clicked items in the test dataset ranked. The Upper-Bound is computed by ranking items in descending order of P​(R)P(R), which maximizes utility due to the rearrangement inequality (Day, [1972](https://arxiv.org/html/2508.14180v2#bib.bib10)) (see Appendix [A](https://arxiv.org/html/2508.14180v2#A1 "Appendix A Proofs and conceptual details ‣ RewardRank: Optimizing True Learning-to-Rank Utility")). Traditional LTR baselines (ListNet, ListMLE, LambdaRank, PiRank), trained with per-item IPS–sampled clicks, achieve strong offline/surrogate metrics under Eq. [2](https://arxiv.org/html/2508.14180v2#S3.E2 "In 3 Learning-To-Rank Problem: Utility Maximization vs Sorting ‣ RewardRank: Optimizing True Learning-to-Rank Utility") (e.g., N​D​C​GclickNDCG\_{\text{click}}) but fail to capture the true user utility in Eq. [1](https://arxiv.org/html/2508.14180v2#S3.E1 "In 3 Learning-To-Rank Problem: Utility Maximization vs Sorting ‣ RewardRank: Optimizing True Learning-to-Rank Utility") (e.g., Pr⁡(#​Clicks≥1)\Pr(\#\text{Clicks}\geq 1)).
URCC∗ yields the lowest performance, as it relies heavily on a strong *pretrained* ranker to initialize its search; without such initialization, its effectiveness diminishes significantly (see Appendix [D](https://arxiv.org/html/2508.14180v2#A4 "Appendix D Further ablation studies ‣ RewardRank: Optimizing True Learning-to-Rank Utility")). In particular, URCC∗ explores only the neighborhood of the current permutations via pairwise position swaps, which (i) induces quadratic complexity and (ii) leads to *pessimistic* exploration that can miss superior rankings outside this local region. In contrast, RewardRank does not require any pretrained ranker and performs counterfactual optimization directly, enabling broader exploration beyond the data rankings from logged data.
For PG-Rank\*, we observe that increasing the number of Monte Carlo samples (MC = 1, 5, 10) reduces variance in its estimates, which improves performance, albeit at the cost of longer training time (see Appendix Section [A.3](https://arxiv.org/html/2508.14180v2#A1.SS3 "A.3 Details of baselines ‣ Appendix A Proofs and conceptual details ‣ RewardRank: Optimizing True Learning-to-Rank Utility") for details). In contrast RewardRank attains the highest utility under IPS-Oracle, despite slightly lower NDCGclick\text{NDCG}\_{\mathrm{click}} than some baselines. This reflects a key distinction: proxy metrics, such as NDCG (Eqn. [2](https://arxiv.org/html/2508.14180v2#S3.E2 "In 3 Learning-To-Rank Problem: Utility Maximization vs Sorting ‣ RewardRank: Optimizing True Learning-to-Rank Utility")), may not fully align with the true user utility (Eqn. [1](https://arxiv.org/html/2508.14180v2#S3.E1 "In 3 Learning-To-Rank Problem: Utility Maximization vs Sorting ‣ RewardRank: Optimizing True Learning-to-Rank Utility")). By directly optimizing counterfactual reward, RewardRank better aligns with behavioral objectives beyond conventional ranking accuracy.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | PO-Eval | | LAU-Eval | |
|  | *Counterfactual ( ✓)* | *Offline ( ✗)* | *Counterfactual ( ✓)* | *Offline ( ✗)* |
| Method | Pr​(#​Clicks≥1)\mathrm{Pr}(\#\mathrm{Clicks}\geq 1) | NDCGclick\text{NDCG}\_{\mathrm{click}} | Pr​(#​Purchases≥1)\mathrm{Pr}(\#\mathrm{Purchases}\geq 1) | NDCGpurchase\text{NDCG}\_{\mathrm{purchase}} |
| Upper-Bound | 0.553 ±\pm 0.0007 | – | – | – |
| Policy in data | 0.475 ±\pm 0.0004 | 0.211 ±\pm 0.0003 | 0.497 ±\pm 0.009 | 0.496 ±\pm 0.009 |
| ListNet (Cao et al., [2007](https://arxiv.org/html/2508.14180v2#bib.bib6)) | 0.523 ±\pm 0.0007 | 0.376 ±\pm 0.0002 | 0.521 ±\pm 0.009 | 0.405 ±\pm 0.009 |
| ListMLE (Xia et al., [2008](https://arxiv.org/html/2508.14180v2#bib.bib45)) | 0.522 ±\pm 0.0007 | 0.377 ±\pm 0.0002 | 0.522 ±\pm 0.008 | 0.402 ±\pm 0.008 |
| LambdaRank (Wang et al., [2018](https://arxiv.org/html/2508.14180v2#bib.bib42)) | 0.524 ±\pm 0.0007 | 0.378 ±\pm 0.0002 | 0.523 ±\pm 0.009 | 0.406 ±\pm 0.009 |
| PiRank (Swezey et al., [2021](https://arxiv.org/html/2508.14180v2#bib.bib36)) | 0.525 ±\pm 0.0007 | 0.378 ±\pm 0.0002 | 0.528 ±\pm 0.007 | 0.408 ±\pm 0.009 |
| URCC∗ (Xi et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib44)) | 0.462 ±\pm 0.0005 | 0.315 ±\pm 0.0004 | 0.471 ±\pm 0.008 | 0.401 ±\pm 0.007 |
| PG-rank∗ (Gao et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib13)) | 0.501 ±\pm 0.0005 | 0.327 ±\pm 0.0002 | 0.489 ±\pm 0.007 | 0.402 ±\pm 0.008 |
| RewardRank | 0.536 ±\pm 0.0007 | 0.370 ±\pm 0.0002 | 0.561 ±\pm 0.008 | 0.401 ±\pm 0.007 |

##### LLM-based User Simulation (LAU-Eval).

While PO-Eval captures position bias via IPS-Oracle supervision, it does not account for broader behavioral patterns such as brand bias, similarity aversion, or irrelevance bias. To complement PO-Eval and more fully assess human-centered ranking behavior, we introduce the LAU-Eval framework. In this setup, a large language model (LLM) is prompted to simulate user shopping behavior given a query and its associated product list from the Amazon KDD-Cup dataset. The prompt incorporates behavioral factors such as position bias, brand bias, irrelevance bias, and color bias (full details are provided in Appendix [C.2](https://arxiv.org/html/2508.14180v2#A3.SS2 "C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility")). The LLM generates a binary purchase decision D​(purchase)∈{0,1}D(\text{purchase})\in\{0,1\}, which serves as the reward signal for training a reward model and optimizing rankers. For evaluation, the same prompt is used: each ranker’s ranked item list is assesed by the LLM, and performance is reported as the average purchase decision rate on a held-out test set. For LTR methods that do not rely on reward modeling, we instead use the per-item binary LLM-purchase decision as the training signal. Higher values indicate stronger alignment with human-centered behavioral criteria. Refer to the Appendix Section [C.2](https://arxiv.org/html/2508.14180v2#A3.SS2 "C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility") for implementation details.

Under LAU-Eval, which measures binary purchase decisions made by the LLM, we observe clear differences across methods. The policy\_in\_data baseline (original item order) attains an average purchase rate of 0.4970.497. Classical listwise approaches—ListNet, ListMLE, LambdaRank, and PiRank—yield only modest gains on the true utility Pr⁡(#​Purchase≥1)\Pr(\#\text{Purchase}\!\geq\!1), reaching 0.5000.500–0.5130.513, while achieving very high scores on the offline/surrogate utility (NDCGpurchase)(\mathrm{NDCG}\_{\text{purchase}}). These LTR methods largely succeed by moving the purchased item to the top, which inflates surrogate metrics but does not faithfully capture true preferences under the LLM-Oracle, such as brand or color bias among the items, and therefore does not consistently increase purchases. This underscores the need to optimize *counterfactual utility* as the primary metric for modeling human ranking behavior. We also observe a clear mismatch between surrogate and counterfactual objectives for counterfactual baselines: both PG-rank∗ and URCC∗ attain a strong NDCGpurchase\mathrm{NDCG}\_{\text{purchase}} (formulated by Eqn [2](https://arxiv.org/html/2508.14180v2#S3.E2 "In 3 Learning-To-Rank Problem: Utility Maximization vs Sorting ‣ RewardRank: Optimizing True Learning-to-Rank Utility")), yet *both* methods yield lower values on the counterfactual metric (purchase rate as formulated by Eqn [1](https://arxiv.org/html/2508.14180v2#S3.E1 "In 3 Learning-To-Rank Problem: Utility Maximization vs Sorting ‣ RewardRank: Optimizing True Learning-to-Rank Utility")). This indicates that optimizing the ranking-aware surrogate alone can overfit to list reshuffling (e.g., moving a known purchased item to the top) without improving the actual decision outcome measured by Pr⁡(#​Purchase≥1)\Pr(\#\text{Purchase}\!\geq\!1).

![Refer to caption](fig/misspec.png)

##### Ablations.

We ablate the per-item regularizer and the two parameters of RewardRank: the SoftSort temperature τ\tau, which controls the sharpness of the permutation approximation ([8](https://arxiv.org/html/2508.14180v2#S4.E8 "In Soft Permutation via SoftSort. ‣ 4.2 Stage 2: Ranker Reward Maximization through Soft Sorting ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility")), and the misspecification correction strength λ\lambda, which down-weights rewards on QGs with high prediction error ([13](https://arxiv.org/html/2508.14180v2#S4.E13 "In Mitigating reward misspecification. ‣ 4.2 Stage 2: Ranker Reward Maximization through Soft Sorting ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility")).
Removing the auxiliary item-level reward loss (Eqn [6](https://arxiv.org/html/2508.14180v2#S4.E6 "In 4.1 Stage 1: Learning the Utility Using a Reward Model ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility")) decreased the final expected counterfactual utility of the learned ranker. This indicates that learning to predict the per-item feedback enhances the reward model’s generalization and hence improves downstream ranking performance. As shown in Figure [3](https://arxiv.org/html/2508.14180v2#S5.F3 "Figure 3 ‣ LLM-based User Simulation (LAU-Eval). ‣ 5.1 Large-Scale Reproducible Testbenches for Counterfactual LTR ‣ 5 Experimental Results ‣ RewardRank: Optimizing True Learning-to-Rank Utility"), increasing λ\lambda progressively reduces the influence of unreliable reward estimates by lowering their instance weights, leading to more stable learning. As λ\lambda increases, the influence of low-confidence predictions (lower ww) diminishes, effectively down-weighting misspecified instances. This correction improves stability by emphasizing samples with well-aligned predicted rewards. For illustration, we display soft utility scores from Eqn [17](https://arxiv.org/html/2508.14180v2#A1.E17 "In A.1 Click-based Utility for PO-Eval. ‣ Appendix A Proofs and conceptual details ‣ RewardRank: Optimizing True Learning-to-Rank Utility"); however, all experiments use binary utility signals as defined in Eqn [16](https://arxiv.org/html/2508.14180v2#A1.E16 "In A.1 Click-based Utility for PO-Eval. ‣ Appendix A Proofs and conceptual details ‣ RewardRank: Optimizing True Learning-to-Rank Utility").
We find that τ=0.5\tau=0.5 and λ=0.7\lambda=0.7 achieve the best trade-off between stability and performance. Full details of these ablations are reported in Appendix [D](https://arxiv.org/html/2508.14180v2#A4 "Appendix D Further ablation studies ‣ RewardRank: Optimizing True Learning-to-Rank Utility").

### 5.2 Baidu-ULTR Dataset with Real User Clicks

While we previously used the Baidu-ULTR dataset within the PO-Eval framework under IPS-Oracle supervision, here we instead rely directly on the real click signals provided in the data.

| Method | D​C​Grel​@​5DCG\_{\mathrm{rel}}@5 | D​C​Grel​@​10DCG\_{\mathrm{rel}}@10 |
| --- | --- | --- |
| Point IPS† (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)) | 4.79 | 7.43 |
| List IPS† (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)) | 5.20 | 7.88 |
| LambdaRank† (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)) | 5.45 | 8.23 |
| ListNet (Cao et al., [2007](https://arxiv.org/html/2508.14180v2#bib.bib6)) | 5.05 | 7.64 |
| ListMLE (Xia et al., [2008](https://arxiv.org/html/2508.14180v2#bib.bib45)) | 5.13 | 7.88 |
| PiRank (Swezey et al., [2021](https://arxiv.org/html/2508.14180v2#bib.bib36)) | 5.23 | 8.01 |
| URCC∗ Xi et al. ([2024](https://arxiv.org/html/2508.14180v2#bib.bib44)) | 5.01 | 7.44 |
| PG-rank∗ Gao et al. ([2023](https://arxiv.org/html/2508.14180v2#bib.bib13)) | 5.09 | 7.62 |
| RewardRank | 5.83 | 8.42 |

Following the protocol in (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)), models are trained with a binary click labels for each query groups (u=1u=1 if any item is clicked, otherwise 0).
Since counterfactual evaluation is not feasible here, we follow (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)) and report *Relevance DCG* at 5 and 10, computed on the human-assigned relevance labels provided with the test set111We report DCG rather than NDCG for consistency with (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)) .
As shown in Table [2](https://arxiv.org/html/2508.14180v2#S5.T2 "Table 2 ‣ 5.2 Baidu-ULTR Dataset with Real User Clicks ‣ 5 Experimental Results ‣ RewardRank: Optimizing True Learning-to-Rank Utility"), our method achieves a new state of the art D​C​G​@​5DCG@5 and D​C​G​@​10DCG@10 across all baselines. Importantly, these improvements are observed on human-assigned relevance labels that were never used in training by any method. This is particularly noteworthy given that our method is not optimized for relevance DCG. These results highlight both the robustness of our approach and its ability to generalize to real human feedback in large-scale search settings.

## 6 Conclusion

We present RewardRank, a counterfactual ranking framework that directly optimizes a behaviorally grounded utility instead of relying on proxy click-based surrogates. Notably, our approach accomplishes this without imposing any explicit modeling assumptions. Architecturally, RewardRank uses *SoftSort* to produce a differentiable soft permutation matrix, enabling end-to-end learning with *soft item embeddings* (convex combinations over items) that feed a utility model. To guard against reward model misspecification, we include a *misspecification regularization* term which is an explicit λ\lambda-weighted correction that penalizes over-reliance on noisy preference signals and stabilizes updates against spurious gains. Through the proposed PO-Eval and LAU-Eval protocols, we showed a systematic mismatch between offline/surrogate metrics (e.g., NDCGpurchase\mathrm{NDCG}\_{\text{purchase}}) and true decision outcomes, and demonstrated that RewardRank achieves the highest purchase rates while remaining competitive on surrogate metrics. Unlike URCC∗, RewardRank does *not* require a pretrained ranker and can leverage sessions without purchase labels, extracting useful signal in sparse-feedback regimes. Ablations further indicate that auxiliary per-item losses (including on purchase-free QGs) provide consistent, moderate gains. Overall, aligning training and evaluation with counterfactual utility yields models that better capture decision-relevant user behavior than traditional LTR or locally exploratory counterfactual baselines.

## References

## Appendix A Proofs and conceptual details

### A.1 Click-based Utility for PO-Eval.

The IPS-Oracle simulates user clicks as a probabilistic function of both position-dependent examination and item-specific relevance. Specifically, the click probability for item xπ​(ℓ)x\_{\pi(\ell)} at position ℓ\ell under ranking π\pi is modeled as:

|  |  |  |  |
| --- | --- | --- | --- |
|  | P​(Cq,xπ​(ℓ),ℓ)=P​(Eℓ)⋅σ​(Rq,xπ​(ℓ))\displaystyle P(C\_{q,x\_{\pi(\ell)},\ell})=P(E\_{\ell})\cdot\sigma(R\_{q,x\_{\pi(\ell)}}) |  | (14) |

where P​(Eℓ)P(E\_{\ell}) denotes the examination probability at position ℓ\ell, and σ​(Rq,xπ​(ℓ))\sigma(R\_{q,x\_{\pi(\ell)}}) is the probability of a click given examination. Given a query group (q,{xℓ}ℓ=1L,π)(q,\{x\_{\ell}\}\_{\ell=1}^{L},\pi), the click indicator for each item is sampled as:

|  |  |  |  |
| --- | --- | --- | --- |
|  | cq,xπ​(ℓ),ℓ∼Bernoulli​(P​(Cq,xπ​(ℓ),ℓ))\displaystyle c\_{q,x\_{\pi(\ell)},\ell}\sim\mathrm{Bernoulli}\big(P(C\_{q,x\_{\pi(\ell)},\ell})\big) |  | (15) |

We define the *group-level utility* under the logged policy as a binary signal indicating whether at least one item in the list was clicked:

|  |  |  |  |
| --- | --- | --- | --- |
|  | U​(q,{xℓ},π)={1,if ​∑ℓ=1Lcq,xπ​(ℓ),ℓ>0,0,otherwise.\displaystyle U(q,\{x\_{\ell}\},\pi)=\begin{cases}1,&\text{if }\sum\_{\ell=1}^{L}c\_{q,x\_{\pi(\ell)},\ell}>0,\\ 0,&\text{otherwise.}\end{cases} |  | (16) |

The corresponding observed utility in the dataset, uu, is a realization of U​(q,{xℓ},πlog)U(q,\{x\_{\ell}\},\pi\_{\text{log}}) under the logged ranking πlog\pi\_{\text{log}}.

To obtain a differentiable approximation, we define the expected probability of at least one click as:

|  |  |  |  |
| --- | --- | --- | --- |
|  | UIPS​(q,{xℓ},π)=1−∏ℓ=1L(1−P​(Eℓ)⋅σ​(Rq,xπ​(ℓ)))\displaystyle U\_{\text{IPS}}(q,\{x\_{\ell}\},\pi)=1-\prod\_{\ell=1}^{L}\left(1-P(E\_{\ell})\cdot\sigma\big(R\_{q,x\_{\pi(\ell)}}\big)\right) |  | (17) |

This smoothed utility represents the expected engagement for ranking π\pi and serves as a continuous training signal. The reward model is trained to predict the binary group-level utility u∈{0,1}u\in\{0,1\} from the logged policy, while the ranker maximizes the expected soft utility UIPSU\_{\text{IPS}} under its own predicted rankings. This formulation bridges synthetic click modeling with realistic counterfactual feedback, enabling effective utility-based optimization even without direct supervision on full permutations.

### A.2 Ideal IPS-Oracle: Rearrangement inequality

###### Theorem 1 (Ideal Ranking Maximizes Utility via Rearrangement Inequality).

Let 𝐫=(r1,…,rn)∈ℝ≥0n\mathbf{r}=(r\_{1},\ldots,r\_{n})\in\mathbb{R}\_{\geq 0}^{n} be a vector of predicted relevance scores, and let 𝐞=(e1,…,en)∈ℝ≥0n\mathbf{e}=(e\_{1},\ldots,e\_{n})\in\mathbb{R}\_{\geq 0}^{n} be a non-increasing sequence of examination probabilities: e1≥e2≥…≥ene\_{1}\geq e\_{2}\geq\ldots\geq e\_{n}. Let π∗\pi^{\*} be the permutation that sorts 𝐫\mathbf{r} in descending order: rπ∗​(1)≥rπ∗​(2)≥…≥rπ∗​(n)r\_{\pi^{\*}(1)}\geq r\_{\pi^{\*}(2)}\geq\ldots\geq r\_{\pi^{\*}(n)}. Then, for any permutation π∈𝒮n\pi\in\mathcal{S}\_{n}, we have:

|  |  |  |
| --- | --- | --- |
|  | ∑i=1nei⋅rπ∗​(i)≥∑i=1nei⋅rπ​(i)\sum\_{i=1}^{n}e\_{i}\cdot r\_{\pi^{\*}(i)}\geq\sum\_{i=1}^{n}e\_{i}\cdot r\_{\pi(i)} |  |

###### Proof.

This is a direct consequence of the classical rearrangement inequality (Day, [1972](https://arxiv.org/html/2508.14180v2#bib.bib10)). Among all permutations π\pi of the relevance scores, the weighted sum ∑iei⋅rπ​(i)\sum\_{i}e\_{i}\cdot r\_{\pi(i)} is maximized when the rπ​(i)r\_{\pi(i)} are ordered in the same way as the eie\_{i}, i.e., both decreasing. Hence, sorting 𝐫\mathbf{r} in descending order and aligning it with the already sorted 𝐞\mathbf{e} gives the maximal utility.
∎

Above analysis shows that ideal ranking order under the IPS Oracle is ordering the items such the sorting of item relevance scores and examination probabilities result in the same permutation.

### A.3 Details of baselines

#### A.3.1 PG-rank∗ : PG-rank with Learned Reward Model.

We extend the PG-Rank framework (Gao et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib13)) by replacing the handcrafted reward (e.g., NDCG) with a learned reward model g​(q,{i}L,π)g(q,\{i\}\_{L},\pi) that scores entire permutations based on user utility. The goal is to maximize the expected reward under the Plackett–Luce distribution induced by the ranker’s scores:

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℒPG-reward​(θ)=𝔼π∼ℙθ​[g​(q,{i}L,π)]\mathcal{L}\_{\text{PG-reward}}(\theta)=\mathbb{E}\_{\pi\sim\mathbb{P}\_{\theta}}\left[g(q,\{i\}\_{L},\pi)\right] |  | (18) |

where ℙθ​(π)\mathbb{P}\_{\theta}(\pi) is the Plackett–Luce distribution over permutations, parameterized by model scores s1,…,sLs\_{1},\dots,s\_{L} for each item in the query group. To enable backpropagation through the sampled permutations, we adopt the Gumbel-Softmax trick as in the original PG-Rank implementation, which provides a continuous relaxation of the discrete sampling process.

The gradient of this objective is estimated using the REINFORCE trick with a baseline bb for variance reduction (adopted from PG-rank (Gao et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib13); Kool et al., [2019](https://arxiv.org/html/2508.14180v2#bib.bib23))):

|  |  |  |  |
| --- | --- | --- | --- |
|  | ∇θℒPG-reward≈1K​∑k=1K[(g​(π(k))−b)⋅∇θlog⁡ℙθ​(π(k))]\nabla\_{\theta}\mathcal{L}\_{\text{PG-reward}}\approx\frac{1}{K}\sum\_{k=1}^{K}\left[\left(g(\pi^{(k)})-b\right)\cdot\nabla\_{\theta}\log\mathbb{P}\_{\theta}(\pi^{(k)})\right] |  | (19) |

where π(k)∼ℙθ\pi^{(k)}\sim\mathbb{P}\_{\theta} are KK Monte Carlo samples drawn from the Plackett–Luce model.

The log-probability of a sampled permutation π\pi under this model is given by:

|  |  |  |  |
| --- | --- | --- | --- |
|  | log⁡ℙθ​(π)=∑k=1L[sπ​(k)−log​∑j=kLexp⁡(sπ​(j))]\log\mathbb{P}\_{\theta}(\pi)=\sum\_{k=1}^{L}\left[s\_{\pi(k)}-\log\sum\_{j=k}^{L}\exp(s\_{\pi(j)})\right] |  | (20) |

This formulation allows us to train the ranking model directly on learned, utility-aligned reward signals using fully differentiable, sample-based policy gradients.

#### A.3.2 URCC∗ with Learned Reward Model.

URCC (Xi et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib44)) proposes a two-stage counterfactual reranking framework that jointly learns a set-aware utility function and a context-aware reranker. The utility model in URCC is itself learned from data and used to guide the optimization of the reranker via a pairwise ranking loss over permutations. Since the official implementation of URCC is not publicly available, we re-implemented the method using our own architecture.

In our version of URCC∗ , we retain the core two-stage structure but implement the utility model g​(q,{i}L,π)g(q,\{i\}\_{L},\pi) as a Transformer-based encoder trained to predict user utility over full permutations. Given a query qq and a set of items {i}L\{i\}\_{L}, the reward model assigns a scalar score to a permutation π\pi:

|  |  |  |  |
| --- | --- | --- | --- |
|  | Sπ=g​(q,{i}L,π)S\_{\pi}=g(q,\{i\}\_{L},\pi) |  | (21) |

Following URCC, we then train the ranker fθf\_{\theta} to maximize this learned reward by optimizing a context-aware pairwise loss. For a pair of permutations (π+,π−)(\pi^{+},\pi^{-}) such that g​(q,{i}L,π+)>g​(q,{i}L,π−)g(q,\{i\}\_{L},\pi^{+})>g(q,\{i\}\_{L},\pi^{-}), we minimize the following objective:

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℒURCC-reward​(θ)=𝔼(π+,π−)∼𝒫​[log⁡(1+exp⁡(−(Sπ+−Sπ−)))]\mathcal{L}\_{\text{URCC-reward}}(\theta)=\mathbb{E}\_{(\pi^{+},\pi^{-})\sim\mathcal{P}}\left[\log\left(1+\exp\left(-(S\_{\pi^{+}}-S\_{\pi^{-}})\right)\right)\right] |  | (22) |

Here, 𝒫\mathcal{P} denotes the set of sampled permutation pairs with preference orderings induced by the reward model. Our implementation uses neighborhood-based sampling (e.g., pairwise swaps) to construct π+\pi^{+} and π−\pi^{-} from the base ranking.

Thus, while our training procedure is structurally consistent with the original URCC framework, we employ a more expressive Transformer-based reward model to capture user behavior better and align optimization with utility-oriented objectives.

### A.4 Comparison of Time Complexity and Counterfactual Space Exploration

Table [3](https://arxiv.org/html/2508.14180v2#A1.T3 "Table 3 ‣ A.4 Comparison of Time Complexity and Counterfactual Space Exploration ‣ Appendix A Proofs and conceptual details ‣ RewardRank: Optimizing True Learning-to-Rank Utility") compares the time complexity of three methods: URCC∗ , PG-rank∗ , and RewardRank. The per-iteration time complexity is analyzed based on the number of calls to the reward model.

URCC∗ : n2n^{2}, where nn is the number of items in the list. URCC∗ explores the neighborhood of factual permutations, leading to quadratic complexity due to pairwise comparisons. URCC∗ only explores the neighborhood of factual permutations, meaning it performs limited counterfactual exploration. This approach is considered pessimistic because it does not explore the entire space of possible rankings, which could miss potentially better arrangements.

PG-rank∗ : kk, where kk is the number of Monte Carlo (MC) samples. While kk is typically smaller than nn, PG-rank∗ requires large kk values and variance reduction baselines to converge. PG-Rank uses Monte Carlo (MC) sampling to explore a broader counterfactual space, but this approach requires large MC samples to converge effectively. To ensure stable and accurate exploration, PG-Rank relies on variance-reduction baselines. However, it still faces challenges in accurately capturing all potential counterfactual configurations without a very large number of samples.

RewardRank: 11, as it performs a single call to the reward model. RewardRank explores the entire counterfactual space efficiently and can focus on more certain regions with reward misspecification mitigation.

In Table [3](https://arxiv.org/html/2508.14180v2#A1.T3 "Table 3 ‣ A.4 Comparison of Time Complexity and Counterfactual Space Exploration ‣ Appendix A Proofs and conceptual details ‣ RewardRank: Optimizing True Learning-to-Rank Utility"), we also provide the overall wall-clock time to train the model under the above method for the Baidu-ULTR dataset. Each model is trained for 21 epochs.

| Method | Time Complexity | Wall-Clock Time | Description |
| --- | --- | --- | --- |
| PiRank | 11 | ∼\sim6 hours | No call to the reward model |
| URCC∗ | n2n^{2} | ∼\sim34 hours | Neighborhood search, pessimistic |
| PG-rank∗ | kk | ∼\sim16 hours (k=10k=10) | Needs large kk for convergence |
| RewardRank | 11 | ∼\sim7 hours | Full counterfactual space exploration |

## Appendix B Experimentation details

### B.1 Datasets

##### Baidu-ULTR Reranking Dataset.

| Split | #Query Groups | #Query-Document Pairs |
| --- | --- | --- |
| Training | 1,857,248 | 11,738,489 |
| Validation/Test | 590,612 | 4,797,378 |
| Total | 2,447,860 | 16,535,867 |

The Baidu-ULTR dataset (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)), a large-scale subset of the Baidu-ULTR corpus (Zou et al., [2022](https://arxiv.org/html/2508.14180v2#bib.bib46)), contains user click interactions over web search queries. It includes 1.8M query groups (11.7M query-document pairs) and 590K validation/test sessions (4.8M pairs).The authors of (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)) provide BERT-based CLS embeddings for each query-document pair.

We use the large-scale reranking dataset introduced by (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)): publicly available at: <https://huggingface.co/datasets/philipphager/baidu-ultr_uva-mlm-ctr>, derived from the original Baidu-ULTR corpus (Zou et al., [2022](https://arxiv.org/html/2508.14180v2#bib.bib46)). This dataset is constructed from real-world user interactions on Baidu’s production search engine and is designed to support robust evaluation of learning-to-rank models in counterfactual settings.

Each session consists of a user query, a candidate list of documents retrieved by an upstream ranker, the original presented ranking, and user interaction logs (e.g., clicks and dwell time). For each query-document pair, the dataset provides both sparse lexical features (e.g., BM25, TF-IDF, query likelihood) and dense semantic representations.

To generate the dense features, the authors pretrain a BERT-style model, referred to as MonoBERT, from scratch using masked language modeling (MLM) on the full Baidu corpus. This model is trained in a mono-encoder configuration and outputs a [CLS] token embedding for each query-document pair. These CLS embeddings are included in the dataset and serve as fixed, high-quality dense features for downstream reranking. The pretrained MonoBERT model and inference code are publicly available at:
<https://github.com/philipphager/baidu-bert-model>.

##### Amazon KDD-cup.

The KDD-Cup dataset (Reddy et al., [2022](https://arxiv.org/html/2508.14180v2#bib.bib33)) contains 130K queries and 2.6M annotated query-product pairs in English, Japanese, and Spanish. Each query is linked to up to 40 products with rich textual metadata (titles, descriptions, bullet points), making it well-suited for LLM-based evaluation, unlike Baidu-ULTR. Although the presentation order is not recorded, the dataset primarily consists of relevant query-product pairs that were shown to users. For training, validation, and testing, we sample five random permutations of length 8 per query, resulting in 400,000 training and 50,000 validation/test groups.
We use the English subset of the product search dataset released as part of the KDD Cup 2022 challenge (Reddy et al., [2022](https://arxiv.org/html/2508.14180v2#bib.bib33)), which contains real-world queries and associated candidate products from Amazon. Each query-product pair is annotated using the ESCI labeling scheme:
Exact match, Substitute, Complement, or Irrelevant.

Each query group is identified by a unique query\_id and paired with 10–40 product candidates. For each product, the dataset provides structured metadata including:

product\_title,

product\_brand,

product\_color

product\_description,

product\_bullet\_point (optional fields)

product\_id,

product\_locale, and

ESCI relevance label

To construct our training and evaluation sets, we sample 5 random permutations of length 8 from each query group. Note that we do not use the human-annotated ESCI labels provided in the dataset. Instead, we leverage the LLM’s capability for contextual understanding to generate relevance labels automatically. Ideally, the relevance judgments produced by the LLM should align closely with those of human annotators.
This yields approximately 392​K392\text{K} query groups for training and 20​K20\text{K} for validation, and 20​K20\text{K} for testing. For a given query group, we encode each query-item pair into sentence embeddings using the all-MiniLM-L6-v2: <https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2> model from Sentence Transformers. The input format for the sentence transformer is constructed as:

{query} [SEP] {product\_title} Brand:{brand} Color:{color}

|  |  |  |
| --- | --- | --- |
| Split | #Query groups | #Query-Product Pairs |
| Training | 78,447 | 627,576 |
| Validation | 4,000 | 32,000 |
| Test | 4,000 | 32,000 |
| Total | 86,447 | 691,576 |
| Total (including 5 random permutations) | 392,235 | 3,137,880 |

### B.2 Implementation details

We use a transformer architecture for both the reward model and the ranker across all methods to ensure a consistent architectural backbone. The model contains 12 transformer layers, 768 hidden dimensions, 12 attention heads, and approximately 110M parameters. All models are trained with a learning rate of 2×10−52\times 10^{-5} using the AdamW optimizer (Loshchilov & Hutter, [2017](https://arxiv.org/html/2508.14180v2#bib.bib25)) with a weight decay of 10−210^{-2}. We use a batch size of 512 and train for 21 epochs, applying a learning rate decay at epoch 12 via a step-based learning rate scheduler. All experiments are conducted using 2 NVIDIA A100 GPUs (40GB each).

For our method, RewardRank, we use a soft permutation temperature τ=0.5\tau=0.5 and reward correction term λ=0.7\lambda=0.7. In the PG-rank∗ baseline, which replaces the handcrafted NDCG utility with our learned reward model, we apply Gumbel-Softmax sampling with temperature 0.10.1 to approximate permutation sampling from the Plackett–Luce distribution. We report PG-rank∗ results for different Monte Carlo samples (MC=1,5,10\text{MC}=1,5,10) to evaluate variance in reward estimation.

In our URCC∗ implementation, we follow the original two-stage design: a set-aware utility model and a pairwise ranker. The utility model is trained with a binary cross-entropy loss computed over per-item logits derived from the transformer encoder outputs. Specifically, for each item in the permutation, we pool its embedding from the encoder, apply dropout, and project it through a shared per-item classifier. The per-item predictions are matched to click labels, and their aggregated loss forms the utility supervision.

As an additional baseline, we include a Naive-ranker trained with a relaxed NDCG objective following the PiRank formulation (Swezey et al., [2021](https://arxiv.org/html/2508.14180v2#bib.bib36)), allowing listwise supervision using soft permutation matrices. All baselines are trained using the same reward data and input embeddings to isolate the impact of the learning objective.

Representative code for our implementations of RewardRank, PG-rank∗ , URCC∗ baselines, and evaluation procedures is included in the supplementary material.

## Appendix C Counterfactual evaluation protocols

### C.1 PO-Eval details

PO-Eval provides a click-based framework for counterfactual evaluation of ranking models.
Using the pre-trained Inverse Propensity Scoring model (IPS-Oracle)
(Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17))222<https://github.com/philipphager/baidu-bert-model>
on the Baidu-ULTR dataset, it generates soft click probabilities for items in a ranked query group.
These probabilities serve as counterfactual labels, enabling the evaluation of how effectively a ranker can model user engagement patterns reflected in clicks.

![Refer to caption](fig/ips_y.png)
![Refer to caption](fig/ips_pos.png)

As the Baidu-ULTR dataset is derived from user interaction logs, click activity is heavily concentrated in the top-ranked positions, reflecting strong position bias (see Figure [4(b)](https://arxiv.org/html/2508.14180v2#A3.F4.sf2 "In Figure 4 ‣ C.1 PO-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility")). In contrast, the distilled soft utility (y^\hat{y}) generated by the IPS-Oracle exhibits a more uniform distribution across positions (Figure [4(a)](https://arxiv.org/html/2508.14180v2#A3.F4.sf1 "In Figure 4 ‣ C.1 PO-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility")), indicating that the oracle has successfully learned to correct for position bias. Under the PO-Eval protocol, ranking methods aim to implicitly learn position debiasing from the IPS-Oracle’s soft utility, as indicated by high UIPS-O​(q,{i}L,π^)U\_{\text{IPS-O}}(q,\{i\}\_{L},\hat{\pi}).

##### Training and evaluating ranking schemes.

Using the learned reward model, any ranker ff can be optimized via the reward maximization objective defined in Eqn [12](https://arxiv.org/html/2508.14180v2#S4.E12 "In Soft Permutation via SoftSort. ‣ 4.2 Stage 2: Ranker Reward Maximization through Soft Sorting ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility"). To evaluate its performance under the IPS-Oracle, we define the following metric:
Given a query group (q,{i}L)(q,\{i\}\_{L}) and predicted relevance scores s=[s1,…,sL]s=[s\_{1},\dots,s\_{L}], the induced permutation is π^=argsort​(s)\hat{\pi}=\text{argsort}(s). For each position π^ℓ\hat{\pi}\_{\ell}, the examination probability is P​(Eπ^ℓ)P(E\_{\hat{\pi}\_{\ell}}), and the associated relevance score Rq,iℓR\_{q,i\_{\ell}} is provided by the IPS-Oracle. The overall utility is computed as the probability of at least one click: UIPS​(q,{i}L,π^)U\_{\text{IPS}}(q,\{i\}\_{L},\hat{\pi}), which serves as the primary evaluation metric. It reflects how well ff aligns with the user behavior modeled by the IPS-Oracle; higher values indicating better alignment. Additionally, we report NDCGrel​@​10\text{NDCG}\_{\text{rel}}@10, which measures how much the predicted ranking respects the relevance scores Rq,iR\_{q,i}.

We incorporate the examination probabilities from (Hager et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib17)), which are defined as:

|  |  |  |
| --- | --- | --- |
|  | P​(E)={1:1.0000,2:0.6738,3:0.4145,4:0.2932,5:0.2079,6:0.1714,7:0.1363,8:0.1166}P(E)=\{1:1.0000,2:0.6738,3:0.4145,4:0.2932,5:0.2079,6:0.1714,7:0.1363,8:0.1166\} |  |

![Refer to caption](fig/llm_temp.png)

### C.2 LAU-Eval details

We use Claude 3.5 Sonnet v2 with a temperature of 0.5 and a context window of 5,000 tokens. The LLM is prompted using a consistent instruction template, as illustrated in Figure [6](https://arxiv.org/html/2508.14180v2#A3.F6 "Figure 6 ‣ Ranking Evaluations. ‣ C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility"). To evaluate a ranker with LAU-Eval, its predicted scores are converted into item positions, which are then used to reorder the input list. This reordered list is passed to the LLM alongside the original query, and the LLM outputs a binary decision regarding purchase. We include representative query groups and the corresponding LLM responses to demonstrate this pipeline.

To assess the robustness of LAU-Eval under different sampling conditions, we examine how varying the temperature of the LLM decoding process affects its outputs. Figure [5](https://arxiv.org/html/2508.14180v2#A3.F5 "Figure 5 ‣ Training and evaluating ranking schemes. ‣ C.1 PO-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility") shows the distributions of LLM-simulated purchase decisions and selected item positions at temperatures 0.1, 0.5, and 0.75. While purchase rates exhibit slight variation, the LLM consistently favors top-ranked items—reflecting realistic user behavior in shopping scenarios.

##### Instruction prompt for LLM.

We design the LLM-Eval instruction to incorporate behavioral biases such as position bias, brand preference, irrelevance filtering, similarity aversion, and color bias, guiding the LLM to consider both relevance and context-dependent preferences. Given a query and an ordered product list, the LLM estimates (i) the probability of purchasing at least one item and (ii) the selected item, without explicit relevance constraints. We illustrate the instruction prompt using an example from the Amazon KDD-Cup dataset (Reddy et al., [2022](https://arxiv.org/html/2508.14180v2#bib.bib33)), as shown in Figure [6](https://arxiv.org/html/2508.14180v2#A3.F6 "Figure 6 ‣ Ranking Evaluations. ‣ C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility").

##### Ranking Evaluations.

We present the LLM’s response to the initial list in Figure [7](https://arxiv.org/html/2508.14180v2#A3.F7 "Figure 7 ‣ Ranking Evaluations. ‣ C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility"), including the full reasoning behind the response. It is noteworthy how the LLM is able to reason about the biases present in the query groups effectively. For each initial list, we also show the LLM’s response to the rearranged list generated by Claude, depicted in Figure [8](https://arxiv.org/html/2508.14180v2#A3.F8 "Figure 8 ‣ Ranking Evaluations. ‣ C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility"). As seen, the initial arrangements in Figure [7](https://arxiv.org/html/2508.14180v2#A3.F7 "Figure 7 ‣ Ranking Evaluations. ‣ C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility") lead to a no purchase decision, whereas RewardRank generates arrangements that increase the likelihood of purchase according to the LLM. Furthermore, the LLM’s response enhances the interpretability of LLM-Eval, demonstrating how RewardRank’s ranking capabilities align with the LLM’s reasoning process.

|  |  |  |  |
| --- | --- | --- | --- |
|  | LAU-Eval | | |
|  | *Counterfactual (✓)* | *Offline (✗)* | |
| Method | Pr​(#​Purchases≥1)\mathrm{Pr}(\#\mathrm{Purchases}\geq 1) | NDCGpurchase\text{NDCG}\_{\mathrm{purchase}} | NDCGESCI\text{NDCG}\_{\mathrm{ESCI}} |
| Policy in data | 0.497 ±\pm 0.009 | 0.496±0.0090.496\pm 0.009 | 0.995±0.0090.995\pm 0.009 |
| ListNet (Cao et al., [2007](https://arxiv.org/html/2508.14180v2#bib.bib6)) | 0.521±0.0090.521\pm 0.009 | 0.405±0.0090.405\pm 0.009 | 0.8611±0.0090.8611\pm 0.009 |
| ListMLE (Xia et al., [2008](https://arxiv.org/html/2508.14180v2#bib.bib45)) | 0.522±0.0080.522\pm 0.008 | 0.402±0.0080.402\pm 0.008 | 0.8610±0.0030.8610\pm 0.003 |
| LambdaRank (Wang et al., [2018](https://arxiv.org/html/2508.14180v2#bib.bib42)) | 0.523±0.0090.523\pm 0.009 | 0.406±0.0090.406\pm 0.009 | 0.8610±0.0090.8610\pm 0.009 |
| PiRank (Swezey et al., [2021](https://arxiv.org/html/2508.14180v2#bib.bib36)) | 0.528±0.0070.528\pm 0.007 | 0.408±0.0090.408\pm 0.009 | 0.8623±0.0050.8623\pm 0.005 |
| URCC∗ (Xi et al., [2024](https://arxiv.org/html/2508.14180v2#bib.bib44)) | 0.471±0.0080.471\pm 0.008 | 0.401±0.0070.401\pm 0.007 | 0.8621±0.0090.8621\pm 0.009 |
| PG-rank∗ (Gao et al., [2023](https://arxiv.org/html/2508.14180v2#bib.bib13)) | 0.489±0.0070.489\pm 0.007 | 0.402±0.0080.402\pm 0.008 | 0.8630±0.0090.8630\pm 0.009 |
| RewardRank | 0.561±0.0080.561\pm 0.008 | 0.401±0.0070.401\pm 0.007 | 0.8628±0.0090.8628\pm 0.009 |

Initially, we experimented with smaller language models such as Llama-3.1-8B: <meta-llama/Llama-3.1-8B-Instruct> and DeepSeek-R1-Distill: <deepseek-ai/DeepSeek-R1-Distill-Llama-8B>. However, these models were unable to generate appropriate responses to the instructions. Our experiments revealed that larger models were better at understanding the context.

It is important to note that LAU-Eval is used to simulate user behavior dynamics that may influence user decisions. Our selection of biases and instruction prompt serves as a proof-of-concept demonstrating that an LLM can be used as a proxy user to study counterfactual ranking strategies. We acknowledge that there are likely many variants of instruction prompts that could be designed to simulate user behavior. This area of exploration could be a direction for future work.

|  |  |  |
| --- | --- | --- |
|  | PO-Eval | LAU-Eval |
| Method | Pr​(#​Clicks≥1)\mathrm{Pr}(\#\mathrm{Clicks}\geq 1) | Pr​(#​Purchase≥1)\mathrm{Pr}(\#\mathrm{Purchase}\geq 1) |
| Upper-Bound | 0.553 | - |
| ListNet Cao et al. ([2007](https://arxiv.org/html/2508.14180v2#bib.bib6)) | 0.523 ±\pm 0.0007 | 0.521 ±\pm 0.009 |
| ListMLE Xia et al. ([2008](https://arxiv.org/html/2508.14180v2#bib.bib45)) | 0.522 ±\pm 0.0007 | 0.522 ±\pm 0.008 |
| LambdaRank Wang et al. ([2018](https://arxiv.org/html/2508.14180v2#bib.bib42)) | 0.524 ±\pm 0.0007 | 0.523 ±\pm 0.009 |
| PiRank Swezey et al. ([2021](https://arxiv.org/html/2508.14180v2#bib.bib36)) | 0.525 ±\pm 0.0007 | 0.528 ±\pm 0.007 |
| URCC∗ | 0.462 ±\pm 0.0005 | 0.471 ±\pm 0.008 |
| PG-rank∗ (mc=1) | 0.481 ±\pm 0.0006 | 0.441 ±\pm 0.006 |
| PG-rank∗ (mc=5) | 0.495 ±\pm 0.0005 | 0.465 ±\pm 0.007 |
| PG-rank∗ (mc=10) | 0.501 ±\pm 0.0005 | 0.489 ±\pm 0.007 |
| SoftSort Temperature τ\tau | | |
| RewardRank (τ=0.1,λ=0.0\tau=0.1,\lambda=0.0) | 0.531 ±\pm 0.0005 | 0.548 ±\pm 0.008 |
| RewardRank (τ=0.2,λ=0.0\tau=0.2,\lambda=0.0) | 0.532 ±\pm 0.0005 | 0.550 ±\pm 0.008 |
| RewardRank (τ=0.5,λ=0.0\tau=0.5,\lambda=0.0) | 0.533 ±\pm 0.0005 | 0.551 ±\pm 0.007 |
| RewardRank (τ=0.7,λ=0.0\tau=0.7,\lambda=0.0) | 0.531 ±\pm 0.0005 | 0.550 ±\pm 0.008 |
| RewardRank (τ=1.0,λ=0.0\tau=1.0,\lambda=0.0) | 0.530 ±\pm 0.0005 | 0.549 ±\pm 0.009 |
| Misspecification Correction λ\lambda | | |
| RewardRank (τ=0.5,λ=0.1\tau=0.5,\lambda=0.1) | 0.532 ±\pm 0.0005 | 0.549 ±\pm 0.007 |
| RewardRank (τ=0.5,λ=0.3\tau=0.5,\lambda=0.3) | 0.534 ±\pm 0.0007 | 0.554 ±\pm 0.007 |
| RewardRank (τ=0.5,λ=0.7\tau=0.5,\lambda=0.7) | 0.536 ±\pm 0.0007 | 0.561 ±\pm 0.008 |
| RewardRank (τ=0.5,λ=1.0\tau=0.5,\lambda=1.0) | 0.533 ±\pm 0.0007 | 0.553 ±\pm 0.006 |
| Auxiliary Per-Item Regularizer Eqn [6](https://arxiv.org/html/2508.14180v2#S4.E6 "In 4.1 Stage 1: Learning the Utility Using a Reward Model ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility") | | |
| RewardRank (reward loss = Eqn [3](https://arxiv.org/html/2508.14180v2#S4.E3 "In 4.1 Stage 1: Learning the Utility Using a Reward Model ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility")) | 0.528 ±\pm 0.0005 | 0.553 ±\pm 0.008 |
| RewardRank (reward loss = Eqn [3](https://arxiv.org/html/2508.14180v2#S4.E3 "In 4.1 Stage 1: Learning the Utility Using a Reward Model ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility") + Eqn [6](https://arxiv.org/html/2508.14180v2#S4.E6 "In 4.1 Stage 1: Learning the Utility Using a Reward Model ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility")) | 0.536 ±\pm 0.0005 | 0.561 ±\pm 0.008 |
| Using pretrained ranker: PiRank | | |
| URCC∗ | 0.521 ±\pm 0.0005 | - |
| PG-rank∗ | 0.503 ±\pm 0.0006 | - |
| RewardRank | 0.538 ±\pm 0.0005 | - |

## Appendix D Further ablation studies

We use the Baidu-ULTR dataset to study how the performance of RewardRank varies with two key hyperparameters: the temperature τ\tau of the SoftSort operator, which controls permutation sharpness, and the regularization strength λ\lambda for reward misspecification correction introduced in Eqn [13](https://arxiv.org/html/2508.14180v2#S4.E13 "In Mitigating reward misspecification. ‣ 4.2 Stage 2: Ranker Reward Maximization through Soft Sorting ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility"). Varying τ∈{0.1,0.2,0.7,1.0}\tau\in\{0.1,0.2,0.7,1.0\} shows that moderate temperature (τ=0.2−0.5\tau=0.2-0.5) achieves the best utility and relevance alignment. Too low a temperature leads to unstable gradients due to near-hard permutations, while higher values oversmooth rankings, diluting learning signals. Fixing τ=0.5\tau=0.5, we ablate the correction term with λ∈{0.0,0.1,0.3,0.7,1.0}\lambda\in\{0.0,0.1,0.3,0.7,1.0\}. As shown in Table [7](https://arxiv.org/html/2508.14180v2#A3.T7 "Table 7 ‣ Ranking Evaluations. ‣ C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility") and visualized in Figure [3](https://arxiv.org/html/2508.14180v2#S5.F3 "Figure 3 ‣ LLM-based User Simulation (LAU-Eval). ‣ 5.1 Large-Scale Reproducible Testbenches for Counterfactual LTR ‣ 5 Experimental Results ‣ RewardRank: Optimizing True Learning-to-Rank Utility"), moderate correction (λ=0.5−0.7\lambda=0.5-0.7) yields the best trade-off, by down-weighting unreliable samples without discarding informative ones. This results in higher IPS utility, confirming the benefit of explicitly mitigating reward misspecification.

We explore the impact of incorporating an auxiliary item-level reward loss (Eqn [6](https://arxiv.org/html/2508.14180v2#S4.E6 "In 4.1 Stage 1: Learning the Utility Using a Reward Model ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility")) into the training objective of the reward model. As shown in Table [7](https://arxiv.org/html/2508.14180v2#A3.T7 "Table 7 ‣ Ranking Evaluations. ‣ C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility"), adding this auxiliary loss to the list-level cross-entropy objective (Eqn [3](https://arxiv.org/html/2508.14180v2#S4.E3 "In 4.1 Stage 1: Learning the Utility Using a Reward Model ‣ 4 RewardRank: Data-driven LTR Utility Maximization ‣ RewardRank: Optimizing True Learning-to-Rank Utility")) improves expected utility from 0.528 to 0.536. This indicates that learning to predict the per-item feedback as an auxiliary task enhances the reward model’s generalization and improves the downstream utility-optimized ranking.

Table [7](https://arxiv.org/html/2508.14180v2#A3.T7 "Table 7 ‣ Ranking Evaluations. ‣ C.2 LAU-Eval details ‣ Appendix C Counterfactual evaluation protocols ‣ RewardRank: Optimizing True Learning-to-Rank Utility") presents the results for the pretrained ranker, which is the ranker trained with PiRank Swezey et al. ([2021](https://arxiv.org/html/2508.14180v2#bib.bib36)) LTR loss. URCC∗ , being dependent on the pretrained ranker, demonstrates larger performance improvements. However, the gains from the pre-trained ranker are not as significant, suggesting that URCC∗ ’s performance is more sensitive to the quality of the pretrained model. On the other hand, RewardRank and PG-rank∗ show limited improvements when using the pretrained ranker, as their performance is not heavily reliant on the presence of a strong pretrained model. These methods are more robust in their ranking capabilities and do not exhibit substantial gains from a pretrained ranker.

## Appendix E Inference cost and limitations

##### Inference Cost.

The main inference cost in our work arises from using large language models (LLMs) for ranking and purchase probability estimation. These models require significant computational resources, especially for large datasets and permutations of items. Optimizations like batch processing and multi-GPU use help manage costs, but scalability remains a challenge. Caching frequently accessed queries can further reduce repeated computation costs.

##### Limitations.

While both PO-Eval and LAU-Eval provide valuable insights into ranking quality and user preferences, there are inherent limitations in each approach. These limitations arise from their reliance on specific biases and the quality of input data, which may affect their performance in diverse real-world scenarios. Below, we outline the key limitations of each method:

PO-Eval Limitations: While PO-Eval provides a robust baseline for position-debiasing, it is limited in behavioral scope. It primarily focuses on mitigating position bias without considering other nuanced user preferences, such as brand bias or contextual relevance, which can lead to suboptimal performance in more complex scenarios.

LAU-Eval Limitations: LAU-Eval captures richer heuristics and offers more context-aware ranking, but it depends heavily on the quality and stability of the LLM outputs. Inconsistent or noisy outputs from the LLM can negatively affect the reliability of the evaluation, as the method assumes that the LLM accurately reflects user preferences in all scenarios.

These limitations highlight areas for future improvement, such as incorporating additional user behavior modeling and enhancing the robustness of the LLM outputs.

![Mascot Sammy](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)
