"""Original unbranded compact hatchback, authored in Blender for instancing.
4.04m body length, 1.82m body width (2.04m mirrors), Y-up glTF, +Z nose.
No exterior/interior light is emissive and no GPU preview is run by this script.
"""
import bpy,math,os,bmesh,random
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
def material(name,c,rough=.7,metal=0,alpha=1):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,alpha);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Alpha'].default_value=alpha;p.inputs['Emission Strength'].default_value=0
 if alpha<1:m.surface_render_method='DITHERED';m.use_backface_culling=True
 return m
paint=material('CarPaint',(.058,.083,.087),.30,.67);paint.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.26;paint.node_tree.nodes.get('Principled BSDF').inputs['Coat Roughness'].default_value=.18
rubber=material('Car rubber and dark trim',(.012,.015,.014),.94)
glass=material('Car inset tinted glass',(.022,.038,.044),.13,.13,.79)
alloy=material('Car brushed alloy metal',(.30,.34,.34),.34,.86)
interior=material('Car charcoal cloth interior',(.035,.040,.039),.94)
headlamp=material('Car unlit headlamp glass',(.24,.29,.28),.19,.50)
taillamp=material('Car unlit red reflector lens',(.29,.019,.012),.24,.10)
plate=material('Car numberplate ceramic',(.66,.67,.60),.58,.05)

def mesh(n,vs,fs,m,smooth=True):
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.materials.append(m);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o)
 for f in me.polygons:f.use_smooth=smooth
 return o

def cube(n,loc,size,m,bevel=.01):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=n;o.location=loc;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  b=o.modifiers.new('Stamped radiused edges','BEVEL');b.width=bevel;b.segments=1 if m in [rubber,interior] else 2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
  w=o.modifiers.new('Weighted panel normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=w.name)
 return o

def orb(n,loc,scale,m,seg=20,rings=10):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings);o=bpy.context.object;o.name=n;o.location=loc;o.scale=scale;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o

def tube(n,ps,r,m,seg=6):
 if n in ['Vertical pressed door gap','Rear door shut line','Lower door shut line'] and 'shell' in globals():
  projected=[];side=1 if ps[0][0]>0 else -1
  for pa,pb in zip(ps[:-1],ps[1:]):
   for step in range(5):
    p=Vector(pa).lerp(Vector(pb),step/4);hit,loc,normal,_=shell.ray_cast(Vector((side*2,p.y,p.z)),Vector((-side,0,0)))
    if hit and side*loc.x>.5:projected.append(tuple(loc+normal*.0015))
  if len(projected)>1:ps=projected
 vs=[];fs=[]
 for i,p in enumerate(ps):
  p=Vector(p);t=(Vector(ps[min(i+1,len(ps)-1)])-Vector(ps[max(i-1,0)])).normalized();u=t.cross(Vector((0,0,1)))
  if u.length<.001:u=Vector((0,1,0))
  u.normalize();w=t.cross(u).normalized();rr=r if isinstance(r,(float,int)) else r[i]
  for j in range(seg):a=j*math.tau/seg;vs.append(tuple(p+rr*(math.cos(a)*u+math.sin(a)*w)))
 for i in range(len(ps)-1):
  for j in range(seg):a=i*seg+j;b=i*seg+(j+1)%seg;fs.append((a,b,b+seg,a+seg))
 fs.extend([tuple(range(seg-1,-1,-1)),tuple((len(ps)-1)*seg+j for j in range(seg))]);return mesh(n,vs,fs,m)

def circle(n,x,y,z,r,thick,m,N=40,start=0,end=math.tau):return tube(n,[(x,y+r*math.cos(start+(end-start)*i/N),z+r*math.sin(start+(end-start)*i/N)) for i in range(N+1)],thick,m,5)
def cylinder(n,loc,r,depth,m,verts=24):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc,rotation=(0,math.pi/2,0));o=bpy.context.object;o.name=n;o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o

def panel(n,corners,m,N=8,M=4,bulge=.012):
 a,b,c,d=[Vector(v) for v in corners];vs=[];fs=[]
 normal=(b-a).cross(d-a).normalized()
 center=(a+b+c+d)/4
 if normal.dot(Vector((center.x,center.y,0)))<0:a,b,c,d=a,d,c,b;normal=-normal
 for j in range(M+1):
  t=j/M
  for i in range(N+1):
   u=i/N;p=a.lerp(b,u).lerp(d.lerp(c,u),t);p+=normal*(math.sin(u*math.pi)*math.sin(t*math.pi)*bulge);vs.append(tuple(p))
 for j in range(M):
  for i in range(N):q=j*(N+1)+i;fs.append((q,q+1,q+N+2,q+N+1))
 return mesh(n,vs,fs,m)

