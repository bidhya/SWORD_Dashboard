import base64
import datetime
import io
import os
import netCDF4 as nc
import numpy as np
import pandas as pd
from csv import writer, reader
import time
import dash
try:
    from dash import dcc
except:
    import dash_core_components as dcc
    # seems deprecated in latest version
from dash import html, dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
load_figure_template("cerulean")

#################################################################################################
######################################  FUNCTIONS  ##############################################
#################################################################################################

### Function for formatting input node data.
def get_data(fn):
    nc_files = [file for file in os.listdir(fn) if 'nodes' in file ]
    for ind in list(range(len(nc_files))):
        nodes_nc = nc.Dataset(fn+nc_files[ind])
        node_df = pd.DataFrame(
            np.array(
                [nodes_nc['nodes']['reach_id'][:],
                nodes_nc['nodes']['node_id'][:],
                nodes_nc['nodes']['wse'][:],
                nodes_nc['nodes']['width'][:],
                nodes_nc['nodes']['facc'][:],
                nodes_nc['nodes']['dist_out'][:],
                nodes_nc['nodes']['n_chan_mod'][:],
                nodes_nc['nodes']['sinuosity'][:],
                nodes_nc['nodes']['node_order'][:]]).T)
        node_df.rename(columns = {0:'reach_id', 1:'node_id',
            2:'wse', 3:'width', 4:'facc', 5:'dist_out',
            6:'n_chan_mod',7:'sinuosity',8:'node_order'}, inplace = True)
        try:
            nodes_all = pd.concat([nodes_all, node_df])
        except NameError:
            nodes_all = node_df.copy()
        del(nodes_nc)

    return nodes_all

#################################################################################################
### Function for plotting node level data.

def plot_nodes(df, reach=None):
    if reach is None:
        rch = 81247100041 #default reach
    else:
        rch = reach

    node_reaches = df.loc[df['reach_id'] == rch]

    #add base plots
    fig = make_subplots(rows=3, cols=2)
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
            mode='lines+markers'),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=node_reaches['dist_out']/1000,
            y=node_reaches['node_order'],
            mode='lines+markers'),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=node_reaches['dist_out']/1000,
            y=node_reaches['facc'],
            mode='lines+markers'),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=node_reaches['dist_out']/1000,
            y=node_reaches['n_chan_mod'],
            mode='lines+markers'),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=node_reaches['dist_out']/1000,
            y=node_reaches['sinuosity'],
            mode='lines+markers'),
        row=3, col=2
    )
    # Update xaxis properties
    fig.update_xaxes(
        title_text="Distance from Outlet (km)",
        row=1, col=1)
    fig.update_xaxes(
        title_text="Distance from Outlet (km)",
        row=1, col=2)
    fig.update_xaxes(
        title_text="Distance from Outlet (km)",
        row=2, col=1)
    fig.update_xaxes(
        title_text="Distance from Outlet (km)",
        row=2, col=2)
    fig.update_xaxes(
        title_text="Distance from Outlet (km)",
        row=3, col=1)
    fig.update_xaxes(
        title_text="Distance from Outlet (km)",
        row=3, col=2)
    # Update yaxis properties
    fig.update_yaxes(
        title_text="Water Surface Elevation (m)",
        row=1, col=1)
    fig.update_yaxes(
        title_text="Width (m)",
        row=1, col=2)
    fig.update_yaxes(
        title_text="Node Order",
        row=2, col=1)
    fig.update_yaxes(
        title_text="Flow Accumulation (sq.km)",
        row=2, col=2)
    fig.update_yaxes(
        title_text="Number of Channels",
        row=3, col=1)
    fig.update_yaxes(
        title_text="Sinuosity",
        row=3, col=2)
    #overall figure properties
    fig.update_layout(
        height=1000, #width=1400,
        title_text="Reach "+str(rch)+": Node Level Attributes",
        title_x=0.5,
        showlegend=False,
        plot_bgcolor='#dce0e2' #'whitesmoke'
    )
    return fig

#################################################################################################
### Function to save bulk files when reporting issues.

