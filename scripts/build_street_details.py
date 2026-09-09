import bpy, math, random, os, bmesh
from mathutils import Vector
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
random.seed(44)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
def mat(n,c,r=.75,metal=0):
 m=bpy.data.materials.new(n);m.use_nodes=True;m.diffuse_color=(*c,1);s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*c,1);s.inputs['Roughness'].default_value=r;s.inputs['Metallic'].default_value=metal;return m
cream=mat('Weathered reflective cream enamel',(.69,.66,.51),.39,.14)
red=mat('Municipal red reflective panels',(.48,.044,.027),.36,.13)
metal=mat('Aged galvanized barrier steel',(.26,.29,.27),.55,.8)
black=mat('Black rubber and street lettering',(.022,.028,.025),.86)
blue=mat('Deep blue street name enamel',(.024,.057,.115),.47,.35)
orange=mat('Road cone aged orange vinyl',(.64,.135,.033),.69)
bark=mat('Wet fallen twig bark',(.058,.044,.027),.92)
roots=[]
def root(n,x,z,ang=0):
 o=bpy.data.objects.new(n,None);bpy.context.collection.objects.link(o);o.location=(x,-z,0);o.rotation_euler.z=ang;roots.append(o);return o
def mesh(n,vs,fs,m,p):
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.materials.append(m);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);o.parent=p
 for f in me.polygons:f.use_smooth=True
 return o
def cube(n,loc,size,m,p,bevel=.008):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=n;o.parent=p;o.location=loc;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  b=o.modifiers.new('Soft worn edges','BEVEL');b.width=bevel;b.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
  w=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=w.name)
 return o
def tube(n,pts,r,m,p,seg=7):
 vs=[];fs=[]
 for i,pt in enumerate(pts):
  v=Vector(pt);t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)]);t.normalize();u=t.cross(Vector((0,0,1)))
  if u.length<.01:u=t.cross(Vector((0,1,0)))
  u.normalize();w=t.cross(u).normalized()
  for j in range(seg):vs.append(v+r*(math.cos(j*math.tau/seg)*u+math.sin(j*math.tau/seg)*w))
 for i in range(len(pts)-1):
  for j in range(seg):a=i*seg+j;b=i*seg+(j+1)%seg;fs.append((a,b,b+seg,a+seg))
 fs.extend([tuple(range(seg-1,-1,-1)),tuple((len(pts)-1)*seg+j for j in range(seg))]);return mesh(n,vs,fs,m,p)
def rod(n,a,b,r,m,p,seg=8):return tube(n,[a,b],r,m,p,seg)
def disc(n,loc,r,depth,m,p,rot=(0,0,0),verts=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth);o=bpy.context.object;o.name=n;o.parent=p;o.location=loc;o.rotation_euler=rot;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def text(n,string,loc,size,m,p):
 c=bpy.data.curves.new(n,'FONT');c.body=string;c.size=size;c.align_x='CENTER';c.extrude=.0002;c.resolution_u=1;o=bpy.data.objects.new(n,c);bpy.context.collection.objects.link(o);o.parent=p;o.location=loc;o.rotation_euler=(math.pi/2,0,0);c.materials.append(m);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o.select_set(False);return o

