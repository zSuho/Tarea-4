from abc import ABC, abstractmethod
from datetime import datetime


# --- Excepciones sencillas ---
class ErrorFJ(Exception):
    pass


class DatoMalError(ErrorFJ):
    pass


class ReservaMalError(ErrorFJ):
    pass


# --- Guardar en archivo de logs ---
def guardar_log(texto):
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("logs_fj.txt", "a", encoding="utf-8") as f:
            f.write(f"[{ahora}] {texto}\n")
    except Exception as e:
        print("Error guardando log:", e)


# --- Clase abstracta general ---
class Entidad(ABC):
    def __init__(self, codigo):
        if not codigo:
            raise DatoMalError("Falta el código.")
        self._codigo = codigo

    @property
    def codigo(self):
        return self._codigo

    @abstractmethod
    def resumen(self):
        pass


# --- Clase Cliente ---
class Cliente(Entidad):
    def __init__(self, codigo, nombre, correo):
        super().__init__(codigo)
        self.nombre = nombre
        self.correo = correo

    @property
    def correo(self):
        return self.__correo

    @correo.setter
    def correo(self, valor):
        if "@" not in valor:
            raise DatoMalError("El correo no tiene @.")
        self.__correo = valor

    def resumen(self):
        return f"Cliente {self.codigo}: {self.nombre} ({self.correo})"


# --- Clase abstracta Servicio y 3 servicios ---
class Servicio(Entidad):
    def __init__(self, codigo, nombre, precio_hora):
        super().__init__(codigo)
        if precio_hora <= 0:
            raise DatoMalError("El precio debe ser mayor que 0.")
        self.nombre = nombre
        self.precio_hora = precio_hora
        self.disponible = True

    @abstractmethod
    def calcular_base(self, horas):
        pass

    # "Sobrecarga" con parámetros opcionales (impuesto y descuento)
    def calcular_total(self, horas, impuesto=0, descuento=0):
        if horas <= 0:
            raise DatoMalError("Las horas deben ser mayores que 0.")
        if descuento < 0 or descuento > 100 or impuesto < 0:
            raise DatoMalError("Impuesto o descuento inválido.")

        base = self.calcular_base(horas)
        total = base - (base * descuento / 100)
        total = total + (total * impuesto / 100)
        return round(total, 2)


class Sala(Servicio):
    def __init__(self, codigo, nombre, precio_hora, puestos):
        super().__init__(codigo, nombre, precio_hora)
        self.puestos = puestos

    def calcular_base(self, horas):
        return self.precio_hora * horas + 10  # +10 por aseo de sala

    def resumen(self):
        estado = "Libre" if self.disponible else "Ocupada"
        return f"Sala {self.codigo} - {self.nombre} ({estado})"


class Equipo(Servicio):
    def __init__(self, codigo, nombre, precio_hora, marca):
        super().__init__(codigo, nombre, precio_hora)
        self.marca = marca

    def calcular_base(self, horas):
        return self.precio_hora * horas + 15  # +15 por seguro del equipo

    def resumen(self):
        estado = "Libre" if self.disponible else "Alquilado"
        return f"Equipo {self.codigo} - {self.nombre} [{self.marca}] ({estado})"


class Asesoria(Servicio):
    def __init__(self, codigo, nombre, precio_hora, tema):
        super().__init__(codigo, nombre, precio_hora)
        self.tema = tema

    def calcular_base(self, horas):
        total = self.precio_hora * horas
        if horas >= 4:
            total = total * 0.9  # 10% de rebaja si son 4 horas o más
        return total

    def resumen(self):
        estado = "Libre" if self.disponible else "Ocupada"
        return f"Asesoría {self.codigo} - {self.nombre} ({estado})"


# --- Clase Reserva ---
class Reserva(Entidad):
    def __init__(self, codigo, cliente, servicio, horas):
        super().__init__(codigo)
        if horas <= 0:
            raise DatoMalError("La duración debe ser mayor que 0.")
        self.cliente = cliente
        self.servicio = servicio
        self.horas = horas
        self.estado = "PENDIENTE"
        self.total = 0

    def confirmar(self, impuesto=19, descuento=0):
        if not self.servicio.disponible:
            raise ReservaMalError("Ese servicio ya está ocupado.")
        try:
            self.total = self.servicio.calcular_total(self.horas, impuesto, descuento)
        except DatoMalError as e:
            raise ReservaMalError("Error calculando el pago.") from e

        self.estado = "CONFIRMADA"
        self.servicio.disponible = False

    def cancelar(self):
        if self.estado == "CANCELADA":
            raise ReservaMalError("Ya estaba cancelada.")
        if self.estado == "CONFIRMADA":
            self.servicio.disponible = True
        self.estado = "CANCELADA"

    def resumen(self):
        return f"Reserva {self.codigo} | {self.estado} | {self.cliente.nombre} | {self.servicio.nombre} | ${self.total}"