def save_bulk_data(df):
    colnames = list(df)
    df = np.array(df)
    current = np.array(pd.read_csv('user_reports.csv'))
    rm_ind = []
    for row in list(range(len(df))):
        if df[row,1] == 4:
            if ((current[:,0] == df[row,0]) & (current[:,2] == df[row,2])).any():
                rm_ind.append(row)
        else:
            if ((current[:,0] == df[row,0]) & (current[:,1] == df[row,1])).any():
                rm_ind.append(row)

    df_clean = np.delete(df, rm_ind, axis = 0)
    if len(df_clean) == 0:
        statement = html.Div(['All Reaches Already Reported'], style={'color':'goldenrod'})
    else:
        date_stamp = time.strftime("%d-%b-%Y %H:%M:%S", time.gmtime())
        for ind in list(range(len(df_clean))):
            if df_clean[ind,1] > 4:
                df_clean = pd.DataFrame(df_clean)
                df_clean.columns = colnames
                df_clean.to_csv('reports/'+time.strftime("%d-%b-%Y", time.gmtime())+'_'+time.strftime("%H:%M:%S", time.gmtime())+'_report.csv')
                statement = html.Div(['File Submitted Successfully'], style={'color':'green'})
            else:
                if df_clean[ind,1] == 1:
                    List = list([df_clean[ind,0], 1, df_clean[ind,2], 0, date_stamp, 0])
                elif df_clean[ind,1] == 2:
                    List = list([df_clean[ind,0], 2, 1, 0, date_stamp, 0])
                elif df_clean[ind,1] == 4:
                    List = list([df_clean[ind,0], 4, df_clean[ind,2], df_clean[ind,3], date_stamp, 0])
                else:
                    List = list([df_clean[ind,0], 3, df_clean[ind,2], df_clean[ind,3], date_stamp, 0])
                with open('user_reports.csv', 'a') as w_object:
                    writer_object = writer(w_object)
                    writer_object.writerow(List)
                    w_object.close()
                statement = html.Div(['File Submitted Successfully: '+str(len(df_clean))+ ' - New Reaches Reported; '+str(len(rm_ind))+' - Already Reported'], style={'color':'green'})
    return statement

#################################################################################################
### Function to parse the contents of an uploaded file.

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        statement = save_bulk_data(df)
        # print(statement)
        return html.Div([
            html.Div(filename),
            html.Div(datetime.datetime.fromtimestamp(date)),
            statement
        ])
    except Exception as e:
        print(e)
        return html.Div([
            html.Div(
                'There was an error processing this file.',
                style={'color':'#C42828'}),
            html.Div(
                'Please make sure the file is in CSV format,',
                style={'color':'#C42828'}),
            html.P(
                'and file headers/columns are in the correct format.',
                style={'color':'#C42828'}),
            ])

#################################################################################################
###############################  START OF APP CODE  #############################################
#################################################################################################

# Read in node data.
node_df = get_data("data/")
node_df_cp = node_df.copy()

# Trigger app.
app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN],suppress_callback_exceptions=True, title="SWOT River Database (SWORD)")

#################################################################################################
### Opens 'About SWORD' markdown document used in the modal overlay.
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
    color="#2b3b90", #swot dark blue
    style={
        "textTransform": "none",
        "margin-right": "5px",
        "color":"white",
        "background-color":"#2b3b90",
    },
)

# Download button in header.
button_download = dbc.Button(
    "Download",
    outline=False,
    color="#2b3b90", #swot dark blue
    # href="https://zenodo.org/record/5643392#.Yv-oeezML0s",
    id="download-open",
    style={
        "text-transform": "none",
        "margin-left": "5px",
        "color":"white",
        "background-color":"#2b3b90",
    },
)

#################################################################################################
### Report Modal Components.

# Report index table.
index_tbl = pd.DataFrame(data = {
    'Report Type': ['Reach Type Change', 'Node Order Change', 'Reach Neighbor Change', 'Attribute Value Change'],
    'Report Index': [1, 2, 3, 4]
})

# Attribute index table.
attr_index_tbl = pd.DataFrame(data = {
    'Attribute': [
        'Flow Accumulation (sq. km)',
        'Water Surface Elevation (m)',
        'Width (m)',
        'Slope (m/km)',
        'River Name'],
    'Attribute Index': [1, 2, 3, 4, 5]
})

