
RP2040SystemClockDefaultHz = 125000000

IsRP2 = False
IsRP2040 = False 
IsRP2350 = False

try:
    import machine 
    from .rp2 import *
    IsRP2 = True
    try:
        _testpin = machine.Pin(40, machine.Pin.IN)
        IsRP2350 = True
        from .rp2350 import *
    except:
        IsRP2040 = True 
        from .rp2040 import *
        
except:
    from .desktop import *
    