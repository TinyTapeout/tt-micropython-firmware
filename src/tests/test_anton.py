from ttboard.pins.upython import Pin # rather than from machine, allows dev on desktop
import ttboard.util.time as time     # for time.sleep_ms()
from ttboard.demoboard import DemoBoard

# ========= Config =========

# These are 'do nothing defaults' that get overridden further below:
PAUSE_DELAY = 0
EXTRA_DELAY = 0
BASIC_TEST  = False
FRAME_TEST  = False
PRINT_VSYNC_ERRORS = False
PRINT_LZC_ERRORS = False

# Lazy... override the above. Done this way so we can very quickly comment
# out as required, to disable those tests/configs:
PAUSE_DELAY = 3000  # Milliseconds to pause before each test.
EXTRA_DELAY = 0     # Extra milliseconds to sleep between clock pulses.
BASIC_TEST  = True
FRAME_TEST  = True
# PRINT_VSYNC_ERRORS = True
# PRINT_LZC_ERRORS = True

OUTPUT_TIMING = False

# ========= Helper functions =========

# print_tt_outputs():
# Show the state of the board's 8 uo_outs, and 8 bidir pins (treated also as outputs).
# Optionally also takes what they are *expected* to be, just for visual comparison.
def print_tt_outputs(tt:DemoBoard, expect_out:int=None, expect_bidir:int=None, prefix=''):
    print(f'{prefix} uo_out= {tt.uo_out.value:08b} bidir= {tt.uio_in.value:08b}', end='')
    if [expect_out,expect_bidir] != [None,None]:
        print('; expected', end='')
        if expect_out is not None:
            print(f' uo_out={expect_out:08b}', end='')
        if expect_bidir is not None:
            print(f' bidir={expect_bidir:08b}', end='')
    print()

# print_progress():
# Prints dots to show progress based on X (and optionally Y) input.
# Effectively gives a progress update every 16 pixels.
#NOTE: If 'ok' is False, and a progress character is due to be printed, it will be '!'
# instead of a dot, and True will be returned to show that we've 'reset' from an otherwise
# erroneous batch. If a progress character is NOT due, just return whatever 'ok' is currently.
def print_progress(x:int, y:int=0, ok:bool=True):
    if x&0b1111 == 0:
        # extra keyword arguments given print('.' if ok else '!', end='', flush=True)
        print('.' if ok else '!', end='')
        return True
    else:
        return ok

# announce():
# Print basic header for the next test, and (optionally) how long
# until it starts (given PAUSE_DELAY):
def announce(test_header:str):
    print(f'\n{test_header}')
    if PAUSE_DELAY > 0:
        print(f'(Will continue in {PAUSE_DELAY}ms...)')
        time.sleep_ms(PAUSE_DELAY)

# pulse_clock():
# Quick helper to pulse the clock and optionally wait out configured extra delay.
def pulse_clock(tt:DemoBoard):
    tt.clock_project_once()
    if EXTRA_DELAY > 0:
        time.sleep_ms(EXTRA_DELAY)

# do_reset():
# Go through a reset sequence by asserting reset, pulsing clock 3 times,
# then releasing reset again:
def do_reset(tt:DemoBoard):
    print('Resetting design...')
    tt.reset_project(True)
    for _i in range(3):
        tt.clock_project_once()
    tt.reset_project(False)

# calc_lzc():
# Given h (x) position, v (y) position, and frame number,
# calculates the value that the design's LZC should be returning
# via the bidir pins. Note that the typical output value is in the range
# [0,24] (5 bits) with an extra MSB (bit 5) being set to 1 if all
# 24 input bits are 0.
def calc_lzc(h:int, v:int, frame:int = 0):
    # Constrain input ranges:
    h &= 0x3FF # 10 bits
    v &= 0x3FF # 10 bits
    frame &= 0xF # 4 bits
    # Determine the input to the LZC (ffff'vvvv'vvvv'vvhh'hhhh'hhhh):
    lzc_in = (frame << 20) | (v << 10) | (h)
    # Count leading zeros:
    #NOTE: if lzc_in is 0, not only is out[4:0]==24, but also out[5] is 1
    # to indicate that all 24 bits are 0 (hence 24|32).
    return (24|32) if lzc_in==0 else (24-len(f'{lzc_in:b}'))