# Reach type change table.
type_csv = pd.DataFrame(data = {
    'reach_id': [71212000343, 71452000461, 81322000305, 'etc.'],
    'report_index': [1, 1, 1, 'etc.'],
    'new_type': [1, 3, 3, 'etc.']
})

# Node order change table.
node_csv = pd.DataFrame(data = {
    'reach_id': [71212000343, 71452000461, 81322000305, 'etc.'],
    'report_index': [2, 2, 2, 'etc.']
})

# Reach neighbor change table.
ngh_csv = pd.DataFrame(data = {
    'reach_id': [71212000343, 71452000461, 81322000305, 'etc.'],
    'report_index': [3, 3, 3, 'etc.'],
    'upstream_neighbors': ['71212000351', '71452000101', '81322000405 81322000315', 'etc.'],
    'downstream_neighbors': ['71212000333 71213000321', '71452000451', '81322000295', 'etc.']
})

# Attribute value change table.
attr_csv = pd.DataFrame(data = {
    'reach_id': [71212000343, 71452000461, 81322000305, 'etc.'],
    'report_index': [4, 4, 4, 'etc.'],
    'attribute_index': [1, 3, 5, 'etc.'],
    'attribute_value': [25000, 150, 'Yukon River', 'etc.']
})

# Text for the modal pop-up triggered by the "Report" button above the node plots.
markdown_body = html.Div([
    dcc.Markdown('''
    ### Reporting Instructions

    The SWORD database is an evolving product that is intended to undergo
    continued improvements and updates before and after the launch of SWOT.
    Currently, there are limited manual adjustments made to SWORD which result
    in the database containing some artifacts primarily due to errors that occur
    during the merging process between the various databases. We have done our best
    to manually and automatically find major errors in SWORD, however, input from
    the SWOT Science Team and other hydrologists is helpful to identify persistent
    artifacts. **This page allows users to report common SWORD issues.** More
    details on how to report more complex issues (such as reach definition changes or
    centerline adjustments) can be found in the [SWORD Update Request Documentation]
    (https://drive.google.com/file/d/15OSrP0HY5HnwpEWh67ObYEWqwsAPSIEv/view?usp=sharing).

    ### Update Timeline

    SWORD updates are classified into two categories: 1) trivial and 2) non-trivial.
    Trivial updates are easier to implement and impact less of the database such as
    the report issues on this dashboard: node order changes, river name changes, reach
    neighbor changes, and river name changes. Non-trivial updates are more difficult to
    implement and may take manual intervention. Examples of non-trivial updates are
    river centerline adjustments and reach definition changes.  **Trivial updates can
    be expected to be implemented approximately every quarter, while non-trivial updates
    are not guaranteed to be implemented before SWOT reprocessings (~annually).**

    ### Dashboard Reporting

    Users can report a single reach or a batch CSV file for the report categories below. If
    a customized or non-trival update is required please refer to the [SWORD Update Request Documentation]
    (https://drive.google.com/file/d/15OSrP0HY5HnwpEWh67ObYEWqwsAPSIEv/view?usp=sharing). If you
    encounter any problems while reporting update requests, or have any questions, please feel free to email
    **sword_riverdb@gmail.com**.

    Each request type has a unique "report index" which is required when submitting batch files.
    Report indexes are as follows:
    '''
    ),
    dash_table.DataTable(
        index_tbl.to_dict('records'),
        [{"name": i, "id": i} for i in index_tbl.columns],
        style_cell={'textAlign': 'left'},
    ),
    html.Br(),
    dcc.Markdown('''
    **Reach Type Change:**

    Reach “type” changes do not affect reach boundaries, only the number of the type identifier
    in the reach and node ids (the last digit in the id structure). For example, a user may
    notice that a current reach identified as a lake (type = 3) is located below a reservoir
    and dam and should be reassigned as a river reach (type = 1). Type categories in
    SWORD are: 1 - river, 3 - lake/reservior, 4 - dam/waterfall, 5 - unreliable topology (such as deltas).
    To report a reach type change, users should submit a **CSV file** containing three columns:
    the current "reach id", the "report index", and the "new type" of the reach. **Please note
    that column order matters!**
    '''
    ),
    dash_table.DataTable(
        type_csv.to_dict('records'),
        [{"name": i, "id": i} for i in type_csv.columns],
        style_cell={'textAlign': 'left'},
    ),
    html.Br(),
    dcc.Markdown('''
    **Node Order Change:**

    Node directions can be reversed in areas where flow accumulation and elevation resolution
    are poor (i.e., there is no change), therefore it is difficult to automatically identify
    correct topology. Incorrect node directions are often identified when the node order is the
    in opposite direction of elevation change or, in areas where elevation and flow accumulation
    are spatially static, the upstream or downstream neighbors are incorrect. To report a node order change,
    users should submit a **CSV file** containing two columns: the current "reach id" and the "report index".
    **Please note that column order matters!**
    '''
    ),
    dash_table.DataTable(
        node_csv.to_dict('records'),
        [{"name": i, "id": i} for i in node_csv.columns],
        style_cell={'textAlign': 'left'},
    ),
    html.Br(),
    dcc.Markdown('''
    **Reach Neighbor Change:**

    In areas where topology is hard to automatically determine, upstream and downstream neighbors
    may be incorrect. To report a reach neighbor change, users should submit a **CSV file** containing
    four columns: the current "reach id", the "report index", the new "upstream neighbors", and the new
    "downstream neighbors". **Please note that column order matters!**
    '''
    ),
    dash_table.DataTable(
        ngh_csv.to_dict('records'),
        [{"name": i, "id": i} for i in ngh_csv.columns],
        style_cell={'textAlign': 'left'},
    ),
    html.Br(),
    dcc.Markdown('''
    **Attribute Value Change:**

    SWORD attributes are derived by merging many different global datasets and their respective
    attributes into one congruent product. In cases where the river centerlines do not match well
    between databases, river attributes may be missing or incorrect. These errors are more common
    around tributary and channel junctions, as well as in large braided and anastomosing rivers.
    There are five SWORD attributes users may report new values for. These attributes and their
    "attribute indexes" are as follows:
    '''
    ),
    dash_table.DataTable(
        attr_index_tbl.to_dict('records'),
        [{"name": i, "id": i} for i in attr_index_tbl.columns],
        style_cell={'textAlign': 'left'},
    ),
    html.Br(),
    dcc.Markdown('''
    To report an attribute value change, users should submit a **CSV file** containing four columns:
    the current "reach id", the "report index", the "attribute index" and the new "attribute value".
    **Please note that column order matters!**
    '''
    ),
    dash_table.DataTable(
        attr_csv.to_dict('records'),
        [{"name": i, "id": i} for i in attr_csv.columns],
        style_cell={'textAlign': 'left'},
    ),
    html.Br()
])

