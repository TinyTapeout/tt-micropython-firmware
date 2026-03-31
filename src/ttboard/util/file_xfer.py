'''
Created on Feb 10, 2026

@author: Pat Deegan
@copyright: Copyright (C) 2026 Pat Deegan, https://psychogenic.com
'''
import binascii 
import os
import hashlib

class FileWriter:
    def __init__(self, fpath:str=None, calculate_hash:bool=True, verbose:bool=False):
        self._fh = None 
        self._filepath = None
        self.verbose = verbose
        self.calculate_hash = calculate_hash
        self._hasher = None
        self.digest_value = None
        if fpath is not None:
            self.open(fpath)
    
    
    def open(self, fpath:str):
        self.close()
        
        if not fpath.startswith('/'):
            if self.verbose:
                print("WARN: relative path, adding '/'")
            fpath = f'/{fpath}'
        self._filepath = fpath
        
        # parent dirs ... no os.path here, ugh
        components = fpath.split('/')
        num_components = len(components)
        if num_components > 2:
            # started with / then something, not just filename
            for i in range(2, num_components):
                parent_dir = '/'.join(components[:i])
                try:
                    os.stat(parent_dir)
                except:
                    # DNE!
                    if self.verbose:
                        print(f"DEBUG: creating {parent_dir}")
                    os.mkdir(parent_dir)
            
        if self.verbose:
            print(f'INFO: open {fpath} for write')
        self._fh = open(fpath, 'wb')
        
        if self.calculate_hash:
            self.digest_value = None
            self._hasher = hashlib.sha256()
        
    def w(self, b64chunk:str):
        bin_chunk = binascii.a2b_base64(b64chunk)
            
        self._fh.write(bin_chunk)
        
        if self.calculate_hash:
            self._hasher.update(bin_chunk)
        
    def write_base64(self, b64chunk):
        return self.w(b64chunk)
    
    def close(self):
        if self._fh is not None:
            if self.verbose:
                print(f"INFO: closing {self._filepath}")
                if self.calculate_hash:
                    print(f'INFO: digest {self.digest}')
            self._fh.close()
            self._fh = None
            
    @property 
    def digest(self):
        if self.digest_value is None:
            if self.calculate_hash and self._hasher:
                self.digest_value = self._hasher.digest().hex()
        
        return self.digest_value
                
