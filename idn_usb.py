#!/usr/bin/env python3

import os
import sys
import usb.core
from usb.core import find as finddev
import usbtmc
import serial
from serial.tools import list_ports as lp
import time

def vidpid(vpstr):
    """
        returns numeric vendor ID and product ID from a string vvvv:pppp with hexadecimal values. Ex: '0699:0348', vid=0x699, pid=0x348.
    """
    if vpstr:
        try:
            c = vpstr.find(":")
        except:
            c = -1
        if c != -1:
            try:
                vid = int(vpstr[:c],16)
            except:
                vid = 0
            try:
                pid = int(vpstr[c+1:],16)
            except:
                pid = 0
        else:
            vid = 0; pid = 0
    else:
        vid = 0; pid = 0
    return vid, pid
    
# get command line options
try:
    vpstr = str(sys.argv[1])
except:
    vpstr = None

vid, pid = vidpid(vpstr)
if vid:
    # reset the instrument
    try:
        dev = finddev(idVendor=vid, idProduct=pid)
        dev.reset()
        # print(dev)
    except:
        print("Device [", hex(vid), ":", hex(pid), "] reset error!")
    # identify the instrument
    try:
        instr = usbtmc.Instrument(vid, pid)
        instr.write("*cls")
        time.sleep(0.1)
        idn = instr.ask("*idn?")
    except:
        print("ERROR - Instrument not responding to USBTMC. Trying USBCDC.")
        for com in lp.comports():
            if (com.vid == vid) and (com.pid == pid):
                print(com.device)
                print("\tname:\t\t", com.name)
                if (com.description != "n/a"):  print("\tdescription:\t", com.description)
                if (com.manufacturer != None):  print("\tmanufacturer:\t", com.manufacturer)
                if (com.product != None):       print("\tproduct:\t", com.product)
                if (com.serial_number != None): print("\tserial_number:\t", com.serial_number)
                if (com.location != None):      print("\tlocation:\t", com.location)
                if (com.interface != None):     print("\tinterface:\t", com.interface)
                if (com.hwid != "n/a"):         print("\thwid:\t\t", com.hwid)
        idn = None
    # print idn string
    if idn:
        print("*idn?:", idn)
else:
    print("invalid vid.")

