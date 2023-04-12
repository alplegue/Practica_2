# -*- coding: utf-8 -*-
"""
Álvaro Pleguezuelos Escobar

En este código a diferencia del anterior vamos a establecer un orden de entrada al puente.
"""
import time

import random

from multiprocessing import Lock, Value, Condition, Process, Manager


SOUTH = 'SOUTH'

NORTH = 'NORTH'

NCARS = 10 #Numero de coches

NPED = 10 #Numero de peatones

TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s

TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s

TIME_PED = 3 # a new peaton enters each 5s

class Monitor():
    
    def __init__(self, manager):
        
        self.mutex = Lock()
        
        self.peatones = Value('i', 0)
        
        self.cochesnorte = Value('i', 0) 
        
        self.cochessur = Value('i', 0)
        
        self.entradapeatones = Condition(self.mutex) 
        
        self.entradacoches_norte = Condition(self.mutex) 
        
        self.entradacoches_sur = Condition(self.mutex) 
        
        self.esperacoches_norte = Value('i', 0) 
        
        self.esperacoches_sur = Value('i', 0)
        
        self.esperapeatones = Value('i', 0)
        
        self.turn = Value('i', 0)
        
        # El 0  indica puente vacío
        
        # El 1 indica coches dirección norte cruzando el puente
        
        # El 2 indica coches dirección sur cruzando el puente
        
        # El 3 indica que hay peatones cruzando el puente

    def permisocoche_norte(self):
        
        condicion = (self.cochessur.value == 0 and self.peatones.value == 0) and (self.turn.value == 1)\
            or self.turn.value == 0
            
        return condicion
    
    def permisocoche_sur(self):
        
        condicion = (self.cochesnorte.value == 0 and self.peatones.value == 0) and (self.turn.value == 2)\
            or self.turn.value == 0
            
        return condicion
        
    def solicitaentrar_coche(self, direccion):
        self.mutex.acquire()
       
        if (direccion == NORTH):
            
            self.esperacoches_norte.value += 1
            
            self.entradacoches_norte.wait_for(self.permisocoche_norte)
            
            self.esperacoches_norte.value -= 1
            
            self.cochesnorte.value += 1 
            
            self.turn.value = 1 
            
            
        if (direccion == SOUTH):
            
            self.esperacoches_sur.value += 1
            
            self.entradacoches_sur.wait_for(self.permisocoche_sur)
            
            self.esperacoches_sur.value -= 1
            
            self.cochessur.value += 1
            
            self.turn.value = 2 
            
            
        self.mutex.release()

    def salidacoche(self, direccion):
        
        self.mutex.acquire()
        
        if (direccion == NORTH):
            
            self.cochesnorte.value -= 1
            
            if self.esperacoches_sur.value != 0:
                
                self.turn.value = 2
                
            elif self.esperapeatones.value != 0 :
                
                self.turn.value = 3
                
            else:
                
                self.turn.value = 0
                
            if self.cochesnorte.value == 0:
                
                self.entradacoches_sur.notify_all()
                
                self.entradapeatones.notify_all()

        if (direccion == SOUTH):
            
            self.cochessur.value -= 1
            
            if self.esperacoches_norte.value != 0 :
                
                self.turn.value = 1 
                
            elif self.esperapeatones.value != 0 :
                
                self.turn.value = 3 
                
            else:
                
                self.turn.value = 0
                
                
            if self.cochessur.value == 0:
                
                self.entradacoches_norte.notify_all()
                
                self.entradapeatones.notify_all()
                
    
        self.mutex.release()
        
    def permisopeaton(self):
        
        condicion = (self.cochessur.value == 0 and self.cochesnorte.value == 0) and (self.turn.value == 3)\
            or self.turn.value == 0
       
        return condicion
    
    def solicitaentrar_peaton(self):
        
        self.mutex.acquire()
        
        self.esperapeatones.value += 1
        
        self.entradapeatones.wait_for(self.permisopeaton)
        
        self.esperapeatones.value -= 1
        
        self.peatones.value += 1
        
        self.turn.value = 3 
        
        self.mutex.release()

    def salidapeaton(self):
        
        self.mutex.acquire()
        
        self.peatones.value -= 1
        
        if self.esperacoches_sur.value != 0 :
            
            self.turn.value = 2 
            
        elif self.esperacoches_norte.value != 0 : 
            
            self.turn.value = 1
            
        else:
            
            self.turn.value = 0

        if self.peatones.value == 0:
            
            self.entradacoches_norte.notify_all()
            
            self.entradacoches_sur.notify_all()
            
        self.mutex.release()
    
    def __repr__(self) -> str:
        
        return f'Monitor< Coches_Norte: {self.cochesnorte.value}, Coches_Norte_Waiting : {self.esperacoches_norte.value},\
            Coches_Sur: {self.cochessur.value}, Coches_Sur_Waiting : {self.esperacoches_sur.value},\
                Peatones :  {self.peatones.value}, Peatones_Waiting : {self.esperapeatones.value},> \n'
    
    

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
    
    print(f"Peaton {pid} abandonado el puente.-- {monitor} --")
    
    monitor.salidapeaton()
    
    print(f"Peaton {pid} ha salido del puente.-- {monitor} --")
    

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
