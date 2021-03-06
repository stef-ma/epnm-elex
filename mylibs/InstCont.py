# import matplotlib as mpl
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# from matplotlib.figure import Figure
# import tkinter as tk
# from tkinter import ttk
from mylibs.BaseFrames import *
from mylibs.RmSetup import *

# mpl.use("TkAgg")

# import time

LARGE_FONT = ("Cambria", 12)
SMALL_FONT = ("Cambria", 3)


class InstCont(tk.LabelFrame):
    """The Manual Instrument Control Frame."""

    def __init__(self, parent, controller):
        # Start by initializing self as a tk.LabelFrame with the label 'Instrument Control'
        tk.LabelFrame.__init__(self, parent, bg='black', fg='white', bd=5, padx=10, pady=10, text='Instrument Control',
                               labelanchor='n')
        self.configure(background='black')
        # Set the controller as an attribute for easier handling.
        self.controller = controller
        # Output vars
        self.chanA = False
        self.chanB = False
        # Create constants compatible with rm_setup for the channels so you can create
        # two instances of all the controls later on.
        chan_a = 'a'
        chan_b = 'b'
        # Frames: OUTDATEDOUTDATEDOUTDATEDOUTDATEDOUTDATEDOUTDATEDOUTDATED
        #   |----------------InstCont---------------|OUTDATED
        #   |               top_frame               |
        #   |                   |                   |
        #   |    chanA_Subframe | chanB_Subframe    |OUTDATED
        #   |                   |                   |
        #   |                   |                   |
        #   |------------------ |-------------------|
        #   |                                       |
        #   |                                       |
        #   |                                       |OUTDATED
        #   |                                       |
        #   |------------------ |------------------ |
        #   |                bot_frame              |
        #   |                   |                   |OUTDATED
        #   | chanA_Measframe   |  chanB_Measframe  |
        #   |                   |                   |
        #   |------------------ |-------------------|OUTDATED
        # The Frames are either instances of New_Frame (Subframe) of tk.LabelFrame (Measframe).
        # Top Frames
        top_frame = NewFrame(self, controller.width, 2 * controller.pane_height)
        top_frame.pack_propagate(0)
        top_frame.pack(side='top')

        # We create extra labelframes for easier organizing. I have suffered greatly to figure this out. :c
        lframeA = tk.LabelFrame(top_frame, width=controller.width / 5, height=controller.pane_height*2, bg='black',
                                fg='white', bd=4, padx=10, pady=2, text='ChA')
        lframeA.pack_propagate(0)
        lframeA.grid(row=0, column=0,padx=10)
        # We init the subframes inside top_frame as instances of MeasurementAndOutputSubframe. See below.
        self.chanA_Measframe = MeasurementAndOutputSubframe(lframeA, controller, chan_a, self)
        self.chanA_Measframe.pack()

        # We init the subframes inside top_frame as instances of Channel_Subframe. See below.
        self.chanA_Subframe = ChannelSubframe(top_frame, chan_a, controller)
        self.chanA_Subframe.grid(row=0, column=1,padx=10)

        self.chanB_Subframe = ChannelSubframe(top_frame, chan_b, controller)
        self.chanB_Subframe.grid(row=0, column=2,padx=10)

        lframeB = tk.LabelFrame(top_frame, width=controller.width / 5, height=controller.pane_height*2, bg='black',
                                fg='white', bd=4, padx=10, pady=2, text='ChB')
        lframeB.grid(row=0, column=3,padx=10)
        lframeB.pack_propagate(0)
        self.chanB_Measframe = MeasurementAndOutputSubframe(lframeB, controller, chan_b, self)
        self.chanB_Measframe.pack()

        # Mid Frame
        mid_frame = NewFrame(self, controller.width, controller.pane_height *2)
        mid_frame.pack_propagate(0)
        mid_frame.pack(side='top')
        self.measurement_switcher = MeasurementSwitcher(mid_frame, self)
        self.measurement_switcher.pack(fill='both', pady=2)
        self.measurement_switcher.pack_propagate(0)

        # Bot Frames
        bot_frame = NewFrame(self, controller.width, controller.pane_height)
        bot_frame.pack_propagate(0)
        bot_frame.pack(side='bottom')



        # make A middle frame for quick resistance readings
        bot_mid_frame = NewFrame(bot_frame, controller.width / 3, controller.pane_height)
        bot_mid_frame.grid(row=0, column=0)
        bot_frame.grid_rowconfigure(0, weight=1)
        bot_frame.grid_columnconfigure(0, weight=1)
        bot_mid_frame.pack_propagate(0)
        multimeter_frame = tk.LabelFrame(bot_mid_frame, width=controller.width / 3, height=controller.pane_height,
                                         bg='black',
                                         fg='white', bd=4, padx=2, pady=2, text='Ohmmeter')
        multimeter_frame.pack(side='top', anchor='s', padx=2)
        # multimeter_frame.pack_propagate(0)
        self.multimeter_Measframe = MultimeterFrame(multimeter_frame, controller, self)
        self.multimeter_Measframe.pack()

        # comp_frame = NewFrame(bot_mid_frame, controller.width / 3, controller.pane_height / 2)
        # comp_frame.pack_propagate(0)
        # comp_frame.pack(side='bottom', padx=2, pady=2)


        # self.chB_complianceWarning = ComplianceIndicator(comp_frame, self)
        # self.chB_complianceWarning.pack(side='right')
        # self.chB_complianceWarning.makeOval()
        # self.chB_complianceWarning.makeText('ChB')


    def readSettings(self, chan):
        # Reads the settings for a given channel and updates the respective disabled entries in
        # chanX_Subframe via _updateControlFrame
        func = self.controller.instrument.get_SRC(chan)
        if int(float(func)) == 0:  # for I src
            limit = self.controller.instrument.get_limit_V(chan)
            rng = self.controller.instrument.get_range_I(chan)
            level = self.controller.instrument.get_level_I(chan)
        elif int(float(func)) == 1:  # for V src
            limit = self.controller.instrument.get_limit_I(chan)
            rng = self.controller.instrument.get_range_V(chan)
            level = self.controller.instrument.get_level_V(chan)
        else:  # For unexpected errors.
            limit = 255
            rng = 255
            level = 255
        self._updateControlFrame(chan, limit, rng, level, int(float(func)))

    def _updateControlFrame(self, chan, limit, rng, level, func):
        # Updates the respective disabled entries in chanX_Subframe
        if func == 0 and chan == 'a':  # I src
            comp_unit = 'V'
            rng_unit = 'A'
            lvl_unit = 'A'
            self.chanA_Subframe.updateBlock(comp_unit, rng_unit, lvl_unit, limit, rng, level)
        elif func == 1 and chan == 'a':  # V src
            comp_unit = 'A'
            rng_unit = 'V'
            lvl_unit = 'V'
            self.chanA_Subframe.updateBlock(comp_unit, rng_unit, lvl_unit, limit, rng, level)
        elif func == 0 and chan == 'b':  # I src
            comp_unit = 'V'
            rng_unit = 'A'
            lvl_unit = 'A'
            self.chanB_Subframe.updateBlock(comp_unit, rng_unit, lvl_unit, limit, rng, level)
        elif func == 1 and chan == 'b':  # V src
            comp_unit = 'A'
            rng_unit = 'V'
            lvl_unit = 'V'
            self.chanB_Subframe.updateBlock(comp_unit, rng_unit, lvl_unit, limit, rng, level)
        else:
            pass

    def instContTurnOn(self, chan):
        # Output ON in channel!
        self.controller.instrument.outp_ON(chan)
        # Subscribe the updater if this is the first channel to get switched on.
        if self.chanA is False and self.chanB is False:
            self.controller.observer.subscribe(self._updateMeasurement, 1)
        # Flip the measurement vars.
        if chan == 'a':
            self.chanA = True
        elif chan == 'b':
            self.chanB = True
        # Change to Off button!
        self._switchButton(chan, 'off')

    def instContTurnOff(self, chan):
        # Output OFF in channel!
        self.controller.instrument.outp_OFF(chan)
        # Flip the measurement variable for channel.
        if chan == 'a':
            self.chanA = False
            self.controller.complianceA = False
        elif chan == 'b':
            self.chanB = False
            self.controller.complianceA = False
        # If both are off, unsubscribe the measurement updater
        if self.chanA is False and self.chanB is False:
            self.controller.observer.unsubscribe(self._updateMeasurement)
        # Change to On button!
        self._switchButton(chan, 'on')

    def _switchButton(self, chan, command):
        # Changes the  OUTPUT button between ON and OFF mode.
        if chan == 'a':
            chan_str = 'ChA'
            subframe = self.chanA_Measframe
            subframe.switchCommand(chan, chan_str, command)
        elif chan == 'b':
            chan_str = 'ChB'
            subframe = self.chanB_Measframe
            subframe.switchCommand(chan, chan_str, command)

    def _updateMeasurement(self):
        # Updates the measurement indicators on InstCont.
        # Everything is written twice in case we are simultaneously measuring both channels.
        if self.chanA:
            # Get data
            curr, volt = self.controller.instrument.measure_channel('a')
            # print('current is '+str(curr))
            # print('voltage is '+str(volt))
            # Set subframe
            subframe = self.chanA_Measframe
            subframe.readUpdate(curr, volt)
            self.multimeter_Measframe.updateCallOut()

        if self.chanB:
            # Get data
            curr, volt = self.controller.instrument.measure_channel('b')
            # Set subframe
            subframe = self.chanB_Measframe
            subframe.readUpdate(curr, volt)
            self.multimeter_Measframe.updateCallOut()


