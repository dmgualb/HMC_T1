#!/usr/bin/env python3

###################################################################################################
#   DAQ SERVER - Multiprocess socket server for GVSI DAQ commands 
#   -------------------------------------------------------------
#
#   DESCRIPTION
#   -----------
# 
#   This is the command server for the GVSI DAQ. 
#   It implements a TCP stream server layer for the Alacer HMCLab system. 
#   The server installs services on 4 ports: 
#           DAQ CMD PORT:       57000       Receives command requests for SCPI DAQ commands
#           DAQ DATA PORT:      58000       Unidirectional stream for :TRIG:CONT:READ? data
#           SYS CMD PORT:       59000       Receives system high level commands
#           SVC CTRL PORT:      60000       Service control port and syslog messages
#           
#
#   USB SERIAL PORTS SETUP
#   ----------------------
#
#   The DAQ multichannel data acquisition system is controlled using SCPI commands over a USB CDC serial port.
#   The usb connections are specified using VISA id strings, which contain VID:PID:SERIAL unique identification signatures.
#
#   COMMAND LINE PARAMETERS
#   -----------------------
#
#   The script supports standard gnu short and long command line arguments, and can be automated via standard 
#   shell scripts. Command line arguments can be fetched from a text file. Each option is separated by whitespace, 
#   including line breaks. Options can be mixed, with command line options and config file options combined to form 
#   the program arguments. With config file options, test configurations can be grouped by test type and limits, 
#   simplifying test automation. 
#
#--------------------------------------------------------------------------------------------------
#   THIS CODE IS PROVIDED AS IS, WITH NO IMPLIED OR EXPLICIT GUARANTEES OF PERFORMANCE OR FUNCTIONALITY. 
#   GRIDVORTEX IS NOT LIABLE FOR ANY DIRECT OR INDIRECT DAMAGES DERIVED FROM USE OF THIS CODE. 
#   THIS CODE IS PUBLISHED AS OPEN SOURCE FOR FREE USE. SUPPORT WILL BE PROVIDED ON GOODWILL, WITH NO 
#   OBLIGATION OF SUPPORT OR SERVICE BEING IMPLIED WITH THE PROVISION OF THIS CODE. 
#--------------------------------------------------------------------------------------------------
#   LICENSE:    BSD 2-CLAUSE LICENSE
#       
#               Copyright (c) 2022, 2023, 2024, 2025 by Jonny Doin, GridVortex Systems 
#               
#               Redistribution and use in source and binary forms, with or without
#               modification, are permitted provided that the following conditions are met:
#               
#               1. Redistributions of source code must retain the above copyright notice, this list 
#               of conditions and the following disclaimer.
#               
#               2. Redistributions in binary form must reproduce the above copyright notice, this 
#               list of conditions and the following disclaimer in the documentation and/or other 
#               materials provided with the distribution.
#               
#               THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
#               EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
#               OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
#               SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
#               INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED 
#               TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR 
#               BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
#               CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN 
#               ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH 
#               DAMAGE.
# 
#--------------------------------------------------------------------------------------------------
#   BUGS:
#   -----
#
#--------------------------------------------------------------------------------------------------
#   TODO:
#   -----
# 
#           - :CMD:PEAK? <fieldname>, <time>, <interval>[, FILTER[, <window>]]
#                   # Request find first peak for the specified channel, in the time window provided.
# 
#           # :DATA:LISTEN?
#           # :DATA:NAMES?
#           # :DATA:READ? <from-time>,<to-time>
#           
#           # :CMD:BASE:DRIFT? <fieldname>[, <interval>]
#                   # Request the specified channel baseline drift for the specified period or for the last minute, and report in units/minute.
#           # :CMD:READ? ALL | {<fieldname>[[, <time>], <avg_period>]}
#                   # specify ALL for a full raw record read
#                   # implement the period averaging.
#                   # use the median averaging (np.median(array))
#           # :CMD:TIME:RST
#                   # compute the time offset for the whole buffer, with negative time before T0.
# 
#
#
###################################################################################################

from dataclasses import dataclass, field
from overrides import override
from argparse import Namespace
import multiprocessing as mp
import math
import numpy as np
from scipy.signal import find_peaks
import time
from io import TextIOWrapper
import os
import sys
import traceback
import getopt
from instrument import Instrument
import socket
import threading

script_ver      = "v0.9.433"
copyright_str   = "Copyright (c) 2023, 2024, 2025 Jonny Doin"
license_str     = "License BSD-2-Clause: The 2-Clause BSD License <https://opensource.org/license/bsd-2-clause/>"
license_short   = "This is free software: you are free to change and redistribute it.\r\nThere is NO WARRANTY, to the extent permitted by law."

# instrument identification strings
# --- GVSI --- DAQ ADS8688A interface ----------------------------------
gvsi_visa_id_1  = "USBSER::0x2341::0x0043::GVSI::*::INSTR"              # VISA id string for any GVSI instrument, any serial number, any port (ARDUINO USB)
gvsi_visa_id_2  = "USBSER::0x10c4::0xea60::GVSI::*::INSTR"              # VISA id string for any GVSI instrument, any serial number, any port (CP2102 BRIDGE)
baudrate        = 115200                                                # serial port baud rate

#===============================================================================================#
#               COMMAMD LINE OPTIONS PROCESSING                                                 #
#===============================================================================================#

def defaults() -> Namespace:
    """Return a namespace with the default arg values."""
    default = Namespace()
    default.quiet           = None                              # suppress status messages but display measurement records
    default.silent          = None                              # suppress interactive plot graph and all stdout messages
    default.verbose         = None                              # verbose mode, write all messages to stdout
    default.debug           = None                              # show SCPI messages
    default.nplc            = 5.0                               # ADC NPLC integration constant
    default.bufsize         = 1200.0                            # buffer size in seconds
    default.host_addr       = "127.0.0.1"                       # socket server host address
    default.cmd_port        = 57000                             # DAQ cmd port
    default.data_port       = 58000                             # DAQ continuous data stream port
    default.sys_port        = 59000                             # SYS high level commands port
    default.svc_port        = 60000                             # Service and syslog port
    default.max_handlers    = 5                                 # number of active client handlers for each service
    return default

def version() -> None:
    """Show the program version."""
    print(f'{sys.argv[0]} {script_ver}')
    print(copyright_str)
    print(license_str)
    print(license_short)

def usage() -> None:
    """Show the options help."""
    default = defaults()
    print( 'NAME:')
    print(f'     {sys.argv[0]} -- data acquisition socket server for the multichannel DAQ.')
    print()
    print(f'\t{sys.argv[0].upper()} is a socket server layer that interfaces directly with the DAQ hardware and receives measurement commands from the remote Master module.')
    print()
    print(f'VERSION: {script_ver} - {copyright_str}')
    print()
    print( 'SYNOPSIS:')
    print(f'     {sys.argv[0]} <options>')
    print()
    print( 'options:')
    print( '     --version          show version')
    print( '     -h | --help        show options help')
    print( '     -S | --silent      silent mode. Do not show any messages')
    print( '     -q | --quiet       quiet mode. Do not show status messages, but show measurement records')
    print( '     -v | --verbose     verbose mode, show more detailed messages')
    print( '     -D | --debug       debug mode, show SCPI commands sent')
    print(f'     --nplc <>          ADC integration in NPLC (default {format_SI(default.nplc, precision = 1)})')
    print(f'     --bufsize <>       data buffers size in seconds (default {format_SI(default.bufsize, precision = 1)})')
    print(f'     --host <>          Host address (default {default.host_addr})')
    print(f'     --cmd_port <>      CMD service port (default {default.cmd_port})')
    print(f'     --data_port <>     DATA service port (default {default.data_port})')
    print()

def si_to_eng(s: str, unit: str = "") -> str:
    """Convert a string number with SI suffix to Eng notation."""
    s = s.replace(unit, "")
    s = s.replace("G", "e+9")
    s = s.replace("M", "e+6")
    s = s.replace("k", "e+3")
    s = s.replace("m", "e-3")
    s = s.replace("u", "e-6")
    s = s.replace("n", "e-9")
    return s

def format_SI(val:float, precision:int=2) -> str:
    """Format a numeric value into a string with SI suffix from quecto to QUETTA."""
    if val is None: return 'None'
    prefix = " kMGTPEZYRQ qryzafpnum "
    s = -1.0 if val < 0 else 1.0
    val *= s
    if val < 1e-30:
        # val < 1 quecto
        val = 0.0; i = -12
    elif val < 1.0:
        # normalize 0 < x < 1 to the range 1 <= x < 1000
        i = -1
        while val < 1.0:
            val = val * 1000; i = i - 1
    elif val > 1e30:
        # val > 1 QUETTA
        return "OVR"
    elif val >= 1000.0:
        i = 0
        while val >= 1000.0:
            val = val / 1000; i = i + 1
    else:
        i = 0
    return "{0:.{2}f}{1}".format(s*val, prefix[i:i+1], precision)

