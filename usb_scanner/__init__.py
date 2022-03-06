"""
***********************************************************
        Reader Class
        Date Creation: 09/01/2018
        De: L.VOIRIN
***********************************************************
            Gestion des Versions
   0.1      Adaptation module Reader        LV  09/01/2018

***********************************************************
"""

import time
import usb.core
import usb.util

from .usb_scanners import scanners
from . import mapping


class DeviceException(Exception):
    pass


class ReadException(Exception):
    pass


class Reader:

    def __init__(self, language="FR", debug=False):
        """
        :param vendor_id: USB vendor id (check dmesg or lsusb under Linux)
        :param product_id: USB device id (check dmesg or lsusb under Linux)
        :param data_size: how much data is expected to be read - check experimentally
        :param chunk_size: chunk size like 6 or 8, check experimentally by looking on the raw output with debug=True
        :param should_reset: if true will also try to reset device preventing garbage reading.
        Doesn't work with all devices - locks them
        :param debug: if true will print raw data
        """
        print("\n#################################\n"
              "### INTITALISATION CLASSE USB ###\n"
              "#################################")
        self.language = language
        self.readerName = None
        self.interfaces = 0
        self.vendor_id = None
        self.product_id = None
        self.data_size = 84
        self.chunk_size = 16
        self.should_reset = False
        self.debug = debug
        self._device = None
        self._endpoint = None
        print("\n#### INITIALISATION LECTEUR CODE BARRE ####\n")
        print("*** Detection douchette ***")
        self.initialize()
        print(f" - douchette : {self.readerName}\n")

    def initialize(self):
        for scanner in scanners:
            self._device = usb.core.find(idVendor=scanner[1], idProduct=scanner[2])
            if self._device is not None:
                self.readerName, self.vendor_id, self.product_id, self.chunk_size = scanner
                break
    
        if self._device is None:
            raise DeviceException('No device found, check vendor_id and product_id')

        for nb, config in enumerate(self._device):
            print(f'config {nb + 1}')
            self.interfaces = config.bNumInterfaces
            print(f'Interfaces {config.bNumInterfaces}')
            for i in range(config.bNumInterfaces):
                if self._device.is_kernel_driver_active(i):
                    self._device.detach_kernel_driver(i)

        try:
            self._device.set_configuration()
            if self.should_reset:
                self._device.reset()
        except usb.core.USBError as err:
            raise DeviceException(f'Could not set configuration: {err}')

        # print(self._device[0])
        self._endpoint = self._device[0][(0, 0)][0]

    def get_device_config(self):
        return str(self._device[0])

    def read(self):
        self.initialize()
        data = []
        data_read = False

        while True:
            try:
                data += self._endpoint.read(self._endpoint.wMaxPacketSize)
                data_read = True
            except usb.core.USBError as e:
                if e.args[0] == 110 and data_read:
                    if len(data) < self.data_size:
                        raise ReadException('Got %s bytes instead of %s - %s' % (len(data), self.data_size, str(data)))
                        self.initialize()
                    else:
                        break
               
        if self.debug:
            print('Raw data', data)

        barCode = str(self.decode_raw_data(data).strip())
        self.disconnect()
        print("*** {} ***\n".format(barCode))
        return barCode

    def decode_raw_data(self, raw_data):
        data = self.extract_meaningful_data_from_chunk(raw_data)
        return self.raw_data_to_keys(data)

    def extract_meaningful_data_from_chunk(self, raw_data):
        shift_indicator_index = 0
        raw_key_value_index = 2
        for chunk in self.get_chunked_data(raw_data):
            yield (chunk[shift_indicator_index], chunk[raw_key_value_index])

    def get_chunked_data(self, raw_data):
        for i in iter(range(0, len(raw_data), self.chunk_size)):
            #for i in iter(range(0, len(data), chunks)):
            yield raw_data[i:i + self.chunk_size]

    def map_character(self, c):
        return mapping.keys_page[self.language].get(c, '')

    def raw_to_key(self, key):
        if key[0] == 2:
            return mapping.shift_keys_page[self.language].get(key[1], '')
        else:
            return mapping.keys_page[self.language].get(key[1], '')

    def raw_data_to_keys(self, extracted_data):
        return ''.join(map(self.raw_to_key, extracted_data))

    def disconnect(self):
        if self.should_reset:
            self._device.reset()
        for i in range(self.interfaces):
            usb.util.release_interface(self._device, i)
            self._device.attach_kernel_driver(i)


