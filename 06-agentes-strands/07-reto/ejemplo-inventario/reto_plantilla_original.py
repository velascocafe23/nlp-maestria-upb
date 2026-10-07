"""
reto.py: de verdad necesitas un agente?

Pregunta de investigacion del reto:
    Para una tarea concreta, que gana y que pierde cuando dejas que un LLM
    decida el flujo, en lugar de decidirlo tu en el codigo?

Casi todo el material sobre agentes asume que el agente es la respuesta. Aqui
tienes que demostrarlo o refutarlo con datos propios. Vas a resolver LA MISMA
tarea, en el dominio que tu elijas, con tres arquitecturas:

    A1  cadena determinista   tu codigo decide el flujo; el LLM no decide nada
    A2  agente monolitico     un Agent con todas las herramientas (modulo 04)
    A3  orquestador           delega en especialistas (agent-as-tool, modulo 06)

Despues las mides con el mismo banco de casos y escribes una conclusion
defendible en ANALISIS.md. La conclusion NO esta decidida de antemano: depende
del dominio que elijas y de la mezcla de casos que armes. Un resultado del tipo
"para mi tarea el agente no se justifica" es una respuesta excelente si viene
con numeros.

Estructura de este archivo:
    PARTE 1  dominio y herramientas          (hay un ejemplo, reemplazalo)
    PARTE 2  esquema de salida estructurada  (hay un ejemplo, reemplazalo)
    PARTE 3  A1 cadena determinista          (TODO)
    PARTE 4  A2 agente monolitico            (ejemplo funcional de referencia)
    PARTE 5  A3 orquestador y especialistas  (TODO)
    PARTE 6  banco de casos de prueba        (hay dos, faltan los demas)
    main()   corre el experimento y saca las tablas

La medicion ya esta escrita en arnes.py. No la reimplementes, pero leela: en el
informe vas a defender esos numeros.

El ejemplo que viene incluido es un mini inventario. Sirve para que el archivo
corra desde el primer minuto y veas el mecanismo completo. Se espera que lo
borres y pongas tu dominio.

Ejecutar con:
    python reto.py
"""

import re
import sys

from pydantic import BaseModel, Field
from strands import Agent, tool

from arnes import (
    CATEGORIAS,
    Arquitectura,
    CasoDePrueba,
    Observacion,
    RegistroManual,
    ejecutar_experimento,
    informe_completo,
    observar_agente,
)
from comun import crear_modelo, crear_traza_herramientas

# Repeticiones por caso. Tres es el minimo para que la consistencia signifique
# algo. Si subes este numero, sube tambien el gasto de forma lineal: el arnes te
# imprime el total de corridas antes de empezar.
REPETICIONES = 3

# Ponlo en True mientras desarrollas, para ver que herramienta elige el modelo.
# Dejalo en False cuando corras el experimento completo, o la salida se vuelve
# ilegible.
MOSTRAR_TRAZA = False


def _traza():
    """Devuelve el callback de traza, o None segun MOSTRAR_TRAZA."""
    return crear_traza_herramientas() if MOSTRAR_TRAZA else None


# ===========================================================================
# PARTE 1: tu dominio y tus herramientas
#
# Requisitos:
#   - Al menos TRES herramientas con @tool.
#   - Al menos UNA debe consultar datos y poder FALLAR con un dato inexistente
#     (lanza una excepcion con un mensaje util, como consultar_articulo).
#   - Al menos UNA debe ser composicion pura (calculo determinista).
#
# Elige un dominio donde el flujo no sea siempre el mismo. Si tu tarea siempre
# se resuelve con los mismos tres pasos en el mismo orden, la cadena determinista
# va a ganar por goleada y el reto se vuelve trivial. Dominios que funcionan
# bien: soporte tecnico, consulta de reglamentos, planificacion de viajes,
# diagnostico a partir de sintomas, cotizaciones con reglas de negocio.
#
# Si tu dominio necesita datos reales, ya tienes habilitado strands-agents-tools
# (por ejemplo http_request) y ddgs para busqueda web. Ojo: una herramienta que
# sale a internet mete variabilidad que no controlas, y eso te va a ensuciar la
# consistencia. Si la usas, declaralo en las amenazas a la validez.
# ===========================================================================

# EJEMPLO DE REFERENCIA (reemplazar): mini catalogo en memoria.
CATALOGO = {
    "A-1": {"nombre": "teclado mecanico", "precio": 220000, "stock": 12},
    "B-2": {"nombre": "monitor 27 pulgadas", "precio": 980000, "stock": 0},
    "C-3": {"nombre": "mouse inalambrico", "precio": 85000, "stock": 40},
}

IVA = 0.19


