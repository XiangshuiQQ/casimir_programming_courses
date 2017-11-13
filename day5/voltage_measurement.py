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
        self.current = 0
        self.state = 1

    def packet_handler(self, msg):
        msg = msg.upper()
        r = ""
        try:
            if msg.startswith('SENS'):
                self.commandcounter += 1
                msg = msg.split(':', 1)[-1]
                r = self.sensehandler(msg)
            elif msg.startswith('SOUR'):
                msg = msg.split(':', 1)[-1]
                self.commandcounter += 1
                r = self.sourcehandler(msg)
            elif msg.startswith('CURR'):  # SOURCE is optional
                msg = 'SOUR:'+msg
                return self.packet_handler(msg)
            elif msg.startswith('READ?'):
                return self.packet_handler('SENS:DATA?')
            elif msg.startswith('MEAS') and '?' in msg:
                return self.packet_handler('SENS:DATA?')
            elif msg.startswith('FETC') and '?' in msg:
                return self.packet_handler('SENS:DATA?')
            else:
                r = "ERR:CMD?"
        except:
            print("Houston, We have a problem!!!")
            print(msg)
            traceback.print_exc(file=sys.stdout)
            r = None
            # todo shout!!!
        return r

    def sensehandler(self, command):
        if self.state == 0:
            #time.sleep(20)
            return None
        time.sleep(0.01)
        if random.random() > 0.95:
            return "ERR:BUSY"
        elif command.startswith('DATA') and '?' in command:
            return "SENS:DATA " + str(self.current * self.resistor * (
            0.8 + 0.4 * random.random())) + "V"
        elif command.startswith('RES'):
            return "STAT:RES " + str(self.resistor) + "Ohm"
        #elif command.startswith('CUR'):
        #    return "STAT:CUR:" + str(self.current) + "A"
        return "ERR:CMD?"

    def sourcehandler(self, msg):
        if self.state == 0:
            #time.sleep(20)
            return None
        if random.random() > 0.95:
            return "ERR:BUSY"
        if not msg.startswith('CURR'):
            return "ERR:SOUR?"

        if ':' not in msg:
            msg = 'LEV' + msg
        else:
            msg = msg.split(':', 1)[-1]
        time.sleep(0.01)
        time.sleep(0.01)

        if msg.startswith('MODE'):
            if '?' in msg:
                return 'SOUR:CURR:MODE:FIX'
            else:
                msg = msg.split(':', 1)[-1]
                if msg.startswith('FIX'):
                    return 'SOUR:CURR:MODE:FIX'
                else:
                    return "ERR:MODE?"
        elif msg.startswith('LEV'):
            if '?' in msg:
                return 'SOUR:CURR:LEV ' + str(self.current) + "A"
            cur = ''.join([c for c in msg if c in '-1234567890.'])
            try:
                i = float(cur)
                if abs(i) > 1:
                    return "ERR:RNG?"
                else:
                    self.current = i
                    return 'SOUR:CURR:LEV ' + str(i) + "A"
            except:
                return "ERR:VAL?"
        elif msg.startswith("RES"):
            res = ''.join([c for c in msg if c in '1234567890.'])
            r = float(res)
            for ref in [1, 10, 100, 1000]:
                if ref == r:
                    self.resistor = ref
                    return "STAT:RES " + str(res) + "Ohm"
            return "ERR:RES?"
        return "ERR:CMD?"


instrument = Instrument()

class Server(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024).strip().decode('utf8')
        response = instrument.packet_handler(data)
        if response is not None:
            self.request.send(response.encode('utf8'))
        # otherwise don't respond -- let the client hang

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 5000

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
