import bpy, math, os, random, bmesh, json
from mathutils import Vector
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
random.seed(921)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
def mat(name,c,r=.75,metal=0,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=r;p.inputs['Metallic'].default_value=metal
 if emit:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emit
 return m
iron=mat('Weathered dark cast iron',(.043,.053,.049),.7,.75)
columniron=mat('Blackened structural column frames',(.020,.027,.025),.82,.43)
brass=mat('Oxidized brass trim',(.29,.20,.08),.53,.68)
cream=mat('Warm dirty frosted illuminated glass',(.88,.61,.28),.62,.03,.6)
# Original packed weathered-glass maps: edge grime, condensation streaks, fine variation.
import numpy as np
th,tw=512,128
yy,xx=np.mgrid[0:th,0:tw];rng=np.random.default_rng(118)
u=xx/(tw-1);v=yy/(th-1)
edge=np.exp(-u*22)+np.exp(-(1-u)*22)+.45*np.exp(-v*16)+.25*np.exp(-(1-v)*16)
cloud=.5*np.sin(xx*.071+yy*.029)+.25*np.sin(xx*.19-yy*.012)+.25*np.sin(yy*.11+xx*.048)
streak=(np.sin(xx*.71)+np.sin(xx*.21+.8))*.016*(.4+.6*v)
soft_center=np.exp(-((u-.5)/.34)**2)*(.85+.15*np.sin(v*math.pi))
factor=np.clip(.75+.31*soft_center-.25*edge+.023*cloud+streak+rng.normal(0,.009,(th,tw)),.40,1)
rgba=np.ones((th,tw,4),dtype=np.float32)
for i,c in enumerate([.88,.61,.28]):rgba[:,:,i]=np.power(c*factor,1/2.2)
im=bpy.data.images.new('Original weathered art glass',width=tw,height=th);im.colorspace_settings.name='sRGB';im.pixels.foreach_set(rgba.ravel());im.pack()
tex=cream.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
cream.node_tree.links.new(tex.outputs['Color'],cream.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
cream.node_tree.links.new(tex.outputs['Color'],cream.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'])

ink=mat('Etched charcoal illustrated silhouettes',(.082,.10,.074),.88)
rubber=mat('Weathered bicycle rubber',(.018,.023,.021),.96)
chrome=mat('Aged spoke steel',(.28,.32,.32),.39,.83)
frame=mat('Worn bottle green bicycle enamel',(.037,.102,.083),.56,.65)
saddle=mat('Cracked black saddle leather',(.036,.029,.024),.9)
red=mat('Red rear reflector',(.48,.025,.016),.28,.1)
white=mat('Paper label and reflector',(.67,.66,.53),.89)
boxgreen=mat('Faded park utility enamel',(.071,.16,.113),.88,.35)
black=mat('Speaker cabinet black felt',(.028,.029,.028),.98)
speak=mat('Speaker cones',(.065,.071,.068),.88,.14)
allroots=[]
def root(name,x,z):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=(x,-z,0);allroots.append(o);return o
def mesh(name,vs,fs,m,p):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(m);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.parent=p
 for f in me.polygons:f.use_smooth=True
 return o
def cube(name,loc,scale,m,p,bevel=.01):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;o.location=loc;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);o.parent=p
 if bevel:
  b=o.modifiers.new('Molded rounded edges','BEVEL');b.width=bevel;b.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
  w=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=w.name)
 if m==cream:
  uv=o.data.uv_layers.active or o.data.uv_layers.new(name='Glass pane UV')
  for face in o.data.polygons:
   ax=0 if abs(face.normal.y)>.5 else 1
   for li in face.loop_indices:
    co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co[ax]/scale[ax]+.5,co.z/scale[2]+.5)
 return o
def tube(name,pts,r,m,p,seg=8):
 vs=[];fs=[]
 for i,v in enumerate(pts):
  q=Vector(v);t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)]);t.normalize();u=t.cross(Vector((0,0,1)))
  if u.length<.01:u=t.cross(Vector((0,1,0)))
  u.normalize();w=t.cross(u).normalized()
  for j in range(seg):vs.append(q+r*(math.cos(j*math.tau/seg)*u+math.sin(j*math.tau/seg)*w))
 for i in range(len(pts)-1):
  for j in range(seg):a=i*seg+j;b=i*seg+(j+1)%seg;fs.append((a,b,b+seg,a+seg))
 fs.extend([tuple(range(seg-1,-1,-1)),tuple((len(pts)-1)*seg+j for j in range(seg))]);return mesh(name,vs,fs,m,p)
