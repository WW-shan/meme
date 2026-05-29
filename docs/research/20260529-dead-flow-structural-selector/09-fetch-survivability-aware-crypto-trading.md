##### Report GitHub Issue

Content selection saved. Describe the issue below:

![arXiv logo](/static/browse/0.3.4/images/arxiv-logo-one-color-white.svg)

# Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors

![[Uncaptioned image]](2603.10092v1/figures/true_trading_logo.jpeg)

###### Abstract

OpenClaw-style agent stacks turn language into *privileged execution* by routing LLM intents through tool interception, policy gateways, and a local executor.
In parallel, skill marketplaces such as skills.sh operationalize capability acquisition via installable skills and CLIs, creating a fast-growing *capability supply chain*.
Together, these trends shift the dominant safety failure mode from “wrong answers” to *execution-induced loss*: untrusted prompts, compromised skills, or narrative manipulation can translate into real trades and irreversible side effects.

We propose Survivability-Aware Execution (SAE), an execution-layer survivability standard designed for OpenClaw-style systems and skill-enabled agents.
SAE is deployed as middleware between any strategy engine (LLM or non-LLM) and the exchange executor.
It implements an explicit execution contract (ExecutionRequest, ExecutionContext, ExecutionDecision) and enforces non-bypassable invariants at the last mile: projection-based exposure budgeting, cooldown and order-rate limits, slippage bounds, staged execution, and tool/venue allowlists.
To make delegated execution empirically testable under skill supply-chain risk, we operationalize the Delegation Gap (DG) using a logged Intended Policy Spec that yields deterministic out-of-scope labeling and reproducible DG metrics.

On a reproducible offline replay built from official Binance USD-M BTCUSDT/ETHUSDT perpetual data (15m; 2025-09-01–2025-12-01, including funding),
SAE substantially improves survivability and robustness.
Relative to NoSAE, SAE reduces maximum drawdown from 0.46430.4643 to 0.03190.0319 (Full; 93.1%93.1\%), shrinks tail-loss magnitude |CVaR0.99||\mathrm{CVaR}\_{0.99}| from 4.025×10−34.025\times 10^{-3} to ≈1.02×10−4\approx 1.02\times 10^{-4} (∼97.5%\sim 97.5\%),
and lowers DG loss proxy from 0.6470.647 to 0.0190.019 (∼97.0%\sim 97.0\%), while reducing AttackSuccess from 1.001.00 to 0.7280.728 with zero FalseBlock in this run.
Dependence-aware tests (block bootstrap, paired Wilcoxon, two-proportion test) confirm the shifts are statistically detectable.
Overall, SAE reframes agentic trading safety for the OpenClaw+skills era: treat upstream intent and skills as untrusted, and enforce survivability where actions become side effects.

## 1 Introduction and Real-world Motivation for SAE

