# -*- coding: utf-8 -*-
"""
Álvaro Pleguezuelos Escobar

En este código se ha tenido en cuenta que los coches no pueden cruzar a la vez el puente en sentidos opuestos,
en otras palabras, los coches que cruzan solo lo pueden hacer en 1 dirección.
"""
from multiprocessing import Lock, Manager, Condition, Process, Value

import time

import random


SOUTH = 'SOUTH'

NORTH = 'NORTH'

NCARS = 40 #Numero de coches

TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s

TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s

class Monitor():
    
    def __init__(self, manager):
        
        self.mutex = Lock()
        
        self.cochesnorte = Value('i', 0) 
        
        self.cochessur = Value('i', 0) 
        
        self.d = NORTH
        
        self.acceso = Value('i', 1)
        
        self.puenteVacio= Condition(self.mutex)

    def fijardireccion(self, direccion):
        
        self.d = direccion
        
    
    
    def solicitaentrar_coche(self, direccion):
        
        self.mutex.acquire()
        
        self.fijardireccion(direccion)
        
        self.puenteVacio.wait_for(self.permiso)
        
        if (direccion == NORTH):
            
            self.cochesnorte.value += 1
            
        else:
            
            self.cochessur.value += 1
            
        self.acceso.value = 0 
        
        self.mutex.release()
        
    def permiso(self):
        
        if (self.d == NORTH):
            
            puente_vacio = (self.cochessur.value == 0)
            
        else:
            
            puente_vacio = (self.cochesnorte.value == 0)
            
        return(self.acceso.value or puente_vacio)

    def salidacoche(self, direccion):
        
        self.mutex.acquire()
        
        if (direccion == NORTH):
            
            self.cochesnorte.value -= 1
            
        else:
            
            self.cochessur.value -= 1
            
        if (self.cochesnorte.value == 0 and self.cochessur.value == 0):
            
            self.acceso.value = 1
            
        self.puenteVacio.notify_all()
        
        self.mutex.release()
    
    def __repr__(self) -> str:
        
        return f'Monitor< Coches_Norte: {self.cochesnorte.value}, Coches_Sur: {self.cochessur.value}>'


 

def retrasoCochenorte(factor = TIME_CARS_NORTH) -> None:
    
    time.sleep(factor)

def retrasoCochesur(factor = TIME_CARS_SOUTH) -> None:
    
    time.sleep(factor)

def coche(cid: int, direccion: int, monitor: Monitor)  -> None:
    
    print(f"Coche {cid} con dirección {direccion} quiere entrar en el puente.-- {monitor} --")
    
    monitor.solicitaentrar_coche(direccion)
    
    print(f"Coche {cid} con dirección {direccion} ha entrado en el puente.-- {monitor} --")
    
    if direccion==NORTH :
        
        retrasoCochenorte()
        
    else:
        
        retrasoCochesur()
        
    print(f"Coche {cid} con dirección {direccion} abandonando el puente.-- {monitor} --")
    
    monitor.salidacoche(direccion)
    
    print(f"Coche {cid} con dirección {direccion} ha salido del puente.-- {monitor} --")

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

    coches_norte.start()
    
    coches_sur.start()
    
    coches_norte.join()
    
    coches_sur.join() 
    
if __name__=='__main__':
    
    main()