# ========= Main test code =========

# Get a handle to the base board: config.ini selects ASIC_RP_CONTROL mode to configure
# our RP2040 GPIOs for proper cooperation with an attached TT chip:
tt = DemoBoard()

# Enable my tt03p5-solo-squash design:
#NOTE: This might not be needed given our config.ini
tt.shuttle.tt_um_algofoogle_solo_squash.enable()
print(f'Project {tt.shuttle.enabled.name} selected ({tt.shuttle.enabled.repo})')

# Ensure we are *reading* from all of the ASIC's bidir pins:
for pin in tt.bidirs:
    pin.mode = Pin.IN

# Start with project clock low, and reset NOT asserted:
tt.clk(0)
tt.reset_project(False)

# By default all inputs to the ASIC should be low:
tt.ui_in.value = 0

# Print initial state of all outputs; likely to be somewhat random:
print_tt_outputs(tt, prefix='Pre-reset state:')

# Reset the design:
do_reset(tt)

# Now show the state of all outputs again.
# Expected outputs are what the design should always assert while held in reset:
print_tt_outputs(tt, expect_out=0b11011110, expect_bidir=0b11111000, prefix='Post-reset state:')

if BASIC_TEST:
    error_count = 0
    announce('BASIC_TEST: Basic test of first 2 video lines...')
    # Now, the design should render immediately from the first line of the visible
    # display area, and the first two lines that it renders should be fully yellow...
    #NOTE: RGB outs are registered (hence 'next_color' and 'color')
    # but the rest are not (i.e. hsync, vsync, speaker, col0, row0).
    next_color = 0b110 # Yellow
    for y in range(2):
        print(f'Line {y}:')
        bulk_ok = True  # 'bulk' because it keeps track of ANY error within a progress update batch.
        
        t_start = time.ticks_us()
        for x in range(800):
            # Make sure outputs match what we expect...
            color = next_color
            next_color = 0b110 if x<640 else 0 # Yellow
            hsync = 0 if x>=640+16 and x<640+16+96 else 1 # (HSYNC is active low)
            vsync = 0 if y>=480+10 and y<480+10+2 else 1 # (VSYNC is active low)
            speaker = 0 # Off
            col0 = 1 if x==0 else 0
            row0 = 1 if y==0 else 0
            expect_out = (row0<<7) | (col0<<6) | (speaker<<5) | (vsync<<4) | (hsync<<3) | color
            if tt.uo_out.value != expect_out:
                error_count += 1
                print_tt_outputs(tt, expect_out, prefix=f'[{x},{y}] Error:')
                bulk_ok = False
            bulk_ok = print_progress(x, ok=bulk_ok)
            pulse_clock(tt)
            
        t_end = time.ticks_us()
        if OUTPUT_TIMING:
            print(f'{int( (t_end - t_start)/1000 )}ms')
        else:
            print()
    print(f'\nBASIC_TEST done. Error rate: {error_count}/1600\n')


