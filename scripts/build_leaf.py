import bpy,math,os,random,bmesh
from mathutils import Vector
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
random.seed(773)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
def mat(name,c,r=1,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=r;p.inputs['Metallic'].default_value=metal;return m
leafmat=mat('Dry dark brown autumn leaf',(1,1,1),1)
leafmat.use_backface_culling=False
n=leafmat.node_tree.nodes.new('ShaderNodeVertexColor');n.layer_name='Color';leafmat.node_tree.links.new(n.outputs['Color'],leafmat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
iron=mat('Oxidized utility iron',(.065,.076,.069),.89,.64)
ridge=mat('Worn utility iron relief',(.098,.111,.101),.76,.68)
dark=mat('Drain opening shadow',(.009,.012,.01),1)

def mesh(name,verts,faces,m):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(m);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return o
# Thin tessellated leaf: alternating serrated lobes, curved spine, asymmetric raised edges.
vs=[];fs=[];cs=[]
profile=[(-.059,.003),(-.052,.015),(-.046,.010),(-.040,.027),(-.032,.021),(-.023,.040),(-.015,.026),(-.005,.045),(.006,.024),(.016,.036),(.026,.018),(.039,.027),(.049,.010),(.068,0)]
for i,(y,w) in enumerate(profile):
 t=i/(len(profile)-1);center=.0025+.006*math.sin(t*math.pi)+.026*t**5
 for side in [-1,0,1]:
  x=side*w*(1 if side<0 else .86+.07*math.sin(i*1.13))
  zz=center+(abs(side)*(.003+ .006*math.sin(t*math.pi*1.4+side*.7)))
  if side==0:zz+=.0012
  vs.append((x,y+(side*.0013*math.sin(i*1.7) if side else 0),zz));tone=.72+.22*random.random()+(.10 if side==0 else 0);cs.append((.225*tone,.135*tone,.061*tone,1))
for i in range(len(profile)-1):
 for j in [0,1]:a=i*3+j;fs.extend([(a,a+1,a+4),(a,a+4,a+3)])
# Integrated narrow central rib, represented by two-triangle tapered strips.
for i in range(len(profile)-1):
 y0,w0=profile[i];y1,w1=profile[i+1];z0=vs[i*3+1][2]+.00035;z1=vs[(i+1)*3+1][2]+.00035;hw=.00085*(1-i/len(profile))
 a=len(vs);vs.extend([(-hw,y0,z0),(hw,y0,z0),(hw*.88,y1,z1),(-hw*.88,y1,z1)]);fs.extend([(a,a+1,a+2),(a,a+2,a+3)]);cs.extend([(.13,.083,.037,1)]*4)
# Four fine branched veins follow the lobes; no alpha rectangles.
for i in [3,5,7,10]:
 for side in [-1,1]:
  start=Vector(vs[(i-1)*3+1]);end=Vector(vs[i*3+(0 if side<0 else 2)]);end=start+(end-start)*.88;start.z+=.00065;end.z+=.00065
  tangent=(end-start).normalized();perp=Vector((-tangent.y,tangent.x,0))*.00045;a=len(vs);vs.extend([start-perp,start+perp,end]);fs.append((a,a+1,a+2));cs.extend([(.125,.076,.033,1)]*3)
# Tapered twisted petiole in the same mesh and same material.
a=len(vs)
for y,z,r in [(-.081,.0018,.0009),(-.071,.003,.0012),(-.057,.004,.0014)]:
 for j in range(5):vs.append((r*math.cos(j*math.tau/5),y,z+r*math.sin(j*math.tau/5)));cs.append((.12,.073,.031,1))
for i in range(2):
 for j in range(5):b=a+i*5+j;c=a+i*5+(j+1)%5;fs.extend([(b,c,c+5),(b,c+5,b+5)])
ground_z=min(v[2] for v in vs)
vs=[(v[0],v[1]+.0065,v[2]-ground_z) for v in vs]
leaf=mesh('DryLeaf',vs,fs,leafmat)
colors=leaf.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
for d,c in zip(colors.data,cs):d.color=c
leaf.data.color_attributes.active_color=colors
for p in leaf.data.polygons:p.use_smooth=True

# Optional local-origin low-poly covers. These are separate meshes, never part of the leaf instancing mesh.
def cube(name,loc,size,m):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;o.location=loc;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);return o
def ring(name,r,width,z,depth,m,N=40):
 v=[];f=[]
 for zz,rr in [(z-depth/2,r-width/2),(z-depth/2,r+width/2),(z+depth/2,r-width/2),(z+depth/2,r+width/2)]:
  for j in range(N):v.append((rr*math.cos(j*math.tau/N),rr*math.sin(j*math.tau/N),zz))
 for j in range(N):
  q=(j+1)%N;f.extend([(j,q,q+2*N,j+2*N),(j+N,j+3*N,q+3*N,q+N),(j+2*N,q+2*N,q+3*N,j+3*N)])
 return mesh(name,v,f,m)
def join(objs,name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 mats=[];mapping={}
 for i,m in enumerate(o.data.materials):
  if m not in mats:mats.append(m)
  mapping[i]=mats.index(m)
 inds=[mapping[p.material_index] for p in o.data.polygons];o.data.materials.clear()
 for m in mats:o.data.materials.append(m)
 for p,i in zip(o.data.polygons,inds):p.material_index=i
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free();return o
objs=[]
bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.49,depth=.015,location=(0,0,.0075));o=bpy.context.object;o.data.materials.append(iron);objs.append(o)
objs.extend([ring('Outer cast metal rim',.487,.023,.019,.013,ridge),ring('Engraved ring',.439,.008,.018,.005,ridge),ring('Center cast emblem rim',.105,.008,.018,.005,ridge)])
for j in range(16):
 a=j*math.tau/16
 for rr in [.20,.30,.39]:
  o=cube('Raised anti-slip hatch',(rr*math.cos(a),rr*math.sin(a),.019),(.043,.009,.006),ridge);o.rotation_euler.z=a+.6;objs.append(o)
# A simple original cast municipal star/flower emblem.
for j in range(6):
 a=j*math.tau/6;o=cube('Cast central flower emblem',(.045*math.cos(a),.045*math.sin(a),.019),(.07,.013,.005),ridge);o.rotation_euler.z=a;objs.append(o)
for x in [-.37,.37]:objs.append(cube('Recessed lifting slot',(x,0,.016),(.035,.067,.003),dark))
cover=join(objs,'UtilityCover')
objs=[cube('Dark drain recess',(0,0,.004),(.68,.33,.008),dark)]
for x in [-.335,.335]:objs.append(cube('Cast drain side frame',(x,0,.015),(.03,.35,.03),iron))
for y in [-.16,.16]:objs.append(cube('Cast drain end frame',(0,y,.015),(.67,.03,.03),iron))
for i in range(10):
 x=-.282+i*.0625;objs.append(cube('Heavy cast drain grille bar',(x,0,.016),(.019,.305,.027),ridge))
objs.append(cube('Drain center reinforcement',(0,0,.012),(.64,.017,.022),iron))
for x in [-.328,.328]:
 for y in [-.14,.14]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.006,depth=.003,location=(x,y,.031));o=bpy.context.object;o.data.materials.append(ridge);objs.append(o)
drain=join(objs,'StreetDrain')
bpy.ops.object.select_all(action='DESELECT')
for o in [leaf,cover,drain]:o.select_set(True)
bpy.context.view_layer.objects.active=leaf
bpy.ops.export_scene.gltf(filepath=os.path.join(BASE,'public/assets/leaf.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
for o in [leaf,cover,drain]:o.data.calc_loop_triangles();print('ASSET_RESULT',o.name,len(o.data.loop_triangles),'triangles',len(o.data.materials),'materials')
# Build source and isolated close-up verification.
cover.hide_render=True;drain.hide_render=True
world=bpy.context.scene.world or bpy.data.worlds.new('Studio');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.105,.12,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
bpy.ops.object.light_add(type='AREA',location=(.1,-.1,.2));o=bpy.context.object;o.data.energy=2;o.data.size=.15;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.08,-.14,.19));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.005))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.20;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.filepath=os.path.join(BASE,'.dream-loop/leaf-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE,'.dream-loop/leaf.blend'));bpy.ops.render.render(write_still=True)
