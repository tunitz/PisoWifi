from omada import Omada
import utilities as Util
import OPi.GPIO as GPIO
import traceback
import i2clcd
import json
import time

I2C_BUS = 0
I2C_ADD = 0x27
LCD_WIDTH = 20

SCREEN_MESSAGE_STATE = 0
CLEAR = 0
MENU = 1

SCREEN_STATE = 0
OFF = 0
ON = 1

def lcd_init():
    global lcd
    lcd = i2clcd.i2clcd(i2c_bus=I2C_BUS, i2c_addr=I2C_ADD, lcd_width=LCD_WIDTH)
    lcd.init()

def display_menu(coin_credit, multiplier):
    global SCREEN_MESSAGE_STATE
    if SCREEN_MESSAGE_STATE is not MENU:
        clear_screen()
        SCREEN_MESSAGE_STATE = MENU

    display_message(line1='MottPott Piso WiFi', line3=f'Insert Coin: {coin_credit}', line4=Util.translateCreditTime(coin_credit * multiplier))

def display_message(line1=None, line2=None, line3=None, line4=None):
    if line1 is not None:
        lcd.print_line(line1, line=0)
    if line2 is not None:
        lcd.print_line(line2, line=1)
    if line3 is not None:
        lcd.print_line(line3, line=2)
    if line4 is not None:
        lcd.print_line(line4, line=3)

def clear_screen():
    global SCREEN_MESSAGE_STATE
    if SCREEN_MESSAGE_STATE is not CLEAR:
        SCREEN_MESSAGE_STATE = CLEAR
        lcd.clear()

def turn_off_display():
    global SCREEN_STATE, SCREEN_MESSAGE_STATE
    clear_screen()
    SCREEN_STATE = OFF
    lcd.set_backlight(OFF)

def turn_on_display():
    global SCREEN_STATE
    SCREEN_STATE = ON
    lcd.set_backlight(ON)

class CoinSlot:
    coin_credit = 0
    is_processing = False

    wait_timer = 0
    wait_timeout = 5 # seconds

    sleep_timer = 0
    sleep_timeout = 5
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
        self.sleep_timer = time.time()
        self.new_voucher = None
        self.voucher_settings['rateLimitId'] = None

        display_menu(self.coin_credit, self.voucher_settings['multiplier'])

    def __loop__(self):
        try:
            while True:
                self.lcd_sleep()
                time.sleep(0.01)
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
        shouldSleep = time.time() - self.sleep_timer > self.sleep_timeout
        if self.sleep_timer > 0:
            if SCREEN_STATE is ON and shouldSleep:
                self.sleep_timer = 0
                turn_off_display()
            elif SCREEN_STATE is OFF:
                turn_on_display()
                display_menu(self.coin_credit, self.voucher_settings['multiplier'])

    def toggle_processing(self):
        self.is_processing = not self.is_processing
        if self.is_processing:
            GPIO.output(self.coin_set_pin, 0) # turn off coin slot
        else:
            GPIO.output(self.coin_set_pin, 1) # turn on coin slot

    def input_callback(self, channel):
        global IN_MENU

        # Reset display sleep timer
        self.sleep_timer = time.time()

        # Coin slot input
        if channel == self.coin_pin:
            self.coin_credit += 1
            display_menu(self.coin_credit, self.voucher_settings['multiplier'])

        # Button input
        elif channel == self.button_pin:
            if self.is_processing is False and self.done_waiting():
                if self.coin_credit <= 0:
                    display_menu(self.coin_credit, self.voucher_settings['multiplier'])
                elif self.coin_credit >  0 and self.is_processing == False:
                    self.toggle_processing()
                    clear_screen()
                    display_message(line1='Creating voucher.', line2='Please wait.')
                    IN_MENU = 0
                    self.create_voucher()

                    if self.new_voucher is not None:
                        self.coin_credit = 0
                        clear_screen()
                        display_message(line1='Voucher Code:', line2=str(self.new_voucher['code']), line4='Thank you!')
                        IN_MENU = 0
                        self.new_voucher = None
                        self.wait_for(5)
                    else:
                        clear_screen()
                        display_message(line1='Voucher failed', line2='Press the button', line3='to try again')
                        IN_MENU = 0
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



lcd_init()
display_message(line1='MottPott Piso WiFi', line3='Please wait!', line4='System is starting')

Util.checkOmada()

coinSlot = CoinSlot()
coinSlot.__loop__()