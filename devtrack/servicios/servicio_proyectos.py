"""Capa de aplicación: orquesta los patrones y aplica las reglas de permisos.

La consola (capa de presentación) solo habla con este servicio; no conoce los
comandos, la cadena de aprobación ni los decoradores. Así se mantiene bajo
acoplamiento: se podría cambiar la consola por una interfaz web sin tocar esto.
"""
from __future__ import annotations

from datetime import date

from devtrack.comportamiento.aprobacion import SolicitudAprobacion, solicitar_aprobacion
from devtrack.comportamiento.comandos import (CrearTareaComando, EliminarTareaComando,
                                              GestorComandos, MoverTareaComando)
from devtrack.creacionales.builder import ProyectoBuilder
from devtrack.creacionales.configuracion import ConfiguracionSistema
from devtrack.dominio.modelos import (EstadoTarea, Prioridad, Proyecto, Rol, Tarea,
                                      Usuario)
from devtrack.estructurales.notificaciones import Notificador, construir_notificador
from devtrack.estructurales.vistas import VistaProyecto, crear_vista
from devtrack.excepciones import AccesoDenegadoError, ValidacionError

# Qué roles pueden hacer cada operación
PERMISOS: dict[str, set[Rol]] = {
    "crear_proyecto": {Rol.LIDER, Rol.GERENTE},
    "gestionar_tareas": {Rol.DESARROLLADOR, Rol.LIDER, Rol.GERENTE},
    "mover_tareas": {Rol.DESARROLLADOR, Rol.QA, Rol.LIDER, Rol.GERENTE},
    "solicitar_aprobacion": {Rol.LIDER, Rol.GERENTE},
}


