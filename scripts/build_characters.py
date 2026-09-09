import bpy, math, random, os, bmesh
from mathutils import Vector
random.seed(821)
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in bpy.data.materials: bpy.data.materials.remove(d)
def mat(name,c,rough=.8,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m
cloth=mat('Weathered charcoal canvas',(.055,.064,.069),.94)
trim=mat('Worn stitched charcoal edges',(.092,.104,.106),.88)
bagcloth=mat('Worn olive charcoal backpack canvas',(.115,.126,.103),.95)
bagpipe=mat('Tan olive backpack seam piping',(.225,.194,.133),.92)
denim=mat('Indigo denim',(.027,.042,.057),.94)
sole=mat('Scuffed ivory rubber',(.38,.36,.30),.92)
leather=mat('Rubber and black leather',(.016,.018,.017),.74)
metal=mat('Aged brass hardware',(.3,.235,.12),.45,.6)
skin=mat('Warm shaded skin',(.25,.145,.095),.85)
red=mat('Washed crimson jacket',(.39,.036,.038),.92)
redtrim=mat('Crimson jacket stitching',(.24,.023,.026),.9)
blackskin=mat('Dark warm brown skin',(.115,.060,.038),.84)
lipskin=mat('Warm brown full lips',(.215,.090,.065),.88)
beardmat=mat('Coarse black full beard',(.011,.014,.011),1)
beardgray=mat('Scattered gray beard hairs',(.125,.129,.113),1)
sclera=mat('Warm subdued eye whites',(.11,.102,.083),.75)
catfur=mat('Ginger tabby fur',(.49,.245,.094),.99)
catstripe=mat('Tabby dark stripes',(.125,.069,.036),.99)
catcream=mat('Tabby cream muzzle paws',(.61,.47,.29),.98)
eye=mat('Cat amber eyes',(.63,.59,.22),.48)
# Packed, original micro-weave surface map: no downloaded textures.
import numpy as np
size=128
yy,xx=np.mgrid[0:size,0:size]
rng=np.random.default_rng(172)
norm=np.ones((size,size,4),dtype=np.float32)
norm[:,:,0]=.5+.13*np.sin(xx*math.tau/4)*(.75+.25*np.cos(yy*math.tau/8))
norm[:,:,1]=.5+.13*np.sin(yy*math.tau/4)*(.75+.25*np.cos(xx*math.tau/8))
norm[:,:,2]=.985
weave=bpy.data.images.new('Original woven canvas normal',width=size,height=size)
weave.colorspace_settings.name='Non-Color';weave.pixels.foreach_set(norm.ravel());weave.pack()
for fabric in [cloth,trim,denim,red,redtrim,bagcloth,bagpipe]:
 nodes=fabric.node_tree.nodes;tex=nodes.new('ShaderNodeTexImage');tex.image=weave;tex.extension='REPEAT'
 normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.28
 fabric.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);fabric.node_tree.links.new(normal.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])

# Original coarse beard curl normal map; no hair particles or downloaded image assets.
hairy,hairx=np.mgrid[0:128,0:128]
hairnormal=np.ones((128,128,4),dtype=np.float32)
hair_rng=np.random.default_rng(898);hairgrain=hair_rng.random((128,128))
for _ in range(2):hairgrain=(hairgrain+np.roll(hairgrain,1,0)+np.roll(hairgrain,-1,0)+np.roll(hairgrain,1,1)+np.roll(hairgrain,-1,1))/5
hairnormal[:,:,0]=.5+1.8*(np.roll(hairgrain,1,0)-np.roll(hairgrain,-1,0))
hairnormal[:,:,1]=.5+1.8*(np.roll(hairgrain,1,1)-np.roll(hairgrain,-1,1))
hairnormal[:,:,2]=.97
beardimage=bpy.data.images.new('Coarse natural beard curl normal',width=128,height=128);beardimage.colorspace_settings.name='Non-Color';beardimage.pixels.foreach_set(hairnormal.ravel());beardimage.pack()
beardtex=beardmat.node_tree.nodes.new('ShaderNodeTexImage');beardtex.image=beardimage
beardnormal=beardmat.node_tree.nodes.new('ShaderNodeNormalMap');beardnormal.inputs['Strength'].default_value=.55
beardmat.node_tree.links.new(beardtex.outputs['Color'],beardnormal.inputs['Color']);beardmat.node_tree.links.new(beardnormal.outputs['Normal'],beardmat.node_tree.nodes.get('Principled BSDF').inputs['Normal'])

