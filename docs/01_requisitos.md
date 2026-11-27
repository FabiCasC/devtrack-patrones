# 1. Análisis del sistema — DevTrack

## 1.1 Problema

Los equipos de desarrollo de software suelen gestionar sus proyectos con hojas de cálculo,
chats y correos sueltos. Esto provoca que:

- nadie sepa con certeza el avance real de un proyecto ni de cada hito;
- las tareas se pierdan o se modifiquen sin dejar rastro de quién lo hizo;
- los hitos se den por “cerrados” sin una aprobación formal del líder, el gerente y el cliente;
- cada rol (desarrollador, QA, cliente) reciba información que no necesita o le falte la que sí necesita;
- los avisos importantes no lleguen por el canal que cada persona usa (correo, SMS, aplicación).

**DevTrack** centraliza proyectos, tareas, hitos y aprobaciones, mostrando a cada rol su propia
vista y notificando los cambios por los canales que cada usuario elija.

## 1.2 Actores

| Actor | Descripción |
|---|---|
| **Desarrollador** | Crea tareas, las mueve por el tablero, deshace/rehace sus acciones. Ve sus tareas ordenadas por prioridad. |
| **QA** | Revisa tareas en estado “En revisión” y las pasa a “Terminada”. Ve solo la cola de revisión. |
| **Líder técnico** | Crea proyectos y tareas, solicita la aprobación de hitos y es el **primer** aprobador (calidad técnica). |
| **Gerente de proyecto** | Crea proyectos, solicita aprobaciones y es el **segundo** aprobador (plazo y presupuesto). |
| **Cliente** | Consulta el avance por hito (sin datos internos) y da la conformidad final (**tercer** aprobador). |
| **Sistema de notificaciones** | Actor secundario: entrega los avisos por in-app, email o SMS. |

## 1.3 Requisitos funcionales

| ID | Requisito | Patrón(es) involucrado(s) |
|---|---|---|
| **RF-01** | El sistema debe permitir crear un proyecto indicando nombre, cliente, fechas, presupuesto, metodología, repositorio, equipo e hitos, validando que los datos sean coherentes. | Builder |
| **RF-02** | El sistema debe ofrecer plantillas predefinidas de proyecto (Scrum con N sprints y MVP de 6 semanas). | Builder (Director) |
| **RF-03** | El sistema debe permitir crear tareas con título, prioridad, horas estimadas, responsable e hito asociado. | Command |
| **RF-04** | El sistema debe permitir mover una tarea entre los estados *Por hacer → En progreso → En revisión → Terminada*. | Command |
| **RF-05** | El sistema debe permitir eliminar una tarea. | Command |
| **RF-06** | El sistema debe permitir **deshacer** y **rehacer** las acciones sobre tareas. | Command |
| **RF-07** | El sistema debe registrar una **auditoría** con fecha, usuario y acción realizada. | Command |
| **RF-08** | El sistema debe mostrar una vista del proyecto distinta según el rol: desarrollador (sus tareas), QA (cola de revisión) y cliente (avance por hito). | Adapter |
| **RF-09** | El sistema debe gestionar la aprobación de hitos en orden **líder → gerente → cliente**; si un nivel rechaza, el hito queda rechazado y se registra el motivo. | Chain of Responsibility |
| **RF-10** | El sistema debe notificar a los usuarios los eventos relevantes (asignación de tarea, tarea lista para QA, resultado de aprobación, alta en proyecto) por in-app y, según su preferencia, email y/o SMS. | Decorator |
| **RF-11** | El sistema debe mantener una configuración global única (empresa, canales globales, máximo de horas por tarea, tolerancia de retraso) accesible desde cualquier módulo. | Singleton |
| **RF-12** | El sistema debe restringir las operaciones según el rol (por ejemplo, el cliente no puede crear tareas). | — (capa de servicio) |
| **RF-13** | El sistema debe calcular el porcentaje de avance del proyecto y de cada hito. | Adapter (vista cliente) |

## 1.4 Requisitos no funcionales

| ID | Tipo | Requisito |
|---|---|---|
| **RNF-01** | Mantenibilidad | El código sigue principios SOLID y está separado en capas (dominio, patrones, servicio, presentación). |
| **RNF-02** | Extensibilidad | Agregar un nuevo canal de notificación, un nuevo aprobador o una nueva vista por rol no debe requerir modificar las clases existentes (Abierto/Cerrado). |
| **RNF-03** | Confiabilidad | Los errores de negocio se manejan con excepciones propias (`DevTrackError`) y se muestran al usuario sin cerrar la aplicación. |
| **RNF-04** | Usabilidad | Interfaz de consola con menús numerados, tablas y colores; los mensajes están en español. |
| **RNF-05** | Seguridad | Control de acceso por rol en la capa de servicio; el cliente no ve horas ni responsables. |
| **RNF-06** | Calidad | Pruebas automatizadas con `pytest` que cubren cada patrón (23 casos). |
| **RNF-07** | Portabilidad | Funciona en Windows, macOS y Linux con Python 3.10 o superior. |
| **RNF-08** | Rendimiento | Las operaciones responden en menos de 1 segundo con datos en memoria. |
