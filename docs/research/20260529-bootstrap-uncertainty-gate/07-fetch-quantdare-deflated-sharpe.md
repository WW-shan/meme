* [Artificial Intelligence](https://quantdare.com/category/artificial-intelligence/)
* [Asset Management](https://quantdare.com/category/asset-management/)
* [Risk Management](https://quantdare.com/category/risk-management/)
* [Python](https://quantdare.com/category/python/)
* [R](https://quantdare.com/category/r/)
* [All](https://quantdare.com/category/all/)
* [About us](https://quantdare.com/about-us/)

# **Daring** to quantify the markets |

The scientific blog of [**ETS Asset Management Factory**](https://www.etsfactory.com/)

 [Unlock the Power of Quantitative Strategies: Explore Our Cutting-Edge **Website** Today!](https://www.etsfactory.com/playground)

## All

# Deflated Sharpe Ratio (how to avoid been fooled by randomness)

[### Rubén Briones](https://quantdare.com/author/ruben-briones/)

#### 05/11/2020



As we test more and more strategies the overall probability of choosing at least one poor strategy grows. So we must be very careful with how many backtests we run. We should always record all of them, to later deflate the Sharpe Ratio accordingly.

In this post, we are going to analyze how the Deflated Sharpe Ratio, exposed by Marcos López de Prado and David H. Bailey in this [paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551), can help us to differentiate a good investment strategy from statistical flukes. Keep reading until the end to see a **practical example coded in Python.**

## Context

In [my last post](https://quantdare.com/probabilistic-sharpe-ratio/), we discussed how the *Probabilistic Sharpe Ratio* (PSR) can help us when evaluating the confidence level for a given Sharpe Ratio.

Recall that whatever SR we calculate is actually a SR estimation ([latex]\widehat{SR}[/latex]), since we use past returns to *estimate* its future mean and variance. Therefore, as we explained in the PSR post, each [latex]\widehat{SR}[/latex] has its variance and confidence levels associated, which we saw **are highly influenced by the skewness and kurtosis of the returns**, and by the length of the track record.

As a reminder, the standard deviation of the [latex]\widehat{SR}[/latex] is calculated as:

[latex]\begin{equation}\hat{\sigma}(\widehat{SR})=\sqrt{\frac{1}{n-1}\left(1+\frac{1}{2} \widehat{SR}^{2}-\gamma\_{3} \widehat{SR}+\frac{\gamma\_{4}-3}{4} \widehat{SR}^{2}\right)}\end{equation}[/latex]

Besides, remember that the [latex]PSR[/latex] is a measure that, given a [latex]\widehat{SR}[/latex] and its variance ([latex]\hat{\sigma}(\widehat{SR})[/latex]), indicates the probability that in the future the true SR will be greater than a given benchmark ([latex]SR^{\*}[/latex]). The formula for its calculation is as follows:

[latex]\begin{equation}\widehat{P S R}\left(SR^{\*}\right)=Z\left[\frac{\left(\widehat{SR}-SR^{\*}\right)}{\hat{\sigma}(\widehat{S R})}\right]\end{equation}[/latex]

## Multiple Testing Problem

Alright, now we know that we should **look for strategies with a high PSR**, instead of a high SR. Suppose therefore that we are Quants looking for a new strategy with the best possible PSR. So we make use of our large financial data sets and high-performance computers, and launch thousands of backtests (if not millions), until we discover a strategy with an annualized SR of 2.50 and a PSR of 0.99.

Immediately, we could think that our backtest has been a resounding success. We have found a strategy with a very high estimated SR, and with a 99% chance that our strategy will have positive returns in the future!

But we would be falling into the *Multiple Testing Problem*, given that, without realizing it, **when testing more and more strategies the probability of choosing false positive increases**. The more backtests we do, the more likely it is that by pure chance a strategy obtains very good results in the analyzed period, but not due to an edge of the strategy but by pure chance.

In the end, if we flip 100,000 times 10 coins at a time, and each of those times we do it with a different angle, it is almost certain that in some of those simulations 10 heads will come out. This could lead us to think that we have found the perfect angle that will always get heads when flipping a coin. But, as it is obvious, this is not the case. It is random that 10 heads have come out in that specific simulation. Well, the same thing happens with investment strategies.

## Selection Bias

A possible solution to the above problem would be the Hold-out method. Which consists of dividing the analyzed data into two non-overlapping subsets: the in-sample subset (*IS*), and the out-of-sample subset (*OOS*). The idea is to discover a model with good results in the *IS* period. And then, validate that in the *OOS* period that these results were not the result of chance.

A priori it might seem that with this method we have solved the *Multiple Testing Problem*. In fact, it is the approach to this problem used by many researchers. But, without us realizing it, in the end, we could fall into a very similar problem: Selection Bias. In the end, we have found a strategy with good results in both periods separately. However, the question would be: **how many other strategies did we test and did not pass the hold-out filter?**

Ultimately, we return to the same point as before: if we apply the hold-out method to enough combinations, in the end, there will always be one that gives us good results, not due to an edge, but purely by chance. We have been fooled by randomness!

> The hold-out method does not take into account the number of trials attempted before selecting a model, and consequently is subjected to selection bias.
>
> Marcos López de Prado

## Expected Maximum Sharpe Ratio

In the paper we referred to, López de Prado and Bailey proves that the expected maximum of [latex]\widehat{SR}[/latex] after [latex]N >> 1[/latex] independent trials can be approximated as:

[latex]\begin{equation}\begin{aligned}E\left[\max \left\{\widehat{S R}\_{n}\right\}\right] & \approx E\left[\left\{\widehat{S R}\_{n}\right\}\right] \\&+\sqrt{V\left[\left\{\widehat{S R}\_{n}\right\}\right]}\left((1-\gamma) Z^{-1}\left[1-\frac{1}{N}\right]+\gamma Z^{-1}\left[1-\frac{1}{N} e^{-1}\right]\right)\end{aligned}\end{equation}[/latex]

where [latex]V\left[\left\{\widehat{S R}\_{n}\right\}\right][/latex] is the variance across the trials’ estimated SR, [latex]\gamma[/latex] (approx. 0.5772) is the Euler-Mascheroni constant, [latex]Z[/latex] is the [cumulative function](https://en.wikipedia.org/wiki/Cumulative_distribution_function) of the standard Normal distribution, [latex]N[/latex] is the number of independent trials, and [latex]e[/latex] is Euler’s number.

Using the above formula, and assuming that E[SR]=0 and V[SR]=1, we can quickly check that after only 1,000 independent backtests the expected maximum Sharpe Ratio is 3.26, even if the true SR of the strategy is zero!

## Solution: Deflated Sharpe Ratio

As a result, López de Prado and Bailey developed the *Deflated Sharpe Ratio* (DSR) that **computes the probability that an estimated SR is statistically significant, after controlling for the inflationary effect of multiple trials, non-normal returns, and shorter sample lengths.**

Essentially, DSR is a PSR where the rejection threshold is adjusted to reflect the multiplicity of trials:

[latex]\begin{equation}\widehat{DSR} \equiv \widehat{PSR}\left(\widehat{SR}\_{0}\right)=Z\left[\frac{\left(\widehat{SR}-SR^{\*}\right)}{\hat{\sigma}(\widehat{S R})}\right]\end{equation}[/latex][latex]\begin{equation}=Z\left[\frac{\left(\widehat{SR}-SR^{\*}\right) \sqrt{n-1}}{\sqrt{1+\frac{1}{2} \widehat{SR}^{2}-\gamma\_{3} \widehat{SR}+\frac{\gamma\_{4}-3}{4} \widehat{SR}^{2}}}\right]\end{equation}[/latex]

where [latex]\begin{equation}\begin{aligned} \widehat{SR}\_{0} = E\left[\max \left\{\widehat{S R}\_{n}\right\}\right] \end{aligned} \end{equation}[/latex], assuming that E[SR]=0. We also use information concerning the selected strategy: [latex]\widehat{SR}[/latex] its estimated SR, [latex]T[/latex] track-record length, [latex]\gamma\_{3}[/latex] skewness, [latex]\gamma\_{4}[/latex] kurtosis.

### How to calculate independent trials?

Surely you are wondering what exactly does «independent trials» mean, what is the difference between [latex]N[/latex] and [latex]M[/latex]? Well, [latex]M[/latex] is the number of total trials, and [latex]N[/latex] is the number of trials that are sufficiently different from each other, sufficiently uncorrelated.

To calculate [latex]N[/latex] there are several approaches, here we are going to choose the simplest of them which consists of calculating the average correlation of all the trials [latex]\hat{\rho}[/latex]. And calculate [latex]N[/latex] as [latex]\begin{equation}{N}=\hat{\rho}+(1-\hat{\rho}) M\end{equation}[/latex].

### Practical example in Python

In this [jupyter notebook](https://github.com/rubenbriones/Probabilistic-Sharpe-Ratio/blob/master/notebooks/Deflated%20Sharpe%20Ratio%20Example.ipynb) you can check a practical example, coded in Python. On it the concepts we have seen so far can help us to determine if a backtest with a high Sharpe Ratio is a consequence of a good investment strategy or if it is a trap of randomness.

As a summary, the study case analyzed in the notebook consisted of the following steps:

1. We have defined an investment universe made up of 5 ETFs, during the 2019-2020 period (including the COVID drawdown).
2. **We launched 5,000 simulations on this universe in which for each day we assign random weights to all the ETFs**. *For making the results of the study more obvious, we have done the trading decisions of the simulations totally random. But in practice, these would be determined by different configurations of the entry signal, stop-loss, take-profit, and any other strategy parameter.*
3. We analyzed the SRs of each backtest. And we see that **the best of them has an annualized SR of 1.92!**
4. But since we know that the SR is biased by the assumption of normal-returns, and by not taking into account the length of the track-record, we calculate the *Probabilistic Sharpe Ratio* that does take into account both. And it gives us a **PSR of 0.99**!
5. Up to this point, we can say that we have found a strategy with a Sharpe Ratio of 1.92, with almost two years of track record. And statistically it has a 99% probability that in the future it will have a positive SR. *At this point, many Quants would deploy this strategy in production…*
6. But since we are already aware of the *Multiple Testing Problem* and the *Bias Selection*, we decided that the PSR is not a useful metric for this case (due to a large number of backtests done). So we decided to calculate the *Deflated Sharpe Ratio*. **And it gives a poor DSR of 0.82**.

#### Conclusions

**Therefore, we can conclude that despite the high SR and PSR of the strategy, we do not have a high enough confidence level (usually, at least 95% required) to ensure that the strategy will obtain positive returns in the future.**

In this case, we knew in advance that despite the high SR and PSR, the strategy was really merely random and it was impossible that it had an edge. But in other not so obvious cases, the DSR will be of enormous helpful to us to identify if the good results of a backtest are simply due to overfitting and selection bias, or to a true edge.

Anyway, I encourage you to review the notebook by yourself, clone the repository, and do new experiments to check the usefulness of the *Deflated Sharpe Ratio*.

### Bonus: When should we stop testing?

Given that increasing the number of backtests (trials) increases the probability of finding a false positive, the question that would arise for all of us is: when should we consider a [latex]\widehat{SR}[/latex] good enough, to stop testing more strategies in order not to increase unnecessarily that probability of finding a false positive?

An elegant answer can be found in **the theory of Optimal Stopping** (the *“secretary problem”*):

1. Sample randomly [latex]1/e[/latex] (roughly 37%) of the total strategies that we want to backtest and measure their results.
2. Then test one by one of the remaining strategies, until we find a configuration that is better than all those tested so far.

## Key takeaways

* It is guaranteed that a researcher will always find a misleadingly profitable strategy after a sufficient number of trials. A strategy with a high estimated SR.
* The Deflated Sharpe Ratio can be used to determine the probability that a discovered strategy is a false positive. The key is to record all trials and determine correctly the clusters of effectively independent trials.
* Multiple testing exercises should be carefully planned in advance, so as to avoid running an unnecessarily large number of trials. This is because every additional trial irremediably increases the probability of a false positive.

## References

* [[1]](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551) Marcos López de Prado and David Bailey (2014). *The Deflated Sharpe Ratio: correcting for selection bias, backtest overfitting, and non-normality.*
* [[2]](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1821643) Marcos López de Prado and David Bailey (2012). *The Sharpe ratio efficient frontier*.

## related posts

[[All](https://quantdare.com/category/all/) [## AI case study: Long/Short Strategy](https://quantdare.com/ai-case-study-long-short-strategy/)](https://quantdare.com/ai-case-study-long-short-strategy/)[### Javier Cárdenas](https://quantdare.com/author/javier-cardenas/)

[[Artificial Intelligence](https://quantdare.com/category/artificial-intelligence/) [## A new way to train neural networks: the Forward-Forward algorithm](https://quantdare.com/a-new-way-to-train-neural-networks-the-forward-forward-algorithm/)](https://quantdare.com/a-new-way-to-train-neural-networks-the-forward-forward-algorithm/)[### Alejandro Pérez](https://quantdare.com/author/aperez/)

[[All](https://quantdare.com/category/all/) [## Unlocking Wealth and Diversification: The Powerful Advantages of Investing in Conglomerate Stocks](https://quantdare.com/unlocking-wealth-and-diversification-the-powerful-advantages-of-investing-in-conglomerate-stocks/)](https://quantdare.com/unlocking-wealth-and-diversification-the-powerful-advantages-of-investing-in-conglomerate-stocks/)[### Konstantinos Pappas](https://quantdare.com/author/konstantinos-pappas/)

[[All](https://quantdare.com/category/all/) [## Clustering Forex Market](https://quantdare.com/forex-clustering/)](https://quantdare.com/forex-clustering/)[### aporras](https://quantdare.com/author/xristica/)

Los comentarios están cerrados.