# Meshes are smooth custom rings; folds are part of silhouette, not flat primitives.
def parent_obj(o,p): o.parent=p;return o
def empty(name,loc=(0,0,0),p=None):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=loc
 if p:o.parent=p
 return o
def mesh(name,verts,faces,m,p):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(m);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.parent=p
 for f in me.polygons:f.use_smooth=True
 return o
def orb(name,loc,scale,m,p,seg=16,rings=10):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=(0,0,0));o=bpy.context.object;o.name=name;o.parent=p;o.location=loc;o.scale=scale;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def tube(name,pts,r,m,p,seg=6):
 vs=[];fs=[]
 for i,v in enumerate(pts):
  q=Vector(v);t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)])
  t.normalize();u=t.cross(Vector((0,0,1)))
  if u.length<.01:u=t.cross(Vector((0,1,0)))
  u.normalize();w=t.cross(u).normalized();rr=r if isinstance(r,(int,float)) else r[i]
  for j in range(seg):vs.append(q+rr*(math.cos(j*math.tau/seg)*u+math.sin(j*math.tau/seg)*w))
 for i in range(len(pts)-1):
  for j in range(seg):a=i*seg+j;b=i*seg+(j+1)%seg;fs.append((a,b,b+seg,a+seg))
 fs.append(tuple(range(seg-1,-1,-1)));fs.append(tuple((len(pts)-1)*seg+j for j in range(seg)))
 return mesh(name,vs,fs,m,p)
def body(name,rings,m,p,n=24,fold=.005):
 # (z, width radius, depth radius, xcenter, ycenter)
 density=3 if name=='Heavyset red jacket sculpted torso' else (2 if name=='Wrinkled jacket sleeve' else 1)
 if density>1:
  original=rings;sampled=[]
  for q in range(len(original)-1):
   a,b,c,d=[original[max(0,min(j,len(original)-1))] for j in [q-1,q,q+1,q+2]]
   for step in range(density):
    t=step/density;row=[.5*(2*b[j]+(-a[j]+c[j])*t+(2*a[j]-5*b[j]+4*c[j]-d[j])*t*t+(-a[j]+3*b[j]-3*c[j]+d[j])*t*t*t) for j in range(5)];row[0]=b[0]+(c[0]-b[0])*t;sampled.append(tuple(row))
  rings=sampled+[original[-1]]
 def fold_band(z,center,width):return math.exp(-((z-center)/width)**2)-.62*math.exp(-((z-center+.026)/(width*.70))**2)
 vs=[];fs=[]
 for k,(z,rx,ry,cx,cy) in enumerate(rings):
  for j in range(n):
   a=j*math.tau/n;f=fold*(math.sin(a*7+k/density*1.7)+.4*math.sin(a*11-k/density*2.3))
   if name=='Heavyset red jacket sculpted torso':
    xx=rx*math.cos(a);front=max(0,-math.sin(a));offcenter=1-math.exp(-(xx/.055)**2)
    f+=front*offcenter*(.026*fold_band(z,.873+.14*xx,.022)+.017*fold_band(z,.968-.18*xx,.024))
    f+=.018*max(0,abs(math.cos(a))-.4)*fold_band(z,1.18+.13*xx,.027)
   elif name=='Wrinkled jacket sleeve':
    f+=.018*fold_band(z,-.255+.055*math.cos(a),.021)+.010*fold_band(z,-.326-.023*math.cos(a),.018)
   vs.append((cx+(rx+f)*math.cos(a),cy+(ry+f)*math.sin(a),z))
 for k in range(len(rings)-1):
  for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 fs.append(tuple(range(n-1,-1,-1)));fs.append(tuple((len(rings)-1)*n+j for j in range(n)))
 o=mesh(name,vs,fs,m,p)
 if name not in ['Closely cropped hair','Detailed tabby head']:
  mod=o.modifiers.new('Tailored smooth sculpt','SUBSURF');mod.levels=1;mod.render_levels=1
 return o
def seam(name,pts,m,p,r=.004):return tube(name,pts,r,m,p,5)
def foot(p,side,m):
 # custom boot, heel at +Y and broad rounded toe at -Y
 body('Sculpted sneaker upper',[(.035,.078,.152,0,-.045),(.06,.092,.171,0,-.053),(.095,.092,.169,0,-.048),(.14,.075,.14,0,-.027),(.2,.065,.084,0,.018)],m,p,24,.002)
 body('Layered sneaker sole',[(.017,.078,.15,0,-.048),(.023,.095,.174,0,-.052),(.044,.096,.175,0,-.052),(.059,.09,.17,0,-.052)],sole,p,24,.0005)
 for z,y in [(.161,-.083),(.170,-.052),(.183,-.022)]:seam('Crossed shoelace',[(-.04,y,z),(0,y-.012,z+.005),(.04,y,z)],sole,p,.003)
 for x in [-.073,.073]:seam('Sneaker quarter seam',[(x,.08,.1),(x,-.02,.135),(x*.8,-.12,.11)],m,p,.003)