#################################################################################################
### Formats for the different reporting options triggered by the report list in the
### report modal pop-up.

# Report drop down list.
report_list = [
    {"label": "Reach Type Change", "value": 1},
    {"label": "Node Order Change", "value": 2},
    {"label": "Reach Neighbor Change", 'value': 3},
    {"label": "Attribute Value Change", 'value': 4},
    ]

# Type change options.
type_body = html.Div([
    html.H6(
        "Enter a Reach ID (required)"
    ),
    dcc.Input(
        id = 'report-1',
        type = 'text',
        placeholder = "Reach ID",
        debounce=True,
        required=True,
        maxLength=11,
        ),
    html.Div(html.Br(),),
    html.H6(
        "Choose a new reach type (required)"
    ),
    dcc.RadioItems(
        id = 'type_radio',
        options=[
        {'label':' 1 - River','value':1},
        {'label':' 3 - Lake/Reservior', 'value':3},
        {'label':' 4 - Dam/Waterfall','value':4},
        {'label':' 5 - Unreliable Topology','value':5},],
        className='btn-group-vertical p-2'),
    html.Div([html.Br()]),
    html.Div([
        dbc.Button(
            "Submit",
            id="report-submit1",
            outline=False,
            color="secondary",
            size="sm",
            style={
                "textTransform": "none",
                # "textAlign":"center",
                "width":"30%"
            },
        ),
    ]),
    html.Div([html.Br()]),
    html.Div(id='submit_status1', style={"width":"50%"}),
])

