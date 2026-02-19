# Air-Quality-Sensor
A tabletop mechatronics project using an embedded microcontroller and sensors that collects temperature, humidity, VOC, CO2, and PM data for evaluating air quality.

## Features
- **CO2 Monitoring**: Uses the SCD4x sensor to measure carbon dioxide levels.
- **Temperature and Humidity**: Measures ambient temperature and relative humidity with the SHT4x sensor.
- **VOC Detection**: Detects volatile organic compounds using the SGP40 sensor.
- **Particulate Matter (PM) Monitoring**: Measures PM1.0, PM2.5, and PM10 levels using the PMSA003I sensor.
- **LED Indicator**: Displays air quality status using a NeoPixel LED.
- **Air Quality Score**: Calculates an overall air quality score based on sensor data.

## How It Works
1. **Sensor Initialization**: The microcontroller initializes all connected sensors via the I2C bus.
2. **Data Collection**: Periodically collects data from the sensors, including CO2, temperature, humidity, VOC, and PM levels.
3. **Data Processing**: Formats and processes the collected data to calculate an air quality score.
4. **LED Feedback**: The NeoPixel LED changes color based on the air quality score to provide a visual indication of air quality.
5. **Serial Output**: Prints sensor readings and air quality information to the serial console for monitoring and debugging.

## File Structure
- `main.py`: Entry point for the microcontroller code. Handles sensor data collection and processing.
- `led.py`: Contains the `LED` class for controlling the NeoPixel LED.
- `utils.py`: Utility functions for formatting values and calculating the air quality score.
- `logs/data_log.txt`: Stores logged sensor data for analysis.

## Requirements
- **Hardware**:
  - Microcontroller with CircuitPython support
  - SCD4x CO2 sensor
  - SHT4x temperature and humidity sensor
  - SGP40 VOC sensor
  - PMSA003I particulate matter sensor
  - NeoPixel LED
- **Software**:
  - CircuitPython libraries for the sensors

## Setup
1. Clone the repository to your local machine.
2. Copy the `microcontroller_code` folder to your CircuitPython device.
3. Install the required CircuitPython libraries in the `lib` folder of your device.
4. Connect the sensors and NeoPixel LED to the microcontroller as per the wiring diagram.
5. Open a serial monitor to view the output.

## Usage
- Power on the device to start collecting air quality data.
- Observe the LED for a quick visual indication of air quality.
- Use the serial monitor to view detailed sensor readings and air quality scores.

## Future Improvements
- Add support for additional sensors.
- Implement an external battery
- Implement data logging to an SD card.
- Implement a Real Time Clock
