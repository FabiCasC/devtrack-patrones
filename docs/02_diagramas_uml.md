# 2. Diseño — Diagramas UML

Los diagramas están en sintaxis **Mermaid** (GitHub los dibuja automáticamente).

## 2.1 Arquitectura en capas

```mermaid
flowchart TB
    P["Presentación<br/>presentacion/consola.py"] --> S["Servicio<br/>servicios/servicio_proyectos.py"]
    S --> C["Creacionales<br/>Singleton · Builder"]
    S --> E["Estructurales<br/>Adapter · Decorator"]
    S --> B["Comportamiento<br/>Command · Chain of Responsibility"]
    C --> D["Dominio<br/>Proyecto · Tarea · Hito · Usuario"]
    E --> D
    B --> D
```

La presentación solo conoce al servicio. El servicio orquesta los patrones. Los patrones
trabajan sobre el dominio, que no depende de nadie.

## 2.2 Diagrama de clases

```mermaid
classDiagram
    direction LR

    class Proyecto {
        +nombre: str
        +cliente: str
        +presupuesto: float
        +equipo: list~Usuario~
        +hitos: list~Hito~
        +tareas: list~Tarea~
        +agregar_tarea(t)
        +quitar_tarea(id) Tarea
        +buscar_tarea(id) Tarea
        +avance() float
    }
    class Tarea {
        +id: int
        +titulo: str
        +prioridad: Prioridad
        +estado: EstadoTarea
        +horas_estimadas: float
    }
    class Hito {
        +nombre: str
        +fecha_limite: date
        +estado: EstadoHito
        +historial_aprobacion: list
    }
    class Usuario {
        +nombre: str
        +email: str
        +rol: Rol
        +canales: list
    }
    Proyecto "1" *-- "*" Tarea
    Proyecto "1" *-- "*" Hito
    Proyecto "1" o-- "*" Usuario
    Tarea --> Usuario : responsable

    %% Singleton
    class ConfiguracionSistema {
        -_instance$ ConfiguracionSistema
        +__new__(cls)
        +obtener(clave)
        +establecer(clave, valor)
    }

    %% Builder
    class ConstructorProyecto {
        <<abstract>>
        +con_nombre(n)
        +con_fechas(i, f)
        +agregar_hito(n, f)
        +build() Proyecto
    }
    class ProyectoBuilder
    class DirectorProyecto {
        +construir_proyecto_scrum()
        +construir_mvp()
    }
    ConstructorProyecto <|-- ProyectoBuilder
    DirectorProyecto o-- ConstructorProyecto
    ProyectoBuilder ..> Proyecto : crea

    %% Adapter
    class VistaProyecto {
        <<abstract>>
        +titulo()
        +columnas()
        +filas()
    }
    VistaProyecto <|-- VistaDesarrolladorAdapter
    VistaProyecto <|-- VistaQAAdapter
    VistaProyecto <|-- VistaClienteAdapter
    VistaDesarrolladorAdapter o-- Proyecto : adaptee
    VistaQAAdapter o-- Proyecto : adaptee
    VistaClienteAdapter o-- Proyecto : adaptee

    %% Decorator
    class Notificador {
        <<abstract>>
        +enviar(usuario, mensaje) list
    }
    class NotificadorDecorador {
        -_envuelto: Notificador
    }
    Notificador <|-- NotificadorInApp
    Notificador <|-- NotificadorDecorador
    NotificadorDecorador o-- Notificador
    NotificadorDecorador <|-- EmailDecorador
    NotificadorDecorador <|-- SMSDecorador

    %% Command
    class Comando {
        <<abstract>>
        +ejecutar() str
        +deshacer() str
    }
    class GestorComandos {
        -_hechos: list
        -_deshechos: list
        +ejecutar(c)
        +deshacer()
        +rehacer()
    }
    Comando <|-- CrearTareaComando
    Comando <|-- MoverTareaComando
    Comando <|-- EliminarTareaComando
    GestorComandos o-- Comando
    CrearTareaComando --> Proyecto : receptor
    MoverTareaComando --> Proyecto : receptor
    EliminarTareaComando --> Proyecto : receptor

    %% Chain of Responsibility
    class ManejadorAprobacion {
        <<abstract>>
        -_siguiente: ManejadorAprobacion
        +establecer_siguiente(m)
        +manejar(solicitud) bool
        +evaluar(solicitud)*
    }
    ManejadorAprobacion o-- ManejadorAprobacion : siguiente
    ManejadorAprobacion <|-- LiderTecnicoAprobador
    ManejadorAprobacion <|-- GerenteAprobador
    ManejadorAprobacion <|-- ClienteAprobador

    class ServicioProyectos {
        +crear_proyecto()
        +crear_tarea()
        +mover_tarea()
        +deshacer()
        +vista_para()
        +aprobar_hito()
    }
    ServicioProyectos --> ConfiguracionSistema
    ServicioProyectos ..> ProyectoBuilder
    ServicioProyectos --> GestorComandos
    ServicioProyectos ..> VistaProyecto
    ServicioProyectos ..> Notificador
    ServicioProyectos ..> ManejadorAprobacion
```

