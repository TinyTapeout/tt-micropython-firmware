'''
Created on Jan 6, 2024

The TinyTapeout Demo Board PCB RPi SDK

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import os 

VERSION='0.0.0'
REVISION='n/a'

try:
    with open('/VERSION') as f:
        for ln in f.readlines():
            if ln.startswith('version='):
                VERSION=ln.replace('version=', '').replace('\n', '')
            elif ln.startswith('revision='):
                REVISION=ln.replace('revision=', '').replace('\n', '')
except:
    relfiles = list(
             map(lambda v: v.replace('release_v', ''), 
                filter(lambda f: f.startswith('release_v'), os.listdir('/'))) )
    if len(relfiles):
        VERSION = relfiles[0]
