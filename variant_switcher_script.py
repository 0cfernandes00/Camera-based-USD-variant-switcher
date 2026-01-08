from pxr import Usd, Tf, UsdGeom, Sdf
from typing import Union
import maya.cmds as cmds
from maya.internal.ufeSupport import ufeSelectCmd
import ufe
import math

# Swap out prev. variant
def select_variant_from_varaint_set(prim: Usd.Prim, variant_set_name: str, variant_name: str) -> None:
    variant_set = prim.GetVariantSets().GetVariantSet(variant_set_name)
    variant_set.SetVariantSelection(variant_name)
    

# Calculate obj distance from camera
def calc_dist_from_cam(obj_pos: tuple, cam_pos: tuple) -> float:
    
    dist_x = obj_pos[0] - cam_pos[0]
    dist_y = obj_pos[1] - cam_pos[0]
    dist_z = obj_pos[2] - cam_pos[2]
    
    # find the length
    vector_length = math.sqrt(dist_x * dist_x + dist_y * dist_y + dist_z * dist_z)
    
    return vector_length
 
# Helper to set up shapePath str   
def create_shape_path(prim: str) -> str:
    
    output_str = '|'+ prim + '|' + prim + 'Shape'
    return output_str
    
    
# Get the scene's camera position
camera_obj = 'camera1'
camera_pos = cmds.xform(camera_obj, query=True, translation=True, worldSpace=True)



# Switch variant Test

'''
primPathList = ['/yellowDuck']

# create a selection list
sn = ufe.Selection()

for primPath in primPathList:
    ufePath = ufe.PathString.path(proxyShapePath + ',' + primPath)
    ufeSceneItem = ufe.Hierarchy.createItem(ufePath)
    sn.append(ufeSceneItem)
ufeSelectCmd.replaceWith(sn)

'''

# Select all the usd proxy shape nodes in the scene

proxy_shapes = cmds.ls(type="mayaUsdProxyShape")
#print(proxy_shapes)
file_path = "C:/Users/0cfer/Documents/upenn/cs7000/Camera_based_LOD_tool"

variant_assets = []

# Create a list of assets containing variant sets
for node in proxy_shapes:
    base_name = node[:-5]
    prim = "/" + base_name
    
    usd_file_path = file_path + prim + prim + ".usda"
    
    # Open Stage
    stage = Usd.Stage.Open(usd_file_path)
    
    # Get target prim
    target_prim = stage.GetPrimAtPath(Sdf.Path(prim))
    
    # Check if prim has var set
    variant_set = target_prim.GetVariantSets().GetVariantSet("LOD")
    
    if (variant_set):
        variant_assets.append(base_name)


# Create a list of these assets that are visible to camera


# get shapePath
proxyShapePath = create_shape_path('yellowDuck')

# Get the bbox of the shape node
bbox = cmds.exactWorldBoundingBox(proxyShapePath, ignoreInvisible=False)
xmin, ymin, zmin, xmax, ymax, zmax = bbox[0], bbox[1], bbox[2], bbox[3], bbox[4], bbox[5]

center_x = xmin+xmax / 2
center_y = ymin+ymax / 2
center_z = zmin+zmax / 2

obj_pos = (center_x, center_y, center_z)

dist = calc_dist_from_cam(obj_pos, camera_pos)
'''
# far awawy, reduce detail
if dist > 35:
    # assign LOD1 to asset
    
elif dist > 50:
    #assign LOD2 to asset
'''
    

'''
# Calculate the distance from camera
for asset in variant_assets:
    
    proxyShapePath = '|'+asset+'|'+asset+'Shape'
    primPath = '/'+asset

    ufePath = ufe.PathString.path(proxyShapePath + ',' + primPath)
    ufeSceneItem = ufe.Hierarchy.createItem(ufePath)
    ufeSelectCmd.replaceWith(ufeSceneItem)
    
    # Get center bounding box & compute centerpoint
'''

for asset in variant_assets:
    prim = "/" + asset
    
    usd_file_path = file_path + prim + prim + ".usda"
    
    # Open a stage to the file
    stage = Usd.Stage.Open(usd_file_path)
    
    if stage:
        #default_prim = stage.GetDefaultPrim()
        target_prim = stage.GetPrimAtPath(Sdf.Path(prim))    
        
        
    select_variant_from_varaint_set(target_prim, "LOD", asset + "_LOD2")
