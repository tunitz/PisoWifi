from enum import Enum
import i2clcd

# LCD Variables
I2C_BUS = 0
I2C_ADD = 0x27
LCD_WIDTH = 20

class BACKLIGHT(Enum):
    OFF = 0
    ON = 1

class STATE(Enum):
    CLEAR = 0
    MENU = 1
    PROCESSING = 2
    SUCCESS = 3
    FAILED = 4

class LCD():
    # LCD Line Message Variables
    line1 = None
    line2 = None
    line3 = None
    line4 = None

    BACKLIGHT_STATE = BACKLIGHT.ON
    SCREEN_STATE = STATE.CLEAR

    def __init__(self) -> None:
        self.LCD = i2clcd.i2clcd(i2c_bus=I2C_BUS, i2c_addr=I2C_ADD, lcd_width=LCD_WIDTH)
        self.LCD.init()

    def clear_screen(self) -> None:
        if self.SCREEN_STATE is not STATE.CLEAR:
            self.LCD.clear()
            self.SCREEN_STATE = STATE.CLEAR

    def backlight_off(self) -> None:
        if self.BACKLIGHT_STATE is not BACKLIGHT.OFF:
            self.BACKLIGHT_STATE = BACKLIGHT.OFF
            self.LCD.set_backlight(self.BACKLIGHT_STATE)

    def backlight_on(self) -> None:
        if self.BACKLIGHT_STATE is not BACKLIGHT.ON:
            self.BACKLIGHT_STATE = BACKLIGHT.ON
            LCD.set_backlight(self.BACKLIGHT_STATE)

    def display_message(self, line1 = '', line2 = '', line3 = '', line4 = '') -> None:
        if self.line1 != line1:
            self.line1 = line1
            LCD.print_line(text = self.line1, line = 0)
            
        if self.line2 != line2:
            self.line2 = line2
            LCD.print_line(text = self.line2, line = 1)

        if self.line3 != line3:
            self.line3 = line3
            LCD.print_line(text = self.line3, line = 2)

        if self.line4 != line4:
            self.line4 = line4
            LCD.print_line(text = self.line4, line = 3)