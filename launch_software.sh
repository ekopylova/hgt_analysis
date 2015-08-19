#!/bin/bash

# ----------------------------------------------------------------------------
# Copyright (c) 2015--, Evguenia Kopylova
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

# purpose: launch HGT software on testing data sets, reformat input trees to
#          follow input format for each tool and parse output files to report
#          standardized statistics (number of HGTs, donors, recipients, gains
#          and losses)

# working dir
working_dir=$(readlink -m $1)
# scripts dir
scripts_dir=$(readlink -m $2)
# species tree in Newick format
species_tree_fp=$(readlink -m $3)
# species raw genome in FASTA format
species_genome_fp=$(readlink -m $4)
# species HMM model (produced by GeneMarkS)
species_model_fp=$(readlink -m $5)
# species protein coding sequences in FASTA format
species_coding_seqs_fp=$(readlink -m $6)
# gene trees in Newick format
gene_tree_dir=$(readlink -m $7)
# gene multiple sequence alignment dir
gene_msa_dir=$(readlink -m $8)
# PhyloNet install dir
phylonet_install_dir=$(readlink -m $9)
# Jane 4 install dir
jane_install_dir=$(readlink -m ${10})

TIMEFORMAT='%U %R'
base_input_file_nwk="input_tree.nwk"
base_input_file_nex="input_tree.nex"
base_input_file_phy="input_msa.phy"
base_output_file="output_file.txt"
input_file_nwk=$working_dir/$base_input_file_nwk
input_file_nex=$working_dir/$base_input_file_nex
output_file=$working_dir/$base_output_file
input_msa_phy=$working_dir/$base_input_file_phy
stderr=$working_dir/"stderr.txt"
stdout=$working_dir/"stdout.txt"

if [ ! -d "${working_dir}" ]; then
    mkdir $working_dir
fi

total_user_time_trex="0.0"
total_wall_time_trex="0.0"
total_user_time_rangerdtl="0.0"
total_wall_time_rangerdtl="0.0"
total_user_time_riatahgt="0.0"
total_wall_time_riatahgt="0.0"
total_user_time_jane="0.0"
total_wall_time_jane="0.0"
total_user_time_consel="0.0"
total_wall_time_consel="0.0"

printf "y\n" > $working_dir/puzzle_cmd.txt

