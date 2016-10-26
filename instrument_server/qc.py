#! /usr/bin/env python3
import sys
import traceback
import time
import random
import socketserver

__author__ = 'damazdejong'


class Instrument:
    def __init__(self, **kwargs):
        self.commandcounter = 0
        self.resistor = 50
        self.current = 1
        self.state = 'THEORY'

    def packet_handler(self, msg):
        msg = msg.upper()
        r = ""
        try:
            if msg.startswith('OP:'):
                self.commandcounter += 1
                r = self.ophandler(msg[3:])
            elif msg.startswith('DEBUG:'):
                self.commandcounter += 1
                r = self.debughandler(msg[6:])
            else:
                r = "ERR:CMD?"
        except:
            print("Unintended error occurred")
            print(msg)
            traceback.print_exc(file=sys.stdout)
            r = None
        return r

    def ophandler(self, command):
        if command.startswith('X') or command.startswith('Y'):
            return self.single_qubit_operation(command)
        elif command.startswith('ZERO'):
            return self.single_qubit_operation(command)
        elif command.startswith('NOP'):
            self.decohere()
            return "STAT:OP:OK"
        elif command.startswith('CNOT'):
            return self.cnot(command)
        return "ERR:OP:CMD?"

    def single_qubit_operation(self, command):
        try:
            spl = command.split(":")
            if len(spl) > 2:
                raise Exception()
            n = self.parse_qubit(spl[1])
        except Exception:
            return "ERR:ARGS?"
        print(command, str(n))
        if command.startswith("X90"):
            return "ERR:NI"
        elif command.startswith("Y90"):
            return "ERR:NI"
        elif command.startswith("X45"):
            return "ERR:NI"
        elif command.startswith("Y45"):
            return "ERR:NI"
        elif command.startswith("ZERO"):
            return "ERR:NI"
        else:
            return "ERR:OP:CMD?"
        self.decohere()
        return "STAT:OP:OK"

    def cnot(self, command):
        try:
            spl = command.split(":")
            if len(spl) > 3:
                raise Exception()
            n = self.parse_qubit(spl[1])
            m = self.parse_qubit(spl[2])
        except Exception:
            return "ERR:ARGS?"
        print(command, str(n), str(m))
        self.decohere()
        return "ERR:NI"

    def decohere(self):
        if self.state == 'EXPERIMENT':
            print('NOT IMPLEMENTED')

    def debughandler(self, command):
        if command.startswith("RHO"):
            return "ERR:NI"
        elif command.startswith("EXP"):
            return "ERR:NI"
            self.state = 'EXPERIMENT'
            return "STAT:EXPERIMENT"
        elif command.startswith("TH"):
            self.state = 'THEORY'
            return "STAT:THEORY"
        elif command.startswith("COUNTER"):
            return "STAT:CC:"+str(self.commandcounter)
        return "ERR:DEBUG:CMD?"

    def parse_qubit(self, name):
        return int(name[1:])


instrument = Instrument()

class Server(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024).strip().decode('utf8')
        response = instrument.packet_handler(data)
        if response is not None:
            self.request.send(response.encode('utf8'))
        # otherwise don't respond -- let the client hang

if __name__ == "__main__":
    HOST, PORT = "localhost", 5000

    # Create the server, binding to localhost on port 5000
    server = socketserver.TCPServer((HOST, PORT), Server, bind_and_activate=False)
    server.allow_reuse_address = True
    server.server_bind()
    server.server_activate()
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
