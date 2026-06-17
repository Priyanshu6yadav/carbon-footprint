"""
CarbonTrack — Calculator Pydantic v2 schemas.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TransportationInput(BaseModel):
    car_km_per_month: float = Field(default=0.0, ge=0, le=100_000)
    car_fuel_type: str = Field(default="average")  # petrol, diesel, hybrid, electric, average
    motorcycle_km_per_month: float = Field(default=0.0, ge=0, le=50_000)
    bus_km_per_month: float = Field(default=0.0, ge=0, le=10_000)
    rail_km_per_month: float = Field(default=0.0, ge=0, le=20_000)
    rideshare_km_per_month: float = Field(default=0.0, ge=0, le=10_000)
    flights_short_haul_per_year: int = Field(default=0, ge=0, le=365)  # number of one-way trips
    flights_long_haul_per_year: int = Field(default=0, ge=0, le=100)
    flight_avg_short_distance_km: float = Field(default=800.0, ge=100, le=1500)
    flight_avg_long_distance_km: float = Field(default=8000.0, ge=1500, le=20_000)

    @field_validator("car_fuel_type")
    @classmethod
    def valid_fuel_type(cls, v: str) -> str:
        allowed = {"petrol", "diesel", "hybrid", "electric", "average"}
        if v not in allowed:
            raise ValueError(f"car_fuel_type must be one of {allowed}")
        return v


class HomeEnergyInput(BaseModel):
    electricity_kwh_per_month: float = Field(default=0.0, ge=0, le=50_000)
    natural_gas_m3_per_month: float = Field(default=0.0, ge=0, le=10_000)
    lpg_litres_per_month: float = Field(default=0.0, ge=0, le=5_000)
    region: str = Field(default="us")  # us, uk, eu, india

    @field_validator("region")
    @classmethod
    def valid_region(cls, v: str) -> str:
        allowed = {"us", "uk", "eu", "india"}
        if v not in allowed:
            raise ValueError(f"region must be one of {allowed}")
        return v


class FoodInput(BaseModel):
    diet_type: str = Field(default="average")

    @field_validator("diet_type")
    @classmethod
    def valid_diet(cls, v: str) -> str:
        allowed = {"vegan", "vegetarian", "pescatarian", "average", "meat_heavy"}
        if v not in allowed:
            raise ValueError(f"diet_type must be one of {allowed}")
        return v


class ShoppingInput(BaseModel):
    clothing_usd_per_month: float = Field(default=0.0, ge=0, le=100_000)
    electronics_usd_per_month: float = Field(default=0.0, ge=0, le=100_000)
    general_goods_usd_per_month: float = Field(default=0.0, ge=0, le=100_000)


class CalculatorInput(BaseModel):
    transportation: TransportationInput = Field(default_factory=TransportationInput)
    home_energy: HomeEnergyInput = Field(default_factory=HomeEnergyInput)
    food: FoodInput = Field(default_factory=FoodInput)
    shopping: ShoppingInput = Field(default_factory=ShoppingInput)


class CategoryBreakdown(BaseModel):
    transportation_kg: float
    home_energy_kg: float
    food_kg: float
    shopping_kg: float
    total_monthly_kg: float
    total_annual_kg: float
    transport_detail: dict
    energy_detail: dict


class CalculationResult(BaseModel):
    breakdown: CategoryBreakdown
    comparison: dict  # vs global/US/Paris averages
    emission_factors_version: str


class SavedLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    total_monthly_kg: float
    total_annual_kg: float
    transport_total: float
    energy_total: float
    food_total: float
    shopping_total: float
    created_at: datetime

    model_config = {"from_attributes": True}
