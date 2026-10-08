"""
arnes.py: infraestructura de medicion del reto. NO necesitas modificar este
archivo, pero SI necesitas leerlo: en tu analisis vas a defender numeros que
salen de aqui, y no puedes defender lo que no entiendes.

Que hace este modulo:
  1. Define un contrato comun (Observacion) para que tres arquitecturas muy
     distintas se puedan comparar con las mismas metricas.
  2. Corre un experimento: arquitecturas x casos x repeticiones.
  3. Resume los resultados en tablas e exporta un CSV para tu informe.

Por que hace falta un contrato comun:
Vas a comparar una cadena de codigo normal (sin LLM decidiendo) contra dos
sistemas agenticos. Sus salidas internas no se parecen en nada. Lo unico que
podemos comparar es lo observable: que respondio, que herramientas uso, cuanto
tardo, cuanto costo. Eso es Observacion.

Una decision metodologica importante:
Este arnes crea el sistema DESDE CERO en cada caso y en cada repeticion. Es a
proposito. Si reutilizaramos el mismo agente, el historial de un caso
contaminaria al siguiente y las metricas dejarian de medir el caso: mediran el
orden en que corriste los casos. La memoria entre turnos SI se prueba, pero
dentro de un mismo caso (un caso puede tener varios turnos).
"""

from __future__ import annotations

import csv
import statistics
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

# Categorias de caso que tu banco de pruebas debe cubrir. Cada una existe para
# exponer una debilidad distinta, y ninguna arquitectura gana en todas: ahi esta
# el interes del reto.
CATEGORIAS = (
    "una_tool",  # pide una sola herramienta, camino feliz
    "composicion",  # exige combinar dos o mas herramientas
    "sin_tool",  # no necesita ninguna herramienta (medir falsos positivos)
    "dato_inexistente",  # la herramienta falla o no encuentra el dato
    "ambiguo",  # redaccion imprecisa, con errores de tipeo o incompleta
    "memoria",  # varios turnos: el segundo depende del primero
)


# ===========================================================================
# 1. El contrato comun: Observacion
# ===========================================================================
@dataclass
class Observacion:
    """Lo que el arnes puede ver de una corrida, sea agentica o no.

    Campos:
        texto: la respuesta final en texto, tal como la leeria un usuario.
        herramientas: nombres DISTINTOS de herramientas que se ejecutaron.
        llamadas: total de ejecuciones de herramienta (puede ser mayor que
            len(herramientas) si una se llamo varias veces).
        estructurado: la instancia Pydantic de salida estructurada, o None.
        tokens: tokens totales consumidos (0 si la arquitectura no usa LLM).
        ciclos: iteraciones del agent loop (1 para codigo determinista).
    """

    texto: str
    herramientas: frozenset[str] = frozenset()
    llamadas: int = 0
    estructurado: object | None = None
    tokens: int = 0
    ciclos: int = 1


def observar_agente(resultado, esquema: type | None = None) -> Observacion:
    """Convierte el AgentResult de Strands en una Observacion.

    Cuidado con un detalle que sorprende a casi todo el mundo: la salida
    estructurada de Strands se implementa como una herramienta sintetica con el
    nombre de tu clase Pydantic. Si no la excluyes, tu metrica de seleccion de
    herramientas queda inflada y siempre falla la comparacion con el conjunto
    esperado. Por eso hay que pasar el esquema: para poder ignorarlo.

    Args:
        resultado: lo que devuelve agente(...) en Strands.
        esquema: la clase Pydantic usada como structured_output_model, si la hubo.
    """
    ignorar = {esquema.__name__} if esquema is not None else set()

    metricas = resultado.metrics
    usadas = {
        nombre: datos
        for nombre, datos in metricas.tool_metrics.items()
        if nombre not in ignorar
    }

    return Observacion(
        texto=str(resultado).strip(),
        herramientas=frozenset(usadas),
        llamadas=sum(datos.call_count for datos in usadas.values()),
        estructurado=getattr(resultado, "structured_output", None),
        tokens=int(metricas.accumulated_usage.get("totalTokens", 0)),
        ciclos=int(metricas.cycle_count),
    )


