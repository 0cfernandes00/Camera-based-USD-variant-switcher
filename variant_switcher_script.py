from pxr import Usd, Tf, UsdGeom, Sdf
from typing import Union
import maya.cmds as cmds
import ufe
import math
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMaya as OpenMaya

# Get the scene's camera 
camera_obj = 'camera1'
camera_pos = None
focal_length = None
focus_dist = None
fstop = None

circleOfConfusion = 10

# global adjustment vars
distanceBased = True
dofBased = False
velocityBased = False
screenSpaceBased = False


def create_lod_ui():
    """Create the LOD switching UI"""
    
    window_name = "lodSwitcherWindow"

    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)
    
    # Create window
    window = cmds.window(window_name, title="LOD Switcher", widthHeight=(300, 350))
    
    # Main layout
    main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnAttach=('both', 10))
    
    # Title
    cmds.text(label="LOD Switching Method", font="boldLabelFont", height=30)
    cmds.separator(height=10)
    
    # Radio button collection for switching methods
    cmds.radioCollection()
    cmds.radioButton('distanceRadio', label='Distance Based', select=distanceBased,
                     onCommand=lambda x: update_method('distance'))
    cmds.radioButton('dofRadio', label='Depth of Field Based', select=dofBased,
                     onCommand=lambda x: update_method('dof'))
    cmds.radioButton('velocityRadio', label='Velocity Based', select=velocityBased,
                     onCommand=lambda x: update_method('velocity'))
    cmds.radioButton('screenSpaceRadio', label='Screen Space Based', select=screenSpaceBased,
                     onCommand=lambda x: update_method('screenspace'))
    
    cmds.separator(height=20)
    
    # Camera selection
    cmds.text(label="Camera Settings", font="boldLabelFont")
    cmds.separator(height=5)
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(100, 180), columnAttach=[(1, 'left', 0), (2, 'left', 5)])
    cmds.text(label="Camera:")
    cmds.textField('cameraField', text=camera_obj, editable=True)
    cmds.setParent('..')
    
    cmds.separator(height=20)
    
    # Distance thresholds (visible when distance based is selected)
    cmds.frameLayout('distanceFrame', label='Distance Thresholds (cm)', collapsable=True, visible=distanceBased)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(150, 100))
    cmds.text(label="LOD0 (High) < ")
    cmds.floatField('distLOD0', value=15.0, precision=1)
    cmds.setParent('..')
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(150, 100))
    cmds.text(label="LOD1 (Medium) < ")
    cmds.floatField('distLOD1', value=30.0, precision=1)
    cmds.setParent('..')
    
    cmds.text(label="LOD2 (Low) >= 30.0", align='left')
    
    cmds.setParent('..')  # columnLayout
    cmds.setParent('..')  # frameLayout
    
    # DOF thresholds
    cmds.frameLayout('dofFrame', label='DOF Thresholds', collapsable=True, visible=dofBased)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 80))
    cmds.text(label="LOD0 (Sharp) < ")
    cmds.floatField('dofLOD0', value=0.2, precision=2)
    cmds.setParent('..')
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 80))
    cmds.text(label="LOD1 (Medium Blur) < ")
    cmds.floatField('dofLOD1', value=0.5, precision=2)
    cmds.setParent('..')
    
    cmds.text(label="LOD2 (Blurry) >= 0.5", align='left')
    
    cmds.setParent('..')  # columnLayout
    cmds.setParent('..')  # frameLayout
    
    # Velocity thresholds
    cmds.frameLayout('velocityFrame', label='Velocity Thresholds (cm/frame)', collapsable=True, visible=velocityBased)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 80))
    cmds.text(label="LOD0 (Stationary) < ")
    cmds.floatField('velLOD0', value=7.5, precision=1)
    cmds.setParent('..')
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 80))
    cmds.text(label="LOD1 (Walking) < ")
    cmds.floatField('velLOD1', value=15.0, precision=1)
    cmds.setParent('..')
    
    cmds.text(label="LOD2 (Running) >= 15.0", align='left')
    
    cmds.setParent('..')  # columnLayout
    cmds.setParent('..')  # frameLayout
    
    # Screen space thresholds
    cmds.frameLayout('screenSpaceFrame', label='Screen Space Thresholds (%)', collapsable=True, visible=screenSpaceBased)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 80))
    cmds.text(label="LOD0 (Large) > ")
    cmds.floatField('screenLOD0', value=10.0, precision=1)
    cmds.setParent('..')
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 80))
    cmds.text(label="LOD1 (Medium) > ")
    cmds.floatField('screenLOD1', value=1.0, precision=1)
    cmds.setParent('..')
    
    cmds.text(label="LOD2 (Small) <= 1.0", align='left')
    
    cmds.setParent('..')  # columnLayout
    cmds.setParent('..')  # frameLayout
    
    cmds.separator(height=20)
    
    # Execute button
    cmds.button(label='Apply LOD Switching', height=40, backgroundColor=(0.3, 0.5, 0.3),
                command=lambda x: execute_lod_switching())
    
    cmds.separator(height=10)
    
    # Show window
    cmds.showWindow(window)