class ChannelSubframe(NewFrame):
    """chanX_Subframe inside InstCont, contains configuration indicators and controls,
    in the form of Entries and OptionMenu objects from tk."""

    def __init__(self, parent, channel, controller):
        # Init self as NewFrame
        NewFrame.__init__(self, parent, controller.width / 2.5, controller.pane_height / 2)
        frame = tk.Frame(self)
        frame.pack(side='top')
        # Channel Logic
        if channel == 'a':
            name = 'ChanA'
        elif channel == 'b':
            name = 'ChanB'
        else:  # Should never happen.
            name = '???'
        # Set the Label for the channel.
        label = tk.Label(frame, text=name, font=LARGE_FONT, bg='black', fg='white')
        label.pack(fill='x')
        # Create DropDowns for: Sourcing
        self.sour = InstContSubsMenus(frame, 'Sourcing', 'SRC', ['V', 'I'], channel, controller)
        self.sour.pack(side='left')
        # Create DropDowns for: Measuring
        self.meas = InstContSubsMenus(frame, 'Measuring', 'MEAS', ['V', 'I'], channel, controller)
        self.meas.pack(side='left')
        # Create DropDowns for: Sensing
        self.sens = InstContSubsMenus(frame, 'Sensing', 'SENS', ['2-Point', '4-Point'], channel, controller)
        self.sens.pack(side='left')
        # Create Entries for: Compliance
        what = 'Compliance'
        self.comp = InstContSubsEntries(self, what, self.sour.info, channel, controller)
        self.comp.pack(side='top')
        # Create Entries for: Range
        what = 'Range'
        self.rang = InstContSubsEntries(self, what, self.sour.info, channel, controller)
        self.rang.pack(side='top')
        # Create Entries for: Level
        what = 'Level'
        self.lvl = InstContSubsEntries(self, what, self.sour.info, channel, controller)
        self.lvl.pack(side='top')

        self.volt_switch = tk.Button(self, text='VOLTMETER', bg='gray', fg='white',
                                     command=lambda: self._makeVoltmeter(channel, controller))
        self.volt_switch.pack(side='bottom', anchor='se')

        self.voltmeter_bool = 0

    def _makeVoltmeter(self, channel, controller):
        controller.instrument.voltmeter(channel)
        controller.instrument.meas_range_VOLTS(channel)
        self.volt_switch.configure(bg='green', command=lambda: self._makeSMU(channel, controller))
        self.comp.entry_stringvar.set('0.02')
        self.rang.entry_stringvar.set('0.000001')
        self.lvl.entry_stringvar.set('0.000000')
        self.comp.entry.config(state='disabled')
        self.rang.entry.config(state='disabled')
        self.lvl.entry.config(state='disabled')
        self.sens.ddown.config(state='disabled')
        self.sour.ddown.config(state='disabled')
        self.meas.ddown.config(state='disabled')
        self.voltmeter_bool = 1

    def _makeSMU(self, channel, controller):
        self.volt_switch.configure(bg='gray', command=lambda: self._makeVoltmeter(channel, controller))
        self.comp.entry.config(state='normal')
        self.rang.entry.config(state='normal')
        self.lvl.entry.config(state='normal')
        self.sens.ddown.config(state='normal')
        self.sour.ddown.config(state='normal')
        self.meas.ddown.config(state='normal')
        self.voltmeter_bool = 0

    def updateBlock(self, comp_unit, rng_unit, lvl_unit, limit, rng, level):
        # compliance
        self.comp.read_out_stringvar.set(limit)
        self.comp.read_out.config(state='normal')
        self.comp.read_out.delete(0, tk.END)
        self.comp.read_out.insert(0, self.comp.read_out_stringvar.get() + ' ' + comp_unit)
        self.comp.read_out.config(state='disabled')
        # range
        self.rang.read_out_stringvar.set(rng)
        self.rang.read_out.config(state='normal')
        self.rang.read_out.delete(0, tk.END)
        self.rang.read_out.insert(0, self.rang.read_out_stringvar.get() + ' ' + rng_unit)
        self.rang.read_out.config(state='disabled')
        # level
        self.lvl.read_out_stringvar.set(level)
        self.lvl.read_out.config(state='normal')
        self.lvl.read_out.delete(0, tk.END)
        self.lvl.read_out.insert(0, self.lvl.read_out_stringvar.get() + ' ' + lvl_unit)
        self.lvl.read_out.config(state='disabled')


