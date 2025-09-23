#contar cuantas letas tiene una palabra
def contar_letras(palabra):
    #Definir una funcion llamada contar_letras que toma una cadena palabra como entrada.
    contador = 0
    #iniciar un contador en 0 para llevar la cuenta de las letras.
    for letra in palabra:
        #Iniciar unbucle que itera sobre cada letra en la palabra.
       contador += 1
        #Inicializar el contador en 1 por cada letra en la palablra.
    return contador
    #Devolver el valor final del 1 or cada lletra en lapalabr.
print(contar_letras("Hola"))
    #llamar a la funcion contar_letras con la palabra "hola mundo" y imprimir e resultado.
