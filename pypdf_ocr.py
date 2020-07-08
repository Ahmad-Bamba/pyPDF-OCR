# This library converts a PDF file into a series of JPEGs, and then
# a list of tokens. At minimum, every recognized paragraph will be
# a token and charts of numbers will be a token as well.

# Imports
from PIL import Image, ImageEnhance
import pytesseract
import sys
from pdf2image import convert_from_path
import os
from enum import Enum
import pandas as pd
from PyPDF2 import PdfFileReader
import tempfile
import re
import numpy as np

# Globals

# Memory management
OUTPUT_PAGE_LIMIT = 5

# Regular Expressions
SEARCH_FAMILY = r"(?:पिता|पति) का नाम\s*:?\s*"
SEARCH_ELECTOR = r"निर्वाचक का नाम\s*"
SEARCH_ID = r"(BR\/\d{2}\/\d{3}\/\d{6}|[A-Z]{3}\d{7})"
SEARCH_AGE = r"उम्र\s*:\s*(\d{1,3})"
SEARCH_HOUSE = r"गृह संख्या\s*:\s*(\d{1,4})"
SEARCH_SEX = r"लिंग\s*:\s*(महिला|पुरूष)"

#dataTable1
COLUMN_NAMES1 = ["VoterID", "Name", "Age", "Sex", "HouseNum", "Family"]


"""An enum that determines the token type (explained below)
"""
class TokenType(Enum):
    PARAGRAPH = 1
    CHART = 2

"""A class for representing tokens.

Tokens are machine-readable chunks of data extracted from PDF files. So far supports
paragraphs and charts (represented as pandas dataframes) only. Meant to be a read-only
data structure.
"""
class Token:
    token_type = None
    stored_data = None
    def __init__(self, type, data):
        self.token_type = type
        self.stored_data = data

    def getType(self):
        return self.token_type

    def getData(self):
        return self.getData

"""Returns a temporary directory filled with processed images and PIL Image
objects.

Takes in the path to the pdf to process, and icnreases
"""
def getImagePages(path):
    global OUTPUT_PAGE_LIMIT

    dir = tempfile.TemporaryDirectory(dir = os.getcwd())
    res = []
    pdf = PdfFileReader(open(path,'rb'))
    max_pages = pdf.getNumPages()
    for page in range(0, max_pages, OUTPUT_PAGE_LIMIT):
        res += convert_from_path(path,
                                 dpi=300,
                                 first_page = page,
                                 last_page = min(page + OUTPUT_PAGE_LIMIT - 1, max_pages),
                                 output_folder = dir.name)
    return {"tempdir": dir, "images": res}


"""Returns None

Takes an object created by getImagePages and closes
"""
def cleanupImageOutput(images_obj):
    for image in images_obj["images"]:
        image.close()
    images_obj["tempdir"].cleanup()

"""Returns None

Saves a list of images to "images/namingX.JPEG" where X is the 0 indexed page
number.
"""
def dumpImagePages(pages_obj, naming="page"):
    try:
        os.makedirs("images")
    except FileExistsError:
        print("INFO: images/ already exits. Continuing...")
    for i in range(len(pages_obj["images"])):
        pages_obj["images"][i].save("images/" + naming + str(i) + ".JPEG", "JPEG")


"""Returns None

Save a list of raw text to a list of .txt files in plaintext/namingX.text
"""
def dumpTextPages(pages, naming="page"):
    try:
        os.makedirs("plaintext")
    except FileExistsError:
        print("INFO: plaintext/ already exists. Continuing...")
    for i in range(len(pages)):
        writefile = open("plaintext/" + naming + str(i) + ".txt", "w+")
        writefile.write(pages[i])
        writefile.close()


"""Returns list of strings

Takes a list of images and returns one string of text per page in a list.
Looks for images in "folder" named "naming"X."extension" until num_pages -1.
"""
def extractPagesText(folder="images", naming="page", extension="JPEG", language='eng', num_pages=1, clist="", psm=3):
    clist = "-c " + clist if clist != "" else clist
    print("Performing language {}".format(language))
    res = []
    for i in range(num_pages):
        filename = folder + "/" + naming + str(i) + "." + extension
        text = str(((pytesseract.image_to_string(Image.open(filename), 
            lang=language, config='--psm ' + str(psm) + " " + clist))))
        res.append(text)
    return res

"""Returns a list of tokens found in the page text.

Input is a string of text.
"""
def getTokensFromPageText(text):
    # TODO: Regex, probably. We'll hold off on this idea for now.
    return None

"""Returns a list

x is a list, to is a length (positive integer), and val is any value.

Fills a list in with the specified value if the length is less than the argument.
"""
def fillListTo(x, to, val):
    if len(x) < to:
        for i in range(to - len(x)):
            x.append(val)
    return x

"""Returns a string

Returns a string with every hindi unicode character in it to work with 
python re. Not sure why re doesn't work like any other regex engine but 
whatever.
"""
def getHindiAlphabet():
    string = ""
    for i in range(0x0900, 0x0980):
        string += chr(i)
    return string


