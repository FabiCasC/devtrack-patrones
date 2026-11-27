# 3. Justificación de los patrones de diseño

DevTrack aplica **6 patrones**: 2 creacionales, 2 estructurales y 2 de comportamiento, tal
como recomienda el enunciado para el proyecto 4. Para cada uno se explica el problema que
resuelve, por qué se eligió frente a otras alternativas, cuándo **no** convendría usarlo y
el fragmento de código real donde se aplica.

Las definiciones, nombres de participantes y pasos de implementación siguen los materiales
del curso (Python con el módulo `abc`, Sesiones 06 a 13).

| # | Patrón | Tipo | Archivo | Requisitos |
|---|---|---|---|---|
| 1 | Singleton | Creacional | `devtrack/creacionales/configuracion.py` | RF-11 |
| 2 | Builder | Creacional | `devtrack/creacionales/builder.py` | RF-01, RF-02 |
| 3 | Adapter | Estructural | `devtrack/estructurales/vistas.py` | RF-08, RF-13 |
| 4 | Decorator | Estructural | `devtrack/estructurales/notificaciones.py` | RF-10 |
| 5 | Command | Comportamiento | `devtrack/comportamiento/comandos.py` | RF-03 a RF-07 |
| 6 | Chain of Responsibility | Comportamiento | `devtrack/comportamiento/aprobacion.py` | RF-09 |

---

## 3.1 Singleton — Configuración global del sistema

**Intención (Sesión 06):** garantizar que una clase tenga una única instancia y
proporcionar un punto de acceso global a ella.

**Problema en DevTrack:** el servicio, los aprobadores y el Director del Builder necesitan
leer los mismos parámetros (máximo de horas por tarea, canales globales, tolerancia de
retraso). Si cada módulo tuviera su propia copia, un cambio hecho desde el menú de
configuración no se vería en el resto del sistema.

**Implementación** (variable de clase `_instance` + `__new__`, como en el curso):

```python
class ConfiguracionSistema:
    _instance: "ConfiguracionSistema | None" = None

    def __new__(cls) -> "ConfiguracionSistema":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._inicializar()
        return cls._instance
```

Uso en otro módulo, sin pasar el objeto como parámetro:

```python
# devtrack/comportamiento/aprobacion.py — GerenteAprobador
limite = ConfiguracionSistema().obtener("dias_tolerancia_retraso", 0)
```

**¿Por qué Singleton y no una variable global o un módulo?** Una variable global puede
reasignarse por error desde cualquier parte. El Singleton encapsula el acceso
(`obtener`/`establecer`) y crea la configuración solo cuando se pide por primera vez.

**Cuándo NO usarlo:** el curso advierte que **vulnera el SRP** (controla su instancia y
además ofrece acceso global), genera acoplamiento y **dificulta las pruebas**. Por eso:
(1) solo se usa para la configuración, no para los servicios; y (2) se agregó
`_reiniciar()` exclusivamente para que cada prueba empiece con la configuración limpia
(`tests/conftest.py`).

---

## 3.2 Builder — Construcción paso a paso de un proyecto

**Intención (Sesión 07):** separar la construcción de un objeto complejo de su
representación, para construirlo paso a paso y obtener distintas representaciones con el
mismo proceso.

**Problema en DevTrack:** un `Proyecto` tiene 11 atributos (nombre, cliente, fechas,
presupuesto, metodología, repositorio, equipo, hitos…). Un constructor con tantos
parámetros es difícil de leer, y las reglas de validación (fin posterior al inicio, hitos
dentro del rango del proyecto) quedarían dispersas.

**Participantes:** `ConstructorProyecto` (Builder, abstracto), `ProyectoBuilder`
(ConcreteBuilder), `DirectorProyecto` (Director), `Proyecto` (Product) y
`ServicioProyectos`/consola (Client).

```python
proyecto = (ProyectoBuilder()
            .con_nombre("CRM").para_cliente("ACME")
            .con_fechas(hoy, hoy + timedelta(weeks=4))
            .con_presupuesto(5000)
            .agregar_hito("Entrega", hoy + timedelta(weeks=4))
            .build())          # valida todo y crea el Product
```

El **Director** encapsula recetas que se repiten:

```python
def construir_proyecto_scrum(self, nombre, cliente, inicio, sprints=4) -> Proyecto:
    fin = inicio + timedelta(weeks=2 * sprints)
    self._builder.con_nombre(nombre).para_cliente(cliente).con_fechas(inicio, fin)
    for n in range(1, sprints + 1):
        self._builder.agregar_hito(f"Sprint {n}", inicio + timedelta(weeks=2 * n))
    return self._builder.build()
```

**¿Por qué Builder y no Factory Method?** Factory Method decide *qué clase* crear en un
solo paso; aquí siempre se crea la misma clase (`Proyecto`), pero con **muchos pasos
opcionales** y validación al final. Ese es justo el caso del Builder.

