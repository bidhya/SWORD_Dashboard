# import base64
# import datetime
# import io
import os
import netCDF4 as nc
import numpy as np
import pandas as pd
# from csv import writer, reader
# import time
import dash
from dash import dcc
from dash import html  # , dash_table
from dash.dependencies import Input, Output, State
# from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
load_figure_template("cerulean")

import logging
from utils import get_usgs_data

logging.basicConfig(filename="mylogs.log", level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

#################################################################################################
######################################  FUNCTIONS  ##############################################
#################################################################################################


### Function for formatting input node data.
def get_data(fn):
    nc_files = [file for file in os.listdir(fn) if 'nodes' in file ]
    for ind in list(range(len(nc_files))):
        nodes_nc = nc.Dataset(fn + nc_files[ind])
        node_df = pd.DataFrame(
            np.array([
                nodes_nc['nodes']['reach_id'][:],
                nodes_nc['nodes']['node_id'][:],
                nodes_nc['nodes']['wse'][:],
                nodes_nc['nodes']['width'][:],
                nodes_nc['nodes']['facc'][:],
                nodes_nc['nodes']['dist_out'][:],
                nodes_nc['nodes']['n_chan_mod'][:],
                nodes_nc['nodes']['sinuosity'][:],
                nodes_nc['nodes']['node_order'][:]]).T)
        node_df.rename(columns={0: 'reach_id', 1: 'node_id', 2: 'wse', 3: 'width', 4: 'facc', 5: 'dist_out', 6: 'n_chan_mod', 7: 'sinuosity', 8: 'node_order'}, inplace = True)
        try:
            nodes_all = pd.concat([nodes_all, node_df])
        except NameError:
            nodes_all = node_df.copy()
        del nodes_nc
    return nodes_all


# Load the Reach Timeseries and corresponding Metadata metadata for reach
meta = pd.read_csv("data/metadata/reach_metadata.csv", index_col="col")
reach_ts = pd.read_csv("data/SWOT_sample_CSVs/SWOTreaches.csv", index_col=0)
reach_ts = reach_ts.drop(columns="geometry")
sel_cols = ["reach_id", "time_str", "p_lon", "p_lat", "wse", "width", "slope", "slope2"]  #, "dschg_c"
reach_ts = reach_ts[sel_cols]
# Replace fill_values with nan
for col in sel_cols[3:]:
    fill_value_mask = reach_ts[col] == int(meta.loc[col]["fill_value"])
    reach_ts.loc[fill_value_mask, col] = np.nan
reach_ts["slope"] = reach_ts["slope"] * 1e6
reach_ts["slope2"] = reach_ts["slope2"] * 1e6

# Width column One high value, outside the valid range. Replace this one as well with nan
col = "width"
valid_max_mask = reach_ts[col] >= int(meta.loc[col]["valid_max"])
reach_ts.loc[valid_max_mask, col] = np.nan
# int(meta.loc[col]["valid_max"])
reach_ts["time_str"] = reach_ts.time_str.apply(lambda x: "" if x=="no_data" else x)  # replace with empty string
reach_ts["time_str"] = reach_ts.time_str.apply(lambda x: f"{x[:-3]}:{x[-3:]}")
reach_ts["time_str"] = reach_ts.time_str.apply(lambda x: "" if x==":" else x)  # replace with empty string again
reach_ts["time_str"] = pd.to_datetime(reach_ts.time_str, utc=True)
reach_ts = reach_ts[~reach_ts.time_str.isna()]  # select only with valid datetime
# Index by date for plotting
reach_ts.index = reach_ts.time_str
reach_ts = reach_ts.drop(columns="time_str")
reach_list = list(reach_ts.reach_id.unique())

# Read Node Timeseries data
node_ts = pd.read_csv("data/SWOT_sample_CSVs/SWOTnodes.csv", index_col=0)
# we need WSE and Width
node_cols = ["reach_id", "time_str", "node_id", "node_dist", "xtrk_dist", "p_dist_out", "wse", "width"]
node_ts = node_ts[node_cols]
# Replace fill_values with nan
for col in node_cols[-2:]:
    fill_value_mask = node_ts[col] <= int(meta.loc[col]["fill_value"])
    node_ts.loc[fill_value_mask, col] = np.nan
# Width column One high value, outside the valid range. Replace this one as well with nan
col = "width"
valid_max_mask = node_ts[col] >= int(meta.loc[col]["valid_max"])
node_ts.loc[valid_max_mask, col] = np.nan
node_ts["time_str"] = node_ts.time_str.apply(lambda x: "" if x=="no_data" else x)  # replace with empty string
node_ts["time_str"] = node_ts.time_str.apply(lambda x: f"{x[:-3]}:{x[-3:]}")
node_ts["time_str"] = node_ts.time_str.apply(lambda x: "" if x==":" else x)  # replace with empty string again
node_ts["time_str"] = pd.to_datetime(node_ts.time_str, utc=True)
node_ts = node_ts[~node_ts.time_str.isna()]  # select only with valid datetime
# Index by date for plotting
node_ts.index = node_ts.time_str
node_ts = node_ts.drop(columns="time_str")

# # Dummy csv file for plotting
# # df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/5d1ea79569ed194d432e56108a04d188/raw/a9f9e8076b837d541398e999dcbac2b2826a81f8/gdp-life-exp-2007.csv')
out_csv_folder = "data/velocity_csv_utc"
# # gages = os.listdir(out_csv_folder)
# # gages = [f.split(".csv")[0] for f in gages]
# # gages = [f[2:] for f in gages if len(f) == 10]
# # gages = list(set(gages))
# # csv_file = gages[0]
# # df = pd.read_csv(os.path.join(out_csv_folder, csv_file), index_col='utc_dt', parse_dates=True, infer_datetime_format=True)

# Read usgs gages
df = pd.read_csv("data/reach_gage_mapping.csv", dtype=str)
df.index = df.reach_id
df["basin2"] = df.reach_id.apply(lambda x: x[:2])
df["basin4"] = df.reach_id.apply(lambda x: x[:4])
gages = sorted(list(df[df.basin2=="73"]["STAID"]))
# Remove problematic gages with nodata
gages.remove("01020000")
del df 
# # Or get a subset of gages directly populated inside dropdown box
# gages = ['01131500', '01205500', '01315000', '01371500', '01502632', '01563200', '02104220', '02128000', '02130900', 
# '02160326', '02167582', '02172002', '02172300', '02187910', '02193340', '02197500', '02215500', '02223248', '02338000', 
# '02344700', '02350600', '02399200', '02401000', '02415000', '02474560', '02475000', '02477500', '02479000', '03568933']
# #################################################################################################


def plot_nodes(df, reach=None):
    # Function for plotting node level data.
    if reach is None:
        rch = 81247100041  # default reach
    else:
        rch = reach
    node_reaches = df.loc[df['reach_id'] == rch]

    # add base plots
    fig = make_subplots(rows=1, cols=2)
    fig.add_trace(
        go.Scatter(
            x=node_reaches['dist_out']/1000,
            y=node_reaches['wse'],
            mode='lines+markers'),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=node_reaches['dist_out']/1000,
            y=node_reaches['width'],
            mode='markers'),
        row=1, col=2
    )
    # Update xaxis properties
    fig.update_xaxes(
        title_text="Distance from Outlet (km)",
        row=1, col=1)
    fig.update_xaxes(
        title_text="Distance from Outlet (km)",
        row=1, col=2)
    # Update yaxis properties
    fig.update_yaxes(
        title_text="Water Surface Elevation (m)",
        row=1, col=1)
    fig.update_yaxes(
        title_text="Width (m)",
        row=1, col=2)
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
        height=480, #width=1400,
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


