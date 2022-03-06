# USB Scanner

Package allowing to read a barcode or QR-code from USB scanner listed below.

## Instructions

1. Install:

```
pip install usb-scanner
```

2. Example of use:

```python
from usb_scanner import Reader

# Initialize Reader object
r = Reader(language="UK")

# Waiting for a barcode to be read
r.read()
```