def hands(p,x,y,z,m):
 orb('Relaxed hand',(x,y,z),(.05,.042,.085),m,p)
 for i in range(4):orb('Finger knuckle',(x-.028+i*.018,y-.011,z-.062),(.012,.029,.028),m,p,10,6)
 orb('Thumb',(x-.043 if x<0 else x+.043,y-.024,z+.012),(.023,.027,.042),m,p,10,7)
def leg(p,side,wide=False):
 root=empty('LeftLeg' if side<0 else 'RightLeg',(side*(.12 if not wide else .16),0,.85),p)
 width=.092 if not wide else .116
 body('Creased trouser leg',[(0,width,.105,0,0),(-.12,width*.97,.10,0,0),(-.29,width*.83,.082,side*.006,-.007),(-.39,width*.9,.087,side*.009,-.02),(-.44,width*.77,.078,side*.008,-.017),(-.53,width*.84,.08,0,0),(-.65,width*.71,.073,0,.01),(-.68,width*.73,.072,0,.01)],denim,root,20,.003)
 # boot coordinates offset relative hip
 shoe=empty('Shoe',(0,0,-.85),root);foot(shoe,side,leather)
 seam('Denim side seam',[(side*width,0,-.02),(side*width*.89,0,-.3),(side*width*.84,0,-.43),(side*width*.71,.01,-.67)],denim,root,.003)
 return root
def arm(p,side,wide=False):
 root=empty('LeftArm' if side<0 else 'RightArm',(side*(.235 if not wide else .405),0,1.39 if not wide else 1.40),p)
 m=cloth if not wide else red
 body('Wrinkled jacket sleeve',[(.07,.025,.03,0,0),(.025,.085 if not wide else .12,.085 if not wide else .115,0,0),(-.015,.10 if not wide else .15,.098 if not wide else .13,0,0),(-.065,.095 if not wide else .139,.095 if not wide else .12,side*.035,0),(-.11,.102 if not wide else .143,.103 if not wide else .124,side*.05,-.005),(-.135,.081 if not wide else .123,.082 if not wide else .107,side*.055,-.007),(-.17,.084 if not wide else .125,.086 if not wide else .109,side*.065,-.005),(-.19,.075 if not wide else .116,.08 if not wide else .102,side*.07,-.005),(-.25,.082 if not wide else .117,.085 if not wide else .102,side*.072,-.02),(-.3,.07 if not wide else .09,.07,side*.08,-.03),(-.42,.063 if not wide else .083,.069,side*.082,-.045),(-.47,.061 if not wide else .073,.06,side*.08,-.05)],m,root,20,.004)
 body('Ribbed jacket cuff',[(-.44,.064,.061,side*.08,-.05),(-.46,.062,.059,side*.08,-.05),(-.49,.06,.058,side*.08,-.05)],m,root,20,.001)
 seam('Sleeve stitched seam',[(side*.093,.008,-.03),(side*.145,.006,-.21),(side*.146,-.01,-.35),(side*.139,-.012,-.45)],m,root,.003)
 hands(root,side*.08,-.045,-.555,blackskin if wide else skin)
 return root
def eye_pair(head,m,y=-.13,z=.02,x=.051):
 for s in [-1,1]:
  orb('Deep brown eye',(s*x,y,z),(.013,.01,.008),leather,head,10,6)
  seam('Upper eyelid',[(s*x-.016,y-.001,z+.003),(s*x,y-.003,z+.009),(s*x+.016,y-.001,z+.003)],m,head,.004)