#################################################################################################
###############################  START OF APP CODE  #############################################
#################################################################################################
# Read in node data.
node_df = get_data("data/")
node_df_cp = node_df.copy()

# Trigger app.
app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN],suppress_callback_exceptions=True, title="SWOT Viz")

#################################################################################################
# ## Opens 'About SWORD' markdown document used in the modal overlay.
with open("about.md", "r") as f:
    about_md = f.read()

with open("download.md", "r") as d:
    download_md = d.read()

# Modal pop-up triggered by the "About" button in the header .
modal_overlay = dbc.Modal(
    [
        dbc.ModalBody(
            html.Div([
                dcc.Markdown(about_md)],
                id="about-md")),
        dbc.ModalFooter(
            dbc.Button(
                "Close",
                id="howto-close",
                className="howto-bn")),
    ],
    id="modal",
    size="lg",
)

# Modal pop-up triggered by the "Download" button in the header .
download_overlay = dbc.Modal(
    [
        dbc.ModalBody(
            html.Div([
                dcc.Markdown(download_md)],
                id="download-md")),
        dbc.ModalFooter(
            dbc.Button(
                "Close",
                id="download-close",
                className="howto-bn")),
    ],
    id="download_modal",
    size="lg",
)

# About button in header.
button_about = dbc.Button(
    "About",
    id="howto-open",
    outline=False,
    color="#2b3b90",  # swot dark blue
    style={
        "textTransform": "none",
        "margin-right": "5px",
        "color": "white",
        "background-color": "#2b3b90",
    },
)