class InstContSubsEntries(tk.LabelFrame):
    """Subframes of the Instrument Control Frame. Holds the entries for various configs."""

    def __init__(self, parent, what, config_widget, chan, controller):
        # Init as LabelFrame for more efficient labelling
        tk.LabelFrame.__init__(self, parent, bg='black', fg='white', bd=5, padx=5, pady=5, text=what)
        self.configure(background='black')
        self.controller = controller  # alias the controller
        # Create the StringVar to hold the user input and create the user input entry.
        self.entry_stringvar = tk.StringVar(self.controller)
        self.entry = tk.Entry(self, textvariable=self.entry_stringvar)
        self.entry.pack(side='left')
        self.entry_stringvar.trace_add('write',
                                       lambda a, b, c: self.controller.commandSMU(what, config_widget.get(), chan,
                                                                                  self.entry_stringvar))
        # Create the StringVar to hold the program output and create the user indicator.
        # Indicators are entries that are programmatically disabled so thay only read values.
        self.read_out_stringvar = tk.StringVar(self.controller)
        self.read_out_stringvar.set('N/A')
        self.read_out = tk.Entry(self)
        self.read_out.insert(0, self.read_out_stringvar.get())
        self.read_out.config(state='disabled')
        self.read_out.pack(side='right')


class InstContSubsMenus(tk.LabelFrame):
    """Subframes of the Instrument Control Frame. Holds the OptionMenus for various configs."""

    def __init__(self, parent, text, what, options, chan, controller):
        # Init as LabelFrame for more efficient labelling
        tk.LabelFrame.__init__(self, parent, bg='black', fg='white', bd=5, padx=5, pady=5, text=text)
        self.configure(background='black')
        self.controller = controller  # alias the controller
        # Create and populate the selectable MenuButtons that the user can use to switch
        # between various operating modes of the instrument.
        self.info = tk.StringVar(self.controller)
        self.info.set(what)
        self.ddown = tk.OptionMenu(self, self.info, *options,
                                   command=lambda x: self.controller.configSMU(what, self.info.get(), chan))
        self.ddown.pack(side='bottom')


