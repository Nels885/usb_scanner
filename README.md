# USB Scanner

Package allowing to read a barcode or QR-code from USB scanner listed below.

https://sps.honeywell.com/fr/fr/products/productivity/barcode-scanners/general-purpose-handheld/voyager-xp-1470g-general-duty-scanner

https://www.zebra.com/gb/en/products/scanners/general-purpose-scanners/handheld/ls1203.html


## Instructions

1. Install:

```
pip install usb-scanner
```

2. Example of use:

```python
from usb_scanner import Reader

# Initialize Reader object
r = Reader(keymap="UK")

# Waiting for a barcode to be read
r.read()

# If you want have a timeout for the reading
r.read(timeout=10)
```

## Fix udev permissions


Create a Udev rule for the use of USB scanners (hidraw*)

```shell
$ sudo nano /etc/udev/rules.d/99-hidraw-permissions.rules
```

and add the following lines

```
SUBSYSTEM=="usb", ATTRS{idVendor}=="05e0", ATTRS{idProduct}=="1200", MODE="666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="080c", ATTRS{idProduct}=="0300", MODE="666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0c2e", ATTRS{idProduct}=="1001", MODE="666"
```
Finally reload the udev rules with the following command

```shell
$ sudo udevadm control --reload-rules && sudo udevadm trigger
```