# Download button in header.
button_download = dbc.Button(
    "Download",
    outline=False,
    color="#2b3b90",  # swot dark blue
    # href="https://zenodo.org/record/5643392#.Yv-oeezML0s",
    id="download-open",
    style={
        "text-transform": "none",
        "margin-left": "5px",
        "color": "white",
        "background-color": "#2b3b90",
    },
)

# Button to plot node-level attributes.
button_plot = dbc.Button(
    "Plot Reach",
    id="plot_reach",
    outline=False,
    color="primary",
    style={
        "textTransform": "none",
        "margin-left": "5px",
        "color": "white",
        # "background-color": "green",
        "textAlign": "center"
    },
)

#################################################################################################

# Dashboard header
header = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Img(
                            id="logo1",
                            src=app.get_asset_url("swot_mainlogo_dark.png"),
                            height="60px",
                        ),
                        md="auto",
                    ),
                    dbc.Col(
                        html.Img(
                            id="logo2",
                            src=app.get_asset_url("SWORD_Logo.png"),
                            height="60px",
                        ),
                        md="auto",
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H2(
                                        "SWOT Viz",
                                        style={
                                            "textAlign":"left",
                                            "margin-top":"15px"}),
                                    html.P(html.H4(
                                        "Interactive Dashboard - based on SWOT explorer by Elizabeth Altenau",
                                        style={"textAlign":"left"})),
                                ],
                                id="app-title",
                            )
                        ],
                        md=True,
                        align="center",
                    ),
                ],
                align="center",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.NavbarToggler(id="navbar-toggler"),
                            dbc.Collapse(
                                dbc.Nav(
                                    [
                                        dbc.NavItem(button_about,),
                                        dbc.NavItem(button_download,),
                                    ],
                                    navbar=True,
                                ),
                                id="navbar-collapse",
                                navbar=True,
                            ),
                            modal_overlay,
                            download_overlay,
                        ],
                        md=2,
                    ),
                ],
                align="center",
            ),
        ],
        fluid=True,
        className='bg-primary text-white p-2',
    ),
    # sticky="top", #uncomment to stick to top.
)

#################################################################################################
# Continent tabs formatting. Continent tab layout changes based on the "render_content" callback.

tabs_styles = {
    'height': '51px'
}
tab_style = {
    'borderTop': '5px',  # 2fa4e7 cerulean
    'borderBottom': '5px',
    'padding': '10px',
    'fontWeight': 'bold',
    'color': 'white',
    'background': '#2b3b90'
}

tab_selected_style = {
    'borderTop': '5px solid #2fa4e7',  # 2fa4e7 cerulean
    'borderBottom': '5px solid #2fa4e7',
    'borderLeft': '5px solid #2fa4e7',
    'borderRight': '5px solid #2fa4e7',
    'padding': '10px',
    'color': 'white',
    'background': '#2b3b90'
}
# Africa maps.
dropdown_list_af = [
    {"label": "Choose a Basin to Visualize Reaches", "value": "data/af_basin_map.html"},
    {"label": "Basin 11", "value": "data/hb11_sword_map.html"},
    {"label": "Basin 12", "value": "data/hb12_sword_map.html"},
    {"label": "Basin 13", "value": "data/hb13_sword_map.html"},
    {"label": "Basin 14", "value": "data/hb14_sword_map.html"},
    {"label": "Basin 15", "value": "data/hb15_sword_map.html"},
    {"label": "Basin 16", "value": "data/hb16_sword_map.html"},
    {"label": "Basin 17", "value": "data/hb17_sword_map.html"},
    {"label": "Basin 18", "value": "data/hb18_sword_map.html"},
    ]
