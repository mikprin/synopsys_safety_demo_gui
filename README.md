# synopsys_safety_demo_gui

This is a simple UART wrapping GUI for communication with the ZCU106 board.

# Manual installation

You need to have python3.10 and python3-pip installed for your platform. This is a main requirement.

To install python3 dependencies from attached file, run:

    `pip3 install -r requirements.txt`
using the `requirements.txt` file in the root of this repository.

# Usage

To launch the GUI just run `safety_demo_ctk_gui.py` with your python3.10 installation.

# Archetechture

Source are presented with `safety_demo_ctk_gui.py` with `SafetyDemoGui` class and `uart_handler` with `UartHandler`.


# Regarding serial communication:

Just some links for me:
https://stackoverflow.com/questions/49566331/pyserial-how-to-continuously-read-and-parse
https://stackoverflow.com/questions/19231465/how-to-make-a-serial-port-sniffer-sniffing-physical-port-using-a-python/19232484#19232484