@tool
def consultar_articulo(sku: str) -> dict:
    """Consulta el nombre, el precio unitario y el stock de un articulo.

    Usa esta herramienta siempre que necesites datos de un articulo del
    catalogo. Los SKU tienen el formato letra-numero, por ejemplo A-1.

    Args:
        sku: codigo del articulo, por ejemplo "A-1".
    """
    clave = sku.strip().upper()
    if clave not in CATALOGO:
        raise ValueError(
            f"El SKU {clave} no existe en el catalogo. "
            f"SKU validos: {', '.join(sorted(CATALOGO))}."
        )
    return {"sku": clave, **CATALOGO[clave]}


@tool
def calcular_total(precio_unitario: float, cantidad: int) -> float:
    """Calcula el total a pagar por una cantidad de unidades, con IVA incluido.

    Args:
        precio_unitario: precio de una unidad, sin IVA.
        cantidad: numero de unidades.
    """
    return round(precio_unitario * cantidad * (1 + IVA), 2)


@tool
def verificar_disponibilidad(sku: str, cantidad: int) -> str:
    """Indica si hay stock suficiente de un articulo para una cantidad pedida.

    Args:
        sku: codigo del articulo.
        cantidad: unidades que el cliente quiere comprar.
    """
    articulo = consultar_articulo(sku)
    if articulo["stock"] >= cantidad:
        return f"disponible: hay {articulo['stock']} unidades de {clave_legible(articulo)}"
    return (
        f"insuficiente: solo hay {articulo['stock']} unidades de "
        f"{clave_legible(articulo)} y se piden {cantidad}"
    )


def clave_legible(articulo: dict) -> str:
    """Funcion auxiliar normal (no es una herramienta, el modelo no la ve)."""
    return f"{articulo['nombre']} ({articulo['sku']})"


# TODO 1: define aqui tus propias herramientas con @tool y borra el ejemplo.
# Recuerda que el docstring es la unica documentacion que lee el modelo para
# decidir. En el analisis se te va a preguntar por esta decision de diseno.


# ===========================================================================
# PARTE 2: esquema de salida estructurada
#
# Las tres arquitecturas deben devolver lo mismo para que la comparacion sea
# justa. Un esquema Pydantic te da eso y ademas te permite escribir
# verificadores programaticos en lugar de leer texto a ojo.
#
# Detalle tecnico que vas a encontrar: Strands implementa la salida estructurada
# como una herramienta sintetica con el nombre de tu clase. Por eso a
# observar_agente() hay que pasarle el esquema, para que la excluya de la
# metrica de seleccion de herramientas.
# ===========================================================================

# EJEMPLO DE REFERENCIA (reemplazar por el esquema de tu dominio).
class Cotizacion(BaseModel):
    """Respuesta estructurada de una consulta de cotizacion."""

    resuelta: bool = Field(
        description="True si se pudo responder con datos del catalogo"
    )
    sku: str | None = Field(default=None, description="SKU consultado, si aplica")
    total: float | None = Field(
        default=None, description="Total a pagar con IVA, si se calculo"
    )
    mensaje: str = Field(description="Respuesta en una frase para el usuario")


# TODO 2: define el esquema de TU dominio.


# ===========================================================================
# PARTE 3 (TODO): A1, la cadena determinista
#
# Esta es la arquitectura de control, tu baseline. Aqui TU decides el flujo.
#
# Reglas del juego (respetalas o la comparacion pierde sentido):
#   - El LLM NO decide que herramienta llamar ni en que orden. Eso lo hace tu
#     codigo, con reglas: expresiones regulares, palabras clave, if/else.
#   - Se te permite COMO MAXIMO una llamada al modelo, y solo para redactar la
#     respuesta final en lenguaje natural. Si la usas, suma sus tokens.
#     Tambien es valido no usar el LLM en absoluto.
#   - Debes instrumentar con RegistroManual para que las herramientas se
#     cuenten igual que en las otras arquitecturas.
#
# Que hacer cuando tus reglas no entienden la pregunta: no simules exito.
# Devuelve una Observacion con un texto de rechazo honesto y sin herramientas.
# Eso no es una falla del ejercicio, es justamente el dato que vas a comparar
# contra las arquitecturas agenticas en la categoria "ambiguo".
#
# Y sobre la categoria "memoria": la funcion recibe TODOS los turnos. Decide que
# hacer con ellos. Que tu baseline no tenga estado es un hallazgo legitimo,
# siempre que lo midas y lo cuentes.
# ===========================================================================
def ejecutar_cadena_determinista(turnos) -> Observacion:
    """Resuelve la tarea con reglas fijas, sin dejar que el LLM decida."""
    registro = RegistroManual()

    # TODO 3: implementa tu cadena.
    #
    # Esqueleto del ejemplo de inventario, para que veas la forma. Sirve para el
    # camino feliz y se rompe con cualquier redaccion distinta: eso es el punto.
    texto_completo = " ".join(turnos)
    sku = re.search(r"\b([A-Za-z]-\d+)\b", texto_completo)
    cantidad = re.search(r"\b(\d+)\s*(?:unidades|articulos)\b", texto_completo)

    if sku is None:
        return registro.observar(
            "No pude identificar un SKU en la solicitud.",
            estructurado=Cotizacion(resuelta=False, mensaje="sin SKU reconocible"),
        )

    try:
        articulo = registro.llamar(consultar_articulo, sku.group(1))
    except ValueError as error:
        return registro.observar(
            str(error),
            estructurado=Cotizacion(resuelta=False, mensaje=str(error)),
        )

    # Sin cantidad explicita, la regla decide informar el precio unitario y no
    # llamar a calcular_total. Fijate en el efecto colateral: el conjunto de
    # herramientas usadas cambia segun la rama, y eso es justo lo que mide la
    # metrica de seleccion.
    if cantidad is None:
        mensaje = f"{articulo['nombre']} cuesta {articulo['precio']} por unidad."
        return registro.observar(
            mensaje,
            estructurado=Cotizacion(
                resuelta=True, sku=articulo["sku"], mensaje=mensaje
            ),
        )

    unidades = int(cantidad.group(1))
    total = registro.llamar(calcular_total, articulo["precio"], unidades)
    mensaje = f"{unidades} unidades de {articulo['nombre']} cuestan {total} con IVA."
    return registro.observar(
        mensaje,
        estructurado=Cotizacion(
            resuelta=True, sku=articulo["sku"], total=total, mensaje=mensaje
        ),
    )


