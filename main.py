from enum import Enum
from lcd import LCD
import OPi.GPIO as GPIO
import requests
import utils as Util
import traceback
import json

DAYS_IN_SECONDS = 5 * 24 * 60 * 60 # first digit is the number of days

voucher_config = json.load(open('voucher_config.json'))
multiplier = voucher_config['multiplier']
storeName = voucher_config['storeName']

url = 'https://omada-api.fly.dev'

lcd = LCD()
lcd.display_message(line1=storeName, line3='Please wait!', line4='Starting sytem...')

class PINS(Enum):
    COIN = 11
    COIN_SET = 13
    BUTTON = 15

class CoinSlot():
    new_voucher = None
    credit = 0
    processing = False
    wait_timer = 0
    wait_timeout = 5
    reset_timer = 0
    reset_timeout = 120 # seconds
    debounce_timer = 0

    def __init__(self) -> None:
        GPIO.cleanup()

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(PINS.COIN, GPIO.IN)
        GPIO.setup(PINS.BUTTON, GPIO.IN)

        GPIO.add_event_detect(PINS.COIN , GPIO.FALLING, callback=self.callback)
        GPIO.add_event_detect(PINS.BUTTON, GPIO.RISING, callback=self.callback)

    def run(self) -> None:
        try:
            while True:
                self.reset()
        except Exception:
            GPIO.cleanup()
            print(traceback.format_exc())

    def reset(self):
        if self.reset_timer > 0:
            if Util.getCurrentTime() - self.reset_timer > self.reset_timeout:
                self.reset_timer = 0
                self.display_menu()

    def debounce(self) -> bool:
        return (Util.getCurrentTime() - self.debounce_timer) > 40
    
    def wait_for(self, seconds):
        self.wait_timer = Util.getCurrentTime()
        self.wait_timeout = seconds
    
    def isready(self) -> bool:
        return (self.wait_timer == 0 or Util.getCurrentTime() - self.wait_timer > self.wait_timeout) and not self.processing
    
    def display_menu(self):
        lcd.display_message(line1=storeName, line3=f'Insert Coin: {self.credit}', line4=Util.translateCreditTime(self.credit * multiplier))

    def callback(self, pin):
        self.reset_timer = Util.getCurrentTime()
    
        if pin == PINS.COIN and self.debounce():
            self.wait_for(1) # to prevent user from pressing the button while incrementing
            self.credit += 1
            self.display_menu()
            self.debounce_timer = Util.getCurrentTime()

        elif pin == PINS.BUTTON and self.isready():
            self.processing = True # set processing to True to avoid multiple inputs from button

            if self.credit <= 0:
                self.display_menu()
            else:
                self.new_voucher = None
                self.create_voucher()

                if self.new_voucher is not None:
                    self.credit = 0
                    lcd.display_message(line1='Voucher Code:', line2=str(self.new_voucher['code']), line4='Thank you!')
                    self.wait_for(3)
                else:
                    lcd.display_message(line1='Voucher failed', line2='Please try again')
                    self.wait_for(1)

            self.processing = False # set processing to False

    def create_voucher(self):
        lcd.display_message(line1='Creating Voucher', line2='Please wait')
        try:
            uniqueId = Util.createUniqueId(self.credit, multiplier)
            
            voucher_config['name'] = uniqueId
            voucher_config['unitPrice'] = self.credit
            voucher_config['duration'] = self.credit * multiplier
            voucher_config['expirationTime'] = Util.getCurrentTime() + (DAYS_IN_SECONDS * 1000)
            
            response = requests.post(url, json=voucher_config)

            if response.status_code == 200:
                self.new_voucher = response.json()

        except Exception:
            print(traceback.format_exc())

coinSlot = CoinSlot()
coinSlot.run()