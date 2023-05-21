# -*- coding: utf-8 -*-
"""
Álvaro Pleguezuelos Escobar

En este código se ha tenido en cuenta que los coches no pueden cruzar a la vez el puente en sentidos opuestos,
en otras palabras, los coches que cruzan solo lo pueden hacer en 1 dirección.
"""
from multiprocessing import Lock, Manager, Condition, Process, Value
import time
import random

SOUTH = 'SOUTH'  # Dirección sur
NORTH = 'NORTH'  # Dirección norte
NCARS = 40  # Número total de coches
TIME_CARS_NORTH = 0.5  # Intervalo de tiempo entre la entrada de coches hacia el norte (en segundos)
TIME_CARS_SOUTH = 0.5  # Intervalo de tiempo entre la entrada de coches hacia el sur (en segundos)


class Monitor():
    def __init__(self, manager):
        self.mutex = Lock()  # Mutex para sincronizar el acceso a las variables compartidas
        self.cochesnorte = Value('i', 0)  # Cantidad de coches que van hacia el norte
        self.cochessur = Value('i', 0)  # Cantidad de coches que van hacia el sur
        self.d = NORTH  # Dirección actual del puente
        self.acceso = Value('i', 1)  # Indica si los coches pueden acceder al puente
        self.puenteVacio = Condition(self.mutex)  # Condición para indicar que el puente está vacío

    def fijardireccion(self, direccion):
        self.d = direccion  # Cambiar la dirección actual del puente

    def solicitaentrar_coche(self, direccion):
        self.mutex.acquire()  # Adquirir el mutex para acceder a las variables compartidas
        self.fijardireccion(direccion)  # Establecer la dirección del coche que solicita entrar al puente
        self.puenteVacio.wait_for(self.permiso)  # Esperar hasta que haya permiso para entrar al puente
        if direccion == NORTH:
            self.cochesnorte.value += 1  # Incrementar la cantidad de coches que van hacia el norte
        else:
            self.cochessur.value += 1  # Incrementar la cantidad de coches que van hacia el sur
        self.acceso.value = 0  # Indicar que los coches no tienen acceso al puente
        self.mutex.release()  # Liberar el mutex

    def permiso(self):
        if self.d == NORTH:
            puente_vacio = (self.cochessur.value == 0)  # Verificar si no hay coches en el puente en la dirección opuesta
        else:
            puente_vacio = (self.cochesnorte.value == 0)  # Verificar si no hay coches en el puente en la dirección opuesta
        return self.acceso.value or puente_vacio  # Devolver True si hay acceso al puente o si el puente está vacío

    def salidacoche(self, direccion):
        self.mutex.acquire()  # Adquirir el mutex para acceder a las variables compartidas
        if direccion == NORTH:
            self.cochesnorte.value -= 1  # Decrementar la cantidad de coches que van hacia el norte
        else:
            self.cochessur.value -= 1  # Decrementar la cantidad de coches que van hacia el sur
        if self.cochesnorte.value == 0 and self.cochessur.value == 0:
            self.acceso.value = 1  # Indicar que los coches tienen acceso al puente si no hay coches en ninguna dirección
        self.puenteVacio.notify_all()  # Notificar a todos los coches que esperan por el puente vacío
        self.mutex.release()  # Liberar el mutex

    def __repr__(self) -> str:
        return f'Monitor< Coches_Norte: {self.cochesnorte.value}, Coches_Sur: {self.cochessur.value}>'


def retrasoCochenorte(factor=TIME_CARS_NORTH) -> None:
    time.sleep(factor)  # Retrasar la ejecución del coche que va hacia el norte

def retrasoCochesur(factor=TIME_CARS_SOUTH) -> None:
    time.sleep(factor)  # Retrasar la ejecución del coche que va hacia el sur

def coche(cid: int, direccion: int, monitor: Monitor) -> None:
    print(f"Coche {cid} con dirección {direccion} quiere entrar en el puente.-- {monitor} --")
    monitor.solicitaentrar_coche(direccion)  # Solicitar permiso para entrar al puente
    print(f"Coche {cid} con dirección {direccion} ha entrado en el puente.-- {monitor} --")
    if direccion == NORTH:
        retrasoCochenorte()  # Retrasar la ejecución del coche que va hacia el norte
    else:
        retrasoCochesur()  # Retrasar la ejecución del coche que va hacia el sur
    print(f"Coche {cid} con dirección {direccion} abandonando el puente.-- {monitor} --")
    monitor.salidacoche(direccion)  # Indicar que el coche ha salido del puente
    print(f"Coche {cid} con dirección {direccion} ha salido del puente.-- {monitor} --")

def gen_coches(direccion: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=coche, args=(cid, direccion, monitor))  # Crear un proceso para un coche
        p.start()  # Iniciar el proceso
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))  # Retrasar la generación del siguiente coche

    for p in plst:
        p.join()  # Esperar a que todos los procesos de los coches terminen

def main():
    manager = Manager()
    monitor = Monitor(manager)  # Crear el monitor para controlar el acceso al puente
    coches_norte = Process(target=gen_coches, args=(NORTH, TIME_CARS_NORTH, monitor))  # Procesos para coches que van hacia el norte
    coches_sur = Process(target=gen_coches, args=(SOUTH, TIME_CARS_SOUTH, monitor))  # Procesos para coches que van hacia el sur
    coches_norte.start()  # Iniciar el proceso de los coches que van hacia el norte
    coches_sur.start()  # Iniciar el proceso de los coches que van hacia el sur
    coches_norte.join()  # Esperar a que los procesos de los coches que van hacia el norte terminen
    coches_sur.join()  # Esperar a que los procesos de los coches que van hacia el sur terminen

if __name__ == '__main__':
    main()
