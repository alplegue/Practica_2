# -*- coding: utf-8 -*-
"""
Álvaro Pleguezuelos Escobar

A diferencia con el código anterior, este permite el paso de peatones en ambas direcciones en
el puente con la restricción de que no pueden haber peatones y coches a la vez.
"""
import time

import random

from multiprocessing import Lock, Value, Condition, Process, Manager

SOUTH = 'SOUTH'

NORTH = 'NORTH'

NCARS = 40 #Numero de coches

NPED = 40 #Numero de peatones

TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s

TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s

TIME_PED = 3 # a new peaton enters each 3s


class Monitor():
    
    def __init__(self, manager):
        
        self.mutex = Lock()
        
        self.peatones = Value('i', 0) 
        
        self.cochesnorte = Value('i', 0) 
        
        self.cochessur = Value('i', 0) 
        
    
        self.d = NORTH
        
        self.entradapeatones = Value('i',0)

        self.entradacoches = Value('i', 1)
        
        self.transitopeatones = Condition(self.mutex)
        
        self.transitocoches= Condition(self.mutex)
        

    def fijardireccion(self, direccion):
        
        self.d = direccion
        
    def permisocoche(self):
        
        if (self.d == NORTH):
            
            puentevacio = (self.cochessur.value == 0 and self.peatones.value == 0)
        else:
            puentevacio = (self.cochesnorte.value == 0 and self.peatones.value == 0)
            
        return(self.entradacoches.value or puentevacio or self.entradapeatones.value)
    
    def solicitaentrar_coche(self, direccion):
        
        self.mutex.acquire()
        
        self.fijardireccion(direccion)
        
        self.transitocoches.wait_for(self.permisocoche)
        
        if (direccion == NORTH):
            
            self.cochesnorte.value += 1
            
        else:
            
            self.cochessur.value += 1
            
        self.entradacoches.value = 0
        
        self.entradapeatones.value = 0 
        
        self.mutex.release()

    def salidacoche(self, direccion):
        
        self.mutex.acquire()
        
        if (direccion == NORTH):
            
            self.cochesnorte.value -= 1
            
        else:
            
            self.cochessur.value -= 1
            
        if (self.cochesnorte.value == 0 and self.cochessur.value == 0 and self.peatones.value == 0):
            
            self.entradacoches.value = 1 #No hay nadie cruzando el puente
            
            self.entradapeatones.value = 1
            
        self.transitocoches.notify_all()
        
        self.transitopeatones.notify_all()
        
        self.mutex.release()
        
    def permisopeaton(self):
        
        puentevacio = (self.cochessur.value == 0 and self.cochesnorte.value == 0)
       
        return(self.entradapeatones.value or self.entradacoches.value or puentevacio)
    
    def solicitaentrar_peaton(self):
        
        self.mutex.acquire()
        
        self.transitopeatones.wait_for(self.permisopeaton)
        
        self.peatones.value += 1
        
        self.entradapeatones.value = 0
        
        self.mutex.release()

    def salidapeaton(self):
        
        self.mutex.acquire()
        
        self.peatones.value -= 1
        
        if (self.cochesnorte.value == 0 and self.cochessur.value == 0 and self.peatones.value == 0):
            
            self.entradacoches.value = 1
            
            self.entradapeatones.value = 1
            
        self.transitopeatones.notify_all()
        
        self.transitocoches.notify_all()
        
        self.mutex.release()
    
    def __repr__(self) -> str:
        
        return f'Monitor< Coches_Norte: {self.cochesnorte.value},\
            Coches_Sur: {self.cochessur.value}, Peatones :  {self.peatones.value}> \n'
    
    
def retrasoCochenorte(factor = TIME_CARS_NORTH) -> None:
    
    time.sleep(factor)

def retrasoCochesur(factor = TIME_CARS_SOUTH) -> None:
    
    time.sleep(factor)

def retrasopeaton(factor = TIME_PED) -> None:
    
    time.sleep(factor)

def coche(cid: int, direccion: int, monitor: Monitor)  -> None:
    
    print(f"Coche {cid} con dirección {direccion} quiere entrar al puente.-- {monitor} --")
    
    monitor.solicitaentrar_coche(direccion)
    
    print(f"Coche {cid} con dirección {direccion} ha entrado en el puente.-- {monitor} --")
    
    if direccion==NORTH :
        
        retrasoCochenorte()
        
    else:
        
        retrasoCochesur()
        
    print(f"Coche {cid} con dirección {direccion} abandonando el puente.-- {monitor} --")
    
    monitor.salidacoche(direccion)
    
    print(f"Coche {cid} con dirección {direccion} ha salido del puente.-- {monitor} --")
    
def peaton(pid: int, monitor: Monitor) -> None:
    
    print(f"Peaton {pid} quiere entrar al puente.-- {monitor} --")
    
    monitor.solicitaentrar_peaton()
    
    print(f"Peaton {pid} ha entrado en el puente.-- {monitor} --")
    
    retrasopeaton()
    
    print(f"Peaton {pid} abandonando el puente.-- {monitor} --")
    
    monitor.salidapeaton()
    
    print(f"Peaton {pid} ha salido del puente.--. {monitor} --")

def gen_peaton(monitor: Monitor) -> None:
    
    pid = 0
    
    plst = []
    
    for _ in range(NPED):
        
        pid += 1
        
        p = Process(target=peaton, args=(pid, monitor))
        
        p.start()
        
        plst.append(p)
        
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        
        p.join()
        
def gen_coches(direccion: int, time_cars, monitor: Monitor) -> None:
    
    cid = 0
    
    plst = []
    
    for _ in range(NCARS):
        
        cid += 1
        
        p = Process(target=coche, args=(cid, direccion, monitor))
        
        p.start()
        
        plst.append(p)
        
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        
        p.join()

def main():
    
    manager = Manager()
    
    monitor = Monitor(manager)
    
    coches_norte = Process(target=gen_coches, args=(NORTH, TIME_CARS_NORTH, monitor))
    
    coches_sur = Process(target=gen_coches, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    
    peat = Process(target=gen_peaton, args=(monitor,))
    
    coches_norte.start()
    
    coches_sur.start()
    
    peat.start()
    
    coches_norte.join()
    
    coches_sur.join()
    
    peat.join()

if __name__ == '__main__':
    
    main()