# Node change options.
node_body = html.Div([
    html.H6(
        "Enter a Reach ID (required)"
    ),
    dcc.Input(
        id = 'report-2',
        type = 'text',
        placeholder = "Reach ID",
        debounce=True,
        required=True,
        maxLength=11,
    ),
    html.Div(html.Br(),),
    html.Div([
        dbc.Button(
            "Submit",
            id="report-submit2",
            outline=False,
            color="secondary",
            size="sm",
            style={
                "textTransform": "none",
                "width":"30%"
            },
        ),
    ]),
    html.Div([html.Br()]),
    html.Div(id='submit_status2', style={"width":"50%"}),
])

# Neighbor change options.
neighbor_body = html.Div([
    html.H6(
        "Enter a Reach ID (required)",
    ),
    dcc.Input(
        id = 'report-3',
        type = 'text',
        placeholder = "Reach ID",
        debounce=True,
        required=True,
        maxLength=11,
        ),
    html.Div(html.Br(),),
    html.H6(
        "Correct Upstream Reaches (required)",
    ),
    html.P(
        "Format: 74248300231 74248300341 etc. (a space is needed between Reach IDs)"
    ),
    html.P(

    ),
    dcc.Input(
        id = 'upstream',
        type = 'text',
        placeholder = "Enter upstream reaches",
        debounce=True,
        # required=True,
        maxLength=47,
        ),
    html.Div(html.Br(),),
    html.H6(
        "Correct Downstream Reaches (required)",
    ),
    html.P(
        "Format: 74248300231 74248300341 etc. (a space is needed between Reach IDs)"
    ),
    dcc.Input(
        id = 'downstream',
        type = 'text',
        placeholder = "Enter downstream reaches",
        debounce=True,
        # required=True,
        maxLength=47,
        ),
    html.Div([html.Br()]),
    html.Div([
        dbc.Button(
            "Submit",
            id="report-submit3",
            outline=False,
            color="secondary",
            size="sm",
            style={
                "textTransform": "none",
                # "textAlign":"center",
                "width":"30%"
            },
        ),
    ]),
    html.Div([html.Br()]),
    html.Div(id='submit_status3', style={"width":"50%"}),
])

# Attribute value change options.
attr_body = html.Div([
    html.H6(
        "Enter a Reach ID (required)",
    ),
    dcc.Input(
        id = 'report-4',
        type = 'text',
        placeholder = "Reach ID",
        debounce=True,
        required=True,
        maxLength=11,
        ),
    html.Div(html.Br(),),
    html.H6(
        "Choose an Attribute to Update (required)"
    ),
    dcc.RadioItems(
        id = 'attr_radio',
        options=[
        {'label':' Flow Accumulation (sq. km)','value':1},
        {'label':' Water Surface Elevation (m)', 'value':2},
        {'label':' Width (m)','value':3},
        {'label':' Slope (m/km)','value':4},
        {'label':' River Name','value':5},],
        className='btn-group-vertical p-2'),
    html.Div([html.Br()]),
    html.H6(
        "Enter Attribute Value (required)"
    ),
    dcc.Input(
        id = 'attr_val',
        type = 'text',
        placeholder = "Enter New Value",
        debounce=True,
        required=True,
        ),
    html.Div([html.Br()]),
    html.Div([
         dbc.Button(
            "Submit",
            id="report-submit4",
            outline=False,
            color="secondary",
            size="sm",
            style={
                "textTransform": "none",
                # "textAlign":"center",
                "width":"30%"
            },
        ),
    ]),
    html.Div([html.Br()]),
    html.Div(id='submit_status4', style={"width":"50%"}),
])

