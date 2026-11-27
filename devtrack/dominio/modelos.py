"""Entidades del dominio de DevTrack."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from itertools import count
from typing import Optional

from devtrack.excepciones import TareaNoEncontradaError, ValidacionError


class Rol(Enum):
    DESARROLLADOR = "Desarrollador"
    QA = "QA"
    LIDER = "Líder técnico"
    GERENTE = "Gerente de proyecto"
    CLIENTE = "Cliente"


class EstadoTarea(Enum):
    POR_HACER = "Por hacer"
    EN_PROGRESO = "En progreso"
    EN_REVISION = "En revisión"
    TERMINADA = "Terminada"


class Prioridad(Enum):
    BAJA = 1
    MEDIA = 2
    ALTA = 3


class EstadoHito(Enum):
    PENDIENTE = "Pendiente"
    EN_APROBACION = "En aprobación"
    APROBADO = "Aprobado"
    RECHAZADO = "Rechazado"


@dataclass
class Usuario:
    nombre: str
    email: str
    rol: Rol
    telefono: str = ""
    canales: list[str] = field(default_factory=list)  # canales extra: "email", "sms"


_secuencia_tareas = count(1)


@dataclass
class Tarea:
    titulo: str
    descripcion: str = ""
    responsable: Optional[Usuario] = None
    prioridad: Prioridad = Prioridad.MEDIA
    estado: EstadoTarea = EstadoTarea.POR_HACER
    horas_estimadas: float = 0.0
    id: int = field(default_factory=lambda: next(_secuencia_tareas))

    def __post_init__(self) -> None:
        if not self.titulo or not self.titulo.strip():
            raise ValidacionError("La tarea debe tener un título.")
        if self.horas_estimadas < 0:
            raise ValidacionError("Las horas estimadas no pueden ser negativas.")


@dataclass
class Hito:
    nombre: str
    fecha_limite: date
    estado: EstadoHito = EstadoHito.PENDIENTE
    tareas_ids: list[int] = field(default_factory=list)
    historial_aprobacion: list[str] = field(default_factory=list)


@dataclass
class Proyecto:
    """Proyecto de software. Se construye mediante ProyectoBuilder (patrón Builder)."""

    nombre: str
    descripcion: str
    cliente: str
    fecha_inicio: date
    fecha_fin: date
    presupuesto: float
    metodologia: str
    repositorio: str
    equipo: list[Usuario]
    hitos: list[Hito]
    tareas: list[Tarea] = field(default_factory=list)

    # ----- Operaciones sobre tareas (el Proyecto es el "Receiver" de los comandos) -----
    def agregar_tarea(self, tarea: Tarea) -> None:
        self.tareas.append(tarea)

    def quitar_tarea(self, tarea_id: int) -> Tarea:
        tarea = self.buscar_tarea(tarea_id)
        self.tareas.remove(tarea)
        return tarea

    def buscar_tarea(self, tarea_id: int) -> Tarea:
        for tarea in self.tareas:
            if tarea.id == tarea_id:
                return tarea
        raise TareaNoEncontradaError(f"No existe la tarea #{tarea_id} en '{self.nombre}'.")

    def buscar_hito(self, nombre: str) -> Hito:
        for hito in self.hitos:
            if hito.nombre.lower() == nombre.lower():
                return hito
        raise ValidacionError(f"No existe el hito '{nombre}'.")

    def tareas_de_hito(self, hito: Hito) -> list[Tarea]:
        return [t for t in self.tareas if t.id in hito.tareas_ids]

    def avance(self) -> float:
        """Porcentaje de tareas terminadas."""
        if not self.tareas:
            return 0.0
        terminadas = sum(1 for t in self.tareas if t.estado is EstadoTarea.TERMINADA)
        return round(100 * terminadas / len(self.tareas), 1)