def hood(p):
 h=empty('Head',(0,0,1.605),p);vs=[];fs=[];N=32
 rs=[(-.145,.137,.17,0),(-.1,.184,.224,.016),(-.025,.205,.236,.025),(.07,.201,.234,.029),(.15,.16,.2,.019),(.205,.081,.121,0),(.225,.004,.008,0)]
 for k,(y,rx,rz,cz) in enumerate(rs):
  for j in range(N):
   a=j*math.tau/N;neck=max(0,-math.sin(a));crown=max(0,math.sin(a));weight=math.sin(k*math.pi/(len(rs)-1));relief=weight*(.037*neck*math.sin(5*a+.35)+.016*crown*math.sin(3*a+.7));vs.append((rx*math.cos(a),y+relief,cz+rz*math.sin(a)-.030*neck*weight+.006*weight*math.sin(4*a)+.012*crown*weight*math.exp(-(math.cos(a)/.22)**2)))
 for k in range(len(rs)-1):
  for j in range(N):a=k*N+j;b=k*N+(j+1)%N;fs.append((a,b,b+N,a+N))
 hood_shell=mesh('Deep layered fabric hood',vs,fs,cloth,h)
 hood_smooth=hood_shell.modifiers.new('Sculpted cloth fold smoothing','SUBSURF');hood_smooth.levels=1;hood_smooth.render_levels=1
 rim=[(.139*math.cos(a*math.tau/40),-.148,.173*math.sin(a*math.tau/40)) for a in range(41)];seam('Rolled cloth hood opening rim',rim,trim,h,.016)
 orb('Deep hood shadow',(0,-.081,0),(.131,.072,.165),leather,h)
 orb('Face under hood',(0,-.117,-.011),(.101,.047,.13),skin,h,20,14)
 orb('Nose bridge',(0,-.164,-.025),(.018,.026,.035),skin,h,12,8)
 eye_pair(h,skin,-.162,.022,.041)
 seam('Neutral mouth',[(-.028,-.166,-.067),(0,-.168,-.071),(.027,-.166,-.067)],leather,h,.003)
 for s in [-1,1]:seam('Hood drawcord',[(s*.11,-.15,-.13),(s*.095,-.198,-.2),(s*.093,-.20,-.27)],trim,h,.005)
 crown_path=[]
 for k,(yy,rrx,rrz,ccz) in enumerate(rs):
  ww=math.sin(k*math.pi/(len(rs)-1));crown_path.append((0,yy-.016*ww*math.cos(.7),ccz+rrz+.012*ww+.002))
 seam('Tailored cloth hood center seam',crown_path,trim,h,.0035)
 return h
def backpack(p):
 b=empty('Backpack',(0,.185,1.18),p)
 body('Canvas backpack shell',[(-.31,.15,.10,0,.025),(-.28,.188,.123,0,.035),(-.13,.191,.124,0,.038),(.07,.184,.121,0,.038),(.16,.16,.10,0,.027),(.2,.15,.095,0,.02)],bagcloth,b,24,.003)
 body('Bulging front pocket',[(-.255,.127,.057,0,.151),(-.21,.145,.067,0,.157),(-.11,.134,.063,0,.154),(-.08,.114,.045,0,.139)],bagcloth,b,20,.002)
 body('Overlapping canvas backpack closing flap',[(.09,.125,.012,0,.145),(.105,.158,.024,0,.15),(.164,.156,.025,0,.15),(.199,.113,.020,0,.132)],bagcloth,b,24,.001)
 seam('Raised backpack flap seam',[(-.14,.168,.11),(-.075,.18,.097),(0,.181,.095),(.075,.18,.097),(.14,.168,.11)],bagpipe,b,.005)
 body('Raised woven backpack closing strap',[(-.035,.014,.006,0,.175),(.06,.015,.007,0,.181),(.155,.016,.007,0,.181)],bagpipe,b,12,.0005)
 seam('Rectangular brass backpack strap buckle',[(-.021,.192,-.018),(-.021,.192,.020),(.021,.192,.020),(.021,.192,-.018),(-.021,.192,-.018)],metal,b,.003)
 seam('Pocket zipper',[(-.125,.18,-.096),(-.06,.205,-.082),(0,.211,-.081),(.06,.205,-.082),(.122,.18,-.096)],metal,b,.003)
 seam('Backpack perimeter piping',[(-.16,.12,-.26),(-.186,.14,-.14),(-.18,.135,.05),(-.15,.115,.17),(0,.104,.207),(.15,.115,.17),(.18,.135,.05),(.186,.14,-.14),(.16,.12,-.26)],bagpipe,b,.007)
 for s in [-1,1]:
  seam('Padded shoulder strap',[(s*.115,.07,.18),(s*.175,-.09,.22),(s*.205,-.235,.17),(s*.18,-.3,.05),(s*.13,-.28,-.17),(s*.12,-.09,-.29)],bagcloth,b,.019)
  seam('Side tension strap',[(s*.17,.06,-.07),(s*.185,.17,-.08),(s*.15,.196,-.09)],bagcloth,b,.014)
 seam('Top carry handle',[(-.07,.027,.19),(-.065,.036,.257),(.065,.036,.257),(.07,.027,.19)],bagpipe,b,.012)
 return b