# Report reach modal overlay layout.
report_overlay = dbc.Modal(
    [
        dbc.ModalBody(
            html.Div(children=[
                markdown_body,
                html.Div([
                    html.H5([
                        'Upload a Batch CSV File:'
                    ]),
                ]),
                html.Div([
                    dcc.Upload(id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A(
                            'Select Files',
                            style={
                                'color':'#2fa4e7',
                                'text-decoration':'underline'
                            }
                        )
                    ]), style={
                        'width': '36%',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                    }, multiple=True),
                ]),
                html.Div([html.Br()]),
                html.Div(id='upload-status'),
                html.Div([html.Br()]),
                html.Div([
                    html.H5([
                    'Report a Single Reach:'
                    ]),
                ]),
                html.Div([
                    dcc.Dropdown(
                        id='Report_DropBox',
                        options=report_list,
                        style={
                            # "textAlign":"center",
                            "width":"60%",
                        }
                    ),
                ]),
                html.Div([html.Br()]),
                html.Div(id='report-options'), #different options for reporting a reach.
            ],#style={"textAlign":"center"}
            ),
        ),
        html.Div([html.Br()]),
        dbc.ModalFooter(
            dbc.Button(
                "Close",
                id="report-close",
                className="howto-bn"
                )),
    ],
    id="report-modal",
    size="lg",
)