Tool-using agents have become a mainstream engineering pattern. Yao et al. [[26](#bib.bib1 "ReAct: synergizing reasoning and acting in language models")] demonstrates interleaving reasoning with actions that consult external sources, and Schick et al. [[23](#bib.bib2 "Toolformer: language models can teach themselves to use tools")] shows that models can be trained (self-supervised) to decide *when* and *how* to call tools. As these ideas move into production, the safety boundary shifts: language is no longer only an output medium, but a *control surface* for real-world side effects. The key question is therefore not only whether an agent produces correct text, but whether its *execution interface* converts untrusted intent into harmful actions.

##### Why execution becomes the primary attack surface.

This execution boundary is made explicit by *OpenClaw-style* agent stacks. OpenClaw separates (i) where tools run (sandbox vs. host), (ii) which tools are available (tool policy), and (iii) an explicit escape hatch for host execution under elevated settings [[15](#bib.bib11 "Sandbox vs tool policy vs elevated")]. Its security guidance recommends strict allowlists for high-risk tools, sandboxing whenever untrusted inputs are in the loop, and keeping secrets out of prompts and the agent-accessible filesystem [[16](#bib.bib12 "Security: risks, best practices, and a checklist")]. These design choices capture a security principle that motivates our paper: when tool access is permissive, untrusted text can become privileged actions. In finance, the consequences are immediate because side effects are monetized.

##### Why the skills ecosystem amplifies the problem.

A second trend makes the problem harder: *installable skill ecosystems* that operationalize capability acquisition. The *Agent Skills* standard packages reusable capability context as directories anchored by SKILL.md with YAML frontmatter and progressive-disclosure design [[25](#bib.bib5 "Agent skills for large language models: architecture, acquisition, security, and the path forward")]. Vercel’s open skills ecosystem provides a CLI workflow (e.g., npx skills add …) and a discovery surface via skills.sh [[18](#bib.bib18 "Introducing skills, the open agent skills ecosystem"), [24](#bib.bib19 "skills: the cli for the open agent skills ecosystem")]. In parallel, OpenClaw positions *ClawHub* as a public registry for discovering, installing, updating, and syncing skills [[14](#bib.bib13 "ClawHub"), [17](#bib.bib17 "Skills")]. Together, OpenClaw-style privileged execution and skills.sh-style marketplaces imply a near-term reality: capabilities will be frequently acquired from third parties, and the *capability supply chain* becomes part of the attack surface. This portability is valuable for productivity, but it increases risk because installing a third-party skill is operationally close to importing code and instructions that can influence tool calls and execution parameters. In early 2026, security reports documented malware distributed via marketplace-hosted OpenClaw skills, including crypto-themed skills designed to harvest credentials and other sensitive data [[22](#bib.bib20 "OpenClaw’s ai “skill” extensions are a security nightmare"), [10](#bib.bib21 "Malicious openclaw “skill” targets crypto users on clawhub")]. These incidents support a conservative stance: treat skill installation as a high-risk event and assume adversarial incentives exist wherever execution privileges intersect with asset custody.

##### Why “assume compromise” is a reasonable baseline.

Agent networks can further amplify risk through connectivity. Reuters reported that Moltbook—a Reddit-like social site marketed for AI agents—suffered a major exposure due to a basic security flaw, leaking private agent messages, thousands of owner emails, and a large volume of credentials [[19](#bib.bib22 "“Moltbook” social media site for ai agents had big security hole, cyber firm wiz says")]. Even when downstream impact differs across deployments, the lesson is structural: fast-growing agent ecosystems can externalize sensitive data at scale through simple misconfigurations. When agents are both highly connected and highly privileged, “assume compromise” becomes a reasonable baseline. This stance aligns with broader directions in AI-governed, web-trustworthy architectures that treat governance and trust signals as first-class system inputs [[7](#bib.bib15 "AI-governed agent architecture for web-trustworthy tokenization of alternative assets")].

##### Why crypto perpetuals amplify execution mistakes.

Crypto perpetual trading is a particularly sharp setting for execution-layer safety. Binance documentation notes that funding fees are deducted from a trader’s futures wallet balance and, if insufficient, from position margin—potentially shifting liquidation price and increasing liquidation risk [[2](#bib.bib23 "Introduction to binance futures funding rates")]. Binance also documents that maintenance margin requirements depend on notional tiers and directly affect liquidation thresholds [[1](#bib.bib24 "Binance futures liquidation protocols"), [3](#bib.bib25 "Leverage and margin of usd$-m futures")]. As a result, execution choices that may look minor in an intent string—such as leverage, order rate, slippage tolerance, and timing under stress—can be structurally amplified into nonlinear tail outcomes. Relatedly, constrained formulations of trade execution and independent audit layers have been proposed as system designs to enforce hard participation and compliance constraints, complementing execution-layer enforcement such as SAE [[6](#bib.bib14 "Safe and compliant cross-market trade execution via constrained rl and zero-knowledge audits")].

##### Survivability-Aware Execution (SAE).

These conditions motivate Survivability-Aware Execution (SAE): a standardized execution-layer safety contract designed to plug into OpenClaw-style tool interception and remain robust under skills.sh-style capability supply chains. SAE is designed to be strategy-agnostic and composable within broader agentic trading architectures [[5](#bib.bib16 "AI agent architecture for decentralized trading of alternative assets")]. SAE treats upstream outputs as *untrusted intent* and enforces survivability constraints as *code-level policies* (budgets, cooldowns, tool gating, and kill-switches) before privileged actions can occur.

##### Contributions.

Concretely, our main contributions are: (i) an operational DG measurement protocol grounded in Intended Policy Specs and hard out-of-scope rules; (ii) a survivability-first execution contract compatible with OpenClaw-style tool interception and skills.sh-style capability ecosystems; (iii) practical enforcement algorithms with an exposure-based theoretical bound linking projection to worst-case loss amplification; and (iv) a fully reproducible Binance replay evaluation reporting survivability, robustness, and overhead metrics across SAE variants.

##### Paper roadmap.

We proceed as follows. Section 2.1 formalizes the agentic execution setting and defines the Delegation Gap (DG) using a logged Intended Policy Spec, enabling deterministic out-of-scope labeling and reproducible DG metrics. Section [3](#S3 "3 SAE Design and Algorithms ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors") specifies SAE as an OpenClaw-style execution contract with non-bypassable enforcement (projection-based budgeting, temporal guards, and trust-conditioned tightening under skill supply-chain risk). Sections [6](#S6 "6 Evaluation on Binance Replay ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")–[6.3](#S6.SS3 "6.3 Results ‣ 6 Evaluation on Binance Replay ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors") evaluate SAE on a reproducible Binance USD-M replay with attack instrumentation and dependence-aware statistical tests, and Sections [7](#S7 "7 Discussion ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")–[8](#S8 "8 Limitations and Future Work ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors") discuss trade-offs and limitations.

## 2 Problem Formulation

### 2.1 Formal Delegation Gap

Let 𝒜intended\mathcal{A}\_{\text{intended}} be the set of actions the operator intends to authorize in the current context,
and let 𝒜actual\mathcal{A}\_{\text{actual}} be the set of actions the deployed system can execute given its tools,
permissions, credentials, and integrations (including indirect effects from skills/plugins and elevated local execution).
In agentic execution it is typical that 𝒜intended⊊𝒜actual\mathcal{A}\_{\text{intended}}\subsetneq\mathcal{A}\_{\text{actual}},
and the effective support of executed actions can expand under prompt injection, compromised inputs, or supply-chain events.

##### Delegation Gap (DG).

We define the Delegation Gap as the expected loss introduced by actions that are executable but outside intended scope:

|  |  |  |  |
| --- | --- | --- | --- |
|  | DG≜𝔼​[ℓ​(at)⋅𝟏​{at∉𝒜intended​(St)}],at∼Pπ​(⋅)​over​𝒜actual,\mathrm{DG}\;\triangleq\;\mathbb{E}\big[\,\ell(a\_{t})\cdot\mathbf{1}\{a\_{t}\notin\mathcal{A}\_{\text{intended}}(S\_{t})\}\,\big],\quad a\_{t}\sim P\_{\pi}(\cdot)\ \text{over}\ \mathcal{A}\_{\text{actual}}, |  | (1) |

where ℓ​(⋅)\ell(\cdot) is a fixed loss functional (e.g., realized PnL loss, liquidation indicator/proxy, or security loss proxy),
and StS\_{t} is an explicit *Intended Policy Spec* (defined next).
DG is measurable in a reproducible way because it reduces to (i) a hard out-of-scope test, plus (ii) a fixed loss proxy.

#### 2.1.1 Operationalizing 𝒜intended\mathcal{A}\_{\text{intended}} via an Intended Policy Spec

To avoid treating “user natural language” as the ground truth of intent, we define intent as a structured specification:

|  |  |  |  |
| --- | --- | --- | --- |
|  | St=(Tt,Rt,Mt,Ut),S\_{t}\;=\;(T\_{t},R\_{t},M\_{t},U\_{t}), |  | (2) |

with the following components.

##### (i) Allowed action/tool set TtT\_{t}.

A finite set of permitted action types and tools, e.g.,
{open,close,modify,cancel}\{\texttt{open},\texttt{close},\\
\texttt{modify},\texttt{cancel}\} plus permitted venues/symbols/accounts.

##### (ii) Risk budgets RtR\_{t}.

Hard caps on execution-relevant exposures, e.g., maximum leverage, maximum notional, maximum order rate,
maximum slippage bound, maximum holding time, maximum concurrent positions.

##### (iii) Market-state constraints MtM\_{t}.

State-triggered tightening rules based on market regime indicators (e.g., volatility/liquidity/funding extremes),
so that high-risk regimes reduce feasible budgets.

##### (iv) User/account constraints UtU\_{t}.

Account-state constraints such as margin ratio, drawdown/PnL state, cooldown timers, and exposure concentration.

##### Induced intended action set.

We then define:

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒜intended​(St)={a:a​ satisfies ​Tt,Rt,Mt,Ut}.\mathcal{A}\_{\text{intended}}(S\_{t})\;=\;\{\,a\;:\;a\text{ satisfies }T\_{t},R\_{t},M\_{t},U\_{t}\,\}. |  | (3) |

#### 2.1.2 Out-of-scope rules (hard, reproducible)

An executed/attempted action ata\_{t} is labeled *out-of-scope* if it violates any of the following rule classes:

Cap violation (risk-budget breach):
exceeds leverage/notional/order-rate/slippage/holding-time caps specified by RtR\_{t} (possibly tightened by MtM\_{t} and UtU\_{t}).

Tool/venue violation (capability breach):
invokes an unauthorized tool, market, venue, symbol universe, or cross-account capability not allowed by TtT\_{t}.

State violation (context breach):
executes actions that are disallowed under current market/account states (e.g., “extreme volatility” or “low margin ratio”
states where only reduce-only actions are permitted).

#### 2.1.3 DG estimators and reporting

Given logs of attempted/executed actions {at}t=1N\{a\_{t}\}\_{t=1}^{N}, we report:

##### Out-of-scope rate.

|  |  |  |  |
| --- | --- | --- | --- |
|  | DG^rate=1N​∑t=1N𝟏​{at∉𝒜intended​(St)}.\widehat{\mathrm{DG}}\_{\text{rate}}\;=\;\frac{1}{N}\sum\_{t=1}^{N}\mathbf{1}\{a\_{t}\notin\mathcal{A}\_{\text{intended}}(S\_{t})\}. |  | (4) |

##### Out-of-scope loss contribution (proxy).

For a fixed, pre-declared loss proxy ℓ​(⋅)\ell(\cdot):

|  |  |  |  |
| --- | --- | --- | --- |
|  | DG^loss=∑t=1Nℓ​(at)⋅𝟏​{at∉𝒜intended​(St)}∑t=1N|ℓ​(at)|+ϵ,\widehat{\mathrm{DG}}\_{\text{loss}}\;=\;\frac{\sum\_{t=1}^{N}\ell(a\_{t})\cdot\mathbf{1}\{a\_{t}\notin\mathcal{A}\_{\text{intended}}(S\_{t})\}}{\sum\_{t=1}^{N}\big|\ell(a\_{t})\big|+\epsilon}, |  | (5) |

where ϵ\epsilon is a small constant to avoid division by zero.

##### Paper-facing DG table.

In experiments we report (i) DG^rate\widehat{\mathrm{DG}}\_{\text{rate}}, (ii) DG^loss\widehat{\mathrm{DG}}\_{\text{loss}},
and (iii) the reduction under SAE vs. No-SAE. See Table 3.

### 2.2 Survivability-first objective as constrained optimization

Let π\pi denote the composite policy: strategy →\rightarrow SAE gating →\rightarrow execution runtime.
Let RπR\_{\pi} be the return random variable over a horizon (including funding cash flows).
SAE targets tail-risk reduction under minimal performance constraints:

|  |  |  |  |
| --- | --- | --- | --- |
|  | minπ∈Π⁡CVaRα​(Rπ)s.t.𝔼​[Rπ]≥μ0,Pr⁡(Liquidationπ)≤ϵ.\min\_{\pi\in\Pi}\ \mathrm{CVaR}\_{\alpha}(R\_{\pi})\quad\text{s.t.}\quad\mathbb{E}[R\_{\pi}]\geq\mu\_{0},\quad\Pr(\mathrm{Liquidation}\_{\pi})\leq\epsilon. |  | (6) |

CVaR (expected shortfall) is a standard tail-risk objective [[20](#bib.bib30 "Optimization of conditional value-at-risk"), [21](#bib.bib31 "Conditional value-at-risk for general loss distributions")].
The key point is conceptual: SAE is not “an alpha clamp”; it is a constraint layer that alters the feasible policy set by restricting execution.

##### From conceptual objective to reproducible selection.

In practice, π\pi is instantiated by a parameterized strategy and a parameterized SAE gate.
We write π=πϕ,θ\pi=\pi\_{\phi,\theta} where ϕ∈Φ\phi\in\Phi are strategy parameters (e.g., lookbacks, thresholds)
and θ∈Θ\theta\in\Theta are SAE gate parameters (e.g., budgets, cooldown, trust-conditioned tightening, staged enforcement).
Given a replay dataset 𝒟\mathcal{D} (synthetic or exchange historical data), we evaluate πϕ,θ\pi\_{\phi,\theta} via a deterministic simulator
ℰ​(ϕ,θ;𝒟)\mathcal{E}(\phi,\theta;\mathcal{D}) that returns a metrics vector including drawdown, tail losses, security, and usability outcomes.

##### Operational constraints for agentic execution.

To make the feasibility set explicit for tool-using agents, we augment the survivability constraints in ([6](#S2.E6 "In 2.2 Survivability-first objective as constrained optimization ‣ 2 Problem Formulation ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors"))
with security & usability constraints that are unique to delegated execution:
(i) *attack success* AS​(π)\mathrm{AS}(\pi), the fraction of injected out-of-scope attack attempts that are not blocked;
(ii) *false block* FB​(π)\mathrm{FB}(\pi), the fraction of legitimate in-scope requests that are blocked; and
(iii) optional executor overhead Lat​(π)\mathrm{Lat}(\pi).
These yield the constrained policy family

|  |  |  |  |
| --- | --- | --- | --- |
|  | ΠSAE​(α,β,τ)={π∈Π:AS​(π)≤α,FB​(π)≤β,Lat​(π)≤τ},\Pi\_{\mathrm{SAE}}(\alpha,\beta,\tau)=\left\{\pi\in\Pi:\mathrm{AS}(\pi)\leq\alpha,\ \mathrm{FB}(\pi)\leq\beta,\ \mathrm{Lat}(\pi)\leq\tau\right\}, |  | (7) |

where α\alpha controls acceptable adversarial leakage, β\beta bounds usability degradation, and τ\tau (optional) caps last-mile latency.

##### Best-so-far constrained search (optimization protocol).

Equation ([6](#S2.E6 "In 2.2 Survivability-first objective as constrained optimization ‣ 2 Problem Formulation ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")) is simulator-defined, non-convex, and typically non-differentiable in (ϕ,θ)(\phi,\theta).
We therefore instantiate a black-box *constrained* search to obtain a reproducible *best-so-far* solution.
Concretely, we repeatedly sample candidate configurations (ϕ,θ)(\phi,\theta), replay them on a validation segment, and keep an incumbent
(ϕ(b​e​s​t),θ(b​e​s​t))(\phi^{(best)},\theta^{(best)}).
A candidate is *feasible* if it satisfies the constraints in ([7](#S2.E7 "In Operational constraints for agentic execution. ‣ 2.2 Survivability-first objective as constrained optimization ‣ 2 Problem Formulation ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")) (and survivability constraints such as Pr⁡(Liquidationπ)≤ϵ\Pr(\mathrm{Liquidation}\_{\pi})\leq\epsilon).
Among feasible candidates, we update the incumbent if it improves a fixed selection score that proxies the tail-risk objective while penalizing execution risks:

|  |  |  |  |
| --- | --- | --- | --- |
|  | (ϕ(b​e​s​t),θ(b​e​s​t))←(ϕ,θ)iffπϕ,θ∈ΠSAE​(α,β,τ)∧J​(ϕ,θ)<J​(ϕ(b​e​s​t),θ(b​e​s​t)),(\phi^{(best)},\theta^{(best)})\leftarrow(\phi,\theta)\quad\text{iff}\quad\pi\_{\phi,\theta}\in\Pi\_{\mathrm{SAE}}(\alpha,\beta,\tau)\ \wedge\ J(\phi,\theta)<J(\phi^{(best)},\theta^{(best)}), |  | (8) |

with

|  |  |  |  |
| --- | --- | --- | --- |
|  | J​(ϕ,θ)=w1​MDD​(πϕ,θ)+w2​|CVaR0.99​(Rπϕ,θ)|+w3​DG​\_​loss​(πϕ,θ)+w4​Lat​(πϕ,θ),J(\phi,\theta)=w\_{1}\,\mathrm{MDD}(\pi\_{\phi,\theta})\;+\;w\_{2}\,\big|\mathrm{CVaR}\_{0.99}(R\_{\pi\_{\phi,\theta}})\big|\;+\;w\_{3}\,\mathrm{DG\\_loss}(\pi\_{\phi,\theta})\;+\;w\_{4}\,\mathrm{Lat}(\pi\_{\phi,\theta}), |  | (9) |

where MDD\mathrm{MDD} and CVaR0.99\mathrm{CVaR}\_{0.99} are computed on replay returns (including funding),
DG​\_​loss\mathrm{DG\\_loss} is a fixed delegation-gap cost proxy under an intended policy specification,
and wiw\_{i} are user-chosen weights.
We run the search in batches and terminate by a compute budget or an early-stopping criterion (e.g., stop after KK consecutive batches with no incumbent improvement),
which yields a reproducible best-so-far configuration and a complete search trace.

##### Selection vs. reporting.

To avoid post-hoc “cherry-picking,” the constrained search is performed on a validation segment (or inner fold),
then the chosen (ϕ⋆,θ⋆)(\phi^{\star},\theta^{\star}) is frozen and evaluated once on a disjoint test segment (or outer fold),
with uncertainty estimated via multiple seeds where applicable.
This protocol is implemented in our released code and summarized in the walk-forward tuning procedure (Sec.5.4).

### 2.3 SAE execution API spec as middleware contract

SAE’s engineering contribution is an explicit *execution contract* that can be adopted by
frameworks like OpenClaw (via tool interception) or by any trading bot. The contract standardizes
the last-mile boundary between *strategy intent* and *exchange submission*:

ExecutionRequest: symbol, venue, timestamp\_ms, intent, side,
requested\_notional, requested\_leverage, order\_type, max\_slippage\_bps, strategy\_id.

ExecutionContext: *account state* (equity, drawdown, positions, recent trades, margin ratio),
*market state* (realized volatility, funding, liquidity proxy, regime label),
and a first-class *trust state* ztz\_{t} (defined below), with an optional narrative proxy.

ExecutionDecision: decision ∈{ALLOW,LIMIT,BLOCK}\in\{\texttt{ALLOW},\texttt{LIMIT},\texttt{BLOCK}\} plus enforced constraints:
leverage cap, notional cap, order-rate cap, slippage cap, cooldown, staging plan, and structured audit fields.

#### 2.3.1 SAE subsumes OMS risk limits and adds three agentic layers

A natural question is how SAE relates to conventional OMS risk checks such as leverage caps,
position-size limits, stop-losses, rate limits, and kill-switches.
Our position is not that SAE replaces OMS, but that SAE *includes a standard OMS baseline*
and then adds three layers that become necessary in agentic, skills-enabled execution.

##### Layer 0: Static OMS baseline.

At minimum, SAE can be configured to behave like a conventional OMS:
fixed leverage and position-size limits, stop-loss / reduce-only triggers, and rate limits.
This corresponds to a static control layer that assumes upstream strategy intent is trusted
and focuses on market and margin safety.

##### Layer 1: Trust-state conditioned budgeting.

Agentic stacks acquire capabilities via installable skills and toolchains, so upstream intent is structurally untrusted.
SAE therefore conditions budgets on a first-class trust state ztz\_{t} (provenance, capability risk, injection alerts),
tightening exposure when trust degrades.

##### Layer 2: Supply-chain and scope enforcement.

In skills-enabled systems, “what the agent is allowed to do” must be explicit and auditable.
SAE operationalizes intended scope via an Intended Policy Spec and hard out-of-scope rules,
enabling non-bypassable allowlists over tools, venues, symbols, and accounts.

##### Layer 3: Attack-aware evaluation.

SAE treats prompt, skill supply-chain, and narrative attacks as first-class inputs and reports system metrics such as
AttackSuccess, FalseBlock, latency, DG rate, and DG loss, rather than only trading PnL metrics.
This makes robustness claims reproducible and comparable across implementations.

##### Why NoSAE is a realistic baseline.

While human discretionary traders often rely on stop-losses and broker-side controls,
many deployed agentic bots connect directly from strategy logic to the executor with no intermediate gating layer.
In such systems, the strategy output is effectively the action.
We therefore use NoSAE to represent a common default deployment pattern:
direct strategy-to-executor wiring without a policy-intercepting middleware.
This baseline is included not to advocate unsafe practice, but to quantify how much survivability is gained
once an explicit last-mile execution contract is introduced.

### 2.4 Projection-based enforcement

We generalize “clamping” as a projection of a requested action areqa\_{\text{req}} into a feasible budget region ℱ​(B)\mathcal{F}(B):

|  |  |  |  |
| --- | --- | --- | --- |
|  | aSAE=arg⁡mina∈ℱ​(B)⁡D​(a,areq),a\_{\text{SAE}}\;=\;\arg\min\_{a\in\mathcal{F}(B)}D(a,a\_{\text{req}}), |  | (10) |

where D​(⋅,⋅)D(\cdot,\cdot) is an execution-distance functional (e.g., weighted ℓ2\ell\_{2} over leverage, notional, and order rate).
When DD is convex and ℱ​(B)\mathcal{F}(B) is convex, ([10](#S2.E10 "In 2.4 Projection-based enforcement ‣ 2 Problem Formulation ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")) is a convex projection.

A core engineering special case is leverage projection:

|  |  |  |  |
| --- | --- | --- | --- |
|  | Leff=min⁡(Lreq,Lcap),L\_{\text{eff}}\;=\;\min(L\_{\text{req}},L\_{\text{cap}}), |  | (11) |

which is the projection of requested leverage onto [0,Lcap][0,L\_{\text{cap}}].

##### Proposition (budgeted exposure yields a worst-case one-step loss bound).

Let et∈ℝde\_{t}\in\mathbb{R}^{d} denote the *exposure vector* induced by an execution action at time tt
(e.g., components may encode notional exposure, effective leverage, order-rate, and slippage budget).
Let the SAE enforcement runtime guarantee a budget constraint

|  |  |  |  |
| --- | --- | --- | --- |
|  | ‖et‖≤Bt,et∈ℱ​(Bt),\|e\_{t}\|\leq B\_{t},\qquad e\_{t}\in\mathcal{F}(B\_{t}), |  | (12) |

where ℱ​(Bt)\mathcal{F}(B\_{t}) is the feasible region specified by SAE budgets (including component-wise caps)
and ∥⋅∥\|\cdot\| is any chosen norm consistent with the budget semantics.

Assume the per-step loss functional ℓt​(e)\ell\_{t}(e) is LL-Lipschitz with respect to ∥⋅∥\|\cdot\|, i.e.,

|  |  |  |  |
| --- | --- | --- | --- |
|  | |ℓt​(e)−ℓt​(e′)|≤L​‖e−e′‖,∀e,e′.|\ell\_{t}(e)-\ell\_{t}(e^{\prime})|\leq L\|e-e^{\prime}\|,\quad\forall e,e^{\prime}. |  | (13) |

Then the worst-case additional one-step loss relative to a risk-off (zero-exposure) action is bounded by

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℓt​(et)−ℓt​(0)≤L​‖et‖≤L​Bt.\ell\_{t}(e\_{t})-\ell\_{t}(0)\leq L\|e\_{t}\|\leq LB\_{t}. |  | (14) |

Moreover, if SAE enforces execution via projection eteff=Πℱ​(Bt)​(etreq)e\_{t}^{\mathrm{eff}}=\Pi\_{\mathcal{F}(B\_{t})}(e\_{t}^{\mathrm{req}}),
then the loss deviation from an unbudgeted request is bounded as

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℓt​(eteff)−ℓt​(etreq)≤L​‖eteff−etreq‖≤L⋅dist​(etreq,ℱ​(Bt)).\ell\_{t}(e\_{t}^{\mathrm{eff}})-\ell\_{t}(e\_{t}^{\mathrm{req}})\leq L\|e\_{t}^{\mathrm{eff}}-e\_{t}^{\mathrm{req}}\|\leq L\cdot\mathrm{dist}(e\_{t}^{\mathrm{req}},\mathcal{F}(B\_{t})). |  | (15) |

This statement is intentionally weak but robust: it does not assume any particular return dynamics,
and it directly links *projection-based enforcement* to a deterministic reduction in worst-case
instantaneous loss amplification. Liquidation and exchange-specific margin mechanics are handled in the
empirical replay evaluation rather than in this bound.

## 3 SAE Design and Algorithms

SAE (Survivability-Aware Execution) is an *execution-layer* safety and survivability middleware placed between a strategy engine
(LLM or non-LLM) and an exchange executor. Unlike conventional OMS limits that assume upstream strategy intent is trusted,
SAE treats upstream outputs as *untrusted intent* in agentic settings (prompt/skill/narrative contamination),
and enforces non-bypassable invariants at the last mile where side effects occur.
This section specifies SAE as (i) a deployable system design, and (ii) a set of practical algorithms that map replay-computable state
to enforceable budgets and decisions, compatible with the Binance replay protocol in Section [6](#S6 "6 Evaluation on Binance Replay ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors").

### 3.1 System design and execution contract

##### Middleware placement.

SAE sits in the last-mile boundary:

|  |  |  |
| --- | --- | --- |
|  | Strategy Engine→ExecutionRequest→SAE Middleware→Exchange Executor.\text{Strategy Engine}\rightarrow\text{ExecutionRequest}\rightarrow\text{SAE Middleware}\rightarrow\text{Exchange Executor}. |  |

This placement ensures constraints are *non-bypassable*: even if upstream intent is manipulated, the executor only receives SAE-approved actions.

##### Execution contract (API).

SAE standardizes an explicit execution contract:

ExecutionRequest rtr\_{t}:
symbol, venue, timestamp\_ms, intent, side,
requested\_notional, requested\_leverage, order\_type,
max\_slippage\_bps, strategy\_id.

ExecutionContext ctc\_{t}:
account state (equity, drawdown, positions, recent trades, margin ratio),
market state (volatility, funding, liquidity proxy, regime),
plus a first-class trust state ztz\_{t} (Section [3.4](#S3.SS4 "3.4 Trust state and trust-conditioned budgeting ‣ 3 SAE Design and Algorithms ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")),
and optional narrative/anomaly signals.

ExecutionDecision dtd\_{t}:
decision∈{ALLOW,LIMIT,BLOCK}\texttt{decision}\in\{\texttt{ALLOW},\texttt{LIMIT},\texttt{BLOCK}\}
plus enforced constraints (leverage cap, notional cap, order-rate cap, slippage cap, cooldown, staging plan),
and audit fields (rule hit, budgets, state snapshot, timing).

##### Concrete example (request →\rightarrow SAE decision).

This example shows the practical meaning of SAE. The strategy requests an aggressive trade
(5×\times leverage, 50% notional allocation, and a wide slippage bound), but SAE does not simply accept or reject it.
Instead, it returns a LIMIT decision and converts the request into a safer executable action:
leverage is reduced to 1×\times, notional is reduced to 20% of the default budget, slippage tolerance is tightened,
and a cooldown is imposed. In this way, SAE preserves the intent to trade while enforcing survivability constraints at the execution boundary.

##### Modular components.

Each SAE module is independently deployable and testable:

Trader-State Service: outputs calibrated risk escalation probability pt∈[0,1]p\_{t}\in[0,1].

Market Regime Detector: classifies {calm,volatile,extreme}\{\textsf{calm},\textsf{volatile},\textsf{extreme}\}
using volatility, funding extremes, and liquidity proxies.

Policy Engine: YAML-defined mapping from (regime, risk, trust) to decision and budgets.

Enforcement Runtime: last-mile projection/clamping, cooldown, rate limits, staged execution, and audit logging.

Volatility regime detection is motivated by heteroskedasticity modeling; ARCH/GARCH formalize volatility clustering
[[8](#bib.bib9 "Autoregressive conditional heteroscedasticity with estimates of the variance of united kingdom inflation"), [4](#bib.bib10 "Generalized autoregressive conditional heteroskedasticity")]. In SAE we use deterministic replay-computable proxies rather than fitting heavy time-series models in the hot path.

### 3.2 State construction from Binance replay (reproducible)

SAE must run identically in offline replay and production. We therefore define a per-step state that can be computed deterministically from
Binance USD-M futures replay streams (15m bars, funding history).

##### Market features.

Let ptp\_{t} be the close price and rt=log⁡pt−log⁡pt−1r\_{t}=\log p\_{t}-\log p\_{t-1}.
Realized volatility over a rolling window WσW\_{\sigma}:

|  |  |  |  |
| --- | --- | --- | --- |
|  | σt=∑i=t−Wσ+1tri2.\sigma\_{t}=\sqrt{\sum\_{i=t-W\_{\sigma}+1}^{t}r\_{i}^{2}}. |  | (16) |

Funding rate ftf\_{t} is aligned to the bar timeline (merged from funding history).
A simple deterministic liquidity proxy (any fixed proxy is acceptable as long as it is consistent across runs):

|  |  |  |  |
| --- | --- | --- | --- |
|  | λt=EMA​(vt)σt+ϵ,\lambda\_{t}=\frac{\mathrm{EMA}(v\_{t})}{\sigma\_{t}+\epsilon}, |  | (17) |

where vtv\_{t} is volume and ϵ>0\epsilon>0 avoids division by zero.

##### Account features.

Account state includes equity EtE\_{t}, peak equity EtmaxE\_{t}^{\max}, drawdown
DDt=1−Et/Etmax\mathrm{DD}\_{t}=1-E\_{t}/E\_{t}^{\max}, margin ratio mtm\_{t},
positions (direction, notional, leverage), and pacing statistics
(e.g., orders per window WrateW\_{\text{rate}}, average holding time, recent realized PnL).

### 3.3 Intended-policy specification and out-of-scope rules (DG-ready)

SAE adopts the Intended Policy Spec and hard out-of-scope rules defined in
Sections [2.1.1](#S2.SS1.SSS1 "2.1.1 Operationalizing 𝒜_\"intended\" via an Intended Policy Spec ‣ 2.1 Formal Delegation Gap ‣ 2 Problem Formulation ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")–[2.1.2](#S2.SS1.SSS2 "2.1.2 Out-of-scope rules (hard, reproducible) ‣ 2.1 Formal Delegation Gap ‣ 2 Problem Formulation ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors"). We use the same
𝒮t=(𝒯t,ℛt,ℳt,𝒰t)\mathcal{S}\_{t}=(\mathcal{T}\_{t},\mathcal{R}\_{t},\mathcal{M}\_{t},\mathcal{U}\_{t})
to (i) parameterize intended scope, (ii) enforce allowlists and caps at the executor boundary, and
(iii) label out-of-scope attempts deterministically for DG and attack instrumentation.

Concretely, 𝒯t\mathcal{T}\_{t} is implemented as allowlists over tools, venues, symbols, and accounts;
ℛt\mathcal{R}\_{t} becomes executable caps (leverage, notional, rate, slippage, holding time);
and ℳt/𝒰t\mathcal{M}\_{t}/\mathcal{U}\_{t} become state predicates that trigger tightening or reduce-only modes in the enforcement runtime.
This alignment ensures that the same specification drives both enforcement and measurement.

### 3.4 Trust state and trust-conditioned budgeting

##### Trust state.

Agentic execution adds a trust dimension beyond market/account state. SAE models trust as:

|  |  |  |  |
| --- | --- | --- | --- |
|  | zt=(ptprov,rtcap,𝕀tinj),z\_{t}=\big(p^{\mathrm{prov}}\_{t},\ r^{\mathrm{cap}}\_{t},\ \mathbb{I}^{\mathrm{inj}}\_{t}\big), |  | (18) |

where ptprov∈[0,1]p^{\mathrm{prov}}\_{t}\in[0,1] scores provenance of the active skill/toolchain,
rtcapr^{\mathrm{cap}}\_{t} scores capability risk (privilege and side-effect surface),
and 𝕀tinj∈{0,1}\mathbb{I}^{\mathrm{inj}}\_{t}\in\{0,1\} is an injection-alert flag from safety monitors.

##### Budget vector and tightening.

Let Bt∈ℝ≥0kB\_{t}\in\mathbb{R}^{k}\_{\geq 0} be a budget vector (e.g., leverage cap, notional cap, order-rate cap, slippage cap, max holding time).
We explicitly condition budgets on market/account/trust state:

|  |  |  |  |
| --- | --- | --- | --- |
|  | Bt=B0⋅g​(σt,λt,ft)⋅h​(mt,DDt)⋅q​(zt),B\_{t}=B\_{0}\cdot g(\sigma\_{t},\lambda\_{t},f\_{t})\cdot h(m\_{t},\mathrm{DD}\_{t})\cdot q(z\_{t}), |  | (19) |

where B0B\_{0} is the default budget,
g​(⋅)g(\cdot) tightens under volatile/illiquid/funding-extreme regimes,
h​(⋅)h(\cdot) tightens under constrained accounts (low margin / elevated drawdown),
and q​(⋅)q(\cdot) tightens when provenance is weak, capability risk is high, or injection alerts trigger.

##### Variant-to-switch mapping (for ablations).

We align SAE variants in Section [6.2](#S6.SS2 "6.2 SAE Variants and Measurements ‣ 6 Evaluation on Binance Replay ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors") to algorithmic switches:

NoSAE: bypass policy and enforcement (pass-through).

Budget: enable projection into ℱ​(Bt)\mathcal{F}(B\_{t}) using budgets from B0B\_{0} (optionally regime-conditioned gg).

Budget+Cooldown: Budget + temporal invariants (cooldown, order-rate caps).

Full: Budget+Cooldown + trust-conditioned tightening q​(zt)q(z\_{t}) and additional policy checks (tool/state predicates).

##### Numerical walkthrough (trust tightening in one step).

Consider a request with Lreq=5×L\_{\mathrm{req}}=5\times leverage in an extreme regime, produced by a skill with low provenance
ptprov=0.3p^{\mathrm{prov}}\_{t}=0.3 and an active injection alert 𝕀tinj=1\mathbb{I}^{\mathrm{inj}}\_{t}=1.
Suppose the default leverage budget is B0,L=3×B\_{0,L}=3\times and the default notional budget is B0,N=1.0B\_{0,N}=1.0 (normalized).
Let regime tightening yield gL​(σt,λt,ft)=13g\_{L}(\sigma\_{t},\lambda\_{t},f\_{t})=\tfrac{1}{3} and trust tightening yield qL​(zt)=0.5q\_{L}(z\_{t})=0.5.
Then the effective leverage cap becomes

|  |  |  |
| --- | --- | --- |
|  | Lcap=B0,L⋅gL⋅qL=3×13×0.5=0.5×,L\_{\mathrm{cap}}=B\_{0,L}\cdot g\_{L}\cdot q\_{L}=3\times\tfrac{1}{3}\times 0.5=0.5\times, |  |

which is clamped to 1×1\times in practice. If, for notional, gN=0.5g\_{N}=0.5 and qN=0.4q\_{N}=0.4, then

|  |  |  |
| --- | --- | --- |
|  | Ncap=B0,N⋅gN⋅qN=0.20,N\_{\mathrm{cap}}=B\_{0,N}\cdot g\_{N}\cdot q\_{N}=0.20, |  |

so the notional cap drops to 20%20\% of default. The returned decision is therefore LIMIT
with (Lcap=1×,Ncap=0.20)(L\_{\mathrm{cap}}=1\times,\ N\_{\mathrm{cap}}=0.20), optionally with cooldown enabled under extreme.

### 3.5 Projection-based enforcement: feasibility and a robust bound

##### Feasible set and projection.

Let u​(a)∈ℝdu(a)\in\mathbb{R}^{d} be a normalized action representation (e.g., leverage, notional, order-rate, slippage tolerance).
Budgets induce a feasible set ℱ​(Bt)\mathcal{F}(B\_{t}).
SAE computes an effective action by projection:

|  |  |  |  |
| --- | --- | --- | --- |
|  | ateff=arg⁡mina∈ℱ​(Bt)⁡D​(a,atreq),a\_{t}^{\mathrm{eff}}=\arg\min\_{a\in\mathcal{F}(B\_{t})}D(a,a\_{t}^{\mathrm{req}}), |  | (20) |

where DD is an execution-distance functional (e.g., weighted ℓ2\ell\_{2} over normalized degrees of freedom).
A special case recovers leverage clamping:

|  |  |  |  |
| --- | --- | --- | --- |
|  | Leff=min⁡(Lreq,Lcap).L\_{\mathrm{eff}}=\min(L\_{\mathrm{req}},L\_{\mathrm{cap}}). |  | (21) |

##### A weak but robust one-step loss bound.

Let et∈ℝde\_{t}\in\mathbb{R}^{d} denote the exposure vector induced by an effective action (notional, leverage, rate, slippage budget, etc.).
Assume the per-step loss proxy ℓt​(e)\ell\_{t}(e) is LL-Lipschitz w.r.t. a chosen norm:
|ℓt​(e)−ℓt​(e′)|≤L​‖e−e′‖|\ell\_{t}(e)-\ell\_{t}(e^{\prime})|\leq L\|e-e^{\prime}\|.
If SAE enforces ‖et‖≤Bt\|e\_{t}\|\leq B\_{t}, then

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℓt​(et)−ℓt​(0)≤L​‖et‖≤L​Bt,\ell\_{t}(e\_{t})-\ell\_{t}(0)\leq L\|e\_{t}\|\leq LB\_{t}, |  | (22) |

and under projection eteff=Πℱ​(Bt)​(etreq)e\_{t}^{\mathrm{eff}}=\Pi\_{\mathcal{F}(B\_{t})}(e\_{t}^{\mathrm{req}}) we additionally have

|  |  |  |  |
| --- | --- | --- | --- |
|  | ℓt​(eteff)−ℓt​(etreq)≤L⋅dist​(etreq,ℱ​(Bt)).\ell\_{t}(e\_{t}^{\mathrm{eff}})-\ell\_{t}(e\_{t}^{\mathrm{req}})\leq L\cdot\mathrm{dist}(e\_{t}^{\mathrm{req}},\mathcal{F}(B\_{t})). |  | (23) |

This bound avoids assuming a fixed return path or linear PnL scaling, and directly links last-mile projection to reduced worst-case
instantaneous loss amplification. Liquidation and exchange-specific margin mechanics are evaluated empirically in replay.

### 3.6 Algorithm hyperparameters (defaults) and auto-optimization hooks

| Component | Hyperparameter | Default |
| --- | --- | --- |
| Trader-state | Trade window size NN | 200 |
| Trader-state | Calibration | isotonic |
| Trader-state | Thresholds (τLIMIT,τBLOCK)(\tau\_{\textsf{LIMIT}},\tau\_{\textsf{BLOCK}}) | (0.50, 0.70) |
| Regime | Realized-vol window (bars) WσW\_{\sigma} | 60 |
| Regime | Regime thresholds (τσ,1,τσ,2)(\tau\_{\sigma,1},\tau\_{\sigma,2}) | (1.0, 2.0) |
| Funding | Extreme funding threshold τf\tau\_{f} | 0.01 |
| Liquidity | Illiquidity threshold τλ\tau\_{\lambda} | 0.0 (proxy-specific) |
| Enforcement | Baseline leverage cap | 3.0×3.0\times |
| Enforcement | Volatile leverage cap | 2.0×2.0\times |
| Enforcement | Extreme leverage cap | 1.0×1.0\times |
| Enforcement | Cooldown (volatile / extreme) | 60s / 120s |
| Enforcement | Rate-limit window WrateW\_{\text{rate}} | 60s |
| Enforcement | Staging slices (volatile / extreme) | 4 / 5 |

##### Practical tuning with feasibility constraints.

In binance mode, we tune SAE parameters under hard operational constraints (e.g., FalseBlock ≤0.20\leq 0.20 and AttackSuccess ≤0.80\leq 0.80)
using the auto-optimization protocol described in Section 6. This ensures the design is not merely conceptual:
hyperparameters are selected to satisfy deployability constraints while maximizing survivability objectives on real replay data.

## 4 Threat Model and Mitigations

SAE is motivated by a structural shift: when an agent is granted tool and executor privileges,
*untrusted text becomes a control surface for monetized side effects*.
This section formalizes the threat model for agentic crypto execution and specifies which risks SAE
is designed to mitigate, how mitigations map to enforceable invariants, and how attacks are operationalized
as reproducible tests in our Binance replay evaluation.

### 4.1 Threat model: assets, adversaries, and success conditions

##### System boundary.

We consider the pipeline:

|  |  |  |
| --- | --- | --- |
|  | Strategy (LLM or non-LLM)→SAE middleware→Local executor→Exchange API.\text{Strategy (LLM or non-LLM)}\rightarrow\text{SAE middleware}\rightarrow\text{Local executor}\rightarrow\text{Exchange API}. |  |

The strategy and its inputs (prompts, skills, narratives, external content) are treated as *potentially compromised*.
SAE is assumed to run inside the executor boundary where it can intercept and enforce all outbound execution calls.

##### Assets.

We protect (i) account capital and margin safety (avoid liquidation and tail drawdowns),
(ii) execution integrity (prevent unauthorized tools/venues/symbols and out-of-scope actions),
(iii) availability (prevent order flooding and pathological churn that destabilizes the executor),
and (iv) audit integrity (retain sufficient evidence for post-incident analysis).

##### Adversaries.

We model adversaries with realistic capabilities for agent ecosystems:

Prompt injection (direct/indirect). Attacker controls some instruction channel or retrieved content that the agent treats as guidance
[[12](#bib.bib28 "Formalizing and benchmarking prompt injection attacks and defenses"), [27](#bib.bib29 "Benchmarking and defending against indirect prompt injection attacks on large language models")].

Skill / plugin supply-chain attacker. Attacker publishes or updates an installable skill that influences tool calls and execution behavior
[[25](#bib.bib5 "Agent skills for large language models: architecture, acquisition, security, and the path forward")]. This includes compromised registries or malicious packages distributed via popular discovery surfaces.

Narrative / instruction contagion. Attacker injects action-inducing norms via agent social channels, causing rapid policy drift or unsafe
execution cascades [[11](#bib.bib6 "”Humans welcome to observe”: A First Look at the Agent Social Network Moltbook"), [13](#bib.bib26 "OpenClaw agents on moltbook: risky instruction sharing and norm enforcement in an agent-only social network")].

Execution-layer stress adversary. Attacker does not need to “steal funds” directly; inducing extreme leverage, order flooding, or
slippage tolerance during stress can amplify tail losses in perpetual markets [[9](#bib.bib27 "Fundamentals of perpetual futures")].

##### Assumptions (what SAE does *not* solve).

SAE does not assume it can prevent all compromise or perfectly identify malicious content.
Instead it assumes: (i) upstream intent may be wrong or adversarial; (ii) local execution must be constrained anyway;
(iii) exchange mechanics (funding, maintenance margin tiers) can amplify execution mistakes.
SAE is not a custody solution and does not replace key management, 2FA, or exchange-side controls.

##### Attack success conditions.

An attack is considered successful if it produces an executed action that violates the intended spec
(Section [3.3](#S3.SS3 "3.3 Intended-policy specification and out-of-scope rules (DG-ready) ‣ 3 SAE Design and Algorithms ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")) or violates enforced execution constraints. Concretely, success includes:

Out-of-scope execution: at∉Aintended​(𝒮t)a\_{t}\notin A\_{\mathrm{intended}}(\mathcal{S}\_{t}) passes through to the executor (tool/venue/state/cap violation).

Constraint evasion: effective leverage/notional/order-rate/slippage exceeds SAE caps or violates cooldown/rate limits.

Tail amplification: statistically meaningful worsening of survivability outcomes (higher MDD/CVaR or liquidation proxy)
relative to policy-compliant baselines under the same replay stream.

### 4.2 SAE mitigations as enforceable invariants

SAE mitigations are deliberately *execution-centric*: they are implemented where side effects occur and therefore cannot be bypassed by upstream compromise.

##### (M1) Intended-policy spec and hard out-of-scope rules.

SAE operationalizes “what is allowed” using the structured Intended Policy Spec
𝒮t=(𝒯t,ℛt,ℳt,𝒰t)\mathcal{S}\_{t}=(\mathcal{T}\_{t},\mathcal{R}\_{t},\mathcal{M}\_{t},\mathcal{U}\_{t}) (Section [3.3](#S3.SS3 "3.3 Intended-policy specification and out-of-scope rules (DG-ready) ‣ 3 SAE Design and Algorithms ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")).
This yields deterministic out-of-scope labeling and enables enforceable allowlists:
authorized tools, venues, symbols, accounts; and state-dependent constraints (reduce-only under stress).

##### (M2) Trust-state–conditioned tightening (agent-specific safety input).

SAE explicitly models trust as zt=(ptprov,rtcap,𝕀tinj)z\_{t}=(p^{\mathrm{prov}}\_{t},r^{\mathrm{cap}}\_{t},\mathbb{I}^{\mathrm{inj}}\_{t})
and tightens budgets using a factorized map:

|  |  |  |
| --- | --- | --- |
|  | Bt=B0⋅g​(market)⋅h​(account)⋅q​(zt),B\_{t}=B\_{0}\cdot g(\text{market})\cdot h(\text{account})\cdot q(z\_{t}), |  |

so that low provenance, high capability risk, or injection alerts reduce exposure budgets even if the strategy requests more.
This makes “untrusted intent” non-optional in the enforcement logic.

##### (M3) Projection-based enforcement of exposure budgets.

Given a requested action atreqa\_{t}^{\mathrm{req}}, SAE enforces feasibility via projection
(Section [3.5](#S3.SS5 "3.5 Projection-based enforcement: feasibility and a robust bound ‣ 3 SAE Design and Algorithms ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")):

|  |  |  |
| --- | --- | --- |
|  | ateff=arg⁡mina∈ℱ​(Bt)⁡D​(a,atreq),a\_{t}^{\mathrm{eff}}=\arg\min\_{a\in\mathcal{F}(B\_{t})}D(a,a\_{t}^{\mathrm{req}}), |  |

which generalizes heuristic clamping and ensures effective actions stay inside the budget region.
This blocks parameter escalation attacks without requiring semantic understanding of the prompt.

##### (M4) Temporal invariants: cooldown and order-rate limiting.

Many practical failure modes are temporal (order flooding, churn, rapid flip under stress).
SAE enforces cooldown timers and rate caps as hard invariants at the executor boundary,
preventing high-frequency abuse even if upstream generates repeated actions.

##### (M5) Slippage bounds and staged execution.

Under stress, excessive slippage tolerance can act as a “permission” to trade at any price.
SAE enforces slippage caps and (optionally) staged execution (slicing notional into time-spaced orders),
reducing microstructure-induced loss amplification.

##### (M6) Auditability and incident response.

Each decision emits an audit record (matched rule, budgets, effective action, and state snapshot including trust signals).
This supports post-mortems and reproducibility: given the replay stream and config, the same decision trace is re-generated.

##### Mitigation coverage matrix.

Table [2](#S4.T2 "Table 2 ‣ Mitigation coverage matrix. ‣ 4.2 SAE mitigations as enforceable invariants ‣ 4 Threat Model and Mitigations ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors") summarizes which SAE mechanisms address which threat classes.

| Threat class | SAE mitigations (non-bypassable) |
| --- | --- |
| Prompt injection / untrusted instructions | (M1) intended-spec allowlists + hard OOS rules; (M3) projection into ℱ​(Bt)\mathcal{F}(B\_{t}); (M4) cooldown/rate limits; (M6) audit. |
| Skill / plugin supply chain [[25](#bib.bib5 "Agent skills for large language models: architecture, acquisition, security, and the path forward")] | (M2) trust-state tightening (pprovp^{\mathrm{prov}}); (M1) tool/venue allowlists; (M3) projection; (M6) audit for provenance. |
| Narrative contagion in agent networks [[11](#bib.bib6 "”Humans welcome to observe”: A First Look at the Agent Social Network Moltbook")] | (M2) narrative/injection flags (optional) + tightening; (M4) temporal invariants; (M1) state-dependent reduce-only modes. |
| Execution-layer stress (escalation, flooding, slippage abuse) | (M3) budget projection; (M4) cooldown/rate caps; (M5) slippage bounds + staging; (M6) traceable enforcement. |

### 4.3 Attack suite for evaluation (behavioral safety tests)

To avoid triviality (e.g., only “request 20×\times leverage”), we define a family of reproducible attack generators.
Each generator produces an *out-of-scope action attempt stream* that is interleaved with the strategy’s normal intended actions.
All attacks are labeled using the deterministic out-of-scope rules induced by 𝒮t\mathcal{S}\_{t}.

##### Attack families.

We evaluate the following classes, parameterized for replay:

Parameter escalation: attempt leverage/notional/slippage/order-rate values beyond ℛt\mathcal{R}\_{t} caps
(or beyond tightened caps under ℳt/𝒰t\mathcal{M}\_{t}/\mathcal{U}\_{t}).

Cooldown bypass / order flooding: attempt repeated rapid-fire actions to violate temporal invariants (M4).

Tool/venue misuse: attempt unauthorized tools, venues, symbols, or cross-account actions (violating 𝒯t\mathcal{T}\_{t}).

State-violation stress: attempt risk-on actions while the system is in constrained states
(e.g., extreme volatility regime or low margin ratio where reduce-only is expected).

Narrative-induced flip stress: attempt rapid long/short flipping that is in-scope at the action-type level
but becomes out-of-scope under rate/cooldown and state-dependent tightening.

##### AttackSuccess, FalseBlock, and DG linkage.

For an injected attack attempt stream {atatk}\{a\_{t}^{\mathrm{atk}}\}, we measure:

AttackSuccess (AS): fraction of attack attempts that result in an executed action violating intended scope or enforced caps.
Operationally, AS counts an attempt as successful if the executor receives an effective action that is out-of-scope
or violates leverage/notional/rate/slippage/cooldown constraints.

FalseBlock (FB): fraction of legitimate in-scope intended actions that are blocked (or overly constrained if using a strict definition).
FB serves as an opportunity-cost proxy.

DG metrics: DG\_rate and DG\_loss are computed from the same out-of-scope labeling and loss proxies,
connecting attack robustness to measurable delegation-gap harm (Section [3.3](#S3.SS3 "3.3 Intended-policy specification and out-of-scope rules (DG-ready) ‣ 3 SAE Design and Algorithms ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")).

##### Reproducibility and feasibility constraints.

All attack generators are seeded and replay-deterministic. In binance mode, we tune SAE hyperparameters under
feasibility constraints of the form:

|  |  |  |
| --- | --- | --- |
|  | AS​(π)≤α,FB​(π)≤β,Lat​(π)≤τ,\mathrm{AS}(\pi)\leq\alpha,\qquad\mathrm{FB}(\pi)\leq\beta,\qquad\mathrm{Lat}(\pi)\leq\tau, |  |

matching the constrained selection family in Eq. (10) of our formulation.
In our reported auto-optimization protocol, we instantiate
β=0.20\beta=0.20 and α=0.80\alpha=0.80 (and report latency as an overhead metric), ensuring that improvements in survivability
do not come from trivially blocking everything.

##### Why this matters for perpetual markets.

In perpetual futures, execution mistakes can be amplified via leverage and margin mechanics,
and funding cash flows can directly affect margin and liquidation risk. The attack suite therefore focuses on execution parameters that are structurally amplified (leverage, frequency, slippage)
and on state-triggered tightening where survivability is most fragile.

## 5 Implementation and Reproducibility

### 5.1 System Boundary and Microservice Interfaces

##### Design principle: non-bypassable last-mile enforcement.

SAE is implemented as a *policy-gated executor* that sits at the boundary where side effects occur (order placement,
cancellation, position modification). The core principle is that the LLM output is treated as *untrusted intent*:
all proposed actions must pass a non-bypassable gating/projection step before they are executed.

##### Service decomposition.

Our reference implementation uses a minimal, reproducible split:
(i) MarketData (Binance replay fetch + caching + alignment),
(ii) AgentCore (produces intended actions),
(iii) SAE Gate (budgeting, cooldown, trust-/state-conditioned tightening),
(iv) Executor/Sim (fills, fees, slippage, margin, liquidation),
and (v) Logger (equity curve, actions, safety events, DG labels).

##### Action schema.

The agent produces an IntendedAction object; SAE maps it to ALLOW/LIMIT/BLOCK.
A minimal action schema is:

The meta field carries tool provenance / trust flags (when available), enabling trust-conditioned budgeting.

### 5.2 Binance Data Acquisition and Preprocessing

##### Public endpoints (no API key required for market data).

The replay dataset is constructed from Binance USD-M futures REST market endpoints:
/fapi/v1/klines (candlesticks),
/fapi/v1/fundingRate (funding history),
and /fapi/v1/exchangeInfo (contract metadata).
All fetched artifacts are cached on disk to ensure deterministic reruns.

##### Alignment and state construction.

Klines define the master time index at the selected interval. Funding events are aligned to the nearest subsequent kline
boundary and merged into the per-step state. For each step we construct:

|  |  |  |
| --- | --- | --- |
|  | st=(OHLCVt,fundingt,spread/slip​\_​proxyt,accountt,trustt).s\_{t}=(\mathrm{OHLCV}\_{t},\mathrm{funding}\_{t},\mathrm{spread/slip\\_proxy}\_{t},\mathrm{account}\_{t},\mathrm{trust}\_{t}). |  |

This state is consumed by both the agent and the SAE gate.

### 5.3 Margin Accounting and Liquidation Engine

##### Margin and maintenance margin.

We implement a configurable liquidation check. Liquidation is triggered when:

|  |  |  |
| --- | --- | --- |
|  | margin​\_​balancet≤maintenance​\_​margint.\mathrm{margin\\_balance}\_{t}\leq\mathrm{maintenance\\_margin}\_{t}. |  |

Maintenance margin is computed using the standard tiered form:

|  |  |  |
| --- | --- | --- |
|  | maintenance​\_​margin=notional⋅mmr−maint​\_​amount,\mathrm{maintenance\\_margin}=\mathrm{notional}\cdot\mathrm{mmr}-\mathrm{maint\\_amount}, |  |

where (mmr,maint​\_​amount)(\mathrm{mmr},\mathrm{maint\\_amount}) are tier-dependent. If official tier tables are available, they can be supplied
as configs/mm\_tiers\_<symbol>.csv. If not, the system falls back to a conservative placeholder to avoid
overstating survivability.

### 5.4 Auto-Optimization and Walk-Forward Parameter Selection

##### Constrained search with early stopping.

We provide auto\_optimize.py, a batched best-so-far search around a checkpointed incumbent configuration.
Each sampled candidate is evaluated via a full replay and accepted only if it satisfies feasibility constraints:

|  |  |  |
| --- | --- | --- |
|  | FalseBlock≤τFB,AttackSuccess≤τAS.\mathrm{FalseBlock}\leq\tau\_{\mathrm{FB}},\quad\mathrm{AttackSuccess}\leq\tau\_{\mathrm{AS}}. |  |

The search stops when no improvement is found for patience consecutive batches.

##### Reproducible commands and artifacts.

The canonical command for Binance replay tuning is:

The run writes:
outputs\_auto/best.json (best score + metadata),
outputs\_auto/best\_full\_params.yaml (best parameters),
and outputs\_auto/final/<run\_id>/ (tables, figures, logs).
All experiments fix random seeds at the runner entry point and record configs to ensure bitwise reproducibility of outputs
under a fixed environment.

### 5.5 Open Artifact: Installable SAE Policy Guard Skill (skills.sh)

##### Why a skills.sh artifact matters.

Our threat model emphasizes that *installable skill ecosystems* turn capability acquisition into a supply-chain problem:
an agent can extend its execution surface by installing third-party skills. To make SAE reproducible in such ecosystems,
we package SAE as an installable skills.sh skill, sae-policy-guard.111<https://skills.sh/true-ai-labs/sae-policy-guard/sae-policy-guard>

##### What the artifact implements.

The skill instantiates SAE as *execution-layer middleware* that runs before any order reaches the exchange executor.
Given an intended action and a context snapshot (market state, account state, and optional trust signals), it returns a
three-way decision:

|  |  |  |
| --- | --- | --- |
|  | ALLOW/LIMIT/BLOCK,\texttt{ALLOW}\;/\;\texttt{LIMIT}\;/\;\texttt{BLOCK}, |  |

together with a projected risk budget (e.g., leverage/notional/rate/slippage caps) and a human-readable rationale string,
making the enforcement decision auditable.

##### Installation and minimal usage.

The skill is installable via the skills CLI:

In our experiments, the policy guard is invoked as a pre-trade gate; the simulator logs both the *requested* and
*effective* (post-projection) actions for DG accounting and for reporting AttackSuccess/FalseBlock.

##### Reproducibility linkage.

We recommend reporting (i) the exact skill version or commit hash, (ii) the exported policy spec (caps, cooldown rules),
and (iii) the tuning output (best\_full\_params.yaml). This makes the paper’s SAE evaluation
reproducible in a real skills-enabled agent stack.

### 5.6 Reproducibility Checklist

We recommend reporting the following items for reproducibility:
(i) symbols, interval, and time window (from configs/default.yaml);
(ii) commit hash or version tag of the code package;
(iii) the best-params YAML exported by auto\_optimize;
(iv) cached Binance replay files and their checksums; and
(v) the exact command line used for the reported tables/figures.

## 6 Evaluation on Binance Replay

### 6.1 Experimental Design

##### Objective.

We evaluate whether Survivability-Aware Execution (SAE) reduces tail-risk and execution-induced failure
modes when an agent is granted execution privileges. Our evaluation focuses on:
(i) drawdown and tail losses,
(ii) robustness to out-of-scope action attempts and delegation-gap violations, and
(iii) operational costs such as latency and false blocks.

##### Data: Binance USD-M futures replay.

We replay real Binance USD-M perpetual futures market data for BTCUSDT and ETHUSDT
using a 15-minute bar interval over 2025-09-01 to 2025-12-01.
The dataset is constructed from Binance public REST endpoints (no API key required for market data),
including candlestick (klines), funding-rate history, and exchange metadata.
Funding rates are aligned to the kline timeline and merged into the per-step simulator state.

##### Backtest & execution simulator.

We use a simplified perpetual futures simulator with:
(i) taker fees and slippage modeled as a function of notional,
(ii) margin accounting with a configurable liquidation check (Section [5.3](#S5.SS3 "5.3 Margin Accounting and Liquidation Engine ‣ 5 Implementation and Reproducibility ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")), and
(iii) an agent loop that generates intended actions which are gated by SAE before reaching the executor.
Each variant produces an equity curve and an action stream, from which we compute risk, safety, and usability metrics.

### 6.2 SAE Variants and Measurements

##### Variants.

We compare five variants:
NoSAE (no gating),
StaticOMS (fixed leverage cap + position-size limit + stop-loss + rate limit; no regime detection, no trust-state),
Budget (exposure budgeting / projection with state-based tightening but no trust-state),
Budget+Cooldown (budgeting plus cooldown/order-rate constraints),
and Full (budgeting plus trust-/state-conditioned tightening and additional policy checks).

##### Attack and Delegation-Gap instrumentation.

We inject an adversarial stream of *out-of-scope* action attempts (e.g., tool misuse, cap violations, or state violations,
depending on the configured attack generator). We measure:
AttackSuccess (fraction of attack attempts that pass through),
FalseBlock (fraction of in-scope legitimate actions blocked),
and DG metrics (delegation-gap rate and a loss proxy) computed from out-of-scope executions and their associated
loss contribution under the intended-policy specification.

##### Risk metrics.

We report:
MDD (maximum drawdown),
CVaR0.95 and CVaR0.99 on per-step returns,
Liquidation rate, and Latency (estimated per-step decision overhead attributable to SAE).

### 6.3 Results

##### Main results.

Table [3](#S6.T3 "Table 3 ‣ Main results. ‣ 6.3 Results ‣ 6 Evaluation on Binance Replay ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors") summarizes risk and safety metrics on the Binance replay.
Adding StaticOMS makes clear that SAE adds value not merely on top of an unprotected executor, but also on top of conventional fixed-rule risk management.
Relative to NoSAE, all SAE variants dramatically reduce tail risk (CVaR) and drawdown while reducing the attack success rate.
Relative to StaticOMS, SAE further improves survivability by introducing state-aware and trust-aware execution constraints rather than relying only on fixed caps and stop-loss logic.
In this replay, Budget and Budget+Cooldown achieve the best risk profile among SAE variants, while Full incurs higher overhead and shows slightly worse drawdown/CVaR than budget-only variants, highlighting the importance of calibration and ablation-based design.

| Variant | MDD | CVaR0.95 | CVaR0.99 | Liq. | AS | FB | Lat. (ms) | DGr | DGℓ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NoSAE | 0.4643 | −1.363×10−3-1.363\times 10^{-3} | −4.025×10−3-4.025\times 10^{-3} | 0 | 1.0000 | 0.0000 | 0.00135 | 0.05889 | 0.64712 |
| StaticOMS | 0.1184 | −2.34×10−4-2.34\times 10^{-4} | −5.62×10−4-5.62\times 10^{-4} | 0 | 0.8847 | 0.0112 | 0.00194 | 0.05160 | 0.11890 |
| Budget | 0.03251 | −5.10×10−5-5.10\times 10^{-5} | −1.01×10−4-1.01\times 10^{-4} | 0 | 0.7600 | 0.0000 | 0.00251 | 0.04222 | 0.02132 |
| Budget+Cool | 0.03627 | −5.90×10−5-5.90\times 10^{-5} | −1.03×10−4-1.03\times 10^{-4} | 0 | 0.7588 | 0.0000 | 0.00321 | 0.04333 | 0.02553 |
| Full | 0.03190 | −4.80×10−5-4.80\times 10^{-5} | −1.02×10−4-1.02\times 10^{-4} | 0 | 0.7281 | 0.0000 | 0.01029 | 0.04700 | 0.01916 |

Notes: Liq.=liquidation count; AS=AttackSuccess; FB=FalseBlock; Lat.=decision overhead; DGr=DG rate; DGℓ=DG loss proxy. StaticOMS captures standard fixed-rule risk management without trust-state conditioning or regime-aware tightening.

##### Interpreting AttackSuccess under Full.

The remaining AttackSuccess of 0.7280.728 indicates that Full substantially reduces, but does not eliminate, adversarial leakage.
In our attack suite, explicit cap violations and unauthorized tool/venue requests are usually caught by projection and allowlists.
The residual successes arise primarily from state-sensitive and timing-sensitive attempts that fall near regime boundaries or remain formally in-scope at the request level but are still harmful in context.
In particular, when the gate is calibrated to preserve zero FalseBlock in this run, ambiguous cases are more often LIMITed than BLOCKed.
This should therefore be interpreted as a practical trade-off rather than a contradiction:
Full prioritizes survivability improvement with no observed false blocking, but still leaves room for stricter configurations that would further reduce AttackSuccess at the cost of higher intervention. While SAE substantially reduces AttackSuccess in our current evaluation (from 1.00 to 0.728), further lowering this metric—especially under stronger and adaptive attack suites—is an important direction for future work and will be addressed in a subsequent SAE v2 design.

##### Equity and drawdown.

Figure [2](#S6.F2 "Figure 2 ‣ Equity and drawdown. ‣ 6.3 Results ‣ 6 Evaluation on Binance Replay ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors") highlights that the three SAE variants cluster closely in nominal regimes (SAE-focused zoom),
while Figure [3](#S6.F3 "Figure 3 ‣ Equity and drawdown. ‣ 6.3 Results ‣ 6 Evaluation on Binance Replay ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors") shows that NoSAE experiences substantially larger drawdowns driven by tail events.
This is consistent with SAE acting as a *survivability layer* that primarily removes extreme downside rather than maximizing average returns.

![Refer to caption](2603.10092v1/figures/equity_curves_sae_zoom.png)
![Refer to caption](2603.10092v1/figures/drawdown_curves.png)

Using Table [3](#S6.T3 "Table 3 ‣ Main results. ‣ 6.3 Results ‣ 6 Evaluation on Binance Replay ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors"), SAE yields large survivability gains compared to NoSAE:

Max drawdown (MDD): NoSAE 0.4643→0.4643\rightarrow Budget 0.03250.0325 (93.0% reduction);
NoSAE 0.4643→0.4643\rightarrow Full 0.03190.0319 (93.1% reduction).

Tail risk (CVaR0.99): tail-loss magnitude drops from 4.025×10−34.025\times 10^{-3} to ≈1.02×10−4\approx 1.02\times 10^{-4}
(∼\sim97.5% reduction in magnitude across SAE variants).

Delegation-gap harm: DG\_loss decreases from 0.6470.647 to 0.0190.019–0.0260.026
(96.1%–97.0% reduction), indicating that out-of-scope executions no longer dominate loss contribution.

Attack robustness: AttackSuccess decreases from 1.001.00 to 0.7280.728 (27.2 percentage-point reduction) under Full,
while FalseBlock remains 0.000.00 in this replay.

Operational overhead: latency increases from 1.348×10−31.348\times 10^{-3} ms (NoSAE) to 2.505×10−32.505\times 10^{-3} ms (Budget)
and 1.029×10−21.029\times 10^{-2} ms (Full), quantifying an enforcement-throughput trade-off (Full is ∼7.63×\sim 7.63\times NoSAE here).

### 6.4 Uncertainty and Statistical Significance

##### Why robust tests matter.

Per-step returns in market replay are temporally correlated; naive i.i.d. tests can overstate significance.
We therefore report dependence-aware uncertainty via block bootstrap confidence intervals for mean return,
a paired Wilcoxon signed-rank test on aligned per-step returns, and a two-proportion z-test for AttackSuccess.

##### Block bootstrap (mean return).

The 95% block-bootstrap confidence intervals for mean per-step return are:

|  |  |  |
| --- | --- | --- |
|  | NoSAE:[−9.85,−5.01]×10−5,Full:[−2.27,−1.71]×10−5.\textsc{NoSAE}:[-9.85,\,-5.01]\times 10^{-5},\qquad\textsc{Full}:[-2.27,\,-1.71]\times 10^{-5}. |  |

The intervals are well-separated, consistent with SAE removing catastrophic tail losses and improving the average return in this window.

##### Paired test on returns.

A paired Wilcoxon signed-rank test comparing aligned per-step returns between NoSAE and Full
rejects the null of equal medians (p=0.0113p=0.0113).

##### AttackSuccess significance.

A two-proportion test for AttackSuccess between NoSAE and Full yields
p=1.76×10−8p=1.76\times 10^{-8}, confirming that the reduction in out-of-scope attacks passing through is highly significant.

| Statistic | NoSAE | Full |
| --- | --- | --- |
| Mean return 95% block-bootstrap CI | [−9.85,−5.01]×10−5[-9.85,\,-5.01]\times 10^{-5} | [−2.27,−1.71]×10−5[-2.27,\,-1.71]\times 10^{-5} |
| Wilcoxon signed-rank (pp) | 0.01130.0113 | |
| Two-proportion test on AttackSuccess (pp) | 1.76×10−81.76\times 10^{-8} | |

### 6.5 Discussion and Practical Takeaways

##### Why ablations matter.

Although SAE variants show similar nominal equity in this window (Figure [2](#S6.F2 "Figure 2 ‣ Equity and drawdown. ‣ 6.3 Results ‣ 6 Evaluation on Binance Replay ‣ Execution Is the New Attack Surface: Survivability-Aware Agentic Crypto Trading with OpenClaw-Style Local Executors")), they differ in robustness and overhead.
Budget-only gating offers strong tail-risk reduction with low latency increase, while Full further reduces AttackSuccess and DG\_loss
but incurs higher latency. This motivates reporting ablations and explicitly characterizing the enforcement–throughput trade-off.

##### Limitations.

Results depend on the configured attack generator, the intended-policy specification used for out-of-scope labeling,
and the replay window. Future evaluation should include regime-diverse windows (e.g., high-volatility weeks, cross-asset stress),
and report uncertainty intervals for tail-risk deltas and robustness rates under multiple attack distributions.

## 7 Discussion

##### SAE as the missing contract in OpenClaw-style stacks.

OpenClaw-style architectures already emphasize tool interception and enforceable boundaries.
SAE complements this by specifying a *trading-domain execution contract* that can be enforced at the same gateway/executor boundary:
explicit context, auditable ALLOW/LIMIT/BLOCK decisions, and non-bypassable constraints on exposure, pace, and slippage.
This is precisely the layer that prompt-only safety and model alignment cannot reliably provide.

##### Why skills.sh makes “untrusted intent” unavoidable.

Skill marketplaces such as skills.sh turn capability acquisition into an operational workflow.
From a security perspective, installing a skill is a supply-chain event: it can modify which tools are called, how parameters are chosen,
and how external content is trusted.
Therefore, upstream intent is not merely “noisy”—it is structurally *untrusted* in the presence of third-party skills.
SAE’s trust state and trust-conditioned tightening make this assumption explicit and enforceable.

##### Tail-risk gains without being an alpha model.

SAE does not aim to improve prediction accuracy; it reduces the blast radius of execution mistakes.
The Binance replay shows that SAE variants often preserve nominal trajectories in typical regimes while producing large improvements in MDD/CVaR and DG loss.
This is consistent with SAE acting as a survivability layer: it prevents catastrophic actions (over-leverage, flood, excessive slippage, risk-on under stress) that dominate the tail.

##### Robustness must be reported as a systems metric.

In the OpenClaw+skills setting, robustness is not a property of the model alone.
By operationalizing intent (Intended Policy Spec) and logging out-of-scope actions, SAE enables reproducible reporting of AttackSuccess, FalseBlock, DG rate, and DG loss.
This transforms qualitative security claims into measurable system-level metrics.

##### Ablations and the enforcement–throughput frontier.

More checks are not always better.
Budget-only projection can deliver strong survivability improvements at low overhead, while trust-/state-conditioned tightening and extra policy checks
trade additional robustness for latency.
In practice, OpenClaw-style executors need a Pareto point that matches throughput requirements and acceptable adversarial leakage.
This motivates reporting ablations as first-class results and tuning SAE under explicit feasibility constraints.

## 8 Limitations and Future Work

##### Venue mechanics and replay fidelity.

Liquidation, maintenance margin tiers, fees, and market impact vary across venues and evolve over time.
Our replay uses a configurable simulator and aligned funding, but offline evaluation remains an approximation.
Future work should incorporate verified tier schedules per venue, richer impact models, and stress tests for liquidity holes.

##### Skill supply chain realism.

While we model skill/provenance risk via a trust state, real ecosystems (e.g., skills.sh) introduce additional complexity:
versioning, dependency trees, transitive trust, and registry governance.
A next step is to integrate SBOM-style metadata, signatures, and reproducible build attestations into trust scoring,
and to define standardized provenance benchmarks for skill marketplaces.

##### Adaptive adversaries in OpenClaw-style tool interception.

Attackers can probe gate behavior, adapt prompts, and route around policy checks by switching tools or venues.
Future work should evaluate adaptive multi-step adversaries, multi-venue execution, and cross-margin scenarios,
while keeping the evaluation protocol reproducible and safe.

##### Trust calibration and drift.

Provenance scores, capability-risk scores, and injection alerts can be noisy and drift over time.
Miscalibration can increase FalseBlock or allow leakage.
Future work includes online calibration under drift, Bayesian trust aggregation, and learning-to-tighten policies that remain auditable.

##### Beyond trading: general-purpose executor safety.

Although we focus on crypto execution, the OpenClaw+skills pattern applies broadly (payments, cloud ops, procurement).
A promising direction is a family of SAE-like domain contracts for privileged executors, plus a conformance suite:
“does this OpenClaw-style executor satisfy the contract and log sufficient evidence?”

##### Regime diversity and generalization.

Our main results are for BTCUSDT/ETHUSDT over a specific window.
Future work should extend to regime-diverse periods (high-volatility weeks, cross-asset stress), additional symbols,
and uncertainty intervals across multiple seeds and attack distributions to quantify generalization.

## References

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
