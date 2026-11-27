from devtrack.dominio.modelos import EstadoTarea, Tarea
from devtrack.estructurales.notificaciones import (EmailDecorador, NotificadorDecorador,
                                                   NotificadorInApp, SMSDecorador,
                                                   construir_notificador, registrar_canal)
from devtrack.estructurales.vistas import (VistaClienteAdapter, VistaDesarrolladorAdapter,
                                           VistaQAAdapter, crear_vista)


# ---------------- Adapter ----------------
def test_adapter_elige_vista_segun_rol(proyecto, usuarios):
    assert isinstance(crear_vista(proyecto, usuarios["dev"]), VistaDesarrolladorAdapter)
    assert isinstance(crear_vista(proyecto, usuarios["qa"]), VistaQAAdapter)
    assert isinstance(crear_vista(proyecto, usuarios["cliente"]), VistaClienteAdapter)


def test_adapter_cliente_no_ve_datos_internos(proyecto, usuarios):
    tarea = Tarea("Login", responsable=usuarios["dev"], horas_estimadas=10,
                  estado=EstadoTarea.TERMINADA)
    proyecto.agregar_tarea(tarea)
    proyecto.hitos[0].tareas_ids.append(tarea.id)
    vista = crear_vista(proyecto, usuarios["cliente"])
    assert vista.columnas() == ["Hito", "Fecha límite", "Estado", "Avance"]
    assert vista.filas()[0][3] == "100%"
    assert "Horas" not in vista.columnas()


def test_adapter_qa_solo_ve_tareas_en_revision_o_terminadas(proyecto, usuarios):
    proyecto.agregar_tarea(Tarea("A", estado=EstadoTarea.EN_REVISION))
    proyecto.agregar_tarea(Tarea("B", estado=EstadoTarea.POR_HACER))
    filas = crear_vista(proyecto, usuarios["qa"]).filas()
    assert [f[1] for f in filas] == ["A"]


# ---------------- Decorator ----------------
def test_decorator_acumula_canales_en_orden(usuarios):
    notificador = SMSDecorador(EmailDecorador(NotificadorInApp()))
    entregas = notificador.enviar(usuarios["dev"], "Hola")
    assert entregas[0].startswith("[IN-APP]")
    assert entregas[1].startswith("[EMAIL")
    assert entregas[2].startswith("[SMS")


def test_decorator_sms_se_omite_si_no_hay_telefono(usuarios):
    entregas = construir_notificador(["sms"]).enviar(usuarios["qa"], "Hola")
    assert "omitido" in entregas[-1]


def test_decorator_permite_nuevo_canal_sin_modificar_codigo(usuarios):
    """Extensión (Abierto/Cerrado): se agrega Slack sin tocar notificaciones.py."""
    class SlackDecorador(NotificadorDecorador):
        def enviar(self, destinatario, mensaje):
            return super().enviar(destinatario, mensaje) + [f"[SLACK] {mensaje}"]

    registrar_canal("slack", SlackDecorador)
    entregas = construir_notificador(["slack"]).enviar(usuarios["dev"], "Deploy listo")
    assert entregas[-1] == "[SLACK] Deploy listo"
