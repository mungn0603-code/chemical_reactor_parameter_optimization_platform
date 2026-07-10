# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                            |    Stmts |     Miss |   Cover |   Missing |
|------------------------------------------------ | -------: | -------: | ------: | --------: |
| reactor\_platform/\_\_init\_\_.py               |        1 |        0 |    100% |           |
| reactor\_platform/core/\_\_init\_\_.py          |        0 |        0 |    100% |           |
| reactor\_platform/core/energy.py                |       74 |        3 |     96% |114-115, 138 |
| reactor\_platform/core/explain.py               |       27 |        0 |    100% |           |
| reactor\_platform/core/kinetics.py              |       11 |        0 |    100% |           |
| reactor\_platform/core/reactions.py             |      138 |       14 |     90% |35, 124, 136, 156-160, 174, 177, 186, 223-225, 231, 234 |
| reactor\_platform/core/reactors/\_\_init\_\_.py |        3 |        0 |    100% |           |
| reactor\_platform/core/reactors/base.py         |       45 |        1 |     98% |        73 |
| reactor\_platform/core/reactors/cstr.py         |       73 |       12 |     84% |28, 38, 93-94, 116-117, 119-120, 122-123, 125-126 |
| reactor\_platform/core/scenario\_lab.py         |       75 |        1 |     99% |        33 |
| reactor\_platform/core/thermo.py                |       78 |        4 |     95% |27, 106-107, 130 |
| reactor\_platform/core/units.py                 |       28 |        9 |     68% |62-64, 69, 75, 82-85 |
| reactor\_platform/eda/\_\_init\_\_.py           |        8 |        0 |    100% |           |
| reactor\_platform/eda/history.py                |       53 |        2 |     96% |    73, 80 |
| reactor\_platform/eda/outlier.py                |       73 |       10 |     86% |48, 62, 76, 84-88, 118-120 |
| reactor\_platform/eda/preprocessing.py          |      100 |       21 |     79% |80-81, 88, 95, 112, 128, 133, 135, 144-145, 147, 149, 160, 162, 164-165, 167-169, 175, 190 |
| reactor\_platform/eda/profile.py                |      157 |        8 |     95% |64-67, 86, 88, 118, 175 |
| reactor\_platform/eda/recommendation.py         |      129 |        8 |     94% |90-91, 121, 201, 227, 265-267 |
| reactor\_platform/eda/report.py                 |      106 |        4 |     96% |110, 136, 175, 177 |
| reactor\_platform/eda/sample.py                 |       24 |        0 |    100% |           |
| reactor\_platform/eda/visualization.py          |       81 |        6 |     93% |50, 86-87, 92, 134, 138 |
| reactor\_platform/parameters/\_\_init\_\_.py    |        4 |        0 |    100% |           |
| reactor\_platform/parameters/registry.py        |       53 |       10 |     81% |29, 35, 47, 63, 81-86 |
| reactor\_platform/parameters/schema.py          |       31 |        2 |     94% |    76, 82 |
| reactor\_platform/parameters/validators.py      |       32 |        1 |     97% |        43 |
| **TOTAL**                                       | **1404** |  **116** | **92%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fmungn0603-code%2Fchemical_reactor_parameter_optimization_platform%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.