def cat(p):
 c=empty('Cat',(0,.32,1.54),p)
 # face deliberately peers out toward player's rear, visible from follow camera
 orb('Tabby shoulders',(0,0,-.106),(.115,.087,.113),catfur,c)
 orb('Detailed tabby head',(0,.024,.008),(.123,.102,.105),catfur,c,24,16)
 for s in [-1,1]:
  # pointed ears sculpted triangular shell with thickness
  verts=[(s*.055,-.018,.069),(s*.122,-.014,.082),(s*.103,.009,.19),(s*.055,.035,.071),(s*.12,.038,.082)]
  mesh('Pointed cat ear',verts,[(0,1,2),(3,2,4),(0,2,3),(1,4,2),(0,3,4,1)],catfur,c)
  mesh('Dark ear interior',[(s*.069,.039,.082),(s*.113,.04,.086),(s*.102,.021,.161)],[(0,1,2)],catstripe,c)
  orb('Cream cat cheek',(s*.035,.110,-.027),(.045,.024,.029),catcream,c,12,8)
  orb('Alert amber cat eye',(s*.052,.11,.027),(.025,.01,.019),eye,c,12,8)
  orb('Vertical cat pupil',(s*.052,.124,.028),(.006,.005,.015),leather,c,8,6)
  orb('Cat paw over bag',(s*.086,.102,-.147),(.031,.042,.025),catcream,c,12,8)
  for off in [-.01,.01]:seam('Paw toes',[(s*.086+off,.138,-.14),(s*.086+off,.141,-.152)],catstripe,c,.0018)
  for k in range(3):seam('Tabby cheek stripe',[(s*.089,.086,.035-k*.027),(s*.111,.065,.045-k*.027)],catstripe,c,.007)
  for k in [-1,1]:seam('Whisker',[(s*.04,.133,-.027),(s*.102,.144,-.031+k*.009),(s*.163,.149,-.039+k*.018)],catcream,c,.0012)
 for x in [-.048,0,.048]:seam('Tabby forehead stripes',[(x,.083,.063),(x*.7,.066,.09),(x*.6,.028,.112)],catstripe,c,.008)
 orb('Small cat nose',(0,.141,-.011),(.014,.008,.009),catstripe,c,10,6)
 seam('Cat mouth',[(0,.137,-.018),(0,.137,-.036),(-.017,.133,-.042)],catstripe,c,.002)
 tailpts=[(.087,-.01,-.13),(.148,.02,-.19),(.189,.02,-.26),(.184,.055,-.36),(.155,.098,-.411),(.114,.123,-.397)]
 smooth=[];radii=[]
 for i in range(len(tailpts)-1):
  a,b,d,e=[Vector(tailpts[max(0,min(k,len(tailpts)-1))]) for k in [i-1,i,i+1,i+2]]
  for j in range(4):
   t=j/4;smooth.append(.5*((2*b)+(-a+d)*t+(2*a-5*b+4*d-e)*t*t+(-a+3*b-3*d+e)*t*t*t));radii.append(.025-(i+t)*.0032)
 smooth.append(Vector(tailpts[-1]));radii.append(.009)
 tube('Curled tabby tail',smooth,radii,catfur,c,10)
 for k in range(1,5):
  pt=tailpts[k];orb('Tail dark marking',pt,(.024,.024,.011),catstripe,c,10,6)
 return c

def make_player():
 r=empty('Player')
 body('Anatomical jacket with gathered waist',[(.79,.175,.12,0,.012),(.84,.199,.145,0,.006),(.92,.196,.146,0,0),(1.07,.181,.139,0,0),(1.2,.212,.148,0,0),(1.34,.231,.142,0,.008),(1.42,.211,.122,0,.018),(1.465,.122,.087,0,.015)],cloth,r,32,.004)
 body('Gathered jacket hem',[(.795,.179,.13,0,.011),(.82,.201,.15,0,.007),(.846,.196,.146,0,.008)],trim,r,28,.001)
 seam('Main zipper',[(0,-.129,.84),(0,-.155,1.02),(0,-.149,1.20),(0,-.128,1.39)],trim,r,.005)
 for s in [-1,1]:
  seam('Welt pocket',[(s*.087,-.143,.95),(s*.145,-.12,1.055)],trim,r,.009)
  seam('Jacket side seam',[(s*.184,0,.86),(s*.181,.013,1.1),(s*.218,.023,1.31)],trim,r,.003)
 leg(r,-1);leg(r,1);arm(r,-1);arm(r,1);hood(r);backpack(r)
 return r

