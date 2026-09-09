"""Two original low-cost street pedestrians; Blender modeling, rigid limb animation.
No downloaded assets. Woven normals are generated mathematically in this file.
"""
import bpy, math, random, bmesh, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(941)
def material(name,c,rough=.9):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*c,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=rough;return m
plum=material('Pedestrian plum weathered wool',(.105,.064,.082))
cream=material('Pedestrian oatmeal scarf and tote',(.34,.29,.21))
olive=material('Pedestrian faded olive twill',(.18,.175,.108))
denim=material('Pedestrian blue black denim',(.032,.044,.050))
boots=material('Pedestrian worn dark leather',(.027,.025,.024),.72)
skinA=material('Pedestrian warm tan skin',(.39,.235,.158),.88)
skinB=material('Pedestrian soft pale skin',(.55,.37,.255),.88)
hair=material('Pedestrian brown hair and details',(.033,.021,.016),.96)
# Original generated fine woven normal, packed into the Blender and glTF sources.
import numpy as np
s=128;yy,xx=np.mgrid[:s,:s];normal=np.ones((s,s,4),dtype=np.float32);normal[:,:,0]=.5+.075*np.sin(xx*math.tau/8);normal[:,:,1]=.5+.075*np.sin(yy*math.tau/8);normal[:,:,2]=.994
im=bpy.data.images.new('Original pedestrian woven normal',width=s,height=s);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(normal.ravel());im.pack()
for m in [plum,cream,olive,denim]:
 n=m.node_tree.nodes;t=n.new('ShaderNodeTexImage');t.image=im;p=n.new('ShaderNodeNormalMap');p.inputs['Strength'].default_value=.20;m.node_tree.links.new(t.outputs['Color'],p.inputs['Color']);m.node_tree.links.new(p.outputs['Normal'],n['Principled BSDF'].inputs['Normal'])
def empty(n,p=None,loc=(0,0,0)):
 o=bpy.data.objects.new(n,None);bpy.context.collection.objects.link(o);o.parent=p;o.location=loc;return o
def mesh(n,v,f,m,p):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.materials.append(m);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);o.parent=p
 for poly in me.polygons:poly.use_smooth=True
 return o
def sphere(n,loc,scale,m,p,seg=16,rings=10):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings);o=bpy.context.object;o.name=n;o.parent=p;o.location=loc;o.scale=scale;o.data.materials.append(m)
 for q in o.data.polygons:q.use_smooth=True
 return o
def line(n,pts,r,m,p,seg=5):
 vs=[];fs=[]
 for i,pt in enumerate(pts):
  q=Vector(pt);t=(Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)])).normalized();u=t.cross(Vector((0,0,1)))
  if u.length<.01:u=t.cross(Vector((0,1,0)))
  u.normalize();w=t.cross(u).normalized()
  for j in range(seg):vs.append(q+r*(math.cos(j*math.tau/seg)*u+math.sin(j*math.tau/seg)*w))
 for i in range(len(pts)-1):
  for j in range(seg):a=i*seg+j;b=i*seg+(j+1)%seg;fs.append((a,b,b+seg,a+seg))
 fs += [tuple(range(seg-1,-1,-1)),tuple((len(pts)-1)*seg+j for j in range(seg))];return mesh(n,vs,fs,m,p)
def rings(n,levels,m,p,segments=24,fold=.002,subdivide=1,openfront=False):
 vs=[];fs=[]
 if n=='Compressed elbow coat sleeve':
  dense=[]
  for i in range(len(levels)-1):
   a,b=levels[i],levels[i+1]
   for q in range(3):dense.append(tuple(a[j]+(b[j]-a[j])*q/3 for j in range(5)))
  levels=dense+[levels[-1]]
 for k,(z,rx,ry,cx,cy) in enumerate(levels):
  for j in range(segments):
   a=math.tau*j/segments;f=fold*(math.sin(7*a+1.8*k)+.45*math.sin(11*a-.8*k))
   if n=='Compressed elbow coat sleeve':
    for zz,amp,width in [(-.241,.008,.019),(-.301,.006,.020),(-.369,.0035,.018)]:
     d=z-zz-.026*math.cos(a+.4)
     f+=amp*(math.exp(-(d/width)**2)-.50*math.exp(-((d+.018)/(.7*width))**2))*(.4+.6*max(0,-math.sin(a)))
   if n in ['Long wool wrap coat','Tailored olive chore jacket']:
    f+=.005*math.sin(a*3+.4)*math.exp(-((z-.93-.03*math.cos(a))/.04)**2)
   vs.append((cx+(rx+f)*math.cos(a),cy+(ry+f)*math.sin(a),z))
 for k in range(len(levels)-1):
  for j in range(segments):
   a=k*segments+j;b=k*segments+(j+1)%segments
   if openfront and levels[k][0]<.89:
    opening=range(14,22)
    if j in opening:continue
   fs.append((a,b,b+segments,a+segments))
 if not openfront:fs.append(tuple(range(segments-1,-1,-1)))
 fs.append(tuple((len(levels)-1)*segments+j for j in range(segments)));o=mesh(n,vs,fs,m,p)
 if subdivide:mod=o.modifiers.new('Tailored rounded contour','SUBSURF');mod.levels=subdivide
 return o

