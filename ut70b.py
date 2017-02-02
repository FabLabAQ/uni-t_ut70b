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

import struct, sys
from time import time
import serial

ser = serial.Serial(port='/dev/ttyUSB0', baudrate=2400, bytesize=7, parity='O', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
ser.rts=False
ser.timeout=2


def parse(packet):

    try:
        rang, digit3, digit2, digit1, digit0, function, status, option1, option2, cr, lf = struct.unpack('BBBBBBBBBcc', packet)
    except struct.error:
        return None

    OL    = "OL:%s" % (status & 1 != 0)
    BATT  = "BATT:Low" if status&2 else "BATT:Ok"
    Sign  = -1 if status&4  != 0 else 1
    Judge = status&8  != 0
    VAHZ  = "VAHZ:%s" %  (option1 & 1 != 0)
    Zero  = "Zero:%s" %  (option1 & 2 != 0)
    Pmin  = "Pmin:%s" % (option1 & 4 != 0)
    Pmax  = "Pmax:%s" % (option1 & 8 != 0)
    APO   = "APO:%s"  % (option2 & 1 != 0)
    Auto  = "Range:Auto" if (option2 & 2 != 0) else "Range:Manual"
    ACDC  = "AC" if (option2 & 12 == 4) else "DC" if (option2 & 12 == 8) else None

    mode = {
        (59, False) : 'Voltage',
        (51, False) : 'Resistance',
        (53, False) : 'Continuity',
        (49, False) : 'Diode',
        (54, False) : 'Capacitance',
        (50, False) : 'Frequency',
        (50, True ) : 'RPM',
        (52, True ) : 'Temperature C',
        (52, False) : 'Temperature F',
        (61, False) : 'Current µA',
        (57, False) : 'Current mA',
        (63, False) : 'Current A',
        (62, False) : 'ADP0',
        (60, False) : 'ADP1',
        (56, False) : 'ADP2',
        (58, False) : 'ADP3',
    }[(function, Judge)]

    norm_unit, range_table = {
        'Voltage'       : ('mV', [(10, 'mV', 1), (1000, 'V', 1000), (100, 'V', 1000), (10, 'V', 1000), (1, 'V', 1000)]),
        'Current A'     : ('µA', [(10, 'A', 1000000)]),
        'Current mA'    : ('µA', [(100, 'mA', 1000), (10, 'mA', 1000)]),
        'Current µA'    : ('µA', [(10, 'µA', 1), (1, 'µA', 1)]),
        'Resistance'    : ('Ω', [(10, 'Ω', 1), (1000, 'KΩ', 1000), (100, 'KΩ', 1000), (10, 'KΩ', 1000), (1000, 'MΩ', 1000000), (100, 'MΩ', 1000000)]),
        'Frequency'     : ('Hz', [(1000, 'kHz', 1000), (100, 'kHz', 1000), (10, 'kHz', 1000), (1000, 'MHz', 1000000), (100, 'MHz', 1000000), (10, 'MHz', 1000000)]),
        'RPM'           : ('RPM', [(100, 'kRPM', 1000), (10, 'kRPM', 1000), (1000, 'MRPM', 1000000), (100, 'MRPM', 1000000), (10, 'MRPM', 1000000), (1, 'MRPM', 1000000)]),
        'Capacitance'   : ('nF', [(1000, 'nF', 1), (100, 'nF', 1), (10, 'nF', 1), (1000, 'µF', 1000), (100, 'µF', 1000), (10, 'µF', 1000), (1000, 'mF', 1000000), (100, 'mF', 1000000)]),
        'Continuity'    : ('Ω', [(10, 'Ω', 1)]),
        'Diode'         : ('mV', [(1000, 'V', 1000)]),
        'Temperature C' : ('°C', [(1, '°C', 1)]),
        'Temperature F' : ('°C', [(1, '°F', 1)]),
    }[mode]

    range_codes = [0b0110000, 0b0110001, 0b0110010, 0b0110011, 0b0110100, 0b0110101, 0b0110110, 0b0110111]
    decimal, unit, multiplier = range_table[range_codes.index(rang)]
    value = float(chr(digit3) + chr(digit2) + chr(digit1) + chr(digit0))/decimal*Sign
    norm_val = value*multiplier
    return mode, ACDC, value, unit, norm_val, norm_unit, OL, BATT, VAHZ, Zero, Pmin, Pmax, APO, Auto

#### Main loop
#
packet2=None

while True:
    packet1 = ser.readline()

    if packet1 == packet2:
        data = parse(packet1)
        if data: print ", ".join((str(x) for x in data))
        packet2 = ser.readline()
    else:
        packet2 = packet1

