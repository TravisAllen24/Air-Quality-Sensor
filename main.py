""" Main python code that collects data from the serial port and logs it to a text file. """

import serial
import time
import os

def main():
    """ Main function that collects data from the serial port and logs it to a text file. """
    # Prompt user for a file name
    file_name = input("Enter the log file name (leave blank for default 'data_log.txt'): ").strip()
    if not file_name:
        file_name = "data_log.txt"

    # Ensure the 'logs' directory exists
    os.makedirs('logs', exist_ok=True)

    # Generate a unique file name if the default already exists
    base_name = "data_log"
    extension = ".txt"
    counter = 0
    while os.path.exists(os.path.join('logs', file_name)):
        counter += 1
        file_name = f"{base_name}({counter}){extension}"

    file_name = os.path.join('logs', file_name)

    # Debugging: Print the full path of the log file
    print(f"Log file path: {file_name}")


    # Open the serial port
    try:
        ser = serial.Serial('COM9', baudrate=115200, timeout=1)
        print(f"Connected to {ser.port}")
    except Exception as e:
        print(f"Error: Could not open serial port COM9: {e}")
        return

    # Open the log file
    try:
        with open(file_name, 'a', encoding='utf-8', errors='replace') as log_file:
            print(f"Logging data to {file_name}... Press Ctrl+C to stop.")

            while True:
                try:
                    # Read a line from the serial port
                    raw_line = ser.readline()
                    try:
                        line = raw_line.decode('utf-8', errors='replace').strip()
                    except Exception as decode_error:
                        print(f"Decoding error: {decode_error}")
                        line = raw_line  # Log raw data for debugging

                    if line:
                        # Log the data with a timestamp
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        log_file.write(f"{timestamp} - {line}\n")
                        log_file.flush()

                        # Print to console for feedback
                        print(f"{timestamp} - {line}")
                except KeyboardInterrupt:
                    print("\nLogging stopped by user.")
                    break
                except Exception as e:
                    print(f"Error: {e}")
    except IOError as e:
        print(f"Error: Could not open file {file_name} for writing: {e}")
    finally:
        ser.close()
        print("Serial port closed.")

if __name__ == "__main__":
    main()