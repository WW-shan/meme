# A Comprehensive Survey on Rare Event Prediction

###### Abstract

Rare event prediction involves identifying and forecasting events with a low probability using machine learning (ML) and data analysis. Due to the imbalanced data distributions, where the frequency of common events vastly outweighs that of rare events, it requires using specialized methods within each step of the ML pipeline, i.e., from data processing to algorithms to evaluation protocols. Predicting the occurrences of rare events is important for real-world applications, such as Industry 4.0, and is an active research area in statistical and ML. This paper comprehensively reviews the current approaches for rare event prediction along four dimensions: rare event data, data processing, algorithmic approaches, and evaluation approaches. Specifically, we consider 73 datasets from different modalities (i.e., numerical, image, text, and audio), four major categories of data processing, five major algorithmic groupings, and two broader evaluation approaches. This paper aims to identify gaps in the current literature and highlight the challenges of predicting rare events. It also suggests potential research directions, which can help guide practitioners and researchers.

*K*eywords event-prediction  ⋅⋅\cdot⋅
rare-events  ⋅⋅\cdot⋅
time-series  ⋅⋅\cdot⋅
anomaly detection  ⋅⋅\cdot⋅
forecasting

## 1 Introduction

Events are incidents that are associated with specific locations (spatial), time periods (temporal), and contexts (semantics). Rare events are a subset of events that stand out due to their infrequency. The degree of infrequency of rare events is typically influenced by the specific field of application [[1](https://arxiv.org/html/2309.11356v2#bib.bib1), [2](https://arxiv.org/html/2309.11356v2#bib.bib2)]. Rare event learning is considered an NP-hard problem [[3](https://arxiv.org/html/2309.11356v2#bib.bib3)], as it requires analyzing a large amount of data to identify rare events, which can be computationally intensive and time-consuming, especially in high-dimensional spaces. The size and complexity of rare event data lead to the challenge of handling this problem, resulting in complicated issues in data mining and ML. Imbalanced event datasets exhibit a prevalence of rare occurrences, wherein the quantity of instances associated with one class is significantly lower than the quantity of instances pertaining to the other. These datasets present challenges for learning algorithms since they may result in biased outcomes in downstream tasks such as classification, clustering, forecasting, and simulation. Algorithms necessitate tailoring to effectively address rare events, as these occurrences often give rise to challenges stemming from their uncommon nature.

Considering the significance of rare events across various domains, extensive research has been conducted in diverse knowledge areas, leading to a conflation of terms and issues within the literature. While terms like rare events, anomalies, novelties, and outliers may appear similar, it is crucial to note their distinct differences. Rare events and anomalies share characteristics such as an imbalanced class distribution and representation of all classes in the training set [[4](https://arxiv.org/html/2309.11356v2#bib.bib4)]. However, rare events primarily relate to temporal data, contrasting with anomalies that typically involve static data distributions. Novelties, on the other hand, involve the identification of new or unknown data patterns. Static novelties are characterized by supervised classification with a single class for training, whereas dynamic novelties entail supervised classification with an indeterminate number of labels [[4](https://arxiv.org/html/2309.11356v2#bib.bib4), [5](https://arxiv.org/html/2309.11356v2#bib.bib5), [6](https://arxiv.org/html/2309.11356v2#bib.bib6)]. Outliers, distinguished from the aforementioned categories, are observations significantly deviating from the majority in the dataset [[4](https://arxiv.org/html/2309.11356v2#bib.bib4), [7](https://arxiv.org/html/2309.11356v2#bib.bib7)]. They often manifest in temporal data and are addressed through unsupervised classification methodologies. The primary focus of our investigation in this paper is exclusively directed towards rare events. Hence, we specifically selected studies that include the term ‘rare events’ in the paper title and abstract.

In real-life, rare events can be observed ubiquitously in various domains, including medical diagnosis, fraud detection, and natural disaster prediction. In any field or area of study, rare events can be regarded as occurrences that possess valuable and meaningful information [[8](https://arxiv.org/html/2309.11356v2#bib.bib8)]. Rare events can be weighted by ‘rarity’, a measure of being rare, uncommon, or scarce. Liu and Feng [[9](https://arxiv.org/html/2309.11356v2#bib.bib9)] formulate this as the "Curse of Rarity" (CoR). The fundamental idea behind CoR is that the events of interest are exceptionally rare, resulting in limited information in the available data. CoR leads to many underlying issues, including decision-making, modeling, verification, and validation. For instance, detecting rare diseases or medical conditions is challenging but crucial for effective diagnosis and treatment.
Similarly, detecting fraud in financial transactions can help prevent financial losses and ensure the security of transactions. In the case of natural disaster prediction, identifying rare events such as earthquakes or tsunamis can help in effective disaster management and response. In manufacturing, these events lead to unplanned downtime or shutdowns, which are particularly detrimental for industries regarding equipment life and power consumption. Thus, exploring rare events in advance allows industries to implement mitigation procedures to reduce defects so that equipment downtime can be lowered, optimizing energy consumption and ensuring optimization, quality, and safety standards in processes.

The significance of rare events resides in their capacity to yield a disproportionate influence, surpassing that of more typical events. For instance, a disease that affects a minor percentage of the population can enormously affect public health. Similarly, large-scale fraudulent activities can result in substantial financial losses for individuals and organizations. Hence, it is evident that rare occurrences require specialized attention and analysis. Therefore, developing effective methodologies and algorithms that can handle the uniqueness and mitigate the biases and limitations inherent in rare events is essential. The problem of imbalanced datasets and rare events is not new, and researchers have developed several techniques to address this issue. These techniques range from data-level approaches, such as oversampling and undersampling [[10](https://arxiv.org/html/2309.11356v2#bib.bib10), [11](https://arxiv.org/html/2309.11356v2#bib.bib11), [12](https://arxiv.org/html/2309.11356v2#bib.bib12), [13](https://arxiv.org/html/2309.11356v2#bib.bib13), [14](https://arxiv.org/html/2309.11356v2#bib.bib14), [15](https://arxiv.org/html/2309.11356v2#bib.bib15)], to algorithm-level approaches, such as cost-sensitive learning [[11](https://arxiv.org/html/2309.11356v2#bib.bib11), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [17](https://arxiv.org/html/2309.11356v2#bib.bib17), [18](https://arxiv.org/html/2309.11356v2#bib.bib18)] and ensemble methods [[19](https://arxiv.org/html/2309.11356v2#bib.bib19)]. In recent years, deep learning methods [[20](https://arxiv.org/html/2309.11356v2#bib.bib20), [21](https://arxiv.org/html/2309.11356v2#bib.bib21), [22](https://arxiv.org/html/2309.11356v2#bib.bib22), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [24](https://arxiv.org/html/2309.11356v2#bib.bib24), [25](https://arxiv.org/html/2309.11356v2#bib.bib25), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [27](https://arxiv.org/html/2309.11356v2#bib.bib27)] have also been applied to address the problem of rare events.

This survey paper aims to provide a comparative review of the existing literature on rare event prediction. We have developed a taxonomy that summarizes the research on rare event prediction into four categories: rare event data, data processing, algorithmic approaches, and evaluation approaches. The rare event data section identifies datasets containing rare events, while the data processing section emphasizes the vital role of data processing in handling rare event datasets, refining data quality to enhance predictive model performance. The algorithmic approaches present mathematical models applicable to diverse scenarios encompassing various use cases, and the evaluation section delves into the multifaceted evaluation criteria utilized in rare event prediction studies. Then, we explore the existing literature pertaining to these four categories. The extended review involves the reviewing of each of these four categories with levels of rarity that we introduce, established industries, types of datasets, data modalities, applications, and downstream tasks. Finally, we highlight some open research questions and future directions identified in this area.

### 1.1 The Contributions of this paper

The main contributions of this paper include:

Comparatively review the existing literature on rare event prediction in four approaches; rare event data, data processing, algorithmic and evaluation approaches.

Analyze the literature by examining multiple avenues: dataset types, modalities, and downstream tasks.

Identify gaps, challenges, and special concerns in the current research landscape while discussing potential emerging trends in the realm.

### 1.2 Organization

This study distinguishes a four-fold summarized categorization of approaches to learning from imbalanced event data for rare event prediction that have been implemented within related work. As shown in Figure [1](https://arxiv.org/html/2309.11356v2#S1.F1 "Figure 1 ‣ 1.2 Organization ‣ 1 Introduction ‣ A Comprehensive Survey on Rare Event Prediction"), the main groupings include I) Rare event data, II) Data processing approaches, III) Algorithm level techniques, and IV) Evaluation approaches.

![Refer to caption](x1.png)

## 2 Rare event data

This section analyzes datasets with rare events. Considering a wide range of datasets from multiple industries and different modalities we first categorize them by the rarity percentage. We then explore real-world applications of the data and examine data acquisition methods. Next, we present an analysis considering types of datasets, metadata, and modality. Finally, we discuss the characteristics and challenges of handling such data and the factors contributing to their rarity.

### 2.1 Datasets with rare events – Analysis of existing datasets with rare events

#### 2.1.1 Levels of rarity

In any domain, the rarity of events is inversely correlated with the maturity of that industry. At the same time, rarity is correlated with event frequency or the probability of occurrence. For better understanding and analysis, we introduce the notion of “levels of rarity", which categorizes rarity into four levels as depicted in Figure [2](https://arxiv.org/html/2309.11356v2#S2.F2 "Figure 2 ‣ 2.1.1 Levels of rarity ‣ 2.1 Datasets with rare events – Analysis of existing datasets with rare events ‣ 2 Rare event data ‣ A Comprehensive Survey on Rare Event Prediction"). These rarity levels will be used throughout all the review sections in this paper. We have established the boundaries for the levels based on several factors, such as the distribution of data, significant differences in rarity levels, and context. The R1 category comprises datasets with events that have a frequency of 0-1%, which are considered extremely rare. On the other hand, events with a rarity of 1-5% are classified as very rare and fall under the R2 category. The R3 category includes events with a rarity of 5-10%, which are considered moderately rare. Finally, the rest of the events with a frequency greater than 10% belong to the frequently-rare (R4) category. It is apparent that when moving up in levels, the percentage of rarity and the event frequency tend to decrease, necessitating more sophisticated approaches for identifying and analyzing. The datasets in the studies we reviewed utilized diverse data types, including numeric (N), textual (TX), image (I), and audio (A). A special property of these ‘rare event’ datasets is their adherence to the temporal nature (T) of ‘events‘ and/or adaptation of time-dependent features.
We have encountered a limited number of datasets (2) that deviate from the typical time series data used in rare event studies, which we have excluded from our analysis. Consequently, we delineate the scope of rare events as occurrences within a time series, where an entire or part of a time series may constitute a rare event evolving over an extended duration.

![Refer to caption](x2.png)

#### 2.1.2 Industries and real-world applications

The different industries that have been identified in this review include eight main sectors: economy, healthcare, transportation, telecommunications, manufacturing, energy, earth science, and others. It should be noted that the primary industries include several application domains that we merged into a general main industry, as shown in Table [1](https://arxiv.org/html/2309.11356v2#S2.T1 "Table 1 ‣ 2.1.2 Industries and real-world applications ‣ 2.1 Datasets with rare events – Analysis of existing datasets with rare events ‣ 2 Rare event data ‣ A Comprehensive Survey on Rare Event Prediction"). In Table [1](https://arxiv.org/html/2309.11356v2#S2.T1 "Table 1 ‣ 2.1.2 Industries and real-world applications ‣ 2.1 Datasets with rare events – Analysis of existing datasets with rare events ‣ 2 Rare event data ‣ A Comprehensive Survey on Rare Event Prediction"), we have compiled a list of real-world applications of rare events categorized by industry, application domain, and rarity based on the literature. Notably, these applications have predominantly concentrated on use cases such as detection, diagnosis, prediction, and downstream tasks like classification (CF), clustering (CL), forecasting (FT), regression (RG), and simulation (SM).

|  |  |  |
| --- | --- | --- |
| Industry | Applications Domains | Examples from literature |
| Earth Sciences | |  | | --- | | Environment management, Disaster management, | | Geology | | |  | | --- | | Detection of changes in buildings from aerial images taken before and after | | a tsunami disaster ([[28](https://arxiv.org/html/2309.11356v2#bib.bib28), [29](https://arxiv.org/html/2309.11356v2#bib.bib29)] – R1) | | O3subscript𝑂3O\_{3}italic\_O start\_POSTSUBSCRIPT 3 end\_POSTSUBSCRIPT state prediction, Prediction of hazardous seismic bumps in coal mines ([[16](https://arxiv.org/html/2309.11356v2#bib.bib16)] – R3) | | Detection of oil spills in satellite-borne radar images ([[17](https://arxiv.org/html/2309.11356v2#bib.bib17), [30](https://arxiv.org/html/2309.11356v2#bib.bib30)] – R2) | | Prediction of landslides, undesirable events in offshore oil wells ([[31](https://arxiv.org/html/2309.11356v2#bib.bib31)] – R4) | |
| Manufacturing | Machinery fault diagnosis, Anomaly detection | |  | | --- | | Prediction of paper breaks in the paper manufacturing industry ([[12](https://arxiv.org/html/2309.11356v2#bib.bib12), [32](https://arxiv.org/html/2309.11356v2#bib.bib32)] – R1) | | Prediction of which parts will fail at the end of the production line ([[33](https://arxiv.org/html/2309.11356v2#bib.bib33)] – R1) | |
| Telecommunication | |  | | --- | | Network monitoring, Telecommunication | | failure diagnosis | | |  | | --- | | Prediction of telecommunications equipment failures ([[3](https://arxiv.org/html/2309.11356v2#bib.bib3), [34](https://arxiv.org/html/2309.11356v2#bib.bib34)] – R1) | | Prediction and classification of rare events in power grids ([[35](https://arxiv.org/html/2309.11356v2#bib.bib35), [36](https://arxiv.org/html/2309.11356v2#bib.bib36)] – R1, R2, R3, R4) | |
| Transportation | |  | | --- | | Traffic monitoring, Autonomous driving, | | Aircraft health management | | |  | | --- | | Degradation detection and trending, | | and failure discrimination based on the classification of aircraft systems ([[20](https://arxiv.org/html/2309.11356v2#bib.bib20)] – R1) | | Prediction of wrong-way driving in highways ([[21](https://arxiv.org/html/2309.11356v2#bib.bib21)] –R1) | |
| Economy | Market trend forecasting, Fraud detection | |  | | --- | | Prediction of black-swan events in the Indian stock market ([[23](https://arxiv.org/html/2309.11356v2#bib.bib23)] –R1) | | Predicting credit card frauds ([[18](https://arxiv.org/html/2309.11356v2#bib.bib18)] – R1) | |
| Healthcare | |  | | --- | | Disease diagnosis, Emergent incidents identification, | | Detecting microcalcifications | | |  | | --- | | Post-Traumatic Seizure Detection ([[37](https://arxiv.org/html/2309.11356v2#bib.bib37)] – R1) | | Detection of LASA cases and rare events’ classification in imbalanced | | healthcare data ([[11](https://arxiv.org/html/2309.11356v2#bib.bib11)] –R4) | | Detection of microcalcifications in mammography ([[38](https://arxiv.org/html/2309.11356v2#bib.bib38)] – R2) | |
| Energy | Energy forecasting | Prediction of when to expect a high KWh cost ([[39](https://arxiv.org/html/2309.11356v2#bib.bib39)] –R3) |
| Others | |  | | --- | | Scene understanding, Computer vision, Remote sensing, | | Classification, Criminological investigation | | |  | | --- | | Detection of scene changes from street view panorama images ([[29](https://arxiv.org/html/2309.11356v2#bib.bib29)] – R1) | | Detection of recidivists from criminological events ([[40](https://arxiv.org/html/2309.11356v2#bib.bib40)] – R4) | | Classification of types of glass in criminological events ([[41](https://arxiv.org/html/2309.11356v2#bib.bib41), [42](https://arxiv.org/html/2309.11356v2#bib.bib42)] – R4) | | Detection of a change of digit from a pair of samples in MNIST ([[29](https://arxiv.org/html/2309.11356v2#bib.bib29)] – R1, R4) | |

|  |
| --- |
| Environment management, Disaster management, |
| Geology |

|  |
| --- |
| Detection of changes in buildings from aerial images taken before and after |
| a tsunami disaster ([[28](https://arxiv.org/html/2309.11356v2#bib.bib28), [29](https://arxiv.org/html/2309.11356v2#bib.bib29)] – R1) |
| O3subscript𝑂3O\_{3}italic\_O start\_POSTSUBSCRIPT 3 end\_POSTSUBSCRIPT state prediction, Prediction of hazardous seismic bumps in coal mines ([[16](https://arxiv.org/html/2309.11356v2#bib.bib16)] – R3) |
| Detection of oil spills in satellite-borne radar images ([[17](https://arxiv.org/html/2309.11356v2#bib.bib17), [30](https://arxiv.org/html/2309.11356v2#bib.bib30)] – R2) |
| Prediction of landslides, undesirable events in offshore oil wells ([[31](https://arxiv.org/html/2309.11356v2#bib.bib31)] – R4) |

|  |
| --- |
| Prediction of paper breaks in the paper manufacturing industry ([[12](https://arxiv.org/html/2309.11356v2#bib.bib12), [32](https://arxiv.org/html/2309.11356v2#bib.bib32)] – R1) |
| Prediction of which parts will fail at the end of the production line ([[33](https://arxiv.org/html/2309.11356v2#bib.bib33)] – R1) |

|  |
| --- |
| Network monitoring, Telecommunication |
| failure diagnosis |

|  |
| --- |
| Prediction of telecommunications equipment failures ([[3](https://arxiv.org/html/2309.11356v2#bib.bib3), [34](https://arxiv.org/html/2309.11356v2#bib.bib34)] – R1) |
| Prediction and classification of rare events in power grids ([[35](https://arxiv.org/html/2309.11356v2#bib.bib35), [36](https://arxiv.org/html/2309.11356v2#bib.bib36)] – R1, R2, R3, R4) |

|  |
| --- |
| Traffic monitoring, Autonomous driving, |
| Aircraft health management |

|  |
| --- |
| Degradation detection and trending, |
| and failure discrimination based on the classification of aircraft systems ([[20](https://arxiv.org/html/2309.11356v2#bib.bib20)] – R1) |
| Prediction of wrong-way driving in highways ([[21](https://arxiv.org/html/2309.11356v2#bib.bib21)] –R1) |

|  |
| --- |
| Prediction of black-swan events in the Indian stock market ([[23](https://arxiv.org/html/2309.11356v2#bib.bib23)] –R1) |
| Predicting credit card frauds ([[18](https://arxiv.org/html/2309.11356v2#bib.bib18)] – R1) |

|  |
| --- |
| Disease diagnosis, Emergent incidents identification, |
| Detecting microcalcifications |

|  |
| --- |
| Post-Traumatic Seizure Detection ([[37](https://arxiv.org/html/2309.11356v2#bib.bib37)] – R1) |
| Detection of LASA cases and rare events’ classification in imbalanced |
| healthcare data ([[11](https://arxiv.org/html/2309.11356v2#bib.bib11)] –R4) |
| Detection of microcalcifications in mammography ([[38](https://arxiv.org/html/2309.11356v2#bib.bib38)] – R2) |

|  |
| --- |
| Scene understanding, Computer vision, Remote sensing, |
| Classification, Criminological investigation |

|  |
| --- |
| Detection of scene changes from street view panorama images ([[29](https://arxiv.org/html/2309.11356v2#bib.bib29)] – R1) |
| Detection of recidivists from criminological events ([[40](https://arxiv.org/html/2309.11356v2#bib.bib40)] – R4) |
| Classification of types of glass in criminological events ([[41](https://arxiv.org/html/2309.11356v2#bib.bib41), [42](https://arxiv.org/html/2309.11356v2#bib.bib42)] – R4) |
| Detection of a change of digit from a pair of samples in MNIST ([[29](https://arxiv.org/html/2309.11356v2#bib.bib29)] – R1, R4) |

#### 2.1.3 Types of rare events datasets

The study identified three types of rare event datasets: naturally rare event datasets, derived datasets, and simulated/synthetic datasets.

i) Naturally rare event datasets (RE):
These refer to datasets that inherently exhibit a low occurrence rate of specific events or phenomena. Table [2](https://arxiv.org/html/2309.11356v2#S2.T2 "Table 2 ‣ 2.1.3 Types of rare events datasets ‣ 2.1 Datasets with rare events – Analysis of existing datasets with rare events ‣ 2 Rare event data ‣ A Comprehensive Survey on Rare Event Prediction") summarizes naturally rare event datasets used in rare event literature. It was noticed that approximately 41% of the naturally rare datasets used fall into the extremely-rare category. Naturally rare event datasets can be sourced from various industries and domains, such as manufacturing, healthcare, earth sciences, and economy. For instance, data on environmental disasters such as oil spills [[17](https://arxiv.org/html/2309.11356v2#bib.bib17)] and tsunamis [[28](https://arxiv.org/html/2309.11356v2#bib.bib28)] can be gathered using satellite, ariel, or drone imagery via remote sensing technologies, while machine faults and anomalies can be tracked through data collection from sensors attached to different parts of the machines in manufacturing plants [[12](https://arxiv.org/html/2309.11356v2#bib.bib12), [43](https://arxiv.org/html/2309.11356v2#bib.bib43)]. Similarly, sources for predicting rare economic events may include financial market data, economic indicators, government reports, transaction data, consumer behavior data, social media data, and other relevant sources specific to the economic domain [[23](https://arxiv.org/html/2309.11356v2#bib.bib23)]. Data collected from such sources can be obtained from public databases. Repositories like University of California Irvine (UCI) [[44](https://arxiv.org/html/2309.11356v2#bib.bib44)], Knowledge Extraction based on Evolutionary Learning (KEEL) [[45](https://arxiv.org/html/2309.11356v2#bib.bib45)], Outlier Detection DataSets (ODDS) [[46](https://arxiv.org/html/2309.11356v2#bib.bib46)], Kaggle [[47](https://arxiv.org/html/2309.11356v2#bib.bib47)], research-specific data storages [[31](https://arxiv.org/html/2309.11356v2#bib.bib31), [43](https://arxiv.org/html/2309.11356v2#bib.bib43), [35](https://arxiv.org/html/2309.11356v2#bib.bib35), [48](https://arxiv.org/html/2309.11356v2#bib.bib48), [49](https://arxiv.org/html/2309.11356v2#bib.bib49), [50](https://arxiv.org/html/2309.11356v2#bib.bib50)], industry-specific databases [[34](https://arxiv.org/html/2309.11356v2#bib.bib34), [51](https://arxiv.org/html/2309.11356v2#bib.bib51), [52](https://arxiv.org/html/2309.11356v2#bib.bib52), [53](https://arxiv.org/html/2309.11356v2#bib.bib53), [54](https://arxiv.org/html/2309.11356v2#bib.bib54), [55](https://arxiv.org/html/2309.11356v2#bib.bib55), [56](https://arxiv.org/html/2309.11356v2#bib.bib56), [57](https://arxiv.org/html/2309.11356v2#bib.bib57), [58](https://arxiv.org/html/2309.11356v2#bib.bib58)], Application Programming Interfaces (APIs) [[59](https://arxiv.org/html/2309.11356v2#bib.bib59), [60](https://arxiv.org/html/2309.11356v2#bib.bib60), [61](https://arxiv.org/html/2309.11356v2#bib.bib61)], social media platforms [[62](https://arxiv.org/html/2309.11356v2#bib.bib62), [63](https://arxiv.org/html/2309.11356v2#bib.bib63)], and news outlets [[62](https://arxiv.org/html/2309.11356v2#bib.bib62), [63](https://arxiv.org/html/2309.11356v2#bib.bib63)] would be such databases. Data extraction from them can involve manually accessing public datasets, querying databases, web scraping, or using web services.

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| Sector | |  | | --- | | Event % & | | rarity group | | Datasets with modality | Papers |
| Earth Sciences | 0-1(R1) | |  | | --- | | meteorological (heatwaves) dataset(N,T), | | 3W dataset(N,T) [[31](https://arxiv.org/html/2309.11356v2#bib.bib31)] | | [[39](https://arxiv.org/html/2309.11356v2#bib.bib39), [64](https://arxiv.org/html/2309.11356v2#bib.bib64)] |
|  | 1-5(R2) | |  | | --- | | Oil dataset(I, T) [[17](https://arxiv.org/html/2309.11356v2#bib.bib17)], | | 3W dataset(N,T) [[31](https://arxiv.org/html/2309.11356v2#bib.bib31)], | | Tornado dataset(N,T) [[65](https://arxiv.org/html/2309.11356v2#bib.bib65)] | | |  | | --- | | [[38](https://arxiv.org/html/2309.11356v2#bib.bib38), [42](https://arxiv.org/html/2309.11356v2#bib.bib42), [17](https://arxiv.org/html/2309.11356v2#bib.bib17)], | | [[64](https://arxiv.org/html/2309.11356v2#bib.bib64), [66](https://arxiv.org/html/2309.11356v2#bib.bib66), [67](https://arxiv.org/html/2309.11356v2#bib.bib67)] | |
|  | 5-10(R3) | |  | | --- | | seismic-bumps Data Set | | (N, T) [[68](https://arxiv.org/html/2309.11356v2#bib.bib68)], 3W dataset(N, T) [[31](https://arxiv.org/html/2309.11356v2#bib.bib31)] | | [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [64](https://arxiv.org/html/2309.11356v2#bib.bib64)] |
|  | 10+(R4) | |  | | --- | | LIDAR data(I, T)[[69](https://arxiv.org/html/2309.11356v2#bib.bib69)], 3W dataset(N,T) [[31](https://arxiv.org/html/2309.11356v2#bib.bib31)] | | [[70](https://arxiv.org/html/2309.11356v2#bib.bib70), [64](https://arxiv.org/html/2309.11356v2#bib.bib64)] |
| Manufacturing | 0-1(R1) | |  | | --- | | pulp -and-paper dataset(N,T) [[12](https://arxiv.org/html/2309.11356v2#bib.bib12)], | | Bosch Production Line | | Performance dataset(N,T) [[71](https://arxiv.org/html/2309.11356v2#bib.bib71)] | | |  | | --- | | [[32](https://arxiv.org/html/2309.11356v2#bib.bib32), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [12](https://arxiv.org/html/2309.11356v2#bib.bib12), [37](https://arxiv.org/html/2309.11356v2#bib.bib37)], | | [[72](https://arxiv.org/html/2309.11356v2#bib.bib72), [73](https://arxiv.org/html/2309.11356v2#bib.bib73), [25](https://arxiv.org/html/2309.11356v2#bib.bib25), [26](https://arxiv.org/html/2309.11356v2#bib.bib26)] | |
|  | 10+(R4) | |  | | --- | | Case Western Reserve University | | Rolling Bearing dataset(N,T) [[43](https://arxiv.org/html/2309.11356v2#bib.bib43)], | | IMS bearing dataset)(N,T) [[74](https://arxiv.org/html/2309.11356v2#bib.bib74)], | | XJTU-SY datasets(N,T) [[75](https://arxiv.org/html/2309.11356v2#bib.bib75)], | | PRONOSTIA bearing dataset(N,T) [[76](https://arxiv.org/html/2309.11356v2#bib.bib76)] | | [[77](https://arxiv.org/html/2309.11356v2#bib.bib77), [78](https://arxiv.org/html/2309.11356v2#bib.bib78), [79](https://arxiv.org/html/2309.11356v2#bib.bib79), [75](https://arxiv.org/html/2309.11356v2#bib.bib75)] |
| Telecommunication | 0-1(R1) | |  | | --- | | probe binary-UCI(N, T), | | r2l binary-uci(N,T ), | | KDD Cup 99 Data (N,T) [[46](https://arxiv.org/html/2309.11356v2#bib.bib46), [80](https://arxiv.org/html/2309.11356v2#bib.bib80), [81](https://arxiv.org/html/2309.11356v2#bib.bib81), [82](https://arxiv.org/html/2309.11356v2#bib.bib82)] | | Alarm data(n,T), | | VoIP traffic data(N, T) [[34](https://arxiv.org/html/2309.11356v2#bib.bib34)] | | [[14](https://arxiv.org/html/2309.11356v2#bib.bib14), [3](https://arxiv.org/html/2309.11356v2#bib.bib3), [83](https://arxiv.org/html/2309.11356v2#bib.bib83), [84](https://arxiv.org/html/2309.11356v2#bib.bib84)] |
| Transportation | 1-5(R2) | |  | | --- | | Air Pressure System(APS) Failure | | at Scania Trucks Data Set(N, T) | | [[85](https://arxiv.org/html/2309.11356v2#bib.bib85), [49](https://arxiv.org/html/2309.11356v2#bib.bib49)] | | [[86](https://arxiv.org/html/2309.11356v2#bib.bib86), [87](https://arxiv.org/html/2309.11356v2#bib.bib87), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)] |
|  | 5-10(R3) | |  | | --- | | MnDot traffic data(N, T) [[34](https://arxiv.org/html/2309.11356v2#bib.bib34)] | | Traffic Prediction Dataset(N, T) | | WWD Data (N, T) [[57](https://arxiv.org/html/2309.11356v2#bib.bib57), [58](https://arxiv.org/html/2309.11356v2#bib.bib58)] | | [[21](https://arxiv.org/html/2309.11356v2#bib.bib21), [83](https://arxiv.org/html/2309.11356v2#bib.bib83), [37](https://arxiv.org/html/2309.11356v2#bib.bib37)] |
| Economy | |  | | --- | | 0-1(R1) | | |  | | --- | | S and P BSE SENSEX(N, T)[[63](https://arxiv.org/html/2309.11356v2#bib.bib63), [89](https://arxiv.org/html/2309.11356v2#bib.bib89)] | | Nifty 50(N, T) [[62](https://arxiv.org/html/2309.11356v2#bib.bib62), [90](https://arxiv.org/html/2309.11356v2#bib.bib90)] | | Kaggle Credit Card Fraud Detection(N, T) | | [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [18](https://arxiv.org/html/2309.11356v2#bib.bib18)] |
| Healthcare | 0-1(R1) | |  | | --- | | Thoracic surgery dataset(N, T) [[91](https://arxiv.org/html/2309.11356v2#bib.bib91)], | | Bioassay AID 746(N, T),687(N, T),456(N, T),373(N, T), | | Suicide data(N,T) [[92](https://arxiv.org/html/2309.11356v2#bib.bib92)] | | [[91](https://arxiv.org/html/2309.11356v2#bib.bib91), [93](https://arxiv.org/html/2309.11356v2#bib.bib93)] |
|  | 1-5(R2) | |  | | --- | | stroke dataset(N, T) [[94](https://arxiv.org/html/2309.11356v2#bib.bib94)], | | Bioassay AID 362(N, T) [[91](https://arxiv.org/html/2309.11356v2#bib.bib91)] | | [[8](https://arxiv.org/html/2309.11356v2#bib.bib8), [91](https://arxiv.org/html/2309.11356v2#bib.bib91)] |
|  | 5-10(R3) | Bioassay AID 1608(N, T) [[91](https://arxiv.org/html/2309.11356v2#bib.bib91)] | [[91](https://arxiv.org/html/2309.11356v2#bib.bib91)] |
|  | 10+(R4) | Wong’s dataset from Canadian(TX ,T) [[95](https://arxiv.org/html/2309.11356v2#bib.bib95)] | [[11](https://arxiv.org/html/2309.11356v2#bib.bib11), [95](https://arxiv.org/html/2309.11356v2#bib.bib95)] |
| Energy | 5-10(R3) | |  | | --- | | Daily electric energy production | | measurements dataset(Spain, 2003)(N,T) | | [[39](https://arxiv.org/html/2309.11356v2#bib.bib39)] |
| Others | 0-1(R1) | PCD dataset(I, T) [[96](https://arxiv.org/html/2309.11356v2#bib.bib96)], | [[29](https://arxiv.org/html/2309.11356v2#bib.bib29)] |
|  | 1-5(R2) | K1b-WebACE(N,T) [[97](https://arxiv.org/html/2309.11356v2#bib.bib97)] | [[14](https://arxiv.org/html/2309.11356v2#bib.bib14)] |
|  | 5-10(R3) | La12-TREC(N,T) | [[14](https://arxiv.org/html/2309.11356v2#bib.bib14)] |
|  | 10+(R4) | |  | | --- | | Recidivism dataset (N, T) , | | Audio-Anomaly-Dataset(A, T) [[98](https://arxiv.org/html/2309.11356v2#bib.bib98)] | | [[40](https://arxiv.org/html/2309.11356v2#bib.bib40), [99](https://arxiv.org/html/2309.11356v2#bib.bib99)] |

|  |
| --- |
| Event % & |
| rarity group |

|  |
| --- |
| meteorological (heatwaves) dataset(N,T), |
| 3W dataset(N,T) [[31](https://arxiv.org/html/2309.11356v2#bib.bib31)] |

|  |
| --- |
| Oil dataset(I, T) [[17](https://arxiv.org/html/2309.11356v2#bib.bib17)], |
| 3W dataset(N,T) [[31](https://arxiv.org/html/2309.11356v2#bib.bib31)], |
| Tornado dataset(N,T) [[65](https://arxiv.org/html/2309.11356v2#bib.bib65)] |

|  |
| --- |
| [[38](https://arxiv.org/html/2309.11356v2#bib.bib38), [42](https://arxiv.org/html/2309.11356v2#bib.bib42), [17](https://arxiv.org/html/2309.11356v2#bib.bib17)], |
| [[64](https://arxiv.org/html/2309.11356v2#bib.bib64), [66](https://arxiv.org/html/2309.11356v2#bib.bib66), [67](https://arxiv.org/html/2309.11356v2#bib.bib67)] |

|  |
| --- |
| seismic-bumps Data Set |
| (N, T) [[68](https://arxiv.org/html/2309.11356v2#bib.bib68)], 3W dataset(N, T) [[31](https://arxiv.org/html/2309.11356v2#bib.bib31)] |

|  |
| --- |
| LIDAR data(I, T)[[69](https://arxiv.org/html/2309.11356v2#bib.bib69)], 3W dataset(N,T) [[31](https://arxiv.org/html/2309.11356v2#bib.bib31)] |

|  |
| --- |
| pulp -and-paper dataset(N,T) [[12](https://arxiv.org/html/2309.11356v2#bib.bib12)], |
| Bosch Production Line |
| Performance dataset(N,T) [[71](https://arxiv.org/html/2309.11356v2#bib.bib71)] |

|  |
| --- |
| [[32](https://arxiv.org/html/2309.11356v2#bib.bib32), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [12](https://arxiv.org/html/2309.11356v2#bib.bib12), [37](https://arxiv.org/html/2309.11356v2#bib.bib37)], |
| [[72](https://arxiv.org/html/2309.11356v2#bib.bib72), [73](https://arxiv.org/html/2309.11356v2#bib.bib73), [25](https://arxiv.org/html/2309.11356v2#bib.bib25), [26](https://arxiv.org/html/2309.11356v2#bib.bib26)] |

|  |
| --- |
| Case Western Reserve University |
| Rolling Bearing dataset(N,T) [[43](https://arxiv.org/html/2309.11356v2#bib.bib43)], |
| IMS bearing dataset)(N,T) [[74](https://arxiv.org/html/2309.11356v2#bib.bib74)], |
| XJTU-SY datasets(N,T) [[75](https://arxiv.org/html/2309.11356v2#bib.bib75)], |
| PRONOSTIA bearing dataset(N,T) [[76](https://arxiv.org/html/2309.11356v2#bib.bib76)] |

|  |
| --- |
| probe binary-UCI(N, T), |
| r2l binary-uci(N,T ), |
| KDD Cup 99 Data (N,T) [[46](https://arxiv.org/html/2309.11356v2#bib.bib46), [80](https://arxiv.org/html/2309.11356v2#bib.bib80), [81](https://arxiv.org/html/2309.11356v2#bib.bib81), [82](https://arxiv.org/html/2309.11356v2#bib.bib82)] |
| Alarm data(n,T), |
| VoIP traffic data(N, T) [[34](https://arxiv.org/html/2309.11356v2#bib.bib34)] |

|  |
| --- |
| Air Pressure System(APS) Failure |
| at Scania Trucks Data Set(N, T) |
| [[85](https://arxiv.org/html/2309.11356v2#bib.bib85), [49](https://arxiv.org/html/2309.11356v2#bib.bib49)] |

|  |
| --- |
| MnDot traffic data(N, T) [[34](https://arxiv.org/html/2309.11356v2#bib.bib34)] |
| Traffic Prediction Dataset(N, T) |
| WWD Data (N, T) [[57](https://arxiv.org/html/2309.11356v2#bib.bib57), [58](https://arxiv.org/html/2309.11356v2#bib.bib58)] |

|  |
| --- |
| 0-1(R1) |

|  |
| --- |
| S and P BSE SENSEX(N, T)[[63](https://arxiv.org/html/2309.11356v2#bib.bib63), [89](https://arxiv.org/html/2309.11356v2#bib.bib89)] |
| Nifty 50(N, T) [[62](https://arxiv.org/html/2309.11356v2#bib.bib62), [90](https://arxiv.org/html/2309.11356v2#bib.bib90)] |
| Kaggle Credit Card Fraud Detection(N, T) |

|  |
| --- |
| Thoracic surgery dataset(N, T) [[91](https://arxiv.org/html/2309.11356v2#bib.bib91)], |
| Bioassay AID 746(N, T),687(N, T),456(N, T),373(N, T), |
| Suicide data(N,T) [[92](https://arxiv.org/html/2309.11356v2#bib.bib92)] |

|  |
| --- |
| stroke dataset(N, T) [[94](https://arxiv.org/html/2309.11356v2#bib.bib94)], |
| Bioassay AID 362(N, T) [[91](https://arxiv.org/html/2309.11356v2#bib.bib91)] |

|  |
| --- |
| Daily electric energy production |
| measurements dataset(Spain, 2003)(N,T) |

|  |
| --- |
| Recidivism dataset (N, T) , |
| Audio-Anomaly-Dataset(A, T) [[98](https://arxiv.org/html/2309.11356v2#bib.bib98)] |

∗N-Numeric, TX-Textual, I-Image, A-Audio, T-Time series

ii) Derived datasets (DE):
A derived dataset is a dataset that is not initially rare, results from transformation of an existing dataset, and includes a new insight, ‘derived rarity’. For this, the original dataset should ideally possess sufficient information and features related to multiple events of interest and should initially be not rare. The availability of such data enables performing operations, calculations, or algorithms on the raw dataset to transform it into a derived dataset that captures the ‘derived rarity’ aspect [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [20](https://arxiv.org/html/2309.11356v2#bib.bib20), [100](https://arxiv.org/html/2309.11356v2#bib.bib100)]. One example of derived datasets is the ABCD (AIST Building Change Detection) dataset [[28](https://arxiv.org/html/2309.11356v2#bib.bib28), [101](https://arxiv.org/html/2309.11356v2#bib.bib101), [102](https://arxiv.org/html/2309.11356v2#bib.bib102)], which was initially not designed to include rare events but has been manipulated in certain studies to create rare event scenarios by altering event percentages [[15](https://arxiv.org/html/2309.11356v2#bib.bib15), [29](https://arxiv.org/html/2309.11356v2#bib.bib29), [103](https://arxiv.org/html/2309.11356v2#bib.bib103)]. MNIST dataset [[104](https://arxiv.org/html/2309.11356v2#bib.bib104)], originally an image dataset, has been repurposed in studies to detect letter changes, creating an imbalanced dataset by reducing the frequency of certain letters [[15](https://arxiv.org/html/2309.11356v2#bib.bib15)]. Table [3](https://arxiv.org/html/2309.11356v2#S2.T3 "Table 3 ‣ 2.1.3 Types of rare events datasets ‣ 2.1 Datasets with rare events – Analysis of existing datasets with rare events ‣ 2 Rare event data ‣ A Comprehensive Survey on Rare Event Prediction") summarizes derived datasets used in rare event research in the studied literature. The analysis findings indicate that a substantial portion (34%) of the derived datasets we considered in this review belong to the extremely rare category.

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| Sector | |  | | --- | | Event % & | | rarity group | | Papers | Source Datasets with modality |
| Earth Sciences | 0-1(R1) | [[29](https://arxiv.org/html/2309.11356v2#bib.bib29), [103](https://arxiv.org/html/2309.11356v2#bib.bib103), [15](https://arxiv.org/html/2309.11356v2#bib.bib15)] | |  | | --- | | ABCD (AIST Building Change Detection) dataset(I, T) [[28](https://arxiv.org/html/2309.11356v2#bib.bib28), [101](https://arxiv.org/html/2309.11356v2#bib.bib101), [102](https://arxiv.org/html/2309.11356v2#bib.bib102)], | | Weather data(N,T),Air pollutant data(N,T), | | Space Weather ANalytics for Solar Flares (SWAN-SF) | | benchmark dataset(N, T) [[48](https://arxiv.org/html/2309.11356v2#bib.bib48)] | |
|  | 1-5(R2) | [[15](https://arxiv.org/html/2309.11356v2#bib.bib15)] | |  | | --- | | ABCD (AIST Building Change Detection) dataset(I, T) [[28](https://arxiv.org/html/2309.11356v2#bib.bib28), [101](https://arxiv.org/html/2309.11356v2#bib.bib101), [102](https://arxiv.org/html/2309.11356v2#bib.bib102)], | | Space Weather ANalytics for Solar Flares (SWAN-SF) | | benchmark dataset(N,T) [[48](https://arxiv.org/html/2309.11356v2#bib.bib48)] | |
|  | 5-10(R3) | [[42](https://arxiv.org/html/2309.11356v2#bib.bib42), [103](https://arxiv.org/html/2309.11356v2#bib.bib103)] | |  | | --- | | Oil dataset(I,T) [[17](https://arxiv.org/html/2309.11356v2#bib.bib17)], | | Weather data(N, T), Air pollutant data(N,T) | |
|  | 10+(R4) | [[103](https://arxiv.org/html/2309.11356v2#bib.bib103), [105](https://arxiv.org/html/2309.11356v2#bib.bib105)] | |  | | --- | | Weather data(N, T),Air pollutant data(N,T), | | ABCD (AIST Building Change Detection) dataset(I,T) [[28](https://arxiv.org/html/2309.11356v2#bib.bib28), [101](https://arxiv.org/html/2309.11356v2#bib.bib101), [102](https://arxiv.org/html/2309.11356v2#bib.bib102)], | |
| Telecommunication | 0-1(R1) | [[106](https://arxiv.org/html/2309.11356v2#bib.bib106), [14](https://arxiv.org/html/2309.11356v2#bib.bib14), [107](https://arxiv.org/html/2309.11356v2#bib.bib107)] | |  | | --- | | IEEE 39-bus power system data(N,T) [[35](https://arxiv.org/html/2309.11356v2#bib.bib35)], | | KDD Cup-99 (N,T) [[80](https://arxiv.org/html/2309.11356v2#bib.bib80), [81](https://arxiv.org/html/2309.11356v2#bib.bib81), [82](https://arxiv.org/html/2309.11356v2#bib.bib82)] | |
|  | 1-5(R2) | [[106](https://arxiv.org/html/2309.11356v2#bib.bib106)] | IEEE 39-bus power system data(N, T) [[35](https://arxiv.org/html/2309.11356v2#bib.bib35)] |
|  | 5-10(R3) | [[106](https://arxiv.org/html/2309.11356v2#bib.bib106)] | |  | | --- | | IEEE 39-bus power system data(N, T) [[35](https://arxiv.org/html/2309.11356v2#bib.bib35)], | | Spam data(N, T) [[36](https://arxiv.org/html/2309.11356v2#bib.bib36)] | |
|  | 10+(R4) | [[106](https://arxiv.org/html/2309.11356v2#bib.bib106)] | |  | | --- | | IEEE 39-bus power system data(N, T) [[35](https://arxiv.org/html/2309.11356v2#bib.bib35)], | | Spam data(N, T) [[36](https://arxiv.org/html/2309.11356v2#bib.bib36)] | |
| Transportation | 0-1(R1) | [[100](https://arxiv.org/html/2309.11356v2#bib.bib100), [20](https://arxiv.org/html/2309.11356v2#bib.bib20)] | |  | | --- | | AIRBUS data(N, T), | | ACMS dataset(N, T) [[51](https://arxiv.org/html/2309.11356v2#bib.bib51)] | |
| Healthcare | 0-1(R1) | [[37](https://arxiv.org/html/2309.11356v2#bib.bib37)] | EEG Seizure Dataset(N, T) |
|  | 1-5(R2) | [[108](https://arxiv.org/html/2309.11356v2#bib.bib108), [37](https://arxiv.org/html/2309.11356v2#bib.bib37)] | |  | | --- | | COVID-19(N, T), | | InP -Duke University Health System (DUHS)(N,T) [[109](https://arxiv.org/html/2309.11356v2#bib.bib109)], | | SEER(N, T) [[110](https://arxiv.org/html/2309.11356v2#bib.bib110)], | | EEG Seizure Dataset (N, T) | |
|  | 5-10(R3) | [[108](https://arxiv.org/html/2309.11356v2#bib.bib108)] | COVID-19(N, T) |
| Energy | |  | | --- | | 0-1(R1), | | 1-5(R2), | | 5-10(R3), | | 10+(R4) | | [[111](https://arxiv.org/html/2309.11356v2#bib.bib111)] | MAGIC Gamma Telescope(N,T) [[112](https://arxiv.org/html/2309.11356v2#bib.bib112)] |
| Others | 0-1(R1) | [[29](https://arxiv.org/html/2309.11356v2#bib.bib29)] | |  | | --- | | Augmented MNIST(I,T) [[104](https://arxiv.org/html/2309.11356v2#bib.bib104)], | | WDC dataset(I,T) [[113](https://arxiv.org/html/2309.11356v2#bib.bib113)] | |
|  | 10+(R4) | [[10](https://arxiv.org/html/2309.11356v2#bib.bib10), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [29](https://arxiv.org/html/2309.11356v2#bib.bib29)] | |  | | --- | | Augmented MNIST(I,T) [[104](https://arxiv.org/html/2309.11356v2#bib.bib104)], | | Adult dataset(N,T) [[114](https://arxiv.org/html/2309.11356v2#bib.bib114)], | | AudioSet dataset(A,T) [[115](https://arxiv.org/html/2309.11356v2#bib.bib115)] | |

|  |
| --- |
| Event % & |
| rarity group |

|  |
| --- |
| ABCD (AIST Building Change Detection) dataset(I, T) [[28](https://arxiv.org/html/2309.11356v2#bib.bib28), [101](https://arxiv.org/html/2309.11356v2#bib.bib101), [102](https://arxiv.org/html/2309.11356v2#bib.bib102)], |
| Weather data(N,T),Air pollutant data(N,T), |
| Space Weather ANalytics for Solar Flares (SWAN-SF) |
| benchmark dataset(N, T) [[48](https://arxiv.org/html/2309.11356v2#bib.bib48)] |

|  |
| --- |
| ABCD (AIST Building Change Detection) dataset(I, T) [[28](https://arxiv.org/html/2309.11356v2#bib.bib28), [101](https://arxiv.org/html/2309.11356v2#bib.bib101), [102](https://arxiv.org/html/2309.11356v2#bib.bib102)], |
| Space Weather ANalytics for Solar Flares (SWAN-SF) |
| benchmark dataset(N,T) [[48](https://arxiv.org/html/2309.11356v2#bib.bib48)] |

|  |
| --- |
| Oil dataset(I,T) [[17](https://arxiv.org/html/2309.11356v2#bib.bib17)], |
| Weather data(N, T), Air pollutant data(N,T) |

|  |
| --- |
| Weather data(N, T),Air pollutant data(N,T), |
| ABCD (AIST Building Change Detection) dataset(I,T) [[28](https://arxiv.org/html/2309.11356v2#bib.bib28), [101](https://arxiv.org/html/2309.11356v2#bib.bib101), [102](https://arxiv.org/html/2309.11356v2#bib.bib102)], |

|  |
| --- |
| IEEE 39-bus power system data(N,T) [[35](https://arxiv.org/html/2309.11356v2#bib.bib35)], |
| KDD Cup-99 (N,T) [[80](https://arxiv.org/html/2309.11356v2#bib.bib80), [81](https://arxiv.org/html/2309.11356v2#bib.bib81), [82](https://arxiv.org/html/2309.11356v2#bib.bib82)] |

|  |
| --- |
| IEEE 39-bus power system data(N, T) [[35](https://arxiv.org/html/2309.11356v2#bib.bib35)], |
| Spam data(N, T) [[36](https://arxiv.org/html/2309.11356v2#bib.bib36)] |

|  |
| --- |
| IEEE 39-bus power system data(N, T) [[35](https://arxiv.org/html/2309.11356v2#bib.bib35)], |
| Spam data(N, T) [[36](https://arxiv.org/html/2309.11356v2#bib.bib36)] |

|  |
| --- |
| AIRBUS data(N, T), |
| ACMS dataset(N, T) [[51](https://arxiv.org/html/2309.11356v2#bib.bib51)] |

|  |
| --- |
| COVID-19(N, T), |
| InP -Duke University Health System (DUHS)(N,T) [[109](https://arxiv.org/html/2309.11356v2#bib.bib109)], |
| SEER(N, T) [[110](https://arxiv.org/html/2309.11356v2#bib.bib110)], |
| EEG Seizure Dataset (N, T) |

|  |
| --- |
| 0-1(R1), |
| 1-5(R2), |
| 5-10(R3), |
| 10+(R4) |

|  |
| --- |
| Augmented MNIST(I,T) [[104](https://arxiv.org/html/2309.11356v2#bib.bib104)], |
| WDC dataset(I,T) [[113](https://arxiv.org/html/2309.11356v2#bib.bib113)] |

|  |
| --- |
| Augmented MNIST(I,T) [[104](https://arxiv.org/html/2309.11356v2#bib.bib104)], |
| Adult dataset(N,T) [[114](https://arxiv.org/html/2309.11356v2#bib.bib114)], |
| AudioSet dataset(A,T) [[115](https://arxiv.org/html/2309.11356v2#bib.bib115)] |

∗N-Numeric, TX-Textual, I-Image, A-Audio, T-Time series

|  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| Sector | |  | | --- | | Event % & | | rarity group | | Papers | Data type | Technique |
| Earth Sciences | 0-1 (R1) | [[30](https://arxiv.org/html/2309.11356v2#bib.bib30), [64](https://arxiv.org/html/2309.11356v2#bib.bib64), [116](https://arxiv.org/html/2309.11356v2#bib.bib116)] | N, T | |  | | --- | | OLGA Dynamic Multiphase | | Flow Simulator [[117](https://arxiv.org/html/2309.11356v2#bib.bib117)], MATLAB | |
|  | 1-5 (R2) | [[30](https://arxiv.org/html/2309.11356v2#bib.bib30), [64](https://arxiv.org/html/2309.11356v2#bib.bib64)] | N, T | |  | | --- | | OLGA Dynamic Multiphase | | Flow Simulator [[117](https://arxiv.org/html/2309.11356v2#bib.bib117)], MATLAB | |
|  | 5-10 (R3) | |  | | --- | | [[103](https://arxiv.org/html/2309.11356v2#bib.bib103), [42](https://arxiv.org/html/2309.11356v2#bib.bib42)] | | [[30](https://arxiv.org/html/2309.11356v2#bib.bib30), [64](https://arxiv.org/html/2309.11356v2#bib.bib64)] | | N, T | |  | | --- | | MATLAB, OLGA Dynamic Multiphase | | Flow Simulator [[117](https://arxiv.org/html/2309.11356v2#bib.bib117)], | |
|  | 10+ (R4) | [[30](https://arxiv.org/html/2309.11356v2#bib.bib30), [64](https://arxiv.org/html/2309.11356v2#bib.bib64)] | N, T | |  | | --- | | OLGA Dynamic Multiphase | | Flow Simulator [[117](https://arxiv.org/html/2309.11356v2#bib.bib117)] | |
|  | |  | | --- | | Rarity not | | reported | | [[118](https://arxiv.org/html/2309.11356v2#bib.bib118), [119](https://arxiv.org/html/2309.11356v2#bib.bib119), [120](https://arxiv.org/html/2309.11356v2#bib.bib120)] | N, T | |  | | --- | | Signal Fragment Assembler (SFA), | | Variational Autoencoder (VAE), | | Data Picker (DP), | | Quality Classifier (QC) | |
| Others | 0-1 (R1) | |  | | --- | | [[22](https://arxiv.org/html/2309.11356v2#bib.bib22), [121](https://arxiv.org/html/2309.11356v2#bib.bib121), [122](https://arxiv.org/html/2309.11356v2#bib.bib122), [111](https://arxiv.org/html/2309.11356v2#bib.bib111), [107](https://arxiv.org/html/2309.11356v2#bib.bib107)] | | |  | | --- | | N, T | | N, T | | |  | | --- | | Monte Carlo, MATLAB | | Importance sampling | |
|  | |  | | --- | | 1-5 (R1), | | 5-10 (R3) | | [[122](https://arxiv.org/html/2309.11356v2#bib.bib122), [111](https://arxiv.org/html/2309.11356v2#bib.bib111)] | |  | | --- | | N, T | | N, T | | |  | | --- | | Monte Carlo, MATLAB | | Importance sampling | |
|  | 10 + (R4) | [[16](https://arxiv.org/html/2309.11356v2#bib.bib16)] | N, T | MOA [[123](https://arxiv.org/html/2309.11356v2#bib.bib123)] |

|  |
| --- |
| Event % & |
| rarity group |

|  |
| --- |
| OLGA Dynamic Multiphase |
| Flow Simulator [[117](https://arxiv.org/html/2309.11356v2#bib.bib117)], MATLAB |

|  |
| --- |
| OLGA Dynamic Multiphase |
| Flow Simulator [[117](https://arxiv.org/html/2309.11356v2#bib.bib117)], MATLAB |

|  |
| --- |
| [[103](https://arxiv.org/html/2309.11356v2#bib.bib103), [42](https://arxiv.org/html/2309.11356v2#bib.bib42)] |
| [[30](https://arxiv.org/html/2309.11356v2#bib.bib30), [64](https://arxiv.org/html/2309.11356v2#bib.bib64)] |

|  |
| --- |
| MATLAB, OLGA Dynamic Multiphase |
| Flow Simulator [[117](https://arxiv.org/html/2309.11356v2#bib.bib117)], |

|  |
| --- |
| OLGA Dynamic Multiphase |
| Flow Simulator [[117](https://arxiv.org/html/2309.11356v2#bib.bib117)] |

|  |
| --- |
| Rarity not |
| reported |

|  |
| --- |
| Signal Fragment Assembler (SFA), |
| Variational Autoencoder (VAE), |
| Data Picker (DP), |
| Quality Classifier (QC) |

|  |
| --- |
| [[22](https://arxiv.org/html/2309.11356v2#bib.bib22), [121](https://arxiv.org/html/2309.11356v2#bib.bib121), [122](https://arxiv.org/html/2309.11356v2#bib.bib122), [111](https://arxiv.org/html/2309.11356v2#bib.bib111), [107](https://arxiv.org/html/2309.11356v2#bib.bib107)] |

|  |
| --- |
| N, T |
| N, T |

|  |
| --- |
| Monte Carlo, MATLAB |
| Importance sampling |

|  |
| --- |
| 1-5 (R1), |
| 5-10 (R3) |

|  |
| --- |
| N, T |
| N, T |

|  |
| --- |
| Monte Carlo, MATLAB |
| Importance sampling |

∗N-Numeric, T-Time series

iii) Simulated / Synthetic (SIY) datasets:
A simulated (also termed synthetic) dataset is an artificially generated dataset that mimics the characteristics and patterns of real-world rare events. They are typically created based on known models, distributions, or algorithms to replicate the statistical properties and relationships observed in the original data. These data can be generated in cases where collecting direct data on rare events is challenging and impractical. They are beneficial for predicting rare events that have not yet occurred or for testing the accuracy of predictive models in a controlled environment [[22](https://arxiv.org/html/2309.11356v2#bib.bib22), [30](https://arxiv.org/html/2309.11356v2#bib.bib30), [31](https://arxiv.org/html/2309.11356v2#bib.bib31), [42](https://arxiv.org/html/2309.11356v2#bib.bib42), [103](https://arxiv.org/html/2309.11356v2#bib.bib103)]. In the literature, SIY datasets have been generated in controlled environments using tools such as MATLAB, OLGA Dynamic Multiphase Flow Simulator [[117](https://arxiv.org/html/2309.11356v2#bib.bib117)], Signal Fragment Assembler (SFA), Variational Autoencoder (VAE), Data Picker (DP), Quality Classifier (QC) [[118](https://arxiv.org/html/2309.11356v2#bib.bib118), [119](https://arxiv.org/html/2309.11356v2#bib.bib119), [120](https://arxiv.org/html/2309.11356v2#bib.bib120)], and frameworks like Massive Online Analysis (MOA) [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [123](https://arxiv.org/html/2309.11356v2#bib.bib123)], as presented in Table [4](https://arxiv.org/html/2309.11356v2#S2.T4 "Table 4 ‣ 2.1.3 Types of rare events datasets ‣ 2.1 Datasets with rare events – Analysis of existing datasets with rare events ‣ 2 Rare event data ‣ A Comprehensive Survey on Rare Event Prediction"). While most studies focus on naturally rare and derived datasets, considerably less research is based on simulated / synthetic datasets.

#### 2.1.4 Rare event metadata

Metadata refers to the descriptive information that provides additional context about a dataset. It includes information about the structure, format, quality, source, and other data characteristics. In rare event data acquisition, metadata acquisition involves extracting relevant information from the data that contributes to a better understanding of the rare events. While metadata may be applicable to both rare and majority classes, its importance for rare events stems from the need to capture additional attributes specific to these events. This can include attributes such as timestamps, geographical location, variables related to the event’s occurrence, data sources, data collection methods, and any other contextual information that aids in analyzing and interpreting the rare events. The following methods were revealed as ways of acquiring metadata.

Data collection: Metadata can be collected during data acquisition. This includes capturing information such as the source of the data, timestamps, geographical coordinates, sensor settings, or any other relevant contextual details that help describe the data [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [100](https://arxiv.org/html/2309.11356v2#bib.bib100), [124](https://arxiv.org/html/2309.11356v2#bib.bib124), [125](https://arxiv.org/html/2309.11356v2#bib.bib125)].

Expert opinions: Engaging domain experts or subject matter specialists can provide valuable metadata. Experts can contribute their knowledge about rare events, their causes-effects, associated variables of interest, equations, hypotheses, or factors that influence their occurrence [[103](https://arxiv.org/html/2309.11356v2#bib.bib103), [100](https://arxiv.org/html/2309.11356v2#bib.bib100), [22](https://arxiv.org/html/2309.11356v2#bib.bib22), [64](https://arxiv.org/html/2309.11356v2#bib.bib64), [30](https://arxiv.org/html/2309.11356v2#bib.bib30), [31](https://arxiv.org/html/2309.11356v2#bib.bib31)]. This knowledge can assist in identifying appropriate metadata to enhance the analysis and prediction of rare events.

Data annotation: Adding annotations or labels to the data can serve as metadata. This requires manually categorizing data instances as rare events or non-rare events, assigning event severity or damage levels, utilizing standard metrics and indexes, and providing additional descriptive labels that capture specific attributes or characteristics of the rare events [[22](https://arxiv.org/html/2309.11356v2#bib.bib22), [126](https://arxiv.org/html/2309.11356v2#bib.bib126), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [127](https://arxiv.org/html/2309.11356v2#bib.bib127), [64](https://arxiv.org/html/2309.11356v2#bib.bib64), [39](https://arxiv.org/html/2309.11356v2#bib.bib39)].

External sources: Documents, technical reports, publications, and websites offer insights, statistical data, or contextual details that contribute to the understanding and analysis of rare events. For example, clinical reports, insurance claims data, state mortality records from government websites, outpatient visit details from electronic health records, and responses to patient-reported measures like the Patient Health Questionnaire (PHQ-9) have provided valuable information in predicting rare medical incidents [[93](https://arxiv.org/html/2309.11356v2#bib.bib93), [128](https://arxiv.org/html/2309.11356v2#bib.bib128)].

#### 2.1.5 Characteristics of rare event datasets and associated challenges

Rare event datasets exhibit distinct characteristics that lead to various related issues, some outlined below.

Skewed class distribution and lack of data: A skewed class distribution is a distribution of classes that is not symmetrical or evenly distributed. Class imbalance is a specific case of skewed class distribution featuring a substantial disparity in the number of instances between classes [[129](https://arxiv.org/html/2309.11356v2#bib.bib129), [130](https://arxiv.org/html/2309.11356v2#bib.bib130)]. In rare events datasets, the minority class has a significantly smaller number of samples than the majority class. This skewness in class distribution makes it difficult for ML algorithms to learn patterns and classify the minority class accurately [[17](https://arxiv.org/html/2309.11356v2#bib.bib17)]. Lack of data can take two forms. Absolute rarity occurs where the number of samples associated with the minority class is small in the absolute sense, whereas relative rarity happens where the minority class samples are less relative to the other classes [[131](https://arxiv.org/html/2309.11356v2#bib.bib131)]. These rarity forms pose consequential challenges for classifiers in identifying patterns and regularities within these rare occurrences to learn a robust model [[17](https://arxiv.org/html/2309.11356v2#bib.bib17), [22](https://arxiv.org/html/2309.11356v2#bib.bib22)].

Temporal property: An inherent characteristic of rare event datasets is the temporal aspect, which refers to the occurrence or sequencing of events over time. Temporal property is essential in analyzing and understanding rare event data, as it provides insights into the timing, duration, order, and interdependencies of rare events and normal events [[4](https://arxiv.org/html/2309.11356v2#bib.bib4)]. However, due to the imbalanced class distribution and data sparsity in a temporal context, capturing the time-dependent patterns and correlations in data can be a major challenge. Thus, handling these issues in a temporal context adds complexity to the analysis, necessitating specialized techniques for accurate prediction.

Class overlap: In some cases, there may be overlapping patterns or similarities between the rare event(minority class) and the non-rare events(majority class) [[132](https://arxiv.org/html/2309.11356v2#bib.bib132), [133](https://arxiv.org/html/2309.11356v2#bib.bib133)]. This can lead to misclassifying rare events as more common, resulting in false negatives.

Uncertainty: Uncertainty, in the context of rare event datasets, refers to the lack of precise knowledge and confidence in the observed data. This arises from the limited sample size, data sparsity, high-class imbalance, and lack of information, and it becomes a challenging issue in generalizing the findings of any downstream task [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [122](https://arxiv.org/html/2309.11356v2#bib.bib122)].

High dimensionality: Rare event datasets can include many features or dimensions, including numerical, categorical, or textual variables [[86](https://arxiv.org/html/2309.11356v2#bib.bib86), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)]. Including multiple features complicates the modeling process and requires careful feature selection or dimensionality reduction techniques.

Event complexity: Rare events involve intricate relationships between multiple variables, which generate complex patterns and interactions in real-world systems [[125](https://arxiv.org/html/2309.11356v2#bib.bib125)]. This often makes modeling rare events difficult, necessitating sophisticated modeling approaches to capture the underlying complexity.

#### 2.1.6 Factors that cause rarity in a dataset

Several factors can cause rarity in a dataset, including:

Natural occurrences: Some events simply occur less frequently in nature than others. For example, diseases that affect a small percentage of the population will naturally result in highly imbalanced datasets. Natural hazards like landslides, tsunamis, and seismic bumps or climate catastrophes like heavy flooding that may occur once in a century are also rare occurrences [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [70](https://arxiv.org/html/2309.11356v2#bib.bib70), [126](https://arxiv.org/html/2309.11356v2#bib.bib126), [134](https://arxiv.org/html/2309.11356v2#bib.bib134)]. Black-swan events, unpredictable events with severe global economic consequences, are extremely rare natural events in the economic sector. Events like the 9/11 attack and the Chinese economic downturn are examples of these [[23](https://arxiv.org/html/2309.11356v2#bib.bib23)].

Class definition: The definition of a class can also impact its rarity. If a class is defined narrowly or specifically, it may contain fewer instances than if defined broadly [[132](https://arxiv.org/html/2309.11356v2#bib.bib132)]. For instance, when estimating the likelihood of stroke based on varied input parameters like demographic data, additional illnesses, and smoking status, the definitions of "having a stroke" and "not having a stroke" may be narrowly defined. Due to these specific criteria used in classification, stroke events within the dataset may be deemed rare.

Sampling bias: If data are collected from a biased sample, they may not precisely reflect the true distribution of the population. In particular, if a rare event dataset only contains events occurring in certain geographic regions or in certain types of people, this can cause rarity. For instance, while HIV (Human Immunodeficiency Virus) is not classified as rare due to its global prevalence [[135](https://arxiv.org/html/2309.11356v2#bib.bib135)], there are specific regions and subpopulations where HIV is relatively rare, indicating variations in its incidence and prevalence.

Cost and measurement errors: Data collection and labeling can be expensive, and in some cases, collecting large amounts of data for a rare event may not be feasible. Evidently, the generation of simulated data and synthetic data may be costly. It may be challenging to accurately observe and measure rare events in natural and controlled environments, resulting in fewer labeled instances. Similarly, rare events that involve complex interactions among their dimensions may not always be observable and measurable accurately. For example, rare events like Wrong-Way Driving (WWD) are influenced by multiple variables like roadway geometry and configurations, traffic volume, lighting conditions, weather conditions, and driver’s age and medical conditions. However, the impact of these complex interactions is not always readily observable and measurable, giving rise to various complications [[21](https://arxiv.org/html/2309.11356v2#bib.bib21)].

Subjective decisions: Curators can selectively include instances of a rare event based on specific criteria by selecting features and classes that impact the rarity of that class within the dataset. The decision to include only such instances can affect the rarity of the class within the dataset. This is apparent when creating new datasets by generating derived, simulated, or synthetic data based on the original rare event datasets. For example, in predicting rare events like extreme heat waves, curators have used subjective decisions by selecting temperature and humidity thresholds and time periods based on their understanding of heat wave severity [[39](https://arxiv.org/html/2309.11356v2#bib.bib39)]. These decisions can be made to categorize the data into classes and identify patterns related to moderate, severe, or extreme heat waves.

The relationship between rare event data, acquisition methods, rarity factors, characteristics, and challenges of rare event datasets is multifaceted and interconnected, as summarized in Figure [3](https://arxiv.org/html/2309.11356v2#S2.F3 "Figure 3 ‣ 2.1.6 Factors that cause rarity in a dataset ‣ 2.1 Datasets with rare events – Analysis of existing datasets with rare events ‣ 2 Rare event data ‣ A Comprehensive Survey on Rare Event Prediction"). The factors contributing to a dataset’s rarity inherently result in rare event data and their characteristics. Rare event data constitute rare event datasets, which can be acquired through various methods. The characteristics of these data, in turn, give rise to various challenges in analyzing and predicting rare events, as discussed in the previous section.

![Refer to caption](x3.png)

In conclusion, this section examined four significant subsections in depth: rare event datasets, data acquisition methods, factors of rarity, characteristics, and challenges of dealing with rare event data. We devised a rarity hierarchy that provided a systematic method for summing data pertinent to rare events for the purposes of analysis. While most datasets and studies fall under the extremely-rare category in the hierarchy of rarity, many research projects are based on naturally rare and derived datasets. Textual and audio data-based research on rare events has received less attention than time series, image, and numerical data-based datasets. It is worth revealing that rare event-related problems and research are not restricted to a specific domain, industry, or sector, as we investigated research efforts across multiple sectors. Finally, the relationship between rare event data, acquisition methods, rarity factors, characteristics, and challenges of rare event datasets are drawn to summarize the overall scope of review in this section.

## 3 Data Processing Approaches

This section focuses on the importance of data processing methods in enhancing data quality for improved predictive model performance when dealing with rare event datasets. It explores various data processing approaches used in rare event prediction research, emphasizing their specific objectives. The subsequent discussion provides a detailed examination of each objective, including an analysis of how these approaches intersect with data modality, rarity groups, and downstream tasks.

### 3.1 Objectives of Data Processing Approaches

In the literature, we identified that data processing approaches aim to achieve four main objectives. Firstly, it’s responsible for data cleaning, which improves the quality, consistency, and reliability of data analysis results. Secondly, it caters to feature selection by selecting the optimal variables by limiting the input variables to the model and utilizing only relevant features. Thirdly, it aids in sampling by modifying the data samples to balance the distribution and/or eliminating undesirable samples at the data level. Finally, data processing methods are applied in feature engineering to transform raw series data into a stable format suitable for modeling. In Figure [4](https://arxiv.org/html/2309.11356v2#S3.F4 "Figure 4 ‣ 3.1 Objectives of Data Processing Approaches ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction"), we classify the data processing approaches in rare event research that adhere to the aforementioned four objectives into four main categories. The approaches to data processing in rare event studies are summarized in Table [5](https://arxiv.org/html/2309.11356v2#S3.T5 "Table 5 ‣ 3.5.2 Analyzing feature engineering approaches with data modalities, rarity groups, and downstream tasks ‣ 3.5 Feature Engineering (FE) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction"), along with their primary categories, rarity groups, data modalities, and subsequent tasks.

![Refer to caption](x4.png)

### 3.2 Data Cleaning (DC)

Data cleaning focuses on the important task of preparing and refining the data. This involves various techniques and processes to improve the dataset’s quality, consistency, and reliability. This subsection examines various data cleaning approaches and discusses the application of them in various data modalities, rarity levels, and downstream tasks (See Figure [5](https://arxiv.org/html/2309.11356v2#S3.F5 "Figure 5 ‣ 3.2.3 Analyzing data cleaning approaches with data modalities, rarity groups, and downstream tasks ‣ 3.2 Data Cleaning (DC) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction") and discussion in the sub section [3.2.3](https://arxiv.org/html/2309.11356v2#S3.SS2.SSS3 "3.2.3 Analyzing data cleaning approaches with data modalities, rarity groups, and downstream tasks ‣ 3.2 Data Cleaning (DC) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction").

#### 3.2.1 Approaches to data cleaning

Various approaches address data cleaning tasks, often depending on the specific data modalities. Some common data cleaning methods used in rare event-based data mining include data sifting, filtering, imputation, noise removal, audio-based preprocessing, text-based preprocessing, and image processing techniques.

#### 3.2.2 Approaches to data cleaning

Various approaches address data cleaning tasks, often depending on the specific data modalities. Some common data cleaning methods used in rare event-based data mining include data sifting, filtering, imputation, noise removal, audio-based preprocessing, text-based preprocessing, and image processing techniques.

i) Data sifting:
Refers to refining large volumes of data to identify the most relevant and important information. In rare event literature, sifting has been used to systematically sort through the data to identify and extract specific subsets of data. There are two types of data sifting: heuristic data sifting and statistical data sifting. Heuristic data sifting relies on expert knowledge and intuition, while statistical data sifting relies on quantitative measures and algorithms to identify relevant features [[83](https://arxiv.org/html/2309.11356v2#bib.bib83), [103](https://arxiv.org/html/2309.11356v2#bib.bib103), [136](https://arxiv.org/html/2309.11356v2#bib.bib136), [137](https://arxiv.org/html/2309.11356v2#bib.bib137)]. In [[103](https://arxiv.org/html/2309.11356v2#bib.bib103)], important knowledge about Ozone (O3subscript𝑂3O\_{3}italic\_O start\_POSTSUBSCRIPT 3 end\_POSTSUBSCRIPT) concentration (i.e., time periods where O3subscript𝑂3O\_{3}italic\_O start\_POSTSUBSCRIPT 3 end\_POSTSUBSCRIPT is high) has been used as a heuristic, and several statistical measures were undertaken to identify relationships between different O3subscript𝑂3O\_{3}italic\_O start\_POSTSUBSCRIPT 3 end\_POSTSUBSCRIPT states and related components.

ii) Data filtering:
Involves segregating and removing unwanted, irrelevant data or information from a large dataset. This includes techniques like removing duplicate data [[27](https://arxiv.org/html/2309.11356v2#bib.bib27)], removing records containing very small number of records per group [[26](https://arxiv.org/html/2309.11356v2#bib.bib26), [138](https://arxiv.org/html/2309.11356v2#bib.bib138)], removing rows containing irrelevant types [[83](https://arxiv.org/html/2309.11356v2#bib.bib83)], and removing rows that meet specific conditions [[108](https://arxiv.org/html/2309.11356v2#bib.bib108)]. For instance, in [[83](https://arxiv.org/html/2309.11356v2#bib.bib83)], only the connected calls were used, discarding the unconnected calls from VoIP traffic data in unsupervised rare event detection in spatiotemporal environments. [[108](https://arxiv.org/html/2309.11356v2#bib.bib108)] used a cut-off time to define an event of interest and excluded subjects censored before the cut-off time.

iii) Imputation:
Imputation or value approximation techniques estimate and represent missing and incorrect values in a dataset with reasonable approximations based on the available data. These techniques are vital for addressing the sparse, incomplete, and imbalanced nature of the rare event data, requiring careful consideration to avoid skewed results. Simple methods like mean and median imputation, though commonly used, can introduce bias in rare event scenarios due to the skewed nature of the data [[49](https://arxiv.org/html/2309.11356v2#bib.bib49), [108](https://arxiv.org/html/2309.11356v2#bib.bib108), [88](https://arxiv.org/html/2309.11356v2#bib.bib88), [87](https://arxiv.org/html/2309.11356v2#bib.bib87), [86](https://arxiv.org/html/2309.11356v2#bib.bib86), [85](https://arxiv.org/html/2309.11356v2#bib.bib85)]. Advanced techniques such as Interpolation techniques [[139](https://arxiv.org/html/2309.11356v2#bib.bib139), [15](https://arxiv.org/html/2309.11356v2#bib.bib15)], Iterative Imputation [[140](https://arxiv.org/html/2309.11356v2#bib.bib140), [127](https://arxiv.org/html/2309.11356v2#bib.bib127), [8](https://arxiv.org/html/2309.11356v2#bib.bib8)], Multiple Imputation by Chained Equation(MICE)[[88](https://arxiv.org/html/2309.11356v2#bib.bib88)], Soft Impute [[141](https://arxiv.org/html/2309.11356v2#bib.bib141)], Expectation maximization (EM) [[142](https://arxiv.org/html/2309.11356v2#bib.bib142), [8](https://arxiv.org/html/2309.11356v2#bib.bib8)], and Singular Value Decomposition (SVD) [[143](https://arxiv.org/html/2309.11356v2#bib.bib143), [144](https://arxiv.org/html/2309.11356v2#bib.bib144)] are better suited for rare-event datasets, as they account for complex patterns and correlations [[127](https://arxiv.org/html/2309.11356v2#bib.bib127), [141](https://arxiv.org/html/2309.11356v2#bib.bib141), [143](https://arxiv.org/html/2309.11356v2#bib.bib143)]. These methods help maintain the integrity of rare events during the imputation process, making them significant for accurate predictions.

iv) Noise removal: Involves eliminating random and irrelevant data variations that don’t contribute meaningful information to patterns and relationships. The Brooks-Iyengar algorithm is a fault-tolerant method for sensor fusion, handling faulty sensor readings effectively [[145](https://arxiv.org/html/2309.11356v2#bib.bib145)]. Iyer et al. [[146](https://arxiv.org/html/2309.11356v2#bib.bib146)] utilized Brooks-Iyengar along with ensemble data cleaning trees to handle random noise and missing data. Sampling methods like Tomek-links (TL) and Edited Nearest Neighbors (ENN) are used for noise removal. TL removes noise and boundary points in the majority class during rare events [[147](https://arxiv.org/html/2309.11356v2#bib.bib147), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [21](https://arxiv.org/html/2309.11356v2#bib.bib21), [17](https://arxiv.org/html/2309.11356v2#bib.bib17)], while ENN eliminates noisy data samples, resulting in smoother decision boundaries [[21](https://arxiv.org/html/2309.11356v2#bib.bib21)].

v) Text-based cleaning techniques: Standard text preprocessing techniques, such as converting text to lowercase, removing stop-words, and employing stemming and lemmatization, have been used in rare event prediction studies involving textual data. This standardization improves the reliability of predictions by addressing textual inconsistencies, reducing noise and data variability in rare events involving textual data [[95](https://arxiv.org/html/2309.11356v2#bib.bib95), [11](https://arxiv.org/html/2309.11356v2#bib.bib11)]. For instance, in healthcare, R packages such as ’tm’, ’snowball’, and ’Rstem’ have been used to standardize text data by normalizing word variations through stemming and lemmatization, thereby enhancing the prediction of rare medical incidents [[95](https://arxiv.org/html/2309.11356v2#bib.bib95)].

vi) Image processing techniques:
In rare event prediction using images, image processing techniques have been employed to clean and normalize the images. These techniques aim to detect suspicious regions and extract relevant features that differentiate rare regions from similar ones. Kubat et al. [[17](https://arxiv.org/html/2309.11356v2#bib.bib17)] used various image processing methods to correct for radar beam incidence angle, identify dark regions, and extract specific features like the size of oil spills and average brightness. The output of the image processing is a fixed-length feature vector for each suspicious region, facilitating further analysis and prediction.

#### 3.2.3 Analyzing data cleaning approaches with data modalities, rarity groups, and downstream tasks

![Refer to caption](x5.png)

To explore the data cleaning approaches, we referred to 116 rare event prediction-related papers. Then, we analyzed these by data cleaning approach, modality, and rarity group. We observed the interplay between these as shown in Figure [5](https://arxiv.org/html/2309.11356v2#S3.F5 "Figure 5 ‣ 3.2.3 Analyzing data cleaning approaches with data modalities, rarity groups, and downstream tasks ‣ 3.2 Data Cleaning (DC) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction"). In terms of numerical data cleaning, techniques such as data sifting, data filtering, imputation, and noise removal have been commonly employed, with the rarity level being independent of these techniques. Notably, noise removal has not been applied to the extremely-rare group. Moreover, specific modalities are addressed, such as image processing techniques for image-based rare event prediction and text-related techniques encompassing textual summary generation, text conversions, stemming, and lemmatization for text-based predictions. These audio-based and text-based approaches were used for frequently-rare datasets. Furthermore, image processing techniques are employed to predict images within the very-rare group. While many data processing methods have supported classification tasks, some of these methods have been used in clustering and forecasting research.

### 3.3 Feature Selection (FS)

Feature selection aims to identify a subset of input features from a dataset to extract the most pertinent information and improve the model’s predictive capacities by reducing complexity. This subsection examines various approaches for feature selection in rare event studies and discusses the application of these techniques to various data modalities, rarity levels, and downstream tasks (See Figure [6](https://arxiv.org/html/2309.11356v2#S3.F6 "Figure 6 ‣ 3.3.2 Analyzing feature selection approaches with data modalities, rarity groups, and downstream tasks ‣ 3.3 Feature Selection (FS) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction") and discussion in Section [3.3.2](https://arxiv.org/html/2309.11356v2#S3.SS3.SSS2 "3.3.2 Analyzing feature selection approaches with data modalities, rarity groups, and downstream tasks ‣ 3.3 Feature Selection (FS) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction")).

#### 3.3.1 Approaches to feature selection

Feature selection in rare event prediction is crucial due to the imbalance and sparsity of the data, requiring careful adaptation to identify the most relevant features while preserving critical information related to rare events. The techniques can be categorized into unsupervised and supervised methods.


I) Unsupervised methods:
Unsupervised feature selection methods are applied without considering the response or target variable, focusing on the relationships and patterns within the independent variables. For example, Correlation-based feature selection, frequently used in rare-event studies, evaluates the relationships between features using correlation coefficients like Pearson correlation, Analysis of Variance (ANOVA), and chi-squared tests. However, given the rarity of the events, thresholds for eliminating features must be set carefully to preserve variables that may appear redundant in general datasets but are critical in rare-event contexts [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [100](https://arxiv.org/html/2309.11356v2#bib.bib100), [22](https://arxiv.org/html/2309.11356v2#bib.bib22), [148](https://arxiv.org/html/2309.11356v2#bib.bib148)].

II) Supervised methods:
These methods use the response/target variable in the feature selection process and eliminate irrelevant variables in making a prediction. The supervised methods can be categorized into wrapper-based, filter-based, and intrinsic-based. Wrapper-based methods search for well-performing subsets of input features. They wrap or embed an ML algorithm within their core to perform feature selection. In rare-event scenarios, wrapper-based methods like Recursive Feature Elimination (RFE) can be adapted to preserve features critical for identifying rare events, even if these features do not show strong significance in a broader dataset. For instance, RFE has been combined with Hidden Markov Models (HMMs) to predict rare events, as it is sensitive to the subtle temporal patterns that may indicate these uncommon occurrences [[77](https://arxiv.org/html/2309.11356v2#bib.bib77)].
Standard filter-based methods extract or select features based on their statistical relationship with the target variable. Given their rarity, traditional statistical measures can be misleading or insufficient to identify rare events. For instance, sliding window techniques and wavelet transforms can be adjusted to focus on detecting rare spikes or patterns that could be easily overshadowed by more frequent but less relevant data [[79](https://arxiv.org/html/2309.11356v2#bib.bib79)]. The adaptation of methods like wavelet analysis [[79](https://arxiv.org/html/2309.11356v2#bib.bib79)], Discrete Wavelet Transform (DWT) [[77](https://arxiv.org/html/2309.11356v2#bib.bib77)] and Gumbel copula function [[126](https://arxiv.org/html/2309.11356v2#bib.bib126)], Minimum Redundancy Maximum Relevance (mRMR) [[148](https://arxiv.org/html/2309.11356v2#bib.bib148)], Term Frequency-Inverse Document Frequency (TF-IDF) [[95](https://arxiv.org/html/2309.11356v2#bib.bib95), [11](https://arxiv.org/html/2309.11356v2#bib.bib11)] as seen in rare-event studies involves fine-tuning these techniques to capture the unique, low-frequency signals that often characterize rare events. Furthermore, statistical methods ranging from simple calculations like mean, median, variance, skewness, kurtosis, and standard deviation to more advanced measures like spectral energy and frequency entropy derived from time and frequency domain analyses have been used in rare event prediction in the financial domain [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [72](https://arxiv.org/html/2309.11356v2#bib.bib72)]. In rare-event prediction, feature importance methods require special attention to ensure that features relevant to rare occurrences are not overlooked. Methods like Gini importance [[33](https://arxiv.org/html/2309.11356v2#bib.bib33), [86](https://arxiv.org/html/2309.11356v2#bib.bib86), [8](https://arxiv.org/html/2309.11356v2#bib.bib8)] or XGBoost’s accuracy and cover measurements [[33](https://arxiv.org/html/2309.11356v2#bib.bib33)] have been adapted to emphasize features that, while they might contribute minimally to overall model accuracy, are critical in predicting rare events. For example, the application of Mel-frequency Cepstral Coefficients (MFCC) in rare-event contexts goes beyond traditional audio signal processing, aiming to capture subtle acoustic variations that could signify the occurrence of an event, as demonstrated in studies focusing on audio-based rare-event prediction [[99](https://arxiv.org/html/2309.11356v2#bib.bib99), [149](https://arxiv.org/html/2309.11356v2#bib.bib149)].
Intrinsic methods, such as attention mechanisms, are particularly valuable in rare-event prediction due to their ability to dynamically focus on the most relevant features across different scales and dimensions. For instance, multi-variate and multi-scale attention methods have been specifically adapted to enhance the prediction of rare events by focusing on spatial-temporal features that are often subtle and dispersed [[37](https://arxiv.org/html/2309.11356v2#bib.bib37)]. Additionally, decision trees, which are intrinsically capable of feature selection, have been adapted to handle the unique distributional characteristics of rare-event datasets, ensuring that the rare but critical branches of the tree are not pruned away during model training [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [17](https://arxiv.org/html/2309.11356v2#bib.bib17)].

#### 3.3.2 Analyzing feature selection approaches with data modalities, rarity groups, and downstream tasks

![Refer to caption](x6.png)

Figure [6](https://arxiv.org/html/2309.11356v2#S3.F6 "Figure 6 ‣ 3.3.2 Analyzing feature selection approaches with data modalities, rarity groups, and downstream tasks ‣ 3.3 Feature Selection (FS) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction") illustrates the intricate association between feature selection methods, modality variations, and rarity groups within the context of rare event prediction, as analyzed across the reviewed papers. Regarding numerical-based feature selection, feature importance, and intrinsic-based methods are independent of the rarity groups. Correlation-based feature selection, wrapper-based, filter-based, and intrinsic methods have been used with data belonging to extremely-rare and very-rare groups. TF-IDF and MFCC-based feature extraction has been used with frequently-rare data. Decision tree-based intrinsic methods were utilized with very-rare image datasets. Likewise, in data cleaning, most data processing methods support classification tasks; some have been used in clustering, regression, simulation, and forecasting research.

### 3.4 Sampling (SL)

Sampling techniques in ML are essential methods for selecting a subset of data from larger datasets and are often used to tackle challenges like class imbalance and large data sizes while enhancing computational efficiency. The application of rare event data showcases their effectiveness in significantly improving performance in mining rare events, highlighting their importance in research contributions. This subsection examines various approaches for sampling and discusses their application to various data modalities, rarity levels, and downstream tasks (See Figure LABEL:fig:sampling and discussion in Section [3.4.2](https://arxiv.org/html/2309.11356v2#S3.SS4.SSS2 "3.4.2 Analyzing data sampling approaches with data modalities, rarity groups, and downstream tasks ‣ 3.4 Sampling (SL) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction")).

#### 3.4.1 Approaches to sampling

Sampling techniques used in rare event prediction can be categorized into basic and advanced methods based on the complexity and sophistication of the sampling approaches utilized.

I) Basic sampling techniques:
These techniques seek to address the issue of class imbalance by eliminating instances from the majority class or increasing the minority class by duplicating minority class samples. Random minority oversampling (ROS) and random majority undersampling (RUS) are the most frequent basic sampling strategies. In ROS, instances of the minority class are replicated randomly in the dataset, while in RUS, occurrences of the majority class are randomly eliminated from the dataset. In rare event-based research, many studies have used ROS and RUS methods to achieve a more balanced class distribution [[10](https://arxiv.org/html/2309.11356v2#bib.bib10), [11](https://arxiv.org/html/2309.11356v2#bib.bib11), [12](https://arxiv.org/html/2309.11356v2#bib.bib12), [13](https://arxiv.org/html/2309.11356v2#bib.bib13), [14](https://arxiv.org/html/2309.11356v2#bib.bib14), [15](https://arxiv.org/html/2309.11356v2#bib.bib15)]. Some researchers have combined sampling techniques with clustering models [[18](https://arxiv.org/html/2309.11356v2#bib.bib18), [14](https://arxiv.org/html/2309.11356v2#bib.bib14)] and ensemble learning methods [[38](https://arxiv.org/html/2309.11356v2#bib.bib38)] to improve predictive performance. Some others have applied randomly over/under-sampling in conjunction with advanced architectures, such as the Siamese CNN [[29](https://arxiv.org/html/2309.11356v2#bib.bib29)], to enhance rare event detection. Additionally, statistical sampling methods, like Hoeffding bounds, have been employed in rare event learning using associative rules and higher-order statistics [[146](https://arxiv.org/html/2309.11356v2#bib.bib146)]. Even though basic sampling has been extensively used, it has several limitations. The drawback of the oversampling method is that it leads to overfitting since the model learns from the same duplicated samples repeatedly. Undersampling eliminates lots of data that could have been utilized to train the model and improve its accuracy.

II) Advanced sampling techniques:
Going beyond basic random adjustments, advanced sampling techniques utilize intelligent mechanisms that consider the distribution of data points and the nuance of learning specific examples, resulting in greater effectiveness for handling complex, imbalanced datasets.

1) Synthetic minority oversampling technique (SMOTE):
SMOTE is a popular advanced sampling technique used in ML to address class imbalances. It generates new synthetic minority cases by extrapolating from existing minority instances, and it considers the difference between a sample and its closest neighbor to create synthetic examples. SMOTE has been adopted in various rare event-related use cases implementing different modeling techniques [[11](https://arxiv.org/html/2309.11356v2#bib.bib11), [91](https://arxiv.org/html/2309.11356v2#bib.bib91), [150](https://arxiv.org/html/2309.11356v2#bib.bib150), [21](https://arxiv.org/html/2309.11356v2#bib.bib21), [87](https://arxiv.org/html/2309.11356v2#bib.bib87)]. It has been observed that logistic regression combined with SMOTE produces good results in detecting Look-Alike-Sound-Alike (LASA) cases in textual data [[11](https://arxiv.org/html/2309.11356v2#bib.bib11)], but it can be computationally expensive. Adaptive swarm balancing algorithms [[91](https://arxiv.org/html/2309.11356v2#bib.bib91)] and dynamic churn prediction frameworks [[150](https://arxiv.org/html/2309.11356v2#bib.bib150)] have also utilized SMOTE for rare event prediction in imbalanced datasets.
Additionally, Borderline-SMOTE is a variation that selectively applies SMOTE to minority instances on the border of the minority decision region, yielding effective results in mining tasks [[10](https://arxiv.org/html/2309.11356v2#bib.bib10)]. While SMOTE has been adopted in various rare event use cases, it has a significant drawback due to the arbitrary generation of synthetic data. As a result, the class boundaries between the majority class and the minority class in the synthetic data may appear significantly different from those in the original dataset, potentially deviating from the actual distribution of the minority class.

2) Adaptive synthetic sampling (ADASYN):
ADASYN [[151](https://arxiv.org/html/2309.11356v2#bib.bib151)] is a method that solves the issue with SMOTE by following a weighted distribution for minority classes according to their level of difficulty in learning. It generates synthetic observations of the harder-to-learn minority samples compared to the easier-to-learn minority samples and adaptively shifts the decision boundary towards the harder-to-learn samples. Asraf et al. [[21](https://arxiv.org/html/2309.11356v2#bib.bib21)] have used ADASYN with the XGBoost model in rare event modeling in highrisk WWD roadway segment identification.

3) Similarity majority undersampling (SMUTE): SMUTE [[16](https://arxiv.org/html/2309.11356v2#bib.bib16)] is an undersampling technique that distinguishes between the majority and minority class samples by considering the cosine similarity between each and its neighboring minority class samples. SMUTE works by calculating similarity scores between each majority class sample and a given number of minority class samples, then selecting a subset of majority class samples with the highest percentage of high similarity scores based on a specified undersampling rate.

4) Edited nearest neighbor (ENN):
ENN [[152](https://arxiv.org/html/2309.11356v2#bib.bib152)] is an undersampling method that reduces noise and refines decision boundaries in imbalanced datasets. ENN eliminates samples whose class labels differ from most of their nearest neighbors, resulting in a dataset with smoother decision boundaries and reduced noise. It has been applied with SMOTE oversampling to create a balanced, noise-free training dataset for improved rare event prediction [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [21](https://arxiv.org/html/2309.11356v2#bib.bib21)].

5) Neighborhood cleaning rule (NCL): NCL is an undersampling technique that removes redundant, noisy, or ambiguous samples. NCL employs the ENN technique to remove the data samples [[153](https://arxiv.org/html/2309.11356v2#bib.bib153)]. However, compared with ENN, NCL has the additional benefit of removing redundant instances based on feature space similarity [[16](https://arxiv.org/html/2309.11356v2#bib.bib16)].

6) NearMiss (NM):
NM [[154](https://arxiv.org/html/2309.11356v2#bib.bib154)] is a technique that uses distance measures of majority class samples to minority class samples in selecting samples. When two points from different classes are located very close to one another in a distribution, this algorithm eliminates the data point from the larger class to balance the distribution. NearMiss-2(NM2), a variation of NM, has been used in rare event prediction data processing [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [21](https://arxiv.org/html/2309.11356v2#bib.bib21)].

7) One-sided selection (OSS):
OSS is an undersampling technique that balances imbalanced datasets by removing redundant and noisy majority-class instances. It combines the use of Tomek Links to identify ambiguous points on the class boundary with the Condensed Nearest Neighbor (CNN) rule [[155](https://arxiv.org/html/2309.11356v2#bib.bib155)] to eliminate distant redundant examples from the majority class, resulting in a minimally consistent subset without compromising model performance. OSS has the advantage over other methods of intelligently locating and removing redundant and noisy majority class instances by utilizing Tomek Links and the CNN rule. This makes a more refined and representative subset of the majority class. OSS has been employed in various rare event studies to address the high imbalance in learning tasks [[42](https://arxiv.org/html/2309.11356v2#bib.bib42), [17](https://arxiv.org/html/2309.11356v2#bib.bib17), [38](https://arxiv.org/html/2309.11356v2#bib.bib38), [10](https://arxiv.org/html/2309.11356v2#bib.bib10)].

8) Cluster-based oversampling (CBO):
CBO employs resampling by clustering each class’s training data separately and then performing random oversampling, cluster by cluster [[13](https://arxiv.org/html/2309.11356v2#bib.bib13), [10](https://arxiv.org/html/2309.11356v2#bib.bib10)]. CBO employs separate clustering of each class’s training data followed by random oversampling within each cluster, enhancing the representation of rare classes in a balanced manner. The advantage of this method is that it considers both between-class and within-class imbalances and then oversamples the data to correct both imbalances simultaneously.

9) Time series subsampling:
This involves selecting a subset of time points from the original to create a new, shorter, and more balanced time series [[156](https://arxiv.org/html/2309.11356v2#bib.bib156), [157](https://arxiv.org/html/2309.11356v2#bib.bib157)]. The difference between subsampling and time series subsampling is that subsampling is a general term that refers to selecting a random subset of data points, while time series subsampling is a specific type of subsampling used for time series data involving the selection of a subset of time points from a time series. In industrial-based research on machinery fault diagnosis [[78](https://arxiv.org/html/2309.11356v2#bib.bib78)], subsampling of time series has been performed to consider the balanced time series length of normal and different bearing fault types. Further, time series subsampling reduces the computational cost of analyzing long time series and aids in training ML models.

10) Stratified sampling:
It is a general sampling technique that divides the dataset into subgroups (strata) based on the target variable’s classes and then randomly samples from each stratum to ensure representation of all classes. To sample normal and different bearing fault failure types, [[78](https://arxiv.org/html/2309.11356v2#bib.bib78)] uses stratified techniques to represent these subgroups in the final dataset properly.

11) Audio data sampling:
Data framing has been used as a data sampling technique for audio data [[99](https://arxiv.org/html/2309.11356v2#bib.bib99)] that involves converting the audio data into a machine-readable format to fix the audio file sampling (frame) rate. In this method, the audio data is divided into frames, each representing a segment of the audio signal sampled at a specific rate. The total number of frames can be calculated by multiplying the sampling rate by the audio file’s duration.

12) Uncertainty sampling:
It is a data sampling technique widely used in active learning, particularly relevant to rare event prediction research. It entails selecting instances from a dataset based on the uncertainty or low confidence of their predicted labels by a ML model. The goal is to prioritize sampling data points for which the model lacks certainty in its predictions. This approach is valuable in scenarios where labeling data is resource-intensive, such as in rare event prediction [[116](https://arxiv.org/html/2309.11356v2#bib.bib116)], as it allows researchers to actively select the most informative instances for annotation, thereby improving the model’s performance with limited labeled data.

13) Choice-based or endogenous sampling:
Endogenous sampling is a rare event prediction method that selects samples based on the dependent variable (y) rather than the independent variable (X). It aims to obtain a representative sample that accurately reflects the distribution of rare events in the dataset, addressing the imbalance issue and improving predictive performance. Choice-based or endogenous stratified sampling has been used in various applications, such as Light Detection and Ranging (LIDAR) maps, where non-landslide cells are sampled one to five times more than landslide cells to achieve better representation [[70](https://arxiv.org/html/2309.11356v2#bib.bib70)]. Variations of regression models have been experimented with in endogenous sampling approaches [[84](https://arxiv.org/html/2309.11356v2#bib.bib84)].

#### 3.4.2 Analyzing data sampling approaches with data modalities, rarity groups, and downstream tasks

![Refer to caption](x7.png)

Investigating sampling approaches, we analyzed 116 rare event prediction-related papers based on sampling approach, modality, and rarity group and observed their interrelationships as depicted in Figure LABEL:fig:sampling. It’s seen that basic data sampling techniques are independent of rarity groups. They are used for numeric, image, and audio data and have been utilized in studies focusing on downstream tasks such as clustering, classification, and forecasting. The advanced sampling technique, SMOTE, is independent of rarity groups and is used in classification-based studies and numerical data. Most of the advanced sampling techniques, like SMUTE, ENN, NCL, NM, OSS, CBO, and time series subsampling, have been widely used in rare event prediction research with numeric datasets of varying rarity levels and are mostly used in classification-based studies. Uncertainty sampling and choice-based or endogenous sampling methods have been employed for regression and forecasting tasks across different rarity groups.

### 3.5 Feature Engineering (FE)

Feature engineering involves converting raw data into a relevant feature set for modeling. It aims to extract meaningful information from the dataset and present it in a format suitable for the learning algorithm. This subsection examines various approaches to feature engineering in rare-event contexts. Then, it discusses their application to various data modalities, rarity levels, and downstream tasks (See Figure [8](https://arxiv.org/html/2309.11356v2#S3.F8 "Figure 8 ‣ 3.5.2 Analyzing feature engineering approaches with data modalities, rarity groups, and downstream tasks ‣ 3.5 Feature Engineering (FE) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction") and discussion in Section [3.5.2](https://arxiv.org/html/2309.11356v2#S3.SS5.SSS2 "3.5.2 Analyzing feature engineering approaches with data modalities, rarity groups, and downstream tasks ‣ 3.5 Feature Engineering (FE) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction")).

#### 3.5.1 Approaches to Feature engineering

Investigating rare events, we will review commonly utilized techniques in feature engineering as outlined below.

I) Data augmentation:
In rare event prediction, data augmentation has been important in addressing the scarcity of event samples and the challenges of imbalanced datasets. Unlike general applications, where augmentation primarily boosts generalization, in rare events, it must be tailored to enhance model sensitivity to infrequent patterns. For instance, in the pulp-and-paper industry, a tailored augmentation method combined with Fast Fourier Transform (FFT) has been used to enrich time series data with synthetic rare event examples, improving fault detection [[32](https://arxiv.org/html/2309.11356v2#bib.bib32), [12](https://arxiv.org/html/2309.11356v2#bib.bib12)]. Wasserstein GANs (WGANs) have been adapted for rare event prediction by generating high-quality synthetic data to address data scarcity and improve training stability, while Conditional GANs (CGANs) are used in creating targeted samples based on specific attributes or conditions [[87](https://arxiv.org/html/2309.11356v2#bib.bib87)]. Apart from those, standard image-based augmentation techniques, like cropping, have been applied to create additional training samples while preserving the critical spatial features necessary for detecting rare mineral deposits, predicting mineral prospectivity, and identifying scene changes [[158](https://arxiv.org/html/2309.11356v2#bib.bib158), [29](https://arxiv.org/html/2309.11356v2#bib.bib29), [159](https://arxiv.org/html/2309.11356v2#bib.bib159)].
These targeted approaches ensure that models remain sensitive to rare events, improving their prediction accuracy.

II) Data discretization:
Data discretization can manage the unique challenges of skewed class distributions and high-dimensional data. Converting continuous data into discrete categories can help highlight the rare event patterns that might otherwise be overshadowed in continuous data [[8](https://arxiv.org/html/2309.11356v2#bib.bib8)], simplifying the model’s ability to detect and learn from rare occurrences. Standard techniques like optimal binning have allowed supervised discretization that preserves essential characteristics of rare event data, ensuring that the model captures the subtle distinctions necessary for accurate prediction [[72](https://arxiv.org/html/2309.11356v2#bib.bib72), [39](https://arxiv.org/html/2309.11356v2#bib.bib39)].

III) Feature scaling:
In rare event research, standardization has been used to align feature distributions with a standard normal distribution, which helps in mitigating the effect of class imbalance by ensuring that features do not disproportionately influence the model based on their scale [[78](https://arxiv.org/html/2309.11356v2#bib.bib78), [73](https://arxiv.org/html/2309.11356v2#bib.bib73), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [99](https://arxiv.org/html/2309.11356v2#bib.bib99)]. Normalization rescales values to a uniform range, preventing features with larger ranges from dominating the model’s learning process [[30](https://arxiv.org/html/2309.11356v2#bib.bib30)]. Both techniques ensure the model’s sensitivity to minority class features.

IV) Dimensionality reduction:
Dimensionality reduction is more than a standard preprocessing step; it is essential for rare event prediction as it addresses the high dimensionality and complexity inherent in rare event datasets. Principal Component Analysis (PCA) reduces the feature space by preserving the most informative components that distinguish rare events from normal occurrences [[79](https://arxiv.org/html/2309.11356v2#bib.bib79), [77](https://arxiv.org/html/2309.11356v2#bib.bib77), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [99](https://arxiv.org/html/2309.11356v2#bib.bib99), [87](https://arxiv.org/html/2309.11356v2#bib.bib87), [30](https://arxiv.org/html/2309.11356v2#bib.bib30), [8](https://arxiv.org/html/2309.11356v2#bib.bib8), [37](https://arxiv.org/html/2309.11356v2#bib.bib37), [20](https://arxiv.org/html/2309.11356v2#bib.bib20), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [99](https://arxiv.org/html/2309.11356v2#bib.bib99)]. Focusing on the principal components, PCA filters out noise and highlights subtle signals, which aids models in learning from imbalanced data.

V) Fourier transform:
This is widely used in signal processing and image processing. It transforms a time-domain signal into its frequency-domain representation, allowing for analyzing and manipulating the signal’s frequency components. In rare event prediction, it can be used to uncover frequency-domain characteristics that reveal rare occurrences often hidden by time-domain noise. In audio-based rare event research, [[99](https://arxiv.org/html/2309.11356v2#bib.bib99)], fourier transform is applied to convert audio waveforms into the frequency domain for further analysis.

#### 3.5.2 Analyzing feature engineering approaches with data modalities, rarity groups, and downstream tasks

Figure [8](https://arxiv.org/html/2309.11356v2#S3.F8 "Figure 8 ‣ 3.5.2 Analyzing feature engineering approaches with data modalities, rarity groups, and downstream tasks ‣ 3.5 Feature Engineering (FE) ‣ 3 Data Processing Approaches ‣ A Comprehensive Survey on Rare Event Prediction") presents a comprehensive overview of the association between feature engineering techniques, data modality, and rarity groups in the context of rare event prediction, as examined from the reviewed papers. It is observed that classification has been the primary focus of the majority of research. Standardization, normalization, and dimensionality reduction have been applied to numerical and audio data, whereas data augmentation has been used on numerical and image data. Discretization and encoding have been used with numerical data, and in addition to classification, these techniques focus on clustering tasks. It is noted that none of the feature engineering techniques are rarity-independent; hence, each of the techniques seems to perform well with specific rarity groups.

![Refer to caption](x8.png)

|  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Data processing approach | Papers | Rarity group | |  | | --- | | Downstream | | tasks | | Modality | |  | | --- | | Dataset Type | |
| 1. Data Cleaning | | | | | |
| Data sifting | [[103](https://arxiv.org/html/2309.11356v2#bib.bib103), [83](https://arxiv.org/html/2309.11356v2#bib.bib83), [137](https://arxiv.org/html/2309.11356v2#bib.bib137), [136](https://arxiv.org/html/2309.11356v2#bib.bib136)] | R1, R2, R3, R4 | FT, CL, CF | N | RE, DE |
| Data filtering | [[27](https://arxiv.org/html/2309.11356v2#bib.bib27), [138](https://arxiv.org/html/2309.11356v2#bib.bib138), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [83](https://arxiv.org/html/2309.11356v2#bib.bib83)] | R1, R2, R3, R4 | CF | N | RE |
| Imputation | |  | | --- | | [[37](https://arxiv.org/html/2309.11356v2#bib.bib37), [10](https://arxiv.org/html/2309.11356v2#bib.bib10), [15](https://arxiv.org/html/2309.11356v2#bib.bib15), [103](https://arxiv.org/html/2309.11356v2#bib.bib103), [127](https://arxiv.org/html/2309.11356v2#bib.bib127)], | | [[8](https://arxiv.org/html/2309.11356v2#bib.bib8), [86](https://arxiv.org/html/2309.11356v2#bib.bib86), [88](https://arxiv.org/html/2309.11356v2#bib.bib88), [108](https://arxiv.org/html/2309.11356v2#bib.bib108), [8](https://arxiv.org/html/2309.11356v2#bib.bib8), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)] | | R1, R2, R3, R4 | |  | | --- | | CL, CF, FT | | N | |  | | --- | | RE, DE, SIY | |
| Noise removal | [[8](https://arxiv.org/html/2309.11356v2#bib.bib8), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [146](https://arxiv.org/html/2309.11356v2#bib.bib146), [21](https://arxiv.org/html/2309.11356v2#bib.bib21)]] | R2, R3, R4 | CL, CF | N | RE, DE |
| Textual summary generation | [[95](https://arxiv.org/html/2309.11356v2#bib.bib95), [11](https://arxiv.org/html/2309.11356v2#bib.bib11)] | R4 | CF | TX | RE |
| Text conversions | [[95](https://arxiv.org/html/2309.11356v2#bib.bib95)] | R4 | CF | TX | RE |
| Stemming and lemmatization | [[95](https://arxiv.org/html/2309.11356v2#bib.bib95)] | R4 | CF | TX | RE |
| Image processing techniques | [[17](https://arxiv.org/html/2309.11356v2#bib.bib17)] | R2 | CF | I | RE |
| 2. Feature Selection | | | | | |
| |  | | --- | | Correlation-based | | feature selection | | [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [100](https://arxiv.org/html/2309.11356v2#bib.bib100), [22](https://arxiv.org/html/2309.11356v2#bib.bib22)] | R1, R1, R3 | CF, SM | N | |  | | --- | | RE, DE, SIY | |
| |  | | --- | | Wrapper-based methods | | [[77](https://arxiv.org/html/2309.11356v2#bib.bib77)] | R4 | CL | N | RE |
| |  | | --- | | Statistical measures | | |  | | --- | | [[20](https://arxiv.org/html/2309.11356v2#bib.bib20), [15](https://arxiv.org/html/2309.11356v2#bib.bib15), [86](https://arxiv.org/html/2309.11356v2#bib.bib86), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [30](https://arxiv.org/html/2309.11356v2#bib.bib30), [79](https://arxiv.org/html/2309.11356v2#bib.bib79)], | | [[95](https://arxiv.org/html/2309.11356v2#bib.bib95), [11](https://arxiv.org/html/2309.11356v2#bib.bib11)] | | R1, R2, R4 | CF, FT | N, TX | RE, SIY |
| |  | | --- | | Gini feature importance and | | XGBoost accuracy and | | cover measurement | | [[38](https://arxiv.org/html/2309.11356v2#bib.bib38), [8](https://arxiv.org/html/2309.11356v2#bib.bib8), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [86](https://arxiv.org/html/2309.11356v2#bib.bib86), [8](https://arxiv.org/html/2309.11356v2#bib.bib8)] | R1, R2, R3, R4 | CL, CF | N | RE |
| |  | | --- | | MFCC-based feature extraction | | [[99](https://arxiv.org/html/2309.11356v2#bib.bib99), [149](https://arxiv.org/html/2309.11356v2#bib.bib149)] | R4 | CF | A | RE |
| |  | | --- | | Intrinsic-based feature selection | | |  | | --- | | [[37](https://arxiv.org/html/2309.11356v2#bib.bib37), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [17](https://arxiv.org/html/2309.11356v2#bib.bib17)] | | R1, R2, R3, R4 | CF, RG | N, I | RE, DE |
| 3. Sampling | | | | | |
| |  | | --- | | Basic sampling | | i) ROS & RUS | | |  | | --- | | [[11](https://arxiv.org/html/2309.11356v2#bib.bib11), [18](https://arxiv.org/html/2309.11356v2#bib.bib18), [14](https://arxiv.org/html/2309.11356v2#bib.bib14), [95](https://arxiv.org/html/2309.11356v2#bib.bib95), [12](https://arxiv.org/html/2309.11356v2#bib.bib12)], | | [[41](https://arxiv.org/html/2309.11356v2#bib.bib41), [29](https://arxiv.org/html/2309.11356v2#bib.bib29), [15](https://arxiv.org/html/2309.11356v2#bib.bib15), [146](https://arxiv.org/html/2309.11356v2#bib.bib146), [18](https://arxiv.org/html/2309.11356v2#bib.bib18), [38](https://arxiv.org/html/2309.11356v2#bib.bib38)] | | R1, R2, R3, R4 | CF, FT, CL | N, I, TX | RE, DE |
| Advanced sampling |  |  |  |  |  |
| i) SMOTE | [[11](https://arxiv.org/html/2309.11356v2#bib.bib11), [38](https://arxiv.org/html/2309.11356v2#bib.bib38), [95](https://arxiv.org/html/2309.11356v2#bib.bib95), [91](https://arxiv.org/html/2309.11356v2#bib.bib91), [150](https://arxiv.org/html/2309.11356v2#bib.bib150), [100](https://arxiv.org/html/2309.11356v2#bib.bib100), [10](https://arxiv.org/html/2309.11356v2#bib.bib10)] | R1, R2, R3, R4 | CF | N, TX | RE, DE |
| ii) ADASYN | [[21](https://arxiv.org/html/2309.11356v2#bib.bib21)] | R3 | CF | N | RE, DE |
| iii) SMUTE | [[16](https://arxiv.org/html/2309.11356v2#bib.bib16)] | R3, R4 | CF | N | |  | | --- | | RE, DE, SIY | |
| iv) ENN | [[152](https://arxiv.org/html/2309.11356v2#bib.bib152), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [21](https://arxiv.org/html/2309.11356v2#bib.bib21)] | R3, R4 | CF | N | |  | | --- | | RE, DE, SIY | |
| v) NCL | [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [21](https://arxiv.org/html/2309.11356v2#bib.bib21)] | R3, R4 | CF | N | |  | | --- | | RE, DE, SIY | |
| vi) NearMiss | [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [21](https://arxiv.org/html/2309.11356v2#bib.bib21)] | R3, R4 | CF | N | |  | | --- | | RE, DE, SIY | |
| vii) OSS | [[42](https://arxiv.org/html/2309.11356v2#bib.bib42), [17](https://arxiv.org/html/2309.11356v2#bib.bib17), [38](https://arxiv.org/html/2309.11356v2#bib.bib38), [10](https://arxiv.org/html/2309.11356v2#bib.bib10)] | R2, R3 | CF | N, I | RE, DE |
| viii) CBO | [[13](https://arxiv.org/html/2309.11356v2#bib.bib13), [10](https://arxiv.org/html/2309.11356v2#bib.bib10)] | R2, R3, R4 | CL, CF | N | DE |
| ix) Time series subsampling | |  | | --- | | [[156](https://arxiv.org/html/2309.11356v2#bib.bib156), [157](https://arxiv.org/html/2309.11356v2#bib.bib157), [78](https://arxiv.org/html/2309.11356v2#bib.bib78)] | | R3, R4 | CF | N | RE |
| x) Stratified sampling | [[78](https://arxiv.org/html/2309.11356v2#bib.bib78)] | R4 | CF | N | RE |
| xi) Data framing | [[99](https://arxiv.org/html/2309.11356v2#bib.bib99)] | R4 | CF | A | RE |
| xii) Uncertainty sampling | [[116](https://arxiv.org/html/2309.11356v2#bib.bib116)] | R1 | FT, SM | N | SIY |
| |  | | --- | | xiii) Choice-based / | | endogenous sampling | | [[84](https://arxiv.org/html/2309.11356v2#bib.bib84), [70](https://arxiv.org/html/2309.11356v2#bib.bib70)] | R1,R2,R3, R4 | CF | N, I | RE |
| 4. Feature Engineering | | | | | |
| Data augmentation | [[87](https://arxiv.org/html/2309.11356v2#bib.bib87), [21](https://arxiv.org/html/2309.11356v2#bib.bib21), [32](https://arxiv.org/html/2309.11356v2#bib.bib32), [12](https://arxiv.org/html/2309.11356v2#bib.bib12), [158](https://arxiv.org/html/2309.11356v2#bib.bib158), [29](https://arxiv.org/html/2309.11356v2#bib.bib29), [159](https://arxiv.org/html/2309.11356v2#bib.bib159)] | R1, R3 | |  | | --- | | CF, RG, CL | | N, I | RE |
| Data discretization | [[8](https://arxiv.org/html/2309.11356v2#bib.bib8), [10](https://arxiv.org/html/2309.11356v2#bib.bib10), [72](https://arxiv.org/html/2309.11356v2#bib.bib72), [39](https://arxiv.org/html/2309.11356v2#bib.bib39)] | R2, R4 | CL, CF | N | RE, DE |
| Encoding | [[78](https://arxiv.org/html/2309.11356v2#bib.bib78)] | R4 | CL, CF | N | RE |
| Feature scaling | |  | | --- | | [[78](https://arxiv.org/html/2309.11356v2#bib.bib78), [73](https://arxiv.org/html/2309.11356v2#bib.bib73), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [99](https://arxiv.org/html/2309.11356v2#bib.bib99), [30](https://arxiv.org/html/2309.11356v2#bib.bib30), [24](https://arxiv.org/html/2309.11356v2#bib.bib24), [25](https://arxiv.org/html/2309.11356v2#bib.bib25)] | | R1, R2, R4 | CL, CF | N, A | RE, DE |
| Dimensionality reduction | |  | | --- | | [[79](https://arxiv.org/html/2309.11356v2#bib.bib79), [77](https://arxiv.org/html/2309.11356v2#bib.bib77), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [99](https://arxiv.org/html/2309.11356v2#bib.bib99), [87](https://arxiv.org/html/2309.11356v2#bib.bib87), [30](https://arxiv.org/html/2309.11356v2#bib.bib30)], | | [[8](https://arxiv.org/html/2309.11356v2#bib.bib8), [37](https://arxiv.org/html/2309.11356v2#bib.bib37), [20](https://arxiv.org/html/2309.11356v2#bib.bib20), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [99](https://arxiv.org/html/2309.11356v2#bib.bib99)] | | R1, R2, R4 | |  | | --- | | RG, CF, FT | | N,A | RE, DE |
| Fourier transform | [[99](https://arxiv.org/html/2309.11356v2#bib.bib99)] | R4 | CL | A | RE |

|  |
| --- |
| Downstream |
| tasks |

|  |
| --- |
| Dataset Type |

|  |
| --- |
| [[37](https://arxiv.org/html/2309.11356v2#bib.bib37), [10](https://arxiv.org/html/2309.11356v2#bib.bib10), [15](https://arxiv.org/html/2309.11356v2#bib.bib15), [103](https://arxiv.org/html/2309.11356v2#bib.bib103), [127](https://arxiv.org/html/2309.11356v2#bib.bib127)], |
| [[8](https://arxiv.org/html/2309.11356v2#bib.bib8), [86](https://arxiv.org/html/2309.11356v2#bib.bib86), [88](https://arxiv.org/html/2309.11356v2#bib.bib88), [108](https://arxiv.org/html/2309.11356v2#bib.bib108), [8](https://arxiv.org/html/2309.11356v2#bib.bib8), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)] |

|  |
| --- |
| CL, CF, FT |

|  |
| --- |
| RE, DE, SIY |

|  |
| --- |
| Correlation-based |
| feature selection |

|  |
| --- |
| RE, DE, SIY |

|  |
| --- |
| Wrapper-based methods |

|  |
| --- |
| Statistical measures |

|  |
| --- |
| [[20](https://arxiv.org/html/2309.11356v2#bib.bib20), [15](https://arxiv.org/html/2309.11356v2#bib.bib15), [86](https://arxiv.org/html/2309.11356v2#bib.bib86), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [30](https://arxiv.org/html/2309.11356v2#bib.bib30), [79](https://arxiv.org/html/2309.11356v2#bib.bib79)], |
| [[95](https://arxiv.org/html/2309.11356v2#bib.bib95), [11](https://arxiv.org/html/2309.11356v2#bib.bib11)] |

|  |
| --- |
| Gini feature importance and |
| XGBoost accuracy and |
| cover measurement |

|  |
| --- |
| MFCC-based feature extraction |

|  |
| --- |
| Intrinsic-based feature selection |

|  |
| --- |
| [[37](https://arxiv.org/html/2309.11356v2#bib.bib37), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [17](https://arxiv.org/html/2309.11356v2#bib.bib17)] |

|  |
| --- |
| Basic sampling |
| i) ROS & RUS |

|  |
| --- |
| [[11](https://arxiv.org/html/2309.11356v2#bib.bib11), [18](https://arxiv.org/html/2309.11356v2#bib.bib18), [14](https://arxiv.org/html/2309.11356v2#bib.bib14), [95](https://arxiv.org/html/2309.11356v2#bib.bib95), [12](https://arxiv.org/html/2309.11356v2#bib.bib12)], |
| [[41](https://arxiv.org/html/2309.11356v2#bib.bib41), [29](https://arxiv.org/html/2309.11356v2#bib.bib29), [15](https://arxiv.org/html/2309.11356v2#bib.bib15), [146](https://arxiv.org/html/2309.11356v2#bib.bib146), [18](https://arxiv.org/html/2309.11356v2#bib.bib18), [38](https://arxiv.org/html/2309.11356v2#bib.bib38)] |

|  |
| --- |
| RE, DE, SIY |

|  |
| --- |
| RE, DE, SIY |

|  |
| --- |
| RE, DE, SIY |

|  |
| --- |
| RE, DE, SIY |

|  |
| --- |
| [[156](https://arxiv.org/html/2309.11356v2#bib.bib156), [157](https://arxiv.org/html/2309.11356v2#bib.bib157), [78](https://arxiv.org/html/2309.11356v2#bib.bib78)] |

|  |
| --- |
| xiii) Choice-based / |
| endogenous sampling |

|  |
| --- |
| CF, RG, CL |

|  |
| --- |
| [[78](https://arxiv.org/html/2309.11356v2#bib.bib78), [73](https://arxiv.org/html/2309.11356v2#bib.bib73), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [99](https://arxiv.org/html/2309.11356v2#bib.bib99), [30](https://arxiv.org/html/2309.11356v2#bib.bib30), [24](https://arxiv.org/html/2309.11356v2#bib.bib24), [25](https://arxiv.org/html/2309.11356v2#bib.bib25)] |

|  |
| --- |
| [[79](https://arxiv.org/html/2309.11356v2#bib.bib79), [77](https://arxiv.org/html/2309.11356v2#bib.bib77), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [99](https://arxiv.org/html/2309.11356v2#bib.bib99), [87](https://arxiv.org/html/2309.11356v2#bib.bib87), [30](https://arxiv.org/html/2309.11356v2#bib.bib30)], |
| [[8](https://arxiv.org/html/2309.11356v2#bib.bib8), [37](https://arxiv.org/html/2309.11356v2#bib.bib37), [20](https://arxiv.org/html/2309.11356v2#bib.bib20), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [99](https://arxiv.org/html/2309.11356v2#bib.bib99)] |

|  |
| --- |
| RG, CF, FT |

∗ N-Numeric, TX-Textual, I-Image, A-Audio, T-Time series, FT-Forecasting, CL-Clustering, CF-Classification, RG-Regression, RE-Naturally rare, DE-Derived, SIY-Simulated/Synthetic

In this section, we explored four primary techniques, data cleaning, feature selection, sampling, and feature engineering, as approaches to data processing. Data cleaning methods help to ensure data quality and remove noise, while feature selection techniques aim to identify the most relevant features for rare event prediction. Sampling approaches assist in selecting a subset of datasets and address issues with class imbalance and large dataset sizes. Feature engineering methods effectively extract meaningful information and represent the data more discriminatively.
We also examined their application in various data modalities, rarity levels, and downstream tasks. It is observed that many studies utilize standard data processing techniques common to general ML research. This highlights the need to investigate standardized approaches adapted to rare events to assist the unique challenges of classification, clustering, regression, and forecasting. Notably, numerical data cleaning techniques like data sifting, filtering, imputation, and noise removal are commonly used, while feature selection methods such as correlation-based, wrapper-based, and filter-based techniques are applied across different rarity groups, with classification tasks being the primary focus across all methodologies.

## 4 Algorithmic Approaches

Algorithmic approaches are pivotal in any ML pipeline and contribute significantly in making informed and effective decisions. They provide mathematical models for varied use cases centered around downstream tasks like classification, clustering, forecasting, regression, and simulation. Firstly, this section analyzes a subset of algorithmic approaches utilized in the literature on rare events. Then, each approach would be examined concerning several algorithmic indicators. Finally, each approach would be analyzed with the data modality, rarity groups, data processing techniques, and downstream tasks.

![Refer to caption](x9.png)

### 4.1 Significance of algorithmic approaches

Algorithmic approaches provide tools and modeling techniques to analyze and interpret complex datasets, enabling the identification of patterns, relationships, and key factors and predicting events of significant importance. We categorize algorithmic approaches in rare event research into five major groups: Supervised classification and regression, Clustering, Statistical modeling, Meta-heuristic optimization, and Advanced learning methods as shown in Figure [9](https://arxiv.org/html/2309.11356v2#S4.F9 "Figure 9 ‣ 4 Algorithmic Approaches ‣ A Comprehensive Survey on Rare Event Prediction").

### 4.2 Supervised Classification and Regression Methods

Classification and regression are two fundamental supervised learning tasks in machine learning aimed at predicting the output of a target variable based on input features. The key difference lies in the type of target variable they handle. Classification algorithms are used to predict discrete values such as gender, binary labels (true/false), or categories like spam or not spam, while regression algorithms are employed for predicting continuous values like price, salary, or age. In rare event prediction, various techniques have been used, including threshold methods, tree-based classification, one-class learning, cost-sensitive methods, non-parametric classification algorithms, kernel-based methods, and inference/rule-based methods.

#### 4.2.1 Threshold methods

These approaches set a specific threshold for classifying data instances into rare or non-rare classes based on a pre-defined criterion, rendering them well-suited for modeling rare events. Instances above the threshold are considered rare, while those below it are classified as non-rare. Existing research has employed probabilistic statistical methods such as Logistic Regression (LR), Naive Bayes classifiers (NB), and Neural Networks (NN) that generate a score or probability threshold. If the categorization is binary, this probability is subsequently transferred and mapped to a binary mapping, like malignant or benign, spam or not spam, normal or abnormal.
In rare event prediction, certain researchers have utilized LR as a fundamental base classifier [[11](https://arxiv.org/html/2309.11356v2#bib.bib11), [70](https://arxiv.org/html/2309.11356v2#bib.bib70)], while others have explored various adaptations and variations, including incorporating regularization techniques [[20](https://arxiv.org/html/2309.11356v2#bib.bib20), [21](https://arxiv.org/html/2309.11356v2#bib.bib21)] and utilizing weighting methods [[84](https://arxiv.org/html/2309.11356v2#bib.bib84)]. It was observed that the conventional LR encountered convergence challenges in scenarios with limited sample sizes or rare events in the data. To address this issue, an alternative approach known as Firth’s logistic regression [[160](https://arxiv.org/html/2309.11356v2#bib.bib160)] has been employed, wherein a penalty is added to the log-likelihood function of the LR model. Several studies that include rare events [[22](https://arxiv.org/html/2309.11356v2#bib.bib22), [21](https://arxiv.org/html/2309.11356v2#bib.bib21)] have demonstrated improved performance using Firth’s logistic regression. LR methods are easy to implement, interpretable, and suitable for rare event prediction with small sample sizes.

Bayes classifiers and neural networks are also threshold-based models utilized in rare event prediction research. Bayes classifiers have been used in rare event prediction by [[88](https://arxiv.org/html/2309.11356v2#bib.bib88), [16](https://arxiv.org/html/2309.11356v2#bib.bib16)]. Studies have explored the application of neural networks, including Deep neural networks [[127](https://arxiv.org/html/2309.11356v2#bib.bib127), [111](https://arxiv.org/html/2309.11356v2#bib.bib111), [16](https://arxiv.org/html/2309.11356v2#bib.bib16)], Convolutional Neural Networks (CNN) [[111](https://arxiv.org/html/2309.11356v2#bib.bib111), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [158](https://arxiv.org/html/2309.11356v2#bib.bib158), [159](https://arxiv.org/html/2309.11356v2#bib.bib159), [73](https://arxiv.org/html/2309.11356v2#bib.bib73)], Multi-Layer Perceptron (MLP) [[99](https://arxiv.org/html/2309.11356v2#bib.bib99)], Autoencoders [[21](https://arxiv.org/html/2309.11356v2#bib.bib21), [25](https://arxiv.org/html/2309.11356v2#bib.bib25), [26](https://arxiv.org/html/2309.11356v2#bib.bib26)], CNN-based autoencoders [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [24](https://arxiv.org/html/2309.11356v2#bib.bib24), [25](https://arxiv.org/html/2309.11356v2#bib.bib25), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [27](https://arxiv.org/html/2309.11356v2#bib.bib27)], Long Short-Term Memory (LSTM) autoencoders [[24](https://arxiv.org/html/2309.11356v2#bib.bib24), [27](https://arxiv.org/html/2309.11356v2#bib.bib27)] in various applications such as mineral prospectivity prediction [[158](https://arxiv.org/html/2309.11356v2#bib.bib158), [159](https://arxiv.org/html/2309.11356v2#bib.bib159)], black-swan event prediction [[23](https://arxiv.org/html/2309.11356v2#bib.bib23)], rare sound classification in audio forensics [[99](https://arxiv.org/html/2309.11356v2#bib.bib99)] and manufacturing failure prediction [[24](https://arxiv.org/html/2309.11356v2#bib.bib24), [27](https://arxiv.org/html/2309.11356v2#bib.bib27)]. LSTMs can preserve temporal properties of rare events by capturing sequential dependencies and managing long-term relationships through gating mechanisms. NB offers robustness, probabilistic inference, and flexibility compared to LR, while NN excels in representation learning and scalability. But, both risks being affected by the insufficient sample size in rare events [[22](https://arxiv.org/html/2309.11356v2#bib.bib22)].

#### 4.2.2 Tree-based classification methods

These are supervised ML methods that partition the training data into subsets using a series of conditional statements. These splits create a tree-like structure, each representing a logical test on a specific feature. The final model comprises multiple such trees, enabling predictions and offering insights into the relationships within the data. Tree-based classification methods are widely used in rare event prediction due to their ability to handle complex and non-linear relationships in the data. Random Forest (RF) [[93](https://arxiv.org/html/2309.11356v2#bib.bib93), [111](https://arxiv.org/html/2309.11356v2#bib.bib111), [86](https://arxiv.org/html/2309.11356v2#bib.bib86), [87](https://arxiv.org/html/2309.11356v2#bib.bib87), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [88](https://arxiv.org/html/2309.11356v2#bib.bib88), [30](https://arxiv.org/html/2309.11356v2#bib.bib30)] and Boosted Classification Trees, such as XGBoost [[33](https://arxiv.org/html/2309.11356v2#bib.bib33), [87](https://arxiv.org/html/2309.11356v2#bib.bib87), [21](https://arxiv.org/html/2309.11356v2#bib.bib21), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)], are popular choices in this group. In rare event prediction, researchers have applied these models to estimate the probability of rare events like suicide attempts [[93](https://arxiv.org/html/2309.11356v2#bib.bib93)], APS failures [[86](https://arxiv.org/html/2309.11356v2#bib.bib86), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)], and manufacturing faults [[87](https://arxiv.org/html/2309.11356v2#bib.bib87), [33](https://arxiv.org/html/2309.11356v2#bib.bib33)]. Data augmentation techniques have been used to enhance the performance of tree-based models further, optimizing parameters to avoid overfitting [[21](https://arxiv.org/html/2309.11356v2#bib.bib21)]. Tree-based methods also benefit from handling overfitting using random subsets during model training. However, they can be challenging to interpret due to the large number of trees in the model, making it difficult to understand the combined effect of all trees. Despite this limitation, tree-based classification methods are valuable tools for capturing complex relationships and making accurate predictions in rare event prediction tasks.

#### 4.2.3 Cost-sensitive learning

These methods consider the costs associated with prediction errors and other potential costs during the training of a ML model. Instead of maximizing accuracy, the focus shifts to minimizing overall misclassification costs, where each class or instance is assigned a specific misclassification cost. False negatives (misses) are assigned higher costs than false positives (false alarms). Two main approaches to cost-sensitive learning are decision trees and weighting. Decision trees employ a parameterized threshold mechanism to dynamically adjust the decision boundary of the classifier, making them suitable for modeling rare events in a manner that is nuanced and contextually adaptable [[11](https://arxiv.org/html/2309.11356v2#bib.bib11), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [17](https://arxiv.org/html/2309.11356v2#bib.bib17), [18](https://arxiv.org/html/2309.11356v2#bib.bib18)]. On the other hand, weighting assigns higher weights to the minority class to penalize misclassifications of the rare class [[106](https://arxiv.org/html/2309.11356v2#bib.bib106), [38](https://arxiv.org/html/2309.11356v2#bib.bib38)]. Researchers have explored cost-sensitive learning methods with various classifiers such as Logistic Regression, Random Forest, and Support Vector Machines. Weighted Random Forest and AdaClassWeight are examples of algorithms that adaptively adjust the weights of the rare class to address the imbalanced data problem [[106](https://arxiv.org/html/2309.11356v2#bib.bib106), [38](https://arxiv.org/html/2309.11356v2#bib.bib38)]. Overall, it’s observed that cost-sensitive learning methods offer effective solutions for handling imbalanced datasets and predicting rare events in various real-world applications.

#### 4.2.4 Non-parametric classification algorithms

They are ML algorithms that do not make explicit assumptions about the data’s underlying probability distribution or functional form. Unlike parametric classification algorithms, which assume a specific functional form (linear or polynomial) and estimate parameters, non-parametric algorithms learn directly from the data without assuming any specific model structure. K-nearest neighbors (k-NN) is an instance adopted by [[88](https://arxiv.org/html/2309.11356v2#bib.bib88)] in APS failure prediction. They are often more flexible and can capture complex relationships in the data, which becomes more advantageous in rare event prediction [[73](https://arxiv.org/html/2309.11356v2#bib.bib73), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)].

#### 4.2.5 Kernal-Based Methods

They are ML algorithms that transform data into a higher-dimensional space using kernel functions, enabling them to capture non-linear relationships and solve downstream tasks like classification and regression. Support Vector Machines (SVMs) are a well-known kernel technique that outperforms neural networks in some rare event research, particularly for small to medium datasets demanding explainable outcomes. SVM-based kernels can disambiguate hard-to-classify rare event datasets using soft-margins [[146](https://arxiv.org/html/2309.11356v2#bib.bib146), [15](https://arxiv.org/html/2309.11356v2#bib.bib15), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)]. One-class SVM has been used in evaluating large sample sizes in unsupervised learning environments [[20](https://arxiv.org/html/2309.11356v2#bib.bib20), [146](https://arxiv.org/html/2309.11356v2#bib.bib146)]. In imbalanced healthcare data, L.SVM (Support Vector Machine with Linear kernel) and R.SVM (Support Vector Machine with Radial kernel) have been used as base classifiers for incident detection [[11](https://arxiv.org/html/2309.11356v2#bib.bib11)]. SVMs have also been applied in importance sampling for rare event detection to identify multiple failure regions and estimate the structural failure probability of rare events [[121](https://arxiv.org/html/2309.11356v2#bib.bib121)]. Granular SVM (GSVM) is a variation of SVM that combines statistical learning theory and granular computing theory [[161](https://arxiv.org/html/2309.11356v2#bib.bib161)]. In [[66](https://arxiv.org/html/2309.11356v2#bib.bib66)], GSVM has been used with under-sampling techniques to improve efficacy by locally reducing redundant data through parallel processing. Rare event weighted kernel logistic regression (RE-WKLR) [[67](https://arxiv.org/html/2309.11356v2#bib.bib67)] is an algorithmic SVM enhancement optimized for unbalanced and rare event data. It offers the advantages of weighing, bias correction, and the strength of kernel approaches, especially when datasets are imbalanced or not linearly separable.

#### 4.2.6 Inference/Rule-Based Methods

This class of algorithms focuses on deriving knowledge and insights from data through explicit if-then rules.
In rare event literature, these methods can be Bayesian methods, Inductive algorithms, Two-phase rule induction, Knowledge-based and human interaction-based approaches, and Association rule mining. These methods are applicable to rare event prediction due to their ability to leverage expert domain knowledge, create human-readable rules, and provide interpretable outputs, which are crucial for understanding the decision-making process in scenarios where data scarcity and complexity make traditional modeling approaches challenging.

i) Bayesian methods:
These are statistical techniques that use prior information on a certain population, and they rely on Bayes’ theorem to update the probability of a hypothesis based on new evidence. Bayesian methods offer multiple benefits, including handling incomplete and noisy data, understanding causal relationships between variables, and integrating domain expertise and data through Bayesian networks. Utilizing Bayesian methods, as demonstrated in [[103](https://arxiv.org/html/2309.11356v2#bib.bib103)], along with Bayesian networks, results in superior performance in forecasting daily ozone states by incorporating expert knowledge and historical data. Bayesian networks also prove useful for extreme rare event identification, as shown in [[72](https://arxiv.org/html/2309.11356v2#bib.bib72)], where the Jaynes inferential approach is used for feature engineering and optimal binning, leading to reduced features and improved identification of relevant diagnostic features.

ii) Inductive algorithms:
In rare event prediction, some researchers have proposed various inductive bias methods such as Maximum Specificity Bias (MSB) and Instance-Based Learning (IBL). MSB aims to discover specific rules for individual training examples, enhancing the performance of small disjuncts but leading to worse overall performance. IBL, also known as lazy learning, is a ML approach that focuses on the local generalization of instances based on similarity measures. 1-NN (1-Nearest Neighbor) algorithm is a type of IBL used in [[17](https://arxiv.org/html/2309.11356v2#bib.bib17)] along with one-sided selection in detecting oil spills. This study shows promising results for improving accuracy in small disjuncts, but even this method has not been able to provide conclusive evidence.

iii) Two-phase rule induction:
Is a ML technique that involves a two-step process for inducing rules from data and is commonly used in data mining and knowledge discovery. The PNrule algorithm [[162](https://arxiv.org/html/2309.11356v2#bib.bib162)] is a two-phase rule induction approach that involves the discovery of positive rules (P-rules) to predict the presence of a class and negative rules (N-rules) to predict its absence. P-rules are learned in the first phase to capture the most positive cases while maintaining a respectable false positive rate. N-rules are discovered in the second phase to reduce false positives introduced by the union of P-rules while maintaining an acceptable detection rate. The study by [[107](https://arxiv.org/html/2309.11356v2#bib.bib107)] uses the PNRule method to address the challenge of maximizing recall and precision in rare event prediction. By creating rules with great accuracy, the initial phase concentrates on recall. The second phase concentrates on precision by utilizing rules that eliminate false positives from the records covered by the first phase.

iv) Knowledge-based and human interaction-based approaches:
Knowledge and human interactions have been researched and explored in predicting rare events like international conflicts, wars, coups, revolutions, massive economic depressions, and economic crises [[163](https://arxiv.org/html/2309.11356v2#bib.bib163)]. Knowledge-driven models are particularly useful in areas with limited exploration data or that have not been extensively studied. They rely on the expertise of professionals to make decisions, but they can be subjected to limitations due to their subjective nature. Some instances of using knowledge include modeling knowledge from geological experts in mineral prospectivity prediction [[158](https://arxiv.org/html/2309.11356v2#bib.bib158), [159](https://arxiv.org/html/2309.11356v2#bib.bib159)] and using expert knowledge like chemical equations and hypotheses in solar flare forecasting [[103](https://arxiv.org/html/2309.11356v2#bib.bib103)]. Nevertheless, while these approaches may demonstrate efficacy when applied to small and straightforward systems, their effectiveness might be low when dealing with more complex and diverse systems [[100](https://arxiv.org/html/2309.11356v2#bib.bib100)].

v) Association rule mining:
These utilize basic If/Then statements to reveal relationships between independent relational or other data repositories. [[164](https://arxiv.org/html/2309.11356v2#bib.bib164)] adopts an association rule mining approach to identify frequently occurring patterns preceding target rare events, which are subsequently integrated into a rule-based predictive model. ‘PREVENT’ is a general purpose inter-transaction association rules mining algorithm that uses inter-transactional patterns to predict rare events in transactional databases [[39](https://arxiv.org/html/2309.11356v2#bib.bib39)]. FP-Growth, a state-of-the-art algorithm for classical association rule mining, is utilized there. The algorithm’s computational cost is minimal as it involves limited scans of the database, making it well-suited for the requirements of rare event prediction.

### 4.3 Semi-supervised and Unsupervised methods

Semi-supervised methods for rare event prediction leverage a combination of labeled data from the rare event class and unlabeled data from normal instances, aiming to improve predictive accuracy and generalization. In contrast, unsupervised methods rely solely on unlabeled data, focusing on identifying patterns or anomalies that deviate significantly from the norm, which can be indicative of rare events.

#### 4.3.1 Clustering methods

Clustering is a type of unsupervised learning where samples are categorized based on their resemblance to neighboring data points. Several clustering-based methods have been employed in the literature on rare events. Distance-based unsupervised methods such as Random Forest (RF) clustering, Partition Around Medoids (PAM), K-means, and hierarchical clustering are commonly used [[165](https://arxiv.org/html/2309.11356v2#bib.bib165), [26](https://arxiv.org/html/2309.11356v2#bib.bib26)]. For instance, hierarchical clustering has been used to detect abnormal production behaviors in the paper manufacturing industry [[26](https://arxiv.org/html/2309.11356v2#bib.bib26)]. K-means clustering has been utilized to identify rare change events based on the distance between common features [[29](https://arxiv.org/html/2309.11356v2#bib.bib29)]. Additionally, clustering-based undersampling techniques, like Clustering Large Applications (CLARA) [[18](https://arxiv.org/html/2309.11356v2#bib.bib18)] and Classification using lOcal clusterinG (COG) algorithms [[14](https://arxiv.org/html/2309.11356v2#bib.bib14)], have aimed to generate balanced sub-classes for classification. In some cases, ensembles of clustering methods, such as RF Clustering and PAM, are been combined to optimize the clustering process [[8](https://arxiv.org/html/2309.11356v2#bib.bib8)]. Moreover, the combination of nearest neighbor and Balanced Iterative Reducing and Clustering using Hierarchies (BIRCH) clustering with dynamic markov chains has shown promise in detecting rare events in spatiotemporal environments using sensor and traffic data [[83](https://arxiv.org/html/2309.11356v2#bib.bib83)].

#### 4.3.2 One-class learning

One-class learning is an unsupervised learning strategy used for extremely skewed class distributions, with the classifier being trained exclusively on data from one class. It can be considered a semi-supervised or unsupervised approach, depending on how it is implemented and the specific context of its application.
Adaptation of one-class classification algorithms for imbalanced classification has been researched in early studies, and they have also been employed in rare event prediction. HIPPO (i.e.,a classification method based on Hippocampus functioning) [[166](https://arxiv.org/html/2309.11356v2#bib.bib166)] is a standard method where only the rare class is learned, and Repeated Incremental Pruning to Produce Error Reduction (RIPPER) [[167](https://arxiv.org/html/2309.11356v2#bib.bib167)] is a standard method where the algorithm selects the majority class as its default class and learns the rules for detecting the minority class. Hamaguchi et al. [[29](https://arxiv.org/html/2309.11356v2#bib.bib29)] have proposed a variational autoencoder-based method to learn disentangled representations on only low-cost negative samples of image data. As a result, rare events were detected as outliers. Some autoencoder models we presented under threshold methods also do intersect with this group, such as [[24](https://arxiv.org/html/2309.11356v2#bib.bib24)], which was trained only on normal samples, and [[21](https://arxiv.org/html/2309.11356v2#bib.bib21)] where samples of rare events were used for training.
The advantages of one-class classifiers come at the cost of ignoring all available information about one class; consequently, this solution should be approached cautiously, as it may not be suitable for all circumstances.

### 4.4 Statistical Modeling

Statistical models are algorithms that apply statistics and mathematics concepts to generate a representation of data, which is then analyzed to determine any relationships or discover insights. Statistical approaches like Autoregressive Integrated Moving Average (ARIMA) modeling and Vector Autoregression (VAR) have been used in rare event prediction [[20](https://arxiv.org/html/2309.11356v2#bib.bib20), [27](https://arxiv.org/html/2309.11356v2#bib.bib27)]. ARIMA is an autoregressive statistical model that predicts future values based on past values. Alestra et al. have utilized ARIMA modeling separately for each aircraft to predict the degradation behavior over time [[20](https://arxiv.org/html/2309.11356v2#bib.bib20)]. Vector Autoregression follows a stochastic process model that captures linear interdependencies among multiple time series using a linear function of past values of each variable. [[27](https://arxiv.org/html/2309.11356v2#bib.bib27)] explored VAR in evaluating the LSTM-Autoencoder model developed. ARIMA and VAR models effectively capture time-based dependencies and sequential (temporal) data patterns, which enhances prediction accuracy and addresses challenges in predicting rare events based on past observations. The Gumbel copula function is a statistical modeling technique in copula-based algorithms utilized in rare event research. Copulas are mathematical functions used to model the dependence structure between random variables. They describe the joint distribution of variables by connecting their marginal distributions. The Gumbel copula function, specifically, is a type of copula that is based on the Gumbel distribution. It is commonly used to model extreme-value dependence, making it suitable for applications involving rare events or extremes. It captures the tail dependence between variables, which is vital in scenarios where the behavior of variables in the extreme tails is of interest [[126](https://arxiv.org/html/2309.11356v2#bib.bib126)].

### 4.5 Meta-Heuristic Optimization

Meta-heuristic algorithms are optimization techniques for solving complex problems by iteratively exploring and exploiting the search space to find near-optimal solutions [[168](https://arxiv.org/html/2309.11356v2#bib.bib168)]. These algorithms, such as particle swarm optimization and the bat algorithm, have been applied to improve efficiency and scalability on large imbalanced healthcare data, [[91](https://arxiv.org/html/2309.11356v2#bib.bib91)], and genetic algorithms have been utilized for learning to predict rare events in categorical time series data [[3](https://arxiv.org/html/2309.11356v2#bib.bib3)]. Additionally, evolutionary ensemble algorithms have shown promise in enhancing the identification rate of minority classes in rare event-based imbalanced datasets [[169](https://arxiv.org/html/2309.11356v2#bib.bib169)]. These algorithms would excel in rare event prediction due to their ability to efficiently explore complex search spaces and adaptively exploit the underlying patterns and structures in imbalanced datasets.

### 4.6 Advanced Learning Methods

Recently, advanced learning methods like Attention-based mechanisms, Markov methods, Active learning, and Meta-learning have emerged to tackle the challenges posed by rare event datasets. These approaches strive to enhance rare event predictive capability by leveraging temporal dependencies, probabilistic modeling, and selective data labeling.

#### 4.6.1 Attention-based mechanisms

Attention mechanisms enable the model to selectively concentrate on important input elements for accurate predictions while disregarding less relevant parts. This has gained attention in rare event research as well. For instance, Liu et al. proposed a fault diagnosis approach using one-dimensional CNN, Gated Recurrent Unit (GRU), and attention mechanisms, combined with knowledge graphs, to achieve more precise predictions in bearing fault detection [[78](https://arxiv.org/html/2309.11356v2#bib.bib78)]. Xu et al. have utilized attention-based-LSTM and Extra-Tree models for fault mode and severity prediction based on bearing datasets, while Ravindranath et al. introduced the M2NN architecture with an attention mechanism for post-traumatic seizure detection, demonstrating its effectiveness in finding unusual seizures in EEG data [[79](https://arxiv.org/html/2309.11356v2#bib.bib79), [37](https://arxiv.org/html/2309.11356v2#bib.bib37)]. Kulkarni and team utilized soft-attention CNN for rare marker event detection and localization in well-logs [[170](https://arxiv.org/html/2309.11356v2#bib.bib170)]. Attention-based mechanisms preserve temporal properties by selectively focusing on important time steps, capturing both short- and long-term dependencies in sequential data. These methods have proven useful in handling rare event detection tasks, such as anomaly detection in manufacturing, rare disease diagnosis, and identifying specific rare occurrences in multiple domains.

#### 4.6.2 Markov methods

Markov models represent the Markov property, which asserts that the prediction of an outcome depends only on information about the current state and is independent of the previous sequence of events. Extensible Markov Models (EMM) and Monte Carlo methods are among the markov methods adopted in rare event literature. These models capture the time-dependent behavior by modeling transitions between states over time and, hence, can address the temporal properties inherent in rare events.

I) Extensible markov models (EMM):
Extensible Markov Models (EMM) are a dynamic variation of traditional static Markov models. They excel in modeling spatiotemporal data and have proven to help predict spatiotemporal events, including rare occurrences, by capturing spatial, temporal, and unusual event transitions [[171](https://arxiv.org/html/2309.11356v2#bib.bib171)]. Meng et al. [[83](https://arxiv.org/html/2309.11356v2#bib.bib83)] introduced an approach that combines clustering and EMM for rare event detection in spatiotemporal data, particularly sensor and traffic data. Their contribution lies in modeling the transitions between rare and typical events using EMM, effectively detecting rare occurrences.

II) Monte carlo methods:
Monte carlo methods, also called Monte carlo simulations, are probabilistic mathematical techniques that estimate the possible outcomes of uncertain events. In rare event estimation, Monte Carlo methods have been applied to estimate model uncertainty, such as using Monte Carlo Dropout to create multiple predictions and measuring the standard deviation of detection depths as a proxy for uncertainty [[170](https://arxiv.org/html/2309.11356v2#bib.bib170)]. Additionally, they have been used to predict rare events using trajectory data and unscheduled aircraft maintenance actions [[172](https://arxiv.org/html/2309.11356v2#bib.bib172), [173](https://arxiv.org/html/2309.11356v2#bib.bib173), [22](https://arxiv.org/html/2309.11356v2#bib.bib22), [111](https://arxiv.org/html/2309.11356v2#bib.bib111), [121](https://arxiv.org/html/2309.11356v2#bib.bib121), [174](https://arxiv.org/html/2309.11356v2#bib.bib174), [175](https://arxiv.org/html/2309.11356v2#bib.bib175), [100](https://arxiv.org/html/2309.11356v2#bib.bib100)].

#### 4.6.3 Active learning

Active learning is a learning strategy that iteratively chooses the most instructive or uncertain instances from a pool of unlabeled data and asks an oracle (such as a human expert or a pre-existing labeled dataset) to annotate their labels [[176](https://arxiv.org/html/2309.11356v2#bib.bib176)]. Recent research efforts have been to predict rare events using active learning, exemplified by studies like [[122](https://arxiv.org/html/2309.11356v2#bib.bib122), [116](https://arxiv.org/html/2309.11356v2#bib.bib116)]. Dhulipala et al. [[122](https://arxiv.org/html/2309.11356v2#bib.bib122)] proposed a methodology for rare event simulation by combining active learning and multi-fidelity modeling, which leverages multiple levels of models’ fidelity (accuracy or complexity) to predict outcomes efficiently. Deep Neural Operators (DNOs), like DeepONet [[177](https://arxiv.org/html/2309.11356v2#bib.bib177)], are nonlinear operators created to handle systems with infinite dimensions, making them highly effective surrogate models for precisely representing extreme events. Pickering et al. [[116](https://arxiv.org/html/2309.11356v2#bib.bib116)] introduced a Bayesian-inspired framework based on active learning for DNOs, specifically designed for discovering and quantifying extreme events, focusing on uncertainty quantification.

#### 4.6.4 Meta learning

Meta-learning, or "learning to learn", is a ML approach focusing on training models to effectively adapt and generalize to new tasks or domains with minimal data. It can be applied to rare event prediction by training a model on various rare event scenarios. With limited data, it can rapidly adapt and accurately predict new and infrequent events. The advantage of meta-learning over other advanced learning approaches lies in its ability to dynamically adapt and integrate different predictive techniques, a faster and cheaper training process, thus enhancing the model’s generalization capability and performance across varied scenarios. Several studies [[136](https://arxiv.org/html/2309.11356v2#bib.bib136), [137](https://arxiv.org/html/2309.11356v2#bib.bib137), [149](https://arxiv.org/html/2309.11356v2#bib.bib149)] have looked at how meta-learning techniques can be used to improve failure prediction in different areas, such as large-scale computing systems and acoustic event detection, by dynamically combining base methods and improving accuracy in situations with few labeled data. While this existing research primarily focuses on failure prediction, it is worth noting that no prior studies have specifically addressed the prediction of rare events using meta-learning techniques.

### 4.7 Comparison of algorithmic approaches

Table [6](https://arxiv.org/html/2309.11356v2#S4.T6 "Table 6 ‣ 4.7 Comparison of algorithmic approaches ‣ 4 Algorithmic Approaches ‣ A Comprehensive Survey on Rare Event Prediction") offers a comparative analysis of the approaches discussed in the preceding section. We use 12 algorithmic indicators based on four major factors: computational efficiency, model analysis and understanding, data availability and model performance. Table [7](https://arxiv.org/html/2309.11356v2#S4.T7 "Table 7 ‣ 4.7 Comparison of algorithmic approaches ‣ 4 Algorithmic Approaches ‣ A Comprehensive Survey on Rare Event Prediction") analyses algorithmic approaches with rarity groups, downstream tasks, modalities, dataset types, and data processing tasks based on our reviewed papers. Predominantly, research has centered on classifying numeric rarity within real datasets, showcasing a blend of various data processing methodologies. Limited research is dedicated to alternative downstream tasks such as clustering, forecasting, simulation, and diverse modalities encompassing text, images and audio.

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Major Factor | Algorithmic Indicator | |  | | --- | | Supervised | | Classif. & Regress. | | |  | | --- | | Semi-Sup. | | & Un-Sup. | | |  | | --- | | Statistical | | Modeling | | |  | | --- | | Meta-Heuristic | | Optimization | | |  | | --- | | Advanced Learning | | Methods | |
| |  | | --- | | Computational | | Efficiency | | |  | | --- | | Training Time | | ✓\* | ✓ | ✓ | ✓ | ✓\* |
|  | |  | | --- | | Memory Usage | | ✓\* | ✓ | ✓ | ✓ | ✓\* |
|  | |  | | --- | | Model Size | | ✓\* | ✓ | ✓ | ✓ | ✓\* |
|  | |  | | --- | | Model Complexity | | ✓\* | ✓\* | ✓\* | ✓\* | ✓\* |
| |  | | --- | | Model Analysis | | & Understanding | | |  | | --- | | Feature Importance | | ✓ | - | ✓ | - | ✓ |
|  | |  | | --- | | Model Explainability | | ✓ | - | ✓ | - | ✓ |
|  | Interpretability | ✓ | - | - | - | ✓ |
| |  | | --- | | Data | | Availability | | |  | | --- | | Labeled Data | | ✓ | ✓ | ✓ | ✓ | ✓ |
|  | |  | | --- | | Unlabeled Data | | - | ✓ | - | - | ✓ |
| |  | | --- | | Model | | Performance | | |  | | --- | | Performance on Large Data | | ✓ | - | ✓ | ✓\* | ✓ |
|  | |  | | --- | | Ability to Handle Noise | | ✓ | - | ✓ | ✓\* | ✓ |
|  | Generalization | ✓ | ✓ | ✓ | ✓ | ✓ |

|  |
| --- |
| Supervised |
| Classif. & Regress. |

|  |
| --- |
| Semi-Sup. |
| & Un-Sup. |

|  |
| --- |
| Statistical |
| Modeling |

|  |
| --- |
| Meta-Heuristic |
| Optimization |

|  |
| --- |
| Advanced Learning |
| Methods |

|  |
| --- |
| Computational |
| Efficiency |

|  |
| --- |
| Training Time |

|  |
| --- |
| Memory Usage |

|  |
| --- |
| Model Size |

|  |
| --- |
| Model Complexity |

|  |
| --- |
| Model Analysis |
| & Understanding |

|  |
| --- |
| Feature Importance |

|  |
| --- |
| Model Explainability |

|  |
| --- |
| Data |
| Availability |

|  |
| --- |
| Labeled Data |

|  |
| --- |
| Unlabeled Data |

|  |
| --- |
| Model |
| Performance |

|  |
| --- |
| Performance on Large Data |

|  |
| --- |
| Ability to Handle Noise |

∗includes variability- depends on specific factors such as the problem domain, dataset, or implementation

Explanations of the considered algorithmic indicators are as follows, which we derived from the comprehensive analysis of the papers reviewed in this study.

Training time: Indicates the time required to train the model.

Memory usage: Reflects the memory required for training and storing the model.

Model size: Represents the model’s size in terms of parameters.

Feature importance: Refers to the ability of the algorithm to provide insights into the importance of different features.

Model explainability: Indicates the ease of understanding the model’s outcomes.

Generalization: Reflects the model’s ability to perform well on unseen or test data.

Model complexity: Describes the complexity of the model in terms of its structure or mathematical formulation.

Labeled data: Indicates that the algorithms require labeled data for training, which is typical for supervised and semi-supervised learning tasks.

Unlabeled data: Leverage unlabeled data in unsupervised learning scenarios.

Performance on large data: Suggests that the algorithms perform well on large datasets.

Ability to handle noise: Can handle noise effectively, making them robust to noisy data.

Interpretability: Enabling a better understanding of the model’s decision process.

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Algo. Group | |  | | --- | | Sub Algo. | | Group | | |  | | --- | | Algo. | | Approach | | Papers | |  | | --- | | Rarity | | Group | | |  | | --- | | Downstream | | Tasks | | Modality | |  | | --- | | Dataset | | Type | | |  | | --- | | Data Processing | | Tasks | |
| |  | | --- | | Supervised | | Classification/ | | Regression | | Methods | | |  | | --- | | Threshold | | methods | | |  | | --- | | Logistic | | regression | | |  | | --- | | [[70](https://arxiv.org/html/2309.11356v2#bib.bib70), [11](https://arxiv.org/html/2309.11356v2#bib.bib11), [22](https://arxiv.org/html/2309.11356v2#bib.bib22)], | | [[20](https://arxiv.org/html/2309.11356v2#bib.bib20), [84](https://arxiv.org/html/2309.11356v2#bib.bib84), [87](https://arxiv.org/html/2309.11356v2#bib.bib87)] | | R4, R1 | CF, FT | I,TX, N | RE, DE, SIY | SL, FE, DC, FS |
|  |  | |  | | --- | | Bayes & | | Neural networks | | |  | | --- | | [[111](https://arxiv.org/html/2309.11356v2#bib.bib111), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [99](https://arxiv.org/html/2309.11356v2#bib.bib99), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)], | | [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [158](https://arxiv.org/html/2309.11356v2#bib.bib158), [159](https://arxiv.org/html/2309.11356v2#bib.bib159), [73](https://arxiv.org/html/2309.11356v2#bib.bib73)] | | R1,R2,R3,R4 | CF | N, A, I | SI, RE, SIY | SL, FE, DC, FS |
|  |  | Autoencoders | |  | | --- | | [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [25](https://arxiv.org/html/2309.11356v2#bib.bib25), [26](https://arxiv.org/html/2309.11356v2#bib.bib26)], | | [[24](https://arxiv.org/html/2309.11356v2#bib.bib24), [27](https://arxiv.org/html/2309.11356v2#bib.bib27)] | | R1 | CF | N | RE | SL, FE, DC, FS |
|  | |  | | --- | | Tree-based | | classification | | methods | | Random Forest | |  | | --- | | [[93](https://arxiv.org/html/2309.11356v2#bib.bib93), [111](https://arxiv.org/html/2309.11356v2#bib.bib111), [86](https://arxiv.org/html/2309.11356v2#bib.bib86)], | | [[87](https://arxiv.org/html/2309.11356v2#bib.bib87), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)] | | R1, R2 | CF | N | RE | FE, DC, FS |
|  |  | |  | | --- | | Boosted | | Classification | | Trees(XGBoost, | | Adaboost) | | |  | | --- | | [[33](https://arxiv.org/html/2309.11356v2#bib.bib33), [87](https://arxiv.org/html/2309.11356v2#bib.bib87), [21](https://arxiv.org/html/2309.11356v2#bib.bib21)], | | [[88](https://arxiv.org/html/2309.11356v2#bib.bib88), [12](https://arxiv.org/html/2309.11356v2#bib.bib12)] | | R1, R2, R3 | CF | N | RE | SL, FE, DC, FS |
|  | |  | | --- | | Cost-sensitive | | learning | | |  | | --- | | Decision tree based | | cost-sensitive learning, | | Weighting based | | cost-sensitive learning | | [[11](https://arxiv.org/html/2309.11356v2#bib.bib11), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [106](https://arxiv.org/html/2309.11356v2#bib.bib106), [38](https://arxiv.org/html/2309.11356v2#bib.bib38)] | R1,R2,R3,R4 | CF | N, TX | RE, SIY, DE | SL, DC, FS |
|  | |  | | --- | | Non-parametric | | classification | | algorithms | | |  | | --- | | k-nearest neighbors | | (k-NN) | | [[88](https://arxiv.org/html/2309.11356v2#bib.bib88)] | R1, R2 | CF | N | RE | FE, DC |
|  | |  | | --- | | Kernal-based | | Methods | | SVM | |  | | --- | | [[146](https://arxiv.org/html/2309.11356v2#bib.bib146), [15](https://arxiv.org/html/2309.11356v2#bib.bib15), [20](https://arxiv.org/html/2309.11356v2#bib.bib20), [11](https://arxiv.org/html/2309.11356v2#bib.bib11)], | | [[121](https://arxiv.org/html/2309.11356v2#bib.bib121), [66](https://arxiv.org/html/2309.11356v2#bib.bib66), [67](https://arxiv.org/html/2309.11356v2#bib.bib67), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)] | | R1, R4, R2, R3 | |  | | --- | | CF, | | FT | | N, TX | RE, SIY | SL, DC, FS |
|  | |  | | --- | | Inference/ | | Rule-Based | | Methods | | |  | | --- | | Inference methods, | | More appropriate | | inductive bias, | | Two phase | | rule induction, | | Utilizing knowledge | | and human | | interactions, | | Association | | rule mining | | |  | | --- | | [[103](https://arxiv.org/html/2309.11356v2#bib.bib103), [72](https://arxiv.org/html/2309.11356v2#bib.bib72), [108](https://arxiv.org/html/2309.11356v2#bib.bib108)], | | [[178](https://arxiv.org/html/2309.11356v2#bib.bib178), [131](https://arxiv.org/html/2309.11356v2#bib.bib131), [17](https://arxiv.org/html/2309.11356v2#bib.bib17)], | | [[107](https://arxiv.org/html/2309.11356v2#bib.bib107), [163](https://arxiv.org/html/2309.11356v2#bib.bib163), [158](https://arxiv.org/html/2309.11356v2#bib.bib158)], | | [[159](https://arxiv.org/html/2309.11356v2#bib.bib159), [103](https://arxiv.org/html/2309.11356v2#bib.bib103), [39](https://arxiv.org/html/2309.11356v2#bib.bib39)] | | R1, R2, R3 | |  | | --- | | CF, | | FT | | N, I | RE, DE | SL, DC, FE |
| |  | | --- | | Semi-Supervised | | & Unsupervised | | Methods | | |  | | --- | | Random forest, PAM, K-means, | | Hierarchical, K-Nearest Neighbor, | | BIRCH, K-Medoids | | | |  | | --- | | [[8](https://arxiv.org/html/2309.11356v2#bib.bib8), [29](https://arxiv.org/html/2309.11356v2#bib.bib29), [14](https://arxiv.org/html/2309.11356v2#bib.bib14)], | | [[77](https://arxiv.org/html/2309.11356v2#bib.bib77), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [83](https://arxiv.org/html/2309.11356v2#bib.bib83), [18](https://arxiv.org/html/2309.11356v2#bib.bib18)] | | R1, R2, R3, R4 | CL | N, I | RE, DE | SL, FE, DC, FS |
| |  | | --- | | Statistical/ | | Time series | | Modeling | | |  | | --- | | Gumbel copula function | | | [[126](https://arxiv.org/html/2309.11356v2#bib.bib126)] | R1 | CF | N | RE | FE, DC, FS |
|  | |  | | --- | | ARIMA | | | [[20](https://arxiv.org/html/2309.11356v2#bib.bib20)] | R1 | |  | | --- | | CF, FT | | N | DE | FE, DC, FS |
|  | |  | | --- | | VAR | | | [[27](https://arxiv.org/html/2309.11356v2#bib.bib27)] | R1, R2, R3, R4 | CF | N | RE | FE, DC, FS |
| |  | | --- | | Meta- | | Heuristic | | Optimization | | |  | | --- | | Particle swarm optimization, | | Bat algorithm, | | Genetic algorithms, | | Evolutionary ensemble algorithms | | | [[91](https://arxiv.org/html/2309.11356v2#bib.bib91), [3](https://arxiv.org/html/2309.11356v2#bib.bib3), [169](https://arxiv.org/html/2309.11356v2#bib.bib169)] | R1, R2, R3, R4 | CF | N | RE , DE | SL |
| |  | | --- | | Advanced | | Learning | | Methods | | |  | | --- | | Attention-based mechanisms | | | [[78](https://arxiv.org/html/2309.11356v2#bib.bib78), [79](https://arxiv.org/html/2309.11356v2#bib.bib79), [37](https://arxiv.org/html/2309.11356v2#bib.bib37), [170](https://arxiv.org/html/2309.11356v2#bib.bib170)] | R1, R2, R3, R4 | CF | N | RE | SL, FE, DC, FS |
|  | |  | | --- | | Markov | | methods | | |  | | --- | | Extensible markov | | models, | | Monte carlo methods | | |  | | --- | | [[83](https://arxiv.org/html/2309.11356v2#bib.bib83), [172](https://arxiv.org/html/2309.11356v2#bib.bib172), [173](https://arxiv.org/html/2309.11356v2#bib.bib173)], | | [[22](https://arxiv.org/html/2309.11356v2#bib.bib22), [111](https://arxiv.org/html/2309.11356v2#bib.bib111), [121](https://arxiv.org/html/2309.11356v2#bib.bib121), [100](https://arxiv.org/html/2309.11356v2#bib.bib100)] | | R1, R2, R3, R4 | CF, FT, RG | N | |  | | --- | | RE, SIY, | | DE | | SL, FE, DC, FS |
|  | |  | | --- | | Active and Meta learning | | | |  | | --- | | [[122](https://arxiv.org/html/2309.11356v2#bib.bib122), [116](https://arxiv.org/html/2309.11356v2#bib.bib116), [136](https://arxiv.org/html/2309.11356v2#bib.bib136)], | | [[137](https://arxiv.org/html/2309.11356v2#bib.bib137), [149](https://arxiv.org/html/2309.11356v2#bib.bib149)] | | R1 | FT, SM, CF | N, I | SIY, RE | SL, FE, DC, FS |

|  |
| --- |
| Sub Algo. |
| Group |

|  |
| --- |
| Algo. |
| Approach |

|  |
| --- |
| Rarity |
| Group |

|  |
| --- |
| Downstream |
| Tasks |

|  |
| --- |
| Dataset |
| Type |

|  |
| --- |
| Data Processing |
| Tasks |

|  |
| --- |
| Supervised |
| Classification/ |
| Regression |
| Methods |

|  |
| --- |
| Threshold |
| methods |

|  |
| --- |
| Logistic |
| regression |

|  |
| --- |
| [[70](https://arxiv.org/html/2309.11356v2#bib.bib70), [11](https://arxiv.org/html/2309.11356v2#bib.bib11), [22](https://arxiv.org/html/2309.11356v2#bib.bib22)], |
| [[20](https://arxiv.org/html/2309.11356v2#bib.bib20), [84](https://arxiv.org/html/2309.11356v2#bib.bib84), [87](https://arxiv.org/html/2309.11356v2#bib.bib87)] |

|  |
| --- |
| Bayes & |
| Neural networks |

|  |
| --- |
| [[111](https://arxiv.org/html/2309.11356v2#bib.bib111), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [99](https://arxiv.org/html/2309.11356v2#bib.bib99), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)], |
| [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [158](https://arxiv.org/html/2309.11356v2#bib.bib158), [159](https://arxiv.org/html/2309.11356v2#bib.bib159), [73](https://arxiv.org/html/2309.11356v2#bib.bib73)] |

|  |
| --- |
| [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [25](https://arxiv.org/html/2309.11356v2#bib.bib25), [26](https://arxiv.org/html/2309.11356v2#bib.bib26)], |
| [[24](https://arxiv.org/html/2309.11356v2#bib.bib24), [27](https://arxiv.org/html/2309.11356v2#bib.bib27)] |

|  |
| --- |
| Tree-based |
| classification |
| methods |

|  |
| --- |
| [[93](https://arxiv.org/html/2309.11356v2#bib.bib93), [111](https://arxiv.org/html/2309.11356v2#bib.bib111), [86](https://arxiv.org/html/2309.11356v2#bib.bib86)], |
| [[87](https://arxiv.org/html/2309.11356v2#bib.bib87), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)] |

|  |
| --- |
| Boosted |
| Classification |
| Trees(XGBoost, |
| Adaboost) |

|  |
| --- |
| [[33](https://arxiv.org/html/2309.11356v2#bib.bib33), [87](https://arxiv.org/html/2309.11356v2#bib.bib87), [21](https://arxiv.org/html/2309.11356v2#bib.bib21)], |
| [[88](https://arxiv.org/html/2309.11356v2#bib.bib88), [12](https://arxiv.org/html/2309.11356v2#bib.bib12)] |

|  |
| --- |
| Cost-sensitive |
| learning |

|  |
| --- |
| Decision tree based |
| cost-sensitive learning, |
| Weighting based |
| cost-sensitive learning |

|  |
| --- |
| Non-parametric |
| classification |
| algorithms |

|  |
| --- |
| k-nearest neighbors |
| (k-NN) |

|  |
| --- |
| Kernal-based |
| Methods |

|  |
| --- |
| [[146](https://arxiv.org/html/2309.11356v2#bib.bib146), [15](https://arxiv.org/html/2309.11356v2#bib.bib15), [20](https://arxiv.org/html/2309.11356v2#bib.bib20), [11](https://arxiv.org/html/2309.11356v2#bib.bib11)], |
| [[121](https://arxiv.org/html/2309.11356v2#bib.bib121), [66](https://arxiv.org/html/2309.11356v2#bib.bib66), [67](https://arxiv.org/html/2309.11356v2#bib.bib67), [88](https://arxiv.org/html/2309.11356v2#bib.bib88)] |

|  |
| --- |
| CF, |
| FT |

|  |
| --- |
| Inference/ |
| Rule-Based |
| Methods |

|  |
| --- |
| Inference methods, |
| More appropriate |
| inductive bias, |
| Two phase |
| rule induction, |
| Utilizing knowledge |
| and human |
| interactions, |
| Association |
| rule mining |

|  |
| --- |
| [[103](https://arxiv.org/html/2309.11356v2#bib.bib103), [72](https://arxiv.org/html/2309.11356v2#bib.bib72), [108](https://arxiv.org/html/2309.11356v2#bib.bib108)], |
| [[178](https://arxiv.org/html/2309.11356v2#bib.bib178), [131](https://arxiv.org/html/2309.11356v2#bib.bib131), [17](https://arxiv.org/html/2309.11356v2#bib.bib17)], |
| [[107](https://arxiv.org/html/2309.11356v2#bib.bib107), [163](https://arxiv.org/html/2309.11356v2#bib.bib163), [158](https://arxiv.org/html/2309.11356v2#bib.bib158)], |
| [[159](https://arxiv.org/html/2309.11356v2#bib.bib159), [103](https://arxiv.org/html/2309.11356v2#bib.bib103), [39](https://arxiv.org/html/2309.11356v2#bib.bib39)] |

|  |
| --- |
| CF, |
| FT |

|  |
| --- |
| Semi-Supervised |
| & Unsupervised |
| Methods |

|  |
| --- |
| Random forest, PAM, K-means, |
| Hierarchical, K-Nearest Neighbor, |
| BIRCH, K-Medoids |

|  |
| --- |
| [[8](https://arxiv.org/html/2309.11356v2#bib.bib8), [29](https://arxiv.org/html/2309.11356v2#bib.bib29), [14](https://arxiv.org/html/2309.11356v2#bib.bib14)], |
| [[77](https://arxiv.org/html/2309.11356v2#bib.bib77), [26](https://arxiv.org/html/2309.11356v2#bib.bib26), [83](https://arxiv.org/html/2309.11356v2#bib.bib83), [18](https://arxiv.org/html/2309.11356v2#bib.bib18)] |

|  |
| --- |
| Statistical/ |
| Time series |
| Modeling |

|  |
| --- |
| Gumbel copula function |

|  |
| --- |
| ARIMA |

|  |
| --- |
| CF, FT |

|  |
| --- |
| VAR |

|  |
| --- |
| Meta- |
| Heuristic |
| Optimization |

|  |
| --- |
| Particle swarm optimization, |
| Bat algorithm, |
| Genetic algorithms, |
| Evolutionary ensemble algorithms |

|  |
| --- |
| Advanced |
| Learning |
| Methods |

|  |
| --- |
| Attention-based mechanisms |

|  |
| --- |
| Markov |
| methods |

|  |
| --- |
| Extensible markov |
| models, |
| Monte carlo methods |

|  |
| --- |
| [[83](https://arxiv.org/html/2309.11356v2#bib.bib83), [172](https://arxiv.org/html/2309.11356v2#bib.bib172), [173](https://arxiv.org/html/2309.11356v2#bib.bib173)], |
| [[22](https://arxiv.org/html/2309.11356v2#bib.bib22), [111](https://arxiv.org/html/2309.11356v2#bib.bib111), [121](https://arxiv.org/html/2309.11356v2#bib.bib121), [100](https://arxiv.org/html/2309.11356v2#bib.bib100)] |

|  |
| --- |
| RE, SIY, |
| DE |

|  |
| --- |
| Active and Meta learning |

|  |
| --- |
| [[122](https://arxiv.org/html/2309.11356v2#bib.bib122), [116](https://arxiv.org/html/2309.11356v2#bib.bib116), [136](https://arxiv.org/html/2309.11356v2#bib.bib136)], |
| [[137](https://arxiv.org/html/2309.11356v2#bib.bib137), [149](https://arxiv.org/html/2309.11356v2#bib.bib149)] |

∗N-Numeric, TX-Textual, I-Image, A-Audio, T-Time series, FT-Forecasting, CL-Clustering, CF-Classification, RG-Regression, RE-Naturally rare, DE-Derived, SIY-Simulated/Synthetic, SL-Sampling, FE-Feature engineering, DC-Data cleaning, FS-Feature selection

This section extensively examined different algorithmic approaches applied in rare event prediction.
The findings contribute to a better understanding of the diverse strategies employed in rare event prediction research and highlight the importance of selecting appropriate algorithms based on specific downstream tasks and modality requirements.

## 5 Evaluation Approaches

As ML models are developed, measuring the performance of every model is critical. Multiple evaluation metrics are employed in ML depending on the model and the results produced. This section focuses on the varied evaluation aspects used in rare event prediction. Firstly, we will highlight the significance of evaluation concerning rare event studies, followed by the evaluation methodologies and performance metrics used in related studies.

![Refer to caption](x10.png)

### 5.1 Significance of evaluation

Evaluation in rare event prediction research plays an integral role as it allows the assessment of the model’s performance in accurately identifying and predicting rare events. Due to the imbalanced nature of rare events, traditional evaluation metrics might not provide a comprehensive assessment, making it vital to employ specialized evaluation techniques that focus on both overall performance and the ability to detect rare occurrences. Figure [10](https://arxiv.org/html/2309.11356v2#S5.F10 "Figure 10 ‣ 5 Evaluation Approaches ‣ A Comprehensive Survey on Rare Event Prediction") depicts the evaluation approaches we identified in rare event literature grouped into their evaluation categories.

### 5.2 Evaluation Methodologies

Evaluation methodologies in rare event prediction research involve general and rare event-specific approaches. General methods find widespread application in diverse ML tasks, while rare event-specific metrics are tailored to address the unique challenges and requirements of predicting rare events.

#### 5.2.1 General evaluation methods

In rare event prediction research, various general evaluation methods are employed to assess the performance of algorithmic approaches (Table [8](https://arxiv.org/html/2309.11356v2#S5.T8 "Table 8 ‣ 5.2.1 General evaluation methods ‣ 5.2 Evaluation Methodologies ‣ 5 Evaluation Approaches ‣ A Comprehensive Survey on Rare Event Prediction")). Cross-validation techniques, such as K-Fold, Stratified K-Fold, and Leave-One-Out are commonly used for performance estimation [[15](https://arxiv.org/html/2309.11356v2#bib.bib15), [32](https://arxiv.org/html/2309.11356v2#bib.bib32), [38](https://arxiv.org/html/2309.11356v2#bib.bib38), [93](https://arxiv.org/html/2309.11356v2#bib.bib93), [87](https://arxiv.org/html/2309.11356v2#bib.bib87), [86](https://arxiv.org/html/2309.11356v2#bib.bib86), [150](https://arxiv.org/html/2309.11356v2#bib.bib150), [17](https://arxiv.org/html/2309.11356v2#bib.bib17), [11](https://arxiv.org/html/2309.11356v2#bib.bib11), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [73](https://arxiv.org/html/2309.11356v2#bib.bib73)]. Holdout evaluation through random splitting [[93](https://arxiv.org/html/2309.11356v2#bib.bib93), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [78](https://arxiv.org/html/2309.11356v2#bib.bib78), [12](https://arxiv.org/html/2309.11356v2#bib.bib12)] and time-based splitting [[103](https://arxiv.org/html/2309.11356v2#bib.bib103), [93](https://arxiv.org/html/2309.11356v2#bib.bib93), [100](https://arxiv.org/html/2309.11356v2#bib.bib100)] is utilized to create distinct train-test datasets, facilitating the process of model training and evaluation. Analysis with standard baselines, cost and error analysis, training time evaluation [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [23](https://arxiv.org/html/2309.11356v2#bib.bib23)], and ablation studies [[29](https://arxiv.org/html/2309.11356v2#bib.bib29)] for understanding individual components’ contributions are among the general evaluation approaches employed in this field.

|  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Evaluation methodology | Sub methods | Papers | Rarity group | Algorithmic approach | Modality | |  | | --- | | Type of the | | dataset | |
| Cross validation methods | K-Fold Cross-Validation | |  | | --- | | [[15](https://arxiv.org/html/2309.11356v2#bib.bib15), [38](https://arxiv.org/html/2309.11356v2#bib.bib38), [93](https://arxiv.org/html/2309.11356v2#bib.bib93), [87](https://arxiv.org/html/2309.11356v2#bib.bib87)], | | [[86](https://arxiv.org/html/2309.11356v2#bib.bib86), [150](https://arxiv.org/html/2309.11356v2#bib.bib150), [17](https://arxiv.org/html/2309.11356v2#bib.bib17), [95](https://arxiv.org/html/2309.11356v2#bib.bib95)] | | R1, R2 | |  | | --- | | SVM, Cost-sensitive | | learning, RF, LR, | | XGBoost, | | IBL | | N, I, TX | DE, RE |
|  | LOOCV , Stratified K-Fold | |  | | --- | | [[17](https://arxiv.org/html/2309.11356v2#bib.bib17), [11](https://arxiv.org/html/2309.11356v2#bib.bib11), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [73](https://arxiv.org/html/2309.11356v2#bib.bib73)] | | R1, R2, R4 | |  | | --- | | Cost-sensitive learning, | | IBL, LR, SVM, RF, | | XGBoost, CNN, | | VAR, k-NN | | I, N, TX | RE |
| |  | | --- | | Holdout evaluation | | (Train-test-validation splitting) | | Random Split | |  | | --- | | [[93](https://arxiv.org/html/2309.11356v2#bib.bib93), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [78](https://arxiv.org/html/2309.11356v2#bib.bib78), [12](https://arxiv.org/html/2309.11356v2#bib.bib12)] | | R1, R4 | |  | | --- | | RF, XGBoost, | | Attention-based, | | Adaboost | | N | RE |
|  | Time-Based Split | |  | | --- | | [[103](https://arxiv.org/html/2309.11356v2#bib.bib103), [93](https://arxiv.org/html/2309.11356v2#bib.bib93), [100](https://arxiv.org/html/2309.11356v2#bib.bib100)] | | R1,R3,R4 | |  | | --- | | Bayesian methods, RF, | | Monte Carlo methods | | N | DE, RE |
| |  | | --- | | Cost and error analysis, | | Baseline comparison | |  | [[99](https://arxiv.org/html/2309.11356v2#bib.bib99), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [103](https://arxiv.org/html/2309.11356v2#bib.bib103), [100](https://arxiv.org/html/2309.11356v2#bib.bib100)] | R1, R2, R3, R4 | |  | | --- | | SVM, KNN, XGB, | | MLP, RF, LR | | |  | | --- | | N, A, | | TX, I | | |  | | --- | | RE, DE, | | SI, SY | |
| Training time evaluation |  | [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [73](https://arxiv.org/html/2309.11356v2#bib.bib73)] | R1 | |  | | --- | | CNN-Autoencoders, | | CNN, VAR, | | k-nearest neighbors | | N | RE |
| Ablation studies |  | [[29](https://arxiv.org/html/2309.11356v2#bib.bib29)] | R1, R4 | K-means, One-class learning | I, N | DE |

|  |
| --- |
| Type of the |
| dataset |

|  |
| --- |
| [[15](https://arxiv.org/html/2309.11356v2#bib.bib15), [38](https://arxiv.org/html/2309.11356v2#bib.bib38), [93](https://arxiv.org/html/2309.11356v2#bib.bib93), [87](https://arxiv.org/html/2309.11356v2#bib.bib87)], |
| [[86](https://arxiv.org/html/2309.11356v2#bib.bib86), [150](https://arxiv.org/html/2309.11356v2#bib.bib150), [17](https://arxiv.org/html/2309.11356v2#bib.bib17), [95](https://arxiv.org/html/2309.11356v2#bib.bib95)] |

|  |
| --- |
| SVM, Cost-sensitive |
| learning, RF, LR, |
| XGBoost, |
| IBL |

|  |
| --- |
| [[17](https://arxiv.org/html/2309.11356v2#bib.bib17), [11](https://arxiv.org/html/2309.11356v2#bib.bib11), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [73](https://arxiv.org/html/2309.11356v2#bib.bib73)] |

|  |
| --- |
| Cost-sensitive learning, |
| IBL, LR, SVM, RF, |
| XGBoost, CNN, |
| VAR, k-NN |

|  |
| --- |
| Holdout evaluation |
| (Train-test-validation splitting) |

|  |
| --- |
| [[93](https://arxiv.org/html/2309.11356v2#bib.bib93), [33](https://arxiv.org/html/2309.11356v2#bib.bib33), [78](https://arxiv.org/html/2309.11356v2#bib.bib78), [12](https://arxiv.org/html/2309.11356v2#bib.bib12)] |

|  |
| --- |
| RF, XGBoost, |
| Attention-based, |
| Adaboost |

|  |
| --- |
| [[103](https://arxiv.org/html/2309.11356v2#bib.bib103), [93](https://arxiv.org/html/2309.11356v2#bib.bib93), [100](https://arxiv.org/html/2309.11356v2#bib.bib100)] |

|  |
| --- |
| Bayesian methods, RF, |
| Monte Carlo methods |

|  |
| --- |
| Cost and error analysis, |
| Baseline comparison |

|  |
| --- |
| SVM, KNN, XGB, |
| MLP, RF, LR |

|  |
| --- |
| N, A, |
| TX, I |

|  |
| --- |
| RE, DE, |
| SI, SY |

|  |
| --- |
| CNN-Autoencoders, |
| CNN, VAR, |
| k-nearest neighbors |

∗N-Numeric, TX-Textual, I-Image, A-Audio, T-Time series, RE-Naturally rare, DE-Derived, SI-Simulated, SY-Synthetic

#### 5.2.2 Rare event-specific evaluation methods

Evaluation methods that are specific to rare events emphasize early prediction, proactive decision-making, and economic feasibility in the prediction task. We identified several methods below as specific to rare events as presented in Table [9](https://arxiv.org/html/2309.11356v2#S5.T9 "Table 9 ‣ 5.2.2 Rare event-specific evaluation methods ‣ 5.2 Evaluation Methodologies ‣ 5 Evaluation Approaches ‣ A Comprehensive Survey on Rare Event Prediction").

I) Ahead-of-time prediction evaluation:
Ahead-of-time prediction evaluation assesses a model’s predictive capability for events or outcomes occurring multiple time steps into the future. This approach contrasts with the usual prediction evaluation, which focuses on predicting the immediate next event or outcome. Evaluating models "ahead of time" is particularly important in scenarios where early detection and proactive decision-making are critical. In the studies by [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [24](https://arxiv.org/html/2309.11356v2#bib.bib24), [100](https://arxiv.org/html/2309.11356v2#bib.bib100)], the performance of the proposed models has been evaluated over various lead times, ranging from one to many units of time. It was observed that while the accuracy of the models might decrease as the lead time increases, their performance has remained stable, demonstrating their potential utility in providing valuable insights well before the occurrence of rare events, such as black-swan or equipment failures.

II) Cost-benefit analysis:
Cost-benefit analysis has been used to assess rare event prediction’s economic feasibility and potential advantages. Methods like assessing potential financial loss reduction, optimizing resource allocation, and evaluating the potential mitigation of losses or damages are utilized to quantify and compare the costs and benefits linked to early prediction of rare events, as explored in [[73](https://arxiv.org/html/2309.11356v2#bib.bib73)] and [[72](https://arxiv.org/html/2309.11356v2#bib.bib72)].

III) Root cause analysis:
This could be viewed as a problem-solving approach focused on discerning the fundamental elements contributing to rare occurrences. It involves investigating and tracing the chain of events to determine the fundamental causes [[73](https://arxiv.org/html/2309.11356v2#bib.bib73)].

|  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Evaluation methodology | Papers | Rarity group | Algorithmic approach | Modality | |  | | --- | | Type of the | | dataset | |
| |  | | --- | | Ahead-of-time prediction | | evaluation | | |  | | --- | | [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [100](https://arxiv.org/html/2309.11356v2#bib.bib100), [3](https://arxiv.org/html/2309.11356v2#bib.bib3), [26](https://arxiv.org/html/2309.11356v2#bib.bib26)] | | R1, R3 | |  | | --- | | CNN-Autoencoders, CNN, | | Genetic algorithms | | N | RE, DE |
| Cost-benefit analysis | [[73](https://arxiv.org/html/2309.11356v2#bib.bib73), [72](https://arxiv.org/html/2309.11356v2#bib.bib72)] | R1 | |  | | --- | | k-nearest neighbors, | | Bayes and neural networks, | | Bayesian methods | | N | RE |
| Root cause analysis | [[73](https://arxiv.org/html/2309.11356v2#bib.bib73)] | R2 | |  | | --- | | k-nearest neighbors, | | Bayes and neural networks | | N | RE |

|  |
| --- |
| Type of the |
| dataset |

|  |
| --- |
| Ahead-of-time prediction |
| evaluation |

|  |
| --- |
| [[23](https://arxiv.org/html/2309.11356v2#bib.bib23), [100](https://arxiv.org/html/2309.11356v2#bib.bib100), [3](https://arxiv.org/html/2309.11356v2#bib.bib3), [26](https://arxiv.org/html/2309.11356v2#bib.bib26)] |

|  |
| --- |
| CNN-Autoencoders, CNN, |
| Genetic algorithms |

|  |
| --- |
| k-nearest neighbors, |
| Bayes and neural networks, |
| Bayesian methods |

|  |
| --- |
| k-nearest neighbors, |
| Bayes and neural networks |

∗N-Numeric, TX-Textual, I-Image, A-Audio, T-Time series, RE-Naturally rare, DE-Derived, SI-Simulated, SY-Synthetic

### 5.3 Performance metrics

Performance metrics aid in monitoring and optimizing algorithmic approaches, facilitating comparison of algorithms, determining optimal thresholds, supporting data-driven decision-making and conducting risk assessments. We categorize these performance metrics used in rare event research, which differ based on the downstream tasks involved. The detailed analysis of performance metrics and rarity groups, algorithmic approaches, modality, and dataset types is included in Table [11](https://arxiv.org/html/2309.11356v2#S5.T10 "Table 11 ‣ 5.3 Performance metrics ‣ 5 Evaluation Approaches ‣ A Comprehensive Survey on Rare Event Prediction").

I) Downstream tasks: Classification and Forecasting

i) Accuracy: Evaluating model accuracy is essential, particularly in imbalanced scenarios, where relying solely on accuracy can be deceptive. Since accuracy only assigns overall class weights rather than weights for unusual classes or minorities. Zhao et al. [[11](https://arxiv.org/html/2309.11356v2#bib.bib11)] highlight that standard classifiers like LR and SVM assume equal class distribution, which leads to poor sensitivity for rare events. To address this, variants of accuracy such as Faulty-Normal Accuracy (FNACC) and Real Faulty-Normal Accuracy (RFNACC) are introduced [[20](https://arxiv.org/html/2309.11356v2#bib.bib20), [30](https://arxiv.org/html/2309.11356v2#bib.bib30)]. FNACC assesses how well the model identifies normal samples preceding faults, while RFNACC evaluates the accuracy in predicting actual faults, offering a more nuanced view of model performance on rare events.

ii) Geometric mean (G-Mean): G-Mean combines sensitivity and specificity to measure the balance between classification performance for the majority and minority classes. It is particularly useful in rare event prediction as a low G-Mean indicates poor prediction of rare events, despite good performance on the majority class [[38](https://arxiv.org/html/2309.11356v2#bib.bib38), [41](https://arxiv.org/html/2309.11356v2#bib.bib41), [66](https://arxiv.org/html/2309.11356v2#bib.bib66)].

iii) Cohen’s kappa index: It is a metric that has been used in earth science and healthcare-based rare event prediction evaluation for use cases like landslide prediction[[70](https://arxiv.org/html/2309.11356v2#bib.bib70)], hazardous seismic bumps in coal mines, detecting changes in geospatial trajectories [[146](https://arxiv.org/html/2309.11356v2#bib.bib146)], [[16](https://arxiv.org/html/2309.11356v2#bib.bib16)], mineral prospectivity prediction [[158](https://arxiv.org/html/2309.11356v2#bib.bib158)] and thoracic events prediction [[91](https://arxiv.org/html/2309.11356v2#bib.bib91)]. [[16](https://arxiv.org/html/2309.11356v2#bib.bib16)] has selected Kappa as the primary evaluation metric since it indicates the generalizability of the classifier’s predictive ability on the supplementary datasets. However, some research attempts have proven that the Kappa metric produces unreliable results due to its high sensitivity to the distribution of the marginal totals [[179](https://arxiv.org/html/2309.11356v2#bib.bib179)].

iv) Balanced error rate (BER): BER measures the average of the errors for each class in a classification problem, which has been used by [[16](https://arxiv.org/html/2309.11356v2#bib.bib16), [146](https://arxiv.org/html/2309.11356v2#bib.bib146)] in rare event model evaluation.

v) Matthews’s correlation coefficient (MCC): MCC is a more accurate statistical metric that provides a reliable measure of a model’s performance by considering all four confusion matrix categories (TP, FN, TN, and FP) and balancing the impact of both positive and negative class sizes [[179](https://arxiv.org/html/2309.11356v2#bib.bib179), [16](https://arxiv.org/html/2309.11356v2#bib.bib16), [180](https://arxiv.org/html/2309.11356v2#bib.bib180)].
Hence, this metric is beneficial when dealing with highly imbalanced rare event datasets.

vi) Cost matrix: A cost matrix specifies the relative importance of accuracy for different classification predictions by assigning costs or weights to various classification predictions. In a cost matrix, positive numbers (costs) influence negative outcomes, whereas negative numbers (benefits) influence positive outcomes. An instance is [[87](https://arxiv.org/html/2309.11356v2#bib.bib87)], which tries to minimize the cost matrix for binary misclassification using threshold and tree-based classification models. This approach helps prioritize detecting rare events by adjusting the cost of false positives and false negatives.

vii) Top-decile lift (TDL):
TDL is a metric used in the economic domain that compares the incidence in the top 10% samples with the highest model predictions to the incidence of the entire sample [[181](https://arxiv.org/html/2309.11356v2#bib.bib181)]. [[150](https://arxiv.org/html/2309.11356v2#bib.bib150)] used TDL and assumed it returned the customers predicted to be most likely to churn rather than a random selection. In rare event scenarios, TDL helps the model identify the most promising cases by highlighting its ability to distinguish rare events from non-rare ones, thus providing insights beyond overall accuracy.

viii) Reconstruction error:
This measures the discrepancy between the original input data and its reconstructed version generated by a model by quantifying how well the model can reproduce the input data. In models like autoencoders, the model is trained to reconstruct its input data from a compressed latent representation [[27](https://arxiv.org/html/2309.11356v2#bib.bib27)].
Reconstruction error identifies significant deviations from normal patterns, aiding in effective rare event prediction and enhancing the model’s ability to prioritize and identify rare events.

ix) Moran index:
Used in spatial analysis and statistics and measures a variable’s spatial autocorrelation or clustering within a geographic space. It calculates the degree of similarity or dissimilarity between neighboring locations based on the values of the analyzed variable. It provides a measure of spatial dependence, indicating whether similar values tend to cluster together (positive spatial autocorrelation) or are dispersed (negative spatial autocorrelation) [[126](https://arxiv.org/html/2309.11356v2#bib.bib126)]. Moran index has been used to detect spatial clustering of rare events, and it gives insights into spatial locations where these events are more likely to occur [[182](https://arxiv.org/html/2309.11356v2#bib.bib182), [126](https://arxiv.org/html/2309.11356v2#bib.bib126)].

II) Downstream task: Clustering

i) Elbow method:
The Elbow method, typically used to identify the optimal number of clusters, is beneficial in rare event prediction tasks where the majority class can dominate the clustering process. This also ensures that minority class clusters are not merged into larger majority class clusters, thereby preserving the distinct characteristics of rare events. This approach is helpful in studies focusing on class imbalance, where detecting minority classes with high specificity and sensitivity is vital for model performance [[18](https://arxiv.org/html/2309.11356v2#bib.bib18)].

ii) Silhouette coefficient:
It is another metric used for internal cluster validation. This metric is particularly important in rare event prediction as it helps to determine whether rare event clusters are well-defined and distinct from non-rare event clusters. A small silhouette width may indicate that rare events are being inaccurately grouped with non-rare events, which can significantly impact the model’s ability to identify and predict rare occurrences [[8](https://arxiv.org/html/2309.11356v2#bib.bib8)].

iii) Hopkins statistics test
The Hopkins statistics test is used to assess the clustering tendency of a dataset. Omar et al. [[8](https://arxiv.org/html/2309.11356v2#bib.bib8)] used it to evaluate the clustering tendency in a rare event dataset. This revealed well-defined and meaningful clusters that standard clustering evaluation methods might miss due to the high data imbalance and the distinct patterns often exhibited by the minority class.

iv) True skill statistic (TSS):
TSS combines sensitivity and specificity into a single measure, offering a more balanced model performance evaluation in rare event prediction. Unlike accuracy, which can be misleading in imbalanced datasets, TSS provides a robust assessment of a model’s positive and negative predictive abilities [[183](https://arxiv.org/html/2309.11356v2#bib.bib183), [184](https://arxiv.org/html/2309.11356v2#bib.bib184)]. This makes it particularly useful in scenarios like species distribution modeling or solar flare forecasting, where both false positives and false negatives carry significant consequences [[15](https://arxiv.org/html/2309.11356v2#bib.bib15)].

v) Sum of squared errors (SSE):
SSE measures the variation within clusters by calculating the sum of the squared differences between each observation and the group mean and is often used to evaluate cluster compactness [[185](https://arxiv.org/html/2309.11356v2#bib.bib185)]. In rare event prediction, minimizing SSE ensures that rare event clusters are as distinct and well-defined as possible [[77](https://arxiv.org/html/2309.11356v2#bib.bib77)]. High SSE values may indicate that the model fails to accurately capture the unique characteristics of rare events, leading to poor prediction performance [[77](https://arxiv.org/html/2309.11356v2#bib.bib77)].

III) Downstream task: Regression

i) Mean absolute error (MAE) and root mean squared error (RMSE),
mean absolute percentage error (MAPE):

MAE or Mean Absolute Deviation (MAD), RMSE, and MAPE or Mean Absolute Percentage Deviation (MAPD) are popular scale-dependent metrics used in evaluation. MAE provides a straightforward measure of prediction error, highlighting performance on underrepresented rare events. RMSE penalizes more significant errors, making it ideal for assessing precision in datasets where rare occurrences have high variance. Though sensitive to small actual values, MAPE offers insights into percentage accuracy, which is essential for comparing model performance across different events. These metrics have been employed in rare event studies, with Xu et al. [[79](https://arxiv.org/html/2309.11356v2#bib.bib79)] selecting MAE and RMSE as regression loss functions and Ravindranath et al. [[37](https://arxiv.org/html/2309.11356v2#bib.bib37)] using these metrics in multivariate multiscale attention research.

IV) Downstream task: Simulation

i) Probability evaluation of rare event:
This metric directly measures the likelihood of the rare event occurring. It provides a quantitative assessment in a simulation of the occurrence of the event of interest [[111](https://arxiv.org/html/2309.11356v2#bib.bib111), [122](https://arxiv.org/html/2309.11356v2#bib.bib122), [22](https://arxiv.org/html/2309.11356v2#bib.bib22)].

ii) Rare event detection metrics:
The standard metrics that evaluate the performance of algorithms designed to predict rare events like precision, recall, F1 score, and Area Under the Receiver Operating Characteristic Curve (AUC-ROC), RMSE, have also been utilized in simulation evaluations [[111](https://arxiv.org/html/2309.11356v2#bib.bib111), [22](https://arxiv.org/html/2309.11356v2#bib.bib22)].

iii) Statistical robustness:
Statistical robustness refers to the ability of statistical models to produce reliable and consistent results under varying sample sizes, distributional assumptions, or data perturbations [[111](https://arxiv.org/html/2309.11356v2#bib.bib111)].

iv) Confidence intervals:
This metric provides a range of values within which the actual value of a performance metric is expected to fall and quantifies the uncertainty associated with the estimated performance metric [[22](https://arxiv.org/html/2309.11356v2#bib.bib22)].

|  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Downstream task | Performance metric | Papers | Rarity group | Algorithmic approach | Modality | |  | | --- | | Dataset type | |
| |  | | --- | | Downstream task: | | Classification and | | Forecasting | | Accuracy | |  | | --- | | [[99](https://arxiv.org/html/2309.11356v2#bib.bib99), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [93](https://arxiv.org/html/2309.11356v2#bib.bib93)], | | [[100](https://arxiv.org/html/2309.11356v2#bib.bib100), [88](https://arxiv.org/html/2309.11356v2#bib.bib88), [95](https://arxiv.org/html/2309.11356v2#bib.bib95)] | | R4, R1,R2 | |  | | --- | | Bayes & Neural networks, RF, | | Monte Carlo methods | | A, N, TX | RE, DE |
|  | |  | | --- | | Confusion matrix, Sensitivity, | | Specificity, FPR, FNR, | | Precision, F1 score | | |  | | --- | | [[99](https://arxiv.org/html/2309.11356v2#bib.bib99), [39](https://arxiv.org/html/2309.11356v2#bib.bib39), [23](https://arxiv.org/html/2309.11356v2#bib.bib23)], | | [[38](https://arxiv.org/html/2309.11356v2#bib.bib38), [103](https://arxiv.org/html/2309.11356v2#bib.bib103), [93](https://arxiv.org/html/2309.11356v2#bib.bib93)], | | [[100](https://arxiv.org/html/2309.11356v2#bib.bib100), [88](https://arxiv.org/html/2309.11356v2#bib.bib88), [27](https://arxiv.org/html/2309.11356v2#bib.bib27)], | | [[170](https://arxiv.org/html/2309.11356v2#bib.bib170), [3](https://arxiv.org/html/2309.11356v2#bib.bib3)], | | [[95](https://arxiv.org/html/2309.11356v2#bib.bib95), [11](https://arxiv.org/html/2309.11356v2#bib.bib11)] | | R1, R3,R4, R2 | |  | | --- | | Bayes & Neural networks, | | Association rule mining, | | Cost-sensitive learning, | | Bayesian methods, RF, | | Monte Carlo methods, | | VAR, LSTM-autoencoder, | | Genetic algos | | A, N, TX | RE, DE |
|  | Geometric Mean (G-Mean) | |  | | --- | | [[39](https://arxiv.org/html/2309.11356v2#bib.bib39), [100](https://arxiv.org/html/2309.11356v2#bib.bib100), [17](https://arxiv.org/html/2309.11356v2#bib.bib17)] | | R1, R3,R4, R2 | |  | | --- | | Association | | rule mining, | | Monte Carlo methods, | | Attention-based mechanisms | | N | DE, RE |
|  | Cohen’s Kappa Index | |  | | --- | | [[146](https://arxiv.org/html/2309.11356v2#bib.bib146), [91](https://arxiv.org/html/2309.11356v2#bib.bib91), [158](https://arxiv.org/html/2309.11356v2#bib.bib158)] | | R1, R2, R3 | |  | | --- | | SVM, Particle swarm optimization, | | Bat algorithm, CNN | | N, I | Real |
|  | Balanced Error Rate | [[146](https://arxiv.org/html/2309.11356v2#bib.bib146)] |  | SVM | N |  |
|  | Matthews’s correlation coefficient | [[16](https://arxiv.org/html/2309.11356v2#bib.bib16)] | R3 | |  | | --- | | Cost-sensitive learning | | Bayes & Neural networks | | N | RE |
|  | PR curve, ROC, AUC and AUPRC | |  | | --- | | [[99](https://arxiv.org/html/2309.11356v2#bib.bib99), [20](https://arxiv.org/html/2309.11356v2#bib.bib20), [38](https://arxiv.org/html/2309.11356v2#bib.bib38)], | | [[93](https://arxiv.org/html/2309.11356v2#bib.bib93), [150](https://arxiv.org/html/2309.11356v2#bib.bib150), [95](https://arxiv.org/html/2309.11356v2#bib.bib95)] | | R1, R4, R2 | |  | | --- | | Bayes & Neural networks, | | ARIMA, SVM, Cost-sensitive | | learning, RF | | A, N, TX | DE, RE |
|  | Cost matrix | [[87](https://arxiv.org/html/2309.11356v2#bib.bib87)] | R2 | RF, LR, XGB | N | RE |
|  | Top-decile lift | [[150](https://arxiv.org/html/2309.11356v2#bib.bib150)] |  | Hybrid | N | RE |
|  | Reconstruction error | [[27](https://arxiv.org/html/2309.11356v2#bib.bib27), [26](https://arxiv.org/html/2309.11356v2#bib.bib26)] | R1 | |  | | --- | | VAR, LSTM-autoencoder, | | autoencoders, hierarchical clustering | | N | RE |
|  | Moran index | [[126](https://arxiv.org/html/2309.11356v2#bib.bib126)] | R1 | Statistical Modeling | N | RE |
| |  | | --- | | Downstream task: | | Clustering | | Hopkins statistics test | [[8](https://arxiv.org/html/2309.11356v2#bib.bib8)] | R2 | |  | | --- | | Random forest clustering, | | PAM | | N | RE |
|  | Silhouette coefficient | [[8](https://arxiv.org/html/2309.11356v2#bib.bib8)] | R3 | |  | | --- | | Random forest clustering, | | PAM | | N | RE |
|  | Elbow method | [[18](https://arxiv.org/html/2309.11356v2#bib.bib18)] | R1, R2 | K-Medoids clustering | N | RE |
|  | True Skill Statistic | [[15](https://arxiv.org/html/2309.11356v2#bib.bib15)] | R1, R2 | Kernel-based methods - SVM | N | DE |
|  | Sum of Squared Errors | [[77](https://arxiv.org/html/2309.11356v2#bib.bib77)] | R4 | K-nearest neighbur | N | RE |
| |  | | --- | | Downstream task: | | Regression | | |  | | --- | | Mean Absolute Error and | | Root Mean Squared Error, | | Mean absolute percentage error | | [[79](https://arxiv.org/html/2309.11356v2#bib.bib79), [37](https://arxiv.org/html/2309.11356v2#bib.bib37)] | R1, R3, R4 | |  | | --- | | Attention-based | | mechanisms | | N | RE |
| |  | | --- | | Downstream task: | | Simulation | | Probability evaluation of rare events | |  | | --- | | [[111](https://arxiv.org/html/2309.11356v2#bib.bib111), [122](https://arxiv.org/html/2309.11356v2#bib.bib122), [22](https://arxiv.org/html/2309.11356v2#bib.bib22)] | | R1,R2,R3,R4 | |  | | --- | | Monte carlo methods, | | Bayes and NN, RF, LR | | N | SI |
|  | Rare event detection metrics | [[111](https://arxiv.org/html/2309.11356v2#bib.bib111), [22](https://arxiv.org/html/2309.11356v2#bib.bib22)] | R1,R2,R3,R4 | |  | | --- | | Monte carlo methods, | | Bayes and NN, RF, LR | | N | SI |
|  | Statistical Robustness | [[111](https://arxiv.org/html/2309.11356v2#bib.bib111)] | R1,R2,R3,R4 | |  | | --- | | Monte carlo methods, | | Bayes and NN, RF | | N | SI |
|  | Confidence intervals | [[22](https://arxiv.org/html/2309.11356v2#bib.bib22)] | R1,R2,R3,R4 | LR, Monte carlo | N | SI |

|  |
| --- |
| Dataset type |

|  |
| --- |
| Downstream task: |
| Classification and |
| Forecasting |

|  |
| --- |
| [[99](https://arxiv.org/html/2309.11356v2#bib.bib99), [23](https://arxiv.org/html/2309.11356v2#bib.bib23), [93](https://arxiv.org/html/2309.11356v2#bib.bib93)], |
| [[100](https://arxiv.org/html/2309.11356v2#bib.bib100), [88](https://arxiv.org/html/2309.11356v2#bib.bib88), [95](https://arxiv.org/html/2309.11356v2#bib.bib95)] |

|  |
| --- |
| Bayes & Neural networks, RF, |
| Monte Carlo methods |

|  |
| --- |
| Confusion matrix, Sensitivity, |
| Specificity, FPR, FNR, |
| Precision, F1 score |

|  |
| --- |
| [[99](https://arxiv.org/html/2309.11356v2#bib.bib99), [39](https://arxiv.org/html/2309.11356v2#bib.bib39), [23](https://arxiv.org/html/2309.11356v2#bib.bib23)], |
| [[38](https://arxiv.org/html/2309.11356v2#bib.bib38), [103](https://arxiv.org/html/2309.11356v2#bib.bib103), [93](https://arxiv.org/html/2309.11356v2#bib.bib93)], |
| [[100](https://arxiv.org/html/2309.11356v2#bib.bib100), [88](https://arxiv.org/html/2309.11356v2#bib.bib88), [27](https://arxiv.org/html/2309.11356v2#bib.bib27)], |
| [[170](https://arxiv.org/html/2309.11356v2#bib.bib170), [3](https://arxiv.org/html/2309.11356v2#bib.bib3)], |
| [[95](https://arxiv.org/html/2309.11356v2#bib.bib95), [11](https://arxiv.org/html/2309.11356v2#bib.bib11)] |

|  |
| --- |
| Bayes & Neural networks, |
| Association rule mining, |
| Cost-sensitive learning, |
| Bayesian methods, RF, |
| Monte Carlo methods, |
| VAR, LSTM-autoencoder, |
| Genetic algos |

|  |
| --- |
| [[39](https://arxiv.org/html/2309.11356v2#bib.bib39), [100](https://arxiv.org/html/2309.11356v2#bib.bib100), [17](https://arxiv.org/html/2309.11356v2#bib.bib17)] |

|  |
| --- |
| Association |
| rule mining, |
| Monte Carlo methods, |
| Attention-based mechanisms |

|  |
| --- |
| [[146](https://arxiv.org/html/2309.11356v2#bib.bib146), [91](https://arxiv.org/html/2309.11356v2#bib.bib91), [158](https://arxiv.org/html/2309.11356v2#bib.bib158)] |

|  |
| --- |
| SVM, Particle swarm optimization, |
| Bat algorithm, CNN |

|  |
| --- |
| Cost-sensitive learning |
| Bayes & Neural networks |

|  |
| --- |
| [[99](https://arxiv.org/html/2309.11356v2#bib.bib99), [20](https://arxiv.org/html/2309.11356v2#bib.bib20), [38](https://arxiv.org/html/2309.11356v2#bib.bib38)], |
| [[93](https://arxiv.org/html/2309.11356v2#bib.bib93), [150](https://arxiv.org/html/2309.11356v2#bib.bib150), [95](https://arxiv.org/html/2309.11356v2#bib.bib95)] |

|  |
| --- |
| Bayes & Neural networks, |
| ARIMA, SVM, Cost-sensitive |
| learning, RF |

|  |
| --- |
| VAR, LSTM-autoencoder, |
| autoencoders, hierarchical clustering |

|  |
| --- |
| Downstream task: |
| Clustering |

|  |
| --- |
| Random forest clustering, |
| PAM |

|  |
| --- |
| Random forest clustering, |
| PAM |

|  |
| --- |
| Downstream task: |
| Regression |

|  |
| --- |
| Mean Absolute Error and |
| Root Mean Squared Error, |
| Mean absolute percentage error |

|  |
| --- |
| Attention-based |
| mechanisms |

|  |
| --- |
| Downstream task: |
| Simulation |

|  |
| --- |
| [[111](https://arxiv.org/html/2309.11356v2#bib.bib111), [122](https://arxiv.org/html/2309.11356v2#bib.bib122), [22](https://arxiv.org/html/2309.11356v2#bib.bib22)] |

|  |
| --- |
| Monte carlo methods, |
| Bayes and NN, RF, LR |

|  |
| --- |
| Monte carlo methods, |
| Bayes and NN, RF, LR |

|  |
| --- |
| Monte carlo methods, |
| Bayes and NN, RF |

∗N-Numeric, TX-Textual, I-Image, A-Audio, T-Time series, RE-Naturally rare, DE-Derived, SI-Simulated, SY-Synthetic

#### 5.3.1 Analyzing evaluation approaches vs. rarity groups, modality, type of data and algorithmic approaches

Based on our literature review, the analysis of general evaluation methods and rare event-specific evaluation methods, along with their respective components, is summarized in Tables [8](https://arxiv.org/html/2309.11356v2#S5.T8 "Table 8 ‣ 5.2.1 General evaluation methods ‣ 5.2 Evaluation Methodologies ‣ 5 Evaluation Approaches ‣ A Comprehensive Survey on Rare Event Prediction") and [9](https://arxiv.org/html/2309.11356v2#S5.T9 "Table 9 ‣ 5.2.2 Rare event-specific evaluation methods ‣ 5.2 Evaluation Methodologies ‣ 5 Evaluation Approaches ‣ A Comprehensive Survey on Rare Event Prediction"). The analysis highlighted that standard techniques like cross-validation have predominantly been employed in datasets encompassing numerical, textual, and image data, particularly in extremely-rare and very-rare categories. Only limited research has been dedicated to rare event-specific evaluation methods applied to numerical data. In classification and forecasting, widely used performance metrics such as accuracy, precision, recall, AUC, and ROC have been employed for evaluation, regardless of the data modalities. However, evaluation has predominantly been conducted on numerical data for other downstream tasks like clustering, regression, and simulation. Moreover, our analysis reveals the limited availability of rare event-specific evaluation techniques and highlights the need for conceptualized evaluation methodologies explicitly designed for rare event prediction. Such tailored approaches would be essential to address the unique challenges of rare events.

In conclusion, we presented a comprehensive analysis of various evaluation approaches used in rare event prediction.
From our analysis, we identified most studies rely on standard evaluation metrics, highlighting the need for tailored metrics explicitly designed for rare events. This is particularly important given the limited availability of rare event-specific evaluation techniques, especially in datasets comprising numerical, textual, and image data across diverse tasks such as classification, forecasting, clustering, regression, and simulation. Through this examination, we also gained valuable insights into the suitability and limitations of different evaluation methodologies and performance metrics for handling rare events. The findings underscore the significance of choosing appropriate metrics tailored to specific downstream tasks and modalities.

## 6 Research Findings and Discussion

This section provides an overview of the research findings, emphasizing identified gaps, and open challenges in the field. It also explores emerging research trends and novel approaches, aiming to address the complexities of rare event prediction and drive advancements in the field.

### 6.1 The gaps in current literature

Lack of standardized benchmark datasets: “Standardized dataset” represents real-world scenarios that include an ideal rarity percentage, annotated ground truth, scalability, temporal and spatial association, feature diversity, noise, and outliers. They should also adhere to privacy and ethical standards to enable fair and comprehensive comparisons of algorithms and advance the state-of-the-art in the field. The absence of such widely accepted benchmark datasets for rare event prediction makes it challenging to compare the performance of different algorithms and approaches consistently.

Imbalanced data processing techniques: While many studies explore standard methods for addressing imbalanced data, there is a necessity for in-depth investigation of standardized techniques for data processing, especially for handling extreme rarity, since general data imbalance techniques may inadequate and underperform.

Scalability issues: Current research has not addressed scalability challenges in handling large-scale rare event datasets, such as computational complexity, memory constraints, and algorithmic efficiency.

Limited focus on Uncertainty Quantification (UQ): UQ involves quantifying and characterizing uncertainties associated with predictions, offering insights into the reliability and confidence of estimates. The lack of comprehensive studies on UQ for rare event prediction undermines confidence in model predictions, which is essential for making informed decisions when dealing with infrequent and high-impact events.

Real-world applicability: More research is needed to assess the practical usability and robustness of prediction models in critical real-world applications, particularly in domains such as healthcare, finance, and earth sciences.

Limited focus on rare event-specific evaluation techniques: Many studies still rely on standard and general evaluation metrics designed for balanced datasets, which is challenging because these metrics fail to accurately reflect model performance in rare events, leading to misleading assessments and suboptimal model improvements.

Measuring data quality: The absence of standardized methods for measuring data quality in data sampling and augmentation for rare event data is a research gap.

### 6.2 Open challenges of rare event prediction

Based on our study, below are some open issues and challenges in the field of rare event prediction that we identified.

Lack of annotated data: Collecting and annotating data about rare events proves complex and time-intensive, posing an inherent obstacle in developing proficient rare event prediction models.

Interdependence between rare events: Identifying complex relationships and dependencies among rare events (when more than one rare event occurs) remains elusive.

Bias in data: Bias refers to systematic errors or prejudices in data collection, sampling, or labeling that can skew the results of prediction models. This bias is especially challenging in rare events since it can lead to significant misrepresentations of the events, resulting in highly inaccurate and unreliable predictions.

Generalization and real-world applicability: Achieving generalizability in rare event prediction models presents challenges due to the potentially significant differences
in variability and distribution of new, unseen, or real-world data compared with the training data.

Interpretability: The infrequency and high stakes of rare events necessitate clear and understandable explanations to ensure trust and accurate decision-making in critical domains like healthcare or finance.

### 6.3 Research trends in rare event prediction

Research in rare event prediction has surged in recent years due to the increasing importance of rare events in many fields. Some of the research trends in this area include:

Incorporation of domain knowledge: Domain knowledge, expert opinions, and human insights Human-in-the-Loop Systems) can aid in rare event prediction. They have led in emerging applications that combine data-driven and algorithmic approaches with qualitative knowledge, knowledge graphs, expert systems, and rule-based models to improve the robustness and reliability of predictions [[186](https://arxiv.org/html/2309.11356v2#bib.bib186), [187](https://arxiv.org/html/2309.11356v2#bib.bib187), [188](https://arxiv.org/html/2309.11356v2#bib.bib188), [189](https://arxiv.org/html/2309.11356v2#bib.bib189), [190](https://arxiv.org/html/2309.11356v2#bib.bib190)].

Explainability: The growing emphasis on transparency and comprehension in model predictions has led to the rise of explainability as a prospective future trend in rare event prediction research [[191](https://arxiv.org/html/2309.11356v2#bib.bib191), [191](https://arxiv.org/html/2309.11356v2#bib.bib191), [192](https://arxiv.org/html/2309.11356v2#bib.bib192)]. This development aims to enhance decision-making processes and foster trust in the accuracy of models.

Ensemble learning: This involves combining multiple algorithms to improve prediction performance, which is particularly effective in handling imbalanced datasets and has recently gained attention [[193](https://arxiv.org/html/2309.11356v2#bib.bib193), [194](https://arxiv.org/html/2309.11356v2#bib.bib194), [195](https://arxiv.org/html/2309.11356v2#bib.bib195), [196](https://arxiv.org/html/2309.11356v2#bib.bib196)].

Meta-learning, few-shot learning, and transfer learning:
Meta-learning [[197](https://arxiv.org/html/2309.11356v2#bib.bib197)] and few-shot learning [[198](https://arxiv.org/html/2309.11356v2#bib.bib198)] have proven to enhance rare event prediction recently by enabling model learning from related events and generalization to new and infrequent events with limited labeled data, thus improving adaptability and accuracy.
Transfer learning is a meta-learning technique that involves using knowledge from one domain to improve learning in another. This approach is promising in rare event prediction, where data from different domains can be leveraged to improve predictive performance [[195](https://arxiv.org/html/2309.11356v2#bib.bib195), [199](https://arxiv.org/html/2309.11356v2#bib.bib199)].

Using multi-modal data: Integrating information from multiple data sources and modalities has improved rare event predictive power, generalization, and robustness while uncovering hidden patterns [[200](https://arxiv.org/html/2309.11356v2#bib.bib200), [201](https://arxiv.org/html/2309.11356v2#bib.bib201)]. However, it also presents challenges related to data integration, feature engineering, and model complexity.

Uncertainty quantification with rarity: Recently, UQ has gained prominence within rare event prediction. Using UQ, decision-makers can make more informed choices, assess risk, optimize resource allocation, and enhance the robustness to mitigate the impacts of rare events. These can incorporate advancements using probabilistic modeling [[188](https://arxiv.org/html/2309.11356v2#bib.bib188)], Bayesian inference [[202](https://arxiv.org/html/2309.11356v2#bib.bib202)], Monte Carlo methods [[203](https://arxiv.org/html/2309.11356v2#bib.bib203)], and Deep Ensembles [[204](https://arxiv.org/html/2309.11356v2#bib.bib204), [203](https://arxiv.org/html/2309.11356v2#bib.bib203)].

Privacy-preserving techniques: Rare event research on techniques like federated learning, differential privacy, encrypted data processing [[205](https://arxiv.org/html/2309.11356v2#bib.bib205), [206](https://arxiv.org/html/2309.11356v2#bib.bib206)], and privacy-preserving data mining [[207](https://arxiv.org/html/2309.11356v2#bib.bib207)] can be prioritized for sensitive rare event data to ensure confidentiality .

Leveraging edge devices and neuromorphic computing techniques: Incorporating edge devices and advanced neuromorphic computing techniques has emerged as a trend in rare event prediction [[208](https://arxiv.org/html/2309.11356v2#bib.bib208), [209](https://arxiv.org/html/2309.11356v2#bib.bib209)], enabling efficient real-time processing, low-latency analytics, and enhanced model adaptability at the edge while leveraging efficient computing paradigms for improved pattern recognition and prediction accuracy.

## 7 Vision Forward

As the methods, data, and applications for predicting rare events continue to advance, we can see how it will affect tasks beyond prediction. We envision that it will have a significant impact on three specific areas: improving our understanding of causality, using process knowledge workflows to predict rare events, and implementing automated planning strategies to mitigate them effectively. This is illustrated in Figure [11](https://arxiv.org/html/2309.11356v2#S7.F11 "Figure 11 ‣ 7 Vision Forward ‣ A Comprehensive Survey on Rare Event Prediction").

![Refer to caption](x11.png)

Investigating causality for explainability and interpretability

An integral component of our strategy entails delving deeper into causality, which will aid us in delivering more lucid explanations. This requires us to gauge the influence of individual input-output associations and actions. In doing so, we can deduce the causes of infrequent occurrences and determine which actions by sub-systems, robots, or simulators triggered them. By comprehending causality in this manner, we can uncover the underlying reasons behind rare events and plan mitigation procedures accordingly.

Process knowledge workflows for rare event prediction

Another direction for rare-event prediction entails the integration of process knowledge workflows into the prediction of rare events. This methodology enhances rare event prediction by integrating domain-specific procedural knowledge with data-driven approaches. This integration has the potential to reveal nuanced abnormalities and disparities that may not be readily apparent, hence leading to more accurate and efficient rare-event prediction.

Automated planning for mitigation strategies

Lastly, the road map toward advanced rare-event prediction applications envisions the integration of automated planning techniques. Once rare events are detected and understood, the next step involves devising effective mitigation strategies. Automated planning aims to generate dynamic response plans that can mitigate the impact of rare events. These strategies can encompass various scenarios, offering a comprehensive and adaptable framework for handling unexpected, uncertain occurrences.

In essence, a forward-thinking approach in predicting rare events relies on three crucial components: exploring causes, following knowledge workflows, and implementing automated planning. For instance, predicting rare events in manufacturing assembly pipelines, such as unexpected machinery failures or missing parts, is significant for reducing time and labor costs and improving work processes. Predicting such events involves understanding causality to identify root causes, using process knowledge workflows for accurate prediction, and implementing automated planning strategies to mitigate their impact effectively.

A key insight that we foresee here is that, these components are intricately connected, with each one capable of informing and enhancing the others. For instance, investigating causes can help detect abnormal occurrences and irregularities in knowledge workflows, while insights gained from knowledge workflows can improve automated planning techniques to prevent rare events. By identifying the causes of rare events through exploration, mitigation strategies can be developed in automated planning, and optimized strategies can be used to manipulate variables and gain a better understanding of the causal relationships between factors and rare events. Ultimately, this collaborative approach generates a more comprehensive and holistic framework for predicting rare events across various domains, as information and insights are exchanged between the three elements.

## 8 Conclusion

This paper presents a detailed analysis of rare event prediction, encompassing rare event data, data processing, algorithmic and evaluation approaches. Through our examination of the current literature, we identified several gaps and challenges in the field, highlighting the need for specialized evaluation techniques and their integration. As rare events continue to play a vital role in diverse domains, like manufacturing, healthcare, finance, and earth sciences, addressing these challenges will foster the development of more robust and accurate prediction models. By embracing emerging research trends and leveraging advanced learning methods, we can unlock new opportunities to enhance the prediction and management of rare events, ultimately contributing to safer and more efficient decision-making processes. As the field evolves, interdisciplinary collaboration and innovative solutions will pave the way for transformative advancements in rare event prediction.

## 9 Acronyms

Table [12](https://arxiv.org/html/2309.11356v2#A1.T12 "Table 12 ‣ Appendix A ACRONYMS: Table 12 ‣ A Comprehensive Survey on Rare Event Prediction") under the Appendix [A](https://arxiv.org/html/2309.11356v2#A1 "Appendix A ACRONYMS: Table 12 ‣ A Comprehensive Survey on Rare Event Prediction") includes the acronyms used in the paper.

## 10 Acknowledgments

This work is supported in part by NSF grants #2133842, "EAGER: Advancing Neuro-symbolic AI with Deep Knowledge Infused Learning", and #2119654, "RII Track 2 FEC: Enabling Factory to Factory (F2F) Networking for Future Manufacturing". Any opinions, findings, conclusions, or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the NSF.

## References

## Appendices

## Appendix A ACRONYMS: Table [12](https://arxiv.org/html/2309.11356v2#A1.T12 "Table 12 ‣ Appendix A ACRONYMS: Table 12 ‣ A Comprehensive Survey on Rare Event Prediction")

| Acronym | Description | Acronym | Description |
| --- | --- | --- | --- |
| N | Numeric data | LIDAR | Light detection and ranging |
| TX | Textual data | LASA | Look-alike-sound-alike |
| I | Image data | FFT | Fast fourier transform |
| A | Audio data | GAN | Generative adversarial networks |
| T | Time series | CGAN | Conditional generative adversarial networks |
| CF | Classification | WGAN | Wasserstein agenerative adversarial networks |
| CL | Clustering | MPM | Mineral prospectivity mapping |
| FT | Forecasting | PCA | Principal component analysis |
| RG | Regression | LR | Logistic regression |
| SM | Simulation | NB | Naive bayes |
| RE | Naturally rare event datasets | NN | Neural networks |
| DE | Derived datasets | CNN | Convolutional neural networks |
| SI | Simulated datasets | MLP | Multi-layer perceptron |
| SY | Synthetic datasets | LSTM | Long short-term memory |
| UCI | University of California Irvine | RF | Random forest |
| KEEL | Knowledge extraction based on evolutionary learning | k-NN | K-nearest neighbors |
| API | Application programming interface | RIPPER | Repeated incremental pruning to produce error reduction |
| DC | Data cleaning | SVM | Support vector machines |
| FS | Feature selection | L.SVM | Support vector machine with linear kernel |
| SL | Sampling | R.SVM | Support vector machine with radial kernel |
| FE | Feature engineering | GSVM | Granular support vector machines |
| ML | Machine learning | RE-WKLR | Rare event weighted kernel logistic regression |
| R1 | Extremely-rare category | MSB | Maximum specificity bias |
| R2 | Very-rare category | IBL | Instance-based learning |
| R3 | Moderately-rare category | 1-NN | 1-Nearest neighbor |
| R4 | Frequently-rare category | PAM | Partition around medoids |
| CoR | Curse of rarity | CLARA | Clustering large applications |
| SFA | Signal fragment assembler | COG | Classification using lOcal clusterinG |
| VAE | Variational autoencoder | BIRCH | Balanced iterative reducing and clustering |
| DP | Data picker | using hierarchies | |
| QC | Quality classifier | ARIMA | Autoregressive integrated moving average |
| MOA | Massive online analysis | VAR | Vector autoregression |
| WEKA | Waikato environment for knowledge analysis | GRU | Gated recurrent unit |
| PHQ | Patient health questionnaire | EMM | Extensible markov models |
| HIV | Human immunodeficiency virus | DNO | Deep neural operators |
| WWD | Wrong-way driving | FNACC | Faulty-normal accuracy |
| APS | Air pressure system | RFNACC | Real faulty-normal accuracy |
| SVD | Singular value decomposition | TP | True positives |
| MICE | Multiple imputation by chained equation | FN | False negatives |
| ANOVA | Analysis of variance | TN | True negatives |
| TL | Tomek links | FP | False positives |
| ENN | Edited nearest neighbors | TNR | True negative rate |
| RFE | Recursive feature elimination | FPR | False positive rate |
| HMM | Hidden markov model | FNR | False negative rate |
| DWT | Discrete wavelet transform | G-Mean | Geometric Mean |
| mRMR | Minimum redundancy maximum relevance | BER | Balanced error rate |
| TF-IDF | Term frequency-inverse document frequency | MCC | Matthews’s correlation coefficient |
| XGBoost | eXtreme Gradient Boosting | PR | Precision-Recall |
| MFCC | Mel-frequency cepstral coefficients | AUPRC | Area under precision-recall curve |
| MDI | Mean decrease in impurity | TDL | Top-decile lift |
| ROS | Random minority oversampling | TSS | True skill statistic |
| RUS | Random majority undersampling | SSE | Sum of squared errors |
| SMOTE | Synthetic minority oversampling technique | MAE | Mean absolute error |
| ADASYN | Adaptive synthetic sampling technique | RMSE | Root mean squared error |
| SMUTE | Similarity majority under-sampling technique | MAPE | Mean absolute percentage error |
| NCL | Neighborhood cleaning rule | MAD | Mean absolute deviation |
| NM | NearMiss | MAPD | Mean absolute percentage deviation |
| NM2 | NearMiss-2 | AUC-ROC | Area under the receiver operating |
| OSS | One-sided selection | characteristic curve | |
| CBO | Cluster-based oversampling | UQ | Uncertainty quantification |
|  |  | F2F | Factory to Factory |

![Mascot Sammy](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)
