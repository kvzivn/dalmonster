"""Actual Cycles diffuse irradiance bake for Knarkrondellen's static ground.
Usage: Blender --background --python scripts/bake_lighting.py
PNG is 16-bit sRGB encoded; load with THREE.SRGBColorSpace to recover linear light.
World UV: u=(ThreeX+65)/130, v=(65-ThreeZ)/130.
"""
import bpy, math, os, json, time, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
START=time.time()
def denoise_bake(img):
    scene=bpy.context.scene
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene.view_settings.exposure=0;scene.view_settings.gamma=1
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='16'
    tree=bpy.data.node_groups.new('Ground irradiance OpenImageDenoise','CompositorNodeTree')
    tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    source=tree.nodes.new('CompositorNodeImage');source.image=img
    denoise=tree.nodes.new('CompositorNodeDenoise')
    output=tree.nodes.new('NodeGroupOutput')
    tree.links.new(source.outputs['Image'],denoise.inputs['Image']);tree.links.new(denoise.outputs['Image'],output.inputs['Image'])
    scene.compositing_node_group=tree
    hidden={o:o.hide_render for o in scene.objects}
    for o in hidden:o.hide_render=True
    old_camera=scene.camera;old_samples=scene.cycles.samples
    camera_data=bpy.data.cameras.new('Denoise pass camera');camera=bpy.data.objects.new('Denoise pass camera',camera_data);scene.collection.objects.link(camera);scene.camera=camera
    scene.cycles.samples=1;scene.render.resolution_x=2048;scene.render.resolution_y=2048;scene.render.resolution_percentage=100
    print('OpenImageDenoise compositor pass',flush=True)
    bpy.ops.render.render()
    bpy.data.images['Render Result'].save_render(str(ROOT/'public/assets/ground-lightmap.png'),scene=scene)
    for o,h in hidden.items():o.hide_render=h
    scene.camera=old_camera;scene.cycles.samples=old_samples;bpy.data.objects.remove(camera,do_unlink=True)

if '--denoise-only' in sys.argv:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'.dream-loop/lighting.blend'))
    denoise_bake(bpy.data.images['Ground irradiance linear'])
    print('DENOISED ground-lightmap.png saved',flush=True)
    sys.exit(0)

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'.dream-loop/environment.blend'))
# Match the playable scene's replacement architecture and removed park entrance.
# Delete only the original source meshes before importing their replacements.
for obj in list(bpy.data.objects):
    if obj.name.startswith(('Building_North_', 'Building_West_', 'Park_Gate_')) or obj.name in {'Tree_0_Bark','Tree_1_Bark','Tree_2_Bark','Tree_3_Bark'}:
        bpy.data.objects.remove(obj, do_unlink=True)
bake_assets=['planting.glb', 'border-planting.glb', 'surroundings-no-gate.glb',
             'streets.glb', 'architecture-polish.glb', 'cosy-street.glb', 'trees-polish.glb']
# The completed courtyard is optional during --prepare-only; the final bake uses
# it whenever present. Pavement-joins and old facade-aprons are receiving surfaces,
# so neither is imported as an opaque occluder above the world-space target.
if (ROOT/'public/assets/courtyard-edge.glb').exists():bake_assets.append('courtyard-edge.glb')
for asset in bake_assets:
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'public/assets'/asset))
    if asset=='surroundings-no-gate.glb':
        # New facades and their corner shop replace the previous detail overlays.
        for obj in set(bpy.data.objects)-before:
            if obj.name.startswith(('Building_North_Additions', 'Building_West_Additions')):
                bpy.data.objects.remove(obj, do_unlink=True)
# The world bake target represents these receiving surfaces. Avoid baking
# beneath an opaque duplicate sidewalk/road plane from the streets asset.
for o in list(bpy.data.objects):
    if any(slot.material and slot.material.name in ['Street_Asphalt','Street_Sidewalk'] for slot in o.material_slots):
        o.hide_render=True
# Parked cars share the same placement data as Three.js, converted from Y-up.
for placement in json.loads((ROOT/'src/layout.json').read_text()).get('parkedCars',[]):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'public/assets/parked-car.glb'))
    from mathutils import Matrix
    transform=Matrix.Translation((placement['x'],-placement['z'],0)) @ Matrix.Rotation(placement['yaw'],4,'Z')
    added=set(bpy.data.objects)-before
    for o in added:
        if o.parent not in added:o.matrix_world=transform @ o.matrix_world

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.cycles.use_denoising=True
scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=3
scene.cycles.glossy_bounces=1;scene.cycles.transmission_bounces=0
scene.cycles.transparent_max_bounces=4
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL';prefs.get_devices()
    devices=list(prefs.devices)
    for d in devices:d.use=d.type=='METAL'
    if any(d.type=='METAL' for d in devices):scene.cycles.device='GPU'
    print('BAKE DEVICES',[(d.name,d.type,d.use) for d in devices],flush=True)
