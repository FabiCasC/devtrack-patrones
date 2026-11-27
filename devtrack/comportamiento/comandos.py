"""Patrón COMMAND — Acciones sobre tareas con deshacer/rehacer y auditoría.

Problema que resuelve: crear, mover y eliminar tareas son operaciones que el
usuario quiere poder DESHACER si se equivoca, y que el equipo necesita
AUDITAR (quién hizo qué). Encapsular cada acción en un objeto permite guardar
un historial, deshacer/rehacer y registrar cada operación sin que la consola
(cliente) conozca los detalles de cómo se ejecuta.

Participantes (nombres del curso, Sesión 13):
- Comando ............. Comando (abc, método ejecutar())
- ComandoConcreto ..... CrearTareaComando, MoverTareaComando, EliminarTareaComando
- Receptor ............ Proyecto (contiene la lógica real sobre sus tareas)
- Invocador ........... GestorComandos (ejecuta, guarda historial, deshace/rehace)
- Cliente ............. ServicioProyectos / consola
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from devtrack.dominio.modelos import EstadoTarea, Proyecto, Tarea
from devtrack.excepciones import SinAccionesError, ValidacionError


class Comando(ABC):
    @abstractmethod
    def ejecutar(self) -> str: ...

    @abstractmethod
    def deshacer(self) -> str: ...


class CrearTareaComando(Comando):
    def __init__(self, proyecto: Proyecto, tarea: Tarea, hito: str | None = None) -> None:
        self._proyecto = proyecto
        self._tarea = tarea
        self._hito = proyecto.buscar_hito(hito) if hito else None

    def ejecutar(self) -> str:
        self._proyecto.agregar_tarea(self._tarea)
        if self._hito:
            self._hito.tareas_ids.append(self._tarea.id)
        return f"Tarea #{self._tarea.id} '{self._tarea.titulo}' creada"

    def deshacer(self) -> str:
        self._proyecto.quitar_tarea(self._tarea.id)
        if self._hito and self._tarea.id in self._hito.tareas_ids:
            self._hito.tareas_ids.remove(self._tarea.id)
        return f"Se deshizo la creación de la tarea #{self._tarea.id}"


class MoverTareaComando(Comando):
    """Mueve una tarea a otra columna del tablero (cambia su estado)."""

    def __init__(self, proyecto: Proyecto, tarea_id: int, nuevo_estado: EstadoTarea) -> None:
        self._proyecto = proyecto
        self._tarea_id = tarea_id
        self._nuevo_estado = nuevo_estado
        self._estado_anterior: EstadoTarea | None = None

    def ejecutar(self) -> str:
        tarea = self._proyecto.buscar_tarea(self._tarea_id)
        if tarea.estado is self._nuevo_estado:
            raise ValidacionError(f"La tarea #{tarea.id} ya está en '{tarea.estado.value}'.")
        self._estado_anterior = tarea.estado
        tarea.estado = self._nuevo_estado
        return f"Tarea #{tarea.id} movida: {self._estado_anterior.value} → {tarea.estado.value}"

    def deshacer(self) -> str:
        tarea = self._proyecto.buscar_tarea(self._tarea_id)
        assert self._estado_anterior is not None
        tarea.estado = self._estado_anterior
        return f"Tarea #{tarea.id} regresó a '{tarea.estado.value}'"


class EliminarTareaComando(Comando):
    def __init__(self, proyecto: Proyecto, tarea_id: int) -> None:
        self._proyecto = proyecto
        self._tarea_id = tarea_id
        self._tarea: Tarea | None = None
        self._posicion = 0
        self._hitos_afectados: list = []

    def ejecutar(self) -> str:
        tarea = self._proyecto.buscar_tarea(self._tarea_id)
        self._posicion = self._proyecto.tareas.index(tarea)
        self._tarea = self._proyecto.quitar_tarea(self._tarea_id)
        self._hitos_afectados = [h for h in self._proyecto.hitos if self._tarea_id in h.tareas_ids]
        for hito in self._hitos_afectados:
            hito.tareas_ids.remove(self._tarea_id)
        return f"Tarea #{tarea.id} '{tarea.titulo}' eliminada"

    def deshacer(self) -> str:
        assert self._tarea is not None
        self._proyecto.tareas.insert(self._posicion, self._tarea)
        for hito in self._hitos_afectados:
            hito.tareas_ids.append(self._tarea.id)
        return f"Tarea #{self._tarea.id} restaurada"


class GestorComandos:
    """Invocador: ejecuta comandos y mantiene historial para deshacer/rehacer."""

    def __init__(self, usuario: str = "sistema", auditoria: list[str] | None = None) -> None:
        self.usuario = usuario
        self._hechos: list[Comando] = []
        self._deshechos: list[Comando] = []
        # puede compartirse entre varios invocadores para tener un único registro
        self.auditoria: list[str] = auditoria if auditoria is not None else []

    def ejecutar(self, comando: Comando) -> str:
        resultado = comando.ejecutar()  # si falla, no entra al historial
        self._hechos.append(comando)
        self._deshechos.clear()
        self._registrar(resultado)
        return resultado

    def deshacer(self) -> str:
        if not self._hechos:
            raise SinAccionesError("No hay acciones para deshacer.")
        comando = self._hechos.pop()
        resultado = comando.deshacer()
        self._deshechos.append(comando)
        self._registrar(resultado)
        return resultado

    def rehacer(self) -> str:
        if not self._deshechos:
            raise SinAccionesError("No hay acciones para rehacer.")
        comando = self._deshechos.pop()
        resultado = comando.ejecutar()
        self._hechos.append(comando)
        self._registrar("Rehecho: " + resultado)
        return resultado

    def _registrar(self, texto: str) -> None:
        marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.auditoria.append(f"{marca} | {self.usuario} | {texto}")
