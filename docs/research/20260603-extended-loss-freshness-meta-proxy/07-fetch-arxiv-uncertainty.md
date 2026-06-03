##### Report GitHub Issue

Content selection saved. Describe the issue below:

![arXiv logo](/static/browse/0.3.4/images/arxiv-logo-one-color-white.svg)

# Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence

###### Abstract

Post-hoc explanation methods are widely used to interpret black-box predictions, but their generation is often computationally expensive and their reliability is not guaranteed. We propose epistemic uncertainty as a low-cost proxy for explanation reliability: high epistemic uncertainty identifies regions where the decision boundary is poorly defined and where explanations become unstable and unfaithful. This insight enables two complementary use cases: ‘improving worst-case explanations’ (routing samples to cheap or expensive XAI methods based on expected explanation reliability), and ‘recalling high-quality explanations’ (deferring explanation generation for uncertain samples under constrained budget). Across four tabular datasets, five diverse architectures, and four XAI methods, we observe a strong negative correlation between epistemic uncertainty and explanation stability. Further analysis shows that epistemic uncertainty distinguishes not only stable from unstable explanations, but also faithful from unfaithful ones. Experiments on image classification confirm that our findings generalize beyond tabular data.⋆

## 1 Introduction

Explainable AI (XAI) methods have become essential for interpreting black-box model predictions in high-stakes domains [[1](#bib.bib14 "Peeking inside the black-box: a survey on explainable artificial intelligence (xai)"), [4](#bib.bib15 "Explainable artificial intelligence (xai): concepts, taxonomies, opportunities and challenges toward responsible ai")]. In particular, ‘model-agnostic’ explanations [[18](#bib.bib31 "A unified approach to interpreting model predictions"), [27](#bib.bib33 "\"Why should i trust you?\" explaining the predictions of any classifier")] have proven flexible across a wide range of models, but this comes with substantial computational cost and unreliable outputs: explanations may inherit uncertainty from the model or arise from biases intrinsic to the explanation technique, often in an input-dependent manner. Existing evaluation criteria such as faithfulness and stability [[35](#bib.bib13 "On the (in) fidelity and sensitivity of explanations"), [2](#bib.bib60 "Sanity checks for saliency maps")] can detect unreliable explanations, but only retrospectively and at high computational cost, making them impractical at runtime. Thus, current XAI lacks a low-cost mechanism to decide how much computational effort to invest in an explanation before generating it.

Uncertainty quantification (UQ) addresses model reliability by identifying regions where predictions are poorly supported by training data. Recent works connect UQ with XAI – using explanations to estimate uncertainty [[28](#bib.bib37 "Explainability and uncertainty: two sides of the same coin for enhancing the interpretability of deep learning models in healthcare")], analyzing how uncertainty undermines explanation stability [[8](#bib.bib41 "Uncertainty propagation in xai: a comparison of analytical and empirical estimators")], or explaining uncertainty itself [[6](#bib.bib8 "Explaining predictive uncertainty by exposing second-order effects")] – yet all still require generating explanations first. Most closely related, [[38](#bib.bib36 "Robust explanations through uncertainty decomposition: a path to trustworthier ai")] uses uncertainty to guide explanation type selection or reject unreliable explanations. However, no prior work frames uncertainty-guided XAI resource allocation as a cost-benefit problem, where deferring explanations yields computational savings or prevents misleading attributions.

In this paper, we systematically explore the relationship between epistemic uncertainty and explanation reliability across multiple datasets, architectures, and XAI methods. We hypothesize that explanations are inherently unstable and unfaithful in high epistemic uncertainty regions, enabling two complementary use cases: (1) *improving worst-case explanations*, where epistemic uncertainty routes samples to low- or high-cost XAI methods depending on expected reliability, and (2) *recalling high-quality explanations*, where explanation generation is deferred for high-uncertainty samples under constrained computational budget.
For models without low-cost native epistemic uncertainty estimation, lightweight surrogate models provide effective proxies.
Our contributions are as follows:

*UQ-XAI correlation analysis:* We identify systematic relationships between epistemic uncertainty and XAI stability and faithfulness, including a clear monotonic pattern across epistemic strata (low >> medium ≫\gg high).

*Uncertainty-guided resource allocation:* We propose a framework that routes explanation effort based on epistemic uncertainty and quantify the resulting cost-quality trade-offs across XAI methods and deferral regimes.

*Cost-efficient epistemic proxies:* We demonstrate that lightweight uncertainty estimators (e.g., random forest) provide sufficiently strong signals to enable reliable gating at negligible overhead relative to XAI cost.

## 2 Related Work

Our work lies at the intersection of uncertainty quantification, XAI, and AI robustness under perturbations, with a focus on tabular data. The related work can be organized in three categories.

##### Methods for Uncertainty Quantification

Uncertainty quantification (UQ) distinguishes *aleatoric uncertainty*, induced by inherent data noise, from *epistemic uncertainty*, reflecting limited model knowledge in underrepresented regions [[13](#bib.bib19 "Aleatoric and epistemic uncertainty in machine learning: an introduction to concepts and methods"), [14](#bib.bib20 "What uncertainties do we need in bayesian deep learning for computer vision?")]. For ensemble-based models, epistemic uncertainty is typically computed as prediction variance across ensemble members:

|  |  |  |  |
| --- | --- | --- | --- |
|  | 𝒰epi​(𝐱)=Varm​[fm​(y=k|𝐱)],\displaystyle\mathcal{U}\_{\text{epi}}(\mathbf{x})=\text{Var}\_{m}[f\_{m}(y=k|\mathbf{x})], |  | (1) |

Established methods include prediction variance for random forests [[30](#bib.bib24 "Aleatoric and epistemic uncertainty with random forests")], deep ensembles and MC Dropout for neural networks [[16](#bib.bib27 "Simple and scalable predictive uncertainty estimation using deep ensembles"), [12](#bib.bib28 "Dropout as a bayesian approximation: representing model uncertainty in deep learning")], surrogate-based approaches for gradient boosting [[21](#bib.bib23 "Uncertainty in gradient boosting via ensembles"), [10](#bib.bib10 "Ngboost: natural gradient boosting for probabilistic prediction")], and bootstrap resampling for linear models [[11](#bib.bib55 "An introduction to the bootstrap")].

In contrast to these works, we do not propose a new method for estimating predictive uncertainty but use the latter as a criterion for deciding how much effort is required to explain those predictions.

##### Evaluating Explanation Methods

As XAI typically cannot be simply assessed based on ground-truth explanations, and must also fulfill complex multifaceted desiderata [[34](#bib.bib62 "Explanation in second generation expert systems")], significant work has been dedicated to the question of how to assess explanation quality and usefulness, summarized in reviews such as [[26](#bib.bib63 "From anecdotal evidence to quantitative evaluation methods: a systematic review on evaluating explainable ai")]. As major families of evaluation techniques, we can mention the ‘pixel-flipping’ and insertion/deletion metrics [[29](#bib.bib64 "Evaluating the visualization of what a deep neural network has learned")], as well as measures of explanation stability [[25](#bib.bib66 "Methods for interpreting and understanding deep neural networks"), [3](#bib.bib12 "On the robustness of interpretability methods"), [23](#bib.bib7 "Evaluating the stability of semantic concept representations in cnns for robust explainability")]. Multiple works document explanation vulnerability to perturbations and adversarial attacks [[5](#bib.bib44 "Adversarial attacks and defenses in explainable artificial intelligence: a survey"), [24](#bib.bib6 "Unveiling the anatomy of adversarial attacks: concept-based xai dissection of cnns")].

In comparison to these classical methods for evaluating explanations, which often require repeatedly calling the ML model with XAI-derived input perturbations, we establish a fast surrogate that is purely based on predictive uncertainty and that can be computed quickly for single data points.

##### Connections between UQ and XAI

Recent work integrates UQ with XAI. Bayesian extensions of LIME and SHAP model explanation uncertainty internally by producing credible intervals for individual attributions [[37](#bib.bib1 "Baylime: bayesian local interpretable model-agnostic explanations"), [31](#bib.bib2 "Reliable post hoc explanations: modeling uncertainty in explainability")]; a broader review of UQ modeling and human perception of uncertainty in explanations is provided in [[9](#bib.bib3 "Uncertainty in xai: human perception and modeling approaches")]. Uncertainty decomposition can guide both explanation rejection and explanation type selection [[38](#bib.bib36 "Robust explanations through uncertainty decomposition: a path to trustworthier ai")]. Uncertainty-aware explanations reduce interpretation biases in healthcare [[28](#bib.bib37 "Explainability and uncertainty: two sides of the same coin for enhancing the interpretability of deep learning models in healthcare")] and identify uncertainty drivers in manufacturing [[22](#bib.bib40 "Quantifying and explaining machine learning uncertainty in predictive process monitoring: an operations research perspective")]. Work on uncertainty propagation examines how perturbations in the data and model affect explanation stability [[8](#bib.bib41 "Uncertainty propagation in xai: a comparison of analytical and empirical estimators")], while [[6](#bib.bib8 "Explaining predictive uncertainty by exposing second-order effects")] proposes a method that explains the prediction uncertainty itself, by identifying input features that contribute to it.

Compared to these works, we provide a different perspective, viewing UQ as a proxy for explanation reliability, enabling both computational gains and quality-aware routing in dataset-wide XAI. Specifically, this is achieved by leveraging strong correlations between epistemic uncertainty and explanation stability and faithfulness.

## 3 Epistemic Gating for Cost-Aware XAI

In this section, we propose using epistemic uncertainty as a routing signal to allocate explanation effort based on predicted reliability.

### 3.1 The Epistemic Gating Mechanism

Post-hoc explanation methods vary in cost: KernelSHAP [[18](#bib.bib31 "A unified approach to interpreting model predictions")] requires thousands of model evaluations per sample, while TreeSHAP [[17](#bib.bib11 "From local explanations to global understanding with explainable ai for trees")] operates in polynomial time. Crucially, not all predictions require equally thorough analysis: samples in well-constrained regions yield reliable explanations with lightweight methods, whereas samples near poorly-defined decision boundaries warrant more thorough attribution. Our framework exploits this asymmetry by routing samples toward the appropriate explanation effort based on epistemic uncertainty.

We consider supervised classification settings where a model
f:ℝd→ΔKf:\mathbb{R}^{d}\to\Delta^{K} maps an input 𝐱∈ℝd\mathbf{x}\in\mathbb{R}^{d}
to a probability distribution over KK classes. Given a test sample,
we aim to assess whether the post-hoc explanation is expected to be
faithful and stable under input perturbations, and whether these
properties are predictable from the epistemic uncertainty of the prediction.

Epistemic uncertainty captures model uncertainty from limited data and insufficiently constrained parameters. We hypothesize that high epistemic uncertainty indicates regions where the decision boundary is poorly defined and explanations are prone to instability, making it a natural proxy for local model reliability and a gate for explanation resource allocation. As illustrated in Figure [1](#S3.F1 "Figure 1 ‣ 3.1 The Epistemic Gating Mechanism ‣ 3 Epistemic Gating for Cost-Aware XAI ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") (left), for each input 𝐱\mathbf{x} of model ff, epistemic uncertainty 𝒰epi​(𝐱)\mathcal{U}\_{\text{epi}}(\mathbf{x}) is compared to the threshold τ\tau to route the sample to the appropriate downstream action. For models lacking low-cost native uncertainty estimation, a lightweight Random Forest surrogate provides a stable proxy signal [[30](#bib.bib24 "Aleatoric and epistemic uncertainty with random forests")].

![Refer to caption](2603.29915v1/x1.png)

### 3.2 Dimensionality Analysis of Computational Gains

A key motivation for epistemic gating is the substantial asymmetry between uncertainty estimation and post-hoc explanation generation. Although epistemic uncertainty can typically be obtained through lightweight ensembling or stochastic inference, model-agnostic XAI techniques require orders of magnitude more model evaluations per sample, making them impractical to apply exhaustively on large datasets. To formalize this asymmetry, let mm represent the number of model evaluations required to produce an uncertainty estimate, and dd the number required to generate an explanation. If a fraction ν\nu of samples is deferred by epistemic gating, the total computational cost relative to the baseline is:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | q\displaystyle q | =md+(1−ν)\displaystyle=\frac{m}{d}+(1-\nu) |  | (2) |

If the explained model is itself an ensemble (e.g., a random forest), uncertainty estimation reduces to a byproduct of inference, improving the ratio to:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | q\displaystyle q | =1d+(1−ν)\displaystyle=\frac{1}{d}+(1-\nu) |  | (3) |

Cost improvements are drastic when starting from an expensive XAI method (large dd) and allowing a high deferral rate (large ν\nu). For example, LIME [[27](#bib.bib33 "\"Why should i trust you?\" explaining the predictions of any classifier")] requires d∼103d\sim 10^{3}–10410^{4} perturbations per sample, while MC Dropout [[12](#bib.bib28 "Dropout as a bayesian approximation: representing model uncertainty in deep learning")] requires only m∼101m\sim 10^{1}–10210^{2} forward passes, yielding m/d∼0.01m/d\sim 0.01.

More broadly, *epistemic gating ensures that high-cost explanation is incurred only where the model is uncertain*, rather than applied uniformly to all inputs.

### 3.3 Exemplary Use Cases

The right-hand side of Figure [1](#S3.F1 "Figure 1 ‣ 3.1 The Epistemic Gating Mechanism ‣ 3 Epistemic Gating for Cost-Aware XAI ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") illustrates two complementary deployment scenarios enabled by the gating mechanism.

Use Case 1: Improving Worst-Case Explanations. When explanations are required for all inputs, epistemic uncertainty guides the *choice of XAI method* rather than the decision to explain. If 𝒰epi​(𝐱)<τ\mathcal{U}\_{\text{epi}}(\mathbf{x})<\tau, a low-cost method suffices; if 𝒰epi​(𝐱)≥τ\mathcal{U}\_{\text{epi}}(\mathbf{x})\geq\tau, the sample lies near a poorly-defined decision boundary and a more thorough multi-pass method is required. This routing strategy allocates greater explanation effort precisely where reliability is hardest to achieve.

Use Case 2: Recalling High-Quality Explanations. When computational budget is limited, epistemic uncertainty serves as a *hard gate*: low-uncertainty samples proceed to XAI computation, while high-uncertainty samples are deferred, saving computation on predictions where attributions would be fragile and potentially misleading.

Beyond these cases, epistemic uncertainty can accompany any explanation as a continuous reliability indicator, helping users contextualize attributions [[36](#bib.bib4 "Effect of confidence and explanation on accuracy and trust calibration in ai-assisted decision making"), [19](#bib.bib5 "“Are you really sure?” understanding the effects of human self-confidence calibration in ai-assisted decision making")].

## 4 Experimental Setup

This section describes our experimental framework: the datasets used for evaluation, the ML models and their uncertainty estimation methods, the XAI techniques under comparison, and the stability metrics and perturbation types.

### 4.1 Datasets

We evaluate our framework on diverse sets of tabular classification benchmarks from the UCI Machine Learning Repository111<https://archive.ics.uci.edu/>, summarized in Table [1](#S4.T1 "Table 1 ‣ 4.1 Datasets ‣ 4 Experimental Setup ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence"). These datasets span binary and multi-class classification settings with varying sample sizes and feature dimensionalities, and exhibit different degrees of noise and class imbalance, providing a representative testbed for assessing the relationship between epistemic uncertainty and explanation reliability. Data are split randomly (not stratified) into training, validation, and test set (70/15/15), and features are standardized using a z-score normalization fitted on the training split.

|  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| Type | Dataset | Features | Classes | Train | Val | Test |
| Tabular | Wine Quality | 11 | 2 | 4547 | 975 | 975 |
| Dry Bean | 16 | 7 | 9527 | 2042 | 2042 |
| Rice | 7 | 2 | 2667 | 571 | 572 |
| Ecoli | 7 | 8 | 235 | 50 | 51 |
| Image | PlantVillage | 128×\times128×\times3 | 3 | 3936 | 843 | 847 |

The Wine Quality dataset combines red and white wine samples described by physicochemical properties. Quality scores are binarized into low (≤5\leq 5) and high (≥6\geq 6) classes. The Dry Bean dataset contains features of different bean varieties, 7 well-separated classes. The Rice dataset distinguishes between 2 rice varieties based on grain characteristics.
The Ecoli dataset comprises protein localization sites with 8 highly imbalanced classes.
To assess cross-domain generality of our proposed framework, we further consider an image classification task using a subset of the PlantVillage222<https://www.kaggle.com/datasets/emmarex/plantdisease> dataset containing “healthy”, “bacterial spot”, and “late blight” tomato leaf images. Images are resized to 128×128×3128\times 128\times 3 pixels and normalized to [−1,1][-1,1].

### 4.2 ML Models

To ensure architectural diversity, we train five models of different architectures: Logistic Regression (LR) serves as a linear baseline with L2-regularization (C=1.0C=1.0). Epistemic uncertainty is estimated using a bootstrap ensemble of 20 resampled models.
Random Forest (RF) consists of 100 trees with a maximum depth of 15. Epistemic uncertainty is obtained directly via prediction variance across trees.
Multi-Layer Perceptron (MLP) employs a fully-connected network with architecture d→128→64→Kd\to 128\to 64\to K, ReLU activations, and dropout rate p=0.3p=0.3 after each hidden layer. Models are trained for up to 100 epochs with Adam optimizer (learning rate 10−310^{-3}) and early stopping. Epistemic uncertainty is estimated using MC Dropout with 50 stochastic forward passes.
Gradient Boosting (GBDT): LightGBM (LGBM) and CatBoost (CB) with 200 trees, learning rate 0.1, depth 6-8. As GBDTs lack native epistemic estimates, a RF surrogate provides uncertainty signals.
For the PlantVillage dataset, we train a VGG-like CNN model composed of three convolutional blocks followed by a classification head. Each block consists of a 3×33\times 3 convolution (pad 11), ReLU activation, 2×22\times 2 max pooling, and dropout with rate p=0.3p=0.3. The number of channels increases across blocks from 32 →\to 64 →\to 128. The feature extractor is followed by global average pooling and a final linear layer producing class logits.

### 4.3 XAI Methods

We benchmark five XAI methods: SHAP (TreeExplainer / KernelExplainer) [[18](#bib.bib31 "A unified approach to interpreting model predictions"), [17](#bib.bib11 "From local explanations to global understanding with explainable ai for trees")], LIME [[27](#bib.bib33 "\"Why should i trust you?\" explaining the predictions of any classifier")], Integrated Gradients (IG) [[33](#bib.bib57 "Axiomatic attribution for deep networks")], SmoothGrad (SG) [[32](#bib.bib59 "Smoothgrad: removing noise by adding noise")], and Smooth Integrated Gradients (SIG). These methods are briefly described in Appendix [0.A](#Pt0.A1 "Appendix 0.A Explanation Methods ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence").
All explanation methods are implemented using standard and widely adopted libraries333shap: <https://github.com/shap/shap>; lime: <https://github.com/marcotcr/lime>; captum: <https://captum.ai/>, pytorch: <https://pytorch.org/> with default hyperparameters to ensure a fair comparison.
SHAP explanations are computed using TreeExplainer for tree-based models and KernelExplainer with 100 background samples for other models, reporting attributions for the predicted class only.
LIME explanations generate 5,000 perturbed samples, reporting the top 10 feature attributions.
Integrated Gradients (IG) explanations are computed using 50 integration steps from a zero baseline, with gradients taken with respect to the predicted class logit.
SmoothIG combines IG with input noise, averaging 50 noisy samples (σ=0.1\sigma=0.1) via captum’s NoiseTunnel.
SmoothGrad averages gradients over 20 noisy input samples (σ=0.1\sigma=0.1), reduced to grayscale for image data.

### 4.4 Perturbations

To simulate realistic noise, out-of-distribution effects, and distribution shifts in the input space, we apply three types of natural perturbations with controlled intensity. First, gaussian noise, which we apply to each feature independently, i.e. x~i=xi+σ⋅std​(Xi)⋅ϵi,ϵi∼𝒩​(0,1),\tilde{x}\_{i}=x\_{i}+\sigma\cdot\text{std}(X\_{i})\cdot\epsilon\_{i},\epsilon\_{i}\sim\mathcal{N}(0,1),
where std​(Xi)\text{std}(X\_{i}) is computed on the current input split (not training data) and
σ\sigma controls the perturbation strength.
Then, missing values, where individual feature entries are randomly masked with probability pp, followed by median imputation computed on the perturbed sample, simulating incomplete or corrupted measurements. Finally, permutation, which randomly permutes a fraction ff of features across samples, breaking feature-target dependencies while preserving marginal distributions.

Additionally, for MLP models, we evaluate robustness under three types of gradient-based adversarial attacks: BIM [[15](#bib.bib61 "Adversarial examples in the physical world")], PGD [[20](#bib.bib52 "Towards deep learning models resistant to adversarial attacks")], and C&W [[7](#bib.bib50 "Towards evaluating the robustness of neural networks")]. These attacks represent worst-case adversarial distribution shifts that maximally disrupt predictions while remaining imperceptible to human observers. BIM is run for 10 iterations with strength ϵ\epsilon under an ℓ∞\ell\_{\infty} constraint. The step size is set to α=0.25​ϵ\alpha=0.25\,\epsilon, following α=ϵ/niter⋅2.5\alpha=\epsilon/n\_{\text{iter}}\cdot 2.5.
PGD is run for 20 iterations with strength ϵ\epsilon and ℓ∞\ell\_{\infty} constraint. The step size is set to α=0.125​ϵ\alpha=0.125\,\epsilon using the same scaling rule. Attacks are initialized with a random start, while only a single restart is used (no multi-restart search is performed).
C&W uses an untargeted ℓ2\ell\_{2} attack with fixed parameters cc, κ=0.0\kappa=0.0, niter=100n\_{\text{iter}}=100, and learning rate 0.010.01.

### 4.5 Evaluation Metrics

To quantify explanation stability under input perturbations for tabular data, we use rank-based correlation measures, which are scale-invariant and emphasize relative feature importance.
Given a clean input 𝐱\mathbf{x} and its perturbed counterpart 𝐱~\tilde{\mathbf{x}}, we compute attributions ϕ​(𝐱)\bm{\phi}(\mathbf{x}) and ϕ​(𝐱~)\bm{\phi}(\tilde{\mathbf{x}}), then rank features by absolute attribution magnitude: Ri=rank​(|ϕi​(𝐱)|)R\_{i}=\mathrm{rank}(|\phi\_{i}(\mathbf{x})|) and R~i=rank​(|ϕi​(𝐱~)|)\tilde{R}\_{i}=\mathrm{rank}(|\phi\_{i}(\tilde{\mathbf{x}})|).
Specifically, we employ Spearman’s ρ\rho for dd features:

|  |  |  |  |
| --- | --- | --- | --- |
|  | ρ(ϕ(𝐱),ϕ(𝐱~))=1−6​∑i=1d(Ri−R~i)2d​(d2−1),∈[−1,1],\displaystyle\rho(\bm{\phi}(\mathbf{x}),\bm{\phi}(\tilde{\mathbf{x}}))=1-\frac{6\sum\_{i=1}^{d}(R\_{i}-\tilde{R}\_{i})^{2}}{d(d^{2}-1)},\quad\in[-1,1], |  | (4) |

and Kendall’s τ\tau:

|  |  |  |  |
| --- | --- | --- | --- |
|  | τ(ϕ(𝐱),ϕ(𝐱~))=C−D(d2),∈[−1,1],\displaystyle\tau(\bm{\phi}(\mathbf{x}),\bm{\phi}(\tilde{\mathbf{x}}))=\frac{C-D}{\binom{d}{2}},\quad\in[-1,1], |  | (5) |

where C=|{(i,j):(Ri−Rj)​(R~i−R~j)>0}|C=|\{(i,j):(R\_{i}-R\_{j})(\tilde{R}\_{i}-\tilde{R}\_{j})>0\}| counts concordant pairs and D=|{(i,j):(Ri−Rj)​(R~i−R~j)<0}|D=|\{(i,j):(R\_{i}-R\_{j})(\tilde{R}\_{i}-\tilde{R}\_{j})<0\}| discordant.

While Spearman’s ρ\rho captures global rank consistency, Kendall’s τ\tau is more sensitive to local rank inversions. We use Kendall’s τ\tau for the stability of feature rankings in individual explanations, and Spearman’s ρ\rho for global trends where the overall monotonic change matters more than individual swaps.
For both metrics we use scipy’s implementation.

In contrast to tabular data, images are inherently spatial and, therefore, we quantify stability using structural similarity (SSIM):

|  |  |  |  |
| --- | --- | --- | --- |
|  | SSIM(A,B)=(2​μA​μB+c1)​(2​σA​B+c2)(μA2+μB2+c1)​(σA2+σB2+c2),∈[0,1],\displaystyle\text{SSIM}(A,B)=\frac{(2\mu\_{A}\mu\_{B}+c\_{1})(2\sigma\_{AB}+c\_{2})}{(\mu\_{A}^{2}+\mu\_{B}^{2}+c\_{1})(\sigma\_{A}^{2}+\sigma\_{B}^{2}+c\_{2})},\quad\in[0,1], |  | (6) |

where μ\mu, σ2\sigma^{2}, σA​B\sigma\_{AB} denote local means (luminance), variances (contrast), and covariance (structure), and c1c\_{1}, c2c\_{2} are stabilization constants.

## 5 Experimental Results

This section reports experimental results evaluating the relationship between epistemic uncertainty and explanation stability, as well as the effectiveness of uncertainty-based gating.

### 5.1 UQ Models performance

Predictive performance and uncertainty statistics of all models are summarized in Table [2](#S5.T2 "Table 2 ‣ 5.1 UQ Models performance ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence"). Introducing uncertainty quantification does not materially affect predictive performance: F1 scores of UQ-enabled models closely match those of their deterministic counterparts across all datasets and architectures.

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| Dataset | Model | F1 (Non-UQ) | F1 (UQ) | Epistemic | CVepi\text{CV}\_{\text{epi}} |
| Wine | LR | 0.736 | 0.733 | 0.0004 | 1.40 |
|  | RF | 0.810 | 0.810 | 0.083 | 0.50 |
|  | MLP | 0.764 | 0.773 | 0.023 | 0.71 |
|  | LGBM | 0.808 | 0.806 | – | – |
|  | CB | 0.780 | 0.780 | – | – |
| Bean | LR | 0.921 | 0.923 | 0.0001 | 3.71 |
|  | RF | 0.925 | 0.925 | 0.0083 | 1.57 |
|  | MLP | 0.936 | 0.935 | 0.026 | 1.41 |
|  | LGBM | 0.930 | 0.930 | – | – |
|  | CB | 0.931 | 0.931 | – | – |
| Rice | LR | 0.921 | 0.923 | 0.0003 | 2.21 |
|  | RF | 0.919 | 0.919 | 0.026 | 1.44 |
|  | MLP | 0.930 | 0.921 | 0.0066 | 1.12 |
|  | LGBM | 0.918 | 0.916 | – | – |
|  | CB | 0.916 | 0.916 | – | – |
| Ecoli | LR | 0.842 | 0.875 | 0.0016 | 2.25 |
|  | RF | 0.845 | 0.845 | 0.0197 | 0.74 |
|  | MLP | 0.869 | 0.869 | 0.044 | 0.71 |
|  | LGBM | 0.824 | 0.809 | – | – |
|  | CB | 0.841 | 0.841 | – | – |

In addition to mean epistemic uncertainty, we characterize how uncertainty is distributed across samples using the *epistemic coefficient of variation*

|  |  |  |
| --- | --- | --- |
|  | CVepi=std​(𝒰epi)/mean​(𝒰epi).\text{CV}\_{\text{epi}}=\mathrm{std}(\mathcal{U}\_{\text{epi}})~/~\mathrm{mean}(\mathcal{U}\_{\text{epi}}). |  |

Importantly, CVepi\mathrm{CV}\_{\mathrm{epi}} does not quantify how uncertain a model is on average, instead, it captures whether epistemic uncertainty is discriminative across the input space. High values indicate that uncertainty varies substantially between samples, separating regions where the model’s predictions are epistemically well-determined from regions where they are not. In contrast, low values indicate a near-uniform uncertainty landscape in which the model is similarly uncertain.
This distinction is crucial for uncertainty-aware explainability. Epistemic uncertainty can only serve as a validity signal for explanations if it can be used to meaningfully discriminate between samples. When epistemic uncertainty is highly scattered (high CVepi\mathrm{CV}\_{\mathrm{epi}}), it localizes regions of epistemic indeterminacy, enabling stratification into reliable and unreliable explanation regimes. When dispersion is low (low CVepi\mathrm{CV}\_{\mathrm{epi}}), epistemic uncertainty collapses to an almost uniform uncertainty landscape, where no such separation is possible.

The Dry Bean and Rice datasets exhibit higher epistemic variation, indicating heterogeneous model confidence and well-structured decision boundaries where epistemic uncertainty meaningfully separates samples. In contrast, lower epistemic variation in Wine Quality and Ecoli suggests that uncertainty is dominated by intrinsic data noise. In Wine, noise stems from subjective labeling, and in Ecoli from the small-sample, multi-class structure, creating a global uncertainty floor that limits the discriminative utility of epistemic uncertainty.

For LightGBM and CatBoost, native epistemic uncertainty is not reported due to architectural limitations; in subsequent experiments, epistemic uncertainty for these models is obtained via a Random Forest surrogate.

These observations provide context for the following experiments, which investigate when epistemic uncertainty can reliably predict explanation stability and when its utility is limited by dataset noise characteristics.

### 5.2 XAI-UQ correlation analysis

In the following we examine whether epistemic uncertainty provides a reliable signal of explanation stability. Therefore, we analyze the relationship between changes in epistemic growth and degradation of post-hoc explanations under controlled perturbations. This analysis tests the central premise of uncertainty-aware explainability: that epistemic uncertainty increases precisely in regimes where explanations become unstable.
For each dataset, model, and XAI method, correlations are computed on a fixed test subset of size n=min⁡(100,|Xtest|)n=\min(100,|X\_{\text{test}}|) (sampled once with a fixed random seed) and shared across all perturbation strengths to ensure comparability.
The perturbation levels are denoted by λ∈Λ\lambda\in\Lambda. The levels are set as follows for the different types:

Gaussian noise scale Λ≡σ∈{0.01,0.05,0.1,0.3,0.5,1.0,2.0}\Lambda\equiv\sigma\in\{0.01,0.05,0.1,0.3,0.5,1.0,2.0\},

Missing values rate Λ≡p∈{0.01,0.05,0.1,0.2,0.3,0.4,0.5}\Lambda\equiv p\in\{0.01,0.05,0.1,0.2,0.3,0.4,0.5\},

Feature permutation fraction Λ≡f∈{0.01,0.02,0.05,0.1,0.15,0.2,0.25}\Lambda\equiv f\in\{0.01,0.02,0.05,0.1,0.15,0.2,0.25\},

BIM/PGD attack strength Λ≡ϵ∈{0.01,0.05,0.1,0.2}\Lambda\equiv\epsilon\in\{0.01,0.05,0.1,0.2\},

C&W regularization parameter Λ≡c∈{0.1,1.0,10.0}\Lambda\equiv c\in\{0.1,1.0,10.0\}.

Explanation degradation (ED) is quantified by Kendall’s τ\tau (Eq. [5](#S4.E5 "Equation 5 ‣ 4.5 Evaluation Metrics ‣ 4 Experimental Setup ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")) between attributions of clean inputs 𝐱i\mathbf{x}\_{i} and their perturbed counterparts 𝐱~i(λ)\tilde{\mathbf{x}}\_{i}^{(\lambda)} at level λ\lambda, averaged across nn samples:

|  |  |  |  |
| --- | --- | --- | --- |
|  | X​D​(λ)=1n​∑i=1nτ​(ϕ​(𝐱i),ϕ​(𝐱~i(λ))),\displaystyle XD(\lambda)=\frac{1}{n}\sum\_{i=1}^{n}\tau\!\left(\bm{\phi}(\mathbf{x}\_{i}),\bm{\phi}(\tilde{\mathbf{x}}\_{i}^{(\lambda)})\right), |  | (7) |

To capture the response of epistemic uncertainty to perturbations, we define epistemic growth (EG) as the relative increase444Alternatively, E​G​(λ)=1n​∑i=1n𝒰epi​(𝐱~i(λ))EG(\lambda)=\frac{1}{n}\sum\_{i=1}^{n}\mathcal{U}\_{\text{epi}}(\tilde{\mathbf{x}}\_{i}^{(\lambda)}) – absolute values yield identical XEC since Spearman’s ρ\rho operates on ranks; the ratio aids human interpretability. in mean epistemic uncertainty under perturbation:

|  |  |  |  |
| --- | --- | --- | --- |
|  | E​G​(λ)=∑i=1n𝒰epi​(𝐱~i(λ))∑i=1n𝒰epi​(𝐱i),\displaystyle EG(\lambda)=\frac{\sum\_{i=1}^{n}\mathcal{U}\_{\text{epi}}(\tilde{\mathbf{x}}\_{i}^{(\lambda)})}{\sum\_{i=1}^{n}\mathcal{U}\_{\text{epi}}(\mathbf{x}\_{i})}, |  | (8) |

Finally, for each perturbation type, we quantify the explanation-epistemic correlation (XEC) between XD and EG by computing the Spearman rank correlation ρ\rho (Eq. [4](#S4.E4 "Equation 4 ‣ 4.5 Evaluation Metrics ‣ 4 Experimental Setup ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")) across all perturbation levels Λ\Lambda:

|  |  |  |  |
| --- | --- | --- | --- |
|  | X​E​C​(Λ)=ρ​(X​D​(Λ),E​G​(Λ)),\displaystyle XEC(\Lambda)=\rho\big(XD(\Lambda),EG(\Lambda)\big), |  | (9) |

A strongly negative correlation indicates that epistemic uncertainty consistently increases as explanations degrade. Throughout, we consider X​E​C<−0.6XEC<-0.6 as indicative of a strong negative association, suggesting that UQ reliably predicts XAI degradation.

![Refer to caption](2603.29915v1/x2.png)

Figure [2](#S5.F2 "Figure 2 ‣ 5.2 XAI-UQ correlation analysis ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") summarizes the relationship between XAI stability and epistemic uncertainty across datasets, models, explanation methods, and perturbation regimes. Across nearly all settings, a strong negative association between EG and XD is observed, indicating that epistemic uncertainty systematically increases in regimes where explanations become fragile. This consistency across perturbation types and data modalities demonstrates that epistemic uncertainty captures a fundamental aspect of explanation robustness rather than a method- or perturbation-specific artifact.

Overall, SHAP yields stronger XEC than LIME, while Integrated Gradients consistently outperforms SmoothGrad among gradient-based methods. Across models and perturbation types, SHAP is the most reliable baseline, motivating its use in subsequent experiments.

Permutation perturbations yield the weakest correlations (XEC>−0.6\text{XEC}>-0.6 frequently). This behavior is expected, as feature permutation induces non-additive distribution shifts that explicitly disrupt feature-target dependencies.

For GBDTs (LightGBM and CatBoost), epistemic uncertainty was estimated via a RF surrogate. XEC remained strong and comparable to models with native epistemic estimates, indicating that the surrogate provides a sufficiently informative and stable epistemic signal.

Furthermore, dataset-specific effects are also observed. Ecoli exhibits weaker correlations than Wine, Bean, and Rice, which is consistent with its small sample size, multi-class structure, and higher intrinsic noise.
These challenging characteristics limit the dispersion of epistemic uncertainty and, consequently, its ability to discriminate between stable and unstable explanation regimes.

Under adversarial perturbations, the overall XEC signal remains clearly negative. A mild weakening is observed for LIME, likely due to internal sampling noise partially reducing adversarial effects.

Together, these results establish epistemic uncertainty as a robust indicator for explanation instability across models, explanation methods, and perturbation methods. Based on these findings, subsequent experiments focus primarily on RF-based models, the Wine, Bean, and Rice datasets, SHAP explanations, and Gaussian noise as a canonical perturbation. Other models and perturbation types are retained selectively for comparative analysis.

### 5.3 Stratified validation

In the following, we perform a stratified validation to assess whether epistemic uncertainty provides a meaningful proxy for explanation robustness at the level of individual predictions.
While the previous correlation analysis established a global association between epistemic uncertainty and explanation instability (EG vs XD), we now test the stronger condition required for uncertainty-aware explainability: whether samples with higher epistemic uncertainty exhibit systematically stronger explanation degradation under input perturbations compared to low-epistemic samples.

For each sufficiently large dataset (Wine, Dry Bean, Rice), epistemic uncertainty is computed on the clean test set using the RF-based uncertainty model. The Ecoli dataset is excluded due to insufficient sample size for reliable stratification. Test samples are then stratified into three epistemic groups using quantile-based binning with equal-sized bins over the empirical epistemic uncertainty distribution, corresponding to low, medium, and high epistemic regimes. From each group, 50 samples are randomly selected.

For each selected sample, SHAP explanations are computed for the clean input and for the perturbed inputs obtained by adding Gaussian noise with σ∈{0.01,0.05,0.1}\sigma\in\{0.01,0.05,0.1\} across 10 noise seeds. Explanation stability is measured per sample using Kendall’s τ\tau (Eq. [5](#S4.E5 "Equation 5 ‣ 4.5 Evaluation Metrics ‣ 4 Experimental Setup ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")) between the rankings of absolute attributions and averaged across noise seeds.

Figure [3](#S5.F3 "Figure 3 ‣ 5.3 Stratified validation ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") reports stratified SHAP explanation stability across epistemic uncertainty strata (low, medium, high) under increasing Gaussian noise levels.
For each dataset and σ\sigma, violin plots show the distribution of SHAP τ\tau values within each epistemic group.

![Refer to caption](2603.29915v1/x3.png)

Across all datasets and noise levels, we observe low >> medium ≫\gg high consistently.
As perturbation strength increases (σ=0.01→0.1\sigma=0.01\rightarrow 0.1, top →\rightarrow bottom rows), overall τ\tau decreases for all groups. Samples with low epistemic uncertainty exhibit the most stable explanations, medium-epistemic samples show moderate degradation, and high-epistemic samples consistently display substantially reduced stability. As perturbation strength increases (σ=0.01→0.1\sigma=0.01\rightarrow 0.1), explanation stability decreases across all groups, however, the τ\tau degradation is markedly stronger for the high epistemic group.

Overall, these results provide sample-level evidence that epistemic uncertainty reliably serves as a proxy for explanation fragility: samples identified as epistemically uncertain are systematically associated with less stable SHAP explanations, justifying the use of epistemic uncertainty as a routing signal for explanation effort allocation.

### 5.4 Recalling High-Quality Explanations

In realistic deployment scenarios, the magnitude and nature of input perturbations are typically unknown. To simulate this uncertainty, we evaluate epistemic gating under mixed perturbation conditions. Therefore, we consider 500 test samples over 10 noise levels σ∈{0.02×k}k=110\sigma\in\{0.02\times k\}\_{k=1}^{10}. For each σ\sigma, we generate 5 perturbed versions per sample and average RF epistemic uncertainty (computed on perturbed inputs) and SHAP τ\tau (Eq. [5](#S4.E5 "Equation 5 ‣ 4.5 Evaluation Metrics ‣ 4 Experimental Setup ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")) across seeds, using clean SHAP ranks as the reference. The resulting mixed-noise population (5000 samples), formed by concatenating these per-σ\sigma averaged samples, is used for evaluation.

##### Deferral-stability trade-off.

Filtering by epistemic uncertainty introduces a fundamental trade-off: higher deferral rate ν\nu (see Sec. [3.2](#S3.SS2 "3.2 Dimensionality Analysis of Computational Gains ‣ 3 Epistemic Gating for Cost-Aware XAI ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")) yields higher-quality explanations but fewer of them.
A qualitative view of this trade-off, illustrating stable and unstable explanations as a function of epistemic uncertainty, is provided in Appendix [0.B](#Pt0.A2 "Appendix 0.B Epistemic Uncertainty vs. XAI stability ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence"). To quantify this, we label samples as stable if τ≥0.7\tau\geq 0.7 and unstable otherwise. We then evaluate epistemic-based filtering at various deferral rates ν∈[0.1,0.9]\nu\in[0.1,0.9]: at ν\nu, we reject samples with epistemic uncertainty above the ν\nu-th percentile of the epistemic distribution.

Table [3](#S5.T3 "Table 3 ‣ Deferral-stability trade-off. ‣ 5.4 Recalling High-Quality Explanations ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") quantifies the precision-recall trade-off across deferral rates. In human-facing applications where explanation reliability is critical, precision is typically prioritized: at 50% deferral, Bean and Rice achieve near-perfect precision (99.6% and 100%), while Wine reaches 73.5%. Lower ν\nu increases recall at the cost of precision, allowing practitioners to tune the trade-off based on their tolerance for unreliable explanations.

|  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | Wine | | Bean | | Rice | |
| ν\nu | Prec. | Rec. | Prec. | Rec. | Prec. | Rec. |
| 90% | 0.932 | 0.144 | 1.000 | 0.123 | 1.000 | 0.114 |
| 70% | 0.788 | 0.367 | 1.000 | 0.370 | 1.000 | 0.342 |
| 50% | 0.735 | 0.570 | 0.996 | 0.614 | 1.000 | 0.570 |
| 30% | 0.687 | 0.746 | 0.989 | 0.854 | 0.998 | 0.797 |
| 10% | 0.648 | 0.904 | 0.890 | 0.987 | 0.937 | 0.962 |

##### Computational cost analysis.

Beyond indicating explanation reliability, epistemic gating directly reduces computational cost by avoiding the computation of explanations for predictions that are epistemically ill-posed. The cost reduction depends on the relative cost of uncertainty estimation and explanation generation (see our dimensionality analysis in Section [3.2](#S3.SS2 "3.2 Dimensionality Analysis of Computational Gains ‣ 3 Epistemic Gating for Cost-Aware XAI ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")). Here we consider two representative scenarios:

RF with TreeSHAP: Epistemic uncertainty (tree variance) is a byproduct of prediction, so m/d≈0m/d\approx 0 in Eq. ([3](#S3.E3 "Equation 3 ‣ 3.2 Dimensionality Analysis of Computational Gains ‣ 3 Epistemic Gating for Cost-Aware XAI ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")). Cost reduction simplifies to q=1/d+(1−ν)≈(1−ν)q=1/d+(1-\nu)\approx(1-\nu).

MLP with LIME: MC Dropout requires m=50m{=}50 forward passes, while LIME requires d=5000d{=}5000 perturbations. From Eq. ([2](#S3.E2 "Equation 2 ‣ 3.2 Dimensionality Analysis of Computational Gains ‣ 3 Epistemic Gating for Cost-Aware XAI ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")), m/d=0.01m/d=0.01, making filtering highly cost-effective.

To quantify the trade-off between explanation stability and cost, we evaluate both configurations on the same mixed-noise population.
Table [4](#S5.T4 "Table 4 ‣ Computational cost analysis. ‣ 5.4 Recalling High-Quality Explanations ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") reports mean stability and relative cost qq at varying deferral rates ν\nu. Filtering does not degrade explanation quality; mean stability increases as deferral rate grows, confirming that epistemic gating preferentially retains high-quality explanations.

For RF with TreeSHAP, rejecting ν=50%\nu=50\% of samples halves cost while improving stability from 0.740 to 0.777 (Wine), 0.821 to 0.937 (Bean), and 0.879 to 0.965 (Rice). Gains are largest for Bean and Rice where epistemic uncertainty is most discriminative (higher CVepi\text{CV}\_{\text{epi}}, cf. Table [2](#S5.T2 "Table 2 ‣ 5.1 UQ Models performance ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")).

For MLP with LIME, stability improvements are smaller; Wine exhibits near-constant stability across deferral rates, reflecting weaker epistemic signal. Nonetheless, ν=0.5\nu=0.5 achieves twofold cost reduction without degrading quality.

Overall, epistemic gating enables a controllable trade-off between deferral rate, quality, and computational cost. This also motivates Use Case 1: the same monotonic relationship supports routing high-uncertainty samples to more thorough XAI methods rather than applying expensive methods uniformly.

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
|  |  | RF + TreeSHAP | | MLP + LIME | |
| Dataset | ν\nu | Stability (τ\tau) | qq | Stability (τ\tau) | qq |
| Wine | 70% | 0.797±0.1210.797\pm 0.121 | 0.30 | 0.722±0.1060.722\pm 0.106 | 0.31 |
|  | 50% | 0.777±0.1300.777\pm 0.130 | 0.50 | 0.725±0.1080.725\pm 0.108 | 0.51 |
|  | 30% | 0.758±0.1410.758\pm 0.141 | 0.70 | 0.729±0.1080.729\pm 0.108 | 0.71 |
|  | 0% | 0.740±0.1490.740\pm 0.149 | 1.00 | 0.747±0.1070.747\pm 0.107 | 1.00 |
| Bean | 70% | 0.959±0.0310.959\pm 0.031 | 0.30 | 0.712±0.1200.712\pm 0.120 | 0.31 |
|  | 50% | 0.937±0.0500.937\pm 0.050 | 0.50 | 0.692±0.1440.692\pm 0.144 | 0.51 |
|  | 30% | 0.908±0.0720.908\pm 0.072 | 0.70 | 0.669±0.1560.669\pm 0.156 | 0.71 |
|  | 0% | 0.821±0.1790.821\pm 0.179 | 1.00 | 0.635±0.1650.635\pm 0.165 | 1.00 |
| Rice | 70% | 0.976±0.0340.976\pm 0.034 | 0.30 | 0.828±0.1090.828\pm 0.109 | 0.31 |
|  | 50% | 0.965±0.0420.965\pm 0.042 | 0.50 | 0.811±0.1200.811\pm 0.120 | 0.51 |
|  | 30% | 0.947±0.0580.947\pm 0.058 | 0.70 | 0.787±0.1320.787\pm 0.132 | 0.71 |
|  | 0% | 0.879±0.1500.879\pm 0.150 | 1.00 | 0.751±0.1510.751\pm 0.151 | 1.00 |

### 5.5 Explanation Quality: Feature removal sensitivity

The preceding experiments establish epistemic uncertainty as a reliable proxy for explanation stability. We now test via feature removal whether this extends to *faithfulness*: low-epistemic explanations may not only be more stable but also more *faithful*, identifying features that genuinely drive model predictions.
We address this explanation faithfulness through a feature removal experiment, by consecutively removing features that were correctly identified by SHAP as important features, which should substantially change the model’s output. A complementary noise-attribution experiment, testing whether explanations focus on the signal rather than the noise, is reported in Appendix [0.C](#Pt0.A3 "Appendix 0.C Explanation Quality: Noise feature attribution ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence").

For each epistemic group (lowest, highest, random; 50 samples each), we compute SHAP attributions and successively remove the top-kk (k∈{1,…,5}k\in\{1,\ldots,5\}) features by replacing their values with the training set median and measured the corresponding prediction shift with MSE.
To avoid saturation effects in the probability space, where highly confident predictions show negligible probability changes despite meaningful decision boundary shifts, we compute MSE in log-odds space rather than probability space.

From Figure [4](#S5.F4 "Figure 4 ‣ 5.5 Explanation Quality: Feature removal sensitivity ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") we can observe that low-epistemic samples exhibit substantially higher prediction shifts than high-epistemic or random samples across all configurations. This indicates that SHAP attributions for low-epistemic samples correctly identify features that are genuinely important for model predictions. In contrast, high-epistemic samples show minimal prediction shifts, indicating that their explanations do not reliably capture the important features.

![Refer to caption](2603.29915v1/x4.png)

Together, the feature removal and noise attribution experiments demonstrate that epistemic uncertainty separates not only *stable* from *unstable* explanations, but also *faithful* from *unfaithful* ones. Low-epistemic explanations focus on signal features and reliably identify decision-relevant features, whereas high-epistemic explanations lack this semantic validity.

### 5.6 Cross-Domain Validation: Image Classification

The preceding experiments establish a robust relationship between epistemic uncertainty and explanation stability for tabular data. To assess whether this relationship generalizes beyond tabular settings, we performed a cross-domain validation. We use the subset of PlantVillage dataset and CNN model described in Sections [4.1](#S4.SS1 "4.1 Datasets ‣ 4 Experimental Setup ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") and [4.2](#S4.SS2 "4.2 ML Models ‣ 4 Experimental Setup ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence"). Epistemic uncertainty is estimated via MC Dropout with 50 stochastic forward passes, computed as the variance of softmax probabilities. For explanations, we use Integrated Gradients and SmoothGrad (Sec. [4.3](#S4.SS3 "4.3 XAI Methods ‣ 4 Experimental Setup ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence"); SG with vanilla gradients). Attribution stability is measured using SSIM (Eq. [6](#S4.E6 "Equation 6 ‣ 4.5 Evaluation Metrics ‣ 4 Experimental Setup ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")) between clean and noisy saliency maps.
For the evaluation, we sample 100 test images and apply Gaussian noise at levels σ∈{0,0.025,0.05,0.075,0.1,0.15,0.2}\sigma\in\{0,0.025,0.05,0.075,0.1,0.15,0.2\}. Similarly to XEC (Eq. [9](#S5.E9 "Equation 9 ‣ 5.2 XAI-UQ correlation analysis ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence"), using SSIM as a measure of stability), for each σ\sigma, we compute mean epistemic uncertainty and mean SSIM, then measure their correlation across the different σ\sigma using Spearman’s ρ\rho.

##### Aggregate correlation.

Figure [5](#S5.F5 "Figure 5 ‣ Aggregate correlation. ‣ 5.6 Cross-Domain Validation: Image Classification ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") shows the relationship between epistemic uncertainty and attribution stability for increasing noise levels. Epistemic uncertainty increases monotonically with an increasing noise level, while SSIM decreases correspondingly for both explanation methods. The XEC (Eq. [9](#S5.E9 "Equation 9 ‣ 5.2 XAI-UQ correlation analysis ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")) between mean epistemic and mean SSIM across noise levels is ρ=−1.0\rho=-1.0 for both IG and SG, indicating perfect negative rank correlation.

![Refer to caption](2603.29915v1/x5.png)

##### Qualitative analysis.

Figure [6](#S5.F6 "Figure 6 ‣ Qualitative analysis. ‣ 5.6 Cross-Domain Validation: Image Classification ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") visualizes saliency maps at epistemic extremes. Samples with low epistemic uncertainty (<2.5×10−3<2.5\times 10^{-3}) produce semantically coherent attributions (leaf venation for “healthy”, lesion regions for “blight”). This pattern is stable even under perturbation (SSIM>0.47\text{SSIM}>0.47 at σ=0.2\sigma{=}0.2). High-epistemic samples (>4×10−2>4\times 10^{-2}) show diffuse saliency even on clean inputs and degrade rapidly (SSIM≈0.3\text{SSIM}\approx 0.3 at σ=0.2\sigma{=}0.2), reinforcing uncertainty as a reliability indicator.

![Refer to caption](2603.29915v1/x6.png)

The consistency across data modalities, model architectures, explanation methods, and stability metrics confirms that epistemic uncertainty generalizes as a predictor of explanation quality.

## 6 Discussion and Conclusion

This work addresses a largely overlooked question in Explainable AI: not how to evaluate explanations once they have been produced, but how much computational effort explanation generation warrants.
We introduce a framework that leverages epistemic uncertainty as a low-cost proxy for explanation reliability, enabling uncertainty-guided selective explanation generation across XAI methods.
Experiments across four tabular datasets, five model architectures, multiple XAI methods, and diverse perturbation types demonstrate that epistemic uncertainty reliably predicts explanation degradation.
Stratified validation confirms that samples with high epistemic uncertainty exhibit systematically lower explanation stability, while quality experiments show that explanations of low-epistemic samples focus on signal features and faithfully capture model behavior.
These findings generalize beyond tabular data as shown on an image classification task with CNNs and gradient-based explanations.
Together these results establish epistemic uncertainty as a reliability signal for post-hoc explanation methods. Specifically, our framework supports two deployment modes:
First, epistemic uncertainty guides adaptive method selection, routing samples to low- or high-cost XAI methods based on expected reliability. Second, under constrained budget, it serves as a hard gate triggering explanation computation only when explanations are expected to be meaningful.

Our analysis also highlights the limitations of uncertainty-aware explainability.
In datasets where epistemic uncertainty exhibits low dispersion, quantified by a low epistemic coefficient of variation, uncertainty only provides weak separation between stable and unstable XAI samples.
Permutation perturbations yield weaker XAI-UQ correlations due to non-additive distribution shifts that break feature dependencies.
The uncertainty threshold is not universal across use cases and requires per-dataset calibration, though statistical approaches (e.g., percentile-based) offer reasonable defaults.
Finally, this work focuses exclusively on classification; extension to other tasks remains to be explored.

In practice, the value of epistemic gating depends on the context. For inexpensive methods like TreeSHAP, filtering may add unnecessary complexity, but for costly methods like LIME, or when combining multiple explainers, the savings become substantial.
Lightweight RF epistemic surrogates work well when native epistemic estimation is unavailable or too expensive (e.g., GBDTs [[21](#bib.bib23 "Uncertainty in gradient boosting via ensembles")]). However, the surrogate captures data-space uncertainty of a different model class rather than the target model’s parameter uncertainty; in regions where RF and GBDT decision boundaries diverge, gating decisions may be unreliable.
The rejection rate is best treated as an engineering knob rather than a fixed threshold.
And even when full coverage is needed, uncertainty remains useful: it can accompany each explanation as a trust indicator, letting users judge reliability for themselves.

In summary, epistemic uncertainty separates explanations not only by their stability but also by their epistemic validity. Predictions with high epistemic uncertainty yield explanations that are fragile and unfaithful, whereas explanations based on low-epistemic uncertain predictions yield explanations that are both robust and faithful. This dual role, as both a stability predictor and a quality indicator, provides a principled foundation for uncertainty-aware explainability pipelines. We demonstrate the usefulness of our proposed framework in data modalities, model architectures, and explanation methods. It offers a practical tool for deploying reliable XAI either through adaptive method selection and epistemic gating in resource-constrained environments or as a continuous reliability indicator when full coverage is required.

#### 6.0.1 Acknowledgments

This work was funded by the Federal Ministry of Research, Technology and Space through the project REFRAME (ref. 01IS24073B), which supports research on robustness, trustworthiness, and domain adaptation of foundation models, and the project DCropS4OneHealth (ref. 16LW0528K), which investigates causal links between diversified cropping systems, agrobiodiversity, food quality, and human health in large-scale on-farm experiments. Furthermore it was funded by SpinFert, one of the Soil Mission projects within the Horizon European program (ref. 101157265).

#### 6.0.2 Disclosure of Interests

The authors have no competing interests to declare that are relevant to the content of this article.

## References

## Appendix 0.A Explanation Methods

This appendix briefly describes the post-hoc model-agnostic attribution methods considered in this paper. Formulas for computing them are provided in Table [5](#Pt0.A1.T5 "Table 5 ‣ Appendix 0.A Explanation Methods ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence").

|  |  |  |
| --- | --- | --- |
| Method | Attribution | Approach |
| SHAP [[18](#bib.bib31 "A unified approach to interpreting model predictions")] | ϕi=∑S⊆ℱ∖{i}|S|!​(|ℱ|−|S|−1)!|ℱ|!​[fS∪{i}−fS]\phi\_{i}=\sum\_{S\subseteq\mathcal{F}\setminus\{i\}}\frac{|S|!(|\mathcal{F}|-|S|-1)!}{|\mathcal{F}|!}\big[f\_{S\cup\{i\}}-f\_{S}\big] | Shapley values |
| LIME [[27](#bib.bib33 "\"Why should i trust you?\" explaining the predictions of any classifier")] | ϕi=wi∗\phi\_{i}=w\_{i}^{\*} from min𝐰​∑𝐳π𝐱​(𝐳)​(f​(𝐳)−𝐰⊤​𝐳)2\min\_{\mathbf{w}}\sum\_{\mathbf{z}}\pi\_{\mathbf{x}}(\mathbf{z})(f(\mathbf{z})-\mathbf{w}^{\top}\mathbf{z})^{2} | Local surrogate |
| IG [[33](#bib.bib57 "Axiomatic attribution for deep networks")] | ϕi=(xi−xi′)​∫01∂f​(𝐱′+α​(𝐱−𝐱′))∂xi​𝑑α\phi\_{i}=(x\_{i}-x^{\prime}\_{i})\int\_{0}^{1}\frac{\partial f(\mathbf{x}^{\prime}+\alpha(\mathbf{x}-\mathbf{x}^{\prime}))}{\partial x\_{i}}d\alpha | Path integration |
| SG/SIG [[32](#bib.bib59 "Smoothgrad: removing noise by adding noise")] | ϕi=1N​∑n=1Nϕibase​(𝐱+ϵn)\phi\_{i}=\frac{1}{N}\sum\_{n=1}^{N}\phi\_{i}^{\text{base}}(\mathbf{x}+\epsilon\_{n}) | Noise averaging |

SHAP computes Shapley values from cooperative game theory, where ℱ\mathcal{F} denotes the feature set and fS​(𝐱)f\_{S}(\mathbf{x}) the model prediction with only features in SS present. TreeSHAP [[17](#bib.bib11 "From local explanations to global understanding with explainable ai for trees")] provides exact polynomial-time computation for tree models, while KernelSHAP [[18](#bib.bib31 "A unified approach to interpreting model predictions")] approximates values for black-box models via weighted regression.
LIME [[27](#bib.bib33 "\"Why should i trust you?\" explaining the predictions of any classifier")] fits a weighted linear model to perturbed inputs, where π𝐱​(𝐳)\pi\_{\mathbf{x}}(\mathbf{z}) weights samples by proximity. The learned coefficients wj∗w\_{j}^{\*} serve as attributions.
Integrated Gradients (IG) [[33](#bib.bib57 "Axiomatic attribution for deep networks")] accumulates gradients along a straight path from baseline 𝐱′\mathbf{x}^{\prime} (typically zero) to 𝐱\mathbf{x}, satisfying completeness and sensitivity axioms.
SmoothGrad (SG) [[32](#bib.bib59 "Smoothgrad: removing noise by adding noise")] and Smooth Integrated Gradients (SIG) reduce noise by averaging attributions over NN noisy input copies, where ϵn∼𝒩​(0,σ2​I)\epsilon\_{n}\sim\mathcal{N}(0,\sigma^{2}I) is Gaussian noise and ϕbase\phi^{\text{base}} is vanilla gradients (SG) or IG (SIG). We use SIG for tabular data and SG for images.

## Appendix 0.B Epistemic Uncertainty vs. XAI stability

This appendix provides a qualitative visualization of the coverage-stability trade-off discussed in Section [5.4](#S5.SS4 "5.4 Recalling High-Quality Explanations ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence"). In Figure [7](#Pt0.A2.F7 "Figure 7 ‣ Appendix 0.B Epistemic Uncertainty vs. XAI stability ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") the relationship between epistemic uncertainty and explanation stability under pooled noise conditions for Wine and Bean is illustrated, representing weak and strong epistemic separation. Rice (not shown) behaves similarly to Bean. For the Bean dataset, we can observe a clear separation: stable samples concentrate at low epistemic values, and deferral rate ν=50%\nu=50\% retains almost exclusively stable explanations. Wine shows a more diffuse pattern due to higher intrinsic noise (lower CVepi\text{CV}\_{\text{epi}} cf. Table [2](#S5.T2 "Table 2 ‣ 5.1 UQ Models performance ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")), though filtering still improves stability of the accepted set.

![Refer to caption](2603.29915v1/x7.png)

.

## Appendix 0.C Explanation Quality: Noise feature attribution

Here we complement the feature removal analysis (Section [5.5](#S5.SS5 "5.5 Explanation Quality: Feature removal sensitivity ‣ 5 Experimental Results ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence")) by testing whether epistemic uncertainty also affects the *focus* of explanations. Specifically, we examine whether high-epistemic samples spuriously attribute importance to irrelevant noise features. Therefore, each dataset is augmented with synthetic Gaussian noise features at varying ratios (1:1 to 10:1 noise-to-signal features for RF, 1:1 to 3:1 for LR). Models are retrained on the augmented data, and SHAP explanations are computed for three stratified epistemic groups: low, high, and random (50 test samples per group).

Attribution focus is quantified by the *signal mass* – the fraction of total absolute SHAP attribution assigned to original (signal) features:

|  |  |  |  |
| --- | --- | --- | --- |
|  | Signal Mass=∑i∈𝒮|ϕi|∑i=1d|ϕi|,\displaystyle\text{Signal Mass}=\frac{\sum\_{i\in\mathcal{S}}|\phi\_{i}|}{\sum\_{i=1}^{d}|\phi\_{i}|}, |  | (10) |

where 𝒮\mathcal{S} denotes the set of signal feature indices. Higher signal mass indicates that explanations correctly focus on predictive features rather than noise.

Figure [8](#Pt0.A3.F8 "Figure 8 ‣ Appendix 0.C Explanation Quality: Noise feature attribution ‣ Uncertainty Gating for Cost-Aware Explainable Artificial Intelligence") reports signal and noise attribution mass across epistemic groups, noise ratios, datasets, and models. Low-epistemic samples consistently maintain higher signal mass, indicating that their explanations better focus on predictive features. In contrast, high-epistemic samples show substantial drift toward noise features. Random samples fall between the two groups, as expected.
These results explain *why* low-epistemic explanations are more stable: they rely on genuine data patterns rather than spurious correlations with noise. When perturbations are applied, explanations grounded in signal features remain consistent, while those drifting toward noise are inherently fragile.

![Refer to caption](2603.29915v1/x8.png)
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
