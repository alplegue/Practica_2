# Practica_2

En esta tarea de programación concurrente se nos plantea un problema: en un puente compartido por peatones y vehículos, solo se puede permitir que los vehículos circulen en una dirección simultáneamente. Es decir, cuando un coche va hacia el norte, no se puede permitir que ningún peatón o coche vaya hacia el sur (y viceversa). Sin embargo, los peatones pueden cruzar en cualquier dirección. Para solucionar nos hemos ayuudado de el lenguaje de programación Python y la biblioteca multiprocessing.

En la práctica 2.1, solo se permiten coches y nos creamos dos variables compartidas: una para los coches que cruzan hacia el norte (cochesN) y otra para los que se dirigen hacia el sur (cochesS). También tenemos una variable condición (puenteVacio) para aquellos coches que no puedan cruzar en ese momento debido a la presencia de otros coches en dirección opuesta. En todo momento, aseguramos la exclusión mutua con mutex.

En ambas prácticas, puede darse inanición ya que no hay un turno establecido para dar paso a los coches o a los peatones. Por ello, en la práctica 2.2, establecemos un orden de acceso mediante una variable compartida (turn). Si turn=0, no hay nadie en el puente. Si turn=1 y no hay coches hacia el sur ni peatones cruzando, se cumple la condición para permitir que los coches hacia el norte crucen (pasoCochesNorte). Si turn=2 y no hay peatones cruzando ni coches hacia el norte, se cumple la condición para permitir que los coches hacia el sur crucen (pasoCochesSur). La condición para que los peatones crucen es que no haya coches en el puente y turn=3 (pasoPeatones). Además, al salir los coches o los peatones, cambiamos el valor de la variable turn para permitir el paso a los demás coches o peatones que esperan. La exclusión mutua se garantiza con mutex.

En la memoria desarrollamos las soluciones y analizamos la inanición, exclusión mutua, dinamismo y ausencia de deadlocks en cada programa. También planteamos el invariante del monitor. Además, el código está comentado y se explica al principio de cada práctica en qué consiste.
