#   -*- coding: utf-8 -*-

"""\
See 'printUsage()' function.
"""

import sys
import os
import os.path
import time

import params as p
import rwfiles as rw


special_parnames = set([ "Batch", "Read", "file" ])
nosl_parnames = set([ "Read", "file" ])
must_parnames = [ "file" ]
zip_extensions = set([ ".gz" ])

global input_path   # absolute path for input file
global parnames     # [ parname ] -- like Phenotype, CellType, ...
global filelist     # [ map : parname --> parvalue ]
global unique_samplenames   # [ sample-name ]
global unique_filenames     # [ file-name ]
global is_paired_end        # either "T", or "F", or empty string
global primary_ext          # like ".fastq", ".CEL", ...
global secondary_ext        # either ".gz" or empty string

# Parsers and related {{{
def loadTxt(input_path): #{{{
    def getSplitPos(line):
        split_pos = []
        state = 1   # 0: waiting for space;  1: waiting for non-space
        for (i,c) in enumerate(line):
            if state==0:
                if c==' ':
                    state = 1
            else: #state==1
                if c!=' ':
                    split_pos.append(i)
                    state = 0
        sp2 = split_pos + [2**32-1]
        return [ (sp2[_i],sp2[_i+1]) for _i in range(len(split_pos)) ]
    def splitByPos(line, split_pos_pairs):
        return map(str.strip, [ line[_l:_r] for (_l,_r) in split_pos_pairs ])
        
    lines = rw.loadLines(input_path, stripws=False)
    rows = []
    state = 0
    for line in lines:
        pure_line = line.partition('#')[0].rstrip()
        if pure_line!="":
            if state==0:
                # Found header line
                split_pos_pairs = getSplitPos(pure_line)
                parnames = splitByPos(pure_line, split_pos_pairs)
                state = 1
            else: #state==1
                words = splitByPos(pure_line, split_pos_pairs)
                rows.append( dict([ (parnames[_i],words[_i]) for _i in range(len(parnames)) ]) )
    return (rows,parnames)
#}}}
def checkAndFillOmissions(): # Fill omissions in 'filelist' {{{
    def checkParValue(parname, parvalue):
        if ' ' in parvalue:
            p.vprint(0, 'ERROR: value in column "%s" constains spaces: "%s"' % (parname, parvalue))
            exit()
    
    rw.checkColnames(must_parnames, parnames, input_path)
    
    for parname in parnames:
        if ' ' in parname:
            p.vprint(0, 'ERROR: spaces in parameter name: "%s"' % parname)
            exit()
    if len(filelist)==0:
        p.vprint(0, "ERROR: no file is described in input.")
        exit()
    
    refrow = filelist[0]
    for parname in parnames:
        parvalue = refrow.get(parname,"").strip()
        checkParValue(parname,parvalue)
        if parvalue=="":
            p.vprint(0, "ERROR: no value for parameter %s in row 1 of input." % parname)
            exit()
        refrow[parname] = parvalue
    for row in filelist[1:]:
        for parname in parnames:
            parvalue = row.get(parname,"").strip()
            if parvalue=="":  parvalue = refrow[parname]
            checkParValue(parname,parvalue)
            row[parname] = parvalue
        refrow = row
    
    global is_paired_end
    is_paired_end = ""
    if "Read" in parnames:
        reads = set([ _r["Read"] for _r in filelist ])
        if not (reads==set(["R1"]) or reads==set(["R1","R2"])):
            p.vprint(0, "ERROR: 'Read' must be 'R1' or 'R2' (found: %s)" % ", ".join(reads))
            exit()
        is_paired_end = "F" if reads==set(["R1"]) else "T"
#}}}
def getExtensions(): #{{{
    global primary_ext, secondary_ext
    priexts = set()
    secexts = set()
    for row in filelist:
        (base,ext) = os.path.splitext(row["file"])
        if ext in zip_extensions:
            secexts.add(ext)
            (_,ext) = os.path.splitext(base)
        else:
            secexts.add("")
        priexts.add(ext)
    if len(priexts) > 1:
        p.vprint(0, "ERROR: multiple primary extensions found: '%s'" % "', '".join(priexts))
        exit()
    primary_ext = min(priexts)
    if len(secexts) > 1:
        p.vprint(0, "ERROR: multiple secondary extensions found: '%s'" % "', '".join(secexts))
        exit()
    secondary_ext = min(secexts)
#}}}
def addBasenames(): #{{{
    global unique_samplenames, unique_filenames
    unique_samplenames = []
    unique_filenames = []
    base_parnames = [ _p for _p in parnames if _p not in special_parnames ]
    file_parnames = base_parnames + (["Read"] if "Read" in parnames else [])
    for row in filelist:
        samplename = '_'.join([ row[_p] for _p in base_parnames ])
        filename = '_'.join([ row[_p] for _p in file_parnames ])
        row["SampleName"] = samplename
        row["Basefilename"] = filename
        row["Affyfilename"] = samplename + primary_ext + secondary_ext
        if samplename not in unique_samplenames:  unique_samplenames.append(samplename)
        if filename not in unique_filenames:  unique_filenames.append(filename)
#}}}
#}}}

