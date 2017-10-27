#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
import functools
import multiprocessing

# Internal modules
from access_control import Database, AccessControl
from relay import Relay
from tcp_server import RelayServerProtocol
from barscanner import Barscanner


def barscanner_handle(read_code, direction, relay, access_ctl):
    if access_ctl.isValidAccess(read_code, direction):
        relay.send_pulse(50)
        if direction == "in":
            access_ctl.userEnters(read_code)
            print("Entering")
        if direction == "out":
            access_ctl.userExits(read_code)
            print("Exiting")


def mov_write_db_handle(movdbCredentials, movWriteQueue):
    movementsDB = Database(*movdbCredentials)
    movementsDB.connect()
    while True:
        if not movWriteQueue.empty():
            (affiliate_id, mov_type, timestamp) = movWriteQueue.get()

            sql = "insert into movimientos (carne,tipo,fecha) values\
            ('%s', '%d', '%s')" % (affiliate_id, mov_type, timestamp)

            print("Before movementsDB query")
            movementsDB.query(sql)
            print("After movementsDB query")

            movWriteQueue.task_done()

# --------------- Main Program ---------------


def main():
    # Relay GPIO Board Pin
    RELAY_PIN = 37 

    # Setup relay
    relay = Relay(RELAY_PIN)

    # Setup Databases
    credentials = []
    with open("/home/pi/fecoteme_access_control/dbcredentials.txt") as f:
        for line in f:
            credentials.append(line.split())

    # Read-Only Access Subscription Database
    accessDB = Database(*credentials[0])
    accessDB.connect()

    # Write-Only Movements Register Database (Handled by daemon)
    movQueue = multiprocessing.JoinableQueue(False)
    movementsDB_Handler = multiprocessing.Process(target=mov_write_db_handle,
                                      args=(credentials[1], movQueue))
    movementsDB_Handler.daemon = True
    movementsDB_Handler.start()

    # Setup Access Control System
    accessControl = AccessControl(accessDB, movQueue)

    # Set Barscanners Callbacks
    barscanner0_cb = functools.partial(barscanner_handle,
                                       relay=relay,
                                       access_ctl=accessControl)

    barscanner1_cb = functools.partial(barscanner_handle,
                                       relay=relay,
                                       access_ctl=accessControl)
    # Setup Barscanners
    barscanner0 = Barscanner('/dev/barscanner0', "in", barscanner0_cb)
    barscanner1 = Barscanner('/dev/barscanner1', "out", barscanner1_cb)

    loop = asyncio.get_event_loop()

    async def handle_exception(coroutine):
        try:
            await coroutine()
        except OSError:
            print("OSError Exception: Barcode scanner failed")
            exit(1)

    # Setup Barscanners Async Handle Tasks
    for barscanner in barscanner0, barscanner1:
        asyncio.ensure_future(handle_exception(barscanner.read_code_coroutine))

    # Run Main Event Loop
    try:
        loop.run_forever()
    except:
        loop.close()
        movQueue.join()  # Wait for all DB transactions to complete

if __name__ == "__main__":
    main()
