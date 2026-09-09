"""Low park railings around the five planting footprints in src/layout.json.
Original Blender geometry. Rails sit on the blocked side of existing paths.
"""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
layout=json.loads((ROOT/'src/layout.json').read_text())
mat=bpy.data.materials.new('Weathered sage black park iron');mat.use_nodes=True
p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.115,.145,.122,1);p.inputs['Metallic'].default_value=.58;p.inputs['Roughness'].default_value=.69

def tube(a,b,r):
 a,b=Vector(a),Vector(b)
 bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=(b-a).length,location=(a+b)/2)
 o=bpy.context.object;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

def fence(name,points):
 parts=[];lengths=[math.dist(points[i],points[(i+1)%len(points)]) for i in range(len(points))];total=sum(lengths)
 for i,(x,z) in enumerate(points):
  xx,zz=points[(i+1)%len(points)]
  for h,r in [(.43,.018),(.735,.026)]:parts.append(tube((x,-z,h),(xx,-zz,h),r))
 count=math.ceil(total/1.08)
 for k in range(count):
  d=k*total/count;i=0
  while d>lengths[i] and i<len(points)-1:d-=lengths[i];i+=1
  f=d/lengths[i];a=points[i];b=points[(i+1)%len(points)];x=a[0]+(b[0]-a[0])*f;z=a[1]+(b[1]-a[1])*f
  parts.append(tube((x,-z,.155),(x,-z,.80),.035))
  for h in [.19,.735]:parts.append(tube((x,-z,h-.016),(x,-z,h+.016),.046))
  bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=.038,location=(x,-z,.80));o=bpy.context.object;o.data.materials.append(mat);parts.append(o)
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 # Keep the export at five draw calls, with no transparent or animated materials.
 for poly in o.data.polygons:poly.material_index=0
 while len(o.data.materials)>1:o.data.materials.pop(index=len(o.data.materials)-1)
 return o
objects=[]
for i,b in enumerate(layout['beds']):
 pts=[]
 for k in range(96):
  a=k*math.tau/96;x=(b['rx']-.04)*math.cos(a);z=(b['rz']-.04)*math.sin(a);c=math.cos(b['angle']);s=math.sin(b['angle']);pts.append((b['x']+x*c-z*s,b['z']+x*s+z*c))
 objects.append(fence(f'IslandFence_Central_{i+1}',pts))
for i,b in enumerate(layout['borderBeds']):
 pts=[]
 for outer,indices in [(True,range(81)),(False,range(80,-1,-1))]:
  for k in indices:
   a=b['start']+(b['end']-b['start'])*k/80;rx=b['outerRx']-.04 if outer else b['innerRx']+.04;rz=b['outerRz']-.04 if outer else b['innerRz']+.04
   pts.append((rx*math.sin(a),rz*math.cos(a)))
 objects.append(fence(f'IslandFence_Border_{i+1}',pts))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/island-fences.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/island-fences.blend'))
tri=0
for o in objects:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
print('FENCE_RESULT',len(objects),'meshes',tri,'triangles',flush=True)
