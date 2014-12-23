#   -*- coding: utf-8 -*-

"""\
This program collects summary files from FastQC folders specified in command line
and compiles them into a single summary (printed to stdout)
Usage:
    scripts/xvpy  scripts/fqcsumm.py  filenames-file  fastqc-dir  [ > result.txt ]
"""

import sys
import os
import os.path
from termcolor import colored

import params as p
import rwfiles as rw

header = """\
Basic Statistics
| Per base sequence quality
| | Per sequence quality scores
| | | Per base sequence content
| | | | Per base GC content
| | | | | Per sequence GC content
| | | | | | Per base N content
| | | | | | | Sequence Length Distribution
| | | | | | | | Sequence Duplication Levels
| | | | | | | | | Overrepresented sequences
| | | | | | | | | | Kmer Content
| | | | | | | | | | |\
"""

marks = dict([
        ("PASS", colored("+",on_color="on_green",attrs=["bold"])),
        ("WARN", colored("?",on_color="on_yellow",attrs=["bold"])),
        ("FAIL", colored("-",on_color="on_red",attrs=["bold"]))
])

global is_paired_end
global basenames    # [ base-filename ]
global basename_len
def prepareFileList(): #{{{
    global is_paired_end, basenames, basename_len
    is_paired_end = os.getenv("IS_PAIRED_END")=="T"
    basenames = os.getenv("BASE_FILENAMES").split()
    basename_len = max([ len(_bn) for _bn in basenames ]) + 2
#}}}

def printHeader(): #{{{
    for hline in header.split('\n'):
        p.vprint(0, "%*s %s" % (basename_len, " ", hline))
#}}}

def processSamples(fqc_dir): #{{{
    for basename in basenames:
        if is_paired_end:
            fn_suffix = "val_%s.fq_fastqc" % basename[-1]
        else:
            fn_suffix = "trimmed.fq_fastqc"
        summary_fn = os.path.join(fqc_dir, "%s_%s" % (basename,fn_suffix), "summary.txt")
        (rows,_) = rw.loadCSV( summary_fn, ["Status","Descr","Name"] )
        out_line = "%-*s" % (basename_len, basename)
        for row in rows:
            out_line += " " + marks[ row["Status"] ]
        p.vprint(0, out_line)
#}}}

def main(): #{{{
    fqc_dir = sys.argv[1]
    prepareFileList()
    printHeader()
    processSamples(fqc_dir)
#}}}

# Start-up code ================================================={{{
if __name__=="__main__":
    main()
#................................................................}}}
