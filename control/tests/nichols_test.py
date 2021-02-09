"""nichols_test.py - test Nichols plot

RMM, 31 Mar 2011
"""
import pytest

from control import nichols
from control import nichols_plot
from control import StateSpace


@pytest.fixture()
def tsys():
    """Set up a system to test operations on."""
    A = [[-3.0, 4.0, 2.0], [-1.0, -3.0, 0.0], [2.0, 5.0, 3.0]]
    B = [[1.0], [-3.0], [-2.0]]
    C = [[4.0, 2.0, -3.0]]
    D = [[0.0]]
    return StateSpace(A, B, C, D)


def test_nichols(tsys, mplcleanup):
    """Generate a Nichols plot."""
    nichols_plot(tsys)


def test_nichols_alias(tsys, mplcleanup):
    """Test the control.nichols alias and the grid=False parameter"""
    nichols(tsys, grid=False)
