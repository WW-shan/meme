# The Triple Barrier Labeling of Marco Lopez de Prado

[![Image 1: Quantreo](https://substackcdn.com/image/fetch/$s_!Y0GG!,w_40,h_40,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fd5709b73-08d5-47ec-9254-66545ec25261_512x512.png)](https://www.newsletter.quantreo.com/)

# [![Image 2: Quantreo](https://substackcdn.com/image/fetch/$s_!xzaG!,e_trim:10:white/e_trim:10:transparent/h_72,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F35edc488-2dcf-47b3-8faa-ae91b793c142_1100x300.png)](https://www.newsletter.quantreo.com/)

Subscribe Sign in

![Image 3: User's avatar](https://substackcdn.com/image/fetch/$s_!QIRk!,w_64,h_64,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fbd07a0c7-18f7-447f-b735-2962768d14bb_989x989.png)

Discover more from Quantreo

Real-life quant trading tips. All Friday by mail.

Over 3,000 subscribers

Subscribe

By subscribing, you agree Substack's [Terms of Use](https://substack.com/tos), and acknowledge its [Information Collection Notice](https://substack.com/ccpa#personal-data-collected) and [Privacy Policy](https://substack.com/privacy).



Already have an account? [Sign in](https://www.newsletter.quantreo.com/p/the-triple-barrier-labeling-of-marco)

# The Triple Barrier Labeling of Marco Lopez de Prado

### Why Most Labels in Trading Are Wrong

[![Image 4: Lucas's avatar](https://substackcdn.com/image/fetch/$s_!QIRk!,w_36,h_36,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fbd07a0c7-18f7-447f-b735-2962768d14bb_989x989.png)](https://substack.com/@lucas368891)

[Lucas](https://substack.com/@lucas368891)

May 02, 2025

8

Share

You want to train a model to predict good trades.

So what do you do? You create a label like:

> “If price goes up after 10 bars → label = 1, else 0.”

It sounds logical — but in reality, it’s flawed.

This kind of label ignores two fundamental things every real trade faces:

*   **Risk** (what if the price drops before going up?)

*   **Timing** (what if it goes up… but only after weeks?)

That’s why serious quants don’t use simple returns as labels.

They use something far more robust: the **Triple Barrier Method**.

In this newsletter, you’ll learn how it works, why it’s better, and how to implement it in Python using the **[quantreo](https://docs.quantreo.com/)** library, so your backtests stop lying and your models start learning.

Thanks for reading Quantreo! Subscribe for free to receive new posts and support my work.

Subscribe

* * *

## 1. What Is the Triple Barrier Method?

The **Triple Barrier Method**, introduced by Marcos López de Prado, is a powerful way to label trading data.

Instead of checking whether the price goes up or down after _n_ candles, it simulates **realistic trade conditions** using three key barriers:

### **🟢 1. Upper Barrier → Take Profit**

Set at a fixed percentage or return above the entry price.

If the price hits this level first, the trade is labeled as **+1** (profit).

### 🔴 2. Lower Barrier → Stop Loss

Placed below the entry price.

If this level is reached first, the label is **-1** (loss).

### ⏱ 3. Vertical Barrier → Max Holding Time

If neither TP nor SL is hit within a certain number of periods, the trade **expires**, and the label is **0** (neutral).

[![Image 5](https://substackcdn.com/image/fetch/$s_!8j09!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fd3f141f9-7d21-4f04-ac18-4debd1d207a3_1321x734.heic)](https://substackcdn.com/image/fetch/$s_!8j09!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fd3f141f9-7d21-4f04-ac18-4debd1d207a3_1321x734.heic)

📌 **What makes it powerful?**

It doesn’t just care about how much the price moved —

It asks **how the trade played out** under realistic conditions:

*   Did it reach the profit fast enough?

*   Was it stopped out?

*   Did it just move sideways?

> The result is a label that reflects both the **direction**, the **risk**, and the **timing** of each opportunity.

And that makes it **ideal for machine learning**, especially in noisy markets.

* * *

## 2. How to Use the Triple Barrier Method in Practice

Now that you understand the concept, let’s make it concrete.

You don’t need to reinvent the wheel, the method is already implemented in the **[quantreo](https://docs.quantreo.com/target-engineering/directional/#triple-barrier-labeling)** library.

Let’s go through a simple example to label your data.

### 🧪 Step 1: Load a Sample Dataset

```
from quantreo.datasets import load_generated_ohlcv_with_time

df = load_generated_ohlcv_with_time()
df = df.loc["2016"]
```

[![Image 6](https://substackcdn.com/image/fetch/$s_!oobI!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F31f2c602-e6b4-42cd-8af0-19580fe6ce68_1111x472.heic)](https://substackcdn.com/image/fetch/$s_!oobI!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F31f2c602-e6b4-42cd-8af0-19580fe6ce68_1111x472.heic)

To use the Triple Barrier Method, you **must have**`low_time`**and**`high_time`**columns**, they tell when the price reached its lowest and highest points during the holding period.

If you’re working with resampled data (like 1H or 4H candles), just extract 1-minute data first, then resample it; this way, you can easily track **when** the high or low occurred. If you use alternative bars, just use the ticks.

### 🧱 Step 2: Apply the Triple Barrier Labeling

`df["label"] = te.directional.triple_barrier_labeling(df, 500, open_col="open", high_col="high", low_col="low", high_time_col="high_time", low_time_col="low_time", tp=0.015, sl=-0.015, buy=True)`
This function scans each row in the dataset, applies the three barriers (TP, SL, time), and creates a new column `label`with values:

*   `1` → trade hit the **take-profit**

*   `-1` → trade hit the **stop-loss**

*   `0` → trade expired with neither hit

[![Image 7](https://substackcdn.com/image/fetch/$s_!MSKk!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Faa055474-4bca-479a-8240-a71178ae3347_1227x529.heic)](https://substackcdn.com/image/fetch/$s_!MSKk!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Faa055474-4bca-479a-8240-a71178ae3347_1227x529.heic)

**✅ That’s it.**

Now your ML models won’t just learn from oversimplified returns.

They’ll learn from **real-world trade outcomes**, shaped by profit, loss, and time.

> The Triple Barrier Method gives your model a much stronger foundation to distinguish between **valid trades** and **noisy signals**.

* * *

## 3. Why It’s a Perfect Fit for Meta-Labelling

The Triple Barrier Method is a **natural foundation** for building meta-labels.

In meta-labelling, your goal isn’t to predict the market directly — it's to **decide whether to act** on a primary signal (long/short). But to do that, your model needs feedback on how those signals typically end.

That’s exactly what the triple barrier provides.

It gives each entry signal a **structured label**:

*   `+1` if the trade would have reached take-profit,

*   `-1` if it would have hit the stop-loss,

*   `0` if it expired before reaching either.

This clear outcome gives your meta-model a **concrete objective**: learn to **filter out bad signals**, and only act on those with a higher chance of success.

In short, the Triple Barrier Method transforms raw directional signals into a reliable training set for smarter decision-making.

* * *

Thanks for reading Quantreo! Subscribe for free to receive new posts and support my work.

Subscribe

Most traders label their data in a simplistic way, and wonder why their models don’t work.

The **Triple Barrier Method** changes the game.

It adds _realism_ to your backtests by mimicking what would actually happen in a trade:

Take-profit, stop-loss, or timeout.

And if you’re building advanced workflows like **meta-labelling**, it’s not optional —

it’s the backbone that allows your meta-model to **learn from real trade outcomes**, not noisy price shifts.

👉 Start using it today with just a few lines of code in the **[quantreo](https://docs.quantreo.com/)** library.

Your model, and your future self, will thank you.

* * *

#### Subscribe to Quantreo

By Lucas · Launched a year ago

Real-life quant trading tips. All Friday by mail.

Subscribe

By subscribing, you agree Substack's [Terms of Use](https://substack.com/tos), and acknowledge its [Information Collection Notice](https://substack.com/ccpa#personal-data-collected) and [Privacy Policy](https://substack.com/privacy).



[![Image 8: Qaribullah Almasi's avatar](https://substackcdn.com/image/fetch/$s_!OfV3!,w_32,h_32,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F01306c5b-3d63-46de-9a75-ca8ae9ada8ce_1242x2208.jpeg)](https://substack.com/profile/327704959-qaribullah-almasi)[![Image 9: Chepell's avatar](https://substackcdn.com/image/fetch/$s_!mzeP!,w_32,h_32,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fa04b8b36-bde7-457b-a698-e4e70bacd59c_144x144.png)](https://substack.com/profile/24800503-chepell)[![Image 10: Tobi's avatar](https://substackcdn.com/image/fetch/$s_!dvUg!,w_32,h_32,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fbucketeer-e05bbc84-baa3-437e-9518-adb32be77984.s3.amazonaws.com%2Fpublic%2Fimages%2F78011349-3e2f-4aae-9549-8872491ba038_144x144.png)](https://substack.com/profile/14316529-tobi)[![Image 11: White Fang's avatar](https://substackcdn.com/image/fetch/$s_!q4uI!,w_32,h_32,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F7e0dda1a-d206-46f0-9b24-2c8293d5bdc5_3072x3072.webp)](https://substack.com/profile/379154145-white-fang)[![Image 12: Lucas's avatar](https://substackcdn.com/image/fetch/$s_!QIRk!,w_32,h_32,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fbd07a0c7-18f7-447f-b735-2962768d14bb_989x989.png)](https://substack.com/profile/101111526-lucas)

[8 Likes](https://www.newsletter.quantreo.com/p/the-triple-barrier-labeling-of-marco)

[](https://substack.com/note/p-162537079/restacks?utm_source=substack&utm_content=facepile-restacks)

8

Share

Previous Next

#### Discussion about this post

Comments Restacks

![Image 13: User's avatar](https://substackcdn.com/image/fetch/$s_!TnFC!,w_32,h_32,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack.com%2Fimg%2Favatars%2Fdefault-light.png)

Top Latest Discussions

[The PCA Trick I Use All the Time (But Almost No One Talks About)](https://www.newsletter.quantreo.com/p/the-pca-trick-i-use-all-the-time)

[A complete hands-on tutorial (with code) using volatility features to create one clean, interpretable signal for your trading models.](https://www.newsletter.quantreo.com/p/the-pca-trick-i-use-all-the-time)

Apr 4, 2025•[Lucas](https://substack.com/@lucas368891)

48

1

![Image 14](https://substackcdn.com/image/fetch/$s_!tM7r!,w_320,h_213,c_fill,f_auto,q_auto:good,fl_progressive:steep,g_auto/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F17877c42-fb9d-445b-9ded-d16923027d80_1208x505.heic)

[Strategies Generate Returns. Portfolios Control Risk.](https://www.newsletter.quantreo.com/p/strategies-generate-returns-portfolios)

[Why the real edge is not a single strategy](https://www.newsletter.quantreo.com/p/strategies-generate-returns-portfolios)

Jan 9•[Lucas](https://substack.com/@lucas368891)

29

7

6

![Image 15](https://substackcdn.com/image/fetch/$s_!hLiT!,w_320,h_213,c_fill,f_auto,q_auto:good,fl_progressive:steep,g_auto/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fe33d1d87-6cee-4e72-9f42-0ef5239b5084_1338x644.heic)

[Stop Trusting Your Backtests (Until You’ve Fixed These 5 Errors)](https://www.newsletter.quantreo.com/p/stop-trusting-your-backtests-until)

[Learn why most backtests fail in live trading and how to fix them before it's too late.](https://www.newsletter.quantreo.com/p/stop-trusting-your-backtests-until)

Apr 25, 2025•[Lucas](https://substack.com/@lucas368891)

29

2

![Image 16](https://substackcdn.com/image/fetch/$s_!ePYb!,w_320,h_213,c_fill,f_auto,q_auto:good,fl_progressive:steep,g_auto/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fb5ea5462-b227-4081-bbf8-fe868525479f_842x520.heic)

See all

### Ready for more?

Subscribe

© 2026 Lucas · [Privacy](https://substack.com/privacy) ∙ [Terms](https://substack.com/tos) ∙ [Collection notice](https://substack.com/ccpa#personal-data-collected)

[Start your Substack](https://substack.com/signup?utm_source=substack&utm_medium=web&utm_content=footer)[Get the app](https://substack.com/app/app-store-redirect?utm_campaign=app-marketing&utm_content=web-footer-button)

[Substack](https://substack.com/) is the home for great culture
