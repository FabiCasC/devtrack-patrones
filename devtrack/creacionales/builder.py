"""Patrón BUILDER — Construcción paso a paso de un Proyecto complejo.

Problema que resuelve: un Proyecto tiene muchos atributos (fechas, presupuesto,
metodología, repositorio, equipo, hitos...). Un constructor con 10 parámetros es
difícil de leer y fácil de usar mal. El Builder permite armarlo por pasos,
validando al final con ``build()``.

Participantes (nombres del curso, Sesión 07):
- Builder ............ ConstructorProyecto (clase abstracta con abc)
- ConcreteBuilder .... ProyectoBuilder
- Director ........... DirectorProyecto (configuraciones predefinidas)
- Product ............ Proyecto
- Client ............. ServicioProyectos / consola
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta

from devtrack.creacionales.configuracion import ConfiguracionSistema
from devtrack.dominio.modelos import Hito, Proyecto, Usuario
from devtrack.excepciones import ValidacionError


class ConstructorProyecto(ABC):
    """Builder: declara los pasos de construcción."""

    @abstractmethod
    def con_nombre(self, nombre: str) -> "ConstructorProyecto": ...

    @abstractmethod
    def con_descripcion(self, descripcion: str) -> "ConstructorProyecto": ...

    @abstractmethod
    def para_cliente(self, cliente: str) -> "ConstructorProyecto": ...

    @abstractmethod
    def con_fechas(self, inicio: date, fin: date) -> "ConstructorProyecto": ...

    @abstractmethod
    def con_presupuesto(self, monto: float) -> "ConstructorProyecto": ...

    @abstractmethod
    def con_metodologia(self, metodologia: str) -> "ConstructorProyecto": ...

    @abstractmethod
    def con_repositorio(self, url: str) -> "ConstructorProyecto": ...

    @abstractmethod
    def agregar_miembro(self, usuario: Usuario) -> "ConstructorProyecto": ...

    @abstractmethod
    def agregar_hito(self, nombre: str, fecha_limite: date) -> "ConstructorProyecto": ...

    @abstractmethod
    def build(self) -> Proyecto: ...


class ProyectoBuilder(ConstructorProyecto):
    """ConcreteBuilder: cada paso retorna ``self`` para encadenar llamadas."""

    def __init__(self) -> None:
        self.reiniciar()

    def reiniciar(self) -> None:
        self._nombre = ""
        self._descripcion = ""
        self._cliente = ""
        self._inicio: date | None = None
        self._fin: date | None = None
        self._presupuesto = 0.0
        self._metodologia = "Scrum"
        self._repositorio = ""
        self._equipo: list[Usuario] = []
        self._hitos: list[Hito] = []

    def con_nombre(self, nombre: str) -> "ProyectoBuilder":
        self._nombre = nombre.strip()
        return self

    def con_descripcion(self, descripcion: str) -> "ProyectoBuilder":
        self._descripcion = descripcion
        return self

    def para_cliente(self, cliente: str) -> "ProyectoBuilder":
        self._cliente = cliente
        return self

    def con_fechas(self, inicio: date, fin: date) -> "ProyectoBuilder":
        self._inicio, self._fin = inicio, fin
        return self

    def con_presupuesto(self, monto: float) -> "ProyectoBuilder":
        self._presupuesto = monto
        return self

    def con_metodologia(self, metodologia: str) -> "ProyectoBuilder":
        self._metodologia = metodologia
        return self

    def con_repositorio(self, url: str) -> "ProyectoBuilder":
        self._repositorio = url
        return self

    def agregar_miembro(self, usuario: Usuario) -> "ProyectoBuilder":
        self._equipo.append(usuario)
        return self

    def agregar_hito(self, nombre: str, fecha_limite: date) -> "ProyectoBuilder":
        self._hitos.append(Hito(nombre=nombre, fecha_limite=fecha_limite))
        return self

    def build(self) -> Proyecto:
        self._validar()
        proyecto = Proyecto(
            nombre=self._nombre,
            descripcion=self._descripcion,
            cliente=self._cliente,
            fecha_inicio=self._inicio,  # type: ignore[arg-type]
            fecha_fin=self._fin,  # type: ignore[arg-type]
            presupuesto=self._presupuesto,
            metodologia=self._metodologia,
            repositorio=self._repositorio,
            equipo=list(self._equipo),
            hitos=list(self._hitos),
        )
        self.reiniciar()
        return proyecto

    def _validar(self) -> None:
        errores = []
        if not self._nombre:
            errores.append("el nombre es obligatorio")
        if not self._cliente:
            errores.append("el cliente es obligatorio")
        if self._inicio is None or self._fin is None:
            errores.append("las fechas son obligatorias")
        elif self._fin < self._inicio:
            errores.append("la fecha de fin no puede ser anterior a la de inicio")
        if self._presupuesto < 0:
            errores.append("el presupuesto no puede ser negativo")
        for hito in self._hitos:
            if self._fin and hito.fecha_limite > self._fin:
                errores.append(f"el hito '{hito.nombre}' vence después del fin del proyecto")
        if errores:
            raise ValidacionError("No se puede crear el proyecto: " + "; ".join(errores) + ".")


class DirectorProyecto:
    """Director: conoce recetas predefinidas de proyectos."""

    def __init__(self, builder: ConstructorProyecto) -> None:
        self._builder = builder

    def construir_proyecto_scrum(self, nombre: str, cliente: str, inicio: date,
                                 sprints: int = 4) -> Proyecto:
        """Proyecto Scrum con un hito por sprint de 2 semanas."""
        fin = inicio + timedelta(weeks=2 * sprints)
        self._builder.con_nombre(nombre).para_cliente(cliente).con_fechas(inicio, fin)
        self._builder.con_metodologia("Scrum")
        for n in range(1, sprints + 1):
            self._builder.agregar_hito(f"Sprint {n}", inicio + timedelta(weeks=2 * n))
        return self._builder.build()

    def construir_mvp(self, nombre: str, cliente: str, inicio: date) -> Proyecto:
        """MVP corto de 6 semanas con los hitos clásicos."""
        limite = ConfiguracionSistema().obtener("limite_presupuesto_lider")
        return (self._builder.con_nombre(nombre).para_cliente(cliente)
                .con_fechas(inicio, inicio + timedelta(weeks=6))
                .con_metodologia("Kanban").con_presupuesto(limite)
                .agregar_hito("Análisis", inicio + timedelta(weeks=1))
                .agregar_hito("Desarrollo", inicio + timedelta(weeks=4))
                .agregar_hito("Entrega", inicio + timedelta(weeks=6))
                .build())
