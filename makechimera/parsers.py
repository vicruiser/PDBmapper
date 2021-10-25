#!/usr/bin/python

import argparse


def parse_args() -> argparse.Namespace: 
    """
    Parses arguments provided to the tool via the command line and stores them for later use.

    Returns:
        argparse.Namespace: information provided through the command line arguments.
    """  
    parser = argparse.ArgumentParser(description="""makechimerax generates ChimeraX scripts of the provided PDB
                                     code(s) from the data contained in the mapped file generated by 3Dmapper.""")
    
    parser.add_argument('-p', '--pdb_code',
                        required=True,
                        nargs='+',
                        help="""PDB code/s to be found within the mapped file. If assembly is not included
                                it will generate a script for all mapped assemblies of that PDB code.""",
                        action='store',
                        type=str,
                        metavar='<string>',
                        dest='pdb')
    
    parser.add_argument('--pdb_list',
                        required=False,
                        help='Specifies that PDBs provided are in a file, sepparated by spaces, tabs or new lines.',
                        action='store_true',
                        dest='pdb_list')
    
    parser.add_argument('-i', '--interface_positions',
                        required=False,
                        help='File containing the variants mapped to interfaces generated by 3Dmapper.',
                        action='store',
                        type=str,
                        metavar='<string>',
                        dest='interface_file')
    
    parser.add_argument('-s', '--structure_positions',
                        required=False,
                        help='File containing the variants mapped to protein structure generated by 3Dmapper.',
                        action='store',
                        type=str,
                        metavar='<string>',
                        dest='structure_file')
    
    parser.add_argument('-o', '--output',
                        required=False,
                        help='Output folder in which the ChimeraX script/s will be saved.',
                        action='store',
                        type=str,
                        metavar='<string>',
                        dest='output')
    
    parser.add_argument('-n', '--name',
                        required=False,
                        help='Base name for the ChimeraX scripts.',
                        action='store',
                        type=str,
                        metavar='<string>',
                        dest='name')
    
    parser.add_argument('-it', '--inter_type',
                        required=False,
                        help='If interfaces are available, filter by specified interaction type (ligand, protein or nucleic).',
                        action='store',
                        type=str,
                        metavar='<string>',
                        dest='filter_it')
    
    parser.add_argument('-l', '--lighting',
                        required=False,
                        help='Select lighting option: full, soft or simple.',
                        choices=['full', 'soft', 'simple'],
                        default='full', 
                        action='store',
                        type=str,
                        metavar='<string>',
                        dest='lighting')
    
    parser.add_argument('-bg', '--background',
                        required=False,
                        help='Select background option: white or black.',
                        choices=['white', 'black'],
                        default='white', 
                        action='store',
                        type=str,
                        metavar='<string>',
                        dest='bg')
    
    parser.add_argument('-ns', '--no_silhouette',
                        required=False,
                        help='Display will not present silhouettes.',
                        action='store_true',
                        dest='sil')
    
    parser.add_argument('-mol', '--mol_style',
                        required=False,
                        help='Select option for molecule style: ball, sphere or stick.',
                        choices=['ball', 'sphere', 'stick'],
                        default='ball',
                        action='store',
                        type=str,
                        metavar='<string>',
                        dest='mol_style')
    
    parser.add_argument('-is', '--itf_style',
                        required=False,
                        help='Select option for molecule style of the interfaces displayed: ball, sphere or stick.',
                        choices=['ball', 'sphere', 'stick'],
                        default='sphere',
                        action='store',
                        type=str,
                        metavar='<string>',
                        dest='itf_style')
    
    parser.add_argument('-f', "--force",
                        required=False,
                        help='Force to overwrite? Active by default.',
                        action='store_true',
                        dest='overwrite')

    return parser.parse_args()