if FRAME_TEST:
    vsync_errors = 0
    lzc_errors = 0
    announce('FRAME_TEST: Content test of the first full frame...')
    do_reset(tt)
    # I'm lazy, so let's just count how many pixels there are of each colour in a full frame,
    # and compare with a prediction using the following guide...
    # Blue (varies):
    #   ~ 18.75%+/-1% of ((640-32)*(480-64)-32*64-16*16, i.e. playfield area minus paddle and ball.
    #   = 44485..49498
    # Green:
    #   + 28*28*20*2 - Interior of each block in the top and bottom walls
    #   + 28*28*13 - Interior of each block in the RHS wall
    #   + 16*16 - Ball  #NOTE: Ball area is less if the ball is off-screen or intersecting paddle
    #   = 41808
    # Red:
    #   + 32*64 - Paddle
    #   = 2048
    # Yellow:
    #   + 640*4 - Top/bottom borders for each of top and bottom walls
    #   + 28*4*20*2 - Left/right borders for each block of top/bottom walls
    #   + (32*32-28*28)*13 - All borders for each block of RHS wall
    #   = 10160
    # Cyan, Magenta, White: all 0
    cols=800
    rows=525
    total_pixels = rows*cols
    # With 3 colour bits, there are 8 possible colours to count:
    color_stats = [
        # [0]Name [1]Actual   [2]Expected
        ['Black',         0,  None                ], # Colour 0 # Irrelevant if others are (about) right.
        ['Blue',          0,  range(44485, 49499) ], # Colour 1
        ['Green',         0,  41808               ], # Colour 2
        ['Cyan',          0,  0                   ], # Colour 3
        ['Red',           0,  2048                ], # Colour 4
        ['Magenta',       0,  0                   ], # Colour 5
        ['Yellow',        0,  10160               ], # Colour 6
        ['White',         0,  0                   ]  # Colour 7
    ]
    paddle_y = None
    ball_x = None
    ball_y = None
    for y in range(rows):
        print(f'Line {y}:')
        bulk_ok = True
        t_start = time.ticks_us()
        for x in range(cols):
            # Increment the count in the bin of the current pixel colour:
            color = tt.uo_out.value & 0b111
            color_stats[color][1] += 1
            # Try to detect the paddle's Y position (i.e. the first line to have a red pixel):
            if paddle_y is None and color == 0b100: # Red.
                paddle_y = y
                print(f'Detected paddle_y: {paddle_y}')
            # Try to detect the ball position:
            if ball_x is None and color == 0b010 and y>=32 and y<480-32 and x<640-32: # Green.
                ball_x = x-1  # Registered, so delayed by 1.
                ball_y = y
                print(f'Detected ball position: ({ball_x},{ball_y})')
            # Make sure vsync is asserted at the right times:
            expected_vsync = 0 if y>=480+10 and y<480+10+2 else 1 # (VSYNC is active low)
            actual_vsync = (tt.uo_out.value & 0b10000) >> 4
            expected_lzc = calc_lzc(x, y)
            actual_lzc = tt.uio_in.value & 0b111111
            if actual_vsync != expected_vsync:
                bulk_ok = False
                vsync_errors += 1
                if PRINT_VSYNC_ERRORS:
                    print_tt_outputs(tt, expect_out, prefix=f'[{x},{y}] VSYNC error:')
            if actual_lzc != expected_lzc:
                bulk_ok = False
                lzc_errors += 1
                if PRINT_LZC_ERRORS:
                    print_tt_outputs(tt, expect_out, prefix=f'[{x},{y}]   LZC error:')
            bulk_ok = print_progress(x, y, ok=bulk_ok)
            pulse_clock(tt)
        t_end = time.ticks_us()
        if OUTPUT_TIMING:
            print(f'{int( (t_end - t_start)/1000 )}ms')
        else:
            print()

    print()
    if vsync_errors==0:
        print('No VSYNC errors.')
    else:
        print(f'VSYNC error rate: {vsync_errors}/{total_pixels}')
    
    if lzc_errors==0:
        print('No LZC errors.')
    else:
        print(f'LZC error rate: {lzc_errors}/{total_pixels}')

    if paddle_y is None:
        print('ERROR: Paddle was NOT detected')
    else:
        print(f'Paddle was detected; top edge is Y={paddle_y}')

    if ball_x is None:
        print('ERROR: Ball was NOT detected')
    else:
        print(f'Ball was detected at position ({ball_x},{ball_y})')

    print('\nCounted pixel colours:')
    print(f'=============================================')
    print(f"{'RGB':5s}{'Color':10s}{'Actual':>10s}{'Expected':>10s}")
    print(f'---------------------------------------------')
    for i in range(len(color_stats)):
        name = color_stats[0]
        actual = color_stats[1]
        expected = color_stats[2]
        print(f'{i:03b}  {name:10s}{actual:>10d}', end='')
        if expected is None:
            print('-')
            continue
        elif isinstance(expected, range):
            print(expected, end='')
            fail = actual not in expected
        else:
            print(f"{expected:>10d}", end='')
            fail = actual != expected

        if fail:
            print(' - ERROR')
        else:
            print()
    print(f'=============================================')

    print('\FRAME_TEST done\n')


"""
    TODO:
    -   Try running on upython/RP2040
    -   Is there a good way to write inputs/outputs to a file, e.g. VCD?
    -   Can we make mapped pin names to suit actual pin names for our design?
    -   Test running the design at full speed... IRQs to check expected conditions?
    -   Print '*' instead of '.' for any batch that contains at least 1 error
"""
