# [Quantitative Trading](http://epchan.blogspot.com/)

Quantitative investment and trading ideas, research, and analysis.

## Thursday, October 24, 2013

### How Useful is Order Flow and VPIN?

Can short-term price movement be predicted? (I am speaking of  seconds or minutes here.) This is a question not only relevant to high frequency traders, but to every long-term investor as well. Even if  one plans to buy and hold a stock for years,  nobody likes to suffer short-term negative P&L immediately after entry into position.

 One short-term prediction method that has long found favor with academic researchers and traders alike is order flow. Order flow is just signed transaction volume: if a transaction of 100 shares is classified as a "buy", the order flow is +100; if it is classified as a "sell", the order flow is -100. This might strike some as rather strange: every transaction has a buyer and seller, so what does it mean by a "buy" or a "sell"? Well, the "buyer" is defined as the one who is the "aggressor", i.e. one that is using a market order to buy at the ask price. (And vice versa for the seller, whom I will henceforth omit in this discussion.) The intuitive reason why a series of large "buy" market orders are predictive of short-term price increase is that if someone is so eager to go long, s/he is likely to know something about the market that others don't (either due to superior fundamental knowledge or technical model), so we better join her/him! Such superior traders are often called "informed traders", and their order flow is often called "toxic flow". Toxic, that is, to the uninformed market maker.

 In theory, if one has a tick data feed, one can tell whether an execution is a "buy" or "sell" by comparing the trade price with the bid and ask price: if the trade price is equal to the ask, it is a "buy". This is called the "Quote Rule". But in practice, there is a hitch. If the bid and ask prices change quickly, a buy market order may end up buying at the bid price if the market has fortuitously moved lower since the order was sent. Besides, perhaps 1/3 of trading in the US equities markets take place in dark pools or via hidden orders, so the quotes are simply invisible and order flow non-computable. So this classification scheme is not foolproof. Therefore, a number of researchers (see "[Flow Toxicity and Volatility in a High Frequency World](http://papers.ssrn.com/sol3/papers.cfm?abstract_id=1695596)" by Easley, et. al.) proposed an alternative, "easier", method to compute order flow. Instead of checking the trade price of each tick, they just need the "open" and "close" trade prices of a bar, preferably a volume bar, and assign a fraction of the volume in that bar to "buy" or "sell" depending on whether the close price is higher or lower than the open price. (The assignment formula is based on the cumulative probability density of a Gaussian distribution, which incidentally models price changes of volume bars, but not time bars, pretty well.) The absolute difference between buy and sell volume expressed as a fraction of the total volume is called "VPIN" by the authors, or *Volume-Synchronized Probability of Informed Trading*. The higher VPIN is, the more likely we will experience short-term momentum due to informed trading.

 Theory and intuition aside, how well does order flow work in practice as a short-term predictor in various markets? And how predictive is VPIN as compared to the old Quote Rule?  In my experience, while this indicator is predictive of price change, the change is often too small to overcome transaction costs including the bid-ask spread. And more disturbingly, in those markets where both Quote Rule and VPIN should work (e.g. futures markets), VPIN has so far underperformed Quote Rule, despite (?) it being patented and highly touted. I have informally polled other investment professionals on their experience, and the answer usually come back indifferent as well.

 Do you have live experience with VPIN? Or more generally, do you find strategies built using volume bars superior to those using time bars? If so, please leave us your comments!

 ===

 My online Quantitative Momentum Strategies workshop will be offered in December. Please visit [epchan.com/](http://epchan.com/my-workshops)[my-workshops](http://epchan.com/my-workshops)for registration details.

Posted by   [Ernie Chan](https://www.blogger.com/profile/02747099358519893177 "author profile")     at [4:07 PM](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html "permanent link")       [![](https://resources.blogblog.com/img/icon18_email.gif)](https://www.blogger.com/email-post/35364652/5933365541814525630 "Email Post")     [![](https://resources.blogblog.com/img/icon18_edit_allbkg.gif)](https://www.blogger.com/post-edit.g?blogID=35364652&postID=5933365541814525630&from=pencil "Edit Post")

[Email This](https://www.blogger.com/share-post.g?blogID=35364652&postID=5933365541814525630&target=email "Email This")[BlogThis!](https://www.blogger.com/share-post.g?blogID=35364652&postID=5933365541814525630&target=blog "BlogThis!")[Share to X](https://www.blogger.com/share-post.g?blogID=35364652&postID=5933365541814525630&target=twitter "Share to X")[Share to Facebook](https://www.blogger.com/share-post.g?blogID=35364652&postID=5933365541814525630&target=facebook "Share to Facebook")[Share to Pinterest](https://www.blogger.com/share-post.g?blogID=35364652&postID=5933365541814525630&target=pinterest "Share to Pinterest")

Labels: [Strategies](http://epchan.blogspot.com/search/label/Strategies)

#### 31 comments:

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   Check out the recent academic literature on this topic- the concept of v p i n has been debunked by well known econometricians.

    the whole scheme is a joke
:   [Thursday, October 24, 2013 at 4:49:00 PM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1382647767717#c7180016140567436619 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/7180016140567436619 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Anon,
    Thanks for your input. Do you have a link to a relevant paper debunking it?
    Ernie
:   [Thursday, October 24, 2013 at 5:09:00 PM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1382648958159#c1064213862921812335 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/1064213862921812335 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   Ernie,

    I agree with you. I have read a lot on VPIN but have not found it to work well for trading. Signed order flow seems to work better. This is a bit disappointing since the VPIN literature is quite cool. There are plenty of VPIN papers on SSRN that supports it and that refutes it.
:   [Friday, October 25, 2013 at 4:47:00 AM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1382690857435#c7574171700560309148 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/7574171700560309148 "Delete Comment")

[![](//resources.blogblog.com/img/blank.gif "GekkoQuant")](http://www.gekkoquant.com) [GekkoQuant](http://www.gekkoquant.com) said...
:   Volume bars are an interesting concept, they contain much richer information than just time bars alone. Volume bars naturally sample the price faster at important parts of the day.

    One pitfall to lookout for during backtesting is to check that when a new volume bar is formed (and some relevant entry exit critria is met) it's during market hours.
:   [Friday, October 25, 2013 at 8:55:00 AM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1382705728021#c1034455428282969879 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/1034455428282969879 "Delete Comment")

[![](https://resources.blogblog.com/img/blank.gif "Gary")](https://www.blogger.com/profile/01590445291614242672) [Gary](https://www.blogger.com/profile/01590445291614242672) said...
:   Marcos Lopez de Prado one of the makers of the VPIN has many videos which he claims are in real time (you tube).... but I have not seen anyone replicate the same results yet
:   [Friday, October 25, 2013 at 10:48:00 AM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1382712483757#c1600796431295127341 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/1600796431295127341 "Delete Comment")

[![](//resources.blogblog.com/img/blank.gif "experquisite")](http://experquisite.tumblr.com) [experquisite](http://experquisite.tumblr.com) said...
:   Re: Volume bars, I did a brief study of SPY trades ordered by tick count (not volume sum), for normality:

    http://experquisite.tumblr.com/post/62621839837/spy-1000-tick-open-close-log-returns-over-the-last

    The series definitely seem better behaved when organized in some fashion of volume-clock/tick-clock/event-time/etc, but I have yet to attempt to adapt a co-integrated pairs trading scheme to in-homogeneous timescales.
:   [Friday, October 25, 2013 at 11:59:00 AM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1382716785451#c6208758898450629141 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/6208758898450629141 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "DR")](https://www.blogger.com/profile/07395057401348319239) [DR](https://www.blogger.com/profile/07395057401348319239) said...
:   The HFT shops that have good predictive models (i.e. are frequently trading in a directional way) are way more sophisticated than VPIN. They do trade on order flow (among other things), but in a deeply complex derived from massive datasets, tons of computing power and state of the art machine learning techniques.

    The hope of a simple indicator like VPIN beating this is pretty small. I'd expect you could find some evidence that it works well pre-2007, but I highly doubt there'd be any alpha left in any market of reasonable liquidity.
:   [Friday, October 25, 2013 at 7:36:00 PM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1382744161469#c7245587388955306586 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/7245587388955306586 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Hi all,
    Hat tip to a reader Mark who has shared with us these 2 papers:

    http://papers.ssrn.com/sol3/papers.cfm?abstract\_id=1881731

    http://papers.ssrn.com/sol3/papers.cfm?abstract\_id=2062450

    Ernie
:   [Monday, October 28, 2013 at 9:36:00 AM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1382967405102#c2292791071053375501 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/2292791071053375501 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   experquisite:
    Yes, I do agree that returns based on volume bars are more normally distributed than those based on time bars.
    Ernie
:   [Monday, October 28, 2013 at 9:38:00 AM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1382967490247#c8773180944990989655 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/8773180944990989655 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   Hi Ernie,

    thank you very much for sharing your comments on this interesting topic on which, in Italy, me and other academics are working since the mid of 2000s (an example it's the "quite old" working paper published in 2010
    http://www.eea-esem.com/files/papers/eea-esem/2011/885/Mosconi\_Carlini\_Manzoni\_Oslo.pdf).

    I really appreciate the fact that you point out the impossibility to generate profits net of transaction costs, considering that if you are able to gain, from a complete trading cycle, a gross profit equal to the sum of the bid ask spread plus one tick movement of the price, you are really skilled.

    But I'm still doubtful on a specific evidence: if you say that a trading rule based on order imbalance is not able to generate profits because gross profits are lower than transaction costs, in which way do high frequency traders gain profits generated by their activity of arbitrage obtained from same financial products traded on different venues? I don't think that high frequency traders, making profits from this type of arbitrage trading activity, are able to generate gross profits higher than bid ask spread + one tick of price movement. Moreover I'm not really sure that the estimation of transaction costs could be easily generalized, because it depends on the characteristics of each market operator.

    I would like also to share another point: actually, no one in academic literature has showed that the main intuitions of Easley, De Prado and O'Hara are not based on VPIN indicator (that is quite similar to simple indicators based on order imbalance used by other authors in the recent past), but on the innovative intuition of discretize high frequency data using volume buckets rather than clock time: the bucketing algorithm choice is the main explanation of why order imbalance hardly improves its predictive capabilities on financial returns
:   [Monday, October 28, 2013 at 5:59:00 PM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1382997550470#c6432877865468986300 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/6432877865468986300 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Hi Anon,
    Thanks for your input!

    HFT is able to take advantage of order flow plus "exploratory trading" to exploit short term returns. Please google: Clark-Joseph, 2013 “Exploratory Trading”.

    Actually, many traders know of using volume bars instead of time bars prior to this paper, but I agree this may be a better way to backtest many strategies.

    Ernie
:   [Tuesday, October 29, 2013 at 9:24:00 AM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1383053086678#c2789196125813570763 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/2789196125813570763 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   Ernie, thanks for your reply.

    I would like to ask you one more thing: how much you estimate a sufficient gross profit (in terms of basis point) before transaction costs per trading cycle (that's so say open buy\sell and then close sell\buy), in order to make profitable a trading rule based on order flow?
:   [Tuesday, October 29, 2013 at 1:11:00 PM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1383066664210#c1145626367336261694 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/1145626367336261694 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Anon,
    The main transaction cost is the bid-ask spread, which for ES is about 2 bps for a round trip. Commissions, exchange fee, regulatory fee totals about 0.3 bps one way for a retail account. So you need a profit per trade of about 1.3 bps.

    Ernie
:   [Tuesday, October 29, 2013 at 3:27:00 PM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1383074833412#c1570825220330204369 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/1570825220330204369 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   Thank you again Ernie!

    I think that if I would like to gain profits with order flow I must transform bid ask spread from a center of cost to a center of profit. Or, maybe, try to be neutral to bid-ask spread (that's to say when I open the position I can use market orders (directly hitting bid or ask on limit order book), but when I close the original opened position I must use limit orders - in this way I'll be neutral to bid-ask spread, because first time): in this way, if I'm able to statistically forecast the short term direction of price movement, gaining profit only from 1 tick price movement, if this 1 tick price movement is higher than commissions + exchange fee + regulatory fee I can have success in this kind of trading strategy.
:   [Tuesday, October 29, 2013 at 5:07:00 PM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1383080829025#c2447284709342643095 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/2447284709342643095 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   hi Ernie,

    If we get portfolio margin in IB, and trade long/short ETFs, could we get about 6 times leverage for overnight positions?

    Or if we trade intraday long/short ETFs, could we get even higher leverage?
:   [Friday, November 8, 2013 at 3:43:00 AM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1383900189452#c1148027444142105402 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/1148027444142105402 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Hi Anon,
    IB's portfolio margin is based on the exact composition of your portfolio. So yes, it is theoretically possible to get x6 intraday and/or overnight leverage with very safe constituents (e.g. long-short large cap ETF). But it all depends on running their risk model on your specific portfolio.

    Ernie
:   [Friday, November 8, 2013 at 7:40:00 AM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1383914412665#c8473895341367371884 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/8473895341367371884 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   hi Ernie,

    In your new book,you mention about "Danger of Data errors."

    You said that broker's data feed cause some losing trades, so you switched data feed to a third-party provider.
    May I ask which is this 3rd party provider? Which real-time data feed is stable and cheap?
    I think I cannot afford Bloomberg now.

    I guess the broker you mentioned here is IB.
:   [Friday, November 8, 2013 at 5:40:00 PM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1383950433289#c1161228292717967730 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/1161228292717967730 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Hi Anon,
    I have been told that IQFeed is a good one.
    Ernie
:   [Friday, November 8, 2013 at 6:38:00 PM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1383953925047#c8267793932119109386 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/8267793932119109386 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   hi Ernie,

    Do you do cross validation?

    For Kalman filter, as you mentioned before, there is no need to separate the data into "training" and "test" sets. Therefore, how do we do cross validation?
:   [Wednesday, November 13, 2013 at 2:12:00 AM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1384326723869#c7271055921960132285 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/7271055921960132285 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Hi Anon,
    Even in Kalman Filter, you still need a separate training set for parameters that define the initial distributions for the state and observed variables.

    Cross-validation is a different way to separate training and test data, since it involves dividing the data into many subsets and picking each subset as the test data in turn. This method is not particularly suitable for Kalman Filter because the time series won't be the same if you introduce gaps into the sequence of prices.

    Ernie
:   [Wednesday, November 13, 2013 at 8:13:00 AM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1384348409279#c9133854358874144541 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/9133854358874144541 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   Hi Ernie,

    In your book, you mentioned "Primary vs. Consolidated stock prices."

    Could we get historical prices from the primary exchanges from IQfeed?

    I guess it shall be ok for tick data because they usually have "Exchange column."

    I wonder if it is ok for 1 minute bars or end-of-day.
:   [Thursday, November 14, 2013 at 9:17:00 AM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1384438664469#c4375605210445059177 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/4375605210445059177 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Hi Anon,
    I personally have not used IQFeed, so I don't know if they provide primary exchange data. If they do, I am sure that it should be available both for 1-min bars and EOD prices.
    Ernie
:   [Thursday, November 14, 2013 at 9:51:00 AM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1384440682145#c3692512229904232290 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/3692512229904232290 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   hi Ernie,

    In IB, when we download historical stock data, we can choose "Primary Exchange" instead of "SMART" in contract.
    Does that mean we can get historical 1 minute bars directly from "NYSE" or "NASDAQ"?
:   [Thursday, November 14, 2013 at 6:12:00 PM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1384470737116#c7188402472019445476 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/7188402472019445476 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Hi Anon,
    Actually, I don't believe IB will let you download primary exchange data. I am not sure setting exchange=NYSE will work for historical data.
    Ernie
:   [Thursday, November 14, 2013 at 8:37:00 PM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1384479437099#c1257305709987273139 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/1257305709987273139 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   Hi Ernie,
    I have a trading system based on some technical indicators and I would now like to setup an quantitative trading algorithm for it so it can trade faster. Would you suggest someone I can work with?

    J
:   [Sunday, December 8, 2013 at 6:41:00 PM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1386546064394#c5103238720832918584 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/5103238720832918584 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Hi J,
    My associate does work on such projects. Please email me so I can connect you both.
    Ernie
:   [Sunday, December 8, 2013 at 7:04:00 PM EST](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1386547463866#c4872223655859795729 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/4872223655859795729 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Anonymous") Anonymous said...
:   I would take the other side to all of you fools. You're always looking at the wrong thing in the wrong places. Vpin, computer models. Who programs the models you mupets. Trading. Proper trading is done by people. There is your bigest and only clue...
:   [Friday, March 20, 2015 at 7:03:00 PM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1426892611659#c1053103924063988851 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/1053103924063988851 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "sunnycalif")](https://www.blogger.com/profile/05925235491084049337) [sunnycalif](https://www.blogger.com/profile/05925235491084049337) said...
:   Hi Ernie..i think Volume is the heart beat of the market. I am retail and do not have sophisticated platforms available to Quants. However I have been studying Speed in the markets and it is Volume & Speed which turns the markets. Have been doing some indicator with sub-second precision on retail platform such as Tradestation for number of years.
    Recently came across the concept of VPIN and I decided to also look into your thoughts.
    The topic of VPIN interests me quite a bit as it involves balance/imbalance and Speed and study of Volume. I would like to know if you have any development recommendation of VPIN using retail platforms such as Ninjatrader which is coded using C# >Net. And how can I try and pursue this. Any insights will be appreciated. I did see you on a previous post mention probably of an associate and hence thought of checking.
:   [Friday, October 21, 2016 at 10:26:00 PM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1477103181068#c4894666088976446071 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/4894666088976446071 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Hi Sunnycalif,

    The best way to compute order flow accurately is if the data feed has an aggressor flag to determine if a trade is buy or sell-side initiated. But such data feed is very expensive. So for a less accurate estimate, we can use the VPIN method, which only requires the volume and the last trade prices of bars. Any brokers' data feed would provide that. The method to compute order flow using just bar data is given in the papers I cited in the article above.
    Ernie
:   [Saturday, October 22, 2016 at 7:17:00 AM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1477135040949#c4449441945172341243 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/4449441945172341243 "Delete Comment")

![](//resources.blogblog.com/img/blank.gif "Francois Laurent") Francois Laurent said...
:   This boils down to adverse selection and the probability of informed trading (PIN) and subsequently how to skew prices and quantities. Any good documents/papers on this topics that have had some practical uses? Especially on the last bit which is about integrating the PIN into a strategy (I have already a good estimate of my PIN).
:   [Thursday, July 13, 2017 at 6:53:00 AM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1499943234801#c2504989688953808767 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/2504989688953808767 "Delete Comment")

[![](//www.blogger.com/img/blogger_logo_round_35.png "Ernie Chan")](https://www.blogger.com/profile/02747099358519893177) [Ernie Chan](https://www.blogger.com/profile/02747099358519893177) said...
:   Hi Francois,
    Actually the Intraday Trading chapter of my new book Machine Trading has a complete implementation of a trading strategy using VPIN. Have you taken a look?
    Ernie
:   [Thursday, July 13, 2017 at 9:01:00 AM EDT](http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html?showComment=1499950861532#c8926809169085600675 "comment permalink")    [![](https://resources.blogblog.com/img/icon_delete13.gif)](https://www.blogger.com/comment/delete/35364652/8926809169085600675 "Delete Comment")

[Post a Comment](https://www.blogger.com/comment/fullpage/post/35364652/5933365541814525630)

[Newer Post](http://epchan.blogspot.com/2013/11/cointegration-trading-with-log-prices.html "Newer Post")   [Older Post](http://epchan.blogspot.com/2013/08/guest-post-qualitative-review-of-vix-f.html "Older Post")  [Home](http://epchan.blogspot.com/)

Subscribe to: [Post Comments (Atom)](http://epchan.blogspot.com/feeds/5933365541814525630/comments/default)
