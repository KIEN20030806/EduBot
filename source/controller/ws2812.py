# ws2812.py
import neopixel
from machine import Pin
import time

class LEDRing:
    def __init__(self, pin=10, num_leds=16):
        """
        Khởi tạo vòng LED WS2812.
        :param pin: GPIO kết nối tín hiệu DIN của LED
        :param num_leds: số lượng LED trong vòng
        """
        self.num_leds = num_leds
        self.pin = Pin(pin, Pin.OUT)
        self.ring = neopixel.NeoPixel(self.pin, self.num_leds)
        self.clear()

    def clear(self):
        for i in range(self.num_leds):
            self.ring[i] = (0, 0, 0)
        self.ring.write()

    def fill(self, color):
        for i in range(self.num_leds):
            self.ring[i] = color
        self.ring.write()

    def set_color(self, index, color):
        if 0 <= index < self.num_leds:
            self.ring[index] = color
            self.ring.write()

    def show_pattern(self, pattern, delay=100):
        """
        Hiển thị một mẫu list màu (list các tuple RGB)
        """
        self.fill((0,0,0))
        for i in range(min(self.num_leds, len(pattern))):
            self.ring[i] = pattern[i]
        self.ring.write()
        time.sleep_ms(delay)

    def flash(self, color, times=3, delay=200):
        """
        Nhấp nháy toàn bộ vòng với màu đã chọn
        """
        for _ in range(times):
            self.fill(color)
            time.sleep_ms(delay)
            self.clear()
            time.sleep_ms(delay)

leds = LEDRing(pin=16, num_leds= 9)
