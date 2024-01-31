# TT4+ MicroPython SDK

&copy; 2024 Pat Deegan, [psychogenic.com](https://psychogenic.com)

This library provides the DemoBoard class, which is the primary
entry point to all the TinyTapeout demo pcb's RP2040 functionality, including

    * pins (named, transparently muxed)
    * projects (all shuttle projects and means to enable)
    * basic utilities (auto clocking projects etc)
    * default and per-project configuration with ini file
    
## Quick Start

See main.py for some sample usage.


### Automatic Load and Default Config

The `config.ini` file has a **DEFAULT** section that may be used to specify the demo board mode, and default project to enable.

```
[DEFAULT]
# project: project to load by default
project = tt_um_test

# start in reset (bool)
start_in_reset = no

# mode can be any of
#  - SAFE: all RP2040 pins inputs
#  - ASIC_ON_BOARD: TT inputs,nrst and clock driven, outputs monitored
#  - ASIC_MANUAL_INPUTS: basically same as safe, but intent is clear
mode = ASIC_ON_BOARD

```
Each project on the shuttle may have it's own section as well, with additional attributes.  All attributes are optional.
See the config section, below, for details.


### REPL and Scripting

After install, scripts or the REPL may be used.  With micropython, the contents of main.py are executed on boot.

Efforts have been made to make console use easy, so do try out code completion using <TAB>, e.g.

```
tt.shuttle.<TAB><TAB>

```

will show you all the projects that might be enabled, etc.

Here's a sample REPL interaction with an overview of things to do

```
from machine import Pin
from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard

# get a handle to the board
tt = DemoBoard()

# enable a specific project, e.g.
tt.shuttle.tt_um_test.enable()

print(f'Project {tt.shuttle.enabled.name} running ({tt.shuttle.enabled.repo})')

# play with the inputs
tt.in0(1)
tt.in7(1)
# or as a byte
tt.input_byte = 0xAA

# start automatic project clocking
tt.clock_project_PWM(2e6) # clocking projects @ 2MHz


# observe some outputs
if tt.out2():
    print("Aha!")

print(f'Output is now {tt.output_byte}')

# play with bidir pins manually (careful)
tt.uio2.mode = Pin.OUT
tt.uio2(1) # set high

# or set a PWM on some pin (output to RP2040/input to ASIC)
tt.uio2.pwm(2000) # set to 2kHz, duty may be specified

tt.uio2.pwm(0) # stop PWMing

# if you changed modes on pins, like bidir, and want 
# to switch project, reset them to IN or just
tt.mode = RPMode.ASIC_ON_BOARD # or RPMode.SAFE etc
```


# Installation 

For all this to work, you need [MicroPython](https://micropython.org/) and these modules installed.

The directions for installing uPython are exactly those for 
[installing it on the Raspberry Pi Pico](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html).  Hold the BOOT button while plugging into usb, copy over the UF2 file. The end.

Next, copy over the entire contents of this directory to the /pyboard/ using rshell or mpremote.

Finally, access the REPL using a serial terminal (under Linux, the port shows up as /dev/ttyACM0, baudrate seem irrelevant).


# Usage

The quick start above gives you a good idea of how this all works.

If using this code as-is, with the main.py included, a `tt` object will already be instantiated.  Type

```
tt.
```

and then use the TAB-completion--it's really handy and let's you know what's available.  E.g.

```
tt.shuttle.<TAB><TAB>
```

will show you all the projects you can enable.


## Initialization

When the DemoBoard object is created, you _may_ give it a parameter to indicate how you intend to use it.  

If not specifed, the value in `config.ini` DEFAULT section `mode` will be used.


Possible values are:

```
# use ini value
tt = DemoBoard() # whatever was in DEFAULT.mode of config.ini


# safe mode, the default
tt = DemoBoard(RPMode.SAFE) # all RP2040 pins are inputs

# or: ASIC on board
tt = DemoBoard(RPMode.ASIC_ON_BOARD) # ASIC drives the inputs (i.e. in0, in1 etc are OUTPUTS for the RP2040)

# or: ASIC on board but you want to twiddle inputs and clock 
# using on-board DIP switches and buttons
tt = DemoBoard(RPMode.ASIC_MANUAL_INPUTS) # ASIC drives only management pins all else are inputs


```

If you've played with the pin mode (direction), you've loaded a project that modified the mode or you just want to change modes, you can set the attribute explicitly or call reset() on the Pins container

```

# simply set the tt mode
tt.mode = RPMode.ASIC_ON_BOARD

# or call reset on the pins, to set to whatever the
# last mode was
tt.pins.reset()

# or with a parameter, to change modes
tt.pins.reset(RPMode.SAFE) # make everything* an input
```


## Projects

The DemoBoard object has a `shuttle` attribute, which is a container with all the project designs (loaded from a JSON file).

Projects are objects which are accessed by name, e.g.

```
tt.shuttle.tt_um_gatecat_fpga_top
# which has attributes
tt.shuttle.tt_um_gatecat_fpga_top.repo
tt.shuttle.tt_um_gatecat_fpga_top.commit
# ...

```

These can be enabled by calling ... enable()

```
tt.shuttle.tt_um_gatecat_fpga_top.enable()
```

This does all the control signal twiddling needed to select and enable the project using the snazzy TinyTapeout MUX.

The currently enabled project, if any, is accessible in

```
>>> tt.shuttle.tt_um_test.enable()

>>> tt.shuttle.enabled
<Design 54: tt_um_test>

>>> tt
<DemoBoard as ASIC_ON_BOARD, auto-clocking @ 10, project 'tt_um_test' (in RESET)>

>>> tt.reset_project(False)

>>> tt
<DemoBoard as ASIC_ON_BOARD, auto-clocking @ 10, project 'tt_um_test'>

```


## Configuration

A `config.ini` file may be used to setup defaults (e.g. default mode or project to load on boot) as well as specific configuration to apply when loading a project in particular.  See the included `config.ini` for samples with commentary.

### Sections and Values

This is *similar* to, but not the same (because hand-crufted) as the python config parser.

Sections are simply name `[SECTION]`.

Values are 

```
key = value
```

Where the value may be

   * a string
   * a numerical value (an int, float, 0xnn or 0bnnnnnnnn representation)
   * a boolean (true, false, yes, no)
   * a comment (a line beginning with #)


### System Defaults

System-wide default settings supported are

project: (string) name of project to load on boot, e.g. *tt_um_loopback*

mode: (string) ASIC_ON_BOARD, ASIC_MANUAL_INPUTS (to use the on-board switches/buttons), or SAFE 

start_in_reset: (bool) whether projects should have their nRESET pin held low when enabled


### Project-specific

Some values may be auto-configured when enabling a project, by having them specified in their own section.
The section name is 

```
[PROJECT_NAME]
```

as specified in the shuttle, for instance

```
[tt_um_psychogenic_neptuneproportional]

```

Values that may be set are
 * clock_frequency: Frequency, in Hz, to auto-clock on project clock pin (ignored if in ASIC_MANUAL_INPUTS)
 * input_byte: value to set for inputs on startup (ignored if in ASIC_MANUAL_INPUTS)
 * bidir_direction: bits set to 1 are driven by RP2040
 * bidir_byte: actual value to set (only applies to outputs)
 * mode: tt mode to set for this project
 
Project auto-clocking is stopped by default when a project is loaded.  If the clock_frequency is set, then 
it will be setup accordingly.

Bi-directional pins (uio*) are reset to inputs when enabling another project.


## Pins

Pins may be read by "calling" them:

```
if tt.out5():
    # do something
```

and set by calling with a param

```
tt.in7(1)
```

Mode may be set with the `mode` attrib

```
tt.ui03.mode = Pin.OUT
```


Pins that are outputs (depends on tt mode) may be setup to automatically clock using

```
tt.uio3.pwm(FREQUENCY, [DUTY_16])
```

If FREQUENCY is 0, PWM will stop and it will revert to simple output.  If duty cycle is not specified, it will be 50% (0xffff/2).


The tt ran out of pinnage for all the things it wanted to do, so some of the connections actually go through a multiplexer.

Do you care?  No.  And you shouldn't need to.

All the pins can be read or set by simply calling them:

```
tt.uio4() # no param: read.  Returns the current value of uio4
tt.in7(0) # with a param: write.  So here, make in7 low
```


The callable() interface for the pins is available regardless of which pin it is.

Under the hood, these aren't actually *machine.Pin* objects (though you can access that too) but in most instances they behave the same, so you could do things like `tt.in7.irq(...)` etc.  In addition, they have some useful properties that I have no idea why are lacking from machine.Pin most of the time, e.g.

```
tt.uio4.mode = Pin.IN
tt.uio4.pull = Pin.PULL_UP

print(f'{tt.uio4.name} is on GPIO {tt.uio4.gpio_num} and is an {tt.uio4.mode_str}')
```



In some instances--those pins that are actually behind the hardware multiplexer--*all* they 
have is the call() interface and will die if you try to do machine.Pin type things.

This is on purpose, as a reminder that these are special (e.g. `out0` isn't really a pin, here... 
you want an IRQ? set it explicitly on `tt.sdi_out0`).  See below, in "MUX Stuff" for more info.

Pins that are logically grouped together in our system can be accessed that way:

```

for i in tt.inputs:
    i(1)

# easier to just
tt.input_byte = 0xff

print(tt.output_byte)
tt.bidirs[2](1)

```

The list (all 8 pins) and _byte attributes are available for inputs, outputs and bidir.



If you do not care for all this OO mucking about, you can always do things manual style as well.  The 
RP GPIO to name mapping is available in the schematic or just use GPIOMap class attribs:

```
import machine
from ttboard.pins import GPIOMap

p = machine.Pin(GPIOMap.IN6, machine.Pin.OUT)
# and all that
```

Just note that the MUX stuff needs to be handled for those pins.  


### Available pins
The pins available on the tt object include

  * out0 - out7
  * in0 - in7
  * uio0 - uio7
  * project_clk
  * project_nrst



NOTE that this naming reflect the perspective of the *ASIC*.  The *ASIC* normally be writing to out pins and reading from in pins, and this is how pins are setup when using the `ASIC_ON_BOARD` mode (you, on the RP2040, read from out5 so it is an Pin.IN, etc).


### MUX Stuff

In all instance except where the GPIO pins are MUXed, these behave just like machine.Pin objects.

For the MUXed pins, these are also available, namely

  * sdi_out0
  * sdo_out1
  * ncrst_out2
  * cinc_out3
  
You don't normally want to play with these, but you can.  The interesting thing you 
don't *have* to know is how the MUX is transparently handled, but I'm telling you 
anyway with an example

```
tt.sdi(1) # writing to this output
# MUX now has switched over to control signal set
# and sdi_out0 is an OUTPUT (which is HIGH)
print(tt.out0()) # reading that pin
# to do this MUX has switched back to the outputs set
# and sdi_out0 is an INPUT
```

## Useful Utils

You may do everything manually, if desired, using the pins.  Some useful utility methods are

```

# reset_project: make it clear
tt.reset_project(True) # held in reset
tt.reset_project(False) # not in reset


# under normal operation, the project clock is 
# an output 
>>> tt.project_clk
<StandardPin rp_projclk 0 OUT>


# clock_project_PWM: enough bit-banging already
# auto PWM the project_clk
tt.clock_project_PWM(500e3) # clock at 500kHz

Since it's PWMed, we now have direct access to that
>>> tt.project_clk
<PWM slice=0 channel=0 invert=0>

>>> tt.project_clk.freq()
500000


# later
tt.clock_project_stop() # ok, stop that
# or
tt.clock_project_PWM(0) # stops it

# back to normal output
>>> tt.project_clk
<StandardPin rp_projclk 0 OUT>

```

Also, many objects have decent representation so you can inspect them just by entering their references in the console

```
>>> tt
<DemoBoard as ASIC_ON_BOARD, auto-clocking @ 10, project 'tt_um_test' (in RESET)>

>>> tt.uio3
<StandardPin uio3 24 IN>

>>> tt.in0
<StandardPin in0 9 OUT>

```

And the DemoBoard objects have a *dump()* method to help with debug.

```
>>> tt.dump()

Demoboard status
Demoboard default mode is ASIC_ON_BOARD
Project nRESET pin is OUT 0
Project clock PWM enabled and running at 10
Selected design: tt_um_test
Pins configured in mode ASIC_ON_BOARD
Currently:
  cinc_out3 IN 0
  ctrl_ena OUT 1
  hk_csb OUT 1
  hk_sck IN 0
  in0 OUT 0
  in1 OUT 0
  in2 OUT 0
  in3 OUT 0
  in4 OUT 0
  in5 OUT 0
  in6 OUT 0
  in7 OUT 0
  ncrst_out2 IN 0
  nproject_rst OUT 0
  out4 IN 0
  out5 IN 0
  out6 IN 0
  out7 IN 0
  rp_projclk OUT 0
  rpio29 IN 0
  sdi_out0 IN 0
  sdo_out1 IN 0
  uio0 IN 0
  uio1 IN 0
  uio2 IN 0
  uio3 IN 0
  uio4 IN 0
  uio5 IN 0
  uio6 IN 0
  uio7 IN 0

```

