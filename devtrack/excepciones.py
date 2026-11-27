"""Excepciones propias del sistema (manejo de errores explícito)."""


class DevTrackError(Exception):
    """Error base de DevTrack."""


class ValidacionError(DevTrackError):
    """Datos inválidos al crear o modificar una entidad."""


class TareaNoEncontradaError(DevTrackError):
    """Se intentó operar sobre una tarea que no existe."""


class SinAccionesError(DevTrackError):
    """No hay acciones para deshacer o rehacer."""


class AprobacionError(DevTrackError):
    """El hito no puede entrar al flujo de aprobación."""


class AccesoDenegadoError(DevTrackError):
    """El rol actual no tiene permiso para la operación."""
