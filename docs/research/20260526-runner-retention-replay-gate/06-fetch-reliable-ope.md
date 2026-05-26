# Reliable Off-policy Evaluation for Reinforcement Learning 

Jie Wang 

> School of Science and Engineering, The Chinese University of Hong Kong, Shenzhen jiewang@link.cuhk.edu.cn

Rui Gao 

> Department of Information, Risk and Operations Management, The University of Texas at Austin rui.gao@mccombs.utexas.edu

Hongyuan Zha 

> School of Data Science, The Chinese University of Hong Kong, Shenzhen zhahy@cuhk.edu.cn

In a sequential decision-making problem, off-policy evaluation estimates the expected cumulative reward of a target policy using logged trajectory data generated from a different behavior policy, without execution of the target policy. Reinforcement learning in high-stake environments, such as healthcare and education, is often limited to off-policy settings due to safety or ethical concerns, or inability of exploration. Hence it is imperative to quantify the uncertainty of the off-policy estimate before deployment of the target policy. In this paper, we propose a novel framework that provides robust and optimistic cumulative reward estimates using one or multiple logged trajectories data. Leveraging methodologies from distributionally robust optimization, we show that with proper selection of the size of the distributional uncertainty set, these estimates serve as confidence bounds with non-asymptotic and asymptotic guarantees under stochastic or adversarial environments. Our results are also generalized to batch reinforcement learning and are supported by empirical analysis. 

Key words : Uncertainty quantification; Reinforcement learning; Wasserstein robust optimization 

## 1. Introduction 

Reinforcement learning (RL) has achieved phenomenal success in games and robotics (OpenAI et al. 2019, Mnih et al. 2015, Kober et al. 2013) in the past decade, which also stimulates the enthusiasm of extending these techniques in other areas including healthcare (Raghu et al. 2017, Gottesman et al. 2019), education (Mandel et al. 2014), autonomous driving (Sallab et al. 2017), recommendation systems (Liu et al. 2018a, Wang et al. 2018), etc. One of the major challenges in applying RL to these real-world applications, especially those involve high-stake environments, is the problem of off-policy evaluation (OPE): how one can evaluate a new policy before deployment, using only historical data collected from a different policy, known as the behavior policy. Indeed, for many practical applications, one may not have a faithful simulator of the domain from which sufficient amount of data can be exploited to train the RL system, and it may not always be feasible to try out a new policy without causing unintended harms. For example, consider the problem of finding the best treatment plan for a patient, or testing the performance of an automated driving system, or suggesting a personalized curriculum for a student. In those tasks, conducting experimentation involves interactions with real people, thus it can be costly to collect data. Even worse, a bad policy can be risky or unethical and may result in severe consequences. Therefore, it is important for the RL system to have the ability to predict how well a new policy would perform without having to deploy it first. While most existing works on OPE aim to provide accurate point estimates for short-horizon problems (Thomas et al. 2017, Precup 2000, Hanna et al. 2017, Jiang and Li 2016) as well as long-or infinite-horizon problems (Liu et al. 2018b, Zhang et al. 2020, Tang et al. 2019, Farajtabar et al. 2018, Kallus and Uehara 2019a, Chen et al. 2019), it is equally important to quantify the uncertainty of the OPE point estimates for both safe exploration and optimistic planning. On the one hand, in high-stake mission-critical environments as aforementioned, providing a lower confidence bound for OPE enables us to explore policies with safety guarantees and thus help to reduce the risk and 

> 12

circumvent catastrophic events; specifically, in batch reinforcement learning in which a fixed set of logged data is used for policy optimization, this pessimism principle is important to guarantee good performance (Buckman et al. 2020, Jin et al. 2020). On the other hand, for risk-seeking policy optimization algorithms that apply the optimism principle in the face of uncertainty (Munos 2014), an upper confidence bound used to balance the exploration and exploitation trade-off is desirable. Motivated by these problems, the main goal of this paper is to develop reliable confidence interval (CI) estimates for OPE with provable statistical guarantees. Let us discuss several challenges in deriving a CI for OPE. Arguably, the most straightforward thought is based on the sample mean and sample deviation estimates and invokes some form of concentration inequality to implement. Unfortunately, this could be problematic due to various reasons. (I) To begin with, most existing approaches (Thomas et al. 2015, Hanna et al. 2017) are based on step-wise importance sampling, which do not work in long- or infinite-horizon setting. This is because the OPE point estimate suffers from the “curse of horizon” (Liu et al. 2018b): it has excessively high variance arising from the multiplication of importance ratios at each time period in the horizon. (II) To reduce the variance, one may consider approaches based on a marginalized formulation (Liu et al. 2018b) that applies importance sampling to the average state visitation distribution. Essentially this yields a bilevel stochastic optimization (feasibility) problem (see also equations (2)(3) in Section 2), in which the lower-level problem estimates the marginalized importance weight function and the upper-level problem estimates the cumulative discounted reward. Developing a CI for its optimal value is a highly non-trivial task. (III) Even for asymptotic CIs, existing concentration results for the marginalized formulation (e.g. Kallus and Uehara (2019b)) depend crucially on certain mixing conditions, i.e., the finite-sample distribution of the associated Markov chain should be close to its steady-state distribution. For non-asymptotic CIs, Feng et al. (2020) proposes a variational framework that solves an optimization problem over a confidence set containing the underlying true state-action value function with high probability, but assumes the access to i.i.d. state-action transition pairs, and the length of their CI depends on the sample size in a sub-optimal (fourth-root) rate; Dai et al. (2020) applies the generalized empirical likelihood method to the Lagrangian reformulation of the bilevel stochastic program, which assumes i.i.d. state-action-next-state transition tuples (and may be relaxed to certain fast-mixing condition) and involves a nonconvex-concave saddle-point problem that may not have global optimality guarantees. Unfortunately, the i.i.d. or mixing conditions aforementioned generally do not hold in practice. Indeed, the historical trajectory data may not serve as a faithful representation of the steady-state distribution under the behavior policy, because the number of trajectories in the data set is usually limited or even only one, each of which has dependent data sequence with finite length and thus may not be mixing yet. (IV) In OPE, the environment where the target policy will be deployed may deviate from the past environment where the historical data were collected. For instance, in clinical trials, a medicine or vaccine is initially tested for young and healthy people, but eventually we would like to know its safety and effectiveness on other population such as the elderly people. As such, there is a shift in the age distribution between the training population and the testing population. This is usually referred to as covariate shift or distribution shift in the literature (Si et al. 2020, Kato et al. 2020). In this case, it is important to evaluate the risk of a new policy under adversarial scenarios so that the decision-maker would have a sense of what the worst that could happen and makes plans accordingly. To take these concerns into account, we propose a novel framework for computing CI estimates for the infinite-horizon discounted OPE, inspired from distributionally robust Markov Decision Process (MDP) (Iyengar 2005, Nilim and Ghaoui 2005, Wiesemann et al. 2013). In a nutshell, the idea is to develop a distributionally robust/optimistic counterpart of the marginalized formulation as mentioned 3

in the item (II) above (see formulation (P) in Section 3), whose optimal values serve as the lower/upper confidence bounds for the OPE under proper selection of the radius of the uncertainty set. This gives rise to an end-to-end framework that uses logged trajectory data to simultaneously learn the importance weight function, find the worst-case/best-case scenarios, and compute the CI. Specifically, we consider an s-rectangular Wasserstein distributional uncertainty set (Yang 2017) centered around the empirical conditional action-next-state distributions under the behavior policy, which captures the distributional uncertainty (e.g. adversarial data perturbation and distribution shift) of the average visitation distribution, and naturally incorporates the geometry of the state-action space and is suitable for distributions with non-overlapping support. Our main contributions are as follows. 

• We derive exact tractable reformulations for the distributionally robust and optimistic OPE (Theorem 1), based on which the CI can be computed via robust value iteration algorithm (Algorithm 1). We also develop an equivalent Lagrangian formulation that can be solved numerically in a fashion similar to generative adversarial networks (Goodfellow et al. 2014), in which the discriminator is regularized by its Lipschitz norm (Proposition 3). 

• In stochastic setting, we develop both asymptotic and non-asymptotic CIs for OPE (Theorem 2 and Remark 1), only assuming that the logged data are collected from (one or more) trajectories under the behavior policy and the underlying Markov chain transition dynamics. In adversarial setting where there is a distribution shift due to changing environments, we provide asymptotic and non-asymptotic CIs for the adversarial reward (Theorems 3 and 4). When applying to on-policy problems, our results provide an end-to-end statistical inference approach for robust MDP that directly uses trajectory data without estimating the transition probability matrix. 

• We extend our framework to batch reinforcement learning by developing efficient algorithms and provide finite-sample performance guarantees (Theorems 5 and 6). Our theoretical findings are verified by numerical experiments. 

• Our analysis is based on two new results on Wasserstein distributionally robust optimization in discrete finite space, both of which may be of independent interest. The first result is on its equivalence to a discrete form of Lipschitz regularization; and the second result is a new finite-sample guarantee that does not suffer from the curse of dimensionality, which, to the best of our knowledge, is the first result of this kind in discrete settings. 

1.1. Related Work Uncertainty Quantification for OPE. Recently, there is a surge of interest in studying uncertainty quantification for OPE. Existing works (Feng et al. 2020, Dai et al. 2020, Kallus and Uehara 2019b) assume i.i.d. transitions pairs or mixing condition. The non-asymptotic CI in Dai et al. (2020) is computed from solving a nonconvex-concave optimization involving an 푓 -divergence distributional uncertainty set. The non-asymptotic CI derived in Feng et al. (2020) exploits concentration bounds for U/V-statistics, whose length of the CI depends on the sample size in a sub-optimal fourth-root rate. Asymptotic CIs are developed in Kallus and Uehara (2019b) for a broad class of MDPs using central limit theorem under various mixing conditions. In addition, by assuming the value function can be approximated by linear functions under certain basis, nonasymptotic and asymptotic CIs are constructed in Duan and Wang (2020), Shi et al. (2020), but this approach suffers from model misspecification and may lead to biased estimate. Asymptotic CIs are also derived using bootstrapping (Kostrikov and Nachum 2020) and Bayesian hypothesis testing (Lu et al. 2020). Besides, Jiang and Huang (2020) considers a different notion of the CI that does not capture the randomness of data. For finite, short-horizon problems, CIs are proposed based on concentration inequalities (Thomas et al. 2015) and bootstraping (Hanna et al. 2017). However, those bounds become vacuous due to the large variance of estimators in long- or infinite-horizon problems (Liu et al. 2018b). In all above works, it is assumed that the deployment environment remains the same. OPE for bandit learning under distribution shift is investigated in Si et al. (2020). 4

(Distributionally) Robust MDP and RL. Our framework is closely related to robust MDPs and its distributionally robust counterpart and applications in RL. Robust MDPs take account of the uncertainty in transition dynamics by hedging against a family of transition probability matrices specifying the range of transition probabilities, and rectangularity is a useful property to maintain tractability of the resulting optimization problem (Iyengar 2005, Nilim and El Ghaoui 2005, Wiesemann et al. 2013, Mannor et al. 2016, Goyal and Grand-Clement 2018). Distributionally robust MDP exploits a-priori distributional information to construct the distributional uncertainty set of transition probability distributions (Xu and Mannor 2010). Different distributional uncertainty sets of transition dynamics have been studied, including the set constructed based on relative entropy (Smirnova et al. 2019), Wasserstein metric (Yang 2017, Tirinzoni et al. 2018, Abdullah et al. 2019, Hou et al. 2020, Song and Zhao 2020), 퐿1-norm (Ho et al. 2020), or general statistical distances together with certain moment conditions (Chen et al. 2018). Most of these works do not consider off-policy evaluations with exceptions of Tirinzoni et al. (2018) and Petrik and Russel (2019), which consider entropy-based and Bayesian uncertainty sets, respectively. The idea of using distributionally robust optimization for uncertainty quantification has appeared in the context of simulation optimization (Lam and Zhou 2017, Lam and Qian 2017). In RL, pessimistic MDPs based on offline data are considered in Kidambi et al. (2020), Yu et al. (2020), Matsushima et al. (2020), but the way of uncertainty quantification in these works are orthogonal to our work. Our framework is consistent to the pessimism principle introduced in Buckman et al. (2020), but our bound is data-dependent and thus tighter than their state-wise bound. The rest of this paper is organized as follows. Section 2 presents preliminaries on OPE and robust MDPs. Section 3 outlines our framework for robust and optimistic off-policy evaluation for MDPs with discounted reward. Section 4 derives tractable reformulations and develops algorithms. Section 5 presents the theoretical analysis of the optimistic and robust reward evaluation. Section 6 extends the algorithm to robust batch reinforcement learning, and Section 7 demonstrates some numerical experiments and analysis. The Appendices contain the proofs of all the results. 

## 2. Off-Policy Evaluation 

We consider an infinite-horizon discounted MDP represented by a tuple 〈S, A, 푃, 푅,훾,푑 0〉, where 

S, A denote, respectively, the state and the action spaces, which are assumed to be finite; 푃 =

{푃 (푠′|푠, 푎 )} 푠,푠 ′ ∈S,푎 ∈A is the set of transition probability matrices, where 푃 (푠′|푠, 푎 ) represents the state transition probability from the current state 푠 to the next state 푠′ after taking an action 푎; 푅 =

{푟 (푠, 푎 )} 푠 ∈S,푎 ∈A is the reward table with the (푠, 푎 )-th entry being the reward after taking the action 푎

in state 푠; 훾 ∈ ( 0, 1) is a discount factor; and 푑0 denotes the initial state distribution before executing a policy. A stochastic policy 휋 is represented by a conditional distribution that takes action 푎 with probability 휋 (푎|푠) in state 푠. At each time 푡, a decision maker observes the current state 푠푡 , takes an action 푎푡 according to a policy 휋 (·| 푠푡 ), receives a non-negative reward 푟푡 whose expectation is 푟 (푠푡 , 푎 푡 ),and transit to the next state 푠푡+1 according to transition probability 푃 (푠푡+1 |푠푡 , 푎 푡 ). The performance of a policy 휋 is measured by the expected discounted cumulative reward 푅휋 , or its value , defined as 

푅휋 := (1 −훾) lim   

> 푇→∞

피

[ 푇∑

> 푡=0

훾푡 푟푡

]

,

where the expectation is taken with respect to the distribution of the trajectories under the policy 휋.Off-policy evaluation is the problem of estimating 푅휋 for a new target policy 휋 using a set of trajectory data collected from a behavior policy 휋푏 . As is well-known, OPE with long- or infinite-horizon MDPs suffers from the curse of horizon: the variance of the importance sampling-based estimates grows exponentially with respect to the length of the horizon 푇 . To address this issue, one may consider an alternative formulation of the target policy value based on the marginalized importance sampling of the average visitation distribution of state-action pairs (Liu et al. 2018b). To this end, let us provide an 5

alternative representation of the value 푅휋 . Let 푑휋,푡 be the distribution of the state 푠푡 at time 푡 when executing a policy 휋 with initial distribution 푑0, and define the average visitation distribution as 

푑휋 (푠) := (1 −훾) lim  

> 푇→∞
> 푇

∑

> 푡=0

훾푡푑휋,푡 (푠), 푠 ∈ S, (1) which becomes the steady-state distribution under the policy 휋 when 훾 → 1. By making use of (1) , the value 푅휋 can be expressed in the expectation form 

푅휋 = 피(푠,푎 )∼ 푑휋 [푟 (푠, 푎 )] = ∑  

> 푠∈S,푎 ∈A

푑휋 (푠)휋 (푎 | 푠)푟 (푠, 푎 ),

where we have used the overloaded notation 푑휋 (푠, 푎 ) := 푑휋 (푠)휋 (푎 | 푠). Now define 훽 : S × A → ℝ+ as 

훽푠 (푎) := 휋 (푎 | 푠)

휋푏 (푎 | 푠) , 푠 ∈ S, 푎 ∈ A,

which is assumed to be known or can be estimated from the logged trajectory data. Throughout this paper, we make the following assumptions, which are standard in the literature. 

Assumption 1. The Markov chains induced by 휋 and 휋푏 are ergodic. 

Assumption 2. 푑휋푏 (푠), 훽푠 (푎) > 0 for all 푠 ∈ S, 푎 ∈ A.

Define the marginalized importance ratio 푤 : S → ℝ+ as 

푤 (푠) := 푑휋 (푠)

푑휋푏 (푠) , 푠 ∈ S,

to be the density ratio between the average visitation state distributions of the target policy and that of the behavior policy. By the importance sampling technique, the value 푅휋 for the target policy 휋 can be computed as 

푅휋 = 피(푠,푎 )∼ 푑휋푏

[푤 (푠)훽푠 (푎)푟 (푠, 푎 )] . (2) Thereby, the problem of OPE is transformed into estimating the marginalized importance ratio – also known as stationary distribution correction (Nachum et al. 2019) – with a plethora of approaches developed covering various settings (Xie et al. 2019, Kallus and Uehara 2019a,b, Uehara and Jiang 2019, Tang et al. 2019, Chen et al. 2019, Zhang et al. 2020). With a slight abuse of notation, we use 푑휋 (푠, 푎, 푠 ′) to denote the average visitation probability for the state-action-state pair (푠, 푎, 푠 ′) of a policy 휋, i.e., 푑휋 (푠, 푎, 푠 ′) = 푑휋 (푠)휋 (푎 | 푠)푃 (푠′ | 푠, 푎 ). Using the stationary equation under policy 휋, it can be easily shown that 푤 and 훽 satisfy the following system of stationary equations, whose proof can be found in Appendix EC.1. 

Lemma 1. Let 훾 ∈ ( 0, 1]. Then it holds that 

푤 (푠′)푑휋푏 (푠′) = (1 −훾)푑0 (푠′) + 훾 ∑  

> 푠∈S,푎 ∈A

푑휋푏 (푠, 푎, 푠 ′)훽푠 (푎)푤 (푠), ∀푠′ ∈ S. (3) This lemma helps to develop an estimation of 푤 using the logged trajectory data. Indeed, 푑휋푏 can be estimated directly from the trajectories, thereby 푤 can be obtained by solving (3) , and thus the value 

푅휋 can be computed using (2) . Typically in the literature, it is assumed that the empirical estimation of 푑휋푏 is a good surrogate. However in reality, the empirical estimate from the trajectory may deviate from the deploying environment since we only have access to trajectories with limited length and may face the issue of changing environments. The rest of this paper is devoted to address these issues. 6

## 3. Distributionally Robust and Optimistic Off-Policy Evaluation 

As previously mentioned, the finite-length Markovian trajectory data and potential shifts of MDP environments may both lead to potential estimation error in the importance ratio 푤 and thus the value 

푅휋 . In this section, we develop a distributionally robust/optimistic framework that takes these issues into account. We make the following assumption on the logged trajectory data generation process throughout the remainder of this paper. 

Assumption 3. The trajectories are generated according to the behavior policy 휋푏 and the transition dynamics 푃. Namely, given current state 푠, the action is generated according to 휋푏 (·| 푠); and given the current state 푠 and action 푎, the next state is generated independently according to 푃 (·| 푠, 푎 ).