# Asia maps
dropdown_list_as = [
    {"label": "Choose a Basin to Visualize Reaches", "value": "data/as_basin_map.html"},
    {"label": "Basin 31", "value": "data/hb31_sword_map.html"},
    {"label": "Basin 32", "value": "data/hb32_sword_map.html"},
    {"label": "Basin 33", "value": "data/hb33_sword_map.html"},
    {"label": "Basin 34", "value": "data/hb34_sword_map.html"},
    {"label": "Basin 35", "value": "data/hb35_sword_map.html"},
    {"label": "Basin 36", "value": "data/hb36_sword_map.html"},
    {"label": "Basin 41", "value": "data/hb41_sword_map.html"},
    {"label": "Basin 42", "value": "data/hb42_sword_map.html"},
    {"label": "Basin 43", "value": "data/hb43_sword_map.html"},
    {"label": "Basin 44", "value": "data/hb44_sword_map.html"},
    {"label": "Basin 45", "value": "data/hb45_sword_map.html"},
    {"label": "Basin 46", "value": "data/hb46_sword_map.html"},
    {"label": "Basin 47", "value": "data/hb47_sword_map.html"},
    {"label": "Basin 48", "value": "data/hb48_sword_map.html"},
    {"label": "Basin 49", "value": "data/hb49_sword_map.html"},
    ]
# Europe/Middle East maps
dropdown_list_eu = [
    {"label": "Choose a Basin to Visualize Reaches", "value": "data/eu_basin_map.html"},
    {"label": "Basin 21", "value": "data/hb21_sword_map.html"},
    {"label": "Basin 22", "value": "data/hb22_sword_map.html"},
    {"label": "Basin 23", "value": "data/hb23_sword_map.html"},
    {"label": "Basin 24", "value": "data/hb24_sword_map.html"},
    {"label": "Basin 25", "value": "data/hb25_sword_map.html"},
    {"label": "Basin 26", "value": "data/hb26_sword_map.html"},
    {"label": "Basin 27", "value": "data/hb27_sword_map.html"},
    {"label": "Basin 28", "value": "data/hb28_sword_map.html"},
    {"label": "Basin 29", "value": "data/hb29_sword_map.html"},
    ]
# Oceania maps
dropdown_list_oc = [
    {"label": "Choose a Basin to Visualize Reaches", "value": "data/oc_basin_map.html"},
    {"label": "Basin 51", "value": "data/hb51_sword_map.html"},
    {"label": "Basin 52", "value": "data/hb52_sword_map.html"},
    {"label": "Basin 53", "value": "data/hb53_sword_map.html"},
    {"label": "Basin 55", "value": "data/hb55_sword_map.html"},
    {"label": "Basin 56", "value": "data/hb56_sword_map.html"},
    {"label": "Basin 57", "value": "data/hb57_sword_map.html"},
    ]
# South America maps
dropdown_list_sa = [
    {"label": "Choose a Basin to Visualize Reaches", "value": "data/sa_basin_map.html"},
    {"label": "Basin 61", "value": "data/hb61_sword_map.html"},
    {"label": "Basin 62", "value": "data/hb62_sword_map.html"},
    {"label": "Basin 63", "value": "data/hb63_sword_map.html"},
    {"label": "Basin 64", "value": "data/hb64_sword_map.html"},
    {"label": "Basin 65", "value": "data/hb65_sword_map.html"},
    {"label": "Basin 66", "value": "data/hb66_sword_map.html"},
    {"label": "Basin 67", "value": "data/hb67_sword_map.html"},
    ]