class MeasurementAndOutputSubframe(NewFrame):

    def __init__(self, parent, controller, channel, overframe):
        # Init as NewFrame
        fac = 4
        NewFrame.__init__(self, parent, controller.width / fac, controller.pane_height*3)
        self.overframe = overframe
        # Channel Logic
        if channel == 'a':
            chan = 'ChA'
        elif channel == 'b':
            chan = 'ChB'
        else:
            chan = '???'

        # We use two frames for spatial organizing, again - top_frame and bot_frame
        # top_frame
        top_frame = NewFrame(self, controller.width / fac, controller.pane_height / 1.25)
        top_frame.pack_propagate(0)
        top_frame.pack(side='top', padx=2, pady=2)
        # Measured Voltage Indicator
        self.read_V_StringVar = tk.StringVar(controller)
        self.read_V_StringVar.set('(V)')
        self.read_V = tk.Entry(top_frame)
        self.read_V.insert(0, self.read_V_StringVar.get())
        self.read_V.config(state='disabled')
        self.read_V.pack(side='top', padx=2, pady=2)
        # Measured Current Indicator
        self.read_I_StringVar = tk.StringVar(controller)
        self.read_I_StringVar.set('(A)')
        self.read_I = tk.Entry(top_frame)
        self.read_I.insert(0, self.read_I_StringVar.get())
        self.read_I.config(state='disabled')
        self.read_I.pack(side='top', padx=2, pady=2)
        # bot_frame
        bot_frame = NewFrame(self, controller.width / fac, controller.pane_height / 0.75)
        bot_frame.pack_propagate(0)
        bot_frame.pack(side='top', padx=2, pady=2)
        # On Button
        self.outp = tk.Button(bot_frame, text=chan + ' ON', bg='orange', fg='white',
                              command=lambda: overframe.instContTurnOn(channel))
        self.outp.pack(side='left', padx=2, pady=2)
        # Get Config Button
        self.read_conf = tk.Button(bot_frame, text='GET CONF', bg='gray', fg='white',
                                   command=lambda: overframe.readSettings(channel))
        self.read_conf.pack(side='left', padx=2, pady=2)

        self.complianceWarning = ComplianceIndicator(bot_frame, self.overframe)
        self.complianceWarning.pack(side='right')
        self.complianceWarning.makeOval()
        self.complianceWarning.makeText(chan)

    def switchCommand(self, chan, chan_str, command):

        if command == 'on':
            self.outp.config(text=chan_str + ' ON', bg='orange', fg='white',
                             command=lambda: self.overframe.instContTurnOn(chan))
        elif command == 'off':
            self.outp.config(text=chan_str + ' OFF', bg='BLUE', fg='white',
                             command=lambda: self.overframe.instContTurnOff(chan))

    def readUpdate(self, curr, volt):
        # Current
        self.read_I_StringVar.set(curr + ' (A)')
        self.read_I.config(state='normal')
        self.read_I.delete(0, tk.END)
        self.read_I.insert(0, self.read_I_StringVar.get())
        self.read_I.config(state='disabled')

        # Voltage
        self.read_V_StringVar.set(volt + ' (V)')
        self.read_V.config(state='normal')
        self.read_V.delete(0, tk.END)
        self.read_V.insert(0, self.read_V_StringVar.get())
        self.read_V.config(state='disabled')


