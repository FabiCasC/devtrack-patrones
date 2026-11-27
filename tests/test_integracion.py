"""Pruebas de integración: el servicio combina todos los patrones."""
from datetime import date, timedelta

import pytest

from devtrack.datos_demo import cargar_demo
from devtrack.dominio.modelos import EstadoTarea, Prioridad
from devtrack.excepciones import AccesoDenegadoError, ValidacionError
from devtrack.servicios.servicio_proyectos import ServicioProyectos


def test_flujo_completo_crear_mover_notificar_y_aprobar(usuarios):
    servicio = ServicioProyectos()
    hoy = date.today()
    proyecto = servicio.crear_proyecto(usuarios["lider"], "Portal", "ACME", hoy,
                                       hoy + timedelta(weeks=4), 20_000,
                                       equipo=list(usuarios.values()),
                                       hitos=[("Beta", hoy + timedelta(weeks=2))])
    servicio.crear_tarea(usuarios["dev"], proyecto, "Home", Prioridad.ALTA, 6,
                         usuarios["dev"], "Beta")
    tarea_id = proyecto.tareas[0].id
    servicio.mover_tarea(usuarios["dev"], proyecto, tarea_id, EstadoTarea.EN_REVISION)
    servicio.mover_tarea(usuarios["qa"], proyecto, tarea_id, EstadoTarea.TERMINADA)

    assert servicio.aprobar_hito(usuarios["lider"], proyecto, "Beta", 5_000, True)
    # Decorator: el desarrollador recibe por in-app, email y SMS
    canales = [n.split("]")[0] for n in servicio.registro_notificaciones if "Bruno" in n or "bruno" in n or "999" in n]
    assert {"[IN-APP", "[EMAIL → bruno@x.pe", "[SMS → 999111222"} <= set(canales)
    assert len(servicio.auditoria()) == 3


def test_permisos_por_rol(usuarios, proyecto):
    servicio = ServicioProyectos()
    with pytest.raises(AccesoDenegadoError):
        servicio.crear_tarea(usuarios["cliente"], proyecto, "Hackear")
    with pytest.raises(AccesoDenegadoError):
        servicio.aprobar_hito(usuarios["dev"], proyecto, "Sprint 1", 0, True)


def test_configuracion_global_limita_horas_de_tarea(usuarios, proyecto):
    servicio = ServicioProyectos()
    servicio.config.establecer("max_horas_por_tarea", 8)
    with pytest.raises(ValidacionError):
        servicio.crear_tarea(usuarios["dev"], proyecto, "Tarea enorme", horas=20)


def test_datos_demo_cargan_sin_errores():
    servicio, usuarios = cargar_demo()
    proyecto = next(iter(servicio.proyectos.values()))
    assert len(proyecto.tareas) == 5 and len(usuarios) == 6
    assert servicio.auditoria() == [] and servicio.registro_notificaciones == []
