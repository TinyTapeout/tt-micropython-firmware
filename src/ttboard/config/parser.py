'''
Created on Jan 22, 2024

Minimal and functional version of CPython's ConfigParser module.

This is a module reimplemented specifically for MicroPython standard library,
with efficient and lean design in mind. Note that this module is likely work
in progress and likely supports just a subset of CPython's corresponding
module. Please help with the development if you are interested in this
module.

From unmerged PR to uPython, 
https://github.com/micropython/micropython-lib/pull/265/files
https://github.com/Mika64/micropython-lib/tree/master/configparser

@author: Michaël Ricart

Augmented by Pat Deegan, 2024-01-22, to provide auto conversions to ints/floats/bools, 
support comments, etc.

For TT shuttles, a DEFAULT section has defaults, including (optional) a project 
to load on startup.

Each following section may be defined using
[PROJECT_NAME]
and include
 * clock_frequency: Freq, in Hz, to auto-clock
 * input_byte: value to set for inputs on startup
 * bidir_direction: bits set to one are driven by RP2040
 * bidir_byte: actual value to set (only applies to outputs)
 * mode: tt mode to set
 
============= sample config ===============
# TT 3.5 shuttle init file
# comment out lines by starting with #
[DEFAULT]
# project: project to load by default
project = tt_um_test



[tt_um_test]
clock_frequency = 10

[tt_um_psychogenic_neptuneproportional]
clock_frequency = 4e3
input_byte = 0b11001000


============= /sample config ===============

'''

class ConfigParser:
    def __init__(self):
        self.convertToBools = {
            'true': True,
            'yes': True,
            'no': False,
            'false': False
        }
        self.config_dict = {}

    def sections(self):
        """Return a list of section names, excluding [DEFAULT]"""
        to_return = [section for section in self.config_dict.keys() if not section in "DEFAULT"]
        return to_return

    def add_section(self, section):
        """Create a new section in the configuration."""
        self.config_dict[section] = {}

    def has_section(self, section):
        """Indicate whether the named section is present in the configuration."""
        if section in self.config_dict.keys():
            return True
        else:
            return False
        
    def add_option(self, section, option):
        """Create a new option in the configuration."""
        if self.has_section(section) and not option in self.config_dict[section]:
            self.config_dict[section][option] = None
        else:
            raise

    def options(self, section):
        """Return a list of option names for the given section name."""
        if not section in self.config_dict:
            raise
        return self.config_dict[section].keys()

    def read(self, filename=None, fp=None):
        """Read and parse a filename or a list of filenames."""
        if not fp and not filename:
            print("ERROR : no filename and no fp")
            raise
        elif not fp and filename:
            fp = open(filename)

        content = fp.read()
        fp.close()
        self.config_dict = {line.replace('[','').replace(']',''):{} for line in content.split('\n')\
                if line.startswith('[') and line.endswith(']')
                }

        striped_content = [line.strip() for line in content.split('\n')]
        for section in self.config_dict.keys():
            start_index = striped_content.index('[%s]' % section)
            end_flag = [line for line in striped_content[start_index + 1:] if line.startswith('[')]
            if not end_flag:
                end_index = None
            else:
                end_index = striped_content.index(end_flag[0])
            block = striped_content[start_index + 1 : end_index]
            commentless_block = []
            for line in block:
                if line.startswith('#'):
                    continue 
                commentless_block.append(line)
                
            block = commentless_block
            options = [line.split('=')[0].strip() for line in block if '=' in line]
            for option in options:
                if option.startswith('#'):
                    continue
                start_flag = [line for line in block if line.startswith(option) and '=' in line]
                start_index = block.index(start_flag[0])
                end_flag = [line for line in block[start_index + 1:] if '=' in line]
                if not end_flag:
                    end_index = None
                else:
                    end_index = block.index(end_flag[0])
                values = [value.split('=',1)[-1].strip() for value in block[start_index:end_index] if value]
                if not values:
                    values = None
                elif len(values) == 1:
                    values = values[0]
                    
                    if isinstance(values, str):
                        commentPos = values.find('#')
                        if commentPos >= 0:
                            values = values[:commentPos].strip()
                            
                    
                    
                    vInt = None
                    vFloat = None
                    try:
                        radix = 10 
                        if values.startswith('0b'):
                            radix = 2
                        elif values.startswith('0x'):
                            radix = 16
                        vInt = int(values, radix)
                        values = vInt
                    except ValueError:
                        pass
                    if vInt is None:
                        try:
                            vFloat = float(values)
                            values = vFloat
                        except ValueError:
                            pass 
                    
                    if vInt is None and vFloat is None:
                        if values in self.convertToBools:
                            values = self.convertToBools[values]
                    
                self.config_dict[section][option] = values

    def get(self, section, option):
        """Get value of a givenoption in a given section."""
        if not self.has_section(section) \
                or not self.has_option(section,option):
                    return None
        return self.config_dict[section][option]

    def has_option(self, section, option):
        """Check for the existence of a given option in a given section."""
        if not section in self.config_dict:
            return False
        if option in self.config_dict[section].keys():
            return True
        else:
            return False

    def write(self, filename = None, fp = None):
        """Write an .ini-format representation of the configuration state."""
        if not fp and not filename:
            print("ERROR : no filename and no fp")
            raise
        elif not fp and filename:
            fp = open(filename,'w')

        for section in self.config_dict.keys():
            fp.write('[%s]\n' % section)
            for option in self.config_dict[section].keys():
                fp.write('\n%s =' % option)
                values = self.config_dict[section][option]
                if type(values) == type([]):
                    fp.write('\n    ')
                    values = '\n    '.join(values)
                else:
                    fp.write(' ')
                fp.write(values)
                fp.write('\n')
            fp.write('\n')


    def remove_option(self, section, option):
        """Remove an option."""
        if not self.has_section(section) \
                or not self.has_option(section,option):
                    raise
        del self.config_dict[section][option]

    def remove_section(self, section):
        """Remove a file section."""
        if not self.has_section(section):
            raise
        del self.config_dict[section]
