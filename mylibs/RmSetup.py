# Note that for this to work with FOSS linux libraries you need to have the pyvisa-py backend as well as
# pyvisa (with pyusb/pygpib/pyserial) as packages in your python environment. ni-visa shouldn't be needed.
# If you want to not need root access to see your instrument, you need to add udev rules to recognise the instruments.
# See https://github.com/python-ivi/python-usbtmc for example udev rules and guidelines.
from re import split  # We need to process some regular expressions so I'll need the split function from re.

#from gpib_ctypes import make_default_gpib
import pyvisa  # Controls instruments via the VISA protocol

from sys import platform
from gpib_ctypes import make_default_gpib
if platform == "linux" or platform == "linux2":
    # linux
    make_default_gpib()  # Comment for NI drivers (Windows)
    # We create a resourcemanager instance as rm that we use throughout the pyvisa k2612B_instrument control.
    rm = pyvisa.ResourceManager('@py')  # FOSS pyvisa driver
elif platform == "darwin":
    # OS X
    print('Invalid OS!')
    exit(1)
elif platform == "win32":
    # Windows...
    # rm = pyvisa.ResourceManager()  # default, I think the ni-visa pyvisa driver
    rm = pyvisa.ResourceManager('@py')


def inst_seek():
    # This function returns a dictionary where the keys are the k2612B_instrument response strings to the standard command
    # "*IDN?" and the values are the addresses rm found the instrum
    # ents at. The address is the most important
    # information as it is needed to init instances of Inst_Class.
    insts = dict()
    for instrument in rm.list_resources():
        try:
            inst = rm.open_resource(instrument)
            inst.write('*IDN?')
            response = inst.read()
            insts[response] = instrument
            print(f'............Hello, I am: {response}.\n'
                  f'............My address is: {instrument}!\n')
        except:
            print(f'Failed at address: {instrument}')  # Prints a little notification if it fails at any
            # available address.
    return insts


