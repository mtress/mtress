from mtress.physics import (
    Gas, 
    HYDROGEN, 
    NATURAL_GAS, 
    BIOGAS, 
    BIO_METHANE
    )
from mtress.physics import molar_mass
import pytest
import math

@pytest.mark.parametrize(
    "gas, true_molar_mass",
    [
        (HYDROGEN, 0.00201588),
        (NATURAL_GAS, 0.0175833),
        (BIOGAS, 0.023032499999999997),
        (BIO_METHANE,  0.01604),
    ],
)
def test_molar_mass(gas: Gas, true_molar_mass):
    
    assert math.isclose(
        gas.molar_mass,
        true_molar_mass,
        abs_tol=1e-3
        )
    
def test_triggering_errors():
    
    # gas components do not match
    with pytest.raises(ValueError):
        molar_mass(
            shares={
                'a': 0.1,
                'b': 0.9
                },
            molar_masses={
                'a': 3
                }
            )
    # shares do not add up to 1
    with pytest.raises(ValueError):
        molar_mass(
            shares={
                'a': 0.1,
                'b': 0.8
                },
            molar_masses={
                'a': 3,
                'b': 4
                }
            )
