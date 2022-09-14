from ast import pattern
# import tkinter as tk
import tkinter
import threading
import time, os, sys
import customtkinter as tk


# Imports to work with serial port
import serial
import serial.tools.list_ports

from PIL import ImageTk, Image 

from apscheduler.schedulers.blocking import BlockingScheduler

class SafetyDemoGui():

    board_connected = False

    board_product_name = "CP2108 Quad USB to UART Bridge Controller"

    def __init__(self):
        self.window = self.create_window()
        self.grid_matrix = 0 # Matrix to procedurally generate vertical widgets
        self.window.columnconfigure(0, weight=1)

        self.connect_button = tk.CTkButton(self.window, text ="Connect", command = self.check_ports)
        self.connect_button.grid(column=0, row=self.grid_matrix, sticky="nsew", padx=10, pady=10 , columnspan=3)
        self.grid_matrix += 1
        # self.change_connection_status_button = tk.CTkButton(self.window, text ="Change Connection Status", command = self.change_connection_status)
        # self.change_connection_status_button.grid(column=0, row=1 , padx=10, pady=10, sticky="nsew")
        
        
        # Synopsys logo image
        
        synopsys_logo_img = Image.open("../img/Synopsys_Logo.png") # USE ABSOLUTE PATH TODO
        
        logo_width, logo_height = synopsys_logo_img.size
        synopsys_logo_img = synopsys_logo_img.resize((int(logo_width/5), int(logo_height/5)), Image.ANTIALIAS)
        synopsys_logo_tk = ImageTk.PhotoImage(synopsys_logo_img)
        label1 = tk.Label(image=synopsys_logo_tk)
        label1.image = synopsys_logo_tk
        label1.grid(column=5, row=0 , pady=10 , padx=10)
        
        # Create locks
        self.uart_lock = threading.Lock()
        self.uart_log_lock = threading.Lock()
        
        # Add blink button

        self.blink_button = tk.CTkButton(self.window, text ="Blink", command = self.send_blink_command)
        self.blink_button.grid(column=0, row=self.grid_matrix , padx=5, pady=5 , sticky="nsew")
        self.grid_matrix += 1

        # Add serial status log
        # self.serial_status_log = tk.Text(self.window, height=10, width=30)


        # Create patterns buttons
        self.pattern_names = ["Pattern 1", "Pattern 2", "Pattern 3", "Pattern 4", "Pattern 5"]
        self.patterns = []
        for i in range(len(self.pattern_names)):
            self.patterns.append(Pattern_Block ( self.window, self.pattern_names[i], i , self.grid_matrix ))
        # self.grid_matrix += len(self.patterns)
        for pattern in self.patterns:
            self.grid_matrix += pattern.height
        


        # Debug window
        self.serial_status_label = tk.Label(self.window, text = "Serial Status")
        self.serial_status_label.grid(column=0, row=self.grid_matrix, pady=5 , columnspan=2)
        self.grid_matrix += 1
        # Create text widget and specify size.
        self.serial_status_log = tk.Text(self.window, height = 15, width = 100)
        self.serial_status_log.grid(column=0, row=self.grid_matrix , columnspan=2 , pady=2)
        # self.connect_button.pack()
        self.grid_matrix += 1

        # self.change_connection_status_button.pack()

        self.periodic_add_serial_status()
        # self.serial_status_label.pack()
        # self.serial_status_log.pack()
        self.periodic_connection_check_init()

        self.window.mainloop()

    def create_window(self):
        # window = tk.Tk()
        window = tk.CTk()
        window.title("Welcome to Safety GUI app")
        return window

    
    def board_connect(self):
        # self.
        self.board_connected = True
        self.connect_button.configure(text="Connected", bg="green" , fg="white")

    def board_disconnect(self):
        self.board_connected = False
        self.connect_button.configure(text="Not Connected", fg="White", bg="Red")
    
    def send_blink_command(self):
        if self.board_connected:
            # port = self.get_serial_ports()[0].device
            port = "/dev/ttyUSB0"
            data = "b"
            self.write_to_serial_port(data, port, self.uart_lock)
            # write_thread = threading.Thread(target=self.write_to_serial_port, args=(data, self.uart_port, self.uart_lock))
        else:
            print("Board not connected")


    # def periodic_connection_check_init(self):
    #     scheduler = BlockingScheduler()
    #     scheduler.add_job(self.check_board_connection, 'interval', seconds=3)
    #     # scheduler.start()
    #     check_thread =  threading.Thread(target=scheduler.start)
    #     return check_thread

    def periodic_connection_check_init(self):
        self.check_ports()
        self.window.after(2000, self.periodic_connection_check_init)

    def get_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return ports

    def check_ports(self):
        ports = self.get_serial_ports()
        for port in ports:
            if port.product == self.board_product_name:
                self.board_connect()
                return True
        self.board_disconnect()
        return False    

    # def periodic_check_connection(self):
        
    #     self.check_board_connection()
    #     self.window.after(2000, self.periodic_check_connection)

    # Debug call

    def change_connection_status(self):
        self.board_connected = not self.board_connected
        print(f"Connection status changed to {self.board_connected}")

    def periodic_add_serial_status(self):
        self.serial_status_log.delete(1.0, tk.END)
        self.serial_status_log.insert(tk.END,self.get_serial_ports())
        self.serial_status_log.insert(tk.END, f"Connection status: {self.board_connected}")
        self.window.after(2000, self.periodic_add_serial_status)



    # def read_uart(self,port, uart_lock, file_lock, baud_rate=115200, temp_file="uart.log"):
    #     serial_port = serial.Serial(port, baud_rate, timeout=0.1)
    #     while True:
    #         with uart_lock:
    #             line = serial_port.readline().decode('utf-8').rstrip()
    #         with file_lock:
    #             with open(temp_file, 'a') as f:
    #                 f.write(line + '\n')
            
    def write_to_serial_port(self, data, port, uart_lock, baud_rate=115200):
        with self.uart_lock:
            with serial.Serial(port, baud_rate, timeout=0.05) as serial_port:
                print(f"Writting to serial port: {data}")
                serial_port.write(f'{data}\r\n'.encode())
        time.sleep(0.01)