# search for HGTs in each gene tree
for gene_tree in $gene_tree_dir/*.nwk
do
    # T-REX
    # input conditions: binary trees; gene tree labels must match exactly to
    # species leaves in gene tree
    echo "Run T-REX"
    python ${scripts_dir}/reformat_input.py --method 'trex' \
                                            --gene-tree-fp $gene_tree \
                                            --species-tree-fp $species_tree_fp \
                                            --output-tree-fp $input_file_nwk
    TIME="$( time (hgt3.4 -inputfile=$base_input_file_nwk -outputfile=$base_output_file 1>$stdout 2>$stderr) 2>&1)"
    user_time=$(echo $TIME | awk '{print $1;}')
    wall_time=$(echo $TIME | awk '{print $2;}')
    total_user_time_trex=$(python -c "print $total_user_time_trex + $user_time")
    total_wall_time_trex=$(python -c "print $total_wall_time_trex + $wall_time")

    # RANGER-DTL
    echo "Run RANGER-DTL"
    python ${scripts_dir}/reformat_input.py --method 'ranger-dtl' \
                                            --gene-tree-fp $gene_tree \
                                            --species-tree-fp $species_tree_fp \
                                            --output-tree-fp $input_file_nwk
    TIME="$( time (ranger-dtl-U.linux -i $input_file_nwk -o $output_file 1>$stdout 2>$stderr) 2>&1)"
    user_time=$(echo $TIME | awk '{print $1;}')
    wall_time=$(echo $TIME | awk '{print $2;}')
    total_user_time_rangerdtl=$(python -c "print $total_user_time_rangerdtl + $user_time")
    total_wall_time_rangerdtl=$(python -c "print $total_wall_time_rangerdtl + $wall_time")

    # RIATA-HGT (in PhyloNet)
    echo "Run RIATA-HGT"
    python ${scripts_dir}/reformat_input.py --method 'riata-hgt' \
                                            --gene-tree-fp $gene_tree \
                                            --species-tree-fp $species_tree_fp \
                                            --output-tree-fp $input_file_nex
    TIME="$( time (java -jar $phylonet_install_dir/PhyloNet_3.5.6.jar $input_file_nex 1>$output_file 2>$stderr) 2>&1)"
    user_time=$(echo $TIME | awk '{print $1;}')
    wall_time=$(echo $TIME | awk '{print $2;}')
    total_user_time_riatahgt=$(python -c "print $total_user_time_riatahgt + $user_time")
    total_wall_time_riatahgt=$(python -c "print $total_wall_time_riatahgt + $wall_time")

    # JANE4
    # input conditions: requires NEXUS input file;
    # supports one-to-many mapping in both directions (ex. multiple genes per
    # species)
    echo "Jane 4"
    python ${scripts_dir}/reformat_input.py --method 'jane4' \
                                            --gene-tree-fp $gene_tree \
                                            --species-tree-fp $species_tree_fp \
                                            --output-tree-fp $input_file_nex
    TIME="$( time ($jane_install_dir/jane-cli.sh $input_file_nex 1>$output_file 2>$stderr) 2>&1)"
    user_time=$(echo $TIME | awk '{print $1;}')
    wall_time=$(echo $TIME | awk '{print $2;}')
    total_user_time_jane=$(python -c "print $total_user_time_jane + $user_time")
    total_wall_time_jane=$(python -c "print $total_wall_time_jane + $wall_time")

    # CONSEL (AU Test)
    # input conditions: matrix of the site-wise log-likelihoods
    # (a) if no MSA provided, CLUSTALW (align sequences)
    # (b) if MSA provided (ex. ALF), Fasta2Phylip.py
    # TREE-PUZZLE (reconstruct phylogenetic tree using maximum likelihood)
    # CONSEL (apply AU Test on matrix)
    echo "Run Tree-Puzzle and CONSEL"
    gene_tree_file=$(basename $gene_tree)
    gene_number=$(echo $gene_tree_file | sed 's/[^0-9]*//g')
    gene_msa_fasta_fp=$gene_msa_dir/"MSA_${gene_number}_aa.fa"
    gene_msa_phylip_fp=$working_dir/"MSA_${gene_number}_aa.phy"
    python ${scripts_dir}/reformat_input.py --method 'tree-puzzle' \
                                            --gene-tree-fp $gene_tree \
                                            --species-tree-fp $species_tree_fp \
                                            --gene-msa-fa-fp $gene_msa_fasta_fp \
                                            --output-tree-fp $input_file_nwk \
                                            --output-msa-phy-fp $gene_msa_phylip_fp
    puzzle -wsl $gene_msa_phylip_fp $input_file_nwk < $working_dir/puzzle_cmd.txt 1>$stdout 2>$stderr
    # makermt removes the .sitelh extension and writes to the edited file path
    # which would overwrite the Newick tree. Rename the input file to avoid this.
    mv ${input_file_nwk}.sitelh ${input_file_nwk}_puzzle.sitelh
    TIME="$( time (makermt --puzzle ${input_file_nwk}_puzzle.sitelh 1>$stdout 2>$stderr) 2>&1)"
    consel ${input_file_nwk}_puzzle 1>$stdout 2>$stderr
    catpv ${input_file_nwk}_puzzle.pv 1>$output_file 2>$stderr
    user_time=$(echo $TIME | awk '{print $1;}')
    wall_time=$(echo $TIME | awk '{print $2;}')
    total_user_time_consel=$(python -c "print $total_user_time_consel + $user_time")
    total_wall_time_consel=$(python -c "print $total_wall_time_consel + $wall_time")
done

# Wn-SVM
TIME="$( time (lgt_svm -genes $species_coding_seqs_fp > $output_file) 2>&1)"
user_time=$(echo $TIME | awk '{print $1;}')
wall_time=$(echo $TIME | awk '{print $2;}')

# run GeneMarkS training (generate typical and atypical gene models)
species_model_fp=$working_dir/"species_model"
TIME="$( time (gmsn.pl --combine --gm --clean --name $species_model_fp $species_genome_fp 1>$stdout 2>$stderr) 2>&1)"
user_time=$(echo $TIME | awk '{print $1;}')
wall_time=$(echo $TIME | awk '{print $2;}')

# run GeneMark.hmm
TIME="$( time (gmhmmp -r -m $species_model_fp -o $output_file $species_genome_fp 1>$stdout 2>$stderr) 2>&1)"
user_time=$(echo $TIME | awk '{print $1;}')
wall_time=$(echo $TIME | awk '{print $2;}')

