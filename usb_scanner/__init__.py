"""
***********************************************************
        Reader Class
        Create Date: 09/01/2018
        By: L.VOIRIN
***********************************************************
   0.0.1    Adaptation module Reader        LV  09/01/2018
   0.0.2    Package creation                LV  06/03/2022
   0.0.3    Finalize of the test version    LV  06/03/2022

***********************************************************
"""

import usb

from .usb_devices import scanners
from .exceptions import ReadException, DeviceException
from . import mapping


class Reader:

    def __init__(self, keymap="FR", debug=False, **kwargs):
        """
        :param keymap: select keyboard map
        :param debug: if true will print raw data
        :param vendor_id: USB vendor id (check dmesg or lsusb under Linux)
        :param product_id: USB device id (check dmesg or lsusb under Linux)
        :param device_name: USB device name
        :param data_size: how much data is expected to be read
        :param chunk_size: chunk size like 8 or 16, check by looking on the raw output with debug=True
        :param should_reset: if true will also try to reset device preventing garbage reading.
        Doesn't work with all devices - locks them
        """
        self.keymap = keymap
        self.debug = debug
        self.idVendor = kwargs.get("vendor_id", None)
        self.idProduct = kwargs.get("product_id", None)
        self.deviceName = kwargs.get("device_name", "unknown")
        self.dataSize = kwargs.get("data_size", 84)
        self.chunkSize = kwargs.get("chunk_size", 16)
        self.shouldReset = kwargs.get("should_reset", False)
        self.interfaces, self.configs = 0, 0
        self._device = None
        self._endpoint = None
        self.initialize()

    def initialize(self):
        for scanner in scanners:
            self._device = usb.core.find(idVendor=scanner[1], idProduct=scanner[2])
            if self._device is not None:
                self.deviceName, self.idVendor, self.idProduct, self.chunkSize = scanner
                break
    
        if self._device is None:
            raise DeviceException('No device found, check vendor_id and product_id')

        for config in self._device:
            self.configs += 1
            self.interfaces = config.bNumInterfaces
            for i in range(config.bNumInterfaces):
                if self._device.is_kernel_driver_active(i):
                    self._device.detach_kernel_driver(i)

        try:
            self._device.set_configuration()
            if self.shouldReset:
                self._device.reset()
        except usb.core.USBError as err:
            raise DeviceException(f'Could not set configuration: {err}')

        self._endpoint = self._device[0][(0, 0)][0]

    def get_device_config(self):
        return print(self._device[0])

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
                    if len(data) < self.dataSize:
                        self.disconnect()
                        raise ReadException('Got %s bytes instead of %s - %s' % (len(data), self.dataSize, str(data)))
                    else:
                        break
               
        if self.debug:
            print('Raw data', data)

        self.disconnect()
        return str(self._decode_raw_data(data).strip())

    def map_character(self, c):
        return mapping.keys_page[self.keymap].get(c, '')
    
    def disconnect(self):
        if self.shouldReset:
            self._device.reset()
        for i in range(self.interfaces):
            usb.util.release_interface(self._device, i)
            self._device.attach_kernel_driver(i)

    def _decode_raw_data(self, raw_data):
        data = self._extract_meaningful_data_from_chunk(raw_data)
        return self._raw_data_to_keys(data)

    def _extract_meaningful_data_from_chunk(self, raw_data):
        shift_indicator_index = 0
        raw_key_value_index = 2
        for chunk in self._get_chunked_data(raw_data):
            yield (chunk[shift_indicator_index], chunk[raw_key_value_index])

    def _get_chunked_data(self, raw_data):
        for i in iter(range(0, len(raw_data), self.chunkSize)):
            yield raw_data[i:i + self.chunkSize]

    def _raw_to_key(self, key):
        if key[0] == 2:
            return mapping.shift_keys_page[self.keymap].get(key[1], '')
        else:
            return mapping.keys_page[self.keymap].get(key[1], '')

    def _raw_data_to_keys(self, extracted_data):
        return ''.join(map(self._raw_to_key, extracted_data))