class Pattern_Block:
    def __init__(self, window, pattern_name, pattern_number , offset = 0):
        self.height = 1
        self.colomn_couter = 0
        self.window = window
        self.pattern_name = pattern_name
        self.pattern_number = pattern_number

        self.pattern_status = "Never run"
        self.pattern_result = "None"

        # self.pattern_label 

        # ADd pattern button
        self.pattern_button = tk.CTkButton(self.window, text = f"Run {self.pattern_name}", command = self.send_pattern_command)
        self.pattern_button.grid(column=self.colomn_couter, row= pattern_number + offset , padx=5, pady=5 , sticky="nsew" )
        self.colomn_couter += 1

        # Add pattern status

        self.pattern_status = tk.Label(self.window, text = self.pattern_status)
        self.pattern_status.grid(column=self.colomn_couter, row= pattern_number + offset , padx=5, pady=5 , sticky="nsew" )
        self.colomn_couter += 1

        # Add pattern result

        self.pattern_result = tk.Label(self.window, text = self.pattern_result)
        if self.pattern_result == "Pass":
            self.pattern_result.configure(bg="green")
        elif self.pattern_result == "Fail":
            self.pattern_result.configure(bg="red")
        else:
            self.pattern_result.configure(bg="white")
        self.pattern_result.grid(column=self.colomn_couter, row= pattern_number + offset , padx=5, pady=5 , sticky="nsew" )
        self.colomn_couter += 1

    def send_pattern_command(self):
        print(f"Pattern {self.pattern_number} selected")


if __name__ == '__main__':
    safety_gui = SafetyDemoGui()