class MultimeterFrame(NewFrame):

    def __init__(self, parent, controller, overframe):
        fac = 3.5
        NewFrame.__init__(self, parent, controller.width / fac, controller.pane_height)
        # Measured Resistance Indicator
        self.overframe = overframe
        self.controller = controller
        self.read_R_StringVar = tk.StringVar(controller)
        self.read_R_StringVar.set('N/A')
        self.read_R = tk.Entry(self)
        self.read_R.insert(0, self.read_R_StringVar.get())
        self.read_R.config(state='disabled')
        self.read_R.pack(side='top', padx=2, pady=2)

    def updateCallOut(self):
        if self.overframe.chanA and self.overframe.chanB:
            if self.overframe.chanA_Subframe.voltmeter_bool == 1 and \
                    self.overframe.chanB_Subframe.voltmeter_bool == 0:

                source = self.overframe.chanB_Measframe.read_I_StringVar
                voltmeter = self.overframe.chanA_Measframe.read_V_StringVar

                if source.get() != '(A)' and voltmeter.get() != '(V)':
                    current = float(split('[ ]', source.get())[0])
                    voltage = float(split('[ ]', voltmeter.get())[0])
                    resistance = round(voltage / current, 4)
                    self._updateMultimeter(resistance)
                else:
                    pass

            elif self.overframe.chanA_Subframe.voltmeter_bool == 0 and \
                    self.overframe.chanB_Subframe.voltmeter_bool == 1:

                source = self.overframe.chanA_Measframe.read_I_StringVar
                voltmeter = self.overframe.chanB_Measframe.read_V_StringVar

                if source.get() != '(A)' and voltmeter.get() != '(V)':
                    current = float(split('[ ]', source.get())[0])
                    voltage = float(split('[ ]', voltmeter.get())[0])
                    resistance = round(voltage / current, 4)
                    self._updateMultimeter(resistance)
                else:
                    pass
            else:
                pass

    def _updateMultimeter(self, resistance):
        self.read_R_StringVar.set(str(resistance) + ' Ohm')
        self.read_R.config(state='normal')
        self.read_R.delete(0, tk.END)
        self.read_R.insert(0, self.read_R_StringVar.get())
        self.read_R.config(state='disabled')


