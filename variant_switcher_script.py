from pxr import Usd, Tf, UsdGeom, Sdf
from typing import Union
import maya.cmds as cmds
import ufe
import math
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMaya as OpenMaya

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

def world_to_screen_space(world_pos: OpenMaya.MPoint, proj_matrix: OpenMaya.MMatrix, view_matrix: OpenMaya.MMatrix)-> OpenMaya.MVector:
    
    # ViewProj Mat * P (combined into one projection matrix)
    # Convert from world to camera space
    vert_space = world_pos * view_matrix
    cam_space = vert_space * proj_matrix
    
    tmp_space = [cam_space[0],cam_space[1],cam_space[2],cam_space[3]]
      
    # Convert to screen space
    tmp_space[0] /= cam_space[3]
    tmp_space[1] /= cam_space[3]
    tmp_space[2] /= cam_space[3]
    
    out_point = OpenMaya.MVector(tmp_space[0],tmp_space[1],tmp_space[2])
    
    return out_point

# Get the scene's camera position
camera_obj = 'camera1'
camera_pos = cmds.xform(camera_obj, query=True, translation=True, worldSpace=True)

view = OpenMayaUI.M3dView.active3dView()
mayaModelMatrix = OpenMaya.MMatrix()
view.modelViewMatrix(mayaModelMatrix)
mayaProjMatrix = OpenMaya.MMatrix()
view.projectionMatrix(mayaProjMatrix)


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


# Cull assets from list NOT visible to camera
    
# Loop over asset list and swap variants according to distance
for asset in variant_assets:

    shapePath = create_shape_path(asset)
    
    # Get the bbox of the shape node
    bbox = cmds.exactWorldBoundingBox(shapePath, ignoreInvisible=False)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox[0], bbox[1], bbox[2], bbox[3], bbox[4], bbox[5]
    
    lower_corner = OpenMaya.MPoint(xmin,ymin,zmin,1)
    upper_corner = OpenMaya.MPoint(xmax,ymax,zmax,1)
    min_P = world_to_screen_space(lower_corner, mayaProjMatrix, mayaModelMatrix)
    max_P = world_to_screen_space(upper_corner, mayaProjMatrix, mayaModelMatrix)

    width_P = max_P.x - min_P.x
    height_P = max_P.y - min_P.y
    obj_screen_area = width_P * height_P
    print(obj_screen_area)
    
    bbox_percent = (obj_screen_area / 1) * 100
    
    print(bbox_percent)

    var_swap = ""
    
    # Screen Space Percentage
    # Set LOD thresholds: >10% = LOD0, 1-10% = LOD1, 0.1-1% = LOD2, etc.
    
    if bbox_percent < 1:
        var_swap = "_LOD2"
        
    # far awawy, reduce detail
    if bbox_percent > 1:
        # assign LOD1 to asset
        var_swap = "_LOD1"
        
    if bbox_percent > 10:
        #assign LOD2 to asset
        var_swap = "_LOD0"

    '''
    # Distance Based
    center_x = xmin+xmax / 2
    center_y = ymin+ymax / 2
    center_z = zmin+zmax / 2
    
    obj_pos = (center_x, center_y, center_z)
    dist = calc_dist_from_cam(obj_pos, camera_pos)
    
    if dist < 15:
        var_swap = "_LOD0"
        
    # far awawy, reduce detail
    if dist > 15:
        # assign LOD1 to asset
        var_swap = "_LOD1"
        
    if dist > 30:
        #assign LOD2 to asset
        var_swap = "_LOD2"
    '''
    
    '''
    Swapping out the variant
    '''
    
    prim = "/" + asset
    usd_file_path = file_path + prim + prim + ".usda"
    
    # Open a stage to the file
    stage = Usd.Stage.Open(usd_file_path)
    
    if stage:
        target_prim = stage.GetPrimAtPath(Sdf.Path(prim))    
        
    select_variant_from_varaint_set(target_prim, "LOD", asset + var_swap)
