# gcvb

(G)enerate (C)ompute (V)alidate (B)enchmark

*gcvb* is a Python 3 module aiming at facilitating non-regression, validation and benchmarking of simulation codes.

*gcvb* is not a complete tool of continuous integration (CI). It is rather a component of the testing part of a CI workflow. It can compare the different metrics of your computation with references that can be a file, depends of the "configuration" or are absolute.

## Install gcvb

Clone this repository and in the directory run :
```
pip3 install .
```

## Getting started

As of today, the documentation is mainly available under the form of examples in the [gcvb-example repository](https://github.com/jm-cc/gcvb-examples).

## Jobrunner

When launching computation with *compute*, by default a script is submitted.
It is also possible to launch a jobrunner that computes job in parallel. (*gcvb compute --with-jobrunner <num_cores>*)

Multiple jobrunner can be launched through *gcvb jobrunner <num_cores>*.

## Copyright and license

Copyright 2019 Airbus S.A.S

Code released under the MIT License.