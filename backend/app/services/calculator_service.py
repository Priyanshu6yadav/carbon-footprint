"""
CarbonTrack — Carbon Calculator Service.
Computes emissions using emission_factors.json (EPA/DEFRA sourced).
"""
import json
from functools import lru_cache
from pathlib import Path

from app.schemas.calculator import (
    CalculationResult,
    CalculatorInput,
    CategoryBreakdown,
)

FACTORS_PATH = Path(__file__).parent.parent.parent / "data" / "emission_factors.json"


@lru_cache
def load_emission_factors() -> dict:
    """Load and cache the emission factors JSON."""
    with open(FACTORS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_transportation(data, factors: dict) -> tuple[float, dict]:
    """
    Returns (total_kg_per_month, detail_dict).
    Flights converted from annual to monthly.
    """
    tf = factors["transportation"]
    detail = {}

    # Car
    fuel_key = f"{data.car_fuel_type}_per_km"
    if fuel_key not in tf["car"]:
        fuel_key = "average_per_km"
    car_kg = data.car_km_per_month * tf["car"][fuel_key]
    detail["car_kg"] = round(car_kg, 3)

    # Motorcycle
    moto_kg = data.motorcycle_km_per_month * tf["motorcycle"]["per_km"]
    detail["motorcycle_kg"] = round(moto_kg, 3)

    # Bus
    bus_kg = data.bus_km_per_month * tf["bus"]["per_km"]
    detail["bus_kg"] = round(bus_kg, 3)

    # Rail
    rail_kg = data.rail_km_per_month * tf["rail"]["per_km"]
    detail["rail_kg"] = round(rail_kg, 3)

    # Rideshare
    rideshare_kg = data.rideshare_km_per_month * tf["rideshare"]["per_km"]
    detail["rideshare_kg"] = round(rideshare_kg, 3)

    # Flights (annual → monthly, with radiative forcing multiplier)
    rf_mult = tf["flights"]["radiative_forcing_multiplier"]
    short_annual = (
        data.flights_short_haul_per_year
        * data.flight_avg_short_distance_km
        * tf["flights"]["short_haul_per_km"]
        * rf_mult
    )
    long_annual = (
        data.flights_long_haul_per_year
        * data.flight_avg_long_distance_km
        * tf["flights"]["long_haul_per_km"]
        * rf_mult
    )
    flights_monthly = (short_annual + long_annual) / 12
    detail["flights_kg"] = round(flights_monthly, 3)

    total = car_kg + moto_kg + bus_kg + rail_kg + rideshare_kg + flights_monthly
    return round(total, 3), detail


def calculate_home_energy(data, factors: dict) -> tuple[float, dict]:
    """Returns (total_kg_per_month, detail_dict)."""
    ef = factors["home_energy"]
    detail = {}

    # Electricity — region-specific factor
    region_key = f"{data.region}_average_per_kwh"
    elec_factor = ef["electricity"].get(region_key, ef["electricity"]["us_average_per_kwh"])
    elec_kg = data.electricity_kwh_per_month * elec_factor
    detail["electricity_kg"] = round(elec_kg, 3)

    # Natural gas
    gas_kg = data.natural_gas_m3_per_month * ef["natural_gas"]["per_m3"]
    detail["natural_gas_kg"] = round(gas_kg, 3)

    # LPG
    lpg_kg = data.lpg_litres_per_month * ef["lpg"]["per_litre"]
    detail["lpg_kg"] = round(lpg_kg, 3)

    total = elec_kg + gas_kg + lpg_kg
    return round(total, 3), detail


def calculate_food(data, factors: dict) -> float:
    """Returns total_kg_per_month."""
    diet_factors = factors["food"]["diet_types"]
    per_day = diet_factors[data.diet_type]["per_day_kg"]
    return round(per_day * 30.44, 3)  # average days per month


def calculate_shopping(data, factors: dict) -> float:
    """Returns total_kg_per_month."""
    sf = factors["shopping"]
    clothing = data.clothing_usd_per_month * sf["clothing"]["per_usd"]
    electronics = data.electronics_usd_per_month * sf["electronics"]["per_usd"]
    general = data.general_goods_usd_per_month * sf["general_goods"]["per_usd"]
    return round(clothing + electronics + general, 3)


def compute_carbon(input_data: CalculatorInput) -> CalculationResult:
    """
    Main calculation entry point.
    All logic delegated to category helpers using emission_factors.json.
    """
    factors = load_emission_factors()

    transport_kg, transport_detail = calculate_transportation(input_data.transportation, factors)
    energy_kg, energy_detail = calculate_home_energy(input_data.home_energy, factors)
    food_kg = calculate_food(input_data.food, factors)
    shopping_kg = calculate_shopping(input_data.shopping, factors)

    total_monthly = round(transport_kg + energy_kg + food_kg + shopping_kg, 2)
    total_annual = round(total_monthly * 12, 2)

    avgs = factors["averages_for_comparison"]

    return CalculationResult(
        breakdown=CategoryBreakdown(
            transportation_kg=transport_kg,
            home_energy_kg=energy_kg,
            food_kg=food_kg,
            shopping_kg=shopping_kg,
            total_monthly_kg=total_monthly,
            total_annual_kg=total_annual,
            transport_detail=transport_detail,
            energy_detail=energy_detail,
        ),
        comparison={
            "global_average_annual_kg": avgs["global_average_annual_kg"],
            "us_average_annual_kg": avgs["us_average_annual_kg"],
            "paris_target_annual_kg": avgs["paris_target_annual_kg"],
            "your_vs_global_pct": round((total_annual / avgs["global_average_annual_kg"]) * 100, 1),
            "your_vs_us_pct": round((total_annual / avgs["us_average_annual_kg"]) * 100, 1),
        },
        emission_factors_version=factors["version"],
    )