def shoes(p,side,ankle=.0,mat=boots):
 rings('Rounded worn boot',[(.02,.068,.126,0,-.035),(.032,.078,.148,0,-.04),(.052,.079,.148,0,-.04),(.071,.074,.14,0,-.042),(.105,.071,.129,0,-.03),(.152,.06,.076,0,.005),(.18,.059,.072,0,.01)],mat,p,20,.0007)
 line('Leather toe welt',[(-.066,-.105,.062),(-.05,-.16,.064),(0,-.18,.065),(.05,-.16,.064),(.066,-.105,.062)],.0025,mat,p)
 for z in [.14,.165]:line('Boot ankle creasing',[(-.050,-.044,z),(0,-.07,z+.005),(.050,-.044,z)],.0025,mat,p)
def legs(p,side,female):
 h=.91 if female else .88;g=empty('LeftLeg' if side<0 else 'RightLeg',p,(side*(.088 if female else .112),0,h));w=.073 if female else .092;m=boots if female else denim
 rings('Tailored creased trouser',[(.018,w,.088,0,0),(-.04,w,.088,0,0),(-.20,w*.93,.082,0,-.006),(-.33,w*.85,.075,0,-.014),(-.37,w*.90,.080,0,-.022),(-.41,w*.83,.073,0,-.017),(-.47,w*.89,.073,0,-.011),(-.59,w*.75,.067,0,.006),(-h+.12,w*.74,.063,0,.01)],m,g,20,.0015)
 # Add shoe meshes directly under each leg to merge into the limb draw.
 before=set(bpy.data.objects);shoes(g,side)
 for o in set(bpy.data.objects)-before:
  if o.type=='MESH':o.location.z-=h
 line('Trouser side seam',[(side*w,.005,-.03),(side*w*.88,-.001,-.31),(side*w*.79,.007,-.56),(side*w*.73,.01,-h+.15)],.002,m,g)
 return g

def arms(p,side,female):
 shoulder=.207 if female else .241;g=empty('LeftArm' if side<0 else 'RightArm',p,(side*shoulder,.012,1.39 if female else 1.405));m=plum if female else olive
 rows=[]
 for z,rx,ry,dx,dy in [(.027,.025,.027,0,0),(.015,.074,.072,0,0),(-.015,.090,.080,.008,0),(-.075,.085,.082,.035,-.005),(-.14,.078,.077,.049,-.012),(-.21,.078,.075,.055,-.035),(-.25,.085,.078,.056,-.037),(-.278,.070,.067,.058,-.039),(-.310,.076,.071,.062,-.044),(-.345,.065,.063,.067,-.050),(-.40,.060,.058,.069,-.057),(-.475,.052,.052,.068,-.06)]:rows.append((z,rx*(.83 if female else .91),ry*(.87 if female else .94),side*dx,dy))
 rings('Compressed elbow coat sleeve',rows,m,g,20,.002)
 rings('Turned sleeve cuff',[(-.446,.055,.054,side*.068,-.060),(-.46,.056,.055,side*.068,-.060),(-.48,.054,.053,side*.068,-.060)],m,g,20,.001)
 sm=skinA if female else skinB
 sphere('Relaxed natural hand',(side*.068,-.061,-.535),(.039,.030,.063),sm,g)
 for i in range(3):sphere('Resting finger',(side*.068-.016+i*.015,-.066,-.581),(.009,.022,.017),sm,g,8,6)
 sphere('Folded thumb',(side*.10,-.080,-.521),(.016,.019,.030),sm,g,10,6)
 line('Tailored sleeve seam',[(side*.08,.00,-.025),(side*.135,-.017,-.23),(side*.118,-.045,-.437)],.0025,m,g)
 return g

