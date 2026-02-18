"""
PalmOpsSim - Model Layer
Refactored from Phase 3 Prototype
Contains simulation logic only (no printing, no plotting, no exports)
"""

import numpy as np
import pandas as pd

# ------------------------
# Yield Behaviour Function (15/2/2026)
# Phase 5 Implementation (16/2/2026): Change to a smoother piecewise curve
# Phase 5 Improvement (18/2//2026): Improving Age-Yield Curve 
# ------------------------

def base_yield_by_age(age):
    if age < 3:
        return 0
    elif 3 <= age < 6:
        return 8 + (age - 3) * 4 # Stronger ramp-up
    elif 6 <= age <= 9:
        return 20 + (age - 6) * 2  # Approaching peak
    elif 9 <= age <= 18: 
        return 26 # Peak plateau (~26t/ha realistic)
    elif 19 <= age <= 28:
        return 26 - (age - 18) * 1.0 # Gradual decline
    else:
        return 0 # After 25, no yield (replant triggers)
    
# ------------------------
# Main Simulation Function (15/2/2026)
# Phase 5 Implementation (16/2/2026): Added Staggered planting for plantation blocks
# Phase 5 Implementation (16/2/2026): Added replanting logic in simulation loop
# Phase 5 Implementation (16/2/2026): Added fertilizer in yield calculation
# Phase 5 Implementation (16/2/2026): Added climate slider and pest slider
# ------------------------

def run_simulation(
        scenario_name = "Conservative",
        yield_adjustment = 0.10,
        num_blocks = 10,
        simulation_years = 10,
        fertilizer = 0,
        harvest_interval = 12,
        block_area_ha = 25,
        initial_age_range = (3, 25),
        random_seed = 42,
        climate_slider = 0, # new parameter (% adjustment to climate)
        pest_slider = 5 # new parameter (% yield loss from pests)
):
    
    # Scenario configuration
    if scenario_name == "Conservative":
        yield_adjustment = -0.10
    elif scenario_name == "Moderate":
        yield_adjustment = 0.00
    elif scenario_name == "Aggressive":
        yield_adjustment = 0.10
    else:
        yield_adjustment = 0.00

    np.random.seed(random_seed)

    # Initialize plantation blocks
    blocks = []
    for block_id in range(1, num_blocks + 1):
        block_age = np.random.randint(initial_age_range[0], initial_age_range[1] + 1)
        block = {
            "Block": f"B{block_id}",
            "Area_ha": block_area_ha,
            "Age": block_age,
            "Planted_Year": 0 # Track year of planting for replanting logic
        }
        blocks.append(block)
    
    # Simulation loop
    results = []

    for year in range(1, simulation_years + 1):

        # Phase 5 Implementation (18/2/2026): Separate Climate from random noise
        # Phase 5 Addition (18/2/2026): Modified climate factor to include climate slider
        for block in blocks:
            climate_factor = np.random.normal(1 + climate_slider/100, 0.05) # Yearly rainfall effect

            age = block["Age"]
            base_yield = base_yield_by_age(age)

            # Apply scenario adjustment + fertilizer effect
            # (18/2/2026): Make fertilizer response non-linear
            fertilizer_response = 1 + (0.4 * (fertilizer / 100))
            adjusted_yield = base_yield * (1 + yield_adjustment) * fertilizer_response

            # Apply variability as before
            # (18/2/2026): Added harvest efficiency
            # (18/2/2026): Added pest pressure
            block_variation = np.random.normal(1.0, 0.03)
            harvest_efficiency = 0.95 if harvest_interval <= 12 else 0.88
            pest_pressure = 0.05 # 5% loss
            yield_t_ha = max(adjusted_yield * climate_factor * block_variation, 0)
            yield_t_ha *= harvest_efficiency
            yield_t_ha *= (1 - pest_pressure)
            yield_t_ha *= (1 - pest_slider/100)
            total_ffb = yield_t_ha * block["Area_ha"]

            results.append({
                "Year": year,
                "Block": block["Block"],
                "Age": age,
                "Planted_Year": block["Planted_Year"],
                "FFB_t_ha": round(yield_t_ha, 2),
                "Total_FFB_t": round(total_ffb, 2)
            })

            # Phase 5: Check for replanting at economic age (25 years)
            block["Age"] += 1

            # (18/2/2026): Improve replanting logic
            # Phase 5 Improvement (18/12/2026): Removed automatic replanting
            # if block["Age"] > 28:
            #     # Replant block
            #     block["Age"] = 0
            #     block["Planted_Year"] = year

            # base_yield = base_yield_by_age(block["Age"])

        # Phase 5 Improvement (18/12/2026): New Replanting logic
        # Identify overaged blocks
        overaged_blocks = [b for b in blocks if b["Age"] > 28]

        # Replant only limited number (e.g. 5% of total blocks)
        max_replant = max(1, int(0.05 * num_blocks))

        if len(overaged_blocks) > 0:
            np.random.shuffle(overaged_blocks)
            blocks_to_replant = overaged_blocks[:max_replant]

            for b in blocks_to_replant:
                b["Age"] = 0

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Management metrics
    total_ffb = df["Total_FFB_t"].sum()
    total_area = num_blocks * block_area_ha * simulation_years
    avg_yield = total_ffb / total_area
    final_year = df["Year"].max()
    old_blocks = df[(df["Year"] == final_year) & (df["Age"] > 25)]["Block"].nunique()

    # Annual summary for charts
    annual_summary = df.groupby("Year")["Total_FFB_t"].sum()

    # Return structured results
    return {
        "dataframe": df,
        "total_ffb": round(total_ffb, 1),
        "average_yield": round(avg_yield, 2),
        "old_blocks": old_blocks,
        "annual_summary": annual_summary
    }