except Exception as e:print('Metal unavailable, using CPU',str(e),flush=True)

world=bpy.data.worlds.new('Cool autumn night sky');scene.world=world;world.use_nodes=True
bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.17,.245,.34,1);bg.inputs['Strength'].default_value=.065

def simple_material(name,color,roughness=.8):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=roughness
    return m
iron=simple_material('Bake iron occluders',(.035,.045,.04))
stone=simple_material('Bake weathered curb',(.20,.21,.19))

def cube(name,loc,scale,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
    return o
def cylinder(name,loc,radius,depth,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(mat)
    return o
def point(name,x,y,z,energy,radius=.075):
    data=bpy.data.lights.new(name,'POINT');data.energy=energy;data.color=(1,.54,.19);data.shadow_soft_size=radius
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=(x,y,z)
    return obj
def area(name,loc,target,energy,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.color=(1,.54,.19);data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    return obj

def add_warm_window_spill():
    """Find the actual illuminated near-facade window boxes, not dim windows.
    glTF splits vertices at normals/UV seams, so weld coordinates logically before
    extracting connected components. Meshes and material assignments stay intact.
    """
    report=[]
    for obj in list(bpy.data.objects):
        if obj.type!='MESH' or not obj.name.startswith(('Building_North_Polish_', 'Building_West_Polish_')):continue
        warm_slots={i for i,slot in enumerate(obj.material_slots) if slot.material and slot.material.name.split('.')[0]=='Cosy_WarmRoom'}
        polys=[p for p in obj.data.polygons if p.material_index in warm_slots]
        if not polys:continue
        points={};vertex_map={};parents=[];coordinates=[]
        for poly in polys:
            for vi in poly.vertices:
                if vi in vertex_map:continue
                co=obj.matrix_world @ obj.data.vertices[vi].co;key=tuple(round(float(c),5) for c in co)
                if key not in points:
                    points[key]=len(parents);parents.append(len(parents));coordinates.append(co.copy())
                vertex_map[vi]=points[key]
        def find(i):
            while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
            return i
        for poly in polys:
            ids=[vertex_map[vi] for vi in poly.vertices];first=find(ids[0])
            for i in ids[1:]:parents[find(i)]=first
        components={}
        for i,co in enumerate(coordinates):components.setdefault(find(i),[]).append(co)
        facade_radius=27 if obj.name.startswith('Building_North') else 29
        for component in components.values():
            lo=Vector(tuple(min(v[j] for v in component) for j in range(3)));hi=Vector(tuple(max(v[j] for v in component) for j in range(3)));center=(lo+hi)*.5
            radial=Vector((center.x,center.y,0));radius=radial.length
            if not (.5<center.z<3.5 and abs(radius-facade_radius)<.6):continue
            radial.normalize()
            # Emissive backing lies 42cm behind the front. Moving 70cm inward
            # puts the emitter 28cm outside the wall, clear of glass and curtains.
            location=center-radial*.70;target=center-radial*2.70;target.z=.16
            emitter=area('Warm inhabited ground floor window',location,target,32,1.10)
            emitter.data.shape='RECTANGLE';emitter.data.size=1.10;emitter.data.size_y=.80;emitter.data.color=(1,.61,.28)
            report.append({'facade':'North' if facade_radius==27 else 'West','windowCenterBlender':[round(float(v),4) for v in center], 'radius':round(radius,4),'lightBlender':[round(float(v),4) for v in location],'watts':32})
    (ROOT/'.dream-loop/window-spill-report.json').write_text(json.dumps(report,indent=2))
    print('WARM WINDOW SPILL',len(report),'lights', {side:sum(v['facade']==side for v in report) for side in ['North','West']},flush=True)
    return report

window_spills=add_warm_window_spill()

# Local warm shop spill at the new street arrival. Three.js Y-up
# (-21.624, 2.463, -21.240) -> Blender east/north/up below.
shop_spill=point('Hornets Livs warm shop spill',-21.624,21.240,2.463,190,.20)
shop_spill.data.color=(1,.63,.31)

lamps=json.loads((ROOT/'src/layout.json').read_text())['lamps']
for i,(x,gz,h,power) in enumerate(lamps):
    y=-gz
    if i<3:
        cylinder('Art column stone base',(x,y,.22),.43,.2,iron)
        cylinder('Art column cap',(x,y,h-.18),.4,.14,iron)
        # Four vertical amber luminous faces reproduce the actual tall light source.
        for j in range(4):
            a=j*math.pi/2;dx=math.cos(a);dy=math.sin(a)
            light=area('Art column panel',(x+dx*.245,y+dy*.245,h*.50),(x+dx*3,y+dy*3,h*.35),55,.50)
            light.data.shape='RECTANGLE';light.data.size=.40;light.data.size_y=h-.75
            aa=a+math.pi/4;cube('Column slender metal corner',(x+math.cos(aa)*.345,y+math.sin(aa)*.345,h/2),(.045,.045,h-.4),iron)
    else:
        cylinder('Street lamp post',(x,y,h/2),.07,h,iron)
        cylinder('Street lamp foot',(x,y,.12),.22,.24,iron)
        # Low-radius source preserves crisp but physically softened branch shadows.
        point('Amber street lantern',x,y,h+.17,440*power,.09)
        cylinder('Lantern top cap',(x,y,h+.49),.31,.13,iron)

# The authored curb is part of the bake, for contact shadows and the raised island.
for j in range(140):
    a=j*math.tau/140;x=math.sin(a)*11;y=-math.cos(a)*14
    o=cube('Individual granite curb',(x,y,.11),(.55,.25,.22),stone)
    o.rotation_euler.z=-math.atan2(14*math.sin(a),11*math.cos(a))

verts=[];faces=[];N=256
# Road ring maps exactly to a 130 m square, its centre removed to avoid UV overlaps.
for j in range(N):
    a=j*math.tau/N;cs=math.cos(a);sn=math.sin(a)
    ext=65/max(abs(cs),abs(sn));verts.extend([(11*cs,14*sn,0),(ext*cs,ext*sn,0)])
for j in range(N):
    k=(j+1)%N;faces.append((j*2,j*2+1,k*2+1,k*2))
center=len(verts);verts.append((0,0,.14));start=len(verts)
for j in range(N):
    a=j*math.tau/N;verts.append((11*math.cos(a),14*math.sin(a),.14))
for j in range(N):faces.append((center,start+j,start+(j+1)%N))
data=bpy.data.meshes.new('World-space UV bake target');data.from_pydata(verts,[],faces);data.update()
uv=data.uv_layers.new(name='GroundLightUV')
for p in data.polygons:
    for li in p.loop_indices:
        v=data.vertices[data.loops[li].vertex_index].co
        uv.data[li].uv=((v.x+65)/130,(v.y+65)/130)
target=bpy.data.objects.new('GROUND IRRADIANCE BAKE TARGET',data);scene.collection.objects.link(target)
mat=simple_material('Pure white diffuse bake target',(1,1,1),1);target.data.materials.append(mat)
img=bpy.data.images.new('Ground irradiance linear',width=2048,height=2048,alpha=False,float_buffer=True)
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;mat.node_tree.nodes.active=node;node.select=True
scene.render.bake.margin=2;scene.render.bake.use_clear=True
scene.render.bake.use_pass_direct=True;scene.render.bake.use_pass_indirect=True;scene.render.bake.use_pass_color=False
bpy.ops.object.select_all(action='DESELECT');target.select_set(True);bpy.context.view_layer.objects.active=target
if '--prepare-only' in sys.argv:
    print('PREPARED ONLY, no bake started',len(window_spills),'window spills; assets',bake_assets,flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/lighting-prepared.blend'))
    sys.exit(0)

print('BAKING 2048x2048, 32 samples, direct + indirect diffuse, colour disabled',flush=True)
bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT','INDIRECT'})

# Save using Standard display transform, so PNG's encoded values are conventional
# sRGB. TextureLoader + SRGBColorSpace decodes them back to linear irradiance.
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='16'
denoise_bake(img)
img.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/lighting.blend'))
import numpy as np
pixels=np.array(img.pixels[:],dtype=np.float32).reshape(-1,4)[:,:3]
print('LINEAR IRRADIANCE stats p0,p50,p90,p99,max',np.percentile(pixels,[0,50,90,99,100],axis=0).tolist(),flush=True)
print('BAKE COMPLETE',round(time.time()-START,1),'seconds. PNG: 16-bit sRGB. UV=(X+65,65-Z)/130.',flush=True)
