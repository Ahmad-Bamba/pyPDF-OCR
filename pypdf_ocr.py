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
import json

# Globals

# Memory management
OUTPUT_PAGE_LIMIT = 5

# Regular Expressions
SEARCH_FAMILY = r"(?:पिता|पति) का नाम\s*(?:४|:|न)?\s*"
SEARCH_ELECTOR = r"निर्वाचक का नाम\s*"
SEARCH_ID = r"(BR\/\d{2}\/\d{3}\/\d{6}|[A-Z]{3}\d{7})"
SEARCH_AGE = r"उम्र\s*(?:४|:|न)?\s*(\d{1,3})"
SEARCH_HOUSE = r"गृह संख्या\s*(?:४|:|न)?\s*(\d{1,4})"
SEARCH_SEX = r"लिंग\s*(?:४|:|न)?\s*(महिला|पुरूष)"

SEARCH_AC = r"विधान सभा क्षेत्र की संख्या\s*,\s*नाम व आरक्षण स्थिति\s*:\s*(\d+)[\s\"&\-'“”‘’?!.:,#*|]*"
SEARCH_PART = r"संख्या\s*:\s*(\d+)"
SEARCH_PC = r"लोक सभा क्षेत्र की संख्या\s*,\s*नाम व आरक्षण स्थिति\s*:\s*(\d+)[\s\"&\-'“”‘’?!.:,#*|]*"
SEARCH_SUBPART = r"\(\d+\)\s*"
SEARCH_VILLAGE = r"मुख्य ग्राम\s*(?:४|:|न)?\s*"
SEARCH_POST_OFFICE = r"डाकघर\s*(?:४|:|न)?\s*"
SEARCH_POLICE = r"थाना\s*(?:४|:|न)?\s*"
SEARCH_RAJASVA_HALKA = r"राजस्व हलका\s*(?:४|:|न)?\s*((?:\d{3})+)"
SEARCH_PANCHAYAT = r"पंचायत\s*(?:४|:|न)?\s*"
SEARCH_ANCHAL = r"अंचल ु\s*(?:४|:|न)?\s*"
SEARCH_PRAKHAND = r"प्रखंड\s*(?:४|:|न)?\s*"
SEARCH_ANUMANDAL = r"अनूमंडल\s*(?:४|:|न)?\s*"
SEARCH_DISTRICT = r"जिला\s*(?:४|:|न)?\s*"
SEARCH_ZIP = r"पिन कोड\s*(?:४|:|न)?\s*\.*\s*(\d{6})"
SEARCH_POLLING_BOOTH = r"मतदान केन्द्र की संख्या व नाम\s*(?:४|:|न)?\s*\d+[.,\s]*"



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

Save a list of raw text to a list of plaintext files in plaintext/namingX.text
The extension is adjustable with the extension parameter.
"""
def dumpTextPages(pages, naming="page", extension="txt"):
    try:
        os.makedirs("plaintext")
    except FileExistsError:
        print("INFO: plaintext/ already exists. Continuing...")
    for i in range(len(pages)):
        writefile = open("plaintext/" + naming + str(i) + "." + extension, "w+")
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

    elector_name_pattern = re.compile(SEARCH_ELECTOR + SEARCH_NAME, re.UNICODE)
    family_name_pattern = re.compile(SEARCH_FAMILY + SEARCH_NAME, re.UNICODE)
    voterid_pattern = re.compile(SEARCH_ID, re.UNICODE)
    age_pattern = re.compile(SEARCH_AGE, re.UNICODE)
    house_pattern = re.compile(SEARCH_HOUSE, re.UNICODE)
    sex_pattern = re.compile(SEARCH_SEX, re.UNICODE)

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


"""Returns a dictionary

This function is to be used to parse the first page of Bihar electoral rolls.
It expects a string of the hindi-parsed data. Dictionary contains

 - AC number
 - Part
 - PC number
 - Subpart
 - Village
 - Post office
 - Police
 - Rajasva Halka
 - Panchayat
 - Anchal
 - Prakhand
 - District
 - Zip code
 - Polling booth
