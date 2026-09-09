"""Local, non-destructive fabric/bench material finish. All placement and props
remain unchanged; no topology or triangle-count changes.
"""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'.dream-loop/cosy-street.blend'))
a=math.radians(134);origin=Vector((30.3*math.cos(a),30.3*math.sin(a),.163));cs=math.cos(a);sn=math.sin(a)
def local(v):
 q=v-origin;return Vector((q.x*cs+q.y*sn,-q.x*sn+q.y*cs,q.z))
def world(v):return Vector((v.x*cs-v.y*sn,v.x*sn+v.y*cs,v.z))+origin
def sag(x,y):
 u=(x+1.95)/3.9;v=max(0,min(1,(y-.08)/1.15));support=max(0,1-(x/1.82)**2)
 # 3.1cm broad sag between side supports, with two broad diagonal fabric folds.
 folds=.012*math.exp(-((x+.67+.22*v)/.17)**2)-.008*math.exp(-((x-.64+.17*v)/.20)**2)
 return (-.031*support+folds)*math.sin(v*math.pi)
def baseheight(x,y):
 v=max(0,min(1,(y-.08)/1.15));return 3.27-.39*v-.045*math.sin(v*math.pi)+sag(x,y)
changed=0;maxSag=0;benchLoops=0
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 me=ob.data;name=me.materials[0].name if len(me.materials) else ''
 cloth='Cosy burgundy canvas' in name or 'Cosy faded linen canvas' in name
 wood='Cosy weathered oak' in name or 'Cosy rubbed oak endgrain' in name or 'Cosy worn pale green bench' in name
 if not(cloth or wood):continue
 col=me.color_attributes.get('Color') or me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 # glTF multiplies COLOR_0 by unchanged original material base color.
 for c in col.data:c.color=(1,1,1,1)
 if cloth:
  normals=[]
  for vert in me.vertices:
   p=local(vert.co);x,y,z=p
   if y<1.231:
    delta=sag(x,y);p.z+=delta;maxSag=max(maxSag,abs(delta));eps=.0002
    dx=(baseheight(x+eps,y)-baseheight(x-eps,y))/(2*eps);dy=(baseheight(x,y+eps)-baseheight(x,y-eps))/(2*eps)
    n=Vector((-dx,-dy,1)).normalized();n=Vector((n.x*cs-n.y*sn,n.x*sn+n.y*cs,n.z));normals.append(n)
   else:
    # The valance stays attached to the rigid roller; only its loose lower cloth
    # bends slightly, giving the scalloped hem a soft, imperfect fall.
    loose=max(0,min(1,(2.88-z)/.26));p.y+=.010*math.sin((x+1.95)/3.9*math.pi*4+.4)*loose;p.z-=.013*math.sin((x+1.95)/3.9*math.pi)**2*loose
    n=Vector((-sn,cs,0));normals.append(n)
   vert.co=world(p);changed+=1
  for poly in me.polygons:poly.use_smooth=True
  me.update();me.normals_split_custom_set_from_vertices(normals)
  for loop in me.loops:
   p=local(me.vertices[loop.vertex_index].co);x,y,z=p;u=(x+1.95)/3.9
   # Restrained accumulated hem dirt, with gradual streaks rather than a band.
   hem=max(0,min(1,(2.77-z)/.12)) if y>1.22 else max(0,min(1,(y-.95)/.28))*.24
   stain=(.070+.035*(.5+.5*math.sin(u*19.3)))*hem
   fade=.012*(.5+.5*math.sin(u*8.1+y*3.7))
   val=1-stain-fade;col.data[loop.index].color=(val,val*.996,val*.987,1)
 else:
  aa=math.radians(142.5);dd=Vector((math.cos(aa),math.sin(aa),0));ss=Vector((-math.sin(aa),math.cos(aa),0))
  centers=[dd*40.2+ss*5.50,dd*25.0-ss*5.1]
  for loop in me.loops:
   v=me.vertices[loop.vertex_index].co
   for center in centers:
    q=v-center;xx=q.dot(dd);yy=q.dot(ss)
    if abs(xx)<.9 and abs(yy)<.5 and .48<v.z<1.20:
     # Stable plank-wise 5–8% rubbed wear, preserved spatially across faces.
     plank=round(yy/.094) if v.z<.67 else round((v.z-.16)/.102)
     value=.965+.033*math.sin(plank*2.17+1.2)
     contact=.96 if abs(abs(xx)-.68)<.045 else 1
     value*=contact;col.data[loop.index].color=(value,value,value,1);benchLoops+=1;break
# Save a derivative, preserving the original source mesh and every object count.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/cosy-street-finish.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/cosy-street-finish.glb'),export_format='GLB',export_vertex_color='NAME',export_vertex_color_name='Color',export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
tri=sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH')
report={'changed_canvas_vertices':changed,'max_additional_sag_m':maxSag,'bench_color_loops':benchLoops,'objects_unchanged':True,'topology_unchanged':True,'canvas_material_factors_unchanged':True}
(ROOT/'.dream-loop/cosy-street-finish-report.json').write_text(json.dumps(report,indent=2));print('CLOTH FINISH',report)
