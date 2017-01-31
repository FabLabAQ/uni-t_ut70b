# -*- coding: utf-8 -*-

# Library and command line tool that parses RAW data from
# UNI-T UT70B multimeter
#
# Copyright (C) 2017 Fabio Di Bernardini and www.fablaquila.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import struct
from time import time
import serial

ser = serial.Serial(port='/dev/ttyUSB0', baudrate=2400, bytesize=7, parity='O', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
ser.rts=False
ser.timeout=5

value=mode=unit=None

def parse(packet):

    rang, digit3, digit2, digit1, digit0, function, status, option1, option2, cr, lf = struct.unpack('BBBBBBBBBcc', packet)

    OL    = status&1  != 0
    BATT  = status&2  != 0
    Sign  = -1 if status&4  != 0 else 1
    Judge = status&8  != 0
    VAHZ  = option1&1 != 0
    Zero  = option1&2 != 0
    Pmin  = option1&4 != 0
    Pmax  = option1&8 != 0
    APO   = option1&1 != 0
    Auto  = option1&2 != 0
    AC    = option1&4 != 0
    DC    = option1&8 != 0

    mode = {
        (59, False) : 'Voltage',
        (51, False) : 'Resistance',
        (53, False) : 'Continuity',
        (49, False) : 'Diode',
        (54, False) : 'Capacitance',
        (50, False) : 'Frequency',
        (50, True ) : 'RPM',
        (52, True ) : 'Temperature (C)',
        (52, False) : 'Temperature (F)',
        (61, False) : 'Current µA',
        (57, False) : 'Current mA',
        (63, False) : 'Current A',
        (62, False) : 'ADP0',
        (60, False) : 'ADP1',
        (56, False) : 'ADP2',
        (58, False) : 'ADP3',
    }[(function, Judge)]

    # try:
    range_table = {
        'Voltage'         : [(10, 'mV'), (1000, 'V'), (100, 'V'), (10, 'V'), (1, 'V')],
        'Current A'       : [(10, 'A')],
        'Current mA'      : [(100, 'mA'), (10, 'mA')],
        'Current µA'      : [(10, 'µA'), (1, 'µA')],
        'Resistance'      : [(10, 'Ohm'), (1000, 'KOhm'), (100, 'KOhm'), (10, 'KOhm'), (1000, 'MOhm'), (100, 'MOhm')],
        'Frequency'       : [(1000, 'kHz'), (100, 'kHz'), (10, 'kHz'), (1000, 'MHz'), (100, 'MHz'), (10, 'MHz')],
        'RPM'             : [(100, 'kRPM'), (10, 'kRPM'), (1000, 'MRPM'), (100, 'MRPM'), (10, 'MRPM'), (1, 'MHz')],
        'Capacitance'     : [(1000, 'nF'), (100, 'nF'), (10, 'nF'), (1000, 'µF'), (100, 'µF'), (10, 'µF'), (1000, 'mF'), (100, 'mF')],
        'Continuity'      : [(10, 'Ω')],
        'Diode'           : [(1, 'V')],
        'Temperature (C)' : [(1, 'C')],
        'Temperature (F)' : [(1, 'F')],
    }[mode]

    # except KeyError:
    range_codes = [0b0110000, 0b0110001, 0b0110010, 0b0110011, 0b0110100, 0b0110101, 0b0110110, 0b0110111]
    multiplier, unit = range_table[range_codes.index(rang)]
    value = float(chr(digit3) + chr(digit2) + chr(digit1) + chr(digit0))/multiplier*Sign
    return mode, value, unit, OL, BATT, Judge, VAHZ, Zero, Pmin, Pmax, APO, Auto, AC, DC

#### Main loop
#
packet2=None

while True:
    packet1 = ser.readline()

    if packet1 == packet2:
        print "mode, value, unit, OL, BATT, Judge, VAHZ, Zero, Pmin, Pmax, APO, Auto, AC, DC"
        print ", ".join((str(x) for x in parse(packet1)))
        packet2 = ser.readline()

    else:

        packet2 = packet1

