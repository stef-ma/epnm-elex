import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # , NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib as mpl

# import tkinter as tk
# from tkinter import ttk
# from rm_setup import *
from mylibs.InstCont import *

mpl.rcParams.update({
    # "text.usetex": True,
    "font.family": "serif",
    # "font.serif": ["Cambria"]
})
skatargs1 = {
    'marker': 'v',
    's': 100,
    'linewidth': 1,
    'facecolor': 'lightblue',
    'edgecolor': 'white'
}
skatargs2 = {
    'marker': '^',
    's': 100,
    'linewidth': 1,
    'facecolor': 'red',
    'edgecolor': 'white'
}
mpl.use("TkAgg")

# import time

LARGE_FONT = ("Cambria", 12)


class Measurement(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, width=controller.width, height=controller.pane_height * 4)
        self.configure(bg='black')
        self.pack()

        self.controller = controller
        self.path = str()
        self.suffix = str()
        self.header = []
        self.dirname = str()
        self.exp_time = float()
        self.start_time = float()
        self.running_time = float()
        self.iter = 0
        self.params = {}
        self.measurement = {}
        self.dpoint = 0
        self.goalres = None
        self.inst_cont = InstCont_K2612B

        top_frame = tk.Frame(self, bg='black', width=int(controller.width * .95), height=.75 * controller.pane_height)
        top_frame.pack_propagate(0)
        top_frame.pack(side='top')
        self.label = tk.Label(top_frame, text=" ", font=LARGE_FONT, bg='black', fg='white')
        self.label.pack(side='left', pady=2, padx=10)
        RetInstCont = tk.Button(top_frame, bg='gray', fg='white', text="Return to Instrument Control",
                                command=lambda: self._return_to_inst_cont())
        RetInstCont.pack(side='left', pady=2, padx=10)
        self.label2 = tk.Label(top_frame, text=" ", font=LARGE_FONT, bg='black', fg='white')
        self.label2.pack(side='left', pady=2, padx=10)
        self.label3 = tk.Label(top_frame, text=" END: ", font=LARGE_FONT, bg='black', fg='white')
        self.label3.pack(side='left', pady=2, padx=10)
        self.End_StringVar = tk.StringVar(self.controller)
        self.End_StringVar.trace_add('write', lambda x, y, z: self._set_goal())
        End = tk.Entry(top_frame, textvariable=self.End_StringVar)
        End.pack(side='left', pady=2, padx=10)
        StartMeasurement = tk.Button(top_frame, bg='orange', fg='white', text="Measure",
                                     command=lambda: self._new_measurement())
        StartMeasurement.pack(side='right', pady=2, padx=10)
        StopMeasurement = tk.Button(top_frame, bg='red', fg='white', text="Halt Measurement",
                                    command=lambda: self._stop_measurement())
        StopMeasurement.pack(side='right', pady=2, padx=10)

        self.fig = Figure(figsize=(5, 5), dpi=100, facecolor='black', tight_layout=True)

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # toolbar = NavigationToolbar2Tk(canvas, self)
        # toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _return_to_inst_cont(self):
        self._stop_measurement()
        self.controller._show_frame(self.inst_cont)

    def _new_measurement(self):
        self._find_voltmeter()
        self._get_params()
        self._datastructure()
        self._check_param_validity()
        self.controller._check_dirs(self.dirname)
        fp = self.controller.filedir + '/' + self.dirname
        self.controller._create_file(fp, self.suffix)
        self._send_line(self.header)
        self.controller.observer.subscribe(self._measure, 2)
        self.controller.observer.subscribe(self._check_goal, 2)
        self.controller.observer.subscribe(self._update_plot, 0)

    def _stop_measurement(self):
        # print(self.measurement)

        lastdata = []
        if self.dpoint != 0:
            for key in self.header:
                try:
                    lastdata.append(self.measurement[key][self.dpoint])
                except:
                    lastdata.append(' ')

        try:
            self._send_line(lastdata)
        except:
            pass

        try:
            self.controller.file_obj.close()
        except:
            pass

        self.controller.observer.unsubscribe(self._measure)
        self._update_plot()
        self.controller.observer.unsubscribe(self._update_plot)

        self._inst_cont_turn_off()

        self.dpoint = 0

    def _datastructure(self):
        shp = self._get_number_of_datapoints()
        for key in self.header:
            self.measurement[key] = np.zeros(shp, dtype=np.float64)
        print(self.measurement)
        print('Shape is', shp)

    def _set_datadict_vals(self, iterable, index):
        for key, measure in zip(self.header, iterable):
            self.measurement[key][index] = float(measure)

    def _find_voltmeter(self):
        if self.controller.mid_subframes[self.inst_cont].chanA_Subframe.voltmeter_bool == 0:
            self.voltmeter = self.controller.mid_subframes[self.inst_cont].chanB_Subframe
            self.smu = self.controller.mid_subframes[self.inst_cont].chanA_Subframe
            self.smu_src = self.smu.sour.info.get()
            self.smu_chan = 'a'
            self.vm_chan = 'b'
            print(self.smu_src)
        else:
            self.voltmeter = self.controller.mid_subframes[self.inst_cont].chanA_Subframe
            self.smu = self.controller.mid_subframes[self.inst_cont].chanB_Subframe
            self.smu_src = self.smu.sour.info.get()
            self.smu_chan = 'b'
            self.vm_chan = 'a'
            print(self.smu_src)

    def _check_param_validity(self):
        for value in self.params.values():
            try:
                float(value)
                print(value)
            except:
                tk.messagebox.showwarning('ERROR: BAD PARAMS',
                                          'Please check the input parameters on the previous screen.')
                break
        print('self.smu_src is', self.smu_src)
        if self.smu_src not in ['I', 'V']:
            tk.messagebox.showwarning('ERROR: BAD PARAMS', 'Please check the input parameters on the previous screen.')

    def _inst_cont_turn_on(self):
        self.controller.k2612B_instrument.outp_ON('a')
        self.controller.k2612B_instrument.outp_ON('b')
        # print('unsubscribing measurement')

    def _inst_cont_turn_off(self):
        self.controller.k2612B_instrument.outp_OFF('a')
        self.controller.k2612B_instrument.outp_OFF('b')
        # self.controller.k2612B_instrument.beeper(0.1)
        # self.controller.k2612B_instrument.beeper(0.1)
        # print('unsubscribing measurement')

    def _send_line(self, iterable):
        line = str()
        for value in iterable:
            if type(value) is str:
                line += value + ', '
            else:
                value = str(round(value, 9))
                line += value + ', '
        self.controller._write_line_to_file(line)

    def _set_sourcing(self, level):
        inst = self.controller.k2612B_instrument
        if self.smu_src == 'I':
            # inst.beeper(0.1)
            # inst.beeper(0.1)
            # inst.beeper(0.1)
            # inst.src_I(self.smu_chan)
            inst.src_level_AMPS(self.smu_chan, level)
        elif self.smu_src == 'V':
            # inst.beeper(0.1)
            # inst.beeper(0.1)
            # inst.beeper(0.1)
            # inst.src_I(self.smu_chan)
            inst.src_level_VOLTS(self.smu_chan, level)

    def _get_from_inst(self):
        smu_curr, smu_volt = self.controller.k2612B_instrument.measure_channel(self.smu_chan)
        _, vm_volt = self.controller.k2612B_instrument.measure_channel(self.vm_chan)
        return smu_curr, smu_volt, vm_volt

    def _measure(self):
        pass

    def _get_number_of_datapoints(self):
        pass

    def _get_params(self):
        pass

    def _update_plot(self):
        pass

    def _set_goal(self):
        pass

    def _check_goal(self):
        pass


class I_V_Measurement(Measurement):
    def __init__(self, parent, controller):
        Measurement.__init__(self, parent, controller)
        # added 20220520
        self.inst_cont = InstCont_K2612B

        self.label.configure(text='Current - Voltage')
        self.suffix = 'Curr-Volt'
        self.dirname = 'IV'
        self.header = ['TIME_seconds', 'SRC_V_volts', 'SRC_I_amps', 'VOLTMETER_volts']

        self.ax = self.fig.add_subplot(111)
        decorate_ax(self.ax)

    def _get_params(self):
        inscont = self.controller.mid_subframes[self.inst_cont].measurement_switcher
        self.params = {
            'START': inscont.IV_start.entry_stringvar.get(),
            'STOP': inscont.IV_stop.entry_stringvar.get(),
            'STEP': inscont.IV_step.entry_stringvar.get(),
            'CYCLES': inscont.IV_cycles.entry_stringvar.get()
        }

    def _get_number_of_datapoints(self):
        sta = float(self.params['START'])
        stp = float(self.params['STOP'])
        sep = float(self.params['STEP'])
        cyc = float(self.params['CYCLES'])
        return int(abs(((stp - sta) / sep) * cyc))


class R_t_Measurement(Measurement):
    def __init__(self, parent, controller):
        Measurement.__init__(self, parent, controller)
        # added 20220520
        self.inst_cont = InstCont_K2612B

        self.label.configure(text='Resistance - Time')
        self.suffix = 'Res-Time'
        self.dirname = 'Rt'
        self.header = ['TIME_seconds', 'SRC_V_volts', 'SRC_I_amps', 'VOLTMETER_volts', 'RESISTANCE_Ohms']

        self.ax = self.fig.add_subplot(111)
        decorate_ax(self.ax)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Resistance (Ohm)')

        self.scat = self.ax.scatter([], [], **skatargs1)

    def _update_plot(self):
        if self.dpoint >= 1:
            time = self.measurement['TIME_seconds'][1:self.dpoint]
            res = self.measurement['RESISTANCE_Ohms'][1:self.dpoint]
            # offsets=list(np.stack((time,res),axis=1))
            # print(offsets)
            self.ax.clear()
            self.scat = self.ax.scatter(time, res, **skatargs1)
            decorate_ax(self.ax)
            # self.ax.relim()
            # self.ax.autoscale_view()
            self.canvas.draw()
            self.canvas.flush_events()

    def _get_params(self):
        inscont = self.controller.mid_subframes[InstCont_K2612B].measurement_switcher
        self.params = {
            'PROBE': inscont.probe_current.entry_stringvar.get(),
            'DURATION': inscont.probe_duration.entry_stringvar.get(),
            'DATASTEP': inscont.datastep.entry_stringvar.get(),
        }

    def _get_number_of_datapoints(self):
        dur = float(self.params['DURATION'])
        stp = float(self.params['DATASTEP'])
        return int(dur / stp)

    def _measure(self):
        inst = self.controller.k2612B_instrument
        if self.iter == 0:
            if self.smu_src == 'I':
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.src_I(self.smu_chan)
                inst.src_level_AMPS(self.smu_chan, self.params['PROBE'])
            elif self.smu_src == 'V':
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.src_I(self.smu_chan)
                inst.src_level_VOLTS(self.smu_chan, self.params['PROBE'])
            self.iter += 1
            self.exp_time = self.controller.runtime
            self.start_time = self.controller.runtime
            self.running_time = self.controller.runtime
            self._inst_cont_turn_on()
            smu_curr, smu_volt = self.controller.k2612B_instrument.measure_channel(self.smu_chan)
            _, vm_volt = self.controller.k2612B_instrument.measure_channel(self.vm_chan)
            time = str(round(self.exp_time, 6))
            res = round(float(vm_volt) / float(smu_curr), 4)
            self._send_line([time, smu_volt, smu_curr, vm_volt, str(res)])
            self._set_datadict_vals([time, smu_volt, smu_curr, vm_volt], self.dpoint)
            self.dpoint += 1
        else:
            if (self.exp_time - self.start_time) >= float(self.params['DURATION']):
                self._stop_measurement()
            elif (self.exp_time - self.running_time) >= float(self.params['DATASTEP']):
                self.exp_time = self.controller.runtime
                self.running_time = self.controller.runtime
                smu_curr, smu_volt = self.controller.k2612B_instrument.measure_channel(self.smu_chan)
                _, vm_volt = self.controller.k2612B_instrument.measure_channel(self.vm_chan)
                time = str(round(self.exp_time, 6))
                res = str(round(float(vm_volt) / float(smu_curr), 4))
                self._send_line([time, smu_volt, smu_curr, vm_volt, res])
                self._set_datadict_vals([time, smu_volt, smu_curr, vm_volt, res], self.dpoint)
                self.dpoint += 1
            else:
                self.exp_time = self.controller.runtime


