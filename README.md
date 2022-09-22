# synopsys_safety_demo_gui

This is a simple UART wrapping GUI for communication with the ZCU106 board.

# Manual installation

You need to have python3.10 and python3-pip installed for your platform. This is a main requirement. You can find the latest python [here](https://www.python.org/downloads/). You also need to install  python3-pip along the way.

To install python3 dependencies from attached file, run:

    `pip3 install -r requirements.txt`
using the `requirements.txt` file in the root of this repository.


## Drivers

You need to install CP21xx drivers from [ the link  ( official silicon labs site ) ](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads)

# Usage

To launch the GUI just run `safety_demo_ctk_gui.py` with your python3.10 installation.

## Hardware connection

To see that board was connected all you need is to connect computer USB port with the board's UART micro USB port. After that you will see that connection button is green and board readings is there. Board will send readings only of power is ON.

(picture of the port will be here)
# Archetechture

Source are presented with `safety_demo_ctk_gui.py` with `SafetyDemoGui` class and `uart_handler` with `UartHandler`.

## Event mechanism

To handle events from the board, we use `UartHandler` class. It is a thread that is constantly reading from the UART port. It is also responsible for sending commands to the board. Messages with `EVENT:` are checked for events and are sent to the `SafetyDemoGui` class. `SafetyDemoGui` class is responsible for handling events and updating the GUI. It is also responsible for sending commands to the `UartHandler` class according to button-specific and pereodic actions.

As of writing this, there are following events that are handled by the `SafetyDemoGui` class:
```
    events_dict = { "PATTERN_DONE":"" ,
                    "STARTED":"" ,
                    "PATTERN_STOP":"",
                    "PATTERN_SKIP":"" ,
                    "BLINK":"" ,
                    "SMS_RESET":"",
                    "START_LOOP":"",
                    "STOP_LOOP":"" ,
                    "CHECK_LOOP":"",
                    "VALUE_UPDATE":"" }
```
# Known issues

* If too many messages are recived to the board, UartHandler will split it into 2 readings and event line might be split in half. You can overcome this issue by not dfining `DEBUG_PRINTS` in `main.c` file of the firmware to limit the number of prints.
* If you are using Windows, you might need to install [this](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads) driver to make the board work.


# Regarding serial communication:

Just some links for me:
https://stackoverflow.com/questions/49566331/pyserial-how-to-continuously-read-and-parse
https://stackoverflow.com/questions/19231465/how-to-make-a-serial-port-sniffer-sniffing-physical-port-using-a-python/19232484#19232484