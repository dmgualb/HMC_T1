#!/usr/bin/env python3

###################################################################################################
#   HMC MASTER - CH4 MASTER ANALYSIS CONTROL MODULE
#   -----------------------------------------------
#
#   DESCRIPTION
#   -----------
# 
#   This is the control module for the Alacer Bio HMC Lab instrument. 
#   It contains the high level business logic for the HMC (Hydrogen / Methane / CO2) analysis, 
#   and controls the lower layer daq_server via socket IPC channels. 
# 
#   The following ports are used by the Master:
#           SYS CMD PORT:       59000       Command Request/response interface to the DAQ_SERVER.
#           DAQ DATA PORT:      58000       Data stream channel, receives DAQ datapoints stream.
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
#   BUGS:
#   -----
#
#--------------------------------------------------------------------------------------------------
#   TODO:
#   -----
#           # washing procedure: pull from vent, push to intake
#           - peak command with filter
#           - bulk data capture and waveform file saving 
#           - calibration commands and calib data file save/restore
#           - DISCUSS still air correction
# 
#
###################################################################################################

#COMPORT = '/dev/cu.usbserial-MULTIPLEX_V01'
COMPORT = 'COM6'

from dataclasses import dataclass, field
from overrides import override
from argparse import Namespace
import multiprocessing as mp
from collections import namedtuple
import math
import numpy as np
import time
import re
from io import TextIOWrapper
import os
import sys
import getopt
from instrument import Instrument
import socket
import threading
from serial_ctrl import SerialCtrl
# import hid

script_ver      = "v0.9.432"
copyright_str   = "Copyright (c) 2023, 2024, 2025 Alacer Biomedica"
license_str     = "All Rights Reserved."
license_short   = "This is proprietary software, all rights reserved by Alacer Biomedica."

#===============================================================================================#
#               COMMAMD LINE OPTIONS PROCESSING                                                 #
#===============================================================================================#

