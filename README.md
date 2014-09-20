python-oslom-runner
===================

An OSLOM Runner for Python. OSLOM means Order Statistics Local Optimization Method and it's a clustering algorithm designed for networks. You can obtain a copy of OSLOM from [http://www.oslom.org/](http://www.oslom.org/).

Usage
-----

First, make sure you have a working copy of OSLOM installed. OSLOM version 2 is strongly recommended as it is faster with very similar clustering performance.

To use this runner, you will need an input file with network edges in the same format OSLOM expects: (```source```, ```target```, ```weight```). The fields in this file must be ```TAB``` separated. For example:

```
100 \t 200 \t 1
200 \t 500 \t 1
100 \t 500 \t 8
```

Then you can run OSLOM over this network in the following way:

```
$ ./run_oslom.py --user-edges myedges.tsv --output-communities communities.json --oslom-output oslom-files
```

The OSLOM Runner supports the following command line options:

* ```--user-edges```: user edges file in TSV (Tab-separated values) format.
* ```--output-communities```: output found communities file in JSON format.
* ```--oslom-output```: output directory to put resulting OSLOM files.
* ```--min-comm-size```: minimum community size for filtering after running OSLOM. Default: ```0```.
* ```--oslom-exec```: path to OSLOM executable to invoke. Default: ```oslom_dir```. You can use OSLOM in directed or undirected mode. See the OSLOM documentation.

Finally, you can also pass custom OSLOM arguments (with the exception of the ```-f``` option!) after all options to the runner in the following way:

```
$ ./run_oslom.py --user-edges myedges.tsv --output-communities communities.json --oslom-output oslom-files --oslom-exec /opt/oslom/oslom2_dir -- -hr 1 -r 1
```

Please note the usage of double dashes (```--```) to separate the own runner arguments from the OSLOM native options. The default arguments for OSLOM are ```-w -r 10 -hr 10```, which sets the usage of a weighted network and 10 computation iterations for first and higher hierarchical levels respectively. When you pass your own OSLOM arguments, none of the default options are used. You should *NOT* give the ```-f``` option because the runner automatically fills the value for it.
