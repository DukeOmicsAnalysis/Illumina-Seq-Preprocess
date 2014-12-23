#   -*- coding: utf-8 -*-

"""\
Some parameters, both taken from environment and defined here.
"""

import sys
import os
import itertools

# projdir will be None if environment variable is not set
projdir = os.getenv('PROJDIR')

global vlevel
try:
    vlevel = int( os.getenv('VERBOSITY_LEVEL','0') )
except:
    vlevel = 0
global vlstack
try: vlstack
except NameError: vlstack = []

def changeVL(newvl): #{{{
    global vlevel
    vlstack.append(vlevel)
    vlevel = max(newvl,0)
#}}}
def restoreVL(): #{{{
    global vlevel
    if len(vlstack)>0: vlevel = vlstack.pop()
#}}}
def resetVL(): #{{{
    while len(vlstack)>0: restoreVL()
#}}}

def vprint(level, string): # Print depending on vlevel {{{
    """Print string if vlevel>=level."""
    if vlevel>=level: print string
#}}}


def printDict(level, d, fieldnames=None): #{{{
    """Print dictionary, one field per line.
    Fieldnames, if given, specifies what fields to print and in what order.
    """
    if fieldnames is None:  fieldnames = d.keys()
    maxwidth = max( [ len(x) for x in fieldnames ] )
    for fn in fieldnames:
        vprint(level, "%*s : %s" % (maxwidth, fn, d[fn]))
#}}}

def printLists(level,patt,tofl): #{{{
    """Print multiple lists in parallel.
    Example:
        printLists(1, "  First=%-*s  :  second=%s", (['a','bbb','cc'],['x','y','z']))
    will print:
    >>>>    First=a    :  second=x
    >>>>    First=bbb  :  second=y
    >>>>    First=cc   :  second=z
    The 'tofl' argument is a tuple of lists of equal length.
    """
    widths = [ max([len(str(_n)) for _n in _l]) for _l in tofl ]
    for t in itertools.izip(*tofl):
        subst = []
        for i in range(len(t)-1):
            subst.append(widths[i]);  subst.append(t[i])
        subst.append(t[-1])
        vprint(level, patt % tuple(subst) )
#}}}

def printTuples(level,patt,loft): #{{{
    """Print multiple lists in parallel.
    Example:
        printTuples(1, "  First=%-*s  :  second=%s", [('a','x'),('bbb','y'),('cc','z')])
    will print:
    >>>>    First=a    :  second=x
    >>>>    First=bbb  :  second=y
    >>>>    First=cc   :  second=z
    The 'loft' argument is a a list of tuples.
    """
    if len(loft)==0: return
    printLists(level,patt, tuple([ [ x[i] for x in loft ] for i in range(len(loft[0])) ]))
#}}}

def printList(level,patt,lst): # printList("Found %d bad",['a']) {{{
    """Print 1 or 2 values from a long list.
    Example 1:
        printList(1, "Found %d bad values", ['a'])
    will print:
        Found 1 bad values: a
    Example 2:
        printList(1, "Found %d bad values", ['a','bb'])
    will print:
        Found 2 bad values: a, bb
    Example 3:
        printList(1, "Found %d bad values", ['a','bb','ccc'])
    will print:
        Found 3 bad values: a, bb, ...
          Full list:
            a
            bb
            ccc
    First line is printed with 'vlevel', other lines (if any) are printed with 'vlevel+1;
    """
    s = (patt % len(lst)) + ": "
    if len(lst)==0:
        return
    elif len(lst)==1:
        vprint(level, s + ("%s" % str(lst[0])))
        return
    elif len(lst)==2:
        vprint(level, s + ("%s, %s" % (str(lst[0]),str(lst[1]))))
        return
    else:
        vprint(level, s + ("%s, %s, ..." % (str(lst[0]),str(lst[1]))))
        vprint(level+1, "  Full list:")
        for v in lst:
            vprint(level+1, "    %s" % v)
#}}}