# North America maps
dropdown_list_na = [
    {"label": "Choose a Basin to Visualize Reaches", "value": "data/na_basin_map.html"},
    {"label": "Basin 71", "value": "data/hb71_sword_map.html"},
    {"label": "Basin 72", "value": "data/hb72_sword_map.html"},
    {"label": "Basin 73", "value": "data/hb73_sword_map.html"},
    {"label": "Basin 74", "value": "data/hb74_sword_map.html"},
    {"label": "Basin 75", "value": "data/hb75_sword_map.html"},
    {"label": "Basin 76", "value": "data/hb76_sword_map.html"},
    {"label": "Basin 77", "value": "data/hb77_sword_map.html"},
    {"label": "Basin 78", "value": "data/hb78_sword_map.html"},
    {"label": "Basin 81", "value": "data/hb81_sword_map.html"},
    {"label": "Basin 82", "value": "data/hb82_sword_map.html"},
    {"label": "Basin 83", "value": "data/hb83_sword_map.html"},
    {"label": "Basin 84", "value": "data/hb84_sword_map.html"},
    {"label": "Basin 85", "value": "data/hb85_sword_map.html"},
    {"label": "Basin 86", "value": "data/hb86_sword_map.html"},
    {"label": "Basin 91", "value": "data/hb91_sword_map.html"},
    ]

#################################################################################################
# ## PRIMARY APP LAYOUT.

app.layout = html.Div([
    header,
    # insert tabs
    html.Div([
        dcc.Tabs(
            id="all-tabs-inline",
            value='tab-4',
            children=[
                dcc.Tab(
                    label='Africa',
                    value='tab-1',
                    style=tab_style,
                    selected_style=tab_selected_style),
                dcc.Tab(
                    label='Asia',
                    value='tab-2',
                    style=tab_style,
                    selected_style=tab_selected_style),
                dcc.Tab(
                    label='Europe & Middle East',
                    value='tab-3',
                    style=tab_style,
                    selected_style=tab_selected_style),
                dcc.Tab(
                    label='North America',
                    value='tab-4',
                    style=tab_style,
                    selected_style=tab_selected_style),
                dcc.Tab(
                    label='Oceania',
                    value='tab-5',
                    style=tab_style,
                    selected_style=tab_selected_style),
                dcc.Tab(
                    label='South America',
                    value='tab-6',
                    style=tab_style,
                    selected_style=tab_selected_style),
            ], style=tabs_styles)]),
    html.Br(),
    html.Div(id='tabs-content-example-graph'),  # callback for tab content.
    html.Div(
        [
            html.H5('Type a Reach ID and click ENTER or "Plot Reach" to see node level attributes:', style={'marginTop' : '5px', 'marginBottom': '5px', 'size': '25'}),
            dcc.Input(
                id='ReachID',
                type='number',
                value=81247100041,
                placeholder="Reach ID",
                debounce=True,
                min=int(np.min(node_df['reach_id'])),
                max=int(np.max(node_df['reach_id'])),
                step=1,
                required=False,
                size='100'),
            button_plot,
            # button_report,
            # report_overlay,
            dcc.Graph(figure=plot_nodes(node_df_cp), id='ReachGraph')
        ]
    ),  # end subdiv3
    # BNY
    html.Div([
        html.H5("Reach Data"),
        html.Div([
            html.Label('Listing of Reaches'),
            dcc.Dropdown(reach_list, placeholder="Select a reach to plot", id="reach_list_dropdown", searchable=True, clearable=True, maxHeight=200),
        ], style={"width": "25%", 'align-items': 'left', 'justify-content': 'left'}),
        dcc.Graph(id="Reach_TS"),
        # dcc.Graph(id="Node_TS")  # WSE and Width long profile of NODES for each reach
    ]),

    html.Div(
        [
            html.H5("USGS Field Measure Data"),
            html.Div(
                [
                    html.Label('Select USGS Gage to pull field measure data'),
                    dcc.Dropdown(gages, gages[0], id="gage_list", searchable=True, clearable=False, maxHeight=200,),  # optionHeight=100, # style={'color': 'Gold', 'font-size': 15}
                    html.Br()
                ],
                style={"width": "25%", 'align-items': 'left', 'justify-content': 'left'}  # , 'color': 'Gold', 'font-size': 15
            ),

            dcc.Graph(id="Field_Measure_ts"),  # , figure=plot_field_measure(df)
            dcc.Graph(id="Field_Measure_Scatter")  # , figure=plot_scatter(df)        
        ]),
    html.Div(children=[
        html.Div(
            'Copyright (c) 2022 University of North Carolina at Chapel Hill',
            style={
                'textAlign': 'left',
                'font-size': '0.7em',
                'marginLeft': '5px',
            },
        ),
        html.Div(
            'Dashboard written in Python using the Dash web framework.',
            style={
                'textAlign': 'left',
                'font-size': '0.7em',
                'marginLeft': '5px',
            }
        ),
        html.Div(
            'Base map layer is the "cartodbpositron" map style provided by CARTO.',
            style={
                'textAlign':'left',
                'font-size': '0.7em',
                'marginLeft':'5px',
            }
        )
    ], style={'textAlign': 'left', 'color': 'slateGrey'})],
    style={'marginTop': '5px', 'marginRight': '50px', 'marginBottom': '5px', 'marginLeft': '50px', "textAlign": "center"}
)  # end of app layout