# Continuous formed-metal lower shell, with genuine cut wheel openings.
sections=[(-2.02,.69,.31,.64,.735),(-1.91,.815,.245,.72,.80),(-1.64,.88,.225,.825,.91),(-1.00,.897,.22,.905,.995),(-.30,.905,.22,.93,1.015),(.48,.905,.23,.955,1.022),(1.16,.88,.245,.955,1.02),(1.76,.825,.26,.925,.985),(1.99,.745,.30,.82,.89),(2.02,.66,.345,.76,.83)]
vs=[];fs=[]
for y,rx,base,shoulder,top in sections:
 cross=[(0,top),(.64*rx,top-.005),(.91*rx,shoulder+.035),(rx,shoulder-.025),(1.014*rx,(base+shoulder)/2),(.97*rx,base+.035),(.71*rx,base),(-.71*rx,base),(-.97*rx,base+.035),(-1.014*rx,(base+shoulder)/2),(-rx,shoulder-.025),(-.91*rx,shoulder+.035),(-.64*rx,top-.005)]
 vs.extend((x,y,z) for x,z in cross)
N=len(cross)
for j in range(len(sections)-1):
 for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
fs.extend([tuple(range(N-1,-1,-1)),tuple((len(sections)-1)*N+i for i in range(N))]);shell=mesh('Continuous stamped hatchback body',vs,fs,paint)
bpy.context.view_layer.objects.active=shell
s=shell.modifiers.new('Smooth formed body panels','SUBSURF');s.levels=2;s.render_levels=2;bpy.ops.object.modifier_apply(modifier=s.name)
for axle in [-1.27,1.27]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.370,depth=2.35,location=(0,axle,.325),rotation=(0,math.pi/2,0));cut=bpy.context.object
 bpy.context.view_layer.objects.active=shell;bo=shell.modifiers.new('True wheel arch opening','BOOLEAN');bo.operation='DIFFERENCE';bo.solver='EXACT';bo.object=cut;bpy.ops.object.modifier_apply(modifier=bo.name);bpy.data.objects.remove(cut,do_unlink=True)
# Cut a true passenger well so no opaque body surface crosses the empty cabin.
cut=cube('Temporary rounded passenger cavity',(0,.28,1.08),(1.43,2.03,1.30),rubber,.08)
bpy.context.view_layer.objects.active=shell;bo=shell.modifiers.new('Hollow passenger compartment','BOOLEAN');bo.operation='DIFFERENCE';bo.solver='EXACT';bo.object=cut;bpy.ops.object.modifier_apply(modifier=bo.name);bpy.data.objects.remove(cut,do_unlink=True)
cube('Dark cabin floor',(0,.20,.438),(1.40,2.0,.07),interior,.01)
for side in [-1,1]:cube('Empty cabin interior door card',(side*.707,.20,.72),(.03,1.96,.47),interior,.025)

# Low visible chassis and molded sill lips between wheel wells.
cube('Recessed underbody pan',(0,0,.235),(1.53,2.0,.13),rubber,.03)
for side in [-1,1]:
 tube('Subtle sculpted rocker sill',[(side*.868,-.85,.29),(side*.91,-.65,.28),(side*.914,.65,.29),(side*.855,.89,.31)],.028,paint,8)
 for axle in [-1.27,1.27]:
  circle('Rolled painted wheel arch lip',side*.877,axle,.325,.370,.010,paint,32,0,math.pi)
  circle('Recessed black wheel arch liner',side*.81,axle,.325,.377,.017,rubber,30,0,math.pi)

def conforming_lamp(name,side,rear=False):
 points=[(.39,.710),(.75,.755),(.73,.895),(.405,.865)] if rear else [(.365,.565),(.755,.610),(.745,.725),(.375,.690)]
 corners=[Vector((side*x,z)) for x,z in points];vs=[];fs=[];N=10;M=4
 for j in range(M+1):
  t=j/M
  for i in range(N+1):
   u=i/N;p=corners[0].lerp(corners[1],u).lerp(corners[3].lerp(corners[2],u),t)
   hit,loc,normal,_=shell.ray_cast(Vector((p.x,3 if rear else -3,p.y)),Vector((0,-1 if rear else 1,0)))
   if not hit:raise RuntimeError('Lamp projection missed car shell')
   vs.append(tuple(loc+normal*.004))
 for j in range(M):
  for i in range(N):q=j*(N+1)+i;fs.append((q,q+1,q+N+2,q+N+1))
 mesh(name,vs,fs,taillamp if rear else headlamp)
 border=[vs[i] for i in range(N+1)]+[vs[j*(N+1)+N] for j in range(1,M+1)]+[vs[M*(N+1)+i] for i in range(N-1,-1,-1)]+[vs[j*(N+1)] for j in range(M-1,0,-1)];tube('Inset lamp perimeter gasket',border+[border[0]],.004,rubber,5)

