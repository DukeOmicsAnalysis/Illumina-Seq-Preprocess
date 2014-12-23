#   -*- coding: utf-8 -*-

"""\
This module provides simple utilities to read/write Excel, CSV, and line files.

The path to a file may be given in tree ways:
    /path/to/file       -- absolute path
    path/to/file        -- relative to project directory
    ./path/to/file      -- relative to the current directory
"""

import os
import os.path
from collections import namedtuple

import xlrd
import xlwt
import csv

import params as p

def checkColnames(expected_colnames,real_colnames,filename): # {{{
    """Check colnames:
    1) Do real_colnames list contains duplicates?
    2) Is expected_colnames subset of real_colnames?
    Returns True if lists are OK, False otherwise; print warning message if something is wrong.
    'expected_colnames' and 'real_colnames' are lists of strings; 'expected_colnames can be None.
    Argument filename is used only for error message.
    """
    is_ok = True
    expected_colnames_set = set() if expected_colnames is None else set(expected_colnames)
    real_colnames_set = set(real_colnames)
    # Check duplicates
    if len(real_colnames_set) < len(real_colnames):
        p.vprint(0, "WARNING: Repeated column names (file %s):" % filename)
        for rc in real_colnames_set:
            if real_colnames.count(rc) > 1:  p.vprint(0, "    %s" % rc)
        is_ok = False
    if not expected_colnames_set <= real_colnames_set:
        p.vprint(0, "WARNING: Required column names are absent (file %s):" % filename)
        for ec in expected_colnames_set-real_colnames_set:
            p.vprint(0, "    %s" % ec)
        is_ok = False
    return is_ok
#}}}
def printTable(rows,colnames=None,maxwidth=50): #{{{
    if colnames is None:
        cnset = set()
        for row in rows: cnset |= set(row.keys())
        colnames = list(cnset)
    ncols = len(colnames)
    srows = stringify(rows)
    colwidths = []
    for cn in colnames:
        cw = max( len(cn), max( [ len(_r[cn]) for _r in srows ] ) )
        if cw>maxwidth: cw=maxwidth
        colwidths.append( cw )
    print "  ".join( [ "%*s" % (colwidths[i],colnames[i][:maxwidth]) for i in range(ncols) ] )
    for row in srows:
        print "  ".join( [ "%*s" % (colwidths[i],row[colnames[i]][:maxwidth]) for i in range(ncols) ] )
#}}}

def addRowNumbers(rows, colname): #{{{
    """Add row number to each row, starting from 0.
    'rows' is a list of dictionaries.
    'colname' is a string.
    This function adds mapping (colname --> row number) to each row.
    Original dictionaries are updated.
    For convenience, updated 'rows' is returned as result.
    """
    for i in range(len(rows)):
        rows[i][colname] = i
    return rows
#}}}

def stringify(rows): #{{{
    """All-digit values are considered as floats in Excel, even if they are intended to be strings
    (but not made strings by adding ').
    Moreover, Excel does not distinguish integers and floats.
    This function converts everything to strings; float values equal to integers
    are first converted to integers.
    """
    import numbers
    rrows = []
    for row in rows:
        rrow = dict()
        for (k,v) in row.iteritems():
            if isinstance(v, numbers.Number):
                if int(v)==float(v):
                    v = int(v)
                v = str(v)
            v = v.strip()
            rrow[k] = unicode(v)
        rrows.append(rrow)
    return rrows
#}}}

def resolvePath(path): # Converts path to absolute {{{
    """Argument may have one of tree forms:
    /path/to/file       -- absolute path
    path/to/file        -- relative to project directory
    ./path/to/file      -- relative to the current directory
    """
    if path.startswith("./"):
        return os.path.abspath( os.path.join(os.getcwd(),path) )
    else:
        return os.path.abspath( os.path.join(p.projdir,path) )
#}}}

def makePath(path): #{{{
    """Like 'os.makedirs', but:
    (a) does not raise error when path exists
    (b) if path is relative, it is relative to p.projdir.
    Returns the created absolute path.
    """
    apath = resolvePath(path)
    if not os.path.isdir(apath):
        os.makedirs(apath)
    return apath
