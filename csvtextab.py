#!/usr/bin/python3
"""
MIT License

Copyright (c) 2020 Christian Strauch (flinti)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

"""
usage: csvtextab [-h] [-a ARGUMENT] [-c COLUMN_ORDER_INT] [-C COLUMN_ORDER_STRING] [-t]
                 [-T] [-V VSPACE] [-L] [-H] [-e ENCODING] [-v] [-f INFORMAT] [-l]
                 [-p PRETEXT] [-P POSTTEXT]
                 [infile] [outfile]

Create tex formatted table (tabular environment) output from csv file. Leading spaces are
stripped from the column headers. Try 'csvtextab.py -LV 4pt <INFILE>' if you are unsure
which options to use. If not file is specified, the program reads from stdin and outputs to
stdout. If only one file is specified, the program reads from the file and outputs to
stdout.

positional arguments:
  infile                input file
  outfile               output file

optional arguments:
  -h, --help            show this help message and exit
  -a ARGUMENT, --argument ARGUMENT
                        Argument to the tabular environment. Make sure that it is
                        appropriate for the number of columns in the actual output. Default
                        is 'cccc...', i.e. as many 'c' as there are columns.
  -c COLUMN_ORDER_INT, --column-order-int COLUMN_ORDER_INT
                        Specify the columns (as index 0..N) in the order as they should
                        appear in the tex output. A column may be specified multiple times.
                        Example: -c 1,0,0,2
  -C COLUMN_ORDER_STRING, --column-order-string COLUMN_ORDER_STRING
                        Specify the columns (as string, i.e. the column header) in the
                        order as they should appear in the tex output. A column may be
                        specified multiple times. Example: -c name,title,name,address.
  -t, --texheader       Do not escape column headers, assume that every header is valid
                        latex.
  -T, --texcells        Do not escape the cells, assume that every cell in the csv file is
                        valid tex.
  -V VSPACE, --vspace VSPACE
                        Vertical space between the rows. Parameter needs to be a valid
                        latex unit. If negative, this option cannot be used in conjunction
                        with -L (--headerline). Example: -V 5.5pt
  -L, --headerline      Use a horizontal line after the header line (\hline). If the -V
                        (--vspace) option is specified, an empty row with a negative
                        vertical space of the same magnitude is added after the line.
  -H, --noheader        Treat the first row as data. Use -H for files that do not have a
                        first line with column names.
  -e ENCODING, --encoding ENCODING
                        Encoding for input and output file. Format <encoding
                        in>[,<encoding_out>] (naming as in the 'encoding' named argument of
                        the python open function). If only <encoding in> is specified, it
                        is assumed to be the encoding for both files. Example: -e utf-8
  -v, --verbose         Enable verbose mode. Writes debug information to stderr
  -f INFORMAT, --informat INFORMAT
                        specify input file format. 1 to 2 characters:
                        <delimiter><quotechar>.
  -l, --latex           Output compilable latex document, i.e. a document with preamble and
                        \begin{document}...\end{document}
  -p PRETEXT, --pretext PRETEXT
                        PRETEXT is prepended in front of the \begin{tabular}
                        command. Example: -p "\centering" for a centered table.
  -P POSTTEXT, --posttext POSTTEXT
                        POSTTEXT is appended after the \end{tabular} command.
"""


import csv
import os
import sys
import re
import argparse

#for this snippet, thanks to https://stackoverflow.com/a/25875504
#note that 'unicode' is renamed to 'str' in py3
def tex_escape(text):
    """
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key = lambda item: - len(item))))
    return regex.sub(lambda match: conv[match.group()], text)


# default settings
verbose = False
inencoding = "utf-8"
outencoding = "utf-8"
informat = [',', '"']
noheader = False

column_array = []
tabular_arg = None
texheader = False
texcells = False
vspace = ""
lastrow = ""
pretext = ""
posttext = ""
headerline = False
titlepostfix = ""


########################################################################################################################
#                                        Tex creation
########################################################################################################################

def headerwrap(cellstr):
    if texheader:
        return cellstr
    else:
        return tex_escape(cellstr)

def cellwrap(cellstr):
    if texcells:
        return cellstr
    else:
        return tex_escape(cellstr)

def rowprefix(index, maxidx):
    return ""

def rowpostfix(index, maxidx):
    postfix = "\\\\"
    if vspace != "":
        postfix += "[" + vspace + "]"
    return postfix