"""Returns a list of lists of Pandas Dataframes

Between the specified start and end pages, this function looks for the variables:
voterID, name, fathers_name, house_no, age and sex.

Somewhat limited -- expects that hindi_text and english_text were parsed
from the same source and are ordered in the same way. Standard electoral roll
of Bihar.

The code creates 30 slots to fill in DataFrame information. If less than thirty 
slots are found those DataFrames will be empty. The list reads left to right
top to bottom.

It also expects the english to be ordered column first, and the hindi to be
ordered row first. It's all hard-coded.

Skips the whole token idea. One list per page between start_index and
end_index.
"""
def extractTable1(hindi_text, english_text, start_index = 0, end_index = 0):
    global SEARCH_FAMILY
    global SEARCH_ELECTOR
    global SEARCH_ID
    global SEARCH_AGE
    global SEARCH_HOUSE
    global SEARCH_SEX
    global COLUMN_NAMES1

    SEARCH_NAME = r"([" + getHindiAlphabet() + r"]+ " + r"[" + getHindiAlphabet() + r"]+)"

    elector_name_pattern = re.compile(SEARCH_ELECTOR + SEARCH_NAME)
    family_name_pattern = re.compile(SEARCH_FAMILY + SEARCH_NAME)
    voterid_pattern = re.compile(SEARCH_ID)
    age_pattern = re.compile(SEARCH_AGE)
    house_pattern = re.compile(SEARCH_HOUSE)
    sex_pattern = re.compile(SEARCH_SEX)

    start = start_index
    end = end_index + 1 if end_index != 0 else len(text_pages)
    res = []

    for i in range(start, end):
        thispage_entries = []
        
        thisenglish = english_text[i]
        thishindi = hindi_text[i]

        # these are in the "correct" order (left to right)
        # these all need to be the same size so we can make the dataframe
        elector_match_list = re.findall(elector_name_pattern, thishindi)
        elector_match_list = fillListTo(elector_match_list, 30, "")

        family_match_list = re.findall(family_name_pattern, thishindi)
        family_match_list = fillListTo(family_match_list, 30, "")

        # age we auto-convert to a number because we can
        age_match_list = re.findall(age_pattern, thishindi)
        age_match_list = fillListTo(age_match_list, 30, "")
        age_match_list = [int(age) for age in age_match_list]

        house_match_list = re.findall(house_pattern, thishindi)
        house_match_list = fillListTo(house_match_list, 30, "")

        sex_match_list = re.findall(sex_pattern, thishindi)
        sex_match_list = fillListTo(sex_match_list, 30, "")

        _voterid_match_list = re.findall(voterid_pattern, thisenglish)
        _voterid_match_list = fillListTo(_voterid_match_list, 30, "")

        # these come column first and are therefore wrong and bad
        # but we can fix that :)
        voterid_match_list = []
        for j in range(10):
            voterid_match_list.append(_voterid_match_list[j])
            voterid_match_list.append(_voterid_match_list[j + 10])
            voterid_match_list.append(_voterid_match_list[j + 10 * 2])

        for j in range(30):
            entry = {
                "VoterID": voterid_match_list[j],
                "Name": elector_match_list[j],
                "Age": age_match_list[j],
                "Sex": sex_match_list[j],
                "HouseNum": house_match_list[j],
                "Family": family_match_list[j]
            }
            thispage_entries.append(entry)
        
        thispage = pd.DataFrame(columns = COLUMN_NAMES1, data = thispage_entries) 
        res.append(thispage)
    
    return res


if __name__ == "__main__":
    print("Running LoremIpsum.pdf")
    lorem_ipsum_pages = getImagePages("test_files/LoremIpsum.pdf")
    dumpImagePages(lorem_ipsum_pages)
    text_pages = extractPagesText(num_pages=3)
    dumpTextPages(text_pages)

    #print("Running english.pdf")
    #english_pages = getImagePages("test_files/english.pdf")
    #dumpImagePages(english_pages, naming="en-page")
    #en_text_pages = extractPagesText(num_pages=6, naming="en-page")
    #dumpTextPages(en_text_pages, naming="en-page")

    print("Running hindi.pdf")
    hindi_pages = getImagePages("test_files/hindi.pdf")
    dumpImagePages(hindi_pages, naming="hin-page")
    hin_text_pages = extractPagesText(num_pages=4, naming="hin-page", language="hin", psm=4,
        clist="tessedit_char_blacklist=॥")
    en_text_text_pages = extractPagesText(num_pages=4, naming="hin-page", language="eng",
        clist="tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ:/")
    dumpTextPages(hin_text_pages, naming="hin-page")
    dumpTextPages(en_text_text_pages, naming="ehin-page")

    cleanupImageOutput(lorem_ipsum_pages)
    # cleanupImageOutput(english_pages)
    cleanupImageOutput(hindi_pages)

    print("Converting to dataframe...")
    dataframes = extractTable1(hin_text_pages, en_text_text_pages, 2)
    print(dataframes[0].head())
