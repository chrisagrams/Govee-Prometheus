import asyncio
import sys
from prometheus_client import start_http_server, Gauge
from bleak import BleakScanner

device_name = sys.argv[1]   # Take device name as argument to look for

# Define Prometheus metrics
temperature_gauge = Gauge('device_temperature', 'Temperature of the device', ['device_name'])
humidity_gauge = Gauge('device_humidity', 'Humidity of the device', ['device_name'])
battery_gauge = Gauge('device_battery', 'Battery level of the device', ['device_name'])

class DataDecoder:
    def __init__(self, device_name, manufacturer_data):
        self.device_name = device_name
        self.bdata = manufacturer_data[1]
        self.hex_data = self.bdata.hex()
        self.temperature = self.decode_temperature()
        self.humidity = self.decode_humidity()
        self.battery = self.decode_battery()

    def decode_temperature(self):
        start_byte, end_byte = 4, 10
        raw_temp = int(self.hex_data[start_byte:end_byte], 16)
        temp = float(format(raw_temp / 10000, '.2f'))
        temperature_gauge.labels(device_name=self.device_name).set(temp)
        return temp

    def decode_humidity(self):
        start_byte, end_byte = 4, 10
        raw_humidity = int(self.hex_data[start_byte:end_byte], 16)
        humidity = float(format((raw_humidity % 1000) / 10, '.2f'))
        humidity_gauge.labels(device_name=self.device_name).set(humidity)
        return humidity

    def decode_battery(self):
        end_byte = 10
        battery_level = int(self.hex_data[end_byte:end_byte + 2], 16)
        battery_gauge.labels(device_name=self.device_name).set(battery_level)
        return battery_level

    def __str__(self):
        return (f"Temperature: {self.temperature}°C, "
                f"Humidity: {self.humidity}%, "
                f"Battery: {self.battery}%")


async def main():
    start_http_server(8000)
    print(f"Prometheus metrics server running on http://localhost:8000")

    while(True):
        devices = await BleakScanner.discover(return_adv=True)
        for d, adv_data in devices.values():
            if d.name == device_name:
                decoder = DataDecoder(device_name, adv_data.manufacturer_data)
                print(decoder)


if __name__ == "__main__":
    asyncio.run(main())