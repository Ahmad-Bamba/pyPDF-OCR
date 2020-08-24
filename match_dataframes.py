from libindic.transliteration import getInstance # better transliteration liberary
from pypdf_ocr import getHindiAlphabet
from difflib import SequenceMatcher
import pandas as pd
import numpy as np
import argparse
import string
import re

USEFUL_COLUMNS = ['age', 'gender', 'social_cat', 'village', 'district', 'panchayat', 'fathers_and_mothers_name', 'tehsil', 'head_of_hh']
USEFUL_COLUMNS.sort()
LATIN_ALPHABET = string.ascii_letters
HINDI_ALPHABET = getHindiAlphabet()
TRANSLIT_INSTANCE = getInstance()
THRESHOLD = 0.9 # 90%

USEFUL_COLUMNS2 = ['district', 'block', 'panchayat_nagar', 'vill_ward', 'name_hoh', 'age']
USEFUL_COLUMNS2.sort()

def int_(val):
    try:
        return int(val)
    except:
        pass
    try:
        return int(float(val))
    except:
        pass
    return 0


# expects a single name returns transliterated name
def translit_and_format_name(name):
    global LATIN_ALPHABET
    global HINDI_ALPHABET

    # if there's a \ separator, just take the first name
    try:
        i = name.index('\\')
        name = name[0:i]
    except ValueError:
        name = name

    try:
        if name[0] in LATIN_ALPHABET:
            return name.upper()
        return TRANSLIT_INSTANCE.transliterate(name, "en_US").upper()
    except:
        return name


# returns true if similar and false if not
def are_similar(str1, str2):
    global THRESHOLD

    return SequenceMatcher(None, str1, str2).ratio() >= THRESHOLD


# returns how similar two lists are
def get_similarity(l1, l2):
    return SequenceMatcher(None, l1, l2).ratio()


def main(secc_path, mahadalit_path):
    global USEFUL_COLUMNS
    global USEFUL_COLUMNS2

    df0 = pd.read_csv(secc_path, 
        error_bad_lines=False,
        encoding='utf-8',
        na_values=['na'])
    print(df0.head())
    print(df0.columns)

    # filter columns and rows
    df = df0[USEFUL_COLUMNS]
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    df.dropna()
    # we want only men over the age of 13 in the SC social category
    df = df[(df['gender']=='M') & (df['age']>=13) & (df['social_cat']=='SC')]
    df.reindex()
    print(df.head())

    # remove from memory, since it takes up a lot of RAM
    del df0
    # save the clean version to disk for safe keeping
    # with open('output/trimmed_secc.csv', 'w+') as outfile:
    #     outfile.write(df.to_csv(index=False))
    
    # now we're ready for some matching
    print('Beginning matching between {} and {}...'.format(secc_path, mahadalit_path))

    # get district from file name
    match_full_path = re.compile(r'\/(.+\/)*(.+)\.(.+)$') # if the full path was passed
    match_file_name = re.compile(r'([a-zA-Z0-9_\'"\-+$%#@()!]+)\.csv') # if it's a local file

    m = re.search(match_full_path, mahadalit_path)
    district_name = ''
    if m:
        district_name = m.group(2)
    else:
        m = re.match(match_file_name, mahadalit_path)
        if m:
            district_name = m.group(1)
        else:
            raise Exception('Mahdalit cenus path invalid!')
    
    print('Working with district {}!'.format(district_name))


    # get all the entries of this district
    df_district = df[df['district'].str.upper() == district_name.upper()]

    mdf0 = pd.read_csv(mahadalit_path,
        error_bad_lines=False,
        encoding='utf-8',
        na_values=['na'])
    print(mdf0.head())
    print(mdf0.columns)
    mdf0['age'] = pd.to_numeric(mdf0['age'], errors='coerce')
    mdf0.dropna()

    print('Comparing blocks...')
    block_cmp = 'block,{},{},{}'.format( 
        df.tehsil.unique(),
        mdf0.block.unique(),
        get_similarity(df.tehsil.unique(), mdf0.block.unique()))
    block_cmp = block_cmp.replace('\n', '')
    print('Comparing panchayat...')
    panchayat_cmp = 'panchayat,{},{},{}'.format(
        df.panchayat.unique(),
        mdf0.panchayat_nagar.unique(),
        get_similarity(df.panchayat.unique(), mdf0.panchayat_nagar.unique()))
    panchayat_cmp = panchayat_cmp.replace('\n', '')
    print('Returning comparison...')

    with open('output/base_comparison_{}.csv'.format(district_name), 'w') as outfile:
        outfile.write(',secc,district_{},sim_ratio,\n'.format(district_name))
        outfile.write('{},\n'.format(block_cmp))
        outfile.write('{},\n'.format(panchayat_cmp))
    
    mdf = mdf0[USEFUL_COLUMNS2]
    del mdf0

    # get a sample from the secc data and try to find them in the census
    mdf_sample = mdf.sample(n=100)

    # if district, age, and head of household match, we'll call it a match
    with open('output/sample_match_{}.csv'.format(district_name), 'w') as outfile:
        outfile.write('sample#,match_found,father_name,\n')
        i = 0
        for row in mdf_sample.iterrows():
            # find age matches
            age_matches = df_district[df_district['age'] == row[1]['age']]
            potential_match = False
            secc_name = ''
            # find a head of household that matches
            for arow in age_matches.iterrows():
                if are_similar(translit_and_format_name(arow[1]['head_of_hh']), translit_and_format_name(row[1]['name_hoh'])):
                    potential_match = True
                    secc_name = translit_and_format_name(arow[1]['fathers_and_mothers_name'])
                    break      
            if potential_match:
                outfile.write('{},1,{},\n'.format(i, secc_name))
            else:
                outfile.write('{},0,{},\n'.format(i, secc_name))
            i += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match SECC data to Mahadalit Census.')
    parser.add_argument('--secc_path', help='Path to secc csv.', required=True)
    parser.add_argument('--mahadalit_path', help='Path to census data.', required=True)
    args = parser.parse_args()
    main(args.secc_path, args.mahadalit_path)
