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

root_genome_fp=$1
custom_tree_fp=$2
scripts_dir=$3
working_dir=$4
alf_params="alf_params.txt"

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
		#bash run_alf_simulations.sh $custom_tree_fp $params $working_dir
		i=$((i+1))
	done
done
