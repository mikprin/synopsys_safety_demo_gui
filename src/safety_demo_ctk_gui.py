from ast import pattern
import tkinter
import numpy as np
import customtkinter as tk
import threading
import time, os, sys, io , re
import matplotlib.pyplot as plt

# Imports to work with serial port
import serial
import serial.tools.list_ports

from PIL import ImageTk, Image 

from apscheduler.schedulers.blocking import BlockingScheduler
from functools import partial
# My own files
import uart_handler


tk.set_appearance_mode("dark")


class SafetyDemoGui():

    board_connected = False

    board_product_name = "CP2108 Quad USB to UART Bridge Controller"
    board_pattern = ".*Silicon Labs Quad CP2108 USB to UART Bridge: Interface 0.*"
    events_dict = { "PATTERN_DONE":"" , "STARTED":"" ,  "PATTERN_STOP":"", "PATTERN_SKIP":"" , "BLINK":"" , "SMS_RESET":"" }

    def __init__(self):
        self.root_window = self.create_window()
        self.uart = None
        self.root_window.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed
        # Make temp directory if doesn't exist
        self.this_file_path = os.path.abspath(os.path.dirname(__file__))
        tempdir = os.path.join( self.this_file_path , "..","temp")  
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
                                                 width=400,
                                                 corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nswe")
        self.frame_left.grid_propagate(0)


        self.window = tk.CTkFrame(master=self.root_window, corner_radius=0)
        self.window.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)
  
        # ============ create left frame  ============

        # Synopsys logo image
        
        synopsys_logo_img = Image.open( os.path.join ( self.this_file_path, "..", "img" , "Synopsys_Logo.png")) # USE ABSOLUTE PATH TODO
        
        logo_width, logo_height = synopsys_logo_img.size
        synopsys_logo_img = synopsys_logo_img.resize((int(logo_width/5), int(logo_height/5)), Image.ANTIALIAS)
        synopsys_logo_tk = ImageTk.PhotoImage(synopsys_logo_img)
        label1 = tk.CTkLabel(image=synopsys_logo_tk , master=self.frame_left)
        label1.image = synopsys_logo_tk
        label1.grid(column= self.far_right_colomn, row=0 , pady=10 , padx=10 , columnspan=2, rowspan=2, sticky="nw")
        
        # Add logo to the left frame
        # self.frame_left.grid_columnconfigure(0, weight=1)
        self.label_log = tk.CTkLabel(text="Safety Demo log", master=self.frame_left)
        self.label_log.grid(column= self.far_right_colomn, row=2 , pady=10 , padx=10 , columnspan=2, sticky="n")

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
        self.progress_bar.grid(column=3, row=self.grid_matrix, sticky="we", padx=10, pady=10, columnspan=2)
        
        self.progress_bar_value = 0
        self.update_progress_bar_value()

        
        # Add blink button

        self.blink_button = tk.CTkButton(self.window, text ="Blink", command = self.send_blink_command , height = 50) 
        self.blink_button.grid(column=0, row=self.grid_matrix , padx=10, pady=10 , sticky="we" , columnspan = 1  )


        # Add error injection button

        self.error_injection_button = tk.CTkButton(self.window, text ="Error Injection", command = self.send_error_injection_command , height = 50)
        self.error_injection_button.grid(column=1, row=self.grid_matrix , padx=10, pady=10 , sticky="we" , columnspan = 1  )
        self.grid_matrix += 1

        # Add reset button
        self.reset_button = tk.CTkButton(self.window, text ="Reset", command = self.send_reset_command , height = 50)
        self.reset_button.grid(column=0, row=self.grid_matrix , padx=10, pady=10 , sticky="we" , columnspan = 2  )
        self.grid_matrix += 1

        # Add serial status log
        # self.serial_status_log = tk.CTkTextbox(self.window, height=10, width=30)


        # Create patterns buttons
        # self.pattern_definition = ["Connectivity_check", "BIST", "XLBIST", "Pattern 4", "Pattern 5"]
        self.pattern_definition_dict = [
                                    {"name":"Connectivity_check","index":0,"reset":True}, 
                                    {"name":"BIST","index":1,"reset":True},
                                    {"name":"XLBIST","index":2,"reset":True}
                                    ]
        self.patterns = []
        for pattern_def in self.pattern_definition_dict:
            self.patterns.append(Pattern_Block ( self.window,
                                                pattern_def["name"],
                                                pattern_def["index"],
                                                reset = pattern_def["reset"],
                                                offset = self.grid_matrix,
                                                # function = lambda: self.run_pattern( pattern_def['index'] )
                                                )
            self.grid_matrix += self.patterns[pattern_def["name"]].height
        # self.grid_matrix += len(self.patterns)
        # for pattern in self.patterns:
        #     self.grid_matrix += pattern.height
    
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

        # Periodic updates
        
        self.pereodic_process_check()
        self.periodic_connection_check_init() # Init port check
        self.event_check()
        self.root_window.mainloop()


    def create_window(self):
        window = tk.CTk()
        window.title("Synopsys demontration safety GUI app")
        return window

    
    def board_connect(self):
        # self.
        self.board_connected = True
        self.connect_button.configure(text="Connected" , fg_color="green")

    def board_disconnect(self):
        if self.uart:
            with self.uart_lock:
                del(self.uart)
                self.uart = None
        self.board_connected = False
        self.connect_button.configure(text="Not Connected", fg_color="red")
    
    def send_blink_command(self):
        if self.board_connected:
            # Add text to the label_log
            text = ""
            for event in self.uart.events:
                text += str(event) + "\n"
            self.label_log.configure(text=text)
            self.write_to_serial_port("b")
        else:
            print("Board not connected")
       
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
        

    def periodic_connection_check_init(self):
        self.check_ports()
        self.root_window.after(2000, self.periodic_connection_check_init)


    def check_ports(self):
        """Scan for available ports. If board is detected, connect to it (create uart handler)."""
        # ports = self.get_serial_ports()
        if not self.board_connected:
            for port in serial.tools.list_ports.comports():
                # check ports against regular expression
                if re.match(self.board_pattern, port.description):
                    print("Board found")
                    try:
                        self.uart = uart_handler.UartHandler(port.device, 115200 , events_dict=self.events_dict)
                        self.board_connect()
                    except Exception as e:
                        print("Failed to create UartHandler")
                        print(e)
                        self.board_disconnect()
                        return False
                    return True
                # for port in ports:
                #     if port.product == self.board_product_name:
                #         self.board_connect()
                #         return True
            self.board_disconnect()
            return False
        else:
            for port in serial.tools.list_ports.comports():
                # check ports against regular expression
                if re.match(self.board_pattern, port.description):
                    return True
            self.board_disconnect()
            return False
        return False


    def pereodic_process_check(self):
        for pattern in self.patterns.values():
            if pattern.run:
                ## HERE IS THE CODE TO RUN THE PATTERN
                self.run_pattern(pattern)
                pattern.run = False
        self.root_window.after(500, self.pereodic_process_check)


    def event_check(self):
        '''Check if there are any events in the events queue of the UartHandler and process them.'''
        if self.uart:
            events_to_process = [] # Adding events to the list to avoid changing the list while iterating
            with self.uart.event_mutex:
                # print(f"Events to process: {len(self.uart.events)}")
                if self.uart.events:
                    for event in self.uart.events:
                        self.label_log.configure(text=str(event))

                        # EVENT PROCESS_DONE -> What to do if the pattern is done
                        if event.event_type == "PATTERN_DONE":
                            events_to_process.append(event)
                        self.uart.events.remove(event)

                        

                        # EVENT ...

                        # EVENT STARTED -> What to do if the board is reseted.
                        if event.event_type == "STARTED":
                            for pattern in self.patterns:
                                pattern.reset_pattern_gui()

            # Now iterate over processes without mutex
            for event in events_to_process:
                self.update_pattern_status(event)

        for pattern in self.patterns:
            pattern.update_gui()
        self.root_window.after(100, self.event_check)


    def update_pattern_status(self,event):
        print(f"Updating pattern {event} status")
        # self.patterns[pattern_index].run = False
        # self.patterns[pattern_index].last_run = int(time.time())
        if event.dict_data:
            pattern_index = int(event.dict_data["patternIdx"])
            pattern_result = str(event.dict_data["result"])
            self.patterns[pattern_index].last_run = int(time.time())
            # pattetn_name = self.patterns[pattern_index].pattern_name

            self.patterns[pattern_index].status = pattern_result
            self.patterns[pattern_index].pattern_result.configure(text=pattern_result)
            self.patterns[pattern_index].pattern_result.configure(fg_color="green" if pattern_result == "PASSED" else "red")

        else:
            print("Event dict data is empty!!!")

    def change_connection_status(self):
        self.board_connected = not self.board_connected
        print(f"Connection status changed to {self.board_connected}")

    def periodic_add_serial_status(self):
        # self.serial_status_log.delete(1.0, tk.END)
        # self.serial_status_log.insert(tk.END,self.get_serial_ports())
        # self.serial_status_log.insert(tk.END, f"Connection status: {self.board_connected}")
        self.serial_status_log.configure(text = f" {self.get_serial_ports()}\nConnection status: {self.board_connected}")
        self.root_window.after(2000, self.periodic_add_serial_status)


            
    def write_to_serial_port(self, data):
        if self.uart:
            with self.uart_lock:
                self.uart.send(str.encode(data))

    
    def update_progress_bar_value(self):
        if self.progress_bar_value >= 1:
            self.progress_bar_value = 0
        self.progress_bar_value = self.progress_bar_value + 0.05
        self.progress_bar.set (value=self.progress_bar_value)
        # print(f"Progress bar value: {self.progress_bar_value}")
        self.root_window.after(1000, self.update_progress_bar_value)

    def on_closing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        if self.uart:
            with self.uart_lock:
                del(self.uart)
                self.uart = None
        self.root_window.destroy()

    def run_pattern(self,pattern):
        # pattern_number = pattern.pattern_number
        print(f"Running pattern {pattern.pattern_name}")
        if self.uart:
            if pattern.reset:
                with self.uart_lock:
                    self.uart.send(str.encode("r"))
                time.sleep(0.5)
            with self.uart_lock:
                self.uart.send(str(pattern.pattern_number).encode())

    def send_reset_command(self):
        if self.uart:
            with self.uart_lock:
                self.uart.send(str.encode("r"))

    def send_error_injection_command(self):
        print("Sending error injection command")
        if self.uart:
            with self.uart_lock:
                self.uart.send(str.encode("e"))
        self.error_injection_button.configure(fg_color="red")

class Pattern_Block:
    default_button_height = 30
    pady = 10

    def __init__(self, window, pattern_name, pattern_number , reset = False , offset = 0 , function = None):
        self.height = 1
        self.colomn_couter = 0
        self.window = window
        self.function = function
        self.reset = reset
        self.pattern_name = pattern_name
        self.pattern_number = pattern_number
        self.last_run = None
        self.run = False

        self.pattern_status = "Never run"
        self.pattern_result = "None"

        # self.pattern_label 

        # ADd pattern button
        self.pattern_button = tk.CTkButton(self.window, text = f"Run {self.pattern_name}", command = self.run_pattern , height = self.default_button_height)
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

    def run_pattern(self):
        print(f"Run pattern {self.pattern_name}")
        self.pattern_status.configure(text = "Running")
        self.pattern_result.configure(text = "None")
        self.run = True

    def reset_pattern_gui(self):
        self.pattern_status.configure(text = "Never run")
        self.pattern_result.configure(text = "None", fg_color = "grey", bg_color = "grey")
        self.last_run = None
        self.run = False

    def update_gui(self):
        if self.last_run:
            last_run = str(int(time.time()) - self.last_run) 
            self.pattern_status.configure(text = f"Last run {last_run} seconds ago" )


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
    input("Press Enter to continue...")
