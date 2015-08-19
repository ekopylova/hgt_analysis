#!/usr/bin/env python

# ----------------------------------------------------------------------------
# Copyright (c) 2015--, Evguenia Kopylova
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

"""
Reformat input files to format accepted by given HGT tool
=========================================================
"""

import sys
import click
from tempfile import mkstemp
from string import replace
from os import remove

import skbio.io
from skbio import TreeNode, Alignment


def join_trees(gene_tree,
               species_tree,
               output_tree_fp):
    """ Concatenate Newick trees into one file (species followed by gene)

    Parameters
    ----------
    gene_tree: skbio.TreeNode
        TreeNode instance for gene tree
    species_tree_fp: skbio.TreeNode
        TreeNode instance for species tree
    output_tree_fp: string
        file path to output species and gene tree

    See Also
    --------
    skbio.TreeNode
    """
    with open(output_tree_fp, 'w') as output_tree_f:
            output_tree_f.write(
                "%s\n%s\n" % (str(species_tree)[:-1], str(gene_tree)[:-1]))


def trim_gene_tree_leaves(gene_tree):
    """ Remove '_GENENAME' from tree leaf names

    Parameters
    ----------
    gene_tree: skbio.TreeNode
        TreeNode instance

    See Also
    --------
    skbio.TreeNode
    """
    for node in gene_tree.tips():
        gene_tree.find(node).name = node.name.split()[0]


def species_gene_mapping(gene_tree,
                         species_tree):
    """ Find the mapping between the leaves in species and gene trees

    The format for species and gene leaves must be a single string
    (no spaces). Only one instance of the '_' delimiter is allowed in the
    gene leaves and this is used as a separator between the species name
    and the gene name. The species names in the species tree (ex. "species")
    must match exactly to the species name in the gene tree
    (ex. "species_gene")
    
    Parameters
    ----------
    gene_tree: skbio.TreeNode
        TreeNode instance for gene tree
    species_tree_fp: skbio.TreeNode
        TreeNode instance for species tree

    See Also
    --------
    skbio.TreeNode

    Returns
    -------
    mapping_leaves: dictionary
        Mapping between the species tree leaves and the gene tree leaves;
        species tips are the keys and gene tips are the values
    """
    mapping_leaves = {}
    for node in species_tree.tips():
        if node.name not in mapping_leaves:
            mapping_leaves[node.name] = []
        else:
            raise ValueError(
                "Species tree leaves must be uniquely labeled: %s" % node.name)
    for node in gene_tree.tips():
        species, gene = node.name.split()
        if species in mapping_leaves:
            mapping_leaves[species].append(species)
        else:
            raise ValueError(
                "Species %s does not exist in the species tree" % species)

    return mapping_leaves


def id_mapper(ids):
    """
    """
    return [_id.split('/')[0] for _id in ids]


def reformat_rangerdtl(gene_tree,
                       species_tree,
                       output_tree_fp):
    """ Reformat input trees to the format accepted by RANGER-DTL

    The species name in the leaves of species and gene trees must be equal.
    For multiple genes from the same species, the format
    "SPECIESNAME_GENENAME" is acceptable in the gene trees

    Parameters
    ----------
    gene_tree: skbio.TreeNode
        TreeNode instance for gene tree
    species_tree_fp: skbio.TreeNode
        TreeNode instance for species tree
    output_tree_fp: string
        file path to output trees (species followed by gene)

    See Also
    --------
    skbio.TreeNode
    """
    join_trees(gene_tree,
        species_tree,
        output_tree_fp)


def reformat_trex(gene_tree,
                  species_tree,
                  output_tree_fp):
    """ Reformat input trees to the format accepted by T-REX

    Binary trees only, leaves of species and gene trees must be equally
    labeled

    Parameters
    ----------
    gene_tree: skbio.TreeNode
        TreeNode instance for gene tree
    species_tree_fp: skbio.TreeNode
        TreeNode instance for species tree
    output_tree_fp: string
        file path to output trees (species followed by gene)

    See Also
    --------
    skbio.TreeNode
    """
    # trim gene tree leaves to exclude '_GENENAME' (if exists)
    trim_gene_tree_leaves(gene_tree)
    tmp_fp, abs_path = mkstemp()
    with open(abs_path, 'w') as out_f:
       out_f.write(str(gene_tree))
    # join species and gene tree into one file
    join_trees(tmp_gene_tree,
        species_tree,
        output_tree_fp)
    remove(tmp_gene_tree_fp)


