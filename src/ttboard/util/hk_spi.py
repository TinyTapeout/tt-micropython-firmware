'''
Created on Jan 18, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.util.platform import IsRP2040
from ttboard.pins import Pins
from ttboard.demoboard import DemoBoard

if IsRP2040:
    import machine

class Enum:
    def __init__(self):
        pass 
class RegisterAddress(Enum):
    ManufacturerID = 0x01
    ProductID = 0x03
    UserProjectID = 0x04
    CPUIRQ = 0x0a
    CPUReset = 0x0b
    
    GPIOControl = 0x13 # gpio_adr | 12'h000 : spiaddr = 8'h13;    // GPIO control
    BaseGPIOAddress = 0x1d

class GPIOMode(Enum):
    MGMT_INPUT_NOPULL     = 0x0403
    MGMT_INPUT_PULLDOWN = 0x0c01
    MGMT_INPUT_PULLUP     = 0x0801
    MGMT_OUTPUT         = 0x1809
    MGMT_BIDIRECTIONAL     = 0x1801
    MGMT_ANALOG         = 0x000b
    
    
    USER_INPUT_NOPULL     = 0x0401
    USER_INPUT_PULLDOWN = 0x0c00
    USER_INPUT_PULLUP     = 0x0800
    USER_OUTPUT         = 0x1808
    USER_BIDIRECTIONAL     = 0x1800
    USER_ANALOG         = 0x000a
    
    
class GPIOPadBits(Enum):
    MGMT_ENABLE       = 0x0001
    OUTPUT_DISABLE    = 0x0002
    HOLD_OVERRIDE     = 0x0004
    INPUT_DISABLE     = 0x0008
    MODE_SELECT       = 0x0010
    ANALOG_ENABLE     = 0x0020
    ANALOG_SELECT     = 0x0040
    ANALOG_POLARITY   = 0x0080
    SLOW_SLEW_MODE    = 0x0100
    TRIPPOINT_SEL     = 0x0200
    DIGITAL_MODE_MASK = 0x1c00



class GPIOConfig:
    def __init__(self, mode=0):
        self.stdmode = None
        if not type(mode) == int:
            self.val = mode.value 
            self.stdmode = mode 
        else:
            self.val = mode
            try:
                self.stdmode = mode # GPIOMode(mode)
            except ValueError:
                pass
            
    @property 
    def value(self):
        return self.val 
        
    @value.setter
    def value(self, setTo:int):
        if not type(setTo) == int:
            self.val = setTo.value 
        else:
            self.val = setTo
            
    def maskBits(self, bits:GPIOPadBits):
        return self.val & bits # bits.value 
    
    def setBits(self, bits:GPIOPadBits):
        self.val =  self.val | bits # bits.value 
        
    def clearBits(self, bits:GPIOPadBits):
        self.val = self.val & ~bits # (bits.value)
        
    def _set(self, bits:GPIOPadBits, setTo:bool):
        
        if setTo:
            self.setBits(bits)
        else:
            self.clearBits(bits)
        
        
        
    @property 
    def mgmt_enable(self):
        return self.maskBits(GPIOPadBits.MGMT_ENABLE)
        
    @mgmt_enable.setter
    def mgmt_enable(self, setTo:bool):
        self._set(GPIOPadBits.MGMT_ENABLE, setTo)
    
    
    
    @property 
    def output_disable(self):
        return self.maskBits(GPIOPadBits.OUTPUT_DISABLE)
        
    @output_disable.setter
    def output_disable(self, setTo:bool):
        self._set(GPIOPadBits.OUTPUT_DISABLE, setTo)
        
        
    @property 
    def mode_select(self):
        return self.maskBits(GPIOPadBits.MODE_SELECT)
        
    @mode_select.setter
    def mode_select(self, setTo:bool):
        self._set(GPIOPadBits.MODE_SELECT, setTo)
        
        
    @property 
    def hold_override (self):
        return self.maskBits(GPIOPadBits.HOLD_OVERRIDE)
        
    @hold_override.setter
    def hold_override(self, setTo:bool):
        self._set(GPIOPadBits.HOLD_OVERRIDE, setTo)
        
    @property 
    def input_disable(self):
        return self.maskBits(GPIOPadBits.INPUT_DISABLE)
        
    @input_disable.setter
    def input_disable(self, setTo:bool):
        self._set(GPIOPadBits.INPUT_DISABLE, setTo)
        
        
    @property 
    def analog_enable (self):
        return self.maskBits(GPIOPadBits.ANALOG_ENABLE)
        
    @analog_enable.setter
    def analog_enable(self, setTo:bool):
        self._set(GPIOPadBits.ANALOG_ENABLE, setTo)
        
    
    @property 
    def analog_select(self):
        return self.maskBits(GPIOPadBits.ANALOG_SELECT)
        
    @analog_select.setter
    def analog_select(self, setTo:bool):
        self._set(GPIOPadBits.ANALOG_SELECT, setTo)
        
        
    @property 
    def analog_polarity(self):
        return self.maskBits(GPIOPadBits.ANALOG_POLARITY)
        
    @analog_polarity.setter
    def analog_polarity(self, setTo:bool):
        self._set(GPIOPadBits.ANALOG_POLARITY, setTo)
        
    
    def __repr__(self):
        return f'<GPIOConfig {hex(self.value)}>'
        
    def __str__(self):
        if self.stdmode is not None:
            retStr = f'{hex(self.value)} ({str(self.stdmode)})\n'
        else:
            retStr = f'{hex(self.value)}\n'
        props = [
            'mgmt_enable',
            'output_disable',
            'input_disable',
            'hold_override',
            'mode_select',
            'analog_enable',
            'analog_select',
            'analog_polarity',
        ]
        
        propDetails = []
        for p in props:
            v = 'false'
            if getattr(self, p):
                v = 'TRUE'
            
            propDetails.append(f'  {p}:\t{v}')
        
        retStr += '\n'.join(propDetails)
        return retStr
        
   
DUMPSPI = False
ReadReg  = 0b01000000
WriteReg = 0b10000000  
def arrayBytesString(bts):
    return ','.join(map(lambda x: hex(x), bts))
       
class HKSPI:
    def __init__(self, db:DemoBoard):
        self._db = db 
        self._spi = None 
        self._cs = self.pins.hk_csb
        
        
    @property 
    def cs(self):
        return self._cs
    @property 
    def pins(self) -> Pins:
        return self._db.pins
    @property 
    def spi(self):
        if not self._spi:
            self._spi = machine.SPI(0)
            self._spi = machine.SPI(0, baudrate=1000000, 
                                    sck=self.pins.pin_hk_sck, 
                                    mosi=self.pins.pin_sdi_out0, 
                                    miso=self.pins.pin_sdo_out1)

        return self._spi
    
    def select(self, doSelect:bool):
        if doSelect:
            self._cs(0)
        else:
            self._cs(1)
    
    
    def readRegister(self, startAddress, numBytes=1):
        spi = self.spi
        
        startAddr = startAddress
        if type(startAddress) != int:
            startAddr = startAddress.value 
            
        cmd = [ReadReg, startAddr]
        
        if DUMPSPI:
            cmdAndPayload = []
            for b in cmd:
                cmdAndPayload.append(b)
            for _i in range(numBytes):
                cmdAndPayload.append(0) 
                
            print(f"SPI READ: {arrayBytesString(cmdAndPayload)}")
            
        self.select(True)
        spi.write(bytearray(cmd))
        
        retVal = spi.read(numBytes)
        self.select(False)
        return retVal
        
    def writeRegisters(self, startAddress, bytesToWrite):
        spi = self.spi
        startAddr = startAddress
        if type(startAddress) != int:
            startAddr = startAddress.value 
            
        cmdAndPayload = [WriteReg, startAddr]
        for b in bytesToWrite:
            cmdAndPayload.append(b) 
            
        if DUMPSPI:
            print(f'SPI WRITE: {arrayBytesString(cmdAndPayload)}')
        self.select(True)
        spi.write(bytearray(cmdAndPayload))
        self.select(False)
        
    
    def get16bitRegister(self, startAddr):
        contents = self.readRegister(startAddr, 2)
        val =  (contents[0] << 8) | contents[1]
        return val
        
    
    def GPIOConfigAddress(self, gpio:int):
        return RegisterAddress.BaseGPIOAddress + (2*gpio)
        
    def getGPIOConfig(self, gpio:int):
        startAddr = self.GPIOConfigAddress(gpio)
        val = self.get16bitRegister(startAddr)
        return GPIOConfig(val)
        
    def setGPIOConfig(self, gpio:int, setTo:GPIOConfig):
        startAddr = self.GPIOConfigAddress(gpio)
        config = [0]*2
        config[0] = ((setTo & 0xff00) >> 8) # ((setTo.value & 0xff00) >> 8)
        config[1] = setTo & 0x00ff # setTo.value & 0x00ff
        self.writeRegisters(startAddr, config)
        
    def latchGPIOConfig(self):
        self.writeRegisters(RegisterAddress.GPIOControl, [1])
        
    def GPIOConfigReg(self):
        return self.get16bitRegister(RegisterAddress.GPIOControl)
        
    def GPIOConfigIsLatching(self):
        return self.GPIOConfigReg() & 0x01
        
    
    def setReset(self, on:bool=True):
        val = 1
        if not on:
            val = 0
        self.writeRegisters(RegisterAddress.CPUReset, [val])
        
    def dumpGPIOConfig(self):
        print(f'GCNF: {hex(self.GPIOConfigReg())}')
        
        