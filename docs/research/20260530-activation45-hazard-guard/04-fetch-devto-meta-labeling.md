![DEV Community](https://media2.dev.to/dynamic/image/quality=100/https://dev-to-uploads.s3.amazonaws.com/uploads/logos/resized_logo_UQww2soKuUsjaOGNB38o.png)

## DEV Community

![](https://assets.dev.to/assets/heart-plus-active-9ea3b22f2bc311281db911d416166c5f430636e76b15cd5df6b3b841d830eefa.svg)
![](https://assets.dev.to/assets/sparkle-heart-5f9bee3767e18deb1bb725290cb151c25234768a0e9a2bd39370c382d02920cf.svg)
![](https://assets.dev.to/assets/multi-unicorn-b44d6f8c23cdd00964192bedc38af3e82463978aa611b4365bd33a0f1f4f3e97.svg)
![](https://assets.dev.to/assets/exploding-head-daceb38d627e6ae9b730f36a1e390fca556a4289d5a41abb2c35068ad3e2c4b5.svg)
![](https://assets.dev.to/assets/raised-hands-74b2099fd66a39f2d7eed9305ee0f4553df0eb7b4f11b01b6b1b499973048fe5.svg)
![](https://assets.dev.to/assets/fire-f60e7a582391810302117f987b22a8ef04a2fe0df7e3258a5f49332df1cec71e.svg)
![NydarTrading](https://media2.dev.to/dynamic/image/width=50,height=50,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Fuser%2Fprofile_image%2F3720042%2F7fd5734c-786c-4910-9cb4-ec1673eba043.png)

Posted on Feb 20
• Originally published at [nydar.co.uk](https://nydar.co.uk/blog/meta-labeling-filtering-bad-trades)

# Meta-Labeling: Filtering Bad Trades Before They Happen

## The Problem with Raw Predictions

Imagine a model that's 55% accurate. That means 45% of its signals are wrong. If you follow every signal, you're taking a lot of bad trades alongside the good ones.

What if there was a way to know *which* predictions are likely to be correct — before the trade happens?

That's meta-labeling.

[![Prediction Widget](/images/blog/prediction-widget.jpg)](/images/blog/prediction-widget.jpg)

![Prediction Widget](/images/blog/prediction-widget.jpg)

## What Is Meta-Labeling?

Meta-labeling is a two-stage prediction framework popularised by Marcos Lopez de Prado in *Advances in Financial Machine Learning*. The concept is simple:

**Stage 1 — Primary Model:** Predicts the direction (bullish or bearish). This is our XGBoost model.

**Stage 2 — Meta Model:** Takes the primary model's prediction and asks: "Is this specific prediction likely to be correct?"

The meta model doesn't predict direction — it predicts the *quality* of the primary prediction. It outputs a confidence score. If the meta-confidence is below our threshold, we withhold the signal.

### Think of It Like a Quality Filter

vs.

The result: fewer signals, but higher quality.

## How We Train the Meta Model

The training process uses a 70/30 split within each walk-forward window:

The meta model is a separate XGBoost classifier with more regularisation than the primary (shallower trees, higher regularisation) to avoid overfitting.

Critically, the meta model sees features the primary model *doesn't* optimise for. The primary model optimises for direction prediction. The meta model optimises for *when the primary is right*. These are different problems.

## Our Experiment Results

We tested meta-labeling across 10 cryptocurrencies at three confidence thresholds:

### 1-Hour Timeframe

| Threshold | Accuracy | Coverage | Improvement |
| --- | --- | --- | --- |
| No filter (baseline) | 54.9% | 100% | — |
| Meta ≥ 0.55 | 56.0% | 53% | +1.1% |
| Meta ≥ 0.60 | 56.3% | 44% | **+1.4%** |
| Meta ≥ 0.65 | 56.1% | 38% | +1.2% |

### 4-Hour Timeframe

| Threshold | Accuracy | Coverage | Improvement |
| --- | --- | --- | --- |
| No filter | 52.3% | 100% | — |
| Meta ≥ 0.55 | 52.5% | 48% | +0.2% |
| Meta ≥ 0.60 | 52.2% | 41% | -0.1% |
| Meta ≥ 0.65 | 52.8% | 36% | +0.5% |

### Daily Timeframe

| Threshold | Accuracy | Coverage | Improvement |
| --- | --- | --- | --- |
| No filter | 51.2% | 100% | — |
| Meta ≥ 0.55 | 54.4% | 52% | +3.2% |
| Meta ≥ 0.60 | 54.7% | 43% | +3.5% |
| Meta ≥ 0.65 | 55.7% | 39% | **+4.5%** |

The daily timeframe showed the strongest meta-labeling effect — a +4.5% improvement is substantial.

## The Accuracy vs Coverage Tradeoff

This is the core tension in meta-labeling. Higher thresholds mean:

At threshold 0.65 on the daily timeframe, you only get signals ~39% of the time. The other 61% of periods, the meta model says "I'm not confident enough" and no signal is generated.

Is this a problem? It depends on your perspective:

We chose **threshold 0.60** as the default — it gives the best accuracy-to-coverage balance on the hourly timeframe where most of our signals are generated.

## Per-Coin Results

Meta-labeling doesn't help every coin equally:

| Coin | Baseline | With Meta | Improvement |
| --- | --- | --- | --- |
| AUCTION | 54.8% | 63.9% | +9.2% |
| BTC (1d) | 50.6% | 66.1% | +15.5% |
| ETH (1d) | 55.0% | 62.7% | +7.7% |
| SOL | 53.7% | 54.9% | +1.2% |
| ETH (1h) | 55.6% | 55.2% | -0.5% |
| HIVE (1d) | 51.0% | 49.8% | -1.2% |

Some observations:

## What the Meta Model Learns

The meta model's feature importance reveals what it's actually learning:

In other words, the meta model learns to trust the primary model more when:

## Implementation Considerations

If you're building a similar system:

**Train/meta split matters.** We use 70/30 within each walk-forward window. Too little meta-training data (e.g., 90/10) makes the meta model unreliable. Too much (e.g., 50/50) starves the primary model.

**The meta model should be more regularised.** We use shallower trees (depth 5 vs 8) and higher regularisation. The meta model sees fewer samples and has an easier classification task.

**Include primary confidence as a meta feature.** This is the single most important feature for the meta model. Without it, meta-labeling performance drops significantly.

**Walk-forward prevents leakage.** The meta model must only be trained on data the primary model hasn't seen. Our 70/30 split within each walk-forward window ensures this.

## Key Takeaways

## Part of Our Research Series

Full methodology: [How Our AI Works](https://dev.to/how-our-ai-works)

*AI trading signals are probabilistic predictions, not financial advice. Meta-labeling improves signal quality but does not eliminate risk. Past performance does not guarantee future results.*

*Originally published at [Nydar](https://nydar.co.uk/blog/meta-labeling-filtering-bad-trades). Nydar is a free trading platform with AI-powered signals and analysis.*

## Top comments (0)

![pic](https://media2.dev.to/dynamic/image/width=256,height=,fit=scale-down,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F8j7kvp660rqzt99zui8e.png)

Templates let you quickly answer FAQs or store snippets for re-use.

Are you sure you want to hide this comment? It will become hidden in your post, but will still be visible via the comment's [permalink](#).

Hide child comments as well

Confirm

For further actions, you may consider blocking this person and/or [reporting abuse](/report-abuse)

![](https://media2.dev.to/dynamic/image/width=90,height=90,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Fuser%2Fprofile_image%2F3720042%2F7fd5734c-786c-4910-9cb4-ec1673eba043.png)

### More from [NydarTrading](/nydartrading)

💎 DEV Diamond Sponsors

Thank you to our Diamond Sponsors for supporting the DEV Community

![Google AI - Official AI Model and Platform Partner](https://media2.dev.to/dynamic/image/width=880%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fxjlyhbdqehj3akhz166w.png)

Google AI is the official AI Model and Platform Partner of DEV

![Neon - Official Database Partner](https://media2.dev.to/dynamic/image/width=880%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fbnl88cil6afxzmgwrgtt.png)

Neon is the official database partner of DEV

![Algolia - Official Search Partner](https://media2.dev.to/dynamic/image/width=880%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fv30ephnolfvnlwgwm0yz.png)

Algolia is the official search partner of DEV

[DEV Community](/) — A space to discuss and keep up software development and manage your software career

Built on [Forem](https://www.forem.com) — the [open source](https://dev.to/t/opensource) software that powers [DEV](https://dev.to) and other inclusive communities.

Made with love and [Ruby on Rails](https://dev.to/t/rails). DEV Community © 2016 - 2026.

![DEV Community](https://media2.dev.to/dynamic/image/width=190,height=,fit=scale-down,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F8j7kvp660rqzt99zui8e.png)

We're a place where coders share, stay up-to-date and grow their careers.

![](https://assets.dev.to/assets/sparkle-heart-5f9bee3767e18deb1bb725290cb151c25234768a0e9a2bd39370c382d02920cf.svg)
![](https://assets.dev.to/assets/multi-unicorn-b44d6f8c23cdd00964192bedc38af3e82463978aa611b4365bd33a0f1f4f3e97.svg)
![](https://assets.dev.to/assets/exploding-head-daceb38d627e6ae9b730f36a1e390fca556a4289d5a41abb2c35068ad3e2c4b5.svg)
![](https://assets.dev.to/assets/multi-unicorn-b44d6f8c23cdd00964192bedc38af3e82463978aa611b4365bd33a0f1f4f3e97.svg)
![](https://assets.dev.to/assets/exploding-head-daceb38d627e6ae9b730f36a1e390fca556a4289d5a41abb2c35068ad3e2c4b5.svg)
![](https://assets.dev.to/assets/exploding-head-daceb38d627e6ae9b730f36a1e390fca556a4289d5a41abb2c35068ad3e2c4b5.svg)
![](https://assets.dev.to/assets/raised-hands-74b2099fd66a39f2d7eed9305ee0f4553df0eb7b4f11b01b6b1b499973048fe5.svg)
![](https://assets.dev.to/assets/fire-f60e7a582391810302117f987b22a8ef04a2fe0df7e3258a5f49332df1cec71e.svg)
