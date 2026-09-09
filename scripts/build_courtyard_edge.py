"""Small original courtyard edge beyond the southwest pavement: low masonry,
slender railings, an authored parked bicycle and quiet utility details.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'scripts/build_props.py').read_text().split('with open(os.path.join(BASE,\'src/layout.json\'))')[0]
exec(compile(source,str(ROOT/'scripts/build_props.py'),'exec'))
from collections import defaultdict
with bpy.data.libraries.load(str(ROOT/'.dream-loop/environment.blend'),link=False) as (src,dst):dst.materials=[n for n in ['Brick','Stone_Dark','Stone_Trim'] if n in src.materials]
mm={m.name:m for m in dst.materials};brick=mm['Brick'];stone=mm['Stone_Dark'];cap=mm['Stone_Trim']
gravel=mat('Courtyard worn aggregate',(.125,.132,.116),.99)
# Original generated dark aggregate/soil litter gives the closed courtyard a
# physical surface instead of a blank color plane.
im=bpy.data.images.load(str(ROOT/'public/assets/soil-autumn.png'));im.pack();tx=gravel.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;gravel.node_tree.links.new(tx.outputs['Color'],gravel.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
wood=mat('Courtyard faded timber',(.13,.085,.040),.95)
a=math.radians(230);d=Vector((math.cos(a),math.sin(a),0));l=Vector((-math.sin(a),math.cos(a),0))
def P(t,b,z=0):return d*t+l*b+Vector((0,0,z))
def rootat(name,t,b,z=0,ang=a):
 q=P(t,b,z);p=root(name,q.x,-q.y);p.location.z=z;p.rotation_euler.z=ang;return p
wall=rootat('Courtyard_Edge_Masonry',38,7.78,.02)
cube('Continuous low brick courtyard wall',(0,0,.40),(22.0,.37,.80),brick,wall,.01)
# Lightly varied capstone lengths follow the whole wall without a new entrance.
for i in range(34):cube('Individual courtyard coping',(-10.67+i*.646,0,.835),(.636,.52,.11),cap,wall,.014)
# Mortar courses are restrained recesses against a warm brick surface.
for z in [.12,.245,.37,.495,.62,.745]:mesh('Masonry horizontal mortar',[(-10.99,-.190,z-.0045),(10.99,-.190,z-.0045),(10.99,-.190,z+.0045),(-10.99,-.190,z+.0045)],[(0,1,2,3)],stone,wall)
for row in range(6):
 z=.057+row*.125
 for i in range(75):
  x=-10.85+i*.292+(.146 if row%2 else 0)
  if x<10.97:mesh('Staggered masonry bed joint',[(x-.004,-.191,z-.057),(x+.004,-.191,z-.057),(x+.004,-.191,z+.057),(x-.004,-.191,z+.057)],[(0,1,2,3)],stone,wall)
for x in [-10.6,-6.35,-2.1,2.15,6.4,10.6]:
 cube('Low courtyard brick pier',(x,0,.66),(.54,.54,1.32),brick,wall,.012)
 cube('Courtyard pier granite cap',(x,0,1.34),(.67,.67,.13),cap,wall,.018)
 # Rounded finial is subdued dark metal rather than an illuminated orb.
 orb('Courtyard fence post finial',(x,0,1.48),(.051,.051,.064),iron,wall)
for z in [.96,1.27]:rod('Continuous dark iron fence rail',(-10.7,0,z),(10.7,0,z),.016,iron,wall,8)
for i in range(117):
 x=-10.58+i*.182
 rod('Slender courtyard railing upright',(x,0,.87),(x,0,1.30),.007,iron,wall,6)
# A short return makes a planted courtyard volume rather than a line into black.
ret=rootat('Courtyard_Edge_Return',27,13.53,.02,ang=a+math.pi/2)
cube('Low return brick wall',(0,0,.37),(11.45,.36,.74),brick,ret,.01)
for i in range(18):cube('Return coping block',(-5.37+i*.633,0,.76),(.622,.50,.10),cap,ret,.012)
# Inner courtyard is a subdued gravel rectangle, with a small offset paved strip.
yard=rootat('Courtyard_Edge_Ground',38,14.25,.018)
cube('Inset courtyard gravel ground',(0,0,0),(21.95,12.45,.026),gravel,yard,.002)
for i in range(19):
 for j in range(3):cube('Old courtyard stepping slab',(-9+i*.98,-4.9+j*.49,.031),(.95,.465,.042),stone,yard,.008)
# One recognizable, fully authored city bicycle sits inside the courtyard edge.
q=P(31.0,8.22,.06);bike=bicycle(q.x,-q.y,a+.09);bike.name='Courtyard_Edge_Bicycle';bike.location.z=.06
# Raised timber herb bed with bare dormant stems supplies depth behind railings.
for t,b in [(34.4,10.3),(41.6,11.8)]:
 bed=rootat('Courtyard_Edge_DormantBed',t,b,.04)
 for y in [-.65,.65]:
  for z in [.075,.19]:cube('Raised-bed weathered timber',(0,y,z),(2.4,.055,.105),wood,bed,.004)
 for x in [-1.18,1.18]:
  for z in [.075,.19]:cube('Raised-bed corner timber',(x,0,z),(.055,1.3,.105),wood,bed,.004)
 cube('Dormant soil surface',(0,0,.115),(2.34,1.24,.10),gravel,bed,.003)
 for i in range(21):
  x=random.uniform(-1.08,1.08);y=random.uniform(-.53,.53);h=random.uniform(.13,.35)
  rod('Dry dormant stalk',(x,y,.18),(x+.021,y+.018,.18+h),.0034,wood,bed,5)
  for s in [-1,1]:rod('Sparse dry side shoot',(x+.012,y+.009,.25+h*.4),(x+s*.07,y+.035,.29+h*.4),.002,wood,bed,4)
# Existing courtyard services: three simple wheeled bins clustered against return.
for i in range(3):
 p=rootat('Courtyard_Edge_WheeledBin',28.1,9.4+i*.73,.05)
 cube('Tapered bin body',(0,0,.46),(.50,.55,.87),boxgreen,p,.04)
 cube('Hinged bin lid',(0,0,.93),(.56,.60,.08),iron,p,.025)
 for x in [-.205,.205]:
  tube('Bin molded rubber wheel',[(x,-.21+.075*math.cos(j*math.tau/18),.095+.075*math.sin(j*math.tau/18)) for j in range(19)],.022,rubber,p,8)
  rod('Wheel axle',(x-.022,-.21,.095),(x+.022,-.21,.095),.022,iron,p,8)
 cube('Small recycling label',(0,-.292,.70),(.15,.003,.12),white,p,.003)
# Batch every material once. Geometry stays outside all playable coordinates.
bpy.context.view_layer.update();parts=defaultdict(lambda:[[],[]])
for ob in list(bpy.context.scene.objects):
 if ob.type!='MESH':continue
 for idx,m in enumerate(ob.data.materials):
  faces=[tuple(p.vertices) for p in ob.data.polygons if p.material_index==idx]
  if not faces:continue
  vs,fs=parts[m];offset=len(vs);vs.extend(tuple(ob.matrix_world@v.co) for v in ob.data.vertices);fs.extend(tuple(i+offset for i in f) for f in faces)
for ob in list(bpy.context.scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
triangles=0
for m,(verts,faces) in parts.items():
 me=bpy.data.meshes.new('Courtyard_Edge_'+m.name);me.from_pydata(verts,[],faces);me.materials.append(m);me.update();uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  axis=max(range(3),key=lambda i:abs(p.normal[i]))
  for li in p.loop_indices:
   q=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(q[(axis+1)%3]*2.0,q[(axis+2)%3]*2.0)
 ob=bpy.data.objects.new('Courtyard_Edge_'+m.name,me);bpy.context.collection.objects.link(ob)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();me.calc_loop_triangles();triangles+=len(me.loop_triangles)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/courtyard-edge.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/courtyard-edge.glb'),export_format='GLB',export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
print('COURTYARD RESULT',len(parts),'draws',triangles,'triangles')