def reformat_riatahgt(gene_tree,
                      species_tree,
                      output_tree_fp):
    """ Reformat input trees to the format accepted by RIATA-HGT (PhyloNet)

    Input to RIATA-HGT is a Nexus file.

    gene_tree: skbio.TreeNode
        TreeNode instance for gene tree
    species_tree_fp: skbio.TreeNode
        TreeNode instance for species tree
    output_tree_fp: string
        file path to output trees (Nexus format)

    See Also
    --------
    skbio.TreeNode
    """
    nexus_file = """#NEXUS
BEGIN TREES;
Tree speciesTree = SPECIES_TREE
Tree geneTree = GENE_TREE
END;
BEGIN PHYLONET;
RIATAHGT speciesTree {geneTree};
END;
    """
    # trim gene tree leaves to exclude '_GENENAME' (if exists)
    trim_gene_tree_leaves(gene_tree)
    p = replace(nexus_file, 'SPECIES_TREE', str(species_tree))
    p = replace(p, 'GENE_TREE', str(gene_tree))
    with open(output_tree_fp, 'w') as output_tree_f:
        output_tree_f.write(p)


def reformat_jane4(gene_tree,
                   species_tree,
                   output_tree_fp):
    """ Reformat input trees to the format accepted by Jane4

    Input to Jane4 is a Nexus file, the trees cannot not contain
    branch lengths and the species/gene leaves mapping is required

    Parameters
    ----------
    gene_tree: skbio.TreeNode
        TreeNode instance for gene tree
    species_tree_fp: skbio.TreeNode
        TreeNode instance for species tree
    output_tree_fp: string
        file path to output trees (Nexus format)

    See Also
    --------
    skbio.TreeNode
    """
    nexus_file = """#NEXUS
begin host;
tree host = SPECIES_TREE
endblock;
begin parasite;
tree parasite = GENE_TREE
endblock;
begin distribution;
Range MAPPING;
endblock;
    """
    # create a mapping between the species and gene tree leaves
    mapping_dict = species_gene_mapping(gene_tree=gene_tree,
                                        species_tree=species_tree)
    # trim gene tree leaves to exclude '_GENENAME' (if exists)
    trim_gene_tree_leaves(gene_tree)
    # set branch lengths to None
    for node in gene_tree.postorder():
        node.length = None
    for node in species_tree.postorder():
        node.length = None
    mapping_str = ""
    for species in mapping_dict:
        for gene in mapping_dict[species]:
            mapping_str = "%s%s:%s, " % (mapping_str, species, gene)
    p = replace(nexus_file, 'SPECIES_TREE', str(species_tree))
    p = replace(p, 'GENE_TREE', str(gene_tree))
    p = replace(p, 'MAPPING', mapping_str[:-2])
    with open(output_tree_fp, 'w') as output_tree_f:
        output_tree_f.write(p)


def reformat_treepuzzle(gene_tree,
                        species_tree,
                        gene_msa_fa_fp,
                        output_tree_fp,
                        output_msa_phy_fp):
    """ Reformat input trees to the format accepted by Tree-Puzzle

    Parameters
    ----------
    gene_tree: skbio.TreeNode
        TreeNode instance for gene tree
    species_tree_fp: skbio.TreeNode
        TreeNode instance for species tree
    gene_msa_fa_fp: string
        file path to gene alignments in FASTA format
    output_tree_fp: string
        file path to output trees (Nexus format)
    output_msa_phy_fp: string
        file path to output MSA in PHYLIP format

    See Also
    --------
    skbio.TreeNode
    """
    # remove the root branch length (output with ALF)
    for node in gene_tree.postorder():
        if node.is_root():
            node.length = None
    for node in species_tree.postorder():
        if node.is_root():
            node.length = None
    # trim gene tree leaves to exclude '_GENENAME' (if exists)
    trim_gene_tree_leaves(gene_tree)
    join_trees(gene_tree,
        species_tree,
        output_tree_fp)
    # trim FASTA sequence labels to exclude '/GENENAME' (if exists)
    msa_fa = Alignment.read(gene_msa_fa_fp, format='fasta')
    msa_fa_update_ids, new_to_old_ids = msa_fa.update_ids(func=id_mapper)
    msa_fa_update_ids.write(output_msa_phy_fp, format='phylip')


