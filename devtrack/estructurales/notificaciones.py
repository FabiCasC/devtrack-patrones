"""Patrón DECORATOR — Notificaciones personalizables (in-app, email, SMS).

Problema que resuelve: cada usuario elige por qué canales recibe avisos. Con
herencia tendríamos una clase por combinación (EmailSms, EmailInApp,
EmailSmsInApp...). Con Decorator envolvemos el notificador base con tantos
canales como se quiera, en tiempo de ejecución y sin tocar el código existente
(Principio Abierto/Cerrado, como indica la Sesión 09).

Participantes (nombres del curso, Sesión 09):
- Componente ............ Notificador (abc)
- ComponenteConcreto .... NotificadorInApp
- Decorador ............. NotificadorDecorador
- DecoradorConcreto ..... EmailDecorador, SMSDecorador

Nota: el envío es simulado (se registra en una bandeja), no se usan servicios reales.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from devtrack.dominio.modelos import Usuario


class Notificador(ABC):
    """Componente."""

    @abstractmethod
    def enviar(self, destinatario: Usuario, mensaje: str) -> list[str]:
        """Envía el mensaje y devuelve la lista de entregas realizadas."""


class NotificadorInApp(Notificador):
    """ComponenteConcreto: notificación dentro de la aplicación."""

    def __init__(self) -> None:
        self.bandeja: list[tuple[str, str]] = []

    def enviar(self, destinatario: Usuario, mensaje: str) -> list[str]:
        self.bandeja.append((destinatario.email, mensaje))
        return [f"[IN-APP] {destinatario.nombre}: {mensaje}"]


class NotificadorDecorador(Notificador):
    """Decorador: mantiene una referencia a un Componente y respeta su interfaz."""

    def __init__(self, envuelto: Notificador) -> None:
        self._envuelto = envuelto

    def enviar(self, destinatario: Usuario, mensaje: str) -> list[str]:
        return self._envuelto.enviar(destinatario, mensaje)


class EmailDecorador(NotificadorDecorador):
    def enviar(self, destinatario: Usuario, mensaje: str) -> list[str]:
        entregas = super().enviar(destinatario, mensaje)
        entregas.append(f"[EMAIL → {destinatario.email}] {mensaje}")
        return entregas


class SMSDecorador(NotificadorDecorador):
    def enviar(self, destinatario: Usuario, mensaje: str) -> list[str]:
        entregas = super().enviar(destinatario, mensaje)
        if destinatario.telefono:
            entregas.append(f"[SMS → {destinatario.telefono}] {mensaje[:160]}")
        else:
            entregas.append(f"[SMS omitido: {destinatario.nombre} no tiene teléfono]")
        return entregas


_DECORADORES: dict[str, type[NotificadorDecorador]] = {
    "email": EmailDecorador,
    "sms": SMSDecorador,
}


def registrar_canal(nombre: str, decorador: type[NotificadorDecorador]) -> None:
    """Punto de extensión: agrega un canal nuevo (ej. Slack) sin modificar este módulo."""
    _DECORADORES[nombre.lower()] = decorador


def canales_disponibles() -> list[str]:
    return ["in-app", *_DECORADORES.keys()]


def construir_notificador(canales: list[str], base: Notificador | None = None) -> Notificador:
    """Envuelve el notificador base con los decoradores de los canales pedidos."""
    notificador: Notificador = base or NotificadorInApp()
    for canal in canales:
        decorador = _DECORADORES.get(canal.lower())
        if decorador:
            notificador = decorador(notificador)
    return notificador
