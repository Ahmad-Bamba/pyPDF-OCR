from polyglot.transliteration import Transliterator
import argparse

"""Returns None

Takes a path to a file as its first parameter and saves the transliterated 
version to a new file (second paramter if given)
"""
def transliterate_csv(path_in, path_out):
    res = []
    transliterator = Transliterator(source_lang="hi", target_lang="en")
    with open(path_in, "r", encoding='utf-8') as in_file:
        lines = in_file.read().splitlines()
        res.append(lines[0])
        for i in range(1, len(lines)):
            en_str = transliterator.transliterate(lines[i])
            if i < 5:
                print("{}: {} | {}".format(type(en_str), en_str, lines[i]))
            res.append(en_str)

    print("{}\n{}".format(len(res), res[1]))

    with open(path_out, "w+") as out_file:
        for line in res:
            out_file.write("{}".format(line))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple tool to transliterate a hindi csv to English")
    parser.add_argument("--infile", help="the file to transliterate", required=True)
    parser.add_argument("--outfile", help="the path to save to", required=True)

    args = parser.parse_args()
    transliterate_csv(args.infile, args.outfile)
