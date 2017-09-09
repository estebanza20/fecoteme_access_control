#!/usr/bin/python3
# -*- coding: utf-8 -*-

#TODO: Handle no device exception

import RPi.GPIO as GPIO
import time
import evdev
import asyncio


barscanner0 = evdev.InputDevice('/dev/barscanner0')
barscanner1 = evdev.InputDevice('/dev/barscanner1')


scancodes = {
    # Scancode: ASCIICode
    0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
    10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
    20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
    30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';',
    40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
    50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'
}

PIN = 37

GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN, GPIO.OUT)
GPIO.output(PIN, GPIO.LOW)

match_code = '9051203990002'

#grab provides exclusive access to the devices
barscanner0.grab()
barscanner1.grab()


def relay_pulse(ms):
    GPIO.output(PIN, GPIO.HIGH)
    time.sleep(0.001*ms)
    GPIO.output(PIN, GPIO.LOW)

def map_code(data, code_dict):
    return u'{}'.format(code_dict.get(data.scancode)) or u'UNKNOWN:[{}]'.format(data.scancode)

def match_handle(device):
    if device.phys == barscanner0.phys:
        print("Barscanner 0")
        relay_pulse(50)
    if device.phys == barscanner1.phys:
        print("Barscanner 1")
        relay_pulse(50)

        
async def read_codes(device):
    read_code = ''
    async for event in device.async_read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            data = evdev.categorize(event)
            if data.keystate == 1:  # Down events only                    
                key_lookup = map_code(data, scancodes)

                if data.scancode != 28:
                    read_code += key_lookup
                else:
                    print("Read code: ", read_code)
                    if read_code == match_code:
                        print("Code match success")
                        match_handle(device)
                    else:
                        print("Code match failed")
                    read_code = ''

                    
async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    print("Received %r from %r" % (message, addr))

    if message.split('\n')[0] == 'open':
        relay_pulse(50)

    #print("Send: %r" % message)
    #writer.write(data)
    #await writer.drain()

    print("Close the client socket")
    writer.close()



loop = asyncio.get_event_loop()

rpi_ip = '192.168.2.49'
server_coro = asyncio.start_server(handle_echo, rpi_ip, 8888, loop=loop)

asyncio.ensure_future(server_coro)
    
for device in barscanner0, barscanner1:
    asyncio.ensure_future(read_codes(device))

    
try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.close()
    
