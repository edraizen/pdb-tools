#!/usr/bin/env python

"""
Extracts a portion of the PDB file, from residue i (to residue j).
Slices are inclusive.

usage: python pdb_rslice.py <i>:<j> <pdb file>
examples: python pdb_rslice.py 1:10 1CTF.pdb # Extracts residues 1 to 10
          python pdb_rslice.py 1: 1CTF.pdb # Extracts residues 1 to END
          python pdb_rslice.py :5 1CTF.pdb # Extracts residues from START to 5.
          python pdb_rslice.py :5  10: 1CTF.pdb # Extracts residues from START to 5 10 to END

Author: {0} ({1})

This program is part of the PDB tools distributed with HADDOCK
or with the HADDOCK tutorial. The utilities in this package
can be used to quickly manipulate PDB files, with the benefit
of 'piping' several different commands. This is a rewrite of old
FORTRAN77 code that was taking too much effort to compile. RIP.
"""

import os
import re
import sys

__author__ = "Joao Rodrigues"
__email__ = "j.p.g.l.m.rodrigues@gmail.com"

USAGE = __doc__.format(__author__, __email__)

SEQUENTIAL = False

def check_input(args):
    """
    Checks whether to read from stdin/file and validates user input/options.
    """
    if not len(args):
        sys.stderr.write(USAGE)
        sys.exit(1)
    elif len(args) >= 1:
        if not sys.stdin.isatty() and not os.path.isfile(args[-1]):
            # Options & Pipe
            pdbfh = sys.stdin
            end = len(args)
        elif os.path.isfile(args[-1]):
            # Options & File
            pdbfh = open(args[-1], 'r')
            end = -1
        else:
            sys.stderr.write('File not found: ' + args[-1] + '\n')
            sys.stderr.write(USAGE)
            sys.exit(1)

        rslice = args[:end]
    else:
        sys.stderr.write(USAGE)
        sys.exit(1)

    # Parse st and end of slices
    _rslices = []
    for _rslice in rslice:
        match = re.match('[\-0-9]*:[\-0-9]*', _rslice)
        bits = [b for b in _rslice.split(':') if b.strip()]
        if match and len(bits) == 2:
            st_slice, en_slice = map(int, bits)
        elif match and len(bits) == 1 and _rslice[0] == ':':
            st_slice = -9999
            en_slice = int(bits[0])
        elif match and len(bits) == 1 and _rslice[-1] == ':':
            st_slice = int(bits[0])
            en_slice = 999999
        else:
            sys.stderr.write('Invalid slice: ' + _rslice + '\n')
            sys.stderr.write(USAGE)
            sys.exit(1)

        print
        if st_slice > en_slice:
            #Assume PDBs are numbered strangeley
            global SEQUENTIAL
            SEQUENTIAL = True

        _rslices.append((st_slice, en_slice))

    return (_rslices, pdbfh)


def _slice_pdb(fhandle, rslice):
    """Enclosing logic in a function to speed up a bit"""

    if not SEQUENTIAL:
        for line in fhandle:
            if line.startswith(('ATOM', 'HETATM', 'TER')):
                if any((st <= int(line[22:26]) <= en for st, en in rslice)):
                    yield line
            else:
                yield line
    else:
        print >> sys.stderr, "HERE"
        status = [False]*len(rslice)
        for line in fhandle:
            if line.startswith(('ATOM', 'HETATM', 'TER')):
                res = int(line[22:26])
                for i, (st, en) in enumerate(rslice):
                    if res == st:
                        yield line
                        status[i] = True
                        break
                    elif res == en:
                        yield line
                        status[i] = False
                        break
                else:
                    for i in xrange(len(rslice)):
                        if status[i]:
                            yield line
                            break


if __name__ == '__main__':

    # Check Input
    rslice, pdbfh = check_input(sys.argv[1:])

    # Do the job
    new_pdb = _slice_pdb(pdbfh, rslice)

    try:
        sys.stdout.write(''.join(new_pdb))
        sys.stdout.flush()
    except IOError:
        # This is here to catch Broken Pipes
        # for example to use 'head' or 'tail' without
        # the error message showing up
        pass

    # last line of the script
    # We can close it even if it is sys.stdin
    pdbfh.close()
    sys.exit(0)