def rod(name,a,b,r,m,p,seg=10):return tube(name,[a,b],r,m,p,seg)
def orb(name,loc,scale,m,p):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8);o=bpy.context.object;o.name=name;o.location=loc;o.scale=scale;o.data.materials.append(m);o.parent=p
 for f in o.data.polygons:f.use_smooth=True
 return o
def ring(name,center,r,t,m,p,a0=0,a1=math.tau,n=48):
 x,y,z=center;return tube(name,[(x+r*math.cos(a0+(a1-a0)*i/n),y,z+r*math.sin(a0+(a1-a0)*i/n)) for i in range(n+1)],t,m,p,8)
def text(name,string,loc,size,m,p,rotation=(math.pi/2,0,0)):
 c=bpy.data.curves.new(name,'FONT');c.body=string;c.size=size;c.align_x='CENTER';c.extrude=.0003;c.resolution_u=2;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.parent=p;o.location=loc;o.rotation_euler=rotation;c.materials.append(m);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return o

def column(x,z,h,index):
 p=root('Illustrated light column '+str(index),x,z)
 cube('Dressed stone plinth',(0,0,.065),(.69,.69,.13),columniron,p,.018)
 cube('Beveled column footing',(0,0,.155),(.6,.6,.09),brass,p,.016)
 cube('Layered base iron',(0,0,.23),(.555,.555,.08),columniron,p,.007)
 cube('Recessed warm glass inner',(0,0,(h+.28)/2),(.433,.433,h-.44),cream,p,.009)
 for xx in [-.243,.243]:
  for yy in [-.243,.243]:
   cube('Slim molded iron corner',(xx,yy,(h+.28)/2),(.058,.058,h-.24),columniron,p,.009)
   cube('Fine brass corner bead',(xx*.907,yy*1.045,(h+.28)/2),(.009,.012,h-.35),brass,p,.004)
   for zz in [.33,h-.16]:orb('Round cast panel bolt',(xx,yy*1.127,zz),(.017,.012,.017),brass,p)
 for zz in [.315,h-.11]:
  cube('Panel crossbar',(0,0,zz),(.532,.532,.035),columniron,p,.005)
  cube('Narrow weathered brass trim',(0,0,zz+.026),(.541,.541,.015),brass,p,.003)
 cube('Overhanging cap',(0,0,h-.04),(.62,.62,.09),columniron,p,.016)
 cube('Copper cap lid',(0,0,h+.014),(.56,.56,.025),brass,p,.006)
 # Drawings are custom geometric linework, one face at a time, with flowers and elongated figures.
 for face in range(4):
  a=face*math.pi/2
  def pos(u,v):return (u*math.cos(a)-(-.224)*math.sin(a),u*math.sin(a)+(-.224)*math.cos(a),v)
  def line(name,pts,r=.006):return tube(name,[pos(u,v) for u,v in pts],r,ink,p,5)
  base=.55;top=h-.40
  # deliberately irregular continuous wandering stem, silhouette resembles public-art etching
  line('Etched winding stem',[(.02,base),(-.031,base+.28),(.02,base+.62),(-.045,base+.98),(.028,base+1.36),(-.012,top-.28)],.009)
  for k in range(5):
   yy=base+.16+k*(h-.98)/5;sg=-1 if (k+face+index)%2 else 1
   line('Etched narrow leaf',[(0,yy),(sg*.13,yy+.11),(sg*.106,yy+.2),(0,yy)],.005)
  cy=top-.08;cx=-.012
  for petal in range(5):
   th=petal*math.tau/5;pts=[]
   for j in range(13):
    t=j*math.tau/12;u=cx+.058*math.cos(th)+.047*math.cos(t)*math.cos(th)-.028*math.sin(t)*math.sin(th);v=cy+.058*math.sin(th)+.047*math.cos(t)*math.sin(th)+.028*math.sin(t)*math.cos(th);pts.append((u,v))
   line('Engraved flower petal',pts,.005)
  line('Flower center',[(cx+.026*math.cos(j*math.tau/16),cy+.026*math.sin(j*math.tau/16)) for j in range(17)],.006)
  if face==0:
   text('Tiny Swedish artwork title','NATTENS VÄXTER',(-.002,-.235,.455),.027,ink,p)
   text('Tiny Swedish artwork label','DÄLMÖNSTER · 03',(-.002,-.235,.406),.02,ink,p)
 # narrow weather streaks, actual engraved marks under trim
 for k in range(12):
  xx=random.uniform(-.185,.185);zz=random.uniform(.7,h-.3)
  rod('Fine worn glass scratch',(xx,-.222,zz),(xx+.002,-.222,zz+random.uniform(.025,.12)),.001,ink,p,4)
 return p

