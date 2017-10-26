#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
import functools

# Internal modules
from access_control import Database, AccessControl
from relay import Relay
from tcp_server import RelayServerProtocol
from barscanner import Barscanner


def barscanner_handle(read_code, direction, relay, access_ctl):
    if access_ctl.is_valid_access(read_code, direction):
        relay.send_pulse(50)

        if direction == "in":
            access_ctl.userEnters(read_code)
            print("Entering")
        if direction == "out":
            access_ctl.userExits(read_code)
            print("Exiting")


# --------------- Main Program ---------------


def main():
    # Constants definition
    RELAY_PIN = 37           # Relay GPIO Board Pin

    # Setup relay
    relay = Relay(RELAY_PIN)

    # Setup databases
    credentials = []
    with open("/home/pi/fecoteme_access_control/dbcredentials.txt") as f:
        for line in f:
            credentials.append(line.split())

    accessDB = Database(*credentials[0])
    accessDB.connect()
    movementsDB = Database(*credentials[1])
    movementsDB.connect()

    # Setup access control system
    accessControl = AccessControl(accessDB, movementsDB)

    # Set barscanners callbacks
    barscanner0_cb = functools.partial(barscanner_handle,
                                       relay=relay,
                                       access_ctl=accessControl)

    barscanner1_cb = functools.partial(barscanner_handle,
                                       relay=relay,
                                       access_ctl=accessControl)
    # Setup barscanners
    barscanner0 = Barscanner('/dev/barscanner0', "in", barscanner0_cb)
    barscanner1 = Barscanner('/dev/barscanner1', "out", barscanner1_cb)

    loop = asyncio.get_event_loop()

    async def handle_exception(coroutine):
        try:
            await coroutine()
        except OSError:
            print("OSError Exception: Barcode scanner failed")
            exit(1)

    # Setup barscanners async handle tasks
    for barscanner in barscanner0, barscanner1:
        asyncio.ensure_future(handle_exception(barscanner.read_code_coroutine))

    # Run main event loop
    try:
        loop.run_forever()
    except:
        loop.close()

if __name__ == "__main__":
    main()