class MeasurementSwitcher(tk.LabelFrame):

    def __init__(self, parent, overframe):
        tk.LabelFrame.__init__(self, parent, width=overframe.controller.width * .9,
                               height=overframe.controller.pane_height * 2, bg='black', fg='white', bd=5, padx=5,
                               pady=5, text='Measurements', labelanchor='n')
        self.controller = overframe.controller

        frame1 = NewFrame(self, overframe.controller.width * .3, overframe.controller.pane_height * 2)
        frame1.pack_propagate(0)
        frame1.pack(side='left')
        # button
        self.measure_button_Rt = tk.Button(frame1, text='R(t)', bg='gray', fg='white',
                                           command=lambda: self.controller.startMeasurement('Rt'))
        #
        self.measure_button_Rt.pack(pady=0)
        self.probe_current = MeasurementSwitcherSubsEntries(frame1, self.controller, 'Probe  (A or V): ')
        self.probe_current.pack(pady=2)
        self.probe_duration = MeasurementSwitcherSubsEntries(frame1, self.controller, '    Duration (s): ')
        self.probe_duration.pack(pady=2)
        self.datastep = MeasurementSwitcherSubsEntries(frame1, self.controller, '    Datastep (s) : ')
        self.datastep.pack(pady=2)

        frame2 = NewFrame(self, overframe.controller.width * .3, overframe.controller.pane_height * 2)
        frame2.pack_propagate(0)
        frame2.pack(side='left', padx=20)
        # button
        self.measure_button_IV = tk.Button(frame2, text='I(V)', bg='gray', fg='white', state='disabled',
                                           command=lambda: self.controller.startMeasurement('IV'))
        #
        self.measure_button_IV.pack(pady=0)
        self.IV_start = MeasurementSwitcherSubsEntries(frame2, self.controller, ' Start (A): ')
        self.IV_start.pack(pady=1)
        self.IV_stop = MeasurementSwitcherSubsEntries(frame2, self.controller, '  Stop (A): ')
        self.IV_stop.pack(pady=1)
        self.IV_step = MeasurementSwitcherSubsEntries(frame2, self.controller, '  Step (A): ')
        self.IV_step.pack(pady=1)
        self.IV_cycles = MeasurementSwitcherSubsEntries(frame2, self.controller, '    Cycles: ')
        self.IV_cycles.pack(pady=1)

        frame3 = NewFrame(self, overframe.controller.width * .3, overframe.controller.pane_height * 2)
        frame3.pack_propagate(0)
        frame3.pack(side='right')
        # button
        self.measure_button_PulseRt = tk.Button(frame3, text='Pulse Sequence', bg='gray', fg='white',
                                                command=lambda: self.controller.startMeasurement('PLS'))
        #
        self.measure_button_PulseRt.pack(pady=0)
        self.pulsing_start = MeasurementSwitcherSubsEntries(frame3, self.controller, 'Pulsing start (A or V): ')
        self.pulsing_start.pack(pady=1)
        self.pulsing_stop = MeasurementSwitcherSubsEntries(frame3, self.controller, ' Pulsing stop (A or V): ')
        self.pulsing_stop.pack(pady=1)
        self.pulsing_step = MeasurementSwitcherSubsEntries(frame3, self.controller, ' Pulsing step (A or V): ')
        self.pulsing_step.pack(pady=1)
        self.pulsing_duration = MeasurementSwitcherSubsEntries(frame3, self.controller, '      Pulsing Duration (s): ')
        self.pulsing_duration.pack(pady=1)


