# receive data from /dev/ttyV1 and print it to the console
import serial
ser = serial.Serial('/dev/ttyV0', 115200)
while True:
    line = ser.readline()
    print(line.decode('utf-8').rstrip())

