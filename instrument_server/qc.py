#! /usr/bin/env python3
import sys
import traceback
import numpy as np
import socketserver
import qutip
from qutip import qip
from itertools import product

__author__ = 'damazdejong'


class Instrument:
    def __init__(self, **kwargs):
        self.commandcounter = 0
        self.state = 'THEORY'
        self.rho = None
        self.nqubits = 4
        self.reset()

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
            return self.reset()
        elif command.startswith('NOP'):
            self.decohere()
            return "STAT:OP:OK"
        elif command.startswith('CNOT'):
            return self.cnot(command)
        elif command.startswith('MEASURE'):
            return self.measure()
        return "ERR:OP:CMD?"

    def single_qubit_operation(self, command):
        X90 = qip.gates.rx(np.pi / 2)
        X45 = qip.gates.rx(np.pi / 4)
        Y90 = qip.gates.ry(np.pi / 2)
        Y45 = qip.gates.ry(np.pi / 4)
        I = qutip.qeye(2)
        Ilist = [I]*self.nqubits
        try:
            spl = command.split(":")
            if len(spl) > 2:
                raise Exception()
            n = self.parse_qubit(spl[1])
            if n >= self.nqubits:
                raise Exception()
        except Exception:
            return "ERR:ARGS?"
        print(command, str(n))
        if command.startswith("X90"):
            Ilist[n] = X90
        elif command.startswith("Y90"):
            Ilist[n] = Y90
        elif command.startswith("X45"):
            Ilist[n] = X45
        elif command.startswith("Y45"):
            Ilist[n] = Y45
        else:
            return "ERR:OP:CMD?"
        # applying gate
        U = qutip.tensor(Ilist)
        self.rho = U * self.rho * U.dag()
        self.decohere()
        return "STAT:OP:OK"

    def cnot(self, command):
        try:
            spl = command.split(":")
            if len(spl) > 3:
                raise Exception()
            n = self.parse_qubit(spl[1])
            m = self.parse_qubit(spl[2])
            if n >= self.nqubits or m >= self.nqubits:
                raise Exception
        except Exception:
            return "ERR:ARGS?"
        cnot = qutip.qip.cnot(N=self.nqubits, control=n, target=m)
        self.rho = cnot * self.rho * cnot.dag()
        print(command, str(n), str(m))
        self.decohere()
        return "ERR:NI"

    def decohere(self):
        if self.state == 'EXPERIMENT':
            print('NOT IMPLEMENTED')

    def measure(self, debug=False):
        r = self.measure_z_basis(self.rho)
        r = [str(e) for e in r]
        if not debug:
            self.reset()
        return "STAT:"+":".join(r)

    def reset(self):
        # initial state
        psi0 = qutip.basis(2, 0)
        rho0 = qutip.ket2dm(psi0)
        self.rho = qutip.tensor([rho0] * self.nqubits)

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
        elif command.startswith('measure'):
            return self.measure(debug=True)
        return "ERR:DEBUG:CMD?"

    def parse_qubit(self, name):
        return int(name[1:])

    def get_state(self, state_tuple):
        """
        state_tuple: tuple of zeros and ones (e.g., (0,0,1,1,0)).
            returns a qutip Qobj that contains that statevector.
        """
        psi0 = qutip.basis(2, 0)
        psi1 = qutip.basis(2, 1)
        states = []
        for i in state_tuple:
            if i == 0:
                states += [psi0]
            elif i == 1:
                states += [psi1]
            else:
                raise ValueError()
        combined_psi = qutip.tensor(states)
        return combined_psi

    def measure_z_basis(self, rho):
        probs = get_z_basis_msmst_probs(rho)
        random_float = np.random.rand()
        c_probs = np.cumsum(probs)
        msmt_outcomes = list(product([0, 1], repeat=len(c_probs)))
        for i, cp in enumerate(c_probs):
            if cp > random_float:
                return msmt_outcomes[i]


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
