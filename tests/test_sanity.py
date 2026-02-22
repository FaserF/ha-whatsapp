from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

def test_import() -> None:
    import homeassistant

    assert homeassistant