class InstClass_K2612B():

    """Instrument control class for our dual channel Keithley K2612B SMU.
    Is based on pyvisa and needs an k2612B_instrument address to initialize."""

    def __init__(self, inst):
        # Init via rm.open_resource
        self.instrument = rm.open_resource(inst)
        self.instrument.write('reset()')
        self.instrument.write('status.clear()')

    def _close(self):
        # Close via rm.open_resource
        self._reset()
        self.instrument.close()

    def _reset(self):
        # Send reset command method.
        self._send('reset()')

    def _send(self, command: str):
        # Send command method.
        self.instrument.write(command)

    def _read(self):
        # Read method.
        return self.instrument.read()

    def _query(self, command: str):
        # Query method. Includes some regular expression handling due to the TSP-python communication.
        self.instrument.write('status.clear()')
        r = split('[\n\t]', self.instrument.query('print(' + command + ')'))
        r_el = [element for element in r if element != '']
        if len(r_el) == 1:
            ans = r_el[0]
        else:
            ans = r_el
        # if ans == 'true':
        #     ans = True
        # elif ans == 'false':
        #     ans = False
        self.instrument.write('status.clear()')
        return ans

    def sense_remote(self, channel_str: str):
        # Set 4-point.
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.sense=smu' + channel_str + '.SENSE_REMOTE')
        else:
            print('Valid channels are "a" and "b". ')

    # The methods below are kinda self explanatory as they are the basic controls of the SMU.
    # I will maybe comment them all later.

    def sense_local(self, channel_str: str):
        # Set 2-point.
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.sense=smu' + channel_str + '.SENSE_LOCAL')
        else:
            print('Valid channels are "a" and "b". ')

    def src_I(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.source.func=smu' + channel_str + '.OUTPUT_DCAMPS')
        else:
            print('Valid channels are "a" and "b". ')

    def src_V(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.source.func=smu' + channel_str + '.OUTPUT_DCVOLTS')
        else:
            print('Valid channels are "a" and "b". ')

    #
    # def meas_IV(self, channel_str: str):
    #     if channel_str in ['a', 'b']:
    #         self._query('smu' + channel_str + '.measure.iv()')
    #     else:
    #         print('Valid channels are "a" and "b". ')

    def measure_channel(self, channel_str: str):
        if channel_str in ['a', 'b']:
            response = self._query('smu' + channel_str + '.measure.iv()')
            if len(response)!=2:
                curr, volt = 255,255
                print(f'Bad response: {response}')
            else:
                curr, volt = response
        else:
            curr, volt = 255,255
            print('Valid channels are "a" and "b". ')
        return curr, volt

    def meas_V(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._send('display.smu' + channel_str + '.measure.func=display.MEASURE_DCVOLTS')
            self._send('smu' + channel_str + '.measure.autorangev=smu' + channel_str + '.AUTORANGE_ON')
        else:
            print('Valid channels are "a" and "b". ')

    def meas_I(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._send('display.smu' + channel_str + '.measure.func=display.MEASURE_DCAMPS')
            self._send('smu' + channel_str + '.measure.autorangev=smu' + channel_str + '.AUTORANGE_ON')
        else:
            print('Valid channels are "a" and "b". ')

    def src_range_AMPS(self, channel_str: str, range: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.source.rangei=' + range)
        else:
            print('Valid channels are "a" and "b". ')

    def src_range_VOLTS(self, channel_str: str, range: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.source.rangev=' + range)
        else:
            print('Valid channels are "a" and "b". ')

    def src_level_AMPS(self, channel_str: str, level: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.source.leveli=' + level)
        else:
            print('Valid channels are "a" and "b". ')

    def src_level_VOLTS(self, channel_str: str, level: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.source.levelv=' + level)
        else:
            print('Valid channels are "a" and "b". ')

    def src_limit_AMPS(self, channel_str: str, limit: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.source.limiti=' + limit)
        else:
            print('Valid channels are "a" and "b". ')

    def src_limit_VOLTS(self, channel_str: str, limit: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.source.limitv=' + limit)
        else:
            print('Valid channels are "a" and "b". ')

    def sense_range_AMPS(self, channel_str: str, rng: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.measure.rangei=' + rng)
        else:
            print('Valid channels are "a" and "b". ')

    def sense_range_VOLTS(self, channel_str: str, rng: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.measure.rangev=' + rng)
        else:
            print('Valid channels are "a" and "b". ')

    def sense_autorange_VOLTS(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.measure.autorangev=1')
        else:
            print('Valid channels are "a" and "b". ')

    def sense_autorange_AMPS(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.measure.autorangei=1')
        else:
            print('Valid channels are "a" and "b". ')

    def outp_ON(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.source.output=1')
        else:
            print('Valid channels are "a" and "b". ')

    def outp_OFF(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.source.output=0')
        else:
            print('Valid channels are "a" and "b". ')

    def get_limit_I(self, channel_str: str):
        if channel_str in ['a', 'b']:
            res = self._query('smu' + channel_str + '.source.limiti')
        else:
            res = 255
            print('Valid channels are "a" and "b". ')
        return res

    def get_limit_V(self, channel_str: str):
        if channel_str in ['a', 'b']:
            res = self._query('smu' + channel_str + '.source.limitv')
        else:
            res = 255
            print('Valid channels are "a" and "b". ')
        return res

    def get_range_I(self, channel_str: str):
        if channel_str in ['a', 'b']:
            res = self._query('smu' + channel_str + '.source.rangei')
        else:
            res = 255
            print('Valid channels are "a" and "b". ')
        return res

    def get_range_V(self, channel_str: str):
        if channel_str in ['a', 'b']:
            res = self._query('smu' + channel_str + '.source.rangev')
        else:
            res = 255
            print('Valid channels are "a" and "b". ')
        return res

    def get_level_I(self, channel_str: str):
        if channel_str in ['a', 'b']:
            res = self._query('smu' + channel_str + '.source.leveli')
        else:
            res = 255
            print('Valid channels are "a" and "b". ')
        return res

    def get_level_V(self, channel_str: str):
        if channel_str in ['a', 'b']:
            res = self._query('smu' + channel_str + '.source.levelv')
        else:
            res = 255
            print('Valid channels are "a" and "b". ')
        return res

    def get_SRC(self, channel_str: str):
        if channel_str in ['a', 'b']:
            res = self._query('smu' + channel_str + '.source.func')
        else:
            res = 255
            print('Valid channels are "a" and "b". ')
        return res

    def base_test_src_I(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._reset()
            self.src_I(channel_str)
            self.sense_local(channel_str)
            self.src_range_AMPS(channel_str, '0.001')
            self.src_level_AMPS(channel_str, '0.0001')
            self.src_limit_VOLTS(channel_str, '0.5')
        else:
            print('Valid channels are "a" and "b". ')

    def base_test_read_V(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self.src_I(channel_str)
            self.src_range_AMPS(channel_str, '0.001')
            self.src_level_AMPS(channel_str, '0.000')
            self.src_limit_VOLTS(channel_str, '0.2')
        else:
            print('Valid channels are "a" and "b". ')

    def base_test(self, src_chann, meas_chann):
        if src_chann in ['a', 'b'] and meas_chann in ['a', 'b']:
            self.base_test_src_I(src_chann)
            self.base_test_read_V(meas_chann)
            self.outp_ON(meas_chann)
            self.outp_ON(src_chann)
        else:
            print('Valid channels are "a" and "b". ')

    def voltmeter(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self.src_I(channel_str)
            self.src_limit_VOLTS(channel_str, '20')
            # self.src_limit_VOLTS(channel_str, '200')
            self.src_range_AMPS(channel_str, '0.000001')
            self.src_level_AMPS(channel_str, '0.000000')
        else:
            print('Valid channels are "a" and "b". ')

    def beeper(self, time):
        self._send(f'beeper.beep({time},2400)')


class InstClass_K2182A():
    """Controller for the nanovoltmeter... Should be pretty simple!"""

    def __init__(self, inst):
        # Init via rm.open_resource
        self.instrument = rm.open_resource(inst)
        self.instrument.write('*RST')

    def _close(self):
        # Close via rm.open_resource
        self._reset()
        self.instrument.close()

    def _reset(self):
        # Send reset command method.
        self._send('*RST')

    def _send(self, command: str):
        # Send command method.
        self.instrument.write(command)

    def _read(self):
        # Read method.
        return self.instrument.read()

    def _query(self, command):
        r = split('[\n\t]', self.instrument.query(command))
        r_el = [element for element in r if element != '']
        if len(r_el) == 1:
            ans = r_el[0]
        else:
            ans = r_el
        return ans
        # return self.instrument.query(command)

    def measure_channel(self, chan):
        if chan == 1 or chan == 2:
            return self._query(f':SENS:CHAN {str(chan)}; :SENS:FUNC "VOLT"; :INIT:CONT ON; :SENS:DATA:FRES?')
        else:
            print('Bad Channel!')

    def read_both(self):
        return self.measure_channel(1), self.measure_channel(2)

    def sense_range_VOLTS(self, chan, rng):
        if chan == 1 or chan == 2:
            self._send(f':SENS:CHAN {str(chan)}; :SENS:VOLT:RANG {format(rng, ".8E")}')
        else:
            print('Bad Channel!')

    def sense_digits(self, chan, dig):
        # dig between 4 and 8
        if chan == 1 or chan == 2:
            self._send(f':SENS:CHAN {str(chan)}; :SENS:VOLT:DIG {str(dig)}')
        else:
            print('Bad Channel!')

    def sense_rate(self, chan, nplc):
        # nplc between 0.1 (fast) to 5 (slow)
        if chan == 1 or chan == 2:
            self._send(f':SENS:CHAN {str(chan)}; :SENS:VOLT:NPLC {str(nplc)}')
        else:
            print('Bad Channel!')

    def set_all(self, chan, rng, dig, nplc):
        if chan == 1 or chan == 2:
            self._send(
                f':SENS:CHAN {str(chan)}; :SENS:VOLT:RANG {format(rng, ".8E")}; :SENS:VOLT:DIG {str(dig)}; :SENS:VOLT:NPLC {str(nplc)}')

    # Not needed yet...
    def get_range_V(self):
        pass

    def get_digits(self):
        pass

    def get_rate(self):
        pass


class InstClass_K6221():
    """Controller for the function generator... Should be pretty simple!"""

    def __init__(self, inst):
        # Init via rm.open_resource
        self.instrument = rm.open_resource(inst)
        self.instrument.write('*RST')

    def _close(self):
        # Close via rm.open_resource
        self._reset()
        self.instrument.close()

    def _reset(self):
        # Send reset command method.
        self._send('*RST')

    def _send(self, command: str):
        # Send command method.
        self.instrument.write(command)

    def _read(self):
        # Read method.
        return self.instrument.read()

    def _query(self, command):
        return self.instrument.query(command)

    def src_wave_SIN(self):
        self._send(':SOUR:WAVE:FUNC SIN;')  # can also be square etc

    def src_wave_amp_AMPS(self, amp):
        self._send(f':SOUR:WAVE:AMPL {format(amp, ".6E")};')

    def src_wave_freq_HERZ(self, freq):
        self._send(f':SOUR:WAVE:FREQ {format(freq, ".6E")};')

    def src_wave_offs_DEG(self, offs):
        self._send(f':SOUR:WAVE:OFFS {format(offs, ".6E")};')

    def src_wave_duration_SECS(self, duration):
        self._send(f':SOUR:WAVE:DUR:TIME {format(duration, ".6E")};')

    def src_BestWaverange_BOOL(self, boolean_switch: bool):
        if boolean_switch is True:
            self._send(':SOUR:WAVE:RANG BEST;')
        elif boolean_switch is False:
            self._send(':SOUR:WAVE:RANG FIXED;')

    def src_limit_VOLTS(self, comp: str):
        self._send(f':SOUR:CURR:COMP {format(comp, ".6E")};')  # format to 1.000000E-1 VOLTS

    def src_level_AMPS(self, curr: str):
        self._send(f':SOUR:CURR {format(curr, ".6E")};')

    def src_range_AMPS(self, rng: str):
        self._send(f':SOUR:CURR:RANG {format(rng, ".6E")};')

    def src_autorange_AMPS(self, boolean_switch: bool):
        if boolean_switch is True:
            self._send(':SOUR:CURR:RANG:AUTO ON;')
        elif boolean_switch is False:
            self._send(':SOUR:CURR:RANG:AUTO OFF;')

    def outp_ON(self, boolean_switcher: bool):
        if boolean_switcher is True:
            self._send(':OUTP ON;')
        elif boolean_switcher is False:
            self._send(':OUTP OFF;')

    def src_DC(self):
        self._reset()
        self._send('CLE')
        self.src_autorange_AMPS(True)
        self.src_limit_VOLTS(0.1)

    # def testDC(self):
    #     self.src_DC()
    #     self.src_range_AMPS(1e-3)
    #     self.src_limit_VOLTS(5e-1)
    #     self.src_level_AMPS(1e-5)
    #     self.outp_ON(True)
    #
    # def testACPLS(self):
    #     self._reset()
    #     self.src_wave_SIN()
    #     self.src_limit_VOLTS(1e-1)
    #     self.src_wave_amp_AMPS(1e-5)
    #     self.src_wave_freq_HERZ(987)
    #     self.src_wave_offs_DEG(0)
    #     self.src_autorange_AMPS(True)
    #     self.src_BestWaverange_BOOL(True)
    #     self.src_wave_duration_SECS(10)
    #
    def arm_init_ACPLS(self):
        self._send(':SOUR:WAVE:ARM; :SOUR:WAVE:INIT')

    def abort_ACPLS(self):
        self._send(':SOUR:WAVE:ABOR')

    def performACPLS(self, comp, amp, freq, offs, autorng, waverngm, dur):
        self._reset()
        self.src_wave_SIN()
        self.src_limit_VOLTS(comp)
        self.src_wave_amp_AMPS(amp)
        self.src_wave_freq_HERZ(freq)
        self.src_wave_offs_DEG(offs)
        self.src_autorange_AMPS(autorng)
        self.src_BestWaverange_BOOL(waverngm)
        self.src_wave_duration_SECS(dur)
        self.arm_init_ACPLS()


class InstClass_K2400():
    """Controller for the older sources... Should be pretty simple!"""

    def __init__(self, inst):
        # Init via rm.open_resource
        self.instrument = rm.open_resource(inst)
        self.instrument.write('*RST')

    def _close(self):
        # Close via rm.open_resource
        self._reset()
        self.instrument.close()

    def _reset(self):
        # Send reset command method.
        self._send('*RST')

    def _send(self, command: str):
        # Send command method.
        self.instrument.write(command)

    def _read(self):
        # Read method.
        return self.instrument.read()

    def _query(self, command):
        r = split('[\n\t,]', self.instrument.query(command))
        r_el = [element for element in r if element != '']
        if len(r_el) == 1:
            ans = r_el[0]
        else:
            ans = r_el
        return ans

    # ############################################## Taken from K2612B
    def meas_V(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(':SENS:FUNC "VOLT"')

    def meas_I(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(':SENS:FUNC "CURR"')

    def src_V(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(':SOUR:FUNC VOLT')

    def src_I(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(':SOUR:FUNC CURR')

    def src_range_AMPS(self, rng: str, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(f'SOUR:CURR:RANG {rng}')

    def src_range_VOLTS(self, rng: str, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(f'SOUR:VOLT:RANG {rng}')

    def src_level_AMPS(self, level: str, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(f'SOUR:CURR {level}')

    def src_level_VOLTS(self, level: str, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(f':SOUR:VOLT {level}')

    def src_limit_AMPS(self, limit: str, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self.meas_I()
            self._send(f'SENS:CURR:PROT {limit}')

    def src_limit_VOLTS(self, limit: str, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self.meas_V()
            self._send(f'SENS:VOLT:PROT {limit}')

    def sense_range_AMPS(self, rng: str, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(f':SOUR:CURR:RANG {rng}')

    def sense_range_VOLTS(self, rng: str, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(f':SOUR:VOLT:RANG {rng}')

    def sense_autorange_VOLTS(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(f':SOUR:VOLT:RANG:AUTO ON')

    def sense_autorange_AMPS(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(f':SOUR:CURR:RANG:AUTO ON')

    def outp_ON(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send(':OUTP ON')

    def outp_OFF(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            self._send('OUTP OFF')

    def get_limit_I(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            return self._query(f'SENS:CURR:PROT?')

    def get_limit_V(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            return self._query(f'SENS:VOLT:PROT?')

    def get_range_I(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            return self._query(':SOUR:CURR:RANG?')

    def get_range_V(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            return self._query(':SOUR:VOLT:RANG?')

    def get_level_I(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            return self._query('SOUR:CURR?')

    def get_level_V(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels.f You passed channel_str: {channel_str}')
        else:
            return self._query('SOUR:VOLT?')

    def get_SRC(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            return self._query(':SOUR:FUNC?')

    def measure(self, channel_str=None):
        if channel_str is not None:
            print(f'This source does not have separate channels. You passed channel_str: {channel_str}')
        else:
            return self._query(':READ?')
