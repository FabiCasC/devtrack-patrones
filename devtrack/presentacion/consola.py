"""Capa de presentación: interfaz de consola con menús según el rol.

Solo depende de ServicioProyectos; todos los errores del dominio (DevTrackError)
se muestran como mensajes amigables sin cerrar el programa.
"""
from __future__ import annotations

from datetime import date, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table

from devtrack.creacionales.builder import DirectorProyecto, ProyectoBuilder
from devtrack.datos_demo import cargar_demo
from devtrack.dominio.modelos import EstadoTarea, Prioridad, Proyecto, Usuario
from devtrack.estructurales.notificaciones import canales_disponibles
from devtrack.excepciones import DevTrackError

consola = Console()


class AppConsola:
    def __init__(self) -> None:
        self.servicio, self.usuarios = cargar_demo()
        self.usuario: Usuario | None = None
        self.proyecto: Proyecto | None = None
        self.opciones = [
            ("Ver tablero del proyecto (vista según rol)", self.ver_tablero),
            ("Seleccionar proyecto", self.seleccionar_proyecto),
            ("Crear proyecto (Builder)", self.crear_proyecto),
            ("Crear tarea", self.crear_tarea),
            ("Mover tarea de estado", self.mover_tarea),
            ("Eliminar tarea", self.eliminar_tarea),
            ("Deshacer última acción", lambda: self._ok(self.servicio.deshacer(self.usuario))),
            ("Rehacer acción", lambda: self._ok(self.servicio.rehacer(self.usuario))),
            ("Solicitar aprobación de hito", self.aprobar_hito),
            ("Ver notificaciones enviadas", self.ver_notificaciones),
            ("Ver auditoría de acciones", self.ver_auditoria),
            ("Configuración del sistema", self.configuracion),
            ("Cambiar de usuario", self.iniciar_sesion),
        ]

    # ---------------- ciclo principal ----------------
    def ejecutar(self) -> None:
        empresa = self.servicio.config.obtener("empresa")
        consola.print(Panel.fit(f"[bold cyan]DevTrack[/] — Gestión de Proyectos de Software\n{empresa}",
                                border_style="cyan"))
        self.iniciar_sesion()
        while True:
            self._menu()
            opcion = IntPrompt.ask("Opción", default=0)
            if opcion == 0:
                consola.print("[cyan]¡Hasta luego![/]")
                return
            if 1 <= opcion <= len(self.opciones):
                try:
                    self.opciones[opcion - 1][1]()
                except DevTrackError as error:
                    consola.print(f"[bold red]✖ {error}[/]")
            else:
                consola.print("[red]Opción no válida.[/]")

    def _menu(self) -> None:
        assert self.usuario
        nombre_proyecto = self.proyecto.nombre if self.proyecto else "ninguno"
        consola.rule(f"[bold]{self.usuario.nombre}[/] ({self.usuario.rol.value}) · "
                     f"Proyecto: {nombre_proyecto}")
        for i, (texto, _) in enumerate(self.opciones, 1):
            consola.print(f"  [cyan]{i:>2}[/]. {texto}")
        consola.print("  [cyan] 0[/]. Salir")

    @staticmethod
    def _ok(mensaje: str) -> None:
        consola.print(f"[green]✔ {mensaje}[/]")

    # ---------------- sesión y proyecto ----------------
    def iniciar_sesion(self) -> None:
        tabla = Table(title="Usuarios")
        for col in ("#", "Nombre", "Rol", "Canales"):
            tabla.add_column(col)
        for i, u in enumerate(self.usuarios, 1):
            tabla.add_row(str(i), u.nombre, u.rol.value, ", ".join(["in-app", *u.canales]))
        consola.print(tabla)
        indice = IntPrompt.ask("Ingresar como", choices=[str(i) for i in range(1, len(self.usuarios) + 1)])
        self.usuario = self.usuarios[indice - 1]
        mis = self.servicio.proyectos_de(self.usuario)
        self.proyecto = mis[0] if mis else None

    def seleccionar_proyecto(self) -> None:
        proyectos = list(self.servicio.proyectos.values())
        for i, p in enumerate(proyectos, 1):
            consola.print(f"  {i}. {p.nombre} — {p.cliente} ({p.avance()}%)")
        indice = IntPrompt.ask("Proyecto", choices=[str(i) for i in range(1, len(proyectos) + 1)])
        self.proyecto = proyectos[indice - 1]

    def _proyecto(self) -> Proyecto:
        if not self.proyecto:
            raise DevTrackError("Primero selecciona o crea un proyecto.")
        return self.proyecto

    # ---------------- Adapter ----------------
    def ver_tablero(self) -> None:
        vista = self.servicio.vista_para(self.usuario, self._proyecto())
        tabla = Table(title=vista.titulo(), header_style="bold magenta")
        for columna in vista.columnas():
            tabla.add_column(columna)
        for fila in vista.filas():
            tabla.add_row(*fila)
        consola.print(tabla if vista.filas() else f"[yellow]{vista.titulo()}: sin elementos.[/]")

    # ---------------- Builder ----------------
    def crear_proyecto(self) -> None:
        self.servicio.verificar_permiso(self.usuario, "crear_proyecto")
        nombre = Prompt.ask("Nombre del proyecto")
        cliente = Prompt.ask("Cliente")
        tipo = Prompt.ask("Plantilla", choices=["scrum", "mvp", "personalizado"], default="scrum")
        builder = ProyectoBuilder()
        for miembro in self.usuarios:
            if Confirm.ask(f"¿Agregar a {miembro.nombre} ({miembro.rol.value})?", default=True):
                builder.agregar_miembro(miembro)
        hoy = date.today()
        if tipo == "scrum":
            sprints = IntPrompt.ask("Número de sprints", default=4)
            builder.con_presupuesto(FloatPrompt.ask("Presupuesto (S/)", default=50000.0))
            proyecto = DirectorProyecto(builder).construir_proyecto_scrum(nombre, cliente, hoy, sprints)
        elif tipo == "mvp":
            proyecto = DirectorProyecto(builder).construir_mvp(nombre, cliente, hoy)
        else:
            semanas = IntPrompt.ask("Duración en semanas", default=8)
            builder.con_nombre(nombre).para_cliente(cliente)
            builder.con_fechas(hoy, hoy + timedelta(weeks=semanas))
            builder.con_presupuesto(FloatPrompt.ask("Presupuesto (S/)", default=30000.0))
            builder.con_metodologia(Prompt.ask("Metodología", default="Kanban"))
            while Confirm.ask("¿Agregar un hito?", default=False):
                semana = IntPrompt.ask("¿En qué semana vence?", default=semanas)
                builder.agregar_hito(Prompt.ask("Nombre del hito"), hoy + timedelta(weeks=semana))
            proyecto = builder.build()
        self.proyecto = self.servicio.registrar_proyecto(self.usuario, proyecto)
        self._ok(f"Proyecto '{proyecto.nombre}' creado con {len(proyecto.hitos)} hitos "
                 f"(fin: {proyecto.fecha_fin.isoformat()})")

    # ---------------- Command ----------------
    def crear_tarea(self) -> None:
        proyecto = self._proyecto()
        self.servicio.verificar_permiso(self.usuario, "gestionar_tareas")
        titulo = Prompt.ask("Título de la tarea")
        prioridad = Prioridad[Prompt.ask("Prioridad", choices=["BAJA", "MEDIA", "ALTA"], default="MEDIA")]
        horas = FloatPrompt.ask("Horas estimadas", default=4.0)
        equipo = [m for m in proyecto.equipo if m.rol.name in ("DESARROLLADOR", "LIDER")]
        for i, m in enumerate(equipo, 1):
            consola.print(f"  {i}. {m.nombre}")
        responsable = equipo[IntPrompt.ask("Responsable", choices=[str(i) for i in range(1, len(equipo) + 1)]) - 1]
        hitos = [h.nombre for h in proyecto.hitos]
        hito = Prompt.ask("Hito", choices=hitos, default=hitos[0]) if hitos else None
        self._ok(self.servicio.crear_tarea(self.usuario, proyecto, titulo, prioridad, horas,
                                           responsable, hito))

    def mover_tarea(self) -> None:
        tarea_id = IntPrompt.ask("Número de tarea")
        estados = {e.name: e for e in EstadoTarea}
        estado = estados[Prompt.ask("Nuevo estado", choices=list(estados))]
        self._ok(self.servicio.mover_tarea(self.usuario, self._proyecto(), tarea_id, estado))

    def eliminar_tarea(self) -> None:
        tarea_id = IntPrompt.ask("Número de tarea a eliminar")
        self._ok(self.servicio.eliminar_tarea(self.usuario, self._proyecto(), tarea_id))

    # ---------------- Chain of Responsibility ----------------
    def aprobar_hito(self) -> None:
        proyecto = self._proyecto()
        self.servicio.verificar_permiso(self.usuario, "solicitar_aprobacion")
        nombre = Prompt.ask("Hito", choices=[h.nombre for h in proyecto.hitos])
        costo = FloatPrompt.ask("Costo ejecutado (S/)", default=0.0)
        conformidad = Confirm.ask("¿El cliente dio su conformidad?", default=True)
        aprobado = self.servicio.aprobar_hito(self.usuario, proyecto, nombre, costo, conformidad)
        hito = proyecto.buscar_hito(nombre)
        for paso in hito.historial_aprobacion:
            color = "green" if "APROBÓ" in paso else "red"
            consola.print(f"   [{color}]→ {paso}[/]")
        consola.print("[bold green]Hito aprobado ✔[/]" if aprobado else "[bold red]Hito rechazado ✖[/]")

    # ---------------- Decorator / auditoría / Singleton ----------------
    def ver_notificaciones(self) -> None:
        registros = self.servicio.registro_notificaciones[-20:]
        consola.print("\n".join(registros) if registros else "[yellow]Aún no hay notificaciones.[/]")

    def ver_auditoria(self) -> None:
        registros = self.servicio.auditoria()
        consola.print("\n".join(registros) if registros else "[yellow]Sin acciones registradas.[/]")

    def configuracion(self) -> None:
        config = self.servicio.config
        tabla = Table(title="Configuración global (instancia única)")
        tabla.add_column("Clave")
        tabla.add_column("Valor")
        for clave, valor in config.como_diccionario().items():
            tabla.add_row(clave, str(valor))
        consola.print(tabla)
        if Confirm.ask("¿Cambiar los canales globales de notificación?", default=False):
            elegidos = Prompt.ask(f"Canales separados por coma {canales_disponibles()}", default="in-app")
            config.establecer("canales_notificacion", [c.strip() for c in elegidos.split(",") if c.strip()])
            self._ok("Configuración actualizada para todo el sistema")


def main() -> None:
    try:
        AppConsola().ejecutar()
    except (KeyboardInterrupt, EOFError):
        consola.print("\n[cyan]Sesión finalizada.[/]")


if __name__ == "__main__":
    main()
