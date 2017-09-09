#!/usr/bin/python3
# -*- coding: utf-8 -*-

#TODO: Handle no device exception

import RPi.GPIO as GPIO
import time
import evdev
import asyncio
import MySQLdb
import functools

from datetime import datetime, date
from dateutil.relativedelta import relativedelta


#--------------- Relay class ---------------

class Relay:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def send_pulse(self, ms=50):
        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(0.001*ms)
        GPIO.output(self.pin, GPIO.LOW)

    
#--------------- Barscanner class ---------------

class Barscanner:
    def __init__(self, device_name, code_ready_handle=None):
        self.device = evdev.InputDevice(device_name)
        self.read_code = ""
        self.code_ready_handle = code_ready_handle

    #Scancode: ASCIICode
    SCANCODES = {0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9',
                 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R', 20: u'T',
                 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL', 30: u'A',
                 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';', 40: u'"',
                 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N', 50: u'M',
                 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'}

    #Get corresponding ascii code for each event
    def map_code(self, data):
        return u'{}'.format(Barscanner.SCANCODES.get(data.scancode)) or u'UNKNOWN:[{}]'.format(data.scancode)

    #Get exclusive access to serial device
    def grab(self):
        self.device.grab()
        
    #Barscanner async read code coroutine
    async def read_code_coroutine(self):
        read_code = ''
        async for event in self.device.async_read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                data = evdev.categorize(event)
                if data.keystate == 1:  # Down events only                    
                    key_lookup = self.map_code(data)

                    if data.scancode != 28: #Building code
                        self.read_code += key_lookup
                    else: #Code ready
                        self.code_ready_handle(self.read_code)
                        self.read_code = ''

                        
#--------------- Relay TCP Server Protocol class ---------------                            

class RelayServerProtocol(asyncio.Protocol):
    def __init__(self, relay):
        self.relay = relay
        
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        print('Data received: {!r}'.format(message))

        if message.split('\n')[0] == 'open':
            self.relay.send_pulse(50)

        #print('Send: {!r}'.format(message))
        #self.transport.write(data)

        print('Close the client socket')
        self.transport.close()

#--------------- Program Misc functions ---------------

#FIXME: Change to consider quick pass special dates

def is_valid_access(db, affiliate_id):
    is_valid = False

    cursor = db.cursor()
    sql = "select firstName,lastName,subscriptionDate \
    from afiliado where (id='%d')" % (int(affiliate_id))
    try:
        cursor.execute(sql)
        db.commit()
    except:
        db.rollback()
        
    data = cursor.fetchone()
    print(60 * "-")
    print("Affiliate ID:", affiliate_id)
    
    if data is not None:
        name = " ".join(data[0:2])
        subscription_date = data[2]

        print("Name:", name)
        
        if subscription_date is not None:
            last_valid_access_date = subscription_date + relativedelta(days=+30)
            today = date.today()
            is_valid = (today <= last_valid_access_date)

            print("Subscription Date:",subscription_date)
            print("Last Valid Access Date:",last_valid_access_date)
            print("Days from Last Subscription Update:",(today-subscription_date).days)

            if is_valid == False:
                print("")
                print("Invalid access: Affiliate subscription has caducated.")
                print("Less or equal than 30 days from last subscription update")
                print("is required for access")
        else:
            print("")
            print("Invalid access: Affiliate has never been subscribed")
    else:
        print("")
        print("Invalid access: Affiliate does not exist")

    print(60 * "-")
        
    return is_valid


def barscanner_handle(read_code, relay, direction, database):
    if direction == "in":
        if is_valid_access(database, read_code):
            print("Entering")
            relay.send_pulse(50)
        else:
            print("Invalid access")
    if direction == "out":
        if is_valid_access(database, read_code):
            print("Exiting")
            relay.send_pulse(50)
        else:
            print("Invalid access")


        
#--------------- Main Program ---------------
        
def main():    
    #Constants definition
    RELAY_PIN = 37 #Relay GPIO Board Pin
    RPI_IP = '192.168.2.49' #Raspberry PI IP Address
    RPI_PORT = '8888' #Barcode_relay server port

    #Setup relay
    relay = Relay(RELAY_PIN)

    #Setup database
    db = MySQLdb.connect("localhost", "root", "", "fecoteme")

    #Set barscanners code ready callbacks
    barscanner0_cb = functools.partial(barscanner_handle,
                                       relay=relay, direction="in", database=db)
    barscanner1_cb = functools.partial(barscanner_handle,
                                       relay=relay, direction="out", database=db)
    #Setup barscanners
    barscanner0 = Barscanner('/dev/barscanner0', barscanner0_cb)
    barscanner1 = Barscanner('/dev/barscanner1', barscanner1_cb)
    
    #Get exclusive access to barscanners
    barscanner0.grab()
    barscanner1.grab()
    
    #Setup main event loop
    loop = asyncio.get_event_loop()

    #Setup barscanners async handle tasks
    for barscanner in barscanner0, barscanner1:
        asyncio.ensure_future(barscanner.read_code_coroutine())

    #Setup server    
    bound_protocol = functools.partial(RelayServerProtocol, relay)
    server_coroutine = loop.create_server(bound_protocol, RPI_IP, RPI_PORT)
    asyncio.ensure_future(server_coroutine)
    
    #Run main event loop
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
    

if __name__ == "__main__":
    main()
    
