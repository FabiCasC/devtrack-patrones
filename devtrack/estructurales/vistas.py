"""Patrón ADAPTER — Vistas de un proyecto según el rol.

Problema que resuelve: la consola (cliente) solo sabe mostrar objetos que cumplan
el contrato ``VistaProyecto`` (título, columnas y filas). El ``Proyecto`` del
dominio (Adaptee) tiene otra interfaz: listas de tareas, hitos, presupuesto...
Cada rol necesita ver los datos de forma distinta:

- Desarrollador: sus tareas con prioridad y horas estimadas.
- QA: tareas listas para revisar o terminadas.
- Cliente: solo avance por hito (sin datos internos como horas o responsables).

Participantes (nombres del curso, Sesión 08):
- Target .... VistaProyecto (contrato con abc)
- Adaptee ... Proyecto (clase del dominio, no se modifica)
- Adapter ... VistaDesarrolladorAdapter, VistaQAAdapter, VistaClienteAdapter
              (adaptadores de objeto: contienen al Adaptee por composición)
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from devtrack.dominio.modelos import EstadoTarea, Proyecto, Rol, Usuario


class VistaProyecto(ABC):
    """Target: lo que la interfaz de usuario sabe dibujar."""

    @abstractmethod
    def titulo(self) -> str: ...

    @abstractmethod
    def columnas(self) -> list[str]: ...

    @abstractmethod
    def filas(self) -> list[list[str]]: ...


class VistaDesarrolladorAdapter(VistaProyecto):
    def __init__(self, proyecto: Proyecto, usuario: Usuario) -> None:
        self._proyecto = proyecto
        self._usuario = usuario

    def titulo(self) -> str:
        return f"Mis tareas en {self._proyecto.nombre} ({self._usuario.nombre})"

    def columnas(self) -> list[str]:
        return ["#", "Tarea", "Estado", "Prioridad", "Horas"]

    def filas(self) -> list[list[str]]:
        mias = [t for t in self._proyecto.tareas
                if t.responsable is None or t.responsable.email == self._usuario.email]
        mias.sort(key=lambda t: t.prioridad.value, reverse=True)
        return [[str(t.id), t.titulo, t.estado.value, t.prioridad.name.title(),
                 f"{t.horas_estimadas:g}"] for t in mias]


class VistaQAAdapter(VistaProyecto):
    _ESTADOS_QA = (EstadoTarea.EN_REVISION, EstadoTarea.TERMINADA)

    def __init__(self, proyecto: Proyecto) -> None:
        self._proyecto = proyecto

    def titulo(self) -> str:
        return f"Cola de QA — {self._proyecto.nombre}"

    def columnas(self) -> list[str]:
        return ["#", "Tarea", "Estado", "Responsable"]

    def filas(self) -> list[list[str]]:
        return [[str(t.id), t.titulo, t.estado.value,
                 t.responsable.nombre if t.responsable else "Sin asignar"]
                for t in self._proyecto.tareas if t.estado in self._ESTADOS_QA]


class VistaClienteAdapter(VistaProyecto):
    def __init__(self, proyecto: Proyecto) -> None:
        self._proyecto = proyecto

    def titulo(self) -> str:
        return f"Avance de {self._proyecto.nombre}: {self._proyecto.avance()}%"

    def columnas(self) -> list[str]:
        return ["Hito", "Fecha límite", "Estado", "Avance"]

    def filas(self) -> list[list[str]]:
        filas = []
        for hito in self._proyecto.hitos:
            tareas = self._proyecto.tareas_de_hito(hito)
            hechas = sum(1 for t in tareas if t.estado is EstadoTarea.TERMINADA)
            avance = f"{round(100 * hechas / len(tareas))}%" if tareas else "—"
            filas.append([hito.nombre, hito.fecha_limite.isoformat(), hito.estado.value, avance])
        return filas


def crear_vista(proyecto: Proyecto, usuario: Usuario) -> VistaProyecto:
    """Elige el adaptador según el rol del usuario."""
    if usuario.rol is Rol.QA:
        return VistaQAAdapter(proyecto)
    if usuario.rol is Rol.CLIENTE:
        return VistaClienteAdapter(proyecto)
    return VistaDesarrolladorAdapter(proyecto, usuario)