"""
def extractPage1(page_one_text):
    global SEARCH_AC
    global SEARCH_PC
    global SEARCH_PART
    global SEARCH_SUBPART
    global SEARCH_VILLAGE
    global SEARCH_POLICE
    global SEARCH_POST_OFFICE
    global SEARCH_PRAKHAND
    global SEARCH_ANUMANDAL
    global SEARCH_DISTRICT
    global SEARCH_POLLING_BOOTH

    alpha = getHindiAlphabet()
    alpha_ = alpha + " "
    alphanum = alpha_ + "0123456789"

    # build regex strings
    SEARCH_AC_STR = SEARCH_AC + r"([" + alpha + "]+)" + r"\s*-\s*([" + alpha + "]+)"
    SEARCH_PC_STR = SEARCH_PC + r"([" + alpha + "]+)" + r"\s*-\s*([" + alpha + "]+)"
    SEARCH_SUBPART_STR = SEARCH_SUBPART + r"([" + alpha_ + r"]+)"
    SEARCH_VILLAGE_STR = SEARCH_VILLAGE + r"([" + alpha_ + r"]+)"
    SEARCH_POST_OFFICE_STR = SEARCH_POST_OFFICE + r"([" + alpha_ + r"]+)"
    SEARCH_POLICE_STR = SEARCH_POLICE + r"([" + alpha_ + r"]+)"
    SEARCH_PANCHAYAT_STR = SEARCH_PANCHAYAT + r"([" + alpha_ + r"]+)"
    SEARCH_ANCHAL_STR = SEARCH_ANCHAL + r"([" + alphanum + r"]+)"
    SEARCH_PRAKHAND_STR = SEARCH_PRAKHAND + r"([" + alphanum + r"]+)"
    SEARCH_ANUMANDAL_STR = SEARCH_ANUMANDAL + r"([" + alpha_ + r"]+)"
    SEARCH_DISTRICT_STR = SEARCH_DISTRICT + r"([" + alpha_ + r"]+)"
    SEARCH_POLLING_BOOTH_STR = SEARCH_POLLING_BOOTH + r"([" + alpha_ + r"]+\s*,\s*[" + alpha_ + r"]+)"

    # these ones don't change
    SEARCH_ZIP_STR = SEARCH_ZIP
    SEARCH_RAJASVA_HALKA_STR = SEARCH_RAJASVA_HALKA
    SEARCH_PART_STR = SEARCH_PART

    # okay time to search
    ac_pattern = re.compile(SEARCH_AC_STR, re.UNICODE)
    part_pattern = re.compile(SEARCH_PART_STR, re.UNICODE)
    pc_pattern = re.compile(SEARCH_PC_STR, re.UNICODE)
    village_pattern = re.compile(SEARCH_VILLAGE_STR, re.UNICODE)
    post_office_pattern = re.compile(SEARCH_POST_OFFICE_STR, re.UNICODE)
    police_pattern = re.compile(SEARCH_POLICE_STR, re.UNICODE)
    rajasva_halka_pattern = re.compile(SEARCH_RAJASVA_HALKA_STR, re.UNICODE)
    panchayat_pattern = re.compile(SEARCH_PANCHAYAT_STR, re.UNICODE)
    prakhand_pattern = re.compile(SEARCH_PRAKHAND_STR, re.UNICODE)
    district_pattern = re.compile(SEARCH_DISTRICT_STR, re.UNICODE)
    anchal_pattern = re.compile(SEARCH_ANCHAL_STR, re.UNICODE)
    zip_pattern = re.compile(SEARCH_ZIP_STR, re.UNICODE)
    polling_pattern = re.compile(SEARCH_POLLING_BOOTH_STR, re.UNICODE)

    # make the result
    res = {
        "Assembly Constituency": None,
        "Part": None,
        "Parlimentary Constituency": None,
        "Village": None,
        "Post Office": None,
        "Police Station": None,
        "Rajasva Halka": None,
        "Panchayat": None,
        "Anchal": None,
        "Prakhand": None,
        "District": None,
        "Zip Code": None,
        "Polling Booth": None
    }

    # run the searches
    try:
        ac_hit = re.search(ac_pattern, page_one_text)
        res["Assembly Constituency"] = ac_hit.group(0)
    except IndexError:
        pass

    try:
        part_hit = re.search(part_pattern, page_one_text)
        res["Part"] = part_hit.group(1)
    except IndexError:
        pass

    try:
        pc_hit = re.search(pc_pattern, page_one_text)
        res["Parlimentary Constituency"] = pc_hit.group(0)
    except IndexError:
        pass

    try:
        village_hit = re.search(village_pattern, page_one_text)
        res["Village"] = village_hit.group(1)
    except IndexError:
        pass

    try:
        post_office_hit = re.search(post_office_pattern, page_one_text)
        res["Post Office"] = post_office_hit.group(1)
    except IndexError:
        pass

    try:
        police_station_hit = re.search(police_pattern, page_one_text)
        res["Police Station"] = police_station_hit.group(1)
    except IndexError:
        pass

    try:
        rajasva_halka_hit = re.search(rajasva_halka_pattern, page_one_text)
        res["Rajasva Halka"] = rajasva_halka_hit.group(1)
    except IndexError:
        pass

    try:
        panchayat_hit = re.search(panchayat_pattern, page_one_text)
        res["Panchayat"] = panchayat_hit.group(1)
    except IndexError:
        pass

    try:
        anchal_hit = re.search(anchal_pattern, page_one_text)
        res["Anchal"] = anchal_hit.group(1)
    except IndexError:
        pass

    try:
        prakhand_hit = re.search(prakhand_pattern, page_one_text)
        res["Prakhand"] = prakhand_hit.group(1)
    except IndexError:
        pass

    try:
        district_hit = re.search(district_pattern, page_one_text)
        res["District"] = district_hit.group(1)
    except IndexError:
        pass

    try:
        zip_hit = re.search(zip_pattern, page_one_text)
        res["Zip Code"] = zip_hit.group(1)
    except IndexError:
        pass

    try:
        polling_hit = re.search(polling_pattern, page_one_text)
        res["Polling Booth"] = polling_hit.group(1)
    except IndexError:
        pass


    return res
  

if __name__ == "__main__":
    #print("Running LoremIpsum.pdf")
    #lorem_ipsum_pages = getImagePages("test_files/LoremIpsum.pdf")
    #dumpImagePages(lorem_ipsum_pages)
    #text_pages = extractPagesText(num_pages=3)
    #dumpTextPages(text_pages)

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
    
    # cleanupImageOutput(lorem_ipsum_pages)
    # cleanupImageOutput(english_pages)
    cleanupImageOutput(hindi_pages)

    dumpTextPages(hin_text_pages, naming="hin-page")
    dumpTextPages(en_text_text_pages, naming="ehin-page")

    print("Parsing page 1...")
    page1 = extractPage1(hin_text_pages[0])
    page1str = json.dumps(page1, ensure_ascii=False)

    print(page1str)
    dumpTextPages([page1str], naming="p1parsed", extension="json")

    #print("Converting to dataframe...")
    #dataframes = extractTable1(hin_text_pages, en_text_text_pages, 2)
    #print(dataframes[0].head())