def insert_text(text:list[str], i:int, line: str) -> list[str]:
    """Helper function to manage the textbox list."""
    t = text
    if not isinstance(t, list): t = []
    if i is None: return t
    while len(t) <= i:
        t.append("")
    t.insert(i, line)
    t.pop(i+1)
    return t

def quote(x: str) -> str | None:
    """Helper function to search for the first single or double quote."""
    if '"' in x:
        if "'" in x:
            if x.find('"') < x.find("'"):
                return '"'
            else:
                return "'"
        else:
            return '"'
    elif "'" in x:
        return "'"
    else:
        return None

def splitargs(x: str) -> list[str]:
    """Return a list with args delimited by whitespace or quotes, like sys.argv."""
    d = quote(x)
    if not d:
        return x.split()
    l,s,r = x.partition(d)
    args = l.split()
    if s == d:
        l,s,r = r.partition(d)
        if s == d:
            args.append(l)
            return args+splitargs(r)
        else:
            return args+l.split()
    else:
        return args

def get_options(fconf: str | None = None) -> Namespace:
    """
        Get command line options, and return a namespace containing all the options.
        This function is called recursivelly for each config file processed, and all options are reprocessed on each call. 
        All options processing code must be stateless. 
        The only state of the function is the list of options, list of expanded arguments and the options filenames list, to avoid infinite recursion. 
    """
    global opts_long
    if 'opts_long' not in globals():
        opts_long = [   
            'help', 'version', 'quiet', 'silent', 'verbose', 'debug', 'nplc=', 'bufsize=',
            'host=', 'cmd_port=', 'data_port=',
        ]

    opts_short = "hvqDS"
    # init arg namespace with default options
    arg = defaults()
    try:
        argv = sys.argv[1:]
        optlist, arglist = getopt.getopt(argv, opts_short, opts_long)
        for opt, val in optlist:
            # --- general options ---
            if opt in ['-h', '--help']:
                usage()
                sys.exit(0)
            elif opt in ['--version']:
                version()
                sys.exit(0)
            elif opt in ['-D', '--debug']:
                arg.debug = True
            elif opt in ['-q', '--quiet']:
                if arg.verbose: raise RuntimeError("Illegal quiet and verbose at the same time")
                if arg.silent: raise RuntimeError("Illegal quiet and silent at the same time")
                arg.quiet = True
            elif opt in ['-v', '--verbose']:
                if arg.quiet: raise RuntimeError("Illegal quiet and verbose at the same time")
                if arg.silent: raise RuntimeError("Illegal silent and verbose at the same time")
                arg.verbose = True
            elif opt in ['-S', '--silent']:
                if arg.verbose: raise RuntimeError("Illegal silent and verbose at the same time")
                if arg.quiet: raise RuntimeError("Illegal silent and quiet at the same time")
                arg.quiet = True
                arg.silent = True
            elif opt in ['--timestamp']:
                arg.timestamp = float(val)
            # --- specific options ---
            elif opt in ['--nplc']:
                arg.nplc = float(si_to_eng(val))
            elif opt in ['--bufsize']:
                arg.bufsize = float(si_to_eng(val))
            elif opt in ['--host']:
                arg.host_addr = val
            elif opt in ['--cmd_port']:
                arg.cmd_port = int(val)
            elif opt in ['--data_port']:
                arg.data_port = int(val)
            else:
                assert False, f'unhandled option: {opt=}, {val=}'
                sys.exit(2)
    except SystemExit:
        level = sys.exc_info()[1]
        sys.exit(level)
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    except AssertionError as err:
        print('Error:', err)
        sys.exit(2)
    except:
        print('Error in command line:', sys.exc_info()[1])
        sys.exit(2)
    arg.timestamp = time.time()
    return arg

#===============================================================================================#
#   CLASS   Sensor base class                                                                   #
#===============================================================================================#

@dataclass
class Sensor():
    """
        Abstract Base Class for sensors.</br>
        The Sensor() base class has a container for all sensors instances, and class methods to view instances data.</br>
       
        ## Properties

        ### Getters
        ```
            .name: (str):               scpi signal name.
            .plot: (str):               associated axes name for the related plotline.
            .label: (str):              plot legend string.
            .unit: (str):               unit string.
            .fmt: (str):                plot line format string.
            .calib: (float):            calibration value.
        ```

        ### Setters
        ```
            .name: (str):               scpi signal name.
            .plot: (str):               associated axes name for the related plotline.
            .label: (str):              plot legend string.
            .unit: (str):               unit string.
            .fmt: (str):                plot line format string.
            .calib: (float):            calibration value.
        ```

        ## Methods
        
        ### Instance Methods
        ```
            .val(vadc):                 translate the ADC reading in Volts into the value in equivalent sensor units.
                                        derived classes overwrite this method to implement the sensor transfer function.
            .format(vadc):              format the ADC reading in Volts into a printable representaion with the format string and the unit.
                                        this method calls the instance .val() to translate the ADC reading prior to format it.
        ```
        
        ### Class Methods
        ```
            Sensor.clear(plotname):     remove all Sensor instances.
            Sensor.count(plotname):     return the current number of sensors instances.
            Sensor.sensors(plotname):   return an iterator for the sensors instances.
            Sensor.names(plotname):     return an iterator for sensor SCPI names.
            Sensor.labels(plotname):    return an iterator for sensor label strings.
        ```
    """
    _name: str
    _plot: str
    _label: str
    _unit: str
    _fmt: str

    @property
    def type(self): return f'{type(self)}'.split('.')[-1].split("'")[0]
    @property
    def name(self): return self._name
    @name.setter
    def name(self, name: str): self._name = name
    @property
    def plot(self): return self._plot
    @plot.setter
    def plot(self, plot: str): self._plot = plot
    @property
    def label(self): return self._label
    @label.setter
    def label(self, label: str): self._label = label
    @property
    def unit(self): return self._unit
    @unit.setter
    def unit(self, unit: str): self._unit = unit
    @property
    def fmt(self): return self._fmt
    @fmt.setter
    def fmt(self, fmt: str): self._fmt = fmt

    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}'):
        """
            ### Parameters
            ```
                name: str   
                    SCPI channel name.
                plot: str   
                    name of the plot axes to plot this sensor data line.
                label: str
                    plot legend for this channel.
                unit: str
                    formatted data unit.
                fmt: str
                    number formatting string.
            ```
        """
        self.name = name
        self.plot = plot
        self.label = label
        self.unit = unit
        self.fmt = fmt
        if not hasattr(Sensor, '_sensors'):
            Sensor._sensors = []
        Sensor._sensors.append(self)

    def val(self, vadc: float):
        """Return the sensor float value from the raw adc volts reading."""
        return vadc

    def format(self, vadc: float):
        """Return a string formatted with the sensor value from the raw adc reading."""
        return (self._fmt + '{}').format(self.val(vadc), self._unit)

    @classmethod
    def clear(cls):
        """Remove all Sensor instances."""
        if hasattr(cls, '_sensors'):
            del cls._sensors

    @classmethod
    def count(cls, plotname: str | None = None):
        """Return the number of sensors instances for the axes plot, if the plotname is specified, or of all sensors if not."""
        return len([x for x in cls._sensors if (plotname is None) or (x.plot == plotname)]) if hasattr(cls, '_sensors') else 0

    @classmethod
    def sensors(cls, plotname: str | None = None):
        """Return an iterator for the sensors defined for the axes plot, if the plotname is specified, or of all sensors if not."""
        return (x for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []

    @classmethod
    def names(cls, plotname: str | None = None):
        """Return an iterator of SCPI names for the sensors defined for the axes plot, if the plotname is specified, or of all sensors if not."""
        return (x.name for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []

    @classmethod
    def labels(cls, plotname: str | None = None):
        """Return an iterator of label strings for the sensors defined for the axes plot, if the plotname is specified, or of all sensors if not."""
        return (x.label for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []

#===============================================================================================#
#   CLASS   Sensor_ADC                                                                          #
#===============================================================================================#

@dataclass
class Sensor_ADC(Sensor):
    """
        Class for ADC inputs in Volts.</br>
        The ADC sensor is a thin wrapper for the base Sensor class, with values in raw ADC volts, 
        so the base class .val() method is not overridden. 
    """
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}'):
        super().__init__(name, plot, label, unit, fmt)

#===============================================================================================#
#   CLASS   Sensor_H2_MEMS                                                                      #
#===============================================================================================#

@dataclass
class Sensor_H2_MEMS(Sensor):
    """
        Class for H2 MEMS sensors type GMV-2021B.</br>
        The ADC voltage read from the H2 sensor is the raw sensor voltage, and we don't have its transfer 
        function at this moment, so the base class .val() method is not overridden. 
    """
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}'):
        super().__init__(name, plot, label, unit, fmt)

#===============================================================================================#
#   CLASS   Sensor_CH4_MQ4B                                                                     #
#===============================================================================================#

@dataclass
class Sensor_CH4_MQ4B(Sensor):
    """
        Class for CH4 sensors type MQ-4B.
        The ADC voltage read from the CH4 sensor is the raw sensor voltage, and we don't have its transfer 
        function at this moment, so the base class .val() method is not overridden. 
    """
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}'):
        super().__init__(name, plot, label, unit, fmt)