def defaults() -> Namespace:
    """Return a namespace with the default arg values."""
    default = Namespace()
    default.quiet           = None                              # suppress status messages but display measurement records
    default.silent          = None                              # suppress interactive plot graph and all stdout messages
    default.verbose         = None                              # verbose mode, write all messages to stdout
    default.boot            = None                              # perform full tests at startup
    default.debug           = None                              # show SCPI messages
    default.nplc            = 5.0                               # ADC NPLC integration constant
    default.host_addr       = "127.0.0.1"                       # socket server host address
    default.cmd_port        = 57000                             # DAQ cmd port
    default.data_port       = 58000                             # DAQ continuous data stream port
    default.vendor_id       = 0x23EC                            # Substitua pelo VID real
    default.product_id      = 0x0002                            # 0x0001 multiplex / 0x0002 pump
    default.wait_hid        = 0.05                              # default wait for HID
    default.quiet_hid       = True                              # debug OFF by default
    default.h2_base_drift   = 5.0                               # mV/min of drift criteria
    default.ch4_base_drift  = 2.0                               # mV/min of drift criteria
    default.bufsize         = 600                               # size of the buffer in seconds
    default.wash_cycles     = 0                                 # number of wash cycles
    default.sample_size     = 0                                 # volume for partial fill
    default.operation       = None                              # operation to execute
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
    print(f'     {sys.argv[0]} -- analysis control toplevel module for the HMC Lab instrument.')
    print()
    print(f'\t{sys.argv[0].upper()} is a client toplevel layer that interfaces with the DAQ server and sends coordination control commands to perform full analyses.')
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
    print(f'     --boot             perform full cold start boot with still air baseline calibration')
    print(f'     --home             HOME the syringe')
    print(f'     --wash <cycles>    execute system washing')
    print(f'     --fill <volume>    execute partial volume fill, closes syringe valve after filling')
    print(f'     --empty            execute empty movement, close syringe valve after emptying')
    print(f'     --breath-open      opens the valves for breath intake')
    print(f'     --nplc <>          ADC integration in NPLC (default {format_SI(default.nplc, precision = 1)}nplc)')
    print(f'     --host <>          Host address (default {default.host_addr})')
    print(f'     --cmd-port <>      CMD service port (default {default.cmd_port})')
    print(f'     --data-port <>     DATA service port (default {default.data_port})')
    print(f'     --wait-hid <>      wait delay for HID (default {default.wait_hid}s)')
    print(f'     --h2-drift <>      H2 baseline drift (default {default.h2_base_drift}mV/min)')
    print(f'     --ch4-drift <>     CH4 baseline drift (default {default.ch4_base_drift}mV/min)')
    print(f'     --bufsize <>       datapoints buffer length in seconds (default {default.bufsize}s)')
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
            'help', 'version', 'quiet', 'silent', 'verbose', 'debug', 'boot', 'wash=', 'fill=', 'empty', 'breath-open', 'home',
            'host=', 'cmd-port=', 'data-port=', 'wait-hid=', 'h2-drift=', 'ch4-drift=', 'bufsize=',
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
            elif opt in ['--boot']:
                arg.boot = True
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
            elif opt in ['--bufsize']:
                arg.bufsize = float(si_to_eng(val))
            elif opt in ['--host']:
                arg.host_addr = val
            elif opt in ['--cmd-port']:
                arg.cmd_port = int(val)
            elif opt in ['--data-port']:
                arg.data_port = int(val)
            elif opt in ['--wait-hid']:
                arg.wait_hid = float(val)
            elif opt in ['--h2-drift']:
                arg.h2_base_drift = float(val)
            elif opt in ['--ch4-drift']:
                arg.ch4_base_drift = float(val)
            elif opt in ['--wash']:
                arg.operation = 'WASH'
                arg.wash_cycles = int(val)
            elif opt in ['--fill']:
                arg.operation = 'FILL'
                arg.sample_size = int(val)
            elif opt in ['--empty']:
                arg.operation = 'EMPTY'
            elif opt in ['--home']:
                arg.operation = 'HOME'
            elif opt in ['--breath-open']:
                arg.operation = 'BREATH'
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
    def sensor(cls, label):
        """Return an instance that corresponds to the given label."""
        return [x for x in cls._sensors if (label is x.label)][0] if hasattr(cls, '_sensors') else None

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
#   CLASS   AppException                                                                        #
#===============================================================================================#

class AppException(Exception):
    """This is the application exception raised by the application code."""

#===============================================================================================#
#   CLASS   Hid                                                                                 #
#===============================================================================================#