def head(p,female):
 h=empty('Head',p,(0,-.003,1.598 if female else 1.622));sm=skinA if female else skinB
 sphere('Neck',(0,.012,-.135),(.050,.052,.085),sm,h)
 rings('Adult facial skull',[(-.123,.028,.048,0,-.008),(-.104,.061,.061,0,-.003),(-.071,.082,.075,0,0),(-.02,.089,.082,0,.001),(.040,.088,.087,0,.008),(.087,.080,.081,0,.014),(.123,.054,.057,0,.016),(.140,.011,.014,0,.016)],sm,h,28,.0003)
 for s in [-1,1]:
  sphere('Ear',(s*.086,.004,-.019),(.014,.022,.031),sm,h,12,8)
  sphere('Eye socket shadow',(s*.036,-.077,.007),(.014,.007,.005),hair,h,12,8)
  line('Upper eyelid',[(s*.036-.019,-.079,.010),(s*.036,-.086,.015),(s*.036+.017,-.079,.011)],.004,sm,h)
  line('Brow',[(s*.020,-.080,.038),(s*.039,-.083,.041),(s*.056,-.073,.036)],.0025,hair,h)
 sphere('Defined nose',(0,-.086,-.020),(.015,.031,.030),sm,h,16,10)
 sphere('Nose tip',(0,-.107,-.038),(.020,.015,.013),sm,h,12,8)
 line('Quiet mouth',[(-.024,-.079,-.068),(0,-.087,-.071),(.024,-.079,-.068)],.0025,hair,h)
 # Back hair volume under knit cap; woman's low ponytail reads from overhead.
 o=rings('Hair behind cap',[(-.048,.074,.07,0,.025),(.010,.091,.086,0,.020),(.086,.088,.085,0,.019),(.123,.057,.061,0,.018)],hair,h,24,.001)
 # Keep front facial region visible by deleting hair polygons in the front half below cap.
 if o:
  bm=bmesh.new();bm.from_mesh(o.data);faces=[f for f in bm.faces if f.calc_center_median().y<-.020 and f.calc_center_median().z<.052];bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(o.data);bm.free()
 if female:
  sphere('Low gathered hair',(0,.109,-.075),(.051,.044,.065),hair,h)
  line('Ponytail',[(-.01,.105,-.089),(.00,.123,-.145),(.015,.116,-.197)],.032,hair,h,8)
 # Knit cap folded band, using hair material to keep head to two material draws.
 rings('Wool watch cap',[(.068,.091,.091,0,.013),(.080,.096,.096,0,.014),(.110,.099,.096,0,.014),(.146,.087,.083,0,.015),(.172,.058,.056,0,.016),(.180,.018,.019,0,.016)],hair,h,28,.002)
 rings('Turned ribbed cap brim',[(.069,.093,.094,0,.013),(.076,.101,.100,0,.013),(.097,.102,.101,0,.013),(.106,.097,.098,0,.013)],hair,h,28,.001)
 return h

def pedestrian(female):
 r=empty('PedestrianA' if female else 'PedestrianB');m=plum if female else olive
 if female:
  rings('Long wool wrap coat',[(.59,.221,.140,0,.020),(.62,.221,.141,0,.020),(.71,.210,.145,0,.010),(.83,.194,.135,0,.009),(.93,.174,.127,0,.001),(1.02,.165,.120,0,0),(1.12,.182,.132,0,-.002),(1.25,.198,.135,0,0),(1.37,.208,.115,0,.005),(1.425,.169,.091,0,.010),(1.465,.081,.062,0,.010)],m,r,24,.003,1,True)
  for s in [-1,1]:
   line('Coat long panel stitch',[(s*.12,-.105,.64),(s*.125,-.120,.83),(s*.10,-.11,1.05),(s*.14,-.12,1.28)],.0025,m,r)
   line('Coat slant welt pocket',[(s*.11,-.123,.91),(s*.16,-.102,1.02)],.009,m,r)
  # Cream draped scarf and tote, one shared cloth material.
  rings('Wrapped oatmeal scarf',[(1.38,.070,.061,0,-.003),(1.415,.105,.090,0,-.010),(1.452,.108,.091,0,-.007),(1.478,.086,.077,0,.003)],cream,r,28,.002)
  rings('Loose scarf end',[(1.12,.043,.012,.055,-.141),(1.17,.047,.016,.053,-.151),(1.28,.045,.020,.047,-.149),(1.40,.055,.025,.047,-.125)],cream,r,16,.001)
  for xx in [.024,.044,.064,.084]:line('Scarf fringe',[(xx,-.15,1.136),(xx+.002,-.15,1.10)],.002,cream,r)
  rings('Soft slouching canvas tote',[(.66,.105,.036,.452,.042),(.69,.130,.052,.450,.038),(.82,.131,.049,.453,.031),(.95,.119,.037,.447,.026),(.995,.105,.026,.443,.025)],cream,r,24,.003)
  for y in [-.003,.054]:line('Woven tote handle',[(.361,y,.977),(.235,y,1.24),(.202,y,1.391),(.253,y,1.365),(.429,y,1.15),(.536,y,.966)],.008,cream,r,6)
 else:
  rings('Tailored olive chore jacket',[(.82,.178,.121,0,.012),(.84,.203,.139,0,.010),(.895,.207,.141,0,.010),(.955,.199,.134,0,.001),(1.02,.190,.135,0,0),(1.12,.202,.142,0,0),(1.25,.232,.137,0,.005),(1.37,.241,.124,0,.010),(1.435,.193,.097,0,.015),(1.48,.087,.065,0,.013)],m,r,28,.003)
  line('Center dark zipper',[(0,-.139,.855),(0,-.14,1.02),(0,-.145,1.22),(0,-.113,1.405)],.004,m,r)
  for s in [-1,1]:
   # Raised flap pockets and folded collar are true silhouette detail.
   rings('Chore jacket lower patch pocket',[(.89,.052,.010,s*.129,-.117),(.94,.059,.015,s*.129,-.128),(1.019,.060,.015,s*.127,-.127)],m,r,16,.001)
   line('Pocket flap upper edge',[(s*.078,-.142,1.02),(s*.13,-.15,1.017),(s*.176,-.133,1.016)],.004,m,r)
   line('Folded jacket collar',[(s*.018,-.137,1.396),(s*.082,-.129,1.468),(s*.110,-.025,1.475)],.017,m,r,6)
   line('Shoulder yoke stitch',[(s*.037,-.100,1.43),(s*.13,-.11,1.397),(s*.218,-.067,1.373)],.0025,m,r)
  rings('Corduroy jacket waistband',[(.818,.179,.122,0,.012),(.837,.207,.140,0,.010),(.852,.204,.139,0,.010)],m,r,28,.001)
 for side in [-1,1]:legs(r,side,female);arms(r,side,female)
 head(r,female);return r