#===============================================================================================#
#   CLASS   Sensor_CH4_TGS2611                                                                  #
#===============================================================================================#

@dataclass
class Sensor_CH4_TGS2611(Sensor):
    """
        Class for CH4 sensors type TGS2611.
        The ADC voltage read from the CH4 sensor is the raw sensor voltage, and we don't have its transfer 
        function at this moment, so the base class .val() method is not overridden. 
    """
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}'):
        super().__init__(name, plot, label, unit, fmt)

#===============================================================================================#
#   CLASS   Sensor_T10k                                                                         #
#===============================================================================================#

@dataclass
class Sensor_T10k(Sensor):
    """
        Class for 10kohm thermistor sensors, with a conversion transfer function.
        The ADC signal received is linearly proportional to the sensor resistance, with
        a 100uA current source converting the resistance to voltage.
        
        The base class method .val() is overridden to return the converted temperature in degrees Celsius.
        
        The transfer function is the Steinhart-Hart thermistor equation with Beta solved for Temperature
        and transposed for resistance as ADC Volts.
        
        Default Beta for the MF52B 10K thermistor used in the Lab: 4010.0 (back-annotated from 
        tabulated experimental measurement).
    """

    __beta: float       # thermistor Beta
    __vref: float       # Fixed Vref term at R0, T0
    __t0: float         # reference temperature in Kelvins
    __v0: float         # reference voltage (R0 * 100uA)

    @property
    def beta(self): return self.__beta
    @beta.setter
    def beta(self, beta: float): self.set_beta(beta)
    @property
    def vref(self): return self.__vref
    @property
    def t0(self): return self.__t0
    @property
    def v0(self): return self.__v0

    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, label, unit, fmt)
        self.set_beta()

    def set_beta(self, beta: float = 4010.0, t0: float = 298.15, v0: float = 1.0):
        """Set the Beta parameter and recalculate the reference term."""
        self.__beta = beta
        self.__t0 = t0
        self.__v0 = v0
        self.__vref = self.v0 * math.exp(-self.beta / self.t0)

    def vadc(self, temp: float):
        """Return the Vadc equivalent to a given temperature."""
        K0 = 273.15
        vadc = self.v0 * math.exp(self.beta * (1/(temp + K0) - 1/self.t0))
        return vadc

    @override
    def val(self, vadc: float):
        """Return the temperature in Celsius for a given thermistor mV reading."""
        if vadc <= 0.0: vadc = 1e-6     # saturate zero/negative values to avoid domain errors
        return (self.beta / math.log(vadc / self.vref)) - 273.15


#===============================================================================================#
#   CLASS   Sensor_PT100                                                                        #
#===============================================================================================#

@dataclass
class Sensor_PT100(Sensor):
    """
        Class for RTD PT100 temperature sensors.

        The ADC signal received is directly proportional to the sensor resistance, with
        a 100uA current source converting the resistance to voltage, and a voltage gain 
        of x100 (10mV/ohm), so that at 0 degrees Celsius, the sensor signal (vref) is 1.000V:

            Vrtd = R(rtd) * 0.0001 * 100
        
        The base class method .val() is overridden to return the converted temperature in degrees Celsius.
        
        The transfer function is the quadratic solution equation form of the simplified second order 
        Callendar-Van Dusen RTD polynomial solved for T and transposed for ADC Volts.
        
        The coefficients A and B are defined for the IEC 60751 standard PT-385 platinum alloy with 
        a TCR of 3850 ppm/K:
        
            PT-385:     A = 3.9083e-3, B = -5.775e-7    (IEC 60751 Std)
            PT-392:     A = 3.9827e-3, B = -5.875e-7    (American Std)
            
        The Heraeus M222 Class A sensor was used in the Lab prototypes and experimentally verified 
        with the transfer function.
        
        ### ERRORS:

        The RTD circuit can introduce the following errors in the converted voltage:

            Ei = current source error
            Eg = voltage gain error
            E0 = voltage offset error

        The full transfer function with the error sources is then:

            Vrtd = (R(rtd) * (0.0001 * Ei) + E0) * (100 * Eg)
            Vrtd = ((R(rtd) * 0.0001 * 100) + (E0 * 100)) * (Ei * Eg)
            Vrtd = ((R(rtd) * 0.01) + Eo) * Ex
            Vc = (Vrtd - Eo) / Ex

            Where:  Ex is the total combined gain error
                    Eo is the total offset related to output (RTO)
                    Vc is the corrected ADC voltage

        Ex is measured with a known calibration resistor to obtain the errors from the current source and loop gain.

        Eo is measured with the sensor inputs shorted.

        Experimental data measured with a reference calibration resistance of 100.000 ohms:

            Ec = 1/Ex = 0.997663
            Eo = 1e-3 (10uV input offset)
    """

    __A: float          # RTD A coefficient
    __B: float          # RTD B coefficient
    __vref: float       # adc voltage at 0 degrees Celsius
    __Ec: float         # total calibration gain error correction for Vadc
    __Eo: float         # total offset voltage error (Voffs * 100) for Vadc

    @property
    def a(self): return self.__A
    @property
    def b(self): return self.__B
    @property
    def vref(self): return self.__vref
    @property
    def Ec(self): return self.__Ec
    @property
    def Eo(self): return self.__Eo

    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, label, unit, fmt)
        self.set_coeffs()

    def set_coeffs(self, A: float = 3.9083e-3, B: float = -5.775e-7, vref: float = 1.0, Ec: float = 0.997663, Eo: float = 1e-3):
        """
            Set the transfer function polynomial coefficients and error terms.
                A,B : RTD standard coefficients
                vref: value at 0 degrees Celsius
                Ec: calibration gain correction term for Vadc
                Eo: calibration offset error (Voffs * 100) for Vadc
        """
        self.__A = A
        self.__B = B
        self.__vref = vref
        self.__Ec = Ec
        self.__Eo = Eo

    @override
    def val(self, vadc: float):
        """Return the temperature in Celsius for a given RTD volts reading, compensating the circuit calibration errors."""
        vc = (vadc - self.Eo) * self.Ec
        return (-self.a + math.sqrt(self.a**2 - (4 * self.b * (1.0 - vc/self.vref)))) / (2 * self.b)

#===============================================================================================#
#   CLASS   Sensor_O2_AO_03                                                                     #
#===============================================================================================#

@dataclass
class Sensor_O2_AO_03(Sensor):
    """
        Class for Asair AO-03 Oxygen Electrochemical cell, with a conversion transfer function.
        The sensor is a current source with 100uA at ambient air.
        The signal conditioning circuit gives circa 1000mV +/- 50mV for 20.9% (Air).
        
        The Sensor base class method .val() is overridden to return the converted O2 concentration in % O2.
        The transfer function is a straight line fit, with back-annotated Lab data for the voltage
        offset and typical observed baseline voltage for the prototype circuit and AO-03 sensor
        used in the prototype.
    """

    __offset: float     # voltage offset with the sensor shorted
    __baseline: float   # sensor baseline reading in Air
    __ref_o2: float     # percent of O2 in Air

    @property
    def offset(self): return self.__offset
    @offset.setter
    def offset(self, offset: float): self.__offset = offset
    @property
    def baseline(self): return self.__baseline
    @baseline.setter
    def baseline(self, baseline: float): self.__baseline = baseline
    @property
    def ref_o2(self): return self.__ref_o2
    @ref_o2.setter
    def ref_o2(self, ref_o2: float): self.__ref_o2 = ref_o2

    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, label, unit, fmt)
        self.ref_o2 = 20.9      # average O2 concentration in Air
        self.offset = 1.151e-3  # measured voltage offset in the prototype
        self.baseline = 1.02    # set default typical baseline value

    @override
    def val(self, vadc: float):
        """Return the percent of O2 for a given sensor mV reading."""
        return ((vadc - self.offset) * self.ref_o2) / (self.baseline - self.offset)

#===============================================================================================#
#   CLASS   Sensor_O2_Me2_O2                                                                    #
#===============================================================================================#

@dataclass
class Sensor_O2_Me2_O2(Sensor):
    """
        Class for Winsen Me2_O2 Oxygen Electrochemical cell, with a conversion transfer function.
        The sensor is a current source with 100uA at ambient air.
        The signal conditioning circuit gives circa 1000mV +/- 50mV for 20.9% (Air).
        
        The Sensor base class method .val() is overridden to return the converted O2 concentration in % O2.
        The transfer function is a straight line fit, with back-annotated Lab data for the voltage
        offset and typical observed baseline voltage for the prototype circuit and Me2-O2 sensor
        used in the prototype.
    """

    __offset: float     # voltage offset with the sensor shorted
    __baseline: float   # sensor baseline reading in Air
    __ref_o2: float     # percent of O2 in Air

    @property
    def offset(self): return self.__offset
    @offset.setter
    def offset(self, offset: float): self.__offset = offset
    @property
    def baseline(self): return self.__baseline
    @baseline.setter
    def baseline(self, baseline: float): self.__baseline = baseline
    @property
    def ref_o2(self): return self.__ref_o2
    @ref_o2.setter
    def ref_o2(self, ref_o2: float): self.__ref_o2 = ref_o2

    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, label, unit, fmt)
        self.ref_o2 = 20.9      # average O2 concentration in Air
        self.offset = 1.151e-3  # measured output voltage offset in the prototype
        self.baseline = 1.29    # set default typical baseline value

    @override
    def val(self, vadc: float):
        """Return the percent of O2 for a given sensor mV reading."""
        return ((vadc - self.offset) * self.ref_o2) / (self.baseline - self.offset)

