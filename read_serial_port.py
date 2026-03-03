""" Script to read serial data and print to console only. """

import serial
import time

def main():
	port = 'COM4'  # Change as needed
	baudrate = 115200
	try:
		ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
		print(f"Connected to {ser.port}. Press Ctrl+C to stop.")
	except Exception as e:
		print(f"Error: Could not open serial port {port}: {e}")
		return

	try:
		while True:
			try:
				raw_line = ser.readline()
				line = raw_line.decode('utf-8', errors='replace').strip()
				if line:
					timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
					print(f"{line}")
			except KeyboardInterrupt:
				print("\nStopped by user.")
				break
			except Exception as e:
				print(f"Error: {e}")
	finally:
		ser.close()
		print("Serial port closed.")

if __name__ == "__main__":
	main()