class Pulse_Series_Measurement(Measurement):
    def __init__(self, parent, controller):
        Measurement.__init__(self, parent, controller)
        self.resmeas_bool = False
        self.resmeas_bool_polarity_switch = False
        self.lastres = None
        # added 20220520
        self.inst_cont = InstCont_K2612B

        self.label.configure(text='Pulse Series')
        self.suffix = 'PLS'
        self.dirname = 'PLS'
        self.header = ['PLS_number', 'PLS_V_volts', 'PLS_I_amps', 'RMAX_Ohms', 'VOLTMETER_volts', 'RMIN_Ohms']

        self.ax1 = self.fig.add_subplot(211)
        self.ax1_twin = self.ax1.twinx()
        self.ax2 = self.fig.add_subplot(212)
        self.ax2_twin = self.ax2.twinx()
        for ax in [self.ax1, self.ax2, self.ax1_twin, self.ax2_twin]:
            decorate_ax(ax)

        self.ax1.sharex(self.ax2)
        self.ax2.set_xlabel('PLS Number')
        self.ax1.set_ylabel('Pulse Current (A)')
        self.ax1_twin.set_ylabel('Pulse Voltage (V)')
        self.ax2.set_ylabel('Resistance_min (Ohm)')
        self.ax2_twin.set_ylabel('Resistance_max (Ohm)')

        self.scat1 = self.ax1.scatter([], [], **skatargs1)
        self.scat1_twin = self.ax1_twin.scatter([], [], **skatargs2)
        self.scat2 = self.ax2.scatter([], [], **skatargs1)
        self.scat2_twin = self.ax2_twin.scatter([], [], **skatargs2)

        self.measurement_accumulator = []
        self.measurement_accumulator1 = []
        self.measurement_accumulator2 = []
        self.measurement_accumulator3 = []

        self.plsvals = []

    def _update_plot(self):
        if self.dpoint >= 1:
            plsno = self.measurement['PLS_number'][1:self.dpoint]
            plsvolt = self.measurement['PLS_V_volts'][1:self.dpoint]
            plsamp = self.measurement['PLS_I_amps'][1:self.dpoint]
            res_max = self.measurement['RMAX_Ohms'][1:self.dpoint]
            res_min = self.measurement['RMIN_Ohms'][1:self.dpoint]
            for ax in self.fig.get_axes():
                ax.clear()
            self.scat1 = self.ax1.scatter(plsno, plsamp, label='Current (A)', **skatargs1)
            self.scat1_twin = self.ax1_twin.scatter(plsno, plsvolt, label='Voltage (V)', **skatargs2)
            self.scat2 = self.ax2.scatter(plsno, res_min, label='Res_Min (Ohm)', **skatargs1)
            self.scat2_twin = self.ax2_twin.scatter(plsno, res_max, label='Res_Max (Ohm)', **skatargs2)
            for ax in self.fig.get_axes():
                decorate_ax(ax)

            self.ax2.set_xlabel('PLS Number')
            self.ax1.set_ylabel('Pulse Current (A)')
            self.ax1_twin.set_ylabel('Pulse Voltage (V)')
            self.ax2.set_ylabel('Resistance_min (Ohm)')
            self.ax2_twin.set_ylabel('Resistance_max (Ohm)')

            self.ax2.legend(loc='upper left')
            self.ax1.legend(loc='upper left')
            self.ax1_twin.legend(loc='upper right')
            self.ax2_twin.legend(loc='upper right')

            self.canvas.draw()
            self.canvas.flush_events()

    def _measure(self):
        inst = self.controller.k2612B_instrument

        if self.resmeas_bool == True:
            if self.resmeas_bool_polarity_switch == False:
                if self.iter == 0:
                    self._set_sourcing(self.params['PROBE'])

                    self.iter += 1
                    self.exp_time = self.controller.runtime
                    self.start_time = self.controller.runtime
                    self.running_time = self.controller.runtime
                    self._inst_cont_turn_on()

                    smu_curr, _ = self.controller.k2612B_instrument.measure_channel(self.smu_chan)
                    _, vm_volt = self.controller.k2612B_instrument.measure_channel(self.vm_chan)
                    res = round(float(vm_volt) / float(smu_curr), 4)

                    self.measurement_accumulator.append(res)
                else:
                    if (self.exp_time - self.start_time) >= float(self.params['PROBEDURATION']):
                        smu_curr, _ = self.controller.k2612B_instrument.measure_channel(self.smu_chan)
                        _, vm_volt = self.controller.k2612B_instrument.measure_channel(self.vm_chan)
                        res = round(float(vm_volt) / float(smu_curr), 4)
                        self.measurement_accumulator.append(res)
                        # inst.beeper(0.1)
                        self._inst_cont_turn_off()
                        self.resmeas_bool_polarity_switch = True
                        self.iter = 0
                    elif (self.exp_time - self.running_time) >= float(self.params['PROBEDATASTEP']):
                        self.exp_time = self.controller.runtime
                        self.running_time = self.controller.runtime
                        smu_curr, _ = self.controller.k2612B_instrument.measure_channel(self.smu_chan)
                        _, vm_volt = self.controller.k2612B_instrument.measure_channel(self.vm_chan)
                        res = round(float(vm_volt) / float(smu_curr), 4)
                        self.measurement_accumulator.append(res)
                    else:
                        self.exp_time = self.controller.runtime
            else:
                if self.iter == 0:
                    self._set_sourcing(str(-1 * float(self.params['PROBE'])))

                    self.iter += 1
                    self.exp_time = self.controller.runtime
                    self.start_time = self.controller.runtime
                    self.running_time = self.controller.runtime
                    self._inst_cont_turn_on()

                    smu_curr, _, vm_volt = self._get_from_inst()
                    res = round(float(vm_volt) / float(smu_curr), 4)
                    self.measurement_accumulator.append(res)

                else:
                    if (self.exp_time - self.start_time) >= float(self.params['PROBEDURATION']):
                        # print(self.measurement_accumulator)
                        rmin = sum(self.measurement_accumulator) / len(self.measurement_accumulator)
                        self.measurement['RMIN_Ohms'][self.dpoint] = rmin
                        self.lastres = rmin
                        self._send_line([
                            self.measurement['PLS_number'][self.dpoint], self.measurement['PLS_V_volts'][self.dpoint],
                            self.measurement['PLS_I_amps'][self.dpoint], self.measurement['RMAX_Ohms'][self.dpoint],
                            self.measurement['VOLTMETER_volts'][self.dpoint], self.measurement['RMIN_Ohms'][self.dpoint]
                        ])

                        self.dpoint += 1
                        if self.dpoint >= len(self.plsvals):
                            self._stop_measurement()
                        else:
                            # inst.beeper(0.1)
                            self._inst_cont_turn_off()
                            self.measurement_accumulator = []
                            self.resmeas_bool = False
                            self.resmeas_bool_polarity_switch = False
                            self.iter = 0
                    elif (self.exp_time - self.running_time) >= float(self.params['PROBEDATASTEP']):
                        self.exp_time = self.controller.runtime
                        self.running_time = self.controller.runtime
                        smu_curr, _, vm_volt = self._get_from_inst()
                        res = round(float(vm_volt) / float(smu_curr), 4)
                        self.measurement_accumulator.append(res)
                    else:
                        self.exp_time = self.controller.runtime
        else:
            if self.iter == 0:
                # Pulsing
                self._set_sourcing(str(self.plsvals[self.dpoint]))

                self.iter += 1
                self.exp_time = self.controller.runtime
                self.start_time = self.controller.runtime
                self.running_time = self.controller.runtime
                self._inst_cont_turn_on()

                smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                vm_volt = float(vm_volt)
                smu_curr = float(smu_curr)
                res = round(vm_volt / smu_curr, 4)

                self.measurement_accumulator.append(res)
                self.measurement_accumulator1.append(float(smu_curr))
                self.measurement_accumulator2.append(float(smu_vlt))
                self.measurement_accumulator3.append(float(vm_volt))

            else:
                if (self.exp_time - self.start_time) >= float(self.params['DURATION']):
                    mylen = len(self.measurement_accumulator)
                    rmax = sum(self.measurement_accumulator) / mylen
                    plscurr = sum(self.measurement_accumulator1) / mylen
                    plsvlt = sum(self.measurement_accumulator2) / mylen
                    nanovlt = sum(self.measurement_accumulator3) / mylen
                    self.measurement['RMAX_Ohms'][self.dpoint] = rmax
                    self.measurement['PLS_V_volts'][self.dpoint] = plsvlt
                    self.measurement['PLS_I_amps'][self.dpoint] = plscurr
                    self.measurement['VOLTMETER_volts'][self.dpoint] = nanovlt
                    self.measurement['PLS_number'][self.dpoint] = self.dpoint
                    # inst.beeper(0.1)
                    self._inst_cont_turn_off()
                    self.measurement_accumulator = []
                    self.measurement_accumulator1 = []
                    self.measurement_accumulator2 = []
                    self.measurement_accumulator3 = []
                    self.iter = 0

                    # self._send_line([
                    #     self.measurement['PLS_number'][self.dpoint], self.measurement['PLS_V_volts'][self.dpoint],
                    #     self.measurement['PLS_I_amps'][self.dpoint], self.measurement['RMAX_Ohms'][self.dpoint],
                    #     self.measurement['VOLTMETER_volts'][self.dpoint], self.measurement['RMIN_Ohms'][self.dpoint]
                    # ])
                    # self.dpoint += 1
                    self.resmeas_bool = True

                    # if self.dpoint >= len(self.plsvals):
                    #     self.__Stop_Measurement__()


                elif (self.exp_time - self.running_time) >= 0.01:
                    self.exp_time = self.controller.runtime
                    self.running_time = self.controller.runtime

                    smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                    vm_volt = float(vm_volt)
                    smu_curr = float(smu_curr)
                    res = round(vm_volt / smu_curr, 4)

                    self.measurement_accumulator.append(res)
                    self.measurement_accumulator1.append(float(smu_curr))
                    self.measurement_accumulator2.append(float(smu_vlt))
                    self.measurement_accumulator3.append(float(vm_volt))

                else:
                    self.exp_time = self.controller.runtime

    def _get_params(self):
        inscont = self.controller.mid_subframes[InstCont_K2612B].measurement_switcher
        self.params = {
            'START': inscont.pulsing_start.entry_stringvar.get(),
            'STOP': inscont.pulsing_stop.entry_stringvar.get(),
            'STEP': inscont.pulsing_step.entry_stringvar.get(),
            'DURATION': inscont.pulsing_duration.entry_stringvar.get(),
            'PROBE': inscont.probe_current.entry_stringvar.get(),
            'PROBEDURATION': inscont.probe_duration.entry_stringvar.get(),
            'PROBEDATASTEP': inscont.datastep.entry_stringvar.get(),
        }
        print(self.params)
        steps = (float(self.params['STOP']) - float(self.params['START'])) / float(self.params['STEP'])
        for i in range(int(steps)):
            self.plsvals.append(float(self.params['START']) + i * float(self.params['STEP']))
        print('plsvals are', self.plsvals)

    def _get_number_of_datapoints(self):
        sta = float(self.params['START'])
        stp = float(self.params['STOP'])
        sep = float(self.params['STEP'])
        dur = float(self.params['DURATION'])
        print('start, stop, step', sta, stp, sep)
        return int(abs(((stp - sta) / sep)))

    def _set_goal(self):
        # print('trying to set Goal...')
        stringvar = self.End_StringVar.get()
        # print(stringvar)
        try:
            floatvar = float(stringvar)
            # print(floatvar)
            self.goalres = floatvar
        except:
            print('Bad Value')

    def _check_goal(self):
        # print('checking...\n', f'Last ressitance is {self.lastres}\n',f'Goal resistance is {self.goalres}')
        if self.goalres is not None and self.lastres is not None and abs(self.lastres) >= abs(self.goalres):
            # self._inst_cont_turn_off()
            # self.goalres = None
            self.lastres = None
            self._stop_measurement()


