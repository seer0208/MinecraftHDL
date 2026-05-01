import pytest

from mhdlc.techlib import CellLibraryError, load_cell_library

from tests.conftest import FIXTURES, TECHLIB_PATH


def test_loads_default_redstone_library():
    library = load_cell_library(TECHLIB_PATH)

    assert library.name == "redstone_v1"
    assert set(library.kinds()) == {
        "AND",
        "OR",
        "XOR",
        "INV",
        "MUX",
        "INPUT",
        "OUTPUT",
        "CONST0",
        "CONST1",
    }


def test_library_rejects_missing_required_pin():
    with pytest.raises(CellLibraryError):
        load_cell_library(FIXTURES / "techlib" / "invalid_missing_pin.yaml")


def test_library_rejects_invalid_orientation():
    with pytest.raises(CellLibraryError):
        load_cell_library(FIXTURES / "techlib" / "invalid_orientation.yaml")


def test_library_rejects_missing_required_field():
    with pytest.raises(CellLibraryError):
        load_cell_library(FIXTURES / "techlib" / "invalid_missing_field.yaml")


def test_library_rejects_out_of_bounds_pin_anchor():
    with pytest.raises(CellLibraryError):
        load_cell_library(FIXTURES / "techlib" / "invalid_anchor.yaml")