#################################################################################################
######################################  CALLBACKS  ##############################################
#################################################################################################

# Callback that triggers the main map dispaly to change based on which tab is clicked.
# output is the tab layout.
@app.callback(Output('tabs-content-example-graph', 'children'),
              Input('all-tabs-inline', 'value'),)
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.H6(
                dbc.Row(
                    [
                        dbc.Col(html.H3(
                            'SWOTViz v0.0'),
                            width=8,
                            className='mt-2',
                            style={"textAlign": "left"}),
                        dbc.Col(dcc.Dropdown(
                            id='DropBox',
                            options=dropdown_list_af,
                            value=dropdown_list_af[0]['value'],
                            style={"textAlign": "left"}),
                            style={"textAlign": "right"})
                    ]
                ),
            ),
            html.Div([
                html.Div(
                    '**PLEASE NOTE: Reach geometries have been simplified for map efficiency, however, some large basins (i.e. Amazon, Ganges-Barmaputra) may still take a few moments to load.**',
                    style={'marginTop': '5px', 'marginBottom': '5px', 'size': '25', 'color': '#C42828'})]
            ),
            html.Iframe(id='BasinMap', srcDoc=open('data/af_basin_map.html', 'r').read(), style={"height": "500px", "width": "100%"})
        ])  # end subdiv2
    elif tab == 'tab-2':
        return html.Div([
            html.H6(
                dbc.Row(
                    [
                        dbc.Col(html.H3(
                            'SWOTViz v0.0'),
                            width=8,
                            className='mt-2',
                            style={"textAlign": "left"}),
                        dbc.Col(dcc.Dropdown(
                            id='DropBox',
                            options=dropdown_list_as,
                            value=dropdown_list_as[0]['value'],
                            style={"textAlign": "left"}),
                        style={"textAlign": "right"})
                    ]
                ),
            ),
            html.Div([
                html.Div(
                    '**PLEASE NOTE: Reach geometries have been simplified \
                        for map efficiency, however, some large basins \
                            (i.e. Amazon, Ganges-Barmaputra) may still take \
                                a few moments to load.**',
                    style={
                        'marginTop': '5px',
                        'marginBottom': '5px',
                        'size':'25',
                        'color':'#C42828'},
                    ),
            ]),
            html.Iframe(
                id='BasinMap',
                srcDoc=open('data/as_basin_map.html', 'r').read(),
                style={"height": "500px", "width": "100%"}
                )
        ]) #end subdiv2
    elif tab == 'tab-3':
        return html.Div([
            html.H6(
                dbc.Row(
                    [
                        dbc.Col(html.H3(
                            'SWOTViz v0.0'),
                            width=8,
                            className='mt-2',
                            style={"textAlign":"left"}),
                        dbc.Col(dcc.Dropdown(
                            id='DropBox',
                            options=dropdown_list_eu,
                            value=dropdown_list_eu[0]['value'],
                            style={"textAlign": "left"}),
                    style={"textAlign": "right"})
                    ]
                ),
            ),
            html.Div([
                html.Div(
                    '**PLEASE NOTE: Reach geometries have been simplified \
                        for map efficiency, however, some large basins \
                            (i.e. Amazon, Ganges-Barmaputra) may still take \
                                a few moments to load.**',
                    style={
                        'marginTop' : '5px',
                        'marginBottom' : '5px',
                        'size':'25',
                        'color':'#C42828'},
                    ),
            ]),
            html.Iframe(
                id='BasinMap',
                srcDoc=open('data/eu_basin_map.html', 'r').read(),
                style={"height": "500px", "width": "100%"}
                )
        ]) #end subdiv2
    elif tab == 'tab-4':
        return html.Div([
            html.H6(
                dbc.Row(
                    [
                        dbc.Col(html.H3(
                            'SWOTViz v0.0'),
                            width=8,
                            className='mt-2',
                            style={"textAlign":"left"}),
                        dbc.Col(dcc.Dropdown(
                            id='DropBox',
                            options=dropdown_list_na,
                            value=dropdown_list_na[0]['value'],
                            style={"textAlign":"left"}),
                        style={"textAlign":"right"})
                    ]
                ),
            ),
            html.Div([
                html.Div(
                    '**PLEASE NOTE: Reach geometries have been simplified \
                        for map efficiency, however, some large basins \
                            (i.e. Amazon, Ganges-Barmaputra) may still take \
                                a few moments to load.**',
                    style={
                        'marginTop' : '5px',
                        'marginBottom' : '5px',
                        'size':'25',
                        'color':'#C42828'},
                    ),
            ]),
            html.Iframe(
                id='BasinMap',
                srcDoc=open('data/na_basin_map.html', 'r').read(),
                style={"height": "500px", "width": "100%"}
                )
        ]) #end subdiv2
    elif tab == 'tab-5':
        return html.Div([
            html.H6(
                dbc.Row(
                    [
                        dbc.Col(html.H3(
                            'SWOTViz v0.0'),
                            width=8,
                            className='mt-2',
                            style={"textAlign":"left"}),
                        dbc.Col(dcc.Dropdown(
                            id='DropBox',
                            options=dropdown_list_oc,
                            value=dropdown_list_oc[0]['value'],
                            style={"textAlign":"left"}),
                        style={"textAlign":"right"})
                    ]
                ),
            ),
            html.Div([
                html.Div(
                    '**PLEASE NOTE: Reach geometries have been simplified \
                        for map efficiency, however, some large basins \
                            (i.e. Amazon, Ganges-Barmaputra) may still take \
                                a few moments to load.**',
                    style={
                        'marginTop' : '5px',
                        'marginBottom' : '5px',
                        'size':'25',
                        'color':'#C42828'},
                    ),
            ]),
            html.Iframe(
                id='BasinMap',
                srcDoc=open('data/oc_basin_map.html', 'r').read(),
                style={"height": "500px", "width": "100%"}
                )
        ]) #end subdiv2
    elif tab == 'tab-6':
        return html.Div([
            html.H6(
                dbc.Row(
                    [
                        dbc.Col(html.H3(
                            'SWOTViz v0.0'),
                            width=8,
                            className='mt-2',
                            style={"textAlign":"left"}),
                        dbc.Col(dcc.Dropdown(
                            id='DropBox',
                            options=dropdown_list_sa,
                            value=dropdown_list_sa[0]['value'],
                            style={"textAlign":"left"}),
                        style={"textAlign":"right"})
                    ]
                ),
            ),
            html.Div([
                html.Div(
                    '**PLEASE NOTE: Reach geometries have been simplified \
                        for map efficiency, however, some large basins \
                            (i.e. Amazon, Ganges-Barmaputra) may still take \
                                a few moments to load.**',
                    style={
                        'marginTop' : '5px',
                        'marginBottom' : '5px',
                        'size':'25',
                        'color':'#C42828'},
                    ),
            ]),
            html.Iframe(
                id='BasinMap',
                srcDoc=open('data/sa_basin_map.html', 'r').read(),
                style={"height": "500px", "width": "100%"}
                )
        ]) #end subdiv2