class R_t_Measurement_K2612Bandk2182A(Measurement):

    def __init__(self, parent, controller):
        Measurement.__init__(self, parent, controller)

        self.label.configure(text='Resistance - Time')
        self.suffix = 'Res-Time'
        self.dirname = 'Rt'
        self.header = ['TIME_seconds', 'SRC_V_volts', 'SRC_I_amps',
                       'K2182A_Ch1_VOLTMETER_volts', 'K2182A_Ch1_RESISTANCE_Ohms',
                       'K2612B_VOLTMETER_volts', 'K2612B_RESISTANCE_Ohms',
                       'K2182A_Ch2_VOLTMETER_volts', 'K2182A_Ch2_RESISTANCE_Ohms']

        self.ax1 = self.fig.add_subplot(131)
        self.ax2 = self.fig.add_subplot(132)
        self.ax3 = self.fig.add_subplot(133)
        for ax in self.fig.get_axes():
            decorate_ax(ax)

        self.scat1 = self.ax1.scatter([], [], **skatargs1)
        self.scat2 = self.ax2.scatter([], [], **skatargs1)
        self.scat3 = self.ax3.scatter([], [], **skatargs1)
        self.ax2.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Resistance (Ohm)')

        self.controller.k2182A_instrument.set_all(1, 1e-1, 8, 0.4)

    def _find_voltmeter(self):
        if self.controller.mid_subframes[InstCont_K2612BandK2182A].chanA_Subframe.voltmeter_bool == 0:
            self.voltmeter = self.controller.mid_subframes[InstCont_K2612BandK2182A].chanB_Subframe
            self.smu = self.controller.mid_subframes[InstCont_K2612BandK2182A].chanA_Subframe
            self.smu_src = self.smu.sour.info.get()
            self.smu_chan = 'a'
            self.vm_chan = 'b'
            print(self.smu_src)
        else:
            self.voltmeter = self.controller.mid_subframes[InstCont_K2612BandK2182A].chanA_Subframe
            self.smu = self.controller.mid_subframes[InstCont_K2612BandK2182A].chanB_Subframe
            self.smu_src = self.smu.sour.info.get()
            self.smu_chan = 'b'
            self.vm_chan = 'a'
            print(self.smu_src)

    def _return_to_inst_cont(self):
        self._stop_measurement()
        self.controller._show_frame(InstCont_K2612BandK2182A)

    def _update_plot(self):
        if self.dpoint >= 1:
            time = self.measurement['TIME_seconds'][1:self.dpoint]
            res1 = self.measurement['K2182A_Ch1_RESISTANCE_Ohms'][1:self.dpoint]
            res2 = self.measurement['K2612B_RESISTANCE_Ohms'][1:self.dpoint]
            res3 = self.measurement['K2182A_Ch2_RESISTANCE_Ohms'][1:self.dpoint]
            # offsets=list(np.stack((time,res),axis=1))
            # print(offsets)
            self.ax1.clear()
            self.scat1 = self.ax1.scatter(time, res1, **skatargs1)
            self.ax2.clear()
            self.scat2 = self.ax2.scatter(time, res2, **skatargs1)
            self.ax3.clear()
            self.scat3 = self.ax3.scatter(time, res3, **skatargs1)
            for ax in self.fig.get_axes():
                decorate_ax(ax)
            self.ax2.set_xlabel('Time (s)')
            self.ax1.set_ylabel('Resistance (Ohm)')
            self.canvas.draw()
            self.canvas.flush_events()

    def _get_params(self):
        inscont = self.controller.mid_subframes[InstCont_K2612BandK2182A].measurement_switcher
        self.params = {
            'PROBE': inscont.probe_current.entry_stringvar.get(),
            'DURATION': inscont.probe_duration.entry_stringvar.get(),
            'DATASTEP': inscont.datastep.entry_stringvar.get(),
        }

    def _get_number_of_datapoints(self):
        dur = float(self.params['DURATION'])
        stp = float(self.params['DATASTEP'])
        return int(dur / stp)

    def _measure(self):
        inst_K2612B = self.controller.k2612B_instrument
        inst_k2182A = self.controller.k2182A_instrument
        if self.iter == 0:
            if self.smu_src == 'I':
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.src_I(self.smu_chan)
                inst_K2612B.src_level_AMPS(self.smu_chan, self.params['PROBE'])
            elif self.smu_src == 'V':
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.src_I(self.smu_chan)
                inst_K2612B.src_level_VOLTS(self.smu_chan, self.params['PROBE'])
            self.iter += 1
            self.exp_time = self.controller.runtime
            self.start_time = self.controller.runtime
            self.running_time = self.controller.runtime
            self._inst_cont_turn_on()
            smu_curr, smu_volt = inst_K2612B.measure_channel(self.smu_chan)
            # smu_curr, smu_volt = self.controller.k2612B_instrument.measure_channel(self.smu_chan)
            _, vm_volt = inst_K2612B.measure_channel(self.vm_chan)
            nvm1, nvm2 = inst_k2182A.read_both()
            time = str(round(self.exp_time, 6))
            res1 = round(float(nvm1) / float(smu_curr), 4)
            res2 = round(float(vm_volt) / float(smu_curr), 4)
            res3 = round(float(nvm2) / float(smu_curr), 4)
            dat = [time, smu_volt, smu_curr, nvm1, str(res1), vm_volt, str(res2), nvm2, str(res3)]
            self._send_line(dat)
            self._set_datadict_vals(dat, self.dpoint)
            self.dpoint += 1
        else:
            if (self.exp_time - self.start_time) >= float(self.params['DURATION']):
                self._stop_measurement()
            elif (self.exp_time - self.running_time) >= float(self.params['DATASTEP']):
                self.exp_time = self.controller.runtime
                self.running_time = self.controller.runtime
                smu_curr, smu_volt = inst_K2612B.measure_channel(self.smu_chan)
                # smu_curr, smu_volt = self.controller.k2612B_instrument.measure_channel(self.smu_chan)
                _, vm_volt = inst_K2612B.measure_channel(self.vm_chan)
                nvm1, nvm2 = inst_k2182A.read_both()
                time = str(round(self.exp_time, 6))
                res1 = round(float(nvm1) / float(smu_curr), 4)
                res2 = round(float(vm_volt) / float(smu_curr), 4)
                res3 = round(float(nvm2) / float(smu_curr), 4)
                dat = [time, smu_volt, smu_curr, nvm1, str(res1), vm_volt, str(res2), nvm2, str(res3)]
                self._send_line(dat)
                self._set_datadict_vals(dat, self.dpoint)
                self.dpoint += 1
            else:
                self.exp_time = self.controller.runtime


