from polyglot.transliteration import Transliterator
from pypdf_ocr import getHindiAlphabet
import argparse

"""Returns None

Takes a path to a file as its first parameter and saves the transliterated 
version to a new file (second paramter if given)
"""
def transliterate_csv(path_in, path_out):
    res = []
    transliterator = Transliterator(source_lang="hi", target_lang="en")
    alpha = getHindiAlphabet()

    with open(path_in, "r", encoding='utf-8') as in_file:
        lines = in_file.read().splitlines()
        res.append(lines[0])
        for i in range(1, len(lines)):
            k = 0
            j = k
            res_line = ""
            while j < len(lines[i]):
                # if this is a hindi character, start trying to find the 
                # whole word
                if lines[i][k] in alpha:
                    # skip to the end of the hindi characters
                    while k + 1 < len(lines[i]) and lines[i][k+1] in alpha:
                        k += 1
                    # use this next variable to get where the last hindi character was
                    m = j
                    while m >= 1 and lines[i][m - 1] not in alpha:
                        m -= 1
                    res_line += lines[i][m:j]
                    hindi_str = lines[i][j:k+1]
                    en_str = transliterator.transliterate(hindi_str)
                    res_line += en_str
                k += 1
                j = k
            # start at the end and add in the last bit of non-hindi
            m = len(lines[i])
            while m >= 1 and lines[i][m - 1] not in alpha:
                m -= 1
            res_line += lines[i][m:len(lines[i])]
            res.append(res_line)

    with open(path_out, "w+") as out_file:
        for line in res:
            out_file.write("{}\n".format(line))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple tool to transliterate a hindi csv to English")
    parser.add_argument("--infile", help="the file to transliterate", required=True)
    parser.add_argument("--outfile", help="the path to save to", required=True)

    args = parser.parse_args()
    transliterate_csv(args.infile, args.outfile)
