Advertisement

![Advertisement](//pubads.g.doubleclick.net/gampad/ad?iu=/270604982/springerlink/40163/article&sz=728x90&pos=top&articleid=s40163-018-0093-5)
![Springer Nature Link](/oscar-static/images/darwin/header/img/logo-springer-nature-link-05805fde18.svg)

# To the moon: defining and detecting cryptocurrency pump-and-dumps

You have full access to this [open access](https://www.springernature.com/gp/open-science/about/the-fundamentals-of-open-access-and-open-research) article

![](https://media.springernature.com/w72/springer-static/cover-hires/journal/40163?as=webp)

195k Accesses

166 Citations

45
Altmetric

1 Mention

[Explore all metrics](/article/10.1186/s40163-018-0093-5/metrics)

## Abstract

Pump-and-dump schemes are fraudulent price manipulations through the spread of misinformation and have been around in economic settings since at least the 1700s. With new technologies around cryptocurrency trading, the problem has intensified to a shorter time scale and broader scope. The scientific literature on cryptocurrency pump-and-dump schemes is scarce, and government regulation has not yet caught up, leaving cryptocurrencies particularly vulnerable to this type of market manipulation. This paper examines existing information on pump-and-dump schemes from classical economic literature, synthesises this with cryptocurrencies, and proposes criteria that can be used to define a cryptocurrency pump-and-dump. These pump-and-dump patterns exhibit anomalous behaviour; thus, techniques from anomaly detection research are utilised to locate points of anomalous trading activity in order to flag potential pump-and-dump activity. The findings suggest that there are some signals in the trading data that might help detect pump-and-dump schemes, and we demonstrate these in our detection system by examining several real-world cases. Moreover, we found that fraudulent activity clusters on specific cryptocurrency exchanges and coins. The approach, data, and findings of this paper might form a basis for further research into this emerging fraud problem and could ultimately inform crime prevention.

### Similar content being viewed by others

![](https://media.springernature.com/w215h120/springer-static/image/art%3A10.1007%2Fs42521-021-00034-6/MediaObjects/42521_2021_34_Fig1_HTML.png)

### [Profitability of cryptocurrency Pump and Dump schemes](https://link.springer.com/10.1007/s42521-021-00034-6?fromPaywallRec=false)

![](https://media.springernature.com/w92h120/springer-static/cover-hires/book/978-3-030-95391-1?as=webp)

### [Short and Distort Manipulations in the Cryptocurrency Market: Case Study, Patterns and Detection](https://link.springer.com/10.1007/978-3-030-95391-1_31?fromPaywallRec=false)

![](https://media.springernature.com/w215h120/springer-static/image/art%3A10.1007%2Fs42521-024-00121-4/MediaObjects/42521_2024_121_Fig1_HTML.png)

### [Detecting Pump &Dump stock market manipulation from online forums](https://link.springer.com/10.1007/s42521-024-00121-4?fromPaywallRec=false)

### Explore related subjects

## Introduction

Cryptocurrencies have been increasingly gaining the attention of the public, and their use as an investment platform has been on the rise. These digital currencies facilitate payments in the online sector without the need for a central authority (e.g., a bank). The market for cryptocurrencies is rapidly expanding, and at the time of writing currently had a market capitalisation of around 300 billion US dollars (CoinMarketCap [2018](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")) making it comparable to the GDP of Denmark (Cryptocurrency Prices [2018](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")). Despite the vast amounts of money being invested and traded into cryptocurrencies, they are uncharted territory and are for a large part unregulated. The lack of regulation, combined with their technical complexity, makes them an attractive target for scammers who would seek to prey on the misinformed. One such scam is known as a pump-and-dump (P&D), where bad actors attempt to make a profit by spreading misinformation about a commodity (i.e., a specific cryptocurrency coin) to artificially raise the price (Kramer [2004](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")). This scam has a long history in traditional economic settings, going as far back as London’s South Sea Company in the 1700s (Brooker [1998](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")), then found a natural home in penny stocks and on the Internet (Kramer [2004](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353."); Temple [2000](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")), and has now recently appeared in cryptocurrency markets (Khan [2018](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                ."); Mac and Lytvynenko [2018](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                ."); Martineau [2018](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1.")).

The academic literature on cryptocurrency (crypto) P&D schemes is scarce (for an exception, see the recent working paper of Li, Shin, & Wang, [2018](/article/10.1186/s40163-018-0093-5#ref-CR01 "Li, T., Shin, D., & Wang, B. (2018). Cryptocurrency Pump-and-Dump Schemes. Available at SSRN 3267041")). Thus, this paper will give an overview of what is currently known about the topic from blogs and news sites. To provide a theoretical angle, economic literature related to the topic is examined, and this information synthesised with cryptocurrencies by highlighting the similarities and potential differences. As these patterns are a type of anomaly, literature on anomaly detection algorithms is also discussed. The goal is to propose some defining criteria for what a crypto P&D is and to subsequently use this information to detect points in exchange data that match these criteria, forming a foundation for further research.

### What is a pump-and-dump scheme?

A pump-and-dump scheme is a type of fraud in which the offenders accumulate a commodity over a period, then artificially inflate the price through means of spreading misinformation (pumping), before selling off what they bought to unsuspecting buyers at the higher price (dumping). Since the price was inflated artificially, the price usually drops, leaving buyers who bought on the strength of the false information at a loss. While we do not provide a rigorous crime script analysis (see Borrion [2013](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353."); Keatley [2018](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353."); Warren et al. [2017](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1.")) here, Fig. [1](/article/10.1186/s40163-018-0093-5#Fig1) can be viewed as a script abstraction of three main stages—accumulation, pump, and dump. The accumulation phase usually occurs incrementally over a more extended period of time, in order to avoid raising the price before the pump.

![Fig. 1](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig1_HTML.png)

Schematic abstraction of the three phases of a pump-and-dump operation

### What are cryptocurrencies?

Cryptocurrencies are a digital medium of exchange, and they usually rely on cryptography instead of a central institution to prevent problems like counterfeiting. For example, the most popular cryptocurrency is Bitcoin (BTC), and some of its benefits are that it allows for trustless and de-centralised transactions since it is impossible to reverse a payment, and there are no third parties (e.g., banks) involved (Nakamoto [2008](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")). In traditional financial systems, a customer trusts the third-party (e.g., a bank) to update their ledger to reflect the customer’s accounts balance. To the contrary, with Bitcoin, this ledger is distributed across a network, and everyone on the network possesses a copy and can—in principle—verify its contents. That public ledger is known as the blockchain and is the core technology upon which Bitcoin and many other cryptocurrencies rest. There are now many different types of cryptocurrencies, with less widely known ones referred to as ‘altcoins’, and they all run on slightly different technical principles, with different utilities and benefits (Bitcoin Magazine [2017](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")). Besides Bitcoin, some of the other currently more popular cryptocurrencies include Ethereum (<https://ethereum.org/>), Ripple (<https://litecoin.org/>), and Litecoin (<https://litecoin.org/>).

### Aims of this paper

In this paper, we set out to achieve three primary goals. First, absent a body of academic research on cryptocurrency pump-and-dump schemes, we provided an initial working formalisation of crypto P&Ds identifying criteria that might help in locating and ideally preventing this emerging fraud problem. Second, we utilise these indicators and propose an automated anomaly detection approach for locating suspicious transactions patterns. Third, to better understand the crypto P&D phenomenon, we zoom in on the exchange level and on the cryptocurrency pairings level. The overarching aim of this paper is to spark academic interest in the topic and to introduce P&Ds as an emerging problem.

### Pump-and-dump schemes in the traditional economic context

In the early eighteenth century, con artists who owned stock in the South Sea Company began to make false claims about the company and its profits. The goal was to artificially raise the price of the stock, and then sell it off to misinformed buyers who were led to believe that they were buying a promising commodity. This was referred to as the *South Sea Bubble* and serves as an early documented example of a P&D scheme (Bartels [2000](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353."); Brooker [1998](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")).

In modern times, P&D schemes have predominantly been Internet-based focusing on so-called “penny” or “microcap” stocks, which are smaller companies that do not meet the requirements to be listed on the larger exchanges such as the NASDAQ (Dugan [2002](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353."); Temple [2000](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")). Microcap stock exchanges are not held to the same standard of regulation, which implies that there is usually not as much information about the companies that are listed making them easier to manipulate. For example, in the US, large public companies file publicly available reports with the Security Exchange Commission (SEC) which are often analysed by professionals (US Securities and Exchange Commission [2017](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")). Access to and the verification of information is typically more difficult with microcap companies. Misinformation about the stocks is often spread through email spam which has been found to have a net positive effect on the stock price (i.e., the spam is effective in increasing the price, see Bouraoui [2009](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")). In the United States, it is illegal to run a P&D operation on penny stocks, and there are multiple cases of people having charges pressed against them for their participation in a P&D scam (“Developments in Banking and Financial Law: 2013,” [2014](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1."); Yang and Worden [2015](/article/10.1186/s40163-018-0093-5#ref-CR28 "U.S. Commodity Futures Trading Commission. (2018). CFTC issues first pump-and-dump virtual currency customer protection advisory. Retrieved June 27, 2018, from
                  https://www.cftc.gov/PressRoom/PressReleases/pr7697-18

                .")).

### Pump-and-dump schemes in the cryptocurrency context

There is currently a lack of academic literature on cryptocurrency pump-and-dump schemes, so this section seeks to give an overview of the current landscape of cryptocurrency P&D schemes as they have been realised in various blog posts and news articles. In the cryptocurrency context there is an overall slightly different modus operandi than in the traditional context of penny stocks; specifically, this has been seen in the rise of dedicated public P&D groups. These groups have emerged in online chat rooms such as Discord (<https://discordapp.com>) and Telegram (<https://telegram.org>) with the sole purpose of organising pump-and-dump scams on select cryptocurrencies (Fig. [2](/article/10.1186/s40163-018-0093-5#Fig2)). The number of members in some of these groups is reported to have been as high as 200,000, with smaller groups still running about 2000 (Martineau [2018](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1.")). Price increases of up to 950% have been witnessed, demonstrating the extent of manipulation these groups are capable of (Thompson [2018](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1.")). For these P&D groups to achieve the best results, several reports of activity show that they almost exclusively target less popular coins, specifically those with a low market cap and low circulation, since they are deemed easier to manipulate (Khan [2018](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                ."); Mac and Lytvynenko [2018](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                ."); Town [2018](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")). Estimating the full scope of the damages caused by cryptocurrency pump-and-dumps is difficult; yet there is some evidence to show that such schemes are generating millions of dollars of trading activity. The Wall Street Journal published an investigative article that looked at public pump-and-dump groups and 6 months of trading activity. They found $825 million linked to pump-and-dump schemes, with one group alone accounting for $222 million in trades (Shifflett [2018](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")). This gives a glimpse of how much monetary activity is generated by these groups, the impact of which could be even greater as many groups presumably operate in private or invite-only groups.

![Fig. 2](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig2_HTML.png)

Example of a pump-and-dump chat group with over 40,000 members. Left: Telegram group ‘Rocket dump’. Right: Corresponding exchange data (Binance) of the targeted coin (Yoyo) showing the effect of the pump. The yellow, purple, and maroon lines represent the moving average for the last 7, 25, and 99 days respectively

The pump-and-dump procedure usually consists of the group leaders declaring that a pump will take place at a particular time on a particular exchange, and only after the specified time will the coin be announced (see Fig. [2](/article/10.1186/s40163-018-0093-5#Fig2)). After the coin is announced members of the group chat try to be amongst the first to buy the coin, in order to secure more profits. Indeed, if they are too slow, they may end up buying at the peak and be unable to sell for a profit. The ‘hype’ around buying the coin once the pump is announced is due to the short timescale of these schemes: Martineau ([2018](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1.")) reported on two pumps that reached their peaks within 5–10 min. During the pumping phase, users are often encouraged to spread misinformation about the coin, in an attempt to trick others into buying it, allowing them to sell easier. The misinformation varies, but some common tactics include false news stories, non-existent projects, fake partnerships, or fake celebrity endorsements (Martineau [2018](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1."); Town [2018](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")). Consider the example where a group of offenders impersonated Internet entrepreneur John Mcafee’s twitter account
@OfficialMcafee
 by including an extra ‘
l
’ in the username (Mac and Lytvynenko [2018](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")). The fake account sent a positive tweet about a particular altcoin and all the users in the P&D group were told to retweet it. Within 5 min. The price of the coin had gone from $30,- to $45,-, collapsing back down to $30,- after about 20 min. Anything which creates a general air of positivity is fair game because the goal is to dump their coins on unwitting investors who have not done their due diligence, by preying on their fear of missing out on the next big crypto investment.

In a move to secure profit for themselves, many pump-and-dump group leaders will often use their insider information to their advantage: because they know which coin will be pumped, they can pre-purchase the coin for a lower price before they announce it. This guarantees them profit while leaving other users to essentially gamble on whether or not they can predict the peak. The fear of missing out and the potential to beat the odds might drive prospective cryptocurrency investors into joining a pump. Group leaders can also guarantee profits by offering access to the pump notification at an earlier stage prior to the group-wide announcement, in exchange for payment. Even a few seconds of temporal advantage are sufficient to potentially place buy orders before others, and thereby obtain cheaper coins, hence increasing the buyer’s benefit from the of the pump-and-dump operation (Martineau [2018](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1.")).

Due to the fact that the technology behind cryptocurrencies is relatively new, and that most exchanges are unregulated, pump-and-dump manipulation is currently not always illegal; and even where it is, it cannot always be easily enforced. However, governing bodies are beginning to realise the problem, and in the United States the Commodity Futures Trading Commission has issued guidelines on how to avoid P&D scams, as well as offering a whistle blower program (U.S. Commodity Futures Trading Commission [2018](/article/10.1186/s40163-018-0093-5#ref-CR28 "U.S. Commodity Futures Trading Commission. (2018). CFTC issues first pump-and-dump virtual currency customer protection advisory. Retrieved June 27, 2018, from
                  https://www.cftc.gov/PressRoom/PressReleases/pr7697-18

                .")).

### Defining a cryptocurrency pump-and-dump

Mitigating and preventing pump-and-dump schemes will require knowledge about their operation, and thus the detection of these pump-and-dump schemes is a step towards the goal of mitigation. To begin searching for and identifying potential P&D type patterns in exchange data, a working definition for what constitutes a P&D is needed. A proposal for defining criteria will be given in this section by summarising the insights regarding traditional and crypto P&D schemes that have been outlined in the previous section. Table [1](/article/10.1186/s40163-018-0093-5#Tab1) summarises some of the key similarities and differences with the respect to the target, tactic, and timescale of traditional penny stock and crypto pump-and-dump schemes.

Table [1](/article/10.1186/s40163-018-0093-5#Tab1) indicates that a crypto P&D seems similar to a penny stock P&D in that assets that share the same properties are targeted. However, in general, it appears that as a result of different tactics the time scale has been narrowed and moved towards near real-time. Just as the digitisation of information via the Internet increased the rate of P&D scams on penny stocks, so too it seems the digitisation of currency itself has increased the rate and speed at which a P&D can take place.

Using the identified characteristics of crypto P&Ds allows us to formulate criteria that could be helpful in detecting P&D patterns in exchange data (Table [2](/article/10.1186/s40163-018-0093-5#Tab2)). Specifically, we argue that indicators of P&Ds can be subdivided into *breakout indicators* which refer to the signals that will always be present during a pump-and-dump, and *reinforcers* which refer to indicators which may help increase the confidence that the observed data point is the result of manipulation. The volume and price are discussed with an *estimation window*, referring to a collection of previous data points, of some user-specified length. For example, a moving average over a previously defined time period could be used, which would allow for discussing spikes with regards to some local history. This is not to say that the proposed criteria are sufficient to encompass all crypto P&Ds. Instead, we chose to resort to conservative criteria that are necessary for a P&D and that appear to have emerged based on the information in the previous section.

## Method

### Data

To obtain data for analysis, the CCXT (Ccxt [2018](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")) library was used which provides a unified way to programmatically access the data from a variety of cryptocurrency exchanges using the python programming language. Despite the unified access, the exchanges still differ in the amount of historical data they serve, and in the cryptocurrencies, they have listed. Therefore, decisions had to be made on what data to obtain.

#### Data availability statement

The data and code to reproduce the analysis and data retrieval are publicly available at <https://osf.io/827wd/>.

#### Format of cryptocurrency exchange data

Cryptocurrencies are listed on exchanges in symbol pairs denoting which currencies are trading for which. For example, to trade Litecoin (LTC) for Bitcoin (BTC), the symbol pair listed is “LTC/BTC”. Exchange data are returned as a set of Open High Low Close Volume (OHLCV) entries, detailing the trading data for that particular moment in time. Table [3](/article/10.1186/s40163-018-0093-5#Tab3) shows an example of the OHLCV terminology in its raw representation and Fig. [3](/article/10.1186/s40163-018-0093-5#Fig3) shows the candlestick chart representation of OHLCV data. The top and bottom wicks represent the highest and lowest value respectively, while the coloured candle represents whether the closing price was higher than the opening price (green) or lower than the opening price (red). The top of a green candle is the closing price, and the bottom is the opening price, and vice versa for a red candle. Candles can represent a variety of timeframes, but they often represent 30 min, 1 h, or 24 h. Smaller candle sizes mean more data per time period, so usually the smaller the candle size, the fewer days one can retrieve from an exchange, due to imposed limitations on the amount of data retrievable using their API. One-hour candles were chosen as a compromise between the resolution of the data and the amount of historical data available.

![Fig. 3](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig3_HTML.png)

An example of a candlestick chart for the YOYOW/BTC trading pair

#### Obtaining the data

The CCXT library (<https://github.com/ccxt/ccxt>) supports access to 115 different cryptocurrency exchanges. However, not all of these permit the public retrieval of historical data. After filtering for those conditions, 24 exchanges remained. To make the results more robust, the 24 candidate exchanges were filtered further to exchanges with at least 50 symbol pairs and at least 20 days of historical 1-h OHLCV data. In total, five exchanges matched all the criteria, and 480 candles (~ 20 days) of data for every available symbol pair were pulled from each of these exchanges (see [Appendix](/article/10.1186/s40163-018-0093-5#Sec43)).

### Analytical approach

A successful P&D will often exhibit a marked spike in price and volume (see Table [2](/article/10.1186/s40163-018-0093-5#Tab2)) that can easily be detected by human observation. However, with hundreds of exchanges and symbol pairings, and trading transactions not bound to specific times during the day, it is impractical and infeasible to resort to a manual approach for the detection of P&Ds only. Therefore, we resorted to an automated detection approach using anomaly detection.

#### A brief introduction to anomaly detection

Data points which do not conform to the rest of a dataset are often referred to as anomalies or outliers. Anomaly detection is the process of identifying these non-conforming points (Chandola et al. [2009](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")). Anomaly detection techniques can be broadly categorised into supervised and unsupervised anomaly detection. Supervised anomaly detection relies on a training data set to learn what “normal” is for the domain. The latter hinges on the ability to acquire an adequately sized training set, something which is often challenging. Conversely, unsupervised techniques rely on the assumption that anomalies are a rare occurrence in the data to prevent an excess of false signals. Here, it is the researcher’s or analyst’s task to determine the parameters that constitute an anomaly.

### Types of anomalies

There are various types of anomalies, which have been grouped into three major categories by Chandola et al. ([2009](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")): point anomalies, collective anomalies, and contextual anomalies. Point anomalies are merely points in the data which are anomalous to the rest of the data. An example would be an unusually large purchase relative to an individual’s historic spending behavior. Collective anomalies, on the other hand, refer to a situation in which one single data point may not be anomalous by itself. Instead, a co-occurrence or temporal proximity of anomalous data points might indicate behavior that is anomalous (e.g., a human electrocardiogram in which a single low point would not necessarily be anomalous, but consecutive low values would be indicative of a problem). Finally, contextual anomalies (also known as ‘conditional anomalies’, Song et al. [2007](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")) are data points which would only be considered anomalous in specific contexts. For example, a warm temperature in the winter would be anomalous, but in the summer would be considered normal.

### Anomaly detection in the context of crypto P&D schemes

In the context of this paper, unsupervised anomaly detection will be the focus, as no labelled training data is currently available for cryptocurrency pump-and-dump schemes (see [Discussion](/article/10.1186/s40163-018-0093-5#Sec38)). Conditional anomalies consider contextual information about the setting (Song et al. [2007](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353.")). This is described through *indicator variables*, of which the values may be directly indicative of an anomaly, and *environment variables*, whose variables are not directly indicative of an anomaly. The indicator variables are determined to be anomalous depending on the values of the environmental variables. In the current context this means the goal is to locate the breakout indicators, with respect to the reinforcers (Table [2](/article/10.1186/s40163-018-0093-5#Tab2)). For the scope of this paper, we do not consider the reinforcer of whether a symbol pair was present on multiple exchanges, due to the amount of data available. Thus, the goal is to locate corresponding price and volume spikes of coins with a low market cap that are trading for other cryptocurrencies. Due to the nature of P&D schemes, pumps are inherently local phenomena, so the goal is to detect local anomalies concerning recent history (i.e., to detect *local conditional point anomalies*).

### Anomaly anatomy

The anomaly detection technique utilised is a thresholding technique, inspired by previous research regarding denial of service attacks on a network (Siris and Papagalou [2004](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1.")). For a particular value, a simple moving average is computed by taking the average of previous values in a given time window, the length which is known as the lag factor. In this way, one can compare a value to the trend over a time period, as opposed to a singular value, allowing for the detection of local anomalies in comparison to recent history. This type of thresholding algorithm, allows us to provide a functioning baseline which further research could then expand upon with more sophisticated algorithms. Additionally, as more is learned about cryptocurrency pump-and-dump schemes, it is likely that more domain information (e.g., certain times, coins, or trading patterns) can be incorporated into the algorithms in an effort to increase the detection accuracy.

#### Price anomaly

If the high price at any given point is greater than the computed anomaly threshold for that point, then the point is determined to be anomalous. The anomaly threshold is computed using a given percentage increase \(\epsilon\), a lag factor \(\gamma\) and the simple moving average \(\mu\_{\gamma } \left( x \right)\) over the closing price. An instance *x* is a particular observation in the time series that is associated with the respective OHLCV values. In this case, *x* and \(\gamma\) can be considered as datetime objects, therefore \(x - \gamma\) would indicate moving backwards in the time series by a factor of \(\gamma\). The moving average is thus \(\mu\_{\gamma } \left( x \right) = \frac{{\mathop \sum \nolimits\_{i = x - \gamma }^{x} x\_{close} }}{\gamma }\) which is defined for all *x* where \(x - \gamma \ge 0\). The threshold for any given point after the time lag is defined as \(\epsilon \cdot \mu\_{\gamma } \left( x \right)\) giving us the point anomaly function:

#### Volume anomaly

The volume anomaly is defined almost identically to the above, except with the moving average computed as \(\mu\_{\gamma } \left( x \right) = \frac{{\mathop \sum \nolimits\_{i = x - \gamma }^{x} x\_{volume} }}{\gamma }\), resulting in:

#### Pump anomaly

The goal is to detect local conditional point anomalies, that is the co-occurrence of both a price anomaly and a volume anomaly. Additionally, the contextual information of whether or not the coin has a low market cap or is a crypto/crypto trading pair can be considered. There are perhaps other contextual indicators that could be investigated, though for the scope of this paper, only the two mentioned above will be looked at.

#### Low market cap

The market cap of a coin is defined as its price times the supply, and represents a way of judging the popularity, or size, of a coin. The market cap data were pulled from <https://coinmarketcap.com/>. The top ten coins from the dataset and the percent of the total market cap they account for are shown in Table [4](/article/10.1186/s40163-018-0093-5#Tab4). From this it can be seen that the top ten coins account for over 85% of the total market capitalisation, implying that a vast majority of coins have a much smaller market cap relative to the top. For the rest of this paper, “low market cap” will be defined as any coin below the 75th percentile (0.029%) of the total market cap.

## Results

This section investigates various values for the different parameters and shows how changing these affects the results found, with the goal of providing a suggestion for balanced parameters. Hopefully, these parameters could then be taken to a real-time system, to be further monitored and tuned as time progresses.

### Locating crypto pump-and-dumps

It is possible to formulate expectations based on the domain information presented in earlier sections. Since low market cap coins are targeted more often, we would expect to see more P&Ds amongst that group of coins. Similarly, crypto/crypto symbol pairs would also be expected to exhibit more P&D activity. Additionally, since this paper only simulates real-time detection, it is possible to look forward in time, and see which of the alleged pumps were followed by a marked drop in price, which could be an indication of users dumping their coins, making it more likely that the preceding pump was the result of nefarious activity (i.e., a pump-and-dump).

### Anomaly detection

#### Initial parameters

The idea behind the initial parameters for the detection system was to start off relatively ‘weak’, to give an initial starting point. We chose a 12 h estimation window, 25% volume increase and a 3% price increase. The results show that the 25% volume increase threshold was perhaps too low, due to the abundance of volume spikes found. Similarly, the 3% increase threshold for the price spikes also proved to be a bit too low, as indicated by (Table [5](/article/10.1186/s40163-018-0093-5#Tab5)). This led to finding over 9000 alleged pump-and-dumps across the dataset, which is an average of about nine P&Ds per coin over 20 days. While these may be interesting points to investigate, making the parameters stricter could help reduce false positives (i.e., false flags). Ultimately the goal is to find a set of balanced parameters that filter the points detected down to a more reasonable number that can then be further assessed by humans. The percentage of spikes that were found to have corresponding price dips was quite high with the initial parameters (90%), but this could be due to the vast number of spikes detected, to begin with. Figure [4](/article/10.1186/s40163-018-0093-5#Fig4) shows an example of an annotated candlestick chart using the initial parameters.

![Fig. 4](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig4_HTML.png)

Candlestick chart with anomaly detection indicators for the initial parameter set

#### Strict parameters

We increased the estimation window to 24 h, so it required a more drastic change in comparison to the average. Additionally, the volume and price thresholds were increased to 400% and 10% respectively (Fig. [5](/article/10.1186/s40163-018-0093-5#Fig5)). This led to detecting 920 alleged pump-and-dumps over 20 days, about 0.5 P&Ds per symbol. Price dips followed only 50% of the alleged pumps, and the total number of pump-and-dumps was consequently lower than with the initial parameter set.

![Fig. 5](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig5_HTML.png)

Candlestick chart with anomaly detection indicators for the strict parameter set

#### Balanced parameters

With the information gained from the previous two parameter sets, we attempted to find a balance between the two. The estimation window was returned to 12 h to constrain the search locally, and the volume and price thresholds were a compromise between the initial and strict parameter values, at 300% and 5% respectively. This resulted in about 1.6 pump-and-dumps per symbol, for a total of 2150 over the 20 days of data (Fig. [6](/article/10.1186/s40163-018-0093-5#Fig6)). Moreover, 75% of the alleged pumps were found to have corresponding price dumps; which could mean that in a real-time system, these parameters could lead to detecting points that would often be flagged for further investigation because they are possibly indicative of a P&D scheme.

![Fig. 6](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig6_HTML.png)

Candlestick chart with anomaly detection indicators for the balanced parameter set

### Closer inspection of the balanced parameter set

The results of the balanced parameter set were investigated closer to identify P&D dynamics at the exchange- and symbol pair-level. To do so, we filtered the results to only include observations where the P&Ds detected were on crypto/crypto symbol pairs with a low market cap.

#### Exchange-level findings

The number of P&Ds can be investigated on an exchange level, offering insight into which exchanges may be suitable targets for further investigation and mitigation techniques. An illustration of how the percentage of symbols analysed relates to the percentage of pumps detected is shown in Fig. [7](/article/10.1186/s40163-018-0093-5#Fig7). The exchanges *Binance* and *Bittrex* account for more of the pumps than the relative number of symbols analysed, suggesting these exchanges are utilised more for P&D schemes than others. Conversely, the exchange *Kraken* accounts for almost 6% of the symbols, yet less than 1% of the pumps. This is perhaps best explained by the fact that Kraken is one of the more regulated US-based exchanges, and deals mainly with crypto/fiat currency pairs, as opposed to crypto/crypto. These findings suggest that exchanges which offer more regulated trading would be less susceptible to P&D schemes.

![Fig. 7](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig7_HTML.png)

The percentage of symbols and alleged pumps per cryptocurrency exchange

#### Symbol pair-level findings

Breaking down the pump-and-dumps on a symbol level allows for a look into which cryptocurrencies, are disproportionately often affected, and hence more vulnerable (Table [6](/article/10.1186/s40163-018-0093-5#Tab6)). The data show that the most P&Ds for one symbol pair was 13, with the vast majority of symbols having between 0 and 3 P&Ds. This is consistent with the notion that specific coins may be targeted more often than others. Also interesting to note is that five of the top ten most pumped coins were pumped on the *Bittrex* exchange. Further research could perhaps investigate the properties of these coins, in an attempt to see if there are links between the most pumped coins.

Figure [8](/article/10.1186/s40163-018-0093-5#Fig8) shows almost 9 days of candlestick data for the coin with the most P&D patterns detected. The individual spikes have been muted in the figure, to highlight only the pump-and-dumps. The resulting graph depicts rather suspicious trading activity, with many periods of lower price and volume, followed by significant spikes in both. During the 9-day period shown eight pumps were detected. This type of trading activity would be consistent with the activity of P&D groups organising multiple attacks on a single vulnerable coin. Regardless of whether it is directly the result of nefarious activity, it is still a pattern which raises question.

![Fig. 8](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig8_HTML.png)

A candlestick chart of the most pumped coin

### Real-world detectability

A core test of a pump-and-dump identification system is its real-world detectability. We used pump-and-dump schemes that we were explicitly orchestrated in online chat groups as the ‘gold standard’ of confirmed cases. Albeit to a smaller extent, this source of confirmed P&Ds allows us to look at the detectability on a case-wise basis. The confirmed P&Ds were obtained by monitoring two pump-and-dump groups, *Moonlight Signal* (ca. 3000 members) and *Crypto Trading™* (ca. 56,000 members) and observing their announcements. Using this information, we illustrate two cases where our system (with the balanced parameter set) successfully detected a confirmed P&D, and two cases where our system could not clearly identify the P&D.

#### Successful detection

##### Case 1

In Case 1 (Fig. [9](/article/10.1186/s40163-018-0093-5#Fig9)) the coin that was to be victimised was announced on the 17th of August 2018, at 4 p.m. As a result of their coordinated efforts a large price and volume spike is visible, beginning exactly at the time at which the announcement took place. Our system was able detect the anomalous spikes, and correctly flagged the strange trading activity as being the result of a P&D.

![Fig. 9](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig9_HTML.png)

The chart depicts the results of a pump-and-dump promoted by the group *Moonlight Signal*, which was signalled to commence at 4 pm (UTC) on the 17th of August. Anomalous price and volume spikes at the specified time are clearly visible, and the suspicious activity was correctly marked as a P&D scheme by our detection system. *Symbol:* OAX/BTC. *Exchange:* Binance

##### Case 2

The announcement time for the P&D in Case 2 (Fig. [10](/article/10.1186/s40163-018-0093-5#Fig10)) was the 21st of August 2018, at 4 p.m. Once again, the warning signals of corresponding price and volume spikes are present, and the system correctly marks the strange activity at the announced starting time as fraudulent. In this case we also observe the price and volume beginning to increase just prior to the announcement time, perhaps indicating insider trading by the group leaders.

![Fig. 10](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig10_HTML.png)

The chart depicts the results of a pump-and-dump promoted by the group *Moonlight Signal*, which was signalled to commence at 4 pm (UTC) on the 21st of August. Anomalous price and volume spikes at the specified time are clearly visible, and the suspicious activity was correctly marked as a P&D scheme by our detection system. *Symbol:* RDN/BTC. *Exchange:* Binance

#### Unsuccessful detection

##### Case 3

The pump announcement in this case was given on the 4th of September 2018, at 3:30 p.m. Once again, we observe corresponding price and volume spikes (Fig. [11](/article/10.1186/s40163-018-0093-5#Fig11)), yet in this case our system failed to mark them as being the result of a pump-and-dump scheme. The reason for this is that the price continued to climb for a while after the pump, instead of immediately dumping. Thus, we can observe that sometimes the momentum caused by a pump group may actually persist for a period of time (in this case about 24 h). The coin being pumped in this case (RDN) was also pumped by the same group about 13 days previously (see “[Case 2](/article/10.1186/s40163-018-0093-5#Sec34)”); lending support to the idea that certain coins are targeted more often than others.

![Fig. 11](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig11_HTML.png)

The chart depicts the results of a pump-and-dump promoted by the group *Moonlight Signal*, which was signalled to commence at 3:30 p.m (UTC) on the 4th of September. While our system correctly marked the corresponding price and volume spikes at the specified time, it failed to identify them as being the result of a pump-and-dump. *Symbol:* RDN/BTC. *Exchange:* Binance

##### Case 4

In Case 4 (Fig. [12](/article/10.1186/s40163-018-0093-5#Fig12)) the pump announcement was made at 4 p.m. on the 3rd of September 2018. Similarly, to Case 3, our system again fails to mark the anomalous spikes as a pump-and-dump, for the same reason of the price not dipping quickly enough afterwards. In order to correctly identify these cases in which the price maintains momentum for some time after the announcement, a potential improvement could be made to the algorithm whereby decreasing volume is also taken into consideration. That way, if either the price, or the volume dips, it is counted as a P&D, as opposed to only relying on price dips. Additionally, in this case, we see that the following day a P&D is detected by our system, though it is unknown whether this is a result of additional targeting by the group, or merely a false positive.

![Fig. 12](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40163-018-0093-5/MediaObjects/40163_2018_93_Fig12_HTML.png)

The chart depicts the results of a pump-and-dump promoted by the group *Crypto Trading*™, which was signalled to commence at 4 p.m (UTC) on the 3rd of September. In this case we once again observe that the system detects large corresponding price and volume spikes at the announced time, however it does not identify these anomalies as being the result a P&D. *Symbol:* TRIG/BTC. *Exchange:* Binance

## Discussion

This paper attempted to introduce to the crime science community the problem of cryptocurrency pump-and-dump schemes. With cryptocurrencies becoming increasingly popular, they are also becoming a more likely target for criminal activity. Cryptocurrency pump-and-dump schemes are orchestrated attempts to inflate the price of a cryptocurrency artificially. We identified breakout indicators and reinforcers as criteria for locating a pump-and-dump and investigated the data using an anomaly detection approach. While the choice of parameters that define an anomaly is inherently subjective, we observed that a balanced approach between the naïve initial parameters and the strict parameters might help in flagging suspicious trading activity. We were also able to show that using a limited set of parameters it is possible to detect *pumping* activity in the data as well as subsequent *dumping* activity. Moreover, we monitored two pump-and-dump groups in order to obtain several cases of real life pump-and-dump schemes which we then applied our detection algorithm to, in order to demonstrate its performance in real scenarios.

### Pump-and-dumps as a challenge for crime science

Besides locating potential pump-and-dumps, we found evidence of clustering in the data. The vast majority of the coins are ones with a low market cap while the top ten coins accounted for 85% of the market cap. Furthermore, the final distribution of the pump-and-dumps showed that about 30% of the symbols accounted for roughly 80% of the pumps, indicating that even amongst low market cap coins, some coins are targeted more frequently than others. Translated to the environmental criminology literature, this pattern resembles repeat victimisation (Farrell and Pease [1993](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1."); Kleemans [2001](/article/10.1186/s40163-018-0093-5#ref-CR11 "Developments in Banking and Financial Law: 2013. (2014). Review of banking and financial law, 33, 1."); Weisel [2005](/article/10.1186/s40163-018-0093-5#ref-CR1 "Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. Indiana Law Journal, 75, 353."); Farrell [2015](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")). If a P&D chat group, for example, finds a suitable coin that they targeted successfully before, it is possible they may be more likely to perform another pump on that same coin; an example of this was shown in the case study section, where the group *Moonlight Signal* targeted the same coin (RDN) twice, in about a 2-week period. The clustering can be exploited for preventative purposes since efforts can be concentrated towards the clusters, finding out what makes them attractive targets, and implementing strategies to help mitigate potentially nefarious activity. Ideas from situational crime prevention, for example, such as increasing the risk or effort required to commit a P&D could also serve as useful methods for prevention (Clarke [2012](/article/10.1186/s40163-018-0093-5#ref-CR2 "Bitcoin Magazine. (2017, May). What is an Altcoin? Retrieved from
                  https://bitcoinmagazine.com/guides/what-altcoin/

                .")). Consider an exchange which requires additional verification for users trading certain symbol pairs which are determined to be vulnerable. Such an intervention would increase the effort required to trade and hence to pump the vulnerable coin. When considering how to increase the risk, an example could be a system in which the automated detection of anomalous trading activity is used in cooperation with humans. That system could mark suspicious points which observers may then investigate further, increasing the chances that such P&D schemes are detected.

A major challenge for pump-and-dump prevention might lie in coordinating the efforts between private bodies such as cryptocurrency exchanges and government bodies. While governments are catching up on the problem and have allocated more resources to the mitigation of pump-and-dump schemes, exchanges might have little incentive to cooperate because they benefit from trading activity on their platforms. Finally, a move towards more government regulation—in our data less regulated exchanges were targeted disproportionately more frequently—might undermine the very concept of cryptocurrency trading as a decentralised exchange without government interference. An interdisciplinary, problem-oriented approach from both the practitioners’ and the research community seems a path worthwhile exploring in the mitigation of cryptocurrency pump-and-dump schemes.

### Limitations

In the current investigation, we resorted to publicly available data and provided a framework for the future analysis of cryptocurrency pump-and-dumps. However, several limitations merit attention. First, the accuracy of flagging an alleged pump-and-dump is dependent upon the parameters chosen and cannot be ascertained absent a ground truth of confirmed pump-and-dumps. Our analysis should be treated as a first attempt to place the topic in the academic literature. Second, the dataset only covers 20 days of data with hourly granularity. While this was sufficient for the scope of this paper, future research would want to attempt to collect more substantial quantities of data and at a smaller granularity (e.g., per minute). Third, as with any flagging system, there is a decision to be made how many false positives are acceptable (i.e., incorrectly flagged coins). Arguably, an exchange would want to avoid announcing a coin of being used for fraudulent activity if this were not the case. This compromise is particularly complex in real-time settings so an interesting alternative avenue for future research might be to move towards the identification of early warning signals that can highlight suspicious trading at a point in time where the costs of false positives are relatively low (e.g., in the rather lengthy, low-activity accumulation phase preceding a pump). It is important to recognise the presence of both false positives and false negatives in any P&D detection system. In order to minimise the likelihood of Type I errors (i.e., false positives), the parameters for the detection algorithm can be set stricter (e.g., larger price or volume increases) which in turn increases the likelihood of committing a Type II error (i.e., incorrectly missing a real pump-and-dump; false negative). Thus, a cost for both Type I and Type II errors needs to be determined, and a balance struck between the two. The only way to be entirely confident that a particular set of price and volume spikes is the result of a P&D group, is to cross reference those spikes with a group’s intent to manipulate. Thus, a desirable area for future research would be to create of a database of confirmed pumps. While labour intensive to do in a fully manual way, the creation of such a database could likely be achieved through a smart combination of automated and manual tasks (e.g., an automated filtering system with human review). Such a database could be used as a means of testing the accuracy of a detection algorithm, as well as allowing for the use of supervised machine learning methods.

### Future research

Two lines of research seem particularly interesting for an extension of cryptocurrency pump-and-dump identification. First, identifying vulnerable coins and understanding the characteristics of those coins that are repeatedly targeted in more detail would allow for efficient resource allocation of detection systems (e.g., those involving both automated systems and human judgment). Second, moving away from exchange trading data, the modus operandi of pump-and-dumps could be examined in more detail. A particularly promising path for future studies could be the linguistic analysis of the coordination of pump-and-dumps in online chat groups, on the one hand; and the means by which misinformation about specific coins is spread on, for example, social media, on the other hand.

## Conclusion

This paper has attempted to provide a first look into research for cryptocurrency pump-and-dump schemes. A historical basis for the phenomenon was described with literature from traditional economics and synthesised with the currently available information on cryptocurrency P&D schemes. We proposed a set of defining criteria that could help describe a crypto P&D and showed how an anomaly detection technique could be used to detect patterns of suspicious activity. Ultimately, it is the hope that the information presented in this paper will serve useful as a basis for further research into the detection of these fraudulent schemes.

## Abbreviations

cryptocurrency

pump-and-dump

US Securities and Exchange Commission

Open High Low Close Volume

Bitcoin

Litecoin

## References

Bartels, K. C. (2000). Click here to buy the next Microsoft: the penny stock rules, online microcap fraud, and the unwary investor. *Indiana Law Journal,* *75,* 353.

[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Click%20here%20to%20buy%20the%20next%20Microsoft%3A%20the%20penny%20stock%20rules%2C%20online%20microcap%20fraud%2C%20and%20the%20unwary%20investor&journal=Ind.%20LJ&volume=75&publication_year=2000&author=Bartels%2CKC)

Bitcoin Magazine. (2017, May). *What is an Altcoin?* Retrieved from <https://bitcoinmagazine.com/guides/what-altcoin/>.

Borrion, H. (2013). Quality assurance in crime scripting. *Crime Science,* *2*(1), 6. <https://doi.org/10.1186/2193-7680-2-6>.

[Article](https://link.springer.com/doi/10.1186/2193-7680-2-6) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Quality%20assurance%20in%20crime%20scripting&journal=Crime%20Science&doi=10.1186%2F2193-7680-2-6&volume=2&issue=1&publication_year=2013&author=Borrion%2CH)

Bouraoui, T. (2009). Stock spams: An empirical study on penny stock market. *International Review of Business Research Papers,* *5*(4), 292–305.

[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Stock%20spams%3A%20An%20empirical%20study%20on%20penny%20stock%20market&journal=International%20Review%20of%20Business%20Research%20Papers&volume=5&issue=4&pages=292-305&publication_year=2009&author=Bouraoui%2CT)

Brooker, K. (1998, October). *The scary rise of internet stock scams on the net*. Retrieved from <http://archive.fortune.com/magazines/fortune/fortune_archive/1998/10/26/250019/index.htm>.

Ccxt. (2018). *ccxt/ccxt*. Retrieved from <https://github.com/ccxt/ccxt>.

Chandola, V., Banerjee, A., & Kumar, V. (2009). Anomaly detection: A survey. *ACM Computing Surveys (CSUR),* *41*(3), 15.

[Article](https://doi.org/10.1145%2F1541880.1541882) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Anomaly%20detection%3A%20A%20survey&journal=ACM%20Computing%20Surveys%20%28CSUR%29&doi=10.1145%2F1541880.1541882&volume=41&issue=3&publication_year=2009&author=Chandola%2CV&author=Banerjee%2CA&author=Kumar%2CV)

Clarke, R. V. (2012). Opportunity makes the thief. Really? And so what? *Crime Science,* *1*(1), 3. <https://doi.org/10.1186/2193-7680-1-3>.

[Article](https://link.springer.com/doi/10.1186/2193-7680-1-3) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Opportunity%20makes%20the%20thief.%20Really%3F%20And%20so%20what%3F&journal=Crime%20Science&doi=10.1186%2F2193-7680-1-3&volume=1&issue=1&publication_year=2012&author=Clarke%2CRV)

CoinMarketCap. (2018). *Cryptocurrency market capitalizations*. Retrieved from <https://coinmarketcap.com/>.

Cryptocurrency Prices. (2018). *Compare cryptos to GDP of countries*. Retrieved from <http://www.cryptocurrencyprices.net/cryptocurrency_vs_country_gdp.php>.

Developments in Banking and Financial Law: 2013. (2014). *Review of banking and financial law*, *33*, 1.

Dugan, B. (2002). The internet and the law part two—Commercial matters: Facilitating and regulating commerce. *Victoria University of Wellington Law Review,* *33,* 433.

[Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20internet%20and%20the%20law%20part%20two%E2%80%94Commercial%20matters%3A%20Facilitating%20and%20regulating%20commerce&journal=Victoria%20University%20of%20Wellington%20Law%20Review&volume=33&publication_year=2002&author=Dugan%2CB)

Farrell, G. (2015). Crime concentration theory. *Crime Prevention and Community Safety,* *17*(4), 233–248.

[Article](https://doi.org/10.1057%2Fcpcs.2015.17) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Crime%20concentration%20theory&journal=Crime%20Prevention%20and%20Community%20Safety&doi=10.1057%2Fcpcs.2015.17&volume=17&issue=4&pages=233-248&publication_year=2015&author=Farrell%2CG)

Farrell, G., & Pease, K. (1993). *Once bitten, twice bitten: repeat victimisation and its implications for crime prevention*. London: Home Office Police Research Group.

[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Once%20bitten%2C%20twice%20bitten%3A%20repeat%20victimisation%20and%20its%20implications%20for%20crime%20prevention&publication_year=1993&author=Farrell%2CG&author=Pease%2CK)

Keatley, D. (2018). Crime script analysis. *Pathways in crime: An introduction to behaviour sequence analysis* (pp. 125–136). Cham: Springer International Publishing.

[Chapter](https://link.springer.com/doi/10.1007/978-3-319-75226-6_10) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Crime%20script%20analysis&doi=10.1007%2F978-3-319-75226-6_10&pages=125-136&publication_year=2018&author=Keatley%2CD)

Khan, M. F. (2018). *How to avoid getting duped by cryptocurrency pump and dump schemes (like I did)*. Retrieved from <https://thenextweb.com/contributors/2018/03/15/avoid-getting-duped-cryptocurrency-pump-dump-schemes-like/>.

Kleemans, E. R. (2001). Repeat burglary victimization. Results of empirical research in the Netherlands. In G. Farrell & K. Pease (Eds.), *Repeat Victimization. Crime Prevention Studies* (pp. 53–68). Monsey: Criminal Justice Press.

[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Repeat%20burglary%20victimization.%20Results%20of%20empirical%20research%20in%20the%20Netherlands&pages=53-68&publication_year=2001&author=Kleemans%2CER)

Kramer, D. B. (2004). The way it is and the way it should be: liability under sec. 10(b) of the exchange act and rule 10b-5 thereunder for making false and misleading statements as part of a scheme to pump and dump a stock. *University of Miami Business Law Review,* *13,* 243.

[Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20way%20it%20is%20and%20the%20way%20it%20should%20be%3A%20liability%20under%20sec.%2010%28b%29%20of%20the%20exchange%20act%20and%20rule%2010b-5%20thereunder%20for%20making%20false%20and%20misleading%20statements%20as%20part%20of%20a%20scheme%20to%20pump%20and%20dump%20a%20stock&journal=University%20of%20Miami%20Business%20Law%20Review&volume=13&publication_year=2004&author=Kramer%2CDB)

Li, T., Shin, D., & Wang, B. (2018). Cryptocurrency Pump-and-Dump Schemes. Available at SSRN 3267041

Mac, R., & Lytvynenko, J. (2018). *Here’s how scammers are using fake news to screw with Bitcoin Investors*. Retrieved from [https://www.buzzfeed.com/ryanmac/heres-how-scammers-are-using-fake-news-to-screw-with-bitcoin?utm\_term=.ukny8oOev#.iyxxAZ7R3](https://www.buzzfeed.com/ryanmac/heres-how-scammers-are-using-fake-news-to-screw-with-bitcoin%3futm_term%3d.ukny8oOev#.iyxxAZ7R3).

Martineau, P. (2018, January). *Inside the group chats where people pump and dump cryptocurrency*. Retrieved from <https://theoutline.com/post/3074/inside-the-group-chats-where-people-pump-and-dump-cryptocurrency>.

Nakamoto, S. (2008). *Bitcoin: A peer-to-peer electronic cash system*. Retrieved from <https://bitcoin.org/bitcoin.pdf>.

Shifflett, S. (2018, August 05). *Some traders are talking up cryptocurrencies, then dumping them, costing others millions*. Retrieved from <https://www.wsj.com/graphics/cryptocurrency-schemes-generate-big-coin/>.

Siris, V. A., & Papagalou, F. (2004). Application of anomaly detection algorithms for detecting SYN flooding attacks. In *Global Telecommunications Conference, 2004. GLOBECOM’04. IEEE* (vol. 4, pp. 2050–2054). IEEE.

Song, X., Wu, M., Jermaine, C., & Ranka, S. (2007). Conditional anomaly detection. *IEEE Transactions on Knowledge and Data Engineering,* *19*(5), 631–645.

[Article](https://doi.org/10.1109%2FTKDE.2007.1009) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Conditional%20anomaly%20detection&journal=IEEE%20Transactions%20on%20Knowledge%20and%20Data%20Engineering&doi=10.1109%2FTKDE.2007.1009&volume=19&issue=5&pages=631-645&publication_year=2007&author=Song%2CX&author=Wu%2CM&author=Jermaine%2CC&author=Ranka%2CS)

Temple, S. (2000). Cybertrading: Financial markets and the internet. *Australian Law Librarian,* *8,* 337.

[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Cybertrading%3A%20Financial%20markets%20and%20the%20internet&journal=Australian%20Law%20Librarian&volume=8&publication_year=2000&author=Temple%2CS)

Thompson, P. (2018, June). *Pump and dump in crypto: cases, measures, warnings*. Retrieved from <https://cointelegraph.com/news/pump-and-dump-in-crypto-cases-measures-warnings>.

Town, S. (2018, February). *How to spot a pump and dump (and avoid it)*. Retrieved from <https://cryptobriefing.com/how-to-spot-a-pump-and-dump-avoid/>.

U.S. Commodity Futures Trading Commission. (2018). *CFTC issues first pump-and-dump virtual currency customer protection advisory*. Retrieved June 27, 2018, from <https://www.cftc.gov/PressRoom/PressReleases/pr7697-18>.

US Securities and Exchange Commission. (2017). *Microcap fraud*. Retrieved June 27, 2018, from <https://www.sec.gov/spotlight/microcap-fraud.shtml>.

Warren, S., Oxburgh, G., Briggs, P., & Wall, D. (2017). How might crime-scripts be used to support the understanding and policing of cloud crime?.

Weisel, D. L. (2005). *Analyzing repeat victimization*. Washington, DC: US Department of Justice, Office of Community Oriented Policing Services.

[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Analyzing%20repeat%20victimization&publication_year=2005&author=Weisel%2CDL)

Yang, E., & Worden, J. (2015). The treacherous terrain of penny stocks and how firms are attempting to navigate it.

[Download references](https://citation-needed.springer.com/v2/references/10.1186/s40163-018-0093-5?format=refman&flavour=references)

## Authors’ contributions

JK collected the data, ran the analyses and wrote the first draft of the paper; BK and JK conceived of the idea, concept, and analysis; BK wrote the final version of the manuscript. Both authors read and approved the final manuscript.

### Acknowledgements

Not applicable.

### Competing interests

Not applicable.

### Availability of data and materials

The data and code needed to reproduce the findings can be found at <https://osf.io/827wd/>.

### Funding

Not applicable.

### Publisher’s Note

Springer Nature remains neutral with regard to jurisdictional claims in published maps and institutional affiliations.

## Author information

### Authors and Affiliations

Department of Computer Science, VU University Amsterdam, Amsterdam, The Netherlands

Josh Kamps

Dawes Centre for Future Crime, Department of Security and Crime Science, University College London, 35 Tavistock Square, London, WC1H 9EZ, UK

Bennett Kleinberg

Department of Psychology, University of Amsterdam, Amsterdam, The Netherlands

Bennett Kleinberg

Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Josh%20Kamps) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Josh%20Kamps%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)

Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Bennett%20Kleinberg) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Bennett%20Kleinberg%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)

### Corresponding author

Correspondence to
[Bennett Kleinberg](mailto:bennett.kleinberg@ucl.ac.uk).

## Appendix

### Appendix

See Table [7](/article/10.1186/s40163-018-0093-5#Tab7).

## Rights and permissions

**Open Access** This article is distributed under the terms of the Creative Commons Attribution 4.0 International License (<http://creativecommons.org/licenses/by/4.0/>), which permits unrestricted use, distribution, and reproduction in any medium, provided you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons license, and indicate if changes were made.

[Reprints and permissions](https://s100.copyright.com/AppDispatchServlet?title=To%20the%20moon%3A%20defining%20and%20detecting%20cryptocurrency%20pump-and-dumps&author=Josh%20Kamps%20et%20al&contentID=10.1186%2Fs40163-018-0093-5&copyright=The%20Author%28s%29&publication=2193-7680&publicationDate=2018-11-26&publisherName=SpringerNature&orderBeanReset=true&oa=CC%20BY)

## About this article

![Check for updates. Verify currency and authenticity via CrossMark](data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjgxIiB3aWR0aD0iNTciIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIj48cGF0aCBkPSJtMTcuMzUgMzUuNDUgMjEuMy0xNC4ydi0xNy4wM2gtMjEuMyIgZmlsbD0iIzk4OTg5OCIvPjxwYXRoIGQ9Im0zOC42NSAzNS40NS0yMS4zLTE0LjJ2LTE3LjAzaDIxLjMiIGZpbGw9IiM3NDc0NzQiLz48cGF0aCBkPSJtMjggLjVjLTEyLjk4IDAtMjMuNSAxMC41Mi0yMy41IDIzLjVzMTAuNTIgMjMuNSAyMy41IDIzLjUgMjMuNS0xMC41MiAyMy41LTIzLjVjMC02LjIzLTIuNDgtMTIuMjEtNi44OC0xNi42Mi00LjQxLTQuNC0xMC4zOS02Ljg4LTE2LjYyLTYuODh6bTAgNDEuMjVjLTkuOCAwLTE3Ljc1LTcuOTUtMTcuNzUtMTcuNzVzNy45NS0xNy43NSAxNy43NS0xNy43NSAxNy43NSA3Ljk1IDE3Ljc1IDE3Ljc1YzAgNC43MS0xLjg3IDkuMjItNS4yIDEyLjU1cy03Ljg0IDUuMi0xMi41NSA1LjJ6IiBmaWxsPSIjNTM1MzUzIi8+PHBhdGggZD0ibTQxIDM2Yy01LjgxIDYuMjMtMTUuMjMgNy40NS0yMi40MyAyLjktNy4yMS00LjU1LTEwLjE2LTEzLjU3LTcuMDMtMjEuNWwtNC45Mi0zLjExYy00Ljk1IDEwLjctMS4xOSAyMy40MiA4Ljc4IDI5LjcxIDkuOTcgNi4zIDIzLjA3IDQuMjIgMzAuNi00Ljg2eiIgZmlsbD0iIzljOWM5YyIvPjxwYXRoIGQ9Im0uMiA1OC40NWMwLS43NS4xMS0xLjQyLjMzLTIuMDFzLjUyLTEuMDkuOTEtMS41Yy4zOC0uNDEuODMtLjczIDEuMzQtLjk0LjUxLS4yMiAxLjA2LS4zMiAxLjY1LS4zMi41NiAwIDEuMDYuMTEgMS41MS4zNS40NC4yMy44MS41IDEuMS44MWwtLjkxIDEuMDFjLS4yNC0uMjQtLjQ5LS40Mi0uNzUtLjU2LS4yNy0uMTMtLjU4LS4yLS45My0uMi0uMzkgMC0uNzMuMDgtMS4wNS4yMy0uMzEuMTYtLjU4LjM3LS44MS42Ni0uMjMuMjgtLjQxLjYzLS41MyAxLjA0LS4xMy40MS0uMTkuODgtLjE5IDEuMzkgMCAxLjA0LjIzIDEuODYuNjggMi40Ni40NS41OSAxLjA2Ljg4IDEuODQuODguNDEgMCAuNzctLjA3IDEuMDctLjIzcy41OS0uMzkuODUtLjY4bC45MSAxYy0uMzguNDMtLjguNzYtMS4yOC45OS0uNDcuMjItMSAuMzQtMS41OC4zNC0uNTkgMC0xLjEzLS4xLTEuNjQtLjMxLS41LS4yLS45NC0uNTEtMS4zMS0uOTEtLjM4LS40LS42Ny0uOS0uODgtMS40OC0uMjItLjU5LS4zMy0xLjI2LS4zMy0yLjAyem04LjQtNS4zM2gxLjYxdjIuNTRsLS4wNSAxLjMzYy4yOS0uMjcuNjEtLjUxLjk2LS43MnMuNzYtLjMxIDEuMjQtLjMxYy43MyAwIDEuMjcuMjMgMS42MS43MS4zMy40Ny41IDEuMTQuNSAyLjAydjQuMzFoLTEuNjF2LTQuMWMwLS41Ny0uMDgtLjk3LS4yNS0xLjIxLS4xNy0uMjMtLjQ1LS4zNS0uODMtLjM1LS4zIDAtLjU2LjA4LS43OS4yMi0uMjMuMTUtLjQ5LjM2LS43OC42NHY0LjhoLTEuNjF6bTcuMzcgNi40NWMwLS41Ni4wOS0xLjA2LjI2LTEuNTEuMTgtLjQ1LjQyLS44My43MS0xLjE0LjI5LS4zLjYzLS41NCAxLjAxLS43MS4zOS0uMTcuNzgtLjI1IDEuMTgtLjI1LjQ3IDAgLjg4LjA4IDEuMjMuMjQuMzYuMTYuNjUuMzguODkuNjdzLjQyLjYzLjU0IDEuMDNjLjEyLjQxLjE4Ljg0LjE4IDEuMzIgMCAuMzItLjAyLjU3LS4wNy43NmgtNC4zNmMuMDcuNjIuMjkgMS4xLjY1IDEuNDQuMzYuMzMuODIuNSAxLjM4LjUuMjkgMCAuNTctLjA0LjgzLS4xM3MuNTEtLjIxLjc2LS4zN2wuNTUgMS4wMWMtLjMzLjIxLS42OS4zOS0xLjA5LjUzLS40MS4xNC0uODMuMjEtMS4yNi4yMS0uNDggMC0uOTItLjA4LTEuMzQtLjI1LS40MS0uMTYtLjc2LS40LTEuMDctLjctLjMxLS4zMS0uNTUtLjY5LS43Mi0xLjEzLS4xOC0uNDQtLjI2LS45NS0uMjYtMS41MnptNC42LS42MmMwLS41NS0uMTEtLjk4LS4zNC0xLjI4LS4yMy0uMzEtLjU4LS40Ny0xLjA2LS40Ny0uNDEgMC0uNzcuMTUtMS4wNy40NS0uMzEuMjktLjUuNzMtLjU4IDEuM3ptMi41LjYyYzAtLjU3LjA5LTEuMDguMjgtMS41My4xOC0uNDQuNDMtLjgyLjc1LTEuMTNzLjY5LS41NCAxLjEtLjcxYy40Mi0uMTYuODUtLjI0IDEuMzEtLjI0LjQ1IDAgLjg0LjA4IDEuMTcuMjNzLjYxLjM0Ljg1LjU3bC0uNzcgMS4wMmMtLjE5LS4xNi0uMzgtLjI4LS41Ni0uMzctLjE5LS4wOS0uMzktLjE0LS42MS0uMTQtLjU2IDAtMS4wMS4yMS0xLjM1LjYzLS4zNS40MS0uNTIuOTctLjUyIDEuNjcgMCAuNjkuMTcgMS4yNC41MSAxLjY2LjM0LjQxLjc4LjYyIDEuMzIuNjIuMjggMCAuNTQtLjA2Ljc4LS4xNy4yNC0uMTIuNDUtLjI2LjY0LS40MmwuNjcgMS4wM2MtLjMzLjI5LS42OS41MS0xLjA4LjY1LS4zOS4xNS0uNzguMjMtMS4xOC4yMy0uNDYgMC0uOS0uMDgtMS4zMS0uMjQtLjQtLjE2LS43NS0uMzktMS4wNS0uN3MtLjUzLS42OS0uNy0xLjEzYy0uMTctLjQ1LS4yNS0uOTYtLjI1LTEuNTN6bTYuOTEtNi40NWgxLjU4djYuMTdoLjA1bDIuNTQtMy4xNmgxLjc3bC0yLjM1IDIuOCAyLjU5IDQuMDdoLTEuNzVsLTEuNzctMi45OC0xLjA4IDEuMjN2MS43NWgtMS41OHptMTMuNjkgMS4yN2MtLjI1LS4xMS0uNS0uMTctLjc1LS4xNy0uNTggMC0uODcuMzktLjg3IDEuMTZ2Ljc1aDEuMzR2MS4yN2gtMS4zNHY1LjZoLTEuNjF2LTUuNmgtLjkydi0xLjJsLjkyLS4wN3YtLjcyYzAtLjM1LjA0LS42OC4xMy0uOTguMDgtLjMxLjIxLS41Ny40LS43OXMuNDItLjM5LjcxLS41MWMuMjgtLjEyLjYzLS4xOCAxLjA0LS4xOC4yNCAwIC40OC4wMi42OS4wNy4yMi4wNS40MS4xLjU3LjE3em0uNDggNS4xOGMwLS41Ny4wOS0xLjA4LjI3LTEuNTMuMTctLjQ0LjQxLS44Mi43Mi0xLjEzLjMtLjMxLjY1LS41NCAxLjA0LS43MS4zOS0uMTYuOC0uMjQgMS4yMy0uMjRzLjg0LjA4IDEuMjQuMjRjLjQuMTcuNzQuNCAxLjA0Ljcxcy41NC42OS43MiAxLjEzYy4xOS40NS4yOC45Ni4yOCAxLjUzcy0uMDkgMS4wOC0uMjggMS41M2MtLjE4LjQ0LS40Mi44Mi0uNzIgMS4xM3MtLjY0LjU0LTEuMDQuNy0uODEuMjQtMS4yNC4yNC0uODQtLjA4LTEuMjMtLjI0LS43NC0uMzktMS4wNC0uN2MtLjMxLS4zMS0uNTUtLjY5LS43Mi0xLjEzLS4xOC0uNDUtLjI3LS45Ni0uMjctMS41M3ptMS42NSAwYzAgLjY5LjE0IDEuMjQuNDMgMS42Ni4yOC40MS42OC42MiAxLjE4LjYyLjUxIDAgLjktLjIxIDEuMTktLjYyLjI5LS40Mi40NC0uOTcuNDQtMS42NiAwLS43LS4xNS0xLjI2LS40NC0xLjY3LS4yOS0uNDItLjY4LS42My0xLjE5LS42My0uNSAwLS45LjIxLTEuMTguNjMtLjI5LjQxLS40My45Ny0uNDMgMS42N3ptNi40OC0zLjQ0aDEuMzNsLjEyIDEuMjFoLjA1Yy4yNC0uNDQuNTQtLjc5Ljg4LTEuMDIuMzUtLjI0LjctLjM2IDEuMDctLjM2LjMyIDAgLjU5LjA1Ljc4LjE0bC0uMjggMS40LS4zMy0uMDljLS4xMS0uMDEtLjIzLS4wMi0uMzgtLjAyLS4yNyAwLS41Ni4xLS44Ni4zMXMtLjU1LjU4LS43NyAxLjF2NC4yaC0xLjYxem0tNDcuODcgMTVoMS42MXY0LjFjMCAuNTcuMDguOTcuMjUgMS4yLjE3LjI0LjQ0LjM1LjgxLjM1LjMgMCAuNTctLjA3LjgtLjIyLjIyLS4xNS40Ny0uMzkuNzMtLjczdi00LjdoMS42MXY2Ljg3aC0xLjMybC0uMTItMS4wMWgtLjA0Yy0uMy4zNi0uNjMuNjQtLjk4Ljg2LS4zNS4yMS0uNzYuMzItMS4yNC4zMi0uNzMgMC0xLjI3LS4yNC0xLjYxLS43MS0uMzMtLjQ3LS41LTEuMTQtLjUtMi4wMnptOS40NiA3LjQzdjIuMTZoLTEuNjF2LTkuNTloMS4zM2wuMTIuNzJoLjA1Yy4yOS0uMjQuNjEtLjQ1Ljk3LS42My4zNS0uMTcuNzItLjI2IDEuMS0uMjYuNDMgMCAuODEuMDggMS4xNS4yNC4zMy4xNy42MS40Ljg0LjcxLjI0LjMxLjQxLjY4LjUzIDEuMTEuMTMuNDIuMTkuOTEuMTkgMS40NCAwIC41OS0uMDkgMS4xMS0uMjUgMS41Ny0uMTYuNDctLjM4Ljg1LS42NSAxLjE2LS4yNy4zMi0uNTguNTYtLjk0LjczLS4zNS4xNi0uNzIuMjUtMS4xLjI1LS4zIDAtLjYtLjA3LS45LS4ycy0uNTktLjMxLS44Ny0uNTZ6bTAtMi4zYy4yNi4yMi41LjM3LjczLjQ1LjI0LjA5LjQ2LjEzLjY2LjEzLjQ2IDAgLjg0LS4yIDEuMTUtLjYuMzEtLjM5LjQ2LS45OC40Ni0xLjc3IDAtLjY5LS4xMi0xLjIyLS4zNS0xLjYxLS4yMy0uMzgtLjYxLS41Ny0xLjEzLS41Ny0uNDkgMC0uOTkuMjYtMS41Mi43N3ptNS44Ny0xLjY5YzAtLjU2LjA4LTEuMDYuMjUtMS41MS4xNi0uNDUuMzctLjgzLjY1LTEuMTQuMjctLjMuNTgtLjU0LjkzLS43MXMuNzEtLjI1IDEuMDgtLjI1Yy4zOSAwIC43My4wNyAxIC4yLjI3LjE0LjU0LjMyLjgxLjU1bC0uMDYtMS4xdi0yLjQ5aDEuNjF2OS44OGgtMS4zM2wtLjExLS43NGgtLjA2Yy0uMjUuMjUtLjU0LjQ2LS44OC42NC0uMzMuMTgtLjY5LjI3LTEuMDYuMjctLjg3IDAtMS41Ni0uMzItMi4wNy0uOTVzLS43Ni0xLjUxLS43Ni0yLjY1em0xLjY3LS4wMWMwIC43NC4xMyAxLjMxLjQgMS43LjI2LjM4LjY1LjU4IDEuMTUuNTguNTEgMCAuOTktLjI2IDEuNDQtLjc3di0zLjIxYy0uMjQtLjIxLS40OC0uMzYtLjctLjQ1LS4yMy0uMDgtLjQ2LS4xMi0uNy0uMTItLjQ1IDAtLjgyLjE5LTEuMTMuNTktLjMxLjM5LS40Ni45NS0uNDYgMS42OHptNi4zNSAxLjU5YzAtLjczLjMyLTEuMy45Ny0xLjcxLjY0LS40IDEuNjctLjY4IDMuMDgtLjg0IDAtLjE3LS4wMi0uMzQtLjA3LS41MS0uMDUtLjE2LS4xMi0uMy0uMjItLjQzcy0uMjItLjIyLS4zOC0uM2MtLjE1LS4wNi0uMzQtLjEtLjU4LS4xLS4zNCAwLS42OC4wNy0xIC4ycy0uNjMuMjktLjkzLjQ3bC0uNTktMS4wOGMuMzktLjI0LjgxLS40NSAxLjI4LS42My40Ny0uMTcuOTktLjI2IDEuNTQtLjI2Ljg2IDAgMS41MS4yNSAxLjkzLjc2cy42MyAxLjI1LjYzIDIuMjF2NC4wN2gtMS4zMmwtLjEyLS43NmgtLjA1Yy0uMy4yNy0uNjMuNDgtLjk4LjY2cy0uNzMuMjctMS4xNC4yN2MtLjYxIDAtMS4xLS4xOS0xLjQ4LS41Ni0uMzgtLjM2LS41Ny0uODUtLjU3LTEuNDZ6bTEuNTctLjEyYzAgLjMuMDkuNTMuMjcuNjcuMTkuMTQuNDIuMjEuNzEuMjEuMjggMCAuNTQtLjA3Ljc3LS4ycy40OC0uMzEuNzMtLjU2di0xLjU0Yy0uNDcuMDYtLjg2LjEzLTEuMTguMjMtLjMxLjA5LS41Ny4xOS0uNzYuMzFzLS4zMy4yNS0uNDEuNGMtLjA5LjE1LS4xMy4zMS0uMTMuNDh6bTYuMjktMy42M2gtLjk4di0xLjJsMS4wNi0uMDcuMi0xLjg4aDEuMzR2MS44OGgxLjc1djEuMjdoLTEuNzV2My4yOGMwIC44LjMyIDEuMi45NyAxLjIuMTIgMCAuMjQtLjAxLjM3LS4wNC4xMi0uMDMuMjQtLjA3LjM0LS4xMWwuMjggMS4xOWMtLjE5LjA2LS40LjEyLS42NC4xNy0uMjMuMDUtLjQ5LjA4LS43Ni4wOC0uNCAwLS43NC0uMDYtMS4wMi0uMTgtLjI3LS4xMy0uNDktLjMtLjY3LS41Mi0uMTctLjIxLS4zLS40OC0uMzctLjc4LS4wOC0uMy0uMTItLjY0LS4xMi0xLjAxem00LjM2IDIuMTdjMC0uNTYuMDktMS4wNi4yNy0xLjUxcy40MS0uODMuNzEtMS4xNGMuMjktLjMuNjMtLjU0IDEuMDEtLjcxLjM5LS4xNy43OC0uMjUgMS4xOC0uMjUuNDcgMCAuODguMDggMS4yMy4yNC4zNi4xNi42NS4zOC44OS42N3MuNDIuNjMuNTQgMS4wM2MuMTIuNDEuMTguODQuMTggMS4zMiAwIC4zMi0uMDIuNTctLjA3Ljc2aC00LjM3Yy4wOC42Mi4yOSAxLjEuNjUgMS40NC4zNi4zMy44Mi41IDEuMzguNS4zIDAgLjU4LS4wNC44NC0uMTMuMjUtLjA5LjUxLS4yMS43Ni0uMzdsLjU0IDEuMDFjLS4zMi4yMS0uNjkuMzktMS4wOS41M3MtLjgyLjIxLTEuMjYuMjFjLS40NyAwLS45Mi0uMDgtMS4zMy0uMjUtLjQxLS4xNi0uNzctLjQtMS4wOC0uNy0uMy0uMzEtLjU0LS42OS0uNzItMS4xMy0uMTctLjQ0LS4yNi0uOTUtLjI2LTEuNTJ6bTQuNjEtLjYyYzAtLjU1LS4xMS0uOTgtLjM0LTEuMjgtLjIzLS4zMS0uNTgtLjQ3LTEuMDYtLjQ3LS40MSAwLS43Ny4xNS0xLjA4LjQ1LS4zMS4yOS0uNS43My0uNTcgMS4zem0zLjAxIDIuMjNjLjMxLjI0LjYxLjQzLjkyLjU3LjMuMTMuNjMuMi45OC4yLjM4IDAgLjY1LS4wOC44My0uMjNzLjI3LS4zNS4yNy0uNmMwLS4xNC0uMDUtLjI2LS4xMy0uMzctLjA4LS4xLS4yLS4yLS4zNC0uMjgtLjE0LS4wOS0uMjktLjE2LS40Ny0uMjNsLS41My0uMjJjLS4yMy0uMDktLjQ2LS4xOC0uNjktLjMtLjIzLS4xMS0uNDQtLjI0LS42Mi0uNHMtLjMzLS4zNS0uNDUtLjU1Yy0uMTItLjIxLS4xOC0uNDYtLjE4LS43NSAwLS42MS4yMy0xLjEuNjgtMS40OS40NC0uMzggMS4wNi0uNTcgMS44My0uNTcuNDggMCAuOTEuMDggMS4yOS4yNXMuNzEuMzYuOTkuNTdsLS43NC45OGMtLjI0LS4xNy0uNDktLjMyLS43My0uNDItLjI1LS4xMS0uNTEtLjE2LS43OC0uMTYtLjM1IDAtLjYuMDctLjc2LjIxLS4xNy4xNS0uMjUuMzMtLjI1LjU0IDAgLjE0LjA0LjI2LjEyLjM2cy4xOC4xOC4zMS4yNmMuMTQuMDcuMjkuMTQuNDYuMjFsLjU0LjE5Yy4yMy4wOS40Ny4xOC43LjI5cy40NC4yNC42NC40Yy4xOS4xNi4zNC4zNS40Ni41OC4xMS4yMy4xNy41LjE3LjgyIDAgLjMtLjA2LjU4LS4xNy44My0uMTIuMjYtLjI5LjQ4LS41MS42OC0uMjMuMTktLjUxLjM0LS44NC40NS0uMzQuMTEtLjcyLjE3LTEuMTUuMTctLjQ4IDAtLjk1LS4wOS0xLjQxLS4yNy0uNDYtLjE5LS44Ni0uNDEtMS4yLS42OHoiIGZpbGw9IiM1MzUzNTMiLz48L2c+PC9zdmc+)

### Cite this article

Kamps, J., Kleinberg, B. To the moon: defining and detecting cryptocurrency pump-and-dumps.
*Crime Sci* **7**, 18 (2018). https://doi.org/10.1186/s40163-018-0093-5

[Download citation](https://citation-needed.springer.com/v2/references/10.1186/s40163-018-0093-5?format=refman&flavour=citation)

Received: 03 July 2018

Accepted: 16 November 2018

Published: 26 November 2018

Version of record: 26 November 2018

DOI: https://doi.org/10.1186/s40163-018-0093-5

### Share this article

Anyone you share the following link with will be able to read this content:

Sorry, a shareable link is not currently available for this article.

Provided by the Springer Nature SharedIt content-sharing initiative

### Keywords

## Associated Content

Part of a collection:

### [Cybercrime: interdisciplinary approaches to cutting crime and victimisation in cyber space](https://link.springer.com/collections/dghibaddhb)

### [Breast Cancer Epidemiology and Prevention](https://link.springer.com/collections/bcceghecca)

Advertisement

## Search

## Navigation

## Footer Navigation

### Discover content

### Publish with us

### Products and services

### Our brands

### Corporate Navigation

84.115.229.87

Not affiliated

![Springer Nature](/oscar-static/images/logo-springernature-white-0689727e50.svg)

© 2026 Springer Nature
