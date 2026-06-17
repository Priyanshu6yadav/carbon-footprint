// Base API types shared across the app

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  xp_total: number;
  level: number;
  created_at: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// ─── Calculator Types ──────────────────────────────────────────────

export interface TransportationInput {
  car_km_per_month: number | string;
  car_fuel_type: 'petrol' | 'diesel' | 'hybrid' | 'electric' | 'average';
  motorcycle_km_per_month: number | string;
  bus_km_per_month: number | string;
  rail_km_per_month: number | string;
  rideshare_km_per_month: number | string;
  flights_short_haul_per_year: number | string;
  flights_long_haul_per_year: number | string;
  flight_avg_short_distance_km: number | string;
  flight_avg_long_distance_km: number | string;
}

export interface HomeEnergyInput {
  electricity_kwh_per_month: number | string;
  natural_gas_m3_per_month: number | string;
  lpg_litres_per_month: number | string;
  region: 'us' | 'uk' | 'eu' | 'india';
}

export interface FoodInput {
  diet_type: 'vegan' | 'vegetarian' | 'pescatarian' | 'average' | 'meat_heavy';
}

export interface ShoppingInput {
  clothing_usd_per_month: number | string;
  electronics_usd_per_month: number | string;
  general_goods_usd_per_month: number | string;
}

export interface CalculatorInput {
  transportation: TransportationInput;
  home_energy: HomeEnergyInput;
  food: FoodInput;
  shopping: ShoppingInput;
}

export interface CategoryBreakdown {
  transportation_kg: number;
  home_energy_kg: number;
  food_kg: number;
  shopping_kg: number;
  total_monthly_kg: number;
  total_annual_kg: number;
  transport_detail: Record<string, number>;
  energy_detail: Record<string, number>;
}

export interface CalculationResult {
  breakdown: CategoryBreakdown;
  comparison: {
    global_average_annual_kg: number;
    us_average_annual_kg: number;
    paris_target_annual_kg: number;
    your_vs_global_pct: number;
    your_vs_us_pct: number;
  };
  emission_factors_version: string;
}

export interface SavedLog {
  id: string;
  user_id: string;
  total_monthly_kg: number;
  total_annual_kg: number;
  transport_total: number;
  energy_total: number;
  food_total: number;
  shopping_total: number;
  created_at: string;
}

// ─── API Error ─────────────────────────────────────────────────────

export interface ApiError {
  detail: string | { msg: string; type: string }[];
}
