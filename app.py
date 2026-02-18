import streamlit as st
import pandas as pd
import plotly.express as px
from palmopsim_model import run_simulation

# ------------------------
# Page Configuration (15/2/2026)
# ------------------------
st.set_page_config(
    page_title ="PalmOpsSim",
    layout ="wide"
)

# ------------------------
# Title (15/2/2026)
# ------------------------
st.title("PalmOpsSim")
st.subheader("Operational Simulation Dashboard")

# ------------------------
# Sidebar - Simulation Configuration (15/2/2026)
# Phase 5 Implementation (16/2/2026): Added harvest interval and fertilizer application
# Phase 5 Implementation (16/2/2026): Added replanting logic explanation
# Phase 5 Implementation (17/2/2026): Multiple scenarios (Introduction)
# ------------------------
st.sidebar.header("Simulation Configuration")
st.sidebar.caption("Note: A fixed random seed is used for reproducible results across runs.")

# (17/2/2026) Changed selectbox to multiselect to pick one or more scenarios at once
scenarios = st.sidebar.multiselect(
    "Select Strategy",
    ["Conservative", "Moderate", "Aggressive"]
)

# if scenarios == "Conservative":
#     st.sidebar.caption("Lower yield assumption (-10%). Risk-averse planning.")
# elif scenario == "Moderate":
#     st.sidebar.caption("Baseline yield assumption (0%). Standard operations.")
# elif scenario == "Aggressive":
#     st.sidebar.caption("Higher yield assumption (+10%). Optimistic strategy.")

simulation_years = st.sidebar.number_input(
    "Simulation Duration (Years)",
    min_value = 1,
    max_value = 30,
    value = 10
)

num_blocks = st.sidebar.number_input(
    "Number of Blocks",
    min_value = 1,
    max_value = 50,
    value = 10
)

harvest_interval = st.sidebar.slider(
    "Harvest Interval (Months)",
    min_value = 6,
    max_value = 12,
    value = 12,
    step = 1
)

fertilizer = st.sidebar.slider(
    "Fertilizer Effect (%)",
    min_value = -10, # under-fertilization reduces yield
    max_value = 20, # over-fertilization can increase yield
    value = 0,
    step = 1   
)

# Phase 5 Implementation (18/2/2026): added climate and pest slider
climate_slider = st.sidebar.slider(
    "Climate Factor Adjustment (%)",
    min_value = -20,
    max_value = 20,
    value = 0,
    step = 1,
    help = "Adjust expected climate conditions: negative = dry year, positive = wet year."
)

pest_slider = st.sidebar.slider(
    "Pest Pressure (%)",
    min_value = 0,
    max_value = 20,
    value = 5,
    step = 1,
    help = "Average yield reduction due to pests / diseases."
)

# Phase 5 Modification (18/2/2026): Disable run button until one scenario is selected
run_button = st.sidebar.button("Run Simulation", disabled = (len(scenarios) == 0))

if not run_button:
    st.info("Configure simulation parameters in the sidebar and click 'Run Simulation' to generate results.")
    
# Phase 5 Implementation (18/2/2026) : Check if at least 1 scenario is selected
if run_button:
    if len(scenarios) == 0:
         st.warning("Please select at least one scenario to run the simulation.")
    
    else:
        results_dict = {} 
        
        for scenario in scenarios: # (17/2/2026): Scenarios come from multiselect
            results_dict[scenario] = run_simulation (
            scenario_name = scenario,
            simulation_years = simulation_years,
            num_blocks = num_blocks,
            fertilizer = fertilizer,
            harvest_interval = harvest_interval,
            climate_slider = climate_slider, # Pass slider value
            pest_slider = pest_slider # Pass slider value
        )

        # KPI Metrics
        # Phase 5 Implementation (17/2/2026): Add KPI Comparison Table
        kpi_table = pd.DataFrame([
            {
                "Scenario": s,
                "Total FFB (t)": results_dict[s]["total_ffb"],
                "Average Yield (t/ha)": results_dict[s]["average_yield"],
                "Blocks > 25 yrs": results_dict[s]["old_blocks"]
            }
            for s in scenarios
        ])

        st.subheader("Scenario Comparison - KPIs")
        st.dataframe(kpi_table)

        st.markdown("---")
        
        st.subheader("Annual Production Trend")

        comparison_df = pd.DataFrame()

        for s in scenarios:
            comparison_df[s] = results_dict[s]["annual_summary"].round(2) # round to 2 decimals
        
        comparison_df = comparison_df.reset_index().rename(columns={"index": "Year"})

        fig = px.line(
            comparison_df,
            x = "Year",
            y = scenarios,
            labels = {"value": "Total FFB (t)", "variable": "Scenario"},
            title = "Annual FFB Production Comparison"
        )

        # Force hover to show 2 decimals
        fig.update_traces(hovertemplate = 'Year: %{x}<br>Total FFB(t): %{y:.2f}')

        st.plotly_chart(fig, width = "stretch")

        combined_df = pd.concat(
            [
                results_dict[s]["dataframe"].assign(scenario = s)
                for s in scenarios
            ],
            ignore_index = True
        )

        # Round numeric columns to 2 decimals
        combined_df[["FFB_t_ha", "Total_FFB_t"]] = combined_df[["FFB_t_ha", "Total_FFB_t"]].round(2)

        with st.expander("View Detailed Simulation Data"):
            st.dataframe(combined_df)
        
        csv = combined_df.to_csv(index = False).encode("utf-8")

        st.download_button(
            "Download Results as CSV",
            csv,
            "PalmOpsSim_Results.csv",
            "text/csv"
        )
st.markdown("---")
st.caption("PalmOpsSim – Phase 4 UI Prototype | © 2026")