# --- Listas del sistema ---
clientes = []
servicios = []
reservas = []


def buscar_cliente(cod):
    for c in clientes:
        if c.codigo == cod:
            return c
    return None


def buscar_servicio(cod):
    for s in servicios:
        if s.codigo == cod:
            return s
    return None


def crear_cliente(cod, nombre, correo):
    try:
        if buscar_cliente(cod):
            raise DatoMalError("Ese código de cliente ya existe.")
        c = Cliente(cod, nombre, correo)
        clientes.append(c)
    except ErrorFJ as e:
        print("Error cliente:", e)
        guardar_log(f"ERROR cliente {cod}: {e}")
    else:
        print("Guardado:", c.resumen())
        guardar_log(f"OK cliente: {c.resumen()}")


def crear_servicio(serv):
    try:
        if buscar_servicio(serv.codigo):
            raise DatoMalError("Ese código de servicio ya existe.")
        servicios.append(serv)
    except ErrorFJ as e:
        print("Error servicio:", e)
        guardar_log(f"ERROR servicio {serv.codigo}: {e}")
    else:
        print("Guardado:", serv.resumen())
        guardar_log(f"OK servicio: {serv.resumen()}")


def hacer_reserva(cod_res, cod_cli, cod_serv, horas, impuesto=19, descuento=0):
    try:
        cli = buscar_cliente(cod_cli)
        if not cli:
            raise ReservaMalError("Cliente no existe.")
        serv = buscar_servicio(cod_serv)
        if not serv:
            raise ReservaMalError("Servicio no existe.")

        r = Reserva(cod_res, cli, serv, horas)
        r.confirmar(impuesto, descuento)
        reservas.append(r)
    except ErrorFJ as e:
        print("Error reserva:", e)
        guardar_log(f"ERROR reserva {cod_res}: {e}")
    else:
        print("Reserva lista:", r.resumen())
        guardar_log(f"OK reserva: {r.resumen()}")
    finally:
        guardar_log(f"Fin proceso reserva {cod_res}")


def cancelar_una_reserva(cod_res):
    try:
        encontrada = None
        for r in reservas:
            if r.codigo == cod_res:
                encontrada = r
                break
        if not encontrada:
            raise ReservaMalError("Reserva no encontrada.")
        encontrada.cancelar()
    except ErrorFJ as e:
        print("Error cancelar:", e)
        guardar_log(f"ERROR cancelar {cod_res}: {e}")
    else:
        print("Cancelada reserva:", cod_res)
        guardar_log(f"OK cancelada reserva: {cod_res}")


# --- Pruebas (12 operaciones) ---
def main():
    guardar_log("--- Inicio programa Software FJ ---")

    # 1 y 2: clientes buenos
    crear_cliente("C1", "Sofia", "sofia@mail.com")
    crear_cliente("C2", "Mateo", "mateo@mail.com")

    # 3: cliente malo (sin @)
    crear_cliente("C3", "Pedro", "pedromail.com")

    # 4, 5 y 6: servicios buenos
    try:
        crear_servicio(Sala("S1", "Sala Norte", 30, 10))
        crear_servicio(Equipo("S2", "Portatil", 12, "HP"))
        crear_servicio(Asesoria("S3", "Ayuda BD", 45, "SQL"))
    except ErrorFJ as e:
        print("Error creando servicio:", e)
        guardar_log(f"ERROR servicio: {e}")

    # 7: servicio malo (precio negativo)
    try:
        crear_servicio(Sala("S4", "Sala Mala", -10, 5))
    except ErrorFJ as e:
        print("Error servicio malo:", e)
        guardar_log(f"ERROR servicio malo: {e}")

    # 8: reserva buena
    hacer_reserva("R1", "C1", "S1", 2, impuesto=19)

    # 9: reserva mala (sala ya ocupada)
    hacer_reserva("R2", "C2", "S1", 2)

    # 10: reserva buena con descuento
    hacer_reserva("R3", "C2", "S3", 4, impuesto=19, descuento=5)

    # 11: reserva mala (descuento mayor a 100)
    hacer_reserva("R4", "C1", "S2", 1, impuesto=19, descuento=120)

    # 12: cancelar R1 y volver a usar S1
    cancelar_una_reserva("R1")
    hacer_reserva("R5", "C2", "S1", 3, impuesto=19)

    print("\n--- RESUMEN ---")
    for c in clientes:
        print(c.resumen())
    for s in servicios:
        print(s.resumen())
    for r in reservas:
        print(r.resumen())


if __name__ == "__main__":
    main()