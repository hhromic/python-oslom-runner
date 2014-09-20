#!/usr/bin/env python
# Hugo Hromic - http://github.com/hhromic

"""Run OSLOM over a list of edges and process the output clusters."""

import sys
import os
import argparse
import re
import tempfile
import shutil
import time
import subprocess
import itertools
import json
import logging

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
        args += oslom_args
        with open(log_filename, "w") as logwriter:
            start_time = time.time()
            retval = subprocess.call(args, cwd=self.working_dir,
                stdout=logwriter, stderr=subprocess.STDOUT)
            self.last_result = {"args": args, "retval": retval,
                "time": time.time() - start_time,
                "output_dir": self.get_path("{}_oslo_files".format(
                OslomRunner.TMP_EDGES_FILE))}
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
                    clusters += [{"id": int(info[0]), "bs": float(info[2]),
                        "nodes": [{"id": self.id_remapper.get_str_id(int(n))}
                        for n in nodes]}]
                num_found += 1
        return {"num_found": num_found, "clusters": clusters}
    def store_output_files(self, dir_path):
        """Store OSLOM output files to a directory."""
        if self.last_result:
            for entry in os.listdir(self.last_result["output_dir"]):
                path = os.path.join(self.last_result["output_dir"], entry)
                if os.path.isfile(path):
                    shutil.copy(path, os.path.join(dir_path, entry))
            shutil.copy(self.get_path(OslomRunner.SEED_FILE),
                os.path.join(dir_path, OslomRunner.SEED_FILE))
            args_file = os.path.join(dir_path, OslomRunner.ARGS_FILE)
            with open(args_file, "w") as writer:
                writer.write("{}\n".format(" ".join(self.last_result["args"])))
            self.id_remapper.store_mapping(os.path.join(dir_path,
                OslomRunner.IDS_MAPPING_FILE))
    def cleanup(self):
        """Clean the working directory."""
        shutil.rmtree(self.working_dir)

def run_oslom(args):
    """Main OSLOM runner function."""
    # Create an OSLOM runner with a temporary working directory
    oslom_runner = OslomRunner(tempfile.mkdtemp())

    # (Re-)create OSLOM output directory
    shutil.rmtree(args.oslom_output, ignore_errors=True)
    os.makedirs(args.oslom_output)

    # Read edges file
    logging.info("Reading edges file ...")
    edges = []
    with open(args.edges, "r") as reader:
        for line in reader:
            source, target, weight = line.strip().split("\t", 2)
            edges += [(source, target, weight)]
    logging.info("{} edge(s) found.".format(len(edges)))

    # Write temporary edges file with re-mapped Ids
    logging.info("Writing temporary edges file with re-mapped Ids ...")
    oslom_runner.store_edges(edges)

    # Run OSLOM
    logging.info("Running OSLOM ...")
    result = oslom_runner.run(args.oslom_exec, args.oslom_args,
        os.path.join(args.oslom_output, OSLOM_LOG_FILE))
    if result["retval"] != 0:
        logging.info("Error running OSLOM. Check the log file.")
        return False
    logging.info("OSLOM2 execution time: {:.3f} secs.".format(result["time"]))

    # Read back clusters found by OSLOM
    logging.info("Reading OSLOM clusters output file ...")
    clusters = oslom_runner.read_clusters(args.min_cluster_size)
    logging.info("{} cluster(s) found, {} with minimum required size.".format(
        clusters["num_found"], len(clusters["clusters"])))

    # Write clusters file
    logging.info("Writing clusters file ...")
    with open(args.output_clusters, "w") as writer:
        json.dump(clusters["clusters"], writer, separators=(",",":"))

    # Store OSLOM output files
    logging.info("Writing OSLOM output files ...")
    oslom_runner.store_output_files(args.oslom_output)

    # Clean-up temporary working directory
    oslom_runner.cleanup()

    # Finished
    logging.info("Finished.")
    return True

def main():
    """Main interface function for the command line."""
    # Setup logging for the command line
    name = os.path.splitext(os.path.basename(__file__))[0]
    logging.basicConfig(format="%(asctime)s [{}] %(message)s".format(name),
        level=logging.INFO)

    # Program arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edges", metavar="FILE", required=True,
        help="input network edges file (TSV format)")
    parser.add_argument("--output-clusters", metavar="FILE", required=True,
        help="output clusters file (JSON format)")
    parser.add_argument("--min-cluster-size", metavar="INT", required=False,
        help="minimum cluster size", type=int, default=DEF_MIN_CLUSTER_SIZE)
    parser.add_argument("--oslom-output", metavar="DIRECTORY", required=True,
        help="output directory for OSLOM files")
    parser.add_argument("--oslom-exec", metavar="PROGRAM", required=False,
        help="OSLOM executable path to use", default=DEF_OSLOM_EXEC)
    parser.add_argument("oslom_args", metavar="OSLOM_ARG", nargs="*",
        help="argument to pass to OSLOM (don't pass '-f' !)",
        default=DEF_OSLOM_ARGS)

    # Run OSLOM with parsed arguments
    sys.exit(not run_oslom(parser.parse_args()))

if __name__ == "__main__":
    main()