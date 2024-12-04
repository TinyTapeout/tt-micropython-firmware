import sys
import os
from ttboard.project_mux import DesignIndex
BinFileSuffix = 'bin'

def main():
    if len(sys.argv) < 2:
        print("MUST pass SHUTTLE.JSON argument")
        return False
    fname = sys.argv[1]
    if not os.path.exists(fname):
        print(f'Cannot find {fname}?')
        return False
    
    basename = os.path.basename(fname)
    destdir = os.path.dirname(fname)
    dest_file = os.path.join(destdir, f'{basename}.{BinFileSuffix}')
    
    d = DesignIndex(None, fname)
    d.to_bin_file(dest_file)
    
    if os.path.exists(dest_file):
        print(f'Wrote out {dest_file}')
        return True
        
    print(f'Cannot find resulting file {dest_file}?')
    return False

if __name__ == '__main__':
    if not main():
        print("Prawblemz")
#from ttboard.project_mux import *
#d = DesignIndex(None, 'ho.json')