@click.command()
@click.option('--gene-tree-fp', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True,
                              file_okay=True),
              help='Gene tree in Newick format')
@click.option('--species-tree-fp', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True,
                              file_okay=True),
              help='Species tree in Newick format')
@click.option('--gene-msa-fa-fp', required=False,
              type=click.Path(resolve_path=True, readable=True, exists=True,
                              file_okay=True),
              help='MSA of genes in FASTA format')
@click.option('--output-tree-fp', required=False,
              type=click.Path(resolve_path=True, readable=True, exists=False,
                              file_okay=True),
              help='Output formatted species and gene tree')
@click.option('--output-msa-phy-fp', required=False,
              type=click.Path(resolve_path=True, readable=True, exists=False,
                              file_okay=True),
              help='Output MSA in PHYLIP format')
@click.option('--method', required=True,
              type=click.Choice(['trex', 'ranger-dtl',
                                 'riata-hgt', 'consel',
                                 'darkhorse', 'wn-svm',
                                 'genemark', 'hgtector',
                                 'distance-method', 'jane4',
                                 'tree-puzzle']),
              help='The method to be used for HGT detection')
def _main(gene_tree_fp,
          species_tree_fp,
          gene_msa_fa_fp,
          output_tree_fp,
          output_msa_phy_fp,
          method):
    """ Call different reformatting functions depending on method used
        for HGT detection

        Species tree can be multifurcating, however will be converted to
        bifurcating trees for software that require them. Leaf labels of
        species tree and gene tree must match, however the label
        SPECIESNAME_GENENAME is acceptable for multiple genes in the gene
        tree. Leaf labels must also be at most 10 characters long (for
        PHYLIP manipulations)

    Parameters
    ----------
    gene_tree_fp: string
        file path to gene tree in Newick format
    species_tree_fp: string
        file path to species tree in Newick format
    gene_msa_fa_fp: string
        file path to gene alignments in FASTA format
    output_tree_fp: string
        file path to output tree file (to be used an input file to HGT tool)
    output_msa_phy_fp: string
        file path to output MSA in PHYLIP format
    method: string
        the method to be used for HGT detection
    """

    # add function to check where tree is multifurcating and the labeling
    # is correct
    gene_tree = TreeNode.read(gene_tree_fp, format='newick')
    species_tree = TreeNode.read(species_tree_fp, format='newick')

    if method == 'ranger-dtl':
        reformat_rangerdtl(gene_tree=gene_tree,
            species_tree=species_tree,
            output_tree_fp=output_tree_fp)
    elif method == 'trex':
        reformat_trex(gene_tree=gene_tree,
            species_tree=species_tree,
            output_tree_fp=output_tree_fp)
    elif method == 'riata-hgt':
        reformat_riatahgt(gene_tree=gene_tree,
            species_tree=species_tree,
            output_tree_fp=output_tree_fp)
    elif method == 'jane4':
        reformat_jane4(gene_tree=gene_tree,
            species_tree=species_tree,
            output_tree_fp=output_tree_fp)
    elif method == 'tree-puzzle':
        reformat_treepuzzle(gene_tree=gene_tree,
            species_tree=species_tree,
            gene_msa_fa_fp=gene_msa_fa_fp,
            output_tree_fp=output_tree_fp,
            output_msa_phy_fp=output_msa_phy_fp)


if __name__ == "__main__":
    _main()