#===============================================================================================#
#   CLASS   Sensor_H2_Fuel_Cell                                                                 #
#===============================================================================================#

@dataclass
class Sensor_H2_Fuel_Cell(Sensor):
    """
        Class for Winsen MEv-GH01 Hidrogen Fuel Cell, with a conversion transfer function.
        The sensor is a current source with 1nA/ppmH2.
        The signal conditioning circuit gives circa 10mV/nA, with a baseline voltage of 318mV 
        at zero ppm, and a full scale of 4.5V at 300ppm.
    """
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, label, unit, fmt)

#===============================================================================================#
#   CLASS   Sensor_CO2_MG812                                                                    #
#===============================================================================================#

@dataclass
class Sensor_CO2_MG812(Sensor):
    """
        Class for Winsen MG-812 CO2 Electrochemical Cell.
        The sensor is a electrochemical cell with output inversely proportional to the CO2 concentration.
    """
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, label, unit, fmt)

#===============================================================================================#
#   CLASS   Sensor_AHT                                                                          #
#===============================================================================================#

@dataclass
class Sensor_AHT(Sensor):
    """
        Class for AHT10 I2C sensors.
        The SCPI read command already send the temperature and relative humidity in converted units, 
        so the base class .val() method is not overridden.
    """
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, label, unit, fmt)

#===============================================================================================#
#               SENSORS INSTANCES                                                               #
#===============================================================================================#

def create_sensors() -> tuple[Sensor]:
    """
        Create the configured sensors instances, and return a tuple of sensor objects.
    """
    Sensor.clear()
    Sensor_CH4_TGS2611('ch0','main','CH4','V','{:.6f}')
    Sensor_T10k('ch1','temp','CH4_TEMP','C','{:.2f}')
    Sensor_O2_Me2_O2('ch2','prct','O2','%','{:.2f}')
    Sensor_H2_Fuel_Cell('ch3','main','H2','V','{:.6f}')
    Sensor_T10k('ch4','temp','HOTSIDE_TEMP','C','{:.2f}')
    Sensor_PT100('ch5','temp','PT100','C','{:.2f}')
    Sensor_T10k('ch6','temp','COLDSIDE_TEMP','C','{:.2f}')
    Sensor_T10k('ch7','temp','HOTPLATE_TEMP','C','{:.2f}')
    Sensor_AHT('temp','temp','AHT10_TEMP','C','{:.2f}')
    Sensor_AHT('rhum','prct','AHT10_RHUM','%','{:.2f}')
    Sensor_ADC('pwm1','prct','SERVO','%','{:.2f}')
    Sensor_ADC('pwm2','prct','CH4_PID','%','{:.2f}')
    Sensor_ADC('pwm3','prct','COLDPLATE_PID','%','{:.2f}')
    Sensor_ADC('pwm4','prct','HOTPLATE_PID','%','{:.2f}')
    return tuple(Sensor.sensors())

#===============================================================================================#
#               INSTRUMENTS AND PROCESS CONFIGURATION                                           #
#===============================================================================================#

def configure_gvsi(gvsi:Instrument, arg:Namespace) -> None:
    """Configure the GVSI instrument (gvsi)."""
    # *RST;:STAT:PRES;:FORM:ASC:PREC 6;:ADC:NPLC 5.0;*CLS;:syst:beep MIN
    gvsi.write("*RST")                                          # reset to defaults
    time.sleep(2.0)                                             # time to boot up
    gvsi.write(":STAT:PRES")                                    # preset status enables
    gvsi.write(":FORM:ASC:PREC 6")                              # decimal digits ascii precision
    gvsi.write(f':ADC:NPLC {arg.nplc}')                         # NPLC integration
    gvsi.write("*CLS")                                          # clear errors
    if not arg.silent: gvsi.write(":syst:beep MIN")             # beep to signal start of communication

def gvsi_capabilities(cap_byte:int) -> str:
    cap_string:str = "("
    sep=''
    if cap_byte & 0x8000: cap_string += sep + "SCPI"; sep=','
    if cap_byte & 0x4000: cap_string += sep + "MEAS"; sep=','
    if cap_byte & 0x2000: cap_string += sep + "PWM_INPUTS"; sep=','
    if cap_byte & 0x1000: cap_string += sep + "PWM_PID"; sep=','
    if cap_byte & 0x0800: cap_string += sep + "SERVO"; sep=','
    if cap_byte & 0x0400: cap_string += sep + "PWM1"; sep=','
    if cap_byte & 0x0200: cap_string += sep + "PWM2"; sep=','
    if cap_byte & 0x0100: cap_string += sep + "PWM3"; sep=','
    if cap_byte & 0x0080: cap_string += sep + "PWM4"; sep=','
    if cap_byte & 0x0040: cap_string += sep + "PWM5"; sep=','
    if cap_byte & 0x0020: cap_string += sep + "ADC"; sep=','
    if cap_byte & 0x0010: cap_string += sep + "ADC_REL"; sep=','
    if cap_byte & 0x0008: cap_string += sep + "AHT1"; sep=','
    if cap_byte & 0x0004: cap_string += sep + "AHT2"; sep=','
    if cap_byte & 0x0002: cap_string += sep + "DIO"; sep=','
    if cap_byte & 0x0001: cap_string += sep + "DAC"; sep=','
    cap_string += ")"
    return cap_string

def valid_cmd(cmd):
    """Returns True for a valid command frame."""
    return cmd[0] in "*:" and len(cmd) > 1

#===============================================================================================#
#               DATA ACQUISITION: SPAWNED PROCESS                                               #
#===============================================================================================#