**Cuándo NO usarlo:** para objetos simples, como `Tarea` (pocos campos), donde basta un
constructor normal. El curso lo indica como desventaja: agrega clases y complejidad.

---

## 3.3 Adapter — Vistas de datos por rol

**Intención (Sesión 08):** resolver la incompatibilidad entre la interfaz que espera el
cliente y una clase existente que no se quiere modificar.

**Problema en DevTrack:** la consola solo sabe dibujar algo con `titulo()`, `columnas()` y
`filas()`. El `Proyecto` del dominio tiene otra interfaz (listas de tareas, hitos, avance).
Además, cada rol necesita los datos de forma distinta: el desarrollador ve horas y
prioridad, QA ve la cola de revisión y el cliente solo ve el avance por hito, sin datos
internos.

**Participantes:** `VistaProyecto` (Target), `Proyecto` (Adaptee) y
`VistaDesarrolladorAdapter`, `VistaQAAdapter` y `VistaClienteAdapter` (Adapter).
Se usa el **adaptador de objeto**: el adaptador contiene al Adaptee por composición.

```python
class VistaClienteAdapter(VistaProyecto):
    def __init__(self, proyecto: Proyecto) -> None:
        self._proyecto = proyecto                       # Adaptee por composición

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
```

**¿Por qué Adapter y no Facade?** Facade simplifica *muchas* llamadas a un subsistema; aquí
el problema es que **una** clase existente (`Proyecto`) no encaja con el contrato que
espera la interfaz. Tampoco se modificó `Proyecto` para agregarle métodos de presentación,
porque eso mezclaría responsabilidades (SRP).

**Cuándo NO usarlo:** si las interfaces ya fueran compatibles, o si controláramos ambas
clases y fuera más simple cambiar una de ellas.

---

## 3.4 Decorator — Notificaciones personalizables

**Intención (Sesión 09):** añadir funcionalidades a un objeto de forma dinámica, sin
modificar su estructura y evitando el abuso de la herencia.

**Problema en DevTrack:** cada usuario elige sus canales (in-app siempre; email y/o SMS
opcionales). Con herencia habría que crear una clase por combinación
(`EmailSms`, `EmailInApp`, `EmailSmsInApp`…), y la cantidad crece cada vez que aparece un
canal nuevo.

**Participantes:** `Notificador` (Componente), `NotificadorInApp` (ComponenteConcreto),
`NotificadorDecorador` (Decorador) y `EmailDecorador`, `SMSDecorador` (DecoradorConcreto).

```python
class EmailDecorador(NotificadorDecorador):
    def enviar(self, destinatario: Usuario, mensaje: str) -> list[str]:
        entregas = super().enviar(destinatario, mensaje)   # delega al envuelto
        entregas.append(f"[EMAIL → {destinatario.email}] {mensaje}")
        return entregas

# En tiempo de ejecución, según las preferencias del usuario:
notificador = SMSDecorador(EmailDecorador(NotificadorInApp()))
```

**Principio Abierto/Cerrado (OCP):** la Sesión 09 lo destaca como ventaja principal. En
DevTrack se demuestra con `registrar_canal`: se puede agregar Slack **sin modificar**
`notificaciones.py` (ver `tests/test_estructurales.py::test_decorator_permite_nuevo_canal_sin_modificar_codigo`).

**¿Por qué Decorator y no Strategy?** Strategy elige **una** forma de enviar; aquí se
necesitan **varias acumuladas** a la vez (in-app + email + SMS).

**Cuándo NO usarlo:** cuando solo existe una forma fija de notificar. Como desventaja, el
curso señala que muchos envoltorios hacen más difícil depurar; por eso cada decorador hace
una sola cosa y devuelve la lista de entregas, para poder rastrearlas.

---

## 3.5 Command — Acciones sobre tareas (crear, mover, eliminar)

**Intención (Sesión 13):** convertir una solicitud en un objeto independiente que contiene
toda la información de la operación, desacoplando a quien la pide de quien la ejecuta.

**Problema en DevTrack:** el usuario necesita **deshacer/rehacer** cambios en el tablero y
el equipo necesita una **auditoría** de quién hizo qué. Si la consola llamara
directamente a `proyecto.tareas.remove(...)`, no habría forma de revertir ni de registrar
la acción de manera uniforme.

**Participantes:** `Comando` (abstracto, con `ejecutar()`), `CrearTareaComando`,
`MoverTareaComando` y `EliminarTareaComando` (ComandoConcreto), `Proyecto` (Receptor),
`GestorComandos` (Invocador) y `ServicioProyectos` (Cliente).

