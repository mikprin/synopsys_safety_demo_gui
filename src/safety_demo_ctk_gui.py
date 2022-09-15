import tkinter
import numpy as np
import customtkinter as tk
import threading
import time, os, sys, io
import matplotlib.pyplot as plt

# Imports to work with serial port
import serial
import serial.tools.list_ports

from PIL import ImageTk, Image 

from apscheduler.schedulers.blocking import BlockingScheduler

tk.set_appearance_mode("dark")


class SafetyDemoGui():

    board_connected = False

    board_product_name = "CP2108 Quad USB to UART Bridge Controller"

    def __init__(self):
        self.root_window = self.create_window()

        self.root_window.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed
        # Make temp directory if doesn't exist

        tempdir = os.path.join("..","temp") # TODO change to absolute path  
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)


        # Create locks
        self.uart_lock = threading.Lock()
        self.uart_log_lock = threading.Lock()

        self.far_right_colomn = 0
        
        # ============ create two frames ============

        # configure grid layout (2x1)
        self.root_window.grid_columnconfigure(1, weight=1)
        self.root_window.grid_rowconfigure(0, weight=1)

        self.frame_left = tk.CTkFrame(master=self.root_window,
                                                 width=180,
                                                 corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nswe")

        self.window = tk.CTkFrame(master=self.root_window , width=400, corner_radius=0)
        self.window.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)



        # ============ create left frame  ============



        # Synopsys logo image
        
        synopsys_logo_img = Image.open("../img/Synopsys_Logo.png") # USE ABSOLUTE PATH TODO
        
        logo_width, logo_height = synopsys_logo_img.size
        synopsys_logo_img = synopsys_logo_img.resize((int(logo_width/5), int(logo_height/5)), Image.ANTIALIAS)
        synopsys_logo_tk = ImageTk.PhotoImage(synopsys_logo_img)
        label1 = tk.CTkLabel(image=synopsys_logo_tk , master=self.frame_left)
        label1.image = synopsys_logo_tk
        label1.grid(column= self.far_right_colomn, row=0 , pady=10 , padx=10 , columnspan=2, rowspan=2, sticky="nsew")
        
        # Add logo to the left frame
        # self.frame_left.grid_columnconfigure(0, weight=1)
        label_log = tk.CTkLabel(text="Safety Demo log", master=self.frame_left)
        label_log.grid(column= self.far_right_colomn, row=2 , pady=10 , padx=10 , columnspan=2, sticky="n")


        # ============ create frame_right grid ============
        self.window.columnconfigure((0, 1), weight=1)
        self.window.columnconfigure(2, weight=0)


        self.grid_matrix = 0 # Matrix to procedurally generate vertical widgets
        # self.window.columnconfigure(0, weight=1)

        self.connect_button = tk.CTkButton(self.window, text ="Connect", command = self.check_ports , height= 40)
        self.connect_button.grid(column=0, row=self.grid_matrix, sticky="we", padx=10, pady=10 , columnspan=4, rowspan=2)
        self.grid_matrix += 2
        # self.change_connection_status_button = tk.CTkButton(self.window, text ="Change Connection Status", command = self.change_connection_status)
        # self.change_connection_status_button.grid(column=0, row=1 , padx=10, pady=10, sticky="nsew")
        
        # Add demo progress bar
        self.progress_bar = tk.CTkProgressBar(self.window, width=200, height=20)
        self.progress_bar.grid(column=2, row=self.grid_matrix, sticky="we", padx=10, pady=10, columnspan=2)
        
        self.progress_bar_value = 0
        self.update_progress_bar_value()

        
        # Add blink button

        self.blink_button = tk.CTkButton(self.window, text ="Blink", command = self.send_blink_command , height = 50) 
        self.blink_button.grid(column=0, row=self.grid_matrix , padx=10, pady=10 , sticky="we" , columnspan = 2  )
        self.grid_matrix += 1

        # Add serial status log
        # self.serial_status_log = tk.CTkTextbox(self.window, height=10, width=30)


        # Create patterns buttons
        self.pattern_names = ["Pattern 1", "Pattern 2", "Pattern 3", "Pattern 4", "Pattern 5"]
        self.patterns = []
        for i in range(len(self.pattern_names)):
            self.patterns.append(Pattern_Block ( self.window, self.pattern_names[i], i , self.grid_matrix ))
        # self.grid_matrix += len(self.patterns)
        for pattern in self.patterns:
            self.grid_matrix += pattern.height
        


        ######################## Add picture to the window ########################

        # Create sqare wave image
        # self.time_value = 0.1
        # img_buf = plot_sqare_wave(self.time_value)
        # Resize image

        


        # Y_DIV = 1
        # X_DIV = 1
        # img_buf = img_buf.resize((int(img_buf.size[0]/X_DIV), int(img_buf.size[1]/Y_DIV)), Image.ANTIALIAS)
        # tk_plot = ImageTk.PhotoImage(img_buf)
        # self.label_plot = tk.CTkLabel(image=tk_plot , master=self.window)
        # self.label_plot.image = tk_plot
        # self.label_plot.grid(column=0, row=self.grid_matrix , pady=10 , padx=10 , columnspan=2, sticky="w")
        
        # self.grid_matrix += 1

        # self.root_window.after(1000, self.update_picture)



        # Debug window
        # self.serial_status_label = tk.CTkLabel(self.window, text = "Serial Status")
        # self.serial_status_label.grid(column= self.far_right_colomn, row=3, pady=2, padx = 15 , columnspan=2)
        # # self.grid_matrix += 1
        # # Create text widget and specify size.
        # self.serial_status_log = tk.CTkLabel(self.window, height = 400, width = 100)
        # self.serial_status_log.grid(column= self.far_right_colomn, row=4 , columnspan=5 , pady=2 , padx = 15 , rowspan=10 )
        # # self.connect_button.pack()
        # # self.grid_matrix += 1


        # self.change_connection_status_button.pack()

        # self.periodic_add_serial_status()
        # self.serial_status_label.pack()
        # self.serial_status_log.pack()



        self.periodic_connection_check_init() # Init port check

        self.root_window.mainloop()







    def create_window(self):
        window = tk.CTk()
        window.title("Welcome to Safety GUI app")
        return window

    
    def board_connect(self):
        # self.
        self.board_connected = True
        self.connect_button.configure(text="Connected", bg_color="green" , fg_color="grey")

    def board_disconnect(self):
        self.board_connected = False
        self.connect_button.configure(text="Not Connected", fg_color="red", bg_color="Red")
    
    def send_blink_command(self):
        if self.board_connected:
            # port = self.get_serial_ports()[0].device
            port = "/dev/ttyUSB0"
            data = "b"
            self.write_to_serial_port(data, port, self.uart_lock)
            # write_thread = threading.Thread(target=self.write_to_serial_port, args=(data, self.uart_port, self.uart_lock))
        else:
            print("Board not connected")

        # blink with button 
        
    def update_picture(self):
        del(self.label_plot.image)
        self.time_value += 0.2
        img_buf = plot_sqare_wave(self.time_value)
        Y_DIV = 1
        X_DIV = 1
        img_buf = img_buf.resize((int(img_buf.size[0]/X_DIV), int(img_buf.size[1]/Y_DIV)), Image.ANTIALIAS)
        tk_plot = ImageTk.PhotoImage(img_buf)
        
        # label_plot = tk.CTkLabel(image=tk_plot , master=self.window)
        # self.label_plot.image = tk_plot
        self.label_plot.configure(image=tk_plot)
        self.label_plot.image = tk_plot
        self.root_window.after(800, self.update_picture)
        
    # def periodic_connection_check_init(self):
    #     scheduler = BlockingScheduler()
    #     scheduler.add_job(self.check_board_connection, 'interval', seconds=3)
    #     # scheduler.start()
    #     check_thread =  threading.Thread(target=scheduler.start)
    #     return check_thread

    def periodic_connection_check_init(self):
        self.check_ports()
        self.root_window.after(2000, self.periodic_connection_check_init)

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
        # self.serial_status_log.delete(1.0, tk.END)
        # self.serial_status_log.insert(tk.END,self.get_serial_ports())
        # self.serial_status_log.insert(tk.END, f"Connection status: {self.board_connected}")
        self.serial_status_log.configure(text = f" {self.get_serial_ports()}\nConnection status: {self.board_connected}")
        self.root_window.after(2000, self.periodic_add_serial_status)



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

    
    def update_progress_bar_value(self):
        if self.progress_bar_value >= 1:
            self.progress_bar_value = 0
        self.progress_bar_value = self.progress_bar_value + 0.05
        self.progress_bar.set (value=self.progress_bar_value)
        # print(f"Progress bar value: {self.progress_bar_value}")
        self.root_window.after(1000, self.update_progress_bar_value)

    def on_closing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.root_window.destroy()