def barrier(x,z,sign=False):
 nx=x/(19.5**2);nz=z/(22.5**2);ang=math.atan2(-nx,-nz);p=root('Municipal A-frame exit barrier',x,z,ang)
 width=3.4
 # two fold-out A supports and cross-tie with retained pivot bolts
 for xx in [-1.33,1.33]:
  for sy in [-1,1]:
   rod('Folding galvanized leg',(xx,sy*.27,.028),(xx,0,.82),.024,metal,p)
   cube('Stable rubber foot',(xx,sy*.27,.025),(.145,.16,.05),black,p,.012)
  rod('A-frame spreader',(xx,-.165,.29),(xx,.165,.29),.014,metal,p)
  disc('Pivot bolt',(xx,-.043,.76),.027,.015,metal,p,(math.pi/2,0,0),12)
 rod('Low lateral stabilizer',(-1.33,.10,.20),(1.33,.10,.20),.013,metal,p)
 cube('Cream reflective upper board',(0,0,.716),(width,.062,.25),cream,p,.014)
 cube('Cream reflective lower board',(0,.018,.345),(width,.046,.115),cream,p,.01)
 # clipped diagonal retroreflective red stripes, both faces
 for yy in [-.033,.033]:
  for k in range(9):
   xa=-1.63+k*.39;xb=xa+.17
   vs=[(xa,yy,.593),(xb,yy,.593),(xb+.17,yy,.839),(xa+.17,yy,.839)]
   if max(v[0] for v in vs)>1.69:continue
   mesh('Diagonal red reflective stripe',vs,[(0,1,2,3)] if yy<0 else [(3,2,1,0)],red,p)
  for k in range(7):
   xx=-1.45+k*.46
   cube('Lower red warning patch',(xx,yy,.345),(.18,.001,.092),red,p,.001)
 for xx in [-1.52,1.52]:
  for zz in [.642,.792]:disc('Board fixing screw',(xx,-.039,zz),.009,.009,metal,p,(math.pi/2,0,0),8)
 # chipped labels and paper notices, small physical signs only
 cube('Peeling municipal sticker',(.93,-.039,.712),(.31,.004,.075),cream,p,.003)
 text('Municipal board ownership','MALMÖ STAD',(.93,-.042,.698),.031,black,p)
 if sign:
  cube('Suspended path closure plate',(0,-.025,.44),(.65,.033,.25),cream,p,.012)
  for xx in [-.24,.24]:rod('Sign suspension hook',(xx,-.03,.56),(xx,-.03,.605),.005,metal,p,6)
  text('Swedish pedestrian closure heading','GÅNGVÄG',(0,-.045,.467),.063,black,p)
  text('Swedish pedestrian closure instruction','AVSTÄNGD',(0,-.045,.379),.060,black,p)
 return p

def cone(x,z):
 p=root('Aged traffic cone',x,z)
 cube('Square heavy rubber cone foot',(0,0,.021),(.33,.33,.042),black,p,.028)
 # tapered orange cone with molded reflective cuff
 for zz0,zz1,r0,r1,m in [(.041,.22,.129,.085,orange),(.22,.315,.085,.063,cream),(.315,.46,.063,.027,orange)]:
  vs=[];fs=[];N=18
  for zz,rr in [(zz0,r0),(zz1,r1)]:
   for i in range(N):vs.append((rr*math.cos(i*math.tau/N),rr*math.sin(i*math.tau/N),zz))
  for i in range(N):fs.append((i,(i+1)%N,(i+1)%N+N,i+N))
  mesh('Molded tapered cone section',vs,fs,m,p)
 disc('Open cone dark top',(0,0,.455),.022,.004,black,p)
 return p

def streetpost(x,z,label,yaw=0):
 p=root('Street name post '+label,x,z,yaw)
 disc('Concrete post socket',(0,0,.055),.13,.11,metal,p,verts=12)
 rod('Galvanized round street sign pole',(0,0,.04),(0,0,2.58),.034,metal,p,12)
 disc('Rounded pole cap',(0,0,2.59),.038,.025,metal,p)
 length=max(1.12,len(label)*.065)
 cube('Pressed blue streetname plaque',(0,-.039,2.35),(length,.033,.22),blue,p,.02)
 # thin enamel cream border strips
 for zz in [2.253,2.447]:cube('White plaque border',(0,-.059,zz),(length-.05,.004,.009),cream,p,.003)
 for xx in [-length/2+.023,length/2-.023]:cube('White plaque border',(xx,-.059,2.35),(.009,.004,.19),cream,p,.003)
 text('Swedish street name',label,(0,-.063,2.316),.083,cream,p)
 for xx in [-.085,.085]:disc('Street plaque screw',(xx,-.064,2.415),.006,.008,metal,p,(math.pi/2,0,0),8)
 return p