class ServicioProyectos:
    def __init__(self) -> None:
        self.config = ConfiguracionSistema()
        self.proyectos: dict[str, Proyecto] = {}
        self._gestores: dict[str, GestorComandos] = {}
        self.registro_notificaciones: list[str] = []
        self.registro_auditoria: list[str] = []

    # ---------------- permisos ----------------
    @staticmethod
    def verificar_permiso(usuario: Usuario, accion: str) -> None:
        """Lanza AccesoDenegadoError si el rol no puede realizar la acción."""
        ServicioProyectos._verificar(usuario, accion)

    @staticmethod
    def _verificar(usuario: Usuario, accion: str) -> None:
        if usuario.rol not in PERMISOS[accion]:
            raise AccesoDenegadoError(
                f"El rol {usuario.rol.value} no puede realizar '{accion.replace('_', ' ')}'.")

    def _gestor(self, usuario: Usuario) -> GestorComandos:
        if usuario.email not in self._gestores:
            self._gestores[usuario.email] = GestorComandos(usuario.nombre, self.registro_auditoria)
        return self._gestores[usuario.email]

    # ---------------- proyectos (Builder) ----------------
    def registrar_proyecto(self, usuario: Usuario, proyecto: Proyecto) -> Proyecto:
        self._verificar(usuario, "crear_proyecto")
        clave = proyecto.nombre.lower()
        if clave in self.proyectos:
            raise ValidacionError(f"Ya existe un proyecto llamado '{proyecto.nombre}'.")
        self.proyectos[clave] = proyecto
        self.notificar_equipo(proyecto, f"Fuiste agregado al proyecto '{proyecto.nombre}'.")
        return proyecto

    def crear_proyecto(self, usuario: Usuario, nombre: str, cliente: str, inicio: date,
                       fin: date, presupuesto: float, metodologia: str = "Scrum",
                       descripcion: str = "", equipo: list[Usuario] | None = None,
                       hitos: list[tuple[str, date]] | None = None) -> Proyecto:
        builder = (ProyectoBuilder().con_nombre(nombre).para_cliente(cliente)
                   .con_fechas(inicio, fin).con_presupuesto(presupuesto)
                   .con_metodologia(metodologia).con_descripcion(descripcion))
        for miembro in equipo or []:
            builder.agregar_miembro(miembro)
        for nombre_hito, fecha in hitos or []:
            builder.agregar_hito(nombre_hito, fecha)
        return self.registrar_proyecto(usuario, builder.build())

    def obtener_proyecto(self, nombre: str) -> Proyecto:
        try:
            return self.proyectos[nombre.lower()]
        except KeyError:
            raise ValidacionError(f"No existe el proyecto '{nombre}'.") from None

    def proyectos_de(self, usuario: Usuario) -> list[Proyecto]:
        return [p for p in self.proyectos.values()
                if any(m.email == usuario.email for m in p.equipo)]

    # ---------------- tareas (Command) ----------------
    def crear_tarea(self, usuario: Usuario, proyecto: Proyecto, titulo: str,
                    prioridad: Prioridad = Prioridad.MEDIA, horas: float = 0,
                    responsable: Usuario | None = None, hito: str | None = None) -> str:
        self._verificar(usuario, "gestionar_tareas")
        maximo = self.config.obtener("max_horas_por_tarea")
        if horas > maximo:
            raise ValidacionError(f"Una tarea no puede superar {maximo} horas; divídela.")
        tarea = Tarea(titulo=titulo, prioridad=prioridad, horas_estimadas=horas,
                      responsable=responsable)
        resultado = self._gestor(usuario).ejecutar(CrearTareaComando(proyecto, tarea, hito))
        if responsable:
            self._notificar(responsable, f"Se te asignó la tarea #{tarea.id}: {titulo}")
        return resultado

    def mover_tarea(self, usuario: Usuario, proyecto: Proyecto, tarea_id: int,
                    estado: EstadoTarea) -> str:
        self._verificar(usuario, "mover_tareas")
        resultado = self._gestor(usuario).ejecutar(MoverTareaComando(proyecto, tarea_id, estado))
        if estado is EstadoTarea.EN_REVISION:
            for qa in (m for m in proyecto.equipo if m.rol is Rol.QA):
                self._notificar(qa, f"La tarea #{tarea_id} está lista para revisión.")
        return resultado

    def eliminar_tarea(self, usuario: Usuario, proyecto: Proyecto, tarea_id: int) -> str:
        self._verificar(usuario, "gestionar_tareas")
        return self._gestor(usuario).ejecutar(EliminarTareaComando(proyecto, tarea_id))

    def deshacer(self, usuario: Usuario) -> str:
        return self._gestor(usuario).deshacer()

    def rehacer(self, usuario: Usuario) -> str:
        return self._gestor(usuario).rehacer()

    def auditoria(self) -> list[str]:
        return list(self.registro_auditoria)

    # ---------------- vistas (Adapter) ----------------
    def vista_para(self, usuario: Usuario, proyecto: Proyecto) -> VistaProyecto:
        return crear_vista(proyecto, usuario)

    # ---------------- aprobación (Chain of Responsibility) ----------------
    def aprobar_hito(self, usuario: Usuario, proyecto: Proyecto, nombre_hito: str,
                     costo_ejecutado: float, conformidad_cliente: bool,
                     fecha: date | None = None) -> bool:
        self._verificar(usuario, "solicitar_aprobacion")
        hito = proyecto.buscar_hito(nombre_hito)
        solicitud = SolicitudAprobacion(proyecto, hito, costo_ejecutado, conformidad_cliente,
                                        fecha or date.today())
        aprobado = solicitar_aprobacion(solicitud)
        resultado = "APROBADO" if aprobado else "RECHAZADO"
        self.notificar_equipo(proyecto, f"Hito '{hito.nombre}' {resultado}: "
                                        f"{hito.historial_aprobacion[-1]}")
        return aprobado

    # ---------------- notificaciones (Decorator) ----------------
    def _notificador_para(self, usuario: Usuario) -> Notificador:
        globales = self.config.obtener("canales_notificacion", [])
        canales = list(dict.fromkeys([*globales, *usuario.canales]))
        return construir_notificador(canales)

    def _notificar(self, usuario: Usuario, mensaje: str) -> None:
        self.registro_notificaciones.extend(self._notificador_para(usuario).enviar(usuario, mensaje))

    def notificar_equipo(self, proyecto: Proyecto, mensaje: str) -> None:
        for miembro in proyecto.equipo:
            self._notificar(miembro, mensaje)
