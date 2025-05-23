# linecode.py (chân cố định analog)
from machine import ADC, Pin
import time

class LineCodeScanner:
    def __init__(self):
        # Chỉnh sửa chân ADC tùy bo mạch (ESP8266 chỉ có 1 ADC - pin A0)
        self.sensor_pins = [4, 5, 6, 7, 15, 8, 3, 9]  # ESP32 ADC pins
        self.sensors = [ADC(Pin(pin)) for pin in self.sensor_pins]

        # Cấu hình ADC (ESP32)
        for adc in self.sensors:
            adc.atten(ADC.ATTN_11DB)  # Đọc từ 0 đến 3.3V
            adc.width(ADC.WIDTH_12BIT)  # Độ phân giải 10-bit: 0–1023

    def read(self):
        """
        Đọc giá trị analog từ 8 cảm biến line và trả về list giá trị ADC (0–1023)
        """
        return [sensor.read() for sensor in self.sensors]

    def read_binary(self, threshold=2500):
        """
        Chuyển giá trị ADC sang bit 0/1 dựa vào ngưỡng `threshold`
        """
        return [0 if sensor.read() > threshold else 1 for sensor in self.sensors]

    def decode(self, bits):
        """
        Giải mã list 8 bit thành chuỗi lệnh di chuyển
        """
        binary = ''.join(str(b) for b in bits)
        command_map = {
            '00000000': '0',
            '00000001': '1',
            '00000010': '2',
            '00000011': '3',
            '00000100': '4',
            '00000101': 'XOA'
        }
        return command_map.get(binary, 'UNKNOWN')  # Trả về str, không phải bytes


    def decode_mode(self, bits):
        binary = ''.join(str(b) for b in bits)
        try:
            return int(binary, 2)
        except:
            return 0

    def decode_uid(self, bits):
        return ''.join(str(b) for b in bits)

    def check_mode_change(self):
        bits = self.read_binary()
        binary = ''.join(str(b) for b in bits)
        return binary == '11111111'

# Test
scanner = LineCodeScanner()