def make_npc():
 r=empty('NPC')
 body('Heavyset red jacket sculpted torso',[(.78,.264,.200,0,-.005),(.84,.3294,.2379,0,-.012),(.98,.36722,.25986,0,-.043),(1.12,.3648,.2496,0,-.028),(1.27,.3087,.1869,0,.004),(1.41,.273,.151,0,.015),(1.47,.197,.126,0,.018),(1.49,.117,.09,0,.012)],red,r,36,.003)
 body('Elastic red jacket waistband',[(.775,.2664,.2028,0,-.005),(.8,.30378,.22692,0,-.006),(.827,.31964,.2318,0,-.006)],redtrim,r,32,.001)
 # open jacket central inset and ribbed collar
 body('Dark undershirt neckline',[(1.395,.104,.093,0,-.066),(1.47,.09,.075,0,-.058),(1.505,.069,.067,0,-.04)],denim,r,24,0)
 seam('Jacket center zipper',[(0,-.240,.8),(0,-.312,.99),(0,-.255,1.23),(0,-.144,1.44)],metal,r,.006)
 for s in [-1,1]:
  seam('Angled hand warmer pocket',[(s*.19,-.274,.90),(s*.285,-.234,1.025)],redtrim,r,.009)
  seam('Padded collar',[(s*.019,-.151,1.408),(s*.092,-.118,1.487),(s*.118,-.016,1.475)],redtrim,r,.018)
 leg(r,-1,True);leg(r,1,True);arm(r,-1,True);arm(r,1,True)
 h=empty('Head',(0,0,1.70),r);h.scale.x=1.08
 orb('Broad neck',(0,.015,-.166),(.098,.087,.108),blackskin,h)
 # Reference portrait: bald rounded skull, wide cheeks, full nose and calm half-lidded eyes.
 body('Bald rounded reference head',[(-.155,.068,.074,0,-.005),(-.116,.106,.092,0,-.003),(-.060,.129,.107,0,0),(.015,.133,.115,0,.003),(.078,.131,.119,0,.007),(.133,.119,.111,0,.011),(.179,.092,.083,0,.014),(.207,.049,.049,0,.017),(.216,.006,.012,0,.017)],blackskin,h,36,0)
 orb('Natural full muzzle',(0,-.101,-.087),(.079,.035,.060),blackskin,h,24,14)
 for side in [-1,1]:
  orb('Ear',(side*.133,.005,-.010),(.019,.026,.043),blackskin,h,16,10)
  orb('Ear interior shadow',(side*.141,-.015,-.012),(.009,.006,.024),skin,h,12,8)
  # The eyes sit beneath heavy, relaxed eyelids, matching the supplied calm expression.
  orb('Narrow calm sclera',(side*.057,-.110,.041),(.026,.005,.004),sclera,h,20,10)
  orb('Dark brown iris',(side*.057,-.115,.040),(.008,.002,.0045),leather,h,14,8)
  seam('Heavy upper eyelid',[(side*.032,-.104,.044),(side*.048,-.111,.048),(side*.067,-.109,.049),(side*.083,-.099,.044)],blackskin,h,.007)
  seam('Lower relaxed eyelid',[(side*.032,-.102,.034),(side*.056,-.110,.031),(side*.081,-.100,.034)],blackskin,h,.005)
  brow_path=[(side*.028,-.113,.083),(side*.050,-.115,.092),(side*.074,-.105,.086),(side*.095,-.087,.073)];brow_vs=[]
  for i,(xx,yy,zz) in enumerate(brow_path):
   width=[.002,.005,.004,.0005][i];brow_vs.extend([(xx,yy,zz-width),(xx,yy,zz+width)])
  mesh('Natural flat reference eyebrow',brow_vs,[(0,1,3,2),(2,3,5,4),(4,5,7,6)],beardmat,h)
 orb('Broad natural nose bridge',(0,-.117,.007),(.030,.044,.062),blackskin,h,24,16)
 orb('Full rounded nose tip',(0,-.158,-.034),(.031,.031,.027),blackskin,h,24,14)
 for side in [-1,1]:
  orb('Full nose wing',(side*.025,-.143,-.037),(.023,.024,.020),blackskin,h,18,10)
  orb('Nostril shadow',(side*.025,-.162,-.049),(.012,.008,.005),beardmat,h,12,8)
 # Sculpted lip surfaces meet the skin around their edges rather than floating ellipsoids.
 lip_x=[-.056,-.042,-.022,0,.022,.042,.056]
 for lower in [False,True]:
  lip_vs=[];lip_faces=[]
  top=[-.082,-.071,-.069,-.074,-.069,-.071,-.082] if not lower else [-.082]*7
  bottom=[-.082]*7 if not lower else [-.082,-.097,-.104,-.106,-.104,-.097,-.082]
  for row in range(3):
   for i,xx in enumerate(lip_x):
    t=row/2;zz=top[i]+(bottom[i]-top[i])*t;depth=.137+(.013 if row==1 else .001)*max(0,1-(xx/.056)**2);lip_vs.append((xx,-depth,zz))
  for row in range(2):
   for i in range(6):q=row*7+i;lip_faces.append((q,q+1,q+8,q+7))
  lip=mesh('Natural lower lip' if lower else 'Natural upper lip',lip_vs,lip_faces,lipskin,h);mod=lip.modifiers.new('Soft lip contour','SUBSURF');mod.levels=1;mod.render_levels=1
 seam('Calm closed mouth',[(-.048,-.14,-.081),(-.026,-.144,-.082),(0,-.146,-.082),(.026,-.144,-.082),(.048,-.14,-.081)],beardmat,h,.0012)
 # Voxel union blends the reference skull, nose, muzzle, ears and neck into a continuous face.
 skin_parts=[obj for obj in h.children if obj.type=='MESH' and len(obj.data.materials) and obj.data.materials[0]==blackskin]
 bpy.ops.object.select_all(action='DESELECT')
 for obj in skin_parts:
  obj.select_set(True);bpy.context.view_layer.objects.active=obj
  for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
 bpy.context.view_layer.objects.active=skin_parts[0];bpy.ops.object.join();sculpt=bpy.context.object;sculpt.name='Continuous sculpted reference face'
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rem=sculpt.modifiers.new('Sculpted anatomical union','REMESH');rem.mode='VOXEL';rem.voxel_size=.004;rem.adaptivity=.15;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
 sm=sculpt.modifiers.new('Natural skin transitions','SMOOTH');sm.factor=.65;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
 dec=sculpt.modifiers.new('Efficient character face','DECIMATE');dec.ratio=.45;bpy.ops.object.modifier_apply(modifier=dec.name)
 # Full beard wraps the jaw and cheeks; the bald crown deliberately has no cap or hair mesh.
 bvs=[];bfs=[];N=40
 levels=[(-.215,.034,.072,-.024),(-.201,.086,.118,-.018),(-.169,.121,.150,-.009),(-.125,.138,.155,-.003),(.015,.142,.137,0)]
 for k,(zz,rx,ry,cy) in enumerate(levels):
  for j in range(N):
   a=j*math.tau/N;z=zz
   if k==len(levels)-1:z-=.115*max(0,-math.sin(a))**6+.018*max(0,math.sin(a))
   rough=.0035*(math.sin(j*2.3+k)+math.sin(j*1.7-k));bvs.append(((rx+rough)*math.cos(a),cy+(ry+rough)*math.sin(a),z))
 for k in range(len(levels)-1):
  for j in range(N):
   if math.sin((j+.5)*math.tau/N)>.15:continue # beard stops at jaw sides; the back of the bald head stays skin
   a=k*N+j;b=k*N+(j+1)%N;bfs.append((a,b,b+N,a+N))
 beard=mesh('Full broad sculpted beard',bvs,bfs,beardmat,h)
 mod=beard.modifiers.new('Natural beard contour','SUBSURF');mod.levels=1;mod.render_levels=1
 for side in [-1,1]:
  seam('Natural dark moustache',[(side*.057,-.129,-.066),(side*.035,-.143,-.060),(side*.012,-.148,-.058),(0,-.147,-.059)],beardmat,h,.004)
 # Sparse modeled curls provide readable salt-and-pepper texture without a fur particle system.
 beard_rng=random.Random(667)
 for strand in range(120):
  a=math.pi+beard_rng.random()*math.pi;u=.12+beard_rng.random()*.83;q=u*(len(levels)-1);k=min(int(q),len(levels)-2);t=q-k
  z0,rx0,ry0,cy0=levels[k];z1,rx1,ry1,cy1=levels[k+1]
  if k+1==len(levels)-1:z1-=.115*max(0,-math.sin(a))**6
  rx=rx0+(rx1-rx0)*t;ry=ry0+(ry1-ry0)*t;cy=cy0+(cy1-cy0)*t;zz=z0+(z1-z0)*t
  x=rx*math.cos(a);y=cy+ry*math.sin(a);length=.006+beard_rng.random()*.008
  normal=Vector((math.cos(a),math.sin(a),0));base=Vector((x,y,zz))+normal*.002
  pts=[base,base+normal*.0018+Vector((.0015,0,-length*.35)),base+normal*.0007+Vector((-.001,0,-length*.75)),base+Vector((.0005,0,-length))]
  tube('Individual coarse beard curl',pts,.0008 if strand%5 else .00105,beardgray if strand%5==0 else beardmat,h,4)
 for edge_strand in range(30):
  a=math.pi+(edge_strand+.5)*math.pi/30
  zz=.015-.115*max(0,-math.sin(a))**6;nx=math.cos(a);ny=math.sin(a)
  base=Vector((.142*nx,.137*ny,zz));normal=Vector((nx,ny,0));pts=[base-Vector((0,0,.006)),base+normal*.001,base+normal*.002+Vector((.001,0,.005))]
  tube('Soft beard cheek edge curl',pts,.00085,beardmat,h,4)
 # Increase only the jacket torso cross-section, leaving head and legs at human scale.
 for obj in r.children:
  if obj.type=='MESH':obj.scale.x*=1.35;obj.scale.y*=1.35
 return r

