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
# ------------------------

def base_yield_by_age(age):
    if age < 3:
        return 0
    elif 3 <= age < 8:
        return 18 + (age - 3) * 1.4 # Ramp up to peak (~25 t/ha)
    elif 8 <= age <= 18:
        return 25 # Peak yield
    elif 19 <= age <= 25: 
        return 25 - (age - 18) * 0.7 # Gradual decline
    else:
        return 0 # After 25, no yield (replant triggers)
    
# ------------------------
# Main Simulation Function (15/2/2026)
# Phase 5 Implementation (16/2/2026): Added Staggered planting for plantation blocks
# Phase 5 Implementation (16/2/2026): Added replanting logic in simulation loop
# Phase 5 Implementaion (16/2/2026): Added fertilizer in yield calculation
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
        random_seed = 42
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
        for block in blocks:

            age = block["Age"]
            base_yield = base_yield_by_age(age)

            # Apply scenario adjustment + fertilizer effect
            adjusted_yield = base_yield * (1 + yield_adjustment + fertilizer / 100)

            # Apply variability as before
            variability = np.random.normal(1.0, 0.1)
            yield_t_ha = max(adjusted_yield * variability, 0)
            total_ffb = yield_t_ha * block["Area_ha"]

            results.append({
                "Year": year,
                "Block": block["Block"],
                "Age": age,
                "FFB_t_ha": round(yield_t_ha, 2),
                "Total_FFB_t": round(total_ffb, 2)
            })

            # Phase 5: Check for replanting at economic age (25 years)
            block["Age"] += 1

            if block["Age"] > 25:
                # Replant block
                block["Age"] = 0
                block["Planted_Year"] = year

            base_yield = base_yield_by_age(block["Age"])

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Management metrics
    total_ffb = df["Total_FFB_t"].sum()
    avg_yield = df["FFB_t_ha"].sum()
    old_blocks = df[df["Age"] > 25]["Block"].nunique()

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