## 2.3 Diagrama de secuencia — Mover tarea a revisión (Command + Decorator)

```mermaid
sequenceDiagram
    actor Dev as Desarrollador
    participant UI as Consola
    participant S as ServicioProyectos
    participant G as GestorComandos (Invocador)
    participant C as MoverTareaComando
    participant P as Proyecto (Receptor)
    participant N as SMSDecorador(NotificadorInApp)

    Dev->>UI: opción 5, tarea #4, EN_REVISION
    UI->>S: mover_tarea(dev, proyecto, 4, EN_REVISION)
    S->>S: verificar permiso del rol
    S->>G: ejecutar(MoverTareaComando)
    G->>C: ejecutar()
    C->>P: buscar_tarea(4)
    P-->>C: tarea
    C->>C: guarda estado anterior y cambia estado
    C-->>G: "Tarea #4 movida…"
    G->>G: historial.push + auditoría
    S->>N: enviar(QA, "lista para revisión")
    N-->>S: [IN-APP, SMS]
    S-->>UI: resultado
    UI-->>Dev: ✔ Tarea #4 movida
```

## 2.4 Diagrama de secuencia — Aprobación de hito (Chain of Responsibility)

```mermaid
sequenceDiagram
    actor L as Líder técnico
    participant S as ServicioProyectos
    participant LT as LiderTecnicoAprobador
    participant GE as GerenteAprobador
    participant CL as ClienteAprobador

    L->>S: aprobar_hito("Sprint 1", costo, conformidad)
    S->>LT: manejar(solicitud)
    LT->>LT: ¿todas las tareas terminadas?
    alt hay tareas pendientes
        LT-->>S: False (RECHAZADO, cadena cortada)
    else todo terminado
        LT->>GE: manejar(solicitud)
        GE->>GE: ¿dentro de plazo y presupuesto?
        alt fuera de plazo o presupuesto
            GE-->>S: False (RECHAZADO)
        else OK
            GE->>CL: manejar(solicitud)
            CL->>CL: ¿conformidad del cliente?
            CL-->>S: True (APROBADO) / False
        end
    end
    S->>S: notificar_equipo(resultado)
```

## 2.5 Diagrama de estados — Tarea

```mermaid
stateDiagram-v2
    [*] --> PorHacer : CrearTareaComando
    PorHacer --> EnProgreso : MoverTareaComando
    EnProgreso --> EnRevision : MoverTareaComando (notifica a QA)
    EnRevision --> EnProgreso : QA devuelve
    EnRevision --> Terminada : QA aprueba
    Terminada --> EnRevision : reabrir
    PorHacer --> [*] : EliminarTareaComando
    EnProgreso --> [*] : EliminarTareaComando
    note right of EnProgreso : Cualquier transición\npuede deshacerse (undo)
```

## 2.6 Diagrama de estados — Hito

```mermaid
stateDiagram-v2
    [*] --> Pendiente
    Pendiente --> EnAprobacion : solicitar_aprobacion
    EnAprobacion --> Aprobado : líder ✔ gerente ✔ cliente ✔
    EnAprobacion --> Rechazado : algún nivel ✖
    Rechazado --> EnAprobacion : se corrige y se vuelve a solicitar
    Aprobado --> [*]
```

## 2.7 Diagrama de actividad — Crear proyecto (Builder)

```mermaid
flowchart TD
    A([Inicio]) --> B[Ingresar nombre y cliente]
    B --> C{¿Plantilla?}
    C -- Scrum --> D[Director: construir_proyecto_scrum<br/>1 hito por sprint]
    C -- MVP --> E[Director: construir_mvp<br/>Análisis, Desarrollo, Entrega]
    C -- Personalizado --> F[Builder paso a paso:<br/>fechas, presupuesto, metodología, hitos]
    D --> G[build]
    E --> G
    F --> G
    G --> H{¿Datos válidos?}
    H -- No --> I[ValidacionError con todos los errores] --> B
    H -- Sí --> J[Registrar proyecto y notificar al equipo]
    J --> K([Fin])
```
