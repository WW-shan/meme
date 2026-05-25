[![back arrow](/images/arrow_left.svg)Go to **TMLR** homepage](/group?id=TMLR "Venue Homepage")

## Conservative Evaluation of Offline Policy Learning

[![Download PDF](/images/pdf_icon_blue.svg)](/pdf?id=kLo4TKh0OP "Download PDF")

### [Hager Radi Abdelwahed](/profile?id=~Hager_Radi_Abdelwahed1 "~Hager_Radi_Abdelwahed1"), [Josiah P. Hanna](/profile?id=~Josiah_P._Hanna1 "~Josiah_P._Hanna1"), [Matthew E. Taylor](/profile?id=~Matthew_E._Taylor2 "~Matthew_E._Taylor2")

Published: 23 Sept 2024, Last Modified: 23 Sept 2024Accepted by TMLREveryone[Revisions](/revisions?id=kLo4TKh0OP)[BibTeX](#)[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/ "Licensed under Creative Commons Attribution 4.0 International")

**Abstract:** The world offers unprecedented amounts of data in real-world domains, from which we can develop successful decision-making systems. It is possible for reinforcement learning (RL) to learn control policies offline from such data but challenging to deploy an agent during learning in safety-critical domains. Offline RL learns from historical data without access to an environment. Therefore, we need a methodology for estimating how a newly-learned agent will perform when deployed in the real environment \emph{before} actually deploying it. To achieve this, we propose a framework for conservative evaluation of offline policy learning (CEOPL). We focus on being conservative so that the probability that our agent performs below a baseline is approximately $\delta$, where $\delta$ specifies how much risk we are willing to accept. In our setting, we assume access to a data stream, split into a train-set to learn an offline policy, and a test-set to estimate a lower-bound on the offline policy using off-policy evaluation with bootstrap confidence intervals. A lower-bound estimate allows us to decide when to deploy our learned policy with minimal risk of overestimation. We demonstrate CEOPL on a range of tasks as well as real-world medical data.

**Submission Length:** Regular submission (no more than 12 pages of main content)

**Assigned Action Editor:** ~Nino\_Vieillard1

**Submission Number:** 2532

Loading

[OpenReview](/about) is a long-term project to advance science through improved peer review with legal nonprofit status. We gratefully acknowledge the support of the [OpenReview Sponsors](/sponsors). © 2026 OpenReview
