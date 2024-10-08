import os
import time
import tkinter.messagebox
from PIL import ImageTk, Image
from mylibs.InstSelect import *
from mylibs.MeasFrame import *
from mylibs.Observer import *

LARGE_FONT = ("Cambria", 12)


class AppWindow(tk.Tk):  # inherits the tkinter root window class
    """"Class that holds the tkinter window."""

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Attribute initialization
        self.k2612B_instrument = None  # pyvisa resourcemanager k2612B_instrument controller
        self.k6221_instrument = None  # pyvisa resourcemanager k6221_instrument controller
        self.k2182A_instrument = None  # pyvisa resourcemanager k2182A_instrument controller
        self.k2400_instrument = None  # pyvisa resourcemanager k2400_instrument controller
        self.filedir = None  # savefile later turned to tkinter filedialog object, use .get() to read
        self.width = 1300  # for window geometry
        self.pane_height = 85  # for window geometry
        self.complianceA = False
        self.complianceB = False
        self.file_obj = None

        # Time management
        self.boot_time = time.time()  # Start time, for time tracking
        self.runtime = time.time() - self.boot_time  # Gets updated in _time every couple ms
        self.exec_time = tk.StringVar()  # For user display
        self.exec_time.set(str(int(self.runtime)))
        self.time1 = 0.  # For observer management
        self.time2 = 0.
        self.time3 = 0.

        # Creating the observer
        self.observer = Observer()  # self.observer[0] are functions executed every .5s
        # self.observer[1], every .083 and self.observer[2] every ms
        # Frames (tkinter containers) are horizontal sections of the window stacked on top of one another,..
        # ...in order to allow for easier organization of the GUI elements. Details of this are set in updateCallOut

        # Set Up the Window
        self.title('EPNM - Testing Workstation')
        self.configure(background='black')

        #    -------------------------------------------------------------------------------------------------------
        #   |                                                                                                       |
        #   |              Frame1:   Title, overview, start and edit button.                                        |
        #   |                                                                                                       |
        #   |-------------------------------------------------------------------------------------------------------|
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |              Frame2:    Holds the active class being used.                                            |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |                                                                                                       |
        #   |-------------------------------------------------------------------------------------------------------|
        #   |                                                                                                       |
        #   |              Frame3:    Holds the indicators                                                          |
        #   |                                                                                                       |
        #    -------------------------------------------------------------------------------------------------------

        # -----------------------------------------------------------------------------------------------------------
        # Frame 1
        # Will have top banner as well as start and stop buttons
        self.top_frame = NewFrame(self, self.width, self.pane_height * 1.2)  # NewFrame inherits tk.Frame,
        # see gui_frames for details
        self.top_frame.pack_propagate(0)  # stops deformation of parent frames by child frames
        self.top_frame.pack(side='top', fill='x')
        self._decorate_top_frame(self.top_frame)  # Decorating method, draws logo, title label
        # and creates the start and stop buttons, see methods below
        # -----------------------------------------------------------------------------------------------------------

        # Frame 2
        # Will have several pages to hold the different measurement setups
        self.mid_frame = NewFrame(self, self.width, 4 * self.pane_height)
        self.mid_frame.pack_propagate(0)
        # to hold most controls and indicators
        self.mid_frame.pack(side='top', fill='x')
        # controller set up!
        # All control panes (InstCont_XXXX) are instanced below and are always held in memory.
        # Selecting one of the measurements in the GUI pulls one of the InstCont frames to front.
        container = self.mid_frame  # got this logic from stackoverflow,
        # essentially all frames that are shown in the middle get created below
        # and are later only raised to top on demand with _show_frame
        # packing the frame:
        container.pack(side="top", fill="both")
        container.grid_rowconfigure(0, weight=1)  # It is necessary to give weight to the grid cells for this to work.
        container.grid_columnconfigure(0, weight=1)
        # create dict to hold the instances we will create
        self.mid_subframes = {}
        for F in (Blank,
                  InstCont_K2612B,
                  InstCont_K2612BandK2182A,
                  InstCont_K6221andK2182A,
                  InstCont_K2400andK2182A
                  ):
            # Classes are defined in InstCont
            frame = F(container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.mid_subframes[F] = frame
        self._show_frame(Blank)
        # -----------------------------------------------------------------------------------------------------------

        # Frame 3
        # Will have a savefile, execution time and k2612B_instrument connection indicator
        self.bot_frame = NewFrame(self, self.width, self.pane_height)
        self.bot_frame.pack_propagate(0)
        self.bot_frame.pack(side='top', fill='x')
        self._decorate_bot_frame(self.bot_frame)
        # -----------------------------------------------------------------------------------------------------------

        # Updating method for time fOand k2612B_instrument indicator for the first time
        self.observer.subscribe(self._time, 2)
        self.observer.subscribe(self._update_bottom, 0)

        self._update()  # Calls itself recursively to invoke the functions managed by the observer.

    #
    #    IMPORTANT TIME CONTROL STUFF
    def _time(self):
        # subscriber to update the time variable
        self.runtime = time.time() - self.boot_time
        # print(self.runtime)
        # uncommment the print to see looptime

    def _update(self):
        # method to update execute all subscribers, recursively calls itself
        if self.runtime - self.time3 > .5:  # self.observer.call_subscribers(0) is executed twice per second.
            self.time3 = self.runtime
            self.observer.call_subscribers(0)
        elif self.runtime - self.time2 > .025:  # self.observer.call_subscribers(1) is executed a 40 tmes per second.
            self.time2 = self.runtime
            self.observer.call_subscribers(1)
        self.observer.call_subscribers(2)  # self.observer.call_subscribers(2) is executed every loop.
        self.after(1, self._update)

    #
    #

    def _safe_exit(self):
        # safe exit method with shutdown for the SMU!
        for instrument in [self.k2612B_instrument,
                           self.k6221_instrument,
                           self.k2182A_instrument,
                           self.k2400_instrument]:
            if instrument is None:
                pass
            else:
                self._closeInstrument(instrument)
        if self.file_obj is not None:
            self.file_obj.close()
        self.destroy()

    def _startup(self):
        # Start Button method. Creates the InstSelect frame whose invocation calls inst_seek() from rm_setup.
        # In order for instruments to show up user must have access to the usb drives of the PC - on linux,
        # main must be run as superuser. On windows administrator privileges could be needed.
        frame = InstSelect(self.mid_frame, self)
        frame.grid(row=0, column=0, sticky="nsew")
        self.mid_subframes[InstSelect] = frame
        self._show_frame(InstSelect)
        self.start_button.destroy()
        self._edit_button(self.top_frame, 'se')

    def _edit_instrument(self):
        # Edit Button method. Closes the k2612B_instrument via _closeInstrument,
        # destroys the InstSelect frame in Frame 2,
        # and then recreates it to allow renewed connection to the instruments.
        for instrument in [self.k2612B_instrument,
                           self.k6221_instrument,
                           self.k2182A_instrument,
                           self.k2400_instrument]:
            if instrument is None:
                pass
            else:
                self._closeInstrument(instrument)
        self.mid_subframes[InstSelect].destroy()
        frame = InstSelect(self.mid_frame, self)
        frame.grid(row=0, column=0, sticky="nsew")
        self.mid_subframes[InstSelect] = frame
        self._show_frame(InstSelect)

    def _show_frame(self, cont):
        # Raises the given subframe of Frame 2 (See diagram above)
        frame = self.mid_subframes[cont]
        frame.tkraise()

    def _decorate_top_frame(self, banner):
        # Load Logo
        fact = 5
        self.img = Image.open("data/logo3.png")  # Use the pillow library to load the image.
        # I should think about maybe replacing this with matplotlib.image
        self.img = self.img.resize((int(self.img.size[0] / fact), int(self.img.size[1] / fact)),
                                   # Image.ANTIALIAS
                                   )  # The (int(), int()) is (height, width)
        self.img = ImageTk.PhotoImage(self.img)
        self.logo = tk.Label(banner, bg='black', image=self.img)  # We pack the image as a tk.Label. 
        # Don't judge me I got this from stackoverflow!
        self.logo.pack(side='left', padx=10)

        # Write Title
        self.title = tk.Label(banner, bg='black', fg='white', text='EPNM Electrical Testbench: Pulse EM')
        self.title.pack(side='left', padx=10)

        # Create Buttons
        self._stop_button(self.top_frame, 'ne')
        self._start_button(self.top_frame, 'se')

    def _decorate_bot_frame(self, banner):
        # Creates all the widgets in Frame 3 of the main window, see schematic above.

        # Make two subframes for organization
        bot1 = NewFrame(banner, self.width / 2, self.pane_height)
        bot1.pack_propagate(0)
        bot1.pack(side='left')
        bot2 = NewFrame(banner, self.width / 2, self.pane_height)
        bot2.pack_propagate(0)
        bot2.pack(side='right')

        # Create tk.Label to display filepath.
        self.save_file_path_label = tk.Label(bot1, bg='black', fg='white',
                                             text='file: N/A')
        self.save_file_path_label.pack()

        # Invoke method for the Save as button
        self._save_as_button(bot1)

        # Create tk.Label for time indicator
        self.bottom_time_label = tk.Label(bot2, bg='black', fg='white', text='Execution time:' + self.exec_time.get())
        self.bottom_time_label.pack(side='top')

        # Create a bool indicator for k2612B_instrument connection.
        self.instrument_bool_indicator_canvas_k2612B = tk.Canvas(bot2, width=self.pane_height / 2,
                                                                 height=self.pane_height / 2,
                                                                 bg='black', bd=0, highlightthickness=0)
        self.instrument_bool_indicator_canvas_k2612B.pack(side='right')
        self.instrument_bool_indicator_canvas_k2612B.bool_indicator = \
            self.instrument_bool_indicator_canvas_k2612B.create_oval(
                int(1 / 3 * 1 / 2 * self.pane_height), int(1 / 3 * 1 / 2 * self.pane_height),
                int(2 / 3 * 1 / 2 * self.pane_height), int(2 / 3 * 1 / 2 * self.pane_height), fill="gray")

        # Create a tk.Label for k2612B_instrument connection.
        self.instrument_bool_indicator_label_k2612B = tk.Label(bot2, bg='black', fg='white', text='K2612B connected?')
        self.instrument_bool_indicator_label_k2612B.pack(side='right')

        # Create a bool indicator for k6221 connection.
        self.instrument_bool_indicator_canvas_k6221 = tk.Canvas(bot2, width=self.pane_height / 2,
                                                                height=self.pane_height / 2,
                                                                bg='black', bd=0, highlightthickness=0)
        self.instrument_bool_indicator_canvas_k6221.pack(side='right')
        self.instrument_bool_indicator_canvas_k6221.bool_indicator = \
            self.instrument_bool_indicator_canvas_k6221.create_oval(
                int(1 / 3 * 1 / 2 * self.pane_height), int(1 / 3 * 1 / 2 * self.pane_height),
                int(2 / 3 * 1 / 2 * self.pane_height), int(2 / 3 * 1 / 2 * self.pane_height), fill="gray")

        # Create a tk.Label for k2612B_instrument connection.
        self.instrument_bool_indicator_label_k6221 = tk.Label(bot2, bg='black', fg='white', text='K6221 connected?')
        self.instrument_bool_indicator_label_k6221.pack(side='right')

        # Create a bool indicator for k2182A connection.
        self.instrument_bool_indicator_canvas_k2182A = tk.Canvas(bot2, width=self.pane_height / 2,
                                                                 height=self.pane_height / 2,
                                                                 bg='black', bd=0, highlightthickness=0)
        self.instrument_bool_indicator_canvas_k2182A.pack(side='right')
        self.instrument_bool_indicator_canvas_k2182A.bool_indicator = \
            self.instrument_bool_indicator_canvas_k2182A.create_oval(
                int(1 / 3 * 1 / 2 * self.pane_height), int(1 / 3 * 1 / 2 * self.pane_height),
                int(2 / 3 * 1 / 2 * self.pane_height), int(2 / 3 * 1 / 2 * self.pane_height), fill="gray")

        # Create a tk.Label for k2612B_instrument connection.
        self.instrument_bool_indicator_label_k2182A = tk.Label(bot2, bg='black', fg='white', text='K2182A connected?')
        self.instrument_bool_indicator_label_k2182A.pack(side='right')

        # Create a bool indicator for k2400 connection.
        self.instrument_bool_indicator_canvas_k2400 = tk.Canvas(bot2, width=self.pane_height / 2,
                                                                height=self.pane_height / 2,
                                                                bg='black', bd=0, highlightthickness=0)
        self.instrument_bool_indicator_canvas_k2400.pack(side='right')
        self.instrument_bool_indicator_canvas_k2400.bool_indicator = \
            self.instrument_bool_indicator_canvas_k2400.create_oval(
                int(1 / 3 * 1 / 2 * self.pane_height), int(1 / 3 * 1 / 2 * self.pane_height),
                int(2 / 3 * 1 / 2 * self.pane_height), int(2 / 3 * 1 / 2 * self.pane_height), fill="gray")

        # Create a tk.Label for k2400_instrument connection.
        self.instrument_bool_indicator_label_k2400 = tk.Label(bot2, bg='black', fg='white', text='K2400 connected?')
        self.instrument_bool_indicator_label_k2400.pack(side='right')

    def _update_bottom(self):
        # Updates the indicators created in _decorate_bot_frame and the Compliance indicator.
        # Needs the .runtime attribute to be updated for it to makes sense. 
        # _update_bottom is subscribed to the observer in the slowest lane as it is only interesting to the user.

        # Set the exec_time tk.StringVar to the current value of runtime.
        self.exec_time.set(str(int(self.runtime)))
        self.bottom_time_label['text'] = 'Execution time:   ' + self.exec_time.get() + ' s'

        # Set the k2612B_instrument bool indicator color.
        if self.k2612B_instrument is None:
            self.instrument_bool_indicator_canvas_k2612B.itemconfig(
                self.instrument_bool_indicator_canvas_k2612B.bool_indicator,
                fill="gray")
        else:
            self.instrument_bool_indicator_canvas_k2612B.itemconfig(
                self.instrument_bool_indicator_canvas_k2612B.bool_indicator,
                fill="green")

        # Set the k6221 bool indicator color.
        if self.k6221_instrument is None:
            self.instrument_bool_indicator_canvas_k6221.itemconfig(
                self.instrument_bool_indicator_canvas_k6221.bool_indicator,
                fill="gray")
        else:
            self.instrument_bool_indicator_canvas_k6221.itemconfig(
                self.instrument_bool_indicator_canvas_k6221.bool_indicator,
                fill="green")

        # Set the k2400_instrument bool indicator color.
        if self.k2400_instrument is None:
            self.instrument_bool_indicator_canvas_k2400.itemconfig(
                self.instrument_bool_indicator_canvas_k2400.bool_indicator,
                fill="gray")
        else:
            self.instrument_bool_indicator_canvas_k2400.itemconfig(
                self.instrument_bool_indicator_canvas_k2400.bool_indicator,
                fill="green")

        # Set the k2182A_instrument bool indicator color.
        if self.k2182A_instrument is None:
            self.instrument_bool_indicator_canvas_k2182A.itemconfig(
                self.instrument_bool_indicator_canvas_k2182A.bool_indicator,
                fill="gray")
        else:
            self.instrument_bool_indicator_canvas_k2182A.itemconfig(
                self.instrument_bool_indicator_canvas_k2182A.bool_indicator,
                fill="green")

            fill = 'blue' if self.complianceA else 'gray'
            frame = self.mid_subframes[InstCont_K2612B]
            frame.chanA_Measframe.complianceWarning.itemconfig(frame.chanA_Measframe.complianceWarning.bool_indicator,
                                                               fill=fill)
            fill = 'blue' if self.complianceB else 'gray'
            frame = self.mid_subframes[InstCont_K2612B]
            frame.chanB_Measframe.complianceWarning.itemconfig(frame.chanB_Measframe.complianceWarning.bool_indicator,
                                                               fill=fill)
            if any([self.complianceA, self.complianceB]):
                self.k2612B_instrument.beeper(0.2)

        # Set the filepath display.        
        if self.filedir is None:
            self.save_file_path_label['text'] = 'file: N\A'
        else:
            self.save_file_path_label['text'] = f'file: {self.filedir}'

    def _stop_button(self, banner, pos):
        # Creates the emergency Stop Button which can safely exit the app via _safe_exit.
        self.halt = tk.Button(banner, bg='red', text='STOP', fg='white', command=self._safe_exit)
        self.halt.pack(anchor=pos, pady=5, padx=5)

    def _start_button(self, banner, pos):
        # Start button; makes you pick an k2612B_instrument via __Start_up__.
        self.start_button = tk.Button(banner, bg='green', text='START', fg='white', command=self._startup)
        self.start_button.pack(anchor=pos, pady=5, padx=5)

    def _edit_button(self, banner, pos):
        # Creates the _edit_button in the position of the old start button. Calls _edit_instrument instead of
        # _startup as you need to close old connections to look for new ones. See methods.
        self.start_button = tk.Button(banner, text='EDIT', command=self._edit_instrument)
        self.start_button.pack(anchor=pos, pady=5, padx=5)

    def _save_as_button(self, banner):
        # Creates the Save As button in Frame 3. Calls _create_save_file.
        self.save_button = tk.Button(banner, text='SAVEDIR', command=self._create_save_file)
        self.save_button.pack(pady=5, padx=5)

    def _create_save_file(self):
        # Calls the tk.filedialog method for creating a savefile and stores the result in self.file.
        # Can later be used to access the file via pythons builtins, while offering the convenience of a prebuilt
        # filedialog.
        # files = [('All Files', '*.*'), ('Text Document', '*.txt')]
        self.filedir = tk.filedialog.askdirectory(
            # filetypes=files, defaultextension=files
        )

    def _setInstrument_K2612B(self, lbox, inlist):
        # Creates an instance of the Inst_Class class from rm_setup as self.k2612B_instrument.
        # This attribute will give us access to the InstClass_K2612B methods defined in rm_setup.
        print(inlist[lbox.curselection()[0]])
        self.k2612B_instrument = InstClass_K2612B(inlist[lbox.curselection()[0]])
        self.observer.subscribe(self._check_compliance_K2612B, 0)

    def _setInstrument_K2182A(self, lbox, inlist):
        # Creates an instance of the Inst_Class class from rm_setup as self.k2182A_instrument.
        # This attribute will give us access to the InstClass_K2182A methods defined in rm_setup.
        print(inlist[lbox.curselection()[0]])
        self.k2182A_instrument = InstClass_K2182A(inlist[lbox.curselection()[0]])

    def _setInstrument_K6221(self, lbox, inlist):
        # Creates an instance of the Inst_Class class from rm_setup as self.k6221_instrument.
        # This attribute will give us access to the InstClass_K6221 methods defined in rm_setup.
        print(inlist[lbox.curselection()[0]])
        self.k6221_instrument = InstClass_K6221(inlist[lbox.curselection()[0]])

    def _setInstrument_K2400(self, lbox, inlist):
        # Creates an instance of the Inst_Class class from rm_setup as self.k2400_instrument.
        # This attribute will give us access to the InstClass_K2400 methods defined in rm_setup.
        print(inlist[lbox.curselection()[0]])
        self.k2400_instrument = InstClass_K2400(inlist[lbox.curselection()[0]])

    def _closeInstrument(self, instrument):
        # Closes the k2612B_instrument connection, if it exists.
        if instrument is None:
            pass
        else:
            instrument._close()

    # Note that K2612B gets two methods as I made the program channel-agnostic for that instrument. One method switches
    # the channel functions (_config_) and the other sets the actual values (_command_). Similarily, the K2400 has a
    # _command_ function to select the sourcing (V or I). The other instruments only get _command_.
    def controller_config_K2612B(self, what, value, chan):
        # Config k2612B_instrument method called by various tk.OptionMenus in the InstCont_K2612B frame of Frame 2.
        # See Schematic.
        if self.k2612B_instrument is None:
            print('You tried to configure a K2612B SMU which is not connected!')
        else:
            if what == 'SRC' and value == 'I':
                self.k2612B_instrument.src_I(chan)
            elif what == 'SRC' and value == 'V':
                self.k2612B_instrument.src_V(chan)
            elif what == 'MEAS' and value == 'I':
                self.k2612B_instrument.meas_I(chan)
            elif what == 'MEAS' and value == 'V':
                self.k2612B_instrument.measure_channel(chan)
            elif what == 'SENS' and value == '2-Point':
                self.k2612B_instrument.sense_local(chan)
            elif what == 'SENS' and value == '4-Point':
                self.k2612B_instrument.sense_remote(chan)

    def controller_command_K2612B(self, what, config_widget, chan, val):
        # Command k2612B_instrument method called by various tk.Entrys in the InstCont_K2612B frame of Frame 2.
        # val is passed as the entry tk.StringVar, values are retrieved by .get()
        if self.k2612B_instrument is None:
            print('You passed a command for a K2612B SMU which is not connected!')
        else:
            if val.get()[:0] in ['e', 'E', '.', '-', '+', ' ']:
                pass
            else:
                try:
                    val_str = val.get()
                    val_float = float(val_str)
                    if what == 'Compliance':
                        # Trying to stop it from issuing "set compliance 0" when the user starts typing, as that causes
                        # an error on the isntrument (compliance must be >0!)
                        if config_widget == 'I' and 0.02 <= val_float <= 200:
                            self.k2612B_instrument.src_limit_VOLTS(chan, val_str)
                        elif config_widget == 'V' and 0.000_000_01 <= val_float <= 200:
                            self.k2612B_instrument.src_limit_AMPS(chan, val_str)
                        else:
                            pass
                    elif what == 'Range' and config_widget == 'I':
                        self.k2612B_instrument.src_range_AMPS(chan, val_str)
                    elif what == 'Range' and config_widget == 'V':
                        self.k2612B_instrument.src_range_VOLTS(chan, val_str)
                    elif what == 'Level' and config_widget == 'I':
                        self.k2612B_instrument.src_level_AMPS(chan, val_str)
                    elif what == 'Level' and config_widget == 'V':
                        self.k2612B_instrument.src_level_VOLTS(chan, val_str)
                except:
                    print('Bad Input')

    def controller_command_K6221(self, what, val):
        if self.k6221_instrument is None:
            print('You passed a command for a K6221 source which is not connected!')
        else:
            if val.get()[:0] in ['e', 'E', '.', '-', '+', ' ']:
                pass
            else:
                try:
                    val_str = val.get()
                    val_float = float(val_str)
                    if what == 'Compliance':
                        self.k6221_instrument.src_limit_VOLTS(val_float)
                    elif what == 'Range':
                        self.k6221_instrument.src_range_AMPS(val_float)
                    elif what == 'Level':
                        self.k6221_instrument.sour_lvl(val_float)
                except:
                    print('Bad Input')

    def controller_command_K2182A(self, what, val):
        if self.k2182A_instrument is None:
            print('You passed a command for a K2182A nvoltmeter which is not connected!')
        else:
            if val.get()[:0] in ['e', 'E', '.', '-', '+', ' ']:
                pass
            else:
                try:
                    val_str = val.get()
                    val_float = float(val_str)
                    if what == 'Rate':
                        self.k6221_instrument.sense_rate(val_float)
                    elif what == 'Range':
                        self.k6221_instrument.set_rng(val_float)
                    elif what == 'Digits':
                        self.k6221_instrument.sense_digits(val_str)
                except:
                    print('Bad Input')

    def controller_config_K2400(self, what, value):
        # Config k2400_instrument method called by various tk.OptionMenus in the InstCont_K2400 frame of Frame 2.
        # See Schematic.
        if self.k2400_instrument is None:
            print('You tried to configure a K2612B SMU which is not connected!')
        else:
            if what == 'SRC' and value == 'I':
                self.k2400_instrument.src_I()
            elif what == 'SRC' and value == 'V':
                self.k2400_instrument.src_V()
            elif what == 'MEAS' and value == 'I':
                self.k2400_instrument.meas_I()
            elif what == 'MEAS' and value == 'V':
                self.k2400_instrument.meas_V()
            elif what == 'SENS' and value == '2-Point':
                self.k2400_instrument.sense_local()
                # not implemented
            elif what == 'SENS' and value == '4-Point':
                self.k2400_instrument.sense_remote()
                # not implemented

    def controller_command_K2400(self, what, config_widget, val):
        # Command k2400_instrument method called by various tk.Entrys in the InstCont_K2400 frame of Frame 2.
        # val is passed as the entry tk.StringVar, values are retriev ed by .get()
        if self.k2400_instrument is None:
            print('You passed a command for a K2400 SMU which is not connected!')
        else:
            if val.get()[:0] in ['e', 'E', '.', '-', '+', ' ']:
                pass
            else:
                try:
                    val_str = val.get()
                    val_float = float(val_str)
                    if what == 'Compliance':
                        # Trying to stop it from issuing "set compliance 0" when the user starts typing, as that causes
                        # an error on the isntrument (compliance must be >0!)
                        if config_widget == 'I' and 0.02 <= val_float <= 200:
                            self.k2400_instrument.src_limit_VOLTS(val_str)
                        elif config_widget == 'V' and 0.000_000_01 <= val_float <= 200:
                            self.k2400_instrument.src_limit_AMPS(val_str)
                        else:
                            pass
                    elif what == 'Range' and config_widget == 'I':
                        self.k2400_instrument.src_range_AMPS(val_str)
                    elif what == 'Range' and config_widget == 'V':
                        self.k2400_instrument.src_range_VOLTS(val_str)
                    elif what == 'Level' and config_widget == 'I':
                        self.k2400_instrument.src_level_AMPS(val_str)
                    elif what == 'Level' and config_widget == 'V':
                        self.k2400_instrument.src_level_VOLTS(val_str)
                except:
                    print('Bad Input')

    def _check_compliance_K2612B(self):
        self.complianceA = True if self.k2612B_instrument._query('smua.source.compliance') == 'true' else False
        # print(self.complianceA)
        self.complianceB = True if self.k2612B_instrument._query('smub.source.compliance') == 'true' else False
        # print(self.complianceB)

    # def _checkCompliance_K6221(self):
    #     self.complianceA = True if self.k2612B_instrument._query('smua.source.compliance') == 'true' else False
    #     # print(self.complianceA)
    #     self.complianceB = True if self.k2612B_instrument._query('smub.source.compliance') == 'true' else False
    #     # print(self.complianceB)

    def _check_conditions_K2612B(self, frame):
        if self.filedir is None:
            tk.messagebox.showwarning('ERROR: No SAVEDIR', 'Please select a saving directory first.')
            return False
        elif self.k2612B_instrument is None:
            tk.messagebox.showwarning('ERROR: No INSTRUMENT', 'Please connect to an instrument first.')
            return False
        elif self.mid_subframes[frame].chanA_Subframe.voltmeter_bool == 0 and \
                self.mid_subframes[frame].chanB_Subframe.voltmeter_bool == 0:
            tk.messagebox.showwarning('ERROR: No Voltmeter', 'Please designate one channel to be the voltmeter first.')
            return False
        else:
            return True

    def start_measurements_sourced_on_K2612B(self, float):
        print(self.filedir)
        if float == 'Rt' or float == 'PLS':
            cond = self._check_conditions_K2612B(InstCont_K2612B)
        elif float == 'Rt_nvm' or float == 'PLS_nvm':
            cond = self._check_conditions_K2612B(InstCont_K2612BandK2182A)

        if cond:
            if float == 'Rt':
                m = R_t_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[R_t_Measurement] = m
                self._show_frame(R_t_Measurement)
            elif float == 'IV':
                m = I_V_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[I_V_Measurement] = m
                self._show_frame(I_V_Measurement)
            elif float == 'PLS':
                m = Pulse_Series_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[Pulse_Series_Measurement] = m
                self._show_frame(Pulse_Series_Measurement)
            elif float == 'Rt_nvm':
                m = R_t_Measurement_K2612Bandk2182A(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[R_t_Measurement_K2612Bandk2182A] = m
                self._show_frame(R_t_Measurement_K2612Bandk2182A)
            elif float == 'PLS_nvm':
                m = Pulse_Series_Measurement_K2612Bandk2182A(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[Pulse_Series_Measurement_K2612Bandk2182A] = m
                self._show_frame(Pulse_Series_Measurement_K2612Bandk2182A)
            else:
                raise AssertionError

    def _check_dirs(self, name):
        if self.filedir == None:
            pass
        else:
            if name not in os.listdir(self.filedir):
                os.mkdir(self.filedir + '/' + name)

    def _create_file(self, fp, suffix):
        string = str()
        for i in range(6):
            string += str(time.localtime()[i])
            string += '-'
        # self.file_obj = open(fp + '/' + string + suffix + '.csv', mode='x')
        self.file_obj = open(os.path.join(fp, f'{string + suffix}.csv'), mode='x')

    def _write_line_to_file(self, line):
        self.file_obj.write(line + '\n')
        self.file_obj.flush()
        os.fsync(self.file_obj)

    def start_measurement(self,myflt):
        if self.k2612B_instrument:
            self.start_measurements_sourced_on_K2612B(myflt)
        elif self.k2400_instrument:
            self.start_measurements_sourced_on_K2400(myflt)

    def start_measurements_sourced_on_K2612B(self, myflt):
        print(self.filedir)
        if myflt == 'Rt' or myflt == 'PLS':
            cond = self._check_conditions_K2612B(InstCont_K2612B)
        elif myflt == 'Rt_nvm' or myflt == 'PLS_nvm':
            cond = self._check_conditions_K2612B(InstCont_K2612BandK2182A)

        if cond:
            if myflt == 'Rt':
                m = R_t_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[R_t_Measurement] = m
                self._show_frame(R_t_Measurement)
            elif myflt == 'IV':
                m = I_V_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[I_V_Measurement] = m
                self._show_frame(I_V_Measurement)
            elif myflt == 'PLS':
                m = Pulse_Series_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[Pulse_Series_Measurement] = m
                self._show_frame(Pulse_Series_Measurement)
            elif myflt == 'Rt_nvm':
                m = R_t_Measurement_K2612Bandk2182A(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[R_t_Measurement_K2612Bandk2182A] = m
                self._show_frame(R_t_Measurement_K2612Bandk2182A)
            elif myflt == 'PLS_nvm':
                m = Pulse_Series_Measurement_K2612Bandk2182A(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[Pulse_Series_Measurement_K2612Bandk2182A] = m
                self._show_frame(Pulse_Series_Measurement_K2612Bandk2182A)
            else:
                raise AssertionError

    def start_measurements_sourced_on_K2400(self, myflt):
        print(self.filedir)
        if myflt == 'Rt' or myflt == 'PLS':
            cond = self._check_conditions_K2612B(InstCont_K2612B)
        elif myflt == 'Rt_nvm' or myflt == 'PLS_nvm':
            cond = self._check_conditions_K2612B(InstCont_K2612BandK2182A)

        # if cond:
        if True:
            if myflt == 'Rt':
                m = R_t_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[R_t_Measurement] = m
                self._show_frame(R_t_Measurement)
            elif myflt == 'IV':
                m = I_V_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[I_V_Measurement] = m
                self._show_frame(I_V_Measurement)
            elif myflt == 'PLS':
                m = Pulse_Series_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[Pulse_Series_Measurement] = m
                self._show_frame(Pulse_Series_Measurement)
            elif myflt == 'Rt_nvm':
                m = R_t_Measurement_K2612Bandk2182A(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[R_t_Measurement_K2612Bandk2182A] = m
                self._show_frame(R_t_Measurement_K2612Bandk2182A)
            elif myflt == 'PLS_nvm':
                m = Pulse_Series_Measurement_K2612Bandk2182A(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[Pulse_Series_Measurement_K2612Bandk2182A] = m
                self._show_frame(Pulse_Series_Measurement_K2612Bandk2182A)
            elif myflt == 'Rt_k2400':
                m = R_t_Measurement_K2400(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[R_t_Measurement_K2400] = m
                self._show_frame(R_t_Measurement_K2400)
            elif myflt == 'PLS_k2400':
                m = Pulse_Series_Measurement_K2400(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[Pulse_Series_Measurement_K2400] = m
                self._show_frame(Pulse_Series_Measurement_K2400)

            else:
                raise AssertionError

