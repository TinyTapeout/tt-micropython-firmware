'''
Created on Apr 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.mode import RPMode
from ttboard.pins.pins import Pins 
from ttboard.project_mux import ProjectMux
from ttboard.boot.demoboard_detect import DemoboardCarrier, DemoboardDetect

class Globals:
    Pins_Singleton = None 
    ProjectMux_Singleton = None 
    
    @classmethod 
    def pins(cls, mode=None) -> Pins:
        if cls.Pins_Singleton is None:
            if mode is None:
                mode = RPMode.SAFE
            cls.Pins_Singleton = Pins(mode=mode)
            
        if mode is not None and mode != cls.Pins_Singleton.mode:
            cls.Pins_Singleton.mode = mode 
            
        return cls.Pins_Singleton
    
    
    @classmethod
    def project_mux(cls, for_shuttle_run:str=None) -> ProjectMux:
        if cls.ProjectMux_Singleton is None:
            # allow shuttle forcing regardless of whether this is 
            # the FPGA breakout or not
            if for_shuttle_run is not None or DemoboardDetect.CarrierVersion != DemoboardCarrier.FPGA:
                # instantiate a normal ASIC project mux
                cls.ProjectMux_Singleton = ProjectMux(cls.pins(), for_shuttle_run)
            else:
                # FPGA breakout and no shuttle forced, we actually need the FPGAMux class in this case
                from ttboard.fpga.fpga_mux import FPGAMux
                # instantiate it
                cls.ProjectMux_Singleton = FPGAMux(cls.pins()) 
                
        elif for_shuttle_run is not None:
            raise RuntimeError('Only expecting a shuttle on first call of Globals.project_mux')
            
        return cls.ProjectMux_Singleton
    