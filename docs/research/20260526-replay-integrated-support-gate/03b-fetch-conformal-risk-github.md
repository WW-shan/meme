## Navigation Menu

# Search code, repositories, users, issues, pull requests...

# Provide feedback

We read every piece of feedback, and take your input very seriously.

# Saved searches

## Use saved searches to filter your results more quickly

To see all available qualifiers, see our [documentation](https://docs.github.com/search-github/github-code-search/understanding-github-code-search-syntax).

# aangelopoulos/conformal-risk

## Folders and files

| Name | | Name | Last commit message | Last commit date |
| --- | --- | --- | --- | --- |
| Latest commit   History[27 Commits](/aangelopoulos/conformal-risk/commits/main/)   27 Commits | | |
| [coco](/aangelopoulos/conformal-risk/tree/main/coco "coco") | | [coco](/aangelopoulos/conformal-risk/tree/main/coco "coco") |  |  |
| [core](/aangelopoulos/conformal-risk/tree/main/core "core") | | [core](/aangelopoulos/conformal-risk/tree/main/core "core") |  |  |
| [hierarchical\_imagenet](/aangelopoulos/conformal-risk/tree/main/hierarchical_imagenet "hierarchical_imagenet") | | [hierarchical\_imagenet](/aangelopoulos/conformal-risk/tree/main/hierarchical_imagenet "hierarchical_imagenet") |  |  |
| [polyps](/aangelopoulos/conformal-risk/tree/main/polyps "polyps") | | [polyps](/aangelopoulos/conformal-risk/tree/main/polyps "polyps") |  |  |
| [qa](/aangelopoulos/conformal-risk/tree/main/qa "qa") | | [qa](/aangelopoulos/conformal-risk/tree/main/qa "qa") |  |  |
| [.gitignore](/aangelopoulos/conformal-risk/blob/main/.gitignore ".gitignore") | | [.gitignore](/aangelopoulos/conformal-risk/blob/main/.gitignore ".gitignore") |  |  |
| [LICENSE](/aangelopoulos/conformal-risk/blob/main/LICENSE "LICENSE") | | [LICENSE](/aangelopoulos/conformal-risk/blob/main/LICENSE "LICENSE") |  |  |
| [README.md](/aangelopoulos/conformal-risk/blob/main/README.md "README.md") | | [README.md](/aangelopoulos/conformal-risk/blob/main/README.md "README.md") |  |  |
| [environment.yml](/aangelopoulos/conformal-risk/blob/main/environment.yml "environment.yml") | | [environment.yml](/aangelopoulos/conformal-risk/blob/main/environment.yml "environment.yml") |  |  |
| View all files | | |

## Latest commit

## History

## Repository files navigation

# Conformal Risk Control

This is the official repository of [Conformal Risk Control](http://arxiv.org/abs/2208.02814) by Anastasios N. Angelopoulos, Stephen Bates, Adam Fisch, Lihua Lei, and Tal Schuster.

[![](https://camo.githubusercontent.com/769fb231668f02155dd01c89bea0c6077702af13af79321ca4a1bf9d79aa177b/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f70617065722d61725869762d726564)](http://arxiv.org/abs/2208.02814)
 [![](https://camo.githubusercontent.com/032c76010df477483fa091a01cbcaf9033357630cda13adeaf7bb64bed135072/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f776562736974652d4265726b656c65792d79656c6c6f77)](https://people.eecs.berkeley.edu/%7Eangelopoulos/)
 [![](https://camo.githubusercontent.com/8c31286dd060b773bd1b4bea209901f9d016caf0629fec95a544d349f5166ecd/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f636f6e64612d656e762d677265656e)](https://docs.conda.io/en/latest/miniconda.html)
 [![](https://camo.githubusercontent.com/7013272bd27ece47364536a221edb554cd69683b68a46fc0ee96881174c4214c/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6c6963656e73652d4d49542d626c75652e737667)](https://opensource.org/licenses/MIT)

![](https://camo.githubusercontent.com/769fb231668f02155dd01c89bea0c6077702af13af79321ca4a1bf9d79aa177b/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f70617065722d61725869762d726564)
![](https://camo.githubusercontent.com/032c76010df477483fa091a01cbcaf9033357630cda13adeaf7bb64bed135072/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f776562736974652d4265726b656c65792d79656c6c6f77)
![](https://camo.githubusercontent.com/8c31286dd060b773bd1b4bea209901f9d016caf0629fec95a544d349f5166ecd/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f636f6e64612d656e762d677265656e)
![](https://camo.githubusercontent.com/7013272bd27ece47364536a221edb554cd69683b68a46fc0ee96881174c4214c/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6c6963656e73652d4d49542d626c75652e737667)

## Technical background

In the risk control problem, we are given some loss function $L\_i(\lambda) = \ell(X\_i,Y\_i,\lambda)$.
For example, in multi-label classification, you can think of the loss function as the false negative proportion $L\_i(\lambda) = 1 - \frac{|Y\_{i} \cap C\_{\lambda}(X\_{i})|}{|Y\_i|}$, where $C\_{\lambda}(X\_{i})$ is the set-valued output of a machine learning model.
As $\lambda$ grows, so does the set $C\_{\lambda}(X\_{i})$, which shrinks the false negative proportion.
We seek to choose $\hat{\lambda}$ based on the first $n$ data points to control the expected value of its loss *on a new test point* at some user-specified risk level $\alpha$, $$\mathbb{E}\big[L\_{n+1}(\hat{\lambda})\big] \leq \alpha.$$

The conformal risk control algorithm is in `core/get_lhat.py`. It is 5 lines long, including the function header.

`core/get_lhat.py`

## Examples

Each of the `{polyps, coco, hierarchical-imagenet, qa}` folders contains a worked example of conformal risk control with a different risk function.
`polyps` does gut polyp segmentation with false negative rate control. `coco` does multi-label classification with false negative rate control. `hierarchical-imagenet` does hierarchical classification and chooses the resolution of its prediction by bounding the graph distance to an ancestor of the true label. Finally, `qa` controls the F1-score in open-world question answering.

`{polyps, coco, hierarchical-imagenet, qa}`
`polyps`
`coco`
`hierarchical-imagenet`
`qa`

### Setup

For the computer vision experiments, run

 `conda env create -f environment.yml
conda activate conformal-risk`

This will install all dependencies for the vision experiments.

For the question-answering task, follow the instructions in `qa/README.md`.

`qa/README.md`

### Reproducing the experiments

After setting up the environment, enter the example folder and run the appropriate `risk_histogram.py` file.
To produce the grids of images in the paper, run the python file containing the word `grid` in each folder.

`risk_histogram.py`
`grid`

### Citation

`@article{angelopoulos2022conformal,
title={Conformal Risk Control},
author={Angelopoulos, Anastasios N and Bates, Stephen and Fisch, Adam and Lei, Lihua and Schuster, Tal},
journal={arXiv preprint arXiv:2208.02814},
year={2022}
}`

## About

Conformal prediction for controlling monotonic risk functions. Simple accompanying PyTorch code for conformal risk control in computer vision and natural language processing.

### Topics

### Resources

### License

### Uh oh!

There was an error while loading. Please reload this page.

There was an error while loading. Please reload this page.

### Stars

### Watchers

### Forks

## [Releases](/aangelopoulos/conformal-risk/releases)

## [Packages 0](/users/aangelopoulos/packages?repo_name=conformal-risk)

### Uh oh!

There was an error while loading. Please reload this page.

There was an error while loading. Please reload this page.

### Uh oh!

There was an error while loading. Please reload this page.

There was an error while loading. Please reload this page.

## [Contributors](/aangelopoulos/conformal-risk/graphs/contributors)

### Uh oh!

There was an error while loading. Please reload this page.

There was an error while loading. Please reload this page.

## Languages

## Footer

### Footer navigation