#}}}

def loadExcel(filename, colnames=None, expected_colnames=None, skip_first=0, worksheet=0): #{{{
    """Read sheet(s) from Excel workbook.
    'filename'  "/path/to/file"     -- absolute,
                "path/to/file"      -- relative to p.projdir,
                "./path/to/file"    -- relative to the current directory
    'colnames' is a list of strings; if present, it is expected that table does not contain
               header row, and exactly len(colnames) columns will be read from each row.
    'expected_colnames' is a list of strings -- names of columns that MUST be present;
                        if table does not have a column from this list, a warning is printed.
    'skip_first' gives a number of rows to be skipped before reading data.
    'worksheet' is either an integer -- worksheet index, or a string -- worksheet name.
                Also, it can be a list of such object -- multiple worksheets will be read.
                If is None, worksheet names are returned.
    
    Result: either (list of rows, list of colnames), or [ (list of rows, list of colnames), ... ],
            or [ worksheet_name ] -- depending on the type of 'worksheet' argument.
    Each row in the list of rows is a map(colname --> value).
    
    The numbers of rows and columns in a worksheet are determined by 'nrows' and 'ncols' properties
    of xlrd.Sheet object.
    
    If colnames is None, ther first (after skipping 'skip_first' rows) row is expected
    to contain column names. If there are repeated colnames, a warning is printed.
    """
    fn = resolvePath(filename)
    p.vprint(1, "Loading workbook %s..." % fn)
    wb = xlrd.open_workbook(fn)
    if worksheet is None:
        return wb.sheet_names()
    elif isinstance(worksheet, (list, tuple, set, frozenset)):
        worksheets = list(worksheet)
    else:
        worksheets = [ worksheet ]
    results = []
    for ws_name in worksheets:
        p.vprint(1, "  Reading worksheet %s..." % ws_name)
        if ws_name in range(wb.nsheets):
            ws = wb.sheet_by_index(ws_name)
        elif str(ws_name) in wb.sheet_names():
            ws = wb.sheet_by_name(str(ws_name))
        else:
            p.vprint(0, "WARNING: worksheet %s is not found." % ws_name)
            ws = None
        if ws is not None:
            #p.vprint(1, "Worksheet %s: %d rows, %d columns" % (ws_name,ws.nrows,ws.ncols))
            first_row = skip_first
            if colnames is not None:
                ws_colnames = colnames[:ws.ncols]
            else:
                # Read colnames from the first row
                ws_colnames = [ ws.cell_value(skip_first,i) for i in range(ws.ncols) ]
                first_row += 1
            #p.vprint(1, "Colnames: %s" % ws_colnames)
            checkColnames(expected_colnames, ws_colnames, fn)
            table_data = []
            for i in range(first_row, ws.nrows):
                row = dict()
                for j in range(len(ws_colnames)):
                    row[ws_colnames[j]] = ws.cell_value(i,j)
                table_data.append(row)
            p.vprint(1, "  Done, %d columns and %d rows." % (len(ws_colnames), len(table_data)))
            results.append( (table_data, ws_colnames) )
            
    p.vprint(1, "Done with workbook.")
    # Return either list of tables or single table depending on type of 'worksheet' argument
    if isinstance(worksheet, (list, tuple, set, frozenset)):
        return results
    else:
        return results[0]
#}}}

