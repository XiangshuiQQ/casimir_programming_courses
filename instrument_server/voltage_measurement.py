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
        self.resistor = 3.1415926535
        self.current = 1
        self.state = 1

    def packet_handler(self, msg):
        r = ""
        try:
            if msg.startswith('READ:'):
                self.commandcounter += 1
                r = self.readhandler(msg[5:])
            elif msg.startswith('SET:'):
                self.commandcounter += 1
                r = self.sethandler(msg[4:])
            else:
                r = "ERR:CMD?"
        except:
            print("Houston, We have a problem!!!")
            print(msg)
            traceback.print_exc(file=sys.stdout)
            r = None
            # todo shout!!!
        return r

    def readhandler(self, command):
        if self.state == 0:
            #time.sleep(20)
            return None
        time.sleep(0.01)
        if random.random() > 0.95:
            return "ERR:BUSY"
        elif command.startswith('VOL'):
            return "STAT:VOL:" + str(self.current * self.resistor * (
            0.8 + 0.4 * random.random())) + "V"
        elif command.startswith('RES'):
            return "STAT:RES:" + str(self.resistor) + "Ohm"
        elif command.startswith('CUR'):
            return "STAT:CUR:" + str(self.current) + "A"
        return "ERR:CMD?"

    def sethandler(self, command):
        if self.state == 0:
            #time.sleep(20)
            return None
        time.sleep(0.01)
        time.sleep(0.01)
        if random.random() > 0.95:
            return "ERR:BUSY"
        elif command.startswith("RES"):
            res = ''.join([c for c in command if c in '1234567890.'])
            r = float(res)
            for ref in [1, 10, 100, 1000]:
                if ref == r:
                    self.resistor = ref
                    return "STAT:RES:" + str(res) + "Ohm"
            return "ERR:RES?"
        elif command.startswith("CUR"):
            cur = ''.join([c for c in command if c in '-1234567890.'])
            try:
                i = float(cur)
                if abs(i) > 1:
                    return "ERR:RNG?"
                else:
                    self.current = i
                    return "STAT:CUR:" + str(i) + "A"
            except:
                return "ERR:VAL?"

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
