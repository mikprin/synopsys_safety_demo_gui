import serial
import  threading

class Board_Serial_Emulator(object):
    def __init__(self, port, baudrate = 115200, timeout = 0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = serial.Serial(port, baudrate, timeout = timeout)
        self.uart_mutex = threading.Lock()
        self.recive_quene = []
        self.stop_reading = False
        
        self.start_recive_threads()
        
    def recive(self):
        """Loop for read thread to read data from the serial port."""
        data_str = []
        while True:
            # Check if incoming bytes are waiting to be read from the serial input 
            # buffer.
            # NB: for PySerial v3.0 or later, use property `in_waiting` instead of
            # function `inWaiting()` below!
            if (self.serial.inWaiting() > 0):
                # read the bytes and convert from binary array to ASCII
                data_str = self.serial.read(self.serial.inWaiting()).decode('utf-8').rstrip().replace("\r","").split("\n")
                # print the incoming string without putting a new-line
                # ('\n') automatically after every print()
                # print(data_str, end='')
                with self.quene_mutex:
                    self.recive_quene.append(*data_str)
            # Break if self.stop_reading is set to True
            if self.stop_reading:
                break
            time.sleep(0.01)
    
    def start_recive_threads(self):
        """Start recive threads."""
        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()
    
    def send(self, data, add_newline=True):
        """Send data to the serial port."""
        if add_newline:
            data += b'\r\n'
        self.serial.write(data)
        
    def recive_parser(self):
        """Parse recive quene."""
        while True:
            if len(self.recive_quene) > 0:
                with self.quene_mutex:
                    data = self.recive_quene.pop(0)
                print(data)
            time.sleep(0.01)

if __name__ == "__main__":
    board_serial_emulator = Board_Serial_Emulator("/dev/ttyUSB0")