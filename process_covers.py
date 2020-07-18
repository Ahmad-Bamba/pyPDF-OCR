import pypdf_ocr
import argparse
import sys
import os
import re

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
def main(naming, directory, AC, max_part):
    regex = re.compile(naming + r"No_" + str(AC).zfill(3) + r"PartNo_\d{3}.pdf")
    directory = os.getcwd() if directory == "" else directory

    images = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if regex.match(f):
                images.append(pypdf_ocr.getImagePages(os.path.join(root, f)))
    imagesFolded = {
        "tempdir": None,
        "images": foldImages(images)
    }
    dumpImagePages(imagesFolded, naming="hin-covers")
    vals = {
        "x": [246, 656, 1022, 1384, 1713, 2090],
        "y": [3048, 3048, 3097, 3097, 3097, 3097],
        "w": [60, 104, 80, 80, 109, 109],
        "h": [60, 48, 37, 37, 39, 39]
    }
    i = 0
    for img in imagesFolded["images"]:
        copy = imagesFolded["images"][0].copy()
        for j in range(i, i + 6):        
            generateCropped(copy, i, 
                vals["x"][i],
                vals["y"][i],
                vals["w"][i],
                vals["h"][i])
            cropped_text_pages = extractPagesText(num_pages=6, naming="cropped", language="eng", psm=8,
                clist="tessedit_char_whitelist=0123456789")
        i += 6
    
    covers_text_pages = extractPagesText(num_pages=len(imagesFolded["images"]), naming="hin-covers", language="hin", psm=4,
        clist="tessedit_char_blacklist=॥")
    
    for img_obj in images:
        cleanupImageOutput(img_obj)
    
    dumpTextPages(naming="hin-covers")
    dumpTextPages(naming="cropped")

    i = 0
    pages = []
    for page in covers_text_pages:
        page1 = extractPage1(page)
        page1["Sanity"] = retreiveCropped(6, start=i)
        pages.append(json.dumps(page1, ensure_ascii=False))
        i += 6
    
    i = 0
    dumpTextPages(pages, naming="output/hin-cover", extension="json")

