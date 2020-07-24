import pypdf_ocr
import argparse
import shutil
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
        res += img_obj["images"]
    return res


# processess all cover pages with the format
# [naming]No_0ACPartNo_0xx.pdf
# If max_part is 0, it will search for all
# files that fit this format. Otherwise, it
# will process at most X many 
def main(naming, directory, AC, part_start=0, part_end=MAX_PARTS):
    regex = re.compile(naming + r"No_" + str(AC).zfill(3) + r"PartNo_(\d{3}).pdf")
    directory = os.getcwd() if directory == "" else directory

    i = 0
    for root, dirs, files in os.walk(directory):
        for f in files:
            m = regex.match(f)
            if m and is_between(part_start, int(m.group(1)), part_end):
                img = pypdf_ocr.getImagePages(os.path.join(root, f), 1)
                pypdf_ocr.dumpImagePages(img, naming="hin-covers", start=i)
                pypdf_ocr.cleanupImageOutput(img)
                i += 1

    imagesFolded = {
        "tempdir": None,
        "images": []
    }

    imagesFolded["images"] = pypdf_ocr.loadImagesToArray(naming="hin-covers", directory="images")

    vals = {
        "x": [246, 656, 1022, 1384, 1713, 2090],
        "y": [3048, 3048, 3097, 3097, 3097, 3097],
        "w": [60, 104, 80, 80, 109, 109],
        "h": [60, 48, 37, 37, 39, 39]
    }
    i = 0
    for img in imagesFolded["images"]:
        copy = imagesFolded["images"][0].copy()
        for j in range(6):        
            pypdf_ocr.generateCropped(copy, i + j, 
                vals["x"][j],
                vals["y"][j],
                vals["w"][j],
                vals["h"][j])
        i += 6

    
    print(len(imagesFolded["images"]))
    
    cropped_text_pages = pypdf_ocr.extractPagesText(num_pages=len(imagesFolded["images"]) * 6, naming="cropped", language="eng", psm=8,
            clist="tessedit_char_whitelist=0123456789")
    
    covers_text_pages = pypdf_ocr.extractPagesText(num_pages=len(imagesFolded["images"]), naming="hin-covers", language="hin", psm=4,
        clist="tessedit_char_blacklist=॥")
    
    pypdf_ocr.dumpTextPages(pages=covers_text_pages, naming="hin-covers")
    pypdf_ocr.dumpTextPages(pages=cropped_text_pages, naming="cropped")

    i = 0
    pages = []
    dicts = []
    for page in covers_text_pages:
        page1 = pypdf_ocr.extractPage1(page)
        page1["Sanity"] = pypdf_ocr.retreiveCropped(6, start=i)
        dicts.append(page1)
        pages.append(json.dumps(page1, ensure_ascii=False))
        i += 6
    
    keys = dicts[0].keys()
    with open("output.csv", "w+") as csv_out:
        dict_writer = csv.DictWriter(csv_out, keys)
        dict_writer.writeheader()
        dict_writer.writerows(dicts)

    pypdf_ocr.dumpTextPages(pages, naming="hin-covers", directory="output", extension="json")
    shutil.rmtree("images")
    shutil.rmtree("plaintext")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract data from Bihar electoral roll cover sheets.")
    parser.add_argument("--dir", type=str, metavar="dir", help="The directory the files are stored in")
    parser.add_argument("--filename", type=str, metavar="naming", required=True, help="The naming pattern of every cover sheet ([naming]No_xxxPartNo_xxx.pdf)")
    parser.add_argument("--AC", type=int, metavar="AC", required=True, help="AC number to process")
    parser.add_argument("--startpart", type=int, help="Which part number to start at")
    parser.add_argument("--endpart", type=int, help="Which part number to end at (max of 999)")

    args = parser.parse_args()
    real_dir = "" if args.dir is None else args.dir
    real_start = 0 if args.startpart is None else args.startpart
    real_end = MAX_PARTS if args.endpart is None else args.endpart 
    main(args.filename, real_dir, args.AC, real_start, real_end)