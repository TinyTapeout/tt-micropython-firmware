'''
Created on Aug 5, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''


class ShuttleProperties:
    def __init__(self, shuttle:str='n/a', repo:str='n/a', commit:str='n/a'):
        self._shuttle = shuttle 
        self._repo = repo 
        self._commit = commit
        
    
    @property
    def shuttle(self):
        return self._shuttle
    
    @property 
    def repo(self):
        return self._repo
    
    @property 
    def commit(self):
        return self._commit


class HardcodedShuttle(ShuttleProperties):
    
    def __init__(self, shuttle:str, repo:str='', commit:str=''):
        super().__init__(shuttle, repo, commit)

