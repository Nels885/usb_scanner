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
```
