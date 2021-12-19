import os
# import tkinter as tk
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

        # Attributes
        self.instrument = None  # pyvisa resourcemanager instrument controller
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

        #    ---------------------------------------
        #   |                                       |
        #   |              Frame1                   |
        #   |                                       |
        #   |---------------------------------------|
        #   |                                       |
        #   |                                       |
        #   |                                       |
        #   |                                       |
        #   |                                       |
        #   |                                       |
        #   |              Frame2                   |
        #   |                                       |
        #   |                                       |
        #   |                                       |
        #   |                                       |
        #   |                                       |
        #   |                                       |
        #   |                                       |
        #   |                                       |
        #   |---------------------------------------|
        #   |                                       |
        #   |              Frame3                   |
        #   |                                       |
        #    ---------------------------------------

        # Frame 1
        # Will have top banner as well as start and stop buttons
        self.top_frame = NewFrame(self, self.width, self.pane_height * 1.2)  # Inherits tk.Frame, see gui_frames
        self.top_frame.pack_propagate(0)
        self.top_frame.pack(side='top', fill='x')
        self._decorateTopFrame(self.top_frame)  # Decorating method, draws logo, title label
        # and creates the start and stop buttons, see methods below

        # Frame 2
        # Will have several pages to hold the different measurement setups
        self.mid_frame = NewFrame(self, self.width, 4 * self.pane_height)
        self.mid_frame.pack_propagate(0)  # Is 4x taller than other frames,
        # to hold most controls and indicators
        self.mid_frame.pack(side='top', fill='x')
        container = self.mid_frame  # got this logic from stackoverflow,
        # essentially all frames that are shown in the middle get created below
        # and are later only raised to top on demand with _showFrame
        container.pack(side="top", fill="both")
        container.grid_rowconfigure(0, weight=1)  # It is necessary to give weight to the grid cells for this to work.
        container.grid_columnconfigure(0, weight=1)
        self.mid_subframes = {}
        for F in (Blank, InstCont  # , R_t_Measurement, I_V_Measurement,
                # , Pulse_Series_Measurement
                  ):  # Classes are defined in gui_frames
            # print(F)
            frame = F(container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.mid_subframes[F] = frame
        self._showFrame(Blank)
        # self._showFrame(Pulse_Series_Measurement)

        # Frame 3
        # Will have a savefile, execution time and instrument connection indicator
        self.bot_frame = NewFrame(self, self.width, self.pane_height)
        self.bot_frame.pack_propagate(0)
        self.bot_frame.pack(side='top', fill='x')
        self._decorateBotFrame(self.bot_frame)

        # Updating method for time fOand instrument indicator for the first time
        self.observer.subscribe(self._time, 2)
        self.observer.subscribe(self._updateBottom, 0)

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
            # see observer
            self.time3 = self.runtime
            self.observer.call_subscribers(0)
            # print(self.observer.dict)
        elif self.runtime - self.time2 > .025:  # self.observer.call_subscribers(1) is executed a dozen times per
            # second. 
            # see observer
            self.time2 = self.runtime
            self.observer.call_subscribers(1)
        self.observer.call_subscribers(2)  # self.observer.call_subscribers(2) is executed every loop.
        # self.observer.call_subscribers(2)  is therefore the greatest risk
        self.after(1, self._update)

    #
    #

    def _safeExit(self):
        # safe exit method with shutdown for the SMU!
        if self.instrument is None:
            if self.file_obj is not None: self.file_obj.close()
            self.destroy()
        else:
            self._closeInstrument()  # see rm_setup
            if self.file_obj is not None: self.file_obj.close()
            self.destroy()

    def _startUp(self):
        # Start Button method. Creates the InstSelect frame whose invocation calls inst_seek() from rm_setup.
        # In order for instruments to show up user must have access to the usb drives of the PC - on linux,
        # main must be run as superuser. Didn't test on windows yet.
        frame = InstSelect(self.mid_frame, self)
        frame.grid(row=0, column=0, sticky="nsew")
        self.mid_subframes[InstSelect] = frame
        self._showFrame(InstSelect)
        self.start_button.destroy()
        self._editButton(self.top_frame, 'se')

    def _editInstrument(self):
        # Edit Button method. Closes the instrument via _closeInstrument, destroys the InstSelect frame in Frame 2,
        # and then recreates it to allow renewed connection to the instrument.
        self._closeInstrument()
        self.mid_subframes[InstSelect].destroy()
        frame = InstSelect(self.mid_frame, self)
        frame.grid(row=0, column=0, sticky="nsew")
        self.mid_subframes[InstSelect] = frame
        self._showFrame(InstSelect)

    def _showFrame(self, cont):
        # Raises the given subframe of Frame 2 (See diagram above)
        frame = self.mid_subframes[cont]
        frame.tkraise()

    def _decorateTopFrame(self, banner):
        # Load Logo
        fact = 5
        self.img = Image.open("data/logo3.png")  # Use the pillow library to load the image.
        # I should think about maybe replacing this with matplotlib.image
        self.img = self.img.resize((int(self.img.size[0] / fact), int(self.img.size[1] / fact)),
                                   Image.ANTIALIAS)  # The (int(), int()) is (height, width)
        self.img = ImageTk.PhotoImage(self.img)
        self.logo = tk.Label(banner, bg='black', image=self.img)  # We pack the image as a tk.Label. 
        # Don't judge me I got this from stackoverflow!
        self.logo.pack(side='left', padx=10)

        # Write Title
        self.title = tk.Label(banner, bg='black', fg='white', text='EPNM Electrical Testbench: Pulse EM')
        self.title.pack(side='left', padx=10)

        # Create Buttons
        self._stopButton(self.top_frame, 'ne')
        self._startButton(self.top_frame, 'se')

    def _decorateBotFrame(self, banner):
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
        self._saveAsButton(bot1)

        # Create tk.Label for time indicator
        self.bottom_time_label = tk.Label(bot2, bg='black', fg='white', text='Execution time:' + self.exec_time.get())
        self.bottom_time_label.pack(side='top')

        # Create a bool indicator for instrument connection.
        self.instrument_bool_indicator_canvas = tk.Canvas(bot2, width=self.pane_height / 2, height=self.pane_height / 2,
                                                          bg='black', bd=0, highlightthickness=0)
        self.instrument_bool_indicator_canvas.pack(side='top')
        self.instrument_bool_indicator_canvas.bool_indicator = self.instrument_bool_indicator_canvas.create_oval(
            int(1 / 3 * 1 / 2 * self.pane_height), int(1 / 3 * 1 / 2 * self.pane_height),
            int(2 / 3 * 1 / 2 * self.pane_height), int(2 / 3 * 1 / 2 * self.pane_height), fill="gray")

        # Create a tk.Label for instrument connection.
        self.instrument_bool_indicator_label = tk.Label(bot2, bg='black', fg='white', text='Instrument connected?')
        self.instrument_bool_indicator_label.pack(side='top')

    def _updateBottom(self):
        # Updates the indicators created in _decorateBotFrame and the Compliance indicator.
        # Needs the .runtime attribute to be updated for it to makes sense. 
        # _updateBottom is subscribed to the observer in the slowest lane as it is only interesting to the user.

        # Set the exec_time tk.StringVar to the current value of runtime.
        self.exec_time.set(str(int(self.runtime)))
        self.bottom_time_label['text'] = 'Execution time:   ' + self.exec_time.get() + ' s'

        # Set the instrument bool indicator color.
        if self.instrument is None:
            self.instrument_bool_indicator_canvas.itemconfig(self.instrument_bool_indicator_canvas.bool_indicator,
                                                             fill="gray")
        else:
            self.instrument_bool_indicator_canvas.itemconfig(self.instrument_bool_indicator_canvas.bool_indicator,
                                                             fill="green")

            fill = 'blue' if self.complianceA else 'gray'
            frame = self.mid_subframes[InstCont]
            frame.chanA_Measframe.complianceWarning.itemconfig(frame.chanA_Measframe.complianceWarning.bool_indicator,
                                                               fill=fill)
            fill = 'blue' if self.complianceB else 'gray'
            frame = self.mid_subframes[InstCont]
            frame.chanB_Measframe.complianceWarning.itemconfig(frame.chanB_Measframe.complianceWarning.bool_indicator,
                                                               fill=fill)
            if any([self.complianceA, self.complianceB]):
                self.instrument.beeper(0.2)
        # Set the filepath display.        
        if self.filedir is None:
            self.save_file_path_label['text'] = 'file: N\A'
        else:
            self.save_file_path_label['text'] = 'file: ' + self.filedir

    def _stopButton(self, banner, pos):
        # Creates the emergency Stop Button which can safely exit the app via _safeExit.
        self.halt = tk.Button(banner, bg='red', text='STOP', fg='white', command=self._safeExit)
        self.halt.pack(anchor=pos, pady=5, padx=5)

    def _startButton(self, banner, pos):
        # Start button; makes you pick an instrument via __Start_up__.
        self.start_button = tk.Button(banner, bg='green', text='START', fg='white', command=self._startUp)
        self.start_button.pack(anchor=pos, pady=5, padx=5)

    def _editButton(self, banner, pos):
        # Creates the _editButton in the position of the old start button. Calls _editInstrument instead of
        # _startUp as you need to close old connections to look for new ones. See methods.
        self.start_button = tk.Button(banner, text='EDIT', command=self._editInstrument)
        self.start_button.pack(anchor=pos, pady=5, padx=5)

    def _saveAsButton(self, banner):
        # Creates the Save As button in Frame 3. Calls _createSaveFile.
        self.save_button = tk.Button(banner, text='SAVEDIR', command=self._createSaveFile)
        self.save_button.pack(pady=5, padx=5)

    def _createSaveFile(self):
        # Calls the tk.filedialog method for creating a savefile and stores the result in self.file.
        # Can later be used to access the file via pythons builtins, while offering the convenience of a prebuilt
        # filedialog.
        # files = [('All Files', '*.*'), ('Text Document', '*.txt')]
        self.filedir = tk.filedialog.askdirectory(
            # filetypes=files, defaultextension=files
        )

    def _setInstrument(self, lbox, inlist):
        # Creates an instance of the Inst_Class class from rm_setup as self.instrument.
        # This attribute will give us access to the instrument methods defined in rm_setup.
        self.instrument = InstClass_K2612B(inlist[lbox.curselection()[0]])
        self.observer.subscribe(self._checkCompliance, 0)

    def _closeInstrument(self):
        # Closes the instrument connection, if it exists.
        if self.instrument is None:
            pass
        else:
            self.instrument._close()
            self.instrument = None

    def configSMU(self, what, value, chan):
        # Config instrument method called by various tk.OptionMenus in the InstCont frame of Frame 2. See Schematic.
        if self.instrument is None:
            pass
        else:
            if what == 'SRC' and value == 'I':
                self.instrument.src_I(chan)
            elif what == 'SRC' and value == 'V':
                self.instrument.src_V(chan)
            elif what == 'MEAS' and value == 'I':
                self.instrument.meas_I(chan)
            elif what == 'MEAS' and value == 'V':
                self.instrument.meas_V(chan)
            elif what == 'SENS' and value == '2-Point':
                self.instrument.sense_local(chan)
            elif what == 'SENS' and value == '4-Point':
                self.instrument.sense_remote(chan)

    def commandSMU(self, what, config_widget, chan, val):
        # Command instrument method called by various tk.Entrys in the InstCont frame of Frame 2. See Schematic.
        # val is passed as the entry tk.StringVar, values are retrieved by .get()
        if self.instrument is None:
            pass
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
                            self.instrument.src_limit_VOLTS(chan, val_str)
                        elif config_widget == 'V' and 0.000_000_01 <= val_float <= 200:
                            self.instrument.src_limit_AMPS(chan, val_str)
                        else:
                            pass
                    elif what == 'Range' and config_widget == 'I':
                        self.instrument.src_range_AMPS(chan, val_str)
                    elif what == 'Range' and config_widget == 'V':
                        self.instrument.src_range_VOLTS(chan, val_str)
                    elif what == 'Level' and config_widget == 'I':
                        self.instrument.src_level_AMPS(chan, val_str)
                    elif what == 'Level' and config_widget == 'V':
                        self.instrument.src_level_VOLTS(chan, val_str)
                except:
                    print('Bad Input')

    def _checkCompliance(self):
        self.complianceA = True if self.instrument._query('smua.source.compliance') == 'true' else False
        # print(self.complianceA)
        self.complianceB = True if self.instrument._query('smub.source.compliance') == 'true' else False
        # print(self.complianceB)

    def startMeasurement(self, float):
        print(self.filedir)
        if self.filedir is None:
            tk.messagebox.showwarning('ERROR: No SAVEDIR', 'Please select a saving directory first.')
        elif self.instrument is None:
            tk.messagebox.showwarning('ERROR: No INSTRUMENT', 'Please connect to an instrument first.')
        elif self.mid_subframes[InstCont].chanA_Subframe.voltmeter_bool == 0 and \
                self.mid_subframes[InstCont].chanB_Subframe.voltmeter_bool == 0:
            tk.messagebox.showwarning('ERROR: No Voltmeter', 'Please designate one channel to be the voltmeter first.')
        else:
            if float == 'Rt':
                m = R_t_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[R_t_Measurement] = m
                self._showFrame(R_t_Measurement)
            elif float == 'IV':
                m = I_V_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[I_V_Measurement] = m
                self._showFrame(I_V_Measurement)
            elif float == 'PLS':
                m = Pulse_Series_Measurement(self.mid_frame, self)
                m.grid(row=0, column=0, sticky="nsew")
                self.mid_subframes[Pulse_Series_Measurement] = m
                self._showFrame(Pulse_Series_Measurement)
            else:
                raise AssertionError

    def _checkDirs(self, name):
        if self.filedir == None:
            pass
        else:
            if name not in os.listdir(self.filedir):
                os.mkdir(self.filedir + '/' + name)

    def _createFile(self, fp, suffix):
        string = str()
        for i in range(6):
            string += str(time.localtime()[i])
            string += '-'
        # self.file_obj = open(fp + '/' + string + suffix + '.csv', mode='x')
        self.file_obj = open(os.path.join(fp, f'{string+suffix}.csv'), mode='x')

    def _writeLineToFile(self, line):
        self.file_obj.write(line + '\n')
        self.file_obj.flush()
        os.fsync(self.file_obj)
