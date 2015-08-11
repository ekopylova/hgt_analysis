#!/usr/bin/env python

# ----------------------------------------------------------------------------
# Copyright (c) 2015--, Evguenia Kopylova
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

"""
Create parameters file for ALF genome simulations
=================================================
"""

import sys
from string import replace
from os.path import join, basename, abspath
from subprocess import Popen, PIPE


def run_fasta_to_darwin(root_genome_fp,
                        root_genome_db_fp):
    """ Run ALF's script to convert FASTA to Darwin files

    Parameters
    ----------
    root_genome_fp: string
        file path of root genome (protein sequences in FASTA format)
    root_genome_db_fp: string
        file path of root genome in Darwin format
    """
    proc = Popen(
        ["fasta2darwin", root_genome_fp, "-o", root_genome_db_fp],
        stdout=PIPE,
        stderr=PIPE,
        close_fds=True)
    proc.wait()
    stderr = proc.communicate()[1]
    if stderr:
        raise ValueError(stderr)


def create_param_file(root_genome_fp,
                      custom_tree_fp,
                      working_dp,
                      output_file_name="alf_params.txt",
                      lgt_rate=0.003,
                      orth_rep=0.5,
                      gc_content_amelioration='False'):
    """ Create parameters file for ALF genome simulation

    Parameters
    ----------
    root_genome_fp: string
        file path of root genome (protein sequences in FASTA format)
    custom_tree_fp: string
        file path to Newick tree
    working_dp: string
        working directory path
    output_file_name: string
        name of the resulting parameters file
    lgt_rate: float
        rate of horizontal gene transfer
    orth_rep: float
        proportion of horizontal gene transfers that are orthologous
        replacements
    gc_content_amelioration: string
        if True, create random target frequencies for all leaf species
        and all models (See ALF user manual for more information)
        if False, GC content amelioration is disabled
    """
    root_genome_db_fp = join(working_dp, "%s.db" % basename(root_genome_fp))
    run_fasta_to_darwin(
        root_genome_fp=abspath(root_genome_fp),root_genome_db_fp=abspath(root_genome_db_fp))
    alf_params_fp = join(working_dp, output_file_name)
    p = replace(parameter_file, 'WORKING_DIR_PATH', abspath(working_dp))
    p = replace(p, 'ORGANISM.db', abspath(root_genome_db_fp))
    p = replace(p, 'CUSTOM_TREE.nwk', abspath(custom_tree_fp))
    p = replace(p, 'LGT_RATE', str(lgt_rate))
    p = replace(p, 'ORTHREP', str(orth_rep))
    if gc_content_amelioration == 'True':
        p = p + "targetFreqs := ['Random'];\n"
    with open(alf_params_fp, 'w') as alf_params_f:
        alf_params_f.write(p)


def main(argv):
    """ Create parameters file for ALF genome simulation
    """
    root_genome_fp = sys.argv[1]
    custom_tree_fp = sys.argv[2]
    working_dp = sys.argv[3]
    output_file_name = sys.argv[4]
    lgt_rate = float(sys.argv[5])
    orth_rep = float(sys.argv[6])
    gc_content_amelioration = sys.argv[7]

    create_param_file(root_genome_fp=root_genome_fp,
                      custom_tree_fp=custom_tree_fp,
                      working_dp=working_dp,
                      output_file_name=output_file_name,
                      lgt_rate=lgt_rate,
                      orth_rep=orth_rep,
                      gc_content_amelioration=gc_content_amelioration)


parameter_file = """# name of simulation - you may want to change this
mname := uuid;

# directories for file storage - you may want to change these
wdir := 'WORKING_DIR_PATH';
dbdir := 'DB/';
dbAncdir := 'DBancestral/';

# time scale for simulation (PAM is default)
unitIsPam := false:

# parameters concerning the root genome
realseed := true;
;realorganism := 'ORGANISM.db'; # change path to root genome here
blocksize := 1:

# parameters concerning the species tree
treeType := 'Custom';
treeFile := 'CUSTOM_TREE.nwk'; # change path to tree file here

# parameters concerning the substitution models
substModels := [SubstitutionModel('WAG')];
indelModels := [IndelModel(0.00005, ZIPF, [1.821], 50)];
rateVarModels := [RateVarModel()];
modelAssignments := [1]:
modelSwitchS := [[1]]:
modelSwitchD := [[1]]:

# parameters concerning gene duplication
geneDuplRate := 0.0006;
numberDupl := 5;
transDupl := 0;
fissionDupl := 0;
fusionDupl := 0;
P_pseudogene := 0;
P_neofunc := 0;
P_subfunc := 0;

# parameters concerning gene loss
geneLossRate := 0.001;
numberLoss := 5;

# parameters concerning LGT
lgtRate := LGT_RATE;
orthRep := ORTHREP;
lgtGRate := 0;
lgtGSize := 0;

# parameters concerning rate heterogeneity among genes
amongGeneDistr := 'Gamma';
aGAlpha := 1;

"""


if __name__ == "__main__":
    main(sys.argv[1:])