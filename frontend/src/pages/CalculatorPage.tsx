import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Car, Zap, Salad, ShoppingBag, ChevronRight, ChevronLeft, Leaf } from 'lucide-react';
import type { CalculatorInput } from '@/types';

// ─── Default values ────────────────────────────────────────────────
const defaultValues: CalculatorInput = {
  transportation: {
    car_km_per_month: '',
    car_fuel_type: 'average',
    motorcycle_km_per_month: '',
    bus_km_per_month: '',
    rail_km_per_month: '',
    rideshare_km_per_month: '',
    flights_short_haul_per_year: '',
    flights_long_haul_per_year: '',
    flight_avg_short_distance_km: 800,
    flight_avg_long_distance_km: 8000,
  },
  home_energy: {
    electricity_kwh_per_month: '',
    natural_gas_m3_per_month: '',
    lpg_litres_per_month: '',
    region: 'us',
  },
  food: { diet_type: 'average' },
  shopping: {
    clothing_usd_per_month: '',
    electronics_usd_per_month: '',
    general_goods_usd_per_month: '',
  },
};


// ─── Steps config ──────────────────────────────────────────────────
const steps = [
  { id: 'transport', label: 'Transportation', icon: Car, color: 'text-blue-400' },
  { id: 'energy', label: 'Home Energy', icon: Zap, color: 'text-yellow-400' },
  { id: 'food', label: 'Food', icon: Salad, color: 'text-green-400' },
  { id: 'shopping', label: 'Shopping', icon: ShoppingBag, color: 'text-purple-400' },
];

// ─── Shared input field ────────────────────────────────────────────
function Field({
  label,
  id,
  unit,
  hint,
  children,
}: {
  label: string;
  id: string;
  unit?: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="flex items-center justify-between text-sm font-medium text-white/70">
        <span>{label}</span>
        {unit && <span className="text-xs text-white/30">{unit}</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-white/30 italic">{hint}</p>}
    </div>
  );
}

function NumberInput({ id, onChange, onBlur, ...props }: { id: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.replace(/[^0-9.]/g, '');
    const parts = val.split('.');
    if (parts.length > 2) {
      val = parts[0] + '.' + parts.slice(1).join('');
    }
    e.target.value = val;
    if (onChange) onChange(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    if (e.target.value !== '') {
      let val = e.target.value;
      if (val.length > 1 && val.startsWith('0') && !val.startsWith('0.')) {
        val = val.replace(/^0+/, '');
        if (val === '') val = '0';
      }
      e.target.value = val;
      if (onChange) {
        onChange(e as unknown as React.ChangeEvent<HTMLInputElement>);
      }
    }
    if (onBlur) onBlur(e);
  };

  return (
    <input
      id={id}
      type="text"
      inputMode="decimal"
      onChange={handleChange}
      onBlur={handleBlur}
      className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/20 text-sm outline-none transition-all duration-200 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20"
      {...props}
    />
  );
}

function SelectInput({
  id,
  options,
  ...props
}: {
  id: string;
  options: { value: string; label: string }[];
} & React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      id={id}
      className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white text-sm outline-none transition-all duration-200 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 cursor-pointer"
      {...props}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value} className="bg-[#0a1a0a]">
          {o.label}
        </option>
      ))}
    </select>
  );
}