# DOF calculation
def calc_dof_blur(obj_dist: float) -> float:
    obj_dist_mm = obj_dist * 10.0
    focus_dist_mm = focus_dist * 10.0
    
    aperture = focal_length / fstop
    denominator = obj_dist_mm * (focus_dist_mm - focal_length)
    blur = abs(aperture * focal_length * (obj_dist_mm - focus_dist_mm) / denominator)
        
    return blur

# Swap out prev. variant
def select_variant_from_varaint_set(prim: Usd.Prim, variant_set_name: str, variant_name: str) -> None:
    variant_set = prim.GetVariantSets().GetVariantSet(variant_set_name)
    variant_set.SetVariantSelection(variant_name)
    

# Check distance from one frame to antoher, velocity based LOD switching
def velocity_change(lower_corner: tuple, upper_corner: tuple, shapePath: str) -> float:

    currTime = cmds.currentTime(q=True)
    cmds.currentTime(12, edit = True)

    moved_bbox = cmds.exactWorldBoundingBox(shapePath, ignoreInvisible=False)
    xmin, ymin, zmin, xmax, ymax, zmax = moved_bbox[0], moved_bbox[1], moved_bbox[2], moved_bbox[3], moved_bbox[4], moved_bbox[5]
    
    moved_upper_corner = OpenMaya.MPoint(xmax,ymax,zmax,1)
    max_update = moved_upper_corner - upper_corner

    result = math.sqrt(max_update[0] * max_update[0] + max_update[1] * max_update[1] + max_update[2] * max_update[2])

    cmds.currentTime(currTime, edit = True)

    """
    24 frames/second
    walking speed ~ 140 cm/s, running speed ~ 300 cm/s
    12 frames -> 70 cm, 150 cm 
    """

    return result

def update_method(method):
    global distanceBased, dofBased, velocityBased, screenSpaceBased
    if method == 'distance':
        distanceBased = True
        dofBased = False
        velocityBased = False
        screenSpaceBased = False
    if method == 'dof':
        distanceBased = False
        dofBased = True
        velocityBased = False
        screenSpaceBased = False
    if method == 'velocity':
        distanceBased = False
        dofBased = False
        velocityBased = True
        screenSpaceBased = False
    if method == 'screenspace':
        distanceBased = False
        dofBased = False
        velocityBased = False
        screenSpaceBased = True

    # Update visibility of threshold frames based on selected method
    cmds.frameLayout('distanceFrame', edit=True, visible=distanceBased)
    cmds.frameLayout('dofFrame', edit=True, visible=dofBased)
    cmds.frameLayout('velocityFrame', edit=True, visible=velocityBased)
    cmds.frameLayout('screenSpaceFrame', edit=True, visible=screenSpaceBased)


# Calculate obj distance from camera
def calc_dist_from_cam(obj_pos: tuple, cam_pos: tuple) -> float:
    
    dist_x = obj_pos[0] - cam_pos[0]
    dist_y = obj_pos[1] - cam_pos[1]
    dist_z = obj_pos[2] - cam_pos[2]
    
    vector_length = math.sqrt(dist_x * dist_x + dist_y * dist_y + dist_z * dist_z)
    return vector_length
 
