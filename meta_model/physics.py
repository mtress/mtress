import numpy as np

# Absolute zero
ZERO_CELSIUS = 273.15  # K

# Natural gas
HS_PER_HI_GAS = 1.11  # according to DIN V 18599

# Wood pellets
HS_PER_HI_WP = 1.08  # according to DIN V 18599
HHV_WP = 4.8  # kWh/kg  /  MWh/t

# Water in heat storage
H2O_HEAT_CAPACITY = 4.182  # kJ/(kg*K)
H2O_HEAT_FUSION = 0.09265  # MWh/t, = 333.55 J/g
H2O_DENSITY = 1000  # Kg/m^3
H2O_HEAT_CAPACITY = 4.182  # kJ/(kg*K)

# Thermal conductivity
TC_CONCRETE = 0.8  # W / (m * K)
TC_INSULATION = 0.04  # W / (m * K)

# improve readability, used e.g. for J -> Wh
SECONDS_PER_HOUR = 3600


def kilo_to_mega(arg):
    """
    use to make explicit unit conversions instead of just dividing by 1000
    """
    return arg/1000


def celsius_to_kelvin(arg):
    """
    converts °C to K
    """
    return ZERO_CELSIUS + arg


def kelvin_to_celsius(arg):
    """
    converts K to °C
    """
    return arg - ZERO_CELSIUS


def kJ_to_MWh(arg):  # pylint: disable=C0103
    """
    converts kJ to MWh
    """
    return kilo_to_mega(arg / SECONDS_PER_HOUR)


def mean_logarithmic_temperature(t_high, t_low):
    """
    Logarithmic mean temperature as used by the
    Lorenz CIO Model

    :param t_high: High Temperature [K]
    :param t_low: Low Temperature [K]
    :return: Mean Logarithmic Temperature [K]
    """
    return (t_low - t_high) / np.log(t_low / t_high)


def lorenz_cop(temp_in, temp_out):
    """
    Calculate the theoretical COP of a infinite number
    of heat pump processes acc. to Lorenz 1895

    (Lorenz, H, 1895. Die Ermittlung der Grenzwerte der
    thermodynamischen Energieumwandlung. Zeitschrift für
    die gesammte Kälte-Industrie, 2(1-3, 6-12).)
    :param temp_in: Inlet Temperature
    :param temp_out: Outlet Temperature
    :return: Ideal COP
    """
    return temp_out / np.maximum(temp_out - temp_in, 1e-3)


def calc_cop(temp_input_high, temp_input_low,
             temp_output_high, temp_output_low):
    """
    Calculating COP of heat pump acc. to Reinholdt et.al. 2016
    https://backend.orbit.dtu.dk/ws/files/149827036/Contribution_1380_final.pdf

    :param temp_input_high: Higher Temperature of the source
    :param temp_input_low: Lower Temperature of the source
    :param temp_output_high: Flow Temperature of the heating system
    :param temp_output_low: Return Temperature of the heating system
    :return: Realistic COP for the given temperatures
    """
    cop_norm = 4.6

    # Acc. to EN14511 (B0/W35)
    temp_input_high_norm = celsius_to_kelvin(0)
    temp_input_low_norm = celsius_to_kelvin(-3)
    temp_output_high_norm = celsius_to_kelvin(35)
    temp_output_low_norm = celsius_to_kelvin(30)

    lorentz_efficiency = 0.6

    temp_input_logarithmic_norm = \
        mean_logarithmic_temperature(temp_input_high_norm,
                                     temp_input_low_norm)
    temp_output_logarithmic_norm = \
        mean_logarithmic_temperature(temp_output_high_norm,
                                     temp_output_low_norm)

    cpf_norm = cop_norm \
               / lorenz_cop(temp_input_logarithmic_norm,
                            temp_output_logarithmic_norm)

    temp_input_logarithmic = \
        mean_logarithmic_temperature(temp_input_high,
                                     temp_input_low)
    temp_output_logarithmic = \
        mean_logarithmic_temperature(temp_output_high,
                                     temp_output_low)

    theoretical_cop = cpf_norm * lorenz_cop(temp_input_logarithmic,
                                            temp_output_logarithmic)

    cop = theoretical_cop * lorentz_efficiency

    return cop


if __name__ =='__main__':
    print(calc_cop(celsius_to_kelvin(10),
                   celsius_to_kelvin(7),
                   celsius_to_kelvin(20),
                   celsius_to_kelvin(15)
                   ))