def bicycle(x,z,heading=0):
 p=root('Authored city bicycle',x,z);p.rotation_euler=(.115,0,heading)
 rear=(-.56,0,.355);front=(.59,0,.355)
 for j,(wx,wy,wz) in enumerate([rear,front]):
  ring('Rounded bicycle tire',(wx,0,wz),.325,.026,rubber,p)
  for yy in [-.018,.018]:ring('Steel wheel rim',(wx,yy,wz),.302,.008,chrome,p)
  rod('Wheel axle',(wx,-.095,wz),(wx,.095,wz),.023,chrome,p,12)
  for i in range(24):
   a=i*math.tau/24;rod('Tensioned crossed wheel spoke',(wx+.027*math.cos(a+.3),.026 if i%2 else -.026,wz+.027*math.sin(a+.3)),(wx+.30*math.cos(a),0,wz+.30*math.sin(a)),.0018,chrome,p,5)
  for yy in [-.013,.013]:ring('Curved full metal mudguard',(wx,yy,wz),.371,.017,frame,p,-.22,math.pi+.21,32)
  for s in [-1,1]:rod('Mudguard stay',(wx,s*.022,wz),(wx-.29,s*.031,wz+.225),.004,chrome,p,6)
  orb('Amber spoke reflector',(wx+.21,0,wz),(.033,.012,.012),brass,p)
 # diamond frame with authentic triangle topology
 crank=(-.055,0,.31);seat=(-.21,0,.87);head=(.42,0,.89)
 for a,b in [(crank,seat),(seat,head),(head,crank),(crank,rear),(rear,seat)]:rod('Round brazed frame tubing',a,b,.022,frame,p,12)
 rod('Head tube',(.43,0,.79),(.385,0,1.015),.029,frame,p,12)
 for yy in [-.042,.042]:
  tube('Curved front fork',[(.43,yy,.79),(.47,yy,.59),(.545,yy,.38),(.59,yy,.355)],.014,frame,p,10)
  rod('Rear axle frame stay',(-.55,yy,.355),(-.22,yy,.81),.012,frame,p)
 rod('Seat post',(-.21,0,.84),(-.25,0,1.00),.017,chrome,p)
 orb('Shaped leather saddle',(-.28,0,1.017),(.125,.078,.029),saddle,p)
 rod('Handlebar riser',(.394,0,.985),(.38,0,1.10),.012,chrome,p)
 tube('Swept handlebar',[(.33,-.225,1.085),(.405,-.18,1.104),(.43,-.085,1.113),(.40,0,1.11),(.43,.085,1.113),(.405,.18,1.104),(.33,.225,1.085)],.01,chrome,p,10)
 for yy in [-1,1]:
  rod('Textured rubber handgrip',(.33,yy*.235,1.085),(.397,yy*.175,1.104),.016,rubber,p)
  rod('Curved brake lever',(.365,yy*.20,1.063),(.405,yy*.125,1.071),.006,chrome,p)
  tube('Bicycle brake cable',[(.393,yy*.17,1.09),(.47,yy*.12,.97),(.49,yy*.06,.8),(.51,yy*.023,.71)],.0025,rubber,p,5)
 # chainset and pedals, chain loop on drive side
 ring('Chain ring',(crank[0],-.079,crank[2]),.097,.012,chrome,p)
 ring('Chain ring internal',(crank[0],-.079,crank[2]),.067,.008,iron,p)
 for a in range(5):rod('Chainring spider',(-.055,-.08,.31),(-.055+.078*math.cos(a*math.tau/5),-.08,.31+.078*math.sin(a*math.tau/5)),.006,chrome,p)
 tube('Bicycle chain',[(-.06,-.092,.407),(-.56,-.092,.395),(-.6,-.092,.35),(-.56,-.092,.312),(-.06,-.092,.214),(.025,-.092,.254),(.037,-.092,.345),(-.06,-.092,.407)],.0045,iron,p,6)
 for yy,sg in [(-.11,1),(.11,-1)]:
  rod('Crank arm',(-.055,yy,.31),(-.055+sg*.12,yy,.27),.01,chrome,p)
  cube('Grippy rubber pedal',(-.055+sg*.12,yy*1.34,.27),(.08,.09,.025),rubber,p,.004)
 # cargo rack is formed tubing, not solid block
 for yy in [-.085,.085]:tube('Rear cargo rack rail',[(-.77,yy,.86),(-.3,yy,.86),(-.29,yy,.82)],.007,iron,p)
 for xx in [-.75,-.65,-.55,-.45,-.33]:rod('Rear rack crossbar',(xx,-.085,.86),(xx,.085,.86),.006,iron,p)
 for yy in [-.06,.06]:rod('Rear rack stay',(-.55,yy,.37),(-.72,yy,.86),.005,iron,p)
 orb('Red rear lamp',(-.792,0,.87),(.018,.045,.026),red,p)
 orb('Small front dynamo lamp',(.50,0,.80),(.035,.033,.029),white,p)
 rod('Extended kickstand',(-.11,.05,.33),(-.2,.18,.013),.008,iron,p)
 return p

