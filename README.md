# epnm-elex

# Pulsed Electromigration Protocol GUI

This project is a Python-based graphical user interface (GUI) designed for controlling and automating the pulsed electromigration protocol used at **EPNM (Experimental Physics of Nanostructured Materials)**, **ULiège**. The software interfaces with various source-measure units and nanovoltmeters, providing a streamlined way to execute the pusled electromigration protocol under different configurations. Created by Stefan Marinković (smarinkovic@uliege.be; marinkovicstefan@outlook.com). See https://doi.org/10.1103/PhysRevApplied.19.054009 for a description of the protocol.

## Features
- Automated control of source-measure units and nanovoltmeters.
- Configurable parameters for multiple device types.
- Real-time plotting of measurement data.
- Cross-platform support (Linux and Windows).
- Pulsed electromigration protocol.
- R(t) measurement.
  
## Requirements
- Python 3.x
- Libraries:
  - `numpy`
  - `matplotlib`
  - `pyvisa`
  - `pyvisa-py`
  - `pyusb`
  - `pyserial`
  - `gpib-ctypes`
  - `Pillow`
  - `tkinter`
- Keithley Source-Measure Units and/or Nanovoltmeters:
  - K2612B (SMU)
  - K2192A (Nanovoltmeter)
  - K6221 (Signal Generator)
  - K24x0 (SMU)

To install these dependencies, run:
```pip install -r requirements.txt```

## Installation
1. **Clone the repository:**
```
mkdir epnm-elex
cd epnm-elex
git clone https://github.com/stef-ma/epnm-elex.git
```
2. **Install the requirements:**
```pip install -r requirements.txt```


3. **Platform-Specific Notes:**
   - For Linux, ensure you have the necessary FOSS libraries installed. Follow the guidelines for configuring the `pyvisa-py` backend, as well as adding `udev` rules for instrument recognition (see [Python USBTMC GitHub](https://github.com/python-ivi/python-usbtmc)).
   - For Windows, you may need NI-VISA drivers for some configurations.

## Setup and Troubleshooting for pyvisa with GPIB/USB/Serial Backends

### Environment Setup:

- Ensure that all necessary libraries are installed: `pyvisa`, `pyvisa-py`, `pyusb`, `pyserial`, and `gpib-ctypes`.
  
  Install them via:
```pip install pyvisa pyvisa-py pyusb pyserial gpib-ctypes```


### GPIB Driver Setup (Linux):

- Install GPIB drivers (`linux-gpib`) and ensure that GPIB kernel modules are loaded before running the program:
```sudo modprobe gpib_common``` ```sudo modprobe ni_usb_gpib```
- If using USB instruments, ensure the instrument is recognized using `lsusb` or `gpib_config`. You may also need to add appropriate `udev` rules for the instrument.

### udev Rules for USB/GPIB (Linux Specific):
  
For USB and GPIB devices, add `udev` rules to allow non-root access:

```SUBSYSTEM=="usb", ATTR{idVendor}=="your_vendor_id", ATTR{idProduct}=="your_product_id", MODE="0666"```
After adding the rule, reload `udev`:

```
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Common Problems and Solutions:

- **Problem: `ModuleNotFoundError` for `pyvisa` or `gpib_ctypes`**
  - **Solution:** Ensure the correct Python environment is active. Verify that all required libraries are installed.

- **Problem: GPIB errors (`invalid descriptor`, `No such device`)**
  - **Solution:** Ensure GPIB kernel modules are loaded (`gpib_common`, `ni_usb_gpib`). Verify the device connections and GPIB configuration using `gpib_config`.

- **Problem: USB communication errors (e.g., `[Errno 19] No such device`)**
  - **Solution:** Check the USB connection and disable power management for the relevant USB port if needed.

- **Problem: Serial communication failures**
  - **Solution:** Ensure the serial device is properly configured, and avoid serial resources (`ASRL`) if not needed.

- **General Tip:** Enable verbose logging for `pyvisa` to assist in troubleshooting:
```import pyvisa``` ```pyvisa.log_to_screen()```

### Testing the Setup:
After setting everything up, use a simple script to confirm the instrument is recognized:

```
import pyvisa
rm = pyvisa.ResourceManager('@py')
print(rm.list_resources()) # List all connected instruments
```

If the instrument is listed, proceed with opening the resource and sending commands ('*IDN?' is a good starting point).

## Usage
1. **Launch the GUI:**
```python main.py```

2. **Select Configuration:**
   - Choose the source-measure unit or nanovoltmeter configuration from the center display. If none show up, there's something wrong with pyvisa or your instrument connection. This can be painful to configure. Clicking 'EDIT' at any point brings you back to this screen. Once the instrument is selected click the corresponding "Select Instrument" button on the left.
   - Once all desired instruments are connected select the configuration by clicking the buttons on the right.
   - Set the saving directory on the bottom left.
   - Configure your instruments.
   - Adjust the pulsed electromigration protocol parameters.

3. **Run the Experiment:**
   - Start the measurement (R(t) or full pusling protocol), and monitor real-time plots.
   - Threshold resistance can be set in the panel above. Note that it is read in real time and might interrupt measurements during editing if it reads a small number. Set it before starting, or edit it by copy pasting a complete number into it.

4. **Save Data:**
   - The data is saved in `.csv` format for further analysis in your SAVEDIR.

## Publications
This code has been used in the following publications:
- 10.1002/aelm.202101290
- 10.1103/PhysRevApplied.19.054009

## Contact
For more information or questions, contact:
- **Stefan Marinković**
- Email: marinkovicstefan@outlook.com

## Contributing
Contributions are welcome! If you find bugs or want to request new features, please open an issue or submit a pull request.

## License
I didn't take care of the licence yet. Consider it free with attribution.

## Acknowledgements
Special thanks to the **EPNM ULiege** team for providing the research groundwork and testing the protocol with various equipment setups.

## Known bugs
The GUI becomes unusably slow in the K2612B+K2192A setup. Do not use.