def DAQ_process(ctr_Q:mp.Queue, cmd_Q:mp.Queue, data_Q:mp.Queue, msg_Q:mp.Queue, err_Q:mp.Queue, pool_Q:list[mp.Queue], arg:Namespace, sensors: tuple[Sensor]):
    """
        Data acquisition process, interface via the serial port with the external SCPI instrument.
        This process runs in a separate processor core, and is spawned from the main program context.
        All interprocess communications are channelled through multiprocessing.Queue objects, that
        guarantee proper multicore context locking.
        
        The process starts a continuous sampling query of the form ":TRIG:CONT:READ? <>", and sends the 
        response stream through the queue data_Q. 
        It also looks for SCPI command requests via the cmd_Q stream, which is a many-to-one multiplexing 
        stream that is written by all connection handler threads.
        Command responses are sent to each requesting thread using a unidirectional one-to-one stream that 
        is uniquely assigned by each requesting thread.
        The requesting thread sends a command request on the cmd_Q stream, and then blocks on the response
        queue waiting for the command response. 
        All response queues are selected from a pool of preallocated mp.Queue objects in an array, and 
        requesting threads dynamically select an available response queue from a LRU list. The response 
        queue index is sent with the command string, and the requestor thread waits for the response on
        the selected response queue.

        This many-to-one command queue, associated to one-to-one dynamic response queues, allows effective
        and robust multiplexing of the DAQ to N remote processes. 
        
        The main thread can gracefully terminate the DAQ process by sending a "DAQ_ABORT" control message.
        If the DAQ process receives an exception and unexpectedly aborts, it sends "ABORT" and "EXIT" error messages.
    """
    # --- instantiate the instruments -------------------------------------------------------------
    gvsi = Instrument(gvsi_visa_id_1, baudrate = baudrate, start_delay = 2.0)
    if not gvsi:
        if not arg.quiet: msg_Q.put(f'GVSI {gvsi_visa_id_1} not found, trying {gvsi_visa_id_2}...')
        gvsi = Instrument(gvsi_visa_id_2, baudrate = baudrate, start_delay = 2.0)
    if gvsi:
        if not arg.quiet: msg_Q.put(f'{gvsi.idn_str()}, found')
        if arg.verbose: msg_Q.put(f'CAPABILITIES: {gvsi_capabilities(int(gvsi.ask(":SYST:CAP?")))}')
        configure_gvsi(gvsi, arg)
        if arg.verbose: msg_Q.put(f'DAQ Inputs: {tuple((x.label for x in sensors))},')
        # --- start SCPI command server -----------------------------------------
        if arg.verbose: err_Q.put("DAQ process: START")
        # --- make the SCPI for continuous trigger ------------------------------
        cont_read = False
        cmd_trig = ":TRIG:CONT:READ? "
        sep = ''
        for s in (x.name for x in sensors):
            cmd_trig += sep + s
            sep = ','
        if arg.debug: msg_Q.put(f'SCPI: \"{cmd_trig}\"')
        gvsi.write(cmd_trig)        # trigger continuous sampling of the selected channel names
        cont_read = True
        idx = 0
        tstart_ns = time.clock_gettime_ns(time.CLOCK_REALTIME)
        wdt_start = time.time()
        while True:
            try:
                # read continuous samping response
                fields = gvsi.read().split(',')
                wavetime = (time.clock_gettime_ns(time.CLOCK_REALTIME) - tstart_ns) * 1e-9
                record = (idx,wavetime) + tuple([conv_float(x.strip()) for x in fields])
                idx += 1
                data_Q.put(record)
                if not cmd_Q.empty():
                    cmd = cmd_Q.get()
                    if hasattr(cmd, "cmd") and hasattr(cmd, "resp_Qn") and hasattr(cmd, "wait"):
                        # break continuous sampling to send the async command, and resume sampling
                        cmdstr = cmd.cmd.upper()
                        resp_Q = pool_Q[cmd.resp_Qn]
                        if valid_cmd(cmdstr):
                            if any(x in cmdstr for x in(":CMD:TIME:RST",)):
                                tstart_ns = time.clock_gettime_ns(time.CLOCK_REALTIME)
                                response = f'{wavetime}'
                                resp_Q.put(response)
                            else:
                                # stop continuous sampling
                                if arg.debug: msg_Q.put(f'SCPI: \"Q\"')
                                gvsi.write("Q")
                                cont_read = False
                                # send async command and get response if query
                                response = "OK"
                                time.sleep(cmd.wait)
                                if arg.debug: msg_Q.put(f'SCPI: \"{cmdstr}\"')
                                if '?' in cmdstr:
                                    response = gvsi.ask(cmdstr)
                                    if arg.debug: msg_Q.put(f'RESPONSE: \"{response}\"')
                                else:
                                    gvsi.write(cmdstr)
                                # test length of response, if too large the :TRIG:CONT:READ? is probably still running
                                if len(response) > 100:
                                    # --- RE-SYNC THE STREAM ---
                                    print(f'Unexpected response length = {len(response)}: {response}')
                                    time.sleep(0.6)
                                    gvsi.write("Q")
                                    time.sleep(0.6)
                                    gvsi.write("Q")
                                    time.sleep(0.6)
                                    gvsi.write("Q")
                                    time.sleep(0.6)
                                    gvsi.write("*cls")
                                    print(f'Retrying {cmdstr}...')
                                    time.sleep(1.0)
                                    if '?' in cmdstr:
                                        response = gvsi.ask(cmdstr)
                                        if arg.debug: msg_Q.put(f'RESPONSE: \"{response}\"')
                                    else:
                                        gvsi.write(cmdstr)
                                    if len(response) > 100:
                                        print(f'Restarting the serial port...')
                                        sav_visa_str = gvsi.get_visa_str()
                                        sav_baudrate = gvsi.get_baudrate()
                                        gvsi.close()
                                        gvsi = Instrument(sav_visa_str, baudrate = sav_baudrate, start_delay = 2.0)
                                        if not gvsi:
                                            print(f'Attempt to restart the serial port failed: {sav_visa_str}, {sav_baudrate}')
                                            raise(Exception("DAQ RESTART ERROR"))
                                        time.sleep(0.6)
                                        response = gvsi.ask(":SYST:CAP?")
                                        if len(response) > 6:
                                            print(f'Failed attempt of resync: {response=}')
                                            raise(Exception("DAQ SYNC ERROR"))
                                        response = "NOK"
                                        cont_read = False
                                resp_Q.put(response)
                                # resume continuous sampling
                                # time.sleep(0.2)
                                if arg.debug: msg_Q.put(f'SCPI: \"{cmd_trig}\"')
                                gvsi.write(cmd_trig)
                                cont_read = True
                        else:
                            resp_Q.put("NOK")
                if not ctr_Q.empty():
                    if "DAQ_ABORT" in ctr_Q.get():
                        if cont_read:
                            if arg.debug: msg_Q.put(f'SCPI: \"Q\"')
                            gvsi.write("Q")
                            cont_read = False
                        time.sleep(1000e-3)
                        if arg.debug: msg_Q.put(f'SCPI: \"*RST\"')
                        gvsi.write("*RST")
                        time.sleep(2000e-3)
                        break
                if cont_read and ((time.time() - wdt_start) > 10.0):
                    # watchdog keepalive during continuous reading
                    wdt_start = time.time()
                    # if arg.debug: msg_Q.put(f'SCPI: \" \"')
                    gvsi.write(' ')
            except Exception as e:
                if not arg.silent: err_Q.put(f'DAQ process ABORT. Exception: {e}')
                break
        time.sleep(0.1)
        if not arg.silent: gvsi.write(":syst:beep MIN")
        gvsi.close()
        if not arg.silent: err_Q.put("DAQ process: EXIT")
    else:
        if arg.verbose: msg_Q.put("Gridvortex GVSI NOT_FOUND!")
        if not arg.silent: err_Q.put("DAQ process: EXIT")

#===============================================================================================#
#               CMD SOCKET SERVER                                                               #
#===============================================================================================#

evt_terminate = threading.Event()           # All event loops terminate when set to True
cmd_lock = threading.Lock()                 # locks other command handlers
buf_lock = threading.Lock()                 # locks buffer access

def conv_float(x):
    try:
        return float(x.replace('C','').replace('%','').replace('V','').replace('s',''))
    except:
        print(f'conv_float({x}): nan!')
        return float('nan')
    
def find_time_index(t:float):
    """scans the time index and returns the next valid subscript greater than or equal to (t) if the time is found, or the extreme indexes if not. """
    try:
        while len(bufidx[0]) < 2:
            bufidx.pop(0)
        while len(bufidx[-1]) < 2:
            bufidx.pop(-1)
        if (t >= bufidx[0][1]) and (t <= bufidx[-1][1]):
            for p in range(len(bufidx)):
                if len(bufidx[p]) > 1:
                    if t <= bufidx[p][1]:
                        return p
                else:
                    print(f'find_time_index(): Removed orphan tuple p={p}')
                    bufidx.pop(p)
            else:
                return len(bufidx)-1
        elif t < bufidx[0][1]:
            return 0
        else:
            return len(bufidx)-1
    except IndexError:
        return 0

def median_avg(s, p1, period):
    """Compute the median average for a buffer slice. s = sensor index, pos = ending position, period = integration length."""
    p0 = find_time_index(bufidx[p1][1] - period)
    # print(f'{p0=}, {bufidx[p0][1]}')
    if p0 == -1:
        p0 = 0
    # extract the tuple of sensors values from the slice, and index the sensor tuple to extract only the value of that sensor. 
    X = tuple(t[s] for t in bufadc[p0:p1+1])
    m = np.median(X)
    return m

