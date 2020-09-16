import pypdf_ocr
import argparse
import shutil
import errno
import json
import csv
import sys
import os
import re

MAX_PARTS = 999

def is_between(start, x, end):
    return (x >= start) and (x <= end)


# a small helper function that rolls a bunch of independent images into one
def foldImages(list_of_images):
    res = []
    for img_obj in list_of_images:
        res += img_obj['images']
    return res


# processess all cover pages with the format
# [naming]No_0ACPartNo_0xx.pdf
# If max_part is 0, it will search for all
# files that fit this format. Otherwise, it
# will process at most X many 
def main(naming, directory, AC, part_start=0, part_end=MAX_PARTS, instance=0):
    if not os.path.exists(directory):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), directory)

    images_dir = 'images' if instance == 0 else 'images{}'.format(instance)
    plaintext_dir = 'plaintext' if instance == 0 else 'plaintext{}'.format(instance)

    regex = re.compile(naming + r'No_' + str(AC).zfill(3) + r'PartNo_(\d{3}).pdf')
    directory = os.getcwd() if directory == '' else directory

    i = 0
    f_array = []
    print('Dumping images', end='')
    for root, dirs, files in os.walk(directory):
        for f in files:
            m = regex.match(f)
            if m and is_between(part_start, int(m.group(1)), part_end):
                print('.', end='')
                img = pypdf_ocr.getImagePages(os.path.join(root, f), 1)
                f_array.append(img['file'])
                pypdf_ocr.dumpImagePages(img, naming='hin-covers', start=i, directory=images_dir)
                pypdf_ocr.cleanupImageOutput(img)
                i += 1

    print('\nImages dumped!')

    imagesFolded = {
        'tempdir': None,
        'images': [],
        'files': f_array
    }

    print('Reading images to array...')
    imagesFolded['images'] = pypdf_ocr.loadImagesToArray(naming='hin-covers', directory=images_dir)
    print('Images read!')

    vals = {
        'x': [246, 656, 1022, 1384, 1713, 2090, 2242, 1812, 1800, 1804],
        'y': [3048, 3048, 3097, 3097, 3097, 3097, 238, 2158, 1602, 2092],
        'w': [60, 104, 80, 80, 109, 109, 96, 186, 280, 330],
        'h': [60, 48, 37, 37, 39, 39, 96, 78, 74, 72]
    }
    
    i = 0
    print('Cropping images', end='')
    for j in range(len(imagesFolded['images'])):
        print('.', end='')
        copy = imagesFolded['images'][j].copy()
        for k in range(10):        
            pypdf_ocr.generateCropped(copy, i + k, 
                vals['x'][k],
                vals['y'][k],
                vals['w'][k],
                vals['h'][k],
                directory=images_dir)
        i += 10
    print('\nImages cropped!')

    print('({}) Doing OCR...'.format(instance))
    # just extract all the cropped pages to english    
    cropped_text_pages = pypdf_ocr.extractPagesText(num_pages=len(imagesFolded['images']) * 10, naming='cropped', language='eng', psm=8,
            clist='tessedit_char_whitelist=0123456789', directory=images_dir)
    # loop to replace the right english attempts with hindi
    for a in range(len(imagesFolded['images'])):
        hi_crop = pypdf_ocr.extractPagesText(num_pages=2, naming='cropped', language='hin', start=10*a+8, psm=8,
            clist='tessedit_char_blacklist=॥._', directory=images_dir)
        cropped_text_pages[10*a+8]   = hi_crop[0]
        cropped_text_pages[10*a+8+1] = hi_crop[1]
    
    covers_text_pages = pypdf_ocr.extractPagesText(num_pages=len(imagesFolded['images']), naming='hin-covers', language='hin', psm=4,
        clist='tessedit_char_blacklist=॥', directory=images_dir)
    
    pypdf_ocr.dumpTextPages(pages=covers_text_pages, naming='hin-covers', directory=plaintext_dir)
    pypdf_ocr.dumpTextPages(pages=cropped_text_pages, naming='cropped', directory=plaintext_dir)
    print('({}) All OCR dumped!'.format(instance))

    part_from_file = re.compile(r'PartNo_(\d{3})')

    pages = []
    dicts = []
    print('Doing regex', end='')
    for j in range(len(covers_text_pages)):
        print('.', end='')
        page = covers_text_pages[j]
        page1 = pypdf_ocr.extractPage1(page)
        # get it because it's a bunch of crops? lol
        farm = pypdf_ocr.retreiveCropped(10, start=10*j, directory=plaintext_dir)
        page1['Sanity'] = farm[0:6]
        page1['Part'] = farm[6]
        page1['Zip Code'] = farm[7]
        page1['Post Office'] = farm[8]
        page1['District'] = farm[9]
        page1['File Name'] = imagesFolded['files'][j]
        match = re.search(part_from_file, page1['File Name'])
        if match:
            if int(match.group(1)) != page1['Part']:
                page1['Part'] = int(match.group(1))
        dicts.append(page1)
        pages.append(json.dumps(page1, ensure_ascii=False))
    print('\nRegex done!')
    
    keys = dicts[0].keys()
    with open('output/output{}.csv'.format(AC), 'w+') as csv_out:
        dict_writer = csv.DictWriter(csv_out, keys)
        dict_writer.writeheader()
        dict_writer.writerows(dicts)

    # pypdf_ocr.dumpTextPages(pages, naming='hin-covers', directory='output', extension='json')
    shutil.rmtree(images_dir + '/')
    shutil.rmtree(plaintext_dir + '/')
    print('Done!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract data from Bihar electoral roll cover sheets.')
    parser.add_argument('--dir', type=str, metavar='dir', help='The directory the files are stored in')
    parser.add_argument('--filename', type=str, metavar='naming', required=True, help='The naming pattern of every cover sheet ([naming]No_xxxPartNo_xxx.pdf)')
    parser.add_argument('--AC', type=int, metavar='AC', required=True, help='AC number to process')
    parser.add_argument('--startpart', type=int, help='Which part number to start at')
    parser.add_argument('--endpart', type=int, help='Which part number to end at (max of 999)')
    parser.add_argument('--instance', type=int, help='Instance for parallel processing')

    args = parser.parse_args()
    real_dir = '' if args.dir is None else args.dir
    real_start = 0 if args.startpart is None else args.startpart
    real_end = MAX_PARTS if args.endpart is None else args.endpart
    real_instance = 0 if args.instance is None else args.instance
    main(args.filename, real_dir, args.AC, real_start, real_end, real_instance)