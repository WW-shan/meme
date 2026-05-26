[Skip to article](#screen-reader-main-title)


[![Elsevier logo](/shared-assets/24/images/elsevier-non-solus-new-grey.svg)](/)

[My account](/user/login?targetURL=%2Fscience%2Farticle%2Fpii%2FS2173126812000344&from=globalheader)

[Sign in](/user/institution/login?targetURL=%2Fscience%2Farticle%2Fpii%2FS2173126812000344)

* [Access through **your organization**](/user/institution/login?targetUrl=%2Fscience%2Farticle%2Fpii%2FS2173126812000344)

## Article preview

* [Abstract](#preview-section-abstract)
* [Introduction](#preview-section-introduction)
* [Section snippets](#preview-section-snippets)
* [References (40)](#preview-section-references)
* [Cited by (35)](#preview-section-cited-by)

[![Society Logo](https://ars.els-cdn.com/content/image/D21731268.gif)](/journal/the-spanish-review-of-financial-economics "Go to The Spanish Review of Financial Economics on ScienceDirect")

## [The Spanish Review of Financial Economics](/journal/the-spanish-review-of-financial-economics "Go to The Spanish Review of Financial Economics on ScienceDirect")

[Volume 10, Issue 2](/journal/the-spanish-review-of-financial-economics/vol/10/issue/2 "Go to table of contents for this volume/issue"), July–December 2012, Pages 74-83

[![The Spanish Review of Financial Economics](https://ars.els-cdn.com/content/image/1-s2.0-S2173126812X00032-cov150h.gif)](/journal/the-spanish-review-of-financial-economics/vol/10/issue/2)

# From PIN to VPIN: An introduction to order flow toxicity[☆](#aep-article-footnote-id4)

Author links open overlay panel,

[https://doi.org/10.1016/j.srfe.2012.10.002](https://doi.org/10.1016/j.srfe.2012.10.002 "Persistent link using digital object identifier")[Get rights and content](https://s100.copyright.com/AppDispatchServlet?publisherName=ELS&contentID=S2173126812000344&orderBeanReset=true)

## Abstract

As an update of the well-known PIN measure, [Easley et al. (2012a)](#bib0115) have developed a new measure of order flow toxicity called Volume-Synchronized Probability of Informed Trading or VPIN. Order flow toxicity makes reference to adverse selection risk but applied to the world of high frequency trading (HFT). We provide a detailed description of the VPIN estimation procedure paying special attention to the main innovations introduced and the key variables of this novel tool. By using a sample of stocks listed on the Spanish market, we compare VPIN to PIN. Although VPIN metric is conceived for the HFT environment, our results suggest that certain VPIN specifications provide proxies for adverse selection risk similar to those obtained by the PIN model. Thus, we consider that the key variable in the VPIN procedure is the number of buckets used and that VPIN can be a helpful device which is not exclusively applicable to the HFT world.

## Introduction

The 2010 Flash Crash is without a doubt the shortest event in the recent history of financial markets to merit so much attention and generate so much controversy among practitioners and academics. On May 6th 2010 the Dow Jones Industrial Average plunged about 1000 points – or about 9% – only to recover those losses within minutes.1 Although the ultimate cause of the Flash Crash is still under discussion (e.g., Kirilenko et al., 2011, Madhavan, 2012) it is generally accepted that this event was the result of a new trading paradigm emanating from legislative changes in the US (“Regulation National Market System” of 2005, or “Reg NMS”) and Europe (“Markets in Financial Instruments Directive” of 2007, or “MiFID”) and prompted by substantial technological advances in computation and communication. The new legislative environment fostered both greater competition and market fragmentation while technological advances made high-speed trading technically possible at and between different trading venues. As a result, the world of high frequency trading (HFT) has appeared as a new reality in current markets that is progressively outshining traditional or low frequency trading (LFT).2

A number of studies indicate that HFT is playing a crucial role in liquidity supply activity in current markets. Hasbrouck and Saar (2012), by analyzing low-latency activity (i.e., trading strategies that respond to market events in the millisecond environment) find that it improves traditional market quality measures such as the liquidity in the limit order book. Similarly, Brogaard et al. (2012) find evidence of HFT benefitting price efficiency and the provision of liquidity at stressful times such as the most volatile days and before and after macroeconomic news announcements. Nevertheless, in the HFT environment the liquidity provision activity and its associated risks acquire a new dimension. Thus, Easley et al. (2012a) introduce the concept of “order flow toxicity” to represent adverse selection risk in the HFT context. In the authors’ words “order flow is regarded as toxic when it adversely selects market makers who may be unaware that they are providing liquidity at a loss” (p. 1458). Thus, in this case, adverse selection must be understood not only as a problem of asymmetric information but also as a wider notion that may encompass other risks related to liquidity provision. When order flows are essentially balanced, high frequency market makers have the potential to earn razor thin margins on massive numbers of trades. When order flows become unbalanced, however, market makers face the prospect of losses due to adverse selection. These market makers’ estimates of the time-varying toxicity level now becomes a crucial factor in determining their participation. If they believe that toxicity is high, they will liquidate their positions and leave the market. To measure “order flow toxicity” Easley et al. (2012a) present the Volume Synchronized Probability of Informed Trading or VPIN metric, a new procedure to estimate the probability of informed trading based on volume imbalance and trade intensity.

VPIN is inspired by the well-known PIN model of Easley et al. (1996), henceforth EKOP (1996). The PIN is a consolidated model to measure the presence of informed traders that has been widely adopted to address a variety of issues in the empirical financial literature, among others: information content of the time between trades (Easley et al., 1997a), trade size (Easley et al., 1997b), analyst coverage (Easley et al., 1998), electronic market order flow (Brown et al., 1999), stock splits (Easley et al., 2001), dealer vs. auction markets (Heidle and Huang, 2002), asset pricing (Easley et al., 2002, Aslan et al., 2011), non-anonymous vs. anonymous trading systems (Gramming et al., 2001), market reaction to public and private information (Vega, 2006), corporate investment decision (Ascioglu et al., 2008, Chen et al., 2007), block ownership (Brockman and Yan, 2009), and market anomalies (Kang, 2010, Chen and Zhao, 2012). However, the PIN is not extent from criticism. First, there is a growing debate as to the appropriateness of PIN in measuring information-based trading (Aktas et al., 2007, Duarte and Young, 2009, Easley et al., 2010, Akay et al., 2012). Second, several papers show that the PIN estimations could suffer several biases for different reasons such as trade misclassification (Boehmer et al., 2007), boundary solutions or the floating-point exception, especially in very active stocks (Easley et al., 2010, Lin and Ke, 2011, Yan and Zhang, 2012), and propose different solutions to mitigate such biases.

PIN and VPIN models require trading volume classified as buy or sell and are based on the notion that order imbalances signal the presence of adverse selection risk. However, the VPIN approach has some practical advantages over the PIN methodology that make it particularly attractive for both practitioners and researchers. The main advantage is that VPIN does not require the estimation of non-observable parameters using optimization or numerical methods thereby avoiding all the associated computational problems and biases. In addition, VPIN allows the capturing of risk variations at intraday level while the original PIN model does not.

In a series of related papers Easley et al., 2011a, Easley et al., 2011b, Easley et al., 2012a present the VPIN as a useful tool for different market participants. Easley et al. (2011a) show the VPIN of the e-mini S&P500 futures contract achieving its maximum level around the Flash Crash. Higher levels of toxicity force HF market makers to liquidate their positions and leave the market offering a plausible explanation of the Flash Crash. The authors recommend that regulators use VPIN as a warning tool that could herald the implementation of regulatory actions to forestall crashes.3 Easley et al. (2012a) also show that VPIN has forecasting power over volatility (toxicity-induced) and could become valuable as a risk management tool for market making activity. It can be also useful for trading strategies based on volatility arbitrage and for brokers who look for best time of execution. Easley et al. (2011b) present the specifications of a VPIN contract, which could be used to hedge against the risk of higher than expected levels of toxicity as well as to monitor such risk. On the other hand, Andersen and Bondarenko (2011) put forward several criticisms questioning the predictive power of VPIN. In particular, the authors document that VPIN is a poor predictor of short run volatility with a limited predictive power emanating from the mechanical relation to the underlying trading intensity. Andersen and Bondarenko's analysis provoked a speedy response from Easley et al. (2012d) who basically point to the confusion in the methodology they use, the analysis they perform and the conclusions they draw.

Using a selected sample of 15 Spanish stocks, the main objective of this paper is to offer a detailed description of the VPIN estimation procedure, its key variables, and its usefulness in an attempt to gain a better understanding of this novel tool. Departing from the PIN model, we document the main innovations introduced in this updated version of the probability of informed trading and we analyze the compatibility of both models. To the best of our knowledge, this is the first study to apply VPIN methodology to a sample of European stocks.4 Although the relevance of HFT in the Spanish Stock Exchange has not yet been formally measured, mostly because of data availability problems, informal conversations with regulators corroborate the interest of HF traders in the most active stocks listed on the Spanish market.

Our results suggest that certain VPIN specifications provide proxies for adverse selection risk similar to those obtained by the PIN model. In this sense, we consider that the key variable in the VPIN procedure is the number of buckets used, so estimations of VPIN using one bucket are quite similar to those obtained by the PIN model. We conclude that VPIN is, in the main, a straightforward way to measure adverse selection but not exclusively for the high frequency environment.

The paper is organized as follows: Section 2 briefly reviews the PIN model. Section 3 focuses on VPIN putting special emphasis on the main innovations it incorporates and its computational procedure. Section 4 describes the Spanish stock market and the sample employed. Section 5 compares PIN to VPIN aggregated values. Section 6 concludes.

## Access through your organization

Check access to the full text by signing in through your organization.

[Access through **your organization**](/user/institution/login?targetUrl=%2Fscience%2Farticle%2Fpii%2FS2173126812000344)

## Section snippets

## PIN model (EKOP 1996)

The probability of information-based trading (PIN) is a measure of the information asymmetry between informed and uninformed trades that builds on the theoretical work of Easley and O’Hara, 1987, Easley and O’Hara, 1992. The original PIN model was introduced by Easley et al. (1996). Since then, various empirical papers have implemented, adapted, and improved the PIN approach (Easley et al., 1997a, Easley et al., 1997b, Easley et al., 1998, Easley et al., 2008). The PIN measure is not directly

## VPIN model (Easley et al., 2012a)

The fundamental link between PIN and VPIN can be found in Easley et al. (2008). Departing from EKOP (1996) PIN model as a benchmark, these authors develop a dynamic econometric model of trading by introducing time-varying (GARCH-style) arrival rates of informed and uninformed traders. They show that for a particular period of time *τ* (e.g., days), the expected trade imbalance approximates (PIN numerator) while the expected total number of trades equals

## Market description, data, and sample

Our sample is made up of stocks traded on the electronic trading platform of the Spanish Stock Exchange, known as the SIBE (*Sistema de Interconexión Bursátil Español*). The SIBE is an order-driven market where liquidity is provided by an open limit order book. Trading is continuous from 9:00 am to 5:30 pm. There are two regular call auctions each day: the first one determines the opening price (8:30-9:00 am), whereas the second one sets the official closing price (5:30-5:35 pm). A continuous

## Empirical evidence: PIN and VPIN comparison

In this section we compare the VPIN model with its predecessor PIN by applying both methods to the same stock sample. As we have discussed, both models are based on the observation of order imbalances to measure the probability of being adversely selected. VPIN is introduced as the updated version of PIN in a double sense: (1) as a new tool designed to deal with the new risks from the new market paradigm of HFT, and (2) as a straightforward approach to obtain the probability of being adversely

## Concluding remarks

“HFT is here to stay” (Easley et al., 2012c, p. 27). Whereas several researchers focus on the unavoidable debate about the pros and cons of this growing activity worldwide, other researchers are embarking on the design of new tools to deal with the different demands arising from this new paradigm. Easley, López de Prado and O’Hara belong to this second group. Departing from the well-known PIN model to measure the probability of informed trading, these authors developed a new tool called

## References (40)

* O. Akay *et al.*

  ### [What does PIN identify? Evidence from the T-bill market](/science/article/pii/S1386418111000346)

  ### Journal of Financial Markets

  (2012)
* N. Aktas *et al.*

  ### [The PIN anomaly around M&A announcements](/science/article/pii/S1386418106000553)

  ### Journal of Financial Markets

  (2007)
* Y. Amihud

  ### [Illiquidity and stock returns: cross-section and time-series effects](/science/article/pii/S1386418101000246)

  ### Journal of Financial Markets

  (2002)
* A. Ascioglu *et al.*

  ### [Information asymmetry and investment-cash flow sensitivity](/science/article/pii/S0378426607002932)

  ### Journal of Banking and Finance

  (2008)
* H. Aslan *et al.*

  ### [The characteristics of informed trading: implications for asset pricing](/science/article/pii/S0927539811000600)

  ### Journal of Empirical Finance

  (2011)
* E. Boehmer *et al.*

  ### [Estimating the probability of informed trading-does trade misclassification matter?](/science/article/pii/S138641810600036X)

  ### Journal of Financial Markets

  (2007)
* P. Brockman *et al.*

  ### [Block ownership and firm-specific information](/science/article/pii/S037842660800188X)

  ### Journal of Banking and Finance

  (2009)
* P. Brown *et al.*

  ### [Characteristics of the order flow through an electronic open limit order book](/science/article/pii/S1042443199000190)

  ### Journal of International Financial Markets, Institutions and Money

  (1999)
* Y. Chen *et al.*

  ### [Informed trading, information uncertainty, and price momentum](/science/article/pii/S0378426612000787)

  ### Journal of Banking and Finance

  (2012)
* J. Duarte *et al.*

  ### [Why is PIN priced?](/science/article/pii/S0304405X08001827)

  ### Journal of Financial Economics

  (2009)

- D. Easley *et al.*

  ### [The information content of the trading process](/science/article/pii/S0927539897000054)

  ### Journal of Empirical Finance

  (1997)
- D. Easley *et al.*

  ### [Price, trade size and information in security markets](/science/article/pii/0304405X87900298)

  ### Journal of Financial Economics

  (1987)
- D. Easley *et al.*

  ### [Financial analysts and informed-based trade](/science/article/pii/S1386418198000020)

  ### Journal of Financial Markets

  (1998)
- M. Kang

  ### [Probability of information-based trading and the January effect](/science/article/pii/S0378426610002657)

  ### Journal of Banking and Finance

  (2010)
- C. Vega

  ### [Stock price reaction to public and private information](/science/article/pii/S0304405X06000444)

  ### Journal of Financial Economics

  (2006)
- Y. Yan *et al.*

  ### [An improved estimation method and empirical properties of the probability of informed trading](/science/article/pii/S0378426611002433)

  ### Journal of Banking and Finance

  (2012)
- D. Abad *et al.*

  ### Modelos de estimación de la probabilidad de negociación informada: una comparación metodológica en el mercado español

  ### Revista de Economía Financiera

  (2005)
- Andersen, T., Bondarenko, O., 2011. VPIN and the flash crash. Unpublished Working Paper. Available at SSRN:...
- E.W. Bethel *et al.*

  ### Federal market information technology in the post-flash crash era: roles for supercomputing

  ### Journal of Trading

  (2012)
- Brogaard, J., Hendershott, T., Riordan, R., 2012. High frequency trading and price discovery. Unpublished Working...

## Cited by (35)

* ### [Reflecting on the VPIN dispute](/science/article/pii/S1386418113000475)

  2014, Journal of Financial Markets

  Citation Excerpt :

  We now turn to the remaining ELO references. Abad and Yague (2012) follow the exact ELO (2012a) BV-VPIN procedure and provide no independent analysis of relevance to the current discussion. Bohn (2011) contains no mention of VPIN at all!

  In [Andersen and Bondarenko (2014)](#bib5), using tick data for S&P 500 futures, we establish that the VPIN metric of Easley, López de Prado, and O'Hara (ELO), by construction, will be correlated with trading volume and return volatility (innovations). Whether VPIN is more strongly correlated with volume or volatility depends on the exact implementation. Hence, it is crucial for the interpretation of VPIN as a harbinger of market turbulence or as a predictor of short-term volatility to control for current volume and volatility. Doing so, we find no evidence of incremental predictive power of VPIN for future volatility. Likewise, VPIN does not attain unusual extremes prior to the flash crash. Moreover, the properties of VPIN are strongly dependent on the underlying trade classification. In particular, using more standard classification techniques, VPIN behaves in the exact opposite manner of what is portrayed in [ELO, 2011a](#bib11), [ELO, 2012a](#bib13). At a minimum, ELO should rationalize this systematic reversal as the classification becomes more closely aligned with individual transactions.

  [ELO (2014)](#bib15) dispute our findings. This note reviews the econometric methodology and the market microstructure arguments behind our conclusions and responds to a number of inaccurate assertions. In addition, we summarize fresh empirical evidence that corroborates the hypothesis that VPIN is largely driven, and significantly distorted, by the volume and volatility innovations. Furthermore, we note there is compelling new evidence that transaction-based classification schemes are more accurate than the bulk volume strategies advocated by ELO for constructing VPIN. In fact, using perfect classification leads to diametrically opposite results relative to [ELO, 2011a](#bib11), [ELO, 2012a](#bib13).
* ### [VPIN and the Flash Crash: A rejoinder](/science/article/pii/S1386418113000293)

  2014, Journal of Financial Markets

  Andersen and Bondarenko's paper “VPIN and the Flash Crash” is essentially a comment on our 2011 Journal of Portfolio Management paper using our measure of order toxicity, VPIN. Andersen and Bondarenko dispute our empirical findings and argue that VPIN essentially does not work. This is incorrect, and is refuted by results in AB and by independent research. Far from “replicating” our results, AB attack a methodology we do not advocate, an analysis we never performed, and conclusions we did not draw. Our note here makes clear why microstructure features play an important role in understanding price dynamics.
* ### [Real Earnings Management and Information Asymmetry in the Equity Market](https://doi.org/10.1080/09638180.2016.1261720)

  2018, European Accounting Review
* ### [Does IFRS Mandatory Adoption Affect Information Asymmetry in the Stock Market?](https://doi.org/10.1111/auar.12165)

  2018, Australian Accounting Review
* ### [Assessing measures of order flow toxicity and early warning signals for market turbulence](https://doi.org/10.1093/rof/rfu041)

  2015, Review of Finance
* ### [A big data approach to analyzing market volatility](https://doi.org/10.3233/AF-13030)

  2013, Algorithmic Finance

[View all citing articles on Scopus](http://www.scopus.com/scopus/inward/citedby.url?partnerID=10&rel=3.0.0&eid=2-s2.0-84872388245&md5=38702340833e4ef48727a569ed95d)

[☆](#baep-article-footnote-id4)
:   This paper is inspired by the comments that David Abad made about a preliminary version of [Easley et al. (2012a)](#bib0115) presented at the Workshop “*High Frequency Trading: Financial and Regulatory Implications*” held in Madrid, October 2011. David Abad appreciates helpful comments from Maureen O’Hara and Marcos López de Padro. David Abad acknowledges financial support from the *Ministerio de Ciencia e Innovación* through grants [ECO2010-18567](#gs0005) and [ECO2011-29751](#gs0005). José Yagüe acknowledges financial support from *Fundación Caja Murcia*. The authors also thank Roberto Pascual for his constructive comments, as well as Zheng Junyan for the help in programming of PIN estimation.

[View full text](/science/article/pii/S2173126812000344)

Copyright © 2012 Asociación Española de Finanzas. Published by Elsevier España, S.L. All rights reserved.
