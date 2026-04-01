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
    """
    Returns the baseline FFB yield (t/ha) based on palm age.
    Reflects the six-stage lifecycle defined in Phase 5:
    immature → ramp-up → approaching peak → peak → decline → unproductive.
    """
    if age < 3:
        return 0                        # Immature - No harvestable yield
    elif 3 <= age < 6:
        return 8 + (age - 3) * 4        # Rapid rampup from first fruiting
    elif 6 <= age <= 9:
        return 20 + (age - 6) * 2       # Approaching peak production
    elif 9 <= age <= 18: 
        return 26                       # Peak plateau (~26 t/ha, Phase 5) 
    elif 19 <= age <= 28:
        return 26 - (age - 18) * 1.0    # Gradual decline post-prime
    else:
        return 0                        # Economically unproductive (>28 yrs)
    
# ------------------------
# Main Simulation Function (15/2/2026)
# Phase 5 Implementation (16/2/2026): Added Staggered planting for plantation blocks
# Phase 5 Implementation (16/2/2026): Added replanting logic in simulation loop
# Phase 5 Implementation (16/2/2026): Added fertilizer in yield calculation
# Phase 5 Implementation (16/2/2026): Added climate slider and pest slider
# Phase 6 Implementation (1/3/2026): Added Replanting Strategy Comparison
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
        climate_slider = 0, # (% adjustment to climate)
        pest_slider = 5, # (% yield loss from pests)
        replant_rate = None # Change from 0.05 to None
):
    """
    Simulates FFB production for a managed oil palm estate over a defined period.
    Applies age-yield curve, fertilizer response, climate factor, pest pressure, 
    harvest efficiency, and replanting constraints (Phase 5).
    Returns a dict with: dataframe, total_ffb, average_yield, old_blocks,
    annual summary, annual_yield.
    """
    
    # Scenario configuration
    # Make replanting rate scenario dependent
    if scenario_name == "Conservative":
        yield_adjustment = -0.10
        if replant_rate is None:
            replant_rate = 0.03 # Slow replanting - cost cautious
    elif scenario_name == "Moderate":
        yield_adjustment = 0.00
        if replant_rate is None:
            replant_rate = 0.05 # Standard replanting program
    elif scenario_name == "Aggressive":
        yield_adjustment = 0.10
        if replant_rate is None:
            replant_rate = 0.08 # Fast replanting  - Investing in future yield
    else:
        yield_adjustment = 0.00
        replant_rate = 0.05

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
        # Phase 5 Modification (19/2/2026): changed to one climate factor per year, deterministic
        # Modification (2/3/2026): modified climate factor to incoporate scenario and age distribution
        for block in blocks:
            age = block["Age"]
            year_climate_noise = np.random.normal(1.0, 0.02)
            climate_factor = year_climate_noise * (1 + (climate_slider/100) * (age / 20))
            base_yield = base_yield_by_age(age)

            # Apply scenario adjustment + fertilizer effect
            # (18/2/2026): Make fertilizer response non-linear
            # (2/3/2026): Slight adjustment to fertilizer response

            # Diminishing returns: Doubling fertilizer does not double yield (Phase 5, Improvement 2)
            fertilizer_response = 1 + (0.6 * (fertilizer / (100 + abs(fertilizer))))
            adjusted_yield = base_yield * (1 + yield_adjustment) * fertilizer_response

            # Apply variability as before
            # (18/2/2026): Added harvest efficiency
            # (18/2/2026): Added pest pressure
            # (2/3/2026): Modified pest impact to be stronger at higher yield
            block_variation = np.random.normal(1.0, 0.03) # Small per-block noise
            harvest_efficiency = 1.0 - (harvest_interval - 6) * 0.01
            pest_pressure = pest_slider / 100 # Deterministic from slider

            yield_t_ha = max(adjusted_yield * climate_factor * block_variation, 0)
            yield_t_ha *= harvest_efficiency
            yield_t_ha *= (1 - pest_pressure * (1 + adjusted_yield / 50))
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
            # Phase 5 Improvement (18/2/2026): New replanting logic - constrained rate per year
            # if block["Age"] > 28:
            #     # Replant block
            #     block["Age"] = 0
            #     block["Planted_Year"] = year

            # base_yield = base_yield_by_age(block["Age"])

        # Phase 5 Improvement (18/2/2026): New Replanting logic
        # Identify overaged blocks
        overaged_blocks = [b for b in blocks if b["Age"] > 28]

        # Replant only limited number (e.g. 5% of total blocks)
        max_replant = max(1, round(replant_rate * num_blocks))

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

    # Annual yield (t/ha)
    annual_area = num_blocks * block_area_ha
    annual_yield = annual_summary / annual_area

    # Return structured results
    return {
        "dataframe": df,
        "total_ffb": round(total_ffb, 1),
        "average_yield": round(avg_yield, 2),
        "old_blocks": old_blocks,
        "annual_summary": annual_summary,
        "annual_yield": annual_yield
    }

# Phase 6 Implementation (21/2/2026): Formal Sensitivity Comparison
def run_sensitivity_analysis(
        base_params,
        factor_name,
        low_value,
        high_value
):
    """
    Runs baseline, low, and high variation for a single factor.
    Returns a dict with Factor name and percentage change vs baseline for low and high values.
    """

    # Baseline
    baseline_results = run_simulation(**base_params)
    baseline_ffb = baseline_results["total_ffb"]

    # Low variation
    low_params = base_params.copy()
    low_params[factor_name] = low_value
    low_results = run_simulation(**low_params)
    low_ffb = low_results["total_ffb"]
    
    # 奥巴马想跟你谈恋爱

    # High variation
    high_params = base_params.copy()
    high_params[factor_name] = high_value
    high_results = run_simulation(**high_params)
    high_ffb = high_results["total_ffb"]

    return {
        "Factor": factor_name,
        "Low_Change_%": round((low_ffb - baseline_ffb) / baseline_ffb * 100, 2),
        "High_Change_%": round((high_ffb - baseline_ffb) / baseline_ffb * 100, 2)
    }

# Phase 6 Implementation (1/3/2026): Age Categorization Function
def get_estate_age_distribution(df):
    """
    Returns age category distribution for the final simulation year
    """

    final_year = df["Year"].max()
    final_df = df[df["Year"] == final_year]

    # Use unique blocks only (one record per block)
    block_ages = final_df.groupby("Block")["Age"].first()

    age_categories = {
        "Immature (0-2)": 0,
        "Young (3-8)": 0,
        "Prime (9-18)": 0,
        "Declining (19-25)": 0,
        "Overaged (>25)": 0
    }

    for age in block_ages:
        if age <= 2:
            age_categories["Immature (0-2)"] += 1
        elif age <= 8:
            age_categories["Young (3-8)"] += 1
        elif age <= 18:
            age_categories["Prime (9-18)"] += 1
        elif age <= 25:
            age_categories["Declining (19-25)"] += 1
        else:
            age_categories["Overaged (>25)"] += 1

    total_blocks = len(block_ages)

    # Convert to percentage
    age_distribution = {
        k: round((v / total_blocks) * 100, 1)
        for k, v in age_categories.items()
    }

    return age_distribution