def obtain_tex(csvrows):
    if len(csvrows) == 0:
        return ""
    titles = []
    column_indices = {}
    selected_columns = [*range(0, len(csvrows[0]))]
    column_amount = len(selected_columns)
    
    output = "\\begin{tabular}{"
    
    if not noheader:
        titles = csvrows[0]
        for i in range(0, len(titles)):
            titles[i] = titles[i].lstrip()
            column_indices[titles[i]] = i
    # if a custom column sorting is given
    if len(column_array) > 0:
        if isinstance(column_array[0], int):# col indices were specified
            selected_columns = column_array
            column_amount = len(selected_columns)
        else: # col headers were specified
            selected_columns = []
            for colname in column_array:
                try:
                    idx = column_indices[colname]
                    selected_columns.append(idx)
                except:
                    print("WARNING: column with header '" + colname + "' not found!", file=sys.stderr)
            column_amount = len(selected_columns)
    
    if verbose:
        print("column headers:", titles, file=sys.stderr)
        print("selected columns:", selected_columns, file=sys.stderr)
    
    if column_amount == 0:
        return ""
    
    if tabular_arg == None:
        for i in range(0, column_amount):
            output += "c"
    else:
        output += tabular_arg
    output += "}\n"
    
    # header row
    if noheader:
        pass
    else:
        output += "\t"
        firstidx = selected_columns[0]
        if firstidx < len(titles):
            output += headerwrap(titles[firstidx])
        output += "\t"
        for q in range(1, column_amount):
            idx = selected_columns[q]
            output += "&\t"
            if idx < len(titles):
                output += headerwrap(titles[idx]) + "\t"
        output += "\\\\"
        if vspace != "":
            output += "[" + vspace + "]"

        if headerline:
            output += "\n\t\\hline"
            if vspace != "":
                for i in range(1, column_amount):
                    output += "& "
                output += "\\\\[-" + vspace + "]"
        output += titlepostfix + "\n\n"
    # data rows
    for i in range(0 if noheader else 1, len(csvrows)):
        row = csvrows[i]
        rowlen = len(row)
        
        if rowlen == 0:
            continue
        
        output += "\t" + rowprefix(i, rowlen-1)
        
        firstidx = selected_columns[0]
        if firstidx < rowlen:
            output += cellwrap(row[firstidx])
        output += "\t"
        for q in range(1, column_amount):
            idx = selected_columns[q]
            output += "&\t"
            if idx < rowlen:
                output += cellwrap(row[idx]) + "\t"
        output += rowpostfix(i, rowlen-1) + "\n"
        
    
    output += "\\end{tabular}\n"
    return output


########################################################################################################################
#                                        Argument Parsing
########################################################################################################################


argparser = argparse.ArgumentParser(description="Create tex formatted table (tabular environment) output from csv file. Leading spaces are stripped from the column headers.\nTry 'csvtextab.py -LV 4pt <INFILE>' if you are unsure which options to use. If not file is specified, the program reads from stdin and outputs to stdout. If only one file is specified, the program reads from the file and outputs to stdout.")
argparser.add_argument("infile", nargs='?', default="-", help="input file")
argparser.add_argument("outfile", nargs='?', default="-", help="output file")
argparser.add_argument("-a", "--argument", nargs=1, help="Argument to the tabular environment. Make sure that it is appropriate for the number of columns in the actual output. Default is 'cccc...', i.e. as many 'c' as there are columns.")
argparser.add_argument("-c", "--column-order-int", nargs=1, help="Specify the columns (as index 0..N) in the order as they should appear in the tex output. A column may be specified multiple times. Example: -c 1,0,0,2")
argparser.add_argument("-C", "--column-order-string", nargs=1, help="Specify the columns (as string, i.e. the column header) in the order as they should appear in the tex output. A column may be specified multiple times. Example: -c name,title,name,address.")
argparser.add_argument("-t", "--texheader", action='store_true', help="Do not escape column headers, assume that every header is valid latex.")
argparser.add_argument("-T", "--texcells", action='store_true', help="Do not escape the cells, assume that every cell in the csv file is valid tex.")
argparser.add_argument("-V", "--vspace", nargs=1, help="Vertical space between the rows. Parameter needs to be a valid latex unit. If negative, this option cannot be used in conjunction with -L (--headerline). Example: -V 5.5pt")
argparser.add_argument("-L", "--headerline", action="store_true", help="Use a horizontal line after the header line (\\hline). If the -V (--vspace) option is specified, an empty row with a negative vertical space of the same magnitude is added after the line.")
argparser.add_argument("-H", "--noheader", action='store_true', help="Treat the first row as data. Use -H for files that do not have a first line with column names.")
argparser.add_argument("-e", "--encoding", nargs=1, help="Encoding for input and output file. Format <encoding in>[,<encoding_out>] (naming as in the 'encoding' named argument of the python open function). If only <encoding in> is specified, it is assumed to be the encoding for both files. Example: -e utf-8")
argparser.add_argument("-v", "--verbose", action='store_true', help="Enable verbose mode. Writes debug information to stderr")
argparser.add_argument("-f", "--informat", help="specify input file format. 1 to 2 characters: <delimiter><quotechar>.")
argparser.add_argument("-l", "--latex", action='store_true', help="Output compilable latex document, i.e. a document with preamble and \\begin{document}...\\end{document}")
argparser.add_argument("-p", "--pretext", nargs=1, help="PRETEXT is prepended in front of the \\begin{tabular} command. Example: -p \"\\centering\" for a centered table.")
argparser.add_argument("-P", "--posttext", nargs=1, help="POSTTEXT is appended after the \\end{tabular} command.")

