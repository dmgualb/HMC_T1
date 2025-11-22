import sys
import time
from typing import NoReturn, Self, Any
import usbtmc
import serial
from serial.tools import list_ports as lp

#===============================================================================================#
#               INSTRUMENT CLASS: SCPI INSTRUMENT CONTROL SUPPORT                               #
#===============================================================================================#

class Instrument(object):
    """
        The Instrument Class is an interface class wrapper for PySerial and USBTMC classes. 
        
        ### Args: 
            - visa_str : A valid VISA device identification string.
            - baudrate : A valid baudrate value for serial ports.
            - wait : time interval to sleep after write/read ops.
            - timeout : timeout time for device response.
            - eol: line ending for serial frames, default to CRLF.
            - start_delay: a delay in seconds to wait before initial '*IDN' handshake command.
            
        ### Returns:
            Returns an instance of the device interface, or None if device not found. 
        
        ### Raises: 
            - TypeError on invalid visa_str type, or on invalid operation for the port type.
            - ValueError on invalid visa_str format or invalid parameters.
            - NotImplementedError for other serial interfaces than ('USBSER', 'USB'). 
        
        ### VISA String
            "<USBSER|USB>::<VID>::<PID>::<SERNUM|*>::<IFCNUM|*>::<INSTR>"

            
        ### INSTALL:
            pip install python-usbtmc
            pip install pyusb
            pip install serial

        Implements a uniform transparent interface for serial SCPI instruments, via USBTMC or via USBCDC,
        encapsulating the USBTMC and PySerial classes, and offering a uniform calling interface for instruments, 
        regardless of their serial interface connection. \n
        The selection is done via the VISA instrument identification string, that specifies "USBSER" for PySerial 
        ports, and "USBx" for USBTMC ports. \n
        If the instrument is not found in the USB bus, the class is not instantiated and returns NoneType.
    """
    def __new__(cls, visa_str:str, baudrate:int|None=None, wait:float=0.2, timeout:float=1.0, eol:str='\r\n', start_delay:float|None=None) -> Self | None:
        """Create the object instance and attempt connection with the instrument, returning None if failed."""
        if not isinstance(visa_str, str): raise TypeError("'visa_str': expected <str>")
        s = visa_str.split("::")
        if ((not ("USBSER" in s[0])) and (not ("USB" in s[0]))) or (not ("INSTR" in s[len(s)-1])): 
            raise ValueError("'visa_str': invalid visa string")
        # visa string validated, instantiate new object
        self = super().__new__(cls)
        self.wait = wait
        self.eol = eol
        if("USBSER" in s[0]):
            if not isinstance(baudrate, int): raise TypeError("'baudrate': expected <int>")
            if not isinstance(timeout, float): raise TypeError("'timeout': expected <float>")
            try:
                self.type = "SERIAL"
                self.visa_str = visa_str
                self.vid = int(s[1],0)
                self.pid = int(s[2],0)
                self.sernum = s[3]
                self.ifcnum = s[4] if len(s) > 5 else None
                self.portname = self.search_portname(self.vid, self.pid, self.ifcnum if self.ifcnum != '*' else None)
                self.baudrate = baudrate
                self.timeout = timeout
                if self.portname:
                    self.instr = serial.Serial()
                    self.write = self.serial_write
                    self.read = self.serial_read
                    self.ask = self.serial_ask
                    self.close = self.serial_close
                    self.open = self.serial_open
                    self.instr.port = self.portname
                    self.instr.baudrate = self.baudrate
                    self.instr.timeout = self.timeout
                    self.instr.open()
                    self.is_open = self.instr.is_open
                    if self.is_open:
                        self.instr.reset_input_buffer()
                        self.instr.reset_output_buffer()
                        if (start_delay): time.sleep(start_delay)
                        self.idn = self.ask("*idn?")
                        if len(self.idn) == 0:
                            self.close()
                            print("Invalid IDN string for", visa_str)
                            self = None
                        else:
                            s = self.idn.split(',')
                            if (self.sernum != '*') and (self.sernum not in s[2]):
                                self.close()
                                print("Sernum mismatch for", visa_str)
                                self = None
                    else:
                        # print("Serial port open() failure for", visa_str)
                        self = None
                else:
                    # print("Device not found for", visa_str)
                    self = None
            except:
                print("ERROR -", sys.exc_info()[1], "for", visa_str)
                self = None
        elif ("USB" in s[0]):
            try:
                self.type = "USB"
                self.visa_str = visa_str
                self.vid = int(s[1],0)
                self.pid = int(s[2],0)
                self.sernum = s[3]
                self.instr = usbtmc.Instrument(visa_str)
                self.write = self.usb_write
                self.read = self.usb_read
                self.ask = self.usb_ask
                self.close = self.usb_close
                self.open = self.usb_open
                self.idn = self.ask("*idn?")
                if len(self.idn) == 0:
                    self.close()
                    print("Invalid IDN string for", visa_str)
                    self = None
                else:
                    self.is_open = True
                    if (self.sernum != '*') and (self.sernum not in self.idn):
                        self.close()
                        print("Sernum mismatch for", visa_str)
                        self = None
            except:
                print("ERROR -", sys.exc_info()[1], "for", visa_str)
                self = None
        else: 
            # Other interfaces
            raise NotImplementedError("'%s' not implemented" % s[0])
            self = None
        return self
    def __str__(self) -> str:
        """Return a pretty print string."""
        s = f'<Instrument>.type={self.type}\r\n'
        s += f'<Instrument>.visa_str={self.visa_str}\r\n'
        s += f'<Instrument>.idn={self.idn}\r\n'
        s += f'<Instrument>.is_open={self.is_open}\r\n'
        if self.portname: s += f'<Instrument>.portname={self.portname}\r\n'
        if self.baudrate: s += f'<Instrument>.baudrate={self.baudrate}\r\n'
        return s
    def get_visa_str(self) -> str:
        return self.visa_str
    def get_baudrate(self) -> int:
        return self.baudrate
    def idn_str(self) -> str:
        """Return a string with the instrument manufacturer, model and serial number."""
        idn_fields = self.idn.split(",")
        manufacturer = idn_fields[0].strip() if len(idn_fields) > 0 else ''
        model = idn_fields[1].strip() if len(idn_fields) > 1 else ''
        serial = idn_fields[2].strip() if len(idn_fields) > 2 else ''
        version = idn_fields[3].strip() if len(idn_fields) > 3 else ''
        return "{} {} serial {} version {}".format(manufacturer, model, serial, version)
    def model_str(self) -> str:
        """Return a string with the instrument manufacturer and model."""
        idn_fields = self.idn.split(",")
        manufacturer = idn_fields[0].strip() if len(idn_fields) > 0 else ''
        model = idn_fields[1].strip() if len(idn_fields) > 1 else ''
        return "{} {}".format(manufacturer, model)
    def version_str(self) -> str:
        """Return a string with the instrument version."""
        idn_fields = self.idn.split(",")
        version = idn_fields[3].strip() if len(idn_fields) > 3 else ''
        return "{}".format(version)
    def get_settings(self) -> dict[str, Any]:
        """Return a dictionary with the port settings."""
        return self.instr.get_settings()
    def apply_settings(self, d:dict[str, Any]) -> None:
        """Apply the settings in the settings dictionary."""
        self.instr.apply_settings(d)
    def search_portname(self, vid:int, pid:int, ifcnum:str|None = None) -> str|None:
        """Locate a matching serial device port."""
        for com in lp.comports():       
            if (com.vid == vid) and (com.pid == pid):
                if ifcnum and (ifcnum not in com.device):
                    continue
                # ttyname = com.device.replace("cu.", "tty.")
                return com.device
                # return ttyname
        else:
            return None
    def serial_write(self, str:str, wait:float|None=None) -> None:
        """Encapsulate the write sequence for serial devices."""
        if self.type != "SERIAL": raise TypeError("'serial_write' unsupported for type '%s'" % self.type) # type: ignore
        if not self.is_open: raise RuntimeError("Illegal operation on a closed port.")
        if not wait: wait = self.wait # type: ignore
        str = str + self.eol # type: ignore
        self.instr.write(str.encode(encoding="latin-1", errors="ignore"))
        if wait: time.sleep(wait)
    def serial_ask(self, str:str, wait:float|None=None) -> str:
        """Encapsulate the query/response for serial devices."""
        if self.type != "SERIAL": raise TypeError("'serial_ask' unsupported for type '%s'" % self.type)
        if not self.is_open: raise RuntimeError("Illegal operation on a closed port.")
        if not wait: wait = self.wait
        self.serial_write(str, wait=wait)
        if wait: time.sleep(wait)
        return self.instr.readline().decode(encoding="latin-1", errors="ignore")[:-1]
    def serial_read(self) -> str:
        """Encapsulate read continuous response for serial devices."""
        if self.type != "SERIAL": raise TypeError("'serial_ask' unsupported for type '%s'" % self.type)
        if not self.is_open: raise RuntimeError("Illegal operation on a closed port.")
        return self.instr.readline().decode(encoding="latin-1", errors="ignore")[:-1]
    def serial_close(self) -> None:
        """Encapsulate the close sequence for serial devices."""
        if self.type != "SERIAL": raise TypeError("'serial_close' unsupported for type '%s'" % self.type)
        self.is_open = False
        self.instr.close()
        self.write = self._illegal_stub
        self.ask = self._illegal_stub
        self.close = self._illegal_stub
    def serial_open(self) -> bool:
        """Reopen a closed SERIAL device."""
        if self.is_open: raise RuntimeError("Illegal Open on an already open port.")
        try:
            if self.portname:
                self.instr = serial.Serial()
                self.instr.port = self.portname
                self.instr.baudrate = self.baudrate
                self.instr.timeout = self.timeout
                self.instr.open()
                self.is_open = self.instr.is_open
                if self.is_open:
                    self.write = self.serial_write
                    self.ask = self.serial_ask
                    self.read = self.serial_read
                    self.close = self.serial_close
                    self.open = self.serial_open
                    self.instr.reset_input_buffer()
                    self.instr.reset_output_buffer()
                    self.write("*cls")
                    self.idn = self.ask("*idn?")
                    if (self.sernum != '*') and (self.sernum not in self.idn):
                        self.close()
                        print("Sernum mismatch for", self.visa_str)
                        self = None
                else:
                    self.write = self._illegal_stub
                    self.ask = self._illegal_stub
                    self.close = self._illegal_stub
                    self.open = self.serial_open
                    print("Serial port open() failure for", self.visa_str)
            # else:
            #     print("Device not found for", self.visa_str)
        except:
            print("ERROR -", sys.exc_info()[1], "for", self.visa_str)
        return self.is_open
    def usb_write(self, str:str, wait:float=None) -> None:
        """Encapsulate the write sequence for usbtmc devices."""
        if self.type != "USB": raise TypeError("'usb_write' unsupported for type '%s'" % self.type)
        if not wait: wait = self.wait
        if wait: time.sleep(wait)
        self.instr.write(str)
    def usb_ask(self, str:str, wait:float=None) -> str:
        """Encapsulate the query/response for usbtmc devices."""
        if self.type != "USB": raise TypeError("'usb_ask' unsupported for type '%s'" % self.type)
        if not wait: wait = self.wait
        if wait: time.sleep(wait)
        return self.instr.ask(str)
    def usb_read(self) -> str:
        """Encapsulate continuous read for usbtmc devices."""
        if self.type != "USB": raise TypeError("'usb_ask' unsupported for type '%s'" % self.type)
        return self.instr.readline().decode(encoding="latin-1", errors="ignore")[:-1]
    def usb_close(self) -> None:
        """Encapsulate the close sequence for usbtmc devices."""
        if self.type != "USB": raise TypeError("'usb_close' unsupported for type '%s'" % self.type)
        self.is_open = False
        self.instr.close()
        self.write = self._illegal_stub
        self.ask = self._illegal_stub
        self.close = self._illegal_stub
    def usb_open(self) -> bool:
        """Reopen a closed USB device."""
        if self.is_open: raise RuntimeError("Illegal Open on an already open port.")
        try:
            self.instr = usbtmc.Instrument(self.visa_str)
            self.write = self.usb_write
            self.read = self.usb_read
            self.ask = self.usb_ask
            self.close = self.usb_close
            self.open = self.usb_open
            self.write("*cls")
            time.sleep(self.wait)
            self.idn = self.ask("*idn?")
            self.is_open = True
            if (self.sernum != '*') and (self.sernum not in self.idn):
                self.close()
                print("Sernum mismatch for", self.visa_str)
        except:
            print("ERROR -", sys.exc_info()[1], "for", self.visa_str)
        return self.is_open
    def _illegal_stub(self, *arg) -> NoReturn:
        """Raise exception when called for closed port."""
        raise RuntimeError("Illegal operation on closed port.")