# ===========================================================================
# PARTE 4: A2, el agente monolitico (EJEMPLO FUNCIONAL DE REFERENCIA)
#
# Un solo Agent con todas las herramientas. El modelo decide que usar y en que
# orden. Fijate en tres cosas, porque tus otras arquitecturas deben cumplirlas
# igual:
#   1. El agente se crea DENTRO de la funcion: un estado nuevo en cada corrida.
#   2. Se recorren todos los turnos sobre el mismo agente (asi hay memoria).
#   3. Se observa el ULTIMO resultado, porque las metricas de Strands son
#      acumuladas a nivel de agente y ya incluyen los turnos anteriores.
# ===========================================================================
def ejecutar_agente_monolitico(turnos) -> Observacion:
    """Un Agent con todas las herramientas resuelve la tarea."""
    agente = Agent(
        model=crear_modelo(),
        system_prompt=(
            "Eres un asesor de ventas de una tienda de tecnologia. Responde en "
            "espanol, en una sola frase. Usa las herramientas para obtener "
            "precios, stock y totales; nunca inventes datos del catalogo. Si un "
            "articulo no existe, dilo con claridad. Si la pregunta no necesita "
            "el catalogo, responde directamente sin usar herramientas."
        ),
        tools=[consultar_articulo, calcular_total, verificar_disponibilidad],
        callback_handler=_traza(),
    )

    resultado = None
    for turno in turnos:
        resultado = agente(turno, structured_output_model=Cotizacion)
    return observar_agente(resultado, esquema=Cotizacion)


# ===========================================================================
# PARTE 5 (TODO): A3, orquestador con especialistas
#
# Patron agente como herramienta (modulo 06): un orquestador que no tiene las
# herramientas de dominio, sino especialistas envueltos en @tool.
#
# Requisitos:
#   - Al menos DOS especialistas con responsabilidades distintas, cada uno con
#     su propio system prompt y su propio subconjunto de herramientas.
#   - Los especialistas van en silencio (callback_handler=None).
#   - El orquestador es el unico que habla con el usuario.
#
# Antes de correrlo, escribe tu prediccion en ANALISIS.md: esperas que esta
# arquitectura sea mejor, igual o peor que A2? En que metrica? Predecir antes de
# medir es lo que separa un experimento de una demo.
# ===========================================================================
def ejecutar_orquestador(turnos) -> Observacion:
    """Un orquestador delega en especialistas envueltos como herramientas."""
    # TODO 4: implementa esta arquitectura.
    #
    # Guia de implementacion:
    #   1. Define tus especialistas como funciones @tool. Dentro de cada una,
    #      crea un Agent con su system prompt, sus tools y callback_handler=None,
    #      llamalo con el texto recibido y devuelve str(respuesta).strip().
    #   2. Crea aqui el orquestador con esos especialistas como tools.
    #   3. Recorre los turnos y devuelve observar_agente(resultado, Esquema).
    #
    # Cuidado con la metrica: si envuelves tus herramientas dentro de
    # especialistas, el arnes solo vera los nombres de los ESPECIALISTAS, no los
    # de las herramientas internas. Eso hace que herramientas_esperadas sea
    # distinto para esta arquitectura. Tienes dos salidas honestas: declarar en
    # el analisis que la metrica de seleccion no es comparable entre A2 y A3, o
    # darle al orquestador tambien acceso directo a las herramientas. Elige y
    # justifica: esto es una decision de diseno experimental, no un bug.
    raise NotImplementedError("Implementa la arquitectura A3 (PARTE 5).")