class MeasurementSwitcherSubsEntries(NewFrame):
    """Subframes of the Instrument Control Frame. Holds the entries for various configs."""

    def __init__(self, parent, controller, labeltext, func=None):
        # Init as NewFrame
        NewFrame.__init__(self, parent, controller.width * .3, controller.pane_height * .33)
        self.controller = controller
        # Create the Label to indicate what we are collecting.
        label = tk.Label(self, bg='black', fg='white', text=labeltext)
        label.pack(side='left')
        # Create the StringVar to hold the user input and create the user input entry.
        self.entry_stringvar = tk.StringVar(controller)
        self.entry = tk.Entry(self, textvariable=self.entry_stringvar)
        self.entry.pack(side='right')
        if func is not None:
            self.entry_stringvar.trace_add('write', func)


class ComplianceIndicator(tk.Canvas):
    def __init__(self, parent, overframe):
        # Create a bool indicator for instrument compliance.
        tk.Canvas.__init__(self, parent, width=overframe.controller.pane_height / 3,
                           height=overframe.controller.pane_height / 3,
                           bg='black', bd=0, highlightthickness=0)
        # self.pack(side='right')
        self.overframe = overframe
        self.bool_indicator = None
        self.textlabel = None

    def makeOval(self):
        self.bool_indicator = self.create_oval(
            int(1 / 3 * 1 / 2 * self.overframe.controller.pane_height),
            int(1 / 3 * 1 / 2 * self.overframe.controller.pane_height),
            int(2 / 3 * 1 / 2 * self.overframe.controller.pane_height),
            int(2 / 3 * 1 / 2 * self.overframe.controller.pane_height), fill="gray")

    def makeText(self, text):
        self.textlabel = self.create_text(
            int(1 / 3 * 1 / 2 * self.overframe.controller.pane_height) + 2,
            int(1 / 3 * 1 / 2 * self.overframe.controller.pane_height) - 10, text='Comp', fill='white',
            font=SMALL_FONT)
