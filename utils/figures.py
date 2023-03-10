import os
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
# import logging


def plot_field_measure(df, reach=None):
    """ New function to plot the reach-level SWOT timeseries data """
    # fig = px.scatter(df, x="gdp per capita", y="life expectancy", size="population", color="continent", hover_name="country", log_x=True, size_max=60)
    fig = px.line(
        df,
        x=df.index,
        y="gage_height_va",
        markers=True,
        title="Water Surface Elevation (feet)",        
    )
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
    fig.add_trace(
        go.Scatter(
            x=df.gage_height_va,
            y=df.discharge_va,
            mode="markers", text=df.index.date),
        row=1, col=1)

    fig.add_trace(
        go.Scatter(
            x=df.gage_height_va,
            y=df.chan_width,
            mode="markers", text=df.index.date),
        row=1, col=2)

    fig.add_trace(
        go.Scatter(
            x=df.gage_height_va,
            y=df.chan_area,
            mode="markers", text=df.index.date),
        row=2, col=1)

    fig.add_trace(
        go.Scatter(
            x=df.gage_height_va,
            y=df.chan_velocity,
            mode="markers", text=df.index.date),
        row=2, col=2)
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
