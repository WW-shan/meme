# Action Policy Meta-Label Research

## Question

Can the next live-model improvement be framed as a replay-equivalent action-policy / meta-label problem that combines accepted trade paths and rejected fast-profit or fast-collapse candidates, with support gates and off-policy evaluation, instead of another global threshold tweak?

## SmartSearch Commands

- `smart-search doctor --format json`
- `smart-search deep "Live meme-token trading bot action-policy meta-labeling: how to combine accepted trade paths and rejected fast-profit / fast-collapse candidates into a replay-equivalent take/skip/quick-profit policy with support gates, decision-time features, off-policy evaluation, and leakage-safe walk-forward validation" --budget deep --format json --output docs/research/20260525-action-policy-meta-label/plan.json`
- `smart-search search "action policy meta-labeling triple barrier off-policy evaluation trade selection rejected candidates accepted trades support gates" --validation balanced --extra-sources 3 --timeout 120 --format json --output docs/research/20260525-action-policy-meta-label/01-search.json`
- `smart-search zhipu-search "交易 meta-labeling triple barrier off-policy evaluation action policy 支持门槛" --count 5 --format json --output docs/research/20260525-action-policy-meta-label/02-zhipu.json`
- `smart-search exa-search "meta labeling triple barrier off policy evaluation trading action policy support constraints" --num-results 5 --format json --output docs/research/20260525-action-policy-meta-label/03-exa.json`
- `smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260525-action-policy-meta-label/04-fetch-hudsonthames.md`
- `smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260525-action-policy-meta-label/05-fetch-mlfinpy-labeling.md`
- `smart-search fetch "https://arxiv.org/abs/2212.06355" --format markdown --output docs/research/20260525-action-policy-meta-label/06-fetch-ope-review.md`
- `smart-search fetch "https://proceedings.mlr.press/v48/thomasa16.html" --format markdown --output docs/research/20260525-action-policy-meta-label/07-fetch-data-efficient-ope.md`
- `smart-search fetch "https://zr-obp.readthedocs.io/en/latest/" --format markdown --output docs/research/20260525-action-policy-meta-label/08-fetch-open-bandit-pipeline.md`

## Fetched Sources

- Hudson & Thames meta-labeling / triple-barrier article: `04-fetch-hudsonthames.md`
- mlfinpy labeling docs: `05-fetch-mlfinpy-labeling.md`
- arXiv off-policy evaluation review: `06-fetch-ope-review.md`
- Thomas & Brunskill OPE paper: `07-fetch-data-efficient-ope.md`
- Open Bandit Pipeline docs: `08-fetch-open-bandit-pipeline.md`

## What Applies To This Bot

- Meta-labeling is a secondary model on top of a primary signal; it is a filter/sizing gate, not a replacement for the primary model.
- Triple-barrier labels are path-based, which matches the bot's need to distinguish quick-profit runners, fast-profit-then-collapse paths, and stop-first failures.
- Off-policy evaluation is the right framing when a bad policy is costly and only historical logs are available.
- Open Bandit Pipeline and related OPE tooling reinforce the need for a logged-policy / counterfactual evaluation path with clear action probabilities or support assumptions.

For this repo, the next experiment should treat the candidate stream as an action-policy problem:

- primary signal remains v95/v84 style candidate generation;
- secondary layer decides take / skip / quick-profit / conditional-hold;
- inputs must stay decision-time only;
- evaluation must be replay-equivalent, leakage-safe, and support-gated;
- validation must compare against the current accepted baseline, not the newest artifact.

## What We Reject

- Reject another global threshold relaxation.
- Reject another static quick-take-profit overlay without support gates.
- Reject blanket conditional-exit or blanket partial-exit logic unless it is learned and replay-equivalent.
- Reject using only broad search summaries as proof.

`smart-search search` returned an xAI 503 error in this round, and Zhipu/Exa were not configured. That means the external-search branch was partially blocked, but the fetched sources above are enough to justify the local direction change.

## Next Experiment

Build a replay-integrated action-policy probe that:

- merges accepted trade paths and rejected fast-profit / fast-collapse candidates;
- uses a small support-gated classifier or policy score on decision-time features;
- evaluates precision, coverage, net return, drawdown, walk-forward, and stress under 10% sizing;
- rejects any rule that only wins on the broad aggregate and loses on source-split or support coverage.