class Pulse_Series_Measurement_K2612Bandk2182A(Measurement):
    def __init__(self, parent, controller):
        Measurement.__init__(self, parent, controller)
        self.resmeas_bool = False
        self.resmeas_bool_polarity_switch = False
        self.lastres = None

        self.label.configure(text='Pulse Series')
        self.suffix = 'PLS'
        self.dirname = 'PLS'

        ###EDITS
        self.header = [
            'PLS_number', 'PLS_V_volts', 'PLS_I_amps'
            , 'K2182A_Ch1_RMAX_Ohms', 'K2182A_Ch1_VOLTMETER_volts', 'K2182A_Ch1_RMIN_Ohms'
            , 'K2612B_RMAX_Ohms', 'K2612B_VOLTMETER_volts', 'K2612B_RMIN_Ohms'
            , 'K2182A_Ch2_RMAX_Ohms', 'K2182A_Ch2_VOLTMETER_volts', 'K2182A_Ch2_RMIN_Ohms']
        gs = self.fig.add_gridspec(2, 3)
        self.ax1 = self.fig.add_subplot(gs[0, :])
        self.ax1_twin = self.ax1.twinx()
        self.ax2 = self.fig.add_subplot(gs[1, 1])
        self.ax2_twin = self.ax2.twinx()
        self.ax2_lowleft = self.fig.add_subplot(gs[1, 0])
        self.ax2_lowleft_twin = self.ax2_lowleft.twinx()
        self.ax2_lowright = self.fig.add_subplot(gs[1, 2])
        self.ax2_lowright_twin = self.ax2_lowright.twinx()
        for ax in self.fig.get_axes():
            decorate_ax(ax)

        # self.ax1.sharex(self.ax2)
        self.ax2.set_xlabel('PLS Number')
        self.ax1.set_ylabel('Pulse Current (A)')
        self.ax1_twin.set_ylabel('Pulse Voltage (V)')
        self.ax2_lowleft.set_ylabel('Resistance_min (Ohm)')
        self.ax2_lowright_twin.set_ylabel('Resistance_max (Ohm)')

        self.scat1 = self.ax1.scatter([], [], **skatargs1)
        self.scat1_twin = self.ax1_twin.scatter([], [], **skatargs2)
        self.scat2 = self.ax2.scatter([], [], **skatargs1)
        self.scat2_twin = self.ax2_twin.scatter([], [], **skatargs2)
        self.scat2_lowleft = self.ax2_lowleft.scatter([], [], **skatargs1)
        self.scat2_lowleft_twin = self.ax2_lowleft_twin.scatter([], [], **skatargs2)
        self.scat2_lowright = self.ax2_lowright.scatter([], [], **skatargs1)
        self.scat2_lowright_twin = self.ax2_lowright_twin.scatter([], [], **skatargs2)

        self.measurement_accumulator = []
        self.measurement_accumulator_lowleft = []
        self.measurement_accumulator_lowright = []
        self.measurement_accumulator1 = []
        self.measurement_accumulator2 = []
        self.measurement_accumulator3 = []
        self.measurement_accumulator3_lowleft = []
        self.measurement_accumulator3_lowright = []

        self.plsvals = []

        self.controller.k2182A_instrument.set_all(1, 1e-1, 8, 0.4)

    def _find_voltmeter(self):
        if self.controller.mid_subframes[InstCont_K2612BandK2182A].chanA_Subframe.voltmeter_bool == 0:
            self.voltmeter = self.controller.mid_subframes[InstCont_K2612BandK2182A].chanB_Subframe
            self.smu = self.controller.mid_subframes[InstCont_K2612BandK2182A].chanA_Subframe
            self.smu_src = self.smu.sour.info.get()
            self.smu_chan = 'a'
            self.vm_chan = 'b'
            print(self.smu_src)
        else:
            self.voltmeter = self.controller.mid_subframes[InstCont_K2612BandK2182A].chanA_Subframe
            self.smu = self.controller.mid_subframes[InstCont_K2612BandK2182A].chanB_Subframe
            self.smu_src = self.smu.sour.info.get()
            self.smu_chan = 'b'
            self.vm_chan = 'a'
            print(self.smu_src)

    def _check_param_validity(self):
        for value in self.params.values():
            try:
                float(value)
                print(value)
            except:
                tk.messagebox.showwarning('ERROR: BAD PARAMS',
                                          'Please check the input parameters on the previous screen.')
                break
        print(self.smu_src)
        if self.smu_src not in ['I', 'V']:
            tk.messagebox.showwarning('ERROR: BAD PARAMS', 'Please check the input parameters on the previous screen.')

    def _return_to_inst_cont(self):
        self._stop_measurement()
        self.controller._show_frame(InstCont_K2612BandK2182A)

    def _update_plot(self):
        if self.dpoint >= 1:
            plsno = self.measurement['PLS_number'][1:self.dpoint]
            plsvolt = self.measurement['PLS_V_volts'][1:self.dpoint]
            plsamp = self.measurement['PLS_I_amps'][1:self.dpoint]
            res_max = self.measurement['K2612B_RMAX_Ohms'][1:self.dpoint]
            res_min = self.measurement['K2612B_RMIN_Ohms'][1:self.dpoint]
            res_max_lowleft = self.measurement['K2182A_Ch1_RMAX_Ohms'][1:self.dpoint]
            res_min_lowleft = self.measurement['K2182A_Ch1_RMIN_Ohms'][1:self.dpoint]
            res_max_lowright = self.measurement['K2182A_Ch2_RMAX_Ohms'][1:self.dpoint]
            res_min_lowright = self.measurement['K2182A_Ch2_RMIN_Ohms'][1:self.dpoint]
            for ax in self.fig.get_axes():
                ax.clear()
            self.scat1 = self.ax1.scatter(plsno, plsamp, label='Current (A)', **skatargs1)
            self.scat1_twin = self.ax1_twin.scatter(plsno, plsvolt, label='Voltage (V)', **skatargs2)
            self.scat2 = self.ax2.scatter(plsno, res_min, **skatargs1)
            self.scat2_twin = self.ax2_twin.scatter(plsno, res_max, **skatargs2)
            self.scat2_lowleft = self.ax2_lowleft.scatter(plsno, res_min_lowleft, label='Res_Min (Ohm)', **skatargs1)
            self.scat2_lowleft_twin = self.ax2_lowleft_twin.scatter(plsno, res_max_lowleft, label='Res_Max (Ohm)',
                                                                    **skatargs2)
            self.scat2_lowright = self.ax2_lowright.scatter(plsno, res_min_lowright, **skatargs1)
            self.scat2_lowright_twin = self.ax2_lowright_twin.scatter(plsno, res_max_lowright, **skatargs2)
            for ax in self.fig.get_axes():
                decorate_ax(ax)

            self.ax2.set_xlabel('PLS Number')
            self.ax1.set_ylabel('Pulse Current (A)')
            self.ax1_twin.set_ylabel('Pulse Voltage (V)')
            self.ax2_lowleft.set_ylabel('Resistance_min (Ohm)')
            self.ax2_lowright_twin.set_ylabel('Resistance_max (Ohm)')

            self.ax2_lowleft.legend(loc='upper left')
            self.ax1.legend(loc='upper left')
            self.ax1_twin.legend(loc='upper right')
            self.ax2_lowleft_twin.legend(loc='upper right')

            self.canvas.draw()
            self.canvas.flush_events()

    def _measure(self):
        inst_k2612B = self.controller.k2612B_instrument
        inst_k2182A = self.controller.k2182A_instrument

        if self.resmeas_bool == True:
            if self.resmeas_bool_polarity_switch == False:
                if self.iter == 0:
                    self._set_sourcing(self.params['PROBE'])

                    self.iter += 1
                    self.exp_time = self.controller.runtime
                    self.start_time = self.controller.runtime
                    self.running_time = self.controller.runtime
                    self._inst_cont_turn_on()

                    smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                    nvm1, nvm2 = inst_k2182A.read_both()
                    res = round(float(vm_volt) / float(smu_curr), 4)
                    res_lowleft = round(float(nvm1) / float(smu_curr), 4)
                    res_lowright = round(float(nvm2) / float(smu_curr), 4)

                    self.measurement_accumulator.append(res)
                    self.measurement_accumulator_lowleft.append(res_lowleft)
                    self.measurement_accumulator_lowright.append(res_lowright)
                else:
                    if (self.exp_time - self.start_time) >= float(self.params['PROBEDURATION']):

                        smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                        nvm1, nvm2 = inst_k2182A.read_both()
                        res = round(float(vm_volt) / float(smu_curr), 4)
                        res_lowleft = round(float(nvm1) / float(smu_curr), 4)
                        res_lowright = round(float(nvm2) / float(smu_curr), 4)

                        self.measurement_accumulator.append(res)
                        self.measurement_accumulator_lowleft.append(res_lowleft)
                        self.measurement_accumulator_lowright.append(res_lowright)
                        # inst.beeper(0.1)
                        self._inst_cont_turn_off()
                        self.resmeas_bool_polarity_switch = True
                        self.iter = 0
                    elif (self.exp_time - self.running_time) >= float(self.params['PROBEDATASTEP']):
                        self.exp_time = self.controller.runtime
                        self.running_time = self.controller.runtime

                        smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                        nvm1, nvm2 = inst_k2182A.read_both()
                        res = round(float(vm_volt) / float(smu_curr), 4)
                        res_lowleft = round(float(nvm1) / float(smu_curr), 4)
                        res_lowright = round(float(nvm2) / float(smu_curr), 4)

                        self.measurement_accumulator.append(res)
                        self.measurement_accumulator_lowleft.append(res_lowleft)
                        self.measurement_accumulator_lowright.append(res_lowright)
                    else:
                        self.exp_time = self.controller.runtime
            else:
                if self.iter == 0:
                    self._set_sourcing(str(-1 * float(self.params['PROBE'])))

                    self.iter += 1
                    self.exp_time = self.controller.runtime
                    self.start_time = self.controller.runtime
                    self.running_time = self.controller.runtime
                    self._inst_cont_turn_on()

                    smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                    nvm1, nvm2 = inst_k2182A.read_both()
                    res = round(float(vm_volt) / float(smu_curr), 4)
                    res_lowleft = round(float(nvm1) / float(smu_curr), 4)
                    res_lowright = round(float(nvm2) / float(smu_curr), 4)

                    self.measurement_accumulator.append(res)
                    self.measurement_accumulator_lowleft.append(res_lowleft)
                    self.measurement_accumulator_lowright.append(res_lowright)

                else:
                    if (self.exp_time - self.start_time) >= float(self.params['PROBEDURATION']):
                        # print(self.measurement_accumulator)

                        rmin = sum(self.measurement_accumulator) / len(self.measurement_accumulator)
                        rmin_lowleft = sum(self.measurement_accumulator_lowleft) / len(self.measurement_accumulator)
                        rmin_lowright = sum(self.measurement_accumulator_lowright) / len(self.measurement_accumulator)
                        self.measurement['K2612B_RMIN_Ohms'][self.dpoint] = rmin
                        self.measurement['K2182A_Ch1_RMIN_Ohms'][self.dpoint] = rmin_lowleft
                        self.measurement['K2182A_Ch2_RMIN_Ohms'][self.dpoint] = rmin_lowright

                        self.lastres = rmin
                        self._send_line([
                            self.measurement['PLS_number'][self.dpoint],
                            self.measurement['PLS_V_volts'][self.dpoint],
                            self.measurement['PLS_I_amps'][self.dpoint],
                            self.measurement['K2182A_Ch1_RMAX_Ohms'][self.dpoint],
                            self.measurement['K2182A_Ch1_VOLTMETER_volts'][self.dpoint],
                            self.measurement['K2182A_Ch1_RMIN_Ohms'][self.dpoint],
                            self.measurement['K2612B_RMAX_Ohms'][self.dpoint],
                            self.measurement['K2612B_VOLTMETER_volts'][self.dpoint],
                            self.measurement['K2612B_RMIN_Ohms'][self.dpoint],
                            self.measurement['K2182A_Ch2_RMAX_Ohms'][self.dpoint],
                            self.measurement['K2182A_Ch2_VOLTMETER_volts'][self.dpoint],
                            self.measurement['K2182A_Ch2_RMIN_Ohms'][self.dpoint]
                        ])

                        self.dpoint += 1

                        if self.dpoint >= len(self.plsvals):
                            self._stop_measurement()
                        else:
                            # inst.beeper(0.1)
                            self._inst_cont_turn_off()
                            self.measurement_accumulator = []
                            self.resmeas_bool = False
                            self.resmeas_bool_polarity_switch = False
                            self.iter = 0

                    elif (self.exp_time - self.running_time) >= float(self.params['PROBEDATASTEP']):
                        self.exp_time = self.controller.runtime

                        smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                        nvm1, nvm2 = inst_k2182A.read_both()
                        res = round(float(vm_volt) / float(smu_curr), 4)
                        res_lowleft = round(float(nvm1) / float(smu_curr), 4)
                        res_lowright = round(float(nvm2) / float(smu_curr), 4)

                        self.measurement_accumulator.append(res)
                        self.measurement_accumulator_lowleft.append(res_lowleft)
                        self.measurement_accumulator_lowright.append(res_lowright)
                    else:
                        self.exp_time = self.controller.runtime
        else:
            if self.iter == 0:
                # Pulsing
                self._set_sourcing(str(self.plsvals[self.dpoint]))

                self.iter += 1
                self.exp_time = self.controller.runtime
                self.start_time = self.controller.runtime
                self.running_time = self.controller.runtime
                self._inst_cont_turn_on()

                smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                nvm1, nvm2 = inst_k2182A.read_both()
                res = round(float(vm_volt) / float(smu_curr), 4)
                res_lowleft = round(float(nvm1) / float(smu_curr), 4)
                res_lowright = round(float(nvm2) / float(smu_curr), 4)

                self.measurement_accumulator.append(res)
                self.measurement_accumulator_lowleft.append(res_lowleft)
                self.measurement_accumulator_lowright.append(res_lowright)

                self.measurement_accumulator1.append(float(smu_curr))
                self.measurement_accumulator2.append(float(smu_vlt))

                self.measurement_accumulator3.append(float(vm_volt))
                self.measurement_accumulator3_lowleft.append(float(nvm1))
                self.measurement_accumulator3_lowright.append(float(nvm2))

            else:
                if (self.exp_time - self.start_time) >= float(self.params['DURATION']):
                    mylen = len(self.measurement_accumulator)
                    rmax = sum(self.measurement_accumulator) / mylen
                    rmax_lowleft = sum(self.measurement_accumulator_lowleft) / mylen
                    rmax_lowright = sum(self.measurement_accumulator_lowright) / mylen
                    plscurr = sum(self.measurement_accumulator1) / mylen
                    plsvlt = sum(self.measurement_accumulator2) / mylen
                    nanovlt = sum(self.measurement_accumulator3) / mylen
                    nanovlt_lowleft = sum(self.measurement_accumulator3_lowleft) / mylen
                    nanovlt_lowright = sum(self.measurement_accumulator3_lowright) / mylen
                    self.measurement['K2612B_RMAX_Ohms'][self.dpoint] = rmax
                    self.measurement['K2182A_Ch1_RMAX_Ohms'][self.dpoint] = rmax_lowleft
                    self.measurement['K2182A_Ch2_RMAX_Ohms'][self.dpoint] = rmax_lowright
                    self.measurement['PLS_V_volts'][self.dpoint] = plsvlt
                    self.measurement['PLS_I_amps'][self.dpoint] = plscurr
                    self.measurement['K2612B_VOLTMETER_volts'][self.dpoint] = nanovlt
                    self.measurement['K2182A_Ch1_VOLTMETER_volts'][self.dpoint] = nanovlt_lowleft
                    self.measurement['K2182A_Ch2_VOLTMETER_volts'][self.dpoint] = nanovlt_lowright
                    self.measurement['PLS_number'][self.dpoint] = self.dpoint
                    # inst.beeper(0.1)
                    self._inst_cont_turn_off()
                    self.measurement_accumulator = []
                    self.measurement_accumulator_lowleft = []
                    self.measurement_accumulator_lowright = []
                    self.measurement_accumulator1 = []
                    self.measurement_accumulator2 = []
                    self.measurement_accumulator3 = []
                    self.measurement_accumulator3_lowleft = []
                    self.measurement_accumulator3_lowright = []
                    self.iter = 0

                    # self._send_line([
                    #     self.measurement['PLS_number'][self.dpoint], self.measurement['PLS_V_volts'][self.dpoint],
                    #     self.measurement['PLS_I_amps'][self.dpoint], self.measurement['RMAX_Ohms'][self.dpoint],
                    #     self.measurement['VOLTMETER_volts'][self.dpoint], self.measurement['RMIN_Ohms'][self.dpoint]
                    # ])
                    # self.dpoint += 1
                    self.resmeas_bool = True

                    # if self.dpoint >= len(self.plsvals):
                    #     self.__Stop_Measurement__()


                elif (self.exp_time - self.running_time) >= 0.01:
                    self.exp_time = self.controller.runtime
                    self.running_time = self.controller.runtime

                    smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                    nvm1, nvm2 = inst_k2182A.read_both()
                    res = round(float(vm_volt) / float(smu_curr), 4)
                    res_lowleft = round(float(nvm1) / float(smu_curr), 4)
                    res_lowright = round(float(nvm2) / float(smu_curr), 4)

                    self.measurement_accumulator.append(res)
                    self.measurement_accumulator_lowleft.append(res_lowleft)
                    self.measurement_accumulator_lowright.append(res_lowright)

                    self.measurement_accumulator1.append(float(smu_curr))
                    self.measurement_accumulator2.append(float(smu_vlt))

                    self.measurement_accumulator3.append(float(vm_volt))
                    self.measurement_accumulator3_lowleft.append(float(nvm1))
                    self.measurement_accumulator3_lowright.append(float(nvm2))

                else:
                    self.exp_time = self.controller.runtime

    def _get_params(self):
        inscont = self.controller.mid_subframes[InstCont_K2612BandK2182A].measurement_switcher
        self.params = {
            'START': inscont.pulsing_start.entry_stringvar.get(),
            'STOP': inscont.pulsing_stop.entry_stringvar.get(),
            'STEP': inscont.pulsing_step.entry_stringvar.get(),
            'DURATION': inscont.pulsing_duration.entry_stringvar.get(),
            'PROBE': inscont.probe_current.entry_stringvar.get(),
            'PROBEDURATION': inscont.probe_duration.entry_stringvar.get(),
            'PROBEDATASTEP': inscont.datastep.entry_stringvar.get(),
        }
        print(self.params)
        steps = (float(self.params['STOP']) - float(self.params['START'])) / float(self.params['STEP'])
        for i in range(int(steps)):
            self.plsvals.append(round(float(self.params['START']) + i * float(self.params['STEP']), 8))
        print('plsvals are', self.plsvals)

    def _get_number_of_datapoints(self):
        sta = float(self.params['START'])
        stp = float(self.params['STOP'])
        sep = float(self.params['STEP'])
        dur = float(self.params['DURATION'])
        print('start, stop, step', sta, stp, sep)
        return int(abs(((stp - sta) / sep)))

    def _set_goal(self):
        # print('trying to set Goal...')
        stringvar = self.End_StringVar.get()
        # print(stringvar)
        try:
            floatvar = float(stringvar)
            # print(floatvar)
            self.goalres = floatvar
        except:
            print('Bad Value')

    def _check_goal(self):
        # print('checking...\n', f'Last ressitance is {self.lastres}\n',f'Goal resistance is {self.goalres}')
        if self.goalres is not None and self.lastres is not None and abs(self.lastres) >= abs(self.goalres):
            # self._inst_cont_turn_off()
            # self.goalres = None
            self.lastres = None
            self._stop_measurement()


