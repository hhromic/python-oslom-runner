# An OSLOM (community finding) runner for Python
# Copyright 2014 Hugo Hromic
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# OSLOM -- the community finding algorithm -- is described in:
# Lancichinetti, Andrea, et al. "Finding Statistically Significant
# Communities in Networks." PloS one 6.4 (2011): e18961.

"""An OSLOM Runner for Python."""

import sys
import os
import argparse
import re
import tempfile
import shutil
import time
import subprocess
import itertools
import logging
import simplejson as json

# Defaults
DEF_MIN_CLUSTER_SIZE = 0
DEF_OSLOM_EXEC = "oslom_dir"
DEF_OSLOM_ARGS = ["-w", "-r", "10", "-hr", "10"]

# Constants
OSLOM_LOG_FILE = "oslom.log"

class IdRemapper(object):
    """Maps string Ids into 32 bits signed integer Ids starting from 0."""
    INT_MAX = 2147483647

    def __init__(self):
        """Construct a new Id Remapper class instance."""
        self.curr_id = 0
        self.mapping = {}
        self.r_mapping = {}

    def get_int_id(self, str_id):
        """Get a unique 32 bits signed integer for the given string Id."""
        if not str_id in self.mapping:
            if self.curr_id == IdRemapper.INT_MAX:
                return None # No more 32 bits signed integers available
            self.mapping[str_id] = self.curr_id
            self.r_mapping[self.curr_id] = str_id
            self.curr_id += 1
        return self.mapping[str_id]

    def get_str_id(self, int_id):
        """Get the original string Id for the given signed integer Id."""
        return self.r_mapping[int_id] if int_id in self.r_mapping else None

    def store_mapping(self, path):
        """Store the current Id mappings into a TSV file."""
        with open(path, "w") as writer:
            for key, value in self.mapping.iteritems():
                writer.write("{}\t{}\n".format(key, value))

class OslomRunner(object):
    """Handles the execution of OSLOM."""
    TMP_EDGES_FILE = "edges.tsv"
    OUTPUT_FILE = "tp"
    SEED_FILE = "time_seed.dat"
    IDS_MAPPING_FILE = "ids_mapping.tsv"
    ARGS_FILE = "args.txt"
    RE_INFOLINE = re.compile(r"#module (.+) size: (.+) bs: (.+)", re.I)

    def __init__(self, working_dir):
        """Construct a new OSLOM Runner class instance."""
        self.id_remapper = IdRemapper()
        self.working_dir = working_dir
        self.last_result = None

    def get_path(self, filename):
        """Get the full path to a file using the current working directory."""
        return os.path.join(self.working_dir, filename)

    def store_edges(self, edges):
        """Store the temporary network edges input file with re-mapped Ids."""
        with open(self.get_path(OslomRunner.TMP_EDGES_FILE), "w") as writer:
            for edge in edges:
                writer.write("{}\t{}\t{}\n".format(
                    self.id_remapper.get_int_id(edge[0]),
                    self.id_remapper.get_int_id(edge[1]),
                    edge[2]))

    def run(self, oslom_exec, oslom_args, log_filename):
        """Run OSLOM and wait for the process to finish."""
        args = [oslom_exec, "-f", self.get_path(OslomRunner.TMP_EDGES_FILE)]
        args.extend(oslom_args)
        with open(log_filename, "w") as logwriter:
            start_time = time.time()
            retval = subprocess.call(
                args, cwd=self.working_dir,
                stdout=logwriter, stderr=subprocess.STDOUT)
            self.last_result = {
                "args": args, "retval": retval,
                "time": time.time() - start_time,
                "output_dir": self.get_path(
                    "{}_oslo_files".format(OslomRunner.TMP_EDGES_FILE))
            }
            return self.last_result

    def read_clusters(self, min_cluster_size):
        """Read and parse OSLOM clusters output file."""
        num_found = 0
        clusters = []
        with open(self.get_path(OslomRunner.OUTPUT_FILE), "r") as reader:
            # Read the output file every two lines
            for line1, line2 in itertools.izip_longest(*[reader] * 2):
                info = OslomRunner.RE_INFOLINE.match(line1.strip()).groups()
                nodes = line2.strip().split(" ")
                if len(nodes) >= min_cluster_size: # Apply min_cluster_size
                    clusters.append({
                        "id": int(info[0]),
                        "bs": float(info[2]),
                        "nodes": [{"id": self.id_remapper.get_str_id(int(n))} for n in nodes],
                    })
                num_found += 1
        return {"num_found": num_found, "clusters": clusters}

    def store_output_files(self, dir_path):
        """Store OSLOM output files to a directory."""
        if self.last_result:
            for entry in os.listdir(self.last_result["output_dir"]):
                path = os.path.join(self.last_result["output_dir"], entry)
                if os.path.isfile(path):
                    shutil.copy(path, os.path.join(dir_path, entry))
            shutil.copy(
                self.get_path(OslomRunner.SEED_FILE),
                os.path.join(dir_path, OslomRunner.SEED_FILE))
            args_file = os.path.join(dir_path, OslomRunner.ARGS_FILE)
            with open(args_file, "w") as writer:
                writer.write("{}\n".format(" ".join(self.last_result["args"])))
            self.id_remapper.store_mapping(
                os.path.join(dir_path, OslomRunner.IDS_MAPPING_FILE))

    def cleanup(self):
        """Clean the working directory."""
        shutil.rmtree(self.working_dir)