Note that this is a rather mild assumption requiring nothing more than that the trajectories are consistent with the MDP environment under policy 휋푏 . This implies that conditioning on the current state 푠, we can extract i.i.d. samples (푎, 푠 ′) from the conditional distribution 휋푏 (푎|푠)푃 (푠′|푎, 푠 ) from the trajectories. This is a much weaker assumption than requiring i.i.d. samples (푠, 푎, 푠 ′) that usually are not satisified by the logged trajectories, which are usually assumed in the existing literature. Leveraging ideas from distributionally robust MDP (Wiesemann et al. 2013, Yang 2017), we consider an s-rectangular Wasserstein distributional uncertainty set. Denote by W the Wasserstein metric associated with a metric (transport cost function) 푐 : (S × A)2 → ℝ+:

W (휇, 휈 ) := min    

> 훾∈Γ(휇,휈 )

피( ( 푎,푠 ),(푎′,푠 ′))∼ 훾

[푐 ((푎, 푠 ), (푎′, 푠 ′))] ,

with Γ(휇, 휈 ) represents the joint distribution on (A × S)2 with marginals 휇 and 휈. For any probability distribution 휇 on the state-action-next-state space S × A × S, let 휇 (· , ·| 푠) be the conditional probability distribution on the action-next-state space A × S conditioning on the state 푠 induced from 휇. Denote by D = {( 푠 푗푡 , 푎 푗푡 , 푟 푗푡 )} 1≤푡 ≤푇푗 ,1≤ 푗 ≤퐽 the collected samples under the behavior policy 휋푏 , where D contains 퐽

trajectories with the 푗-th trajectory being (푠 푗

> 1

, 푎 푗

> 1

, 푟 푗

> 1

, . . . , 푠 푗푇푗 , 푎 푗푇푗 , 푟 푗푇 , 푠 푗푇푗 +1). Let 휌 = (휌푠 )푠 ∈S , where 휌푠 is the radius for the Wasserstein ball associated with state 푠, and let ˆ휇 = ( ˆ휇푠 )푠 ∈S , where ˆ휇푠 is the empirical distributions of the conditional action-next-state visitation distributions 푑휋푏 (· , · | 푠) constructed from tuples D:

ˆ휇푠 := 1

푛푠

∑    

> 1≤푡≤푇푗,1≤푗≤퐽

훿(푎푗푡 ,푠 푗푡 +1) 1{( 푠, 푎 푗푡 , 푟 푗푡 ) ∈ D},

and 푛푠 = ∑1≤푡 ≤푇푗 ,1≤ 푗 ≤퐽 1{( 푠, 푎 푗푡 , 푟 푗푡 ) ∈ D} denotes the number of state-action-next-state tuples starting with 푠. It is easy to verify that ∑푠 ∈S 푛푠 = ∑1≤ 푗 ≤퐽 푇푗 . The s-rectangular Wasserstein distributional uncertainty set is defined as 

픐ˆ휇 (휌) :=

{

휇 ∈ P (S × A × S) : W (휇 (· , · | 푠), ˆ휇푠

) ≤ 휌푠, ∀푠 ∈ S

}

.

We propose the following distributionally robust and optimistic formulations, respectively: 

Lˆ휇 (휌)

(

resp . Uˆ휇 (휌)

)

:= min 

> 푤,휇

(

resp . max 

> 푤,휇

) ∑  

> 푠∈S,푎 ∈A

휇 (푠)휋푏 (푎 | 푠)푤 (푠)훽푠 (푎)푟 (푠, 푎 ) (P-a) s.t. 푤 (푠′)휇 (푠′) = (1 −훾)푑0 (푠′) + 훾 ∑  

> 푠∈S,푎 ∈A

휇 (푠, 푎, 푠 ′)훽푠 (푎)푤 (푠), ∀푠′ ∈ S, (P-b) 

휇 ∈ 픐ˆ휇 (휌), 푤 ∈ ℝ|S |+ . (P-c) Via the system of stationary equations (P-b) , every 휇 determines a set of marginalized importance ratio functions compatible with 휇. In particular, the true average visitation distribution under the behavior 7

policy 푑휋푏 satisfies (P-b) with 휇 = 푑휋푏 . When 휌푠 = 0 for all 푠 ∈ S, the optimization problem (P) reduces to the typical sample average formulation studied in the literature (Liu et al. 2018b). Otherwise, the distributional uncertainty set 픐ˆ휇 (휌) induces an uncertainty set {푤 : ∃휇 ∈ 픐ˆ휇 (휌), 푠.푡 ., (P-b) holds } for the importance weight function 푤, which can be viewed as a confidence region for 푤. Under proper selection of the radius {휌푠 }푠 ∈S that will be specified in Section 5, the optimal values of (P) provides a CI estimate [Lˆ휇 (휌), Uˆ휇 (휌)] for 푅휋 . This framework is an end-to-end approach in the sense that it jointly learns the importance weight function, the worst-case/best-case distribution and computing the CI using the logged trajectory data, as opposed to a separate approach that builds the CI based on the estimated importance weight function 푤 using a separate procedure (Mousavi et al. 2020), whereby the estimation error of 푤 may propagate to the CI resulting a larger variance. The advantage of using the s-rectangular Wasserstein distributional uncertainty set is four-fold. First, Wasserstein metric naturally incorporates the geometry of the state-action space, and is suitable for distributions with non-overlapping supports and for hedging against adversarial data perturbations (Gao and Kleywegt 2016). It is purely data-driven whereby ˆ휇 can be directly constructed from the logged trajectories, as opposed to the classical robust MDP literature (e.g. Wiesemann et al. (2013)) in which the nominal transition dynamics are estimated from data using a separate statistical procedure such as maximum likelihood. Second, from the optimization point of view, the s-rectangularity enables a tractable reformulation of (P) that will be presented in Section 4. Third, from the statistical point of view, the s-rectangularity facilitates us to establish a confidence interval with provable guarantees by observing that for any trajectory data, conditioning on the current state 푠, we have i.i.d. samples of action-next-state pairs (푎, 푠 ′) as long as the trajectories are generated according to the behavior policy 

휋푏 (푎|푠) and the transition dynamics 푃 (푠′|푠, 푎 ); see Assumption 3. Fourth, for batch RL setting in Section 6, the 푠-rectanguarity is consistent with the pessimism principle with respect to the state-wise Bellman uncertainty that is introduced in Buckman et al. (2020). 

## 4. Tractable Reformulations and Algorithms 

Problem (P) is not immediately tractable because it involves an optimization over probability distribu-tions as well as a simultaneous optimization over 푤 and 휇. In this section, we provide exact tractable reformulations and algorithms for solving ( P), whose proofs are provided in Appendix EC.2. To simplify the presentation, we state only the results on the distributionally robust OPE, i.e., the minimization problem in (P), and the counterpart for distributionally optimistic OPE can be found in Appendix A. For a function 푓 : S → ℝ, we define the global slope (Ambrosio et al. 2008) of 푓 at 푠 ∈ S as 

픩푓 (푠) = max 

> ˜푠≠푠

푓 (˜푠) − 푓 (푠)

푐 (˜푠, 푠 ) ,

and for any probability measure 휈 ∈ P (S) we define the Lipschitz norm of 푓 with respect to 휈 as 

‖푓 ‖Lip ,휈 = max   

> 푠∈supp (휈)

픩푓 (푠).

Define the following optimization problem on the value function 푣:

max   

> 푣∈ℝ|S|

(1 −훾) ∑

> 푠

푣 (푠)푑0 (푠)

s.t. 푣 (푠) ≤ ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾푉 (푠), ∀푠 ∈ S,

where 푉 (푠) := max  

> 휆≥0

{

− 휆휌 푠 + 1

푛푠푛푠∑

> 푖=1

min   

> 푎∈A,푠 ′∈S

{푣 (푠′)훽푠 (푎) + 휆푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) }}

,

(V)We have the following result showing the equivalence between ( P) and ( V). 8

Theorem 1. For every 푠 ∈ S, let 휖푠 ∈ ( 0, 1−훾 

> 2훾

) and 푀푠 := max 푎 ∈A 훽푠 (푎) − min 푎 ∈A 훽푠 (푎), and assume 휌푠

satisfies 휌푠 ‖훽푠 ‖Lip , ˆ휇푠 ≤ 1−훾 

> 2훾

− 휖푠,. Then with probability at least 1 − ∑푠 ∈S exp (− 2푛푠휖2 

> 푠

/푀푠 ), it holds that 

(I) The vector-valued mapping 

푣 7 →

[∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾푉 (푠)

] 

> 푠∈S

is contractive with Lipschitz constant 1+훾 

> 2

;

(II) The optimal values of (P) and (V) coincide. 

The proof is based on techniques from robust MDP with s-rectangular sets (Wiesemann et al. 2013) and Wasserstein distributionally robust optimization (Esfahani and Kuhn 2018, Blanchet and Murthy 2019, Gao and Kleywegt 2016). One notable difference between Theorem 1 and standard results on s-rectangular robust MDP is that its statement is not deterministic, as the mapping in (I) is contractive only probabilistically. For on-policy evaluation, i.e., 휋 = 휋푏 , we have 훽푠 = 1 and ‖훽푠 ‖Lip , ˆ휇푠 = 푀푠 = 0, (V)becomes deterministic and provides a robust counterpart result of Puterman (1994). Problem (V) can be viewed as a robust Bellman equation, in which 푉 (푠) is the dual reformulation of the robust reward-to-go function min 휇 ∈픐ˆ휇 (휌)

∑푎 ∈A,푠 ′ ∈S 휇 (푎, 푠 ′ | 푠)푣 (푠′)훽푠 (푎). It is clear from Theorem 1 that 푣 satisfies the robust counterpart of the fixed-point condition 

푣 (푠) = ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 min   

> 휇∈픐ˆ휇(휌)

∑  

> 푎∈A,푠 ′∈S

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽푠 (푎), ∀푠 ∈ S, (4) whence 푣 can be solved by value iteration, which is summarized in Algorithm 1. 

Algorithm 1 Value Iteration Algorithm for Robust Reward Evaluation  

> 1:

Input : 훾, ˆ휇, 휌. Initialize 푣 ∈ ℝ|S |+ . 

> 2:

while not converge do  

> 3:

For each 푠 ∈ S, compute 푉 (푠) defined in ( V).  

> 4:

For each 푠 ∈ S, update 

푣 (푠) ← ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 · 푉 (푠) 

> 5:

end while 

The following proposition shows that the iterates in Algorithm 1 are guaranteed to converge into the optimal solution of ( V). 

Proposition 1. Under the setting of Theorem 1, the iterate 푣 in Algorithm 1 converges to the optimal solution to (V).

4.1. A Regularized Lagarangian Perspective 

In this subsection, we provide a different interpretation of (P) and (V) from the perspective of regularization. To this end, we first write the dual form of ( V). 9

Proposition 2. Problem (V) admits a strong dual formulation 

min        

> 휅∈ℝ|S|+,푞 ∈ℝ
> ∑푠∈S푛푠 |A|| S|+

∑  

> 푠∈S,푎 ∈A

휋 (푎 | 푠)휅 (푠)푟 (푠, 푎 )

s.t. (1 −훾)푑0 (푠′) + 훾 ∑  

> 푠∈S,푎 ∈A

훽푠 (푎)휅 (푠)

> 푛푠

∑

> 푖=1

푞(푠) 

> 푖, (푎,푠 ′)

= 휅 (푠′), ∀푠′ ∈ S,

> 푛푠

∑

> 푖=1

∑  

> 푎∈A,푠 ′∈S

푞(푠)

> 푖, (푎,푠 ′)

푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) ≤ 휌푠, ∀푠 ∈ S,

∑  

> 푎∈A,푠 ′∈S

푞(푠) 

> 푖, (푎,푠 ′)

= 1

푛푠

, ∀푖 = 1, 2, . . . , 푛 푠, ∀푠 ∈ S.

(5) This formulation can be interpreted as follows. Note that it can be easily verified that ∑푠 ∈S 휅 (푠) = 1 by adding up the first set of equality constraints in (5) . Thereby the decision variable 휅 can be viewed as the average visitation distribution under the target policy 휋. The decision variable 푞(푠) can be viewed as a transport plan that transports probability mass from the empirical distribution ˆ휇푠 to a new distribution 휇푠 , served as a surrogate for the underlying average state-visitation distribution 푑휋푏 . The first set of constraint in (5) describes the system of stationary equation under the policy 휋. The second and third sets of inequality constraints confines the distribution 휇푠 to be within the Wasserstein ball. When 휇 = 푑휋푏 and 휌푠 = 0 for all 푠 ∈ S, (5) reduces to the bilevel feasibility formulation (2)(3) . Thus, (5) is a robust counterpart that outputs the worst-case average visitation distribution 휅 under the target policy 휋.Introducing a Lagrangian multiplier 푓 for the first set of constraints in (5) , we can obtain an equivalent Lagrangian reformulation of (5). 

Proposition 3. Let Δ|S | be the probability simplex in ℝ|S | . There exists {휌푠 }푠 ∈S ⊂ ℝ+ such that for all 

{휌푠 }푠 ∈S satisfying 휌푠 < 휌푠 , ∀푠 ∈ S, problem (5) is equivalent to 

min   

> 휅∈Δ|S|

max   

> 푓∈ℝ|S|

피푠∼휅,푎 ∼휋 ( · | 푠) [푟 (푠, 푎 )] + ( 1 −훾)피푠∼푑0 [푓 (푠)] + 훾피푠∼휅, (푎,푠 ′)∼ ˆ휇푠 [훽푠 (푎)푓 (푠′)] − 피푠∼휅 [푓 (푠)] −훾피푠∼휅 [휌푠 ‖훽푠 푓 ‖Lip , ˆ휇푠 ].

Proposition 3 indicates that the distributionally robust formulation (P) is equivalent to a weighted Lipschitz regularization on 푓 . This formulation falls into the family of regularized Lagrangian formualtion described in Yang et al. (2020), but it provides a principled Lipschitz regularization resulting from the distributionally robust formulation (P). This min-max formulation is reminiscent of the generative adversarial network (GAN) (Goodfellow et al. 2014) in the deep learning literature, where 

휅 and 푓 are referred to as the generator and discriminator, respectively, and are often parameterized by neural networks. Thus, Proposition 3 suggests an alternative way to solving (P) using deep learning techniques. Meanwhile, substituting 휅 (푠) with ˆ휇 (푠)푤 (푠) for 푠 ∈ S yields 

min   

> 푤≥0

max   

> 푓∈ℝ|S|

(1 −훾)피푠∼푑0 [푓 (푠)] + 피(푠,푎,푠 ′)∼ ˆ휇

[푤 (푠)( 훾 훽 푠 (푎)푓 (푠′) − 푓 (푠) + 피푎0∼휋 ( · | 푠) [푟 (푠, 푎 0)] − 훾휌 푠 ‖훽푠 푓 ‖Lip , ˆ휇푠 ]) ] .

When 휌푠 = 0, ∀푠 ∈ S, this reduces to a feasibility problem that finds an importance weight function 푤

such that 

퐿(푤, 푓 ) := (1 −훾)피푠∼푑0 [푓 (푠)] + 피(푠,푎,푠 ′)∼ ˆ휇

[(훾 훽 푠 (푎)푓 (푠′) − 푓 (푠)) 푤 (푠)] = 0, ∀푓 ∈ ℝ|S | .

In comparison, the algorithm developed in Liu et al. (2018b) solves 

˜퐿(푤, 푓 ) := (1 −훾)피푠∼푑0 [( 1 − 푤 (푠)) 푓 (푠)] + 훾피(푠,푎,푠 ′)∼ ˆ휇

[(푤 (푠)훽푠 (푎) − 푤 (푠′)) 푓 (푠′)] = 0, ∀푓 ∈ F,10 

where F ⊂ ℝ|S | is a suitable family of discriminators. Observe from 

퐿(푤, 푓 ) − ˜퐿(푤, 푓 ) = (1 −훾)피푠∼푑0 [푤 (푠)푓 (푠)] − 피(푠,푎,푠 ′)∼ ˆ휇 [훾 푓 (푠′)푤 (푠′) − 푤 (푠)푓 (푠)] 

that the two objective functions above coinside when ˆ휇 is replaced with 푑휋푏 and 푤 is replaced by the underlying true importance weight function. 

## 5. Uncertainty Quantification 

In this section, we provide uncertainty quantification for OPE under two situations described in the introduction. In Section 5.1, we develop asymptotic and non-asymptotic confidence intervals when the logged trajectory data set contains one or more finite-length (possibly non-stationary) trajectories under the behavior policy. In Section 5.2, we derive the confidence interval estimates of the adversarial reward under changing MDP environments. The results in this section are based on the finite-sample performance guarantees for Wasserstein DRO on the discrete space (Appendix B), which may be of independent interest. Throughout this section and the next section, we define the following parameters for notational simplicity: 

훿푠 = min    

> (푎,푠 ′) ∈ supp 푑휋푏( · ,· | 푠)

푑휋푏 (푎, 푠 ′ | 푠), 훥푠 = 1

( 1−2훿푠 

> 1−훿푠

∨ 2훿푠 −1

> 훿푠

) , 푀푠 := max   

> 푎∈A

훽푠 (푎) − min   

> 푎∈A

훽푠 (푎), 푠 ∈ S,

and assume that |푣 (푠)| ≤ 푀, ∀푠 ∈ S.

5.1. Confidence Interval using Finite-length Trajectories 

In this subsection, we consider a stochastic setting where trajectory data are Markovian. Proofs for results in this section are provided in Appendix EC.3.1. Recall that 푅휋 is the true value of the target policy 휋, and Lˆ휇 (휌), Uˆ휇 (휌) are, respectively, the robust and optimistic value estimates defined in (P). In this subsection, we explicitly use subscript 푛 to denote the dependence on sample size 푛 = (푛푠 )푠 ∈S for relevant quantities. The next theorem establishes non-asymptotic confidence bounds on 푅휋 based on Lˆ휇푛 (휌푛) and Uˆ휇푛 (휌푛).

Theorem 2. For 푠 ∈ S, let 휏푠 > 0, and set 휌푛,푠 =

√ 2휏푠 

> 푛푠

diam (A × S), and 휖푛,푠 = 6 

> 푛푠

. Then with probability at least 1 − ∑푠 ∈S 훼푠 , where 

