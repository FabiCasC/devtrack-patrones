from datetime import date, timedelta

import pytest

from devtrack.creacionales.builder import DirectorProyecto, ProyectoBuilder
from devtrack.creacionales.configuracion import ConfiguracionSistema
from devtrack.excepciones import ValidacionError


# ---------------- Singleton ----------------
def test_singleton_devuelve_siempre_la_misma_instancia():
    a = ConfiguracionSistema()
    b = ConfiguracionSistema()
    assert a is b


def test_singleton_comparte_cambios_en_todo_el_sistema():
    ConfiguracionSistema().establecer("max_horas_por_tarea", 16)
    assert ConfiguracionSistema().obtener("max_horas_por_tarea") == 16


# ---------------- Builder ----------------
def test_builder_construye_proyecto_paso_a_paso():
    hoy = date.today()
    proyecto = (ProyectoBuilder().con_nombre("CRM").para_cliente("ACME")
                .con_fechas(hoy, hoy + timedelta(weeks=4)).con_presupuesto(5000)
                .agregar_hito("Entrega", hoy + timedelta(weeks=4)).build())
    assert proyecto.nombre == "CRM"
    assert proyecto.hitos[0].nombre == "Entrega"
    assert proyecto.metodologia == "Scrum"  # valor por defecto


def test_builder_valida_datos_obligatorios_y_fechas():
    hoy = date.today()
    with pytest.raises(ValidacionError) as error:
        ProyectoBuilder().con_fechas(hoy, hoy - timedelta(days=1)).build()
    mensaje = str(error.value)
    assert "nombre" in mensaje and "cliente" in mensaje and "fecha de fin" in mensaje


def test_director_crea_proyecto_scrum_con_un_hito_por_sprint():
    proyecto = DirectorProyecto(ProyectoBuilder()).construir_proyecto_scrum(
        "App", "ACME", date(2026, 1, 5), sprints=3)
    assert [h.nombre for h in proyecto.hitos] == ["Sprint 1", "Sprint 2", "Sprint 3"]
    assert proyecto.fecha_fin == date(2026, 2, 16)
