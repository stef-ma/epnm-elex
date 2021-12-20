from re import split  # We need to process some regular expressions so I'll need the split function from re.

from gpib_ctypes import make_default_gpib

make_default_gpib()

import pyvisa  # Controls instruments via the VISA protocol

# We create a resourcemanager instance as rm that we use throughout the pyvisa k2612B_instrument control.
rm = pyvisa.ResourceManager('@py')  # FOSS pyvisa driver


# rm = pyvisa.ResourceManager() # NI driver


def inst_seek():
    # This function returns a dictionary where the keys are the k2612B_instrument response strings to the standard command
    # "*IDN?" and the values are the addresses rm found the instruments at. The address is the most important
    # information as it is needed to init instances of Inst_Class.
    insts = dict()
    for instrument in rm.list_resources():
        try:
            inst = rm.open_resource(instrument)
            inst.write('*IDN?')
            response = inst.read()
            insts[response] = instrument

            print(f'\\n'
                  f'            Hello, I am: {response}.\n'
                  f'            My address is: {instrument}  !\\n')

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
        r = split('[\n\t]', self.instrument.query('print(' + command + ')'))
        r_el = [element for element in r if element != '']
        if len(r_el) == 1:
            ans = r_el[0]
        else:
            ans = r_el
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
            curr, volt = self._query('smu' + channel_str + '.measure.iv()')
        else:
            curr, volt = 255
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

    def meas_range_VOLTS(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.measure.autorangev=1')
        else:
            print('Valid channels are "a" and "b". ')

    def meas_range_AMPS(self, channel_str: str):
        if channel_str in ['a', 'b']:
            self._send('smu' + channel_str + '.measure.autorangei=1')
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

    def read_channel(self, chan):
        if chan == 1 or chan == 2:
            return self._query(f':SENS:CHAN {str(chan)}; :SENS:FUNC "VOLT"; :INIT:CONT ON; :SENS:DATA:FRES?')
        else:
            print('Bad Channel!')

    def read_both(self):
        return self.read_channel(1), self.read_channel(2)

    def set_range(self, chan, rng):
        if chan == 1 or chan == 2:
            self._send(f':SENS:CHAN {str(chan)}; :SENS:VOLT:RANG {format(rng, ".8E")}')
        else:
            print('Bad Channel!')

    def set_digits(self, chan, dig):
        # dig between 4 and 8
        if chan == 1 or chan == 2:
            self._send(f':SENS:CHAN {str(chan)}; :SENS:VOLT:DIG {str(dig)}')
        else:
            print('Bad Channel!')

    def set_rate(self, chan, nplc):
        # nplc between 0.1 (fast) to 5 (slow)
        if chan == 1 or chan == 2:
            self._send(f':SENS:CHAN {str(chan)}; :SENS:VOLT:NPLC {str(nplc)}')
        else:
            print('Bad Channel!')

    def set_all(self, chan, rng, dig, nplc):
        if chan == 1 or chan == 2:
            self._send(
                f':SENS:CHAN {str(chan)}; :SENS:VOLT:RANG {format(rng, ".8E")}; :SENS:VOLT:DIG {str(dig)}; :SENS:VOLT:NPLC {str(nplc)}')


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

    def sour_wave(self):
        self._send(':SOUR:WAVE:FUNC SIN;')  # can also be square etc

    def sour_wave_amp(self, amp):
        self._send(f':SOUR:WAVE:AMPL {format(amp, ".6E")};')

    def sour_wave_freq(self, freq):
        self._send(f':SOUR:WAVE:FREQ {format(freq, ".6E")};')

    def sour_wave_offs(self, offs):
        self._send(f':SOUR:WAVE:OFFS {format(offs, ".6E")};')

    def sour_wave_duration(self, duration):
        self._send(f':SOUR:WAVE:DUR:TIME {format(duration, ".6E")};')

    def sour_fixwaverange(self, boolean_switch: bool):
        if boolean_switch is True:
            self._send(':SOUR:WAVE:RANG BEST;')
        elif boolean_switch is False:
            self._send(':SOUR:WAVE:RANG FIXED;')

    def sour_comp(self, comp: str):
        self._send(f':SOUR:CURR:COMP {format(comp, ".6E")};')  # format to 1.000000E-1 VOLTS

    def sour_curr(self, curr: str):
        self._send(f':SOUR:CURR {format(curr, ".6E")};')

    def sour_rng(self, rng: str):
        self._send(f':SOUR:CURR:RANG {format(rng, ".6E")};')

    def sour_autorange(self, boolean_switch: bool):
        if boolean_switch is True:
            self._send(':SOUR:CURR:RANG:AUTO ON;')
        elif boolean_switch is False:
            self._send(':SOUR:CURR:RANG:AUTO OFF;')

    def sour_outp(self, boolean_switcher: bool):
        if boolean_switcher is True:
            self._send(':OUTP ON;')
        elif boolean_switcher is False:
            self._send(':OUTP OFF;')

    def sour_dc(self):
        self._reset()
        self._send('CLE')
        self.sour_autorange(True)
        self.sour_comp(0.1)

    def testDC(self):
        self.sour_dc()
        self.sour_rng(1e-3)
        self.sour_comp(5e-1)
        self.sour_curr(1e-5)
        self.sour_outp(True)

    def testACPLS(self):
        self._reset()
        self.sour_wave()
        self.sour_comp(1e-1)
        self.sour_wave_amp(1e-5)
        self.sour_wave_freq(987)
        self.sour_wave_offs(0)
        self.sour_autorange(True)
        self.sour_fixwaverange(True)
        self.sour_wave_duration(10)

    def arm_init_ACPLS(self):
        self._send(':SOUR:WAVE:ARM; :SOUR:WAVE:INIT')

    def abort_ACPLS(self):
        self._send(':SOUR:WAVE:ABOR')

    def performACPLS(self, comp, amp, freq, offs, autorng, waverngm, dur):
        self._reset()
        self.sour_wave()
        self.sour_comp(comp)
        self.sour_wave_amp(amp)
        self.sour_wave_freq(freq)
        self.sour_wave_offs(offs)
        self.sour_autorange(autorng)
        self.sour_fixwaverange(waverngm)
        self.sour_wave_duration(dur)
        self.ACPLS_arm_and_inti_pulse()