# Four detailed tires, cast alloy rims, brake discs, hubs and tread sipes.
for axle in [-1.27,1.27]:
 for side in [-1,1]:
  xc=side*.783;z=.325;vs=[];fs=[];radial=32
  profile=[(-.103,.231),(-.106,.276),(-.086,.311),(-.060,.325),(.060,.325),(.086,.311),(.106,.276),(.103,.231)]
  for dx,rr in profile:
   for k in range(radial):a=k*math.tau/radial;vs.append((xc+dx,axle+rr*math.cos(a),z+rr*math.sin(a)))
  for j in range(len(profile)):
   for k in range(radial):a=j*radial+k;b=j*radial+(k+1)%radial;c=((j+1)%len(profile))*radial+(k+1)%radial;d=((j+1)%len(profile))*radial+k;fs.append((a,b,c,d))
  mesh('Rounded radial rubber tire',vs,fs,rubber)
  outer=xc+side*.108
  for rr in [.255,.293]:circle('Molded tire sidewall ring',outer,axle,z,rr,.0025,rubber,36)
  for k in range(24):
   a=k*math.tau/24;ps=[]
   for q in range(4):dx=-.066+q*.044;aa=a+q*.018;ps.append((xc+dx,axle+.326*math.cos(aa),z+.326*math.sin(aa)))
   tube('Fine diagonal tread shoulder sipe',ps,.0018,rubber,3)
  cylinder('Recessed brake rotor',(xc+side*.069,axle,z),.205,.014,alloy,32)
  cylinder('Dark inner wheel barrel',(xc+side*.058,axle,z),.230,.075,rubber,32)
  circle('Outer alloy rim flange',outer+side*.003,axle,z,.226,.012,alloy,36)
  circle('Inner alloy rim bead',outer,axle,z,.205,.007,alloy,32)
  # Five tapered double-faced spokes, geometrically separated by real holes.
  for j in range(5):
   a=j*math.tau/5+.18;u=Vector((0,math.cos(a),math.sin(a)));v=Vector((0,-math.sin(a),math.cos(a)));center=Vector((outer,axle,z));pts=[]
   shape=[u*.055-v*.018,u*.192-v*.028,u*.205+v*.028,u*.055+v*.018]
   for depth in [-.019,0]:pts.extend(tuple(center+s+Vector((side*depth,0,0))) for s in shape)
   mesh('Tapered alloy wheel spoke',pts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],alloy)
  cylinder('Plain alloy hub cap',(outer+side*.006,axle,z),.065,.027,alloy,24)
  for j in range(5):
   a=j*math.tau/5;cylinder('Recessed wheel lug bolt',(outer+side*.022,axle+.041*math.cos(a),z+.041*math.sin(a)),.008,.008,rubber,8)
  cube('Visible dark brake caliper',(xc+side*.079,axle+.13,z+.055),(.044,.05,.11),rubber,.011)

# Passenger cell: inset glass, distinct roof, A/B/C pillars and rubber window gaskets.
# The car is empty. The understated interior is visible through tinted alpha glass.
roof_sections=[(-.50,.614,1.426),(-.38,.648,1.476),(-.20,.667,1.501),(.54,.666,1.508),(.84,.636,1.476),(.96,.601,1.421)]
vs=[];fs=[]
for y,w,h in roof_sections:
 for j in range(9):t=j/8*2-1;vs.append((t*w,y,h+.018*(1-t*t)))
for k in range(len(roof_sections)-1):
 for j in range(8):a=k*9+j;fs.append((a,a+1,a+10,a+9))
