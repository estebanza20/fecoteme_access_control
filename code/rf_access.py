#! /usr/bin/python3

import time
import RPi.GPIO as GPIO
import functools
from relay import Relay

D0_PIN = 16

def activate_relay(channel, relay):
    # GPIO.wait_for_edge(D0_PIN, GPIO.FALLING)
    if GPIO.input(D0_PIN):
        relay.send_pulse(50)

def main():
    RELAY_PIN = 37
    VT_PIN = 18

    GPIO.setmode(GPIO.BOARD)

    relay = Relay(RELAY_PIN)

    GPIO.setup(VT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(D0_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    relay_cb = functools.partial(activate_relay, relay=relay)

    # Add ISR to falling edge detected in valid pin
    GPIO.add_event_detect(VT_PIN, GPIO.RISING, callback=relay_cb, bouncetime=500)


    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
