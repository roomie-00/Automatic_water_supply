import I2C_LCD_driver
from time import*

mylcd = I2C_LCD_driver.lcd()
mylcd.lcd_display_string("push the button", 1)
mylcd.lcd_display_string("and select volume" ,  2)