# Callback that triggers the regional maps to change based on the "Dropbox" option.
@app.callback(
    Output("BasinMap", "srcDoc"),
    Input("DropBox", "value"))
def update_output_div(input_value):
    return open(input_value, 'r').read()


# Callback that plots the node level attributes when a Reach ID is put into the input box.
@app.callback(
    [Output('ReachGraph', 'figure'),
    Output('plot_reach', 'n_clicks'),],
    [Input('ReachID', 'value'),
    Input('plot_reach', 'n_clicks'),])
def update_graph(term, n_clicks):
    if term or n_clicks:
        fig = plot_nodes(node_df_cp, term)
        n_clicks = None
        return fig, n_clicks

@app.callback(
    Output("Reach_TS", "figure"),
    # Output("Node_TS", "figure"),
    Input("reach_list_dropdown", "value")
)
def plot_reach(reach_id):
    reach_ts_sel = reach_ts[reach_ts.reach_id == reach_id]
    node_ts_sel = node_ts[node_ts.reach_id == reach_id]
    # Get unique list of dates (without time)

    # Select one data to make plots
    # Make plot directly here rather than calling another function
    fig = make_subplots(rows=2, cols=2)
    fig.add_trace(go.Scatter(x=reach_ts_sel.index, y=reach_ts_sel["wse"], mode="lines+markers", name="wse"), row=1, col=1)
    fig.add_trace(go.Scatter(x=reach_ts_sel.index, y=reach_ts_sel["width"], mode="lines+markers", name="width"), row=1, col=2)
    fig.add_trace(go.Scatter(x=reach_ts_sel.index, y=reach_ts_sel["slope"], mode="lines+markers", name="slope"), row=2, col=1)
    fig.add_trace(go.Scatter(x=reach_ts_sel.index, y=reach_ts_sel["slope2"], mode="lines+markers", name="slope2"), row=2, col=2)
    # Update xaxis properties
    # fig.update_xaxes(title_text="DateTime (UTC)", row=1, col=1)
    fig.update_yaxes(title_text="WSE [m]", row=1, col=1)
    fig.update_yaxes(title_text="Width [m]", row=1, col=2)
    fig.update_yaxes(title_text="Slope [mm/km]", row=2, col=1)
    fig.update_yaxes(title_text="Slope [mm/km]", row=2, col=2)
    # overall figure properties
    fig.update_xaxes(title_text="DateTime (UTC)")
    fig.update_layout(height=600, title_text=f"Reach: {reach_id}", title_x=0.5, showlegend=True, plot_bgcolor='#dce0e2')  # width=1400,  

    # # Plot Node data
    # node_fig = make_subplots(1, 2)
    # node_fig.add_trace(go.Scatter(x=node_ts_sel.index, y=reach_ts_sel["wse"], mode="lines+markers", name="wse"), row=1, col=1)
    # node_fig.add_trace(go.Scatter(x=node_ts_sel.index, y=reach_ts_sel["width"], mode="lines+markers", name="width"), row=1, col=2)
    # node_fig.update_yaxes(title_text="WSE [m]", row=1, col=1)
    # node_fig.update_yaxes(title_text="Width [m]", row=1, col=2)
    # node_fig.update_xaxes(title_text="DateTime (UTC)")
    # node_fig.update_layout(height=400, title_text="Long profile of nodes", title_x=0.5, showlegend=True, plot_bgcolor='#dce0e2')  # width=1400,  
    return fig#, node_fig