def speaker(x,z):
 p=root('Portable battered speaker',x,z)
 cube('Chamfered speaker cabinet',(0,0,.325),(.48,.31,.62),black,p,.036)
 cube('Recessed front baffle',(0,-.16,.327),(.42,.016,.55),iron,p,.018)
 for zz,r in [(.27,.16),(.515,.057)]:
  # face is XZ. Fine dome plus separate surround rings reads beneath grille.
  ring('Radial driver rubber surround',(0,-.182,zz),r,.017,rubber,p)
  orb('Conical speaker diaphragm',(0,-.186,zz),(r*.82,.019,r*.82),speak,p)
  orb('Speaker dust cap',(0,-.208,zz),(r*.28,.016,r*.28),black,p)
 for xx in [i*.025 for i in range(-8,9)]:rod('Speaker protective grille vertical',(xx,-.219,.072),(xx,-.219,.582),.0024,iron,p,5)
 for zz in [.076+i*.025 for i in range(21)]:rod('Speaker protective grille crosswire',(-.205,-.22,zz),(.205,-.22,zz),.0016,iron,p,5)
 for xx in [-.177,.177]:
  for zz in [.076,.579]:orb('Hex baffle fastener',(xx,-.23,zz),(.008,.005,.008),chrome,p)
 for xx in [-.17,.17]:cube('Rubber speaker foot',(xx,0,.012),(.07,.21,.024),rubber,p,.006)
 tube('Carry handle',[(-.095,0,.642),(-.095,0,.69),(.095,0,.69),(.095,0,.642)],.012,rubber,p,10)
 text('Speaker brand plate','EFTERFEST',(0,-.231,.107),.028,white,p)
 return p

def utility(x,z):
 p=root('Stickered green utility cabinet',x,z)
 cube('Utility concrete plinth',(0,0,.08),(.76,.41,.16),iron,p,.018)
 cube('Galvanized enamel cabinet',(0,0,.58),(.68,.36,.99),boxgreen,p,.026)
 cube('Overhanging utility cabinet roof',(0,0,1.09),(.73,.41,.055),boxgreen,p,.016)
 cube('Inset cabinet service door',(0,-.19,.61),(.592,.015,.84),boxgreen,p,.01)
 for xx in [-.27,.27]:rod('Cabinet pressed seam',(xx,-.204,.215),(xx,-.204,.99),.002,iron,p)
 cube('Weathered key escutcheon',(.24,-.214,.55),(.031,.012,.06),chrome,p,.005)
 for zz in [.29,.32,.35,.38]:cube('Stamped ventilation slot',(-.1,-.21,zz),(.28,.005,.008),iron,p,.003)
 # layered original stickers with Swedish text, crooked edges
 stickers=[(-.11,.73,.23,.12,'LEV LITE',white,ink),(.15,.92,.16,.09,'MALMÖ',white,ink),(-.05,.49,.22,.11,'NATTBUSS',red,white)]
 for xx,zz,w,h,label,paper,letters in stickers:
  cube('Weathered paper sticker',(xx,-.215,zz),(w,.003,h),paper,p,.001)
  text('Printed sticker text',label,(xx,-.22,zz-.014),.023,letters,p)
 tube('Handpainted looping graffiti',[(-.19,-.223,.86),(-.14,-.223,.94),(-.03,-.223,.85),(.04,-.223,.92),(.12,-.223,.80)],.004,ink,p,5)
 return p