훼푠 = exp ( −휏푠 +log (| A|( 1+log b푛푠 푀 |S |c) ) +2 exp (− 2푛푠훿2 

> 푠

) + exp 

(

−푛푠 log 훥푠 +log (|A|( 1+log b푛푠 푀 |S |c) ))

,

it holds that 

Lˆ휇푛 (휌푛) − 푑> 

> 0

(퐼 −훾푃 true )−1휖푛 ≤ 푅휋 ≤ Uˆ휇 (휌푛) + 푑> 

> 0

(퐼 −훾푃 true )−1휖푛,

Theorem 2 shows that [Lˆ휇 (휌푛) − 푑> 

> 0

(퐼 − 훾푃 true )−1휖푛, Uˆ휇 (휌푛) + 푑> 

> 0

(퐼 − 훾푃 true )−1휖푛] can be served as a confidence interval for 푅휋 . Each row of the term 푑> 

> 0

(퐼 − 훾푃 true )−1휖푛 is of high-order 푂 (1/푛푠 ), as compared to the length of [Lˆ휇 (휌푛), Uˆ휇 (휌푛)] that has a square-root dependence on 1/푛푠 established in Proposition 4 below. The proof of Theorem 2 is based on a perturbation analysis on the Bellman operator (Lemma EC.6) and a finite-sample performance bound on Wasserstein DRO (Lemma EC.8). In particular, our finite-sample guarantee is based on covering number arguments as opposed to the VC dimension used in Dai et al. (2020). Unlike Dai et al. (2020), Feng et al. (2020), we do not require the assumption that the value function belongs to a reproducing kernel Hilbert space. 11 

Remark 1 (Asymptotic CI). Under the setting of Theorem 2, if we choose the Wasserstein radius 휌푛,푠 =√ 2휏푠 

> 푛푠

diam (A × S) with 휏푠 = 휏 + log (| A|( 1 + log b푛푠 푀 |S |c)) , then with high probability, the underlying reward 푅휋 ∈ [ Lˆ휇 (휌푛) − 푑> 

> 0

(퐼 −훾푃 true )−1휖푛, Uˆ휇 (휌푛) + 푑> 

> 0

(퐼 −훾푃 true )−1휖푛]. Moreover, the probability bound in Theorem 2 converges to 1 − | S |푒−휏 asymptotically. As a consequence, the proposed CI is a (1 − 훼)-asymptotic confidence interval by choosing the parameter 휏 so that 푒−휏+log |S | = 훼.The next proposition provides an upper bound on the length of our proposed CI. 

Proposition 4. For 푠 ∈ S, let 휏푠, 휏 ′ 

> 푠

> 0, 휌푛,푠 =

√ 2휏푠 

> 푛푠

diam (A × S), 푛푠 ≥ 4휏′2  

> 푠훾2
> (1−훾)2

, and set 

휖푛,푠 := 훾휌 푛,푠 max      

> 푣∈ℝ|S|:|푣(푠) | ≤ 푀

‖훽푠푣 ‖Lip ,푑 휋푏 ( · ,· | 푠) .

Then with probability at least 1 − ∑푠 ∈S (exp (−( 2휏 ′2 

> 푠

/푀푠 )) + 2 exp (− 2푛푠훿2 

> 푠

)) , it holds that 

Uˆ휇푛 (휌푛) − Lˆ휇푛 (휌푛) ≤ 2푑푇 

> 0

(퐼 −훾푃 ˆ휇 )−1휖푛,

where 푃ˆ휇푛 (푠, 푠 ′) = ∑푎 ˆ휇 (푎, 푠 ′ | 푠)훽푠 (푎).

Proposition 4 reveals that the length of our established confidence interval depends inversely on 

1/√푛푠 . For small state space in which |S | is viewed as a irrelevant constant, this is optimal; while for large state space, the gap between 1/√푛푠 and 1/√∑푠 ∈S 푛푠 roughly means that our bound has an extra factor of 1/√|S |. Such conservativeness arises from the s-rectangularity of the uncertainty set 

픐ˆ휇 (휌). Nonetheless, the s-rectangularity is designed to maintain tractability for distributionally robust MDP and is seemingly unavoidable; see the NP-hardness discussion in Wiesemann et al. (2013). If we consider the regularized Lagrangian formulation in Section 4.1 and neglect the global optimality of the involved nonconvex problem (as did in Dai et al. (2020)), then an extension of our formulation may achieve optimal sample rate, which is left to the future work. 

5.2. Confidence Interval under Changing Environments 

In this subsection, we consider OPE under distribution shift. Most existing works on OPE for RL are based on a key assumption that the future environment in which the target policy is deployed is the same as the past environment from which the logged trajectory data are collected. As motioned in the introduction, such an assumption may not necessarily hold in practical scenarios. Under the changing environments, the average visitation distribution 푑휋푏 may be different in the future environment, which results in a different value 푅휋 . This holds even when 푑휋푏 is exactly known for the past environment. Hence, it is important to understand the performance of the target policy under adversarial scenarios and quantify its uncertainty. In the spirit of Si et al. (2020) which studies OPE for bandits under distribution shift, we refer to 

Ladv (휌) as the adversarial value under policy 휋 (푠 |푎) = 휋푏 (푠 |푎)훽푠 (푎), defined as the worst-case reward under an adversarial changing environment, with the radius 휌 capturing the discrepancy between the future and the past: 

Ladv (휌) := min 

> 푤,휇

∑  

> 푠∈S,푎 ∈A

휇 (푠)휋푏 (푎 | 푠)푤 (푠)훽푠 (푎)푟 (푠, 푎 )

s.t. 푤 (푠′)휇 (푠′) = (1 −훾)푑0 (푠′) + 훾 ∑  

> 푠∈S,푎 ∈A

휇 (푠, 푎, 푠 ′)훽푠 (푎)푤 (푠), ∀푠′ ∈ S,휇 ∈ 픐푑휋푏 (휌).

(6) The difference between the equation above and (P) is that the center of the Wasserstein ball ˆ휇 in (P) is replaced by the true average visitation distribution 푑휋푏 in the past environment. Different from the 12 

previous subsection, the radius 휌 is fixed and not varying in the sample size, simply because the gap between the future and the past remains even when we have infinite amount of historical data. We are interested in developing a CI for Ladv (휌) using only the logged trajectory data, i.e., based on the empirical estimate Lˆ휇푛 (휌). Proofs for results in this section are provided in Appendix EC.3.2. The following theorem establishes the finite sample guarantee for estimating Ladv (휌) based on 

Lˆ휇푛 (휌). Consider the function space F푠 := {( 푎, 푠 ′) 7 → 훽푠 (푎)푣 (푠′), |푣 (푠′)| ≤ 푀, ∀푠′ ∈ S}. Let 피⊗ [ℜ푛푠 (F푠 )] 

denote the Rademacher complexity of the space F푠 with respect to 푑휋푏 (· , · | 푠) for sample size 푛푠 .

Theorem 3. Let 휏 > 0 and for 푠 ∈ S, let 휖푠 ∈

(

0, 1−훾

> 2훾

)

and set 

퐻푠 = max  

> 푓∈F푠

‖푓 ‖∞, 휄푛,푠 = 21 −훾

(

2피⊗ [ℜ푛푠 (F푠 )] + 퐻푠

√ 휏

2푛푠

)

.

Then there exists {휌푠 }푠 ∈S ⊂ ℝ+ such that for all {휌푠 }푠 ∈S satisfying 휌푠 < 휌푠 and 휌푠 ‖훽푠 ‖Lip ,푑 휋 ( · ,· | 푠) ≤ 1−훾 

> 2훾

− 휖푠 ,

∀푠 ∈ S, with probability at least 1 − ∑푠 훼푠 , where 훼푠 = 2푒−2푛푠 훿2

+ 2푒−휏 + exp (− 2푛푠휖2 

> 푠

/푀푠 ), it holds that 

Lˆ휇푛 (휌) − 푑> 

> 0

(퐼 −훾푃 true )−1휄푛 ≤ Ladv (휌) ≤ Lˆ휇푛 (휌) + 푑> 

> 0

(퐼 −훾푃 true )−1휄푛 .

Note that the term 휄푛 in Theorem 3 and the term 휖푛 in Theorem 2 have different orders of the sample size. This is because the benchmarks are different under stochastic and adversarial settings. In the stochastic setting (Theorem 2), we would like to choose a radius 휌푛 such that the robust reward serves as a high-confidence lower bound, thus the residual 휖푛 is of higher-order than the length of the CI. Whereas in the adversarial setting, the radius of the distributional uncertainty set is fixed in advance, capturing the distribution shift under changing environments. The goal is to provide a CI for the adversarial reward Ladv (휌) using an empirical estimate Lˆ휇푛 (휌), thus the term 휄푛 represents the half length of the CI. Similar to Proposition 4, the length of the confidence interval depends inversely on 

1/√푛푠 .Below we also provide an asymptotic CI for Ladv (휌) based on Lˆ휇 (휌). To ease the exposition, we only consider a single trajectory with length 푇 , but the result is readily generalized to multiple (independent) trajectories. 

Theorem 4. Set 

푟휋 (푠) = ∑

> 푎

푟 (푠, 푎 )휋 (푎 | 푠), 푠 ∈ S,퐷 (푠,푎,푠 ′),(˜푠, ˜푎, ˜푠′) = 1{푠 = ˜푠, 푎 = ˜푎, 푠 ′ = ˜푠′} 1

√푑휋푏 (푠) , 푠, ˜푠, 푠 ′, ˜푠′ ∈ S, 푎, ˜푎 ∈ A,푃휇∗ (푠, 푠 ′) = ∑

> 푎

훽푠 (푎)휇∗ (푎, 푠 ′ | 푠), 푠, 푠 ′ ∈ S,~(푠,푎,푠 ′) = 훾 (1 −훾)

(

(퐼 −훾푃 푇휇∗ )−1푑0푟푇휋 (퐼 −훾푃 푇휇∗ )−1) 

> 푠,푠 ′

훽푠 (푎), 푠, 푠 ′ ∈ S, 푎 ∈ A,

where 휇∗ is the optimal solution to (6) , and Λ ∈ ℝ|S | | A| | S |×| S | | A| | S |+ is defined as 

Λ(푠, (푎,푠 ′)) ,(˜푠, ( ˜푎, ˜푠′)) =

{푑휋푏 (푎, 푠 ′ | 푠)( 1 − 푑휋푏 (푎, 푠 ′ | 푠)) , if (푠, (푎, 푠 ′)) = (˜푠, ( ˜푎, ˜푠′)) ,

−푑휋푏 (푎, 푠 ′ | 푠)푑휋푏 ( ˜푎, ˜푠′ | 푠) if 푠 = ˜푠, (푎, 푠 ′) ≠ ( ˜푎, ˜푠′),

0, otherwise .

Assume that 휌푠 ‖훽푠 ‖Lip ,푑 휋 ( · ,· | 푠) < 1−훾훾 , 푠 ∈ S. Then it holds that 

√푇 (Lˆ휇푇 (휌) − Ladv (휌)) d

−→ N (0,~ 푇 퐷Λ퐷~ ).

Recalling that 푇 = ∑푠 푛푠 , Theorem 4 provides an asymptotic CI with length 푂 (1/√∑푠 푛푠 ), which improves the order in the non-asymptotic CI derived in Theorem 3. 13 

## 6. Distributionally Robust Batch Reinforcement Learning 

Our distributioanlly robust framework can be easily leveraged for batch RL, whereby the decision-maker finds the optimal policy using a fixed set of logged trajectories generated from a behavior policy 휋푏 , by solving the following max-min formulation 

L∗ 

> ˆ휇푛

(휌푛) = sup  

> 휋∈Π

inf     

> 휇∈픐ˆ휇푛 (휌푛)

피휋,휇 

[ ∞∑

> 푡=0

훾푡 푟푡

]

. (7) Let 푅true be the optimal value under the true underlying MDP environment. Below, we develop a robust value iteration algorithm for solving (7) and provide its finite-sample performance guarantee. Proofs for results in this section are given in Appendix EC.4. With a slight abuse of notation 훽휋푠 (푎) := 휋 (푎 |푠)   

> 휋푏(푎|푠)

, define 

max  

> 휋,푣

(1 −훾) ∑

> 푠

푣 (푠)푑0 (푠)

s.t. 푣 (푠) ≤ ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾푉 (푠), ∀푠 ∈ S,

where 푉 (푠) := min    

> 휇∈픐ˆ휇푛 (휌푛)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽휋푠 (푎).

(8) Similar to Theorem 1, this optimization problem can be solved efficiently by robust value iteration. 

Theorem 5. For 푠 ∈ S, let 휖푠 ∈

(

0, 1−훾

> 2훾

)

, and suppose 휌푛,푠 satisfies 휌푛,푠 ‖훽휋푠 ‖Lip , ˆ휇푠 ≤ 1−훾 

> 2훾

− 휖푠 for every deterministic policy 휋. Then with probability at least 1 − ∑푠 ∈S exp (−2푛푠훿2 

> 푠

휖2

> 푠

), it holds that 

(I) The optimal values for problems (7) and (8) coincide; 

(II) Let (푣∗, 휋 ∗) be the optimal solution to problem (8) . Then 푣∗ solves the fixed point equation 

푣 (푠) = max  

> 휋( · | 푠)

∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾푉 (푠), ∀푠 ∈ S, (9) 

and 휋∗ solves the maximization on the right-hand side in (9) :

휋∗ (· | 푠) = arg max  

> 휋( · | 푠)

∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾푉 (푠), ∀푠 ∈ S.

By Theorem 5, we can solve the batch reinforcement learning problem via robust value iteration, and the detailed procedure is presented in Algorithm 2. In each iteration we first obtain the worst-case average visitation distribution of behavior policy conditioned on states, and then perform the policy improvement step. In particular, the policy improvement part will result in a deterministic optimal policy since the objective function is linear with respect to the policy. The next theorem establishes performance guarantees when focusing on the collection of deterministic policies. 

Theorem 6. For 푠 ∈ S, let 휏푠 > 0, 휖푛,푠 = 6 

> 푛푠

, and 휌푛,푠 =

√ 2휏푠 

> 푛푠

diam (A × S). Then with probability at least 

1 − ∑푠 ∈S 훼푠 , where 

훼푠 := exp ( −휏푠 +log (| A|2 (1+log b푛푠 푀 |S |c) ) +2 exp (− 2푛푠훿2 

> 푠

) + exp 

(

−푛푠 log 훥푠 +log (|A|2 (1+log b푛푠 푀 |S |c) ))

,

it holds that 

푅true ≥ L∗ 

> ˆ휇푛

(휌푛) − 푑> 

> 0

(퐼 −훾푃 true )−1휖푛 .14 

Algorithm 2 Value Iteration Algorithm for Robust Batch Reinforcement Learning  

> 1:

Input : ˆ휇, 휌, 훾. Initialize 푣 ∈ ℝ|S |+ . 

> 2:

while not converge do  

> 3:

For each 푠 ∈ S, compute 

휇∗ (· , · | 푠) = arg min   

> 휇∈픐ˆ휇(휌)

∑  

> 푎∈A,푠 ′∈S

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽휋푠 (푎). 

> 4:

For each 푠 ∈ S, update 

푣 (푠) ← max  

> 휋( · | 푠)

∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 ∑  

> 푎∈A,푠 ′∈S

휇∗ (푎, 푠 ′ | 푠)푣 (푠′)훽휋푠 (푎). 

> 5:

end while 

This theorem shows that when choosing the radius 휌푠 = 푂 (1/√푛푠 ), the optimal reward is lower bounded by the estimated robust reward up to a higher order residual. Similar to the discussion in Remark 1, L∗ 

> ˆ휇

(휌푛) is an (1 − 훼)-asymptotic lower bound on the true optimal value 푅true by taking 

휌푠 =

√ 2휏푠 

> 푛푠

diam (A × S) with 휏푠 = 휏 + log (| A|( 1 + log b푛푠 푀 |S |c)) , and the parameter 휏 is chosen such that 

푒−휏+log |S | = 훼.Some recent works including MOReL (Kidambi et al. 2020) and MoPo (Yu et al. 2020) learn pessimistic MDPs based on offline data and then solve the batch reinforcement learning problem. However, their confidence bounds massively rely on the discrepancy between the learned MDP environment and the underlying true MDP environment, which are often conservative in practical settings. Most recently, Kumar et al. (2020) proposes a conservative Q-learning framework for robust batch framework by penalizing Q-values. Their work serves as a counter-part of distributionally robust framework from the perspective of regularization. 

## 7. Numerical Simulations 

In this section, we conduct numerical experiments in two discrete MDP environments to show the performance of the algorithms based on our framework for OPE. The description of two MDP environments is as follows: 

Machine Replacement Problem. This MDP environment (Wiesemann et al. 2013) has 10 states and 

2 actions: Repair and Do Nothing . States 1 to 8 model the states of deterioration of a machine and there are two repair states 푅1 and 푅2. The state 푅1 is a normal repair state with reward 18 , and the state 푅2 is a long repair state with reward 10 . The reward for states 1 to 7 is 20 , and the reward for state 8 is 0. When the action Do Nothing is performed, for 푖 = 1, 2, . . . , 7, the state 푆푖 will remain in its current state with probability 푝 = 0.2, and move to the state 푆푖+1 with probability 푞 = 0.8. States 푆8

and 푅1 will remain in its current state with probability 1. The state 푅2 will remain in its current state with probability 푝 = 0.2, and move to the state 푆1 with probability 푞 = 0.8. When the action Repair 

is performed, for 푖 = 1, 2, . . . , 8, the state 푆푖 will move to repair states 푅1, 푅 2 with probability 0.1, 0.6,respectively, and move to the state 푆min {푖+1,8} with probability 0.3.

Healthcare Management Problem. This MDP (Goyal and Grand-Clement 2018) has six states 

{1, 2, 3, 4, 5, 6} to model the physical conditions of patients, in which the state 6 is an absorbing mortality state. Three actions are available under this setting: Do Nothing (푎1), Prescribe Low Drug Level (푎2), and Prescribe High Drug Level (푎3). The goal of the agent is to minimize the mortality rate of patients and reduce the drug level to lower the harm of treatment. The reward at the state 6 is 0,15 50 400 1200 1800 Number of Trajectories 0.97 0.98 0.99 1.00 1.01 1.02 Normalized Reward    

> Optimistic Reward Robust Reward True Reward 200 1000 1600 2000 Truncation Length 0.98 0.99 1.00 1.01 Normalized Reward  Optimistic Reward Robust Reward True Reward

(a) Machine Replacement Problem 50 400 1200 1800 Number of Trajectories 0.85 0.90 0.95 1.00 1.05 1.10 Normalized Reward    

> Optimistic Reward Robust Reward True Reward 200 1000 1600 2000 Truncation Length 0.95 1.00 1.05 Normalized Reward  Optimistic Reward Robust Reward True Reward

(b) Healthcare Management Problem 

Figure 1 Results for two MDP environments with discounted reward ( 훾 = 0.95 ), in which the ~-axis represents the estimated reward normalized by the underlying true reward under the target policy. The plots show the 95% 

confidence interval of the normalized reward generated by our algorithm across different numbers of trajectories and different truncation lengths. 

while at remaining states, taking the action 푎1, 푎 2, 푎 3 receives reward 10 , 8, 6, respectively. When the action 푎1 is taken, for 푖 = 1, 2, . . . , 5, the state 푆푖 will transit into state 푆푖, 푆 푖+1, 푆 max {1,푖 −1} with probability 

푝1 = 0.4, 푝 2 = 0.3, 푝 3 = 0.3, respectively. When the action 푎2 or 푎3 is taken, the values of [푝1, 푝 2, 푝 3] are replaced with transition probabilities [0.4, 0.2, 0.4] or [0.4, 0.1, 0.5], respectively. In order to simulate the task for OPE numerically, we set the target policy to be the one after running Q-learning for 15 iterations, and set the behavior policy to be the one after 10 iterations. The collected samples of state-action-state pairs are generated under the behavior policy. 

7.1. Confidence Intervals for Non-stationary Trajectory Data 

In this subsection we show the numerical performance for our interval estimates based on non-stationary trajectory data. In particular, we choose the radius size to be the one discussed in Remark 1 to realize the asymptotic 95% coverage rate. Recall that 푇 is the truncation length, and 퐽 is the number of trajectories for observed samples. The default parameters are 푇 = 200 and 퐽 = 200 , unless varying them for performance comparison. The evaluation criterion is our estimated reward normalized by the underlying true reward under the target policy. Figure 1 reports the 95% confidence interval of the normalized reward across different choices of 푇 and 퐽 . As the number of trajectories or truncation length increases, both upper and lower confidence bounds become tighter, which suggests that our algorithm is able to give a reasonable confidence interval for off-policy evaluation with superior data-efficiency. Figure 2 shows the empirical coverage rate for the 95% confidence interval generated by our algorithm with 100 independent trials. The ~-axis represents empirical error rates in which the corresponding confidence intervals do not cover the underlying true reward. The plots indicate that 16 

our method can approximate the allowable 5% error rate for a 95% confidence interval, which justifies that the asymptotic confidence interval constructed in Remark 1 is able to roughly achieve the 95% 

coverage probability. 50 100 200 400 800 Number of Trajectories 0.00 0.05 0.10 0.15 0.20 Failure Probability          

> HMP MRP Error Threshold 200 400 600 800 1000 Truncation Length 0.00 0.05 0.10 0.15 0.20 Failure Probability
> HMP MRP Error Threshold
> Figure 2 Results for two MDP environments with discounted reward ( 훾=0.95 ) on the empirical coverage rate of the constructed 95% confidence intervals. The plots show the empirical error rate generated by 100 independent trials across different numbers of trajectories and different truncation lengths.

7.2. Confidence Intervals for Changing Environment 

Next, we study the uncertainty quantification for OPE under changing environments. Assume that there exist experiment errors during the past MDP environments, and parameters for the transition dynamics will be perturbed a little bit. In particular, parameters for the transition dynamics (푝, 푞 ), (푝1, 푝 2, 푝 3)

in the two MDP environments above are replaced with (푝′ = 푝 + 0.1, 푞 ′ = 푞 − 0.1), (푝′ 

> 1

= 푝1 + 0.01 , 푝 ′ 

> 2

=

푝2 + 0.01 , 푝 ′ 

> 3

= 푝3 − 0.02 ) during the data collection phase. We test the convergence of Lˆ휇푇 (휌) into Ladv (휌) as the trajectory length increases, in which 휌 is chosen to be a constant radius size. Figure 3 shows the estimation of the adversarial reward normalized by its exact value across different number of truncation lengths, where we only use one trajectory to collect samples. Each data point in the plot represents the values of Lˆ휇푇 (휌), and the error bars represent the asymptotic 95% confidence intervals discussed in Theorem 4. Note that the variance stated in Theorem 4 depends on 푑휋푏 and 휇∗, which cannot be obtained exactly. Therefore, we use the approximate variance instead by replacing these terms with ˆ휇 and the optimal solution to Lˆ휇푇 (휌).From the plot we can see that as the sample size increases, both bias and variance for estimated adversarial reward values decrease, which indicates that Lˆ휇푇 (휌) converges into Ladv (휌) well. 

7.3. Distributionally Robust Batch Reinforcement Learning 

Finally, we run experiments on the task of distributionally robust batch reinforcement learning, based on the historical data induced by a single behavior policy. We compare the performance of our robust algorithm with the algorithm based on the sample average approximation (SAA) approach within two MDP environments. These two algorithms are evaluated based on the log of the mean squared error (log MSE) between the estimated optimal reward and the underlying true reward when the MDP environment is exactly known. Figure 4 reports the log MSE of two algorithms across different numbers of trajectories and truncation lengths. Each data point in Figure 4 represents the average of log MSE over 10 independent trials with error bars generated for 95% confidence intervals. From the plot we can see that generally our algorithm reduces log MSE faster than the SAA approach as the sample size increases. Although the last plot in Figure 4 indicates that the mean of log MSE for two algorithms is close to each other, the variance of log MSE for our algorithm is smaller than that for the SAA approach, which demonstrates the robustness of our algorithm. Therefore, we conclude that our algorithm outperforms the SAA approach for the batch reinforcement learning task. 17 1e3 1e4 

Truncation Length    

> 0.90 0.95 1.00 1.05 1.10
> Normalized Reward  T()/ adv ()
> Confidence Interval

(a) Machine Replacement Problem 1e4 1e5 

Truncation Length     

> 0.85 0.90 0.95 1.00 1.05 1.10
> Normalized Reward
> T()/ adv ()
> Confidence Interval

(b) Healthcare Management Problem 

Figure 3 Results on the 95% confidence bound estimate for Ladv . The plots show the robust reward estimates across different truncation lengths within a single trajectory, where error bars are generated based on the asymptotic uncertainty quantification result in Theorem 4. 50 100 200 400 800 Number of Trajectories     

> 5
> 0
> 5
> 10 Log MSE
> SAA Reward Robust Reward 200 400 600 800 1000 Truncation Length
> 6
> 4
> 2
> 0Log MSE
> SAA Reward Robust Reward

(a) Machine Replacement Problem 50 100 200 400 800 Number of Trajectories     

> 4
> 2
> 0
> 2Log MSE
> SAA Reward Robust Reward 200 400 600 800 1000 Truncation Length
> 6
> 5
> 4
> 3
> 2
> 1
> Log MSE
> SAA Reward Robust Reward

(b) Healthcare Management Problem 

Figure 4 Results for two MDP environments with discounted reward ( 훾 = 0.95 ), where the evaluation criterion is chosen to be the MSE between the estimated optimal reward and the underlying true reward when the MDP environment is exactly known. The plots show the log MSE across different number of trajectories and different truncation lengths, in which each data point represents the average of log MSE over 10 independent trials with error bars generated for 95% confidence intervals. 

## 8. Concluding Remarks 

In this paper, we develop a novel framework for computing either non-asymptotic or asymptotic confidence interval estimates for off-policy evaluation in infinite-horizon RL. Unlike existing approaches, we do not assume the restrictive i.i.d. or mixing conditions on the transition tuples and consider both Markovian and adversarial settings. When applying our framework to on-policy problems, our theory provide an end-to-end approach to statistical inference for robust MDP using trajectory data without explicitly estimating the transition probabilities. The length of our proposed CI estimates has an optimal sample rate for small state spaces, in which case we proposed efficient algorithms for both 18 

OPE and batch RL. Our formulation can be naturally extended to the behavior-agnostic setting, in which the behavior policy is not known to the decision maker. Our regularized Lagrangian formulation can be tailored to large or continuous state space by solving a minimax saddle point problem with the Lipschitz regularization, which is left for future work. 

Appendix A: Results for Optimistic OPE 

This section provides tractable formulations for optimistic OPE. It can be reformulated as the following minimization problem: 

min  

> 푣

(1 −훾) ∑

> 푠

푣 (푠)푑0 (푠)

s.t. 푣 (푠) ≥ ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾푉 (푠), ∀푠 ∈ S,푤ℎ푒푟푒 푉 (푠) := min  

> 휆≥0

{

휆휌 푠 + 1

푛푠푛푠∑

> 푖=1

max   

> 푎∈A,푠 ′∈S

{푣 (푠′)훽푠 (푎) − 휆푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) }}

.

Theorem 7. Under the same conditions of Theorem 1, with probability at least 1 − ∑푠 ∈S exp (− 2푛푠휖2 

> 푠

/푀푠 ),the optimal values for the maximization problem (P) and the minimization problem presented above coincide. 

Hence, the optimistic reward can be evaluated by solving for the fixed-point equation 

푣 (푠) = ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 max   

> 휇∈픐ˆ휇(휌)

∑  

> 푎∈A,푠 ′∈S

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽푠 (푎), ∀푠 ∈ S.

With almost the same arguments presented in Section 4.1, we can develop a regularization counterpart for optimistic OPE. This problem with discriminator function constraints can be formulated as 

max        

> 휅∈ℝ|S|+,푞 ∈ℝ
> ∑푠∈S푛푠 |A|| S|+

∑

> (푠,푎 )

휋 (푎 | 푠)휅 (푠)푟 (푠, 푎 )

푠.푡 . (1 −훾)피푠∼푑0 [푓 (푠)] + 훾피푠∼휅

[

피(푎,푠 ′)∼ ∑푛푠 푖=1 푞 (푠 )

> 푖, (푎,푠 ′)

[훽푠 (푎)푓 (푠′)] 

]

= 피푠∼휅 [푓 (푠)] , ∀푓 ∈ ℝ|S |

> 푛푠

∑

> 푖=1

∑  

> 푎∈A,푠 ′∈S

푞(푠)

> 푖, (푎,푠 ′)

푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) ≤ 휌푠, ∀푠 ∈ S

∑  

> 푎∈A,푠 ′∈S

푞(푠) 

> 푖, (푎,푠 ′)

= 1

푛푠

, ∀푖 = 1, 2, . . . , 푛 푠, ∀푠 ∈ S

The following proposition reveals that the optimistic OPE is equivalent to the variation regularization problem. 

Proposition 5. Under the same conditions of Proposition 3, when 휌푠 < 휌푠, 푠 ∈ S, the optimistic OPE is equivalent to 

max   

> 휅≥0

min   

> 푓∈ℝ|S|

피푠∼휅 [피푎∼휋 ( · | 푠) [푟 (푠, 푎 )]] + ( 1 −훾)피푠∼푑0 [푓 (푠)] + 훾피푠∼휅

[피(푎,푠 ′)∼ ˆ휇푠 [훽푠 (푎)푓 (푠′)] ] − 피푠∼휅 [푓 (푠)] +훾피푠∼휅 (푠) 휌푠 · ‖ 훽푠 푓 ‖Lip , ˆ휇푠 .

Using the importance sampling technique, we solve the following problem instead: 

max   

> 푤≥0

min   

> 푓∈ℝ|S|

(1 −훾)피푠∼푑0 [푓 (푠)] + 피(푠,푎,푠 ′)∼ ˆ휇

[(훾 훽 푠 (푎)푓 (푠′) − 푓 (푠) + 피푎0∼휋 ( · | 푠) [푟 (푠, 푎 0)] + 훾휌 푠 · ‖ 훽푠 푓 ‖Lip , ˆ휇푠 ]) 푤 (푠)] .19 

