from omada import Omada
import utilities as Util
import OPi.GPIO as GPIO
import traceback
import json
import time
import lcd

class CoinSlot:
    coin_credit = 0
    is_processing = False

    wait_timer = 0
    wait_timeout = 5 # seconds

    lcd_timer = 0
    lcd_timeout = 120
    lcd_state = False

    coin_pin = 11
    coin_set_pin = 13
    button_pin = 15

    def __init__(self):
        # Setup the GPIO mode and input pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.coin_pin, GPIO.IN)
        GPIO.setup(self.coin_set_pin, GPIO.OUT)
        GPIO.setup(self.button_pin, GPIO.IN)

        GPIO.add_event_detect(self.coin_pin , GPIO.FALLING, callback=self.input_callback)
        GPIO.add_event_detect(self.button_pin, GPIO.RISING, callback=self.input_callback)

        GPIO.output(self.coin_set_pin, 1) # turn on coin slot

        self.voucher_settings = json.load(open('voucher_settings.json'))
        self.omada = Omada()
        self.lcd_timer = time.time()
        self.new_voucher = None
        self.voucher_settings['rateLimitId'] = None

        lcd.display_message(line1='MottPott Piso WiFi', line3=f'Insert Coin: {self.coin_credit}', line4=Util.translateCreditTime(self.coin_credit * self.voucher_settings['multiplier']))


    def __loop__(self):
        try:
            while True:
                self.lcd_sleep()
                time.sleep(1)
        except Exception:
            print(traceback.format_exc())
        finally:
            # Clean up the GPIO settings
            GPIO.cleanup()

    def getPortals(self):
        for portal in self.omada.getAllPortals():
            self.voucher_settings['portals'].append(portal['id'])

    def getProfiles(self):
        for profile in self.omada.getRateLimitProfiles():
            if profile['name'] == self.voucher_settings['rateLimitName']:
                self.voucher_settings['rateLimitId'] = profile['id']

    def wait_for(self, seconds):
        self.wait_timer = time.time()
        self.wait_timeout = seconds
    
    def done_waiting(self):
        isDone = self.wait_timer == 0 or time.time() - self.wait_timer > self.wait_timeout

        if isDone:
            self.wait_timer = 0
        
        return isDone
    
    def lcd_sleep(self):
        shouldSleep = time.time() - self.lcd_timer > self.lcd_timeout
        if self.lcd_state is not shouldSleep:
            self.lcd_state = shouldSleep
            if shouldSleep:
                lcd.display_off()
                lcd.display_message(line1='MottPott Piso WiFi', line3=f'Insert Coin: {self.coin_credit}', line4=Util.translateCreditTime(self.coin_credit * self.voucher_settings['multiplier']))
            else:
                lcd.display_on()

    def toggle_processing(self):
        self.is_processing = not self.is_processing
        if self.is_processing:
            GPIO.output(self.coin_set_pin, 0) # turn off coin slot
        else:
            GPIO.output(self.coin_set_pin, 1) # turn on coin slot

    def input_callback(self, channel):
        # Reset display sleep timer
        self.lcd_timer = time.time()

        # Coin slot input
        if channel == self.coin_pin:
            self.coin_credit += 1
            lcd.display_message(line1='MottPott Piso WiFi', line3=f'Insert Coin: {self.coin_credit}', line4=Util.translateCreditTime(self.coin_credit * self.voucher_settings['multiplier']))

        # Button input
        elif channel == self.button_pin:
            if self.is_processing is False and self.done_waiting():
                if self.coin_credit <= 0:
                    lcd.display_message(line1='MottPott Piso WiFi', line3=f'Insert Coin: {self.coin_credit}', line4=Util.translateCreditTime(self.coin_credit * self.voucher_settings['multiplier']))
                elif self.coin_credit >  0 and self.is_processing == False:
                    self.toggle_processing()

                    lcd.display_message(line1='Creating voucher.', line2='Please wait.')

                    self.create_voucher()

                    if self.new_voucher is not None:
                        self.coin_credit = 0
                        lcd.display_message(line1='Voucher Code:', line2=str(self.new_voucher['code']), line4='Thank you!')
                        self.new_voucher = None
                        self.wait_for(5)
                    else:
                        lcd.display_message(line1='Voucher failed', line2='Press the button', line3='to try again')
                        self.wait_for(3)
                    
                    self.toggle_processing()

    def create_voucher(self):
        try:
            result = self.omada.login()

            if result is not None:
                uniqueId = Util.createUniqueId(self.coin_credit, self.voucher_settings['multiplier'])

                if len(self.voucher_settings['portals']) == 0:
                    self.getPortals()

                if self.voucher_settings['rateLimitId'] is None:
                    self.getProfiles()

                self.voucher_settings['note'] = uniqueId

                self.omada.createVoucher(json=self.voucher_settings)
                for voucher in self.omada.getVoucher(voucherNote = uniqueId)['data']: # this will return only 1
                    if voucher['note'] == uniqueId:
                        self.new_voucher = voucher

                self.omada.logout()
        except Exception:
            print(traceback.format_exc())

lcd.init()
lcd.display_message(line1='MottPott Piso WiFi', line3='Please wait!', line4='System is starting')

Util.checkOmada()

coinSlot = CoinSlot()
coinSlot.__loop__()