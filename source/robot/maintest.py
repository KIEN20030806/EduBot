# === ROBOT (ESP32-S3) ===
# main.py on robot
import time
import espnow
import network
from robot import *
from rfid import *
from ai_robot import *
#from matrixeye import *
#from line import LineSensor
#from vatcan import VatCan
# Init
wifi = network.WLAN(network.STA_IF)
wifi.active(True)

esp = espnow.ESPNow()
esp.active(True)
controller_mac = b'\xcc\xba\x97\n\x8ap'  # replace with actual MAC

try:
    esp.add_peer(controller_mac)
except OSError as e:
    if e.args[0] == -12395:
        print("Peer already exists, skipping...")
    else:
        raise
    
mode = 0

def mode_0_laptrinh():
    print("[MODE 0] Nhận và thực thi lệnh lập trình...")
    command_list = []
    while True:
        peer, msg = esp.recv()
        if msg:
            if msg == b'END':
                print("Hoàn tất nhận lệnh:", command_list)
                for cmd in command_list:
                    print("Thực thi lệnh:", cmd)
                    robot.move(cmd)
                    time.sleep(1)
                command_list = []
                uid = rfid.scan_card()
                if uid:
                    audio.play_file_by_uid(uid)
            
            try:
                cmd = msg.decode()
            
                if cmd == '0':
                    print("Chuyển sang mode 0 (lập trình)")
                    mode_0_laptrinh()
                elif cmd == '1':
                    print("Chuyển sang mode 1 (điều khiển)")
                    mode_1_dieukhien()
                    return  # dừng mode 0 sau khi chuyển
                elif cmd == '2':
                    print("Chuyển sang mode 2 (học)")
                    mode_2_hoc()
                    return
                elif cmd == '3':
                    print("Chuyển sang mode 3 (AI)")
                    mode_3_ai()
                    return
                elif cmd == '4':
                    print("Chuyển sang mode 4 (khác)")
                    mode_4_khac()
                    return

                # Lưu lệnh điều khiển
                command_list.append(cmd)
                
            except Exception as e:
                print("Lỗi decode lệnh:", cmd, e)
                continue
        
def mode_1_dieukhien():
    print("[MODE 1] Điều khiển trực tiếp")
    while True:
        peer, msg = esp.recv()
        if msg:
            try:
                cmd = msg.decode()

                # Ưu tiên xử lý lệnh điều khiển trước
                if cmd in ['f', 'b', 'l', 'r', 's']:
                    print("Điều khiển robot với lệnh:", cmd)
                    robot.control(cmd)
                    continue  # quay lại vòng lặp, không kiểm tra lệnh chuyển mode nữa

                if cmd == '0':
                    print("Chuyển sang mode 0 (lập trình)")
                    mode_0_laptrinh()
                elif cmd == '1':
                    print("Chuyển sang mode 1 (điều khiển)")
                    mode_1_dieukhien()
                    return  # dừng mode 0 sau khi chuyển
                elif cmd == '2':
                    print("Chuyển sang mode 2 (học)")
                    mode_2_hoc()
                    return
                elif cmd == '3':
                    print("Chuyển sang mode 3 (AI)")
                    mode_3_ai()
                    return
                elif cmd == '4':
                    print("Chuyển sang mode 4 (khác)")
                    mode_4_khac()
                    return
            except Exception as e:
                print("Lỗi decode file id học:", msg, e)

def mode_2_hoc():
    print("[MODE 2] Chế độ học")
    while True:
        peer, msg = esp.recv()
        if msg:
            try:
                cmd = msg.decode()

                if cmd == '0':
                    print("Chuyển sang mode 0 (lập trình)")
                    mode_0_laptrinh()
                elif cmd == '1':
                    print("Chuyển sang mode 1 (điều khiển)")
                    mode_1_dieukhien()
                    return  # dừng mode 0 sau khi chuyển
                elif cmd == '2':
                    print("Chuyển sang mode 2 (học)")
                    mode_2_hoc()
                    return
                elif cmd == '3':
                    print("Chuyển sang mode 3 (AI)")
                    mode_3_ai()
                    return
                elif cmd == '4':
                    print("Chuyển sang mode 4 (khác)")
                    mode_4_khac()
                    return
                # Nếu không phải lệnh chuyển mode, xử lý học âm thanh
                print("Phát âm thanh với ID:", cmd)
                audio.play_file_by_uid(cmd)

            except Exception as e:
                print("Lỗi decode file id học:", msg, e)


def mode_3_ai():
    print("[MODE 3] Chế độ AI")
    app.connect()
    while True:
        peer, msg = esp.recv()
        if msg:
            try:
                cmd = msg.decode()
  
                if cmd == '0':
                    print("Chuyển sang mode 0 (lập trình)")
                    mode_0_laptrinh()
                elif cmd == '1':
                    print("Chuyển sang mode 1 (điều khiển)")
                    mode_1_dieukhien()
                    return  # dừng mode 0 sau khi chuyển
                elif cmd == '2':
                    print("Chuyển sang mode 2 (học)")
                    mode_2_hoc()
                    return
                elif cmd == '3':
                    print("Chuyển sang mode 3 (AI)")
                    mode_3_ai()
                    return
                elif cmd == '4':
                    print("Chuyển sang mode 4 (khác)")
                    mode_4_khac()
                    return
                app.listen_for_config()

            except Exception as e:
                print("Lỗi:", msg, e)

def mode_4_khac():
    print("[MODE 4] Chế độ khác")
    peer, msg = esp.recv()
    if msg:
        try:
            cmd = msg.decode()
            if cmd == '0':
                print("Chuyển sang mode 0 (lập trình)")
                mode_0_laptrinh()
            elif cmd == '1':
                print("Chuyển sang mode 1 (điều khiển)")
                mode_1_dieukhien()
                return  # dừng mode 0 sau khi chuyển
            elif cmd == '2':
                print("Chuyển sang mode 2 (học)")
                mode_2_hoc()
                return
            elif cmd == '3':
                print("Chuyển sang mode 3 (AI)")
                mode_3_ai()
                return
            elif cmd == '4':
                print("Chuyển sang mode 4 (khác)")
                mode_4_khac()
                return
            if cmd == 'LINE':
                print("Chế độ theo dõi vạch")
                while not vatcan.detect():
                    robot.follow_line(line_sensor)
                    uid = rfid.scan_card()
                    if uid:
                        audio.play_file_by_uid(uid)

            elif cmd == 'AVOID':
                print("Chế độ tránh vật cản")
                while True:
                    if vatcan.detect():
                        robot.avoid()

            elif cmd == 'DANCE':
                print("Chế độ nhảy múa")
                audio.play_random()
                robot.dance()
                
        except Exception as e:
            print("Lỗi decode lệnh:", cmd, e)

# === MAIN LOOP ===
while True:
    print("Waiting for mode...")
    peer, msg = esp.recv()
    if msg:
        try:
            cmd = msg.decode() if isinstance(msg, bytes) else msg

            if cmd == '0':
                mode_0_laptrinh()
            elif cmd == '1':
                mode_1_dieukhien()
            elif cmd == '2':
                mode_2_hoc()
            elif cmd == '3':
                mode_3_ai()
            elif cmd == '4':
                mode_4_khac()
            else:
                print("Lệnh không hợp lệ, bỏ qua:", cmd)

        except Exception as e:
            print("Lỗi khi xử lý lệnh:", cmd, e)