class RegistroManual:
    """Contador de herramientas para la arquitectura SIN agente.

    La cadena determinista llama a las herramientas como funciones normales, asi
    que nadie lleva la cuenta por ti. Envuelve cada llamada con .llamar() y al
    final construye la Observacion con .observar().

    Uso:
        registro = RegistroManual()
        stock = registro.llamar(consultar_articulo, "A-1")
        return registro.observar("Hay 12 unidades.")
    """

    def __init__(self) -> None:
        self.nombres: list[str] = []

    def llamar(self, herramienta: Callable, *args, **kwargs):
        """Ejecuta la herramienta, la anota y devuelve su resultado.

        Funciona igual con funciones normales y con funciones decoradas con
        @tool, porque Strands deja esas funciones invocables de forma directa.
        """
        nombre = getattr(herramienta, "tool_name", None) or getattr(
            herramienta, "__name__", "desconocida"
        )
        self.nombres.append(nombre)
        return herramienta(*args, **kwargs)

    def observar(
        self,
        texto: str,
        estructurado: object | None = None,
        tokens: int = 0,
    ) -> Observacion:
        """Cierra la corrida y devuelve la Observacion correspondiente."""
        return Observacion(
            texto=texto.strip(),
            herramientas=frozenset(self.nombres),
            llamadas=len(self.nombres),
            estructurado=estructurado,
            tokens=tokens,
            ciclos=1,
        )


# ===========================================================================
# 2. Casos de prueba y arquitecturas
# ===========================================================================
@dataclass(frozen=True)
class CasoDePrueba:
    """Un caso del banco de pruebas.

    Campos:
        nombre: identificador corto, aparece en las tablas.
        categoria: una de CATEGORIAS.
        turnos: uno o varios mensajes de usuario, en orden. Varios turnos
            sirven para probar memoria dentro del mismo caso.
        herramientas_esperadas: conjunto EXACTO de nombres que esperas que se
            ejecuten. Usa frozenset() vacio para los casos sin herramienta.
        verificar: funcion que recibe la Observacion y decide si la tarea se
            resolvio. Si la dejas en None, el exito no se mide (aparece n/d).
        nota: para que existe el caso. Te va a servir al redactar el analisis.
    """

    nombre: str
    categoria: str
    turnos: tuple[str, ...]
    herramientas_esperadas: frozenset[str]
    verificar: Callable[[Observacion], bool] | None = None
    nota: str = ""


@dataclass
class Arquitectura:
    """Una de las tres formas de resolver la tarea.

    Campos:
        nombre: etiqueta corta para las tablas.
        descripcion: quien toma las decisiones en este diseno.
        ejecutar: funcion que recibe los turnos y devuelve una Observacion.

    Contrato que debes respetar en ejecutar():
    crea el estado (el agente, el historial, lo que use tu diseno) DENTRO de la
    funcion, en cada llamada. Si lo creas afuera y lo reutilizas, el arnes deja
    de medir casos aislados y tus numeros no valdran nada.
    """

    nombre: str
    descripcion: str
    ejecutar: Callable[[Sequence[str]], Observacion]


@dataclass
class Medicion:
    """Una fila de resultados: una arquitectura, un caso, una repeticion."""

    arquitectura: str
    caso: str
    categoria: str
    repeticion: int
    seleccion_ok: bool
    exito: bool | None
    latencia: float
    tokens: int
    llamadas: int
    ciclos: int
    herramientas: str
    error: str = ""


# ===========================================================================
# 3. Ejecucion del experimento
# ===========================================================================
def medir(arquitectura: Arquitectura, caso: CasoDePrueba, repeticion: int) -> Medicion:
    """Corre un caso una vez y devuelve su fila de medicion.

    Si la arquitectura lanza una excepcion, NO se corta el experimento: se
    registra como error y se cuenta como fallo. Un sistema que se cae es un
    resultado valido y hay que poder medirlo.
    """
    inicio = time.perf_counter()
    try:
        observacion = arquitectura.ejecutar(caso.turnos)
    except Exception as error:  # noqa: BLE001 - queremos capturar cualquier fallo
        return Medicion(
            arquitectura=arquitectura.nombre,
            caso=caso.nombre,
            categoria=caso.categoria,
            repeticion=repeticion,
            seleccion_ok=False,
            exito=False,
            latencia=time.perf_counter() - inicio,
            tokens=0,
            llamadas=0,
            ciclos=0,
            herramientas="",
            error=f"{type(error).__name__}: {error}",
        )

    latencia = time.perf_counter() - inicio
    seleccion_ok = observacion.herramientas == caso.herramientas_esperadas

    error = ""
    if caso.verificar is None:
        exito = None
    else:
        try:
            exito = bool(caso.verificar(observacion))
        except Exception as fallo:  # noqa: BLE001
            exito = False
            error = f"verificador: {type(fallo).__name__}: {fallo}"

    return Medicion(
        arquitectura=arquitectura.nombre,
        caso=caso.nombre,
        categoria=caso.categoria,
        repeticion=repeticion,
        seleccion_ok=seleccion_ok,
        exito=exito,
        latencia=latencia,
        tokens=observacion.tokens,
        llamadas=observacion.llamadas,
        ciclos=observacion.ciclos,
        herramientas="|".join(sorted(observacion.herramientas)),
        error=error,
    )


