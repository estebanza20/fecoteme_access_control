import RPi.GPIO as GPIO
import time

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
