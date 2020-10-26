# gcvb

(G)enerate (C)ompute (V)alidate (B)enchmark

*gcvb* is a Python 3 module aiming at facilitating non-regression, validation and benchmarking of simulation codes.

*gcvb* is not a complete tool of continuous integration (CI). It is rather a component of the testing part of a CI workflow. It can compare the different metrics of your computation with references that can be a file, depends of the "configuration" or are absolute.

## Install gcvb

Clone this repository and in the directory run :
```
pip3 install .
```

or without git:

```
pip install --upgrade "gcvb[dashboard] @ https://github.com/jm-cc/gcvb/archive/master.zip"
```

## Getting started

As of today, the documentation is mainly available under the form of examples in the [gcvb-example repository](https://github.com/jm-cc/gcvb-examples).

## General philosophy

Input : 
- The "data" folder contains the input files and references.
- A config.yaml file contains relevant information for the current computing environment used.
- Multiple yaml files can then be use to indicate which tests to launch, store the references to detect a regression.

Output :
- a gcvb.db sqlite3 database that contains the metrics stored during runs, but also files you want to keep for each run.
- a "results" folder where the computation are actually computed.

Process :
- Given the input, the user can generate a *base*, that base can then be used for multiple *runs*. Each run compares with the reference and allows to check that everything is in order (or not). A run can launch a subset of the test of a base through filter options.

`gcvb` is mainly used with subcommands. It must be launch in the folder containing the input.

To access the help, just use `gcvb -h`. Help is also available for each subcommands (e.g. `gcvb generate -h`).

## Jobrunner

When launching computation with *compute*, by default a script is submitted.
It is also possible to launch a jobrunner that computes job in parallel. (*gcvb compute --with-jobrunner <num_cores>*)

Multiple jobrunner can be launched through *gcvb jobrunner <num_cores>*.

Note that there is no difference between a jobrunner launched through the *compute* options and by the *jobrunner* command.
It is possible to create the right entries in the database without launching a jobrunner or submit the default launch script with the option *--dry-run*

## Copyright and license

Copyright 2019 Airbus S.A.S

Code released under the MIT License.