# Button to report a reach and trigger the report modal pop-up.
button_report = dbc.Button(
    "Report Reach",
    id="report-open",
    outline=False,
    color="primary",
    style={
        "textTransform": "none",
        "margin-left": "5px",
        "color":"white",
        # "background-color":"#C42828",
        "textAlign":"center"
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
        "color":"white",
        # "background-color":"green",
        "textAlign":"center"
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
                                        "SWOT River Database (SWORD)",
                                        style={
                                            "textAlign":"left",
                                            "margin-top":"15px"}),
                                    html.P(html.H4(
                                        "Interactive Dashboard",
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
    'borderTop': '5px' , #2fa4e7 cerulean
    'borderBottom': '5px',
    'padding': '10px',
    'fontWeight': 'bold',
    'color': 'white',
    'background': '#2b3b90'
}

tab_selected_style = {
    'borderTop': '5px solid #2fa4e7', #2fa4e7 cerulean
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
### PRIMARY APP LAYOUT.

app.layout = html.Div([
        header,
        #insert tabs
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
                ],
            style=tabs_styles
            )
        ]),
        html.Br(),
        html.Div(id='tabs-content-example-graph'), #callback for tab content.
        html.Div([
            html.H5(
                'Type a Reach ID and click ENTER or "Plot Reach" \
                    to see node level attributes:',
                style={
                    'marginTop' : '5px',
                    'marginBottom' : '5px',
                    'size':'25'}
            ),
            html.Div('(click "Report Reach" to file a problem \
                with a reach)'),
            dcc.Input(
                id = 'ReachID',
                type = 'number',
                value = 81247100041,
                placeholder = "Reach ID",
                debounce=True,
                min=int(np.min(node_df['reach_id'])),
                max=int(np.max(node_df['reach_id'])),
                step=1,
                required=False,
                size='100'
                ),
            button_plot,
            button_report,
            report_overlay,
            dcc.Graph(
                figure=plot_nodes(node_df_cp),
                id='ReachGraph')
        ]), #end subdiv3
        html.Br(),
        html.Div(children=[
            html.Div(
                'Copyright (c) 2022 University of North Carolina at Chapel Hill',
                style={
                    'textAlign':'left',
                    'font-size': '0.7em',
                    'marginLeft':'5px',
                },
            ),
            html.Div(
                'Dashboard written in Python using the Dash web framework.',
                style={
                    'textAlign':'left',
                    'font-size': '0.7em',
                    'marginLeft':'5px',
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
        ], style={'textAlign':'left', 'color':'slateGrey'}),
    ],
    style={
        'marginTop' : '5px',
        'marginRight' : '50px',
        'marginBottom' : '5px',
        'marginLeft' : '50px',
        "textAlign":"center"}
) #end of app layout

#################################################################################################
######################################  CALLBACKS  ##############################################
#################################################################################################

#Callback that triggers the main map dispaly to change based on which tab is clicked.
#output is the tab layout.
@app.callback(Output('tabs-content-example-graph', 'children'),
              Input('all-tabs-inline', 'value'),)
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.H6(
                dbc.Row(
                    [
                        dbc.Col(html.H3( #was H5
                            'SWORD Version 14'),
                            width=8,
                            className='mt-2',
                            style={"textAlign":"left"}),
                        dbc.Col(dcc.Dropdown(
                            id='DropBox',
                            options=dropdown_list_af,
                            value=dropdown_list_af[0]['value'],
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
                srcDoc=open('data/af_basin_map.html', 'r').read(),
                style={"height": "500px", "width": "100%"}
                )
        ]) #end subdiv2
    elif tab == 'tab-2':
        return html.Div([
            html.H6(
                dbc.Row(
                    [
                        dbc.Col(html.H3(
                            'SWORD Version 14'),
                            width=8,
                            className='mt-2',
                            style={"textAlign":"left"}),
                        dbc.Col(dcc.Dropdown(
                            id='DropBox',
                            options=dropdown_list_as,
                            value=dropdown_list_as[0]['value'],
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
                            'SWORD Version 14'),
                            width=8,
                            className='mt-2',
                            style={"textAlign":"left"}),
                        dbc.Col(dcc.Dropdown(
                            id='DropBox',
                            options=dropdown_list_eu,
                            value=dropdown_list_eu[0]['value'],
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
                            'SWORD Version 14'),
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
                            'SWORD Version 14'),
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
                            'SWORD Version 14'),
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

#Callback that triggers the regional maps to change based on the "Dropbox" option.
@app.callback(
    Output("BasinMap", "srcDoc"),
    Input("DropBox", "value"))
def update_output_div(input_value):
    return open(input_value,'r').read()

#Callback that plots the node level attributes when a Reach ID is put into the input box.
@app.callback(
    [
        Output(component_id='ReachGraph', component_property='figure'),
        Output(component_id='plot_reach', component_property='n_clicks'),
    ],
    [
        Input(component_id='ReachID', component_property='value'),
        Input(component_id='plot_reach', component_property='n_clicks'),
    ]
)
def update_graph(term, n_clicks):
    if term or n_clicks:
        fig = plot_nodes(node_df_cp, term)
        n_clicks = None
        return fig, n_clicks

# Callback for "About" modal popup
@app.callback(
    Output("modal", "is_open"),
    [Input("howto-open", "n_clicks"), Input("howto-close", "n_clicks")],
    [State("modal", "is_open")])
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# Callback for "Report" modal popup
@app.callback(
    Output("report-modal", "is_open"),
    [Input("report-open", "n_clicks"), Input("report-close", "n_clicks")],
    [State("report-modal", "is_open")],
)
def toggle_modal(n3, n4, is_open):
    if n3 or n4:
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

# Callback update the reporting options based on the report dropdown.
@app.callback(Output('report-options', 'children'),
              Input('Report_DropBox', 'value'))
def render_content(report):
    if report is None:
        raise PreventUpdate
    else:
        if report == 1:
            return type_body
        if report == 2:
            return node_body
        if report == 3:
            return neighbor_body
        if report == 4:
            return attr_body

# Callback to wirte report information and display report status for a Reach Type Change.
@app.callback(
    [
        Output("submit_status1", "children"),
        Output("report-submit1","n_clicks"),
    ],
    [
        Input("report-1", "value"),
        Input("type_radio", "value"),
        Input("report-submit1","n_clicks")
    ],
)
def write_report1(rch1, newtype, n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        rch = rch1
        data = newtype
        date_stamp = time.strftime("%d-%b-%Y %H:%M:%S", time.gmtime())
        List = [rch,'1',data,'0',date_stamp,'0']
        with open('user_reports.csv', 'r') as r_object:
            reader_obj = reader(r_object,delimiter=',')
            for row in reader_obj:
                if (List[0] == row[0] and List[1] == row[1]):
                    repeat = True
                    break
            r_object.close()
        if 'repeat' in locals():
            statement = html.Div(['Reach Issue Already Reported'], style={'color':'#C42828'})
            del(repeat)
        else:
            with open('user_reports.csv', 'a') as w_object:
                writer_object = writer(w_object)
                writer_object.writerow(List)
                w_object.close()
            statement = html.Div(['Report Submitted Successfully'], style={'color':'green'})

    n_clicks = None
    return statement, n_clicks

@app.callback(
    [
        Output("submit_status2", "children"),
        Output("report-submit2","n_clicks"),
    ],
    [
        Input("report-2", "value"),
        Input("report-submit2","n_clicks")
    ],
)

# Callback to wirte report information and display report status for a Node Order Change.
def write_report2(rch2, n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        rch = rch2
        data = '1'
        date_stamp = time.strftime("%d-%b-%Y %H:%M:%S", time.gmtime())
        List = [rch,'2',data,'0',date_stamp,'0']
        with open('user_reports.csv', 'r') as r_object:
            reader_obj = reader(r_object,delimiter=',')
            for row in reader_obj:
                if (List[0] == row[0] and List[1] == row[1]):
                    repeat = True
                    break
            r_object.close()
        if 'repeat' in locals():
            statement = html.Div(['Reach Issue Already Reported'], style={'color':'#C42828'})
            del(repeat)
        else:
            with open('user_reports.csv', 'a') as w_object:
                writer_object = writer(w_object)
                writer_object.writerow(List)
                w_object.close()
            statement = html.Div(['Report Submitted Successfully'], style={'color':'green'})

    n_clicks = None
    return statement, n_clicks

# Callback to wirte report information and display report status for a Reach Neighbor Change.
@app.callback(
    [
        Output("submit_status3", "children"),
        Output("report-submit3","n_clicks"),
    ],
    [
        Input("report-3", "value"),
        Input("upstream", "value"),
        Input("downstream", "value"),
        Input("report-submit3","n_clicks")
    ],
    prevent_initial_call=True,
)
def write_report3(rch3, up, dn, n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        rch = rch3
        if up is None:
            data1 = '0'
        else:
            data1 = up
        if dn is None:
            data2 = '0'
        else:
            data2 = dn

        date_stamp = time.strftime("%d-%b-%Y %H:%M:%S", time.gmtime())
        List = [rch,'3',data1,data2,date_stamp,'0']
        with open('user_reports.csv', 'r') as r_object:
            reader_obj = reader(r_object,delimiter=',')
            for row in reader_obj:
                if (List[0] == row[0] and List[1] == row[1]):
                    repeat = True
                    break
            r_object.close()
        if 'repeat' in locals():
            # print('cond.1')
            statement = html.Div(['Reach Issue Already Reported'], style={'color':'#C42828'})
            del(repeat)
        else:
            # print('cond.2')
            with open('user_reports.csv', 'a') as w_object:
                writer_object = writer(w_object)
                writer_object.writerow(List)
                w_object.close()
            statement = html.Div(['Report Submitted Successfully'], style={'color':'green'})

    n_clicks = None
    return statement, n_clicks

# Callback to wirte report information and display report status for an Attribute Value Change.
@app.callback(
    [
        Output("submit_status4", "children"),
        Output("report-submit4","n_clicks"),
    ],
    [
        Input("report-4", "value"),
        Input("attr_radio", "value"),
        Input("attr_val", "value"),
        Input("report-submit4","n_clicks")
    ],
)
def write_report4(rch4, radio, name, n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        rch = rch4
        data = radio
        data2 = name
        date_stamp = time.strftime("%d-%b-%Y %H:%M:%S", time.gmtime())
        List = [rch,'4', str(data), data2, date_stamp,'0']
        with open('user_reports.csv', 'r') as r_object:
            reader_obj = reader(r_object,delimiter=',')
            for row in reader_obj:
                if (List[0] == row[0] and List[2] == row[2]):
                    repeat = True
                    break
            r_object.close()
        if 'repeat' in locals():
            statement = html.Div(['Reach Issue Already Reported'], style={'color':'#C42828'})
            del(repeat)
        else:
            with open('user_reports.csv', 'a') as w_object:
                writer_object = writer(w_object)
                writer_object.writerow(List)
                w_object.close()
            statement = html.Div(['Report Submitted Successfully'], style={'color':'green'})

    n_clicks = None
    return statement, n_clicks

# Callback to wdisplay report status for a bulk report upload.
@app.callback(Output('upload-status', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is None:
        raise PreventUpdate
    else:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
    list_of_contents = None; list_of_names = None; list_of_dates = None
    return children

if __name__ == '__main__':
    app.run_server()
    # app.run_server(debug=True) #use this line instead of the line before to run the app in debug mode.
