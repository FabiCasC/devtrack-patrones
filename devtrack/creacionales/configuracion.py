"""Patrón SINGLETON — Configuración global del sistema.

Problema que resuelve: toda la aplicación (servicios, notificaciones, vistas) debe
leer la MISMA configuración (nombre de la empresa, canales de notificación activos,
límite de horas por tarea, etc.). Si cada módulo creara su propia copia, un cambio
hecho en un lugar no se vería en los demás.

Implementación según el curso (Sesión 06): variable de clase ``_instance`` y
sobrescritura de ``__new__`` para crear la instancia solo la primera vez.
"""
from __future__ import annotations

from typing import Any


class ConfiguracionSistema:
    _instance: "ConfiguracionSistema | None" = None

    def __new__(cls) -> "ConfiguracionSistema":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._inicializar()
        return cls._instance

    def _inicializar(self) -> None:
        self._valores: dict[str, Any] = {
            "empresa": "DevTrack Solutions",
            "zona_horaria": "America/Lima",
            "max_horas_por_tarea": 40,
            "canales_notificacion": ["in-app"],
            "limite_presupuesto_lider": 50_000,
            "dias_tolerancia_retraso": 2,
        }

    def obtener(self, clave: str, por_defecto: Any = None) -> Any:
        return self._valores.get(clave, por_defecto)

    def establecer(self, clave: str, valor: Any) -> None:
        self._valores[clave] = valor

    def como_diccionario(self) -> dict[str, Any]:
        return dict(self._valores)

    @classmethod
    def _reiniciar(cls) -> None:
        """Solo para pruebas: el curso advierte que Singleton dificulta los tests."""
        cls._instance = None
