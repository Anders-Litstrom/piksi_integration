"""
Reads data from the base station piksi and uploads to OPUS for processing.
Solution file from OPUS is parsed for Latitude, Longitude, and Altitude. Data
is sent to base station, so that RTK position data yields absolute position.

https://github.com/swift-nav/libsbp
Contains libsbp python library - __main__ function based on TCP_example from 
sbp/client/examples

https://github.com/swift-nav/piksi_tools/tree/v2.3.0-release/piksi_tools
Settings.py is from piksi_tools. Console.py is also quite helpful.
"""

import argparse
import time
import os

# import settings from piksi_tools 
# https://github.com/swift-nav/piksi_tools/tree/v2.3.0-release/piksi_tools
import settings

from sbp.client.drivers.network_drivers import TCPDriver
from sbp.client.loggers.JSONLogger import JSONLogger
from sbp.client import Handler, Framer, Forwarder
from sbp.observation import SBP_MSG_OBS, SBP_MSG_BASE_POS_ECEF, SBP_MSG_GLO_BIASES, SBP_MSG_EPHEMERIS_GPS, SBP_MSG_EPHEMERIS_GLO, SBP_MSG_IONO
from sbp.logging import SBP_MSG_LOG
from sbp.piksi import MsgReset
from sbp.settings import (
    SBP_MSG_SETTINGS_READ_BY_INDEX_DONE, SBP_MSG_SETTINGS_READ_BY_INDEX_RESP,
    SBP_MSG_SETTINGS_READ_RESP, SBP_MSG_SETTINGS_WRITE_RESP,
    MsgSettingsReadByIndexReq, MsgSettingsReadReq,
    MsgSettingsSave, MsgSettingsWrite)

# can install with 'pip install selenium'
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

BASE_STATION_IP = "192.168.0.222"
BASE_STATION_PORT = "55555"

# Function uploads file using WebDriver to OPUS for processing
def send_to_OPUS(FILENAME):
    
    # Convert to rinex format - requires sbp2rinex command line tool
    # https://support.swiftnav.com/customer/en/portal/articles/2653446-tools
    os.system("sbp2rinex -v 2.11 " + FILENAME)
    FILENAME += ".obs"
    
    HEIGHT = '1.35'

    # Set to email address
    EMAIL_ADDRESS = 'anderslimstrom@gmail.com'

    # Opens Chrome
    browser = webdriver.Chrome()

    browser.get("https://www.ngs.noaa.gov/OPUS/")

    # Enter file to upload
    element_upload = browser.find_element_by_name("uploadfile")
    element_upload.send_keys(FILENAME)

    # Clears the field and enters the antenna height
    element_height = browser.find_element_by_name("height")
    element_height.clear()
    element_height.send_keys(HEIGHT)

    # Enter email address that solution file is sent to
    element_addr = browser.find_element_by_name("email_address")
    element_addr.send_keys(EMAIL_ADDRESS)

    # Clicks the static button option to submit the form and upload the file
    element_submit = browser.find_element_by_id("Static")
    element_submit.click()

    # closes the Chrome window
    browser.close()

# Connect to base station Piksi and log two hours of data to file
def base_pos_log(source):
    # Hold for 2 hours, + 1 minute to allow Piksi to acquire satellite signal
    TIME_INTERVAL = 7260

    filename = time.strftime("gnss-%Y%m%d-%H%M%S.sbp.json")
    filename = os.path.normpath(
                os.path.join("data", filename))

    # Data structure for logging
    logger = JSONLogger()

    # Sends data from Piksi to logger
    fwd = Forwarder(source, logger)
    fwd.start()
    
    # Collect data during interval
    start = time.perf_counter()
    diff = 0
    while diff < TIME_INTERVAL:
        diff = time.perf_counter() - start
    
    fwd.stop()
    logger.flush()
    logger.close()

    send_to_OPUS(filename)

def parse_position_data(filename):
    f_read = open(FILENAME, "r")

    f_lines = f_read.readlines()

    lat = ""
    lon = ""
    alt = ""

    for line in f_lines:
        tokens = line.split()

        if len(tokens0 == 0):
            continue
        
        if tokens[0] == "LAT:":
            split = tokens[3].split(".")
            lat = tokens[1] + tokens[2] + split[0] + split[1]
        elif tokens[0] == "W":
            split = tokens[4].split(".")
            lon = "-" + tokens[2] + tokens[3] + split[0] + split[1]
        elif tokens[0] == "EL":
            size = len(tokens[2])
            alt = tokens[2][:size-3]

        return (lat, lon, alt)

    stngs = settings(source, timeout=args.timeout)

    stngs.write("surveyed position", "broadcast", "true")
    stngs.write("surveyed position", "surveyed lat", lat)
    stngs.write("surveyed position", "surveyed lon", lon)
    stngs.write("surveyed position", "surveyed alt", alt)
    
# Perhaps add callback functions to handler

def main():

    # Open a connection to Piksi using TCP
    with TCPDriver(BASE_HOST, BASE_PORT) as driver:
        with Handler(Framer(driver.read, None, verbose=False)) as source:
            base_pos_log(source)

            # returns a tuple of the form (latitude, longitude, altitude)
            # still need to find a way to autosave OPUS email to file
            # may need to use RTKLIB for local processing 
            coords = parse_position_data(filename)

            # write settings to base station
            stngs = settings(source, timeout=args.timeout)

            stngs.write("surveyed position", "broadcast", "true")
            stngs.write("surveyed position", "surveyed lat", coords[0])
            stngs.write("surveyed position", "surveyed lon", coords[1])
            stngs.write("surveyed position", "surveyed alt", coords[2])
    
            # TODO: Pipe position data from base station/rover to IRAD


if __name__ == "__main__":
    main()