def cmd_handler(client_socket, addr, daq_cmd_clients:list, cmd_Q:mp.Queue, msg_Q:mp.Queue, err_Q:mp.Queue, pool_Q:list[mp.Queue], free_Qn:list[int]):
    """
        This is the DAQ cmd socket handler thread.
        It runs until the connection is closed by the client.
        The daq_cmd_clients[] list is maintained with all active connections.
        IPC is done via Queues:
            cmd_Q:  channel remote commands to the DAQ_process, shared by handlers.
            msg_Q:  async stream for print messages.
            err_Q:  async stream for error messages.
        IPC for response data:
            resp_X: pool of preallocated async stream Queues.
            resp_L: list of available resp_X queues.
            
        Each handler dynamically binds a response queue from the pool of available
        response queues, to be used for the response stream sent by the DAQ_process.
        Each command is sent with a unique associated response queue, ton allow 
        multiplexing of commands and responses.

        CMDs: 
            ":CMD:HMC:SHUTDOWN"                                         Force server shutdown.
            ":CMD:VERS?"                                                Request server version.
            ":CMD:BUFSZ?"                                               Request buffer size.
            ":CMD:NAMES?"                                               Request DATA field names.
            ":CMD:TIME:RST"                                             Reset waveform time to 0.000000s, adjusting all datapoints in the buffers. 
            ":CMD:TIME:MIN?"                                            Request minimum buffer timestamp.
            ":CMD:TIME:MAX?"                                            Request maximum buffer timestamp.
            ":CMD:DROP <speed>"                                         Droplets collector. Command the droplets servo to a full excursion at the specified speed.
            ":CMD:READ? ALL | {<fieldname>[[, <time>], <avg_period>]}"  Request current value for a given channel, or value at <time>. Optionally give an averaging period. 
            ":CMD:BASE:DRIFT? <fieldname>[, <interval>]"                Request the specified channel baseline drift for the specified period or for the last minute, and report in units/minute.
            ":CMD:PEAK? <fieldname>, <time>, <interval>"                Request find first peak for the specified channel, in the time window provided.
    """

    # ----------------- inner functions ---------------------

    def send_cmd(cmdstr, wait=0.0):
        """Helper function to send a cmd through the cmd Queue."""
        cmd.cmd = cmdstr
        cmd.wait = wait
        cmd_Q.put(cmd)
        return pool_Q[cmd.resp_Qn].get()

    # --------------------------------------------------------

    # Allocate a free response queue from the pool, and associate the queue in the cmd object.
    if len(free_Qn):
        daq_cmd_clients.append(client_socket)
        resp_Qn = free_Qn.pop()
        if arg.verbose: msg_Q.put(f'Accepted cmd connection from {addr}, using queue {resp_Qn}.')
        cmd = Namespace(cmd="", resp_Qn=resp_Qn, wait=0.0)
        # continue serving the connection until it is closed by the peer or the termination event is set.
        while not evt_terminate.is_set():
            try:
                # blocks until command arrives
                data = client_socket.recv(2048)
                if not data:
                    if arg.verbose: msg_Q.put(f'Client {addr} disconnected.')
                    break
                # parse the command string to isolate arguments
                cmdstr = data.decode().strip()
                fields = [x for x in cmdstr.upper().replace(',',' ').split()]
                # ---- handle pseudo commands -----------------------------------------------------
                if any(x == fields[0] for x in(":CMD:HMC:SHUTDOWN",)): 
                    # ":CMD:HMC:SHUTDOWN"
                    if arg.verbose: msg_Q.put(f'Client {addr}: Received {fields[0]}! Terminating the application.')
                    client_socket.sendall("ABORT".encode(encoding="ascii",errors="replace"))
                    evt_terminate.set()
                elif any(x == fields[0] for x in(":CMD:DROP",)):
                    # ":CMD:DROP <NRf>"
                    # perform the DROP pseudo command to collect droplets, and return the servo to MIN position.
                    response = "ERR"
                    try:
                        speed = float(fields[1]) if len(fields) > 1 else 0.0
                        min = 0.0
                        max = 0.0
                        with cmd_lock:
                            send_cmd(f':pwm1:val min')
                        time.sleep(0.5)
                        with cmd_lock:
                            min = float(send_cmd(":pwm1:min?"))
                            max = float(send_cmd(":pwm1:max?"))
                            send_cmd(f':pwm1:move max, {speed}')
                        if speed != 0.0:
                            wait = (max - min) / speed
                            time.sleep(wait + 0.5)
                        with cmd_lock:
                            send_cmd(f':pwm1:move min, max')
                        response = "OK"
                    except Exception as e:
                        response = f'ERR: {e}'
                    finally:
                        client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
                elif any(x == fields[0] for x in(":CMD:VERS?",)):
                    # ":CMD:VERS?"
                    # Request server version
                    response = f'{script_ver}'
                    client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
                elif any(x == fields[0] for x in(":CMD:BUFSZ?",)):
                    # ":CMD:BUFSZ?"
                    # Request buffer size.
                    response = f'{arg.bufsize}'
                    client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
                elif any(x == fields[0] for x in(":CMD:TIME:MIN?",)):
                    # ":CMD:TIME:MIN?"
                    # Request minimum buffer timestamp.
                    tmin = bufidx[0][1]
                    response = f'{tmin}'
                    client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
                elif any(x == fields[0] for x in(":CMD:TIME:MAX?",)):
                    # ":CMD:TIME:MAX?"
                    # Request maximum buffer timestamp.
                    tmax = bufidx[-1][1]
                    response = f'{tmax}'
                    client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
                elif any(x == fields[0] for x in(":CMD:NAMES?",)):
                    # ":CMD:NAMES?"
                    # Request DATA field names
                    response = f'TIME,' + ','.join(Sensor.labels())
                    client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
                elif any(x == fields[0] for x in(":CMD:TIME:RST",)):
                    # ":CMD:TIME:RST"
                    # Reset waveform time to 0.000000s, adjusting all datapoints in the buffers. 
                    cmd.cmd = cmdstr.upper()
                    with cmd_lock:
                        cmd_Q.put(cmd)
                        resp = pool_Q[cmd.resp_Qn].get()
                        try:
                            toffs = float(resp)
                        except:
                            toffs = 0.0
                    with buf_lock:
                        for i in range(len(bufidx)):
                            bufidx[i][1] -= toffs
                    client_socket.sendall(resp.encode(encoding="ascii",errors="replace"))
                elif any(x == fields[0] for x in(":CMD:READ?",)):
                    # ":CMD:READ? ALL | {<fieldname> [[, <time>], <avg_period>]}"
                    # Request current value for a given channel, or value at <time>. Optionally give an averaging period. 
                    # If ALL is specified, retrieve the most current record with all DAQ channels
                    response = "ERR"
                    try:
                        if fields[1] == "ALL":
                            with buf_lock:
                                wavetime = bufidx[-1][1]
                                record = bufadc[-1]
                            strings = tuple((s.format(record[i]) for i, s in enumerate(Sensor.sensors())))
                            response = f'{wavetime:.6f}s,' + ','.join(strings)
                        if fields[1] in Sensor.labels():
                            sns = tuple(Sensor.labels()).index(fields[1])
                            if len(fields) > 2:
                                t = bufidx[-1][1] if fields[2].upper() == "MAX" else bufidx[0][1] if fields[2].upper() == "MIN" else conv_float(fields[2])
                            else:
                                t = bufidx[-1][1]
                            with buf_lock:
                                if (t >= bufidx[0][1]) and (t <= bufidx[-1][1]):
                                    pos = find_time_index(t)
                                    if len(fields) > 3:
                                        avg_period = conv_float(fields[3])
                                        response = tuple(Sensor.sensors())[sns].format(median_avg(sns, pos, avg_period))
                                    else:
                                        response = tuple(Sensor.sensors())[sns].format(bufadc[pos][sns])
                    except Exception as e:
                        response = f'ERR: {e}'
                    finally:
                        client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
                elif any(x == fields[0] for x in(":CMD:BASE:DRIFT?",)):
                    # ":CMD:BASE:DRIFT? <fieldname>[, <interval>]"
                    # Request the specified channel baseline drift for the specified period or for the last minute, and report in units/minute.
                    response = "ERR"
                    try:
                        if fields[1] in Sensor.labels():
                            sns = tuple(Sensor.labels()).index(fields[1])
                            # print(f'{sns=}')
                            if len(fields) > 2:
                                interval = conv_float(fields[2])
                            else:
                                interval = 60.0
                            # print(f'{interval=}')
                            if interval == 0.0: interval = 60.0
                            with buf_lock:
                                # get the time interval
                                t1 = bufidx[-1][1]
                                t0 = t1 - interval
                                if (t0 < bufidx[0][1]): t0 = bufidx[0][1]
                                # print(f'{t0=},{t1=}')
                                # find the datapoints indexes for the time coordinates
                                p0 = find_time_index(t0)
                                p1 = find_time_index(t1)
                                # print(f'{p0=},{p1=}')
                                # compute the median baseline value at the 2 interval ends with 1.0s of integration time
                                b0 = tuple(Sensor.sensors())[sns].val(median_avg(sns, p0, 1.0))
                                b1 = tuple(Sensor.sensors())[sns].val(median_avg(sns, p1, 1.0))
                                # print(f'{b0=},{b1=}')
                                # compute the drift and differentiate in 1 minute
                                drift = b1 - b0
                                diff = drift / interval * 60.0
                                response = f'{diff}'
                    except Exception as e:
                        response = f'ERR: {e}'
                    finally:
                        client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
                elif any(x == fields[0] for x in(":CMD:PEAK?",)):
                    # ":CMD:PEAK? <fieldname>, <time>, <interval>"
                    # returns "<pktim>,<pkval>"
                    # Request find first peak for the specified channel, in the time window provided.
                    response = "ERR"
                    try:
                        if fields[1] in Sensor.labels():
                            sns = tuple(Sensor.labels()).index(fields[1])
                            # print(f'{sns=}')
                            # print(f'{fields=}')
                            if len(fields) > 3:
                                t0 = conv_float(fields[2])
                                interval = conv_float(fields[3])
                                # print(f'{t0=}, {interval=}')
                                with buf_lock:
                                    # get the [t0:t1] time interval
                                    t1 = t0 + interval
                                    if (t0 < bufidx[0][1]): t0 = bufidx[0][1]
                                    if (t1 > bufidx[-1][1]): t1 = bufidx[-1][1]
                                    # print(f'{t0=},{t1=}')
                                    # find the [p0:p1] datapoints indexes for the time coordinates
                                    p0 = find_time_index(t0)
                                    p1 = find_time_index(t1)
                                    # print(f'{p0=},{p1=}')
                                    # find the highest peak in the interval
                                    b0 = (tuple(Sensor.sensors())[sns].val(median_avg(sns, p0, 1.0))) + 1e-3
                                    # print(f'{b0=}')
                                    x = tuple(t[1] for t in bufidx[p0:p1+1])
                                    y = tuple(tuple(Sensor.sensors())[sns].val(t[sns]) for t in bufadc[p0:p1+1])
                                    peaks, _ = find_peaks(np.array(y), height = b0, distance = (p1-p0) / 2.0)
                                    if len(peaks) > 0:
                                        pkval: float = -1e6
                                        pktim: float = 0.0
                                        for i in peaks:
                                            if y[i] > pkval:
                                                pkval = y[i]
                                                pktim = x[i]
                                            elif (pkval - y[i]) > 1000e-6:
                                                break
                                        # print(f'{pktim=},{pkval=}')
                                        if pkval > b0:
                                            response = f'{pktim},{pkval}'
                    except Exception as e:
                        response = f'ERR: {e}'
                    finally:
                        client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
                elif any(x == fields[0] for x in(":TRIG:CONT:READ?",)):
                    # remove the CONT read from SCPI trigger command, and issue a single read instead.
                    cmd.cmd = cmdstr.upper().replace(":CONT", "")
                    with cmd_lock:
                        cmd_Q.put(cmd)
                        resp = pool_Q[cmd.resp_Qn].get()
                    client_socket.sendall(resp.encode(encoding="ascii",errors="replace"))
                elif any(x in fields[0] for x in("*RST",":SAV",":RCL")):
                    # intercept the *RST command any EEPROM read/write command and insert a 2.0s delay to account for firmware response time.
                    cmd.cmd = cmdstr
                    cmd.wait = 2.0
                    with cmd_lock:
                        cmd_Q.put(cmd)
                        resp = pool_Q[cmd.resp_Qn].get()
                    client_socket.sendall(resp.encode(encoding="ascii",errors="replace"))
                else:
                    # send the SCPI command to the ACQ process and wait on the response
                    cmd.cmd = cmdstr
                    with cmd_lock:
                        cmd_Q.put(cmd)
                        resp = pool_Q[cmd.resp_Qn].get()
                    client_socket.sendall(resp.encode(encoding="ascii",errors="replace"))
            except OSError as e:
                if not arg.silent: err_Q.put(f'cmd_handelr: Client {addr} Socket error: {e}')
                break
            except Exception as e:
                if not arg.silent: err_Q.put(f'cmd_handelr: Error handling client {addr}: {e}')
                break
        free_Qn.append(resp_Qn)
        if arg.verbose: msg_Q.put(f'CMD Handler {addr}: releasing queue {resp_Qn}.')
    else:
        if not arg.silent: err_Q.put(f'CMD Handler {addr} ERROR: out of queue resources. Closing connection.')
    if client_socket: 
        client_socket.close()
        if client_socket in daq_cmd_clients: daq_cmd_clients.remove(client_socket)
        if arg.verbose: msg_Q.put(f'Connection with {addr} closed.')
    if arg.verbose: msg_Q.put(f'CMD Handler {addr}: thread stopped.')