"""

Motorola :
Raw data [2, 0, 25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 31, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 32, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 39, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
*** V123999019 ***

CONFIGURATION 1: 400 mA ==================================
   bLength              :    0x9 (9 bytes)
   bDescriptorType      :    0x2 Configuration
   wTotalLength         :   0x22 (34 bytes)
   bNumInterfaces       :    0x1
   bConfigurationValue  :    0x1
   iConfiguration       :    0x4 Bus Powered
   bmAttributes         :   0x80 Bus Powered
   bMaxPower            :   0xc8 (400 mA)
    INTERFACE 0: Human Interface Device ====================
     bLength            :    0x9 (9 bytes)
     bDescriptorType    :    0x4 Interface
     bInterfaceNumber   :    0x0
     bAlternateSetting  :    0x0
     bNumEndpoints      :    0x1
     bInterfaceClass    :    0x3 Human Interface Device
     bInterfaceSubClass :    0x1
     bInterfaceProtocol :    0x1
     iInterface         :    0x0 
      ENDPOINT 0x81: Interrupt IN ==========================
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :   0x81 IN
       bmAttributes     :    0x3 Interrupt
       wMaxPacketSize   :    0x8 (8 bytes)
       bInterval        :    0xa


Metrologic :
Raw data [0, 0, 83, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 83, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 2, 0, 25, 0, 0, 0, 0, 0, 2, 0, 30, 0, 0, 0, 0, 0, 2, 0, 31, 0, 0, 0, 0, 0, 2, 0, 32, 0, 0, 0, 0, 0, 2, 0, 38, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 2, 0, 38, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 2, 0, 38, 0, 0, 0, 0, 0, 2, 0, 39, 0, 0, 0, 0, 0, 2, 0, 30, 0, 0, 0, 0, 0, 2, 0, 38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
*** NLNL!#)( ***

CONFIGURATION 1: 490 mA ==================================
bLength              :    0x9 (9 bytes)
bDescriptorType      :    0x2 Configuration
wTotalLength         :   0x69 (105 bytes)
bNumInterfaces       :    0x3
bConfigurationValue  :    0x1
iConfiguration       :    0x4 C-1
bmAttributes         :   0xe0 Self Powered, Remote Wakeup
bMaxPower            :   0xf5 (490 mA)
INTERFACE 0: Human Interface Device ====================
    bLength            :    0x9 (9 bytes)
    bDescriptorType    :    0x4 Interface
    bInterfaceNumber   :    0x0
    bAlternateSetting  :    0x0
    bNumEndpoints      :    0x2
    bInterfaceClass    :    0x3 Human Interface Device
    bInterfaceSubClass :    0x0
    bInterfaceProtocol :    0x1
    iInterface         :    0x5 HID Keyboard Emulation
    ENDPOINT 0x81: Interrupt IN ==========================
    bLength          :    0x7 (7 bytes)
    bDescriptorType  :    0x5 Endpoint
    bEndpointAddress :   0x81 IN
    bmAttributes     :    0x3 Interrupt
    wMaxPacketSize   :    0x8 (8 bytes)
    bInterval        :    0x8
    ENDPOINT 0x1: Interrupt OUT ==========================
    bLength          :    0x7 (7 bytes)
    bDescriptorType  :    0x5 Endpoint
    bEndpointAddress :    0x1 OUT
    bmAttributes     :    0x3 Interrupt
    wMaxPacketSize   :    0x8 (8 bytes)
    bInterval        :    0x8
INTERFACE 1: Human Interface Device ====================
    bLength            :    0x9 (9 bytes)
    bDescriptorType    :    0x4 Interface
    bInterfaceNumber   :    0x1
    bAlternateSetting  :    0x0
    bNumEndpoints      :    0x2
    bInterfaceClass    :    0x3 Human Interface Device
    bInterfaceSubClass :    0x0
    bInterfaceProtocol :    0x1
    iInterface         :    0x7 HID POS
    ENDPOINT 0x82: Interrupt IN ==========================
    bLength          :    0x7 (7 bytes)
    bDescriptorType  :    0x5 Endpoint
    bEndpointAddress :   0x82 IN
    bmAttributes     :    0x3 Interrupt
    wMaxPacketSize   :   0x40 (64 bytes)
    bInterval        :    0x3
    ENDPOINT 0x2: Interrupt OUT ==========================
    bLength          :    0x7 (7 bytes)
    bDescriptorType  :    0x5 Endpoint
    bEndpointAddress :    0x2 OUT
    bmAttributes     :    0x3 Interrupt
    wMaxPacketSize   :   0x40 (64 bytes)
    bInterval        :    0x3
INTERFACE 2: Human Interface Device ====================
    bLength            :    0x9 (9 bytes)
    bDescriptorType    :    0x4 Interface
    bInterfaceNumber   :    0x2
    bAlternateSetting  :    0x0
    bNumEndpoints      :    0x2
    bInterfaceClass    :    0x3 Human Interface Device
    bInterfaceSubClass :    0x0
    bInterfaceProtocol :    0x1
    iInterface         :    0x9 REM
    ENDPOINT 0x83: Interrupt IN ==========================
    bLength          :    0x7 (7 bytes)
    bDescriptorType  :    0x5 Endpoint
    bEndpointAddress :   0x83 IN
    bmAttributes     :    0x3 Interrupt
    wMaxPacketSize   :   0x40 (64 bytes)
    bInterval        :    0x3
    ENDPOINT 0x3: Interrupt OUT ==========================
    bLength          :    0x7 (7 bytes)
    bDescriptorType  :    0x5 Endpoint
    bEndpointAddress :    0x3 OUT
    bmAttributes     :    0x3 Interrupt
    wMaxPacketSize   :   0x40 (64 bytes)
    bInterval        :    0x3

"""
