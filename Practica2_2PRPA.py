# -*- coding: utf-8 -*-
"""
Álvaro Pleguezuelos Escobar

A diferencia con el código anterior, este permite el paso de peatones en ambas direcciones en el puente con la restricción de que no pueden haber peatones y coches a la vez.
Además, vamos a establecer un orden de entrada al puente.
"""
import time
import random
from multiprocessing import Lock, Value, Condition, Process, Manager

# Constantes para las direcciones
SOUTH = 'SOUTH'
NORTH = 'NORTH'

# Número de coches y peatones
NCARS = 10  # Número de coches
NPED = 10  # Número de peatones

# Tiempos de espera
TIME_CARS_NORTH = 0.5  # Un nuevo coche entra cada 0.5 segundos
TIME_CARS_SOUTH = 0.5  # Un nuevo coche entra cada 0.5 segundos
TIME_PED = 3  # Un nuevo peatón entra cada 3 segundos

class Monitor():
    def __init__(self, manager):
        self.mutex = Lock()  # Mutex para garantizar exclusión mutua
        self.peatones = Value('i', 0)  # Contador de peatones en el puente
        self.cochesnorte = Value('i', 0)  # Contador de coches en dirección norte en el puente
        self.cochessur = Value('i', 0)  # Contador de coches en dirección sur en el puente
        self.entradapeatones = Condition(self.mutex)  # Condición de entrada para peatones
        self.entradacoches_norte = Condition(self.mutex)  # Condición de entrada para coches en dirección norte
        self.entradacoches_sur = Condition(self.mutex)  # Condición de entrada para coches en dirección sur
        self.esperacoches_norte = Value('i', 0)  # Contador de coches en dirección norte esperando
        self.esperacoches_sur = Value('i', 0)  # Contador de coches en dirección sur esperando
        self.esperapeatones = Value('i', 0)  # Contador de peatones esperando
        self.turn = Value('i', 0)  # Indica el estado actual del puente:
        # 0 indica puente vacío
        # 1 indica coches dirección norte cruzando el puente
        # 2 indica coches dirección sur cruzando el puente
        # 3 indica que hay peatones cruzando el puente

    def permisocoche_norte(self):
        # Verifica si hay permiso para que un coche en dirección norte entre al puente
        # No pueden haber peatones y coches en el puente al mismo tiempo
        # Si es el turno de los coches en dirección norte o el puente está vacío, devuelve True
        condicion = (self.cochessur.value == 0 and self.peatones.value == 0) and (self.turn.value == 1) or self.turn.value == 0
        return condicion

    def permisocoche_sur(self):
        # Verifica si hay permiso para que un coche en dirección sur entre al puente
        # No pueden haber peatones y coches en el puente al mismo tiempo
        # Si es el turno de los coches en dirección sur o el puente está vacío, devuelve True
        condicion = (self.cochesnorte.value == 0 and self.peatones.value == 0) and (self.turn.value == 2) or self.turn.value == 0
        return condicion

    def solicitaentrar_coche(self, direccion):
        # Un coche solicita entrar al puente en una dirección específica
        self.mutex.acquire()
        if direccion == NORTH:
            self.esperacoches_norte.value += 1  # Incrementa el contador de coches en dirección norte esperando
            self.entradacoches_norte.wait_for(self.permisocoche_norte)  # Espera hasta que se cumpla la condición para entrar
            self.esperacoches_norte.value -= 1  # Decrementa el contador de coches en dirección norte esperando
            self.cochesnorte.value += 1  # Incrementa el contador de coches en dirección norte en el puente
            self.turn.value = 1  # Establece el turno de los coches en dirección norte
        if direccion == SOUTH:
            self.esperacoches_sur.value += 1  # Incrementa el contador de coches en dirección sur esperando
            self.entradacoches_sur.wait_for(self.permisocoche_sur)  # Espera hasta que se cumpla la condición para entrar
            self.esperacoches_sur.value -= 1  # Decrementa el contador de coches en dirección sur esperando
            self.cochessur.value += 1  # Incrementa el contador de coches en dirección sur en el puente
            self.turn.value = 2  # Establece el turno de los coches en dirección sur
        self.mutex.release()

    def salidacoche(self, direccion):
        # Un coche sale del puente en una dirección específica
        self.mutex.acquire()
        if direccion == NORTH:
            self.cochesnorte.value -= 1  # Decrementa el contador de coches en dirección norte en el puente
            if self.esperacoches_sur.value != 0:  # Si hay coches en dirección sur esperando
                self.turn.value = 2  # Establece el turno de los coches en dirección sur
        if direccion == SOUTH:
            self.cochessur.value -= 1  # Decrementa el contador de coches en dirección sur en el puente
            if self.esperacoches_norte.value != 0:  # Si hay coches en dirección norte esperando
                self.turn.value = 1  # Establece el turno de los coches en dirección norte
        self.mutex.release()

    def solicitaentrar_peaton(self):
        # Un peatón solicita entrar al puente
        self.mutex.acquire()
        self.esperapeatones.value += 1  # Incrementa el contador de peatones esperando
        self.entradapeatones.wait_for(lambda: self.peatones.value == 0)  # Espera hasta que no haya peatones en el puente
        self.esperapeatones.value -= 1  # Decrementa el contador de peatones esperando
        self.peatones.value += 1  # Incrementa el contador de peatones en el puente
        self.turn.value = 3  # Establece el turno de los peatones
        self.mutex.release()

    def salidapeaton(self):
        # Un peatón sale del puente
        self.mutex.acquire()
        self.peatones.value -= 1  # Decrementa el contador de peatones en el puente
        if self.esperapeatones.value != 0:  # Si hay peatones esperando
            self.turn.value = 3  # Establece el turno de los peatones
        elif self.esperacoches_norte.value != 0:  # Si hay coches en dirección norte esperando
            self.turn.value = 1  # Establece el turno de los coches en dirección norte
        elif self.esperacoches_sur.value != 0:  # Si hay coches en dirección sur esperando
            self.turn.value = 2  # Establece el turno de los coches en dirección sur
        else:
            self.turn.value = 0  # El puente está vacío
        self.mutex.release()


