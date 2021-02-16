# -*- coding: utf-8 -*-
# import necessary modules
import pandas as pd
import numpy as np
import glob
import os
from subprocess import call
from .logger import get_logger
from .translate_ensembl import translate_ensembl
from .db_parser import parser
from .PDBmapper import PDBmapper
from .decorator import tags
from .run_subprocess import call_subprocess
from .writefile import writefile


# Emojis
DNA = '\U0001F9EC'

# decorator to monitor function


# @tags(text_start="Running PDBmapper...",
#       text_succeed=" Running PDBmapper...done.",
#       text_fail=" Running PDBmapper...failed!",
#       emoji=DNA)
def wrapper(ensemblid, psdb, vardb, out_dir, pident, isoform, consequence, loc, index_file, uniprot=False, varid=None, csv = False, hdf = False):
    
    # logging
    logger = get_logger('wrapper', out_dir)
    # translate ensembl id
    try:
        if ensemblid == '-': 
            raise IOError()
        ensemblIDs = translate_ensembl(
            ensemblid,  out_dir, isoform)
        geneid = ensemblIDs['geneID']
        protid = ensemblIDs['protID']
        transcriptid = ensemblIDs['transcriptID']
        UniprotID = ensemblIDs['UniprotID']
        APPRIS = ensemblIDs['APPRIS']
        if uniprot is True:
            protid = UniprotID
        # run PDBmapper
        for i in range(0, len(protid)):
            try:
                PDBmapper(protid[i],
                          geneid[i],
                          transcriptid[i],
                          psdb,
                          vardb,
                          out_dir,
                          pident,
                          isoform,
                          APPRIS[i],
                          UniprotID[i],
                          consequence,
                          loc,
                          varid,
                          csv,
                          hdf)
        # error handling
            except:
                if varid is None:
                    logger.error(
                        ('Warning: {} has no mapping variants.'.format(ensemblid)))
                else:
                    logger.error(
                        ('Warning: {} has no mapping variants.'.format(str(varid))))
            continue
        
     # error handling
    except IOError:
        if loc:
            try: 
                if ensemblid == '-':
                    transcriptid = '-'
                else: 
                    cmd = ('grep -w \'{}\' {}').format(ensemblid, index_file)
                    # call subprocess
                    out, err = call_subprocess(cmd)
                    #print(out, err)
                    if err is None and out != b'':
                        toprocess = out.decode('utf-8')
                        # geneid correspond to the 2nd column in the line
                        transcriptid = [s for s in toprocess.split(
                                            " ") if 'ENST' in s][0]
                annovars_left = parser(transcriptid, vardb)
                
                    #annovars_left = annovars[annovars['Feature']==ensemblid]
                            # filter by variant type if one or more selected
                if varid is not None:
                    if 'Existing_variation' in annovars_left.columns:
                        annovars_left =  annovars_left[
                            (annovars_left.Uploaded_variation.astype(str) == str(varid)) |
                            ( annovars_left.Existing_variation.astype(str) == str(varid)) ]
                    else:
                        annovars_left =  annovars_left[
                            ( annovars_left.Uploaded_variation.astype(str) == str(varid))]
                    logger.info('Variant \'' + str(varid) + '\' has been selected.')
                    # if filter returns an empty df, raise error
                    if annovars_left.empty:
                        logger.error(
                            'Variants could not be filtered by variant id \'' + str(varid) + '\'')
                        raise IOError()
                try: 
                    noncoding_variants_index = annovars_left.Protein_position.str.contains('\.|\-', regex=True, na = True)
                    noncoding_variants = annovars_left.loc[noncoding_variants_index]
                except: 
                    noncoding_variants = False 
                if isoform is None:
                    isoform = ['all']
                if consequence is None:
                    consequence = ['all']  
                # non-protein coding mutations
                if noncoding_variants is not False:
                    noncoding_variants['APPRIS_isoform'] = ''
                    noncoding_variants['Mapping_position'] = 'Noncoding'
                    writefile(transcriptid, out_dir, pident, isoform, consequence, noncoding_variants, 'NoncodingVariants', csv, hdf)
                    unmapped_variants = annovars_left.loc[~noncoding_variants_index]
                else: 
                    unmapped_variants = annovars_left
                        
                if unmapped_variants.empty is False:
                    #unmapped_variants = unmapped_variants.iloc[:, 0:16]
                    unmapped_variants.drop_duplicates(inplace=True)
                    unmapped_variants['APPRIS_isoform'] = ''
                    unmapped_variants['Mapping_position'] = 'Unmapped'
                    writefile(transcriptid, out_dir, pident, isoform, consequence, unmapped_variants, 'UnmappedVariants', csv, hdf)
            except:
                pass
        logger.error('Warning: {} has no matching ensembl ids.'.format(ensemblid))
