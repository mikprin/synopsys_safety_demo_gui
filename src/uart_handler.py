import time
import serial
import threading

class UartHandler:
    def __init__(self, port, baudrate , timeout = 0.5):
        '''Initialize the serial port.'''
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = serial.Serial(port, baudrate, timeout=self.timeout)
        # self.serial.open()
        
        self.quene_mutex = threading.Lock()
        self.line_quene_mutex = threading.Lock()
        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()

        self.stop_reading = False

        self.recive_quene = []

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

    def recive_quene_parser(self):
        with self.quene_mutex:
            if len(self.recive_quene) > 0:
                data = self.recive_quene.pop(0).rstrip().split("\n")
                return data
            else:
                return None

    def check_read_thread(self , restart = False):
        if not self.receive_thread.is_alive():
            print("Read thread is dead")
            if restart:
                self.receive_thread = threading.Thread(target=self.receive)
                self.receive_thread.start()
                print("Read thread restarted")
        else :
            print("Read thread is alive")

    def close(self):
        self.serial.close()

    def on_board_reset(self):
        # self.send(b'\x00')
        print("Board was reset")

    def clear_quene(self):
        with self.quene_mutex:
            self.recive_quene = []