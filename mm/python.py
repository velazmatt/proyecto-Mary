Nombre = input ("Ingrese su nombre:  ")
Edad =int (input ("Ingrese su edad: "))
if Edad >= 18:
    print("Eres mayor de edad")

else:
    print("Eres menor de edad")

print("Buenvenido", Nombre, "Tu edad es ", Edad )


#####################################################################################################

# Sumar numeros
Numero1 = int (input ("Ingrese un numero: "))
Numero2 = int (input ("Ingrese el segundo numero: "))

if Numero1 + Numero2 < 100:
    Suma = Numero1 + Numero2
print("La suma es:", Suma)
if Numero1 - Numero2 < 100:
    Resta = Numero1 - Numero2
print("La resta es:", Resta)
if Numero1 * Numero2 < 1000:
    Multiplicacion = Numero1 * Numero2
print("La multiplicacion es: " , Multiplicacion)

###############################################################################################
# tablas de multiplicar
Numero3 = int (input ("Ingrese un numero para ver su tabla de multiplicar: "))
for i in range(1, 11):
    Resultado = Numero3 * i
    print(Numero3, "*", i, "=", Resultado)
###############################################################################################################
# sumas de los numeros ingresados
SumaTotal = 0
for J in range(10): # rango de las sumas que se van a realizar.
    Numero4 = int (input ("Ingrese un numero"))
    SumaTotal += Numero4
    print("La suma es :", SumaTotal)

 ##############################################################################################################
 # 
    