def write_FL_SH(): #{{{
    needs_concat = "F"
    bfn_to_fns = []
    for bfn in unique_filenames:
        flist = [ _r["file"] for _r in filelist if _r["Basefilename"]==bfn ]
        if len(flist)>1:  needs_concat = "T"
        first_prefix = '    [%s]="' % bfn
        next_prefix = ' ' * len(first_prefix)
        bfn_lines = []
        curr_bfn_line = first_prefix
        for fl in flist:
            curr_bfn_line += "%s " % fl
            if len(curr_bfn_line)>=100:
                curr_bfn_line += "\\"
                bfn_lines.append(curr_bfn_line)
                curr_bfn_line = next_prefix
        if curr_bfn_line.strip()=="":
            curr_bfn_line = bfn_lines.pop()[:-1]
        curr_bfn_line = curr_bfn_line[:-1] + '"'
        bfn_lines.append(curr_bfn_line)
        bfn_to_fns.extend(bfn_lines)
    
    out_lines = ("""\
################################################################
##  Automatically generated by makefilelist.py on %s  ##
##------------------------------------------------------------##
##  This file should be sourced by other scripts.             ##
################################################################

NEEDS_CONCATENATION="%s"
IS_PAIRED_END="%s"
PRIMARY_EXT="%s"
SECONDARY_EXT="%s"
NR_SAMPLES="%d"
NR_FILES="%d"
NR_SOURCE_FILES="%d"

SAMPLENAMES="\\
%s"

BASE_FILENAMES="\\
%s"

declare -A BFN_TO_FNS=(
%s
)

# Convert base-filename to a list of original filenames.
# Usage:  getOrigFiles  base-filename
# Result: prints to stdout space-separated list of filenames
getOrigFiles () {
    echo "${BFN_TO_FNS[$1]}"
}
""" % (time.strftime("%Y-%m-%d"),
       needs_concat,
       is_paired_end,
       primary_ext,
       secondary_ext,
       len(unique_samplenames),
       len(unique_filenames),
       len(filelist),
       " \\\n".join(unique_samplenames),
       " \\\n".join(unique_filenames),
       "\n".join(bfn_to_fns)) ).split('\n')
    
    rw.saveLines(os.path.join(p.projdir,"scripts","g_filelist.sh"), out_lines)
#}}}

def write_SD(): #{{{
    sl_parnames = ["SampleName"] + [ _p for _p in parnames if _p not in nosl_parnames ]
    sl_rows = []
    for row in filelist:
        sl_row = dict([ (_p,row[_p]) for _p in sl_parnames ])
        if sl_row not in sl_rows:  sl_rows.append(sl_row)
    rw.saveCSV(os.path.join(p.projdir,"processedData","SampleDescription.csv"),sl_rows,sl_parnames)
#}}}

def write_AffySD(): #{{{
    affy_parnames = [ _p for _p in parnames if _p not in nosl_parnames ]
    affy_parnames1 = [""] + affy_parnames
    affy_parnames2 = ["Affyfilename"] + affy_parnames
    ncols = len(affy_parnames1)
    colwidths = []
    for cn in affy_parnames2:
        cw = max( len(cn), max( [ len(_r[cn]) for _r in filelist ] ) )
        colwidths.append( cw )
    lines = [ "  ".join([ "%-*s" % (colwidths[_i],affy_parnames1[_i]) for _i in range(ncols) ]) ]
    for row in filelist:
        lines.append(
            "  ".join([ "%-*s" % (colwidths[_i],row[affy_parnames2[_i]]) for _i in range(ncols) ]) )
    rw.saveLines(os.path.join(p.projdir,"processedData","AffySampleDescription.csv"), lines)
#}}}

def printUsage(): #{{{
    p.vprint(0, """\
Usage:
        scripts/xvpy [-v] makefilelist.py  desciption-file  out-format [out-format...]
Description-file should be a simple file name and be located in 'scripts/' directory.
It must have one of the following extensions:
    txt -- space-separated, with left-justified columns
    csv -- tab-separated
    xls -- Excel spreadsheet (must have file description in the first worksheet)
Currently supported output formats:
    sd      -- processedData/SampleDescription.csv
    affy    -- processedData/Affy_SampleDescription.txt -- for simpleaffy::read.affy(...)
Fiel scripts/filelist.sh is always generated.
""")
#}}}

# This definitions MUST be after definitions of methods
intype_to_parser = dict([ (".txt", loadTxt),
                          (".csv", rw.loadCSV),
                          (".xls", rw.loadExcel), (".xlsx", rw.loadExcel) ])
outfmt_to_writer = dict([ ("sd", write_SD),
                          ("affy", write_AffySD) ])
def main(): #{{{
    global input_path, parnames, filelist
    p.vprint(0, "=== Parsing description of input files")
    if len(sys.argv)<3:
        printUsage()
        exit()
    
    input_fn = sys.argv[1]
    _, input_type = os.path.splitext(input_fn)
    out_formats = sys.argv[2:]
    
    p.vprint(1, "Execution parameters:")
    p.vprint(1, "    Input file:        %s" % input_fn)
    p.vprint(1, "    Output formats:    %s" % ", ".join(out_formats))
    
    if input_type not in intype_to_parser:
        p.vprint(0, "ERROR: unknown input file format: %s" % input_type)
        printUsage()
        exit()
    
    for out_format in out_formats:
        if not out_format in outfmt_to_writer:
            p.vprint(0, "ERROR: invalid output format: %s" % out_format)
            printUsage()
            exit()
    
    input_path = os.path.join(p.projdir, "scripts", input_fn)
    
    if not os.path.isfile(input_path):
        p.vprint(0, "ERROR: input file does not exist: %s" % input_path)
        printUsage()
        exit()
    
    # Parse
    (filelist,parnames) = intype_to_parser[input_type](input_path)
    checkAndFillOmissions()
    getExtensions()
    addBasenames()
    
    # Print loaded filelist
    p.vprint(2, "Using file list:")
    if p.vlevel >= 2:
        rw.printTable(filelist, parnames)
    
    # Save scripts/filelist.sh
    write_FL_SH()
    
    # Save required output
    for out_format in out_formats:
        outfmt_to_writer[out_format]()
    
    p.vprint(0, "--- Parsing completed.")
#}}}

# Start-up code ================================================={{{
if __name__=="__main__":
    main()
#................................................................}}}
