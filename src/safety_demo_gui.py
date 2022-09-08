from subprocess import call
from tabnanny import check
import tkinter as tk
import threading


# Imports to work with serial port
import serial
import serial.tools.list_ports

from apscheduler.schedulers.blocking import BlockingScheduler

class SafetyDemoGui():

    board_connected = False

    board_product_name = 'CP2108 Quad USB to UART Bridge Controller - CP2108 Interface 3'

    def __init__(self):
        self.window = self.create_window()
        self.connect_button = tk.Button(self.window, text ="Connect", command = self.check_ports)
        self.connect_button.grid(column=0, row=0)
        self.change_connection_status_button = tk.Button(self.window, text ="Change Connection Status", command = self.change_connection_status)
        # self.change_connection_status_button.grid(column=0, row=1)

        self.serial_status_label = tk.Label(self.window, text = "Serial Status")
        # Create text widget and specify size.
        self.serial_status_log = tk.Text(self.window, height = 5, width = 52)

        self.connect_button.pack()
        self.change_connection_status_button.pack()

        self.periodic_add_serial_status()
        self.serial_status_label.pack()
        self.serial_status_log.pack()
        self.periodic_connection_check_init()

        self.window.mainloop()

    def create_window(self):
        window = tk.Tk()
        window.title("Welcome to Safety GUI app")
        return window

    
    def board_connect(self):
        self.board_connected = True
        self.connect_button.configure(text="Connected", bg="green" , fg="white")

    def board_disconnect(self):
        self.board_connected = False
        self.connect_button.configure(text="Not Connected", fg="White", bg="Red")
    


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

if __name__ == '__main__':
    safety_gui = SafetyDemoGui()