def saveExcel(filename, rows, colnames, #{{{
              col_align=None, col_fmts=None, col_xfs=None, col_width=None):
    """Write Excel spreadsheet.
    If 'rows' contains more than 65000 elements, it is stored in multiple worksheets.
    'filename'  "/path/to/file"     -- absolute,
                "path/to/file"      -- relative to p.projdir,
                "./path/to/file"    -- relative to the current directory
    'rows' is a list of map(colname --> value).
           If a row does not have an entry for a colname, empty cell is stored.
    'colnames' is a list of strings; only columns listed in 'colnames' are written to file
               (excessive entries in rows are ignored).
    'col_align' is useful if only alignment formatting is needed; it is ignored if either
                'col_fmts' or 'col_xfs' is not None.
                It is a list of the same length as 'colnames'; possible values:
                -1: left alignment, with 10 pt indent;
                 0: center alignment;
                 1: right alignment;
                any other value (None, for example): general alignment.
    'col_fmts' is a list (of the same length as 'colnames') of strings, which are used as
               arguments for xlwt.easyfx function.
               It is ignored if 'col_xfs' is not None.
    'col_xfs' is a list (of the same length as 'colnames') of xlwt.Style objects (produced
              by xlwt.easyfx function or created in a more sophisticated way).
    'col_width' is a list (of the same length as 'colnames') of integers, width in characters.
    """
    wb = createExcelWorkbook()
    addExcelWorksheet(wb, "Sheet", rows, colnames, col_align, col_fmts, col_xfs, col_width)
    saveExcelWorkbook(wb, filename)
#}}}

# Interface to save multi-sheet Excel tables {{{
def createExcelWorkbook(): #{{{
    return xlwt.Workbook()
#}}}

def openExcelWorkbook(filename): #{{{
    fn = resolvePath(filename)
    p.vprint(1, "Loading workbook %s..." % fn)
    wb = xlrd.open_workbook(fn)
    p.vprint(1, "Done.")
    return wb
#}}}

def addExcelWorksheet(workbook, worksheet_name, rows, colnames, #{{{
              col_align=None, col_fmts=None, col_xfs=None, col_width=None):
    """Add worksheet to Excel workbook.
    If 'rows' contains more than 65000 elements, it is stored in multiple worksheets,
    with names "worksheet_name (1)", ...
    No check whether worksheet name already exists is made.
    'workbook' is a workbook object returned by 'createExcelWorkbook', or 'openExcelWorkbook',
               or this function.
    'worksheet_name' is a string to name added worksheet(s).
    'rows' is a list of map(colname --> value).
           If a row does not have an entry for a colname, empty cell is stored.
    'colnames' is a list of strings; only columns listed in 'colnames' are written to file
               (excessive entries in rows are ignored).
    'col_align' is useful if only alignment formatting is needed; it is ignored if either
                'col_fmts' or 'col_xfs' is not None.
                It is a list of the same length as 'colnames'; possible values:
                -1: left alignment, with 10 pt indent;
                 0: center alignment;
                 1: right alignment;
                any other value (None, for example): general alignment.
    'col_fmts' is a list (of the same length as 'colnames') of strings, which are used as
               arguments for xlwt.easyfx function.
               It is ignored if 'col_xfs' is not None.
    'col_xfs' is a list (of the same length as 'colnames') of xlwt.Style objects (produced
              by xlwt.easyfx function or created in a more sophisticated way).
    'col_width' is a list (of the same length as 'colnames') of integers, width in characters.
    """
    p.vprint(1, "Adding worksheet '%s' to Excel workbook..." % worksheet_name)
    ezxf = xlwt.easyxf
    heading_xf = ezxf("""font: bold on, height 240;
                         align: wrap on, vert center, horiz center;
                         pattern: pattern solid, fore_colour ice_blue""")
    if col_xfs is None:
        col_xfs = [ezxf('')] * len(colnames)
        if col_fmts is not None:
            col_xfs = [ ezxf(fmt) for fmt in col_fmts ]
        elif col_align is not None:
            col_xfs = [ ezxf('align: horiz left, indent 1')     if align==-1 else
                        ezxf('align: horiz center')             if align==0  else
                        ezxf('align: horiz right')              if align==1  else
                        ezxf('')
                        for align in col_align ]
    nr_rows = len(rows)
    if len(rows) <= 65000:
        row_subsets = [ rows ]
        nr_sheets = 1
        sheet_names = [ worksheet_name ]
    else:
        row_subsets = []
        while len(rows)>65000:
            row_subsets.append( rows[:65000] )
            rows = rows[65000:]
        if len(rows) > 0:
            row_subsets.append(rows)
        nr_sheets = len(row_subsets)
        sheet_names = [ "%s (%d)" % (worksheet_name,i) for i in range(nr_sheets) ]
    for sh_i in range(nr_sheets):
        sheet = workbook.add_sheet(sheet_names[sh_i])
        # Create header row
        for (icol, value) in enumerate(colnames):
            sheet.write(0, icol, value, heading_xf)
        sheet.row(0).set_style(ezxf('pattern: pattern solid, fore_colour ice_blue'))
        sheet.row(0).height = 2*256
        sheet.set_panes_frozen(True) # frozen colnames instead of split panes
        sheet.set_horz_split_pos(1)
        sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
        # Create data rows
        irow =0
        for row in row_subsets[sh_i]:
            irow += 1
            for (icol, colname) in enumerate(colnames):
                sheet.write(irow, icol, row.get(colname,''), col_xfs[icol])
        # Set column width if requested
        if col_width is not None:
            for (i, width) in enumerate(col_width):
                if width>0: sheet.col(i).width = width*256
    p.vprint(1,"Done, %d columns and %d rows in %d worksheets." % (len(colnames),nr_rows,nr_sheets))
    return 