def ejecutar_experimento(
    arquitecturas: Sequence[Arquitectura],
    casos: Sequence[CasoDePrueba],
    repeticiones: int = 3,
) -> list[Medicion]:
    """Corre todas las combinaciones y devuelve la lista de mediciones.

    Por que repetir: estos sistemas son estocasticos. Una sola corrida no
    distingue entre "mi diseno funciona" y "tuve suerte". Repetir es lo que te
    permite hablar de consistencia en lugar de anecdotas.
    """
    total = len(arquitecturas) * len(casos) * repeticiones
    turnos = sum(len(caso.turnos) for caso in casos) * len(arquitecturas) * repeticiones
    print(f"Plan del experimento: {len(arquitecturas)} arquitecturas x "
          f"{len(casos)} casos x {repeticiones} repeticiones = {total} corridas")
    print(f"Turnos de usuario en total: {turnos} (esa es la escala del gasto)")
    print("Leyenda del avance: . exito   x fallo   E excepcion   ? sin verificador\n")

    mediciones: list[Medicion] = []
    for arquitectura in arquitecturas:
        print(f"--- {arquitectura.nombre} ---")
        for caso in casos:
            marcas = []
            for repeticion in range(1, repeticiones + 1):
                medicion = medir(arquitectura, caso, repeticion)
                mediciones.append(medicion)
                if medicion.error:
                    marcas.append("E")
                elif medicion.exito is None:
                    marcas.append("?" if medicion.seleccion_ok else "x")
                else:
                    marcas.append("." if medicion.exito else "x")
            print(f"  {caso.nombre:<30}[{''.join(marcas)}]")
        print()
    return mediciones


# ===========================================================================
# 4. Resumen de resultados
# ===========================================================================
def _porcentaje(valores: Sequence[bool]) -> str:
    """Formatea una lista de booleanos como porcentaje, o n/d si esta vacia."""
    if not valores:
        return "n/d"
    return f"{100.0 * sum(1 for v in valores if v) / len(valores):.0f}%"


def _promedio(valores: Sequence[float], decimales: int = 1) -> str:
    if not valores:
        return "n/d"
    return f"{statistics.mean(valores):.{decimales}f}"


def imprimir_resumen(mediciones: Sequence[Medicion]) -> None:
    """Tabla principal: una fila por arquitectura, promediando todos los casos."""
    print("=" * 78)
    print("RESUMEN POR ARQUITECTURA")
    print("=" * 78)
    encabezado = (
        f"{'arquitectura':<24}{'seleccion':>10}{'exito':>8}{'latencia':>10}"
        f"{'tokens':>9}{'llamadas':>10}{'errores':>9}"
    )
    print(encabezado)
    print("-" * 78)

    for nombre in _nombres(mediciones):
        filas = [m for m in mediciones if m.arquitectura == nombre]
        exitos = [m.exito for m in filas if m.exito is not None]
        print(
            f"{nombre:<24}"
            f"{_porcentaje([m.seleccion_ok for m in filas]):>10}"
            f"{_porcentaje(exitos):>8}"
            f"{_promedio([m.latencia for m in filas], 2) + 's':>10}"
            f"{_promedio([m.tokens for m in filas], 0):>9}"
            f"{_promedio([m.llamadas for m in filas], 1):>10}"
            f"{sum(1 for m in filas if m.error):>9}"
        )
    print()
    print("seleccion = el conjunto de herramientas ejecutadas coincide EXACTAMENTE")
    print("            con el esperado (usar una de mas tambien cuenta como fallo).")
    print("exito     = tu verificador dio True. latencia y tokens son promedios.")
    print()


