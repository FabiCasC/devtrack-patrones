from datetime import date, timedelta

import pytest

from devtrack.creacionales.builder import ProyectoBuilder
from devtrack.creacionales.configuracion import ConfiguracionSistema
from devtrack.dominio.modelos import Rol, Usuario


@pytest.fixture(autouse=True)
def configuracion_limpia():
    """Cada prueba arranca con la configuración por defecto."""
    ConfiguracionSistema._reiniciar()
    yield
    ConfiguracionSistema._reiniciar()


@pytest.fixture
def usuarios():
    return {
        "lider": Usuario("Ana", "ana@x.pe", Rol.LIDER),
        "dev": Usuario("Bruno", "bruno@x.pe", Rol.DESARROLLADOR, "999111222", ["email", "sms"]),
        "qa": Usuario("Diego", "diego@x.pe", Rol.QA),
        "cliente": Usuario("Felipe", "felipe@x.pe", Rol.CLIENTE),
    }


@pytest.fixture
def proyecto(usuarios):
    hoy = date.today()
    builder = ProyectoBuilder().con_nombre("Demo").para_cliente("ACME")
    builder.con_fechas(hoy, hoy + timedelta(weeks=8)).con_presupuesto(10_000)
    builder.agregar_hito("Sprint 1", hoy + timedelta(weeks=2))
    for u in usuarios.values():
        builder.agregar_miembro(u)
    return builder.build()
