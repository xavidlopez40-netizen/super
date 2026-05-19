def area_rectangulo(base, altura):
    area = base * altura
    return area
def area_triangulo(base, altura):
    area = (base * altura) / 2
    return area
def area_circulo(radio):
    pi = 3.1416
    area = pi * (radio ** 2)
    return area
print("-areas-")
# Probar Rectángulo
base = float(input("Ingresa la base del rectángulo: "))
altu = float(input("Ingresa la altura del rectángulo: "))
print("El área del rectángulo es:", area_rectangulo(base, altu))
# Probar Triángulo
base = float(input("Ingresa la base del triángulo: "))
altu = float(input("Ingresa la altura del triángulo: "))
print("El área del triángulo es:", area_triangulo(base, altu))
# Probar Círculo
rad = float(input("Ingresa el radio del círculo: "))
print("El área del círculo es:", area_circulo(rad))