```python
class MoverTareaComando(Comando):
    def ejecutar(self) -> str:
        tarea = self._proyecto.buscar_tarea(self._tarea_id)
        self._estado_anterior = tarea.estado          # guarda lo necesario para deshacer
        tarea.estado = self._nuevo_estado
        return f"Tarea #{tarea.id} movida: {self._estado_anterior.value} → {tarea.estado.value}"

    def deshacer(self) -> str:
        tarea = self._proyecto.buscar_tarea(self._tarea_id)
        tarea.estado = self._estado_anterior
        return f"Tarea #{tarea.id} regresó a '{tarea.estado.value}'"
```

```python
class GestorComandos:                       # Invocador
    def ejecutar(self, comando: Comando) -> str:
        resultado = comando.ejecutar()      # si lanza excepción, no entra al historial
        self._hechos.append(comando)
        self._deshechos.clear()
        self._registrar(resultado)          # auditoría
        return resultado
```

**¿Por qué Command y no Memento?** Memento guardaría una copia de todo el proyecto en cada
cambio. Command solo guarda lo mínimo para revertir esa acción (por ejemplo, el estado
anterior) y además permite auditar y, más adelante, encolar acciones.

**Cuándo NO usarlo:** para operaciones de solo lectura (ver tablero, ver notificaciones),
que no necesitan deshacerse ni auditarse; por eso esas opciones no son comandos.

---

## 3.6 Chain of Responsibility — Aprobación de hitos

> En los materiales del curso, Chain of Responsibility aparece en el mapa conceptual de
> patrones de comportamiento (Sesión 12), sin desarrollo detallado. Se aplicó con la
> estructura clásica de GoF: Manejador, ManejadorConcreto y Cliente.

**Intención:** evitar acoplar al emisor de una solicitud con su receptor, dando a varios
objetos la oportunidad de atenderla; los manejadores se encadenan y cada uno decide si la
procesa y si la pasa al siguiente.

**Problema en DevTrack:** un hito se cierra solo si lo aprueban, **en orden**, el líder
técnico (calidad), el gerente (plazo y presupuesto) y el cliente (conformidad). Con un solo
método lleno de `if`, agregar un nuevo nivel (por ejemplo, QA o Seguridad) obligaría a
modificarlo.

**Participantes:** `ManejadorAprobacion` (Manejador abstracto), `LiderTecnicoAprobador`,
`GerenteAprobador` y `ClienteAprobador` (ManejadorConcreto) y `ServicioProyectos` (Cliente).

```python
class ManejadorAprobacion(ABC):
    def manejar(self, solicitud: SolicitudAprobacion) -> bool:
        aprobado, motivo = self.evaluar(solicitud)
        solicitud.hito.historial_aprobacion.append(
            f"{self.rol} {'APROBÓ' if aprobado else 'RECHAZÓ'}: {motivo}")
        if not aprobado:
            solicitud.hito.estado = EstadoHito.RECHAZADO
            return False                                # corta la cadena
        if self._siguiente:
            return self._siguiente.manejar(solicitud)   # pasa al siguiente eslabón
        solicitud.hito.estado = EstadoHito.APROBADO
        return True

def crear_cadena_aprobacion() -> ManejadorAprobacion:
    lider = LiderTecnicoAprobador()
    lider.establecer_siguiente(GerenteAprobador()).establecer_siguiente(ClienteAprobador())
    return lider
```

**¿Por qué Chain of Responsibility y no State?** State modela cómo cambia el
comportamiento de *un* objeto según su estado. Aquí lo importante son **varios
responsables independientes** que revisan la misma solicitud en secuencia y pueden cortar
el flujo. Agregar un aprobador es crear una clase y enlazarla, sin tocar las demás (OCP).

**Cuándo NO usarlo:** si siempre hubiera un solo aprobador o el orden no importara.
Desventaja: una solicitud puede terminar sin ser atendida si la cadena está mal armada;
por eso la cadena se construye en un único lugar (`crear_cadena_aprobacion`).

---

## 3.7 Principios SOLID aplicados

| Principio | Dónde se ve |
|---|---|
| **S** — Responsabilidad única | Cada aprobador valida una sola regla; cada decorador agrega un solo canal; la consola solo presenta y el servicio solo orquesta. |
| **O** — Abierto/Cerrado | Nuevos canales (`registrar_canal`), aprobadores o vistas por rol se agregan con clases nuevas, sin modificar las existentes. |
| **L** — Sustitución de Liskov | Cualquier `VistaProyecto`, `Notificador`, `Comando` o `ManejadorAprobacion` puede reemplazar a su clase base sin romper a quien lo usa. |
| **I** — Segregación de interfaces | Las interfaces abstractas son pequeñas: `Comando` (2 métodos), `Notificador` (1), `VistaProyecto` (3). |
| **D** — Inversión de dependencias | La consola y el servicio dependen de abstracciones (`VistaProyecto`, `Notificador`, `Comando`), no de clases concretas. |
