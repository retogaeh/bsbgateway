##############################################################################
#
#    Part of BsbGateway
#    Copyright (C) Johannes Loehnert, 2013-2015
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import sys
import time
from threading import Thread
import queue
import serial

from .virtual_serial import VirtualSerial
from .event_sources import EventSource


class SerialSource(EventSource):
    """ A source for monitoring a COM port. The COM port is
        opened when the source is started.
        see also EventSource doc.

        event data are (timestamp, data) pairs, where data is a binary
            string representing the received data, and timestamp
            is seconds since epoch as returned by time.time().

        additionaly, a write() method is offered to write to the port.

        port:
            The COM port to open. Must be recognized by the
            system.

        serial_port: SerialDevice with configured baudrate, stopbbits, party, timeouts and rtscts support
        invert_bytes: invert bytes after reading & before sending (XOR with 0xFF)
    """
    def __init__(o,
        name: str,
        serial_port: serial.Serial | VirtualSerial,
        invert_bytes = False,
    ):
        o.name = name
        o.stoppable = True
        o.serial_port = serial_port
        o._invert_bytes = invert_bytes

    def run(o, putevent_func):
        # initial reset of input / output buffers
        o.serial_port.reset_output_buffer()
        o.serial_port.reset_input_buffer()

        while True:
            # Reading 1 byte, followed by whatever is left in the
            # read buffer, as suggested by the developer of
            # PySerial.
            # read() blocks at most forever (timeout=None) until data is available
            data = o.serial_port.read(1)
            data += o.serial_port.read(o.serial_port.in_waiting)
            if o._stopflag:
                break

            if len(data) > 0:
                timestamp = time.time()
                if o._invert_bytes:
                    data = o._invertData(data)
                putevent_func(o.name, (timestamp, data))
        o.serial_port.close()

    def write(o, data):
        if o._invert_bytes:
            data = o._invertData(data)
        # clear to send
        try:
            o.serial_port.write(data)
        except serial.SerialTimeoutException as e:
            o.serial_port.reset_output_buffer()

    def _invertData(o, data: bytes):
        data = bytearray(data)
        for i in range(len(data)):
            data[i] ^= 0xff
        data = bytes(data)
        return data
