""" 
PalmOpsSim - Phase 3 Prototype
Simulation-based block-level FFB yield modelling
"""

# Step 1 - Importing essentials 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ------------------------
# Scenario Configuration (11/2/2026)
# ------------------------
SCENARIO_NAME = "Conservative"
YIELD_ADJUSTMENT = 0.10 #-10% yield assumption

# ------------------------
# Plantation Configuration (10/2/2026)
# ------------------------

NUM_BLOCKS = 10
SIMULATION_YEARS = 10

BLOCK_AREA_HA = 25 # assume uniform block size
INITIAL_AGE_RANGE = (3, 25) # years

# ------------------------
# Define Yield Behaviour (10/2/2026)
# ------------------------

# Base FFB yield by age class (t/ha/year)
def base_yield_by_age(age):
    if age < 3:
        return 0
    elif 3 <= age <= 7:
        return 18
    elif 8 <= age <= 18:
        return 25
    elif 19 <= age <= 25:
        return 20
    else:
        return 15
    
# ------------------------
# Initialize Plantation Blocks (10/2/2026)
# ------------------------

np.random.seed(42) # Reproducability

blocks = []

for block_id in range (1, NUM_BLOCKS + 1):
    block = {
        "Block": f"B{block_id}",
        "Area_ha": BLOCK_AREA_HA,
        "Age": np.random.randint(
            INITIAL_AGE_RANGE[0], INITIAL_AGE_RANGE[1] + 1
        )
    }
    blocks.append(block)

# ------------------------
# Create Simulation Loop (10/2/2026)
# Modification (11/2/2026): Modify simulation loop slightly (Line 76 & 77)
# ------------------------

results = []

for year in range(1, SIMULATION_YEARS + 1):
    for block in blocks:
        age = block["Age"]
        base_yield = base_yield_by_age(age)

        # Introduce variability (± 10%)
        variability = np.random.normal(1.0, 0.1)
        adjusted_yield = base_yield * (1 + YIELD_ADJUSTMENT)
        yield_t_ha = max(adjusted_yield * variability, 0)

        total_ffb = yield_t_ha * block["Area_ha"]

        results.append({
            "Year": year,
            "Block": block["Block"],
            "Age": age,
            "FFB_t_ha": round(yield_t_ha, 2),
            "Total_FFB_t": round(total_ffb, 2)
        })

        block["Age"] += 1 # Palms age each year


# ------------------------
# Convert results into a table (10/2/2026)
# ------------------------
df = pd.DataFrame(results)

# ------------------------
# Management Summary (11/2/2026)
# ------------------------
total_ffb = df["Total_FFB_t"].sum()
avg_yield = df["FFB_t_ha"].mean()

old_blocks = df[df["Age"] > 25]["Block"].nunique()

summary_text = f"""
PalmOpsSim Prototype Summary ({SCENARIO_NAME} Scenario)

- Total simulated FFB Production: {total_ffb:.1f} tonnes
- Average FFB yield: {avg_yield: .2f} t/ha
- Number of blocks above 25 years old: {old_blocks}

This simulation provides a high-level indication of yield trends and supports conservative estate-level planning decisions
"""

print (summary_text)

# Export to Excel (10/2/2026)
# Note (10/2/2026): This uses openpyxl to write excel files
# Addition (11/2/2026): Modified to save excel export files properly
# ------------------------
output_file = f"PalmOpsSim_FFB_Results_{SCENARIO_NAME}.xlsx"
df.to_excel (output_file, index=False)

# ------------------------
# Create Simple Monitoring Plots (10/2/2026)
# Bugfix (10/2/2026): Removed plt.figure() from block-level yield distribution as df.boxplot() creates its own figure
# ------------------------

# Annual estate yield trend
annual_summary = df.groupby("Year")["Total_FFB_t"].sum()

plt.figure()
plt.plot(annual_summary.index, annual_summary.values)
plt.xlabel("Year")
plt.ylabel("Total FFB (t)")
plt.title("Annual Estate FFB Production")
plt.show()

# Block-level yield distribution
df.boxplot(column="FFB_t_ha", by="Year")
plt.xlabel("Year")
plt.ylabel("FFB Yield (t/ha)")
plt.title("FFB Yield Distribution by Year")
plt.suptitle("")
plt.show()