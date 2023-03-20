import os
os.chdir('/Users/ealteanau/Documents/SWORD_Dev/src/SWORD_Dashboard/assets/')
import geopandas as gp
import numpy as np
import folium
from branca.element import MacroElement
from jinja2 import Template
import random
from matplotlib import cm
from mapclassify import Quantiles, EqualInterval
from matplotlib.colors import rgb2hex
import branca_custom as bcm
import time
import glob
import netCDF4 as nc

#################################################################################################
######################################  FUNCTIONS  ##############################################
#################################################################################################

class BindColormap(MacroElement):
    """Binds a colormap to a given layer.

    Parameters
    ----------
    colormap : branca.colormap.ColorMap
        The colormap to bind.
    """
    def __init__(self, layer, colormap):
        super(BindColormap, self).__init__()
        self.layer = layer
        self.colormap = colormap
        self._template = Template(u"""
        {% macro script(this, kwargs) %}
            {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
            {{this._parent.get_name()}}.on('overlayadd', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
                }});
            {{this._parent.get_name()}}.on('overlayremove', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'none';
                }});
        {% endmacro %}
        """)  # noqa

#################################################################################################

class ColormapStyleFunction:
    
    def __init__(self, cmap, attribute,randomcolors=False):
        self._cmap = cmap
        self._attribute = attribute
        self._randomcolors = randomcolors
        
    def __call__(self, x):
        if self._randomcolors:
            #hexcolor = '#ff0000'
            hexcolor="#"+''.join([random.choice('0123456789ABCDEF') for i in range(6) ] )
        else:
            hexcolor = self._cmap(x["properties"][self._attribute])

        return {'color': hexcolor, 'weight' : 3}

#################################################################################################

def colors_at_breaks(cmap, breaks):
    return [rgb2hex(cmap(bb)) for bb in breaks]

#################################################################################################

def getListOfFiles(dirName):

    """
    FUNCTION:
        For the given path, gets a recursive list of all files in the directory tree.

    INPUTS
        dirName -- Input directory

    OUTPUTS
        allFiles -- list of files under directory
    """

    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)

    return allFiles

#################################################################################################

def get_data(fn):
    sword = gp.read_file(fn)
    sword_simple = sword.copy()
    sword_simple = sword_simple.simplify(0.005) #0.002 is better but will add size to file. 
    sword_simple = gp.GeoDataFrame(sword_simple)
    sword_simple['reach_id'] = sword['reach_id'].astype(str)
    sword_simple['wse'] = sword['wse'] 
    sword_simple['facc'] = sword['facc']
    sword_simple['width'] = sword['width']
    sword_simple['dist_out'] = sword['dist_out']
    sword_simple['slope'] = sword['slope']
    sword_simple['river_name'] = sword['river_name']
    sword_simple['rch_id_up'] = sword['rch_id_up']
    sword_simple['rch_id_dn'] = sword['rch_id_dn']
    sword_simple['swot_obs'] = sword['swot_obs']
    sword_simple.rename(columns = {0:'geometry'}, inplace = True)
    sword_json = sword_simple.to_json()
    del(sword)
    return sword_simple, sword_json

#################################################################################################
########################################### MAIN CODE ###########################################
#################################################################################################
# read in and format data
outdir = '/Users/ealteanau/Documents/SWORD_Dev/src/SWORD_Dashboard/data/'
shp_dir = '/Users/ealteanau/Documents/SWORD_Dev/outputs/Reaches_Nodes/v14/shp/'
shp_paths = [file for file in getListOfFiles(shp_dir) if '.shp' in file and 'reaches' in file]
shp_paths = np.unique(shp_paths) 
basins = [path[-12:-8] for path in shp_paths]

