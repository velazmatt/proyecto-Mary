# Contar cuantas vocales tiene una palabra
def contar_vocales(palabra):
    # definir una funcion llamada contar_vocales que toma una cadena palabra como entrada.
    contador = 0
    # iniciar un contador en 0 para llevar la cuenta de las vocales.
    vocales = "aeiouAEIOU"
    # definir una palabre que contiene todas las vocalesd, tanto en minusculas como en mayusculas.
    for letra in palabra:
        # iniciar un bucle que itera sobre cada latra en la palabra.
        if letra in vocales:

            # comprobar s la letra actual es una voval.
            contador += 1
            # iniciar el contador en 1 por cada vocal en la palabra.
    return contador
    # devolver el valor final del contador.
print(contar_vocales("Hola Mundoo"))
# llamar a la funcion contar_vocales con la palabra "hola mundo" e imprimir el resultado.
