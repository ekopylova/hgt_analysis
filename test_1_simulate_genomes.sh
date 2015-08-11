#!/bin/bash

# ----------------------------------------------------------------------------
# Copyright (c) 2015--, Evguenia Kopylova
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

# purpose: simulate genomes with ALF
# usage  : bash test_1_simulate_genomes.sh root_genome.fasta custom_tree.nwk hgt_analysis/scripts_dir working_dir

root_genome_fp=$(readlink -m $1)
custom_tree_fp=$(readlink -m $2)
scripts_dir=$(readlink -m $3)
working_dir=$(readlink -m $4)
alf_params="alf_params.txt"
stderr="stderr.log"
stdout="stdout.log"

lgt_rate=0.005
orth_rep_a=(0 0.3)
gc_cont_am_a=("False" "True")

i=0
echo "Begin simulation .."
for orth_rep in "${orth_rep_a[@]}"
do
    echo -e "\torth_rep: ${orth_rep}"
    for gc_cont_am in "${gc_cont_am_a[@]}"
    do
        echo -e "\tgc_content: ${gc_cont_am}"
        echo -e "\toutput directory: ${working_dir}/params_$i"
        if [ ! -d "${working_dir}/params_$i" ]; then
            mkdir ${working_dir}/"params_$i"
        fi
        python $scripts_dir/create_alf_params.py ${root_genome_fp} \
                                                 ${custom_tree_fp} \
                                                 ${working_dir}/"params_$i" \
                                                 ${alf_params} \
                                                 ${lgt_rate} \
                                                 ${orth_rep} \
                                                 ${gc_cont_am}
        # launch ALF
        echo -e "\tRunning ALF .."
        (cd ${working_dir}/"params_$i"; alfsim "./alf_params.txt" 1>$stdout 2>$stderr)

        # format the ALF genes tree (Newick) to replace '/' with '_' and
        # remove the "[&&NHX:D=N]" tags
        echo -e "Cleaning Newick files .."
        for file in ${working_dir}/"params_$i"/GeneTrees/*.nwk;
        do
            echo $file
            sed -i "s/\//\_/g" $file
            sed -i "s/\[&&NHX:D=N\]//g" $file
        done 
        i=$((i+1))
    done
done
