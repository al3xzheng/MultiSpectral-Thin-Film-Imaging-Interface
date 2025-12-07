import serial
import time

port = "COM4"
baud = 115200

currentTime = 0

class Timer():
    

# with serial.Serial(port, baud, timeout=1) as ser:
#     started = False

#     while True:
#         line = ser.readline().decode(errors="ignore").strip()
#         if not line:
#             continue

#         if "PRINT_START" in line and not started:
#             print("Timer started")
#             start_time = time.time()
#             started = True

#         if started:
#             currentTime = time.time() - start_time
#             # print(f"{time.time() - start_time:.1f} seconds passed", end="\r")

while (True):
    currentTime = time.time()
