# Does Meta Labeling Add to Signal Efficacy? - Hudson & Thames

Loading [MathJax]/extensions/MathMenu.js

[![Image 1: Hudson & Thames](https://hudsonthames.org/wp-content/uploads/2021/01/logo-horisontal-white-teal-1-1030x418.png)](https://hudsonthames.org/)

*   [HOME](https://hudsonthames.org/)
*   [PYTHON LIBRARIES](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method#)
    *   [ARBITRAGELAB](https://hudsonthames.org/arbitragelab/)
    *   [MLFINLAB](https://hudsonthames.org/mlfinlab/)
    *   [PORTFOLIOLAB](https://hudsonthames.org/portfoliolab/)

*   [COURSES](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method#)
    *   [MASTERING BACKTESTING](https://www.udemy.com/course/mastering-backtesting-for-algorithmic-trading/?referralCode=DED2C1825744E0151EAA)

*   [FELLOWSHIP PROGRAM](https://hudsonthames.org/fellowship-program/)
*   [BLOG](https://hudsonthames.org/research/)
    *   [RESEARCH ARTICLES](https://hudsonthames.org/research/)
    *   [COMPREHENSIVE INTRODUCTION TO PAIRS TRADING](https://hudsonthames.org/definitive-guide-to-pairs-trading/)
    *   [MODERN GUIDE TO PORTFOLIO OPTIMIZATION](https://hudsonthames.org/modern-guide-to-portfolio-optimization/)

*   [CONTACT](https://hudsonthames.org/about-us/)
*   [PORTAL LOGIN](https://portal.hudsonthames.org/)
*   [Search](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method?s=)
*   [**Menu**Menu](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method#)

# Does Meta Labeling Add to Signal Efficacy?

By Ashutosh Singh and Jacques Joubert

## **Abstract**

Successful and long-lasting quantitative research programs require a solid foundation that includes procurement and curation of data, creation of building blocks for feature engineering, state of the art methodologies, and backtesting. In this project we explore an example of applying meta labeling to high quality S&P500 EMini Futures data and create an python package ([mlfinlab](https://github.com/hudson-and-thames/mlfinlab)) that is based on the work of Prof. Marcos Lopez de Prado in his book ‘Advances in Financial Machine Learning. Prof. de Prado’s book provides a guideline for creating a successful platform. We also implement a Trend Following and Mean-reverting Bollinger band based trading strategies. Our results confirm the fact that a combination of event-based sampling, triple-barrier method and meta labeling improves the performance of the strategies.

Join the [Reading Group and Community](https://hudsonthames.org/reading-group/): Stay up to date with the latest developments in Financial Machine Learning!

[JOIN NOW](https://hudsonthames.org/reading-group/)

[![Image 2: WorldQuant University MSFE capstone project: Meta Labeling to improve strategy performance metrics.](https://hudsonthames.org/wp-content/uploads/2019/08/meta_paper_preview.png)](https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf)

## 1. Introduction

Inspired by 2019 Quant of the year Dr. Marcos Lopez de Prado we proposed an implementation and further research into the novel ideas and best practices published in his book Advances in Financial Machine Learning. Our project is split into two capstone sessions, the first six weeks create the foundation (of codes) by publishing an open-source python package which will enable further research into the field of quantitative investing. We also test a couple of trading strategies that leverage the foundation. The second 16 weeks would focus on further implementation of de Prado’s work and deeper research that culminates in a research article or a paper.

The key contribution in part one are the following:

1.   An open-source python package.
2.   Transformed data sets to promote further research.
3.   Empirical proof that meta-labeling benefits signal generation and thereby performance of the said strategy.

The rest of the report focuses on SWOT analysis, methodology, results, and conclusions. We also discuss next steps and areas of further research. Many of these ideas / next steps are already being formulated and worked on.

## 2. SWOT Analysis

### 2.1. Strengths

This project reflects the idea of meta-strategies as discussed in (Lopez de Prado, 2018). It is open-source and allows interested quantitative analysts like us to build on and contribute to it. We consider this to be the starting point with much work to be done. Second, we show that by using tick data and converting into event based sampling methods such as volume, dollar or tick leads to better statistical properties of the data and that in turn helps machine learning algorithms learn and predict. Third, our results corroborate (although with only two strategies) that meta-labeling has a propitious effect on the performance of the strategies.

### 2.2. Weaknesses

In order to build viable strategies one needs good quality tick data. This is costly and not readily available for research. However, as we show in this project that an expense of $1,000 can help build and test strategies that can generate interest. Second, as much as we show that meta-labeling works, it also needs a good primary algorithm that should have good performance in in-sample tests. One then needs to combine that algorithm with a rich set of features that are contextual, relevant and intuitive. If the algorithm is bad then meta-labeling would likely only reduce the downside.

### 2.3 Opportunities

This framework offers considerable upside opportunities. For instance,

*   We have seen considerable interest from analysts wanting to expand on our work by building (for instance) imbalance bars, test our strategies on Euro STOXX tick data (that one analysts volunteered to purchase) etc.
*   Build a “feature zoo” – a library of functions or function objects (functors) that would create technical and statistical features from the supplied data.
*   Incorporate fractional differentiation in the feature set.
*   Expand on the research and perhaps write a paper.

### 2.4 Threats

When we started this project we had noticed several efforts to address concepts outlined in (Lopez de Prado, 2018). We think as the quantitative finance community becomes familiar with these concepts (meta-labeling, robust back-testing, use of machine learning in crafting signals and strategies, etc.) their use will expand and will become democratized. This is likely to have a downward pressure on “alpha”. Our belief is that these ideas can be applied to other asset classes and strategies.

## 3. Methodology

In Advances in Financial Machine Learning, Dr. de Prado discusses the key success factors underlying successful algorithmic or quantitative investment strategies. One of the success factors is the concept of “meta-strategies”. First presented in (Lopez de Prado and Foreman 2014), it calls for creating a “factory” like platform for a sustainable long-term success. In this paradigm there are technologies and, roles and responsibilities for data acquisition and curation, high-performance computer infrastructure, feature engineering and analysis, execution simulation, and back-testing. Our methodology therefore starts with creation of the building-blocks for such a platform. For instance,

*   For software development and continuous integration we built an open-source framework that would allow other practitioners to add to our work. Hence we are using Github and Travis CI.
*   Coded packages to convert tick data into dollar, volume and tick bars; compute fractionally differenced series etc. In most cases we have reused the code from Advances in Financial Machine Learning or other sources with attribution. These codes are in a package called “mlfinlab”.
*   Tested two commonly used strategies – trend-following and mean-reversion – to validate the concepts and ideas.
*   Employed techniques like filtering to prevent signal whipsaws and improve the efficacy of the signal generation process; up-sampling when there were unbalanced classes; meta-labeling to improve the performance of the machine-learning process;
*   Segregated data into training, validation and out-of-sample data sets. We ensured that out-of-sample data set was never used in the training and validation steps. As a best practice, we first trained and validated the model in an iterative process. Only when we felt comfortable with the parameters then we used out-of-sample data. This ensures the sanctity of the strategy design and testing process.
*   Lagged the features to ensure that there was no look-ahead bias.
*   Used cross-validation and grid search to train Random Forest machine-learning algorithm. The choice was driven by questions at the back of the chapters (2 and 3) of the book (Lopez de Prado, 2018).

In the subsections below we delve deeper into specific aspects of the methodology of this project.

### 3.1. Financial Data Structures

Machine learning in finance focuses on forecasting stock price movements using stock market data such as price and volume. According to the literature (Thierry and Helyette 2000), the stock price movements are nonlinear and stochastic in nature. Specifically, trading activity is rarely uniform during a day or a week or a month. It varies with the information flow in the form of macro-economic data releases, news about political leaders or company specific announcements. Fama and Blume 1966, showed that daily returns are more long tailed than the normal density. It is therefore necessary to sample data using a paradigm called “event-based time” as discussed in Easley, Lopez de Prado, and O’Hara 2011. These techniques involve sampling a session into equal volume chunks or bars (for instance, 100,000 contracts or shares) or dollar bars ($1 million) etc. Empirical analysis shows that these methods have better statistical properties. In addition to dollar and volume bars, there are also tick bars (100,000 ticks).

We computed above stated bars and performed various tests for statistical properties on the returns from these bars. A notebook [Sample_Techniques.ipynb](https://github.com/hudson-and-thames/research/blob/master/Chapter2/Sample_Techniques.ipynb), in the Chapter 2 directory has the details. Below we show the Jarque-Bera tests for these bars which show that dollar bars are the closest to normality compared to all other bars (because it’s test statistic is the smallest).

Test Statistics:

*   Time: 1782853
*   Tick: 2898186
*   Volume: 337591
*   Dollar: 143045

The ACF of the bars show that dollar bars have the lowest auto-correlation among all others.

![Image 3](https://hudsonthames.org/wp-content/uploads/2019/08/Methodology_ACF_tests.png)
Figure 1: ACF on the various bars

The following figure illustrates how using event based sampling leads to a partial recovery of normality. This chart is inspired by Easley, Lopez de Prado, and O’Hara 2011.

![Image 4](https://hudsonthames.org/wp-content/uploads/2019/08/Methodology_Normality_Chart.png)
Figure 2: Partial Recovery of Normality

### 3.2. Issues with Machine Learning in Finance

Academic researchers and practitioners have found that prediction of stock price movements is more effective (compared to linear models) with algorithms that are themselves nonlinear, adaptive, and don’t assume a fixed functional form. According to literature, machine learning methods such as Random Forests and ANN are better at forecasting stock prices partially because they are better at capturing the non-linearity in the asset prices. Wang and Chan 2006 indicate that efficacy of the forecasts tend to improve when multiple classifiers are organized in ‘serial’, ‘conditional’, ‘hybrid’ or ‘parallel’ combinations.

In the attached Jupyter notebooks we create [trend-following](https://github.com/hudson-and-thames/research/blob/master/Chapter3/2019-03-06_JJ_Trend-Follow-Question.ipynb) and [Bollinger band mean-reversion](https://github.com/hudson-and-thames/research/blob/master/Chapter3/2019-03-09_AS_BBand-Question.ipynb) strategies. These use the concepts and best practices discussed above. The steps in these notebooks have the following flow:

1.   Compute long short signals for the strategy. For instance, in the mean-reverting strategy, generate a long signal when the close price is below the lower Bollinger band and create a sell signal if the close price is higher than the upper Bollinger band. We call this the “Primary model”.
2.   Get time stamps of the events using CUSUM (or cumulative sum control chart) filter and point estimate of the volatility. See section 4.2.
3.   Determine events when one of the three exit points (profit taking, stop-loss and vertical barrier) occur. Advances in Financial Machine Learning discusses this in Chapter 3. The result of this step is a trade decision – long or short, or 1 or -1.
4.   Determine the bet size. The prior step tell us the direction of the trade. This step says if we should trade or not – a one or zero decision.
5.   Tune the hyper-parameters (max_depth and n_estimators) of Random Forest using grid search and cross-validation. We keep the random state constant for reproducibility of the results.
6.   Train a machine-learning algorithm (we use Random Forest for illustration) with new features like one to five day serial correlations, one to five-day returns, 50-day volatility, and 14-day RSI. We iterate over this step number of times until we see in-sample results that are acceptable. In other words, we only exit this step when we consider the model to be ready and there is no turning back.
7.   Evaluate the performance of in sample and out-of-sample or this meta-model model.
8.   Evaluate the performance of the “Primary model”
9.   Compare the performance of the meta-model and the primary model

#### 3.2.1. Training Random Forest

We found that at the completion of step 4 above, the number of observations tagged 1 (“to trade”) were considerably smaller than 0 (not to trade). To provide balanced classes and thereby get better trained classifier we up-sampled (sampled with replacement) the training data to balance the classes. To gauge the performance of the model we employed the Classification Report, Confusion Matrix and Receiver Operating Characteristic (ROC) curve.

### 3.3. Filtering

Alexander 1961; Alexander 1964 showed the belief among the investment professionals that the asset prices gradually adjust to new information. This creates trends as opposed to instantaneous jumps as market participants become aware of new information. Alexander 1961 says that this meant that if the prices have moved up (or down) by x percent then they are likely to move more than x percent further before moving down x percent.

Lam and Yam 1997 use the CUSUM filter to detect an upward or downward shift in the prices and use that to generate trading signals. CUSUM or Cumulative Sum Control Chart is a technique used to detect shift in the mean of a process away from a target value. Consider a locally stationary process ![Image 5: \{y_t\}_{t=1,...,T}](https://hudsonthames.org/wp-content/ql-cache/quicklatex.com-6c21bc2619d318d9ab88dc8f40dafbe3_l3.svg). Define a cumulative sum ![Image 6: S_t](https://hudsonthames.org/wp-content/ql-cache/quicklatex.com-36e9e9a31a055ebab7edcd53c0c1ce91_l3.svg) such that:

S t=m a x{0,S t−1+y t–E t−1[y t]}

A symmetric CUSUM filter can be defined (as done by Lopez de Prado 2018} that will detect any shift on the up and down side.

S+t=m a x{0,S+t−1+y t–E t−1[y t]},S+0=0 S−t=m i n{0,S−t−1+y t–E t−1[y t]},S−0=0 S t=m a x{S+t,−S−t}

Advances in Financial Machine Learning, pg 38 employs the CUSUM filter to detect events that would trigger a trade. These events could be a structural break, an extracted signal or micro-structural phenomenon. There are two advantages to using a filter such as CUSUM: first, it samples key events in the data. Second, the filter prevents multiple events from getting generated when the price series hovers around a threshold value, thereby preventing whipsaws in trading.

We employ CUSUM filter as suggested by Lopez de Prado 2018, with the threshold of point-in-time volatility.

### 3.4 Triple-Barrier Labeling

In the majority of the literature, authors will make use of a labeling scheme where they classify the next periods directional move as either a 1 for a positive move, a -1 for a negative move, and some authors may add a threshold level that if the return is not above or below it, then a 0 label is provided.

This technique has a few flaws. First the threshold level is usually static and stock returns are known to be heteroskedastic, the volatility changes over time and a fixed threshold value fails to account for this. Second, using this {-1, 0, 1} scheme fails to account for positions that would have been closed by stop loss or profit taking orders.

A more advanced technique such as the Triple Barrier method (Lopez de Prado 2018), addresses these concerns and I am sure that many of you will agree – it makes more sense.

In derivatives pricing, a series of stock prices can be modeled using Geometric Brownian Motion. Similarly in the Triple Barrier method, we assume that stock prices follow a random walk with some drift and variance, we then label this path.

At a given time stamp, 3 barriers are set. An upper and lower horizontal barrier to represent a take profit and stop loss levels. A third and vertical barrier is placed to represent the end of the duration of the trade.

Should the path of a stock reach the upper barrier before the vertical then a value of 1 is returned, conversely if it reaches the bottom barrier then a -1, however should the stock price reach the vertical barrier first then a 0 is returned. This is still a {-1. 0, 1} scheme, however we are labeling a path of returns rather than the next directional move.

The horizontal barriers are determined by calculating the daily standard deviation of the log returns multiplied by a user defined multiple. For example a [1, 1] tuple will set both barriers to be equal to 1 standard deviation.

The following figure provides an example:

![Image 7: An example of Triple-Barrier Labeling from Advances in Financial Machine Learning](https://hudsonthames.org/wp-content/uploads/2019/08/triple_barrier.png)
Figure 3: Triple Barrier Labeling (Lopez de Prado 2018)

In chart (a) we can see that the lower horizontal barrier is first reached, a -1 value is returned. In chart (b) the path never reaches the horizontal barriers and triggers a 0 label when the vertical barrier is reached.

### 3.5. Fitting a Primary Model

The primary model is the component that determines which side of the trade to take. It generates a signal {-1, 0, 1}. Where -1 is a short position, 1 is a long position, and 0 means to close all positions.

This model could be but not limited to:

*   Statistical arbitrage model based on the spread between two assets.
*   Machine learning model such as an SVM or Neural Network.
*   Fundamental value or events based strategy where the portfolio manager generates the signal.
*   Rules based, technical trading strategy such as moving average crossovers.

The only requirement is that a signal is generated which is used to determine the side of the position. We look to meta labeling and bet sizing to determine the size of the position.

The following two sections discuss the technical analysis inspired strategies we used.

#### 3.5.1. Trend Following

A simple moving average crossover strategy is employed. The idea behind this strategy is to make use of two moving averages to help smooth out the noise in the data and then determine when a trend is in affect.

Traditionally a slow 200 day and a fast 50 day moving average are used. When the fast moving average crosses above the slow, a buy signal (1) is generated. Conversely when the fast crosses below the slow then a sell signal (-1) is generated. Under this scheme, there is always a long or a short side active, i.e. no 0 signals. The figure below shows an example of this.

![Image 8: Illustration of the Trend Following Strategy](https://hudsonthames.org/wp-content/uploads/2019/08/PrimaryModel_CrossoverStrategy.png)
Figure 4: SMA Crossover Strategy

The green upward arrows indicate when a long (buy) signal is in affect and a red downward arrow a short (sell) signal.

For the primary trend following model we implemented a 20 and 50 bar SMA crossover strategy. Remember that we reduced the number of events by making use of the CUSUM filter, because of this we need much shorter SMA periods to capture the short term trends that may be in affect, and provide more current information to the secondary model since the vertical barrier is set to a single day.

#### 3.5.3. Mean Reversion

The second primary model is based on mean reversion and makes use of Bollinger Bands. Bollinger Bands are a technical analysis indicator which creates bands around the price level which are more than x standard deviations away, where x is a user defined multiple.

The principal is that stock prices are log normally distributed and thus we can make use of the Empirical rule which states that 99.7% of the data lies within 3 standard deviations, 95% within 2 and 68% within 1 standard deviation. Should the closing price be above say 2 standard deviations then we generate short signal (-1) on the premise that prices should mean revert in the near term. The reverse is also true, if prices are below 2 standard deviations a buy signal is generated (1).

The figure below shows an example of a traditional Bollinger band strategy.

![Image 9: Illustration of the Mean Reverting Strategy](https://hudsonthames.org/wp-content/uploads/2019/08/PrimaryModel-BBandStrategy.png)
Figure 5: Bollinger Band Mean Reversion Strategy

The green upward arrows indicate when a long (buy) signal is in affect and a red downward arrow a short (sell) signal.

Typically a position is held until the price reaches the moving average but in our case, because we are using the triple barrier method, a position is held until one of the three barriers are touched.

### 3.6. Meta Labeling

The central idea is to create a secondary machine learning (ML) model that learns how to use the primary exogenous model. This leads to improved performance metrics, including: Accuracy, Precision, Recall, and F1-Score. For those readers who are interested in building up a deeper intuition around meta-labeling, the following [blog post](https://hudsonthames.org/meta-labeling-a-toy-example/) illustrates a toy example. We would like to stress the importance of this concept and see it as a major contribution of Dr Lopez de Prado work.

**Use in Financial Machine Learning**

Meta labeling in finance follows the same principles as we outlined in the toy example on the MNIST dataset. First we make use of a primary model, in this case a simple trend following or mean reverting strategy, to determine the position of the trade. Then we fit a Random Forest meta-label model to the primary model to determine when to trade or not.

## 4. Results

We developed the packages and Jupyter Notebooks and shared them on [Github](https://github.com/hudson-and-thames). The core functionality is under the package name “mlfinlab”. As we stated above (in the section, Methodology) that our goal was to build a platform where practitioners can use our codes and also contribute to this research. We are happy to report that this library has received considerable interest from the quantitative finance community and several have volunteered to add to the code base. A few have forked from the repository to extend the work we have done so far.

![Image 10: Screen shot of the Hudson and Thames Github repo](https://hudsonthames.org/wp-content/uploads/2019/08/project_dashboard.png)
Figure 6: Project Dashboard

### 4.1. Performance of the Strategies

We tested two trading strategies – trend-following and Bollinger band mean-reverting to use our framework and test their performance. During the training and validation phases of the strategy build-out, we manually tuned a few parameters to ensure that we have sufficient data points. For instance, a function called get_t_events filters the data (using CUSUM filter) for events when there has been a structure shift. We changed the threshold parameter manually to get sufficiently large data set. Second, we found that meta-labeling often resulted in unbalanced classes – to trade (=1) or not to trade (=0) with many more instances of “not to trade”. We used up-sampling to balance these classes prior to training the machine-learning algorithm (Random Forest).

#### 4.1.1 Performance Metrics

To evaluate the efficacy of meta-labeling we look at a models performance metrics between the validation set and the out-of-sample test set. This allows us to draw conclusions about the model’s ability to generalize. In particular we need to look at the recall, precision, F1 score, and accuracy.

The reason why we don’t compare the strategies performance metrics (annualized returns, sharpe ratio, and drawdowns) is because the two data sets are from very different time periods. For example, if the validation set has a much higher volatility than the test set, then the validation returns will be larger. This will prevent like for like comparison.

We can however compare strategy metrics if they are both from the same time period. We do provide performance metrics on the test data. Additionally we add a performance tear sheet, and see that meta-labeling results in better strategy metrics but it should be noted that we have yet to add a bet sizing component to the strategy. Additionally the two strategies we test are based on technical analysis and they don’t provide the best signals. A primary model with better predictive power would provide further insights.

#### 4.1.2. Bollinger Band Mean-Reversion Strategy

We construct 1.5 standard deviation upper and lower bands around the average closing price of the S&P500 e-mini futures. The strategy buys when the close price falls at or below the lower band and sells when the close price rises at or above the upper band. These generate the buy/sell signals also called the “side”. The meta-labeling function decides on the size (to trade or not to trade). This information along with features such as 14-day RSI, volatility, 7 and 15-day moving averages, one to five day auto-correlation, and one to five day momentum is used to train Random Forest algorithm. The trained algorithm is used to validate the signal. Finally, after finalizing the algorithm we use the trained model to test out-of-sample.

The results are as follows:

**Validation Data**

![Image 11](https://hudsonthames.org/wp-content/uploads/2019/08/Results_BBands_Validation.png)
Figure 7: Primary Model on Validation Set (Mean Reverting)

![Image 12: Meta labeling tearsheet on validation data: Mean Reversion Strategy](https://hudsonthames.org/wp-content/uploads/2019/08/Results_BBands_MetaModel.png)
Figure 8: Meta Model on Validation Set (Mean Reverting)

In the validation data we can see that the performance metrics increase. The accuracy jumps from 20% to 77%. The precision of correct trades also jumps from 0.21 to 0.39, this will correlate to greater profits and lower drawdowns.

**Out-of-Sample Data**

![Image 13](https://hudsonthames.org/wp-content/uploads/2019/08/Results_BBandsOOS_PrimaryModel.png)
Figure 9: Primary Model on Out-of-Sample Set (Mean Reverting)

![Image 14: Meta labeling tearsheet on out of sample data: Mean Reversion Strategy](https://hudsonthames.org/wp-content/uploads/2019/08/Results_BBandsOOS_Meta-model.png)
Figure 10: Meta Model on Out-of-Sample Set (Mean Reverting)

This test data is completely out-of-sample. The precision jumps from 0.17 to 0.20 and the accuracy from 17% to 63%. This should translate to improved strategy performance metrics as well.

**Strategy Performance Metrics**

![Image 15: Comparison of meta labeling vs the primary model for mean reversion strategy](https://hudsonthames.org/wp-content/uploads/2019/08/Results_OOS_MeanRevert_Table.png)
Table 1: Out-of-sample (2018-01-04 : 2019-01-28)

This shows that the meta-model adds a lot of value to the out-of-sample performance. All the metrics have improved across the board.

**Performance Tear Sheet**

The following charts are added for sake of completeness and to illustrate the risk return profile of the mean reverting strategy.

![Image 16](https://hudsonthames.org/wp-content/uploads/2019/08/Results_BBands_TearSheet1.png)
Figure 11: Cumulative Returns (Mean Reverting)

![Image 17](https://hudsonthames.org/wp-content/uploads/2019/08/Results_BBands_TearSheet2.png)
Figure 12: 6 Month Volatility and Sharpe Ratio (Mean Reverting)

![Image 18](https://hudsonthames.org/wp-content/uploads/2019/08/Results_BBands_TearSheet3.png)
Figure 13: Drawdowns and Underwater Plot (Mean Reverting)

#### 4.1.3. Simple Moving Average (SMA) Crossover – Trend Following Strategy

We construct two moving averages. A fast 20 bar SMA and a slow 50 bar SMA around the closing price of the S&P500 e-mini futures.

The strategy buys when the fast SMA is above the slow SMA and sells when the fast SMA is below the slow SMA. These generate the buy/sell signals also called the “side”. The meta-labeling function decides on the size (to trade or not to trade). This information along with features such as fifty, thirty one, and fifteen bar rolling volatility, one to five day auto-correlation, and one to five day momentum is used to train Random Forest algorithm. The trained algorithm is used to validate the signal. Finally, after finalizing the algorithm we use the trained model to test out-of-sample.

The results are as follows:

**Validation Data**

![Image 19](https://hudsonthames.org/wp-content/uploads/2019/08/tf_valid_prim_model.png)
Figure 14: Primary Model on Validation Set (Trend Following)

![Image 20: Meta labeling on validation set for trend following strategy](https://hudsonthames.org/wp-content/uploads/2019/08/tf_valid_meta_model.png)
Figure 15: Meta Model on Validation Set (Trend Following)

In the validation data we can see that the performance metrics increase. The accuracy jumps from 37% to 56%. The precision of correct trades also increases from 0.37 to 0.42, this will correlate to greater profits and lower drawdowns in the long run.

**Out-of-Sample Data**

![Image 21](https://hudsonthames.org/wp-content/uploads/2019/08/oos-prim.png)
Figure 16: Primary Model on Out-of-Sample Set (Trend Following)

![Image 22: Meta labeling on out of sample set for trend following strategy](https://hudsonthames.org/wp-content/uploads/2019/08/oos-meta.png)
Figure 17: Meta Model on Out-of-Sample Set (Trend Following)

This test data is completely out-of-sample. The precision increases from 0.48 to 0.54 and the accuracy from 48% to 55%. This should translate to improved strategy performance metrics as well.

**Strategy Performance Metrics**

![Image 23: Comparison of meta labeling vs the primary model for trend following strategy](https://hudsonthames.org/wp-content/uploads/2019/08/TrendFollow_table.png)
Table 2: Out-of-sample (2018-01-18 : 2019-01-31)

The above is slightly different to the mean reverting strategy as it doesn’t out perform on all the metrics however it does outperform on a risk adjusted basis. This is exactly what meta-labeling sets out to do!

**Performance Tear Sheet**

The following charts are added for sake of completeness and to illustrate the risk return profile of the trend following strategy.

![Image 24](https://hudsonthames.org/wp-content/uploads/2019/08/tf_cum_rets.png)
Figure 18: Cumulative Returns (Trend Following)

![Image 25](https://hudsonthames.org/wp-content/uploads/2019/08/tf_rolling_vol.png)
Figure 19: 6 Month Volatility and Sharpe Ratio (Trend Following)

![Image 26](https://hudsonthames.org/wp-content/uploads/2019/08/tf_max_dd.png)
Figure 20: Drawdowns and Underwater Plot (Trend Following)

## 5. Next Steps

We plan to continue to enhance and expand the platform and the mlfinlab package. Specifically, in the short-term:

*   Use the best-practices of cross-validation (see section on Random Forests, Cross-Validation and Grid Search).
*   Add position sizing (bet sizing [Lopez de Prado 2018, Chapter 10] and risk management to the strategies. This will provide a much more realistic picture of a strategy’s performance.
*   Build unit-tests for each of the library functions.
*   Build a “feature zoo”.
*   Use new features and a better model to redesign the current trend-following strategy.
*   Test the strategies with other data such as Euro STOXX index.
*   Write a paper.

## 6. Conclusion

This capstone project was conceived as a step toward a larger goal of creating a platform for ongoing quantitative research that (Lopez de Prado 2018) speaks about in the form of meta-strategies. Our goal in this phase of the larger endeavor was to create an open-source package that serves as a foundation and then leverage that to test a couple of trading strategies. We also wanted to use concepts, ideas and theories learnt from courses, projects and papers during the MSFE at WorldQuant University.

Given the interest shown by various quant practitioners and Dr. de Prado, the author of the book “Advances in Financial Machine Learning”, we feel that we are on the right track. We also did not want this to be a purely pedagogical but examine the efficacy of the key concepts like meta-labeling and triple-barrier. Our results on the two strategies – trend-following and mean-reversion – bear that out (See Results section).

But as we stated above, this is only the first step and much work needs to be done. We have discussed in the section Next Steps many of the immediate “to dos”. In the long-term we hope to learn more via the discussion and contribution from others as we continue to contribute.

## References

This section is best referenced via the pdf document.

*   [Ale61] Sidney S. Alexander. “Price Movements in Speculative Markets: Trends or Random Walks”. In: Industrial Management Review 2 (1961), pp. 7–26.
*   [Ale64] Sidney S. Alexander. “Price Movements in Speculative Markets: Trends or Random Walks, No. 2”. In: Industrial Management Review 5 (1964), pp. 25–46. 
*    [EPO11] David Easley, MARCOS L ́OPEZ DE PRADO, and Maureen O’Hara.“The Volume Clock: Insights into the High-Frequency Paradigm”. In: Journal of Portfolio ManagementCl (2011), pp. 901–921. 
*    [FB66] Eugene F. Fama and Marshall E. Blume. “Filter rules and stock-market trading”. In: Journal of Business39.1 (1966), pp. 226–241. 
*    [Has09] Hastie, Trevor. Tibshirani, Robert. Friedman, Jerome. The Elementsof Statistical Learning. 2009. 
*    [LF14] Marcos Lopez de Prado and Matthew D. Foreman. “A mixture ofGaussians approach to mathematical portfolio oversight: the EF3M algorithm”. In: Quantitative Finance14.5 (2014), pp. 913–930. 
*    [LLC18] Tick Data LLC. Global Futures Trade and Quote Data File Format Document, Version 1.6. 2018. 
*    [Lop18] Marcos Lopez de Prado. Advances in Financial Machine Learning. Wiley, 2018, p. 366. 
*    [LY97] Kin Lam and H.C. Yam. “CUSUM Techniques for Technical Trading in Financial Markets”. In: Financial Engineering and Japanese Markets 4 (1997), pp. 257–274. 
*    [NAT16] NATLAT. Scanning hyperspace: how to tune machine learning mod-els. [Online; accessed March 18, 2019].  
*   [Nor18] Norena, Sebastian.Python Model Tuning Methods Using Cross Validation and Grid Search. [Online; accessed March 18, 2019]. 
*   [sci19] scikit learn. Precision and recall. [Online; accessed March 18, 2019].
*   [Sin19] Singh, Ashutosh. Joubert, Jacques. Capstone1. [Online; accessed March18, 2019] 
*   [TH00] Ane Thierry and Geman Helyette. “Order Flow, Transaction Clock, and Normality of Asset Returns”. In: 55.5 (2000), pp. 2259–2284.
*   [WC06] Jar-long Wang and Shu-hui Chan. “Stock market trading rule dis-covery using two-layer bias decision tree”. In: Expert Systems with Applications 30.1 (2006), pp. 605–611.
*   [Wik19] Wikipedia, the free encyclopedia. Precision and recall. [Online; accessed March 18, 2019].

[![Image 27](https://hudsonthames.org/wp-content/uploads/2019/08/quantocracy.png)](https://quantocracy.com/)

Popular

Recent

Comments

Tags

Popular

*   [![Image 28](https://hudsonthames.org/wp-content/uploads/2021/01/Into-to-Copula-Pairs-Trading-36x36.png)**Copula for Pairs Trading: A Detailed, But Practical Int...January 20, 2021 - 1:21 pm**](https://hudsonthames.org/copula-for-pairs-trading-introduction/ "Copula for Pairs Trading: A Detailed, But Practical Introduction")
*   [![Image 29: Best research practices for your quant research group](https://hudsonthames.org/wp-content/uploads/2022/01/Best_research_practices_for_your_quant_research_group-36x36.jpg)**Best Research Practices for Your Quantitative Finance Research...January 14, 2022 - 1:26 pm**](https://hudsonthames.org/best-research-practices-for-your-quantitative-finance-research-group/ "Best Research Practices for Your Quantitative Finance Research Group")
*   [![Image 30](https://hudsonthames.org/wp-content/uploads/2023/04/john-towner-p-rN-n6Miag-unsplash-scaled.jpg)**Machine Learning Trading Essentials (Part 1): Financial...April 13, 2023 - 10:47 am**](https://hudsonthames.org/machine-learning-trading-essentials-part-1-financial-data-structures/ "Machine Learning Trading Essentials (Part 1): Financial Data Structures")
*   [![Image 31](https://hudsonthames.org/wp-content/uploads/2021/01/Copy-of-Copula-Strategy-Variations-in-the-Mispricing-Index-Trading7-36x36.png)**Employing Machine Learning for Pairs Selection January 25, 2021 - 3:09 pm**](https://hudsonthames.org/employing-machine-learning-for-trading-pairs-selection/ "Employing Machine Learning for Pairs Selection")
*   [![Image 32](https://hudsonthames.org/wp-content/uploads/2021/02/Copy-of-Copula-Strategy-Variations-in-the-Mispricing-Index-Trading-36x36.png)**Copula for Pairs Trading: Sampling and Fitting to Data February 4, 2021 - 2:45 pm**](https://hudsonthames.org/copula-for-pairs-trading-sampling-and-fitting/ "Copula for Pairs Trading: Sampling and Fitting to Data")
*   [![Image 33: C-Vine Copula Strategy Thumbnail](https://hudsonthames.org/wp-content/uploads/2021/05/Copy-of-Introduction-to-Vine-Copula-for-Statistical-Arbitrage2-36x36.png)**Copula for Statistical Arbitrage: A C-Vine Copula Trading...May 10, 2021 - 7:09 pm**](https://hudsonthames.org/copula-for-statistical-arbitrage-a-c-vine-copula-trading-strategy/ "Copula for Statistical Arbitrage: A C-Vine Copula Trading Strategy")
*   [![Image 34: Stocks Selection Methods](https://hudsonthames.org/wp-content/uploads/2021/04/Copy-of-Introduction-to-Vine-Copula-for-Statistical-Arbitrage1-36x36.png)**Copula for Statistical Arbitrage: Stocks Selection Meth...April 28, 2021 - 12:11 pm**](https://hudsonthames.org/copula-for-statistical-arbitrage-stocks-selection-methods/ "Copula for Statistical Arbitrage: Stocks Selection Methods")
*   [![Image 35](https://hudsonthames.org/wp-content/uploads/2021/04/Intro-to-Vine-Copula-36x36.png)**Copula for Statistical Arbitrage: A Practical Intro to Vine...April 14, 2021 - 2:54 pm**](https://hudsonthames.org/a-practical-intro-to-vine-copula/ "Copula for Statistical Arbitrage: A Practical Intro to Vine Copula")
*   [![Image 36](https://hudsonthames.org/wp-content/uploads/2020/10/pmfg_graph_only-36x36.png)**Exploring the PMFG Portfolios for Covid-19 Robustness October 4, 2020 - 10:43 pm**](https://hudsonthames.org/exploring-the-pmfg-portfolios-for-covid-19-robustness/ "Exploring the PMFG Portfolios for Covid-19 Robustness")
*   [![Image 37](https://hudsonthames.org/wp-content/uploads/2020/09/Pairs-Trading-with-Ornstein-Uhlenbeck-Model-1-36x36.png)**Optimal Stopping in Pairs Trading: Ornstein-Uhlenbeck M...September 21, 2020 - 8:59 pm**](https://hudsonthames.org/optimal-stopping-in-pairs-trading-ornstein-uhlenbeck-model/ "Optimal Stopping in Pairs Trading: Ornstein-Uhlenbeck Model")

Recent

*   [![Image 38](https://hudsonthames.org/wp-content/uploads/2023/10/Featured-image-wordpress-blog-2023-10-10-36x36.png)**Dynamically combining mean reversion and momentum investment...October 10, 2023 - 2:41 pm**](https://hudsonthames.org/dynamically-combining-mean-reversion-and-momentum-investment-strategies/ "Dynamically combining mean reversion and momentum investment strategies")
*   [![Image 39](https://hudsonthames.org/wp-content/uploads/2023/09/DOCKER-X-MLFinlab-5-36x36.png)**Docker + MLFinlab now in Open Beta to All Subscribers September 13, 2023 - 1:56 pm**](https://hudsonthames.org/docker-mlfinlab-now-in-open-beta-to-all-subscribers/ "Docker + MLFinlab now in Open Beta to All Subscribers")
*   [![Image 40](https://hudsonthames.org/wp-content/uploads/2023/04/LB_HudsonThames_ProductLogos_MLFinLab-03-36x36.png)**Release Announcement: MLFinlab v2.2.0 September 6, 2023 - 12:28 pm**](https://hudsonthames.org/release-announcement-mlfinlab-v2-2-0/ "Release Announcement: MLFinlab v2.2.0")
*   [![Image 41](https://hudsonthames.org/wp-content/uploads/2023/06/LB_Hudson_Thames_ProductLogos_PortfolioLab-03-1-36x36.png)**Release Announcement: PortoflioLab v0.6.0 September 6, 2023 - 8:55 am**](https://hudsonthames.org/release-announcement-portofliolab-v0-6-0/ "Release Announcement: PortoflioLab v0.6.0")
*   [![Image 42](https://hudsonthames.org/wp-content/uploads/2023/04/LB_HudsonThames_ProductLogos_MLFinLab-03-36x36.png)**Release Announcement: MLFinlab v2.1.0 August 17, 2023 - 8:29 am**](https://hudsonthames.org/release-announcement-mlfinlab-v2-1-0/ "Release Announcement: MLFinlab v2.1.0")
*   [![Image 43](https://hudsonthames.org/wp-content/uploads/2023/06/LB_Hudson_Thames_ProductLogos_PortfolioLab-03-1-36x36.png)**Release announcement: PortfolioLab v0.5.0 July 13, 2023 - 1:15 pm**](https://hudsonthames.org/release-announcement-portfoliolab-v0-5-0/ "Release announcement: PortfolioLab v0.5.0")
*   [![Image 44](https://hudsonthames.org/wp-content/uploads/2023/07/docker_beta-36x36.png)**Docker + MLFinlab closed beta announcement July 5, 2023 - 8:01 pm**](https://hudsonthames.org/docker-mlfinlab-closed-beta-announcement/ "Docker + MLFinlab closed beta announcement")
*   [![Image 45](https://hudsonthames.org/wp-content/uploads/2023/06/LB_Hudson_Thames_ProductLogos_ArbitrageLab-03-1-1-36x36.png)**Celebrating ArbitrageLab v0.8 — 85% lifetime discount June 30, 2023 - 12:47 pm**](https://hudsonthames.org/celebrating-arbitragelab-v0-8-85-lifetime-discount/ "Celebrating ArbitrageLab v0.8 — 85% lifetime discount")
*   [![Image 46](https://hudsonthames.org/wp-content/uploads/2023/06/LB_Hudson_Thames_ProductLogos_ArbitrageLab-03-1-36x36.png)**Release announcement: ArbitrageLab v0.8 June 28, 2023 - 1:29 pm**](https://hudsonthames.org/release-announcement-arbitragelab-v0-8/ "Release announcement: ArbitrageLab v0.8")
*   [![Image 47](https://hudsonthames.org/wp-content/uploads/2023/06/manhatten-scaled.jpg)**Breaking Down the “cold-start” Problem in Quantitative...June 13, 2023 - 1:25 pm**](https://hudsonthames.org/breaking-down-the-cold-start-problem-in-quantitative-finance/ "Breaking Down the “cold-start” Problem in Quantitative Finance")

Comments

*   [**[…] Taking your MLFinLab strategy live [Hudson and...July 1, 2023 - 5:45 am by Quantocracy's Daily Wrap for 06/30/2023 - Quantocracy**](https://hudsonthames.org/?p=10932/#comment-48 "Taking your MLFinLab strategy live")
*   [**[…] Machine Learning Trading Essentials (Part 2):...April 28, 2023 - 5:30 am by Quantocracy's Daily Wrap for 04/27/2023 - Quantocracy**](https://hudsonthames.org/machine-learning-trading-essentials-part-2-fractionally-differentiated-features-filtering-and-labelling/#comment-46 "Machine Learning Trading Essentials (Part 2): Fractionally differentiated features, Filtering, and Labelling")
*   [**[…] enjoying our journey towards building a successful...April 26, 2023 - 9:01 am by Machine Learning Trading Essentials (Part 2): Fractionally differentiated features, Filtering, and Labelling - Hudson & Thames**](https://hudsonthames.org/machine-learning-trading-essentials-part-1-financial-data-structures/#comment-45 "Machine Learning Trading Essentials (Part 1): Financial Data Structures")
*   [**[…] Machine Learning Trading Essentials (Part 1):...April 16, 2023 - 5:30 am by Quantocracy's Daily Wrap for 04/15/2023 - Quantocracy**](https://hudsonthames.org/machine-learning-trading-essentials-part-1-financial-data-structures/#comment-41 "Machine Learning Trading Essentials (Part 1): Financial Data Structures")
*   [**[…] QuantConnect Integration with MlFinLab [Hudson...October 22, 2022 - 5:30 am by Quantocracy's Daily Wrap for 10/21/2022 - Quantocracy**](https://hudsonthames.org/quantconnect-integration-with-mlfinlab/#comment-40 "QuantConnect Integration with MlFinLab")
*   [**[…] Best Research Practices for Your Quant Group [Hudson...January 28, 2022 - 6:45 am by Quantocracy's Daily Wrap for 01/19/2022 - Quantocracy**](https://hudsonthames.org/best-research-practices-for-your-quantitative-finance-research-group/#comment-39 "Best Research Practices for Your Quantitative Finance Research Group")
*   [**[…] on our last article regarding best practices for...January 25, 2022 - 6:48 am by How to Build a World-Class Quant Team - Hudson & Thames**](https://hudsonthames.org/best-research-practices-for-your-quantitative-finance-research-group/#comment-38 "Best Research Practices for Your Quantitative Finance Research Group")
*   [**[…] on our last article regarding best practices for...January 23, 2022 - 11:42 pm by How to Build the Best Quant Team in the World - Hudson & Thames**](https://hudsonthames.org/best-research-practices-for-your-quantitative-finance-research-group/#comment-37 "Best Research Practices for Your Quantitative Finance Research Group")
*   [**[…] Pairs Trading with Stochastic Control and OU process...July 12, 2021 - 1:45 am by Quantocracy's Daily Wrap for 06/22/2021 | Quantocracy**](https://hudsonthames.org/pairs-trading-with-stochastic-control-and-ou-process/#comment-35 "Pairs Trading with Stochastic Control and OU process")
*   [**[…] Copula for Statistical Arbitrage: C-Vine Copula...May 19, 2021 - 5:45 am by Quantocracy's Daily Wrap for 05/10/2021 | Quantocracy**](https://hudsonthames.org/copula-for-statistical-arbitrage-a-c-vine-copula-trading-strategy/#comment-34 "Copula for Statistical Arbitrage: A C-Vine Copula Trading Strategy")

Tags

[Asset Management](https://hudsonthames.org/tag/asset-management/)[Benchmarks](https://hudsonthames.org/tag/benchmarks/)[Code Tutorial](https://hudsonthames.org/tag/code-tutorial/)[cointegration](https://hudsonthames.org/tag/cointegration/)[copula](https://hudsonthames.org/tag/copula/)[Correlation Estimation](https://hudsonthames.org/tag/correlation-estimation/)[Covariance Matrix](https://hudsonthames.org/tag/covariance-matrix/)[data](https://hudsonthames.org/tag/data/)[Distance Approach](https://hudsonthames.org/tag/distance-approach/)[Distance measures](https://hudsonthames.org/tag/distance-measures/)[Ensemble](https://hudsonthames.org/tag/ensemble/)[ESG](https://hudsonthames.org/tag/esg/)[futures contracts](https://hudsonthames.org/tag/futures-contracts/)[Github](https://hudsonthames.org/tag/github/)[Hierarchical Clustering](https://hudsonthames.org/tag/hierarchical-clustering/)[Interpretability](https://hudsonthames.org/tag/interpretability/)[lessons](https://hudsonthames.org/tag/lessons/)[Machine Learning](https://hudsonthames.org/tag/machine-learning/)[Mean Reversion](https://hudsonthames.org/tag/mean-reversion/)[meta-labeling](https://hudsonthames.org/tag/meta-labeling/)[Minimum Spanning Tree](https://hudsonthames.org/tag/minimum-spanning-tree/)[mixed copula](https://hudsonthames.org/tag/mixed-copula/)[Momentum](https://hudsonthames.org/tag/momentum/)[Networks](https://hudsonthames.org/tag/networks/)[OLS](https://hudsonthames.org/tag/ols/)[open-source](https://hudsonthames.org/tag/open-source/)[Optimal Stopping](https://hudsonthames.org/tag/optimal-stopping/)[Ornstein-Uhlenbeck](https://hudsonthames.org/tag/ornstein-uhlenbeck/)[OU Model](https://hudsonthames.org/tag/ou-model/)[Pairs Selection](https://hudsonthames.org/tag/pairs-selection/)[Pairs Trading](https://hudsonthames.org/tag/pairs-trading/)[Pattern Matching](https://hudsonthames.org/tag/pattern-matching/)[PCA](https://hudsonthames.org/tag/pca/)[Planar Maximally Filtered Graph](https://hudsonthames.org/tag/planar-maximally-filtered-graph/)[Portfolio Optimisation](https://hudsonthames.org/tag/portfolio-optimisation/)[Portfolio Selection](https://hudsonthames.org/tag/portfolio-selection/)[python](https://hudsonthames.org/tag/python/)[Random walks](https://hudsonthames.org/tag/random-walks/)[research](https://hudsonthames.org/tag/research/)[Risk estimation](https://hudsonthames.org/tag/risk-estimation/)[Risk Parity](https://hudsonthames.org/tag/risk-parity/)[Sustainable Investing](https://hudsonthames.org/tag/sustainable-investing/)[Synthetic Data](https://hudsonthames.org/tag/synthetic-data/)[Trading](https://hudsonthames.org/tag/trading/)[Trading Strategy](https://hudsonthames.org/tag/trading-strategy/)

© Copyright - Hudson & Thames | [Privacy Policy](https://hudsonthames.org/wp-content/uploads/2021/06/PrivacyPolicy.pdf) | [GDPR Policy](https://hudsonthames.org/wp-content/uploads/2021/06/GDPR-Policy.pdf)

[Meta Labeling (A Toy Example)![Image 48](https://hudsonthames.org/wp-content/uploads/2019/07/toy_example-80x80.jpg)](https://hudsonthames.org/meta-labeling-a-toy-example/)[![Image 49](https://hudsonthames.org/wp-content/uploads/2019/07/fracdiff_prado-80x80.png)Fractional Differentiation](https://hudsonthames.org/fractional-differentiation/)

[Scroll to top](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method#top "Scroll to top")