Appendix B: Finite-sample Guarantees for Wasserstein DRO in Discrete Space 

The results in this section are parallel to the results in Gao et al. (2020) which focuses on continuous space. Proofs are given in Appendix B. We begin by introducing some notations in a general setup. Let ℙ푛 denote the empirical distribution constructed from 푛 i.i.d. samples from some underlying true distribution ℙtrue on a finite discrete metric space Z associated with a metric 푐 : Z2 → ℝ+. Let F be a class of functions on Z. We define the 

Wasserstein regularizer for a function 푓 ∈ F as 

R푛 (휌; 푓 ) := sup 

> ℙ

{피푧∼ℙ [푓 (푧)] : W (ℙ, ℙ푛) ≤ 휌} − 피푧∼ℙ푛 [푓 (푧)] .

The global slope of a function 푓 ∈ F at 푧 ∈ Z is defined as 

픩푓 (푧) = max 

> ˜푧≠푧

푓 (˜푧) − 푓 (푧)

푐 (˜푧, 푧 ) ,

and the Lipschitz norm of 푓 with respect to ℙ is defined as 

‖푓 ‖Lip ,ℙ = max    

> 푧∈supp ℙ

픩푓 (푧).

The following result shows the equivalence between Wasserstein DRO in discrete space and Lipschitz regularization. 

Proposition 6. Define Z∞ := {푧 ∈ Z : 픩푓 (푧) = ‖푓 ‖Lip ,ℙ푛 } and 

¯휌 := sup 

> É:Z→Z

{

피ℙ푛 [푐 (É(푧), 푧 )] : É(푧) = 푧, ∀푧 ∉ Z∞, 푓 (É(푧)) − 푓 (푧)

푐 (É(푧), 푧 ) = 픩 푓 (푧), ∀푧 ∈ Z∞

}

.

Then for any 휌 < ¯휌, it holds that 

R푛 (휌; 푓 ) = 휌 · ‖ 푓 ‖Lip ,ℙ푛 .

Next, we study the finite-sample performance guarantee for Wasserstein DRO in discrete space. We introduce a metric d on F

d( ˜푓 , 푓 ) := ‖ ˜푓 − 푓 ‖∞ ∨ ‖ ˜푓 − 푓 ‖lip , ∀ ˜푓 , 푓 ∈ F,

where ‖ · ‖ ∞ and ‖ · ‖ Lip denotes the sup-norm and Lipschitz norm respectively. Denote by N (휖, F, d)

the 휖-covering number of F under the metric d, defined as the smallest cardinality of an 휖-cover of F, where the collection of functions F휖 is called an 휖-cover of F if for any 푓 ∈ F, there exists 

푓 ′ ∈ F휖 so that d(푓 , 푓 ′) ≤ 휖. Finally, let 퐻 (푎‖푏) denote the binary relative entropy function 퐻 (푎‖푏) :=

푎 log 푎푏 + ( 1 − 푎) log 1−푏 

> 1−푎

.

Assumption 4. Suppose F satisfies the following conditions: 

(I) There exists 퐿 > 0 so that 푓 (˜푧) − 푓 (푧) ≤ 퐿푐 (˜푧, 푧 ) for all 푧, ˜푧 ∈ Z and all 푓 ∈ F.

(II) There exists 휂 ∈ ( 0, 1] such that 훿 := inf 푓 ∈F ℙtrue 

{푧 ∈ Z : 픩푓 (푧) ≥ 휂 ‖푓 ‖Lip ,ℙtrue 

} ∈ ( 0, 1).

Proposition 7. Assume Assumption 4 holds. Suppose that 휌푛 = 휌0/√푛 for some 휌0 > 0. Let 푐 < 훿 

> 1−훿

∧ 1−훿훿 .Then with probability at least 1 − exp ( − 푛퐻 (푐 ‖ 훿 

> 1−훿

∧ 1−훿훿

) + log N ( 1 

> 푛

, F, d)), simultaneously for all 푓 ∈ F,

휂휌 푛 ‖푓 ‖Lip ,ℙ푛 − 3 

> 푛

≤ R푛 (휌푛; 푓 ) ≤ 휌푛 ‖푓 ‖Lip ,ℙ푛

Note that this result appears in (Gao et al. 2020, Theorem 2) in a slightly different form for a continuous space. Next, we establish the out-of-sample performance guarantee for Wasserstein DRO on a discrete space. Comparing with the discussion in (Gao et al. 2020), our analysis is easier since the variation only relies on the global slope of a function. Define diam (Z) := max ˜푧,푧 ∈Z 푐 (˜푧, 푧 ).20 

Proposition 8. Assume Assumption 4 holds. Let 휏 > 0. Set 휌푛 = 휂diam (Z)√2휏/푛. Then with probability at least 

1 − exp 

(

−휏 + log N

( 1 

> 푛

, F, d

)) 

− 2푒−2푛훿 2

− exp 

(

푛 log 

( 1 − 2훿

1 − 훿 ∨ 2훿 − 1

훿

)

+ log N

( 1 

> 푛

, F, d

))

,

simultaneously for all 푓 ∈ F,

피푧∼ℙtrue [푓 (푧)] ≤ 피푧∼ℙ푛 [푓 (푧)] + R푛 (휌푛; 푓 ) + 6

푛 .

This indicates that with high probability, by setting the radius in the order of 푂 (diam (Z)/ √푛), the Wasserstein robust loss dominates the true loss up to a higher order remainder. Note that if one choose 

휌푛 using the principle in Esfahani and Kuhn (2018), namely, a high confidence bound on the Wasserstein distance between ℙ푛 and ℙtrue , then one would only obtain a much worse bound 푂 (| Z |/ √푛) that linearly depends on the carnality of Z (Singh and Póczos 2018). This is the curse of dimension in discrete settings: imagine Z is an 휖-covering of a 푘-dimensional unit box, then |Z | = 푂 (휖−푘 ). Our bound does not suffer from the curse of dimensionality which, to the best of knowledge, is the first result of this kind for Wasserstein DRO on a discrete space. The difference between this result and the result on a continuous space (Gao et al. 2020) is that local slope does not serve as the regularization term, which simplifies the analysis on the out-of-sample performance guarantee. We will instantiate this result on OPE and show that the tail probability has a mild dependence on 푛.Finally, we discuss the generalization bound for Wasserstein DRO with fixed radius. 

Proposition 9. Let 훿 = min 푧 ∈Z ℙtrue (푧). Suppose that the function 푓 satisfies 0 ≤ 푓 (푧) ≤ 푀, ∀푧 ∈ Z and 

휌 < 휌 = sup 

> É:Z→Z

{

피ℙ푛 [푐 (É(푧), 푧 )] : É(푧) = 푧, ∀푧 ∉ Z∞, 푓 (É(푧)) − 푓 (푧)

푐 (É(푧), 푧 ) = 픩 푓 (푧), ∀푧 ∈ Z∞

}

.

Define the following two risk functions in which the radius is 휌 and the nominal distributions are different: 

푈 ∗ (휌; 푓 ) = sup 

> ℙ

{피ℙ [푓 (푧)] : 푊 (ℙ, ℙtrue ) ≤ 휌}, 푈푛 (휌; 푓 ) = sup 

> ℙ

{피ℙ [푓 (푧)] : 푊 (ℙ, ℙ푛) ≤ 휌}.

Let 휏 > 0. Then with probability at least 1 − 2푒−2푛훿 2

− 2푒−휏 , simultaneously for all 푓 ∈ F, it holds that 

|푈 ∗ (휌; 푓 ) − 푈푛 (휌; 푓 )| ≤ 푈푛 (휌; 푓 ) + 2피⊗ [픐푛 (F)] + 푀

√ 휏

2푛 .

## References 

Abdullah MA, Ren H, Ammar HB, Milenkovic V, Luo R, Zhang M, Wang J (2019) Wasserstein robust reinforcement learning. arXiv preprint arXiv:1907.13196 .Ambrosio L, Gigli N, Savaré G (2008) Gradient flows: in metric spaces and in the space of probability measures 

(Springer Science & Business Media). Billingsley P (1961) Statistical methods in markov chains. The Annals of Mathematical Statistics 12–40. Blanchet J, Murthy K (2019) Quantifying distributional model risk via optimal transport. Mathematics of Operations Research 44(2):565–600. Buckman J, Gelada C, Bellemare MG (2020) The importance of pessimism in fixed-dataset policy optimization. 

arXiv preprint arXiv:2009.06799 .Chen X, Wang L, Hang Y, Ge H, Zha H (2019) Infinite-horizon off-policy policy evaluation with multiple behavior policies. arXiv preprint arXiv:1910.04849 .21 Chen Z, Yu P, Haskell WB (2018) Distributionally robust optimization for sequential decision making. arXiv preprint arXiv:1801.04745 .Dai B, Nachum O, Chow Y, Li L, Szepesvári C, Schuurmans D (2020) Coindice: Off-policy confidence interval estimation. arXiv preprint arXiv:2010.11652 .Duan Y, Wang M (2020) Minimax-optimal off-policy evaluation with linear function approximation. arXiv preprint arXiv:2002.09516 .Esfahani PM, Kuhn D (2018) Data-driven distributionally robust optimization using the wasserstein metric: Performance guarantees and tractable reformulations. Mathematical Programming 171(1-2):115–166. Farajtabar M, Chow Y, Ghavamzadeh M (2018) More robust doubly robust off-policy evaluation. arXiv preprint arXiv:1802.03493 .Feng Y, Ren T, Tang Z, Liu Q (2020) Accountable off-policy evaluation with kernel bellman statistics. arXiv preprint arXiv:2008.06668 .Gao R (2020) Finite-sample guarantees for wasserstein distributionally robust optimization: Breaking the curse of dimensionality. arXiv preprint arXiv:2009.04382 .Gao R, Chen X, Kleywegt AJ (2020) Wasserstein distributionally robust optimization and variation regularization. 

