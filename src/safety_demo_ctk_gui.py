import tkinter
import numpy as np
import customtkinter as tk
import customtkinter
# from customtkinter.font_manager import BOLD, Font


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

from color_gradient import ColorGradient

tk.set_appearance_mode("dark")


class SafetyDemoGui():

    board_connected = False
    progress_bar_update_speed = 500
    buttons_fading_speed = 300
    left_window_width = 300

    board_product_name = "CP2108 Quad USB to UART Bridge Controller"
    board_pattern = ".*Silicon Labs Quad CP2108 USB to UART Bridge: Interface 0.*"

    # Important! This is the list of events that can be received from the board
    events_dict = { "PATTERN_DONE":"" , "STARTED":"" ,  "PATTERN_STOP":"", "PATTERN_SKIP":"" , "BLINK":"" , "SMS_RESET":"" , "START_LOOP":"", "STOP_LOOP":"" , "CHECK_LOOP":"" }

    top_button_height = 50

    def __init__(self):
        self.root_window = self.create_window()
        self.uart = None
        self.root_window.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed
        # Make temp directory if doesn't exist
        self.this_file_path = os.path.abspath(os.path.dirname(__file__))
        tempdir = os.path.join( self.this_file_path , "..","temp")  
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)


        self.board_loop = False # Here I store if board main function is in the loop or not. If not we need to send S to start it

        # Create locks
        self.uart_lock = threading.Lock()
        self.uart_log_lock = threading.Lock()


        self.far_right_colomn = 0
        
        # ============ create two frames ============

        # configure grid layout (2x1)
        self.root_window.grid_columnconfigure(1, weight=1)
        self.root_window.grid_rowconfigure(0, weight=1)

        self.frame_left = tk.CTkFrame(master=self.root_window,
                                                 width= self.left_window_width,
                                                 corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nswe")
        self.frame_left.grid_propagate(0)


        self.window = tk.CTkFrame(master=self.root_window, corner_radius=0)
        self.window.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)
  
        # ============ create left frame  ============

        # Synopsys logo image
        
        synopsys_logo_img = Image.open( os.path.join ( self.this_file_path, "..", "img" , "Synopsys_Logo.png")) # USE ABSOLUTE PATH TODO
        
        logo_width, logo_height = synopsys_logo_img.size
        synopsys_logo_img = synopsys_logo_img.resize((int(logo_width/4), int(logo_height/4)), Image.ANTIALIAS)
        synopsys_logo_tk = ImageTk.PhotoImage(synopsys_logo_img)
        label1 = tk.CTkLabel(image=synopsys_logo_tk , master=self.frame_left)
        label1.image = synopsys_logo_tk
        label1.grid(column= self.far_right_colomn, row=0 , pady=10 , padx=10 , columnspan=2, rowspan=2, sticky="nw")
        
        # Add logo to the left frame
        # self.frame_left.grid_columnconfigure(0, weight=1)
        self.label_log = tk.CTkLabel(text="Safety Demo log", master=self.frame_left)
        self.label_log.grid(column= self.far_right_colomn, row=2 , pady=10 , padx=10 , columnspan=2, sticky="n")

        # ============ create frame_right grid ============
        
        # self.window.configure("TButton", font=('Arial', 25))
        
        self.window.columnconfigure((0, 1), weight=1)
        self.window.columnconfigure(2, weight=0)


        self.grid_matrix = 0 # Matrix to procedurally generate vertical widgets
        # self.window.columnconfigure(0, weight=1)

        self.connect_button = tk.CTkButton(self.window, text ="Connect", command = self.check_ports , height = self.top_button_height)
        self.connect_button.grid(column=0, row=self.grid_matrix, sticky="we", padx=10, pady=10 , columnspan=3, rowspan=2)
        
        self.grid_matrix += 2 # Go next line


        # self.change_connection_status_button = tk.CTkButton(self.window, text ="Change Connection Status", command = self.change_connection_status)
        # self.change_connection_status_button.grid(column=0, row=1 , padx=10, pady=10, sticky="nsew")
        


        
        # Add blink button

        self.power_button = tk.CTkButton(self.window, text ="KEY ON", command = self.send_start_command ,  height = self.top_button_height ) 
        self.power_button.grid(column=0, row=self.grid_matrix , padx=10, pady=10 , sticky="we" , columnspan = 2  )
        

        # Add error injection button

        self.error_injection_button = tk.CTkButton(self.window, text ="Error Injection", command = self.send_blink_command ,  height = self.top_button_height )
        self.error_injection_button.grid(column=2, row=self.grid_matrix , padx=10, pady=10 , sticky="we" , columnspan = 1  )

        self.grid_matrix += 1 # Go next line

        # Add reset button
        self.reset_button = tk.CTkButton(self.window, text ="Reset", command = self.send_reset_command , height = self.top_button_height )
        self.reset_button.grid(column=0, row=self.grid_matrix , padx=10, pady=10 , sticky="we" , columnspan = 1  )
        

        # Add pereodic switch slider
        self.pereodic_switch_var = customtkinter.StringVar(value="off")
        pereodic_switch = customtkinter.CTkSwitch(master=self.window, text="Pereodic execution", command=self.switch_event,
                                        variable=self.pereodic_switch_var, onvalue="on", offvalue="off")
        pereodic_switch.grid(column=2, row=self.grid_matrix , padx=10, pady=10 , sticky="we" , columnspan = 1  )

        # Add demo progress bar
        self.progress_bar = tk.CTkProgressBar(self.window, width=200, height=20)
        self.progress_bar.grid(column=1, row=self.grid_matrix, sticky="we", padx=10, pady=10, columnspan=1)
        
        self.progress_bar_value = 0
        self.update_progress_bar_value()

        self.grid_matrix += 1
        

 

        # Add serial status log
        # self.serial_status_log = tk.CTkTextbox(self.window, height=10, width=30)


        # Create patterns buttons
        # self.pattern_definition = ["Connectivity_check", "BIST", "XLBIST", "Pattern 4", "Pattern 5"]

        # test_0_0[] = "all_id_sel                                ";
        # test_0_1[] = "FBIST                                     ";
        # test_0_2[] = "BIST                                      ";
        # test_0_3[] = "xlbist_wrapper_4_pattern_1                ";
        # test_0_4[] = "smu_timer_run                             ";
        # test_0_5[] = "ecc_wrapper_2_Initialization              ";
        # test_0_6[] = "ecc_wrapper_2_Step1_interrupt_initiation  ";
        # test_0_7[] = "ecc_wrapper_2_Step2_Interrupt_WDR_status  ";
        # test_0_8[] = "reset                                     ";
        # test_0_9[] = "set_ecc_wrapper_2_Initialization_test_in_0";
        # test_0_10[] = "set_ecc_wrapper_2_Initialization_test_in_1";


        self.pattern_definition_dict = [
                                    {"name":"Connectivity check"        , "index":0, "reset":True  , "group" : None , "visible" : True },
                                    {"name":"Memory transparent BIST"   , "index":1, "reset":True  , "group" : None , "visible" : True },
                                    {"name":"Memory BIST"               , "index":2, "reset":True  , "group" : None , "visible" : True },
                                    {"name":"XLBIST Logic test"         , "index":3, "reset":True  , "group" : None , "visible" : True },
                                    {"name":"smu count"                 , "index":4, "reset":True  , "group" : None , "visible" : True },
                                    {"name":"ECC_init"                  , "index":5, "reset":False , "group" : None , "visible" : True },
                                    {"name":"Ecc_test"                  , "index":6, "reset":False , "group" : None , "visible" : False},
                                    {"name":"ECC read WDR"              , "index":7, "reset":False , "group" : None , "visible" : True }
                                    ]
        self.patterns = []
        for pattern_def in self.pattern_definition_dict:
            self.patterns.append(Pattern_Block ( self.window,
                                                pattern_def["name"],
                                                pattern_def["index"],
                                                reset = pattern_def["reset"],
                                                offset = self.grid_matrix,
                                                group = pattern_def["group"],
                                                visible = pattern_def["visible"]
                                                # function = lambda: self.run_pattern( pattern_def['index'] )
                                                ))
            self.grid_matrix += self.patterns[-1].height
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

        # ==================== Add init process  ====================

        self.root_window.after(500, self.send_check_board_loop_status_command)

        # ================ Turn Periodic updates ON =================
        
        self.pereodic_process_check()
        self.periodic_connection_check_init() # Init port check
        self.event_check()
        self.update_gui()
        self.root_window.mainloop()
        

    def create_window(self):
        window = tk.CTk()
        window.title("Synopsys demontration safety GUI app")
        return window

    def switch_event(self):
        print("switch toggled, current value:", self.pereodic_switch_var.get())  

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
    
    def send_check_board_loop_status_command(self):
        if self.uart:
            self.write_to_serial_port("c")
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
        for pattern in self.patterns:
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

                        # EVENT CHECK_LOOP -> Checks c
                        elif event.event_type == "CHECK_LOOP":
                            if event.dict_data:
                                self.board_loop = bool(event.dict_data["status"]) 
                        # EVENT INNER LOOP START
                        
                        elif event.event_type == "START_LOOP":
                            self.board_loop = True

                        # EVENT INNER LOOP END

                        elif event.event_type == "STOP_LOOP":
                            self.board_loop = False

                        # EVENT STARTED -> What to do if the board is reseted.
                        elif event.event_type == "STARTED":
                            self.board_loop = False
                            for pattern in self.patterns:
                                pattern.reset_pattern_gui()


                        # Remove event from the queue
                        self.uart.events.remove(event)

            # Now iterate over processes without mutex
            for event in events_to_process:
                self.update_pattern_status(event)

        if self.board_loop:
            self.power_button.configure(text="KEY ON", fg_color="green")
        else:
            self.power_button.configure(text="KEY ON", fg_color="grey")
        
        self.root_window.after(100, self.event_check)

    def update_gui(self):
        for pattern in self.patterns:
            pattern.update_gui()
        self.root_window.after(self.buttons_fading_speed, self.update_gui)


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

            if self.patterns[pattern_index].visible:
                self.patterns[pattern_index].pattern_result.configure(text=pattern_result)
                self.patterns[pattern_index].pattern_result.configure(fg_color="green" if pattern_result == "PASSED" else "red")
                if pattern_result == "PASSED":
                    self.patterns[pattern_index].color_gradient = ColorGradient( mode = "green_to_grey")
                else:
                    self.patterns[pattern_index].color_gradient = ColorGradient( mode = "red_to_grey")
            
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

    def send_start_command(self):
        print("Sending start command")
        self.write_to_serial_port("s")
        if not self.board_loop:
            self.root_window.after(1000, self.run_all_tests)
            
    def write_to_serial_port(self, data):
        if self.uart:
            with self.uart_lock:
                self.uart.send(str.encode(data))

    
    def update_progress_bar_value(self):
        if self.pereodic_switch_var.get() == "on": 
            if self.progress_bar_value >= 1:
                self.run_all_tests()

            if self.progress_bar_value >= 1:
                self.progress_bar_value = 0
            self.progress_bar_value = self.progress_bar_value + 0.05
            self.progress_bar.set (value=self.progress_bar_value)
            # print(f"Progress bar value: {self.progress_bar_value}")
        self.root_window.after(self.progress_bar_update_speed, self.update_progress_bar_value)

    def run_all_tests(self):
        print("Running all tests")
        timeout = 0
        pattern_threads = []
        for pattern in self.patterns:
                    print(f"Starting thread for pattern {pattern.pattern_name} with delay {timeout}")
                    pattern_threads.append(
                        threading.Thread(target=self.send_pattern_after_timeout, args=(timeout, pattern.pattern_number))
                    )
                    pattern_threads[-1].start()
                    timeout += 1

    def send_pattern_after_timeout(self, timeout , pattern):
        """Sleep for `timeout` ms and then send pattern to the board."""
        if self.uart:
            time.sleep(timeout)
            self.run_pattern(self.patterns[pattern])
            return 1
        else:
            return 0

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
    default_button_height = 40
    pady = 10

    def __init__(self, window, pattern_name, pattern_number , reset = False , offset = 0 , function = None , visible = True , group = None):
        self.height = 1
        self.colomn_couter = 0
        self.window = window
        self.function = function
        self.reset = reset
        self.visible = visible
        self.pattern_name = pattern_name
        self.pattern_number = pattern_number
        self.last_run = None
        self.run = False

        self.pattern_status = "Never run"
        self.pattern_result = "None"
        self.color_gradient = None
        # self.pattern_label 

        if self.visible:
            # ADd pattern button
            self.pattern_button = tk.CTkButton(self.window, text = f"{self.pattern_name}", command = self.run_pattern , height = self.default_button_height , width = 300)
            self.pattern_button.grid(column=self.colomn_couter, row= pattern_number + offset , padx=10, pady= self.pady , sticky="w" , columnspan= 2 )
            self.colomn_couter += 1

            # Add pattern status

            # self.pattern_status = tk.CTkLabel(self.window, text = self.pattern_status)
            # self.pattern_status.grid(column=self.colomn_couter, row= pattern_number + offset , padx=5, pady = self.pady  , sticky="nsew" , columnspan=2 )
            # self.colomn_couter += 2

            # Add pattern result

            self.pattern_result = tk.CTkLabel(self.window, text = self.pattern_result , height = self.default_button_height , width = 300)
            # if self.pattern_result == "Pass":
            #     self.pattern_result.configure(bg_color="green")
            # elif self.pattern_result == "Fail":
            #     self.pattern_result.configure(bg_color="red")
            # else:
            self.pattern_result.configure(bg_color="grey")
            self.pattern_result.grid(column=self.colomn_couter, row= pattern_number + offset , padx=5, pady= self.pady  , sticky="e" , columnspan = 1 )
            self.colomn_couter += 1

    def run_pattern(self):
        print(f"Run pattern {self.pattern_name}")
        # self.pattern_status.configure(text = "Running")
        if self.visible:
            self.pattern_result.configure(text = "None")
        self.run = True

    def reset_pattern_gui(self):
        # self.pattern_status.configure(text = "Never run")
        if self.visible:
            self.pattern_result.configure(text = "None", fg_color = "grey", bg_color = "grey")
        self.last_run = None
        self.run = False

    def update_gui(self):
        if self.last_run:
            last_run = str(int(time.time()) - self.last_run)
            if self.color_gradient and self.visible:
                self.pattern_result.configure( fg_color = self.color_gradient.get_color() )
            # self.pattern_status.configure(text = f"Last run {last_run} seconds ago" )

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
