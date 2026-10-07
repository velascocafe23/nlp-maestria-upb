"""
reto.py: de verdad necesitas un agente?

Dominio elegido: asistente de reservas para apartamentos turisticos en Armenia,
Quindio (alquiler por noches, estilo Airbnb). Un huesped potencial escribe por
chat y pide cosas distintas: capacidad y precio de un apartamento, si esta libre
en unas fechas, cuanto le sale una estadia, cual apartamento le sirve para su
grupo, o cual es la politica de mascotas o de cancelacion. El flujo NO es fijo:
segun lo que pida hay que consultar una, dos o ninguna herramienta, y en un
orden que depende de la pregunta.

Las tres arquitecturas que se comparan (ver README.md y ANALISIS.md):

    A1  cadena determinista   reglas en codigo; cero llamadas al LLM
    A2  agente monolitico     un Agent con las cinco herramientas
    A3  orquestador           delega en tres especialistas (agent-as-tool)

Los datos del catalogo son ILUSTRATIVOS: codigos, tarifas y calendario estan en
memoria para que el experimento sea reproducible y no dependa de internet.

Ejecutar con:
    python reto.py
"""

import re
import sys
import unicodedata
from datetime import date, timedelta

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

# Tres es el minimo para que la consistencia signifique algo (ver README).
REPETICIONES = 3

# True mientras desarrollas, False para la corrida que se reporta.
MOSTRAR_TRAZA = False


def _traza():
    """Devuelve el callback de traza, o None segun MOSTRAR_TRAZA."""
    return crear_traza_herramientas() if MOSTRAR_TRAZA else None


# ===========================================================================
# PARTE 1: dominio y herramientas
# ===========================================================================

# Catalogo ilustrativo (tarifas en pesos colombianos por noche, sin aseo).
APARTAMENTOS = {
    "APT-1": {
        "nombre": "Estudio Cafetero",
        "capacidad": 2,
        "tarifa_noche": 150000,
        "minimo_noches": 2,
        "descripcion": "estudio para pareja, balcon con vista a los cafetales, wifi y cocina",
    },
    "APT-2": {
        "nombre": "Apartamento Familiar",
        "capacidad": 4,
        "tarifa_noche": 230000,
        "minimo_noches": 2,
        "descripcion": "dos habitaciones, parqueadero cubierto, piscina del conjunto",
    },
    "APT-3": {
        "nombre": "Apartamento Panoramico",
        "capacidad": 6,
        "tarifa_noche": 320000,
        "minimo_noches": 3,
        "descripcion": "tres habitaciones en piso alto, vista a la cordillera, ideal para grupos",
    },
}

TARIFA_ASEO = 60000          # cargo unico por estadia
DESCUENTO_SEMANA = 0.10      # 10% si la estadia es de 7 noches o mas

# Calendario ilustrativo de noches ya reservadas (fecha de la noche, ISO).
OCUPADO = {
    "APT-1": {"2026-12-24", "2026-12-25", "2026-12-26", "2026-12-31", "2027-01-01"},
    "APT-2": {"2026-11-10", "2026-11-11", "2026-12-20", "2026-12-21", "2026-12-22"},
    "APT-3": {"2026-12-28", "2026-12-29", "2026-12-30", "2026-12-31"},
}

POLITICAS = {
    "mascotas": (
        "Se aceptan mascotas pequenas, de hasta 10 kg, con un cargo adicional "
        "unico de 40000 pesos por estadia. No se aceptan en el APT-3."
    ),
    "cancelacion": (
        "Cancelacion gratuita hasta 5 dias antes del check-in. Despues de eso "
        "se cobra la primera noche."
    ),
    "check_in": (
        "Check-in desde las 3 de la tarde y check-out hasta las 11 de la manana. "
        "La entrega de llaves es con codigo de acceso, no hace falta coordinar hora."
    ),
    "parqueadero": (
        "Parqueadero cubierto incluido para un vehiculo en el APT-2 y el APT-3. "
        "El APT-1 no tiene parqueadero propio; hay uno publico a una cuadra."
    ),
}


