from re import S
import time
import serial
import threading

class UartHandler:
    def __init__(self, port, baudrate , events_dict = {}, timeout = 0.5):
        '''Initialize the serial port.'''
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.events_dict = events_dict
        self.serial = serial.Serial(port, baudrate, timeout=self.timeout)
        # self.serial.open()
        
        self.quene_mutex = threading.Lock()
        self.line_quene_mutex = threading.Lock()
        self.event_mutex = threading.Lock()
        self.stop_reading = False
        self.recive_quene = []
        self.events = []

        self.start_recive_threads()

    def __del__(self):
        """Close the serial port."""
        self.stop_reading = True
        time.sleep(0.1)
        self.close()

    def send(self, data, add_newline=True):
        """Send data to the serial port."""
        if add_newline:
            data += b'\r\n'
        self.serial.write(data)

    def receive(self):
        """Loop for read thread to read data from the serial port."""
        while True:
            # Check if incoming bytes are waiting to be read from the serial input 
            # buffer.
            # NB: for PySerial v3.0 or later, use property `in_waiting` instead of
            # function `inWaiting()` below!
            if (self.serial.inWaiting() > 0):
                # read the bytes and convert from binary array to ASCII
                data_str = self.serial.read(self.serial.inWaiting()).decode('utf-8').rstrip().replace("\r","")
                # print the incoming string without putting a new-line
                # ('\n') automatically after every print()
                # print(data_str, end='')
                with self.quene_mutex:
                    self.recive_quene.append(data_str)
            # Break if self.stop_reading is set to True
            if self.stop_reading:
                break
            time.sleep(0.01)

    def start_recive_threads(self):
        """Start recive threads."""
        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()
        self.event_parser_thread = threading.Thread(target=self.event_parser, args=(self.events_dict,))
        self.event_parser_thread.start()
        

    def recive_quene_to_lines_converter(self):
        """Convert recive quene to lines"""
        data = None
        with self.quene_mutex:
            if len(self.recive_quene) > 0:
                data = self.recive_quene.pop(0)
        if data:
            # This lins is added to avoid doing this operation with mutex
            data = data.rstrip().split("\n")
        return data
    

    def event_parser(self, events_dict):
        while True:
            data = self.recive_quene_to_lines_converter()
            if data:
                for line in data:
                    # Check if line contain EVENT:* with regex
                    if line.startswith("EVENT:"):
                        line = line.replace("EVENT: ","")
                        line_list = line.split(" ")
                        for event in events_dict.keys():
                            if line_list[0] in event:
                                print(f"Event detected: {event}. Adding to event dict")
                                with self.event_mutex:
                                    # Add event to event dict
                                    self.events.append(Event(event, original_data=line))
            if self.stop_reading:
                break
            time.sleep(0.01)

    def check_read_thread(self , restart = False):
        """Check if the read thread is running. Restart if restart is True."""
        if not self.receive_thread.is_alive():
            print("Read thread is dead")
            if restart:
                self.start_recive_threads()
                print("Read thread restarted")
        else :
            print("Read thread is alive")

    def close(self):
        self.serial.close()

    def clear_quene(self):
        """Clear the recive quene."""
        with self.quene_mutex:
            self.recive_quene = []

    def clear_events(self):
        """Clear the events quene."""
        with self.event_mutex:
            self.events = []


class Event:
    def __init__(self, event_type , original_data=""):
        self.event_type = event_type
        self.event_timestamp = int(time.time())
        self.original_data = original_data
    def __str__(self):
        return f"{self.event_type}:{self.event_timestamp}"
    def __repr__(self) -> str:
        return f"{self.event_type}:{self.event_timestamp}"