def run(args):
    """Main OSLOM runner function."""
    # Create an OSLOM runner with a temporary working directory
    oslom_runner = OslomRunner(tempfile.mkdtemp())

    # (Re-)create OSLOM output directory
    shutil.rmtree(args.oslom_output, ignore_errors=True)
    os.makedirs(args.oslom_output)

    # Read edges file
    logging.info("reading edges file: %s", args.edges)
    edges = []
    with open(args.edges, "r") as reader:
        for line in reader:
            source, target, weight = line.strip().split("\t", 2)
            edges.append((source, target, weight))
    logging.info("%d edge(s) found", len(edges))

    # Write temporary edges file with re-mapped Ids
    logging.info("writing temporary edges file with re-mapped Ids ...")
    oslom_runner.store_edges(edges)

    # Run OSLOM
    logging.info("running OSLOM ...")
    result = oslom_runner.run(
        args.oslom_exec, args.oslom_args,
        os.path.join(args.oslom_output, OSLOM_LOG_FILE))
    if result["retval"] != 0:
        logging.error("error running OSLOM, check the log file")
        return False
    logging.info("OSLOM executed in %.3f secs", result["time"])

    # Read back clusters found by OSLOM
    logging.info("reading OSLOM clusters output file ...")
    clusters = oslom_runner.read_clusters(args.min_cluster_size)
    logging.info(
        "found %d cluster(s) and %d with size >= %d",
        clusters["num_found"], len(clusters["clusters"]), args.min_cluster_size)

    # Write clusters file
    logging.info("writing output clusters file: %s", args.output_clusters)
    with open(args.output_clusters, "w") as writer:
        json.dump(clusters["clusters"], writer, separators=(",", ":"))

    # Store OSLOM output files
    logging.info("writing OSLOM output files ...")
    oslom_runner.store_output_files(args.oslom_output)

    # Clean-up temporary working directory
    oslom_runner.cleanup()

    # Finished
    logging.info("finished")
    return True

def run_in_memory(args, edges):
    """Run OSLOM with an in-memory list of edges, return in-memory results."""
    # Create an OSLOM runner with a temporary working directory
    oslom_runner = OslomRunner(tempfile.mkdtemp())

    # Write temporary edges file with re-mapped Ids
    logging.info("writing temporary edges file with re-mapped Ids ...")
    oslom_runner.store_edges(edges)

    # Run OSLOM
    logging.info("running OSLOM ...")
    log_file = os.path.join(oslom_runner.working_dir, OSLOM_LOG_FILE)
    result = oslom_runner.run(args.oslom_exec, args.oslom_args, log_file)
    with open(log_file, "r") as reader:
        oslom_log = reader.read()
    if result["retval"] != 0:
        logging.error("error running OSLOM, check the log")
        return (None, oslom_log)
    logging.info("OSLOM executed in %.3f secs", result["time"])

    # Read back clusters found by OSLOM
    logging.info("reading OSLOM clusters output file ...")
    clusters = oslom_runner.read_clusters(args.min_cluster_size)
    logging.info(
        "found %d cluster(s) and %d with size >= %d",
        clusters["num_found"], len(clusters["clusters"]), args.min_cluster_size)

    # Clean-up temporary working directory
    oslom_runner.cleanup()

    # Finished
    logging.info("finished")
    return (clusters, oslom_log)

def main():
    """Main interface function for the command line."""
    # Setup logging for the command line
    name = os.path.splitext(os.path.basename(__file__))[0]
    logging.basicConfig(
        format="%(asctime)s [%(process)s] %(levelname)s {} - %(message)s".format(name),
        level=logging.INFO)

    # Program arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edges", metavar="FILENAME", required=True,
                        help="input network edges file in TSV format")
    parser.add_argument("--output-clusters", metavar="FILENAME", required=True,
                        help="output clusters file in JSON format")
    parser.add_argument("--oslom-output", metavar="DIRECTORY", required=True,
                        help="output directory for OSLOM files")
    parser.add_argument("--min-cluster-size", metavar="INTEGER", type=int,
                        default=DEF_MIN_CLUSTER_SIZE,
                        help="minimum cluster size (default: %(default)s)")
    parser.add_argument("--oslom-exec", metavar="EXECUTABLE",
                        default=DEF_OSLOM_EXEC,
                        help="OSLOM executable program to use "
                             "(default: %(default)s)")
    parser.add_argument("oslom_args", metavar="OSLOM_ARG", nargs="*",
                        default=DEF_OSLOM_ARGS,
                        help="argument to pass to OSLOM (don't pass '-f' !) "
                             "(default: %(default)s)")

    # Run OSLOM with parsed arguments
    sys.exit(not run(parser.parse_args()))

if __name__ == "__main__":
    main()