def imprimir_por_categoria(mediciones: Sequence[Medicion]) -> None:
    """Tabla cruzada: categoria de caso x arquitectura, en tasa de exito.

    Esta es la tabla que sostiene tu conclusion. El promedio general de la tabla
    anterior esconde el hallazgo interesante, porque depende de cuantos casos de
    cada tipo pusiste. Aqui se ve donde gana cada diseno.
    """
    nombres = _nombres(mediciones)
    print("=" * 78)
    print("TASA DE EXITO POR CATEGORIA DE CASO")
    print("=" * 78)
    print(f"{'categoria':<20}" + "".join(f"{n[:16]:>19}" for n in nombres))
    print("-" * 78)
    for categoria in CATEGORIAS:
        filas_categoria = [m for m in mediciones if m.categoria == categoria]
        if not filas_categoria:
            continue
        linea = f"{categoria:<20}"
        for nombre in nombres:
            exitos = [
                m.exito
                for m in filas_categoria
                if m.arquitectura == nombre and m.exito is not None
            ]
            linea += f"{_porcentaje(exitos):>19}"
        print(linea)
    print()


def imprimir_consistencia(mediciones: Sequence[Medicion], repeticiones: int) -> None:
    """Cuantos casos dieron EL MISMO resultado en todas sus repeticiones.

    Un sistema con 80% de exito y 100% de consistencia es predecible: falla
    siempre en lo mismo y puedes arreglarlo. Un sistema con 80% de exito y 50%
    de consistencia es una loteria, y es mucho peor de operar aunque el promedio
    se vea igual.
    """
    print("=" * 78)
    print(f"CONSISTENCIA ENTRE LAS {repeticiones} REPETICIONES")
    print("=" * 78)
    for nombre in _nombres(mediciones):
        filas = [m for m in mediciones if m.arquitectura == nombre]
        casos = sorted({m.caso for m in filas})
        estables = 0
        inestables: list[str] = []
        for caso in casos:
            resultados = {
                (m.seleccion_ok, m.exito) for m in filas if m.caso == caso
            }
            if len(resultados) == 1:
                estables += 1
            else:
                inestables.append(caso)
        print(f"{nombre:<24}{estables}/{len(casos)} casos estables")
        if inestables:
            print(f"{'':<24}inestables: {', '.join(inestables)}")
    print()


def imprimir_errores(mediciones: Sequence[Medicion], maximo: int = 8) -> None:
    """Muestra los primeros errores, que suelen ser lo mas informativo."""
    fallos = [m for m in mediciones if m.error]
    if not fallos:
        return
    print("=" * 78)
    print(f"ERRORES REGISTRADOS ({len(fallos)})")
    print("=" * 78)
    for medicion in fallos[:maximo]:
        print(f"[{medicion.arquitectura}/{medicion.caso}] {medicion.error}")
    if len(fallos) > maximo:
        print(f"... y {len(fallos) - maximo} mas (revisa el CSV)")
    print()


def exportar_csv(mediciones: Sequence[Medicion], ruta: str = "resultados.csv") -> None:
    """Guarda las mediciones crudas. Adjunta este archivo con tu analisis.

    Las tablas de la consola son un resumen; el CSV son los datos. Si en el
    informe afirmas algo, tiene que poder rastrearse hasta aqui.
    """
    campos = [
        "arquitectura",
        "caso",
        "categoria",
        "repeticion",
        "seleccion_ok",
        "exito",
        "latencia",
        "tokens",
        "llamadas",
        "ciclos",
        "herramientas",
        "error",
    ]
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        for medicion in mediciones:
            escritor.writerow(medicion.__dict__)
    print(f"Datos crudos guardados en {ruta} ({len(mediciones)} filas)\n")


def _nombres(mediciones: Sequence[Medicion]) -> list[str]:
    """Nombres de arquitectura en el orden en que aparecieron."""
    vistos: list[str] = []
    for medicion in mediciones:
        if medicion.arquitectura not in vistos:
            vistos.append(medicion.arquitectura)
    return vistos


def informe_completo(mediciones: Sequence[Medicion], repeticiones: int) -> None:
    """Imprime las cuatro tablas y exporta el CSV."""
    print()
    imprimir_resumen(mediciones)
    imprimir_por_categoria(mediciones)
    imprimir_consistencia(mediciones, repeticiones)
    imprimir_errores(mediciones)
    exportar_csv(mediciones)
