from re import split  # We need to process some regular expressions so I'll need the split function from re.

from gpib_ctypes import make_default_gpib
make_default_gpib()

import pyvisa  # Controls instruments via the VISA protocol

# We create a resourcemanager instance as rm that we use throughout the pyvisa instrument control.
rm = pyvisa.ResourceManager('@py') # FOSS pyvisa driver
# rm = pyvisa.ResourceManager() # NI driver


def inst_seek():
    # This function returns a dictionary where the keys are the instrument response strings to the standard command
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
    Is based on pyvisa and needs an instrument address to initialize."""

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
            self.src_limit_VOLTS(channel_str,'20')
            self.src_range_AMPS(channel_str,'0.000001')
            self.src_level_AMPS(channel_str,'0.000000')
        else:
            print('Valid channels are "a" and "b". ')

    def beeper(self,time):
        self._send(f'beeper.beep({time},2400)')


class K2182A_controller():
    """Controller for the nanovoltmeter... Should be pretty simple!"""

    def _init(self, inst):
        # Init via rm.open_resource
        self.instrument = rm.open_resource(inst)
        self.instrument.write('*RST')

    def _close(self):
        # Close via rm.open_resource
        self._reset_()
        self.instrument.close()

    def _reset(self):
        # Send reset command method.
        self._send_('*RST')

    def _send(self, command: str):
        # Send command method.
        self.instrument.write(command)

    def _read(self):
        # Read method.
        return self.instrument.read()

    def _query(self, command=None):
        if command is str:
            self._send(command)
        return self.instrument.query('*READ?')

    def config_voltm_function(self, channel):
        self._send(':CONFIG:FUNC:VOLT' + 'channelstringofsomekind')


    def config_voltm_range(self, channel):


    def config_voltm_speed(self, channel):


    def read_voltm_singlechan(self, chann):
        return reading


    def read_voltm_douoblechan(self):
        return readingA, readingB