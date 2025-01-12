#!/usr/bin/env python3
"""
cursor_on_target.py

This module implements Cursor on Target (CoT) functionality for the OpenAthena project.
It provides functions to create, format, and send CoT messages over a UDP multicast network.

CoT is a XML-based schema for sharing location information between different systems.
This implementation focuses on sending location data from drone imagery analysis.

The module uses the following libraries:
- xml.etree.ElementTree for XML creation
- uuid for generating unique identifiers
- time for timestamping
- socket for network communication

Usage:
    Import this module and use the create_and_send_cot function to send CoT messages
    with resolved target information.

Note:
    This implementation uses UDP multicast by default, which may not be suitable
    for all network environments. Ensure your network supports multicast before use.
"""

import xml.etree.ElementTree as ET
import uuid
import time
import socket
import logging
import math
import hashlib
import argparse
import config

# NATO phonetic alphabet
NATO_ALPHABET = [
    "Alfa", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India",
    "Juliet", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo",
    "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "Xray", "Yankee", "Zulu"
]


def get_mac_address():
    """
    Retrieve the MAC address of the device.
    
    Returns:
    str: The MAC address in the format "XX:XX:XX:XX:XX:XX"
    """
    return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])


def create_device_uid():
    """
    Create a unique device identifier based on the MAC address.
    
    Returns:
    str: A device UID in the format "[NATO_ALPHABET][00-99]"
    """
    mac = get_mac_address()
    hash_value = hashlib.md5(mac.encode()).hexdigest()
    index = int(hash_value[:4], 16) % 2600
    letter_index = index // 100
    number = index % 100
    return f"{NATO_ALPHABET[letter_index]}{number:02d}"

DEVICE_UID = create_device_uid()
SERIAL_FILE = os.path.join(os.path.dirname(__file__), 'calculation_serial.txt')

def get_and_increment_serial():
    """
    Read the current serial number from a file, increment it, and write it back.
    If the file doesn't exist, start with 1.
    
    Returns:
    int: The incremented serial number

    Note: 
    File is expected to be named calculation_serial.txt and located in the src 
    directory
    """
    try:
        with open(SERIAL_FILE, 'r') as f:
            serial = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        serial = 0
    
    serial += 1
    
    with open(SERIAL_FILE, 'w') as f:
        f.write(str(serial))
    
    return serial


def create_uid():
    """
    Create a unique identifier for each CoT message.
    
    Returns:
    str: A unique identifier in the format "OpenAthena-[DEVICE_UID]-[SERIAL_NUMBER]"
    """
    serial = get_and_increment_serial()
    return f"OpenAthena-{DEVICE_UID}-{serial}"


def calculate_ce(theta, le=5.9):
    """
    Calculate the circular error (ce) based on the slant angle and linear error.
    
    Args:
    theta (float): The slant angle in degrees.
    le (float): The linear error in meters. Defaults to 5.9.
    
    Returns:
    float: The calculated circular error in meters.
    """
    return abs(1.0 / math.tan(math.radians(theta)) * le)


def build_cot_xml(lat, lon, alt, le = 5.9, theta, image_timestamp, stale_period):
    """
    Construct a CoT XML message.

    Parameters:
    lat (float): Latitude of the target in decimal degrees.
    lon (float): Longitude of the target in decimal degrees.
    alt (float): Altitude of the target in meters above WGS84 ellipsoid.
    le (float): Linear error of the altitude estimate in meters.
    theta (float): Angle of declanation of the camera
    image_timestamp (string): Timestamp from image's exif metadata
    stale_period (float): duration that the CoT message is valid for

    Returns:
    str: A formatted XML string representing the CoT message.

    Note:
    The function sets the CoT event type to 'a-p-G' (Assumed friend - Pending - Ground)
    and the 'how' attribute to 'h-c' (Human - Calculated).
    Circular error of the position is a function of linear error.
    """
    global DEVICE_UID

    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("uid", create_uid())
    root.set("type", "a-p-G")
    root.set("how", "h-c")
    root.set("time", image_timestamp)
    root.set("start", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    stale_time = time.time() + stale_period
    root.set("stale", time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(stale_time)))

    point = ET.SubElement(root, "point")
    point.set("lat", str(lat))
    point.set("lon", str(lon))
    point.set("hae", str(alt))
    point.set("ce", str(calculate_ce(theta)))
    point.set("le", str(le))

    detail = ET.SubElement(root, "detail")
    precisionlocation = ET.SubElement(detail, "precisionlocation")
    precisionlocation.set("altsrc", "DTED2")
    precisionlocation.set("geopointsrc", "GPS")

    remarks = ET.SubElement(detail, "remarks")
    remarks.text = "Generated by OpenAthena from sUAS data"

    return ET.tostring(root, encoding="utf-8")