arXiv preprint arXiv:1712.06050 .Gao R, Kleywegt AJ (2016) Distributionally robust stochastic optimization with wasserstein distance. arXiv preprint arXiv:1604.02199 .Goodfellow I, Pouget-Abadie J, Mirza M, Xu B, Warde-Farley D, Ozair S, Courville A, Bengio Y (2014) Generative adversarial nets. Advances in neural information processing systems , 2672–2680. Gottesman O, Johansson F, Komorowski M, Faisal A, Sontag D, Doshi-Velez F, Celi LA (2019) Guidelines for reinforcement learning in healthcare. Nat Med 25(1):16–18. Goyal V, Grand-Clement J (2018) Robust markov decision process: Beyond rectangularity. arXiv preprint arXiv:1811.00215 .Hanna JP, Stone P, Niekum S (2017) Bootstrapping with models: Confidence intervals for off-policy evaluation. 

Thirty-First AAAI Conference on Artificial Intelligence .Ho CP, Petrik M, Wiesemann W (2020) Partial policy iteration for l1-robust markov decision processes. arXiv preprint arXiv:2006.09484 .Hou L, Pang L, Hong X, Lan Y, Ma Z, Yin D (2020) Robust reinforcement learning with wasserstein constraint. 

arXiv preprint arXiv:2006.00945 .Iyengar GN (2005) Robust dynamic programming. Math. Oper. Res. 30(2):257–280, ISSN 0364-765X. Jiang N, Huang J (2020) Minimax confidence interval for off-policy evaluation and policy optimization. arXiv preprint arXiv:2002.02081 .Jiang N, Li L (2016) Doubly robust off-policy value evaluation for reinforcement learning. International Conference on Machine Learning , 652–661. Jin Y, Yang Z, Wang Z (2020) Is pessimism provably efficient for offline rl? arXiv preprint arXiv:2012.15085 .Kallus N, Uehara M (2019a) Double reinforcement learning for efficient off-policy evaluation in markov decision processes. arXiv preprint arXiv:1908.08526 .Kallus N, Uehara M (2019b) Efficiently breaking the curse of horizon in off-policy evaluation with double reinforcement learning. arXiv preprint arXiv:1909.05850 .Kato M, Uehara M, Yasui S (2020) Off-policy evaluation and learning for external validity under a covariate shift. 

arXiv preprint arXiv:2002.11642 .Kidambi R, Rajeswaran A, Netrapalli P, Joachims T (2020) Morel : Model-based offline reinforcement learning. 

arXiv preprint arXiv:2005.05951 .Kober J, Bagnell JA, Peters J (2013) Reinforcement learning in robotics: A survey. Int. J. Rob. Res. 32(11):1238–1274, ISSN 0278-3649. 22 Kostrikov I, Nachum O (2020) Statistical bootstrapping for uncertainty estimation in off-policy evaluation. arXiv preprint arXiv:2007.13609 .Kumar A, Zhou A, Tucker G, Levine S (2020) Conservative q-learning for offline reinforcement learning. Lam H, Qian H (2017) Optimization-based quantification of simulation input uncertainty via empirical likelihood. 

arXiv preprint arXiv:1707.05917 .Lam H, Zhou E (2017) The empirical likelihood approach to quantifying uncertainty in sample average approximation. Operations Research Letters 45(4):301–307. Liu F, Tang R, Li X, Ye Y, Chen H, Guo H, Zhang Y (2018a) Deep reinforcement learning based recommendation with explicit user-item interactions modeling. ArXiv abs/1810.12027. Liu Q, Li L, Tang Z, Zhou D (2018b) Breaking the curse of horizon: Infinite-horizon off-policy estimation. Bengio S, Wallach H, Larochelle H, Grauman K, Cesa-Bianchi N, Garnett R, eds., Advances in Neural Information Processing Systems 31 , 5356–5366 (Curran Associates, Inc.). Lu J, Celi LA, Cai T, Szolovits P, et al. (2020) Expert-supervised reinforcement learning for offline policy learning and evaluation. arXiv preprint arXiv:2006.13189 .Mandel T, Liu YE, Levine S, Brunskill E, Popovic Z (2014) Offline policy evaluation across representations with applications to educational games. AAMAS , 1077–1084. Mannor S, Mebel O, Xu H (2016) Robust mdps with k-rectangular uncertainty. Math. Oper. Res. 41:1484–1509. Matsushima T, Furuta H, Matsuo Y, Nachum O, Gu S (2020) Deployment-efficient reinforcement learning via model-based offline optimization. arXiv preprint arXiv:2006.03647 .Mnih V, Kavukcuoglu K, Silver D, Rusu AA, Veness J, Bellemare MG, Graves A, Riedmiller M, Fidjeland AK, Ostrovski G, Petersen S, Beattie C, Sadik A, Antonoglou I, King H, Kumaran D, Wierstra D, Legg S, Hassabis D (2015) Human-level control through deep reinforcement learning. Nature 518(7540):529–533. Mousavi A, Li L, Liu Q, Zhou D (2020) Black-box off-policy estimation for infinite-horizon reinforcement learning. 

arXiv preprint arXiv:2003.11126 .Munos R (2014) From bandits to monte-carlo tree search: The optimistic principle applied to optimization and planning. Foundations and Trends ® in Machine Learning 7(1):1–129, ISSN 1935-8237. Nachum O, Chow Y, Dai B, Li L (2019) Dualdice: Behavior-agnostic estimation of discounted stationary distribution corrections. arXiv:1906.04733 .Nilim A, El Ghaoui L (2005) Robust control of markov decision processes with uncertain transition matrices. 

Operations Research 53(5):780–798. Nilim A, Ghaoui LE (2005) Robust control of markov decision processes with uncertain transition matrices. 

OPERATIONS RESEARCH 53(5):780–798. OpenAI, Berner C, Brockman G, Chan B, Cheung V, Dębiak P, Dennison C, Farhi D, Fischer Q, Hashme S, Hesse C, Józefowicz R, Gray S, Olsson C, Pachocki J, Petrov M, de Oliveira Pinto HP, Raiman J, Salimans T, Schlatter J, Schneider J, Sidor S, Sutskever I, Tang J, Wolski F, Zhang S (2019) Dota 2 with large scale deep reinforcement learning. arXiv preprint arXiv:1912.06680 .Petrik M, Russel RH (2019) Beyond confidence regions: Tight bayesian ambiguity sets for robust mdps. Advances in Neural Information Processing Systems , 7049–7058. Precup D (2000) Eligibility traces for off-policy policy evaluation. Computer Science Department Faculty Publication Series 80. Puterman ML (1994) Markov Decision Processes: Discrete Stochastic Dynamic Programming (USA: John Wiley & Sons, Inc.), 1st edition, ISBN 0471619779. Raghu A, Komorowski M, Ahmed I, Celi L, Szolovits P, Ghassemi M (2017) Deep reinforcement learning for sepsis treatment. arXiv preprint arXiv:1711.09602 .Sallab AE, Abdou M, Perot E, Yogamani SK (2017) Deep reinforcement learning framework for autonomous driving. ArXiv abs/1704.02532. Shapiro A, Dentcheva D, Ruszczynski A (2014) Lectures on Stochastic Programming: Modeling and Theory, Second Edition (USA: Society for Industrial and Applied Mathematics), ISBN 1611973422. 23 Shi C, Zhang S, Lu W, Song R (2020) Statistical inference of the value function for reinforcement learning in infinite horizon settings. arXiv preprint arXiv:2001.04515 .Si N, Zhang F, Zhou Z, Blanchet J (2020) Distributional robust batch contextual bandits. arXiv preprint arXiv:2006.05630 .Singh S, Póczos B (2018) Minimax distribution estimation in wasserstein distance. ArXiv abs/1802.08855. Sion M (1958) On general minimax theorems. Pacific J. Math. 8(1):171–176. Smirnova E, Dohmatob E, Mary J (2019) Distributionally robust reinforcement learning. ArXiv abs/1902.08708. Song J, Zhao C (2020) Optimistic distributionally robust policy optimization. arXiv preprint arXiv:2006.07815 .Tang Z, Feng Y, Li L, Zhou D, Liu Q (2019) Doubly robust bias reduction in infinite horizon off-policy estimation. 

arXiv preprint arXiv:1910.07186 .Thomas PS, Theocharous G, Ghavamzadeh M (2015) High-confidence off-policy evaluation. Twenty-Ninth AAAI Conference on Artificial Intelligence .Thomas PS, Theocharous G, Ghavamzadeh M, Durugkar I, Brunskill E (2017) Predictive off-policy policy evaluation for nonstationary decision problems, with applications to digital marketing. Singh SP, Markovitch S, eds., 

Proceedings of the Thirty-First AAAI Conference on Artificial Intelligence, February 4-9, 2017, San Francisco, California, USA , 4740–4745 (AAAI Press). Tirinzoni A, Chen X, Petrik M, Ziebart BD (2018) Policy-conditioned uncertainty sets for robust markov decision processes. Proceedings of the 32nd International Conference on Neural Information Processing Systems ,8953–8963, NIPS’18 (Red Hook, NY, USA: Curran Associates Inc.). Uehara M, Jiang N (2019) Minimax weight and q-function learning for off-policy evaluation. arXiv preprint arXiv:1910.12809 .Wang L, Zhang W, He X, Zha H (2018) Supervised reinforcement learning with recurrent neural network for dynamic treatment recommendation. Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining , 2447–2456, KDD18 (New York, NY, USA: Association for Computing Machinery), ISBN 9781450355520. Wiesemann W, Kuhn D, Rustem B (2013) Robust markov decision processes. Math. Oper. Res. 38(1):153–183, ISSN 0364-765X. Xie T, Ma Y, Wang YX (2019) Towards optimal off-policy evaluation for reinforcement learning with marginalized importance sampling. Advances in Neural Information Processing Systems , 9668–9678. Xu H, Mannor S (2010) Distributionally robust markov decision processes. Advances in Neural Information Processing Systems , 2505–2513. Yang I (2017) A convex optimization approach to distributionally robust markov decision processes with wasserstein distance. IEEE control systems letters 1(1):164–169. Yang M, Nachum O, Dai B, Li L, Schuurmans D (2020) Off-policy evaluation via the regularized lagrangian. arXiv preprint arXiv:2007.03438 .Yu T, Thomas G, Yu L, Ermon S, Zou J, Levine S, Finn C, Ma T (2020) Mopo: Model-based offline policy optimization. arXiv preprint arXiv:2005.13239 .Zhang R, Dai B, Li L, Schuurmans D (2020) Gendice: Generalized offline estimation of stationary values. 

International Conference on Learning Representations .ec1 

# Proofs of Statements 

## Appendix EC.1: Proofs for Section 2 

Proof of Lemma 1. By using the definition for average visitation distribution 푑휋 in (1) , it can be shown that the following linear system holds (Liu et al. 2018b, Lemma 3): 

푑휋 (푠′) = (1 −훾)푑0 (푠′) + 훾 ∑

> (푠,푎 )

푃 (푠′ | 푠, 푎 )휋 (푎 | 푠)푑휋 (푠), ∀푠′ ∈ S,

Substituting 푑휋 (푠) with 푤 (푠)푑휋푏 (푠) in the equalities above gives 

푤 (푠′)푑휋푏 (푠′) = (1 −훾)푑0 (푠′) + 훾 ∑

> (푠,푎 )

푃 (푠′ | 푠, 푎 )휋 (푎 | 푠)푤 (푠)푑휋푏 (푠), ∀푠′ ∈ S.

Then using the relation 푑휋푏 (푠, 푎, 푠 ′) = 푃 (푠′ | 푠, 푎 )휋푏 (푎 | 푠)푑휋푏 (푠) completes the proof. 

## Appendix EC.2: Proofs for Section 4 

EC.2.1. Proof of Theorem 1 

We need several technical lemmas before the proof of Theorem 1. 

Lemma EC.1. For fixed state 푠 ∈ S, value function 푣, and the empirical distribution ˆ휇 (· , · | 푠) = 1

> 푛푠

∑푛푠 

> 푖=1

훿(푎푖 ,푠 ′  

> 푖)

,the optimization 

min   

> 휇∈픐ˆ휇(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽푠 (푎) (EC.1) 

can be equivalently formulated as 

min  

> 휇푖( · ,·) , 푖 =1,2,...,푛 푠

{

1

푛푠푛푠∑

> 푖=1

휇푖 (푎, 푠 ′)푣 (푠′)훽푠 (푎) : 1

푛푠푛푠∑

> 푖=1

휇푖 (푎, 푠 ′)푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) ≤ 휌

}

,

where 푐 (( 푎1, 푠 ′

> 1

), (푎2, 푠 ′

> 2

)) denotes the transportation cost between the action-state pair (푎1, 푠 ′

> 1

) and (푎2, 푠 ′

> 2

).The optimal value can also be computed from the one-dimensional dual problem: 

max  

> 휅≥0

{

− 휅휌 + 1

푛푠푛푠∑

> 푖=1

min 

> (푎,푠 ′)

{

푣 (푠′)훽푠 (푎) + 휅푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) 

}} 

.

Proof. The problem (EC.1) can be viewed as the minimization of the expectation with respect to the probability measure within a Wasserstein ball. Applying duality results in (Blanchet and Murthy 2019, Gao and Kleywegt 2016) completes the proof. 

Lemma EC.2. The min-min problem in (P) can be equivalently formulated as: 

min 

> 휅,휇

∑

> 푠

휅 (푠) ∑

> 푎

휋푏 (푎 | 푠)훽푠 (푎)푟 (푠, 푎 ) = ∑

> 푠

휅 (푠) ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) (EC.2a) 

subject to 휅 (푠′) = (1 −훾)푑0 (푠′) + 훾 · ∑

> 푠

휅 (푠)

[

1(휇 (푠) > 0) ∑

> 푎

휇 (푠, 푎, 푠 ′)

휇 (푠) 훽푠 (푎)

]

, ∀푠′ ∈ S, (EC.2b) 

휇 ∈ 픐ˆ휇 (휌). (EC.2c) 

Note that this equivalence is independent of the structure of the ambiguity set. Proof. The result follows simply by the change-of-variable technique with 휅 (푠) = 푤 (푠)휇 (푠). ec2 

In particular, when 휇 (푠0) = 0 for some 푠0 ∈ S, by the stationarity constraint (EC.2b) we can assert that 휅 (푠0) = (1 −훾)푑0 (푠0). After substituting 휅 (푠) = (1 −훾)푑0 (푠0) for all 푠 in the set ¯S = {푠 ∈ S : 휇 (푠) = 0},the problem is reduced into a problem with smaller size so that the decision variable becomes 

{휅 (푠), 푠 ∈ S \ ¯S}. Without loss of generality, we can assume that for any 휇 ∈ P, the marginal distribution for state 휇 (푠) > 0 for any 푠 ∈ S. Then the indicator term in (EC.2b) can be omitted, and we denote the fraction 휇 (푠,푎,푠 ′)  

> 휇(푠)

as the conditional probability 휇 (푎, 푠 ′ | 푠) for simplicity. Taking the duality for the minimization over 휇 in (EC.2) , we reformulate the min-min problem as a min-max problem. 

Lemma EC.3. The min-min problem in (EC.2) can be equivalently formulated as: 

min  

> 휇

max  

> 푣

(1 −훾) ∑

> 푠

푣 (푠)푑0 (푠) (EC.3a) 

푠.푡 . 푣 (푠) ≤ ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 ∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽푠 (푎), ∀푠 ∈ S, (EC.3b) 

휇 ∈ 픐ˆ휇 (휌). (EC.3c) The following lemma from Nilim and El Ghaoui (2005) is useful for the reformulation of the min-max problem (EC.3). 

Lemma EC.4. Let 푐 ∈ ℝ푛 

> +

and 푓 : ℝ푛 

> +

→ ℝ푛 

> +

be a component-wise non-decreasing contraction mapping. Then { max 푐푇 푥

subject to 푥 ≤ 푓 (푥)

}

= 푐푇 푥∗,

where 푥∗ is the fixed point of the contraction mapping 푓 , i.e. 푥∗ = 푓 (푥∗).

Define a mapping Trob : ℝ|S | → ℝ|S |+ as 

Trob [푣] =

(

min 휇 ∈픐ˆ휇 (휌)

∑푎 휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 ∑(푎,푠 ′) 휇 (푎, 푠 ′ | 푠)푣 (푠′)훽푠 (푎)

) 

> 푠∈S

, 푣 ∈ ℝ|S | . (EC.4) 

Lemma EC.5. Under the setting of Theorem 1, Trob is a component-wise non-decreasing, and is contractive with constant 1+훾 

> 2

with probability at least 1 − ∑푠 ∈S exp 

(

− 2푛푠 휖2

> 푠
> 푀푠

)

.Proof. Trob is component-wise non-decreasing because of the non-negativity of {휇 (푎, 푠 ′ | 푠)훽푠 (푎)} 푎,푠 ′

for any fixed 푠. For any 푣1, 푣 2 ∈ ℝ|S |+ and 푠 ∈ S, we have 

Trob (푣1)푠 = ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 min   

> 휇∈픐ˆ휇(휌)

∑

> 푎,푠 ′

휇 (푎, 푠 ′ | 푠)푣1 (푠′)훽푠 (푎)

= ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 min   

> 휇∈픐ˆ휇(휌)

{ ∑

> 푎,푠 ′

휇 (푎, 푠 ′ | 푠)푣2 (푠′)훽푠 (푎) + ∑

> 푎,푠 ′

휇 (푎, 푠 ′ | 푠) [ 푣1 (푠′) − 푣2 (푠′)] 훽푠 (푎)

}

≥ ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 min   

> 휇∈픐ˆ휇(휌)

∑

> 푎,푠 ′

휇 (푎, 푠 ′ | 푠)푣2 (푠′)훽푠 (푎)+훾 min   

> 휇∈픐ˆ휇(휌)

∑

> 푎,푠 ′

휇 (푎, 푠 ′ | 푠) [ 푣1 (푠′) − 푣2 (푠′)] 훽푠 (푎)

= Trob (푣2)푠 +훾 min   

> 휇∈픐ˆ휇(휌)

∑

> 푎,푠 ′

휇 (푎, 푠 ′ | 푠) [ 푣1 (푠′) − 푣2 (푠′)] 훽푠 (푎).

It follows that 

Trob (푣2)푠 −Trob (푣1)푠 ≤ 훾 max   

> 휇∈픐ˆ휇(휌)

∑

> 푎,푠 ′

휇 (푎, 푠 ′ | 푠) [ 푣2 (푠′) − 푣1 (푠′)] 훽푠 (푎) ≤ 훾 ‖푣1 −푣2 ‖∞ · max   

> 휇∈픐ˆ휇(휌)

∑

> 푎,푠 ′

휇 (푎, 푠 ′ | 푠)훽푠 (푎).ec3 

Applying Proposition 6, we can assert that 