export default function CalculatorPage() {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState<CalculatorInput>(defaultValues);
  const [direction, setDirection] = useState<1 | -1>(1);
  const navigate = useNavigate();

  function updateTransport(field: string, value: string | number) {
    setFormData((prev) => ({
      ...prev,
      transportation: { ...prev.transportation, [field]: value },
    }));
  }

  function updateEnergy(field: string, value: string | number) {
    setFormData((prev) => ({
      ...prev,
      home_energy: { ...prev.home_energy, [field]: value },
    }));
  }

  function updateFood(field: string, value: string) {
    setFormData((prev) => ({ ...prev, food: { ...prev.food, [field]: value } }));
  }

  function updateShopping(field: string, value: string | number) {
    setFormData((prev) => ({ ...prev, shopping: { ...prev.shopping, [field]: value } }));
  }

  function next() {
    setDirection(1);
    if (step < steps.length - 1) {
      setStep((s) => s + 1);
    } else {
      const sanitized = {
        transportation: {
          ...formData.transportation,
          car_km_per_month: Number(formData.transportation.car_km_per_month) || 0,
          motorcycle_km_per_month: Number(formData.transportation.motorcycle_km_per_month) || 0,
          bus_km_per_month: Number(formData.transportation.bus_km_per_month) || 0,
          rail_km_per_month: Number(formData.transportation.rail_km_per_month) || 0,
          rideshare_km_per_month: Number(formData.transportation.rideshare_km_per_month) || 0,
          flights_short_haul_per_year: Number(formData.transportation.flights_short_haul_per_year) || 0,
          flights_long_haul_per_year: Number(formData.transportation.flights_long_haul_per_year) || 0,
        },
        home_energy: {
          ...formData.home_energy,
          electricity_kwh_per_month: Number(formData.home_energy.electricity_kwh_per_month) || 0,
          natural_gas_m3_per_month: Number(formData.home_energy.natural_gas_m3_per_month) || 0,
          lpg_litres_per_month: Number(formData.home_energy.lpg_litres_per_month) || 0,
        },
        food: formData.food,
        shopping: {
          clothing_usd_per_month: Number(formData.shopping.clothing_usd_per_month) || 0,
          electronics_usd_per_month: Number(formData.shopping.electronics_usd_per_month) || 0,
          general_goods_usd_per_month: Number(formData.shopping.general_goods_usd_per_month) || 0,
        }
      };
      navigate('/results', { state: { input: sanitized } });
    }
  }

  function prev() {
    setDirection(-1);
    setStep((s) => Math.max(0, s - 1));
  }

  const variants = {
    enter: (dir: number) => ({ x: dir > 0 ? 60 : -60, opacity: 0 }),
    center: { x: 0, opacity: 1 },
    exit: (dir: number) => ({ x: dir > 0 ? -60 : 60, opacity: 0 }),
  };

  return (
    <div className="min-h-screen bg-[#030a05] text-white py-12 px-4">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[400px] h-[400px] rounded-full bg-emerald-500/4 blur-3xl" />
      </div>

      <div className="relative max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-2 font-bold text-lg mb-2">
            <Leaf className="w-5 h-5 text-emerald-400" />
            <span className="gradient-text">CarbonTrack</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Calculate your footprint</h1>
          <p className="text-white/40 text-sm">Using EPA & DEFRA verified emission factors</p>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-3">
            {steps.map((s, i) => {
              const Icon = s.icon;
              return (
                <div key={s.id} className="flex flex-col items-center gap-1.5">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 ${
                      i === step
                        ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/30'
                        : i < step
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-white/5 text-white/20'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className={`text-xs ${i === step ? 'text-white' : 'text-white/30'}`}>
                    {s.label}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="h-1 bg-white/5 rounded-full">
            <motion.div
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full"
              animate={{ width: `${((step + 1) / steps.length) * 100}%` }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            />
          </div>
        </div>

        {/* Step content */}
        <div className="overflow-hidden">
          <AnimatePresence mode="wait" custom={direction}>
            {step === 0 && (
              <motion.div
                key="transport"
                custom={direction}
                variants={variants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="glass rounded-2xl p-8 space-y-6"
              >
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Car className="w-5 h-5 text-blue-400" /> Transportation
                </h2>

                <div className="grid grid-cols-2 gap-4">
                  <Field label="Car driving" id="car-km" unit="km/month">
                    <NumberInput
                      id="car-km"
                      value={formData.transportation.car_km_per_month}
                      onChange={(e) => updateTransport('car_km_per_month', e.target.value)}
                      placeholder="e.g. 1200"
                    />
                  </Field>
                  <Field label="Fuel type" id="car-fuel">
                    <SelectInput
                      id="car-fuel"
                      value={formData.transportation.car_fuel_type}
                      onChange={(e) => updateTransport('car_fuel_type', e.target.value)}
                      options={[
                        { value: 'average', label: 'Average fleet' },
                        { value: 'petrol', label: 'Petrol / Gasoline' },
                        { value: 'diesel', label: 'Diesel' },
                        { value: 'hybrid', label: 'Hybrid' },
                        { value: 'electric', label: 'Electric' },
                      ]}
                    />
                  </Field>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Field label="Bus / Metro" id="bus-km" unit="km/month">
                    <NumberInput
                      id="bus-km"
                      value={formData.transportation.bus_km_per_month}
                      onChange={(e) => updateTransport('bus_km_per_month', e.target.value)}
                      placeholder="e.g. 200"
                    />
                  </Field>
                  <Field label="Train / Rail" id="rail-km" unit="km/month">
                    <NumberInput
                      id="rail-km"
                      value={formData.transportation.rail_km_per_month}
                      onChange={(e) => updateTransport('rail_km_per_month', e.target.value)}
                      placeholder="e.g. 100"
                    />
                  </Field>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Field label="Short-haul flights" id="short-flights" unit="trips/year" hint="Under 1,500 km">
                    <NumberInput
                      id="short-flights"
                      value={formData.transportation.flights_short_haul_per_year}
                      onChange={(e) => updateTransport('flights_short_haul_per_year', e.target.value)}
                      placeholder="e.g. 4"
                    />
                  </Field>
                  <Field label="Long-haul flights" id="long-flights" unit="trips/year" hint="Over 1,500 km">
                    <NumberInput
                      id="long-flights"
                      value={formData.transportation.flights_long_haul_per_year}
                      onChange={(e) => updateTransport('flights_long_haul_per_year', e.target.value)}
                      placeholder="e.g. 2"
                    />
                  </Field>
                </div>

                <p className="text-xs text-white/20">
                  * Flights include radiative forcing multiplier (IPCC AR6)
                </p>
              </motion.div>
            )}

            {step === 1 && (
              <motion.div
                key="energy"
                custom={direction}
                variants={variants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="glass rounded-2xl p-8 space-y-6"
              >
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-400" /> Home Energy
                </h2>

                <Field label="Electricity grid region" id="energy-region">
                  <SelectInput
                    id="energy-region"
                    value={formData.home_energy.region}
                    onChange={(e) => updateEnergy('region', e.target.value)}
                    options={[
                      { value: 'us', label: '🇺🇸 United States' },
                      { value: 'uk', label: '🇬🇧 United Kingdom' },
                      { value: 'eu', label: '🇪🇺 European Union' },
                      { value: 'india', label: '🇮🇳 India' },
                    ]}
                  />
                </Field>

                <Field label="Electricity usage" id="electricity" unit="kWh/month">
                  <NumberInput
                    id="electricity"
                    value={formData.home_energy.electricity_kwh_per_month}
                    onChange={(e) => updateEnergy('electricity_kwh_per_month', e.target.value)}
                    placeholder="e.g. 300 (US avg)"
                  />
                </Field>

                <Field label="Natural gas" id="natural-gas" unit="m³/month">
                  <NumberInput
                    id="natural-gas"
                    value={formData.home_energy.natural_gas_m3_per_month}
                    onChange={(e) => updateEnergy('natural_gas_m3_per_month', e.target.value)}
                    placeholder="e.g. 50"
                  />
                </Field>

                <Field label="LPG / Cooking gas" id="lpg" unit="litres/month">
                  <NumberInput
                    id="lpg"
                    value={formData.home_energy.lpg_litres_per_month}
                    onChange={(e) => updateEnergy('lpg_litres_per_month', e.target.value)}
                    placeholder="e.g. 15"
                  />
                </Field>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="food"
                custom={direction}
                variants={variants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="glass rounded-2xl p-8 space-y-6"
              >
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Salad className="w-5 h-5 text-green-400" /> Food Habits
                </h2>

                <p className="text-sm text-white/40">
                  Based on Poore & Nemecek (2018), Science — food system lifecycle emissions.
                </p>

                <div className="space-y-3">
                  {[
                    { value: 'vegan', label: '🌱 Vegan', desc: '~2.9 kg CO₂e/day', color: 'border-emerald-500' },
                    { value: 'vegetarian', label: '🥗 Vegetarian', desc: '~3.8 kg CO₂e/day', color: 'border-green-500' },
                    { value: 'pescatarian', label: '🐟 Pescatarian', desc: '~3.9 kg CO₂e/day', color: 'border-teal-500' },
                    { value: 'average', label: '🍽️ Average diet', desc: '~5.6 kg CO₂e/day', color: 'border-orange-500' },
                    { value: 'meat_heavy', label: '🥩 Meat-heavy', desc: '~7.2 kg CO₂e/day', color: 'border-red-500' },
                  ].map((diet) => (
                    <label
                      key={diet.value}
                      className={`flex items-center justify-between p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
                        formData.food.diet_type === diet.value
                          ? `${diet.color} bg-white/5`
                          : 'border-white/10 hover:border-white/20'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="radio"
                          name="diet"
                          value={diet.value}
                          checked={formData.food.diet_type === diet.value}
                          onChange={() => updateFood('diet_type', diet.value)}
                          className="accent-emerald-500"
                          id={`diet-${diet.value}`}
                        />
                        <span className="font-medium">{diet.label}</span>
                      </div>
                      <span className="text-sm text-white/40">{diet.desc}</span>
                    </label>
                  ))}
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="shopping"
                custom={direction}
                variants={variants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="glass rounded-2xl p-8 space-y-6"
              >
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <ShoppingBag className="w-5 h-5 text-purple-400" /> Shopping & Lifestyle
                </h2>

                <p className="text-sm text-white/40">
                  Monthly spend helps estimate lifecycle emissions from manufacturing and transport.
                </p>

                <Field label="Clothing & Apparel" id="clothing" unit="USD/month">
                  <NumberInput
                    id="clothing"
                    value={formData.shopping.clothing_usd_per_month}
                    onChange={(e) => updateShopping('clothing_usd_per_month', e.target.value)}
                    placeholder="e.g. 80"
                  />
                </Field>

                <Field label="Electronics & Tech" id="electronics" unit="USD/month">
                  <NumberInput
                    id="electronics"
                    value={formData.shopping.electronics_usd_per_month}
                    onChange={(e) => updateShopping('electronics_usd_per_month', e.target.value)}
                    placeholder="e.g. 50"
                  />
                </Field>

                <Field label="General goods" id="general" unit="USD/month">
                  <NumberInput
                    id="general"
                    value={formData.shopping.general_goods_usd_per_month}
                    onChange={(e) => updateShopping('general_goods_usd_per_month', e.target.value)}
                    placeholder="e.g. 150"
                  />
                </Field>

                <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/15 text-xs text-emerald-400/70">
                  Emission factors: EPA & DEFRA lifecycle analysis per dollar spent.
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <div className="flex gap-4 mt-6">
          {step > 0 && (
            <button
              onClick={prev}
              id="calc-prev"
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-white/10 hover:border-white/20 text-white/60 hover:text-white font-medium text-sm transition-all duration-200"
            >
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
          )}
          <button
            onClick={next}
            id="calc-next"
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-sm transition-all duration-200 hover:shadow-lg hover:shadow-emerald-500/25"
          >
            {step < steps.length - 1 ? (
              <>Next step <ChevronRight className="w-4 h-4" /></>
            ) : (
              <>Calculate my footprint 🌱</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
