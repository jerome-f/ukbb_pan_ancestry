#!/usr/bin/env python3

__author__ = 'konradk'

import sys
import argparse
import logging
from tqdm import tqdm
logging.basicConfig(format="%(levelname)s (%(name)s %(lineno)s): %(message)s", level='INFO', filename='saige_pipeline.log')

from ukbb_pan_ancestry import *

logger = logging.getLogger("saige_pan_ancestry")
logger.addHandler(logging.StreamHandler(sys.stderr))
root = f'{bucket}/results'


def main():
    hl.init(log='/tmp/saige_temp_hail.log')

    legacy = True

    key_fields = "\t".join(PHENO_KEY_FIELDS)
    output = f'pop\t{key_fields}\theritability\tinv_normalized\tsaige_version\n'
    for pop in POPS:
        logger.info(f'Setting up {pop}...')
        phenos_to_run = get_phenos_to_run(pop, first_round_phenos=legacy)

        null_model_dir = f'{root}/null_glmm/{pop}'
        for pheno_key_dict in tqdm(phenos_to_run):
            # if pheno_key_dict['phenocode'] != 'whr': continue  # Manually patched WHR results
            quantitative_trait = pheno_key_dict["trait_type"] in ('continuous', 'biomarkers')
            null_glmm_log = get_pheno_output_path(null_model_dir, pheno_key_dict, '.variant.log', legacy=legacy)

            pheno_key_dict = recode_single_pkd_to_new(pheno_key_dict)
            pct = stringify_pheno_key_dict(pheno_key_dict, delimiter='\t')
            try:
                heritability = get_heritability_from_log(null_glmm_log, quantitative_trait)
                inv_normalized = get_inverse_normalize_status(null_glmm_log)
                saige_version = get_saige_version_from_log(null_glmm_log)
                output += f'{pop}\t{pct}\t{heritability}\t{inv_normalized}\t{saige_version}\n'
            except:
                logger.info(f'Missing: {null_glmm_log}')

    with hl.hadoop_open(get_heritability_txt_path(), 'w') as f:
        f.write(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    try_slack('@konradjk', main)

