from app.api import simulation


def test_set_simulation_engine_updates_global_module_state():
    engine = object()
    simulation.set_simulation_engine(engine)

    assert simulation.simulation_engine is engine