class R_t_Measurement_K6221andK2182A(Measurement):
    def __init__(self, parent, controller):
        Measurement.__init__(self, parent, controller)

        self.label.configure(text='Resistance - Time')
        self.suffix = 'Res-Time'
        self.dirname = 'Rt'
        self.header = ['TIME_seconds', 'SRC_DC_I_amps', 'VOLTMETER_volts', 'RESISTANCE_Ohms']

        self.ax = self.fig.add_subplot(111)
        decorate_ax(self.ax)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Resistance (Ohm)')

        self.scat = self.ax.scatter([], [], **skatargs1)

    def _update_plot(self):
        if self.dpoint >= 1:
            time = self.measurement['TIME_seconds'][1:self.dpoint]
            res = self.measurement['RESISTANCE_Ohms'][1:self.dpoint]
            # offsets=list(np.stack((time,res),axis=1))
            # print(offsets)
            self.ax.clear()
            self.scat = self.ax.scatter(time, res, **skatargs1)
            decorate_ax(self.ax)
            # self.ax.relim()
            # self.ax.autoscale_view()
            self.canvas.draw()
            self.canvas.flush_events()

    def _get_params(self):
        inscont = self.controller.mid_subframes[InstCont_K6221andK2182A].measurement_switcher
        self.params = {
            'PROBE': inscont.probe_current.entry_stringvar.get(),
            'DURATION': inscont.probe_duration.entry_stringvar.get(),
            'DATASTEP': inscont.datastep.entry_stringvar.get(),
        }

    def _get_number_of_datapoints(self):
        dur = float(self.params['DURATION'])
        stp = float(self.params['DATASTEP'])
        return int(dur / stp)

    def _measure(self):
        src = self.controller.k6221_instrument
        vm = self.controller.k2182A_instrument
        contfr = self.controller.mid_subframes[InstCont_K6221andK2182A]
        if self.iter == 0:
            self.controller.k2182A_instrument.set_all(1,
                                                      float(contfr.rngframe_K6221.entry_stringvar.get()),
                                                      float(contfr.digframe_K6221.entry_stringvar.get()),
                                                      float(contfr.ratframe_K6221.entry_stringvar.get()))
            smu_curr = float(self.params['PROBE'])
            src.src_DC()
            src.src_limit_VOLTS(float(contfr.compframe_K6221.entry_stringvar.get()))
            src.src_level_AMPS()
            src.src_range_AMPS(float(contfr.rngframe_K6221.entry_stringvar.get()))

            self.iter += 1
            self.exp_time = self.controller.runtime
            self.start_time = self.controller.runtime
            self.running_time = self.controller.runtime

            self._inst_cont_turn_on()

            nvm1, _ = vm.read_both()

            time = str(round(self.exp_time, 6))
            res = round(float(nvm1) / float(smu_curr), 4)
            self._send_line([time, smu_curr, nvm1, str(res)])
            self._set_datadict_vals([time, smu_curr, nvm1, res], self.dpoint)
            self.dpoint += 1
        else:
            if (self.exp_time - self.start_time) >= float(self.params['DURATION']):
                self._stop_measurement()
            elif (self.exp_time - self.running_time) >= float(self.params['DATASTEP']):
                self.exp_time = self.controller.runtime
                self.running_time = self.controller.runtime

                smu_curr = float(self.params['PROBE'])
                nvm1, _ = vm.read_both()

                time = str(round(self.exp_time, 6))
                res = round(float(nvm1) / float(smu_curr), 4)
                self._send_line([time, smu_curr, nvm1, str(res)])
                self._set_datadict_vals([time, smu_curr, nvm1, res], self.dpoint)
                self.dpoint += 1
            else:
                self.exp_time = self.controller.runtime

    def _inst_cont_turn_on(self):
        self.controller.k6221_instrument.outp_ON(True)

    def _inst_cont_turn_off(self):
        self.controller.k6221_instrument.outp_ON(False)

    def _return_to_inst_cont(self):
        self._stop_measurement()
        self.controller._show_frame(InstCont_K6221andK2182A)


