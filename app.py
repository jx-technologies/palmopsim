import streamlit as st
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
scenario = st.sidebar.multiselect(
    "Select Strategy",
    ["Conservative", "Moderate", "Aggressive"]
)

if scenario == "Conservative":
    st.sidebar.caption("Lower yield assumption (-10%). Risk-averse planning.")
elif scenario == "Moderate":
    st.sidebar.caption("Baseline yield assumption (0%). Standard operations.")
elif scenario == "Aggressive":
    st.sidebar.caption("Higher yield assumption (+10%). Optimistic strategy.")

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

run_button = st.sidebar.button("Run Simulation")

if not run_button:
    st.info("Configure simulation parameters in the sidebar and click 'Run Simulation' to generate results.")
    
if run_button:
    results = run_simulation (
        scenario_name = scenario,
        simulation_years = simulation_years,
        num_blocks = num_blocks,
        fertilizer = fertilizer,
        harvest_interval = harvest_interval
    )

    st.subheader("Key Performance Indicators")

    # KPI Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Total FFB Production (tonnes)", 
        f"{results['total_ffb']:,}"
        )
    col2.metric(
        "Average Yield (t/ha)", 
        f"{results['average_yield']:,}"
        )
    col3.metric(
        "Blocks Above 25 Years", 
        f"{results['old_blocks']:,}",
        delta="All blocks replanted" if results['old_blocks'] == 0 else None
        )

    st.markdown("---")
    
    st.subheader("Annual Production Trend")
    st.markdown("<br>", unsafe_allow_html=True)

    st.caption("Annual total FFB production by year")
    st.line_chart(results["annual_summary"], height = 300)
    with st.expander("View Detailed Simulation Data"):
        st.dataframe(results["dataframe"])

    csv = results["dataframe"].to_csv(index = False).encode("utf-8")

    st.download_button(
        "Download Results as CSV",
        csv,
        "PalmOpsSim_Results.csv",
        "text/csv"
    )

st.markdown("---")
st.caption("PalmOpsSim – Phase 4 UI Prototype | © 2026")