roof=mesh('Pressed gently crowned roof panel',vs,fs,paint)
bpy.context.view_layer.objects.active=roof;sol=roof.modifiers.new('Roof inner panel thickness','SOLIDIFY');sol.thickness=.018;bpy.ops.object.modifier_apply(modifier=sol.name)
panel('Curved inset windshield',[(-.766,-.883,1.005),(.766,-.883,1.005),(.615,-.483,1.436),(-.615,-.483,1.436)],glass,16,7,.028)
panel('Curved hatch rear window',[(.726,1.529,1.032),(-.726,1.529,1.032),(-.599,.973,1.421),(.599,.973,1.421)],glass,14,6,.018)
for side in [-1,1]:
 front=[(side*.790,-.823,1.016),(side*.810,.211,1.024),(side*.650,.197,1.484),(side*.625,-.436,1.438)]
 rear=[(side*.810,.299,1.024),(side*.765,1.344,1.033),(side*.610,.872,1.434),(side*.650,.282,1.484)]
 for name,pts in [('Inset front door window',front),('Inset rear door window',rear)]:
  if side<0:pts=pts[::-1]
  panel(name,pts,glass,10,5,.005)
  tube('Black inset window seal',pts+[pts[0]],.010,rubber,6)
 tube('Painted A pillar',[(side*.803,-.896,.996),(side*.72,-.665,1.231),(side*.635,-.472,1.448)],.036,paint,8)
 tube('Black B pillar',[(side*.817,.252,1.015),(side*.737,.252,1.246),(side*.659,.252,1.495)],.032,rubber,8)
 # Broad rear pillar formed as a four-sided stamped panel, not a primitive block.
 panel('Broad sculpted C pillar',[(side*.798,1.428,.985),(side*.726,1.593,1.020),(side*.597,1.000,1.439),(side*.627,.881,1.461)],paint,5,6,.008)
 tube('Roof side stamped rail',[(side*.622,-.487,1.448),(side*.667,-.18,1.505),(side*.669,.53,1.510),(side*.63,.873,1.480),(side*.608,.965,1.433)],.019,paint,7)
 tube('Lower window belt molding',[(side*.8,-.875,.995),(side*.824,-.12,1.008),(side*.823,.67,1.017),(side*.775,1.375,1.024)],.014,rubber,6)
 # Narrow door shut lines and body-color handle shells.
 for yy in [-.825,.25]:tube('Vertical pressed door gap',[(side*.888,yy,.345),(side*.912,yy,.60),(side*.89,yy,.876),(side*.805,yy,1.011)],.0035,rubber,5)
 tube('Rear door shut line',[(side*.818,1.325,1.03),(side*.875,1.20,.86),(side*.894,1.02,.67)],.0035,rubber,5)
 tube('Lower door shut line',[(side*.888,-.79,.337),(side*.903,.25,.337),(side*.868,.915,.355)],.0035,rubber,5)
 for yy in [-.09,.90]:
  orb('Recessed door handle pocket',(side*.897,yy,.892),(.010,.080,.021),rubber,16,8)
  tube('Body-color pull door handle',[(side*.914,yy-.055,.897),(side*.929,yy,.899),(side*.914,yy+.055,.897)],.010,paint,7)
 tube('Mirror mounting arm',[(side*.806,-.682,1.029),(side*.927,-.659,1.054)],.018,rubber,7)
 orb('Sculpted body-color mirror housing',(side*.958,-.625,1.071),(.067,.098,.056),paint,20,12)
 panel('Inset mirror reflective glass',[(side*.911,-.543,1.038),(side*1.006,-.550,1.042),(side*1.005,-.566,1.101),(side*.914,-.552,1.108)],headlamp,5,3,.002)

# Unoccupied cloth seats, console, dashboard and steering wheel.
for row,y in enumerate([-.05,.80]):
 for side in [-1,1]:
  x=side*.397;seat=cube('Empty cloth seat cushion',(x,y-.08,.554),(.425,.445,.13),interior,.058)
  back=cube('Empty sculpted seat back',(x,y+.10,.829),(.413,.13,.53),interior,.055);back.rotation_euler.x=-.11
  cube('Empty adjustable headrest',(x,y+.129,1.124),(.257,.105,.155),interior,.040)
  for yy in [y-.18,y-.03]:tube('Seat cushion stitched channel',[(x-.14,yy,.625),(x+.14,yy,.625)],.002,interior,4)
cube('Matte dashboard',(0,-.691,.883),(1.42,.28,.19),interior,.05)
cube('Low center console',(0,-.025,.52),(.19,.62,.17),rubber,.03)
for x in [-.49,.49]:cube('Dashboard air vent',(x,-.512,.921),(.18,.01,.059),rubber,.01)
# Steering wheel faces the empty left front seat.
ps=[]
for i in range(41):a=i*math.tau/40;ps.append((-.40+.143*math.cos(a),-.456-.044*math.sin(a),.955+.126*math.sin(a)))
tube('Unoccupied steering wheel',ps,.014,rubber,7)
for a in [0,math.tau/3,2*math.tau/3]:tube('Steering wheel spoke',[(-.40,-.456,.955),(-.40+.125*math.cos(a),-.456-.037*math.sin(a),.955+.11*math.sin(a))],.010,rubber,6)
orb('Steering wheel center',(-.40,-.456,.955),(.058,.023,.048),rubber,16,8)

