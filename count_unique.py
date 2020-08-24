from os.path import isfile, join
from os import listdir
import pandas as pd
import argparse
import re

KEEP_COLUMNS = ['block', 'panchayat_nagar', 'vill_ward']

def main(mahadalit_folder):
    global KEEP_COLUMNS

    mahadalit_districts = [f for f in listdir(mahadalit_folder) if isfile(join(mahadalit_folder, f))]
    mahadalit_districts = [district for district in mahadalit_districts if 'lock' not in district]

    print('Total districts: {}'.format(len(mahadalit_districts)))
    block_total = 0
    panchayat_total = 0
    village_total = 0
    for district_file in mahadalit_districts:
        path = mahadalit_folder + district_file
        mdf = pd.read_csv(path, 
                error_bad_lines=False,
                encoding='utf-8',
                na_values=['na'])
        mdf = mdf[KEEP_COLUMNS]
        block_total += len(mdf.block.unique())
        panchayat_total += len(mdf.panchayat_nagar.unique())
        village_total += len(mdf.vill_ward.unique())
    print('Total blocks: {}'.format(block_total))
    print('Total panchayat: {}'.format(panchayat_total))
    print('Total village: {}'.format(village_total))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match SECC data to Mahadalit Census.')
    parser.add_argument('--mahadalit_folder', help='Path to census data.', required=True)
    args = parser.parse_args()
    main(args.mahadalit_folder)