class Pattern_Block:
    default_button_height = 30
    pady = 10

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
        self.pattern_button = tk.CTkButton(self.window, text = f"Run {self.pattern_name}", command = self.send_pattern_command , height = self.default_button_height)
        self.pattern_button.grid(column=self.colomn_couter, row= pattern_number + offset , padx=5, pady= self.pady , sticky="w" , columnspan=1 )
        self.colomn_couter += 1

        # Add pattern status

        self.pattern_status = tk.CTkLabel(self.window, text = self.pattern_status)
        self.pattern_status.grid(column=self.colomn_couter, row= pattern_number + offset , padx=5, pady = self.pady  , sticky="nsew" , columnspan=2 )
        self.colomn_couter += 2

        # Add pattern result

        self.pattern_result = tk.CTkLabel(self.window, text = self.pattern_result)
        if self.pattern_result == "Pass":
            self.pattern_result.configure(bg_color="green")
        elif self.pattern_result == "Fail":
            self.pattern_result.configure(bg_color="red")
        else:
            self.pattern_result.configure(bg_color="grey")
        self.pattern_result.grid(column=self.colomn_couter, row= pattern_number + offset , padx=5, pady= self.pady  , sticky="e" )
        self.colomn_couter += 1

    def send_pattern_command(self):
        print(f"Pattern {self.pattern_number} selected")


def plot_sqare_wave(t):
    # Create pil buffer
    img_buf = io.BytesIO()
    # Create figure
    fig = plt.figure( figsize=(3,2), dpi=200)
    # Add x axis label 
    plt.xlabel('Time (s)')
    # Add y axis label
    plt.ylabel('Voltage (V)')
    # Add title
    plt.title('Approximate clock and derivation')
    x = np.linspace(0, 2*np.pi, 100)
    y = np.sin(x + t)
    y_ref = np.sin(x)
    plt.plot(x, y, label='Signal')
    plt.plot(x, y_ref, label='Reference')
    plt.legend()
    # plt.show()
    plt.savefig(img_buf, format='png')
    # img_buf.seek(0)
    return Image.open(img_buf)
        


if __name__ == '__main__':
    safety_gui = SafetyDemoGui()
