# 4. Manual de usuario (breve)

## 4.1 Iniciar el sistema

```bash
pip install -r requirements.txt
python main.py
```

Al iniciar se muestra la lista de usuarios de demostración. Escribe el número del usuario
con el que quieres entrar:

| # | Usuario | Rol | Canales de notificación |
|---|---|---|---|
| 1 | Ana Torres | Líder técnico | in-app, email |
| 2 | Bruno Díaz | Desarrollador | in-app, email, SMS |
| 3 | Carla Ruiz | Desarrollador | in-app |
| 4 | Diego Paz | QA | in-app, SMS |
| 5 | Elena Vega | Gerente de proyecto | in-app, email |
| 6 | Felipe Ríos | Cliente | in-app, email |

Ya viene cargado el proyecto **“App Cafetería”**, con 3 sprints y 5 tareas.

## 4.2 Menú principal

| Opción | Qué hace | ¿Quién puede? |
|---|---|---|
| 1 | Ver el tablero del proyecto: cada rol ve una vista distinta | Todos |
| 2 | Seleccionar otro proyecto | Todos |
| 3 | Crear proyecto con plantilla Scrum, MVP o personalizado | Líder, Gerente |
| 4 | Crear tarea (título, prioridad, horas, responsable, hito) | Desarrollador, Líder, Gerente |
| 5 | Mover tarea de estado (`POR_HACER`, `EN_PROGRESO`, `EN_REVISION`, `TERMINADA`) | Desarrollador, QA, Líder, Gerente |
| 6 | Eliminar tarea | Desarrollador, Líder, Gerente |
| 7 | Deshacer tu última acción | Quien hizo la acción |
| 8 | Rehacer la acción deshecha | Quien hizo la acción |
| 9 | Solicitar aprobación de un hito (líder → gerente → cliente) | Líder, Gerente |
| 10 | Ver las últimas notificaciones enviadas | Todos |
| 11 | Ver la auditoría (fecha, usuario y acción) | Todos |
| 12 | Ver y cambiar la configuración global | Todos |
| 13 | Cambiar de usuario | Todos |
| 0 | Salir | — |

Si un rol intenta algo no permitido, o los datos no son válidos, el sistema muestra un
mensaje en rojo (✖) y vuelve al menú sin cerrarse.

## 4.3 Guion sugerido para la demostración en vivo

**Flujo feliz**

1. Entrar como **Bruno (2)** → opción **1**: ve sus tareas ordenadas por prioridad.
2. Opción **5** → tarea `4` → `EN_REVISION`. Opción **10**: Diego (QA) recibió el aviso
   por in-app y SMS (*Decorator*).
3. Opción **7** (deshacer) y opción **8** (rehacer). Opción **11**: la auditoría muestra
   todo (*Command*).
4. Opción **13** → entrar como **Diego (4)** → opción **1**: la vista de QA solo muestra la
   cola de revisión (*Adapter*). Opción **5** → tarea `4` → `TERMINADA`.
5. Opción **13** → entrar como **Ana (1)** → opción **9** → `Sprint 1`, costo `5000`, conformidad
   `y`: el hito pasa por líder ✔, gerente ✔ y cliente ✔ (*Chain of Responsibility*).
6. Opción **13** → entrar como **Felipe (6)** → opción **1**: el cliente solo ve el avance
   por hito.

**Manejo de errores y extensión**

7. Como **Ana**, opción **9** → `Sprint 2`: el líder lo **rechaza** porque hay tareas sin
   terminar, y la cadena se corta.
8. Como **Felipe (cliente)**, opción **4**: *“El rol Cliente no puede realizar gestionar
   tareas”*.
9. Opción **12**: cambiar los canales globales a `in-app,email`. Como todos usan la misma
   instancia de configuración (*Singleton*), desde ese momento todos reciben email.
10. Opción **3** con plantilla **personalizado** y una fecha de hito fuera del rango: el
    *Builder* muestra los errores de validación.
11. Extensión sin modificar código: `pytest -k nuevo_canal` agrega un canal **Slack**
    mediante un nuevo decorador.
