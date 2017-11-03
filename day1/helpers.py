import matplotlib
import matplotlib.pyplot as plt
import numpy as np

font = {'family' : 'sans',
        'size'   : 14}

matplotlib.rc('font', **font)

def plot_function(f):
    n = 100
    
    C = np.zeros(shape=(n, n))
    
    for i in range(C.shape[0]):
        for j in range(C.shape[1]):
            C[i, j] = f(j/n*10, i/n*10)
    
    fig = plt.figure(figsize=(5.4, 4))
    ax = fig.add_subplot(111, aspect='equal')
    plt.pcolormesh(np.linspace(0, 10, n), np.linspace(0, 10, n),
                   C, cmap='jet', vmin=0, vmax=5)
    plt.colorbar()
    plt.xlabel('x')
    plt.ylabel('y')
    plt.show()