args = argparser.parse_args()

verbose = args.verbose
noheader = args.noheader
texheader = args.texheader
texcells = args.texcells
headerline = args.headerline

if args.argument:
    tabular_arg = args.argument[0]

if args.column_order_int:
    column_array = args.column_order_int[0].split(",")
    if len(column_array) == 0:
        print("ERROR: Invalid argument to the --column-order-int option.", file=sys.stderr)
        exit(1)
    for i in range(0, len(column_array)):
        index = 0
        try:
            index = int(column_array[i])
        except:
            print("ERROR: Invalid argument to the --column-order-int option. Only a comma separated list of nonnegative integers is allowed!", file=sys.stderr)
            exit(1)
        if index < 0:
            print("ERROR: Invalid argument to the --column-order-int option. Negative indices not allowed!", file=sys.stderr)
            exit(1)
        column_array[i] = index

if args.column_order_string:
    if noheader:
        print("ERROR: Option --column-order-string (-C) is not compatible with --noheader (-h)!", file=sys.stderr)
        exit(1)
    column_array = args.column_order_string[0].split(",")
    if len(column_array) == 0:
        print("ERROR: Invalid argument to the --column-order-string option.", file=sys.stderr)
        exit(1)

if args.encoding:
    encstrs = args.encoding[0].split(",")
    if len(encstrs) > 0:
        inencoding = encstrs[0]
    elif len(encstrs > 1):
        outencoding = encstrs[1]
    else:
        print("ERROR: --encoding needs at least one parameter", file=sys.stderr)
        exit(1)
if verbose:
    print("Selected encodings: in:", inencoding, "out:", outencoding, file=sys.stderr)

if args.vspace:
    vspace = args.vspace[0]

if args.informat:
    informatlen = len(args.informat)
    if informatlen > 0:
        for i in range(min(2, informatlen)):
            informat[i] = args.informat[i]

if args.latex == True:
    pretext = pretext+"\\documentclass{article}\\begin{document}\n"
    posttext = posttext+"\\end{document}\n"

if args.pretext:
    pretext += args.pretext
if args.posttext:
    posttext = args.posttext + posttext

# setup input file
infile = sys.stdin
if args.infile != '-':
    try:
        infile = open(args.infile, "r", encoding = inencoding, newline='')
    except Exception as e:
        print("ERROR: Could not open input file: " + str(e), file=sys.stderr)
        exit(1)
    if verbose:
        print("Reading from file '"+args.infile+"'", file=sys.stderr)
else:
    if verbose:
        print("Reading from stdin", file=sys.stderr)
# setup output file
outfile = sys.stdout
if args.outfile != '-':
    try:
        outfile = open(args.outfile, "w", encoding = outencoding)
    except Exception as e:
        print("ERROR: Could not open input file: " + str(e), file=sys.stderr)
        exit(1)
    if verbose:
        print("Writing to file '"+args.outfile+"'", file=sys.stderr)
else:
    if verbose:
        print("Write to stdout", file=sys.stderr)



########################################################################################################################
#                                        Read and Write files
########################################################################################################################


csvreader = csv.reader(infile, delimiter=informat[0], quotechar=informat[1])
csvrows = []
for row in csvreader:
    csvrows.append(row)
outtext = obtain_tex(csvrows)
if pretext != "":
    pretext += "\n"
outfile.write(pretext)
outfile.write(outtext)
infile.close()
outfile.write(posttext)
outfile.close()