def binprop(x,z):
 p=root('City litter bin',x,z)
 # hex-sided cast metal cylinder with ribbed perforated outer cage
 N=24;vs=[];fs=[]
 for zz,rr in [(0,.235),(.065,.267),(.76,.267),(.82,.246)]:
  for j in range(N):vs.append((rr*math.cos(j*math.tau/N),rr*math.sin(j*math.tau/N),zz))
 for k in range(3):
  for j in range(N):a=k*N+j;b=k*N+(j+1)%N;fs.append((a,b,b+N,a+N))
 mesh('Rolled cylindrical bin shell',vs,fs,iron,p)
 for zz in [.06,.77,.81]:
  tube('Raised rim hoop',[(.267*math.cos(i*math.tau/40),.267*math.sin(i*math.tau/40),zz) for i in range(41)],.011,iron,p)
 # raised lid with front/side deposit gap
 for s in [-1,1]:cube('Bin lid upright',(s*.19,0,.88),(.037,.29,.14),iron,p,.012)
 orb('Shallow rainproof litter lid',(0,0,.95),(.286,.286,.037),iron,p)
 for j in range(16):
  a=j*math.tau/16;rod('Vertical bin reinforcement',(.272*math.cos(a),.272*math.sin(a),.12),(.272*math.cos(a),.272*math.sin(a),.71),.005,brass,p,5)
 text('Small municipal bin label','MALMÖ',(0,-.273,.60),.029,white,p)
 return p

with open(os.path.join(BASE,'src/layout.json')) as layout_file:layout=json.load(layout_file)
for index,(x,z,height,*_) in enumerate(layout['lamps'][:3],1):column(x,z,height,index)
bicycle(-18,-13,.3);bicycle(15,15,2.7);speaker(2.8,-2.1);utility(16,8);binprop(-8,-6.5)
# Merge once, preserve material batches. Precise positions are baked into the static scenery.
bpy.ops.object.select_all(action='DESELECT');objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();combined=bpy.context.object;combined.name='Authored street props';bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
# Normalize normals and strip duplicate material slots.
bm=bmesh.new();bm.from_mesh(combined.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(combined.data);bm.free()
materials=[];mapping={}
for i,m in enumerate(combined.data.materials):
 if m not in materials:materials.append(m)
 mapping[i]=materials.index(m)
indices=[mapping[p.material_index] for p in combined.data.polygons];combined.data.materials.clear()
for m in materials:combined.data.materials.append(m)
for p,i in zip(combined.data.polygons,indices):p.material_index=i
for o in allroots:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT');combined.select_set(True);bpy.context.view_layer.objects.active=combined
bpy.ops.export_scene.gltf(filepath=os.path.join(BASE,'public/assets/props.glb'),use_selection=True,export_format='GLB',export_yup=True,export_apply=True)
combined.data.calc_loop_triangles();print('PROP_RESULT','triangles',len(combined.data.loop_triangles),'draws',len(combined.data.materials))
# Neutral photographic preview, exported asset does not include this rig.
world=bpy.context.scene.world or bpy.data.worlds.new('Studio');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.11,.14,1);world.node_tree.nodes['Background'].inputs[1].default_value=.3
for loc,power,size in [((-3,1,7),600,5),((-10,7,6),850,4),((-18,8,5),900,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((-6.5,5.8,1.8))-o.location).to_track_quat('-Z','Y').to_euler()
column_x,column_z,column_h,*_=layout['lamps'][0]
bpy.ops.object.camera_add(location=(column_x+3.5,-column_z-5.8,3.3));cam=bpy.context.object;cam.rotation_euler=(Vector((column_x,-column_z,column_h/2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.3;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(BASE,'.dream-loop/props-column-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE,'.dream-loop/props.blend'));bpy.ops.render.render(write_still=True)
cam.location=(-16,10.3,1.75);cam.rotation_euler=(Vector((-18,13,.55))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.1;scene.render.filepath=os.path.join(BASE,'.dream-loop/props-bike-preview.png');bpy.ops.render.render(write_still=True)