@app.callback(
    Output("Field_Measure_ts", "figure"),
    Output("Field_Measure_Scatter", "figure"),
    Input("gage_list", "value"))
def update_ts_graph(gage):
    logging.info(gage)
    if os.path.exists(os.path.join(out_csv_folder, f"{gage}.csv")):
        df = pd.read_csv(os.path.join(out_csv_folder, f"{gage}.csv"), index_col='measurement_dt', parse_dates=True, infer_datetime_format=True)
    else:
        # Download file
        df = get_usgs_data.read_usgs_field_data(gage)
        df.to_csv(os.path.join(out_csv_folder, f'{gage}.csv'), index=True, header=True)  # index_label='measurement_dt or utc_dt'
    if len(df) > 0:
        fig_ts = plot_field_measure(df)
        fig_scatter = plot_scatter(df)
        return fig_ts, fig_scatter


# Callback for "About" modal popup
@app.callback(
    Output("modal", "is_open"),
    [Input("howto-open", "n_clicks"), Input("howto-close", "n_clicks")],
    [State("modal", "is_open")])
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Callback for "Download" modal popup
@app.callback(
    Output("download_modal", "is_open"),
    [Input("download-open", "n_clicks"), Input("download-close", "n_clicks")],
    [State("download_modal", "is_open")])
def toggle_modal(n5, n6, is_open):
    if n5 or n6:
        return not is_open
    return is_open


if __name__ == '__main__':
    # app.run_server()
    app.run_server(debug=True)  # use this line instead of the line before to run the app in debug mode.
