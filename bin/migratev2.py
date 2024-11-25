#!/usr/bin/env python
'''
    TT SDK v2.0 migration script
    @copyright: (C) 2024 Pat Deegan, https://psychogenic.com
    
    Tries to do lots of the grunt work of migrating code to the new
    cocotb-like SDK.
    
    Use --help to see:
    usage: migratev2.py [-h] [--outdir OUTDIR] [--overwrite] infile [infile ...]
    
    SDK v2 migration tool
    
    positional arguments:
      infile           files to migrate
    
    options:
      -h, --help       show this help message and exit
      --outdir OUTDIR  Destination directory for migrated file(s)
      --overwrite      Allow overwriting files when outputting
      
      
    Sample use cases
    
    1) Look at a single file
    ./migratev2.py path/to/file.py
    
    2) Write out files
    Specify a directory in which to dump the contents using --outdir
    ./migratev2 --outdir /tmp/new path/to/*.py path/to/more/*.py
    
    All files will endup under /tmp/new/path/to/... in exact 
    reflection of relative path used, to any depth.

'''
import re 
import argparse
import os
import sys

substitutions = [
    
    ('\.input_byte\s*=', '.ui_in.value ='),
    ('(return\s+|=)\s*([\w\.]+)\.input_byte', '\g<1> \g<2>.ui_in.value'),
    ('\.input_byte', '.ui_in.value'),
    ('(return\s+|=)\s*([^\s]+)\.output_byte', '\g<1> \g<2>.uo_out.value'),
    ('\.output_byte', '.uo_out.value'),
    # order matters
    ('\.bidir_byte\s*=', '.uio_in.value ='),
    ('(return\s+|=)\s*([^\s]+)\.bidir_byte', '\g<1> \g<2>.uio_out.value'),
    ('([^\s]+)\.bidir_byte', '\g<1>.uio_out.value'),
    ('\.bidir_mode', '.uio_oe[:]'), #
    ('\.project_nrst', '.rst_n'),
    ('\.project_clk([^_]+)', '.clk\g<1>')
]



special_cases = [
    ('individual_pin_attrib', '\.(in|out|uio)(\d+)'), 
    ('individual_pin_write', '\.(in|out|uio)(\d+)\(([^)]+)\)'),
    ('individual_pin_read', '\.(in|out|uio)(\d+)\((\s*)\)'),
    
]

class Replacer:
    def __init__(self):
        self.substitutions = []
        for v in substitutions:
            self.substitutions.append( [re.compile(v[0]), v[1]])
            
        #self.special_cases = []
        for sc in special_cases:
            #spec = [re.compile(sc[1]), sc[2]]
            #self.special_cases.append(spec)
            setattr(self, sc[0], re.compile(sc[1], re.MULTILINE))
            
    def read(self, fpath:str):
        with open(fpath, 'r') as f:
            return ''.join(f.readlines())
        
    def basic_substitutions(self, contents:str):
        for s in self.substitutions:
            contents = s[0].sub(s[1], contents)
        
        return contents
    
    def special_substitutions(self, contents:str):
        
        set_bitmap = {
            'in': 'ui_in',
            'out': 'uo_out',
            'uio': 'uio_in',
            }
            
        read_bitmat = {
            'in': 'ui_in',
            'out': 'uo_out',
            'uio': 'uio_out',
        
        }
        
        seen = dict()
        
        for p in self.individual_pin_write.findall(contents):
            subre = f'\.{p[0]}{p[1]}\({p[2]}\)'
            repl =  f'.{set_bitmap[p[0]]}[{p[1]}] = {p[2]}'
            print(f"'{subre}', '{repl}'")
            contents = re.sub(subre, repl, contents, 0, re.MULTILINE)
            
        for p in self.individual_pin_read.findall(contents):
            subre = f'\.{p[0]}{p[1]}\({p[2]}\)'
            repl =  f'.{read_bitmap[p[0]]}[{p[1]}]'
            print(f"'{subre}', '{repl}'")
            contents = re.sub(subre, repl, contents, 0, re.MULTILINE)
            
        for p in self.individual_pin_attrib.findall(contents):
            subre = f'\.{p[0]}{p[1]}'
            repl =  f'.pins.{set_bitmap[p[0]]}{p[1]}'
            print(f"PINATTR '{subre}', '{repl}'")
            contents = re.sub(subre, repl, contents, 0, re.MULTILINE)
            
            
            
        
        return contents
    
    def migrate(self, contents:str):
        contents = self.basic_substitutions(contents)
        contents = self.special_substitutions(contents)
        return contents
    
    def migrate_file(self, fpath:str):
        c = self.read(fpath)
        return self.migrate(c)

#
#f = r.read('src/examples/tt_um_psychogenic_neptuneproportional/tt_um_psychogenic_neptuneproportional.py')
def getArgsParser():
    parser = argparse.ArgumentParser(description='SDK v2 migration tool')
    
    parser.add_argument('--outdir', required=False, 
                            type=str, 
                            help="Destination directory for migrated file(s)")
    parser.add_argument('--overwrite', required=False, 
                            action='store_true',
                            help="Allow overwriting files when outputting")
    parser.add_argument('infile', nargs='+', help='files to migrate')
    return parser


def mkdir_if_needed(dirpath:str):
    if not os.path.exists(dirpath):
        print(f'Creating directory: {dirpath}')
        os.makedirs(dirpath)
        
def main():
    
    parser = getArgsParser()
    args = parser.parse_args()
    
    
    if not args.outdir:
        if len(args.infile) != 1:
            print("You MUST specify --outdir if more than one file is to be migrated")
            return
    
    rep = Replacer()
    for infile in args.infile:
        if not os.path.exists(infile):
            print(f"Can't find '{infile}'")
            continue
        print(f"Processing '{infile}'", file=sys.stderr)
        contents = rep.migrate_file(infile)
        if not args.outdir:
            print(contents)
        else:
            destpathdir = os.path.join(args.outdir, os.path.dirname(infile))
            mkdir_if_needed(destpathdir)
            fpath = os.path.join(destpathdir, os.path.basename(infile))
            if os.path.exists(fpath) and not args.overwrite:
                print(f"{fpath} exists and NO --overwrite, skip", file=sys.stderr)
            else:
                print(f"Writing {fpath}", file=sys.stderr)
                with open(fpath, 'w') as f:
                    f.write(contents)

main()
