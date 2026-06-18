"""
CarbonTrack — Calculator service unit tests.
These test the computation logic directly (no DB needed).
"""
import pytest

from app.schemas.calculator import (
    CalculatorInput,
    FoodInput,
    HomeEnergyInput,
    TransportationInput,
)
from app.services.calculator_service import compute_carbon


def test_zero_input_still_counts_food():
    """A user with zero transport/energy/shopping still has a food footprint."""
    result = compute_carbon(CalculatorInput())
    assert result.breakdown.food_kg > 0
    assert result.breakdown.transportation_kg == 0
    assert result.breakdown.home_energy_kg == 0
    assert result.breakdown.total_monthly_kg > 0


def test_vegan_diet_lower_than_meat_heavy():
    vegan = compute_carbon(CalculatorInput(food=FoodInput(diet_type="vegan")))
    meat = compute_carbon(CalculatorInput(food=FoodInput(diet_type="meat_heavy")))
    assert vegan.breakdown.food_kg < meat.breakdown.food_kg


def test_electric_car_lower_than_petrol():
    electric = compute_carbon(CalculatorInput(
        transportation=TransportationInput(car_km_per_month=1000, car_fuel_type="electric")
    ))
    petrol = compute_carbon(CalculatorInput(
        transportation=TransportationInput(car_km_per_month=1000, car_fuel_type="petrol")
    ))
    assert electric.breakdown.transportation_kg < petrol.breakdown.transportation_kg


def test_monthly_annual_relationship():
    result = compute_carbon(CalculatorInput(
        transportation=TransportationInput(car_km_per_month=500)
    ))
    assert abs(result.breakdown.total_annual_kg - result.breakdown.total_monthly_kg * 12) < 0.1


def test_high_electricity_adds_emissions():
    result = compute_carbon(CalculatorInput(
        home_energy=HomeEnergyInput(electricity_kwh_per_month=1000, region="us")
    ))
    assert result.breakdown.home_energy_kg > 300  # 1000 * 0.386 = 386 kg


def test_flights_add_radiative_forcing():
    """Long haul flights should be meaningfully high due to RF multiplier."""
    result = compute_carbon(CalculatorInput(
        transportation=TransportationInput(
            flights_long_haul_per_year=2,
            flight_avg_long_distance_km=10000,
        )
    ))
    # 2 * 10000 * 0.195 * 1.9 / 12 ≈ 617.5 kg/month
    assert result.breakdown.transportation_kg > 500


def test_comparison_data_present():
    result = compute_carbon(CalculatorInput())
    assert "global_average_annual_kg" in result.comparison
    assert "paris_target_annual_kg" in result.comparison
    assert "your_vs_global_pct" in result.comparison


def test_invalid_diet_type():
    with pytest.raises(Exception):
        CalculatorInput(food=FoodInput(diet_type="fruitarian"))


def test_negative_km_rejected():
    with pytest.raises(Exception):
        TransportationInput(car_km_per_month=-100)


def test_emission_factors_version_present():
    result = compute_carbon(CalculatorInput())
    assert result.emission_factors_version == "1.0"
