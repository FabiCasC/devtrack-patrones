"""Patrón CHAIN OF RESPONSIBILITY — Flujo de aprobación de hitos.

Problema que resuelve: un hito solo se da por cerrado si lo aprueban, EN ORDEN,
el líder técnico, el gerente y el cliente. Cada uno revisa algo distinto. Si
pusiéramos todo en un solo método con muchos ``if``, cada cambio de regla (por
ejemplo, agregar un aprobador de QA) obligaría a modificarlo. Con la cadena,
cada aprobador es una clase independiente que decide si aprueba y pasa la
solicitud al siguiente, o la rechaza y corta la cadena.

Nota: en el material del curso Chain of Responsibility solo aparece en el mapa
conceptual de la Sesión 12, por eso se usan los nombres clásicos de GoF:
- Manejador (Handler) .............. ManejadorAprobacion (abc)
- ManejadorConcreto ................ LiderTecnicoAprobador, GerenteAprobador, ClienteAprobador
- Cliente .......................... ServicioProyectos (arma la cadena y envía la solicitud)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

from devtrack.creacionales.configuracion import ConfiguracionSistema
from devtrack.dominio.modelos import EstadoHito, EstadoTarea, Hito, Proyecto
from devtrack.excepciones import AprobacionError


@dataclass
class SolicitudAprobacion:
    proyecto: Proyecto
    hito: Hito
    costo_ejecutado: float = 0.0
    conformidad_cliente: bool = False
    fecha: date = field(default_factory=date.today)


class ManejadorAprobacion(ABC):
    rol = "Aprobador"

    def __init__(self) -> None:
        self._siguiente: ManejadorAprobacion | None = None

    def establecer_siguiente(self, siguiente: "ManejadorAprobacion") -> "ManejadorAprobacion":
        """Devuelve el siguiente para encadenar: lider.establecer_siguiente(g).establecer_siguiente(c)."""
        self._siguiente = siguiente
        return siguiente

    def manejar(self, solicitud: SolicitudAprobacion) -> bool:
        aprobado, motivo = self.evaluar(solicitud)
        estado = "APROBÓ" if aprobado else "RECHAZÓ"
        solicitud.hito.historial_aprobacion.append(f"{self.rol} {estado}: {motivo}")
        if not aprobado:
            solicitud.hito.estado = EstadoHito.RECHAZADO
            return False
        if self._siguiente:
            return self._siguiente.manejar(solicitud)
        solicitud.hito.estado = EstadoHito.APROBADO  # último eslabón
        return True

    @abstractmethod
    def evaluar(self, solicitud: SolicitudAprobacion) -> tuple[bool, str]: ...


class LiderTecnicoAprobador(ManejadorAprobacion):
    """Verifica la calidad técnica: todas las tareas del hito terminadas."""
    rol = "Líder técnico"

    def evaluar(self, solicitud: SolicitudAprobacion) -> tuple[bool, str]:
        tareas = solicitud.proyecto.tareas_de_hito(solicitud.hito)
        if not tareas:
            return False, "el hito no tiene tareas asociadas"
        pendientes = [t for t in tareas if t.estado is not EstadoTarea.TERMINADA]
        if pendientes:
            ids = ", ".join(f"#{t.id}" for t in pendientes)
            return False, f"hay tareas sin terminar ({ids})"
        return True, f"{len(tareas)} tareas terminadas"


class GerenteAprobador(ManejadorAprobacion):
    """Verifica plazo y presupuesto."""
    rol = "Gerente"

    def evaluar(self, solicitud: SolicitudAprobacion) -> tuple[bool, str]:
        if solicitud.costo_ejecutado > solicitud.proyecto.presupuesto:
            return False, "el costo supera el presupuesto del proyecto"
        if solicitud.fecha > solicitud.hito.fecha_limite:
            dias = (solicitud.fecha - solicitud.hito.fecha_limite).days
            limite = ConfiguracionSistema().obtener("dias_tolerancia_retraso", 0)
            if dias > limite:
                return False, f"el hito está retrasado {dias} día(s)"
        return True, "dentro de plazo y presupuesto"


class ClienteAprobador(ManejadorAprobacion):
    """Aceptación final del cliente."""
    rol = "Cliente"

    def evaluar(self, solicitud: SolicitudAprobacion) -> tuple[bool, str]:
        if not solicitud.conformidad_cliente:
            return False, "el cliente no dio su conformidad"
        return True, "conformidad otorgada"


def crear_cadena_aprobacion() -> ManejadorAprobacion:
    """Arma la cadena líder → gerente → cliente y devuelve el primer eslabón."""
    lider = LiderTecnicoAprobador()
    lider.establecer_siguiente(GerenteAprobador()).establecer_siguiente(ClienteAprobador())
    return lider


def solicitar_aprobacion(solicitud: SolicitudAprobacion,
                         cadena: ManejadorAprobacion | None = None) -> bool:
    if solicitud.hito.estado is EstadoHito.APROBADO:
        raise AprobacionError(f"El hito '{solicitud.hito.nombre}' ya fue aprobado.")
    solicitud.hito.estado = EstadoHito.EN_APROBACION
    return (cadena or crear_cadena_aprobacion()).manejar(solicitud)
