import tkinter as tk
import threading


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
        self.grid_matrix = [[0,],[0,]] # Matrix to procedurally generate widgets
        self.window.columnconfigure(0, weight=1)

        self.connect_button = tk.Button(self.window, text ="Connect", command = self.check_ports)
        self.connect_button.grid(column=0, row=0, sticky="nsew")
        
        # self.change_connection_status_button = tk.Button(self.window, text ="Change Connection Status", command = self.change_connection_status)
        # self.change_connection_status_button.grid(column=0, row=1 , padx=10, pady=10, sticky="nsew")
        
        
        # Synopsys logo image
        
        synopsys_logo_img = Image.open("../img/Synopsys_Logo.png") # USE ABSOLUTE PATH TODO
        
        logo_width, logo_height = synopsys_logo_img.size
        synopsys_logo_img = synopsys_logo_img.resize((int(logo_width/5), int(logo_height/6)), Image.ANTIALIAS)
        synopsys_logo_tk = ImageTk.PhotoImage(synopsys_logo_img)
        label1 = tk.Label(image=synopsys_logo_tk)
        label1.image = synopsys_logo_tk
        self.grid_matrix[0].append(1)
        label1.grid(column=1, row=0 , pady=5 , padx=10)
        
        
        


        self.serial_status_label = tk.Label(self.window, text = "Serial Status")
        self.serial_status_label.grid(column=0, row=2, pady=5 , columnspan=2)
        # Create text widget and specify size.
        self.serial_status_log = tk.Text(self.window, height = 15, width = 100)
        self.serial_status_log.grid(column=0, row=3 , columnspan=2 , pady=2)
        # self.connect_button.pack()

        # self.change_connection_status_button.pack()

        self.periodic_add_serial_status()
        # self.serial_status_label.pack()
        # self.serial_status_log.pack()
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



def read_uart(port, uart_lock , baud_rate=115200 ):
    ser = serial.Serial('/dev/ttyUB0', 9600)
    while True:
        line = ser.readline().decode('utf-8').rstrip()
        with uart_lock
        

if __name__ == '__main__':
    safety_gui = SafetyDemoGui()