#}}}

def saveExcelWorkbook(filename, workbook): #{{{
    fn = resolvePath(filename)
    p.vprint(1, "Saving %s..." % fn)
    workbook.save(fn)
    p.vprint(1, "Done.")
#}}}
#}}}

def loadCSV(filename, colnames=None, expected_colnames=None, skip_first=0): # {{{
    """Read CSV file.
    'filename'  "/path/to/file"     -- absolute,
                "path/to/file"      -- relative to p.projdir,
                "./path/to/file"    -- relative to the current directory
    'colnames' is a list of strings; if present, it is expected that table does not contain
               header row, and exactly len(colnames) columns will be read from each row.
    'expected_colnames' is a list of strings -- names of columns that MUST be present;
                        if table does not have a column from this list, a warning is printed.
    'skip_first' gives a number of rows to be skipped before reading data.
    
    Result: (list of rows, list of colnames).
    Each row in the list of rows is a map(colname --> value).
    
    The number of rows is determined by the number of lines in the file, and the number of columns
    is either the lenght of 'colnames' or the number of fields in the first line.
    
    If colnames is None, ther first row (after skipping 'skip_first' rows) is expected
    to contain column names. If there are repeated colnames, a warning is printed.
    """
    fpath = resolvePath(filename)
    p.vprint(1,"Loading %s..." % fpath)
    with open(fpath, 'r') as f:
        # Skip first rows
        for i in range(skip_first): f.readline()
        # Create dictionary reader (fieldnames=None is required to read column names from file)
        csvrdr = csv.DictReader(f, fieldnames=colnames, dialect=csv.excel_tab)
        # Read rows
        rows = [ row for row in csvrdr ]
        colnames = csvrdr.fieldnames
    p.vprint(1,"Done, %d columns and %d rows." % (len(colnames), len(rows)))
    if checkColnames(expected_colnames,colnames,fpath):
        return (rows, colnames)
    else:
        raise Exception()
#}}}

def saveCSV(filename, rows, colnames, restval='', header=True, prefix=[]): # {{{
    """Save CSV file.
    'filename'  "/path/to/file"     -- absolute,
                "path/to/file"      -- relative to p.projdir,
                "./path/to/file"    -- relative to the current directory
    'rows' is a list of map(colname --> value).
           Each row must have entry for each colname in 'colnames'.
    'colnames' is a list of strings; only columns listed in 'colnames' are written to file
               (excessive entries in rows are ignored).
    'header' is either True (write header row) or False (do not write header row).
    'prefix' is a list of strings to be written before the line with column name.
    """
    fpath = resolvePath(filename)
    p.vprint(1, "Saving %s..." % fpath)
    with open(fpath, 'w') as f:
        # Write prefix if needed
        for line in prefix: f.write(line+'\n')
        # in version 2.6, csv has no method 'writeheader' -- we have to do it manually
        if header: f.write( '\t'.join(colnames) + '\n' )
        csvwrt = csv.DictWriter(f, fieldnames=colnames, restval=restval,
                                dialect=csv.excel_tab, extrasaction='ignore')
        csvwrt.writerows(rows)
    p.vprint(1,"Done, %d columns and %d rows." % (len(colnames), len(rows)))
