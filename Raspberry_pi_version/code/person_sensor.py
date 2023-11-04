# AUTHOR: GUILLERMO PEREZ GUILLEN
# Example of accessing the Person Sensor from Useful Sensors on a Pi using
# Python. See https://usfl.ink/ps_dev for the full developer guide.

import io
import fcntl
import struct
import time

########## SERVO CONFIGURATION
import RPi.GPIO as GPIO 

servoPIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(servoPIN, GPIO.OUT)

p = GPIO.PWM(servoPIN, 50) # GPIO 18 for PWM with 50Hz
p.start(7.5) # Initialization 5


# The person sensor has the I2C ID of hex 62, or decimal 98.
PERSON_SENSOR_I2C_ADDRESS = 0x62

# We will be reading raw bytes over I2C, and we'll need to decode them into
# data structures. These strings define the format used for the decoding, and
# are derived from the layouts defined in the developer guide.
PERSON_SENSOR_I2C_HEADER_FORMAT = "BBH"
PERSON_SENSOR_I2C_HEADER_BYTE_COUNT = struct.calcsize(
    PERSON_SENSOR_I2C_HEADER_FORMAT)

PERSON_SENSOR_FACE_FORMAT = "BBBBBBbB"
PERSON_SENSOR_FACE_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_FACE_FORMAT)

PERSON_SENSOR_FACE_MAX = 4
PERSON_SENSOR_RESULT_FORMAT = PERSON_SENSOR_I2C_HEADER_FORMAT + \
    "B" + PERSON_SENSOR_FACE_FORMAT * PERSON_SENSOR_FACE_MAX + "H"
PERSON_SENSOR_RESULT_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_RESULT_FORMAT)

# I2C channel 1 is connected to the GPIO pins
I2C_CHANNEL = 1
I2C_PERIPHERAL = 0x703

# How long to pause between sensor polls. 0.2
PERSON_SENSOR_DELAY = 3

i2c_handle = io.open("/dev/i2c-" + str(I2C_CHANNEL), "rb", buffering=0)
fcntl.ioctl(i2c_handle, I2C_PERIPHERAL, PERSON_SENSOR_I2C_ADDRESS)

while True:
    try:
        read_bytes = i2c_handle.read(PERSON_SENSOR_RESULT_BYTE_COUNT)
    except OSError as error:
        print("No person sensor data found")
        print(error)
        time.sleep(PERSON_SENSOR_DELAY)
        continue
    offset = 0
    (pad1, pad2, payload_bytes) = struct.unpack_from(
        PERSON_SENSOR_I2C_HEADER_FORMAT, read_bytes, offset)
    offset = offset + PERSON_SENSOR_I2C_HEADER_BYTE_COUNT

    (num_faces) = struct.unpack_from("B", read_bytes, offset)
    num_faces = int(num_faces[0])
    offset = offset + 1

    faces = []
    for i in range(num_faces):
        (box_confidence, box_left, box_top, box_right, box_bottom, id_confidence, id,
         is_facing) = struct.unpack_from(PERSON_SENSOR_FACE_FORMAT, read_bytes, offset)
        offset = offset + PERSON_SENSOR_FACE_BYTE_COUNT
        face = {
            "box_confidence": box_confidence,
            "box_left": box_left,
            "box_top": box_top,
            "box_right": box_right,
            "box_bottom": box_bottom,
            "id_confidence": id_confidence,
            "id": id,
            "is_facing": is_facing,
        }
        ## TURN SPRAY ON
        if is_facing == 1:
            print("spray ON")
            p.ChangeDutyCycle(12.5)
            time.sleep(0.5)
            p.ChangeDutyCycle(7.5)
            time.sleep(0.5)
            p.ChangeDutyCycle(12.5)
            time.sleep(0.5)            
            p.ChangeDutyCycle(7.5)
            time.sleep(0.5)
        ## TURN SPRAY OFF
        else:
            print("spray OFF")
            p.ChangeDutyCycle(7.5)
            time.sleep(0.5)            
        faces.append(face)
    checksum = struct.unpack_from("H", read_bytes, offset)
    print(num_faces, faces)
    time.sleep(PERSON_SENSOR_DELAY)
