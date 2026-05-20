# Overfitting and How to Mitigate It

*Published at 1719307964.422943*

Algorithmic trading uses computer algorithms to automate trading decisions. These systems manage investment portfolios and execute orders with the goal of generating positive returns in the financial market. A key component of algorithmic trading is the identification of trading signals, also known as alphas.

In the field of quantitative trading, there are two primary methods for generating alphas. The first method is idea-driven, where alphas are derived from various sources, including trading hypotheses, journal papers, anecdotes, or spontaneous ideas. Quantitative traders transform these ideas into potential trading signals. The second method is data-driven, where alphas are generated from technical analysis, pattern recognition, machine learning models, or economic analysis of financial reports. These alphas can be extracted from datasets that are either collected internally or obtained from external data service providers.

No matter where the alpha comes from, a comprehensive and rigorous verification process is essential. Algorithmic traders estimate the potential for positive returns in real trading scenarios. Backtesting is a vital part of this process, as it evaluates potential returns and considers the maximum drawdown a strategy might encounter. Top-tier quantitative trading firms prioritize robust backtesting and market simulations to solidify their investment performance. This article highlights the fundamental concepts in backtesting and the common pitfalls of overfitting in this process.

# Backtesting

In finance, predictions based on time-series data do not assure absolute certainty for individual instances. In fact, predictions are only feasible in a statistical sense: random errors average out to a reasonable degree of accuracy only over a large number of predictions. Even leading trading firms experience losses in real trading, despite positive returns in market simulations. It’s thus important to allocate capital appropriately among different alphas and trading strategies.

In financial research, many assumptions prove incorrect. Many experiments yield negative results. Only a handful of trading signals have the potential to consistently generate profits in real trading. This is because financial markets often behave counterintuitively. The initial model may work in the market but only have weak effects, overshadowed by other factors. Market simulations and backtesting are therefore essential to figure out potential strategies.

Backtesting enables quantitative traders to simulate their strategies on historical data. It recreates trades that would have happened in the past based on set rules. This allows traders to evaluate the effectiveness of their strategies. The underlying assumption is that if a strategy performed well in the past, it’s likely to do well in the future. A model that didn’t perform well in the past is unlikely to be considered for real trading.

Backtesting also provides vital statistical feedback on specific trading strategies. Key metrics include net profit or loss, volatility, maximum drawdown, annualized return, and risk-adjusted measures such as Sharpe ratio, Sortino ratio, and Information ratio. These metrics help traders compare the performance of their system with existing industry standards.

There are several methods for backtesting. The simplest is the explanatory approach, which examines historical trading data. For example, an algorithmic trader might test a new rule-based Smart Beta portfolio on historical data to predict its future potential. Another technique is the Monte Carlo simulation, which models the uncertainties in the financial market that influence stock and futures prices, resulting in a range of potential returns. A more sophisticated method involves using advanced pricing models to determine the price of assets and derivatives. Examples include the Black-Scholes model (1973), the stochastic volatility model (1976), the jump-diffusion model (1996), and recent data-driven models enabled by advancements in computing and artificial intelligence. The research of neural networks in the past decade, such as variational autoencoders (VAEs) and generative adversarial networks (GANs) shows promising potential in working with financial time-series data.

# Overfitting

In real trading, however, many factors will influence investment performance. Positive backtesting results do not necessarily translate into a profitable strategy for several reasons. First, the current financial market may differ from the historical period used in backtesting. Market rules and participants are constantly changing, and new technologies often change trading behaviors. Second, real trades incur commissions and transaction costs, and the trades themselves can impact the market at a large net asset value. This leads to price slippage and implementation shortfall in unfavorable directions. Lastly, overfitting could occur, where algorithmic traders select alphas from favorable backtesting results due to random chance or emotional bias, but these alphas may have limited predictive power.

Overfitting is the inherent risk in any backtesting process. It happens when a trading strategy is overly adjusted to fit historical data, capturing not just the underlying market signals but also noise and random fluctuations. A seemingly significant correlation or spurious relationship from the historical data may lack the fundamental causes and economic grounds to recur in the future. With enormous computing power, the likelihood of discovering random correlations increases, as does the risk of overfitting.

Complex trading strategies that excel on historical data may have detailed rules and parameters specifically optimized for the training set. However, they may not perform well with new, unseen data because they were optimized under specific conditions, such as the pandemic, which may not recur at a similar scale.

Similar to machine learning, there’s always the bias and variance trade-off in finance. Overfitting happens when a trading strategy captures both the true underlying patterns and excessive variance. Selecting results with impressive backtesting, known as cherry-picking, is a behavioral bias that often leads to overfitting. Excessive parameter optimization can also result in overfitting. Therefore, it’s critical to strike a balance between fitting the data and maintaining the robustness of the strategy.

# How to Mitigate Overfitting

In statistics and machine learning, different methods have been proposed to avoid overfitting during the learning process. Examples are tenfold cross-validation, regularization, and prior probability. Recently, academic research papers addressing overfitting have been published in the field of quantitative finance. Drawing from concepts in statistical learning, the following are some strategies for mitigating overfitting in backtesting.

**Out-of-sample testing.** This involves dividing historical time series data into two or more segments. The idea is to reserve a portion of the historical data to serve as unseen test sets. This reserved partition acts as a proxy for real trading. It’s important to note that out-of-sample periods should not be prior to the training data, as the training data may already absorb past events.

**Cross-validation.** This is a technique used to evaluate how effectively a model can generalize to new, unseen data, similar to out-of-sample testing. An example is in smart beta development. Good alphas typically work across various assets, exchanges, and regions. For example, equity models created in the US can be applied to Asian markets, or models developed for one exchange can be used on another within the same country.

**Increase in-sample Sharpe ratio requirement.** A higher Sharpe ratio in the training set reduces the risk of overfitting in the validation set and in real trading. It’s often recommended to train the model over a longer historical period to capture a diverse range of market events. Extending the backtesting period reduces the chance of accidental overfitting. The number of backtesting days needed to confirm a certain Sharpe ratio level often grows exponentially with the ratio target.

**Minimize parameters and operations.** Overfitting is often a result of a model having too many parameters. These parameters enable the model to closely fit the training data, capturing more noise than actual signals. By reducing the number of parameters helps models become less susceptible to changes in parameters. Fewer parameters often lead to improved generalization.

**Walk-forward optimization.** This is a technique that helps mitigate the risk of overfitting by dividing historical data into overlapping periods. Each segment consists of an in-sample period and an out-of-sample period. For each segment, the parameters are trained using the in-sample period and evaluated on an out-of-sample period. This process is repeated over all segments, and the average results from all out-of-sample periods give a realistic estimate of the strategy’s performance. This method helps find adaptive strategies to different market conditions, and prevent overfitting to a specific timeframe.

# Conclusion

Creating portfolios with genuine alpha strategies that capture the essence of market dynamics leads to profitability. While backtesting is crucial for discovering these alphas, it can also introduce overfitting, resulting in a misleading sense of assurance in profitability. Building a robust system requires finding the right mix of sophistication and adaptability to ensure strategies succeed in real-world conditions, not just in historical simulations and paper trading.

To prevent overfitting, it’s essential to pinpoint robust alphas that serve as a reliable guide. These alphas should be resilient to changes in market specifics or conditions. Financial markets are often characterized by their historical tendencies and gradual evolution, reflecting traders’ activities. An alpha that was effective in the past may not be profitable moving forward. Continuously refining strategies with a robust backtesting framework is crucial for future success.

---

###### Glossary

![]()