@tool
def consultar_apartamento(codigo: str) -> dict:
    """Consulta los datos de un apartamento del catalogo: nombre, capacidad
    maxima de huespedes, tarifa por noche, minimo de noches y descripcion.

    Usa esta herramienta cuando el huesped pregunte por un apartamento concreto
    (capacidad, precio por noche, que tiene). Los codigos tienen el formato
    APT-numero, por ejemplo APT-2.

    Args:
        codigo: codigo del apartamento, por ejemplo "APT-2".
    """
    clave = codigo.strip().upper().replace(" ", "")
    if clave not in APARTAMENTOS:
        raise ValueError(
            f"El apartamento {clave} no existe. Codigos validos: "
            f"{', '.join(sorted(APARTAMENTOS))}."
        )
    return {"codigo": clave, **APARTAMENTOS[clave]}


@tool
def buscar_por_capacidad(huespedes: int) -> list:
    """Devuelve los apartamentos cuya capacidad maxima alcanza para un numero
    de huespedes, con su codigo, nombre, capacidad y tarifa por noche.

    Usa esta herramienta cuando el huesped diga cuantas personas son pero NO
    diga que apartamento quiere, para recomendarle cual le sirve.

    Args:
        huespedes: numero de personas que se van a hospedar.
    """
    opciones = [
        {"codigo": c, "nombre": d["nombre"], "capacidad": d["capacidad"],
         "tarifa_noche": d["tarifa_noche"]}
        for c, d in sorted(APARTAMENTOS.items())
        if d["capacidad"] >= huespedes
    ]
    if not opciones:
        raise ValueError(
            f"Ningun apartamento recibe {huespedes} huespedes; la capacidad "
            f"maxima es {max(d['capacidad'] for d in APARTAMENTOS.values())}."
        )
    return opciones


@tool
def verificar_disponibilidad(codigo: str, fecha_entrada: str, noches: int) -> dict:
    """Indica si un apartamento esta libre para una estadia que empieza en una
    fecha y dura cierto numero de noches. Devuelve si esta disponible y, si no,
    que noches ya estan ocupadas.

    Usa esta herramienta siempre que el huesped mencione fechas concretas de
    viaje. No sirve para calcular precios: para eso esta cotizar_estadia.

    Args:
        codigo: codigo del apartamento, por ejemplo "APT-1".
        fecha_entrada: fecha de llegada en formato AAAA-MM-DD, por ejemplo "2026-12-20".
        noches: numero de noches de la estadia.
    """
    apto = consultar_apartamento(codigo)
    inicio = date.fromisoformat(fecha_entrada.strip())
    noches_pedidas = {(inicio + timedelta(days=i)).isoformat() for i in range(int(noches))}
    ocupadas = sorted(noches_pedidas & OCUPADO.get(apto["codigo"], set()))
    return {
        "codigo": apto["codigo"],
        "fecha_entrada": inicio.isoformat(),
        "noches": int(noches),
        "disponible": not ocupadas,
        "noches_ocupadas": ocupadas,
    }


@tool
def cotizar_estadia(codigo: str, noches: int, huespedes: int) -> dict:
    """Calcula el precio total de una estadia: tarifa por noche multiplicada por
    las noches, mas el cargo unico de aseo, con 10% de descuento sobre las
    noches si la estadia es de 7 noches o mas. Valida que el grupo quepa y que
    se cumpla el minimo de noches.

    Usa esta herramienta cuando el huesped pregunte cuanto le sale, cuanto
    cuesta o cuanto vale una estadia de varias noches.

    Args:
        codigo: codigo del apartamento, por ejemplo "APT-3".
        noches: numero de noches de la estadia.
        huespedes: numero de personas que se van a hospedar.
    """
    apto = consultar_apartamento(codigo)
    noches, huespedes = int(noches), int(huespedes)
    if huespedes > apto["capacidad"]:
        raise ValueError(
            f"El {apto['codigo']} recibe maximo {apto['capacidad']} huespedes y se "
            f"piden {huespedes}. Usa buscar_por_capacidad para encontrar uno que sirva."
        )
    if noches < apto["minimo_noches"]:
        raise ValueError(
            f"El {apto['codigo']} exige un minimo de {apto['minimo_noches']} noches."
        )
    subtotal = apto["tarifa_noche"] * noches
    descuento = round(subtotal * DESCUENTO_SEMANA) if noches >= 7 else 0
    total = subtotal - descuento + TARIFA_ASEO
    return {
        "codigo": apto["codigo"],
        "noches": noches,
        "huespedes": huespedes,
        "subtotal_noches": subtotal,
        "descuento": descuento,
        "aseo": TARIFA_ASEO,
        "total": total,
    }