# ===========================================================================
# PARTE 6: el banco de casos
#
# Debes cubrir las SEIS categorias definidas en arnes.CATEGORIAS, con al menos
# un caso cada una (ocho a diez casos en total es una buena cifra):
#
#   una_tool          camino feliz con una sola herramienta
#   composicion       exige combinar dos o mas herramientas
#   sin_tool          no necesita ninguna: mide falsos positivos
#   dato_inexistente  el dato no existe y la herramienta falla
#   ambiguo           redaccion imprecisa, incompleta o con errores de tipeo
#   memoria           dos turnos, el segundo depende del primero
#
# Cada caso lleva un verificador programatico. No escribas verificadores
# tramposos: si solo compruebas que la respuesta no este vacia, tu tasa de exito
# no mide nada y el informe se cae solo. Apoyate en el campo estructurado, que
# es mas robusto que buscar subcadenas en el texto.
# ===========================================================================

# EJEMPLO DE REFERENCIA (reemplazar por los casos de tu dominio).
CASOS = [
    CasoDePrueba(
        nombre="precio_un_articulo",
        categoria="una_tool",
        turnos=("Cuanto cuesta el articulo A-1?",),
        herramientas_esperadas=frozenset({"consultar_articulo"}),
        verificar=lambda obs: obs.estructurado is not None
        and obs.estructurado.resuelta
        and "220000" in obs.texto.replace(".", "").replace(",", ""),
        nota="Camino feliz. Si esto falla, algo esta mal en el montaje.",
    ),
    CasoDePrueba(
        nombre="sku_inexistente",
        categoria="dato_inexistente",
        turnos=("Cuanto cuesta el articulo Z-9?",),
        herramientas_esperadas=frozenset({"consultar_articulo"}),
        verificar=lambda obs: obs.estructurado is not None
        and not obs.estructurado.resuelta,
        nota="El sistema debe admitir que no existe, no inventar un precio.",
    ),
    # TODO 5: completa el banco hasta cubrir las seis categorias.
    # Faltan: composicion, sin_tool, ambiguo, memoria.
    #
    # Pista para "memoria": turnos=("Cuanto cuesta el A-1?", "Y cuantas
    # unidades hay?"). El segundo turno no menciona el SKU a proposito.
    #
    # Pista para "ambiguo": escribe la pregunta como la escribiria un usuario
    # real y apurado, sin el formato exacto del SKU.
]


def construir_arquitecturas():
    """Las tres arquitecturas que vas a comparar.

    Mientras desarrollas puedes comentar las que aun no implementaste: el arnes
    corre con las que le pases. Para la entrega deben estar las tres.
    """
    return [
        Arquitectura(
            nombre="A1 determinista",
            descripcion="El codigo decide el flujo; el LLM no decide nada.",
            ejecutar=ejecutar_cadena_determinista,
        ),
        Arquitectura(
            nombre="A2 monolitico",
            descripcion="Un Agent con todas las herramientas decide el flujo.",
            ejecutar=ejecutar_agente_monolitico,
        ),
        Arquitectura(
            nombre="A3 orquestador",
            descripcion="Un orquestador delega en especialistas (agent-as-tool).",
            ejecutar=ejecutar_orquestador,
        ),
    ]


def main():
    print("=== Reto: de verdad necesitas un agente? ===")
    print("Misma tarea, tres arquitecturas, el mismo banco de casos.\n")

    arquitecturas = construir_arquitecturas()

    cubiertas = {caso.categoria for caso in CASOS}
    faltantes = [categoria for categoria in CATEGORIAS if categoria not in cubiertas]
    if faltantes:
        print("[aviso] Tu banco de casos no cubre estas categorias: "
              + ", ".join(faltantes))
        print("        Puedes correr el experimento asi para probar el montaje,")
        print("        pero la entrega necesita las seis (ver PARTE 6).\n")

    try:
        mediciones = ejecutar_experimento(arquitecturas, CASOS, REPETICIONES)
    except KeyboardInterrupt:
        print("\n[interrumpido] No se alcanzo a generar el informe.")
        sys.exit(1)

    informe_completo(mediciones, REPETICIONES)

    print("Ahora viene la parte que vale: interpretar esto.")
    print("Abre ANALISIS.md y responde sus preguntas con estos numeros.")
    print("Una tabla sin interpretacion no es un resultado.")


if __name__ == "__main__":
    main()
