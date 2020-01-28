# coding: utf-8

# Import necesary modules
import sys
import os
import re
import glob
import pandas as pd
import numpy as np
from .db_parser import parser
from .interface_parser import reshape
from .decorator import tags
from .explode import explode
from .logger import get_logger


def PDBmapper(protid,  geneid, transcritpID, intdb, vardb, out_dir, pident, consequence, varid=None):
    '''
    Map interfaces and genomic anntoated variants and returns a
    setID.File, necessary input for SKAT. Additionaly, it creates
    another file with detailed information regarding the maped areas.

    Parameters
    ----------
    protid : str
        Ensembl protein ID
    geneid : str
        Translated Ensembl protein ID
    intdb : str
        Directory where to find interface database
    vardb : str
        Directory where to find variants database
    out_dir : str
        Output directory
    pident : int
        Thershold of sequence identity (percertage).

    Returns
    -------
    setID.File
        txt file containing a data frame two columns corresponding to the
        analyzed interface id and the corresponding annotated genomic variants.
    MappedVariants.File
        Same as setID.File but with additional information describing the
        interfaces and the variants.
    '''
    # log file
    logger = get_logger(' PDBmapper', out_dir)

    # parse interfaces corresponding to the selected protein ID
    annoint = parser(protid, intdb)
    if annoint.empty:
        logger.error('Interfaces of protein ' +
                     protid + 'could not be parsed.')
        raise IOError
    else:
        logger.info('Interfaces of protein ' + protid + ' parsed.')

    # if default database is used minor modifications are needed
    if pident is not None:
        logger.info('Filtering interfaces by pident = ' + str(pident) + '%.')
        # filter by pident
        pident = int(pident)  # from str to int
        annoint_pident = annoint.loc[annoint.pident >= pident]
        # if pident threshold is to high, the next maximum value of pident is
        # notified in log file
        if annoint_pident.empty:
            alt_pident = annoint.loc[:, "pident"].max()
            logger.error('Warning: for protid ' + str(pident) +
                         ', the variable "pident" equal to ' +
                         str(pident) + ' is too high.\n A threshold lower than or equal to ' +
                         str(alt_pident) + ' would retrieve results.')

            raise IOError()
        # spread the data frame to have one amino acid position per row instead of compacted.
        annoint = reshape(annoint_pident)

    # parse variants corresponding to the selected protein ID
    annovars = parser(geneid, vardb)
    logger.info('Variants file from gene id ' + geneid + ' parsed.')

    # filter by transcript ID
    annovars = annovars[annovars['Feature'] == transcritpID]
    if annovars.empty:
        raise IOError()

    # filter by variant type if one or more selected
    if consequence is not None:
        annovars = annovars[annovars['Consequence'].astype(
            str).str.contains('|'.join(consequence))]
        logger.info('Filter of features = ' + consequence)
        # if filter returns an empty df, raise error
        if annovars.empty:
            logger.error(
                'Variants could not be filtered by feature type = ' + consequence)
            raise IOError()

    # filter by variant type if one or more selected
    if varid is not None:
        if 'Existing_variation' in annovars.columns:
            annovars = annovars[
                annovars['Uploaded_variation'].astype(
                    str).str.contains(varid) |
                annovars['Existing_variation'].astype(
                    str).str.contains(varid)]
        else:
            annovars = annovars[
                annovars['Uploaded_variation'].astype(
                    str).str.contains(varid)]
        logger.info('Variant \'' + str(varid) + '\' has been selected.')
        # if filter returns an empty df, raise error
        if annovars.empty:
            logger.error(
                'Variants could not be filtered by variant id \'' + str(varid) + '\'')
            raise IOError()

    # for variants with high impact affecting several aminoacidic positions,
    # the protein position is a range. split the range to have each position
    # individually
    if any(annovars['Protein_position'].astype(str).str.contains(r'[0-9]-[0-9]')):
        # subset hight impact variants
        sub_df = annovars[annovars['Protein_position'].astype(str).str.contains(
            r'[0-9]-[0-9]')]
        # subset the remaining variants to concatenate afterwards
        remaining_df = annovars.drop(sub_df.index)
        # split the range or interval
        sub_df[['start', 'end']] = sub_df['Protein_position'].str.split(
            '-', expand=True)
        # sometimes the start or the end position of the interval is a
        # question mark. In that case, we take into account the
        # remaining value of the interval
        if any(sub_df['start'].str.contains('\?')):
            sub_df['start'] = np.where(sub_df['start'] == '?', sub_df['end'],
                                       sub_df['start'])
        if any(sub_df['end'].str.contains('\?')):
            sub_df['end'] = np.where(sub_df['end'] == '?', sub_df['start'],
                                     sub_df['end'])
        # print(sub_df[['end', 'start']])
        # create the range of numbers defined by the interval
        sub_df['Protein_position'] = sub_df.apply(lambda x: list(
            range(int(x['start']), int(x['end'])+1)), 1)
        # spread each individual position into one row
        sub_df = explode(sub_df, ['Protein_position'])
        # drop unnecesary columns
        sub_df.drop(['start', 'end'], inplace=True, axis=1)
        # concatenate final result
        annovars = pd.concat([remaining_df, sub_df], sort=False)

    # for sucessful merge, Protein_position column must be str type
    annoint['Protein_position'] = annoint['Protein_position'].astype(str)
    annovars['Protein_position'] = annovars['Protein_position'].astype(str)

    annoint.set_index('Protein_position', inplace=True)
    annovars.set_index('Protein_position', inplace=True)

    mapped_variants = annovars.join(annoint, how='left')
    # Merge them both files
    # mapped_variants = pd.merge(annovars,
    #                            annoint,
    #                            left_on=['Protein_position'],
    #                            right_on=['Protein_position'],
    #                            sort=False)

    # stop if there are no results
    if mapped_variants.empty:
        # report results
        logger.warning('Warning: ' + protid +
                       ' does not map with any annotated variant.\n')
        raise IOError()

    # if merging was successful, create setID file and
    # save the merged dataframe as well
    else:
        setID_file = mapped_variants[['interface_id',
                                      'Uploaded_variation']]
        setID_file.drop_duplicates(inplace=True)
        mapped_variants.drop_duplicates(inplace=True)

        # Save the merged dataframe, appending results and not
        #  reapeting headers
        with open(os.path.join(out_dir, ('setID_pident' + str(pident) + '.File')), 'a') as f:
            setID_file.to_csv(f, sep=' ', index=False,  header=f.tell() == 0)
        with open(os.path.join(out_dir, ('MappedVariants_pident' + str(pident) + '.File')), 'a') as f:
            mapped_variants.to_csv(f, sep=' ', index=False,
                                   header=f.tell() == 0)

    del(annoint, annoint_pident, annovars)