def setup_multicast_socket(multicast_group, port):
    """
    Create and configure a UDP socket for multicast transmission.

    Parameters:
    multicast_group (str): The IP address of the multicast group.
    port (int): The UDP port number to use.

    Returns:
    socket.socket: A configured UDP multicast socket.

    Note:
    The socket is configured with a TTL of 32, which should be sufficient
    for most local network environments.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    return sock

def send_cot_message(sock, message, multicast_group, port, max_retries=3):
    """
    Send a CoT message over a multicast UDP socket with error handling and retries.

    Parameters:
    sock (socket.socket): The UDP socket to use for sending.
    message (str): The CoT XML message to send.
    multicast_group (str): The IP address of the multicast group.
    port (int): The UDP port number to use.
    max_retries (int, optional): Maximum number of send attempts. Defaults to 3.

    Returns:
    bool: True if the message was sent successfully, False otherwise.

    Raises:
    socket.error: If there's a persistent network error after all retries.

    Note:
    This function implements a simple retry mechanism for handling transient
    network errors. It will attempt to send the message up to 'max_retries'
    times before giving up. All errors are logged for debugging purposes.
    """
    retries = 0
    while retries < max_retries:
        try:
            sock.sendto(message, (multicast_group, port))
            logging.info(f"CoT message sent successfully to {multicast_group}:{port}")
            return True
        except socket.error as e:
            retries += 1
            logging.warning(f"Attempt {retries}/{max_retries} failed. Error: {str(e)}")
            if retries == max_retries:
                logging.error(f"Failed to send CoT message after {max_retries} attempts")
                raise  # Re-raise the last exception
    return False

def get_stale_period():
    """
    Get the stale period from command line arguments or config file.
    Command line argument takes precedence if provided.

    Returns:
    int: The stale period in seconds
    """
    parser = argparse.ArgumentParser(description="Send CoT message")
    parser.add_argument("--stale", type=int, help="Stale period in seconds")
    args = parser.parse_args()
    
    if args.stale is not None:
        return args.stale
    elif hasattr(config, 'STALE_PERIOD'):
        return config.STALE_PERIOD
    else:
        return 180  # default to 3 minutes

STALE_PERIOD = get_stale_period()

def create_and_send_cot(lat, lon, alt, le=5.9, theta, image_timestamp, multicast_group='239.2.3.1', port=6969):
    """
    Create a CoT message and send it over a multicast network.

    This function combines the creation and sending of a CoT message into a single call.

    Parameters:
    lat (float): Latitude of the target in decimal degrees.
    lon (float): Longitude of the target in decimal degrees.
    alt (float): Altitude of the target in meters above WGS84 ellipsoid.
    ce (float, optional): Circular error of the position estimate in meters. Defaults to 15.0.
    le (float, optional): Linear error of the altitude estimate in meters. Defaults to 20.0.
    multicast_group (str, optional): The IP address of the multicast group. Defaults to '239.2.3.1'.
    port (int, optional): The UDP port number to use. Defaults to 6969.

    Returns:
    bool: True if the message was sent successfully, False otherwise.

    Note:
    The default ce and le values are conservative estimates and should be replaced
    with more accurate values when available from sensor data or calculations.
    This function will attempt to send the message multiple times in case of network errors.
    """
    cot_message = build_cot_xml(lat, lon, alt, le, theta, image_timestamp, STALE_PERIOD)
    sock = setup_multicast_socket(multicast_group, port)
    try:
        result = send_cot_message(sock, cot_message, multicast_group, port)
        return result
    except socket.error as e:
        logging.error(f"Failed to send CoT message: {str(e)}")
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    # Example usage
    create_and_send_cot(40.7128, -74.0060, 10.0, 45, "2023-07-08T12:00:00Z")