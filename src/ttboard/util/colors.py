'''
Created on Aug 5, 2024

@author: Uri Shaked
'''
Enable = True 
COLORS = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]

def bold(s):
    if Enable:
        return f"\033[1m{s}\033[0m"
    return s 

def underline(s):
    if Enable:
        return f"\033[4m{s}\033[0m"
    return s

def inverse(s):
    if Enable:
        return f"\033[7m{s}\033[0m"

def color(s, color, bright = True):
    if not Enable:
        return s 
    
    code= str(COLORS.index(color))
    suffix = ";1" if bright else ""
    return f"\033[3{code}{suffix}m{s}\033[0m"