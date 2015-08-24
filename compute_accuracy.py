# ----------------------------------------------------------------------------
# Copyright (c) 2015--, The WGS-HGT Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

"""
Given known HGTs, compute precision, recall and F-score for various tools
=========================================================================
"""

import sys
import click
import re


def parse_expected_transfers(ground_truth_f):
	""" Parse ALF's log file to report horizontal gene transfers with
	information on organism donor, gene donated, organism recipient and gene
	received

	Parameters
	----------
	ground_truth_f: string
		file descriptor to ALF's log file

	Returns
	-------
	expected_transfers: list of tuples
		list of transfers with each tuple representing (organism donor, gene
		donated, organism recipient, gene received)
	"""
	expected_transfers = []
	string = "lgt from organism "
	for line in ground_truth_f:
		if string in line:
			content = re.split(
				'lgt from organism | with gene | to organism |, now gene ',
				line.strip())
			expected_transfers.append(tuple(content[1:]))
	return expected_transfers


def parse_observed_transfers(observed_hgts_f):
	""" Parse summary file of observed transfers for various tools

	observed_hgts_f is expected to follow the format:
	#number of HGTs detected
	#	gene ID	T-REX	RANGER-DTL	RIATA-HGT	Jane 4	Consel
	0	1000	1	1	1	1
	1	1001	0	0	0	0
	..

	Parameters
	----------
	observed_hgts_f: string
		file descriptor of observed transfers (output of launch_software.sh)

	Returns
	-------
	observed_transfers: dict
		dictionary of tools' names (keys) and a list of horizontal gene
		transfers
	"""
	tools = {}
	tools_id = []
	next(observed_hgts_f)
	for line in observed_hgts_f:
		line = line.strip().split('\t')
		if line[0].startswith('#'):
			for tool in line[2:]:
				tools_id.append(tool)
				if tool not in tools:
					tools[tool] = []
			continue
		gene_id = line[1]
		i = 0
		for hgt_num in line[2:]:
			if int(hgt_num) > 0:
				tools[tools_id[i]].append(gene_id) 
			i += 1
	return tools


def compute_accuracy(expected_transfers,
					 observed_transfers):
	""" Compute precision, recall and F-score for horizontally detected genes

	Parameters
	----------
	expected_transfers: list of tuples
		list of transfers with each tuple representing (organism donor, gene
		donated, organism recipient, gene received)
	observed_transfers: dict
		dictionary of tools' names (keys) and a list of horizontal gene
		transfers
	"""
	exp_s = set()
	obs_s = set()
	for tup in expected_transfers:
		exp_s.add(tup[1])
	for tool in observed_transfers:
		obs_s = set(observed_transfers[tool])
		if not obs_s:
			continue
		tp = len(obs_s & exp_s)
		fp = len(obs_s - exp_s)
		fn = len(exp_s - obs_s)
		p = tp / float(tp + fp)
		r = tp / float(tp + fn)
		f = float(2 * p * r) / float(p + r)
		sys.stdout.write("%s\t%.2f\t%.2f\t%.2f\n" % (tool, p, r, f))


@click.command()
@click.option('--ground-truth-fp', required=True,
			  type=click.Path(resolve_path=True, readable=True, exists=True,
							  file_okay=True),
			  help='logfile.txt from ALF simulations')
@click.option('--observed-hgts-fp', required=True,
			  type=click.Path(resolve_path=True, readable=True, exists=True,
							  file_okay=True),
			  help='output from launch_software.sh')
def _main(ground_truth_fp,
		  observed_hgts_fp):
	""" Compute precision, recall and F-score for observed gene transfers,
	losses and gains

	Parameters
	----------
	ground_truth_fp: string
		file path to logfile.txt from ALF simulation
	observed_hgts_fp: string
		file path to output file from launch_software.sh
		(tab separated file with summary for gene transfers, losses and gains)
	"""

	with open(ground_truth_fp, 'U') as ground_truth_f:
		expected_transfers = parse_expected_transfers(ground_truth_f)
	with open(observed_hgts_fp, 'U') as observed_hgts_f:
		observed_transfers = parse_observed_transfers(observed_hgts_f)

	compute_accuracy(expected_transfers, observed_transfers)


if __name__ == "__main__":
    _main()