# Lamp lenses are explicitly unlit; no emissive materials anywhere in this asset.
for side in [-1,1]:
 conforming_lamp('Off swept front headlight',side)
 conforming_lamp('Unlit rear red tail lamp',side,True)
 cube('Lower rear red reflector',(side*.61,1.933,.424),(.18,.020,.037),taillamp,.012)
 tube('Tail lens horizontal flute',[(side*.51,1.97,.82),(side*.714,1.884,.849)],.0035,taillamp,5)
# Lower grille, bumper rub strips and modest anonymous plates.
cube('Recessed front grille',(0,-2.024,.486),(.84,.045,.166),rubber,.035)
for z in [.438,.476,.514,.552]:tube('Thin front grille horizontal slat',[(-.372,-2.05,z),(.372,-2.05,z)],.005,alloy,5)
for x in [-.48,.48]:cube('Dark front bumper corner inlet',(x,-2.01,.460),(.185,.027,.122),rubber,.025)
cube('Front plate mount',(0,-2.011,.647),(.465,.025,.108),rubber,.008)
cube('Plain anonymous front plate',(0,-2.028,.648),(.441,.004,.091),plate,.005)
cube('Rear plate recess',(0,1.993,.718),(.50,.031,.125),rubber,.014)
cube('Plain anonymous rear plate',(0,2.010,.717),(.441,.004,.091),plate,.005)
# Small grouped neutral marks evoke plate lettering without brand or real registration.
for y,z,sg in [(-2.032,.646,-1),(2.014,.715,1)]:
 for k in range(6):cube('Neutral numberplate embossed character',(-.149+k*.06,y,z),(.025,.002,.042),rubber,.001)
tube('Rear bumper protective molding',[(-.7,1.918,.521),(-.4,1.997,.507),(0,2.005,.505),(.4,1.997,.507),(.7,1.918,.521)],.016,rubber,7)
# Hood/hatch shut lines and wipers make the large smooth panels read as a car.
for side in [-1,1]:tube('Parked front windshield wiper',[(side*.45,-.839,1.043),(side*.21,-.742,1.153),(side*.01,-.748,1.149)],.005,rubber,5)
tube('Parked rear window wiper',[(0,1.51,1.060),(.24,1.363,1.169),(.38,1.359,1.176)],.006,rubber,5)
tube('Short roof radio aerial',[(.0,.819,1.522),(.0,.891,1.659)],[.006,.0015],rubber,7)

# One mesh / eight material batches, transforms baked for simple efficient instancing.
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=shell;bpy.ops.object.join();car=bpy.context.object;car.name='ParkedCar';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bm=bmesh.new();bm.from_mesh(car.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(car.data);bm.free()
mats=[];mapping={}
for i,m in enumerate(car.data.materials):
 if m is None:m=paint
 if m not in mats:mats.append(m)
 mapping[i]=mats.index(m)
idx=[mapping[p.material_index] for p in car.data.polygons];car.data.materials.clear()
for m in mats:car.data.materials.append(m)
for p,i in zip(car.data.polygons,idx):p.material_index=i
car.data.calc_loop_triangles();tris=len(car.data.loop_triangles)
if tris>24500:
 bpy.context.view_layer.objects.active=car;reduce=car.modifiers.new('Lossless-scale detail budget','DECIMATE');reduce.ratio=24400/tris;reduce.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=reduce.name);car.data.calc_loop_triangles();tris=len(car.data.loop_triangles)
if tris>25000:raise RuntimeError(f'Car geometry over target: {tris} triangles')
ground_offset=min(v.co.z for v in car.data.vertices)
for v in car.data.vertices:v.co.z-=ground_offset
if len(mats)>8:raise RuntimeError('Too many car materials: '+str([m.name for m in mats]))
for m in mats:
 if m.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value!=0:raise RuntimeError('Car must have all lamps off')
bpy.ops.object.select_all(action='DESELECT');car.select_set(True);bpy.context.view_layer.objects.active=car
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'public/assets/parked-car.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'.dream-loop/parked-car.blend'))
print('PARKED_CAR_RESULT',tris,'triangles',len(mats),'materials','ground',min(v.co.z for v in car.data.vertices),'height',max(v.co.z for v in car.data.vertices))
