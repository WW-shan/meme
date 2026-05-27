# [Order flow toxicity on DEXes](/t/order-flow-toxicity-on-dexes/13177)

I am writing a deep dive on the order flow toxicity on decentralized exchanges such as Uniswap v3. Here is the tl;dr.

To make LPing more profitable, DEXes need to attract a higher volume of non-arbitrage trade. It is particularly important to attract large-volume non-arbitrage traders, think an institutional investor who needs to rebalance. What do they need to come to DEXes? Two things: liquidity and resilience.

Liquidity is crucial because large traders primarily care about their price impacts. The higher the liquidity, the lower the price impact. Uniswap is doing great on liquidity.

What is resilience and why is it important? Large non-arb trades are rarely executed in a single order; instead they are broken down into small orders and executed gradually over time. This is yet another way to minimize price impact costs. For this process to work, the mid-price and liquidity need to recover quickly after an uninformed trade. This is called market resilience. Without it, large traders cannot benefit from order splitting.

And here is one issue with Uniswap as compared to LOB exchanges. With limit order books, both liquidity takers and makers can move the mid-price back to the efficient level. In Uniswap, it is only the takers. But the takers have to pay the swap fee, so they don’t have incentives to do it unless the price has deviated by more than the swap fee. This is not good for resilience.