class Hid:
    def __init__(self, vendor_id: int, product_id: int, quiet: bool = True):
        self.hid = SerialCtrl(COMPORT, 9600)
        self.hid.OpenConnection()
        self.PositionAbs = 0
        self.quiet = quiet

    def connect(self):
        if not self.hid.IsConnected():
            self.hid.OpenConnection()
            return self.hid.IsConnected()

    def is_connected(self):
        return self.hid.IsConnected()

    def close(self):
        if self.hid.IsConnected():
            self.hid.CloseConnection()
    
    def parse_position(self, msg):
        match = re.match(r"<POS:([+-]\d{6})>", msg)
        if match:
            return int(match.group(1))
        else:
            return None

    def position(self):
        if self.hid.IsConnected():
            self.hid.SendString("<GP>", self.quiet)
            data = self.hid.ReceiveBytesByTimeout(100, self.quiet)
            if data:
                self.PositionAbs = self.parse_position(data.decode('utf-8'))
                if self.PositionAbs is not None:
                    position=(self.PositionAbs + 50) // 100     # convert to mm - round
                    return position
            else:
                return None
        else:
            return None

    def request(self, msg:str) -> str | None:
        if self.hid.IsConnected():
            self.hid.SendString(msg, self.quiet)
            while True:
                data = self.hid.ReceiveBytesByTimeout(50, self.quiet)
                if data:
                    response = data.decode()
                    if response[:3] in msg:
                        return response
                else:
                    return None
        else:
            return None

    def status(self) -> str | None:
        if self.hid.IsConnected():
            self.hid.SendString('<ST>', self.quiet)
            while True:
                data = self.hid.ReceiveBytesByTimeout(50, self.quiet)
                if data:
                    response = data.decode()
                    if any(x in response for x in("<OF>","<ON>")):
                        return response
                else:
                    return None
        else:
            return None

    def home(self) -> str | None:
        if self.hid.IsConnected():
            msg = '<GH>'
            self.hid.SendString(msg, self.quiet)
            while True:
                data = self.hid.ReceiveBytesByTimeout(50, self.quiet)
                if data:
                    response = data.decode()
                    if response[:3] in msg:
                        return response
                else:
                    return None
        else:
            return None

    def fill(self) -> str | None:
        if self.hid.IsConnected():
            speed_str = str(250).zfill(3)
            cmdstr = f'<SP:{speed_str}>'
            self.request(cmdstr)
            cmdstr = f'<GO:+010000>'
            self.request(cmdstr)
        else:
            return None

    def empty(self) -> str | None:
        if self.hid.IsConnected():
            speed_str = str(250).zfill(3)
            cmdstr = f'<SP:{speed_str}>'
            self.request(cmdstr)
            cmdstr = f'<GO:+000000>'
            self.request(cmdstr)
        else:
            return None

    def goto(self, pos: int, speed: int = 250) -> str | None:
        if self.hid.IsConnected():
            speed_str = f"{speed:03d}"
            cmdstr = f'<SP:{speed_str}>'
            self.request(cmdstr)
            pos_str = f'{pos * 100:+07d}'
            cmdstr = f'<GO:{pos_str}>'
            self.request(cmdstr)
        else:
            return None

    def push_sample(self, size: int = 35, speed: int = 50) -> str | None:
        if self.hid.IsConnected():
            current = self.position()
            pos = current - size
            speed_str = f"{speed:03d}"
            cmdstr = f'<SP:{speed_str}>'
            self.request(cmdstr)
            pos_str = f'{pos * 100:+07d}'
            cmdstr = f'<GO:{pos_str}>'
            self.request(cmdstr)
        else:
            return None

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
#               CLIENT TCP UTILS                                                                #
#===============================================================================================#

evt_terminate = threading.Event()           # All event loops terminate when set to True
cmd_lock = threading.Lock()                 # locks other command handlers
buf_lock = threading.Lock()                 # locks buffer access

