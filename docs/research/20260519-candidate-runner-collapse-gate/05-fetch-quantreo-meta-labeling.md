[Skip to content](#meta-labelling-explained-filter-noise-boost-precision-win-more)

⚠️ **Quantreo is deprecated.** The project continues as **Oryon** -  [oryonlib.dev](https://oryonlib.dev) .



# Meta-Labelling Explained: Filter Noise, Boost Precision, Win More[¶](#meta-labelling-explained-filter-noise-boost-precision-win-more)

In this notebook, we walk through the **full workflow of a meta-labelling strategy** using a realistic trading scenario.

We'll follow these steps:

1. **📈 Create a basic signal**: based on a classic moving average crossover.
2. **🏁 Apply the Triple Barrier Method**: to label each signal as a win, loss, or neutral.
3. **🧠 Engineer features**: capturing market structure (volatility, distribution, memory).
4. **⚙️ Train a meta-model**: using a Support Vector Classifier to decide which signals are worth acting on.
5. **📊 Evaluate performance**: comparing raw signals vs. filtered signals (meta-model).

> The goal is not to deliver a production-ready model, but to **understand the logic** behind meta-labelling, and how it can **filter noisy trading signals** to improve your edge.



👉 Full Newsletter about this subject available here: [Click here](https://open.substack.com/pub/quantreo/p/meta-labelling-explained-filter-noise?r=1o765i&utm_campaign=post&utm_medium=web&showWelcomeOnShare=true)

📚 Full course talking about ML for Trading: [Click here](https://www.quantreo.com/ml4trading-course/)

In [120]:

Copied!

```
 # Import the Features & Target Engineering Package from Quantreo import  quantreo.features_engineering  as  fe import  quantreo.target_engineering  as  te# Import scikit-learn packages from  sklearn.preprocessing  import StandardScaler # Import pandas & Numpy import  pandas  as  pd import  numpy  as  np # To display the graphics import  matplotlib.pyplot  as  plt plt. style. use("seaborn-v0_8") # To remove some warnings import  warnings warnings. filterwarnings("ignore")
```

# Import the Features & Target Engineering Package from Quantreo import quantreo.features\_engineering as fe import quantreo.target\_engineering as te # Import scikit-learn packages from sklearn.preprocessing import StandardScaler # Import pandas & Numpy import pandas as pd import numpy as np # To display the graphics import matplotlib.pyplot as plt plt.style.use("seaborn-v0\_8") # To remove some warnings import warnings warnings.filterwarnings("ignore")

In [105]:

Copied!

```
 # Import a dataset to test the functions and create new ones easily from  quantreo.datasets  import load_generated_ohlcv_with_time df = load_generated_ohlcv_with_time() # Show the data df
```

# Import a dataset to test the functions and create new ones easily from quantreo.datasets import load\_generated\_ohlcv\_with\_time df = load\_generated\_ohlcv\_with\_time() # Show the data df

Out[105]:

| open | high | low | close | volume | low\_time | high\_time |
| --- | --- | --- | --- | --- | --- | --- |
| time |
| 2015-05-11 20:00:00 | 100.000000 | 100.358754 | 99.971765 | 100.113771 | 868.291731 | 2015-05-11 20:23:00 | 2015-05-11 20:53:00 |
| 2015-05-12 00:00:00 | 100.113771 | 100.274415 | 100.068157 | 100.197068 | 538.344102 | 2015-05-12 03:50:00 | 2015-05-12 00:18:00 |
| 2015-05-12 04:00:00 | 100.197068 | 100.621953 | 100.171421 | 100.550996 | 623.520889 | 2015-05-12 04:21:00 | 2015-05-12 07:47:00 |
| 2015-05-12 08:00:00 | 100.553515 | 100.789037 | 100.544627 | 100.759708 | 752.315201 | 2015-05-12 09:02:00 | 2015-05-12 11:49:00 |
| 2015-05-12 12:00:00 | 100.756989 | 100.975667 | 100.701889 | 100.769042 | 1260.121555 | 2015-05-12 15:37:00 | 2015-05-12 12:44:00 |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 2024-11-13 04:00:00 | 102.104104 | 102.160879 | 101.878808 | 101.931978 | 431.101813 | 2024-11-13 07:23:00 | 2024-11-13 04:02:00 |
| 2024-11-13 08:00:00 | 101.931978 | 102.091758 | 101.931110 | 102.015341 | 1091.853172 | 2024-11-13 10:14:00 | 2024-11-13 12:00:00 |
| 2024-11-13 12:00:00 | 102.016217 | 102.082893 | 101.672509 | 101.853754 | 1848.353946 | 2024-11-13 13:28:00 | 2024-11-13 15:31:00 |
| 2024-11-13 16:00:00 | 101.851943 | 101.855884 | 101.712032 | 101.753414 | 1520.159220 | 2024-11-13 17:09:00 | 2024-11-13 16:08:00 |
| 2024-11-13 20:00:00 | 101.762771 | 101.972575 | 101.740974 | 101.876301 | 757.920331 | 2024-11-13 20:53:00 | 2024-11-13 21:26:00 |

14792 rows × 7 columns

## Basic Trading Signal Using SMA Crossover[¶](#basic-trading-signal-using-sma-crossover)

We create a simple buy signal based on the crossing of two moving averages: a fast one (20 periods) and a slower one (60 periods). A signal is triggered (signal = 1) when the fast SMA crosses above the slow SMA, a classic trend-following setup.

In [106]:

Copied!

```
 # Create two SMAs df["fast_SMA"] = fe. trend. sma(df, col = 'close', window_size = 20) df["slow_SMA"] = fe. trend. sma(df, col = 'close', window_size = 60) # Create a buy signal when we have a crossing up df["signal"] = 0 df. loc[(df["fast_SMA"]. shift(1)< df["slow_SMA"]. shift(1)) &(df["slow_SMA"]< df["fast_SMA"]), "signal"] = 1
```

# Create two SMAs df["fast\_SMA"] = fe.trend.sma(df, col='close', window\_size=20) df["slow\_SMA"] = fe.trend.sma(df, col='close', window\_size=60) # Create a buy signal when we have a crossing up df["signal"] = 0 df.loc[(df["fast\_SMA"].shift(1) < df["slow\_SMA"].shift(1)) & (df["slow\_SMA"] < df["fast\_SMA"]), "signal"] = 1

In [128]:

Copied!

```
 # Sample the dataset to show it better dft = df. loc["2016"] # Create a large figure for better visibility plt. figure(figsize =(20, 6)) # Plot upward cross signals as green triangles plt. scatter(dft. loc[dft["signal"] == 1]. index, dft. loc[dft. loc[dft["signal"] == 1]. index, "fast_SMA"], marker = '^', color = '#32CB20', s = 150, label = 'Cross Up') # Plot the price line in yellow with transparency plt. plot(dft["close"], color = "black", label = "Price", alpha =0.50) plt. plot(dft["fast_SMA"], label = "SMA Fast", alpha =0.50) plt. plot(dft["slow_SMA"], label = "SMA Slow", alpha =0.50) # Show the graph plt. legend() plt. show()
```

# Sample the dataset to show it better dft=df.loc["2016"] # Create a large figure for better visibility plt.figure(figsize=(20, 6)) # Plot upward cross signals as green triangles plt.scatter(dft.loc[dft["signal"]==1].index, dft.loc[dft.loc[dft["signal"]==1].index, "fast\_SMA"], marker='^', color='#32CB20', s=150, label='Cross Up') # Plot the price line in yellow with transparency plt.plot(dft["close"], color="black", label="Price", alpha=0.50) plt.plot(dft["fast\_SMA"], label="SMA Fast", alpha=0.50) plt.plot(dft["slow\_SMA"], label="SMA Slow", alpha=0.50) # Show the graph plt.legend() plt.show()

[embedded image omitted]

## Triple Barrier Labelling for Signal Evaluation[¶](#triple-barrier-labelling-for-signal-evaluation)

We apply the Triple Barrier Method to label each trade signal using realistic trade dynamics. With a take-profit of 0.5% and a stop-loss of -0.5%, the method evaluates whether each signal would have resulted in a win (+1), a loss (-1), or timed out (0), based on the price action after the entry point.

In [45]:

Copied!

```
 # Create a Triple Barrier Labeling df["label"] = te. directional. triple_barrier_labeling(df, 150, open_col = "open", high_col = "high", low_col = "low", high_time_col = "high_time", low_time_col = "low_time", tp =0.005, sl =-0.005, buy = True)
```

# Create a Triple Barrier Labeling df["label"] = te.directional.triple\_barrier\_labeling(df, 150, open\_col="open", high\_col="high", low\_col="low", high\_time\_col="high\_time", low\_time\_col="low\_time", tp=0.005, sl=-0.005, buy=True)

```
100%|█████████████████████████████████| 14792/14792 [00:00<00:00, 829617.90it/s]
```

In [46]:

Copied!

```
 df
```

df

Out[46]:

| open | high | low | close | volume | low\_time | high\_time | fast\_SMA | slow\_SMA | signal | label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| time |
| 2015-05-11 20:00:00 | 100.000000 | 100.358754 | 99.971765 | 100.113771 | 868.291731 | 2015-05-11 20:23:00 | 2015-05-11 20:53:00 | NaN | NaN | 0 | 1 |
| 2015-05-12 00:00:00 | 100.113771 | 100.274415 | 100.068157 | 100.197068 | 538.344102 | 2015-05-12 03:50:00 | 2015-05-12 00:18:00 | NaN | NaN | 0 | 1 |
| 2015-05-12 04:00:00 | 100.197068 | 100.621953 | 100.171421 | 100.550996 | 623.520889 | 2015-05-12 04:21:00 | 2015-05-12 07:47:00 | NaN | NaN | 0 | 1 |
| 2015-05-12 08:00:00 | 100.553515 | 100.789037 | 100.544627 | 100.759708 | 752.315201 | 2015-05-12 09:02:00 | 2015-05-12 11:49:00 | NaN | NaN | 0 | 1 |
| 2015-05-12 12:00:00 | 100.756989 | 100.975667 | 100.701889 | 100.769042 | 1260.121555 | 2015-05-12 15:37:00 | 2015-05-12 12:44:00 | NaN | NaN | 0 | 1 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 2024-11-13 04:00:00 | 102.104104 | 102.160879 | 101.878808 | 101.931978 | 431.101813 | 2024-11-13 07:23:00 | 2024-11-13 04:02:00 | 102.347967 | 102.850859 | 0 | 0 |
| 2024-11-13 08:00:00 | 101.931978 | 102.091758 | 101.931110 | 102.015341 | 1091.853172 | 2024-11-13 10:14:00 | 2024-11-13 12:00:00 | 102.304248 | 102.813318 | 0 | 0 |
| 2024-11-13 12:00:00 | 102.016217 | 102.082893 | 101.672509 | 101.853754 | 1848.353946 | 2024-11-13 13:28:00 | 2024-11-13 15:31:00 | 102.251171 | 102.776545 | 0 | 0 |
| 2024-11-13 16:00:00 | 101.851943 | 101.855884 | 101.712032 | 101.753414 | 1520.159220 | 2024-11-13 17:09:00 | 2024-11-13 16:08:00 | 102.225879 | 102.740652 | 0 | 0 |
| 2024-11-13 20:00:00 | 101.762771 | 101.972575 | 101.740974 | 101.876301 | 757.920331 | 2024-11-13 20:53:00 | 2024-11-13 21:26:00 | 102.201161 | 102.708832 | 0 | 0 |

14792 rows × 11 columns

## Feature Engineering for Meta-Labelling[¶](#feature-engineering-for-meta-labelling)

To train our meta-model, we generate a rich set of volatility and distribution-based features. These include multiple volatility estimators (Close-to-Close, Parkinson, Rogers-Satchell, Yang-Zhang), price distribution bands, autocorrelation, and the Hurst exponent — all designed to capture the structure and behavior of price movement around our signals. We also compute a volatility average to reduce dimensionality and keep only features related to active buy signals.

In [48]:

Copied!

```
 # Standard volatility features df["vol_close_to_close_30"] = fe. volatility. close_to_close_volatility(df, window_size = 30) df["vol_close_to_close_60"] = fe. volatility. close_to_close_volatility(df, window_size = 60) df["vol_close_to_close_90"] = fe. volatility. close_to_close_volatility(df, window_size = 90) # Parkinson volatility features df["vol_parkinson_30"] = fe. volatility. parkinson_volatility(df, high_col = "high", low_col = "low", window_size = 30) df["vol_parkinson_60"] = fe. volatility. parkinson_volatility(df, high_col = "high", low_col = "low", window_size = 60) df["vol_parkinson_90"] = fe. volatility. parkinson_volatility(df, high_col = "high", low_col = "low", window_size = 90) # Rogers Satchell volatility feature df["vol_rogers_satchell_30"] = fe. volatility. rogers_satchell_volatility(df, high_col = "high", low_col = "low", open_col = "open", close_col = "close", window_size = 30) df["vol_rogers_satchell_60"] = fe. volatility. rogers_satchell_volatility(df, high_col = "high", low_col = "low", open_col = "open", close_col = "close", window_size = 60) df["vol_rogers_satchell_90"] = fe. volatility. rogers_satchell_volatility(df, high_col = "high", low_col = "low", open_col = "open", close_col = "close", window_size = 90) # Yang Zhang volatility feature df["vol_yang_zhang_30"] = fe. volatility. yang_zhang_volatility(df, high_col = "high", low_col = "low", open_col = "open", close_col = "close", window_size = 30) df["vol_yang_zhang_60"] = fe. volatility. yang_zhang_volatility(df, high_col = "high", low_col = "low", open_col = "open", close_col = "close", window_size = 60) df["vol_yang_zhang_90"] = fe. volatility. yang_zhang_volatility(df, high_col = "high", low_col = "low", open_col = "open", close_col = "close", window_size = 90) # Price distribution df['0_to_25'] = fe. candle. price_distribution(df, col = "close", window_size = 60, start_percentage =0.00, end_percentage =0.25) df['25_to_75'] = fe. candle. price_distribution(df, col = "close", window_size = 60, start_percentage =0.25, end_percentage =0.75) df['75_to_100'] = fe. candle. price_distribution(df, col = "close", window_size = 60, start_percentage =0.75, end_percentage =1.00) # AutoCorr df["auto_corr_10"] = fe. math. auto_corr(df = df, col = "close", window_size = 50, lag = 10) # Hurst df["hurst_100"] = fe. math. hurst(df = df, col = "close", window_size = 100) # Volatility Mean to reduce the number of features vol_features =[col for col in df. columns if "vol_" in col and "volatility" not in col] df["volatility_mean"] = df[vol_features]. mean(axis = 1)
```

# Standard volatility features df["vol\_close\_to\_close\_30"] = fe.volatility.close\_to\_close\_volatility(df, window\_size=30) df["vol\_close\_to\_close\_60"] = fe.volatility.close\_to\_close\_volatility(df, window\_size=60) df["vol\_close\_to\_close\_90"] = fe.volatility.close\_to\_close\_volatility(df, window\_size=90) # Parkinson volatility features df["vol\_parkinson\_30"] = fe.volatility.parkinson\_volatility(df, high\_col="high", low\_col="low", window\_size=30) df["vol\_parkinson\_60"] = fe.volatility.parkinson\_volatility(df, high\_col="high", low\_col="low", window\_size=60) df["vol\_parkinson\_90"] = fe.volatility.parkinson\_volatility(df, high\_col="high", low\_col="low", window\_size=90) # Rogers Satchell volatility feature df["vol\_rogers\_satchell\_30"] = fe.volatility.rogers\_satchell\_volatility(df, high\_col="high", low\_col="low", open\_col="open", close\_col="close", window\_size=30) df["vol\_rogers\_satchell\_60"] = fe.volatility.rogers\_satchell\_volatility(df, high\_col="high", low\_col="low", open\_col="open", close\_col="close", window\_size=60) df["vol\_rogers\_satchell\_90"] = fe.volatility.rogers\_satchell\_volatility(df, high\_col="high", low\_col="low", open\_col="open", close\_col="close", window\_size=90) # Yang Zhang volatility feature df["vol\_yang\_zhang\_30"] = fe.volatility.yang\_zhang\_volatility(df, high\_col="high", low\_col="low", open\_col="open", close\_col="close", window\_size=30) df["vol\_yang\_zhang\_60"] = fe.volatility.yang\_zhang\_volatility(df, high\_col="high", low\_col="low", open\_col="open", close\_col="close", window\_size=60) df["vol\_yang\_zhang\_90"] = fe.volatility.yang\_zhang\_volatility(df, high\_col="high", low\_col="low", open\_col="open", close\_col="close", window\_size=90) # Price distribution df['0\_to\_25'] = fe.candle.price\_distribution(df, col="close", window\_size=60, start\_percentage=0.00, end\_percentage=0.25) df['25\_to\_75'] = fe.candle.price\_distribution(df, col="close", window\_size=60, start\_percentage=0.25, end\_percentage=0.75) df['75\_to\_100'] = fe.candle.price\_distribution(df, col="close", window\_size=60, start\_percentage=0.75, end\_percentage=1.00) # AutoCorr df["auto\_corr\_10"] = fe.math.auto\_corr(df=df, col="close", window\_size=50, lag=10) # Hurst df["hurst\_100"] = fe.math.hurst(df=df, col="close", window\_size=100) # Volatility Mean to reduce the number of features vol\_features = [col for col in df.columns if "vol\_" in col and "volatility" not in col] df["volatility\_mean"] = df[vol\_features].mean(axis=1)

In [55]:

Copied!

```
 # Conditionate the analysis to the Buy Signal df = df[["volatility_mean", "auto_corr_10", "0_to_25", "25_to_75", "75_to_100", "hurst_100", "signal", "label"]]. loc[df["signal"] == 1]. dropna()
```

# Conditionate the analysis to the Buy Signal df = df[["volatility\_mean", "auto\_corr\_10", "0\_to\_25", "25\_to\_75", "75\_to\_100", "hurst\_100", "signal", "label"]].loc[df["signal"]==1].dropna()

In [56]:

Copied!

```
 # Define the train size train_size = int(len(df)*0.75) # Chronological split X_list =["volatility_mean", "auto_corr_10", "0_to_25", "25_to_75", "75_to_100", "hurst_100"] y_list =["label"] # Split the dataset X_train = df. iloc[: train_size][X_list] y_train = df. iloc[: train_size][y_list] X_test = df. iloc[train_size:][X_list] y_test = df. iloc[train_size:][y_list]
```

# Define the train size train\_size = int(len(df) \* 0.75) # Chronological split X\_list = ["volatility\_mean", "auto\_corr\_10", "0\_to\_25", "25\_to\_75", "75\_to\_100", "hurst\_100"] y\_list = ["label"] # Split the dataset X\_train = df.iloc[:train\_size][X\_list] y\_train = df.iloc[:train\_size][y\_list] X\_test = df.iloc[train\_size:][X\_list] y\_test = df.iloc[train\_size:][y\_list]

In [57]:

Copied!

```
 df
```

df

Out[57]:

| volatility\_mean | auto\_corr\_10 | 0\_to\_25 | 25\_to\_75 | 75\_to\_100 | hurst\_100 | signal | label |
| --- | --- | --- | --- | --- | --- | --- | --- |
| time |
| 2015-07-10 16:00:00 | 0.002159 | -0.448941 | 25.000000 | 55.000000 | 20.000000 | 0.564863 | 1 | 1 |
| 2015-07-29 12:00:00 | 0.001951 | -0.414811 | 31.666667 | 56.666667 | 11.666667 | 0.407086 | 1 | -1 |
| 2015-08-18 16:00:00 | 0.002708 | -0.141767 | 15.000000 | 51.666667 | 33.333333 | 0.398367 | 1 | -1 |
| 2015-09-04 08:00:00 | 0.002063 | 0.064196 | 35.000000 | 50.000000 | 15.000000 | 0.456214 | 1 | -1 |
| 2015-09-21 08:00:00 | 0.001888 | 0.017000 | 20.000000 | 51.666667 | 28.333333 | 0.494735 | 1 | -1 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 2024-06-11 20:00:00 | 0.002043 | -0.065222 | 13.333333 | 56.666667 | 30.000000 | 0.539516 | 1 | 1 |
| 2024-07-05 20:00:00 | 0.002231 | -0.226993 | 11.666667 | 50.000000 | 38.333333 | 0.464584 | 1 | -1 |
| 2024-07-26 08:00:00 | 0.002135 | -0.088219 | 45.000000 | 50.000000 | 5.000000 | 0.553411 | 1 | -1 |
| 2024-08-22 08:00:00 | 0.002316 | -0.221965 | 28.333333 | 56.666667 | 15.000000 | 0.606306 | 1 | 1 |
| 2024-10-17 00:00:00 | 0.002833 | -0.064014 | 35.000000 | 60.000000 | 5.000000 | 0.593118 | 1 | 1 |

143 rows × 8 columns

## Standardization and Model Training[¶](#standardization-and-model-training)

We standardize the feature set using StandardScaler to ensure that all inputs to the SVM have the same scale — a crucial step for distance-based models. Then we train a basic Support Vector Classifier (SVC) on the labeled buy signals to learn how to distinguish between profitable, unprofitable, or neutral trades.

In [58]:

Copied!

```
 # Standardize the data to help the SVC scaler = StandardScaler() X_train_sc = scaler. fit_transform(X_train) X_test_sc = scaler. transform(X_test)
```

# Standardize the data to help the SVC scaler = StandardScaler() X\_train\_sc = scaler.fit\_transform(X\_train) X\_test\_sc = scaler.transform(X\_test)

In [63]:

Copied!

```
 # Create and Train the model from  sklearn.svm  import SVC model = SVC() model. fit(X_train_sc, y_train)
```

# Create and Train the model from sklearn.svm import SVC model = SVC() model.fit(X\_train\_sc, y\_train)

Out[63]:

```
SVC()
```

**In a Jupyter environment, please rerun this cell to show the HTML representation or trust the notebook.
On GitHub, the HTML representation is unable to render, please try loading this page with nbviewer.org.**

```
SVC()
```

## Prediction & Performance Analysis[¶](#prediction-performance-analysis)

Once our meta-model is trained, we evaluate its effectiveness compared to the raw trading signal.

We compute two key metrics:

* **Accuracy**: how often the model predicted the correct label.
* **Precision (positive trades)**: how often predicted positive trades (label = 1) were actually correct — this is especially important when you want to avoid false positives.

We also define a **baseline** where every trading signal is executed (i.e. always predict 1), to simulate the performance of the raw signal **without meta-labelling**.

Here is the comparison table:

| Accuracy | Precision (positive trades) |
| --- | --- |
| Meta-model | 0.556 | 0.478 |
| Signal only | 0.417 | 0.417 |

👉 In this example, the meta-model improves both **accuracy** and **precision**, meaning it filters out some of the bad trades. But keep in mind: this is only a small test — not a final strategy.

In [123]:

Copied!

```
 from  sklearn.metrics  import accuracy_score, precision_score# Meta-model predictions y_pred_meta = model. predict(X_test_sc)# Baseline: assume all signals are executed (always predict 1) y_baseline =[1]* len(y_test)# Compute metrics for meta-model acc_meta = accuracy_score(y_test, y_pred_meta) prec_meta = precision_score(y_test, y_pred_meta, labels =[1], average = 'macro') # Compute metrics for raw signal acc_signal = accuracy_score(y_test, y_baseline) prec_signal = precision_score(y_test, y_baseline, labels =[1], average = 'macro') # Compare results in a clear table performance_df = pd. DataFrame({"Accuracy":[acc_meta, acc_signal],"Precision (positive trades)":[prec_meta, prec_signal]}, index =["Meta-model", "Signal only"]) performance_df. round(3)
```

from sklearn.metrics import accuracy\_score, precision\_score # Meta-model predictions y\_pred\_meta = model.predict(X\_test\_sc) # Baseline: assume all signals are executed (always predict 1) y\_baseline = [1] \* len(y\_test) # Compute metrics for meta-model acc\_meta = accuracy\_score(y\_test, y\_pred\_meta) prec\_meta = precision\_score(y\_test, y\_pred\_meta, labels=[1], average='macro') # Compute metrics for raw signal acc\_signal = accuracy\_score(y\_test, y\_baseline) prec\_signal = precision\_score(y\_test, y\_baseline, labels=[1], average='macro') # Compare results in a clear table performance\_df = pd.DataFrame({ "Accuracy": [acc\_meta, acc\_signal], "Precision (positive trades)": [prec\_meta, prec\_signal] }, index=["Meta-model", "Signal only"]) performance\_df.round(3)

| Accuracy | Precision (positive trades) |
| --- | --- |
| Meta-model | 0.556 | 0.478 |
| Signal only | 0.417 | 0.417 |

⚠️ **Important note before interpreting the results**

In this example, our test set contains **only about 30 data points**, and the full dataset includes **fewer than 150 trades**.
 We’ve used a **simple train/test split**, with **no robustness testing**, no cross-validation, no sensitivity analysis, and no hyperparameter tuning.

> These results are **not statistically significant**. They might look good here, but could easily fail in a different setting.

The real goal of this notebook isn’t to show off a final model.
 It’s to help you understand how **meta-labelling works**, so you can build and refine **your own robust pipeline** later on.