@tool
def consultar_politica(tema: str) -> str:
    """Devuelve la politica de la casa sobre un tema. Temas disponibles:
    "mascotas", "cancelacion", "check_in" (horarios de entrada y salida) y
    "parqueadero".

    Usa esta herramienta cuando el huesped pregunte por reglas o condiciones
    (mascotas, cancelar, horas de entrada o salida, donde parquear). Si el tema
    no esta en la lista, la herramienta falla: no inventes una politica.

    Args:
        tema: uno de "mascotas", "cancelacion", "check_in", "parqueadero".
    """
    clave = _normalizar(tema).replace("-", "_").replace(" ", "_")
    alias = {"checkin": "check_in", "check_out": "check_in", "checkout": "check_in",
             "entrada": "check_in", "salida": "check_in", "cancelaciones": "cancelacion",
             "cancelar": "cancelacion", "mascota": "mascotas", "parqueo": "parqueadero",
             "parking": "parqueadero"}
    clave = alias.get(clave, clave)
    if clave not in POLITICAS:
        raise ValueError(
            f"No hay una politica registrada sobre '{tema}'. Temas disponibles: "
            f"{', '.join(sorted(POLITICAS))}."
        )
    return POLITICAS[clave]


HERRAMIENTAS = [
    consultar_apartamento,
    buscar_por_capacidad,
    verificar_disponibilidad,
    cotizar_estadia,
    consultar_politica,
]