def merge(root):
 for g in [root]+[o for o in root.children_recursive if o.type=='EMPTY']:
  obs=[o for o in g.children if o.type=='MESH']
  if not obs:continue
  bpy.ops.object.select_all(action='DESELECT')
  for o in obs:
   o.select_set(True);bpy.context.view_layer.objects.active=o
   for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
   bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
   tint=o.data.color_attributes.new(name='ClothTint',type='FLOAT_COLOR',domain='CORNER')
   shade=.24 if o.name.startswith('Center dark zipper') else 1.0
   for c in tint.data:c.color=(shade,shade,shade,1)
   o.data.color_attributes.active_color=tint
   uv=o.data.uv_layers.active or o.data.uv_layers.new(name='Woven UV')
   for poly in o.data.polygons:
    axis=max(range(3),key=lambda j:abs(poly.normal[j]));ax=[j for j in range(3) if j!=axis]
    for li in poly.loop_indices:
     co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co[ax[0]]*7,co[ax[1]]*7)
  bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=bpy.context.object;o.name=g.name+'_Mesh';mats=[];mapping={}
  for i,m in enumerate(o.data.materials):
   if m not in mats:mats.append(m)
   mapping[i]=mats.index(m)
  inds=[mapping[q.material_index] for q in o.data.polygons];o.data.materials.clear()
  for m in mats:o.data.materials.append(m)
  for q,i in zip(o.data.polygons,inds):q.material_index=i

def export(root,filename):
 bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
 for o in root.children_recursive:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets'/filename),use_selection=True,export_format='GLB',export_apply=True,export_animations=False)
 for o in root.children_recursive:
  if o.type=='MESH':o.data.calc_loop_triangles()
 tris=sum(len(o.data.loop_triangles) for o in root.children_recursive if o.type=='MESH');draws=sum(len(o.data.materials) for o in root.children_recursive if o.type=='MESH');print('PEDESTRIAN RESULT',filename,tris,draws,flush=True)
 return {'triangles':tris,'drawCalls':draws}
report={}
a=pedestrian(True);merge(a);report['a']=export(a,'pedestrian-a.glb')
for o in [a]+list(a.children_recursive):o.name='SourceA_'+o.name
b=pedestrian(False);merge(b);report['b']=export(b,'pedestrian-b.glb')
a.location.x=-.55;b.location.x=.55
world=bpy.data.worlds.new('Pedestrian studio');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.17,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
for loc,power,size,col in [((2,-3,5),450,3,(1,.80,.62)),((-3,-1,3),230,3,(.6,.72,1)),((0,3,4),350,3,(1,.7,.4))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(3,-5,3));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.9;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=3;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'.dream-loop/pedestrians-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/pedestrians.blend'));(ROOT/'.dream-loop/pedestrians-report.json').write_text(json.dumps(report,indent=2));bpy.ops.render.render(write_still=True)
