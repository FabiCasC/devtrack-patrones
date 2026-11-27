# DevTrack – Sistema de Gestión de Proyectos de Desarrollo de Software

Proyecto final del curso **Diseño de Patrones** (UTP). DevTrack permite a los equipos de
software gestionar proyectos, tareas y asignaciones, controlar el avance de los hitos con
un flujo de aprobación, y notificar los cambios por in-app, email o SMS.

El objetivo es aplicar **patrones de diseño creacionales, estructurales y de comportamiento**
con código limpio, probado y siguiendo los principios SOLID.

## Patrones aplicados

| Tipo | Patrón | Uso en DevTrack | Código |
|---|---|---|---|
| Creacional | **Singleton** | Configuración global única del sistema | [`configuracion.py`](devtrack/creacionales/configuracion.py) |
| Creacional | **Builder** | Construcción paso a paso de un proyecto complejo (con Director para plantillas Scrum y MVP) | [`builder.py`](devtrack/creacionales/builder.py) |
| Estructural | **Adapter** | Vistas del proyecto adaptadas al rol: desarrollador, QA y cliente | [`vistas.py`](devtrack/estructurales/vistas.py) |
| Estructural | **Decorator** | Notificaciones personalizables: in-app + email + SMS | [`notificaciones.py`](devtrack/estructurales/notificaciones.py) |
| Comportamiento | **Command** | Crear, mover y eliminar tareas, con deshacer/rehacer y auditoría | [`comandos.py`](devtrack/comportamiento/comandos.py) |
| Comportamiento | **Chain of Responsibility** | Aprobación de hitos: líder → gerente → cliente | [`aprobacion.py`](devtrack/comportamiento/aprobacion.py) |

La justificación completa de cada patrón está en
[docs/03_justificacion_patrones.md](docs/03_justificacion_patrones.md).

## Requisitos

- Python **3.10** o superior
- Dependencias: `rich` (interfaz de consola) y `pytest` (pruebas)

## Instalación

```bash
git clone https://github.com/FabiCasC/devtrack-patrones.git
cd devtrack-patrones
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Elige un usuario de demostración (cada uno tiene un rol distinto) y usa el menú numerado.
El paso a paso está en el [manual de usuario](docs/04_manual_usuario.md).

## Pruebas

```bash
python -m pytest -v
```

Son 23 pruebas unitarias y de integración que validan el comportamiento de cada patrón
(`tests/`).

## Estructura del proyecto

```
devtrack-patrones/
├── main.py                      # Punto de entrada
├── devtrack/
│   ├── dominio/modelos.py       # Proyecto, Tarea, Hito, Usuario, enums
│   ├── creacionales/            # Singleton, Builder
│   ├── estructurales/           # Adapter, Decorator
│   ├── comportamiento/          # Command, Chain of Responsibility
│   ├── servicios/               # Capa de aplicación (orquesta patrones y permisos)
│   ├── presentacion/consola.py  # Interfaz de consola (rich)
│   ├── datos_demo.py            # Datos para la demostración
│   └── excepciones.py           # Errores propios del dominio
├── tests/                       # Pruebas con pytest
└── docs/                        # Requisitos, UML, justificación de patrones y manual
```

## Documentación

1. [Requisitos y actores](docs/01_requisitos.md)
2. [Diagramas UML: clases, secuencia, estados y actividad](docs/02_diagramas_uml.md)
3. [Justificación de patrones](docs/03_justificacion_patrones.md)
4. [Manual de usuario](docs/04_manual_usuario.md)

## Equipo

| Integrante | Rol en el equipo |
|---|---|
| _(completar)_ | |
| _(completar)_ | |
| _(completar)_ | |
| _(completar)_ | |