def merge_per_group(root):
 groups=[root]+[o for o in root.children_recursive if o.type=='EMPTY']
 for g in groups:
  objs=[o for o in g.children if o.type=='MESH']
  if not objs:continue
  bpy.ops.object.select_all(action='DESELECT')
  for o in objs:o.select_set(True)
  
  for obj in objs:
   bpy.context.view_layer.objects.active=obj
   for mod in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
   bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(obj.data);bm.free()
   uv=obj.data.uv_layers.new(name='Woven surface UV') if not obj.data.uv_layers else obj.data.uv_layers.active
   for polygon in obj.data.polygons:
    axis=max(range(3),key=lambda j:abs(polygon.normal[j]));ax=[j for j in range(3) if j!=axis]
    for li in polygon.loop_indices:
     co=obj.data.vertices[obj.data.loops[li].vertex_index].co;uv.data[li].uv=(co[ax[0]]*18,co[ax[1]]*18)
  bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=g.name+'_Mesh'
  # reduce duplicate material slots using remap
  mats=[];mapping={}
  for i,m in enumerate(o.data.materials):
   if root.name=='Player':
    if g.name in ['LeftArm','RightArm'] and m==skin:m=cloth # practical dark gloves
    if g.name in ['Player','Backpack'] and m==trim:m=cloth
   if m not in mats:mats.append(m)
   mapping[i]=mats.index(m)
  inds=[mapping[p.material_index] for p in o.data.polygons]
  o.data.materials.clear()
  for m in mats:o.data.materials.append(m)
  for p,i in zip(o.data.polygons,inds):p.material_index=i