max   

> 휇∈픐ˆ휇(휌)

∑

> 푎,푠 ′

휇 (푎, 푠 ′ | 푠)훽푠 (푎) ≤ ∑

> 푎,푠 ′

ˆ휇 (푎, 푠 ′ | 푠)훽푠 (푎) + 휌푠 · ‖ 훽푠 ‖Lip , ˆ휇푠 .

Applying the Hoeffding upper bound implies that for any 휖푠 > 0,

ℙ

( ∑

> 푎,푠 ′

ˆ휇 (푎, 푠 ′ | 푠)훽푠 (푎) ≥ 1 + 휖푠

)

≤ exp 

(

− 2푛푠휖2

> 푠

푀푠

)

, where 푀푠 = max  

> 푎

훽푠 (푎) − min  

> 푎

훽푠 (푎).

Therefore, with probability at least 1 − exp 

(

− 2푛푠 휖2

> 푠
> 푀푠

)

,

max   

> 휇∈픐ˆ휇(휌)

∑

> 푎,푠 ′

휇 (푎, 푠 ′ | 푠)훽푠 (푎) ≤ 1 + 휖푠 + 휌푠 · ‖ 훽푠 ‖Lip , ˆ휇푠 ≤ 1 +훾

2훾 ,

which implies that Trob (푣2)푠 − Trob (푣1)푠 ≤ 1+훾 

> 2

‖푣1 − 푣2 ‖∞. We can exchange the role of 푣1 and 푣2 to show that |Trob (푣2)푠 − Trob (푣1)푠 | ≤ 훾 ′‖푣1 − 푣2 ‖∞. Taking the union bound for all 푠 ∈ S completes the proof. 

Now we are ready to prove Theorem 1. 

Proof of Theorem 1. Applying Lemma EC.1, we have 

Trob [푣] =

[∑푎 휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 max 휅 ≥0

{

− 휅휌 푠 + 1

> 푁푠

∑푁푠 

> 푖=1

min (푎,푠 ′)

{

푣 (푠′)훽푠 (푎) + 휅푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) 

}} ] 

> 푠∈S

.

Note that Trob [푣] is an equivalent formulation of the right-hand side of (4) . Applying Lemma EC.5, we can see that Trob is a component-wise non-decreasing contraction mapping with high probability. Whenever this holds, by Lemma EC.4, at optimality each of the constraint (4) is tight. Let 푣∗ be the optimal solution to (V) and let {휇∗ (· , · | 푠)} 푠 ∈S be the corresponding worst-case conditional distributions yielding from Lemma EC.1. Thus, for all 푠 ∈ S,

푣∗ (푠) = min   

> 휇∈픐ˆ휇(휌)

∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 ∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣∗ (푠′)훽푠 (푎)

= ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 ∑

> (푎,푠 ′)

휇∗ (푎, 푠 ′ | 푠)푣∗ (푠′)훽푠 (푎). (EC.5) Because of the rectangularity of 픐ˆ휇 (휌), the pair (휇∗, 푣 ∗) is feasible for (EC.3) . Hence, the optimal value in ( V) is lower bounded by the optimal value of (EC.3). On the other hand, for fixed 휇 ∈ 픐ˆ휇 (휌), the optimum 푣휇 of the inner maximization problem in (EC.3) satisfies 푣휇 (푠) = ∑푎 휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 ∑(푎,푠 ′) 휇 (푎, 푠 ′ | 푠)푣휇 (푠′)훽푠 (푎), ∀푠 ∈ S. Since 휇 is feasible for 픐ˆ휇 (휌),we have 

푣휇 (푠) ≥ min   

> 휇∈픐ˆ휇(휌)

∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 ∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣휇 (푠′)훽푠 (푎).

Since 푣∗ is the solution to the fixed point equation (EC.5) , applying Theorem 6.2.2 in Puterman (Put-erman 1994) gives 푣휇 (푠) ≥ 푣∗ (푠) for all 푠 ∈ S. Because of the non-negativity of 푑0, we conclude that the optimal value in (EC.3) is lower bounded by the optimal value in (V) . Therefore, the proof is completed. 

EC.2.2. Proofs for Propositions 

Proof of Proposition 1. Since the right-hand side of (4) is a contraction mapping with respect to the value function 푣, all constraints (4) are tight at optimality. Because of the non-negativity of 

푑0 (푠), ∀푠, solving the optimization problem (V) is equivalent to computing the unique fixed point of the equation (4) . As a result, the fixed point iteration presented in Algorithm 1 is guaranteed to converge into the optimal solution because the right-hand side at (4) is a contraction mapping. ec4 

Proof of Proposition 2. By assigning the dual multiplier {휅 (푠)} for each constraint in (V), the dual problem becomes 

min  

> 휅≥0

∑

> (푠,푎 )

휋 (푎 | 푠)휅 (푠)푟 (푠, 푎 ) + max 

> 푣

∑

> 푠

푣 (푠) [(1 −훾)푑0 (푠) − 휅 (푠)] +훾 ∑

> 푠

푉 (푠)휅 (푠).

In particular, the inner maximization presented above can be reformulated as 

max  

> 푣,휆 푠≥0

∑

> 푠

푣 (푠)

[

(1 −훾)푑0 (푠) − 휅 (푠)

]

+훾 ∑

> 푠

휅 (푠)

[

− 휆푠 휌푠 + 1

푛푠푛푠∑

> 푖=1

min   

> 푎∈A,푠 ′∈S

{푣 (푠′)훽푠 (푎) + 휆푠푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) }]

= max 푣, 휆푠 ≥0,∀푠 ∈S  

> 훼푠,푖 ,∀푠∈S,∀푖

∑푠 푣 (푠)

[

(1 −훾)푑0 (푠) − 휅 (푠)

]

+훾 ∑푠 휅 (푠)

[

− 휆푠 휌푠 + 1

> 푛푠

∑푛푠 

> 푖=1

훼푠,푖 

]

Subject to 훼푠,푖 ≤ 푣 (푠′)훽푠 (푎) + 휆푠푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) , ∀푖, ∀( 푎, 푠 ′)



.

By assigning the dual multiplier {ℎ(푠) 

> 푖, (푎,푠 ′)

}(푎,푠 ′),푖 , the dual of the maximization problem becomes 

min   

> ℎ≥0

max 푣, 휆푠 ≥0,∀푠 ∈S  

> 훼푠,푖 ,∀푠∈S,∀푖

∑

> 푠

푣 (푠)

[

(1 −훾)푑0 (푠) − 휅 (푠)

]

+훾 ∑

> 푠

휅 (푠)

[

− 휆푠 휌푠 + 1

푛푠푛푠∑

> 푖=1

훼푠,푖 

]

+ ∑

> 푠

∑

> 푖

∑

> (푎,푠 ′)

ℎ(푠)

> 푖, (푎,푠 ′)

[

푣 (푠′)훽푠 (푎) + 휆푠푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) − 훼푠,푖 

]

= min   

> ℎ≥0

max 푣, 휆푠 ≥0,∀푠 ∈S  

> 훼푠,푖 ,∀푠∈S,∀푖

∑

> 푠′

푣 (푠′)

[

(1 −훾)푑0 (푠′) − 휅 (푠′) + ∑

> (푠,푎 )

∑

> 푖

ℎ(푠) 

> 푖, (푎,푠 ′)

훽푠 (푎)

]

+ ∑

> 푠

휆푠

[

−훾휅 (푠)휌푠 + ∑

> 푖

∑

> (푎,푠 ′)

ℎ(푠)

> 푖, (푎,푠 ′)

푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) 

]

+ ∑

> 푠

∑

> 푖

훼푠,푖 

[

1

푛푠

훾휅 (푠) − ∑

> (푎,푠 ′)

ℎ(푠)

> 푖, (푎,푠 ′)

]

.

Therefore, the inner maximization problem is bounded if and only if the following conditions hold: 

(1 −훾)푑0 (푠′) − 휅 (푠′) + ∑

> (푠,푎 )

∑

> 푖

ℎ(푠) 

> 푖, (푎,푠 ′)

훽푠 (푎) = 0, ∀푠′ ∈ S,훾휅 (푠)휌푠 − ∑

> 푖

∑

> (푎,푠 ′)

ℎ(푠)

> 푖, (푎,푠 ′)

푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) ≤ 0, ∀푠 ∈ S,

1

푛푠

훾휅 (푠) − ∑

> (푎,푠 ′)

ℎ(푠) 

> 푖, (푎,푠 ′)

= 0, ∀푠 ∈ S, ∀푖 ∈ [ 푛푠 ].

Hence, the dual of problem ( V) becomes 

min   

> 휅≥0,ℎ ≥0

∑

> (푠,푎 )

휋 (푎 | 푠)휅 (푠)푟 (푠, 푎 )

s.t. (1 −훾)푑0 (푠′) + ∑

> (푠,푎 )

∑

> 푖

ℎ(푠) 

> 푖, (푎,푠 ′)

훽푠 (푎) = 휅 (푠′), ∀푠′ ∈ S,

∑

> 푖

∑

> (푎,푠 ′)

ℎ(푠)

> 푖, (푎,푠 ′)

푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) ≤ 훾휅 (푠)휌푠, ∀푠 ∈ S,

∑

> (푎,푠 ′)

ℎ(푠) 

> 푖, (푎,푠 ′)

= 훾푛푠

휅 (푠), ∀푠 ∈ S, ∀푖 ∈ [ 푛푠 ].ec5 

By change of variable ℎ(푠) 

> 푖, (푎,푠 ′)

← ℎ(푠) 

> 푖, (푎,푠 ′)

/훾, this dual problem can be formulated as 

min   

> 휅≥0,ℎ ≥0

∑

> (푠,푎 )

휋 (푎 | 푠)휅 (푠)푟 (푠, 푎 )

s.t. (1 −훾)푑0 (푠′) + 훾 ∑

> (푠,푎 )

훽푠 (푎) ∑

> 푖

ℎ(푠) 

> 푖, (푎,푠 ′)

= 휅 (푠′), ∀푠′ ∈ S,

∑

> 푖

∑

> (푎,푠 ′)

ℎ(푠)

> 푖, (푎,푠 ′)

푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) ≤ 휅 (푠)휌푠, ∀푠 ∈ S,

∑

> (푎,푠 ′)

ℎ(푠) 

> 푖, (푎,푠 ′)

= 1

푛푠

휅 (푠), ∀푠 ∈ S, ∀푖 ∈ [ 푛푠 ].

Or we make the change of variable ℎ(푠) 

> 푖, (푎,푠 ′)

= 휅 (푠)푞(푠) 

> 푖, (푎,푠 ′)

and consider solving 

min   

> 휅≥0,ℓ ≥0

∑

> (푠,푎 )

휋 (푎 | 푠)휅 (푠)푟 (푠, 푎 )

s.t. (1 −훾)푑0 (푠′) + 훾 ∑

> (푠,푎 )

훽푠 (푎)휅 (푠) ∑

> 푖

푞(푠) 

> 푖, (푎,푠 ′)

= 휅 (푠′), ∀푠′ ∈ S,

∑

> 푖

∑

> (푎,푠 ′)

푞(푠)

> 푖, (푎,푠 ′)

푐 (( 푎, 푠 ′), (푎푖, 푠 ′ 

> 푖

)) ≤ 휌푠, ∀푠 ∈ S,

∑

> (푎,푠 ′)

푞(푠) 

> 푖, (푎,푠 ′)

= 1

푛푠

, ∀푠 ∈ S, ∀푖 ∈ [ 푛푠 ].



Proof of Proposition 3. Define Z푠, ∞ = {( 푎, 푠 ′) ∈ A × S : 픩훽푠 푓 (푎, 푠 ′) = ‖훽푠 푓 ‖Lip , ˆ휇푠 }, and 

휌푠 = sup  

> É:A×S→A×S

{

피ˆ휇푠 [푐 (É(푎, 푠 ′), (푎, 푠 ′))] : É(푎, 푠 ′) = (푎, 푠 ′), ∀( 푎, 푠 ′) ≠ Z푠, ∞,훽푠 푓 (É(푎, 푠 ′)) − 훽푠 푓 (( 푎, 푠 ′)) 

푐 (É(푎, 푠 ′), (푎, 푠 ′)) = 픩 훽푠 푓 (푎, 푠 ′), ∀( 푎, 푠 ′) ∈ Z푠, ∞

}

.

Consider the general case where the function space F is a subset of {푓 : S 3 푠 7 → 푓 (푠) ∈ ℝ}. Then for fixed 휅, the inner problem of robust OPE becomes 

min    

> 휇∈픐ˆ휇(휌),∀푠

max    

> 푓∈L[F]

(1 −훾)피푠∼푑0 [푓 (푠)] +

{ ∑

> 푠

휅 (푠)푟휋 (푠) + 훾피푠∼휅 (푠)

[피(푎,푠 ′)∼ 휇 ( · ,· | 푠) [훽푠 (푎)푓 (푠′)] ] − 피푠∼휅 [푓 (푠)] 

}

= max    

> 푓∈L[F]

(1 −훾)피푠∼푑0 [푓 (푠)] + ∑

> 푠

휅 (푠)푟휋 (푠) − 피푠∼휅 [푓 (푠)] + min   

> 휇∈픐ˆ휇(휌),∀푠

{

훾피푠∼휅 (푠)

[피(푎,푠 ′)∼ 휇 ( · ,· | 푠) [훽푠 (푎)푓 (푠′)] ] }

= max    

> 푓∈L[F]

(1 −훾)피푠∼푑0 [푓 (푠)] + ∑

> 푠

휅 (푠)푟휋 (푠) − 피푠∼휅 [푓 (푠)] + 훾피푠∼휅 (푠)

{

min    

> 휇∈픐ˆ휇(휌)

피(푎,푠 ′)∼ 휇 ( · ,· | 푠) [훽푠 (푎)푓 (푠′)] 

}

,

where the first equality is by applying the sion’s minimax theorem (Sion 1958) based on the fact that 

L[F] is a linear topological space and 픐ˆ휇 (휌) is a compact Wasserstein ball, and the second equality is because of the rectangular structure of the ambiguity set P. Based on the assumption that 휌푠 < 휌푠, ∀푠ec6 

and applying Theorem 6 on the inner minimization within the Wasserstein ball, this problem can be equivalently formulated as 

max   

> 푓∈F

(1−훾)피푠∼푑0 [푓 (푠)] + ∑

> 푠

휅 (푠)푟휋 (푠) − 피푠∼휅 [푓 (푠)] + 훾피푠∼휅 (푠)

{

피(푎,푠 ′)∼ ˆ휇푠 [훽푠 (푎)푓 (푠′)] − 휌푠 · ‖ 훽푠 (·) 푓 (·)‖ Lip , ˆ휇푠

}

.

Combining this formulation with the outer minimization with respect to 휅 completes the proof. 

## Appendix EC.3: Proofs for Section 5 

EC.3.1. Proofs for Section 5.1 

We begin with a lemma on the error bounds for the perturbed value iterations. 

Lemma EC.6. Denote by T true the Bellman operator with the true conditional probability 푑휋푏 (푎, 푠 ′ | 푠):

T true [푣] ( 푠) = ∑푎 휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 ∑(푎,푠 ′) 푑휋푏 (푎, 푠 ′ | 푠)푣 (푠′)훽푠 (푎).

Denote by T 푙 and T 푢 perturbations of T so that 

T 푙 [푣] ( 푠) = 푇 true [푣] ( 푠) − 휖푙푣 (푠),

T 푢 [푣] ( 푠) = 푇 true [푣] ( 푠) + 휖푢푣 (푠).

Assume that there exist 휖푙 = (휖푙 (푠)) 푠 ∈S and 휖푢 = (휖푙 (푠)) 푠 ∈S such that 휖푙푣 (푠) ≤ 휖푙 (푠) and 휖푢푣 (푠) ≤ 휖푢 (푠) for all 

푠 ∈ S and 푣. Let 푣true , 푣 푙 , 푣 푢 be the solutions to the fixed point of T true , T 푙 , T 푢 , respectively. Then 

푣true − 푣푙 ≤ (퐼 −훾푃 true )−1휖푙 ,푣true − 푣푢 ≥ − (퐼 −훾푃 true )−1휖푢,

where 푃true ∈ ℝ|S |×| S | is defined as 푃true  

> 푠,푠 ′

:= ∑푎 푑휋푏 (푎, 푠 ′ | 푠)훽푠 (푎), and the inequality is interpreted component-wise. Proof of Lemma EC.6. Define 푣푙 

> (푘)

as the 푘-th iteration point for the value iteration algorithm with Bellman operator T 푙 . Then we have the relation 

푣 (푘+1) 

> 푙

− 푣true = T 푙 [푣푙 

> (푘)

] − T true [푣true ]

= T true [푣푙 

> (푘)

] − T true [푣true ] − 휖푣푙 

> (푘)

≥ T true [푣푙 

> (푘)

] − T true [푣true ] − 휖푙

= 훾

( ∑

> 푎,푠 ′

푑휋푏 (푎, 푠 ′ | 푠)훽푠 (푎)( 푣푙 

> (푘)

− 푣true )

) 

> 푠∈S

− 휖푙

= 훾푃 true (푣푙 

> (푘)

− 푣true ) − 휖푙 .

Applying the relation inductively, we have 

푣푙 

> (푛)

− 푣true ≥ 훾푛 (푃true )푛 (푣푙 

> (0)

− 푣true ) − 

> 푛−1

∑

> 푘=0

훾푛−푘−1 (푃true )푛−푘−1휖푙 .

Taking the limit 푛 → ∞ and applying the identity (퐼 − 퐴)−1 = lim 푛→∞ 

∑푛−1 

> 푘=0

퐴푘 gives the desired result. The other part of the Lemma follows the similar argument. ec7 

Lemma EC.7. For fixed 푠 ∈ S, we define 

F푠 := {( 푎, 푠 ′) 7 → 푣 (푠′)훽푠 (푎) : 푎 ∈ A, 푠 ′ ∈ S}.

Define d(˜푣, 푣 ) := |푑>

> 0

(퐼 −훾푃 true )−1 (˜푣 − 푣)| . Then 

N

( 1 

> 푛

, F푠, d

)

≤ | A|( 1 + log b푛푀 |S |c) .

Proof of Lemma EC.7. Denote H as the collection of all possible value functions 푣. Without loss of generality, define the metric of H as d(푣, 푣 ′) = |∑푠 ∈S [푣 (푠) − 푣 ′(푠)]| . Then for fixed 푡, consider the line set H푡 = {푣 : ∑푠 푣 (푠) = 푡 }. For any 휖 ≥ 0, we have d(푣, 푣 ′) ≤ 휖 when 푣 ∈ H푡 and 푣 ′ ∈ H푡+휖 . In order to find the 1 

> 푛

-covering number of H, we only need to find the covering number for the 1-dimensional parameter 푡 with 0 ≤ 푡 ≤ 푀 |S |, which is 1 + log b푛푀 |S |c . Since the function class F푠 can be expressed as 

F푠 = ⋃ 

> 푎∈A

훽푠 (푎)H,

the covering number of F푠 can be upper bounded as |A|( 1 + log b푛푀 |S |c) . 

Applying Proposition 8 to the right-hand side of constraint (4) gives the following result. 

