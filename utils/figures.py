import os
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import statsmodels.api as sm
# import logging


def plot_nodes(df, reach=None):
    # Function for plotting node level data.
    if reach is None:
        rch = 81247100041  # default reach
    else:
        rch = reach
    node_reaches = df.loc[df['reach_id'] == rch]

    # add base plots
    fig = make_subplots(rows=1, cols=2)
    fig.add_trace(go.Scatter(x=node_reaches['dist_out']/1000, y=node_reaches['wse'], mode='lines+markers'), row=1, col=1)
    fig.add_trace(go.Scatter(x=node_reaches['dist_out']/1000, y=node_reaches['width'], mode='markers'), row=1, col=2)
    # Update xaxis properties
    fig.update_xaxes(title_text="Distance from Outlet (km)", row=1, col=1)
    fig.update_xaxes(title_text="Distance from Outlet (km)", row=1, col=2)
    # Update yaxis properties
    fig.update_yaxes(title_text="Water Surface Elevation (m)", row=1, col=1)
    fig.update_yaxes(title_text="Width (m)", row=1, col=2)
    # overall figure properties
    fig.update_layout(
        height=400, #width=1400,
        title_text="Reach "+str(rch)+": Node Level Attributes",
        title_x=0.5,
        showlegend=False,
        plot_bgcolor='#dce0e2', # 'whitesmoke'
        transition_duration=500
    )
    return fig


def plot_field_measure(df, reach=None):
    """ New function to plot the reach-level SWOT timeseries data """
    # fig = px.scatter(df, x="gdp per capita", y="life expectancy", size="population", color="continent", hover_name="country", log_x=True, size_max=60)
    fig = px.line(df, x=df.index, y="gage_height_va", markers=True, title="Water Surface Elevation (feet)")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="WSE (feet)")
    fig.update_layout(
        height=480,  #width=1400,
        title_text="WSE from USGS Gage Field Measurements",
        title_x=0.5,
        showlegend=False,
        plot_bgcolor='#dce0e2',  # 'whitesmoke'
        transition_duration=500  # BNY
    )
    return fig


def plot_scatter(df, reach=None):
    """ New function to plot the reach-level SWOT timeseries data """
    # fig = px.scatter(df, x="gdp per capita", y="life expectancy", size="population", color="continent", hover_name="country", log_x=True, size_max=60)
    fig = make_subplots(rows=2, cols=2)
    fig.add_trace(go.Scatter(x=df.gage_height_va, y=df.discharge_va, mode="markers", text=df.index.date), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.gage_height_va, y=df.chan_width, mode="markers", text=df.index.date), row=1, col=2)
    fig.add_trace(go.Scatter(x=df.gage_height_va, y=df.chan_area, mode="markers", text=df.index.date), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.gage_height_va, y=df.chan_velocity, mode="markers", text=df.index.date), row=2, col=2)
    # Update xaxis properties
    fig.update_xaxes(title_text="WSE (feet)", row=1, col=1)
    fig.update_yaxes(title_text="Discharge (cfs)", row=1, col=1)
    fig.update_xaxes(title_text="WSE (feet)", row=1, col=2)
    fig.update_yaxes(title_text="Width (feet)", row=1, col=2)
    fig.update_xaxes(title_text="WSE (feet)", row=2, col=1)
    fig.update_yaxes(title_text="X-section area", row=2, col=1)
    fig.update_xaxes(title_text="WSE (feet)", row=2, col=2)
    fig.update_yaxes(title_text="Velocity (feet/sec)", row=2, col=2)
    # overall figure properties
    fig.update_layout(
        height=700,  # width=1400,
        title_text="USGS Gage Field Measurements",
        title_x=0.5,
        showlegend=False,
        plot_bgcolor='#dce0e2',  # 'whitesmoke'
        transition_duration=500  # BNY
    )
    return fig


def plot_swot_usgs(field_df, ida_df_subset, ida_df, reach_ts_sel, datum_elev=0):
    """ ida_df : matches with reach_ts_sel time closely (1 to 1) """
    fig = make_subplots(rows=1, cols=3, subplot_titles=["SWOT vs USGS Gage WSE", "SWOT and USGS Field Data", "USGS Realtime Discharge"])
    # fig.add_trace(go.Scatter(x=ida_df.stage, y=ida_df.discharge, mode="markers", text=ida_df.index.date), row=1, col=1)
    fig.add_trace(go.Scatter(x=ida_df_subset.stage + datum_elev, y=reach_ts_sel.wse, mode="markers", name="SWOT vs USGS"), row=1, col=1)
    # Add OLS fit to the plot
    mod = sm.OLS(reach_ts_sel.wse.values, sm.add_constant(ida_df_subset.stage.values + datum_elev)).fit()  # , missing="drop"
    fig.add_trace(go.Scatter(x=ida_df_subset.stage + datum_elev, y=mod.fittedvalues, mode="lines", name=f"OLS trendline. (R-squared={mod.rsquared:.2f})"), row=1, col=1)

    fig.add_trace(go.Scatter(x=reach_ts_sel.wse, y=reach_ts_sel.width, mode="markers", name="SWOT"), row=1, col=2)  # SWOT
    fig.add_trace(go.Scatter(x=field_df.gage_height_va + datum_elev, y=field_df.chan_width, mode="markers", name="USGS Field Data"), row=1, col=2)  # USGS Field Measure   
    fig.add_trace(go.Scatter(x=ida_df.index, y=ida_df.discharge, mode="lines", text=ida_df.index, name="hourly (from usgs_IDA)"), row=1, col=3)
    # Update xaxis properties
    fig.update_xaxes(title_text="WSE Gage [m]", row=1, col=1)
    fig.update_yaxes(title_text="WSE SWOT [m]", row=1, col=1)
    fig.update_xaxes(title_text="WSE [m]", row=1, col=2)
    fig.update_yaxes(title_text="Width [m]", row=1, col=2)
    fig.update_xaxes(title_text="Date", row=1, col=3)
    fig.update_yaxes(title_text="Discharge [cumec]", row=1, col=3)
    # overall figure properties
    fig.update_layout(
        height=500,  # width=1400,
        title_text="USGS Data (IDA and Field Measurements)",
        title_x=0.5,
        showlegend=True,
        plot_bgcolor='#dce0e2',
        transition_duration=700)
    return fig