class Pulse_Series_Measurement_K6221andK2182A(Measurement):
    def __init__(self, parent, controller):
        Measurement.__init__(self, parent, controller)
        self.resmeas_bool = False
        self.resmeas_bool_polarity_switch = False
        self.lastres = None

        self.label.configure(text='Pulse Series')
        self.suffix = 'PLS'
        self.dirname = 'PLS'
        self.header = ['PLS_number', 'FREQ_Hz', 'PLS_I_amps', 'VOLTMETER_volts', 'RMIN_Ohms']

        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        for ax in [self.ax1, self.ax2, self.ax2_twin]:
            decorate_ax(ax)

        self.ax1.sharex(self.ax2)
        self.ax2.set_xlabel('PLS Number')
        self.ax1.set_ylabel('Pulse Current (A)')
        self.ax2.set_ylabel('Resistance_min (Ohm)')

        self.scat1 = self.ax1.scatter([], [], **skatargs1)
        self.scat2 = self.ax2.scatter([], [], **skatargs1)

        self.measurement_accumulator = []
        self.measurement_accumulator1 = []
        self.measurement_accumulator2 = []
        self.measurement_accumulator3 = []

        self.plsvals = []

    def _update_plot(self):
        if self.dpoint >= 1:
            plsno = self.measurement['PLS_number'][1:self.dpoint]
            plsamp = self.measurement['PLS_I_amps'][1:self.dpoint]
            res_min = self.measurement['RMIN_Ohms'][1:self.dpoint]
            for ax in self.fig.get_axes():
                ax.clear()
            self.scat1 = self.ax1.scatter(plsno, plsamp, label='Current (A)', **skatargs1)
            self.scat2 = self.ax2.scatter(plsno, res_min, label='Res_Min (Ohm)', **skatargs1)
            for ax in self.fig.get_axes():
                decorate_ax(ax)

            self.ax2.set_xlabel('PLS Number')
            self.ax1.set_ylabel('Pulse Current (A)')
            self.ax2.set_ylabel('Resistance_min (Ohm)')

            self.ax2.legend(loc='upper left')
            self.ax1.legend(loc='upper left')

            self.canvas.draw()
            self.canvas.flush_events()

    def _inst_cont_turn_on(self):
        self.controller.k6221_instrument.outp_ON(True)

    def _inst_cont_turn_off(self):
        self.controller.k6221_instrument.outp_ON(False)

    def _measure(self):
        inst = self.controller.k2612B_instrument

        src = self.controller.k6221_instrument
        nvm = self.controller.k2182A_instrument
        contfr = self.controller.mid_subframes[InstCont_K6221andK2182A]
        smu_curr = float(self.params['PROBE'])
        freq = float(self.params['FREQ'])
        if self.resmeas_bool == True:
            if self.resmeas_bool_polarity_switch == False:
                if self.iter == 0:
                    self.controller.k2182A_instrument.set_all(1,
                                                              float(contfr.rngframe_K6221.entry_stringvar.get()),
                                                              float(contfr.digframe_K6221.entry_stringvar.get()),
                                                              float(contfr.ratframe_K6221.entry_stringvar.get()))

                    src.src_DC()
                    src.src_limit_VOLTS(float(contfr.compframe_K6221.entry_stringvar.get()))
                    src.src_level_AMPS()
                    src.src_range_AMPS(float(contfr.rngframe_K6221.entry_stringvar.get()))

                    self.iter += 1
                    self.exp_time = self.controller.runtime
                    self.start_time = self.controller.runtime
                    self.running_time = self.controller.runtime
                    self._inst_cont_turn_on()

                    nvm1, _ = nvm.read_both()

                    time = str(round(self.exp_time, 6))
                    res = round(float(nvm1) / float(smu_curr), 4)

                    self.measurement_accumulator.append(res)
                else:
                    if (self.exp_time - self.start_time) >= float(self.params['PROBEDURATION']):
                        nvm1, _ = nvm.read_both()

                        time = str(round(self.exp_time, 6))
                        res = round(float(nvm1) / float(smu_curr), 4)

                        self.measurement_accumulator.append(res)
                        # inst.beeper(0.1)
                        self._inst_cont_turn_off()
                        self.resmeas_bool_polarity_switch = True
                        self.iter = 0
                    elif (self.exp_time - self.running_time) >= float(self.params['PROBEDATASTEP']):
                        nvm1, _ = nvm.read_both()

                        time = str(round(self.exp_time, 6))
                        res = round(float(nvm1) / float(smu_curr), 4)

                        self.measurement_accumulator.append(res)
                    else:
                        self.exp_time = self.controller.runtime
            else:
                if self.iter == 0:
                    self._set_sourcing(str(-1 * float(self.params['PROBE'])))

                    self.iter += 1
                    self.exp_time = self.controller.runtime
                    self.start_time = self.controller.runtime
                    self.running_time = self.controller.runtime
                    self._inst_cont_turn_on()
                    nvm1, _ = nvm.read_both()

                    time = str(round(self.exp_time, 6))
                    res = round(float(nvm1) / float(smu_curr), 4)

                    self.measurement_accumulator.append(res)

                else:
                    if (self.exp_time - self.start_time) >= float(self.params['PROBEDURATION']):
                        # print(self.measurement_accumulator)
                        rmin = sum(self.measurement_accumulator) / len(self.measurement_accumulator)
                        self.measurement['RMIN_Ohms'][self.dpoint] = rmin
                        self.lastres = rmin
                        self._send_line([
                            self.measurement['PLS_number'][self.dpoint], self.measurement['FREQ_Hz'],
                            self.measurement['PLS_I_amps'][self.dpoint],
                            self.measurement['VOLTMETER_volts'][self.dpoint], self.measurement['RMIN_Ohms'][self.dpoint]
                        ])

                        self.dpoint += 1
                        if self.dpoint >= len(self.plsvals):
                            self._stop_measurement()
                        else:
                            # inst.beeper(0.1)
                            self._inst_cont_turn_off()
                            self.measurement_accumulator = []
                            self.resmeas_bool = False
                            self.resmeas_bool_polarity_switch = False
                            self.iter = 0
                    elif (self.exp_time - self.running_time) >= float(self.params['PROBEDATASTEP']):
                        self.exp_time = self.controller.runtime
                        self.running_time = self.controller.runtime
                        nvm1, _ = nvm.read_both()

                        time = str(round(self.exp_time, 6))
                        res = round(float(nvm1) / float(smu_curr), 4)

                        self.measurement_accumulator.append(res)
                    else:
                        self.exp_time = self.controller.runtime
        else:
            if self.iter == 0:
                # Pulsing
                # self._set_sourcing(str(self.plsvals[self.dpoint]))
                self.controller.K6221_instrument.performACPLS(float(contfr.compframe_K6221.entry_stringvar.get()),
                                                              self.plsvals[self.dpoint],
                                                              self.params['FREQ'],
                                                              0,
                                                              False,
                                                              False,
                                                              self.params['DURATION'])
                # self.iter += 1
                # self.exp_time = self.controller.runtime
                # self.start_time = self.controller.runtime
                # self.running_time = self.controller.runtime
                # self._inst_cont_turn_on()
                #
                # smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                # vm_volt = float(vm_volt)
                # smu_curr = float(smu_curr)
                # res = round(vm_volt / smu_curr, 4)
                #
                # self.measurement_accumulator.append(res)
                # self.measurement_accumulator1.append(float(smu_curr))
                # self.measurement_accumulator2.append(float(smu_vlt))
                # self.measurement_accumulator3.append(float(vm_volt))

            else:
                if (self.exp_time - self.start_time) >= float(self.params['DURATION']):
                    self.controller.k6221_instrument.abort_ACPLS()
                    mylen = len(self.measurement_accumulator)
                    # rmax = sum(self.measurement_accumulator) / mylen
                    # plscurr = sum(self.measurement_accumulator1) / mylen
                    # plsvlt = sum(self.measurement_accumulator2) / mylen
                    # nanovlt = sum(self.measurement_accumulator3) / mylen
                    # self.measurement['RMAX_Ohms'][self.dpoint] = rmax
                    # self.measurement['PLS_V_volts'][self.dpoint] = plsvlt
                    self.measurement['PLS_I_amps'][self.dpoint] = self.plsvals[self.dpoint]
                    # self.measurement['VOLTMETER_volts'][self.dpoint] = nanovlt
                    self.measurement['PLS_number'][self.dpoint] = self.dpoint
                    # # inst.beeper(0.1)
                    # self._inst_cont_turn_off()
                    # self.measurement_accumulator = []
                    # self.measurement_accumulator1 = []
                    # self.measurement_accumulator2 = []
                    # self.measurement_accumulator3 = []
                    self.iter = 0

                    # self._send_line([
                    #     self.measurement['PLS_number'][self.dpoint], self.measurement['PLS_V_volts'][self.dpoint],
                    #     self.measurement['PLS_I_amps'][self.dpoint], self.measurement['RMAX_Ohms'][self.dpoint],
                    #     self.measurement['VOLTMETER_volts'][self.dpoint], self.measurement['RMIN_Ohms'][self.dpoint]
                    # ])
                    # self.dpoint += 1
                    self.resmeas_bool = True

                    # if self.dpoint >= len(self.plsvals):
                    #     self.__Stop_Measurement__()

                #
                # elif (self.exp_time - self.running_time) >= 0.01:
                #     self.exp_time = self.controller.runtime
                #     self.running_time = self.controller.runtime
                #
                #     smu_curr, smu_vlt, vm_volt = self._get_from_inst()
                #     vm_volt = float(vm_volt)
                #     smu_curr = float(smu_curr)
                #     res = round(vm_volt / smu_curr, 4)
                #
                #     self.measurement_accumulator.append(res)
                #     self.measurement_accumulator1.append(float(smu_curr))
                #     self.measurement_accumulator2.append(float(smu_vlt))
                #     self.measurement_accumulator3.append(float(vm_volt))

                else:
                    self.exp_time = self.controller.runtime

    def _get_params(self):
        inscont = self.controller.mid_subframes[InstCont_K2612B].measurement_switcher
        self.params = {
            'START': inscont.pulsing_start.entry_stringvar.get(),
            'STOP': inscont.pulsing_stop.entry_stringvar.get(),
            'STEP': inscont.pulsing_step.entry_stringvar.get(),
            'DURATION': inscont.pulsing_duration.entry_stringvar.get(),
            'PROBE': inscont.probe_current.entry_stringvar.get(),
            'PROBEDURATION': inscont.probe_duration.entry_stringvar.get(),
            'PROBEDATASTEP': inscont.datastep.entry_stringvar.get(),
            'FREQ': self.controller.mid_subframes[InstCont_K2612B].freqframe_K6221.entry_stringvar.get(),
        }
        print(self.params)
        steps = (float(self.params['STOP']) - float(self.params['START'])) / float(self.params['STEP'])
        for i in range(int(steps)):
            self.plsvals.append(float(self.params['START']) + i * float(self.params['STEP']))
        print('plsvals are', self.plsvals)

    def _get_number_of_datapoints(self):
        sta = float(self.params['START'])
        stp = float(self.params['STOP'])
        sep = float(self.params['STEP'])
        dur = float(self.params['DURATION'])
        print('start, stop, step', sta, stp, sep)
        return int(abs(((stp - sta) / sep)))

    def _set_goal(self):
        # print('trying to set Goal...')
        stringvar = self.End_StringVar.get()
        # print(stringvar)
        try:
            floatvar = float(stringvar)
            # print(floatvar)
            self.goalres = floatvar
        except:
            print('Bad Value')

    def _check_goal(self):
        # print('checking...\n', f'Last ressitance is {self.lastres}\n',f'Goal resistance is {self.goalres}')
        if self.goalres is not None and self.lastres is not None and abs(self.lastres) >= abs(self.goalres):
            # self._inst_cont_turn_off()
            # self.goalres = None
            self.lastres = None
            self._stop_measurement()