def export(root,filename):
 bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
 for o in root.children_recursive:o.select_set(True)
 bpy.context.view_layer.objects.active=root
 bpy.ops.export_scene.gltf(filepath=os.path.join(BASE,'public/assets',filename),use_selection=True,export_format='GLB',export_yup=True,export_apply=True,export_animations=False)
 tris=sum(len(o.data.loop_triangles) for o in root.children_recursive if o.type=='MESH')
 for o in root.children_recursive:
  if o.type=='MESH':o.data.calc_loop_triangles()
 tris=sum(len(o.data.loop_triangles) for o in root.children_recursive if o.type=='MESH')
 draws=sum(len(o.data.materials) for o in root.children_recursive if o.type=='MESH')
 print('CHARACTER_RESULT',filename,'triangles',tris,'draws',draws)

player=make_player();npc=make_npc();merge_per_group(player);merge_per_group(npc)
export(player,'player.glb')
for o in [player]+list(player.children_recursive):o.name='PlayerSource_'+o.name
for o in [npc]+list(npc.children_recursive):
 if '.' in o.name:o.name=o.name.split('.')[0]
export(npc,'npc.glb')
npc.location.x=1.0;player.location.x=-.8
# source file includes studio preview rig, exports above are pure characters
world=bpy.context.scene.world or bpy.data.worlds.new('Studio');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.17,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
for loc,power,size,col in [((2,-3,5),650,4,(1,.79,.6)),((-3,-1,3),350,3,(.55,.7,1)),((0,3,4),700,3,(1,.5,.24))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(3.1,-5,3.1));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=3.5;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(BASE,'.dream-loop/characters-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE,'.dream-loop/characters.blend'))
bpy.ops.render.render(write_still=True)
cam.location=(3,5,3);cam.rotation_euler=(Vector((0,0,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(BASE,'.dream-loop/characters-back-preview.png');bpy.ops.render.render(write_still=True)