Lemma EC.8. Fix 푠 ∈ S and define F푠 = {( 푎, 푠 ′) 7 → 푣 (푠′)훽푠 (푎), 푎 ∈ A, 푠 ′ ∈ S}. Let 휏푠 > 0, and set 

휌푠 =

√ 2휏푠

푛푠

diam (A × S), 훿푠 = min    

> (푎,푠 ′) ∈ supp (푑휋푏)

푑휋푏 (푎, 푠 ′ | 푠), 훥푠 = 1

( 1−2휌 

> 1−휌

∨ 2휌−1

> 휌

) .

With probability at least 1 − 훼푠 , where 

훼푠 := exp ( −휏푠 +log (| A|( 1+log b푛푠 푀 |S |c) ) +2 exp (− 2푛푠훿2 

> 푠

) + exp 

(

−푛푠 log 훥푠 +log (|A|( 1+log b푛푠 푀 |S |c) ))

,

simultaneously for every function 푣 with |푣 (푠)| ≤ 푀, it holds that 

피푑휋푏 [푣 (푠)훽푠 (푎)] ≥ Trob [푣] − 6

푛푠

.

Proof of Theorem 2. Taking the union bound of the probability presented in Lemma EC.8, with probability at least 

1 − ∑ 

> 푠∈S

{

푒−휏푠 +| S | log ( | A| ( 1+ b 푛푠 푀 c)) + 2푒−2푛푠 훿2 

> 푠

+ exp [− 푛푠 log 훥푠 + | S | log (| A|( 1 + b 푛푠 푀c))] 

}

,

the Bellman operator Trob for robust reward admits the following error bound for any value function 푣

satisfying 0 ≤ 푣 (푠) ≤ 푀, ∀푠 ∈ S,

Trob [푣] = T ∗ [푣] + 휖푣, 휖푣 (푠) ≤ 휖푛,푠 .

Recall that we have used 푣∗ to denote the fixed point of Trob . When this upper bound holds, applying Lemma EC.6 implies 

푣true − 푣∗ ≥ −( 퐼 −훾푃 true )−1휖. 

Then the gap between the underlying reward and the robust reward is 

푅휋 ≥ ∑

> 푠

푣∗ (푠)푑0 (푠) − 푑푇 

> 0

(퐼 −훾푃 true )−1휖. 

ec8 

Proof of Proposition 4. Denote by ˆT the empirical Bellman operator such that 

ˆT [푣] ( 푠) = ∑

> 푠

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 ∑ 

> 푠′∈S

푃ˆ휇 (푠, 푠 ′)푣 (푠′) ∀ 푠 ∈ S.

where 푃ˆ휇 ∈ ℝ|S |×| S | denotes the transition kernel with 푃ˆ휇 (푠, 푠 ′) = ∑푎 ˆ휇 (푎, 푠 ′ | 푠)훽푠 (푎). Denote by {ˆ푣 (푠)} 푠 ∈S

the empirical value function, which is the fixed point for the empirical Bellman operator. Define 

휖푠 = 휏 ′ 

> 푠

/√푛푠 , then for fixed 푠, applying the Hoeffding upper bound implies that with probability at least 

1 − exp 

(

− 2휏′2

> 푠
> 푀푠

)

,

∑

> 푠′

푃ˆ휇 (푠, 푠 ′) = ∑  

> 푎∈A,푠 ′∈S

ˆ휇 (푎, 푠 ′ | 푠)훽푠 (푎) ≤ 1 + 휖푠 .

Therefore, with probability at least 1 − ∑푠 ∈S exp 

(

− 2휏′2

> 푠
> 푀푠

)

, for all 푠 ∈ S and for any two value functions 

푣1, 푣 2, it holds that 

ˆT [푣1] ( 푠) − ˆT [푣2] ( 푠) = 훾 ∑  

> 푎∈A,푠 ′∈S

ˆ휇 (푎, 푠 ′ | 푠) [ 푣1 (푠′) − 푣2 (푠′)] 훽푠 (푎)

≤ 훾 ‖푣1 − 푣2 ‖∞

∑  

> 푎∈A,푠 ′∈S

ˆ휇 (푎, 푠 ′ | 푠)훽푠 (푎)≤

(

훾 + 훾휏 ′

> 푠

√푛푠

)

‖푣1 − 푣2 ‖∞ ≤ 1 +훾

2 ‖푣1 − 푣2 ‖∞,

which means that ˆT is a contraction mapping, i.e., the matrix 퐼 −훾푃 ˆ휇 is invertible. Denote by 푇 푙 and 푇푢

the robust and optimistic Bellman operators, with the associated robust and optimistic value functions being 푣푙 and 푣푢 , respectively. Note that the Bellman operator 푇 푙 satisfies 

ˆT (푠) − 푇 푙 (푠) ≤ 휖푙 (푠) := 훾휌 푛,푠 · ‖ 훽푠푣푙 ‖Lip , ˆ휇푠 .

Applying the similar perturbation analysis as in Lemma EC.6 gives 

ˆ푣 − 푣푙 ≤ ( 퐼 −훾푃 ˆ휇 )−1휖푙 .

Similarly, 푣푢 − ˆ푣 ≤ ( 퐼 −훾푃 ˆ휇 )−1휖푢 with 휖푢 (푠) := 훾휌 푛,푠 · ‖ 훽푠푣푢 ‖Lip , ˆ휇푠 .

In summary, with probability at least 1 − ∑푠 ∈S exp 

(

− 2휏′2

> 푠
> 푀푠

)

, the length of the confidence interval can be upper bounded by 

Uˆ휇 (휌) − Lˆ휇 (휌) ≤ ∑

> 푠

푑0 (푠) [ 푣푢 (푠) − 푣푙 (푠)] 

≤ ∑

> 푠

푑0 (푠) [ ˆ푣 (푠) − 푣푙 (푠)] + ∑

> 푠

푑0 (푠) [ 푣푢 (푠) − ˆ푣 (푠)] 

≤ 푑푇 

> 0

(퐼 −훾푃 ˆ휇 )−1휖푙 + 푑푇 

> 0

(퐼 −훾푃 ˆ휇 )−1휖푢 .

We can further upper bound the function variation term as follows. Applying Lemma EC.13 implies that, with probability at least 1 − 2 exp (− 2푛푠훿2 

> 푠

),

‖훽푠푣푙 ‖Lip , ˆ휇푠 = ‖훽푠푣푙 ‖Lip ,푑 휋푏 ( · ,· | 푠) ≤ max     

> 푣∈ℝ|S|,|푣(푠) | ≤ 푀

‖훽푠푣 ‖Lip ,푑 휋푏 ( · ,· | 푠) .

The other function variation term can also be upper bounded similarly. ec9 

EC.3.2. Proofs for Section 5.2 

Proof of Theorem 3. Define the adversarial Bellman operator T : S → S as 

T [푣] ( 푠) = ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 min   

> 휇( · ,· | 푠) ∈ 픐푑휋 푏(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽푠 (푎).

Define the empirical adversarial Bellman operator ˆT : S → S as 

ˆT [푣] ( 푠) = ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 min   

> 휇( · ,· | 푠) ∈ 픐ˆ휇(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽푠 (푎).

Applying Theorem 1 implies that with probability at least 1 − ∑푠 exp (− 2푛푠휖2 

> 푠

/푀푠 ), T is contractive with Lipschitz constant 1+훾 

> 2

. Moreover, Lemma EC.13 implies that with probability at least 1 −

∑푠 exp (− 2푛푠휖2 

> 푠

/푀푠 ) − 2 ∑푠 푒−2푛푠 훿2 

> 푠

, ˆT is also contractive with Lipschitz constant 1+훾 

> 2

.Define the following two thresholds 

휌 (1) 

> 푠

= sup   

> 푇:A×S→A×S

{

피푑휋푏 ( · ,· | 푠) [푐 (É(푎, 푠 ′), (푎, 푠 ′))] : É(푎, 푠 ′) = (푎, 푠 ′), ∀( 푎, 푠 ′) ≠ Z푠, ∞,훽푠 푓 (É(푎, 푠 ′)) − 훽푠 푓 (( 푎, 푠 ′)) 

푐 (É(푎, 푠 ′), (푎, 푠 ′)) = 픩 훽푠 푓 (푎, 푠 ′), ∀( 푎, 푠 ′) ∈ Z푠, ∞

}

,휌 (2) 

> 푠

= sup   

> 푇:A×S→A×S

{

피ˆ휇푠 [푐 (É(푎, 푠 ′), (푎, 푠 ′))] : É(푎, 푠 ′) = (푎, 푠 ′), ∀( 푎, 푠 ′) ≠ Z푠, ∞,훽푠 푓 (É(푎, 푠 ′)) − 훽푠 푓 (( 푎, 푠 ′)) 

푐 (É(푎, 푠 ′), (푎, 푠 ′)) = 픩 훽푠 푓 (푎, 푠 ′), ∀( 푎, 푠 ′) ∈ Z푠, ∞

}

.

Suppose 휌푠 < 휌푠 := 휌 (1) 

> 푠

∧ 휌 (2) 

> 푠

. Applying Proposition 9 implies that with probability at least 1 − 2푒−2푛푠 훿2 

> 푠

−

2푒−휏 , it holds that 

T [푣] ( 푠) − ˆT [푣] ( 푠) ≤ 2피⊗ [ℜ푛푠 (F푠 )] + 퐻푠

√ 휏

2푛푠

,

ˆT [푣] ( 푠) − T [푣] ( 푠) ≤ 2피⊗ [ℜ푛푠 (F푠 )] + 퐻푠

√ 휏

2푛푠

.

Taking the union bound together with the perturbation analysis in Lemma EC.6 completes the proof. 

To prove Theorem 4, We first establish the asymptotic convergence for the transition probabilities ˆ휇푇

into 푑휋푏 , and then the convergence for Ladv (휌) can be built by applying the functional delta theorem. 

Lemma EC.9. Denote by ˆ휇푇 = vec ({ ˆ휇푇 (푎, 푠 ′ | 푠)}) , and 푑휋푏 = vec ({ 푑휋푏 (푎, 푠 ′ | 푠)}) . It holds that 

√푇 (ˆ휇푇 − 푑휋푏

) d

−→ N (0, 퐷 Λ퐷),

where Λ ∈ ℝ|S | | A| | S |×| S | | A| | S |+ is defined as 

Λ(푠, (푎,푠 ′)) ,(˜푠, ( ˜푎, ˜푠′)) =

{푑휋푏 (푎, 푠 ′ | 푠)( 1 − 푑휋푏 (푎, 푠 ′ | 푠)) , if (푠, (푎, 푠 ′)) = (˜푠, ( ˜푎, ˜푠′)) ,

−푑휋푏 (푎, 푠 ′ | 푠)푑휋푏 ( ˜푎, ˜푠′ | 푠) if 푠 = ˜푠, (푎, 푠 ′) ≠ ( ˜푎, ˜푠′),

0, otherwise ,

and 퐷 = diag 

(

vec 

(

(푑휋푏 )− 12 ⊗ 1|A| | S |

)) 

, 푑−1/2 

> 휋푏

:=

{

> 1

√푑휋푏 (푠)

} 

> 푠∈S

, and vec (·) denotes the vectorization of a matrix by stacking the rows of the matrix on top of one another. ec10 

Proof of Lemma EC.9. The proof essentially follows Billingsley (1961) on the maximum likelihood estimate for Markov chains. Denote by 푋 (푚) 

> 푠

be the action-state pair directly after the 푚-th return to 푠.Define 푝푠, (푎,푠 ′) := 휋푏 (푎|푠)푃 (푠′|푠, 푎 ),휏푠, (푎,푠 ′) (푇 ) :=

> 푇

∑

> 푡=1

1{푠푡 = 푠, 푎 푡 = 푎, 푠 푡+1 = 푠′},휏푠 (푇 ) :=

> 푇

∑

> 푡=1

1{푠푡 = 푠},푄푠, (푎,푠 ′) (푇 ) := 

> b푇푑 휋푏(푠) c

∑

> 푚=1

1{푋 (푚) 

> 푠

= (푎, 푠 ′)} .

It follows that 

ˆ휇푇 (푎, 푠 ′|푠) = 휏푠, (푎,푠 ′) (푇 )/ 휏푠 (푇 ).

From the Markov property, for each 푠 ∈ S, {푄푠, (푎,푠 ′) }푎 ∈A,푠 ′ ∈S is multinomially distributed with b푇푑 휋푏 (푠)c 

trials and success probability vector 푝푠, ( · ,·) . As a result, we have 

[푄푠, (푎,푠 ′) (푇 ) − b 푇푑 휋푏 (푠)c 푝푠, (푎,푠 ′)

√b푇푑 휋푏 (푠)c 

] 

> 푠∈S,(푎,푠 ′) ∈ A×S
> d

−→ N (0, Λ).

Next, we prove that 

[휏푠, (푎,푠 ′) (푇 ) − 휏푠 (푇 )푝푠, (푎,푠 ′)

√b푇푑 휋푏 (푠)c 

] 

> 푠∈S,(푎,푠 ′) ∈ A×S
> d

−→ N (0, Λ).

To this end, it suffices to show for each 푠 ∈ S and (푎, 푠 ′) ∈ A × S,

Δ푇 := 휏푠, (푎,푠 ′) (푇 ) − 휏푠 (푇 )푝푠, (푎,푠 ′) − 푄푠, (푎,푠 ′) (푇 ) + b 푇푑 휋푏 (푠)c 푝푠, (푎,푠 ′)

√푇

> p

−→ 0.

Fixing 푠 ∈ S and (푎, 푠 ′) ∈ A × S, setting 푍푚 := 1{푋 (푚) 

> 푠

= (푎, 푠 ′)} − 푝푠, (푎,푠 ′) and 푌푚 := ∑푚푗=1 푍 푗 , we rewrite 

Δ푇 as 

Δ푇 = 푌휏푠 (푇 ) − 푌b푇푑 휋푏 (푠) c 

√푇 .

Let 휖 > 0. By consistency of the empirical frequency 휏푠 (푇 ), there exists 푇0 such that for all 푇 > 푇0,

ℙ{| 휏푠, (푎,푠 ′) (푇 ) − 푇푑 휋푏 (푠)| > 푇 휖 3} ≤ 휖. 

Note that 푍 푗 ’s are i.i.d. with mean 0 and variance 푝푠, (푎,푠 ′) (1 − 푝푠, (푎,푠 ′) ). For 푇 > 푇0, we have from Chebyshev’s inequality that 

ℙ{| Δ푇 | > 휖} ≤ ℙ{| 휏푠, (푎,푠 ′) (푇 ) − 푇푑 휋푏 (푠)| > 푇 휖 3} + ℙ{| Δ푇 | > 휖, |휏푠 (푇 ) − 푇푑 휋푏 (푠)| ≤ 푇 휖 3}≤ 휖 + ℙ

{

max    

> 푚∈ℕ:|푚−푇푑 휋푏(푠) | ≤ 푇 휖 3

|푌푚 − 푌b푇푑 휋푏 (푠) c | > 휖√푇

}

≤ 휖 + 2 ∑  

> 푚∈ℕ:|푚−푇푑 휋푏(푠) | ≤ 푇 휖 3

ℙ{| 푌푚 | > 휖√푇 /2}≤ 휖 + 8푇 휖 3푝푠, (푎,푠 ′) (1 − 푝푠, (푎,푠 ′) )/( 푇 휖 2)

= 휖 (1 + 8푝푠, (푎,푠 ′) (1 − 푝푠, (푎,푠 ′) ) → 0.ec11 

Finally, observe that 

[√푇 (ˆ휇푇 (푎, 푠 ′ | 푠) − 푑휋푏 (푎, 푠 ′ | 푠))] 

> 푠∈S,(푎,푠 ′) ∈ A×S

=

[

1

√푑휋푏 (푠)

(√ 휏푠 (푇 ) ˆ휇푇 (푎, 푠 ′ | 푠) − √휏푠 (푇 )푑휋푏 (푎, 푠 ′ | 푠))] 

> 푠∈S,(푎,푠 ′) ∈ A×S

=

[

1

√푑휋푏 (푠)

(휏푠, (푎,푠 ′) (푇 )

√휏푠 (푇 ) − 휏푠 (푇 )푑휋푏 (푎, 푠 ′ | 푠)

√휏푠 (푇 )

)]  

> 푠∈S,(푎,푠 ′) ∈ A×S

=

[

1

√푑휋푏 (푠)

√b푇푑 휋푏 (푠)c 

√휏푠 (푇 ) ·

[휏푠, (푎,푠 ′) (푇 ) − 휏푠 (푇 )푝푠, (푎,푠 ′)

√b푇푑 휋푏 (푠)c 

] ]  

> 푠∈S,(푎,푠 ′) ∈ A×S
> p

−→N (0, 퐷 Λ퐷),

where the convergence follows using Slutsky’s theorem and linear transformation of multivariate normal distribution. 

Lemma EC.10. Under the setting of Theorem 4, the matrix 퐼 −훾푃 휇 is invertible for any 휇 ∈ 픐푑휋푏 (휌).Proof of Lemma EC.10 It suffices to show that the mapping T : 푣 7 → 훾푃 휇푣 is contractive. For any 

푣1, 푣 2 ∈ ℝ|S | , we have 

‖T [푣1] − T [푣2] ‖ ∞ = 훾 max 

> 푠

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠) [ 푣1 (푠′) − 푣2 (푠′)] 훽푠 (푎)

≤ 훾 ‖푣1 − 푣2 ‖∞ max 

> 푠

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)훽푠 (푎)≤ 훾 ‖푣1 − 푣2 ‖∞ max  

> 푠

max   

> 휇∈픐푑휋 푏(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)훽푠 (푎).

In particular, applying Proposition 6 implies that 

max   

> 휇∈픐푑휋 푏(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)훽푠 (푎) ≤ ∑

> 푎,푠 ′

푑휋푏 (푎, 푠 ′ | 푠)훽푠 (푎) + 휌푠 · ‖ 훽푠 ‖Lip ,푑 휋푏 ( · ,· | 푠) .

Therefore, as long as 1 + 휌푠 · ‖ 훽푠 ‖Lip ,푑 휋푏 ( · ,· | 푠) < 1/훾 for all 푠 ∈ S, the mapping T is contractive. 

Proof of Theorem 4. Define 

휅휇 (푠) = 푤 (푠)휇 (푠),푃휇 (푠, 푠 ′) = ∑

> 푎

훽푠 (푎)휇 (푎, 푠 ′ | 푠),푟휋 = ∑

> 푎

휋푏 (푎 | 푠)훽푠 (푎)푟 (푠, 푎 ),

then the stationary constraint ( P-b) can be reformulated as 

휅휇 (푠′) = (1 −훾)푑0 (푠′) + 훾 ∑

> 푠

휅휇 (푠)푃휇 (푠, 푠 ′).

To apply the delta method, let us compute ∇휇 L푑휋푏 (휌). From Lemma EC.10 we can see that the system of equations above has the unique solution, and we can reformulate L푑휋푏 as the following: 

L푑휋푏 (휌) = min   

> 휇∈픐푑휋 푏(휌)

∑

> 푠

휅휇 (푠)푟휋 (푠) = min    

> 휇∈픐푑휋 푏(휌)

〈( 1 −훾)푟휋 , (퐼 −훾푃 푇휇

)−1푑0〉.ec12 

Denote the minimizer above as 휇∗. By the envelope theorem, the gradient of L휇 (휌) (with respect to 휇)at 휇 = 푑휋푏 can be expressed as 

∇L푑휋푏 (휌) = ∇〈( 1 −훾)푟휋 , (퐼 −훾푃 푇휇∗ )−1푑0〉

= 〈( 1 −훾)푟휋 , ∇( 퐼 −훾푃 푇휇∗ )−1푑0〉

= 〈( 1 −훾)푟휋 ,훾 (퐼 −훾푃 푇휇∗ )−1 (∇ 푃푇휇∗ )( 퐼 −훾푃 푇휇∗ )−1푑0〉

= 훾 (1 −훾)〈 vec 

(

(퐼 −훾푃 푇휇∗ )−1푑0푟푇휋 (퐼 −훾푃 푇휇∗ )−1)

, ∇vec (푃푇휇∗ )〉 

= 훾 (1 −훾)

{ (

(퐼 −훾푃 푇휇∗ )−1푑0푟푇휋 (퐼 −훾푃 푇휇∗ )−1) 

> 푠,푠 ′

훽푠 (푎) : (푠, 푎, 푠 ′) ∈ S × A × S

}

,

where the last inequality is because 

∇vec (푃푇휇∗ ) =

{

1(¯푠 = 푠, ¯푠′ = 푠′)훽푠 ( ¯푎)

} 

> (푠,푠 ′),(¯푠, ¯푎, ¯푠′)

.

Therefore, using the delta theorem and Lemma EC.9 gives the result. 

## Appendix EC.4: Proofs for Section 6 

Lemma EC.11. Under the setting of Theorem 6, with probability at least 1 − exp (−2푛푠훿2 

> 푠

휖2

> 푠

), it holds that 

max 

> 푎

ˆ휇 (푎 | 푠)

휋푏 (푎 | 푠) ≤ 1 +훾

2훾 − 휌푠 max   

> 휋( · | 푠)

‖훽휋푠 ‖Lip , ˆ휇푠 .

Proof. First, we can see that the maximization over the variation term is bounded: 

max   

> 휋( · | 푠)

‖훽휋푠 ‖Lip , ˆ휇푠 = max   

> 휋( · | 푠)

max         

> 푎∈supp (ˆ휇( · | 푠)) ,
> ˜푎≠푎휋(푎|푠)
> 휋푏(푎|푠)

− 휋 ( ˜푎 |푠)   

> 휋푏(˜푎|푠)

푐 (푎, ˜푎)

= max      

> 푎∈supp (ˆ휇( · | 푠)) ,
> ˜푎≠푎
> 1
> 휋푏(푎|푠)

푐 (푎, ˜푎)

= 1min    

> 푎∈supp (ˆ휇( · | 푠)) ,
> ˜푎≠푎

휋푏 (푎 | 푠)푐 (푎, ˜푎) < ∞.

Therefore, the assumption in Theorem 6 is valid for sufficiently small 휌푠 . Applying Dvoret-zky–Kiefer–Wolfowitz inequality gives Pr 

(

max 

> 푎

ˆ휇 (푎 | 푠)

휋푏 (푎 | 푠) ≤ 1 +훾

2훾 − 휌푠 max   

> 휋( · | 푠)

‖훽휋푠 ‖Lip , ˆ휇푠

)

=Pr 

(

max 

> 푎

ˆ휇 (푎 | 푠) − 휋푏 (푎 | 푠)

휋푏 (푎 | 푠) ≤ 1 −훾

2훾 − 휌푠 max   

> 휋( · | 푠)

‖훽휋푠 ‖Lip , ˆ휇푠

)

≥Pr 

(

max  

> 푎

ˆ휇 (푎 | 푠) − 휋푏 (푎 | 푠) ≤ 훿푠

[ 1 −훾

2훾 − 휌푠 max   

> 휋( · | 푠)

‖훽휋푠 ‖Lip , ˆ휇푠

] ) 

≥1 − exp 

(

−2푛푠훿2

> 푠

[ 1 −훾

2훾 − 휌푠 max   

> 휋( · | 푠)

‖훽휋푠 ‖Lip , ˆ휇푠

]2)

≥1 − exp 

(

−2푛푠훿2 

> 푠

휖2

> 푠

)

.

ec13 

Proof of Theorem 5. By exchanging the maximization over 푣 and 휋 in (8) , we can reformulate this problem as the existence problem: 

max  

> 푣

(1 −훾) ∑

> 푠

푣 (푠)푑0 (푠)

s.t. ∃휋, 푣 (푠) ≤ ∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾푉 (푠), ∀푠 ∈ S,

where 푉 (푠) := min   

> 휇∈픐ˆ휇(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽휋푠 (푎).

Or equivalently, we can reformulate this existence problem as 

max  

> 푣

(1 −훾) ∑

> 푠

푣 (푠)푑0 (푠)

s.t. 푣 (푠) ≤ max  

> 휋( · | 푠)

∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾푉 (푠), ∀푠 ∈ S, (*) where 푉 (푠) := min   

> 휇∈픐ˆ휇(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽휋푠 (푎).

Define the operator 휙 (푣) as the right-hand side of the constraint (*), i.e., 

휙 (푣)푠 = max  

> 휋( · | 푠)

∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 min   

> 휇∈픐ˆ휇(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣 (푠′)훽휋푠 (푎), ∀푠 ∈ S.

We can show that 휙 (푣) is a contraction mapping. For any 푣1, 푣 2 ∈ ℝ|S |+ ,

휙 (푣1)푠 = max  

> 휋( · | 푠)

∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 min   

> 휇∈픐ˆ휇(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣1 (푠′)훽휋푠 (푎)≥ max  

> 휋( · | 푠)

∑

> 푎

휋 (푎 | 푠)푟 (푠, 푎 ) + 훾 min   

> 휇∈픐ˆ휇(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)푣2 (푠′)훽휋푠 (푎)+훾 min   

> 휇∈픐ˆ휇(휌)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠) [ 푣1 (푠′) − 푣2 (푠′)] 훽휋푠 (푎)

= 휙 (푣2)푠 +훾 min    

> 휇∈픐ˆ휇(휌),휋 ( · | 푠)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠) [ 푣1 (푠′) − 푣2 (푠′)] 훽휋푠 (푎).

It follows that 

휙 (푣2)푠 − 휙 (푣1)푠 ≤ 훾 max    

> 휇∈픐ˆ휇(휌),휋 ( · | 푠)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠) [ 푣2 (푠′) − 푣1 (푠′)] 훽휋푠 (푎)≤ 훾 ‖푣2 − 푣1 ‖∞ · max    

> 휇∈픐ˆ휇(휌),휋 ( · | 푠)

∑

> (푎,푠 ′)

휇 (푎, 푠 ′ | 푠)훽휋푠 (푎)≤ 훾 ‖푣2 − 푣1 ‖∞ ·

[

max  

> 휋( · | 푠)

∑

> (푎,푠 ′)

ˆ휇 (푎, 푠 ′ | 푠)훽휋푠 (푎) + 휌푛,푠 max   

> 휋( · | 푠)

‖훽휋푠 ‖Lip , ˆ휇

]

= 훾 ‖푣2 − 푣1 ‖∞ ·

[

max 

> 푎

ˆ휇 (푎 | 푠)

휋푏 (푎 | 푠) + 휌푛,푠 max   

> 휋( · | 푠)

‖훽휋푠 ‖Lip , ˆ휇

]

≤ 1 +훾

2 ‖푣2 − 푣1 ‖∞.

We can exchange the role of 푣1 and 푣2 to show that |휙 (푣2)푠 − 휙 (푣1)푠 | ≤ 1+훾 

> 2

‖푣1 − 푣2 ‖∞. Then applying Lemma EC.4 implies that 푣∗ and 휋∗ must be the optimal solution for (8). 

Lemma EC.12. For fixed 푠 ∈ S, we define 

F푠 :=

{

(푎, 푠 ′) 7 → 푣 (푠′)휋 (푎 | 푠)

휋푏 (푎 | 푠) , 휋 (푎 | 푠) is deterministic 

}

.ec14 

Define d(˜푣, 푣 ) := |푑>

> 0

(퐼 −훾푃 true )−1 (˜푣 − 푣)| , then 

N

( 1 

> 푛

, F푠, d

)

≤ | A|2 (1 + log b푛푀 |S |c) .

Proof of Lemma EC.12. Define d and H following the setting in Lemma EC.7. Since 휋 (푎 | 푠) is deterministic, for fixed 푠, it can be expressed as 

휋 (푎 | 푠) = 1{푎 = 푎′}, for some 푎′.

It follows that 

F푠 = ⋃ 

> 푎′∈A

⋃ 

> 푎∈A

1{푎 = 푎′}

휋푏 (푎 | 푠) H,

which implies the covering number of F푠 can be upper bounded as |A|2 (1 + log b푛푀 |S |c) . 

As a result, Proposition EC.1 follows by applying the covering number argument similar as in Lemma EC.8. Next, we build the performance guarantee for robust batch reinforcement learning by applying the perturbation analysis on the Bellman operator and the generalization bound on Wasserstein DRO. 

Proposition EC.1. Fix 푠 ∈ S and define 

F푠 :=

{

(푎, 푠 ′) 7 → 푣 (푠′)휋 (푎 | 푠)

휋푏 (푎 | 푠) , 휋 (푎 | 푠) is deterministic 

}

.

Take 휏푠 > 0 and 휌푠 =

√ 2휏푠 

> 푛푠

diam (A × S),

훿푠 = min    

> (푎,푠 ′) ∈ supp (푑휋푏)

푑휋푏 (푎, 푠 ′ | 푠), 훥푠 = 1

( 1−2휌 

> 1−휌

∨ 2휌−1

> 휌

) ,

then with probability at least 1 − 훼푠 , where 

훼푠 := exp ( −휏푠 +log (| A|2 (1+log b푛푠 푀 |S |c) ) +2 exp (− 2푛푠훿2 

> 푠

) + exp 

(

−푛푠 log 훥푠 +log (|A|2 (1+log b푛푠 푀 |S |c) ))

,

simultaneously for every function 푓 ∈ F푠 , it holds that 

피푧∼ℙtrue [푓 (푧)] ≥ min   

> ℙ:W(ℙ,ℙ푛) ≤ 휌푠

피ℙ [푓 (푧)] − 6

푛푠

.

Now we give a proof of Theorem 6 by utilizing the perturbation analysis on the Bellman operator. 

Proof of Theorem 6. Denote by T true the Bellman operator for the underlying true value function 

푣true , and by T ∗ the Bellman operator for the robust value function 푣∗. Taking the union bound of the probability presented in Proposition EC.1 implies that, with probability at least 1 − ∑푠 훼푠 , it holds that 

T ∗ [푣] = T true [푣] + 휖푣, 휖푣 ≤ 휖푛,푠 .

Applying Lemma EC.6 implies 

푣true − 푣∗ ≥ −( 퐼 −훾푃 true )−1휖푛 .

Substituting 푅true with ∑푠 푑0 (푠)푣true (푠) and L∗ 

> ˆ휇

(휌푛) with ∑푠 푑0 (푠)푣∗ (푠) completes the proof. ec15 

## Appendix EC.5: Proofs of Appendix B 

Proof of Theorem 6. Let (˜푧, 푧 ) ∼ Υ be taken from the set of joint distributions on Z × Z whose second marginal being ℙ푛, and denote by Υ푧 the conditional distribution of ˜푧 given 푧. We have that 

R푛 (휌; 푓 ) = sup 

> Υ

inf  

> 휆≥0

{휆휌 + 피(˜푧,푧 )∼ Υ [푓 (˜푧) − 푓 (푧) − 휆푐 (˜푧, 푧 )] }

≤ inf   

> 휆≥0

sup 

> Υ

{휆휌 + 피(˜푧,푧 )∼ Υ [푓 (˜푧) − 푓 (푧) − 휆푐 (˜푧, 푧 )] }

= inf   

> 휆≥0

sup 

> Υ푧

{휆휌 + 피푧∼ℙ푛

[피˜푧∼Υ푧 [푓 (˜푧) − 푓 (푧) − 휆푐 (˜푧, 푧 )| 푧]] } 

= inf  

> 휆≥0

{휆휌 + 피푧∼ℙ푛

[ sup 

> Υ푧

피˜푧∼Υ푧 [푓 (˜푧) − 푓 (푧) − 휆푐 (˜푧, 푧 )| 푧]] } 

= inf  

> 휆≥0

{

휆휌 + 피푧∼ℙ푛

[

max   

> ˜푧∈Z

{푓 (˜푧) − 푓 (푧) − 휆푐 (˜푧, 푧 )} 

] } 

≤ 휌 · ‖ 푓 ‖Lip ,ℙ푛 ,

where the inequality holds due to Lagrangian relaxation; the second equality follows from the tower property of conditional expectation; the third equality follows from interchangeability principle (Shapiro et al. 2014); the fourth equality holds due to the fact that sup Υ푧 is attained at a Dirac point mass; and the last equality follows by plugging in a feasible solution 휆 = ‖푓 ‖Lip ,ℙ푛 .To show the other direction, by definition of ¯휌, there exists É : Z → Z such that É(푧) = 푧 for 푧 ∉ Z∞,    

> 푓(É(푧))− 푓(푧)
> 푐(É(푧),푧 )

= 픩 푓 (푧) = ‖푓 ‖Lip ,ℙ푛 for 푧 ∈ Z∞, and 피ℙ푛 [푐 (É(푧), 푧 )] = ¯휌. Let 푠 = 휌/ ¯휌. Then 

피ℙ푛 [( 1 − 푠)푓 (푧) + 푠 푓 (É(푧))] − 피ℙ푛 [푓 ] = 푠피ℙ푛 [1{푧 ∈ Z∞}( 푓 (É(푧)) − 푓 (푧))] = 휌 ‖푓 ‖Lip ,ℙ푛 .

Therefore, it holds that R푛 (휌; 푓 ) = 휌 · ‖ 푓 ‖Lip ,ℙ푛 . 

The proof of Proposition 8 relies on the finite-sample convergence of the Lipschitz norm with respect to ℙ푛 into the norm with respect to ℙtrue , which is discussed in the following Lemma. 

Lemma EC.13. Let F be a collection of discrete functions 푓 : Z → ℝ. Denote 훿 = min 푧 ∈Z ℙtrue (푧). With probability at least 1 − 2 exp (−2푛훿 2), the following equality holds uniformly for any discrete function 

푓 ∈ F:

‖푓 ‖Lip ,ℙ푛 = ‖푓 ‖Lip ,ℙtrue .

Proof of Lemma EC.13. Let H be the set of all discrete functions 푓 with support Z, then 

sup  

> 푓∈F

‖푓 ‖Lip ,ℙ푛 − ‖ 푓 ‖Lip ,ℙtrue = sup  

> 푓∈F

max    

> 푧:ℙ푛(푧)≠0

픩푓 (푧) − max   

> 푧∈Z

픩푓 (푧) ,

which equals zero under the event that supp (ℙ푛) = Z. Let 퐹푛 and 퐹true be the distribution function for 

ℙ푛 and ℙtrue , respectively. Then the support of ℙ푛 equals the support of ℙ if and only if sup 푧 ∈Z |퐹푛 (푧) − 

퐹true (푧)| < 훿. Applying the Dvoretzky-Kiefer-Wolfowith inequality gives the desired result. 

Proof of Proposition 8. Note that the underlying distribution ℙtrue satisfies the following transporta-tion information inequality 

W (ℙ, ℙtrue ) ≤ diam (Z)√2퐷KL (ℙ‖ℙtrue ),

where 퐷KL denotes the KL-divergence metric (Gao 2020, Definition 1). Applying the concentration inequality presented in (Gao 2020, Theorem 1), with probability at least 1 − 푒−푡 , for a single function 

푓 ∈ F, we have 

피푧∼ℙtrue [푓 (푧)] ≤ 피푧∼ℙ푛 [푓 (푧)] + Rℙtrue (휌푛; −푓 ) . (EC.6a) ec16 

Let C

( 1 

> 푛

, F, d

)

be a 1 

> 푛

-cover of F, then for any 푓 ∈ F, there exists 푓 ′ ∈ C so that 

피ℙtrue [푓 ] ≤ 피ℙtrue [푓 ′] + 1

푛 . (EC.6b) Applying the union bound over all functions in F on the upper bound (EC.6a) , together with the relation (EC.6b) and the upper bound in Theorem 6, implies that with probability at least 1 − N

( 1 

> 푛

, F, d

)

푒−휏 ,

피푧∼ℙtrue [푓 (푧)] ≤ 피푧∼ℙ푛 [푓 ′(푧)] + Rℙtrue (휌푛; −푓 ′) + 1

푛

≤ 피푧∼ℙ푛 [푓 (푧)] + 휌푛 ‖푓 ′‖Lip ,ℙtrue + 2

푛

≤ 피푧∼ℙ푛 [푓 (푧)] + 휌푛 ‖푓 ‖Lip ,ℙtrue + 3

푛 ,

(EC.6c) where the last inequality above is because 

|‖ 푓 ′‖Lip ,ℙtrue − ‖ 푓 ‖Lip ,ℙtrue | ≤ ‖ 푓 − 푓 ′‖ℙtrue ,∞ ≤ d(푓 , 푓 ′) ≤ 1

푛 .

By Lemma EC.13, with probability at least 1 − 2푒−2푛훿 2

,

휌푛 ‖푓 ‖Lip ,ℙtrue = 휌푛 ‖푓 ‖Lip ,ℙ푛 . (EC.6d) Applying Proposition 7 with 휂 = 1, ℎ 1 = 0, 푐 = 0 implies that, with probability at least 

1 − exp 



−푛 log ©≠≠´

1

( 1−2훿 

> 1−훿

∨ 2훿−1

> 훿

) ™ÆÆ¨

+ log N

( 1

푛 , F, d

)

,

we have 

휌푛 ‖푓 ‖Lip ,ℙ푛 ≤ R푛 (휌푛; 푓 ) + 3

푛 . (EC.6e) Combining (EC.6c)-(EC.6e) completes the proof. 

Proof of Proposition 9. Since 휌 is sufficiently small, applying Theorem 6 gives 

푈푛 (휌; 푓 ) − 푈 ∗ (휌; 푓 ) = (피ℙ푛 [푓 (푧)] − 피ℙtrue [푓 (푧)] ) + (‖푓 ‖Lip ,ℙ푛 − ‖ 푓 ‖Lip ,ℙtrue 

).

Applying Lemma EC.13 implies that with probability at least 1 − 2푒−2푛훿 2

,

‖푓 ‖Lip ,ℙ푛 − ‖ 푓 ‖Lip ,ℙtrue = 0, ∀푓 ∈ F .

Applying Lemma EC.5 in Gao et al. (2020) implies that with probability at least 1 − 푒−휏 ,

피ℙ푛 [푓 (푧)] ≤ 피ℙtrue [푓 (푧)] + 2피⊗ [ℜ(F)] + 푀

√ 푡

2푛 .

Hence, we conclude that with probability at least 1 − 2푒−2푛훿 2

− 푒−휏 ,

푈푛 (휌; 푓 ) − 푈 ∗ (휌; 푓 ) ≤ 2피⊗ [ℜ푛 (F)] + 푀

√ 푡

2푛 .

The other side of inequality can be obtained by following the similar argument. 
