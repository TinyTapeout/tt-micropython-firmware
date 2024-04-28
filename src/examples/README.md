# SDK project interaction examples and tests

This is the home of sample interaction scripts and tests specific to given projects.

The idea is to have a standardized place for sample code and to allow people to try out projects with ease.

## Quick start

We may have a means to do this via the commander app in the near future.  For now, 
if you want to run a sample, plug in the board to USB, connect to the REPL, load and run.


```
>>> import examples.tt_um_psychogenic_neptuneproportional
>>>
>>> examples.tt_um_psychogenic_neptuneproportional.run()
examples.tt_um_psychogenic_neptuneproportional.tt_um_psychogenic_neptuneproportional: Found a neptune section in config--letting it handle things
ttboard.project_mux: Enable design tt_um_psychogenic_neptuneproportional
ttboard.demoboard: Switching to mode ASIC_RP_CONTROL for design "tt_um_psychogenic_neptuneproportional"
ttboard.pins.pins: Setting mode to ASIC_RP_CONTROL
"Playing" a note: E2 (83Hz)
   Bidir count: 41 (ratio 2.0), Outputs 0x4
   Bidir count: 42 (ratio 2.0), Outputs 0xcb
   Bidir count: 41 (ratio 2.0), Outputs 0x9

```

# Adding samples

If you have a project on a chip and would like to include sample usage here:


  * fork this repo
  
  * create a package using the name of your project as per the submitted info.yaml.  This is a subdirectory of that name with an `__init__.py` file.
  
  * Do what you want in there
  
  * expose a `run()` method in your top level `__init__.py`.  This method returns True if all went well.
  
You can see the [neptune sample](tt_um_psychogenic_neptuneproportional/__init__.py) here.


In your code, you can get access to the Demoboard object by using

```
from ttboard.demoboard import DemoBoard

def run():
    tt = DemoBoard.get()
    
    # ... use it
    
```

You can use logging, as in the neptune example.  It will probably be that logging acts as usual and `print()` will come out on the commander when available.

When you have something nice, issue a PR to get us to merge the sample.

## naming and shuttles

What if you have `tt_um_yourname_aproject` on multiple shuttles and they behave differently?

That Demoboard object gives you access to the run of the currently-loaded ASIC (demo board's `shuttle.run`), so you can do things like


```
version_runners = {
    'tt03p5': run_03p5,
    'tt04': run_04,
    # ...
}

if tt.shuttle.run in version_runners:
    return version_runners[tt.shuttle.run]()

# not supported
print("Oh nooooo")
return False
```


If you want even more info on the ASIC, you may access the `tt.shuttle.chip_ROM` object (see docs/code).

## Coding

As long as the package naming is right and there's a way to access run() from the top level, style is pretty open.

My SHA 256 encoder will only be out with TT05, but the example [is already in](tt_um_psychogenic_shaman/) and shows another way to organize things when the system is a bit more complex.  I have a [wrapper around the TT DemoBoard object](tt_um_psychogenic_shaman/shaman.py) that translates in/out/bidir pins to something meaningful in the code.  This also puts a barrier in the way of trying to run it before the ASIC is actually out, by using a check on the tt.shuttle.run.




