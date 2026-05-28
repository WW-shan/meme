# What is data leakage in machine learning?

## Author

IBM Writer

Gather

## What is data leakage in machine learning?

Data leakage in [machine learning](https://www.ibm.com/think/topics/machine-learning?) occurs when a model uses information during training that wouldn't be available at the time of prediction. Leakage causes a predictive model to look accurate until deployed in its use case; then, it will yield inaccurate results, leading to poor decision-making and false insights.

The goal of [predictive modeling](https://www.ibm.com/think/topics/predictive-analytics?) is to create a machine learning model that can make accurate predictions on real-world future data, which is not available during model training. To avoid inaccurate results, models should not be evaluated on the same data they're trained on. So, data scientists typically split the available data into two sets: one for training the model and the other for validating how well the model will perform on unseen data.

## Would your team catch the next zero-day in time?

Join security leaders who rely on the Think Newsletter for curated news on AI, cybersecurity, data and automation. Learn fast from expert tutorials and explainers—delivered directly to your inbox twice weekly. See the [IBM Privacy Statement](https://www.ibm.com/privacy).

## Thank you!

You are subscribed.

## Examples and types of data leakage

Data leakage happens when data from outside the training dataset is used to create the model, but this future data will not be available when the model is used for prediction. The model will perform well in testing and validation, but when used in production, it becomes entirely inaccurate.

There are two types of leakage: **target leakage and** **train-test contamination**.

**Target leakage**: Models include data that will not be available when the model is used to make predictions.

Using information that won't be available during real-world predictions leads to [overfitting](https://www.ibm.com/think/topics/overfitting?), where the model performs exceptionally well on training and validation data but poorly in production.

**Train-test contamination**: When both training and validation data are used to create a model, often due to improper splitting or preprocessing.

### Target leakage example

For example, imagine a model created to predict credit card fraud. This issue is concerning in forecasting applications where models must make reliable future predictions based on incomplete data. The raw dataset will contain information about the customer, the transaction amount, the location, whether fraud was detected and if a chargeback was received.

In training the model, the fraud detection and chargeback columns will have true or false values entered. In the real world, a chargeback is typically initiated after fraud has been detected, so this information would not be available at the time of detection.

Training a model with this information teaches it that transactions with a chargeback are almost always fraudulent. During validation, the model will show high accuracy because, in training, the relationship between fraud and chargebacks is strong. However, the chargeback information will not be available when deployed and the model will perform poorly in practice**.**

### Train-test contamination example

Imagine a data scientist building a model to predict house prices based on features such as house size, number of bedrooms and neighborhood. Standardizing the numerical features (such as house size and age) so they all have the same scale is a common preprocessing step, which is helpful for many [machine learning algorithms](https://www.ibm.com/think/topics/machine-learning-algorithms?).

However, suppose that the data scientist applies standardization to the entire dataset before splitting it into training and test datasets. In that case, the model will indirectly "see" information from the test set during training. As a result, the model's performance on the test data might appear artificially inflated because the test set's information was used in the preprocessing step. This makes it easier for the model to perform well on the test set but potentially reduces its ability to generalize to new, unseen data.

Preprocessing steps such as scaling, imputation or feature selection should be fitted only on the training data and then applied to the validation set, rather than fitting them on the entire dataset before splitting. Misapplying transformers such as scaling or normalization can lead to train-test contamination, especially in neural network models. When these improperly executed preprocessing steps are performed over the whole dataset, it leads to biased predictions and an unrealistic sense of the model's performance.

### Win the enterprise AI race

Join Arvind Krishna to see how IBM is enabling AI-first enterprises through hybrid cloud and emerging quantum capabilities.

## Causes of data leakage

Data leakage can be a time-consuming and multi-million-dollar mistake and leakage in machine learning occurs due to a variety of factors. Some common causes are:

**Inclusion of future information**: When unavailable information that would not be available at the time of the prediction in a real-world scenario is used.

**Inappropriate feature selection**: Selecting features correlated with the target but not causally related. The model is learning to exploit information it wouldn't have access to in real-world predictions.

**External data contamination**: Merging external datasets with training data can lead to biased or inaccurate predictions, as external data can contain direct or indirect information about the target variable.

**Data preprocessing errors**: Incorrect data splitting happens with scaling the data before dividing it into training and validation sets or when filling in missing values with information from the entire dataset. This can be especially problematic in [deep learning](https://www.ibm.com/think/topics/deep-learning?) models, where extensive preprocessing is often required, making it crucial to avoid mixing training and test data.

**Incorrect cross-validation**: When performing cross-validation on a dataset with time-dependent data, if data points from the future are included, the model gains access to information it should not have, resulting in overly optimistic evaluations.

**Normalization:** Data transformations, such as scaling or normalizing features, when incorrectly applied to both training and test data together, rather than applied separately, lead to data leakage**.**

**Validation and process changes leakage**: Changing how validation is performed can introduce leakage by allowing new information into the training set. Adjusting the process partway by re-running cross-validation or re-splitting data after tweaking models can inadvertently leak information into the training process.

## Impact of data leakage on machine learning models

Data leakage is a common pitfall in training machine learning algorithms for predictive modeling. A National Library of Medicine study1 found that across 17 different scientific fields where machine learning methods have been applied, at least 294 scientific papers were affected by data leakage, leading to overly optimistic performance.

A Yale study2 found that data leakage can either inflate or deflate performance metrics of neuroimaging-based models, depending on whether the leaked information introduces noise or creates unrealistic patterns. These models are used for diagnosing illness to identify treatments and help neuroscientists better understand the relationship between brain and body.

Data leakage in machine learning models can have various impacts across different fields and data types, here are the most common:

**Poor generalization to new data**: When models are trained on information that does not represent the real world, the model will struggle to generalize to the unseen data. Predictions on new data might be inaccurate and unreliable.

**Biased decision-making**: Biases in leaked data run the risk of skewing model behavior, resulting in decisions that are unfair and divorced from real-world scenarios.

**Unreliable insights and findings**: Data leakage compromises the reliability of insights derived from the model leading users to mistrust the results.

**Inflated performance metrics**: Leakage in machine learning models often results in models falsely showing high accuracy and precision.

**Resource wastage**: Finding and fixing data leakage after a model has been trained is time-consuming and costly. Fixing data leakage requires retraining models from scratch, which is computationally expensive, and reworking the entire model pipeline, from data preprocessing to retraining, which can be resource-intensive in terms of human effort and computational costs.

**Loss of trust**: Unreliable models eventually lead to mistrust of data science teams and the overall analytical process.

**Legal and compliance risks**: Data leakage in predictive analytics can lead to legal and regulatory risks. If sensitive information is misused, it can result in penalties and reputation damage.

## Detecting data leakage in machine learning

Detecting data leakage requires organizations to be aware of how models are prepared and processed; it requires rigorous strategies for validating the integrity of machine learning models. Here are some best practices to keep in mind regarding constructing models and detecting data leakage:

**Prepare**: The data must be properly split and preprocessing steps should be applied only to the training dataset. Review all features to help ensure they do not represent future or unavailable information during prediction.

**Search**: After the model is trained, investigate suspicious patterns that might indicate leakage. Review feature importance and model behavior to detect any unrealistic relationships.

**Test**: Test a limited model with real-world data. Monitor its performance in real-world scenarios; if performance drops significantly, it might indicate that leakage has occurred during training.

Here are some common red flags for detecting leakage:

**Unusually high performance:** If a model shows significantly higher accuracy, precision or recall than expected, especially on validation data, it might indicate data leakage.

**Discrepancies between training and test performance**: A large gap between performance on the training set and test set is a sign that the model might be overfitting due to leakage.

**Inconsistent cross-validation results**: If performance across cross-validation folds varies greatly or seems unusually high, it might be due to train-test leakage or improper splitting.

**Unexpected model behavior**: If a model relies heavily on features that don't make sense logically, that might indicate leakage.

## Proper evaluation techniques

Minimizing data leakage can be accomplished in various ways and several tools are employed to safeguard model integrity. **Cross-validation**, particularly time-series or stratified k-fold, helps evaluate models correctly and highlights potential leakage. In [LLMs](https://www.ibm.com/think/topics/large-language-models?) (large language models), cross-validation and strict data handling are essential to avoid training the model on data it might later encounter during inference, which would undermine its ability to respond to new inputs. Using a separate **hold-out set** that remains untouched during training adds protection against leakage.

**Feature importance** can reveal if the model relies on data that wouldn't be available during predictions. [**Visualization**](https://www.ibm.com/think/topics/data-visualization?) of data and model predictions can expose patterns or anomalies indicative of leakage. Also, **domain experts** should scrutinize the model to identify if the model is using unrealistic or unavailable data, helping uncover problematic features.

## Preventing data leakage in machine learning

To prevent data leakage, organizations must engage in careful data handling and systematic evaluation. Here are some essential practices:

**Data preprocessing**: To prevent information leakage between sets, apply preprocessing steps such as scaling or imputing missing values separately for training and test sets. Perform preprocessing such as scaling, encoding and imputation separately for training and test sets—automate pipelines when possible.

**Proper data splitting**: Split training and test sets correctly. A carefully planned train/test split protects information from the test set from leaking into the training phase. For time-dependent data, split chronologically to prevent future data from entering the training process. To check for leakage, maintain a separate and distinct validation set not used during training, representative of real-world data.

**Cross-validation**: Use k-fold cross-validation to test the model on multiple subsets of the data, which helps catch potential leakage and improves generalization.

**Feature engineering**: Avoid creating features that introduce future data. Review derived features to confirm that they reflect only what would be available at prediction time. Regularly assess feature relevance to confirm they are appropriate and do not introduce unavailable information at prediction time.

**Time-based validation**: For time-series data, use time-based validation to mimic real-world performance. This helps ensure that past data is used to predict future outcomes and avoids future data leakage. Handle time-series data with care, using methods such as rolling window validation or walk-forward validation to avoid leakage from future data during training.

**Regular model evaluation**: Continuously monitor performance during training and testing to detect any unexpected changes indicating leakage.

## Data leakage in data loss prevention

There is another definition of [data leakage](https://www.ibm.com/think/topics/data-leakage) that has nothing to do with machine learning, but rather refers to unintended exposure of data from a data security perspective. Data leakage in [data loss prevention](https://www.ibm.com/think/topics/data-loss-prevention?) (DLP) occurs when sensitive information is unintentionally exposed to unauthorized parties. For example, a misconfigured [cloud storage](https://www.ibm.com/think/topics/cloud-storage?) server might allow easy access to personally identifiable information ([PII](https://www.ibm.com/think/topics/pii?)) and trade secrets.

The most common [vectors for data leakage stem](https://www.ibm.com/think/topics/attack-surface?) from human error such as an employee misplacing their laptop or sharing sensitive information over email and messaging platforms. Hackers can use exposed data to commit identity theft, steal credit card details or sell the data on the dark web.

Register for this webinar to learn how AI governance helps organizations manage risk, meet evolving regulations and build trusted, responsible AI at scale.

## Resources

Learn how to turn governance and security into drivers of resilience, smarter decision-making and confident growth with practical strategies from this buyer’s guide.

Gain insights to prepare and respond to cyberattacks with greater speed and effectiveness with the IBM X-Force® Threat Intelligence Index.

Join this webinar to explore practical strategies for operating and governing AI agents responsibly at scale, with expert insights on observability, risk management and accountable AI operations.

The KuppingerCole data security platforms report offers guidance and recommendations to find sensitive data protection and governance products that best meet clients’ needs.

Learn how to protect your data at every stage of its lifecycle in our webinars.

Discover the benefits and ROI of IBM Guardium® Data Protection in this Forrester TEI study.

Access this Gartner guide to learn how to manage the complete AI inventory and secure your AI workloads with guardrails. It also shows how to reduce risk and manage the governance process to achieve AI trust for all AI use cases in your organization.

Follow clear steps to complete tasks and learn how to effectively use technologies in your projects.

Identity and access management (IAM) is a cybersecurity discipline that deals with user access and resource permissions.

Protect your most critical data—discover, monitor and secure sensitive information across environments while automating compliance and reducing risk.

Protect data everywhere—discover, classify, monitor and secure sensitive information across your environment.

IBM provides comprehensive data security services to protect enterprise data, applications and AI.

Secure sensitive data and strengthen privacy controls across hybrid environments with centralized monitoring and automated risk reduction.

##### Footnotes