## loop through each level 2 basin and produce SWORD maps. Save to "data" directory.  
for ind in list(range(len(shp_paths))):
    start = time.time()
    b = basins[ind]
    sword_simple, sword_json = get_data(shp_paths[ind])

    # Format map layer properties
    rch_id = folium.GeoJsonTooltip(fields=["reach_id", "river_name", "rch_id_up", "rch_id_dn"])
    facc = folium.GeoJsonTooltip(fields=["reach_id", "river_name", "facc"])
    wse = folium.GeoJsonTooltip(fields=["reach_id", "river_name", "wse"])
    dist_out = folium.GeoJsonTooltip(fields=["reach_id", "river_name", "dist_out"])
    wth = folium.GeoJsonTooltip(fields=["reach_id", "river_name", "width"])
    slope = folium.GeoJsonTooltip(fields=["reach_id", "river_name", "slope"])
    obs = folium.GeoJsonTooltip(fields=["reach_id", "river_name", "swot_obs"])

    wse_bins = Quantiles(sword_simple['wse'], k=25).bins
    facc_bins = Quantiles(sword_simple['facc'], k=25).bins
    dist_bins = Quantiles(sword_simple['dist_out'], k=25).bins
    wth_bins = Quantiles(sword_simple['width'], k=25).bins
    slope_bins = Quantiles(sword_simple['slope'], k=25).bins
    obs_bins = np.array([0,1,2,4,6,8,10])
    # obs_bins = np.round(EqualInterval(swot_obs, k=10).bins)

    wse_ei = EqualInterval(sword_simple['wse'], k=5).bins
    facc_ei = EqualInterval(sword_simple['facc'], k=5).bins
    dist_ei = EqualInterval(sword_simple['dist_out'], k=5).bins
    wth_ei = EqualInterval(sword_simple['width'], k=5).bins
    slope_ei = EqualInterval(sword_simple['slope'], k=5).bins
    obs_ei = np.array([0,1,2,4,6,8,10])
    # obs_ei = np.round(EqualInterval(swot_obs, k=5).bins)

    wse_colors = colors_at_breaks(cm.get_cmap('terrain'), np.linspace(0, 1, len(wse_bins)))
    dist_colors = colors_at_breaks(cm.get_cmap('plasma'), np.linspace(0, 1, len(dist_bins)))
    wth_colors = colors_at_breaks(cm.get_cmap('viridis'), np.linspace(0, 1, len(wth_bins)))
    slope_colors = colors_at_breaks(cm.get_cmap('hot'), np.linspace(0, 1, len(slope_bins)))
    obs_colors = colors_at_breaks(cm.get_cmap('gnuplot2'), np.linspace(0, 1, len(obs_bins)))
    facc_colors = colors_at_breaks(cm.get_cmap('Spectral'), np.linspace(0, 1, len(facc_bins)))
    facc_colors = facc_colors[::-1]

    wse_colors5 = colors_at_breaks(cm.get_cmap('terrain'), np.linspace(0, 1, len(wse_ei)))
    dist_colors5 = colors_at_breaks(cm.get_cmap('plasma'), np.linspace(0, 1, len(dist_ei)))
    wth_colors5 = colors_at_breaks(cm.get_cmap('viridis'), np.linspace(0, 1, len(wth_ei)))
    slope_colors5 = colors_at_breaks(cm.get_cmap('hot'), np.linspace(0, 1, len(slope_ei)))
    obs_colors5 = colors_at_breaks(cm.get_cmap('gnuplot2'), np.linspace(0, 1, len(obs_ei)))
    facc_colors5 = colors_at_breaks(cm.get_cmap('Spectral'), np.linspace(0, 1, len(facc_ei)))
    facc_colors5 = facc_colors5[::-1]

    rch_cmap = []
    wse_cmap = bcm.LinearColormap( #originally: branca.colormap.LinearColormap
            colors=wse_colors,
            index=wse_bins, 
            vmin=wse_bins[0], 
            vmax=wse_bins[-1],
            caption='water surface elevation (m)',
            labels=wse_bins
        )
    facc_cmap = bcm.LinearColormap(
            colors=facc_colors,
            index=facc_bins, 
            vmin=facc_bins[0], 
            vmax=facc_bins[-1],
            caption='flow accumulation (sq.km)',
            labels=facc_bins
        )
    dist_cmap = bcm.LinearColormap(
            colors=dist_colors,
            index=dist_bins, 
            vmin=dist_bins[0], 
            vmax=dist_bins[-1],
            caption='distance from outlet (m)',
            labels=dist_bins
        )
    wth_cmap = bcm.LinearColormap(
            colors=wth_colors,
            index=wth_bins, 
            vmin=wth_bins[0], 
            vmax=wth_bins[-1],
            caption='width (m)',
            labels=wth_bins
        )
    slope_cmap = bcm.LinearColormap(
            colors=slope_colors,
            index=slope_bins, 
            vmin=slope_bins[0], 
            vmax=slope_bins[-1],
            caption='slope (m/km)',
            labels=slope_bins
        )
    obs_cmap = bcm.LinearColormap(
            colors=obs_colors,
            index=obs_bins, 
            vmin=obs_bins[0], 
            vmax=obs_bins[-1],
            caption='SWOT observations',
            labels=obs_bins
        )

    wse_cmap_display = bcm.LinearColormap(
            colors=wse_colors5,
            index=wse_ei, 
            vmin=0, 
            vmax=wse_ei[-1],
            caption='water surface elevation (m)',
            labels=[0, 0, 0, 0, wse_ei[-1]]
        )
    facc_cmap_display = bcm.LinearColormap(
            colors=facc_colors5,
            index=facc_ei, 
            vmin=0, 
            vmax=facc_ei[-1],
            caption='flow accumulation (sq.km)',
            labels=[0, 0, 0, 0, facc_ei[-1]]
        )
    dist_cmap_display = bcm.LinearColormap(
            colors=dist_colors5,
            index=dist_ei, 
            vmin=0, 
            vmax=dist_ei[-1],
            caption='distance from outlet (m)',
            labels=[0, 0, 0, 0, dist_ei[-1]]
        )
    wth_cmap_display = bcm.LinearColormap(
            colors=wth_colors5,
            index=wth_ei, 
            vmin=0, 
            vmax=wth_ei[-1],
            caption='width (m)',
            labels=[0, 0, 0, 0, wth_ei[-1]]
        )
    slope_cmap_display = bcm.LinearColormap(
            colors=slope_colors5,
            index=slope_ei, 
            vmin=0, 
            vmax=slope_ei[-1],
            caption='slope (m/km)',
            labels=[0, 0, 0, 0, slope_ei[-1]]
        )
    obs_cmap_display = bcm.LinearColormap(
            colors=obs_colors5,
            index=obs_ei, 
            vmin=0, 
            vmax=obs_ei[-1],
            caption='SWOT observations',
            labels=obs_ei
        )

    rch_id_sf = ColormapStyleFunction(rch_cmap,'reach_id',randomcolors=True)
    wse_sf = ColormapStyleFunction(wse_cmap,'wse')
    facc_sf = ColormapStyleFunction(facc_cmap,'facc')
    dist_sf = ColormapStyleFunction(dist_cmap,'dist_out')
    wth_sf = ColormapStyleFunction(wth_cmap,'width')
    slope_sf = ColormapStyleFunction(slope_cmap,'slope')
    obs_sf = ColormapStyleFunction(obs_cmap,'swot_obs')

    wse_layer = folium.GeoJson(
        sword_json,
        style_function=wse_sf,
        tooltip=wse,
        name="Water Surface Elevation (m)",
        overlay = True,
        control = True,
        show = False,
        popup=folium.GeoJsonPopup(fields=['reach_id', 'river_name', 'wse']))                       
    wth_layer = folium.GeoJson(
        sword_json,
        style_function=wth_sf,
        tooltip=wth,
        name="Width (m)",
        overlay = True,
        control = True,
        show = False,
        popup=folium.GeoJsonPopup(fields=['reach_id', 'river_name', 'width']))
    facc_layer = folium.GeoJson(
        sword_json,
        style_function=facc_sf,
        tooltip=facc,
        name="Flow Accumulation (sq.km)",
        overlay = True,
        control = True,
        show = False,
        popup=folium.GeoJsonPopup(fields=['reach_id', 'river_name', 'facc']))
    dist_layer = folium.GeoJson(
        sword_json,
        style_function=dist_sf,
        tooltip=dist_out,
        name="Distance From Outlet (m)",
        overlay = True,
        control = True,
        show = False,
        popup=folium.GeoJsonPopup(fields=['reach_id', 'river_name', 'dist_out']))
    rch_layer = folium.GeoJson(
        sword_json,
        style_function=rch_id_sf,
        tooltip=rch_id,
        name="Reach ID",
        overlay = True,
        control = True,
        show = True,
        popup=folium.GeoJsonPopup(fields=['reach_id', 'river_name', 'rch_id_up', 'rch_id_dn', 'swot_obs']))
    slope_layer = folium.GeoJson(
        sword_json,
        style_function=slope_sf,
        tooltip=slope,
        name="Slope (m/km)",
        overlay = True,
        control = True,
        show = False,
        popup=folium.GeoJsonPopup(fields=['reach_id', 'river_name', 'slope']))
    obs_layer = folium.GeoJson(
        sword_json,
        style_function=obs_sf,
        tooltip=obs,
        name="SWOT Observations",
        overlay = True,
        control = True,
        show = False,
        popup=folium.GeoJsonPopup(fields=['reach_id', 'river_name', 'swot_obs']))

    # Retrieve bounding box and center
    bounds = sword_simple.geometry.total_bounds.tolist()
    if b == 'hb35':
        center = (65.5,155)
    else:
        center = (0.5 * (bounds[1] + bounds[3]), 0.5 * (bounds[0] + bounds[2]))

    # Create map
    parent_map = folium.Map(location=center, 
                tiles='cartodbpositron',
                name = 'Carto Basemap', 
                zoom_start=5)

    base2 = folium.TileLayer(
            tiles = 'https://server.arcgisonline.com/ArcGIS/rest/'\
                'services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr = 'Esri',
            name = 'Esri Satellite',
            overlay = False,
            control = True
        ).add_to(parent_map)

    parent_map.add_child(rch_layer)
    parent_map.add_child(wse_layer)
    parent_map.add_child(wth_layer)
    parent_map.add_child(facc_layer)
    parent_map.add_child(dist_layer)
    parent_map.add_child(slope_layer)
    parent_map.add_child(obs_layer)
    parent_map.add_child(wse_cmap_display)
    parent_map.add_child(wth_cmap_display)
    parent_map.add_child(facc_cmap_display)
    parent_map.add_child(dist_cmap_display)
    parent_map.add_child(slope_cmap_display)
    parent_map.add_child(obs_cmap_display)
    parent_map.add_child(BindColormap(wse_layer,wse_cmap_display))
    parent_map.add_child(BindColormap(wth_layer,wth_cmap_display))
    parent_map.add_child(BindColormap(facc_layer,facc_cmap_display))
    parent_map.add_child(BindColormap(dist_layer,dist_cmap_display))
    parent_map.add_child(BindColormap(slope_layer,slope_cmap_display))
    parent_map.add_child(BindColormap(obs_layer,obs_cmap_display))
    folium.LayerControl('bottomright', collapsed=False).add_to(parent_map) 
    
    if os.path.exists(outdir): 
        outpath =  outdir+b+'_sword_map.html'
    else:
        os.makedirs(outdir)
        outpath =  outdir+b+'_sword_map.html'
    
    parent_map.save(outpath)

    end = time.time()
    print('Completed '+b+'_sword_map in: '+str(np.round((end-start),2))+' sec')