def can(x,z,i):
 p=root('Small discarded can',x,z,random.random()*math.tau);p.rotation_euler.x=math.pi/2+.15
 # grounded on curved side after rotation, origin z adjusted
 p.location.z=.177
 m=red if i%2 else metal
 disc('Aluminium drink can',(0,0,.063),.031,.116,m,p,verts=14)
 for zz in [.006,.12]:disc('Rolled aluminium can seam',(0,0,zz),.032,.006,metal,p,verts=14)
 disc('Can lid',(0,0,.124),.029,.003,metal,p,verts=14)
 disc('Dark drink opening',(.009,0,.127),.009,.002,black,p,verts=10)
 # pull ring and cream band
 disc('Can cream label ring',(0,0,.06),.0315,.035,cream,p,verts=14)
 return p

def twig(x,z,i):
 p=root('Fallen autumn twig',x,z,random.random()*math.tau);p.location.z=.017+(0.14 if x*x/12**2+z*z/14**2<1 else 0)
 length=random.uniform(.25,.64);pts=[(-length*.5,0,0),(-length*.15,.03,.01),(length*.15,-.016,.008),(length*.5,.018,.01)]
 tube('Split wet twig stem',pts,.007,bark,p,5)
 for xx,sg in [(-length*.13,1),(length*.13,-1)]:rod('Tiny twig branching tip',(xx,0,.006),(xx+.11,sg*.13,.013),.004,bark,p,5)
 return p

barrier(-19.5,0,True);barrier(0,22.5);barrier(0,-22.5);barrier(18,9)
cone(-19.9,2.05);cone(2.2,-22.65);cone(-2.15,22.8);cone(18.95,7.45)
streetpost(17,13,'KRISTIANSTADSGATAN',-.4);streetpost(18,-12,'NORRA PARKGATAN',.35)
for i,(x,z) in enumerate([(-8,-3),(-7.5,-3.2),(7.5,-3.6),(7.3,-3.75)]):can(x,z,i)
for i,(x,z) in enumerate([(-10,3),(-9,7),(-5,10),(5,11),(10,4),(7,-10),(-3,-11),(-11,-6),(13,7),(2,16)]):twig(x,z,i)
# Batch static details into exactly one mesh with seven material draws.
bpy.ops.object.select_all(action='DESELECT');objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name='Authored exit barriers and street details';bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
mats=[];mapping={}
for i,m in enumerate(o.data.materials):
 if m not in mats:mats.append(m)
 mapping[i]=mats.index(m)
inds=[mapping[f.material_index] for f in o.data.polygons];o.data.materials.clear()
for m in mats:o.data.materials.append(m)
for f,i in zip(o.data.polygons,inds):f.material_index=i
for r in roots:bpy.data.objects.remove(r,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.gltf(filepath=os.path.join(BASE,'public/assets/street-details.glb'),use_selection=True,export_format='GLB',export_yup=True,export_apply=True)
o.data.calc_loop_triangles();print('DETAIL_RESULT',len(o.data.loop_triangles),'triangles',len(mats),'draw calls')
# Save original source and close detail render for visual verification.
world=bpy.context.scene.world or bpy.data.worlds.new('Studio');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.17,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
for loc,power,size in [((-15,-3,5),600,4),((-20,3,5),500,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=size;l.rotation_euler=(Vector((-19.5,0,.5))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(-15.5,-3,2.7));cam=bpy.context.object;cam.rotation_euler=(Vector((-19.5,0,.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.6;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1200;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(BASE,'.dream-loop/street-details-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE,'.dream-loop/street-details.blend'));bpy.ops.render.render(write_still=True)