def _normalizar(texto: str) -> str:
    """Minusculas y sin tildes, para que las reglas de A1 no dependan de la ortografia."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower().strip()


# ===========================================================================
# PARTE 2: esquema de salida estructurada (comun a las tres arquitecturas)
# ===========================================================================
class RespuestaReserva(BaseModel):
    """Respuesta estructurada del asistente de reservas."""

    resuelta: bool = Field(
        description="True si la pregunta se respondio con datos reales (catalogo, "
        "calendario o politicas) o si no necesitaba datos; False si no se pudo "
        "responder, el dato no existe o faltan datos del huesped."
    )
    codigo: str | None = Field(
        default=None, description="Codigo del apartamento al que se refiere la respuesta, si aplica"
    )
    total: float | None = Field(
        default=None, description="Total cotizado en pesos (aseo incluido), si se calculo"
    )
    disponible: bool | None = Field(
        default=None, description="Si se consulto el calendario, True si estaba libre"
    )
    mensaje: str = Field(description="Respuesta para el huesped, en una o dos frases")


SYSTEM_PROMPT_BASE = (
    "Eres el asistente de reservas de tres apartamentos turisticos en Armenia, "
    "Quindio. Responde en espanol, en una o dos frases, con tono amable. Usa las "
    "herramientas para obtener datos de apartamentos, disponibilidad, precios y "
    "politicas; nunca inventes tarifas, fechas ni reglas. Si un apartamento o una "
    "politica no existe, dilo con claridad. Si para cotizar te falta un dato "
    "(fechas, noches o numero de personas), da el dato que si tengas y pide lo que "
    "falta. Si la pregunta no necesita datos de la casa, responde directamente "
    "sin usar herramientas."
)


# ===========================================================================
# PARTE 3: A1, la cadena determinista (sin LLM)
# ===========================================================================
PALABRAS_NUMERO = {"una": 1, "un": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
                   "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10}

TEMAS_POLITICA = {
    "mascotas": ("mascota", "perro", "gato"),
    "cancelacion": ("cancel",),
    "check_in": ("check", "hora de entrada", "hora de salida", "entregan las llaves"),
    "parqueadero": ("parquead", "parqueo", "parking", "carro"),
}

SALUDOS = ("gracias", "chao", "hasta luego", "feliz tarde", "feliz dia", "buen dia",
           "nos vemos", "ya con eso")


def _numero(patron: str, texto: str):
    """Extrae un entero (digitos o palabra) que precede a un patron, o None."""
    m = re.search(r"\b(\d+|" + "|".join(PALABRAS_NUMERO) + r")\s*" + patron, texto)
    if not m:
        return None
    v = m.group(1)
    return int(v) if v.isdigit() else PALABRAS_NUMERO[v]


def ejecutar_cadena_determinista(turnos) -> Observacion:
    """Resuelve la tarea con reglas fijas. El LLM no participa (0 tokens)."""
    registro = RegistroManual()
    # Decision explicita sobre la memoria: concatenamos los turnos. Es la forma
    # mas simple de "recordar", y el analisis discute donde alcanza y donde no.
    texto = _normalizar(" ".join(turnos))

    def rechazar(motivo):
        return registro.observar(
            motivo, estructurado=RespuestaReserva(resuelta=False, mensaje=motivo)
        )

    # --- Regla 0: extraccion de datos con expresiones regulares ---------------
    m_codigo = re.search(r"\bapt\s*-?\s*(\d)\b", texto)
    codigo = f"APT-{m_codigo.group(1)}" if m_codigo else None
    m_fecha = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", texto)
    fecha = m_fecha.group(1) if m_fecha else None
    noches = _numero(r"noches?\b", texto)
    if noches is None and re.search(r"\b(una|1)\s+semana\b", texto):
        noches = 7
    huespedes = _numero(r"(personas?|huespedes?|adultos?|pax)\b", texto)
    if huespedes is None:
        m = re.search(r"\bsomos\s+(\d+)\b", texto)
        huespedes = int(m.group(1)) if m else None
    temas = [t for t, claves in TEMAS_POLITICA.items() if any(k in texto for k in claves)]

    partes = []
    estructura = {}

    # --- Regla 1: politicas (se responden aunque ademas haya una reserva) -----
    for tema in temas:
        try:
            partes.append(registro.llamar(consultar_politica, tema))
        except ValueError as e:
            return rechazar(str(e))

    # --- Regla 2: hay un codigo de apartamento --------------------------------
    if codigo:
        try:
            if fecha and noches:
                disp = registro.llamar(verificar_disponibilidad, codigo, fecha, noches)
                estructura["disponible"] = disp["disponible"]
                partes.append(
                    f"El {codigo} {'esta disponible' if disp['disponible'] else 'NO esta disponible'} "
                    f"desde el {fecha} por {noches} noches"
                    + (f" (ocupado: {', '.join(disp['noches_ocupadas'])})." if disp["noches_ocupadas"] else ".")
                )
            if noches:
                cot = registro.llamar(cotizar_estadia, codigo, noches, huespedes or 1)
                estructura["total"] = cot["total"]
                partes.append(
                    f"{noches} noches para {cot['huespedes']} persona(s) en el {codigo} "
                    f"cuestan {cot['total']} pesos, aseo incluido"
                    + (f" y con descuento de {cot['descuento']}." if cot["descuento"] else ".")
                )
            if not noches:
                apto = registro.llamar(consultar_apartamento, codigo)
                partes.append(
                    f"El {codigo} ({apto['nombre']}) recibe hasta {apto['capacidad']} personas "
                    f"y cuesta {apto['tarifa_noche']} pesos por noche; {apto['descripcion']}."
                )
        except (ValueError, KeyError) as e:
            return rechazar(str(e))
        mensaje = " ".join(partes)
        return registro.observar(
            mensaje,
            estructurado=RespuestaReserva(resuelta=True, codigo=codigo, mensaje=mensaje, **estructura),
        )

    # --- Regla 3: no hay codigo pero si numero de personas --------------------
    if huespedes:
        try:
            opciones = registro.llamar(buscar_por_capacidad, huespedes)
            elegido = opciones[0]
            partes.append(
                f"Para {huespedes} personas sirve el {elegido['codigo']} ({elegido['nombre']}), "
                f"a {elegido['tarifa_noche']} pesos por noche."
            )
            if noches:
                cot = registro.llamar(cotizar_estadia, elegido["codigo"], noches, huespedes)
                estructura["total"] = cot["total"]
                partes.append(f"{noches} noches salen en {cot['total']} pesos, aseo incluido.")
        except ValueError as e:
            return rechazar(str(e))
        mensaje = " ".join(partes)
        return registro.observar(
            mensaje,
            estructurado=RespuestaReserva(resuelta=True, codigo=elegido["codigo"], mensaje=mensaje, **estructura),
        )

    # --- Regla 4: solo politicas ----------------------------------------------
    if partes:
        mensaje = " ".join(partes)
        return registro.observar(mensaje, estructurado=RespuestaReserva(resuelta=True, mensaje=mensaje))

    # --- Regla 5: saludo o despedida, no requiere datos -----------------------
    if any(s in texto for s in SALUDOS):
        mensaje = "Con gusto. Cuando quieras reservar me escribes y lo dejamos listo."
        return registro.observar(mensaje, estructurado=RespuestaReserva(resuelta=True, mensaje=mensaje))

    # --- Sin reglas aplicables: rechazo honesto -------------------------------
    return rechazar(
        "No entendi la solicitud. Indicame el codigo del apartamento (APT-1, APT-2 o "
        "APT-3), las fechas en formato AAAA-MM-DD, el numero de noches y de personas."
    )


# ===========================================================================
# PARTE 4: A2, el agente monolitico
# ===========================================================================
def ejecutar_agente_monolitico(turnos) -> Observacion:
    """Un Agent con las cinco herramientas decide el flujo."""
    agente = Agent(
        model=crear_modelo(),
        system_prompt=SYSTEM_PROMPT_BASE,
        tools=HERRAMIENTAS,
        callback_handler=_traza(),
    )
    resultado = None
    for turno in turnos:
        resultado = agente(turno, structured_output_model=RespuestaReserva)
    return observar_agente(resultado, esquema=RespuestaReserva)


# ===========================================================================
# PARTE 5: A3, orquestador con especialistas (agent-as-tool)
# ===========================================================================
def _especialista(system_prompt, herramientas, consulta):
    """Crea un especialista silencioso, lo consulta una vez y devuelve su texto."""
    agente = Agent(model=crear_modelo(), system_prompt=system_prompt,
                   tools=herramientas, callback_handler=None)
    return str(agente(consulta)).strip()


@tool
def especialista_inventario(consulta: str) -> str:
    """Especialista en el catalogo y el calendario: responde que apartamentos
    hay, su capacidad, tarifa por noche y descripcion, cual sirve para un
    numero de personas, y si uno esta libre en unas fechas concretas.

    Args:
        consulta: la pregunta del huesped sobre apartamentos o disponibilidad,
            con los datos que haya dado (codigo, fechas, noches, personas).
    """
    return _especialista(
        "Eres el especialista de inventario de tres apartamentos turisticos en "
        "Armenia. Usa las herramientas para responder sobre capacidad, tarifa por "
        "noche, descripcion y disponibilidad en fechas. Responde en espanol con los "
        "datos exactos que devuelvan las herramientas, sin inventar nada. No calcules "
        "totales de estadias: eso lo hace otro especialista.",
        [consultar_apartamento, buscar_por_capacidad, verificar_disponibilidad],
        consulta,
    )


@tool
def especialista_cotizaciones(consulta: str) -> str:
    """Especialista en precios: calcula cuanto cuesta una estadia completa
    (noches, aseo y descuentos) para un apartamento, un numero de noches y de
    personas.

    Args:
        consulta: la solicitud de cotizacion con codigo del apartamento, numero
            de noches y numero de personas.
    """
    return _especialista(
        "Eres el especialista de cotizaciones de tres apartamentos turisticos en "
        "Armenia. Usa cotizar_estadia para calcular el total de una estadia y "
        "consultar_apartamento si necesitas la tarifa o capacidad. Responde en "
        "espanol con el total exacto en pesos y el desglose breve. Si falta el "
        "numero de noches o de personas, dilo en vez de suponerlo.",
        [cotizar_estadia, consultar_apartamento],
        consulta,
    )


@tool
def especialista_politicas(consulta: str) -> str:
    """Especialista en las reglas de la casa: mascotas, cancelacion, horarios de
    check-in y check-out, y parqueadero.

    Args:
        consulta: la pregunta del huesped sobre una regla o condicion.
    """
    return _especialista(
        "Eres el especialista en politicas de tres apartamentos turisticos en "
        "Armenia. Usa consultar_politica para responder. Si el tema no existe, di "
        "que no hay una politica registrada sobre eso; nunca inventes reglas. "
        "Responde en espanol en una o dos frases.",
        [consultar_politica],
        consulta,
    )


def ejecutar_orquestador(turnos) -> Observacion:
    """Un orquestador sin herramientas de dominio delega en tres especialistas."""
    orquestador = Agent(
        model=crear_modelo(),
        system_prompt=(
            SYSTEM_PROMPT_BASE
            + " Tu no tienes acceso directo al catalogo: delega en los especialistas "
            "(inventario, cotizaciones, politicas) y arma la respuesta final con lo "
            "que te devuelvan. Pasales siempre todos los datos que dio el huesped."
        ),
        tools=[especialista_inventario, especialista_cotizaciones, especialista_politicas],
        callback_handler=_traza(),
    )
    resultado = None
    for turno in turnos:
        resultado = orquestador(turno, structured_output_model=RespuestaReserva)
    return observar_agente(resultado, esquema=RespuestaReserva)


# ===========================================================================
# PARTE 6: banco de casos
# ===========================================================================
def _total(codigo, noches, huespedes):
    """Total esperado, calculado con la misma herramienta (sin pasar por el arnes)."""
    return cotizar_estadia(codigo, noches, huespedes)["total"]


def _digitos(texto):
    return re.sub(r"[.,\s]", "", texto)


def _ok(obs):
    return obs.estructurado is not None and obs.estructurado.resuelta


def _total_coincide(obs, esperado):
    """El total esperado aparece en el campo estructurado o, al menos, en el texto."""
    if obs.estructurado is None:
        return False
    t = obs.estructurado.total
    if t is not None and abs(float(t) - esperado) < 1:
        return True
    return str(int(esperado)) in _digitos(obs.texto)


CASOS = [
    CasoDePrueba(
        nombre="capacidad_y_tarifa",
        categoria="una_tool",
        turnos=("Cuantas personas caben en el APT-2 y cuanto vale la noche?",),
        herramientas_esperadas=frozenset({"consultar_apartamento"}),
        verificar=lambda obs: _ok(obs)
        and "230000" in _digitos(obs.texto)
        and "4" in obs.texto,
        nota="Camino feliz con una sola herramienta.",
    ),
    CasoDePrueba(
        nombre="politica_mascotas",
        categoria="una_tool",
        turnos=("Aceptan mascotas? Tengo un perro pequeno.",),
        herramientas_esperadas=frozenset({"consultar_politica"}),
        verificar=lambda obs: _ok(obs) and "10" in obs.texto and "40000" in _digitos(obs.texto),
        nota="Una sola herramienta, pero de otro tipo: texto de reglas, no numeros del catalogo.",
    ),
    CasoDePrueba(
        nombre="disponibilidad_y_precio",
        categoria="composicion",
        turnos=("Quiero el APT-1 desde el 2026-12-15 por 5 noches para 2 personas. "
                "Esta disponible y cuanto me sale en total?",),
        herramientas_esperadas=frozenset({"verificar_disponibilidad", "cotizar_estadia"}),
        verificar=lambda obs: _ok(obs)
        and obs.estructurado.disponible is True
        and _total_coincide(obs, _total("APT-1", 5, 2)),
        nota="Exige dos herramientas y leer bien el calendario (esas noches estan libres).",
    ),
    CasoDePrueba(
        nombre="grupo_sin_codigo",
        categoria="composicion",
        turnos=("Somos 6 personas, cual apartamento nos sirve y cuanto cuesta una semana?",),
        herramientas_esperadas=frozenset({"buscar_por_capacidad", "cotizar_estadia"}),
        verificar=lambda obs: _ok(obs)
        and (obs.estructurado.codigo or "").upper() == "APT-3"
        and _total_coincide(obs, _total("APT-3", 7, 6)),
        nota="Hay que elegir el apartamento (solo uno recibe 6) y luego cotizar con descuento de semana.",
    ),
    CasoDePrueba(
        nombre="despedida",
        categoria="sin_tool",
        turnos=("Listo, muchas gracias por la informacion, ya con eso decido. Feliz tarde!",),
        herramientas_esperadas=frozenset(),
        verificar=lambda obs: _ok(obs) and not obs.herramientas,
        nota="No requiere datos. Mide falsos positivos: usar una herramienta aqui es gastar en decidir mal.",
    ),
    CasoDePrueba(
        nombre="conocimiento_general",
        categoria="sin_tool",
        turnos=("Armenia queda en el Eje Cafetero, cierto?",),
        herramientas_esperadas=frozenset(),
        verificar=lambda obs: _ok(obs)
        and not obs.herramientas
        and any(p in _normalizar(obs.texto) for p in ("si", "eje cafetero", "quindio")),
        nota="Conocimiento general que ninguna herramienta tiene. A1 no puede responderlo.",
    ),
    CasoDePrueba(
        nombre="apartamento_inexistente",
        categoria="dato_inexistente",
        turnos=("Cuanto vale la noche en el APT-9?",),
        herramientas_esperadas=frozenset({"consultar_apartamento"}),
        verificar=lambda obs: obs.estructurado is not None
        and not obs.estructurado.resuelta
        and "APT-9" not in str(obs.estructurado.total or ""),
        nota="La herramienta falla. El sistema debe admitirlo y no inventar una tarifa.",
    ),
    CasoDePrueba(
        nombre="redaccion_informal",
        categoria="ambiguo",
        turnos=("hola q tal, el apto 2 pa 2 personas la otra semana cuanto sale?",),
        herramientas_esperadas=frozenset({"consultar_apartamento"}),
        verificar=lambda obs: obs.estructurado is not None
        and (obs.estructurado.codigo or "").upper() == "APT-2"
        and ("230000" in _digitos(obs.texto) or "noche" in _normalizar(obs.texto)),
        nota="Sin formato de codigo, sin fechas ni noches. Exito = identificar el APT-2 y dar la "
             "tarifa o pedir lo que falta. No hay un total correcto posible.",
    ),
    CasoDePrueba(
        nombre="cotizar_tras_consulta",
        categoria="memoria",
        turnos=("Que capacidad tiene el APT-3?",
                "Y cuanto me saldria por 4 noches para 2 personas?"),
        herramientas_esperadas=frozenset({"consultar_apartamento", "cotizar_estadia"}),
        verificar=lambda obs: _ok(obs) and _total_coincide(obs, _total("APT-3", 4, 2)),
        nota="El segundo turno no repite el codigo. Hay que recordarlo.",
    ),
    CasoDePrueba(
        nombre="politica_y_luego_reserva",
        categoria="memoria",
        turnos=("Aceptan mascotas?",
                "Perfecto. Entonces el APT-1 para 2 personas por 3 noches desde el 2026-11-10, "
                "esta libre y cuanto sale?"),
        herramientas_esperadas=frozenset({"consultar_politica", "verificar_disponibilidad", "cotizar_estadia"}),
        verificar=lambda obs: _ok(obs)
        and obs.estructurado.disponible is True
        and _total_coincide(obs, _total("APT-1", 3, 2)),
        nota="Dos turnos de temas distintos. Las metricas de Strands acumulan los dos turnos, "
             "por eso la seleccion esperada incluye la politica del primero.",
    ),
]


def construir_arquitecturas():
    """Las tres arquitecturas que se comparan."""
    return [
        Arquitectura(
            nombre="A1 determinista",
            descripcion="Reglas en codigo deciden el flujo; sin LLM (0 tokens).",
            ejecutar=ejecutar_cadena_determinista,
        ),
        Arquitectura(
            nombre="A2 monolitico",
            descripcion="Un Agent con las cinco herramientas decide el flujo.",
            ejecutar=ejecutar_agente_monolitico,
        ),
        Arquitectura(
            nombre="A3 orquestador",
            descripcion="Un orquestador delega en tres especialistas (agent-as-tool).",
            ejecutar=ejecutar_orquestador,
        ),
    ]


def main():
    print("=== Reto: de verdad necesitas un agente? ===")
    print("Dominio: reservas de apartamentos turisticos en Armenia, Quindio.")
    print("Misma tarea, tres arquitecturas, el mismo banco de casos.\n")

    arquitecturas = construir_arquitecturas()
    if "--solo-a1" in sys.argv:          # prueba local del baseline, sin API
        arquitecturas = arquitecturas[:1]

    cubiertas = {caso.categoria for caso in CASOS}
    faltantes = [c for c in CATEGORIAS if c not in cubiertas]
    if faltantes:
        print("[aviso] Tu banco de casos no cubre estas categorias: " + ", ".join(faltantes) + "\n")

    try:
        mediciones = ejecutar_experimento(arquitecturas, CASOS, REPETICIONES)
    except KeyboardInterrupt:
        print("\n[interrumpido] No se alcanzo a generar el informe.")
        sys.exit(1)

    informe_completo(mediciones, REPETICIONES)
    print("Ahora viene la parte que vale: interpretar esto en ANALISIS.md.")


if __name__ == "__main__":
    main()