Here are the details with examples:  
[Part one](https://medium.com/@alexnezlobin/toxic-order-flow-on-decentralized-exchanges-problem-and-solutions-a1b79f32225a) (describes strategies used by large traders in TradFi), [Part two](https://medium.com/@alexnezlobin/how-resilient-is-uniswap-v3-81bc548a0312) (on resilience of Uniswap v3).

More to come.

What do you think?

I think this is a great framework and I argue that not only do you want high resilience but [you actually want *low* liquidity](https://twitter.com/llllvvuu/status/1552501620679725056?s=20&t=Ac1BQ01V62qJYh9fKfc_ZQ) (high price impact). i.e. you want a market which gets out of the way of dislocations but is, like you said, flexible to revert. Hence selectively taking benign TWAP flow and not sudden pumps/dumps.

FWIW, if gas fees are low then you can have maker-driven discovery, which as you point out, is ideal. I won’t name names, but there are concentrated-liquidity AMMs which are focusing on this message rather than “passive liquidity” which does not engage in price discovery.

I think this is a great framework and I argue that not only do you want high resilience but [you actually want *low* liquidity](https://twitter.com/llllvvuu/status/1552501620679725056?s=20&t=Ac1BQ01V62qJYh9fKfc_ZQ) (high price impact). i.e. you want a market which gets out of the way of dislocations but is, like you said, flexible to revert. Hence selectively taking benign TWAP flow and not sudden pumps/dumps.

That’s exactly right - makers often want to release their liquidity to the market gradually over time so that more of it is taken by uninformed takers and less by arbitrageurs. What I meant to say so far is that *takers* (even uninformed) prefer more liquidity to less.

Ideally, a protocol should offer ways for both gradual making and taking of liquidity. This is, in fact, going to be the main point of our third and fourth posts (to come soon). In traditional exchanges, most of the liquidity is supplied with either iceberg orders or limit orders that are quickly canceled if unfilled. Letting a large amount of liquidity sit for a long time is essentially equivalent to feeding arbitrageurs.

I won’t name names, but there are concentrated-liquidity AMMs which are focusing on this message rather than “passive liquidity” which does not engage in price discovery.

We are going to talk a bit about two protocols making such claims - DODO and Maverick. So far I am not convinced by them but I might be missing something. The biggest problem with DODO in my view is its reliance on external oracles - this is essentially a blank check to frontrunners. Re Maverick, they have not released much detail yet and seem to be falling a bit behind their schedule. From what I could tell from the public beta though, the problem discussed in this post applied to their design as well. We’ll see what happens when they describe the actual price discovery mechanism.

If you know of some other interesting developments, please let me know.

![](https://ethresear.ch/user_avatar/ethresear.ch/llllvvuu/48/9687_2.png)

FWIW, if gas fees are low then you can have maker-driven discovery, which as you point out, is ideal.

A+, I do think this is a principle distinction between concentrated liquidity AMMs and off-chain stuff.

What seems most likely to me would be for there to be something of a bridging class of institutions, those who interface to tradfi institutional investors and access on-chain liquidity sources on the back-end. In this type of world, their flow would still be more toxic than vanilla institutions, since they’d likely have sophisticated routing that only accesses dexes when the dexes’ prices are better than other sources.

![](https://ethresear.ch/user_avatar/ethresear.ch/alexnezlobin/48/9749_2.png)

We are going to talk a bit about two protocols making such claims - DODO and Maverick. So far I am not convinced by them but I might be missing something. The biggest problem with DODO in my view is its reliance on external oracles - this is essentially a blank check to frontrunners. Re Maverick, they have not released much detail yet and seem to be falling a bit behind their schedule. From what I could tell from the public beta though, the problem discussed in this post applied to their design as well. We’ll see what happens when they describe the actual price discovery mechanism.

If you know of some other interesting developments, please let me know.

I think “maker-driven discovery” can mean two things:

What you’ve described are attempts at 2), I imagine. I’m skeptical that we can have 100% 2) (there’s a good reason the top MMs keep their strategies secret), but likely we can have some combination of 1) + 2) where the contract does provide useful safeguards.

.1) is mostly a marketing thing at this point, as concentrated liquidity does technically allow the end user (notwithstanding gas fees) to price nimbly; but few are shifting their messaging to encourage this. I think there are also microstructural things that can be done to enhance 1), such as liquidity that disappears after being filled (like traditional orders), [last-look/minimum-TTL](https://www.crocswap.com/whitepaper) etc. For 2), I agree with you that oracles are a troublesome approach. One thing that may help LPs is some sort of “unexpected volume” penalty for swappers. The assumption would be that normal amounts of volume indicate benign trading activity and should get a good price, whereas abnormal amounts of volume indicate adverse trading activity and should be charged a high price.

[Here](https://twitter.com/llllvvuu/status/1553507807332163584?s=20&t=tgRXIPEs1GHMyTXcJ6442A)’s my current framework on microstructure.

What we have in mind is indeed a combination of 1 and 2 - the contract should provide incentives for additional price discovery when trading is getting slow. We’ll post more about this very soon.

I am also not a fan of pure 2 for many reasons. Yet I’m not fully convinced that it absolutely can’t work.

MMs do keep their strategies secret, but that’s largely because they aggressively compete with other MMs with secret strategies. DEX protocols may not be as efficient in terms of their pure market-making ability but as long as there is demand for trading and LPing on the chain, they have more monopoly power. Basically a DEX is not competing with Citadel in an order-book market but rather with other AMMs with public algorithms. Then the question becomes what kind of market structure is better - algorithmic (crowdfunded) dealer or LOB? With cheap and fast transactions, we sort of know that nothing beats LOBs. But I am not sure that that’s the case when order placements and cancelations are slow, expensive, and publicly observed. A risk-averse dealer implementing a sensible strategy might do better.

100% with you on the liquidity that disappears - that is one of our main points in the last post. (We call it one-way liquidity)

Skeptical on last look largely because of its record in TradFi - it essentially creates opportunities for abuse by makers. Minimum-TTL could make sense, but I’m not sure how consistent it is with the general trend of becoming more LOB-like. After all in LOBs, most limit orders are canceled and repriced very quickly if unfilled, so min-TTL would kill all that vibe. If its significant, it also creates risks for regular LPs. But again, on this one, much depends on calibration

And Crocswap has some nice ideas, I agree. Single contract, pooling of assets, ambient liquidity - all make sense!

![](https://ethresear.ch/user_avatar/ethresear.ch/alexnezlobin/48/9749_2.png)

Then the question becomes what kind of market structure is better - algorithmic (crowdfunded) dealer or LOB? With cheap and fast transactions, we sort of know that nothing beats LOBs. But I am not sure that that’s the case when order placements and cancelations are slow, expensive, and publicly observed. A risk-averse dealer implementing a sensible strategy might do better.

Admittedly my calculus does assume that blockchain will scale, such that the computational and latency constraints can’t be relied upon as much for AMMs. I also think that if/when this happens, aggregators will pit AMMs against RFQs and LOBs for order flow. However, I’m still keen on design of “algorithmic (crowdfunded) dealer” / “risk-averse dealer”.

![](https://ethresear.ch/user_avatar/ethresear.ch/alexnezlobin/48/9749_2.png)

Skeptical on last look largely because of its record in TradFi - it essentially creates opportunities for abuse by makers. Minimum-TTL could make sense, but I’m not sure how consistent it is with the general trend of becoming more LOB-like. After all in LOBs, most limit orders are canceled and repriced very quickly if unfilled, so min-TTL would kill all that vibe. If its significant, it also creates risks for regular LPs. But again, on this one, much depends on calibration

Yup, this one is definitely a tradeoff, which I think TradFi is still figuring out. Benign takers want liquidity to be firm because they make decisions based on visible liquidity, but firm liquidity is vulnerable to adverse takers (resolving this is one of the benefits of RFQ). The question for microstructure is, are makers the sharks or are takers the sharks? To which the answer is of course, both, which makes this very complicated and the discussion in TradFi rages on even today.

The purest case in DeFi where this has implications is aggregators, where trades are routed according to visible liquidity. In a world of sufficiently sophisticated aggregators (which I don’t think exist yet), one might imagine “algorithmic (crowdfunded) dealer” being preferred for order flow if they are considered more firm; another reason they might be preferred is that they’re easier to compute prices/routes over ([optimal routing computation](https://arxiv.org/abs/2204.05238)).

Finally, there is another place where I think the “CFMM” adds value, which is as a form of risk management. If one designs a “smart” AMM but places a restriction on it to never price cheaper than some CFMM with the same reserves, then the maximum loss of the AMM is bounded in terms of the underlying’s price, via the CFMM’s portfolio value function.

Admittedly my calculus does assume that blockchain will scale, such that the computational and latency constraints can’t be relied upon as much for AMMs. I also think that if/when this happens, aggregators will pit AMMs against RFQs and LOBs for order flow. However, I’m still keen on design of “algorithmic (crowdfunded) dealer” / “risk-averse dealer”.

Yep, scaling solutions and aggregators will certainly pose problems for AMMs. Yet there appears to be quite a bit of supply of passive liquidity - some people are willing to do it even at almost zero rates of return. It is interesting to see what is happening with Serum on Solana: they have an order book but Raydium, an AMM which essentially forwards liquidity to Serum, is also very much alive.

The question for microstructure is, are makers the sharks or are takers the sharks?

Somehow I feel that the sharks will always be overrepresented in the group that makes the last move. So, for example, without last look - among takers, with last look - among the makers invoking it. That’s why I think that the right to make the last move should cost money.

Finally, there is another place where I think the “CFMM” adds value, which is as a form of risk management. If one designs a “smart” AMM but places a restriction on it to never price cheaper than some CFMM with the same reserves, then the maximum loss of the AMM is bounded in terms of the underlying’s price, via the CFMM’s portfolio value function.

This is certainly one of the advantages of the CFMM model, but it usually comes at the cost of lower expected profits when the order flow is not too toxic. For instance, in Uniswap v3, if there is sufficient uninformed flow, then the best strategy for LPs is to always concentrate their liquidity as much as possible around the current price (and move it together with it). But then they will lose everything (in expectation, over a long horizon) if the order flow is toxic. They can limit their losses by not moving their liquidity, but then their expected profits will also be lower when the uninformed flow is high. I think that having the option of a limited loss is still useful. It would be good for one of those AMMs that constantly move liquidity to implement it.

By the way, all parts of our series are out now, including our thoughts on how to reduce the problem. I’ll respond to my original post with the links in a few minutes - can’t find the edit button!

UPDATE

All parts of our series are out now:  
[Part three](https://medium.com/@alexnezlobin/executing-large-trades-with-range-orders-on-uniswap-v3-a4a5e4debb67) - on executing large trades with range orders on Uniswap v3  
[Part four](https://medium.com/@alexnezlobin/solving-order-flow-toxicity-d388126cf69a) - solving order flow toxicity

tl;dr

When investors use with limit orders they trade off the execution price improvement for non-execution and pick-off risks. For Uniswap v3 range orders, both of these risks can be high primarily because the orders are self-reversing and their placement options are limited. However, the price improvement can also be high because of the earned fees.

Suggestions for Uniswap:

We also think that there is clearly room for AMMs that position the liquidity automatically. In the last part, we discuss the additional features that such AMMs can implement

Using [@alexnezlobin](/u/alexnezlobin) ’s excellent work as a reference, I implemented a **order-flow toxicity / liquidity-shock detector** and a simple trading policy on top of it.

You can find it on Github → `Divyn/amm-flow-toxicity-alpha-engine`

`Divyn/amm-flow-toxicity-alpha-engine`

At a high level, the system:

Streams real-time DEX pool data

Detects **unexpected volume bursts** combined with sharp, directional price impact

Explicitly estimates short-horizon price impact and flags regimes where liquidity is likely being consumed by **adverse flow** rather than benign TWAP-style trading

The strategy layer then uses this signal to \*\*fade shocks , so it “\*\*steps away” during toxic regimes and only re-engaging once flow normalizes.

The codebase is open and modular, so it should be easy to adapt this either for:

**LP protection mechanisms** (e.g. widening spreads or pulling liquidity during toxic regimes), or

**protocol-level penalties on unexpected volume**, as discussed above.

Does this match how you’d expect toxic flow to manifest empirically, and whether **volume surprise + short-horizon impact** feels like a reasonable primitive from your perspective?

Powered by [Discourse](https://www.discourse.org), best viewed with JavaScript enabled