#}}}


def loadLines(filename,stripws=True): # {{{
    """Load a list of lines from a file.
    'filename'  "/path/to/file"     -- absolute,
                "path/to/file"      -- relative to p.projdir,
                "./path/to/file"    -- relative to the current directory
    Trailing '\n' is removed from each line.
    If, in addition, 'stripws' is True, all whitespaces at the start and at the end of each line
    are removed.
    """
    fpath = resolvePath(filename)
    p.vprint(1, "Loading %s..." % fpath)
    with open(fpath, 'rU') as f:
        lines = [ line.strip() if stripws else line.rstrip('\n') for line in f ]
    p.vprint(1, "Done, %d lines." % len(lines))
    return lines
#}}}

def saveLines(filename, lines): # {{{
    """Save list of lines in a file.
    'filename'  "/path/to/file"     -- absolute,
                "path/to/file"      -- relative to p.projdir,
                "./path/to/file"    -- relative to the current directory
    'lines' is a list of string.
    Trailing '\n' is automatically added to each line.
    """
    fpath = resolvePath(filename)
    p.vprint(1, "Saving %s..." % fpath)
    with open(fpath, 'w') as f:
        for line in lines: f.write(line+'\n')
    p.vprint(1, "Done, %d lines." % len(lines))
#}}}

# PARSERS {{{
# Fasta {{{
# Converts lines of Fasta file into a list of tuples (header, sequence).
# The leading '>' is removed from header line.
# Default length of sequence lines in unparser == 80.
#
Fasta = namedtuple("Fasta", "header sequence")
def parseFasta(lines): # Fasta lines ==> list of Fasta tuples {{{
    """Parse contents of fasta file given by lines.
    Returns list of  namedtuple("Fasta", "header sequence")
    (header -- fasta header without '>', sequence -- sequence, lines concatenated).
    """
    p.vprint(1, "Parsing Fasta...")
    result = []
    nn = len(lines)
    i = 0
    nr_warnings = 0
    while i < nn:
        if not lines[i].startswith('>'):
            p.vprint(2, "WARNING: line %d is not a header: %s" % (i,lines[i]))
            nr_warnings +=1
            i += 1
        else:
            header = lines[i][1:]
            sequence = ""
            i += 1
            while i<nn and not lines[i].startswith('>'):
                sequence += lines[i]
                i += 1
            result.append( Fasta(header=header, sequence=sequence) )
    p.vprint(1, "Done, %d entries (%d warnings)." % (len(result),nr_warnings))
    return result
#}}}
def unparseFasta(fasta_tuples, line_length=80): # List of Fasta tuples ==> Fasta lines {{{
    p.vprint(1, "Unparsing Fasta...")
    lines = []
    for fasta in fasta_tuples:
        lines.append( '>' + fasta.header )
        for i in range(0, len(fasta.sequence), line_length):
            lines.append( fasta.sequence[i:i+line_length] )
    p.vprint(1, "Done, %d entries ==> %d lines" % (len(fasta_tuples),len(lines)))
    return lines
#}}}
#}}}

