# python-oslom-runner

An OSLOM Runner for Python. *OSLOM* stands for *Order Statistics Local Optimization Method* and it's a clustering algorithm designed for networks.

You can obtain a copy of OSLOM from: <http://www.oslom.org/>

More information on OSLOM can be found in the following publication:

> Lancichinetti, Andrea, et al. "Finding Statistically Significant Communities in Networks." PloS one 6.4 (2011): e18961.

## Installation

You can use `pip` (or any `PyPi`-compatible package manager) for installation:

    pip install oslom-runner

or, if you prefer a local user installation:

    pip install --user oslom-runner

## Usage

First, make sure you have a working copy of OSLOM installed. OSLOM version 2 is strongly recommended as it is faster with very similar clustering performance.

To use this runner you will need an input file with network edges in the same format OSLOM expects (`source`, `target`, `weight`).

The fields in this file must be `TAB` separated. For example:

    100 \t 200 \t 1
    200 \t 500 \t 1
    100 \t 500 \t 8

**NOTE:** OSLOM only supports 32-bits signed integers for node identifiers, however this runner supports string-based identifiers that are automatically re-mapped to the supported integers before calling OSLOM. Therefore, the number of **unique string identifiers** is still limited to `2^31 - 1`. An example edges file with string identifiers can be seen below:

    NodeA \t NodeB \t 1
    NodeB \t NodeC \t 1
    NodeA \t NodeC \t 8

You can then run OSLOM over the network using the following command:

    oslom-runner --edges myedges.tsv \
        --output-clusters clusters.json \
        --oslom-output oslom-files

After execution you will get a JSON formatted file with the clusters found by OSLOM from the provided network edges file.

This OSLOM Runner supports the following command line options:

* `--edges`: the network edges file in TSV (Tab-separated values) format.
* `--output-clusters`: the found clusters output file in JSON format.
* `--oslom-output`: the output directory to put resulting OSLOM files.
* `--min-cluster-size`: the minimum cluster size for filtering after running OSLOM. Default: `0`.
* `--oslom-exec`: the path (absolute or relative) to the OSLOM executable to invoke. Default: `oslom_dir`. You can use OSLOM in directed or undirected mode. See the [OSLOM documentation](http://www.oslom.org/code/ReadMe.pdf) for more information.

Finally, you can also pass custom OSLOM arguments (with the exception of the `-f` option!) after all options to the runner using the following command:

    oslom-runner --edges myedges.tsv \
        --output-clusters clusters.json \
        --oslom-output oslom-files \
        --oslom-exec /opt/oslom/oslom2_dir \
        -- -hr 1 -r 1

Please note the usage of double dashes (`--`) to separate the runner's own arguments from the OSLOM native ones.

The default arguments used for OSLOM are `-w -r 10 -hr 10`, which sets the usage of a weighted network and 10 computation iterations for first and higher hierarchical levels respectively.

When you pass your own OSLOM arguments, none of the default options will be used. You should **NEVER** give the `-f` option because the runner automatically fills the value for it accordingly.

## Using Programmatically

This OSLOM Runner can be used programmatically inside your own Python scripts as well.

There are two main functions to run OSLOM, both using nearly the same arguments:

* `run()`: reads input edges and writes output clusters directly on disk. Also outputs OSLOM auxiliary files to a given directory. This is the function used by the command-line interface.
* `run_in_memory()`: similar to `run()` but takes edges from a Python iterable and provides the clusters in a dictionary instead of files on disk. This function does not keep OSLOM auxiliary files. This function is useful for avoiding manual reading/writing of data on disk from your scripts.

The arguments for these functions must be a `Namespace` object from the `argparse` module. A working example for both functions is below:
```python
from argparse import Namespace
import oslom

# run OSLOM with files already on disk
args = Namespace()
args.edges = "/path/to/input_edges.tsv"
args.output_clusters = "/path/to/output_clusters.json"
args.oslom_output = "/path/to/oslom_aux_files"
args.min_cluster_size = oslom.DEF_MIN_CLUSTER_SIZE
args.oslom_exec = oslom.DEF_OSLOM_EXEC
args.oslom_args = oslom.DEF_OSLOM_ARGS
oslom.run(args)

# run OSLOM with data in Python objects
args = Namespace()
args.min_cluster_size = 0
args.oslom_exec = oslom.DEF_OSLOM_EXEC
args.oslom_args = oslom.DEF_OSLOM_ARGS

# edges is an iterable of tuples (source, target, weight)
# in the same format as the command-line version
edges = [(0, 1, 1.0), (1, 2, 1), (2, 0, 1)]
clusters = oslom.run_in_memory(args, edges)
print(clusters)
```

## License

This software is under the **Apache License 2.0**.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

