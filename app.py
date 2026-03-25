import streamlit as st
import pandas as pd
import plotly.express as px
from palmopsim_model import run_simulation, run_sensitivity_analysis, get_estate_age_distribution

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
st.markdown(
    "Configure simulation parameters in the sidebar. Run one or more scenarios to compare"
    "long-term FFB production, sensitive to key inputs, and estate age health."
)
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

scenario_descriptions = {
    "Conservative": "Lower yield assumption (-10%). Risk-averse planning.",
    "Moderate": "Baseline yield assumption (0%). Standard operations.",
    "Aggressive": "Higher yield assumption (+10%). Optimistic strategy."
}
for s in scenarios:
    st.sidebar.caption(f"{s}: {scenario_descriptions[s]}")

st.sidebar.markdown("**Estate Configuration**")
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

st.sidebar.markdown("**Management Inputs**")

fertilizer = st.sidebar.slider(
    "Fertilizer Effect (%)",
    min_value = -10, # under-fertilization reduces yield
    max_value = 20, # over-fertilization can increase yield
    value = 0,
    step = 1,
    help = "Nutrient management input. Negative = under-fertilized, 0 = standard, positive = enhanced application. Follows diminishing returns."   
)

harvest_interval = st.sidebar.slider(
    "Harvest Interval (Months)",
    min_value = 6,
    max_value = 12,
    value = 12,
    step = 1,
    help = "How frequently blocks are harvested. Intervals longer than 12 months reduce harvest efficiency due to over-ripening losses."
)

# Phase 5 Implementation (18/2/2026): added climate and pest slider
st.sidebar.markdown("**Environmental Conditions**")
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
        
        # Phase 6 Implementation (21/2/2026): Added sensitivity function
        selected_scenario = scenarios[0]

        base_params = {
            "scenario_name": selected_scenario,
            "simulation_years": simulation_years,
            "num_blocks": num_blocks,
            "fertilizer": fertilizer,
            "harvest_interval": harvest_interval,
            "climate_slider": climate_slider,
            "pest_slider": pest_slider
        }

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
            title = "Annual FFB Production Comparison",
            markers = True
        )
        
        # Force hover to show 2 decimals
        fig.update_traces(hovertemplate = 'Year: %{x}<br>Total FFB(t): %{y:.2f}')
        fig.update_layout(yaxis_tickformat = "~s")

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

        # Phase 6 implementation (21/2/2026): Sensitivity Section
        st.markdown("---")
        st.subheader("Sensitivity Analysis (±10%)")

        for scenario in scenarios:
            st.caption(f"Based on: {scenario} scenario")

            base_params ["scenario_name"] = scenario
            scenario_sensitivity = []

            # Fertilizer sensitivity (±10%)
            scenario_sensitivity.append(
                run_sensitivity_analysis(
                    base_params,
                    "fertilizer",
                    fertilizer - 10,
                    fertilizer + 10
                )
            )

            # Climate sensitivity (±10%)
            scenario_sensitivity.append(
                run_sensitivity_analysis(
                    base_params,
                    "climate_slider",
                    climate_slider - 10,
                    climate_slider + 10
                )
            )

            # Pest sensitivity (±5% to keep realistic bounds)
            scenario_sensitivity.append(
                run_sensitivity_analysis(
                    base_params,
                    "pest_slider",
                    max(0, pest_slider - 5),
                    pest_slider + 5
                )
            )

            st.dataframe(pd.DataFrame(scenario_sensitivity))
            st.caption(
                "Low_Change_%: impact of reducing the variable by the test amount. "
                "High_Change_%: impact of increasing it. Values show % change vs baseline total FFB."
            )

        # Phase 6 Implementation (1/3/2026): Estate Age Health Indicator
        st.markdown("---")
        st.subheader("Estate Age Health (Final Year)")

        selected_results = results_dict[selected_scenario]

        age_distribution = get_estate_age_distribution(selected_results["dataframe"])

        age_df = pd.DataFrame(
            age_distribution.items(),
            columns = ["Age Category", "Percentage (%)"]
        )

        st.dataframe(age_df)

        # Phase 6 Implementation (1/3/2026): Replanting Strategy Comparison
        st.markdown("---")
        st.subheader("Replanting Strategy Comparison")

        replant_strategies = [0.03, 0.05, 0.08]
        strategy_results = []

        for rate in replant_strategies:

            strategy_params = base_params.copy()
            strategy_params ["replant_rate"] = rate

            sim_results = run_simulation(**strategy_params)

            strategy_results.append({
                "Replant Rate (%)": int(rate * 100),
                "Total FFB (t)": sim_results["total_ffb"],
                "Average Yield (t/ha)": sim_results["average_yield"]
            })
        
        strategy_df = pd.DataFrame(strategy_results)
        st.dataframe(strategy_df)
        
st.markdown("---")
st.caption("PalmOpsSim – Phase 4 UI Prototype | © 2026")
