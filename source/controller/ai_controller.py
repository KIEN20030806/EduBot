import network, socket, time, ujson, os
from machine import Pin, I2S, reset
import espnow
import urequests

class ESP32MicStreamer:
    def __init__(self):
        self.STATE = "CONFIG"
        self.CRED_FILE = "wifi.json"
        self.SSID_AP = "ESP32_Config"

        # I2S setup
        self.SAMPLE_RATE = 8000
        self.BUFFER_SIZE = 4096
        self.MIC_BCK = Pin(21)
        self.MIC_WS = Pin(14)
        self.MIC_SD = Pin(47)
        self.audio_in = I2S(
            0, sck=self.MIC_BCK, ws=self.MIC_WS, sd=self.MIC_SD,
            mode=I2S.RX, bits=16, format=I2S.MONO,
            rate=self.SAMPLE_RATE, ibuf=self.BUFFER_SIZE
        )

        self.button = Pin(12, Pin.IN, Pin.PULL_UP)
        self.SERVER_IP = "192.168.1.60"
        self.SERVER_PORT = 8000

        self.robot_mac = b'\xcc\xba\x97\n\xc1\xe8'  # Thay bằng MAC thật

        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

        self.e = espnow.ESPNow()
        self.e.active(True)
        self.e.add_peer(self.robot_mac)

    def start_ap_mode(self):
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=self.SSID_AP, authmode=network.AUTH_OPEN)
        print(f"📶 Đang phát WiFi: {self.SSID_AP}")
        self.start_config_server()
        
    def url_decode(self, s):
        s = s.replace('+', ' ')
        res = ''
        i = 0
        while i < len(s):
            if s[i] == '%' and i + 2 < len(s):
                try:
                    res += chr(int(s[i+1:i+3], 16))
                    i += 3
                except:
                    res += '%'
                    i += 1
            else:
                res += s[i]
                i += 1
        return res


    def start_config_server(self):
        import network
        wlan_scan = network.WLAN(network.STA_IF)
        wlan_scan.active(True)
        networks = wlan_scan.scan()  # Trả về list (ssid, bssid, channel, RSSI, security, hidden)

        options = ""
        for net in networks:
            ssid = net[0].decode()
            options += f'<option value="{ssid}">{ssid}</option>'

        html_form = f"""
        <html>
        <meta charset="UTF-8">
        <body>
        <h2>WiFi Cấu hình</h2>
        <form action="/" method="post">
            SSID:
            <select name="ssid">
                {options}
            </select><br>
            Password: <input name="password"><br>
            <input type="submit" value="Kết nối">
        </form>
        </body>
        </html>
        """

        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.bind(addr)
        s.listen(1)
        print("🌐 Server cấu hình đang chạy trên http://192.168.4.1")

        while True:
            cl, addr = s.accept()
            data = cl.recv(1024).decode()
            if "POST" in data:
                try:
                    body = data.split("\r\n\r\n")[1]
                    params = {}
                    for pair in body.split("&"):
                        k, v = pair.split("=")
                        params[k] = v

                    ssid = self.url_decode(params.get("ssid", ""))
                    password = self.url_decode(params.get("password", ""))
                    creds = {"ssid": ssid, "password": password}
                    with open(self.CRED_FILE, "w") as f:
                        f.write(ujson.dumps(creds))

                    cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n")
                    cl.send("<h3>✔️ Lưu thành công! Đang kết nối lại...</h3>")
                    cl.close()
                    time.sleep(2)
                    reset()
                except Exception as e:
                    cl.send("HTTP/1.1 500 Internal Server Error; charset=utf-8\r\n\r\n")
                    cl.send(f"<h3>Lỗi: {str(e)}</h3>")
                    cl.close()
            else:
                cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                cl.send(html_form)
                cl.close()


    def connect_wifi_from_file(self):
        try:
            with open(self.CRED_FILE, "r") as f:
                creds = ujson.loads(f.read())
            ssid = creds["ssid"]
            password = creds["password"]

            self.wlan.connect(ssid, password)
            print(f"📡 Đang kết nối tới {ssid}...")
            for _ in range(15):
                if self.wlan.isconnected():
                    print("✅ Kết nối thành công:", self.wlan.ifconfig())
                    return True
                time.sleep(1)
            print("❌ Kết nối thất bại.")
            return False
        except:
            print("⚠️ Không tìm thấy file wifi.json")
            return False

    def send_config_to_slave(self, max_retries=5):
        if not self.wlan.isconnected():
            print("⚠️ Chưa kết nối WiFi, không gửi được")
            return

        with open(self.CRED_FILE, "r") as f:
            creds = ujson.loads(f.read())

        msg = ujson.dumps({
            "ssid": creds["ssid"],
            "password": creds["password"]
        })
        print(f"🔵 Gửi config đến ESP phụ qua ESP-NOW: {msg}")

        for attempt in range(1, max_retries + 1):
            print(f"📤 Đang gửi lần {attempt}...")
            try:
                self.e.send(self.robot_mac, msg.encode())
            except Exception as ex:
                print("❌ Lỗi khi gửi:", ex)
                continue

            start = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start) < 3000:
                host, recv = self.e.irecv(True)
                if recv:
                    if recv == b"ACK":
                        print("✅ ESP phụ đã nhận config")
                        return
                    else:
                        print("❓ ESP phụ phản hồi:", recv)
                        return
            print("⚠️ Không nhận được phản hồi")

        print("❌ Gửi thất bại sau nhiều lần")
        

    def stream_audio(self):
        print("Bắt đầu stream audio")
        url_chunk = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/send_audio_chunk"
        url_end = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/end_audio"
        headers = {'Content-Type': 'application/octet-stream'}

        chunk_buffer = bytearray()

        try:
            while self.button.value() == 0:  # giữ nút
                buf = bytearray(self.BUFFER_SIZE)
                num_bytes = self.audio_in.readinto(buf)
                if num_bytes > 0:
                    chunk_buffer += buf[:num_bytes]

                    # Khi buffer đủ lớn (vd: 16000 bytes ~2s 8kHz 16bit)
                    if len(chunk_buffer) >= 32000:
                        try:
                            response = urequests.post(url_chunk, data=chunk_buffer, headers=headers)
                            response.close()
                            print(f"✅ Đã gửi {len(chunk_buffer)} bytes audio")
                        except Exception as e:
                            print("❌ Gửi dữ liệu thất bại:", e)
                        chunk_buffer = bytearray()  # reset buffer

            # Nút nhả ra, gửi phần còn lại (nếu có) trước khi kết thúc
            if len(chunk_buffer) > 0:
                try:
                    response = urequests.post(url_chunk, data=chunk_buffer, headers=headers)
                    response.close()
                    print(f"✅ Đã gửi {len(chunk_buffer)} bytes audio cuối")
                except Exception as e:
                    print("❌ Gửi dữ liệu thất bại phần cuối:", e)

            # Gửi tín hiệu báo đã kết thúc gửi audio
            try:
                response = urequests.post(url_end)
                response.close()
                print("🛑 Đã gửi tín hiệu kết thúc gửi audio")
            except Exception as e:
                print("❌ Gửi tín hiệu kết thúc thất bại:", e)

            print("🛑 Kết thúc stream audio")

        except KeyboardInterrupt:
            print("🛑 Dừng stream do KeyboardInterrupt")

            
    def run(self):
        if self.CRED_FILE in os.listdir():
            if self.connect_wifi_from_file():
                #self.send_config_to_slave()
                self.STATE = "STREAM"
            else:
                self.STATE = "CONFIG"
        else:
            self.STATE = "CONFIG"
        if self.STATE == "CONFIG":
            self.start_ap_mode()
        elif self.STATE == "STREAM":
           while True:
                if self.button.value() == 0: # Nút được nhấn (kéo xuống đất)
                    print("▶️ Nút được nhấn, bắt đầu stream.")
                    self.stream_audio()
                    time.sleep(1) # Chờ một chút sau khi dừng stream để tránh nhấn nhả liên tục


# === CHẠY ===
app = ESP32MicStreamer()
app.run()