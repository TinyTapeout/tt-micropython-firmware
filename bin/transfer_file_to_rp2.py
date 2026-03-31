#!/usr/bin/env python
'''
Sample implementation of file upload to RP2 FS that doesn't rely on anything but a 
connection to USB serial.

This just puts the RP2 into raw mode, imports a module that is normally ignored, and 
shoots over the file in chunks, b64 encoded.  Easy-peasy.

It also provides a digest (SHA256) if you want to verify validity, demoed here.

Run with

  transfer_file_to_rp2.py -p /dev/ttyACM0 LOCALFILE /FULL/PATH/ON/REMOTE/FS/FILE

'''
import os
import serial
import base64
import argparse
import time
import hashlib

ChunkSize = 256

def read_pending(ser):
    data = b''
    while ser.in_waiting:
        data += ser.read(ser.in_waiting)
        # print(f"GOT DATA: {data}")
        time.sleep(0.005)
    return data
def read_until(ser, ending, timeout=5):
    """
    Read from serial until the ending byte sequence is found.
    """
    data = b''
    start_time = time.time()
    while time.time() - start_time < timeout:
        if ser.in_waiting:
            data += ser.read(ser.in_waiting)
            # print(f"GOT DATA: {data}")
            if data.endswith(ending):
                return data[:-len(ending)]
        time.sleep(0.01)
    raise TimeoutError("Timeout waiting for ending sequence")

def enter_raw_repl(ser):
    """
    Enter raw REPL mode on the MicroPython device.
    """
    # Interrupt any running code with Ctrl-C twice
    ser.write(b'\r\x03\x03')
    time.sleep(0.1)
    # Clear any buffered output
    if ser.in_waiting:
        ser.read(ser.in_waiting)
    # Enter raw REPL with Ctrl-A
    ser.write(b'\r\x01')
    # Expect the raw REPL banner
    banner = read_until(ser, b'raw REPL; CTRL-B to exit\r\n>')
    if not banner:
        raise RuntimeError("Failed to enter raw REPL")

def exec_command(ser, command, expect_output=False):
    """
    Execute a command in raw REPL and return the output if expected.
    """
    # print(f"EXEC COMMAND: {command}")
    print('.', end='', flush=True)
    # Send the command followed by Ctrl-D to execute
    ser.write(command.encode('utf-8') + b'\x04')
    # Read until Ctrl-D (end of output)
    if expect_output:
        time.sleep(0.3)
        
    output = read_pending(ser)
    msg = b''
    if len(output):
        msg = output.replace(b'OK\x04\x04>', b'')
        msg = msg.replace(b'\x04', b'')
        msg = msg.replace(b'OK', b'')
        msg = msg.replace(b'>', b'')
        if len(msg):
            print(msg)
    # In raw REPL, errors appear in output; check for them
    if b'Traceback' in output or b'Error' in output:
        raise RuntimeError(f"Execution error: {output.decode('utf-8', errors='ignore')}")
    if expect_output and len(msg):
        return msg.decode('utf-8', errors='ignore').strip()
    return None

def main():
    parser = argparse.ArgumentParser(description="Transfer file to MicroPython device via raw REPL")
    parser.add_argument('-p', '--port', required=True, help="Serial port to connect to (e.g., COM3 or /dev/ttyACM0)")
    parser.add_argument('local_file_to_send', help="Local file to send")
    parser.add_argument('file_path_to_write', help="Remote (full) file path to write to device (/path/to/file.ext)")
    args = parser.parse_args()
    
    if not os.path.exists(args.local_file_to_send):
        print(f'I cannot seem to find "{args.local_file_to_send}" to send?')
        return
    
    hasher = hashlib.sha256()
    

    # Open serial connection (assuming default baudrate for MicroPython)
    with serial.Serial(args.port, 115200, timeout=5) as ser:
        enter_raw_repl(ser)

        import_cmd = f"from ttboard.util.file_xfer import *\r\n"
        exec_command(ser, import_cmd)
        
        
        # create the file writer on the device
        init_cmd = f"f = FileWriter({repr(args.file_path_to_write)})\r\n"
        exec_command(ser, init_cmd)

        # Read and send the local file in chunks
        with open(args.local_file_to_send, 'rb') as local_file:
            while True:
                chunk = local_file.read(ChunkSize)
                if not chunk:
                    break
                hasher.update(chunk)
                b64_chunk = base64.b64encode(chunk).decode('ascii')
                write_cmd = f"f.w({repr(b64_chunk)})\r\n"
                exec_command(ser, write_cmd)

        # Close the file
        close_cmd = "f.close()\r\n"
        exec_command(ser, close_cmd)

        print(f"\nFile sent, expecting hash:\n{hasher.hexdigest()}.\nRequesting digest...")
        # Get and print the digest
        digest_cmd = "print(f.digest)\r\n"
        digest_output = exec_command(ser, digest_cmd, expect_output=True)
        print(digest_output)

        # Exit raw REPL with Ctrl-B
        ser.write(b'\x02')

if __name__ == "__main__":
    main()