"""
Reads data from the base station piksi and uploads to OPUS for processing.
Solution file from OPUS is parsed for Latitude, Longitude, and Altitude. Data
is sent to base station, so that RTK position data yields absolute position.

https://github.com/swift-nav/libsbp
Contains libsbp python library - __main__ function based on TCP_example from 
sbp/client/examples

https://github.com/swift-nav/piksi_tools/tree/v2.3.0-release/piksi_tools
Console.py is also quite helpful.
"""

import argparse
import time
import os

# https://github.com/swift-nav/piksi_tools/tree/v2.3.0-release/piksi_tools
from piksi_tools import settings

from sbp.client.drivers.network_drivers import TCPDriver
from sbp.client.loggers.json_logger import JSONLogger
from sbp.client import Handler, Framer, Forwarder
from sbp.observation import SBP_MSG_OBS, SBP_MSG_BASE_POS_ECEF, SBP_MSG_GLO_BIASES, SBP_MSG_EPHEMERIS_GPS, SBP_MSG_EPHEMERIS_GLO, SBP_MSG_IONO
from sbp.logging import SBP_MSG_LOG, MsgLog
from sbp.piksi import MsgReset
from sbp.settings import (
    SBP_MSG_SETTINGS_READ_BY_INDEX_DONE, SBP_MSG_SETTINGS_READ_BY_INDEX_RESP,
    SBP_MSG_SETTINGS_READ_RESP, SBP_MSG_SETTINGS_WRITE_RESP,
    MsgSettingsReadByIndexReq, MsgSettingsReadReq,
    MsgSettingsSave, MsgSettingsWrite)

# can install with 'pip install selenium'
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

BASE_HOST = "192.168.0.222"
BASE_PORT = "55555"

DEFAULT_TIMEOUT_SECS = 0.5

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
    TIME_INTERVAL = 60

    filename = time.strftime("gnss-%Y%m%d-%H%M%S.sbp.json")
    infile = open(filename, 'w')
    #filename = os.path.normpath(
    #            os.path.join("data", filename))

    # Data structure for logging
    logger = JSONLogger(infile)

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

    lat = lon = alt = ""

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

    
def main():

    # Open a connection to Piksi using TCP
    with TCPDriver(BASE_HOST, BASE_PORT) as driver:
        with Handler(Framer(driver.read, driver.write, verbose=False)) as source:
            base_pos_log(source)

            # returns a tuple of the form (latitude, longitude, altitude)
            # need to work out how to download email before this runs successfully
            # if worst comes to worst, can use local RTKLIB post processing tool
             coords = parse_position_data(filename)

            # write settings to base station
            stngs = settings.Settings(source, DEFAULT_TIMEOUT_SECS)

            # TODO: Make sure this works. 
            # Try contacting SwiftNav about using Settings class to write
            # settings. These coordinates are hard-coded for testing. Write
            # tuple from parse_position_data to settings in final program.

            stngs.write("surveyed_position", "broadcast", "True")
            stngs.write("surveyed_position", "surveyed_position.surveyed_lat", "61.2735")
            stngs.write("surveyed_position", "surveyed_lon", "-149.85825")
            stngs.write("surveyed_position", "surveyed_alt", "15.000")
    
            # TODO: Pipe position data from base station/rover to IRAD


if __name__ == "__main__":
    main()