def sock_connect(host, port) -> socket.socket:
    """Create a TCP stream connection, and returns the handler."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    return server

def send(server, msg, wait=1.0):
    """Sends a message to the connection server, and returns the response."""
    try: 
        time.sleep(wait)
        server.send(msg.encode())
        response = server.recv(1024).decode()
        return response
    except BrokenPipeError as e:
        return str(e)

def boot_pids():
    """Enables the heatpump and hotplate PID and related cooling fan, and turns ON the purging air pump."""
    with sock_connect(arg.host_addr, arg.cmd_port) as cmd:
        send(cmd, ":dout0.0:write 1")       # purge air pump
        send(cmd, ":dout0.1:write 1")       # cooling fan 1
        send(cmd, ":DOUT0.2:WRITE 1")       # cooling fan 2
        send(cmd, ":pwm3:outp:ena")         # heat pump PID
        send(cmd, ":pwm4:outp:ena")         # hotplate PID

def set_valve(name, state):
    """Control the valves solenoids."""
    try:
        if any(x == state.upper() for x in("ON", "OFF")):
            val = 1 if state.upper() == "ON" else 0
            print(f'set_valve, {name}, {state}, {val=}')
            with sock_connect(arg.host_addr, arg.cmd_port) as cmd:
                match name.upper():
                    case 'SYRINGE':
                        send(cmd, f':dout0.7:write {val}')       # SYRINGE valve    0x80
                    case 'SENSORS':
                        send(cmd, f':dout0.6:write {val}')       # SENSORS valve    0x40
                    case 'INTAKE':
                        send(cmd, f':dout0.5:write {val}')       # INTAKE valve     0x20
                    case 'PURGE':
                        send(cmd, f':dout0.4:write {val}')       # PURGE valve      0x10
                    case 'STILL':
                        send(cmd, f':dout0.3:write {val}')       # STILL valve      0x08
                    case 'COOLING2':
                        send(cmd, f':dout0.2:write {val}')       # COOLING fan 2    0x04
                    case 'COOLING1':
                        send(cmd, f':dout0.1:write {val}')       # COOLING fan 1    0x02
                    case 'PUMP':
                        send(cmd, f':dout0.0:write {val}')       # PUMP fan         0x01
    except:
        pass

def set_valves(value: int) -> None:
    """Control the valves solenoids, with a single write for all valves simultaneously."""
    try:
        print(f'set_valves, 0x{value:02X}')
        with sock_connect(arg.host_addr, arg.cmd_port) as cmd:
            send(cmd, f':dout0:write {value}')  # write all bits in a single operation
    except:
        pass

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
                    bufidx.pop(p)
            else:
                return len(bufidx)-1
        elif t < bufidx[0][1]:
            return 0
        else:
            return len(bufidx)-1
    except IndexError:
        return 0

def h2_baseline_drift(cmd, drift: float):
    stable = False
    h2_drift_val = conv_float(send(cmd, ":CMD:BASE:DRIFT? h2, 60.0")) * 1e3
    if(abs(h2_drift_val) <= drift):
        stable = True
    return h2_drift_val, stable

def tgs_baseline_drift(cmd, drift: float):
    stable = False
    tgs_drift_val = conv_float(send(cmd, ":CMD:BASE:DRIFT? ch4, 60.0")) * 1e3
    if(abs(tgs_drift_val) <= drift):
        stable = True
    return tgs_drift_val, stable

def compute_calib_curves(cal:dict):
    global z_cell_adc2h2, z_tgs_h2_2adc, z_tgs_adc2ch4
    try:
        cell_adc_h2 = [0.0, cal["cell_h2_50ppm"], cal["cell_h2_100ppm"]]
        cell_ppm_h2 = [0.0, 50.0, 100.0]
        tgs_adc_h2 = [0.0, cal["tgs_h2_50ppm"] + cal["tgs_comp"], cal["tgs_h2_100ppm"] + cal["tgs_comp"]]
        tgs_ppm_h2 = [0.0, 50.0, 100.0]
        tgs_adc_ch4 = [0.0, cal["tgs_ch4_50ppm"] + cal["tgs_comp"], cal["tgs_ch4_100ppm"] + cal["tgs_comp"]]
        tgs_ppm_ch4 = [0.0, 50.0, 100.0]
        z_cell_adc2h2 = np.polyfit(cell_adc_h2,cell_ppm_h2,deg=1)
        z_tgs_h2_2adc = np.polyfit(tgs_ppm_h2,tgs_adc_h2,deg=2)
        z_tgs_adc2ch4 = np.polyfit(tgs_adc_ch4,tgs_ppm_ch4,deg=2)
        print("Calibration curves computed.")
    except Exception as e:
        print(f'Exception in compute_calib_curves(): {e}.')

def calc_ppm(h2adc, ch4adc):
    h2ppm = np.polyval(z_cell_adc2h2, [h2adc])
    h2adj = np.polyval(z_tgs_h2_2adc, h2ppm)
    tgs_adjusted = (ch4adc + 20e-3) - h2adj[0]
    ch4ppm = np.polyval(z_tgs_adc2ch4, [tgs_adjusted])
    return (h2ppm[0], ch4ppm[0])

#===============================================================================================#
#               FILE UTILS                                                                      #
#===============================================================================================#

def save_calib_file(txtfname: str, calibdata: dict) -> None:
    """Save the calibration dictionary to the caibration file."""
    if not txtfname.endswith('.txt'):
        raise ValueError("Invalid filename")
    if os.path.exists(txtfname):
        os.remove(txtfname)
    with open(txtfname, "x") as f:
        # identify measurement file in the first line as comment
        f.write(f'# HMC Calibration data generated by {sys.argv[0]}, {time.strftime("%d/%m/%Y %H:%M:%S")}\r\n')
        print("Writing calibration data ...", flush=True)
        for k,v in calibdata.items():
            record = f'{k},{v} \r\n'
            f.write(record)
    print(f'\nData file {txtfname} saved', flush=True)

def read_calib_file(txtfname: str) -> dict:
    """Read the calibration file, and return a dictionary with the read fields."""
    if not txtfname.endswith('.txt'):
        raise ValueError("Invalid filename")
    calibdata = {}
    with open(txtfname, "r") as f:
        for ln in f:
            ln = ln.replace("\r", "").replace("\n", "")
            fields = ln.split(",")
            if fields[0][0]  == '#':
                continue
            if len(fields) > 1:
                calibdata[fields[0]] = conv_float(fields[1])
    return calibdata

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

    # --- create sensors instances ----------------------------------------------------------------
    sensors = create_sensors()

    # --- declare global and prealocate the data buffer objects -----------------------------------
    global recno, bufidx, bufadc
    recno = 0
    bufidx = []
    bufadc = []
    
    # --- instantiate the command and syringe control objects -------------------------------------
    cmd = sock_connect(arg.host_addr, arg.cmd_port)
    hid = Hid(arg.vendor_id, arg.product_id)

    # --- calibration data ------------------------------------------------------------------------
    calib = read_calib_file('hmc_calibdata.txt')

    # --- toplevel thread loop --------------------------------------------------------------------
    wait = arg.wait_hid
    tstart = time.time()
    tgs_base = 0.0
    tgs_t105 = 0.0
    tgs_comp = 0.0
    t105_time_recover = 0.0
    tgs_baseline = 0.0
    h2_baseline = 0.0
    o2_baseline = 0.0
    state =      "WASH_START" if arg.operation == "WASH"        \
            else "FILL_START" if arg.operation == "FILL"        \
            else "EMPTY_START" if arg.operation == "EMPTY"      \
            else "BREATH_START" if arg.operation == "BREATH"    \
            else "HOME_START" if arg.operation == "HOME"        \
            else "INIT"
    while True:
        try:
            match state.upper():
                case 'INIT':
                    """Init state. Boot PIDs and go wait for stable temperatures."""
                    print(f'{state.upper()}')
                    compute_calib_curves(calib)
                    boot_pids()
                    print(f'Reading Temperature Setpoints...')
                    ch4_temp_setp = Sensor.sensor('CH4_TEMP').val(conv_float(send(cmd, ":pwm2:pid:setp?")))
                    coldside_temp_setp = Sensor.sensor('COLDSIDE_TEMP').val(conv_float(send(cmd, ":pwm3:pid:setp?")))
                    hotplate_temp_setp = Sensor.sensor('HOTPLATE_TEMP').val(conv_float(send(cmd, ":pwm4:pid:setp?")))
                    print(f'Temperature setpoints: CH4={ch4_temp_setp:.2f}C, coldside={coldside_temp_setp:.2f}C, hotplate={hotplate_temp_setp:.2f}C', flush=True)
                    moving = False
                    state = 'TEMP_STABILIZING'
                case 'TEMP_STABILIZING':
                    """Wait for temperatures to reach setpoints"""
                    if(moving and (send(cmd, ":PWM1:MOVING?") == '0')):
                        moving = False
                        send(cmd, ":PWM1:MOVE MIN,MAX")
                        send(cmd, ":SYST:BEEP")
                    ch4_temp = conv_float(send(cmd, ":CMD:READ? CH4_TEMP"))
                    coldside_temp = conv_float(send(cmd, ":CMD:READ? COLDSIDE_TEMP"))
                    hotplate_temp = conv_float(send(cmd, ":CMD:READ? HOTPLATE_TEMP"))
                    print(f'Current temperatures:  CH4={ch4_temp:.2f}C, coldside={coldside_temp:.2f}, hotplate={hotplate_temp}            \r', end='', flush=True)
                    if  (abs(ch4_temp_setp - ch4_temp) < 1.0) and               \
                        (abs(coldside_temp_setp - coldside_temp) < 0.50) and    \
                        (abs(hotplate_temp_setp - hotplate_temp) < 3.00):
                        print()
                        print("Temperatures stabilized!")
                        send(cmd, ":SYST:BEEP 1.0")
                        state = 'WAIT_BASELINES'
                        print(f'{state.upper()}')
                case 'CALIB_B0_WAIT_LEVEL':
                    time.sleep(1.0)
                    tgs_level = conv_float(send(cmd, ":CMD:READ? ch4"))
                    now = conv_float(send(cmd, ":CMD:TIME:MAX?"))
                    if now > t105_time_recover:
                        if (abs(tgs_level - tgs_base) < arg.ch4_base_drift) or (tgs_level > tgs_base):
                            # CH4 Baseline returned to previous level, now wait for near zero derivative
                            t105_time_recover = now if t105_time_recover == 0.0 else t105_time_recover
                            state = 'CALIB_B0_WAIT_DRIFT'
                            print(f'{state.upper()}')
                case 'CALIB_B0_WAIT_DRIFT':
                    """Calibration of the still air baseline (1st)"""
                    time.sleep(1.0)
                    tgs_drift_val, tgs_stable = tgs_baseline_drift(cmd, arg.ch4_base_drift)
                    print(f'Ch4 baseline drift: {tgs_drift_val:.2f} mV/min            \r', end='', flush=True)
                    if tgs_stable:
                        # CH4 Baseline is stable: capture data and start still air.
                        send(cmd, ":SYST:BEEP 1.0")
                        print()
                        print(f'Ch4 baseline drift: {tgs_drift_val:.2f} mV/min (PASSED)')
                        set_valve('STILL', "ON")
                        send(cmd, ":CMD:TIME:RST")
                        tstart = time.time()
                        tgs_base = conv_float(send(cmd, ":CMD:READ? ch4, 0.0, 1.0"))
                        state = 'CALIB_B0_WAIT_T105'
                        print(f'{state.upper()}')
                case 'CALIB_B0_WAIT_T105':
                    """Wait for T105."""
                    if (time.time() - tstart) >= 107.0:
                        set_valve('STILL', "OFF")
                        tgs_t105 = conv_float(send(cmd, ":CMD:READ? ch4, 105.5, 1.0"))
                        tgs_comp = tgs_t105 - tgs_base
                        print(f'Baseline compensation CALIBRATED.')
                        print(f'{tgs_base=}.')
                        print(f'{tgs_t105=}.')
                        print(f'{tgs_comp=}.')
                        state = 'WAIT_BASELINES'
                        print(f'{state.upper()}')
                case 'WAIT_BASELINES':
                    tgs_baseline = conv_float(send(cmd, ":CMD:READ? ch4, max, 2.0"))
                    tgs_drift_val, tgs_stable = tgs_baseline_drift(cmd, arg.ch4_base_drift)
                    h2_baseline = conv_float(send(cmd, ":CMD:READ? h2, max, 2.0"))
                    h2_drift_val, h2_stable = h2_baseline_drift(cmd, arg.h2_base_drift)
                    print(f'Ch4 baseline: {tgs_baseline:.6f} mV  drift: {tgs_drift_val:.2f} mV/min ({'STABLE' if tgs_stable else 'DRIFTING'})   H2 baseline: {h2_baseline:.6f} mV/min  drift: {h2_drift_val:.2f} mV/min ({'STABLE' if h2_stable else 'DRIFTING'})                  \r', end='', flush=True)
                    if ((time.time() - tstart) >= 240.0) and (tgs_stable) and (h2_stable):
                        print()
                        if arg.boot:
                            arg.boot = False
                            print(f'Calibrating baseline compensation...')
                            tgs_base = 0.0       # baseline level at start of negative peak
                            tgs_t105 = 0.0       # baseline at T105 in still air
                            tgs_comp = 0.0       # calculated compensation factor for T105 correction
                            state = 'CALIB_B0_WAIT_DRIFT' 
                        else:
                            send(cmd, ":SYST:BEEP 1.0")
                            print(f'Baselines STABLE! READY FOR EXAM!')
                            input("Press ENTER to start exam:>")
                            set_valves(0x47)    # Syringe + Sensors
                            state = 'EXAM_START'
                            print(f'{state.upper()}')
                case 'EXAM_START':
                    # -----------------------------------------------------------------------------
                    # init the sample pushing
                    # get baselines and drifts
                    tgs_baseline = conv_float(send(cmd, ":CMD:READ? ch4, max, 1.0"))
                    h2_baseline = conv_float(send(cmd, ":CMD:READ? h2, max, 1.0"))
                    o2_baseline = conv_float(send(cmd, ":CMD:READ? o2, max, 1.0"))
                    tgs_drift_val = conv_float(send(cmd, ":CMD:BASE:DRIFT? ch4, 60.0")) * 1e3
                    h2_drift_val = conv_float(send(cmd, ":CMD:BASE:DRIFT? h2, 60.0")) * 1e3
                    print(f'Ch4 baseline: {tgs_baseline:.6f} mV  drift: {tgs_drift_val:.2f} mV/min \nH2 baseline: {h2_baseline:.6f} mV/min  drift: {h2_drift_val:.2f} mV/min', flush=True)
                    print(f'Sensors: {send(cmd, ":CMD:READ? ALL")}')
                    hid.connect()
                    hid.push_sample()
                    state = 'EXAM_PUSHING'
                    print(f'{state.upper()}')
                case 'EXAM_PUSHING':
                    """Wait PUSH terminate"""
                    if hid.status() == '<OF>':
                        # terminated sample push. Now close the air valve, reset time to T0, close syringe valves, reset timer and go wait for 107 seconds.
                        tstart = time.time()
                        # --- reset time to T0 ---
                        print(f'{send(cmd, ":CMD:TIME:RST")=}')
                        # --- Configure the valves ---
                        set_valves(0x0F)    # STILL ON
                        print(f'PUSH STOPPED.')
                        state = 'EXAM_WAIT_T107'
                        print(f'{state.upper()}')
                        hid.close()
                case 'EXAM_WAIT_T107':
                    """Wait sensors until T107"""
                    try:
                        if (time.time() - tstart) >= 107.0:
                            rel_hum = conv_float(send(cmd, ":CMD:READ? AHT10_RHUM"))
                            o2_t105_meas = conv_float(send(cmd, ":CMD:READ? o2, 105.0, 1.0"))
                            o2_t105_val = (o2_t105_meas - o2_baseline)
                            tgs_t105_meas = conv_float(send(cmd, ":CMD:READ? ch4, 105.0, 1.0"))
                            tgs_t105_val = (tgs_t105_meas - tgs_baseline) + calib["tgs_comp"]
                            _, h2_peak_str = send(cmd, ":CMD:PEAK? h2, -60, 1200.0").split(',')
                            h2_peak_val = (conv_float(h2_peak_str) - h2_baseline)
                            set_valves(0x07)    # STILL OFF
                            # ---- COMPUTE RESULTS ----
                            print()
                            print(f'{h2_peak_val=:.6f}')
                            print(f'{tgs_t105_val=:.6f}')
                            print(f'{o2_t105_val=:.2f}%')
                            print(f'{h2_baseline=:.6f}')
                            print(f'{tgs_baseline=:.6f}')
                            print(f'{o2_baseline=:.2f}%')
                            print(f'{rel_hum=:.2f}%')
                            print(f'{tgs_t105_meas=:.6f}')
                            print(f'{h2_peak_str=}')
                            # ------
                            h2ppm, ch4ppm = calc_ppm(h2_peak_val, tgs_t105_val)
                            print(f'{h2ppm=: .2f} ppm')
                            print(f'{ch4ppm=: .2f} ppm')
                            print()
                            # ------
                            send(cmd, ":SYST:BEEP 1.5")
                            state = 'WAIT_BASELINES'
                            print(f'{state.upper()}')
                    except Exception as e:
                        print(f'{e}')
                        break
                case 'WASH_START':
                    """Start system wash"""
                    print(f'WASH: {arg.wash_cycles} cycles...')
                    hid.connect()
                    set_valves(0xA7)                    # SYRINGE to INTAKE / INTAKE CLOSED / PURGE OPEN
                    hid.goto(pos=50, speed=350)         # FILL
                    state = 'WASH_FILLING'
                    print(f'{state.upper()}')
                case 'WASH_EMPTYING':
                    """Wait motor OFF"""
                    if hid.status() == '<OF>':
                        arg.wash_cycles -= 1
                        if arg.wash_cycles <= 0:
                            send(cmd, ":SYST:BEEP 1.0")
                            set_valves(0x07)                    # Syringe switched to Sensors, open INTAKE and PURGE
                            state = 'EXIT'
                            print(f'{state.upper()}')
                        else:
                            set_valves(0xA7)                    # SYRINGE to INTAKE / INTAKE CLOSED / PURGE OPEN
                            hid.goto(pos=50, speed=350)         # FILL
                            state = 'WASH_FILLING'
                            print(f'{state.upper()}')
                case 'WASH_FILLING':
                    """Wait motor OFF"""
                    if hid.status() == '<OF>':
                        set_valves(0xA7)                        # SYRINGE to INTAKE / INTAKE CLOSED / PURGE OPEN
                        hid.goto(pos=0, speed=350)              # EMPTY
                        state = 'WASH_EMPTYING'
                        print(f'{state.upper()}')
                case 'FILL_START':
                    """Partial sample Fill"""
                    print(f'FILL: up to {arg.sample_size} ml...')
                    hid.connect()
                    set_valves(0x87)                            # all valves open / Syringe switched to INTAKE
                    hid.goto(pos=arg.sample_size, speed=200)    # FILL
                    state = 'WAIT_FILLING'
                    print(f'{state.upper()}')
                case 'WAIT_FILLING':
                    """Wait motor OFF"""
                    if hid.status() == '<OF>':
                        set_valves(0x07)                        # Syringe switched to Sensors
                        send(cmd, ":SYST:BEEP 1.0")
                        state = 'EXIT'
                        print(f'{state.upper()}')
                case 'EMPTY_START':
                    """empty the syringe"""
                    print(f'EMPTY and close...')
                    hid.connect()
                    set_valves(0xA7)                            # SYRINGE to INTAKE / INTAKE CLOSED / PURGE OPEN
                    hid.goto(pos=0, speed=350)                  # EMPTY
                    state = 'WAIT_EMPTYING'
                    print(f'{state.upper()}')
                case 'WAIT_EMPTYING':
                    """Wait motor OFF"""
                    if hid.status() == '<OF>':
                        set_valves(0x07)                        # switch SYRINGE to Sensors
                        send(cmd, ":SYST:BEEP 1.0")
                        state = 'EXIT'
                        print(f'{state.upper()}')
                case 'HOME_START':
                    """home the syringe"""
                    print(f'HOME...')
                    hid.connect()
                    set_valves(0x07)                            # all valves open, syringe to SENSORS
                    hid.home()                                  # HOME
                    state = 'WAIT_HOMING'
                    print(f'{state.upper()}')
                case 'WAIT_HOMING':
                    """Wait motor OFF"""
                    if hid.status() == '<OF>':
                        set_valves(0x07)                    # switch SYRINGE to Sensors
                        send(cmd, ":SYST:BEEP 1.0")
                        state = 'EXIT'
                        print(f'{state.upper()}')
                case 'BREATH_START':
                    """opens the valves for the breath intake"""
                    print(f'Open valves for breath collection...')
                    hid.connect()
                    set_valves(0x87)                        # switch syringe to INTAKE
                    state = 'EXIT'
                    print(f'{state.upper()}')
                case 'EXIT':
                    """Terminate tests"""
                    print(f'Terminated.')
                    hid.close()
                    raise(AppException("Exiting..."))
        except AppException as e:
            print(f'{e}')
            break
        except Exception as e:
            print(f'Exception: {e}')

    # --- epilog ------------------------------------------------------------------------------
    time.sleep(0.1)
    if threading.active_count() > 1:
        if arg.verbose: print(f'Terminating remaining {threading.active_count() - 1} active threads:')
        for t in (x for x in threading.enumerate() if x != threading.current_thread()):
            if arg.verbose: print(f'    Terminating thread {t.name}...')
            t.join(0.1)
    time.sleep(0.1)
    if not arg.silent: print(f'Exiting ...', flush=True)
    sys.exit(0)

# --- program starts here  ------------------------------------------------------------------------
if __name__  == '__main__':
    main()

