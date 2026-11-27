from datetime import date, timedelta

import pytest

from devtrack.comportamiento.aprobacion import (SolicitudAprobacion, crear_cadena_aprobacion,
                                                solicitar_aprobacion)
from devtrack.comportamiento.comandos import (CrearTareaComando, EliminarTareaComando,
                                              GestorComandos, MoverTareaComando)
from devtrack.dominio.modelos import EstadoHito, EstadoTarea, Tarea
from devtrack.excepciones import AprobacionError, SinAccionesError, TareaNoEncontradaError


# ---------------- Command ----------------
def test_command_crear_y_deshacer_tarea(proyecto):
    gestor = GestorComandos("Ana")
    tarea = Tarea("API de pagos")
    gestor.ejecutar(CrearTareaComando(proyecto, tarea, "Sprint 1"))
    assert tarea in proyecto.tareas and tarea.id in proyecto.hitos[0].tareas_ids
    gestor.deshacer()
    assert tarea not in proyecto.tareas and tarea.id not in proyecto.hitos[0].tareas_ids


def test_command_mover_deshacer_y_rehacer(proyecto):
    tarea = Tarea("Login")
    proyecto.agregar_tarea(tarea)
    gestor = GestorComandos()
    gestor.ejecutar(MoverTareaComando(proyecto, tarea.id, EstadoTarea.EN_PROGRESO))
    gestor.deshacer()
    assert tarea.estado is EstadoTarea.POR_HACER
    gestor.rehacer()
    assert tarea.estado is EstadoTarea.EN_PROGRESO
    assert len(gestor.auditoria) == 3


def test_command_eliminar_restaura_en_la_misma_posicion(proyecto):
    a, b, c = Tarea("A"), Tarea("B"), Tarea("C")
    for t in (a, b, c):
        proyecto.agregar_tarea(t)
    gestor = GestorComandos()
    gestor.ejecutar(EliminarTareaComando(proyecto, b.id))
    gestor.deshacer()
    assert [t.titulo for t in proyecto.tareas] == ["A", "B", "C"]


def test_command_errores_no_entran_al_historial(proyecto):
    gestor = GestorComandos()
    with pytest.raises(TareaNoEncontradaError):
        gestor.ejecutar(EliminarTareaComando(proyecto, 9999))
    with pytest.raises(SinAccionesError):
        gestor.deshacer()


# ---------------- Chain of Responsibility ----------------
def _hito_con_tareas(proyecto, estados):
    hito = proyecto.hitos[0]
    for estado in estados:
        tarea = Tarea("t", estado=estado)
        proyecto.agregar_tarea(tarea)
        hito.tareas_ids.append(tarea.id)
    return hito


def test_chain_aprueba_cuando_los_tres_niveles_estan_conformes(proyecto):
    hito = _hito_con_tareas(proyecto, [EstadoTarea.TERMINADA] * 2)
    assert solicitar_aprobacion(SolicitudAprobacion(proyecto, hito, 1000, True))
    assert hito.estado is EstadoHito.APROBADO
    assert [p.split()[0] for p in hito.historial_aprobacion] == ["Líder", "Gerente", "Cliente"]


def test_chain_lider_corta_la_cadena_si_hay_tareas_pendientes(proyecto):
    hito = _hito_con_tareas(proyecto, [EstadoTarea.TERMINADA, EstadoTarea.EN_PROGRESO])
    assert not solicitar_aprobacion(SolicitudAprobacion(proyecto, hito, 0, True))
    assert hito.estado is EstadoHito.RECHAZADO
    assert len(hito.historial_aprobacion) == 1  # gerente y cliente no fueron consultados


def test_chain_gerente_rechaza_por_presupuesto_y_retraso(proyecto):
    hito = _hito_con_tareas(proyecto, [EstadoTarea.TERMINADA])
    assert not crear_cadena_aprobacion().manejar(SolicitudAprobacion(proyecto, hito, 999_999, True))
    assert "presupuesto" in hito.historial_aprobacion[-1]
    tarde = hito.fecha_limite + timedelta(days=10)
    assert not crear_cadena_aprobacion().manejar(SolicitudAprobacion(proyecto, hito, 0, True, tarde))
    assert "retrasado" in hito.historial_aprobacion[-1]


def test_chain_cliente_rechaza_sin_conformidad_y_no_se_reaprueba(proyecto):
    hito = _hito_con_tareas(proyecto, [EstadoTarea.TERMINADA])
    assert not solicitar_aprobacion(SolicitudAprobacion(proyecto, hito, 0, False))
    assert "Cliente RECHAZÓ" in hito.historial_aprobacion[-1]
    assert solicitar_aprobacion(SolicitudAprobacion(proyecto, hito, 0, True, date.today()))
    with pytest.raises(AprobacionError):
        solicitar_aprobacion(SolicitudAprobacion(proyecto, hito, 0, True))