def cmd_server_listener(server_socket, daq_cmd_clients:list, cmd_Q:mp.Queue, msg_Q:mp.Queue, err_Q:mp.Queue, pool_Q:list[mp.Queue], free_Qn:list[int]):
    """
        This thread runs forever the cmd server socket listener, and starts 
        a new handler thread for each accepted connection.
        The main thread sets the evt_terminate event and closes the 
        cmd socket server to terminate the listener thread.
    """
    client_socket = None
    while not evt_terminate.is_set():
        try:
            # blocks until an incoming connection is received
            client_socket, addr = server_socket.accept()
            # runs each client handler in a thread
            cmd_handler_thread = threading.Thread(target=cmd_handler, args=(client_socket, addr, daq_cmd_clients, cmd_Q, msg_Q, err_Q, pool_Q, free_Qn))
            cmd_handler_thread.daemon = True
            cmd_handler_thread.start()
        except OSError as e:
            if not arg.silent: err_Q.put(f"Cmd Server Listener OSError: {e}")
            break
        except Exception as e:
            if not arg.silent: err_Q.put(f"Cmd Server Listener Exception: {e}")
            break
    if server_socket: server_socket.close()
    if arg.verbose: msg_Q.put("Cmd Server thread stopped.")

def start_cmd_server(host, port, cmd_Q:mp.Queue, msg_Q:mp.Queue, err_Q:mp.Queue, pool_Q:list[mp.Queue], free_Qn:list[int], arg:Namespace):
    """
        This function opens a socket listener and creates a server listener thread. 
        Returns the server socket and a dynamic list of all clients sockets.
        The daq_cmd_clients[] list is maintained by the connection handlers with the active
        connections.
    """
    daq_cmd_clients = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(arg.max_handlers)
    if arg.verbose: msg_Q.put(f"Cmd Server listening on {server_socket.getsockname()}")
    cmd_server_thread = threading.Thread(target=cmd_server_listener, args=(server_socket, daq_cmd_clients, cmd_Q, msg_Q, err_Q, pool_Q, free_Qn))
    cmd_server_thread.daemon = True
    cmd_server_thread.start()
    return server_socket, daq_cmd_clients

#===============================================================================================#
#               DATA SOCKET SERVER                                                              #
#===============================================================================================#

def data_handler(client_socket, addr, data_clients:list, data_queues:list, msg_Q:mp.Queue, err_Q:mp.Queue):
    """
        This is the DAQ data socket stream handler thread.
        It runs until the connection is closed by the client.
        The data_clients[] list is maintained with all active connections.
        The data_queues[] list holds the stream output queues for all data threads.
        IPC is done via Queues:
            msg_Q:  async stream for print messages.
            err_Q:  async stream for error messages.
        The data handler will instantiate a new mp.Queue() object and add it to the pool of active data stream queues. 
        The main thread distributes the DAQ data records to all active data stream queues. 
    """
    # Allocate a free data stream queue, and add it to the list of data stream queues.
    data_clients.append(client_socket)
    if arg.verbose: msg_Q.put(f'Accepted data stream connection from {addr}.')
    # continue serving the connection until it is closed by the peer or the termination event is set.
    while not evt_terminate.is_set():
        try:
            # blocks until command arrives
            data = client_socket.recv(2048)
            if not data:
                if arg.verbose: msg_Q.put(f'Client {addr} disconnected.')
                break
            # parse the command string to isolate arguments
            cmdstr = data.decode().strip()
            fields = [x for x in cmdstr.upper().replace(',',' ').split()]
            # ---- handle DATA control commands ---------------------------------------------------
            if any(x == fields[0] for x in(":DATA:LISTEN",)): 
                # ":DATA:LISTEN"
                # continuous raw data stream until socket is closed by client
                data_Q = mp.Queue()
                data_queues.append(data_Q)
                while True:
                    try:
                        while not data_Q.empty():
                            # send the most recent datapoints to the DATA stream socket
                            record = data_Q.get()
                            client_socket.sendall(record.encode(encoding="ascii",errors="replace"))
                    except Exception as e:
                        if not arg.silent: err_Q.put(f'data_handler: Error: {e}')
                        break
                data_queues.remove(data_Q)
                data_Q.close()
                break
            elif any(x == fields[0] for x in(":DATA:NAMES?",)):
                # ":DATA:NAMES?"
                # Request DATA field names
                response = f'TIME,' + ','.join(Sensor.labels())
                client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
            elif any(x == fields[0] for x in(":DATA:READ?",)):
                # ":DATA:READ? <start_time>[, <end_time>]"
                # Send all data records from <start_time> to <end_time>. Times in seconds.
                # The last record sent is "OK", finishing the command response.
                # If only one time is given, respond with a single data record.
                # If no time is given, respond with "ERR".
                # If the requested time window is invalid, respond with "ERR".
                response = "ERR"
                try:
                    p1 = len(bufidx)
                    p0 = p1 - 1
                    if len(fields) > 1:
                        t0 = conv_float(fields[1])
                        p0 = find_time_index(t0)
                        t1 = None
                        p1 = p0+1
                    if len(fields) > 2:
                        t1 = conv_float(fields[2])
                        p1 = find_time_index(t1) + 1
                    # collect all data lines in a local buffer
                    databuf = []
                    with buf_lock:
                        for idx, record in zip(bufidx[p0:p1], bufadc[p0:p1]):
                            wavetime = idx[1]
                            strings = tuple((s.format(record[i]) for i, s in enumerate(Sensor.sensors())))
                            datarec = f'{wavetime:.6f}s,' + ','.join(strings) + "\n"
                            databuf.append(datarec)
                    # send the data records to the requester
                    while len(databuf):
                        response = databuf.pop(0)
                        client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
                    response = "OK"
                except Exception as e:
                    response = f'ERR: {e}'
                finally:
                    client_socket.sendall(response.encode(encoding="ascii",errors="replace"))
            else:
                # command not recognized, send "ERR"
                client_socket.sendall("ERR".encode(encoding="ascii",errors="replace"))
        except OSError as e:
            if not arg.silent: err_Q.put(f'data_handler: Client {addr} Socket error: {e}')
            break
        except Exception as e:
            if not arg.silent: err_Q.put(f'data_handler: Error handling client {addr}: {e}')
            raise e
            break
    if client_socket: 
        client_socket.close()
        if client_socket in data_clients: data_clients.remove(client_socket)
        if arg.verbose: msg_Q.put(f'Connection with {addr} closed.')
    if arg.verbose: msg_Q.put(f'Data Handler {addr}: thread stopped.')

