# Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions

###### Abstract

We introduce *Conformal Decision Theory*, a framework for producing safe autonomous decisions despite imperfect machine learning predictions.
Examples of such decisions are ubiquitous, from robot planning algorithms that rely on pedestrian predictions, to calibrating autonomous manufacturing to exhibit high throughput and low error, to the choice of trusting a nominal policy versus switching to a safe backup policy at run-time.
The decisions produced by our algorithms are safe in the sense that they come with provable statistical guarantees of having low risk without any assumptions on the world model whatsoever; the observations need not be I.I.D. and can even be adversarial.
The theory extends results from conformal prediction to calibrate decisions directly, without requiring the construction of prediction sets.
Experiments demonstrate the utility of our approach in robot motion planning around humans, automated stock trading, and robot manufacturing.

## I Introduction

Autonomous systems increasingly rely on complex learned models to supply predictions that are the basis for decision-making. Self-driving cars rely on deep neural networks [[2](#bib.bib2), [3](#bib.bib3), [4](#bib.bib4), [5](#bib.bib5)] to plan paths around nearby pedestrians, robotic manipulators leverage learned grasp models [[6](#bib.bib6)] to plan high-throughput pick-and-place maneuvers in factories, and AI-enabled stock trading agents optimize the financial future of investors [[7](#bib.bib7)]. There is a conceptual gap, however, between prediction and decision-making, and it remains an open challenge to ensure that
systems make *good decisions* despite *imperfect predictions*.

One common strategy is to calculate the uncertainty in the predictions independently of their downstream effect on the decision [[8](#bib.bib8), [9](#bib.bib9), [10](#bib.bib10), [11](#bib.bib11), [12](#bib.bib12)].
For example, one can use conformal prediction [[13](#bib.bib13), [14](#bib.bib14), [15](#bib.bib15), [16](#bib.bib16), [17](#bib.bib17), [18](#bib.bib18)] to form uncertainty sets that cover the ground truth outcomes of all predictions uniformly.
Then, the robot can pick any decision that is safe with respect to these sets.
This is guaranteed statistically to result in safe autonomous behavior, without any assumption on the underlying distribution or model.
This strategy has been used to provide safety assurances in robot navigation and control [[19](#bib.bib19), [20](#bib.bib20), [21](#bib.bib21), [22](#bib.bib22), [23](#bib.bib23), [24](#bib.bib24)], early warning systems (e.g., collision alerts) [[25](#bib.bib25)], out-of-distribution detection [[26](#bib.bib26), [27](#bib.bib27)], probabilistic pose estimation [[28](#bib.bib28)], and for large language models [[29](#bib.bib29)].
However, this approach decouples prediction uncertainty from decision-making.
What if we could solve the problem all-at-once, *directly* controling decision-making risk, and bypassing the need to construct prediction sets entirely?

This work presents Conformal Decision Theory, a theoretical and algorithmic framework that unifies predictive uncertainty and safe decision-making. Our key idea is

instead of calibrating prediction sets for coverage, we directly calibrate decisions for low risk.

Our main algorithmic innovation is a class of algorithms called *conformal controllers*.
A conformal controller starts with a conformal control variable, λtsubscript𝜆𝑡\lambda\_{t}italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT, which determines the decision-maker’s conservatism or aggressiveness.
Then, it dynamically adjusts λtsubscript𝜆𝑡\lambda\_{t}italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT to balance risk and performance in such a way that guarantees a low risk.
The main practical benefit of this approach is its *emergent ability to ignore irrelevant uncertainty*, only accounting for that which *affects decisions*.
This can be much less conservative than the prediction-set strategy.
For example, in Figure LABEL:fig:front\_fig, the planner only considers the humans that pose a collision risk.

The contributions of this paper are threefold:

We introduce Conformal Decision Theory, the idea of directly calibrating decisions with conformal controllers. This extends the line of work in online adversarial conformal prediction [[15](#bib.bib15), [30](#bib.bib30), [18](#bib.bib18), [31](#bib.bib31)] to the decision-making setting.

We prove finite-time risk bounds for conformal controllers. Even when applied to prediction sets, these results are stronger than any previously known results for online adversarial conformal prediction.

We show the utility of the framework in three simulations where Conformal Decision Theory is applied to robot navigation: the Stanford Drone Dataset [[1](#bib.bib1)], a stock trading simulation, and a robot manufacturing example.

The main potential impact of this work is to broaden the scope of conformal prediction.
Our methods are more appropriate for disciplines that focus on decision-making, such as control theory, reinforcement learning, and logistics.
In these disciplines, algorithms are ultimately evaluated by the decisions, not the predictions, that they make.
Furthermore, there are many settings where it does not make sense to construct prediction sets, and our technique can provide a distribution-free outlook for such problems (see, e.g., Section [IV-B](#S4.SS2 "IV-B Manufacturing Assembly Line Robot ‣ IV Experiments ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions")).

## II Conformal Decision Theory

Conformal Decision Theory (CDT) is an approach for calibrating an agent’s decisions to achieve statistical guarantees for the realized average loss of those decisions.
Consider a decision-making agent whose input space is 𝒳𝒳\mathcal{X}caligraphic\_X and action space is 𝒰𝒰\mathcal{U}caligraphic\_U.
In our running example of robot navigation, xt∈𝒳subscript𝑥𝑡𝒳x\_{t}\in\mathcal{X}italic\_x start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ∈ caligraphic\_X captures the current state of the robot, the current scene information (e.g., environment geometry), and the agent information (e.g., pedestrian predictions) while ut∈𝒰subscript𝑢𝑡𝒰u\_{t}\in\mathcal{U}italic\_u start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ∈ caligraphic\_U is the action that the ego vehicle plans at the current time t𝑡titalic\_t.
At time t𝑡titalic\_t, the agent has access to a family of *decision functions*

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒟t:={Dtλ:𝒳→𝒰,λ∈ℝ},assignsubscript𝒟𝑡conditional-setsubscriptsuperscript𝐷𝜆𝑡formulae-sequence→𝒳𝒰𝜆ℝ\mathcal{D}\_{t}:=\left\{D^{\lambda}\_{t}:\mathcal{X}\rightarrow\mathcal{U},% \lambda\in\mathbb{R}\right\},caligraphic\_D start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT := { italic\_D start\_POSTSUPERSCRIPT italic\_λ end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT : caligraphic\_X → caligraphic\_U , italic\_λ ∈ blackboard\_R } , |  | (1) |

parameterized by λ𝜆\lambdaitalic\_λ, which we call a *conformal control variable*.
One should think of λ𝜆\lambdaitalic\_λ as indexing the decisions from least to most conservative.
In Figure LABEL:fig:front\_fig, 𝒟tsubscript𝒟𝑡\mathcal{D}\_{t}caligraphic\_D start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT is the set of dynamically feasible splines at time t𝑡titalic\_t, λ𝜆\lambdaitalic\_λ is the coefficient of the reward term for avoiding humans, and Dtλsubscriptsuperscript𝐷𝜆𝑡D^{\lambda}\_{t}italic\_D start\_POSTSUPERSCRIPT italic\_λ end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT is the spline maximizing the total reward given λ𝜆\lambdaitalic\_λ.

Assessing the quality of an agent’s decision depends on a space of targets 𝒴𝒴\mathcal{Y}caligraphic\_Y. Importantly, the realizations of these targets are *unknown* at the time of the decision; the agent only observes them at deployment time, after decisions are made, and in an online fashion. For example, the robot in Figure LABEL:fig:front\_fig does not know the true future state of nearby pedestrians; at any current time t𝑡titalic\_t, it only knows the (potentially erroneous) pedestrian predictions. In this example, 𝒴𝒴\mathcal{Y}caligraphic\_Y is the space of pedestrian states (e.g., 2D positions) and yt∈𝒴subscript𝑦𝑡𝒴y\_{t}\in\mathcal{Y}italic\_y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ∈ caligraphic\_Y is the true state that the pedestrian moves to at time t𝑡titalic\_t.

Mathematically, the quality of the decision-making is quantified by a *loss function* ℒ:𝒰×𝒴→[0,1]:ℒ→𝒰𝒴01\mathcal{L}:\mathcal{U}\times\mathcal{Y}\rightarrow[0,1]caligraphic\_L : caligraphic\_U × caligraphic\_Y → [ 0 , 1 ].111The framework works for any bounded loss, but we assume the loss to be in [0,1]01[0,1][ 0 , 1 ] for simplicity.
Often, the loss is more likely to be large when aggressive decisions are taken—i.e., when λ𝜆\lambdaitalic\_λ is large.
For example, ℒℒ\mathcal{L}caligraphic\_L may be the distance from the planned spline Dtλsubscriptsuperscript𝐷𝜆𝑡D^{\lambda}\_{t}italic\_D start\_POSTSUPERSCRIPT italic\_λ end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT to the nearest human ytsubscript𝑦𝑡y\_{t}italic\_y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT.
Aggressive decisions can be unsafe, but taking λ𝜆\lambdaitalic\_λ too small yields conservative and under-performing decisions.

We seek an algorithm for adapting λtsubscript𝜆𝑡\lambda\_{t}italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT (and thus the corresponding decision Dtλsubscriptsuperscript𝐷𝜆𝑡D^{\lambda}\_{t}italic\_D start\_POSTSUPERSCRIPT italic\_λ end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT) at each time step such that the average loss is controlled in hindsight for any realization of an input-target sequence {(xt,yt)}t=1Tsubscriptsuperscriptsubscript𝑥𝑡subscript𝑦𝑡𝑇𝑡1\{(x\_{t},y\_{t})\}^{T}\_{t=1}{ ( italic\_x start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) } start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT.
This is commonly known as the *adversarial sequence model* [[32](#bib.bib32), [15](#bib.bib15)].
In this setting, our goal is to set λ1:Tsubscript𝜆:1𝑇\lambda\_{1:T}italic\_λ start\_POSTSUBSCRIPT 1 : italic\_T end\_POSTSUBSCRIPT to achieve a *long-term risk bound*:

|  |  |  |  |
| --- | --- | --- | --- |
|  | find ⁢λ1:T⁢ s.t. ⁢R^T⁢(𝒟,λ1:T)≤ε+CT,find subscript𝜆:1𝑇 s.t. subscript^𝑅𝑇𝒟subscript𝜆:1𝑇𝜀𝐶𝑇\text{find }\lambda\_{1:T}\text{ s.t. }\hat{R}\_{T}(\mathcal{D},\lambda\_{1:T})% \leq\varepsilon+\frac{C}{T},find italic\_λ start\_POSTSUBSCRIPT 1 : italic\_T end\_POSTSUBSCRIPT s.t. over^ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( caligraphic\_D , italic\_λ start\_POSTSUBSCRIPT 1 : italic\_T end\_POSTSUBSCRIPT ) ≤ italic\_ε + divide start\_ARG italic\_C end\_ARG start\_ARG italic\_T end\_ARG , |  | (2) |

where ε𝜀\varepsilonitalic\_ε is a pre-defined risk level in [0,1]01[0,1][ 0 , 1 ], C𝐶Citalic\_C is a (small) constant, and

|  |  |  |  |
| --- | --- | --- | --- |
|  | R^T⁢(𝒟1:T,λ1:T):=1T⁢∑t=1Tℒ⁢(Dtλt⁢(xt),yt)andR^0=0.formulae-sequenceassignsubscript^𝑅𝑇subscript𝒟:1𝑇subscript𝜆:1𝑇  1𝑇superscriptsubscript𝑡1𝑇ℒsubscriptsuperscript𝐷subscript𝜆𝑡𝑡subscript𝑥𝑡subscript𝑦𝑡andsubscript^𝑅00\hat{R}\_{T}(\mathcal{D}\_{1:T},\lambda\_{1:T}):=\frac{1}{T}\sum\_{t=1}^{T}% \mathcal{L}(D^{\lambda\_{t}}\_{t}(x\_{t}),y\_{t})\quad{\rm and}\quad\hat{R}\_{0}=0.over^ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( caligraphic\_D start\_POSTSUBSCRIPT 1 : italic\_T end\_POSTSUBSCRIPT , italic\_λ start\_POSTSUBSCRIPT 1 : italic\_T end\_POSTSUBSCRIPT ) := divide start\_ARG 1 end\_ARG start\_ARG italic\_T end\_ARG ∑ start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT caligraphic\_L ( italic\_D start\_POSTSUPERSCRIPT italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ( italic\_x start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) , italic\_y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) roman\_and over^ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT 0 end\_POSTSUBSCRIPT = 0 . |  | (3) |

The bound in ([2](#S2.E2 "2 ‣ II Conformal Decision Theory ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions")) can be readily extended to

|  |  |  |  |
| --- | --- | --- | --- |
|  | R^T⁢(𝒟,λ1:T)≤ε+C⋅h⁢(T)T,subscript^𝑅𝑇𝒟subscript𝜆:1𝑇𝜀⋅𝐶ℎ𝑇𝑇\hat{R}\_{T}(\mathcal{D},\lambda\_{1:T})\leq\varepsilon+\frac{C\cdot h(T)}{T},over^ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( caligraphic\_D , italic\_λ start\_POSTSUBSCRIPT 1 : italic\_T end\_POSTSUBSCRIPT ) ≤ italic\_ε + divide start\_ARG italic\_C ⋅ italic\_h ( italic\_T ) end\_ARG start\_ARG italic\_T end\_ARG , |  | (4) |

where h⁢(T)ℎ𝑇h(T)italic\_h ( italic\_T ) is any sublinear function; i.e., one where h⁢(T)/T→0→ℎ𝑇𝑇0h(T)/T\to 0italic\_h ( italic\_T ) / italic\_T → 0 as T→∞→𝑇T\to\inftyitalic\_T → ∞.

## III Theory & Conformal Controller Algorithm

In this section, we prove the core theoretical results behind Conformal Decision Theory. Specifically, we show that any sequence of families of decision functions 𝒟1:Tsubscript𝒟:1𝑇\mathcal{D}\_{1:T}caligraphic\_D start\_POSTSUBSCRIPT 1 : italic\_T end\_POSTSUBSCRIPT that are eventually safe can be calibrated online to achieve bounded long-term risk.
We then introduce an algorithm called ConformalController which solves Equation ([2](#S2.E2 "2 ‣ II Conformal Decision Theory ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions")) under the assumption of eventual safety.

###### Definition 1 (Eventually Safe).

In the setting above, we say that 𝒟1:Tsubscript𝒟normal-:1𝑇\mathcal{D}\_{1:T}caligraphic\_D start\_POSTSUBSCRIPT 1 : italic\_T end\_POSTSUBSCRIPT is eventually safe if ∃εsafe∈[0,1],λsafe∈ℝformulae-sequencesuperscript𝜀normal-safe01superscript𝜆normal-safeℝ\exists\;\varepsilon^{\rm safe}\in[0,1],\lambda^{\rm safe}\in\mathbb{R}∃ italic\_ε start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT ∈ [ 0 , 1 ] , italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT ∈ blackboard\_R and a time horizon K>0𝐾0K>0italic\_K > 0 such that uniformly over all sequences λ1:Ksubscript𝜆normal-:1𝐾\lambda\_{1:K}italic\_λ start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT and {(x1,y1),…,(xk,yk)}∈𝒳×𝒴subscript𝑥1subscript𝑦1normal-…subscript𝑥𝑘subscript𝑦𝑘𝒳𝒴\{(x\_{1},y\_{1}),\dots,(x\_{k},y\_{k})\}\in\mathcal{X}\times\mathcal{Y}{ ( italic\_x start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , italic\_y start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ) , … , ( italic\_x start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT , italic\_y start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ) } ∈ caligraphic\_X × caligraphic\_Y,

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | {∀k∈[K],λk\displaystyle\big{\{}\forall k\in[K],\lambda\_{k}{ ∀ italic\_k ∈ [ italic\_K ] , italic\_λ start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT | ≤λsafe}\displaystyle\leq\lambda^{\rm safe}\big{\}}≤ italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT } |  | (5) |
|  |  | ⟹1K⁢∑k=1Kℒ⁢(Dkλk⁢(xk),yk)≤εsafe.⟹absent1𝐾superscriptsubscript𝑘1𝐾ℒsubscriptsuperscript𝐷subscript𝜆𝑘𝑘subscript𝑥𝑘subscript𝑦𝑘superscript𝜀safe\displaystyle\Longrightarrow\frac{1}{K}\sum\_{k=1}^{K}\mathcal{L}\left(D^{% \lambda\_{k}}\_{k}(x\_{k}),y\_{k}\right)\leq\varepsilon^{\rm safe}.⟹ divide start\_ARG 1 end\_ARG start\_ARG italic\_K end\_ARG ∑ start\_POSTSUBSCRIPT italic\_k = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_K end\_POSTSUPERSCRIPT caligraphic\_L ( italic\_D start\_POSTSUPERSCRIPT italic\_λ start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ( italic\_x start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ) , italic\_y start\_POSTSUBSCRIPT italic\_k end\_POSTSUBSCRIPT ) ≤ italic\_ε start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT . |  |

Intuitively, this condition says that there exists a safe value λsafesuperscript𝜆safe\lambda^{\rm safe}italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT such that if the conformal control variable lands below that value, it will incur a low risk εsafesuperscript𝜀safe\varepsilon^{\rm safe}italic\_ε start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT after no more than K𝐾Kitalic\_K time steps.
For example, even the most conservative robot planner may not be able to change its trajectory fast enough *in a single timestep*, but it could possibly do so in K𝐾Kitalic\_K time steps.
Note that this is a strictly weaker assumption than that used for the proofs in other works, such as [[15](#bib.bib15), [33](#bib.bib33), [31](#bib.bib31)], which require K=1𝐾1K=1italic\_K = 1.
Conformal controllers are simple yet efficient algorithms that solve the Conformal Decision Theory problem stated in Equation ([2](#S2.E2 "2 ‣ II Conformal Decision Theory ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions")).
An example is below.

###### Theorem 1 (Conformal Controller).

Consider the following update rule for λ𝜆\lambdaitalic\_λ:

|  |  |  |  |
| --- | --- | --- | --- |
|  | λt+1=λt+η⁢(ε−ℓt),subscript𝜆𝑡1subscript𝜆𝑡𝜂𝜀subscriptℓ𝑡\lambda\_{t+1}=\lambda\_{t}+\eta\left(\varepsilon-\ell\_{t}\right),italic\_λ start\_POSTSUBSCRIPT italic\_t + 1 end\_POSTSUBSCRIPT = italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT + italic\_η ( italic\_ε - roman\_ℓ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) , |  | (6) |

where η>0𝜂0\eta>0italic\_η > 0.
If λ1≥λsafe−ηsubscript𝜆1superscript𝜆normal-safe𝜂\lambda\_{1}\geq\lambda^{\rm safe}-\etaitalic\_λ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ≥ italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT - italic\_η and 𝒟1:Tsubscript𝒟normal-:1𝑇\mathcal{D}\_{1:T}caligraphic\_D start\_POSTSUBSCRIPT 1 : italic\_T end\_POSTSUBSCRIPT satisfies Definition [1](#Thmdefinition1 "Definition 1 (Eventually Safe). ‣ III Theory & Conformal Controller Algorithm ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions") for a given K≥1𝐾1K\geq 1italic\_K ≥ 1 and εsafe≤εsuperscript𝜀normal-safe𝜀\varepsilon^{\rm safe}\leq\varepsilonitalic\_ε start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT ≤ italic\_ε, then for any realization of the data, the empirical risk is bounded:

|  |  |  |  |
| --- | --- | --- | --- |
|  | R^t⁢(λ1:t)≤ε+(λ1−λsafe)/η+Kt,subscript^𝑅𝑡subscript𝜆:1𝑡𝜀subscript𝜆1superscript𝜆safe𝜂𝐾𝑡\hat{R}\_{t}(\lambda\_{1:t})\leq\varepsilon+\frac{(\lambda\_{1}-\lambda^{\rm safe% })/\eta+K}{t},over^ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ( italic\_λ start\_POSTSUBSCRIPT 1 : italic\_t end\_POSTSUBSCRIPT ) ≤ italic\_ε + divide start\_ARG ( italic\_λ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT - italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT ) / italic\_η + italic\_K end\_ARG start\_ARG italic\_t end\_ARG , |  | (7) |

for all t∈[T]𝑡delimited-[]𝑇t\in[T]italic\_t ∈ [ italic\_T ].

The update in ([6](#S3.E6 "6 ‣ Theorem 1 (Conformal Controller). ‣ III Theory & Conformal Controller Algorithm ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions")) resembles ACI [[15](#bib.bib15)] and is a hybrid between the RollingRC update [[18](#bib.bib18)], and the P-controller update [[31](#bib.bib31)].
The difference is that the update is applied to λ𝜆\lambdaitalic\_λ and not the conformal quantile or quantile level.

###### Proof of [Theorem 1](#Thmtheorem1 "Theorem 1 (Conformal Controller). ‣ III Theory & Conformal Controller Algorithm ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions").

By the definition of the update rule,

|  |  |  |  |
| --- | --- | --- | --- |
|  | λt=λ1+η⁢∑s=1t(ε−ℓs).subscript𝜆𝑡subscript𝜆1𝜂superscriptsubscript𝑠1𝑡𝜀subscriptℓ𝑠\lambda\_{t}=\lambda\_{1}+\eta\sum\limits\_{s=1}^{t}(\varepsilon-\ell\_{s}).italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT = italic\_λ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT + italic\_η ∑ start\_POSTSUBSCRIPT italic\_s = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_t end\_POSTSUPERSCRIPT ( italic\_ε - roman\_ℓ start\_POSTSUBSCRIPT italic\_s end\_POSTSUBSCRIPT ) . |  | (8) |

Dividing both sides by −η⁢T𝜂𝑇-\eta T- italic\_η italic\_T yields

|  |  |  |  |
| --- | --- | --- | --- |
|  | R^t⁢(λ1:t)=1t⁢∑s=1tℓssubscript^𝑅𝑡subscript𝜆:1𝑡1𝑡superscriptsubscript𝑠1𝑡subscriptℓ𝑠\displaystyle\hat{R}\_{t}(\lambda\_{1:t})=\frac{1}{t}\sum\limits\_{s=1}^{t}\ell\_{s}over^ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ( italic\_λ start\_POSTSUBSCRIPT 1 : italic\_t end\_POSTSUBSCRIPT ) = divide start\_ARG 1 end\_ARG start\_ARG italic\_t end\_ARG ∑ start\_POSTSUBSCRIPT italic\_s = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_t end\_POSTSUPERSCRIPT roman\_ℓ start\_POSTSUBSCRIPT italic\_s end\_POSTSUBSCRIPT | =ε+λ1−λtη⁢t.absent𝜀subscript𝜆1subscript𝜆𝑡𝜂𝑡\displaystyle=\varepsilon+\frac{\lambda\_{1}-\lambda\_{t}}{\eta t}.= italic\_ε + divide start\_ARG italic\_λ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT - italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT end\_ARG start\_ARG italic\_η italic\_t end\_ARG . |  |

To conclude, we just need to show that λt≥O⁢(K)subscript𝜆𝑡𝑂𝐾\lambda\_{t}\geq O(K)italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ≥ italic\_O ( italic\_K ), which is shown in the following Lemma [1.1](#Thmtheorem1.Thmlemma1 "Lemma 1.1. ‣ III Theory & Conformal Controller Algorithm ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions").
∎

###### Lemma 1.1.

For the sequence in Equation  [6](#S3.E6 "6 ‣ Theorem 1 (Conformal Controller). ‣ III Theory & Conformal Controller Algorithm ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions"), with probability one, we have that the parameter λtsubscript𝜆𝑡\lambda\_{t}italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT is bounded below by λt≥λsafe−K⁢ηsubscript𝜆𝑡superscript𝜆normal-safe𝐾𝜂\lambda\_{t}\geq\lambda^{\rm safe}-K\etaitalic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ≥ italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT - italic\_K italic\_η, for all t∈[T]𝑡delimited-[]𝑇t\in[T]italic\_t ∈ [ italic\_T ].

###### Proof.

First note that the maximal change in the parameter is supt∈[T]|λt+1−λt|<ηsubscriptsupremum𝑡delimited-[]𝑇subscript𝜆𝑡1subscript𝜆𝑡𝜂\sup\_{t\in[T]}|\lambda\_{t+1}-\lambda\_{t}|<\etaroman\_sup start\_POSTSUBSCRIPT italic\_t ∈ [ italic\_T ] end\_POSTSUBSCRIPT | italic\_λ start\_POSTSUBSCRIPT italic\_t + 1 end\_POSTSUBSCRIPT - italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT | < italic\_η, because ℓt∈[0,1]subscriptℓ𝑡01\ell\_{t}\in[0,1]roman\_ℓ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ∈ [ 0 , 1 ] and ε∈[0,1]𝜀01\varepsilon\in[0,1]italic\_ε ∈ [ 0 , 1 ]. We will then proceed by contradiction: Assume that with non-zero probability, infu∈[T]λu<λsafe−K⁢ηsubscriptinfimum𝑢delimited-[]𝑇subscript𝜆𝑢superscript𝜆safe𝐾𝜂\inf\_{u\in[T]}\lambda\_{u}<\lambda^{\rm safe}-K\etaroman\_inf start\_POSTSUBSCRIPT italic\_u ∈ [ italic\_T ] end\_POSTSUBSCRIPT italic\_λ start\_POSTSUBSCRIPT italic\_u end\_POSTSUBSCRIPT < italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT - italic\_K italic\_η. Denote t=arg⁡minu∈[T]⁡{u,λu<λsafe−K⁢η}𝑡subscript𝑢delimited-[]𝑇𝑢subscript𝜆𝑢superscript𝜆safe𝐾𝜂t=\arg\min\_{u\in[T]}\{u,\lambda\_{u}<\lambda^{\rm safe}-K\eta\}italic\_t = roman\_arg roman\_min start\_POSTSUBSCRIPT italic\_u ∈ [ italic\_T ] end\_POSTSUBSCRIPT { italic\_u , italic\_λ start\_POSTSUBSCRIPT italic\_u end\_POSTSUBSCRIPT < italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT - italic\_K italic\_η }. That is, t𝑡titalic\_t is the first instant when the parameter goes below that lower bound. Because the max difference between successive steps is η𝜂\etaitalic\_η, we can prove recursively that ∀k∈{0,…,K},λt−k<λsafe−(K−k)⁢ηformulae-sequencefor-all𝑘0…𝐾subscript𝜆𝑡𝑘superscript𝜆safe𝐾𝑘𝜂\forall k\in\{0,\dots,K\},\lambda\_{t-k}<\lambda^{\rm safe}-(K-k)\eta∀ italic\_k ∈ { 0 , … , italic\_K } , italic\_λ start\_POSTSUBSCRIPT italic\_t - italic\_k end\_POSTSUBSCRIPT < italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT - ( italic\_K - italic\_k ) italic\_η. Note that, from those inequalities, we deduce that t>K𝑡𝐾t>Kitalic\_t > italic\_K since λ1≥λsafe−ηsubscript𝜆1superscript𝜆safe𝜂\lambda\_{1}\geq\lambda^{\rm safe}-\etaitalic\_λ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ≥ italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT - italic\_η. By recursively applying the update rule λt=λt−K+K⁢η⁢(ε−1K⁢∑k=1Kℓt−k)subscript𝜆𝑡subscript𝜆𝑡𝐾𝐾𝜂𝜀1𝐾superscriptsubscript𝑘1𝐾subscriptℓ𝑡𝑘\lambda\_{t}=\lambda\_{t-K}+K\eta(\varepsilon-\frac{1}{K}\sum\_{k=1}^{K}\ell\_{t-k})italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT = italic\_λ start\_POSTSUBSCRIPT italic\_t - italic\_K end\_POSTSUBSCRIPT + italic\_K italic\_η ( italic\_ε - divide start\_ARG 1 end\_ARG start\_ARG italic\_K end\_ARG ∑ start\_POSTSUBSCRIPT italic\_k = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_K end\_POSTSUPERSCRIPT roman\_ℓ start\_POSTSUBSCRIPT italic\_t - italic\_k end\_POSTSUBSCRIPT ), we have:

|  |  |  |
| --- | --- | --- |
|  | (∀k∈{0,…,K−1},λt−k<λsafe)formulae-sequencefor-all𝑘0…𝐾1subscript𝜆𝑡𝑘superscript𝜆safe\displaystyle\left(\forall k\in\{0,\dots,K-1\},\;\lambda\_{t-k}<\lambda^{\rm safe% }\right)( ∀ italic\_k ∈ { 0 , … , italic\_K - 1 } , italic\_λ start\_POSTSUBSCRIPT italic\_t - italic\_k end\_POSTSUBSCRIPT < italic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT ) |  |
|  |  |  |
| --- | --- | --- |
|  | ⟹1K⁢∑k=1Kℓt−k≤εsafe⟹absent1𝐾superscriptsubscript𝑘1𝐾subscriptℓ𝑡𝑘superscript𝜀safe\displaystyle\Longrightarrow\frac{1}{K}\sum\_{k=1}^{K}\ell\_{t-k}\leq\varepsilon% ^{\rm safe}⟹ divide start\_ARG 1 end\_ARG start\_ARG italic\_K end\_ARG ∑ start\_POSTSUBSCRIPT italic\_k = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_K end\_POSTSUPERSCRIPT roman\_ℓ start\_POSTSUBSCRIPT italic\_t - italic\_k end\_POSTSUBSCRIPT ≤ italic\_ε start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT |  |
|  |  |  |
| --- | --- | --- |
|  | ⟹λt=λt−K+K⁢η⁢(ε−1K⁢∑k=1Kℓt−k)≥λt−K+K⁢η⁢(ε−εsafe)⟹absentsubscript𝜆𝑡subscript𝜆𝑡𝐾𝐾𝜂𝜀1𝐾superscriptsubscript𝑘1𝐾subscriptℓ𝑡𝑘subscript𝜆𝑡𝐾𝐾𝜂𝜀superscript𝜀safe\displaystyle\Longrightarrow\lambda\_{t}=\lambda\_{t-K}+K\eta\left(\varepsilon-% \frac{1}{K}\sum\_{k=1}^{K}\ell\_{t-k}\right)\geq\lambda\_{t-K}+K\eta(\varepsilon-% \varepsilon^{\rm safe})⟹ italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT = italic\_λ start\_POSTSUBSCRIPT italic\_t - italic\_K end\_POSTSUBSCRIPT + italic\_K italic\_η ( italic\_ε - divide start\_ARG 1 end\_ARG start\_ARG italic\_K end\_ARG ∑ start\_POSTSUBSCRIPT italic\_k = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_K end\_POSTSUPERSCRIPT roman\_ℓ start\_POSTSUBSCRIPT italic\_t - italic\_k end\_POSTSUBSCRIPT ) ≥ italic\_λ start\_POSTSUBSCRIPT italic\_t - italic\_K end\_POSTSUBSCRIPT + italic\_K italic\_η ( italic\_ε - italic\_ε start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT ) |  |
|  |  |  |
| --- | --- | --- |
|  | ⟹λt≥λt−K.⟹absentsubscript𝜆𝑡subscript𝜆𝑡𝐾\displaystyle\Longrightarrow\lambda\_{t}\geq\lambda\_{t-K}.⟹ italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ≥ italic\_λ start\_POSTSUBSCRIPT italic\_t - italic\_K end\_POSTSUBSCRIPT . |  |

Since t𝑡titalic\_t is the first ever timestep to go below λsafe−K⁢ηsuperscript𝜆safe𝐾𝜂\lambda^{\rm safe}-K\etaitalic\_λ start\_POSTSUPERSCRIPT roman\_safe end\_POSTSUPERSCRIPT - italic\_K italic\_η, this is a contradiction.
∎

### Conformal Decision Theory in Batch

Conformal decision theory can also be applied in the so-called batch setting, wherein a separate calibration dataset is available for learning a safe decision.
Here, a dataset or simulator allows for offline experimentation to quantify the risk of different decisions, e.g., offline RL. This requires a different statistical setup.

Consider the case of n+1𝑛1n+1italic\_n + 1 exchangeable decision functions D1⁢(λ),…,Dn+1⁢(λ)

subscript𝐷1𝜆…subscript𝐷𝑛1𝜆D\_{1}(\lambda),\ldots,D\_{n+1}(\lambda)italic\_D start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ( italic\_λ ) , … , italic\_D start\_POSTSUBSCRIPT italic\_n + 1 end\_POSTSUBSCRIPT ( italic\_λ ) and an associated loss function ℒℒ\mathcal{L}caligraphic\_L taking a decision and returning a value in [0,1]01[0,1][ 0 , 1 ].
The first n𝑛nitalic\_n decision functions will be used for calibration of a parameter λ^^𝜆\hat{\lambda}over^ start\_ARG italic\_λ end\_ARG that will be used in the final decision.
These exchangeable decision functions may be produced, for example, by applying a single decision function to a sequence of exchangeable data points.
For the sake of simplicity, we assume that the decisions have monotone loss, i.e., that for all i𝑖iitalic\_i,

|  |  |  |  |
| --- | --- | --- | --- |
|  | λ1≤λ2⟹ℒ⁢(Di⁢(λ1))≤ℒ⁢(Di⁢(λ2)).subscript𝜆1subscript𝜆2ℒsubscript𝐷𝑖subscript𝜆1ℒsubscript𝐷𝑖subscript𝜆2\lambda\_{1}\leq\lambda\_{2}\implies\mathcal{L}\left(D\_{i}(\lambda\_{1})\right)% \leq\mathcal{L}\left(D\_{i}(\lambda\_{2})\right).italic\_λ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ≤ italic\_λ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT ⟹ caligraphic\_L ( italic\_D start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ( italic\_λ start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT ) ) ≤ caligraphic\_L ( italic\_D start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ( italic\_λ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT ) ) . |  | (9) |

Following [[34](#bib.bib34)], the conformal control variable can be chosen as

|  |  |  |  |
| --- | --- | --- | --- |
|  | λ^=sup{λ:1n⁢∑i=1nℒ⁢(Di⁢(λ))≤ϵ−1−ϵn}.^𝜆supremumconditional-set𝜆1𝑛superscriptsubscript𝑖1𝑛ℒsubscript𝐷𝑖𝜆italic-ϵ1italic-ϵ𝑛\hat{\lambda}=\sup\left\{\lambda:\frac{1}{n}\sum\limits\_{i=1}^{n}\mathcal{L}% \left(D\_{i}(\lambda)\right)\leq\epsilon-\frac{1-\epsilon}{n}\right\}.over^ start\_ARG italic\_λ end\_ARG = roman\_sup { italic\_λ : divide start\_ARG 1 end\_ARG start\_ARG italic\_n end\_ARG ∑ start\_POSTSUBSCRIPT italic\_i = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_n end\_POSTSUPERSCRIPT caligraphic\_L ( italic\_D start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT ( italic\_λ ) ) ≤ italic\_ϵ - divide start\_ARG 1 - italic\_ϵ end\_ARG start\_ARG italic\_n end\_ARG } . |  | (10) |

This will give a risk guarantee as a corollary of Theorem 1 of [[34](#bib.bib34)].

###### Corollary 2.

With the choice of λ^normal-^𝜆\hat{\lambda}over^ start\_ARG italic\_λ end\_ARG above,

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝔼⁢[ℒ⁢(Dn+1⁢(λ^))]≤ϵ.𝔼delimited-[]ℒsubscript𝐷𝑛1^𝜆italic-ϵ\mathbb{E}\left[\mathcal{L}\left(D\_{n+1}(\hat{\lambda})\right)\right]\leq\epsilon.blackboard\_E [ caligraphic\_L ( italic\_D start\_POSTSUBSCRIPT italic\_n + 1 end\_POSTSUBSCRIPT ( over^ start\_ARG italic\_λ end\_ARG ) ) ] ≤ italic\_ϵ . |  | (11) |

Though the validity of the algorithm follows from the theory of conformal risk control, it is substantially different in practice and deserves further study.
Specifically, unlike the previous methods, in order to calculate λ^^𝜆\hat{\lambda}over^ start\_ARG italic\_λ end\_ARG, one must iterate through a sequence of counterfactual decisions (in other words, putative values of λ𝜆\lambdaitalic\_λ) and test what the effect would have been.
This restricts the applications of the batch algorithm and also presents an opportunity for future work to make it more efficient and expand its scope.

## IV Experiments

We demonstrate Conformal Decision Theory in three autonomous decision-making domains, which exhibit three different ways in which a conformal controller can be instantiated.
First, we consider a robot-navigation-around- humans example in the Stanford Drone Dataset [[1](#bib.bib1)], where CDT tunes the robot’s reward function in an online manner to be safe but efficient.
Next, we model a manufacturing setting where CDT directly calibrates the speed of the conveyor belt under a robot to achieve high-throughput and successful robot grasps.
Finally, we study an automated high-frequency trading example where CDT must optimize the buying and selling of stocks.

### IV-A Robot Navigation in Stanford Drone Dataset

Robot navigation around people must balance safety (i.e., not colliding with humans) and efficiency (i.e., the robot makes progress towards a goal). To ensure that the risk of collision is low while still making progress to the goal, the robot will calibrate its cost function at run-time using a conformal controller.

|  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | | Metrics | | | | | | | | |
| Method | η𝜂\etaitalic\_η | success | time (s) | safe | min dist (m) | avg dist (m) | 5% dist (m) | 10% dist (m) | 25% dist (m) | 50% dist (m) |
| Aggressive | n/a | ✓ | 8.567 | ✗ | 0.1595 | 4.058 | 1.253 | 1.546 | 2.495 | 4.021 |
| ACI  (α=0.01𝛼0.01\alpha=0.01italic\_α = 0.01) | 0 | ✓ | 27.17 | ✗ | 0.07612 | 5.201 | 1.842 | 2.415 | 3.9 | 5.614 |
| 0.01 | ✓ | 26.67 | ✗ | 0.8026 | 4.575 | 2.261 | 3.014 | 3.507 | 4.574 |
| 0.1 | ✓ | 24.73 | ✗ | 0.7906 | 4.771 | 2.284 | 2.825 | 3.561 | 4.78 |
| Conformal  Controller  (ε=2𝜀2\varepsilon=2italic\_ε = 2m) | 50 | ✓ | 20.03 | ✗ | 0.6122 | 3.299 | 0.8688 | 1.426 | 2.022 | 2.978 |
| 100 | ✓ | 17.4 | ✓ | 1.142 | 3.794 | 1.678 | 1.811 | 2.378 | 3.262 |
| 500 | ✓ | 17.33 | ✓ | 1.116 | 3.989 | 1.69 | 1.812 | 2.452 | 3.795 |
| 1000 | ✓ | 16.17 | ✓ | 1.265 | 3.599 | 1.698 | 1.81 | 2.282 | 3.303 |
| Conservative | n/a | ✗ | ∞\infty∞ | ✓ | 2.268 | 6.291 | 3.801 | 3.982 | 4.982 | 5.993 |

![Refer to caption](x1.png)

Decision Function & Parameterization.
The robot plans via model predictive control, where at each timestep it fits a minimum-cost spline subject to its dynamic constraints, which are modeled as a nonlinear Dubins car [[35](#bib.bib35)]. Let g:=[gx,gy]∈ℝ2assign𝑔subscript𝑔𝑥subscript𝑔𝑦superscriptℝ2g:=[g\_{x},g\_{y}]\in\mathbb{R}^{2}italic\_g := [ italic\_g start\_POSTSUBSCRIPT italic\_x end\_POSTSUBSCRIPT , italic\_g start\_POSTSUBSCRIPT italic\_y end\_POSTSUBSCRIPT ] ∈ blackboard\_R start\_POSTSUPERSCRIPT 2 end\_POSTSUPERSCRIPT be the robot’s goal location.
Let t𝑡titalic\_t be the current time, H<T𝐻𝑇H<Titalic\_H < italic\_T be the planning horizon, and ut:t+H∈ℝH×3subscript𝑢:𝑡𝑡𝐻superscriptℝ𝐻3u\_{t:t+H}\in\mathbb{R}^{H\times 3}italic\_u start\_POSTSUBSCRIPT italic\_t : italic\_t + italic\_H end\_POSTSUBSCRIPT ∈ blackboard\_R start\_POSTSUPERSCRIPT italic\_H × 3 end\_POSTSUPERSCRIPT be a spline consisting of the robot’s planar position and orientation.
The robot also gets as input the current set of short-horizon predictions of each human’s state, xt:t+H∈𝒫tsubscript𝑥:𝑡𝑡𝐻subscript𝒫𝑡x\_{t:t+H}\in\mathcal{P}\_{t}italic\_x start\_POSTSUBSCRIPT italic\_t : italic\_t + italic\_H end\_POSTSUBSCRIPT ∈ caligraphic\_P start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT, generated by an autoregressive predictive model [[36](#bib.bib36)]. Note that this set 𝒫tsubscript𝒫𝑡\mathcal{P}\_{t}caligraphic\_P start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT can include predictions for multiple humans in the scene (as shown in Figure LABEL:fig:front\_fig).
The robot’s planning objective is

|  |  |  |  |
| --- | --- | --- | --- |
|  | J⁢(ut:t+H;𝒫t,λ):=∑τ=tt+H‖uτpos−g‖⏟Goal distance+λ⋅infxτ∈𝒫t‖uτpos−xτ‖22⏟Human avoidance,assign𝐽  subscript𝑢:𝑡𝑡𝐻subscript𝒫𝑡𝜆superscriptsubscript𝜏𝑡𝑡𝐻subscript⏟normsuperscriptsubscript𝑢𝜏pos𝑔Goal distance⋅𝜆subscript⏟subscriptinfimum  subscript𝑥𝜏subscript𝒫𝑡superscriptsubscriptnormsuperscriptsubscript𝑢𝜏possubscript𝑥𝜏22Human avoidanceJ(u\_{t:t+H};\mathcal{P}\_{t},\lambda):={\sum}\limits\_{\tau=t}^{t+H}\underbrace{% \vphantom{\inf\_{\begin{subarray}{c}x\_{\tau}\in\mathcal{P}\_{t}\end{subarray}}}% \|u\_{\tau}^{\mathrm{pos}}-g\|}\_{\text{Goal distance}}+\lambda\cdot\underbrace{% \inf\_{\begin{subarray}{c}x\_{\tau}\in\mathcal{P}\_{t}\end{subarray}}\|u\_{\tau}^{% \mathrm{pos}}-x\_{\tau}\|\_{2}^{2}}\_{\text{Human avoidance}},italic\_J ( italic\_u start\_POSTSUBSCRIPT italic\_t : italic\_t + italic\_H end\_POSTSUBSCRIPT ; caligraphic\_P start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_λ ) := ∑ start\_POSTSUBSCRIPT italic\_τ = italic\_t end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_t + italic\_H end\_POSTSUPERSCRIPT under⏟ start\_ARG ∥ italic\_u start\_POSTSUBSCRIPT italic\_τ end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT roman\_pos end\_POSTSUPERSCRIPT - italic\_g ∥ end\_ARG start\_POSTSUBSCRIPT Goal distance end\_POSTSUBSCRIPT + italic\_λ ⋅ under⏟ start\_ARG roman\_inf start\_POSTSUBSCRIPT start\_ARG start\_ROW start\_CELL italic\_x start\_POSTSUBSCRIPT italic\_τ end\_POSTSUBSCRIPT ∈ caligraphic\_P start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT end\_CELL end\_ROW end\_ARG end\_POSTSUBSCRIPT ∥ italic\_u start\_POSTSUBSCRIPT italic\_τ end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT roman\_pos end\_POSTSUPERSCRIPT - italic\_x start\_POSTSUBSCRIPT italic\_τ end\_POSTSUBSCRIPT ∥ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT 2 end\_POSTSUPERSCRIPT end\_ARG start\_POSTSUBSCRIPT Human avoidance end\_POSTSUBSCRIPT , |  | (12) |

where the notation uτpos∈ℝ2superscriptsubscript𝑢𝜏possuperscriptℝ2u\_{\tau}^{\mathrm{pos}}\in\mathbb{R}^{2}italic\_u start\_POSTSUBSCRIPT italic\_τ end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT roman\_pos end\_POSTSUPERSCRIPT ∈ blackboard\_R start\_POSTSUPERSCRIPT 2 end\_POSTSUPERSCRIPT indicates the x⁢y𝑥𝑦xyitalic\_x italic\_y-positional entries of the robot’s state at time τ𝜏\tauitalic\_τ. Note that the conformal control variable λ𝜆\lambdaitalic\_λ scales the cost of staying far away from predicted human states: if λ=0𝜆0\lambda=0italic\_λ = 0 the robot only cares about reaching the goal; if λ>0𝜆0\lambda>0italic\_λ > 0 then the robot is increasingly penalized for intersecting with predicted human trajectories.
The decision function outputs the minimum-cost trajectory for the robot

|  |  |  |  |
| --- | --- | --- | --- |
|  | Dtλ:=arg⁡minut:t+H∈𝒰⁡J⁢(ut:t+H;𝒫t,λ),assignsubscriptsuperscript𝐷𝜆𝑡subscriptsubscript𝑢:𝑡𝑡𝐻𝒰𝐽  subscript𝑢:𝑡𝑡𝐻subscript𝒫𝑡𝜆D^{\lambda}\_{t}:=\arg\min\_{u\_{t:t+H}\in\mathcal{U}}J(u\_{t:t+H};\mathcal{P}\_{t}% ,\lambda),italic\_D start\_POSTSUPERSCRIPT italic\_λ end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT := roman\_arg roman\_min start\_POSTSUBSCRIPT italic\_u start\_POSTSUBSCRIPT italic\_t : italic\_t + italic\_H end\_POSTSUBSCRIPT ∈ caligraphic\_U end\_POSTSUBSCRIPT italic\_J ( italic\_u start\_POSTSUBSCRIPT italic\_t : italic\_t + italic\_H end\_POSTSUBSCRIPT ; caligraphic\_P start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_λ ) , |  | (13) |

where 𝒰𝒰\mathcal{U}caligraphic\_U is the set of feasible splines (ones that are dynamically feasible for the robot and also do not intersect with environment obstacles). At the next timestep, the robot re-predicts the human trajectory (i.e., generates 𝒫t+1subscript𝒫𝑡1\mathcal{P}\_{t+1}caligraphic\_P start\_POSTSUBSCRIPT italic\_t + 1 end\_POSTSUBSCRIPT) and re-plans the decision Dt+1λsubscriptsuperscript𝐷𝜆𝑡1D^{\lambda}\_{t+1}italic\_D start\_POSTSUPERSCRIPT italic\_λ end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t + 1 end\_POSTSUBSCRIPT.

Loss Function.
Let 𝒴⊂ℝ2𝒴superscriptℝ2\mathcal{Y}\subset\mathbb{R}^{2}caligraphic\_Y ⊂ blackboard\_R start\_POSTSUPERSCRIPT 2 end\_POSTSUPERSCRIPT and the targets yt1,…,ytM∈𝒴

superscriptsubscript𝑦𝑡1…superscriptsubscript𝑦𝑡𝑀
𝒴y\_{t}^{1},\dots,y\_{t}^{M}\in\mathcal{Y}italic\_y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT 1 end\_POSTSUPERSCRIPT , … , italic\_y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_M end\_POSTSUPERSCRIPT ∈ caligraphic\_Y be the actual x⁢y𝑥𝑦xyitalic\_x italic\_y positions of each of the M𝑀Mitalic\_M humans that the robot observes at time t𝑡titalic\_t. The loss function is defined as the negative distance to the nearest human,

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℒ:=−infi∈[M]‖yti−utpos‖2,assignℒsubscriptinfimum𝑖delimited-[]𝑀subscriptnormsubscriptsuperscript𝑦𝑖𝑡subscriptsuperscript𝑢pos𝑡2\mathcal{L}:=-\inf\_{i\in[M]}\|y^{i}\_{t}-u^{\mathrm{pos}}\_{t}\|\_{2},caligraphic\_L := - roman\_inf start\_POSTSUBSCRIPT italic\_i ∈ [ italic\_M ] end\_POSTSUBSCRIPT ∥ italic\_y start\_POSTSUPERSCRIPT italic\_i end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT - italic\_u start\_POSTSUPERSCRIPT roman\_pos end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ∥ start\_POSTSUBSCRIPT 2 end\_POSTSUBSCRIPT , |  | (14) |

where utpossubscriptsuperscript𝑢pos𝑡u^{\mathrm{pos}}\_{t}italic\_u start\_POSTSUPERSCRIPT roman\_pos end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT is the robot’s current position. To make this value bounded, we clip the loss to the size of the video.

Metrics.
We measure a boolean safe variable indicating if the robot did not ever collide with a human.
We also measure a boolean success variable if the robot reached the goal location by the end of the interaction episode (i.e., length of video in the SDD).
We also measure the time to reach the goal location and the minimum, mean, and {5%,10%,25%,50%}percent5percent10percent25percent50\{5\%,10\%,25\%,50\%\}{ 5 % , 10 % , 25 % , 50 % } quantiles of the distance to the nearest human.

![Refer to caption](x2.png)

Experimental Setup. All methods are evaluated on interactions from the nexus\_4 video in the Stanford Drone Dataset (SDD) [[1](#bib.bib1)]. The risk threshold is ε=2⁢m𝜀2𝑚\varepsilon=2mitalic\_ε = 2 italic\_m (i.e., radius around human). The robot always starts from the same initial condition and moves to the same goal. This scenario has a high density of pedestrians, making the risk-performance tradeoff for the robot nontrivial. Our approach (CC) adapts the reward weight λtsubscript𝜆𝑡\lambda\_{t}italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT on the human collision cost based on [Equation 6](#S3.E6 "6 ‣ Theorem 1 (Conformal Controller). ‣ III Theory & Conformal Controller Algorithm ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions") so that the decision risk is calibrated. Our baseline robot planners: conservative which always uses the safe decision function Dtλ=1superscriptsubscript𝐷𝑡𝜆1D\_{t}^{\lambda=1}italic\_D start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_λ = 1 end\_POSTSUPERSCRIPT, aggressive which uses Dtλ=0superscriptsubscript𝐷𝑡𝜆0D\_{t}^{\lambda=0}italic\_D start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_λ = 0 end\_POSTSUPERSCRIPT, and ACI [[21](#bib.bib21)] which first uses adaptive conformal prediction to calibrate prediction sets and then plans to avoid these sets.

![Refer to caption](x3.png)

Results.
Quantitative results shown in Table [I](#S4.T1 "TABLE I ‣ IV-A Robot Navigation in Stanford Drone Dataset ‣ IV Experiments ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions") and qualitative results in LABEL:fig:front\_fig.
Because the conformal controller calibrates the robot’s decisions directly, it is substantially (∼29%similar-toabsentpercent29\sim 29\%∼ 29 %) faster at reaching the goal than the ACI algorithm (see visualization over time in [Figure 1](#S4.F1 "Figure 1 ‣ IV-A Robot Navigation in Stanford Drone Dataset ‣ IV Experiments ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions")).
While the aggressive baseline reaches the goal fastest, it consistently violates the safety threshold. On the other hand, the conservative baseline never completes the task, getting stuck far away from the crowds of pedestrians.
The conformal controller ensures safety so long as the learning rate is fast enough for the robot planner to quickly adapt to changes in nearby human behavior (see [Figure 3](#S4.F3 "Figure 3 ‣ IV-A Robot Navigation in Stanford Drone Dataset ‣ IV Experiments ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions")). Note that ACI can result in collisions for two reasons: 1) the prediction sets do not adapt fast enough for the spline planner to react and swerve out of the way of the pedestrian, 2) if the prediction sets become so large that there is no feasible spline and the robot must stand in
place, the pedestrians sometimes run into the robot.
This issue was independently observed in [[21](#bib.bib21)].

### IV-B Manufacturing Assembly Line Robot

Consider a factory assembly line where a robot has to grab items from a conveyor belt (left, Figure [2](#S4.F2 "Figure 2 ‣ IV-A Robot Navigation in Stanford Drone Dataset ‣ IV Experiments ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions")).
As the speed increases, the throughput of items increases but so does the ratio of robot grasp failures. The agent must calibrate the speed so that the ratio of failures over time stays below ε𝜀\varepsilonitalic\_ε.

Decision Function & Parameterization.
The agent directly modifies the speed, thus the action is defined as ut:=λtassignsubscript𝑢𝑡subscript𝜆𝑡u\_{t}:=\lambda\_{t}italic\_u start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT := italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT. Here we take λt∈[0,1]subscript𝜆𝑡01\lambda\_{t}\in[0,1]italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ∈ [ 0 , 1 ].

Risk Function. For a given conveyor belt speed λ𝜆\lambdaitalic\_λ, the robot will attempt to grab n⁢(λ)𝑛𝜆n(\lambda)italic\_n ( italic\_λ ) items, among which d⁢(λ)𝑑𝜆d(\lambda)italic\_d ( italic\_λ ) are failed grasps. The loss received by the robot will be ℒ⁢(λ):=d⁢(λ)/n⁢(λ)assignℒ𝜆𝑑𝜆𝑛𝜆\mathcal{L}(\lambda):=d(\lambda)/n(\lambda)caligraphic\_L ( italic\_λ ) := italic\_d ( italic\_λ ) / italic\_n ( italic\_λ ).

Metrics. We measure average utility (i.e., ##\## of successful grasps), V^T:=1T⁢∑t=1TV⁢(λt)assignsubscript^𝑉𝑇1𝑇superscriptsubscript𝑡1𝑇𝑉subscript𝜆𝑡\hat{V}\_{T}:=\frac{1}{T}\sum\_{t=1}^{T}V(\lambda\_{t})over^ start\_ARG italic\_V end\_ARG start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT := divide start\_ARG 1 end\_ARG start\_ARG italic\_T end\_ARG ∑ start\_POSTSUBSCRIPT italic\_t = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_T end\_POSTSUPERSCRIPT italic\_V ( italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ), and empirical risk, R^T⁢(λ1:T)subscript^𝑅𝑇subscript𝜆:1𝑇\hat{R}\_{T}(\lambda\_{1:T})over^ start\_ARG italic\_R end\_ARG start\_POSTSUBSCRIPT italic\_T end\_POSTSUBSCRIPT ( italic\_λ start\_POSTSUBSCRIPT 1 : italic\_T end\_POSTSUBSCRIPT ).

Experimental Setup. We assume that the number of items n⁢(λ)𝑛𝜆n(\lambda)italic\_n ( italic\_λ ) the robot attempts to grab is drawn as Pois⁢(C⋅λ)Pois⋅𝐶𝜆\text{Pois}(C\cdot\sqrt{\lambda})Pois ( italic\_C ⋅ square-root start\_ARG italic\_λ end\_ARG ). The number of failed grasps conditioned on the total number of items is d⁢(λ)|n∼Bin⁢(n,C′⋅λ)similar-toconditional𝑑𝜆𝑛Bin𝑛⋅superscript𝐶′𝜆d(\lambda)|n\sim\text{Bin}(n,C^{\prime}\cdot\lambda)italic\_d ( italic\_λ ) | italic\_n ∼ Bin ( italic\_n , italic\_C start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT ⋅ italic\_λ ).
Importantly, the distributions of n,d

𝑛𝑑n,ditalic\_n , italic\_d, and the parameters C,C′

𝐶superscript𝐶′C,C^{\prime}italic\_C , italic\_C start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT are all *unknown to the agent*.
Our conformal controller method (CC) adjusts the speed λtsubscript𝜆𝑡\lambda\_{t}italic\_λ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT based on the update rule from [Equation 6](#S3.E6 "6 ‣ Theorem 1 (Conformal Controller). ‣ III Theory & Conformal Controller Algorithm ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions").
In addition to the risk function, we also track a utility function which is the number of successful grasps V⁢(λ):=n⁢(λ)−d⁢(λ)assign𝑉𝜆𝑛𝜆𝑑𝜆V(\lambda):=n(\lambda)-d(\lambda)italic\_V ( italic\_λ ) := italic\_n ( italic\_λ ) - italic\_d ( italic\_λ ).

We compare our method with two baselines: A bandit algorithm running the upper confidence bound algorithm (UCB)
[[37](#bib.bib37)] to maximize the utility V𝑉Vitalic\_V and another algorithm running the lower confidence bound algorithm (LCB) to minimize the loss ℒℒ\mathcal{L}caligraphic\_L.
We also add two methods with oracle access to the otherwise unknown parameters: Oracle-Value selects the best speed to maximize grasp success λV\*:=arg⁡maxλ⁡𝔼⁢[V⁢(λ)]assignsubscriptsuperscript𝜆𝑉subscript𝜆𝔼delimited-[]𝑉𝜆\lambda^{\*}\_{V}:=\arg\max\_{\lambda}\mathbb{E}[V(\lambda)]italic\_λ start\_POSTSUPERSCRIPT \* end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_V end\_POSTSUBSCRIPT := roman\_arg roman\_max start\_POSTSUBSCRIPT italic\_λ end\_POSTSUBSCRIPT blackboard\_E [ italic\_V ( italic\_λ ) ] and Oracle-Loss selects the best speed λℒ\*subscriptsuperscript𝜆ℒ\lambda^{\*}\_{\mathcal{L}}italic\_λ start\_POSTSUPERSCRIPT \* end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT caligraphic\_L end\_POSTSUBSCRIPT such that 𝔼⁢[ℒ⁢(λℒ\*)]:=εassign𝔼delimited-[]ℒsubscriptsuperscript𝜆ℒ𝜀\mathbb{E}[\mathcal{L}(\lambda^{\*}\_{\mathcal{L}})]:=\varepsilonblackboard\_E [ caligraphic\_L ( italic\_λ start\_POSTSUPERSCRIPT \* end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT caligraphic\_L end\_POSTSUBSCRIPT ) ] := italic\_ε. The values selected for the parameters are in [Figure 2](#S4.F2 "Figure 2 ‣ IV-A Robot Navigation in Stanford Drone Dataset ‣ IV Experiments ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions").
We run all methods for a horizon T=2000𝑇2000T=2000italic\_T = 2000, set C=10𝐶10C=10italic\_C = 10, C′=0.2superscript𝐶′0.2C^{\prime}=0.2italic\_C start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT = 0.2, and the target risk is ε=0.05𝜀0.05\varepsilon=0.05italic\_ε = 0.05 (i.e., ≤5%absentpercent5\leq 5\%≤ 5 % failed grasp).

Results. We run the simulation N=1000𝑁1000N=1000italic\_N = 1000 times, and calculate the average empirical risk and the average number of successful grasps. In [Figure 2](#S4.F2 "Figure 2 ‣ IV-A Robot Navigation in Stanford Drone Dataset ‣ IV Experiments ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions"), we find that our method performs as well as the Oracle-Loss, ensuring that the empirical risk of grasps never exceeds ε=0.05𝜀0.05\varepsilon=0.05italic\_ε = 0.05, while still ensuring high throughput of successfully grasped items. UCB and LCB both violate the empirical risk threshold: UCB incurs this risk but achieves a higher number of successful grasps, while LCB is slow to learn its target, resulting in a higher risk over the time horizon.

### IV-C Stock Trading Agent

![Refer to caption](x4.png)

We consider an automated trading agent that trades a stock at high frequency. We model the agent as able to either buy or short-sell the stock, with no trading cost. When buying the stock at time t𝑡titalic\_t, the agent receives return rtsubscript𝑟𝑡r\_{t}italic\_r start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT. When short-selling the stock, the agent receives a return −rtsubscript𝑟𝑡-r\_{t}- italic\_r start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT. The agent must calibrate its trading decisions so the annualized loss is at or beneath the investor’s loss threshold of ε%percent𝜀\varepsilon\%italic\_ε %.

Decision Function & Parameterization.
At every timestep, t𝑡titalic\_t, the agent has access to the past history of returns and its own actions. The agent can use it to construct a confidence set C^λsubscript^𝐶𝜆\hat{C}\_{\lambda}over^ start\_ARG italic\_C end\_ARG start\_POSTSUBSCRIPT italic\_λ end\_POSTSUBSCRIPT where λ𝜆\lambdaitalic\_λ is the conformal control variable. Given a predicted set, the agent can decide to either buy if the entire set is above zero, short-sell if the entire set is below zero, and not do anything if zero is in the set:

|  |  |  |  |
| --- | --- | --- | --- |
|  | Dtλ:={1if⁢min⁡(C^λ)>0−1if⁢max⁡(C^λ)<00o.w.assignsubscriptsuperscript𝐷𝜆𝑡cases1ifsubscript^𝐶𝜆01ifsubscript^𝐶𝜆00formulae-sequenceowD^{\lambda}\_{t}:=\begin{cases}1&{\rm if}\min(\hat{C}\_{\lambda})>0\\ -1&{\rm if}\max(\hat{C}\_{\lambda})<0\\ 0&{\rm o.w.}\end{cases}italic\_D start\_POSTSUPERSCRIPT italic\_λ end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT := { start\_ROW start\_CELL 1 end\_CELL start\_CELL roman\_if roman\_min ( over^ start\_ARG italic\_C end\_ARG start\_POSTSUBSCRIPT italic\_λ end\_POSTSUBSCRIPT ) > 0 end\_CELL end\_ROW start\_ROW start\_CELL - 1 end\_CELL start\_CELL roman\_if roman\_max ( over^ start\_ARG italic\_C end\_ARG start\_POSTSUBSCRIPT italic\_λ end\_POSTSUBSCRIPT ) < 0 end\_CELL end\_ROW start\_ROW start\_CELL 0 end\_CELL start\_CELL roman\_o . roman\_w . end\_CELL end\_ROW |  | (15) |

Risk Function. The agent’s action is u∈{−1,0,1}𝑢101u\in\{-1,0,1\}italic\_u ∈ { - 1 , 0 , 1 } which incurs a loss ℒ⁢(u,r):=−u⋅r⋅1⁢{u⋅r<0}assignℒ𝑢𝑟⋅𝑢𝑟1⋅𝑢𝑟0\mathcal{L}(u,r):=-u\cdot r\cdot 1\{u\cdot r<0\}caligraphic\_L ( italic\_u , italic\_r ) := - italic\_u ⋅ italic\_r ⋅ 1 { italic\_u ⋅ italic\_r < 0 }, i.e., the agent suffers a loss equal to the amount of money lost by that decision. We clip the loss to make it bounded.

Experimental Setup. We simulate stock returns using a geometric Brownian motion. We assume that we observe returns every hour, so we have n=252⁢(days)×7⁢(hours per day)𝑛252days7hours per dayn=252(\mathrm{days})\times 7(\text{hours per day})italic\_n = 252 ( roman\_days ) × 7 ( hours per day ) steps per year:

|  |  |  |  |
| --- | --- | --- | --- |
|  | rt:=μ⁢Δ+σ⁢Δ⁢ZtwhereΔ=1/n.formulae-sequenceassignsubscript𝑟𝑡  𝜇Δ𝜎Δsubscript𝑍𝑡whereΔ1𝑛r\_{t}:=\mu\Delta+\sigma\sqrt{\Delta}Z\_{t}\quad\text{where}\quad\Delta=1/n.italic\_r start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT := italic\_μ roman\_Δ + italic\_σ square-root start\_ARG roman\_Δ end\_ARG italic\_Z start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT where roman\_Δ = 1 / italic\_n . |  | (16) |

We assume that at time t−1𝑡1t-1italic\_t - 1, the agent has access to a prediction r^tsubscript^𝑟𝑡\hat{r}\_{t}over^ start\_ARG italic\_r end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT and we assume that the correlation corr⁢(rt,r^t):=ρassigncorrsubscript𝑟𝑡subscript^𝑟𝑡𝜌\text{corr}(r\_{t},\hat{r}\_{t}):=\rhocorr ( italic\_r start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , over^ start\_ARG italic\_r end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) := italic\_ρ. The higher ρ𝜌\rhoitalic\_ρ the better the predicted returns r^tsubscript^𝑟𝑡\hat{r}\_{t}over^ start\_ARG italic\_r end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT. The predicted interval is

|  |  |  |
| --- | --- | --- |
|  | C^λ⁢(r^t):=[r^t−σ⁢Δ⁢zλ/2,r^t+σ⁢Δ⁢z1−λ/2],assignsubscript^𝐶𝜆subscript^𝑟𝑡subscript^𝑟𝑡𝜎Δsubscript𝑧𝜆2subscript^𝑟𝑡𝜎Δsubscript𝑧1𝜆2\hat{C}\_{\lambda}(\hat{r}\_{t}):=[\hat{r}\_{t}-\sigma\sqrt{\Delta}z\_{\lambda/2},% \hat{r}\_{t}+\sigma\sqrt{\Delta}z\_{1-\lambda/2}],over^ start\_ARG italic\_C end\_ARG start\_POSTSUBSCRIPT italic\_λ end\_POSTSUBSCRIPT ( over^ start\_ARG italic\_r end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) := [ over^ start\_ARG italic\_r end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT - italic\_σ square-root start\_ARG roman\_Δ end\_ARG italic\_z start\_POSTSUBSCRIPT italic\_λ / 2 end\_POSTSUBSCRIPT , over^ start\_ARG italic\_r end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT + italic\_σ square-root start\_ARG roman\_Δ end\_ARG italic\_z start\_POSTSUBSCRIPT 1 - italic\_λ / 2 end\_POSTSUBSCRIPT ] , |  |

where zλsubscript𝑧𝜆z\_{\lambda}italic\_z start\_POSTSUBSCRIPT italic\_λ end\_POSTSUBSCRIPT is the quantile of level λ𝜆\lambdaitalic\_λ of the normal distribution.

Metrics. In addition to the loss, we also measure return V⁢(u,r):=u⋅rassign𝑉𝑢𝑟⋅𝑢𝑟V(u,r):=u\cdot ritalic\_V ( italic\_u , italic\_r ) := italic\_u ⋅ italic\_r when the agent’s action is u𝑢uitalic\_u.

Results. We run N=100𝑁100N=100italic\_N = 100 simulations over five years. We set μ=0.08,σ=0.2formulae-sequence𝜇0.08𝜎0.2\mu=0.08,\sigma=0.2italic\_μ = 0.08 , italic\_σ = 0.2,
which are approximately the historical values for the S&P 500.
We compare our CC method with: the Buy-and-Hold strategy that simply buys the stock at each timestep, the Greedy strategy that buys the stock whenever the prediction is above zero and short-sells it when the prediction is below zero (equivalent to D⁢(λ=1)𝐷𝜆1D(\lambda=1)italic\_D ( italic\_λ = 1 )), and ACI that adjusts λ𝜆\lambdaitalic\_λ online using the ACI algorithm.
We set the target coverage for ACI at 90%percent9090\%90 % and our annualized loss threshold to be less than ε=25%𝜀percent25\varepsilon=25\%italic\_ε = 25 % (the threshold per time-step is therefore ε/n𝜀𝑛\varepsilon/nitalic\_ε / italic\_n). For the prediction of returns, we simulate another geometric Brownian motion,

|  |  |  |  |
| --- | --- | --- | --- |
|  | r^t:=μ⁢Δ+σ⁢Δ⁢Wtwherewhere corr⁢(Wt,Zt)=ρ.formulae-sequenceassignsubscript^𝑟𝑡  𝜇Δ𝜎Δsubscript𝑊𝑡wherewhere corrsubscript𝑊𝑡subscript𝑍𝑡𝜌\hat{r}\_{t}:=\mu\Delta+\sigma\sqrt{\Delta}W\_{t}\quad\text{where}\quad\text{% where corr}(W\_{t},Z\_{t})=\rho.over^ start\_ARG italic\_r end\_ARG start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT := italic\_μ roman\_Δ + italic\_σ square-root start\_ARG roman\_Δ end\_ARG italic\_W start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT where where corr ( italic\_W start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT , italic\_Z start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT ) = italic\_ρ . |  | (17) |

The results for the different methods are in Figure [4](#S4.F4 "Figure 4 ‣ IV-C Stock Trading Agent ‣ IV Experiments ‣ Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions").
We plot the cumulative return and cumulative loss for all methods and for two models: ρ=0.1𝜌0.1\rho=0.1italic\_ρ = 0.1 (good model) and ρ=−0.05𝜌0.05\rho=-0.05italic\_ρ = - 0.05 (bad model).
In both cases, our CC quickly adapts the parameter to stay below the loss threshold, while having good returns when the predictive model is good (ρ=0.1𝜌0.1\rho=0.1italic\_ρ = 0.1).
The Greedy approach has more extreme returns (negative when the model is bad, positive when the model is good) with a high level of loss.
ACI is highly conservative, resulting in smaller loss, significantly below the threshold.
By being so conservative, the algorithm limits its potential gain when the predictive model is actually good. Buy-and-hold also has high cumulative loss as it moves with the stock, and has a more consistent return, as it is independent of the model quality.

## V Discussion & Conclusion

In this paper, we introduce Conformal Decision Theory, a theoretical and algorithmic framework for producing safe decisions despite being based on imperfect machine-learning predictions.
We have described our method in both the online, adversarial setting, and also the batch, exchangeable setting.
The main difference between the two is that the online algorithms we present are computationally trivial, while the batch setting can require evaluating a large amount of *counterfactual* decisions (indexed by different choices of λ𝜆\lambdaitalic\_λ) on every calibration point.
Though this can be done with binary search, it still presents operational challenges.
One path for future work may be to test the method in settings where simulators or data sets can support this form of offline policy evaluation.
Another may be to develop formally valid approximations of the batch technique which preserve risk control while being more practical.
Furthermore, extensions of the batch technique to non-exchangeable settings are readily available, e.g., by use of the techniques in [[38](#bib.bib38)], and could be evaluated.
Finally, future work may additionally consider optimizing the conformal control variable to maximize utility, perhaps also subject to the constraint of risk control, bringing the work closer to the classical statistical decision theory of Lehmann [[39](#bib.bib39)], von Neuman and Morgenstern [[40](#bib.bib40)], and others.

## References

![[LOGO]](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)

HTML conversions sometimes display errors due to content that did not convert correctly from the source. This paper uses the following packages that are not yet supported by the HTML conversion tool. Feedback on these issues are not necessary; they are known and are being worked on.

Authors: achieve the best HTML results from your LaTeX submissions by selecting from this list of [supported packages](https://corpora.mathweb.org/corpus/arxmliv/tex_to_html/info/loaded_file).