# class Measurement_With_K2400(Measurement):

class R_t_Measurement_K2400(Measurement):
    def __init__(self, parent, controller):
        Measurement.__init__(self, parent, controller)

        self.label.configure(text='Resistance - Time')
        self.suffix = 'Res-Time'
        self.dirname = 'Rt'
        self.header = ['TIME_seconds', 'SRC_V_volts', 'SRC_I_amps', 'VOLTMETER_volts', 'RESISTANCE_Ohms']

        self.ax = self.fig.add_subplot(111)
        decorate_ax(self.ax)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Resistance (Ohm)')

        self.scat = self.ax.scatter([], [], **skatargs1)

    def _return_to_inst_cont(self):
        self._stop_measurement()
        self.controller._show_frame(InstCont_K2400andK2182A)


    def _update_plot(self):
        if self.dpoint >= 1:
            time = self.measurement['TIME_seconds'][1:self.dpoint]
            res = self.measurement['RESISTANCE_Ohms'][1:self.dpoint]
            # offsets=list(np.stack((time,res),axis=1))
            # print(offsets)
            self.ax.clear()
            self.scat = self.ax.scatter(time, res, **skatargs1)
            decorate_ax(self.ax)
            # self.ax.relim()
            # self.ax.autoscale_view()
            self.canvas.draw()
            self.canvas.flush_events()

    def _get_params(self):
        inscont = self.controller.mid_subframes[InstCont_K2400andK2182A].measurement_switcher
        self.params = {
            'PROBE': inscont.probe_current.entry_stringvar.get(),
            'DURATION': inscont.probe_duration.entry_stringvar.get(),
            'DATASTEP': inscont.datastep.entry_stringvar.get(),
        }

    def _get_number_of_datapoints(self):
        dur = float(self.params['DURATION'])
        stp = float(self.params['DATASTEP'])
        return int(dur / stp)

    def _measure(self):
        inst = self.controller.k2400_instrument
        if self.iter == 0:
            if self.smu_src == 'I':
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.src_I(self.smu_chan)
                inst.src_level_AMPS(self.params['PROBE'])
            elif self.smu_src == 'V':
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.beeper(0.1)
                # inst.src_I(self.smu_chan)
                inst.src_level_VOLTS(self.params['PROBE'])
            self.iter += 1
            self.exp_time = self.controller.runtime
            self.start_time = self.controller.runtime
            self.running_time = self.controller.runtime
            self._inst_cont_turn_on()
            smu_volt, smu_curr, *_ = self.controller.k2400_instrument.measure()
            vm_volt = self.controller.k2182A_instrument.measure_channel(1) #hardcoded ch1
            time = str(round(self.exp_time, 6))
            res = round(float(vm_volt) / float(smu_curr), 4)
            self._send_line([time, smu_volt, smu_curr, vm_volt, str(res)])
            self._set_datadict_vals([time, smu_volt, smu_curr, vm_volt], self.dpoint)
            self.dpoint += 1
        else:
            if (self.exp_time - self.start_time) >= float(self.params['DURATION']):
                self._stop_measurement()
            elif (self.exp_time - self.running_time) >= float(self.params['DATASTEP']):
                self.exp_time = self.controller.runtime
                self.running_time = self.controller.runtime
                smu_volt, smu_curr, *_ = self.controller.k2400_instrument.measure()
                vm_volt = self.controller.k2182A_instrument.measure_channel(1) #hardcoded ch1
                time = str(round(self.exp_time, 6))
                res = str(round(float(vm_volt) / float(smu_curr), 4))
                self._send_line([time, smu_volt, smu_curr, vm_volt, res])
                self._set_datadict_vals([time, smu_volt, smu_curr, vm_volt, res], self.dpoint)
                self.dpoint += 1
            else:
                self.exp_time = self.controller.runtime

    def _find_voltmeter(self):
        self.smu=self.controller.mid_subframes[InstCont_K2400andK2182A].SMU_Subframe
        self.smu_src = self.smu.sour.info.get()
        self.voltmeter=self.controller.mid_subframes[InstCont_K2400andK2182A].Ch1_read_V_StringVar

    def _inst_cont_turn_on(self):
        self.controller.k2400_instrument.outp_ON()
        # print('unsubscribing measurement')

    def _inst_cont_turn_off(self):
        self.controller.k2400_instrument.outp_OFF()
        # print('unsubscribing measurement')