# Helper to set up shapePath str   
def create_shape_path(prim: str) -> str:
    
    output_str = '|'+ prim + '|' + prim + 'Shape'
    return output_str
    
def find_MinMax(pointsList: tuple) -> tuple:
    
    x_min = 100000
    y_min = 100000
    x_max = -100000
    y_max = -10000

    for i in range(8):
       
        x = pointsList[i][0]
        y = pointsList[i][1]
        if x < x_min:
            x_min = x
        if y < y_min:
            y_min = y
        if x > x_max:
            x_max = x
        if y > y_max:
            y_max = y
      
    result = (x_min,y_min,x_max,y_max)      
    return result

def world_to_screen_space(world_pos: OpenMaya.MPoint)-> tuple:
    
    # ViewProj Mat * P (combined into one projection matrix)
    # Convert from world to camera space
    vert_space = world_pos * mayaModelMatrix
    cam_space = vert_space * mayaProjMatrix
    
    tmp_space = [cam_space[0],cam_space[1],cam_space[2],cam_space[3]]
      
    # Convert to screen space
    tmp_space[0] /= cam_space[3]
    tmp_space[1] /= cam_space[3]
    tmp_space[2] /= cam_space[3]
    
    out_point = OpenMaya.MVector(tmp_space[0],tmp_space[1],tmp_space[2])
    
    inside = True
    if((out_point[0] > 1) or (out_point[0] < -1)):
        if((out_point[1] > 1) or (out_point[1] < -1)):
            if((out_point[2] > 1) or (out_point[2] < -1)):
                inside = False
    
    return (out_point[0], out_point[1], out_point[2], inside)

def execute_lod_switching():
    global camera_obj, camera_pos, focal_length, focus_dist, fstop, mayaModelMatrix, mayaProjMatrix

    camera_obj = cmds.textField('cameraField', query=True, text=True)
    camera_pos = cmds.xform(camera_obj, query=True, translation=True, worldSpace=True)

    thresholds = {}
    if distanceBased:
        thresholds['distMin'] = cmds.floatField('distLOD0', query=True, value=True)
        thresholds['distMid'] = cmds.floatField('distLOD1', query=True, value=True)
    elif dofBased:
        thresholds['dofMin'] = cmds.floatField('dofLOD0', query=True, value=True)
        thresholds['dofMid'] = cmds.floatField('dofLOD1', query=True, value=True)
    elif velocityBased:
        thresholds['velMin'] = cmds.floatField('velLOD0', query=True, value=True)
        thresholds['velMid'] = cmds.floatField('velLOD1', query=True, value=True)
    elif screenSpaceBased:
        thresholds['screenMin'] = cmds.floatField('screenLOD0', query=True, value=True)
        thresholds['screenMid'] = cmds.floatField('screenLOD1', query=True, value=True)

    focal_length = cmds.getAttr(camera_obj + '.focalLength')
    focus_dist = cmds.getAttr(camera_obj + '.focusDistance')
    fstop = cmds.getAttr(camera_obj + '.fStop')

    view = OpenMayaUI.M3dView.active3dView()
    mayaModelMatrix = OpenMaya.MMatrix()
    view.modelViewMatrix(mayaModelMatrix)
    mayaProjMatrix = OpenMaya.MMatrix()
    view.projectionMatrix(mayaProjMatrix)

    run_switching(thresholds)

