"""Datos de ejemplo para la demostración en vivo."""
from __future__ import annotations

from datetime import date, timedelta

from devtrack.creacionales.builder import DirectorProyecto, ProyectoBuilder
from devtrack.dominio.modelos import EstadoTarea, Prioridad, Rol, Usuario
from devtrack.servicios.servicio_proyectos import ServicioProyectos

USUARIOS = [
    Usuario("Ana Torres", "ana@devtrack.pe", Rol.LIDER, "987654321", ["email"]),
    Usuario("Bruno Díaz", "bruno@devtrack.pe", Rol.DESARROLLADOR, "912345678", ["email", "sms"]),
    Usuario("Carla Ruiz", "carla@devtrack.pe", Rol.DESARROLLADOR),
    Usuario("Diego Paz", "diego@devtrack.pe", Rol.QA, "923456789", ["sms"]),
    Usuario("Elena Vega", "elena@devtrack.pe", Rol.GERENTE, "", ["email"]),
    Usuario("Felipe Ríos", "felipe@cliente.com", Rol.CLIENTE, "", ["email"]),
]


def cargar_demo() -> tuple[ServicioProyectos, list[Usuario]]:
    servicio = ServicioProyectos()
    ana, bruno, carla, diego, elena, felipe = USUARIOS
    inicio = date.today() - timedelta(weeks=1)

    # Director + Builder: proyecto Scrum con 3 sprints
    builder = ProyectoBuilder()
    for miembro in USUARIOS:
        builder.agregar_miembro(miembro)
    builder.con_presupuesto(80_000).con_descripcion("App móvil de pedidos para una cadena de cafeterías")
    builder.con_repositorio("https://github.com/FabiCasC/devtrack-patrones")
    proyecto = DirectorProyecto(builder).construir_proyecto_scrum(
        "App Cafetería", "Café Andino S.A.C.", inicio, sprints=3)
    servicio.registrar_proyecto(ana, proyecto)

    tareas = [
        ("Diseñar modelo de datos", Prioridad.ALTA, 8, bruno, "Sprint 1", EstadoTarea.TERMINADA),
        ("Login con correo", Prioridad.ALTA, 12, bruno, "Sprint 1", EstadoTarea.TERMINADA),
        ("Catálogo de productos", Prioridad.MEDIA, 16, carla, "Sprint 2", EstadoTarea.EN_REVISION),
        ("Carrito de compras", Prioridad.ALTA, 20, bruno, "Sprint 2", EstadoTarea.EN_PROGRESO),
        ("Pasarela de pago", Prioridad.ALTA, 24, carla, "Sprint 3", EstadoTarea.POR_HACER),
    ]
    for titulo, prioridad, horas, responsable, hito, estado in tareas:
        servicio.crear_tarea(ana, proyecto, titulo, prioridad, horas, responsable, hito)
        tarea = proyecto.tareas[-1]
        tarea.estado = estado  # estado inicial de la demo (sin pasar por el historial)

    servicio.registro_notificaciones.clear()
    servicio.registro_auditoria.clear()
    return servicio, USUARIOS