class Pulse_Series_Measurement_K2400(Measurement):
    def __init__(self, parent, controller):
        Measurement.__init__(self, parent, controller)
        self.resmeas_bool = False
        self.resmeas_bool_polarity_switch = False
        self.lastres = None

        self.label.configure(text='Pulse Series')
        self.suffix = 'PLS'
        self.dirname = 'PLS'
        self.header = ['PLS_number', 'PLS_V_volts', 'PLS_I_amps', 'RMAX_Ohms', 'VOLTMETER_volts', 'RMIN_Ohms']

        self.ax1 = self.fig.add_subplot(211)
        self.ax1_twin = self.ax1.twinx()
        self.ax2 = self.fig.add_subplot(212)
        self.ax2_twin = self.ax2.twinx()
        for ax in [self.ax1, self.ax2, self.ax1_twin, self.ax2_twin]:
            decorate_ax(ax)

        self.ax1.sharex(self.ax2)
        self.ax2.set_xlabel('PLS Number')
        self.ax1.set_ylabel('Pulse Current (A)')
        self.ax1_twin.set_ylabel('Pulse Voltage (V)')
        self.ax2.set_ylabel('Resistance_min (Ohm)')
        self.ax2_twin.set_ylabel('Resistance_max (Ohm)')

        self.scat1 = self.ax1.scatter([], [], **skatargs1)
        self.scat1_twin = self.ax1_twin.scatter([], [], **skatargs2)
        self.scat2 = self.ax2.scatter([], [], **skatargs1)
        self.scat2_twin = self.ax2_twin.scatter([], [], **skatargs2)

        self.measurement_accumulator = []
        self.measurement_accumulator1 = []
        self.measurement_accumulator2 = []
        self.measurement_accumulator3 = []

        self.plsvals = []

    def _set_sourcing(self, level):
        inst = self.controller.k2400_instrument
        if self.controller.mid_subframes[InstCont_K2400andK2182A].SMU_Subframe.sour.info.get() == 'I':
            # inst.beeper(0.1)
            # inst.beeper(0.1)
            # inst.beeper(0.1)
            # inst.src_I(self.smu_chan)
            inst.src_level_AMPS(level)
        elif self.controller.mid_subframes[InstCont_K2400andK2182A].SMU_Subframe.sour.info.get() == 'V':
            # inst.beeper(0.1)
            # inst.beeper(0.1)
            # inst.beeper(0.1)
            # inst.src_I(self.smu_chan)
            inst.src_level_VOLTS(level)


    def _check_param_validity(self):
        for value in self.params.values():
            try:
                float(value)
                print(value)
            except:
                tk.messagebox.showwarning('ERROR: BAD PARAMS',
                                          'Please check the input parameters on the previous screen.')
                break
        print('self.smu_src is', self.smu_src)

    def _inst_cont_turn_on(self):
        self.controller.k2400_instrument.outp_ON()
        # print('unsubscribing measurement')

    def _inst_cont_turn_off(self):
        self.controller.k2400_instrument.outp_ON()
        # print('unsubscribing measurement')
    def _return_to_inst_cont(self):
        self._stop_measurement()
        self.controller._show_frame(InstCont_K2400andK2182A)

    def _update_plot(self):
        if self.dpoint >= 1:
            plsno = self.measurement['PLS_number'][1:self.dpoint]
            plsvolt = self.measurement['PLS_V_volts'][1:self.dpoint]
            plsamp = self.measurement['PLS_I_amps'][1:self.dpoint]
            res_max = self.measurement['RMAX_Ohms'][1:self.dpoint]
            res_min = self.measurement['RMIN_Ohms'][1:self.dpoint]
            for ax in self.fig.get_axes():
                ax.clear()
            self.scat1 = self.ax1.scatter(plsno, plsamp, label='Current (A)', **skatargs1)
            self.scat1_twin = self.ax1_twin.scatter(plsno, plsvolt, label='Voltage (V)', **skatargs2)
            self.scat2 = self.ax2.scatter(plsno, res_min, label='Res_Min (Ohm)', **skatargs1)
            self.scat2_twin = self.ax2_twin.scatter(plsno, res_max, label='Res_Max (Ohm)', **skatargs2)
            for ax in self.fig.get_axes():
                decorate_ax(ax)

            self.ax2.set_xlabel('PLS Number')
            self.ax1.set_ylabel('Pulse Current (A)')
            self.ax1_twin.set_ylabel('Pulse Voltage (V)')
            self.ax2.set_ylabel('Resistance_min (Ohm)')
            self.ax2_twin.set_ylabel('Resistance_max (Ohm)')

            self.ax2.legend(loc='upper left')
            self.ax1.legend(loc='upper left')
            self.ax1_twin.legend(loc='upper right')
            self.ax2_twin.legend(loc='upper right')

            self.canvas.draw()
            self.canvas.flush_events()

    def _measure(self):
        smu = self.controller.k2400_instrument
        nvolt = self.controller.k2182A_instrument

        if self.resmeas_bool == True:
            if self.resmeas_bool_polarity_switch == False:
                if self.iter == 0:
                    self._set_sourcing(self.params['PROBE'])

                    self.iter += 1
                    self.exp_time = self.controller.runtime
                    self.start_time = self.controller.runtime
                    self.running_time = self.controller.runtime
                    self._inst_cont_turn_on()

                    smu_volt, smu_curr,  *_ = smu.measure()
                    vm_volt = nvolt.measure_channel(1)
                    res = round(float(vm_volt) / float(smu_curr), 4)

                    self.measurement_accumulator.append(res)
                else:
                    if (self.exp_time - self.start_time) >= float(self.params['PROBEDURATION']):

                        smu_volt, smu_curr,  *_ = smu.measure()
                        vm_volt = nvolt.measure_channel(1)
                        res = round(float(vm_volt) / float(smu_curr), 4)
                        self.measurement_accumulator.append(res)
                        # inst.beeper(0.1)
                        self._inst_cont_turn_off()
                        self.resmeas_bool_polarity_switch = True
                        self.iter = 0
                    elif (self.exp_time - self.running_time) >= float(self.params['PROBEDATASTEP']):
                        self.exp_time = self.controller.runtime
                        self.running_time = self.controller.runtime

                        smu_volt, smu_curr,  *_ = smu.measure()
                        vm_volt = nvolt.measure_channel(1)
                        res = round(float(vm_volt) / float(smu_curr), 4)
                        self.measurement_accumulator.append(res)
                    else:
                        self.exp_time = self.controller.runtime
            else:
                if self.iter == 0:
                    self._set_sourcing(str(-1 * float(self.params['PROBE'])))

                    self.iter += 1
                    self.exp_time = self.controller.runtime
                    self.start_time = self.controller.runtime
                    self.running_time = self.controller.runtime
                    self._inst_cont_turn_on()


                    smu_volt, smu_curr,  *_ = smu.measure()
                    vm_volt = nvolt.measure_channel(1)
                    res = round(float(vm_volt) / float(smu_curr), 4)
                    self.measurement_accumulator.append(res)

                else:
                    if (self.exp_time - self.start_time) >= float(self.params['PROBEDURATION']):
                        # print(self.measurement_accumulator)
                        rmin = sum(self.measurement_accumulator) / len(self.measurement_accumulator)
                        self.measurement['RMIN_Ohms'][self.dpoint] = rmin
                        self.lastres = rmin
                        self._send_line([
                            self.measurement['PLS_number'][self.dpoint], self.measurement['PLS_V_volts'][self.dpoint],
                            self.measurement['PLS_I_amps'][self.dpoint], self.measurement['RMAX_Ohms'][self.dpoint],
                            self.measurement['VOLTMETER_volts'][self.dpoint], self.measurement['RMIN_Ohms'][self.dpoint]
                        ])

                        self.dpoint += 1
                        if self.dpoint >= len(self.plsvals):
                            self._stop_measurement()
                        else:
                            # inst.beeper(0.1)
                            self._inst_cont_turn_off()
                            self.measurement_accumulator = []
                            self.resmeas_bool = False
                            self.resmeas_bool_polarity_switch = False
                            self.iter = 0
                    elif (self.exp_time - self.running_time) >= float(self.params['PROBEDATASTEP']):
                        self.exp_time = self.controller.runtime
                        self.running_time = self.controller.runtime

                        smu_volt, smu_curr,  *_ = smu.measure()
                        vm_volt = nvolt.measure_channel(1)
                        res = round(float(vm_volt) / float(smu_curr), 4)
                        self.measurement_accumulator.append(res)
                    else:
                        self.exp_time = self.controller.runtime
        else:
            if self.iter == 0:
                # Pulsing
                self._set_sourcing(str(self.plsvals[self.dpoint]))

                self.iter += 1
                self.exp_time = self.controller.runtime
                self.start_time = self.controller.runtime
                self.running_time = self.controller.runtime
                self._inst_cont_turn_on()

                smu_volt, smu_curr,  *_ = smu.measure()
                vm_volt = nvolt.measure_channel(1)
                vm_volt = float(vm_volt)
                smu_curr = float(smu_curr)
                res = round(vm_volt / smu_curr, 4)

                self.measurement_accumulator.append(res)
                self.measurement_accumulator1.append(float(smu_curr))
                self.measurement_accumulator2.append(float(smu_volt))
                self.measurement_accumulator3.append(float(vm_volt))

            else:
                if (self.exp_time - self.start_time) >= float(self.params['DURATION']):
                    mylen = len(self.measurement_accumulator)
                    rmax = sum(self.measurement_accumulator) / mylen
                    plscurr = sum(self.measurement_accumulator1) / mylen
                    plsvlt = sum(self.measurement_accumulator2) / mylen
                    nanovlt = sum(self.measurement_accumulator3) / mylen
                    self.measurement['RMAX_Ohms'][self.dpoint] = rmax
                    self.measurement['PLS_V_volts'][self.dpoint] = plsvlt
                    self.measurement['PLS_I_amps'][self.dpoint] = plscurr
                    self.measurement['VOLTMETER_volts'][self.dpoint] = nanovlt
                    self.measurement['PLS_number'][self.dpoint] = self.dpoint
                    # inst.beeper(0.1)
                    self._inst_cont_turn_off()
                    self.measurement_accumulator = []
                    self.measurement_accumulator1 = []
                    self.measurement_accumulator2 = []
                    self.measurement_accumulator3 = []
                    self.iter = 0

                    # self._send_line([
                    #     self.measurement['PLS_number'][self.dpoint], self.measurement['PLS_V_volts'][self.dpoint],
                    #     self.measurement['PLS_I_amps'][self.dpoint], self.measurement['RMAX_Ohms'][self.dpoint],
                    #     self.measurement['VOLTMETER_volts'][self.dpoint], self.measurement['RMIN_Ohms'][self.dpoint]
                    # ])
                    # self.dpoint += 1
                    self.resmeas_bool = True

                    # if self.dpoint >= len(self.plsvals):
                    #     self.__Stop_Measurement__()


                elif (self.exp_time - self.running_time) >= 0.01:
                    self.exp_time = self.controller.runtime
                    self.running_time = self.controller.runtime


                    smu_volt, smu_curr,  *_ = smu.measure()
                    vm_volt = nvolt.measure_channel(1)
                    vm_volt = float(vm_volt)
                    smu_curr = float(smu_curr)
                    res = round(vm_volt / smu_curr, 4)

                    self.measurement_accumulator.append(res)
                    self.measurement_accumulator1.append(float(smu_curr))
                    self.measurement_accumulator2.append(float(smu_volt))
                    self.measurement_accumulator3.append(float(vm_volt))

                else:
                    self.exp_time = self.controller.runtime

    def _get_params(self):
        inscont = self.controller.mid_subframes[InstCont_K2400andK2182A].measurement_switcher
        self.params = {
            'START': inscont.pulsing_start.entry_stringvar.get(),
            'STOP': inscont.pulsing_stop.entry_stringvar.get(),
            'STEP': inscont.pulsing_step.entry_stringvar.get(),
            'DURATION': inscont.pulsing_duration.entry_stringvar.get(),
            'PROBE': inscont.probe_current.entry_stringvar.get(),
            'PROBEDURATION': inscont.probe_duration.entry_stringvar.get(),
            'PROBEDATASTEP': inscont.datastep.entry_stringvar.get(),
        }
        print(self.params)
        steps = (float(self.params['STOP']) - float(self.params['START'])) / float(self.params['STEP'])
        for i in range(int(steps)):
            self.plsvals.append(float(self.params['START']) + i * float(self.params['STEP']))
        print('plsvals are', self.plsvals)

    def _get_number_of_datapoints(self):
        sta = float(self.params['START'])
        stp = float(self.params['STOP'])
        sep = float(self.params['STEP'])
        dur = float(self.params['DURATION'])
        print('start, stop, step', sta, stp, sep)
        return int(abs(((stp - sta) / sep)))

    def _set_goal(self):
        # print('trying to set Goal...')
        stringvar = self.End_StringVar.get()
        # print(stringvar)
        try:
            floatvar = float(stringvar)
            # print(floatvar)
            self.goalres = floatvar
        except:
            print('Bad Value')

    def _check_goal(self):
        # print('checking...\n', f'Last ressitance is {self.lastres}\n',f'Goal resistance is {self.goalres}')
        if self.goalres is not None and self.lastres is not None and abs(self.lastres) >= abs(self.goalres):
            # self._inst_cont_turn_off()
            # self.goalres = None
            self.lastres = None
            self._stop_measurement()

    def _inst_cont_turn_on(self):
        self.controller.k2400_instrument.outp_ON()
        # print('unsubscribing measurement')

    def _inst_cont_turn_off(self):
        self.controller.k2400_instrument.outp_OFF()
        # print('unsubscribing measurement')



def decorate_ax(ax):
    ax.tick_params(direction='in', color='white', labelcolor='white')
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    # ax.grid()
    ax.set_facecolor('black')