def run_switching(thresholds):
    
    # Select all the usd proxy shape nodes in the scene
    proxy_shapes = cmds.ls(type="mayaUsdProxyShape")
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
        
        a = OpenMaya.MPoint(xmin,ymin,zmin,1)
        b = OpenMaya.MPoint(xmin,ymin,zmax,1)
        c = OpenMaya.MPoint(xmin,ymax,zmin,1)
        d = OpenMaya.MPoint(xmax,ymin,zmin,1)
        e = OpenMaya.MPoint(xmax,ymax,zmax,1)
        f = OpenMaya.MPoint(xmax,ymax,zmin,1)
        g = OpenMaya.MPoint(xmax,ymin,zmax,1)
        h = OpenMaya.MPoint(xmin,ymax,zmax,1)
        
        xform_a = world_to_screen_space(a)
        xform_b = world_to_screen_space(b)
        xform_c = world_to_screen_space(c)
        xform_d = world_to_screen_space(d)
        xform_e = world_to_screen_space(e)
        xform_f = world_to_screen_space(f)
        xform_g = world_to_screen_space(g)
        xform_h = world_to_screen_space(h)
        
        if (not xform_a[3] and not xform_b[3] and not xform_c[3] and not xform_d[3] and not xform_e[3] and not xform_f[3] and not xform_g[3] and not xform_h[3]):
            # completely outside view frustum, skip
            print("outside view")
            select_variant_from_varaint_set(target_prim, "LOD", asset + "_LOD2")
        else:
            # within view frustum
            
            xform_list = (xform_a,xform_b,xform_c,xform_d,xform_e,xform_f,xform_g,xform_h)
            min_x,min_y,max_x,max_y = find_MinMax(xform_list)
            
            # bring into 0-1 space
            min_x = min_x * 0.5 + 0.5
            min_y = min_y * 0.5 + 0.5
            max_x = max_x * 0.5 + 0.5
            max_y = max_y * 0.5 + 0.5
            
            var_swap = ""

            # Distance Based
            center_x = xmin+xmax / 2
            center_y = ymin+ymax / 2
            center_z = zmin+zmax / 2
            
            obj_pos = (center_x, center_y, center_z)
            
            dist = calc_dist_from_cam(obj_pos, camera_pos)

            

            if (velocityBased):

                
                vel_change = velocity_change(lower_corner, upper_corner, shapePath)


                # Velcoity based adjustment
                velLOD0 = thresholds['velMin']
                velLOD1 = thresholds['velMid']
                if (vel_change < velLOD0): 
                    var_swap = "_LOD0"         # object is stationary
                elif (vel_change > velLOD1):
                    var_swap = "_LOD1"         # object is at walking speed
                if (vel_change > 15) :
                    var_swap = "_LOD2"         # object is at running speed

            if (dofBased):

                obj_dof = calc_dof_blur(dist)
                print("Dist from camera: " + str(dist))
                print("DOF blur: " + str(obj_dof))

                distance_from_focus = abs(dist - focus_dist) / focus_dist
                print("Distance from focus: " + str(distance_from_focus))

                dofLOD0 = thresholds['dofMin']
                dofLOD1 = thresholds['dofMid']

                # DOF based adjustment
                if distance_from_focus < dofLOD0:
                    var_swap = "_LOD0"
                elif distance_from_focus < dofLOD1:
                    var_swap = "_LOD1"
                else:
                    var_swap = "_LOD2"

            if (screenSpaceBased):

                # Set LOD thresholds: >10% = LOD0, 1-10% = LOD1, 0.1-1% = LOD2, etc.
                width_P = abs(max_x - min_x)
                height_P = abs(max_y - min_y)
                obj_screen_area = width_P * height_P
                
                bbox_percent = (obj_screen_area / 1) * 100

                ssLOD0 = thresholds['screenMin']
                ssLOD1 = thresholds['screenMid']
                
                # Screen-space adjustment
                if bbox_percent < ssLOD0:
                    var_swap = "_LOD2"  
                elif bbox_percent > ssLOD1:
                    var_swap = "_LOD1"
                if bbox_percent > 10:
                    var_swap = "_LOD0"
            
            if (distanceBased):
                distLOD0 = thresholds['distMin']
                distLOD1 = thresholds['distMid']
                # Distance based adjustment
                if dist < distLOD0 :
                    var_swap = "_LOD0"  
                elif dist > distLOD1:
                    var_swap = "_LOD1"    
                if dist > 30:
                    var_swap = "_LOD2"

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

create_lod_ui()