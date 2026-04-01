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

if not run_button and "results_dict" not in st.session_state:
    st.info(
        "Configure simulation parameters in the sidebar and click 'Run Simulation' to generate results. "
        "Run one or more scenarios to compare long-term FFB production, sensitivity to key inputs, and estate age health."
    )
    
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

        # Save results
        st.session_state["results_dict"] = results_dict
        st.session_state["last_scenarios"] = scenarios
        st.session_state["last_params"] = base_params

if "results_dict" in st.session_state:
    results_dict = st.session_state["results_dict"]
    scenarios = st.session_state["last_scenarios"]
    base_params = st.session_state["last_params"]    
    
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

    st.markdown("---")
    st.subheader("Scenario Comparison - KPIs")
    
    for s in scenarios:
        st.markdown(f"**{s} Scenario**")
        col1, col2, col3 = st.columns(3)

        total_ffb = results_dict[s]["total_ffb"]
        avg_yield = results_dict[s]["average_yield"]
        old_blocks = results_dict[s]["old_blocks"]

        col1.metric(
            label = "Total FFB Production",
            value = f"{total_ffb:,.0f} t",
            help = "Total Fresh Fruit Bunch production across all blocks over the full simulation period"
        )

        col2.metric(
            label = "Average yield",
            value = f"{avg_yield:.2f} t/ha",
            help = "Average FFB yield per hectare per year across the simulation"
        )

        col3.metric(
            label = "Overaged blocks",
            value = f"{old_blocks} blocks",
            help = "Number of blocks older than 25 years at the end of the simulation. These are candidates for replanting."
        )

    st.markdown("---")

    # Malaysian benchmark: ~17 t/ha
    benchmark_yield = 17.0

    for s in scenarios:
        avg_yield = results_dict[s]["average_yield"]
        old_blocks = results_dict[s]["old_blocks"]
        total_ffb = results_dict[s]["total_ffb"]

        above_below = "above" if avg_yield >= benchmark_yield else "below"
        gap = abs(avg_yield - benchmark_yield)

        if old_blocks == 0:
            replant_msg = "No blocks have exceeded 25 years — replanting is on track."
        elif old_blocks <= num_blocks * 0.2:
            replant_msg = f"{old_blocks} block(s) need replanting attention soon."
        else:
            replant_msg = (
                f"{old_blocks} block(s) are overaged — replanting is urgently needed "
                f"to prevent further structural decline."
            )

        if avg_yield >= benchmark_yield and old_blocks <= num_blocks * 0.2:
            st.success(
                f"**{s}:** Average yield of {avg_yield:.2f} t/ha is {gap:.2f} t/ha {above_below} "
                f"the Malaysian benchmark of {benchmark_yield} t/ha. {replant_msg}"
            )
        elif avg_yield < benchmark_yield and old_blocks > num_blocks * 0.2:
            st.error(
                f"**{s}:** Average yield of {avg_yield:.2f} t/ha is {gap:.2f} t/ha {above_below} "
                f"the Malaysian benchmark of {benchmark_yield} t/ha. {replant_msg}"
            )
        else:
            st.warning(
                f"**{s}:** Average yield of {avg_yield:.2f} t/ha is {gap:.2f} t/ha {above_below} "
                f"the Malaysian benchmark of {benchmark_yield} t/ha. {replant_msg}"
            )

    st.subheader("Annual Production Trend")
    # Chart caption explaining what trends mean.
    st.caption(
        "Declining trend reflects estate aging. A recovery mid-simulation indicates replanted "
        "blocks reaching productive age. Flat or rising trends suggest a well-managed age structure."
    )

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
    # Phase 6 Improvement (25/3/2026): Y-axis starts at 0
    fig.update_layout(
        yaxis_tickformat = "~s",
        yaxis_rangemode = "tozero"
    )

    # Phase 6 Improvement (25/3/2026): Add a horizontal reference line at baseline yield
    # Reference line at Malaysian average yield (~17 t/ha total estate equivalent)
    baseline_ref = 17 * num_blocks * 25 # t/ha × blocks × block_area_ha
    fig.add_hline(
        y = baseline_ref,
        line_dash = "dot",
        line_color = "gray",
        annotation_text = "Malaysian avg. reference",
        annotation_position = "bottom right"
    )

    st.plotly_chart(fig, width = "stretch")

    # Build the takeaway from the annual summary data
    best_scenario = max(scenarios, key = lambda s: results_dict[s]["total_ffb"])
    worst_scenario = min(scenarios, key = lambda s: results_dict[s]["total_ffb"])
    best_ffb = results_dict[best_scenario]["total_ffb"]
    worst_ffb = results_dict[worst_scenario]["total_ffb"]

    if len(scenarios) == 1:
        # Single scenario - comment on the trend direction instead
        annual = results_dict[scenarios[0]]["annual_summary"]
        trend = annual.iloc[-1] - annual.iloc[0]
        direction = "increased" if trend > 0 else "declined"
        st.info(
            f"**Key takeaway:** Under the **{scenarios[0]}** scenario, total estate production "
            f"has {direction} by **{abs(trend):,.0f} tonnes** from year 1 to year {simulation_years}. "
            f"Check the estate age health section below to understand why."
        )
    
    else: 
        # Multiple scenarios - compare best to worst
        gap = best_ffb - worst_ffb
        st.info(
            f"**Key takeaway:** Across your selected scenarios, **{best_scenario}** produces the "
            f"most at **{best_ffb:,.0f} tonnes** total — **{gap:,.0f} tonnes** more than "
            f"**{worst_scenario}** over the {simulation_years}-year simulation. "
            f"Scroll down to see what is driving this gap."
        )

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
    st.subheader("What affects production the most?")
    # Subheader to explain test range
    st.caption(
        "Each group of bars shows what happens to total FFB production if a factor is "
        "pushed up or down from your current settings. A taller bar — in either direction — "
        "means that factor has a bigger impact on your estate's output."
    )
    for scenario in scenarios:

        base_params ["scenario_name"] = scenario
        scenario_sensitivity = []

        # Fertilizer sensitivity (±10%)
        scenario_sensitivity.append(
            run_sensitivity_analysis(
                base_params,
                "fertilizer",
                fertilizer - 20,    # Was -10
                fertilizer + 20     # Was +10
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

        # Sensitivity analysis
        sens_df = pd.DataFrame(scenario_sensitivity)

        # Rename factors 
        sens_df ["Factor"] = sens_df["Factor"].map({
            "fertilizer": "Fertilizer Input",
            "climate_slider": "Climate Conditions",
            "pest_slider": "Pest Pressure",
        })

        sens_df = sens_df.rename(columns={
            "Low_Change_%": "If reduced",
            "High_Change_%": "If increased"
        })

        y_max = sens_df[["If reduced", "If increased"]].max().max()
        y_min = sens_df[["If reduced", "If increased"]].min().min()

        sens_fig = px.bar (
            sens_df,
            x = "Factor",
            y = ["If reduced", "If increased"],
            barmode = "group",
            title = f"Which factors affect production the most? ({scenario}) scenario",
            labels = {
                "value": "% Change in Total FFB production", 
                "variable": "",
                },
            color_discrete_map = {
                "If reduced": "#EF553B",
                "If increased": "#00CC96"
            }
        )

        sens_fig.update_traces(
            texttemplate = "%{y:+.1f}%",
            textposition = "outside"
        )

        sens_fig.add_hline (y = 0, line_dash = "dash", line_color = "gray")
        
        sens_fig.update_layout(
            yaxis_range = [y_min * 1.4, y_max * 1.4]
        )
        st.plotly_chart (sens_fig, width = "stretch")

        # Find the factor with the biggest overall swing
        sens_df["Max_Swing"] = sens_df[["If reduced", "If increased"]].abs().max(axis=1)
        top_factor = sens_df.loc[sens_df["Max_Swing"].idxmax(), "Factor"]
        top_swing = sens_df["Max_Swing"].max()

        st.info(
            f"**Key takeaway:** For the {scenario} scenario, **{top_factor}** has the "
            f"largest impact on production — swinging output by up to {top_swing:.1f}% "
            f"from your current settings. This is where management effort will have the greatest effect."
        )

    # Phase 6 Implementation (1/3/2026): Estate Age Health Indicator
    st.markdown("---")
    st.subheader("Is the estate in good structural health?")
    st.caption (
        "This shows the age profile of all plantation blocks at the end of the simulation. "
        "A healthy estate has most blocks in the Prime category (9 - 18 years) - these are the"
        "most productive years. A high proportion of Declining or Overaged blocks means the "
        "estate needs a replanting programme, which fertilizer and pest management alone cannot fix."
    )
    for s in scenarios:
        age_distribution = get_estate_age_distribution(results_dict[s]["dataframe"])

        age_df = pd.DataFrame(
            age_distribution.items(),
            columns=["Age Category", "Percentage (%)"]
        )

        age_fig = px.bar (
            age_df,
            x = "Age Category",
            y = "Percentage (%)",
            title = f"Estate Age Distribution - End of Year {simulation_years} ({s})",
            color = "Age Category",
            color_discrete_map = {
                "Immature (0-2)":    "#636EFA",
                "Young (3-8)":       "#00CC96",
                "Prime (9-18)":      "#19D3F3",
                "Declining (19-25)": "#FFA15A",
                "Overaged (>25)":    "#EF553B"
            },
            text = "Percentage (%)"
        )
        age_fig.update_traces(texttemplate = "%{text:.1f}%", textposition = "outside")
        max_pct = age_df["Percentage (%)"].max()
        age_fig.update_layout(
            yaxis_range = [0, max_pct * 1.15],
            showlegend = False
        )
        st.plotly_chart(age_fig, width = "stretch", key=f"age_dist_{s}")

        prime_pct = age_distribution.get("Prime (9-18)", 0)
        overaged_pct = age_distribution.get("Overaged (>25)", 0)
        declining_pct = age_distribution.get("Declining (19-25)", 0)

        if prime_pct >= 40:
            st.success(
                f"**Healthy structure:** {prime_pct:.1f}% of blocks are in their prime productive years. "
                f"The estate is well-positioned for sustained output."
            )
        elif overaged_pct + declining_pct >= 50:
            st.error(
                f"**Structural risk:** {overaged_pct + declining_pct:.1f}% of blocks are Declining or Overaged. "
                f"Production will continue to fall unless a replanting programme is accelerated."
            )
        else:
            st.warning(
                f"**Mixed profile:** The estate has room to improve. Consider increasing replanting rate "
                f"to grow the share of Prime blocks over time."
            )

    st.caption(
        "Tip: Run the simulation again with a higher replanting rate or longer duration "
        "to see how the age profile shifts over time."
    )

    # Phase 6 Implementation (1/3/2026): Replanting Strategy Comparison
    st.markdown("---")
    st.subheader("How does replanting pace affect long-term production?")
    st.caption(
        "Tests three replanting speeds - slow (5%), standard (10%), and fast (20%) - across "
        "all selected scenarios. A higher replanting rate means more overaged blocks are "
        "renewed each year, which protects future yield at the cost of short-term investment."
    )

    replant_strategies = [0.05, 0.10, 0.20]
    strategy_labels = {0.05: "Slow (5%)", 0.10: "Standard (10%)", 0.20: "Fast (20%)"}
    strategy_results = []

    for scenario in scenarios:
        base_params["scenario_name"] = scenario

        for rate in replant_strategies:
            strategy_params = base_params.copy()
            strategy_params["replant_rate"] = rate
            sim_results = run_simulation(**strategy_params)

            strategy_results.append({
                "Scenario": scenario,
                "Replant Rate": strategy_labels[rate],
                "Total FFB (t)": sim_results["total_ffb"],
                "Average Yield (t/ha)": sim_results["average_yield"]
            })
    
    strategy_df = pd.DataFrame(strategy_results)

    replant_fig = px.bar(
        strategy_df,
        x = "Replant Rate",
        y = "Total FFB (t)",
        color = "Scenario",
        barmode = "group",
        text = "Total FFB (t)",
        title = "Total FFB Production by Replanting Rate and Scenario",
        category_orders = {"Replant Rate": ["Slow (3%)", "Standard (5%)", "Fast (8%)"]}
    )

    replant_fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    max_val = strategy_df["Total FFB (t)"].max()
    replant_fig.update_layout(
        yaxis_range = [0, max_val * 1.15],
        xaxis_title = "Replanting Rate",
        yaxis_title = "Total FFB Production (tonnes)",
        legend_title = "Scenario"
    )
    st.plotly_chart(replant_fig, width="stretch")

    # Auto takeaway
    best_row = strategy_df.loc[strategy_df["Total FFB (t)"].idxmax()]
    st.info(
        f"**Key takeaway:** The highest total production across your selected scenarios is "
        f"**{best_row['Total FFB (t)']:,.0f} tonnes** under the **{best_row['Scenario']}** scenario "
        f"with a **{best_row['Replant Rate']}** replanting rate."
    )
    
    # New addition: Final analysis
    st.markdown("---")
    st.subheader("Overall Estate Analysis")
    st.caption(
        "A summary of what this simulation run is telling you, based on all the outputs above."
    )

    # Gather data across all scenarios
    all_yields = {s: results_dict[s]["average_yield"] for s in scenarios}
    all_ffb    = {s: results_dict[s]["total_ffb"] for s in scenarios}
    all_old    = {s: results_dict[s]["old_blocks"] for s in scenarios}
    best_scenario = max(all_yields, key = all_yields.get)
    worst_scenario = min(all_yields, key = all_yields.get)
    benchmark = 17.0

    findings = []

    # --- Finding 1: Overall yield vs benchmark ---
    above_bench = [s for s in scenarios if all_yields[s] >= benchmark]
    below_bench = [s for s in scenarios if all_yields[s] <  benchmark]

    if above_bench:
        findings.append(
            f"**Yield performance:** "
            + ", ".join(f"**{s}** ({all_yields[s]:.2f} t/ha)" for s in above_bench)
            + f" met or exceeded the Malaysian benchmark of {benchmark} t/ha."
        )
    if below_bench:
        findings.append(
            f"**Yield concern:** "
            + ", ".join(f"**{s}** ({all_yields[s]:.2f} t/ha)" for s in below_bench)
            + f" fell below the Malaysian benchmark of {benchmark} t/ha. "
            + "Review fertilizer input and climate conditions."
        )

    # --- Finding 2: Scenario gap (only if multiple scenarios) ---
    if len(scenarios) > 1:
        gap = all_ffb[best_scenario] - all_ffb[worst_scenario]
        pct_gap = (gap / all_ffb[worst_scenario]) * 100
        findings.append(
            f"**Scenario gap:** The **{best_scenario}** scenario outproduced **{worst_scenario}** "
            f"by **{gap:,.0f} tonnes** ({pct_gap:.1f}%) over {simulation_years} years — "
            f"showing how much management assumptions affect long-term output."
        )

    # --- Finding 3: Replanting health ---
    urgent_replant = [s for s in scenarios if all_old[s] > num_blocks * 0.2]
    healthy_replant= [s for s in scenarios if all_old[s] == 0]

    if urgent_replant:
        findings.append(
            f"**Replanting urgency:** "
            + ", ".join(f"**{s}** ({all_old[s]} overaged blocks)" for s in urgent_replant)
            + " show signs of structural aging. Accelerating replanting is strongly recommended "
            "to prevent compounding yield decline."
        )
    if healthy_replant:
        findings.append(
            f"**Replanting health:** "
            + ", ".join(f"**{s}**" for s in healthy_replant)
            + " ended the simulation with no overaged blocks — "
            "the replanting programme is keeping pace with estate aging."
        )

    # --- Finding 4: Simulation duration note ---
    if simulation_years < 10:
        findings.append(
            f"**Short horizon note:** This simulation only covers {simulation_years} year(s). "
            "Consider running a longer simulation (15–25 years) to observe the full impact "
            "of replanting cycles and estate aging on production."
        )
    elif simulation_years >= 20:
        findings.append(
            f"**Long horizon insight:** Over {simulation_years} years, estate age structure "
            "becomes the dominant driver of production — individual management inputs have "
            "diminishing influence compared to the replanting programme."
        )

    # --- Render findings as numbered list ---
    for i, finding in enumerate(findings, 1):
        st.markdown(f"{i}. {finding}")

    # --- Overall verdict ---
    st.markdown("---")
    avg_of_avgs = sum(all_yields.values()) / len(all_yields)
    total_old   = sum(all_old.values())

    if avg_of_avgs >= benchmark and total_old <= num_blocks * 0.2:
        st.success(
            f"**Overall verdict:** This simulation suggests a well-performing estate. "
            f"Average yield across scenarios ({avg_of_avgs:.2f} t/ha) is above the national "
            f"benchmark, and the replanting programme appears to be on track."
        )
    elif avg_of_avgs < benchmark and total_old > num_blocks * 0.2:
        st.error(
            f"**Overall verdict:** This simulation flags structural and productivity concerns. "
            f"Average yield ({avg_of_avgs:.2f} t/ha) is below the national benchmark, and "
            f"overaged blocks indicate a delayed replanting programme. "
            f"Review the Replanting Strategy Comparison section above for options."
        )
    else:
        st.warning(
            f"**Overall verdict:** Mixed results. Some aspects of the estate are performing "
            f"well, but there are areas that need attention — particularly around "
            f"{'replanting' if total_old > 0 else 'yield improvement'}. "
            f"Use the sensitivity analysis above to identify the highest-impact next step."
        )
        
    st.markdown("---")
    st.caption("PalmOpsSim — Simulation-Based Oil Palm Plantation Monitoring System | Phase 7 | © 2026 (Kong Kai Mann / Eng Yong Xiang- JX Tech)")