def data_server_listener(server_socket, data_clients:list, data_queues:list, msg_Q:mp.Queue, err_Q:mp.Queue):
    """
        This thread runs forever the data server socket listener, and starts 
        a new handler thread for each accepted connection.
        The main thread sets the evt_terminate event and closes the 
        data socket server to terminate the listener thread.
    """
    client_socket = None
    while not evt_terminate.is_set():
        try:
            # blocks until an incoming connection is received
            client_socket, addr = server_socket.accept()
            # runs each client handler in a separate thread
            data_handler_thread = threading.Thread(target=data_handler, args=(client_socket, addr, data_clients, data_queues, msg_Q, err_Q))
            data_handler_thread.daemon = True
            data_handler_thread.start()
        except OSError as e:
            if not arg.silent: err_Q.put(f"Data Server Listener OSError: {e}")
            break
        except Exception as e:
            if not arg.silent: err_Q.put(f"Data Server Listener Exception: {e}")
            break
    if server_socket: server_socket.close()
    if arg.verbose: msg_Q.put("Data Server thread stopped.")

def start_data_server(host, port, msg_Q:mp.Queue, err_Q:mp.Queue, arg:Namespace):
    """
        This function opens a socket listener and creates a server listener thread. 
        Returns the server socket and a dynamic list of all clients sockets.
        The data_clients[] list is maintained by the connection handlers with the active
        connections.
    """
    data_clients = []
    data_queues = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(arg.max_handlers)
    if arg.verbose: msg_Q.put(f"Data Server listening on {server_socket.getsockname()}")
    data_server_thread = threading.Thread(target=data_server_listener, args=(server_socket, data_clients, data_queues, msg_Q, err_Q))
    data_server_thread.daemon = True
    data_server_thread.start()
    return server_socket, data_clients, data_queues

#===============================================================================================#
#               MAIN                                                                            #
#===============================================================================================#

def main():
    # --- command line options --------------------------------------------------------------------
    global arg
    arg = get_options()
    
    # --- user hello ------------------------------------------------------------------------------
    if not arg.quiet:
        print()
        print(vstr := f'{sys.argv[0]} version {script_ver}, {copyright_str}')
        print('-' * len(vstr), flush=True)

    if arg.verbose:
        print(f'NPLC: {arg.nplc} ({format_SI(arg.nplc * 17e-3)}s)\r\n', end="", flush=True)

    # --- create sensors instances ----------------------------------------------------------------
    sensors = create_sensors()

    # --- declare global and prealocate the data buffer objects -----------------------------------
    global recno, bufidx, bufadc
    recno = 0
    bufidx = []
    bufadc = []
    
    # --- create the queues for the DAQ process  --------------------------------------------------
    mp.set_start_method('spawn')
    ctr_Q = mp.Queue()      # DAQ process control messages
    cmd_Q = mp.Queue()      # DAQ commands from remote sockets
    data_Q = mp.Queue()     # continuous sampling DAQ responses
    msg_Q = mp.Queue()      # async stream for print messages
    err_Q = mp.Queue()      # async stream for error messages
    pool_Q = [mp.Queue() for x in range(arg.max_handlers)]  # preallocated response Queue pool
    free_Qn = [x for x in range(arg.max_handlers)]          # pool free index list
    # --- spawn DAQ process -----------------------------------------------------------------------
    p1 = mp.Process(target = DAQ_process, args = [ctr_Q, cmd_Q, data_Q, msg_Q, err_Q, pool_Q, arg, sensors])
    p1.daemon = True        # force process termination if parent dies
    p1.start()              # spawn data acquisition CPU process
    time.sleep(1.0)
    while not msg_Q.empty(): 
        print(f'{msg_Q.get()}', flush=True)
    while not err_Q.empty():
        err_msg = err_Q.get()
        print(f'{err_msg}', flush=True)
        if any(x in err_msg for x in("ABORT","EXIT")):
            p1.join(0.1)
            p1.terminate()
            if not arg.silent: print(f'Exiting ...', flush=True)
            sys.exit(1)
    if arg.verbose: 
        print(f'Timestamp: {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(arg.timestamp))}', flush=True)
        print(f'Buffer size: {arg.bufsize}s.', flush=True)
        
    # --- start socket servers ----------------------------------------------------------------
    daq_cmd_server, daq_cmd_clients = start_cmd_server(arg.host_addr, arg.cmd_port, cmd_Q, msg_Q, err_Q, pool_Q, free_Qn, arg)
    daq_data_server, data_clients, data_queues = start_data_server(arg.host_addr, arg.data_port, msg_Q, err_Q, arg)
    
    # --- toplevel thread loop ----------------------------------------------------------------
    # monitors the connections and print threads messages
    wavetime = 0.0
    while not evt_terminate.is_set():
        try:
            # --- handle data_Q: capture the data in buffers ---
            while not data_Q.empty():
                try:
                    with buf_lock:
                        (recno, wavetime, *record) = data_Q.get()
                        bufidx.append([recno,wavetime])
                        bufadc.append(record)
                        if (bufidx[-1][1] - bufidx[0][1]) > arg.bufsize:
                            bufidx.pop(0)
                            bufadc.pop(0)
                    strings = tuple((s.format(record[i]) for i, s in enumerate(sensors)))
                    outrec = f'{wavetime:.6f}s,' + ','.join(strings)
                    for q in data_queues:
                        q.put(outrec)
                except Exception as e:
                    print(f'Exception: {e}')
            # --- handle msg_Q: print messages ---
            if not msg_Q.empty(): print(f'{msg_Q.get()}', flush=True)
            # --- handle err_Q: process error messages ---
            if not err_Q.empty():
                err_msg = err_Q.get()
                print(f'{err_msg}', flush=True)
                if any(x in err_msg for x in("ABORT","EXIT")):
                    evt_terminate.set()
        except KeyboardInterrupt:
            if not arg.silent: print("\nInterrupted.")
            evt_terminate.set()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = exc_tb.tb_frame.f_code.co_filename
            line_number = exc_tb.tb_lineno
            print(f"An exception occurred:")
            print(f"Type: {exc_type.__name__}")
            print(f"Message: {e}")
            print(f"File: {fname}")
            print(f"Line Number: {line_number}")
            # You can also print the full traceback for more detailed information
            traceback.print_exc() 
            if not arg.silent: print(f'\nException! {e}. Exited.')
            evt_terminate.set()
    # signal the process to exit acquisition loop
    if not arg.quiet: print("waiting DAQ process exit...", flush=True)
    ctr_Q.put("DAQ_ABORT")
    time.sleep(1.0)
    p1.join(0.1)
    p1.terminate()
    # terminate all threads event loops
    if arg.verbose: 
        print(f'Shutting down the server...')
        if threading.active_count() > 1:
            print(f'Currently {threading.active_count() - 1} active threads.')
            for t in (x for x in threading.enumerate() if x != threading.current_thread()):
                print(f'    Thread {t.name}')
    evt_terminate.set()
    while not err_Q.empty(): print(f'{err_Q.get()}', flush=True)
    while not msg_Q.empty(): print(f'{msg_Q.get()}', flush=True)
    # close all outstanding socket connections
    if len(daq_cmd_clients):
        if arg.verbose: print(f'Closing remaining {len(daq_cmd_clients)} opened CMD conections:')
        for s in daq_cmd_clients:
            try:
                if arg.verbose: print(f'    {s.getpeername()}')
            except Exception as e:
                if not arg.silent: print(f'Exception {e} while accessing CMD client socket data.')
        for s in daq_cmd_clients:
            try:
                s.close()
            except Exception as e:
                if not arg.silent: print(f'Exception {e} while closing CMD socket.')
    if len(data_clients):
        if arg.verbose: print(f'Closing remaining {len(data_clients)} opened DATA conections:')
        for s in data_clients:
            try:
                if arg.verbose: print(f'    {s.getpeername()}')
            except Exception as e:
                if not arg.silent: print(f'Exception {e} while accessing DATA client socket data.')
        for s in data_clients:
            try:
                s.close()
            except Exception as e:
                if not arg.silent: print(f'Exception {e} while closing DATA socket.')
    if len(data_queues):
        if arg.verbose: print(f'Closing remaining {len(data_queues)} opened DATA queues...')
        for q in data_queues:
            try:
                q.close()
            except Exception as e:
                if not arg.silent: print(f'Exception {e} while closing DATA queue.')
    # close server sockets
    daq_cmd_server.close()
    daq_data_server.close()

    # --- epilog ------------------------------------------------------------------------------
    time.sleep(0.1)
    if threading.active_count() > 1:
        if arg.verbose: print(f'Terminating remaining {threading.active_count() - 1} active threads:')
        for t in (x for x in threading.enumerate() if x != threading.current_thread()):
            if arg.verbose: print(f'    Terminating thread {t.name}...')
            t.join(0.1)
    time.sleep(0.1)
    if not arg.silent: print(f'Exiting ...', flush=True)
    # os._exit(1)
    sys.exit(1)

# --- program starts here  ------------------------------------------------------------------------
if __name__  == '__main__':
    main()