# GFF3 (limited) {{{
# Converts lines of GFF3 file to a list of "gff-genes".
# Each "gff-gene" is a list of "Gff" tuples.
# "Gff" tuple has 10 named fields, first 9 are 9 gff columns, and the 10th is ID extracted from
# the gff "attrs" column (9th column).
# "Gff-gene" always has at least 2 tuples, with types "gene" and "mRNA".
# If the source GFF file contains multiple "mRNA" lines in one "gene" section, multiple
# "gff-genes" are created (they have the same "gene" tuple).
# During unparsing, multiple subsequent "gff-genes" with the same "gene" tuple are combined.
# Indices of fields in gff line {{{
gff_seqid  = 0
gff_source = 1
gff_type   = 2
gff_start  = 3
gff_end    = 4
gff_score  = 5
gff_strand = 6
gff_phase  = 7
gff_attrs  = 8
gff_id     = 9
#}}}
Gff = namedtuple("Gff", "seqid source gfftype start end score strand phase attrs gffid")
def parseGffGenes(lines): # GFF lines ==> list of gff-genes (==list of Gff tuples) {{{
    """Parse contents of gff file given by lines.
    Works for gff files describing genes:
     -- gff file consists of bloks of lines for a gene
     -- each block starts with line with gff_type=='gene' and extends to the start of the next block
     -- if the source GFF file contains multiple "mRNA" lines in one "gene" section, multiple
        "gff-genes" are created (they have the same "gene" tuple).
     -- warns if the first line(s) is not gff_type=='gene'
    Returns list of genes, each gene is a list of gff lines, each line is a tuple of 10 strings.
    The 10th string, "id", is extracted from attributes.
    """
    p.vprint(1, "Parsing GFF...")
    genes = []
    curr_gene = []
    nr_warnings = 0
    for (i,line) in enumerate(lines):
        line1 = line.split('#',1)[0].strip()
        if len(line1) > 0:  # not pure comment
            fields = line1.split('\t')
            if len(fields)!=9:
                p.vprint(2, "WARNING: line %d has %d fields: %s" % (i,len(fields),line))
                nr_warnings += 1
            elif fields[gff_type]!="gene" and len(curr_gene)==0:
                p.vprint(2, "WARNING: line %d before the first 'gene': %s" % (i,line))
                nr_warnings += 1
            else:
                gffid = ""
                attrs = map(str.strip, fields[gff_attrs].split(';'))
                for attr in attrs:
                    if attr.startswith("ID="):
                        gffid = attr[3:]
                        break
                fields.append(gffid)
                fields_tuple = Gff(*fields)
                if fields_tuple.gfftype=="gene":
                    if len(curr_gene)==1:
                        p.vprint(0, "WARNING: orphan 'gene' line: %s" % str(fields_tuple))  
                        nr_warnings += 1
                    elif len(curr_gene)>=2:
                        genes.append(curr_gene)
                    curr_gene = [ fields_tuple ]
                elif fields_tuple.gfftype=="mRNA":
                    if len(curr_gene)>1:
                        gene_tuple = curr_gene[0]
                        genes.append(curr_gene)
                        curr_gene = [ gene_tuple ]
                    curr_gene.append(fields_tuple)
                else:
                    curr_gene.append(fields_tuple)
    if len(curr_gene)>0: genes.append(curr_gene)
    p.vprint(1, "Done, %d genes (%d warnings)." % (len(genes),nr_warnings))
    return genes
#}}}
def unparseGffGenes(gff_genes): # list of gff-genes (==list of Gff tuples) ==> GFF lines {{{
    p.vprint(1, "Unparsing GFF...")
    lines = []
    last_gene_line = None
    nr_genes = 0
    nr_warnings = 0
    for gff_gene in gff_genes:
        if len(gff_gene)==0:
            p.vprint(2, "WARNING: empty gene.")
            nr_warnings += 1
        else:
            gene_line = '\t'.join(gff_gene[0])
            if gene_line!=last_gene_line:
                if last_gene_line is not None:  lines.append("")
                lines.append(gene_line)
                last_gene_line = gene_line
                nr_genes += 1
            for gff_tuple in gff_gene[1:]:
                lines.append( '\t'.join(gff_tuple[:9]) )
    p.vprint(1, "Done, %d genes ==> %d genes, %d lines (%d warnings)"
                % (len(gff_genes), nr_genes, len(lines), nr_warnings))
    return lines
#}}}
#}}}
#}}}
