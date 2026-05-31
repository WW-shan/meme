# RecSys2021 Tutorial

Counterfactual Learning and Evaluation for Recommender Systems: Foundations, Implementations, and Recent Advances

## **Abstract**

Counterfactual estimators enable the use of existing log data to estimate how some new target recommendation policy would have performed, if it had been used instead of the policy that logged the data. We say that those estimators work "off-policy", since the policy that logged the data is different from the target policy. In this way, counterfactual estimators enable ***Off-policy Evaluation (OPE)*** akin to an unbiased offline A/B test, as well as learning new recommendation policies through ***Off-policy Learning (OPL)***. The goal of this tutorial is to summarize ***Foundations, Implementations, and Recent Advances*** of OPE/OPL. Specifically, we will introduce the fundamentals of OPE/OPL and provide theoretical and empirical comparisons of conventional methods. Then, we will cover emerging practical challenges such as how to take into account combinatorial actions, distributional shift, fairness of exposure, and two-sided market structures. We will then present [***Open Bandit Pipeline***](https://www.google.com/url?q=https%3A%2F%2Fgithub.com%2Fst-tech%2Fzr-obp&sa=D&sntz=1&usg=AOvVaw3NQIIbS4nEmmYs2hrM4PPI), an open-source package for OPE/OPL, and how it can be used for both research and practical purposes. We will conclude the tutorial by presenting real-world case studies and future directions.

**The tutorial proposal can be found** [**here**](https://www.google.com/url?q=https%3A%2F%2Fdl.acm.org%2Fdoi%2F10.1145%2F3460231.3473320&sa=D&sntz=1&usg=AOvVaw2BN6fNpUxN3Uv5GPVByXal)

**The list of tutorials at the RecSys2021 conference can be found** [**here**](https://www.google.com/url?q=https%3A%2F%2Frecsys.acm.org%2Frecsys21%2Ftutorials%2F&sa=D&sntz=1&usg=AOvVaw2sCqA6Y_CdNg8ohIjHJH0N)

**A broad list of related papers and resources can be found** [**here**](https://www.google.com/url?q=https%3A%2F%2Fgithub.com%2Fhanjuku-kaso%2Fawesome-offline-rl&sa=D&sntz=1&usg=AOvVaw0UNDcAA7DGxEFqxoQb7Snv)

**Slides are now available [**[**Session 1**](https://drive.google.com/file/d/1ZXWT8Y0ebjsTzzChzWuKVEUkUWVSkIrG/view?usp=sharing)**] [**[**Session 2-1**](https://drive.google.com/file/d/1X90nXSd0sBt7NOKsbcBohZkYfcBVShE2/view?usp=sharing)**] [**[**Session 2-2**](https://drive.google.com/file/d/1aLO7wWktQhNCDEnmLCfq27WunrQIv5EA/view?usp=sharing)**]**

**Example and Simulation Codes are now available on** [**Colab**](https://drive.google.com/drive/folders/1P3IPoFhVQ0n19EU5PCF_ZfkxRdpTJnJa?usp=sharing) **and** [**GitHub**](https://www.google.com/url?q=https%3A%2F%2Fgithub.com%2Fusaito%2Frecsys2021-tutorial&sa=D&sntz=1&usg=AOvVaw0cvm9NehUb6hzlklJMouAc)

## Tutorial Outline

###

### **Session 1** (9:30-11:10)

**Off-Policy Evaluation** (Thorstem Joachims; 30min)

Setup and Foundations

**Bias-Variance Control** (Yuta Saito; 35min)

Advanced Off-Policy Estimators

**Recent Advances** (Yuta Saito; 35min)

Off-Policy Evaluation for Practical Settings

### **Coffee Break** (11:10-11:40)

### **Session 2** (11:40-13:00)

**Off-Policy Learning** (Thorsten Joachims; 40min)

Learning Approaches and Methods

**Implementations** (Yuta Saito; 30min)

Open Bandit Pipeline

**Summary and QA** (Both presenters; 10min)

## **Presenters**

### [**Yuta Saito**](https://www.google.com/url?q=https%3A%2F%2Fusaito.github.io%2F&sa=D&sntz=1&usg=AOvVaw145qenL7E5vvtDRPQIEqGN)([ys552@cornell.edu](mailto:ys552@cornell.edu))

He is a Ph.D. student in the Department of Computer Science at Cornell University, advised by Prof. Thorsten Joachims. He received a B.Eng degree in Industrial Engineering and Economics from Tokyo Institute of Technology in 2021. His current research focuses on OPE of bandit algorithms and learning from human behavior data. He has been collaborating with several tech companies to implement OPE/OPL in practical situations and to conduct large-scale empirical studies. Some of his recent work has been published at top conferences, including ICML, SIGIR, SDM, ICTIR, RecSys, and WSDM.

### [**Thorsten Joachims**](https://www.google.com/url?q=https%3A%2F%2Fwww.cs.cornell.edu%2Fpeople%2Ftj%2F&sa=D&sntz=1&usg=AOvVaw3hI3Ibj2F5k1w3wCeXvHur)([tj@cs.cornell.edu](mailto:tj@cs.cornell.edu))

He is a Professor in the Department of Computer Science and in the Department of Information Science at Cornell University, and he is an Amazon Scholar. His research interests center on the synthesis of theory and system building in machine learning, with applications in information retrieval and recommendation. His past research focused on support vector machines, learning to rank, learning with preferences, and learning from implicit feedback, text classification, and structured output prediction. Working with his students and collaborators, his papers won 9 Best Paper Awards and 4 Test-of-Time Awards. He is also an ACM Fellow, AAAI Fellow, KDD Innovations Award recipient, and member of the SIGIR Academy.

## **Acknowledgements**

This research was supported in part by NSF Awards IIS-1901168 and IIS-2008139. Yuta Saito is supported by Funai Overseas Scholarship. All content represents the opinion of the authors, which is not necessarily shared or endorsed by their respective employers and/or sponsors.
