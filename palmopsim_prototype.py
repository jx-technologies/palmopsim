""" 
PalmOpsSim - Phase 3 Prototype
Simulation-based block-level FFB yield modelling
"""

# Step 1 - Importing essentials 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ------------------------
# Plantation Configuration
# ------------------------

NUM_BLOCKS = 10
SIMULATION_YEARS = 10

BLOCK_AREA_HA = 25 # assume uniform block size
INITIAL_AGE_RANGE = (3, 25) # years

# ------------------------
# Define Yield Behaviour
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
# Initialize Plantation Blocks
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
# Create Simulation Loop
# ------------------------

results = []

for year in range(1, SIMULATION_YEARS + 1):
    for block in blocks:
        age = block["Age"]
        base_yield = base_yield_by_age(age)

        # Introduce variability (± 10%)
        variability = np.random.normal(1.0, 0.1)
        yield_t_ha = max(base_yield * variability, 0)

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
# Convert results into a table
# ------------------------
df = pd.DataFrame(results)

# ------------------------
# Export to Excel
# Note (10/2/2026): This uses openpyxl to write excel files
# ------------------------
df.to_excel ("PalmOpsSim_FFB_Results.xlsx", index=False)

# ------------------------
# Create Simple Monitoring Plots
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