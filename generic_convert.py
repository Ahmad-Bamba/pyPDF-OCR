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

"""Returns a list of images

Expects a PDF file at path. Applies a high contrast filter.
"""
def getImagePages(path):
    images = convert_from_path(path)
    res = []
    for img in images:
        enhancer = ImageEnhance.Contrast(img)
        res.append(enhancer.enhance(3.5))
    return res

"""Returns None

Saves a list of images to "images/namingX.JPEG" where X is the 0 indexed page
number.
"""
def dumpImagePages(pages, naming="page"):
    try:
        os.makedirs("images")
    except FileExistsError:
        print("INFO: images/ already exits. Continuing...")
    for i in range(len(pages)):
        pages[i].save("images/" + naming + str(i) + ".JPEG", "JPEG")


"""Returns list of strings

Takes a list of images and returns one string of text per page in a list.
Looks for images in "folder" named "naming"X."extension" until numPages -1.
"""
def extractPagesText(folder="images", naming="page", extension="JPEG", numPages=1):
    res = []
    for i in range(numPages):
        filename = folder + "/" + naming + str(i) + "." + extension
        text = str(((pytesseract.image_to_string(Image.open(filename)))))
        res.append(text)
    return res

"""Returns a list of tokens found in the page text.

Input is a string of text.
"""
def getTokensFromPageText(text):
    # TODO: Regex, probably.
    return None


if __name__ == "__main__":
    lorem_ipsum_pages = getImagePages("test_files/LoremIpsum.pdf")
    dumpImagePages(lorem_ipsum_pages)
    print(extractPagesText(numPages=3))
