import serial
import time
import json
import requests  # Import the requests library to make HTTP calls

def setup_serial():
    return serial.Serial(
        port='/dev/serial0',   # Adjust as necessary
        baudrate=9600,         # Same as the Arduino side
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )

def is_json(myjson):
    try:
        json_object = json.loads(myjson)
        return True, json_object
    except ValueError:
        return False, None

def send_data_to_thing_speak(data, bin_number):
    # Replace 'YOUR_WRITE_API_KEY' with your ThingSpeak channel's API key
    url = f"https://api.thingspeak.com/update?api_key=J223IR88JBBYUZ7A"
    if bin_number == 1:
        payload = {
            'field1': data['Average Temperature'],
            'field5': data['Average Humidity'],
        }
    if bin_number == 2:
        payload = {
            'field2': data['Average Temperature'],
            'field6': data['Average Humidity'],
        }
    if bin_number == 3:
        payload = {
            'field3': data['Average Temperature'],
            'field7': data['Average Humidity'],
        }
    if bin_number == 4:
        payload = {
            'field4': data['Average Temperature'],
            'field8': data['Average Humidity'],
        }
        
    try:
        response = requests.get(url, params=payload)
        print("Data sent to ThingSpeak with response code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Failed to send data to ThingSpeak:", e)

def xor_decrypt_from_hex(hex_str, key):
    key_length = len(key)
    bytes_from_hex = bytes.fromhex(hex_str)
    decrypted_bytes = bytearray()

    for i in range(len(bytes_from_hex)):
        decrypted_byte = bytes_from_hex[i] ^ ord(key[i % key_length])
        decrypted_bytes.append(decrypted_byte)

    return decrypted_bytes.decode('utf-8')  # Assuming the original message is UTF-8 encoded

def process_data(data_list):
    if not data_list:
        return

    temp_list = []
    humidity_list = []
    bin_number = data_list[0].get('bin_num', 'Unknown')  # Default to 'Unknown' if not found
    for entry in data_list:
        if 'Temp' in entry and 'Humidity' in entry:
            try:
                temp_list.append(float(entry['Temp']))
                humidity_list.append(float(entry['Humidity']))
            except ValueError:
                print("Error converting string to float")

    avg_temp = sum(temp_list) / len(temp_list) if temp_list else None
    avg_humidity = sum(humidity_list) / len(humidity_list) if humidity_list else None

    return {'Average Temperature': avg_temp, 'Average Humidity': avg_humidity, 'Bin Number': bin_number}

ser = setup_serial()
key = "YDN3h0nw1vv6SE0Buwx0h3K0foeDV2yU"
data_list = []
last_data_time = time.time()

print("Ready to receive data...")

try:
    while True:
        current_time = time.time()
        if current_time - last_data_time > 10:
            if data_list:
                result = process_data(data_list)
                if result:
                    send_data_to_thing_speak(result, result['Bin Number'])
                data_list = []  # Reset the data list
            last_data_time = current_time  # Update time to avoid loop trigger without new data
            continue  # Skip to the next loop iteration waiting for new data

        if ser.in_waiting > 0:
            data = ser.readline()
            last_data_time = time.time()
            try:
                data = data.decode('utf-8').strip()
                decrypted_message = xor_decrypt_from_hex(data, key)
                is_json_data, json_data = is_json(decrypted_message)
                if is_json_data:
                    data_list.append(json_data)
                    print("Received JSON data:", json_data)
                else:
                    print("Received non-JSON data:", decrypted_message)
            except UnicodeDecodeError:
                print("Received non-standard UTF-8 data:", data.decode('latin-1').strip())
            except Exception as e:
                print("Error in decryption or JSON parsing:", e)

        time.sleep(0.1)

except serial.SerialException as e:
    print("Serial exception:", e)
    ser.close()
    time.sleep(2)
    ser = setup_serial()

except KeyboardInterrupt:
    print("Program interrupted by the user")

finally:
    if ser.is_open:
        ser.close()
    print("Serial port closed")