def coche(direccion, monitor):
    # Función para simular el comportamiento de un coche
    time.sleep(random.uniform(0, 1))  # Tiempo de espera antes de solicitar entrar al puente
    monitor.solicitaentrar_coche(direccion)  # Solicita entrar al puente en la dirección especificada
    print(f'Coche en dirección {direccion} entra al puente')
    time.sleep(1)  # Tiempo que tarda el coche en cruzar el puente
    monitor.salidacoche(direccion)  # Sale del puente en la dirección especificada
    print(f'Coche en dirección {direccion} sale del puente')


def peaton(monitor):
    # Función para simular el comportamiento de un peatón
    time.sleep(random.uniform(0, 1))  # Tiempo de espera antes de solicitar entrar al puente
    monitor.solicitaentrar_peaton()  # Solicita entrar al puente
    print('Peatón entra al puente')
    time.sleep(1)  # Tiempo que tarda el peatón en cruzar el puente
    monitor.salidapeaton()  # Sale del puente
    print('Peatón sale del puente')


if __name__ == '__main__':
    manager = Manager()
    monitor = Monitor(manager)

    processes = []

    # Crear procesos para los coches
    for i in range(NCARS):
        direction = SOUTH if random.random() < 0.5 else NORTH  # Determina la dirección del coche de forma aleatoria
        p = Process(target=coche, args=(direction, monitor))
        processes.append(p)

    # Crear procesos para los peatones
    for i in range(NPED):
        p = Process(target=peaton, args=(monitor,))
        processes.append(p)

    # Iniciar los procesos
    for p in processes:
        p.start()

    # Esperar a que todos los procesos terminen
    for p in processes:
        p.join()
