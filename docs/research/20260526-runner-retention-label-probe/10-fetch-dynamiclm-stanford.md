## [The Han Lab](https://med.stanford.edu/summerhanlab.html)

### Explore Stanford Medicine

### Find a doctor

### Clinics & Services

### Locations

### Explore Health Care

Learn how we are healing patients through science & compassion

### Research Resources

### Professional Training

### Research News

![Neuroscientist Michelle Monje awarded MacArthur 'genius grant'](/content/dam/sm-news/images/2021/09/monje-michelle.jpg/jcr:content/renditions/original)

Neuroscientist Michelle Monje awarded MacArthur 'genius grant'

### Explore Research

Learn how we are fueling innovation

### Education Resources

### Education News

![Alice L. Walton School of Medicine and Stanford Medicine host AI conference on community health](/content/dam/sm-news/images/2025/01/minor-and-walton.jpg/jcr:content/renditions/original)

Alice L. Walton School of Medicine and Stanford Medicine host AI conference on community health

### Explore Education

Learn how we empower tomorrow's leaders

### Support Stanford Medicine

[Support teaching, research, and patient care.](//medicalgiving.stanford.edu)

### Support Children's Health

[Support Lucile Packard Children's Hospital Stanford and child and maternal health](https://lpfch.org/)

[Stanford School of Medicine](//med.stanford.edu/school.html)

[Stanford Health Care](http://stanfordhealthcare.org)

[Stanford Children's Health](http://www.stanfordchildrens.org)

## dynamicLM: Landmark Supermodel for Dynamic Risk Prediction in Time-to-Event Data with Competing Risk

## Introduction

Dynamic risk prediction is crucial because it allows for continuously updating an individual's risk profile over time. Traditional risk models typically offer a static risk assessment based on data available at a single point, such as diagnosis. However, dynamic risk prediction accounts for changes in a patient's condition, treatments, and other relevant factors as they occur. This approach provides more accurate and personalized risk assessments - essential for effective clinical decision-making and patient management.

The *dynamicLM* tool provides a simple framework to perform dynamic *w*-year risk predictions, i.e. predicting the risk of developing the event of interest within *w* years from each risk assessment. Risk prediction for the next years is made at baseline (e.g. diagnosis) and a later set of risk assessment times (‘landmark’ times).

## Model Development and Implementation

The landmark model for survival data is a powerful approach for dynamically predicting disease progression. It is computationally feasible and interpretable. However, there has been a need for a flexible, comprehensive framework that can handle diverse outcomes, including competing events. **dynamicLM**, our R package and framework, addresses this gap. It offers a user-friendly implementation of the landmark supermodel for survival data with competing risks. This package includes advanced functionalities for data preparation, model development, prediction, and evaluation. Additionally, dynamicLM integrates penalization techniques for high-dimensional data (handling numerous longitudinal variables tractably) and novel model-agnostic summary metrics (which average performance over time) for robust evaluation of predictive performance.

![dynamicLM-predictions](https://med.stanford.edu/summerhanlab/software/dynamiclm/_jcr_content/main/panel_builder_copy/panel_0/panel_builder/panel_0/panel_builder_copy/panel_0/image.img.620.high.png/dynamicLM-prediction.png)

## Application

We applied the penalized landmark supermodel to assess the dynamic (updated) risk of lung cancer-specific mortality. Our study uses static and longitudinal data sources. The static SEER cancer registry (2007-2018) provides tumor characteristics and initial cancer treatment details at diagnosis for U.S. patients. The longitudinal sources include the Medicare Health Outcome Survey (MHOS, 2006-2018) [31], administered biennially to Medicare Advantage enrollees to collect patient-reported outcome data, Medicare Part D Insurance Claims (2007-2018), which documents prescription drug purchases, and the U.S. Census, combining data from the 1990 and 2000 Censuses and the 2008-2012 American Community Survey, to provide neighborhood-based socio-economic data.

Using the framework, we identified key predictors of lung cancer-specific mortality and evaluated the penLM supermodel for predicting 5-year lung cancer mortality using the multi-source data, both shown below. Using the proposed summary metric, we demonstrated significantly higher discrimination using multi-source data vs. four models using single-source data (P < 0.05), thus highlighting the importance of considering diverse risk factors.

![dynamicLM-keyfeatures](https://med.stanford.edu/summerhanlab/software/dynamiclm/_jcr_content/main/panel_builder_copy/panel_0/panel_builder/panel_0/panel_builder/panel_0/image.img.620.high.png/dynamicLM key-features.png)
![dynamicLM-auc](https://med.stanford.edu/summerhanlab/software/dynamiclm/_jcr_content/main/panel_builder_copy/panel_0/panel_builder/panel_0/panel_builder/panel_1/image.img.620.high.png/dynamicLM_auc.png)

## Availability

The dynamicLM R package is freely available on GitHub: <https://github.com/thehanlab/dynamicLM>

## Contacts

Summer S. Han, Ph.D., Principal Investigator  
Anya H. Fries, M.S., Main programmer  
Eunji Choi, Ph.D., Main programmer

Questions and comments should be addressed to [summer.han@stanford.edu](mailto:summer.han@stanford.edu)

## Reference

Anya H Fries\*, Eunji Choi\*, Julie T Wu, Justin H Lee, Victoria Y Ding, Robert J Huang, Su-Ying Liang, Heather A Wakelee, Lynne R Wilkens, Iona Cheng, Summer S Han, Software Application Profile: *dynamicLM*—a tool for performing dynamic risk prediction using a landmark supermodel for survival data under competing risks, *International Journal of Epidemiology*, Volume 52, Issue 6, December 2023, Pages 1984–1989, <https://doi.org/10.1093/ije/dyad122>

## [The Han Lab](https://med.stanford.edu/summerhanlab.html)

## [The Han Lab](https://med.stanford.edu/summerhanlab.html)

### [Stanford Medicine](https://med.stanford.edu/)

[News](https://med.stanford.edu/news.html)

[Careers](https://medcareers.stanford.edu/)

[Contact](https://med.stanford.edu/about/contacts.html)

### [Health Care](https://med.stanford.edu/health-care.html)

[Stanford Health Care](https://stanfordhealthcare.org/)

[Stanford Children's Health](https://www.stanfordchildrens.org/)

### [Stanford School of Medicine](//med.stanford.edu)

[About](https://med.stanford.edu/school.html)

[Contact](https://med.stanford.edu/school/contacts.html)

[Maps & Directions](https://med.stanford.edu/school/contacts/maps.html)

[Careers](https://medcareers.stanford.edu/)

[Basic Science Departments](https://med.stanford.edu/school/directory/basic-science-departments.html)

[Clinical Science Departments](https://med.stanford.edu/school/directory/clinical-science-departments.html)

[Academic Programs](https://med.stanford.edu/education.html)

[Vision](https://med.stanford.edu/about/vision.html)

#### Non-Discrimination

Stanford complies with all applicable civil rights laws and does not engage in illegal preferences or discrimination.
  
[Stanford's Non-Discrimination Policy](https://bulletin.stanford.edu/academic-polices/student-conduct-rights/nondiscrimination)
