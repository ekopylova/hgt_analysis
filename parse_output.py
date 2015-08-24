# ----------------------------------------------------------------------------
# Copyright (c) 2015--, The WGS-HGT Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

"""
Parse output files of HGT tools
===============================
"""

import click
import sys


def parse_trex(input_f):
	""" Parse output of T-REX version 3.6

	Parameters
	----------
	input_f: string
		file descriptor for T-REX output results
	"""
	string = "hgt : number of HGT(s) found = "
	out_str = False
	for line in input_f:
		if string in line:
			number_hgts = line.split(string)[1].strip()
			sys.stdout.write(number_hgts)
			out_str = True
	if not out_str:
		sys.stdout.write("NaN")


def parse_rangerdtl(input_f):
	""" Parse output of RANGER-DTL version 1.0

	Parameters
	----------
	input_f: string
		file descriptor for RANGER-DTL output results
	"""
	string = "The minimum reconciliation cost is: "
	out_str = False
	for line in input_f:
		if string in line:
			number_hgts = line.split("Transfers: ")[1].split(",")[0]
			sys.stdout.write(number_hgts)
			out_str = True
	if not out_str:
		sys.stdout.write("NaN")


def parse_riatahgt(input_f):
	""" Parse output of RIATA-HGT version

	Parameters
	----------
	input_f: string
		file descriptor for RIATA-HGT output results
	"""
	string = "There are "
	out_str = False
	for line in input_f:
		if string in line:
			number_hgts = line.split(string)[1].split(" component(s)")[0]
			sys.stdout.write(number_hgts)
			out_str = True
	if not out_str:
		sys.stdout.write("NaN")


def parse_jane4(input_f):
	""" Parse output of Jane version 4

	Parameters
	----------
	input_f: string
		file descriptor for RIATA-HGT output results
	"""
	string = "Host Switch: "
	out_str = False
	for line in input_f:
		if string in line:
			number_hgts = line.split(string)[1].strip()
			sys.stdout.write(number_hgts)
			out_str = True
	if not out_str:
		sys.stdout.write("NaN")


@click.command()
@click.option('--hgt-results-fp', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True,
                              file_okay=True),
              help='Output file containing HGT information')
@click.option('--method', required=True,
              type=click.Choice(['trex', 'ranger-dtl',
                                 'riata-hgt', 'consel',
                                 'darkhorse', 'wn-svm',
                                 'genemark', 'hgtector',
                                 'distance-method', 'jane4',
                                 'tree-puzzle']),
              help='The method used for HGT detection')
def _main(hgt_results_fp,
          method):
    """ Call different file parsing functions depending on method used
        for HGT detection

    Parameters
    ----------
    hgt_results_fp: string
        file path to HGT results
    method: string
        the method used for HGT detection
    """

    with open(hgt_results_fp, 'U') as input_f:
	    if method == 'ranger-dtl':
	        parse_rangerdtl(input_f=input_f)
	    elif method == 'trex':
	        parse_trex(input_f=input_f)
	    elif method == 'riata-hgt':
	        parse_riatahgt(input_f=input_f)
	    elif method == 'jane4':
	        parse_jane4(input_f=input_f)
	    elif method == 'consel':
	        parse_consel(input_f=input_f)


if __name__ == "__main__":
    _main()