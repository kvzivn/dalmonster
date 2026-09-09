"""Original Blender street-arrival ensemble. Uses this project's hand-authored bicycle
construction helpers; all new props are built here and batched by material/zone.
Coordinates are Blender east/north/up, exported glTF Y-up.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'scripts/build_props.py').read_text().split('with open(os.path.join(BASE,\'src/layout.json\'))')[0]
exec(compile(source,str(ROOT/'scripts/build_props.py'),'exec'))
from collections import defaultdict
import json
# Quiet worn materials: close-up geometry supplies relief, never overbright colors.
wood=mat('Cosy weathered oak',(.20,.115,.056),.92)
woodlight=mat('Cosy rubbed oak endgrain',(.285,.177,.085),.91)
wooddark=mat('Cosy timber joints',(.077,.042,.020),1)
canvasred=mat('Cosy burgundy canvas',(.205,.037,.045),1)
canvascream=mat('Cosy faded linen canvas',(.49,.415,.298),1)
chalk=mat('Cosy warm chalk lettering',(.73,.66,.48),1,0,.10)
chalkboard=mat('Cosy chalkboard',(.023,.038,.033),1)
poster=mat('Cosy offwhite poster paper',(.57,.54,.42),1)
posterred=mat('Cosy brick red poster ink',(.38,.073,.037),1)
posterblue=mat('Cosy petrol blue enamel',(.036,.106,.122),.83,.18)
leafgreen=mat('Cosy living herbs',(.083,.13,.052),1)
fruitred=mat('Cosy autumn red apples',(.34,.046,.023),.78)
fruityellow=mat('Cosy muted golden pears',(.38,.26,.052),.84)
bread=mat('Cosy baked cinnamon bread',(.32,.151,.049),.97)
terracotta=mat('Cosy dark terracotta',(.21,.094,.048),.97)
soil=mat('Cosy pot soil',(.048,.039,.024),1)
stone=mat('Cosy worn tactile granite',(.30,.307,.267),.96)
glass=mat('Cosy dusty olive glass',(.031,.073,.038),.31,.12)
warm=mat('Cosy warm shop lamp diffuser',(.95,.59,.21),.48,0,.65)

obstacles=[]
def circle_obstacle(p,r,name):
 v=p.matrix_world.translation;obstacles.append(dict(x=round(v.x,3),z=round(-v.y,3),radius=r,name=name))
def newroot(name,loc,angle=0):
 p=root(name,loc[0],-loc[1]);p.location.z=loc[2];p.rotation_euler.z=angle;return p
def box(n,loc,sz,m,p,b=.007):return cube(n,loc,sz,m,p,b)
def line(n,a,b,r,m,p):return rod(n,a,b,r,m,p,8)
def lettering(s,loc,size,m,p,side=1):return text('Original Swedish lettering '+s,s,loc,size,m,p,(math.pi/2,0,math.pi if side==1 else 0))
def lathe(name,profile,m,p,n=20):
 vs=[];fs=[]
 for z,r in profile:
  for j in range(n):a=j*math.tau/n;vs.append((r*math.cos(a),r*math.sin(a),z))
 for k in range(len(profile)-1):
  for j in range(n):q=k*n+j;r=k*n+(j+1)%n;fs.append((q,r,r+n,q+n))
 return mesh(name,vs,fs,m,p)
def localpot(parent,x,y,z,rad=.22):
 p=bpy.data.objects.new('Tapered terracotta herb pot',None);bpy.context.collection.objects.link(p);p.parent=parent;p.location=(x,y,z)
 lathe('Real hollow rounded terracotta rim',[(0,rad*.64),(.015,rad*.68),(.36,rad),(.395,rad*1.03),(.405,rad*.96),(.385,rad*.90),(.34,rad*.88)],terracotta,p)
 o=orb('Recessed pot earth',(0,0,.35),(rad*.86,rad*.86,.018),soil,p)
 for i in range(11):
  a=i*2.4;rr=rad*random.uniform(.15,.7);x=math.cos(a)*rr;y=math.sin(a)*rr;h=random.uniform(.15,.32)
  line('Sparse rosemary stem',(x,y,.36),(x+.026,y-.012,.36+h),.0038,wood,p)
  for j in range(4):
   zz=.39+h*j/4
   for sign in [-1,1]:
    vs=[(x,y,zz),(x+sign*.041,y-.012,zz+.022),(x+sign*.026,y+.009,zz+.032)]
    mesh('Small rosemary blades',vs,[(0,1,2),(2,1,0)],leafgreen,p)
 return p

a=math.radians(134);r=30.3
shop=newroot('Building_North_Cosy_Shop',(r*math.cos(a),r*math.sin(a),.163),a)
# Awning with gently sagging fabric and tailored scalloped valance; canopy is a
# continuous eighteen-band construction rather than heavy rectangular blocks.
W=3.9;stripes=18
for i in range(stripes):
 x0=-W/2+i*W/stripes;x1=x0+W/stripes;m=canvasred if i%2==0 else canvascream
 vs=[]
 for j in range(9):
  v=j/8;y=.08+v*1.15;zz=3.27-.39*v-.045*math.sin(v*math.pi)
  for x in [x0,x1]:vs.append((x,y,zz-.015*math.sin((x-x0)/(x1-x0)*math.pi)))
 fs=[(j*2,j*2+1,j*2+3,j*2+2) for j in range(8)];mesh('Tailored canvas canopy strip',vs,fs,m,shop)
 # curved draped bottom scallop with stitched raised border
 vs=[]
 for j in range(9):
  x=x0+(x1-x0)*j/8;zz=2.66-.044*math.sin(j/8*math.pi)
  vs.extend([(x,1.232,2.88),(x,1.232,zz)])
 mesh('Scalloped canvas valance',vs,[(j*2,j*2+2,j*2+3,j*2+1) for j in range(8)],m,shop)
for x in [-1.80,1.80]:
 tube('Slender folding awning arms',[(x,.10,3.21),(x,.58,2.95),(x,1.23,2.83)],.016,iron,shop,8)
line('Awning valance roller',(-1.97,1.21,2.875),(1.97,1.21,2.875),.021,iron,shop)
# Brass shop lettering is deliberately compact, like a local late-night grocer.
box('Timber signboard', (0,.081,3.60),(3.86,.14,.48),wooddark,shop,.025)
for zz in [3.391,3.807]:box('Raised signboard molding',(0,.161,zz),(3.84,.025,.027),woodlight,shop,.005)
lettering('HÖRNETS LIVS',(0,.165,3.47),.235,chalk,shop)
# One enameled wall lamp with bracket, shade and visible frosted bulb.
for x in [-2.07]:
 box('Wall lamp mount',(x,.12,2.56),(.13,.11,.22),iron,shop,.02)
 tube('Lamp curved bracket',[(x,.15,2.56),(x,.32,2.66),(x,.40,2.57)],.018,iron,shop,10)
 orb('Domed lamp cap',(x,.40,2.58),(.18,.18,.052),iron,shop)
 orb('Frosted enclosed warm bulb',(x,.40,2.47),(.086,.086,.115),warm,shop)
 line('Lamp brass base',(x,.40,2.33),(x,.40,2.37),.095,brass,shop)
# Wooden shop crates with real separate slats, corner risers, handles and labels.
def crate(parent,cx,cy,cz,typ=0):
 pp=bpy.data.objects.new('Produce crate',None);bpy.context.collection.objects.link(pp);pp.parent=parent;pp.location=(cx,cy,cz)
 for i in range(5):box('Crate floor board',((i-2)*.12,0,.025),(.113,.43,.041),wood if i%2 else woodlight,pp,.005)
 for x in [-.31,.31]:
  for y in [-.21,.21]:box('Crate corner post',(x,y,.17),(.035,.035,.29),woodlight,pp,.004)
 for zz in [.08,.165,.25]:
  for y in [-.229,.229]:box('Individual produce crate slat',(0,y,zz),(.66,.027,.064),wood,pp,.004)
 for x in [-.326,.326]:
  for zz in [.08,.165]:box('Crate end slat',(x,0,zz),(.026,.44,.064),woodlight,pp,.004)
  for y in [-.168,.168]:box('Handhold ends',(x,y,.253),(.026,.12,.061),woodlight,pp,.004)
  box('Handhold upper lip',(x,0,.282),(.026,.43,.018),woodlight,pp,.004)
 for ix in range(4):
  for iy in range(3):
   x=(ix-1.5)*.133+random.uniform(-.012,.012);y=(iy-1)*.128+random.uniform(-.01,.01);z=.13+random.uniform(-.007,.012)
   if typ==0:
    orb('Hand modeled irregular apple',(x,y,z),(.062,.061,.061),fruitred,pp)
    line('Apple woody stem',(x,y,z+.049),(x+.003,y,z+.072),.0028,wooddark,pp)
   elif typ==1:
    orb('Pear lower body',(x,y,z),(.052,.052,.068),fruityellow,pp);orb('Pear taper',(x+.006,y,z+.062),(.03,.03,.034),fruityellow,pp)
   else:
    ring('Cinnamon bun spiral',(x,y,z),.042,.016,bread,pp,n=14)
 box('Produce price label',(0,.25,.22),(.205,.009,.095),poster,pp,.002)
 lettering('ÄPPLEN  25' if typ==0 else 'PÄRON  29' if typ==1 else 'BULLAR  20',(0,.258,.195),.032,wooddark,pp)
 return pp
# Stack sits beside the doorway rather than across the walking line.
for x,y,z,typ in [(-2.2,.45,.0,0),(-2.2,.45,.31,0),(-2.2,.99,0,1),(1.99,.43,0,2)]:crate(shop,x,y,z,typ)
localpot(shop,2.15,.94,0,.20)
# Three dimensional standing chalkboard, with angled easel legs and brass hinge.
cb=bpy.data.objects.new('Freestanding menu easel',None);bpy.context.collection.objects.link(cb);cb.parent=shop;cb.location=(1.65,1.48,0);cb.rotation_euler.z=-.16
for s in [-1,1]:
 for y in [-.25,.25]:line('Menu easel splayed leg',(s*.34,y,0),(s*.30,0,1.10),.022,woodlight,cb)
box('Recessed chalk face',(0,.012,.65),(.61,.035,.77),chalkboard,cb,.009)
for x in [-.335,.335]:box('Menu side rails',(x,.025,.66),(.043,.056,.87),woodlight,cb,.006)
for zz in [.218,1.083]:box('Menu horizontal rail',(0,.024,zz),(.71,.062,.04),woodlight,cb,.006)
for s,zz,sz in [('KAFFE',.88,.119),('BULLAR',.69,.109),('ÖPPET',.43,.104)]:lettering(s,(0,.05,zz),sz,chalk,cb)
line('Menu chalk underline',(-.2,.05,.645),(.2,.05,.645),.003,chalk,cb)
# Make the sidewalk width at this constrained return explicit for root collisions.
bpy.context.view_layer.update()
for local,radius,n in [((-2.2,.70,.3),.60,'produce display'),((1.65,1.48,.4),.43,'chalkboard'),((2.15,.94,.3),.23,'herb pot')]:
 v=shop.matrix_world@Vector(local);obstacles.append(dict(x=round(v.x,3),z=round(-v.y,3),radius=radius,name=n))

# Furniture on the opposite sidewalk, along the road. Keep central asphalt clear.
street_angle=math.radians(142.5);d=Vector((math.cos(street_angle),math.sin(street_angle),0));side=Vector((-math.sin(street_angle),math.cos(street_angle),0))
def P(t,l,z=.163):return d*t+side*l+Vector((0,0,z))
bench=newroot('Cosy_Street_SlattedBench',P(40.2,5.50),street_angle)
for x in [-.68,.68]:
 tube('Bent cast iron bench support',[(x,-.30,0),(x,-.23,.34),(x,.21,.35),(x,.28,0)],.032,iron,bench,10)
 tube('Curved bench back support',[(x,.18,.31),(x,.23,.56),(x,.30,.93)],.026,iron,bench,10)
for j in range(5):box('Individually worn bench seat plank',(0,-.21+j*.094,.42),(1.74,.082,.055),wood if j%2 else woodlight,bench,.011)
for j in range(4):box('Bench back slat',(0,.267+.019*j,.59+j*.102),(1.74,.045,.083),wood if j%2 else woodlight,bench,.009)
for x in [-.68,.68]:
 for j in range(5):orb('Bench countersunk seat bolt',(x,-.21+j*.094,.45),(.007,.007,.0025),iron,bench)
# Reference-inspired pale green municipal metal bench at the open street mouth.
palegreen=mat('Cosy worn pale green bench enamel',(.245,.345,.273),.81,.34)
greenbench=newroot('Cosy_Street_PaleGreenBench',P(25.0,-5.1),street_angle)
for x in [-.68,.68]:
 tube('Green bench tubular leg frame',[(x,-.26,0),(x,-.19,.43),(x,.21,.43),(x,.29,0)],.025,iron,greenbench,10)
 tube('Green bench rear support',[(x,.20,.34),(x,.28,.82),(x,.24,.94)],.022,iron,greenbench,10)
for j in range(11):
 y=-.245+j*.045
 box('Narrow enamel seat slat',(0,y,.46),(1.64,.032,.022),palegreen,greenbench,.007)
for j in range(9):
 z=.575+j*.041
 box('Narrow enamel backrest slat',(0,.25+(z-.57)*.12,z),(1.64,.022,.029),palegreen,greenbench,.007)
for x in [-.77,.77]:tube('Green bench rounded armrest',[(x,-.20,.46),(x,-.25,.65),(x,-.17,.70),(x,.20,.70),(x,.26,.62)],.018,palegreen,greenbench,10)
# Authored bicycles use fully modeled spokes, brakes, mudguards, pedals, racks.
for t,l,heading in [(27.2,4.55,street_angle+.10),(37.9,6.50,street_angle-.13)]:
 pos=P(t,l);bike=bicycle(pos.x,-pos.y,heading);bike.name='Cosy_Street_CityBicycle';bike.location.z=.163
 # Original constructor leans frame in local X; retain it.
for t in [26.5,28.1,36.8]:
 rack=newroot('Cosy_Street_BicycleHoop',P(t,4.70),street_angle)
 tube('Bent steel Sheffield bicycle stand',[(-.38,0,0),(-.38,0,.66),(-.35,0,.75),(-.27,0,.78),(.27,0,.78),(.35,0,.75),(.38,0,.66),(.38,0,0)],.021,iron,rack,10)
 for x in [-.38,.38]:box('Bike rack base shoe',(x,0,.013),(.13,.11,.026),iron,rack,.006)
# Local public notice board, clear readable typography and irregular paper edges.
notice=newroot('Cosy_Street_NoticeBoard',P(38.0,5.78),street_angle)
for x in [-.45,.45]:line('Notice board slender support',(x,0,0),(x,0,2.13),.035,iron,notice)
box('Notice board rear enamel',(0,0,1.44),(1.07,.10,1.33),posterblue,notice,.025)
for x in [-.495,.495]:box('Notice metal rolled edge',(x,.064,1.45),(.037,.045,1.28),iron,notice,.007)
for zz in [.80,2.10]:box('Notice frame top and bottom',(0,.064,zz),(1.03,.045,.039),iron,notice,.007)
for xx,zz,w,h,inkmat,word in [(-.23,1.68,.41,.62,posterred,'LIVE'),(.24,1.67,.40,.59,posterblue,'MÖLLAN'),(-.23,1.05,.40,.40,posterblue,'LOPPIS'),(.24,1.08,.41,.46,posterred,'09 / 11')]:
 box('Layered local event poster',(xx,.059,zz),(w,.007,h),poster,notice,.001)
 lettering(word,(xx,.067,zz+.03),.065,inkmat,notice)
 for q in range(3):box('Poster small printed line',(xx,.069,zz-.065-q*.024),(w*.72,.004,.006),inkmat,notice,.001)
 for s in [-1,1]:orb('Small drawing pin',(xx+s*w*.42,.070,zz+h*.44),(.007,.003,.007),brass,notice)
# A slender two-sided local cultural poster lightbox, inspired by the supplied
# street photographs. The diffuse panel glows softly instead of adding a lamp.
posterlight=mat('Cosy softly backlit cultural poster',(.45,.37,.24),.92,0,.32)
lightbox=newroot('Cosy_Street_PosterLightbox',P(24.2,5.05),street_angle)
box('Poster lightbox granite footing',(0,0,.055),(.80,.34,.11),stone,lightbox,.024)
for x in [-.32,.32]:box('Slim steel lightbox legs',(x,0,.47),(.046,.09,.77),iron,lightbox,.009)
box('Poster lightbox slim outer housing',(0,0,1.49),(.82,.17,1.92),iron,lightbox,.028)
for sign in [-1,1]:
 box('Softly backlit recessed poster',(0,sign*.094,1.49),(.72,.012,1.81),posterlight,lightbox,.009)
 # Uneven screen-printed dusk sun and simple editorial linework.
 ring('Poster printed sun',(0,sign*.104,1.95),.17,.027,posterred,lightbox,n=28)
 for i in range(7):box('Poster block printed skyline',((i-3)*.072,sign*.11,1.62),(.051,.004,.08+(i%3)*.048),posterblue,lightbox,.001)
 for body,z,sz in [('KVÄLL',1.37,.115),('PÅ MÖLLAN',1.21,.067),('LIVE 21:00',.85,.064)]:lettering(body,(0,sign*.11,z),sz,posterblue,lightbox,side=sign)
 for z in [1.07,1.035,1.0]:box('Poster fine-print line',(0,sign*.112,z),(.43,.003,.007),posterblue,lightbox,.001)
# Hollow litter bin and two well-worn utility cabinets with door seams/hinges.
for t,l in [(41.6,6.0),(45.2,5.70)]:
 p=newroot('Cosy_Street_UtilityCabinet',P(t,l),street_angle)
 box('Old municipal cabinet shell',(0,0,.59),(.63,.37,1.18),boxgreen,p,.026)
 box('Cabinet recessed door',(0,-.195,.60),(.545,.014,1.055),iron,p,.011)
 box('Painted cabinet door face',(0,-.205,.60),(.524,.010,1.027),boxgreen,p,.008)
 for x in [-.248]:
  for zz in [.29,.86]:box('Cabinet barrel hinge',(x,-.225,zz),(.022,.022,.061),iron,p,.006)
 box('Utility door handle',(.205,-.239,.62),(.013,.022,.10),iron,p,.005)
 for x,z,w,h in [(-.12,.77,.12,.14),(.10,.93,.15,.06),(.05,.38,.22,.15)]:
  box('Faded torn sticker',(x,-.216,z),(w,.003,h),poster,p,.001)
  box('Sticker ruled ink',(x,-.220,z),(w*.74,.002,.008),posterred,p,.001)
 # ventilation louvers read in grazing light.
 for z in [.17,.20,.23]:box('Stamped ventilation louver',(0,-.221,z),(.31,.012,.009),iron,p,.001)
# Small human-scale protection bollards with molded feet and scuffed top band.
for t,l in [(24.7,4.39),(29.3,4.20),(39.9,4.39)]:
 p=newroot('Cosy_Street_Bollard',P(t,l),street_angle)
 lathe('Cast iron bollard profile',[(0,.105),(.05,.11),(.08,.064),(.64,.056),(.69,.07),(.735,.045),(.747,0)],iron,p,14)
 lathe('Worn pale bollard reflective band',[(.55,.058),(.59,.058)],white,p,14)
# Drain mouths and tactile granite bands at the street mouth, localized wear.
for t,l in [(23.35,-3.68),(29.0,3.68),(37.7,3.68)]:
 p=newroot('Cosy_Street_DrainDetail',P(t,l,.025),street_angle)
 box('Granite inlet surround',(0,0,0),(.75,.39,.025),stone,p,.015)
 box('Dark recessed inlet', (0,0,.015),(.61,.29,.012),iron,p,.007)
 for j in range(9):box('Drain raised diagonal rib',(-.26+j*.065,0,.026),(.024,.275,.018),iron,p,.003)
for sideSign in [-1,1]:
 p=newroot('Cosy_Street_TactileCrossing',P(23.4,sideSign*4.48),street_angle)
 for x in [-.35,0,.35]:
  box('Worn tactile granite slab',(x,0,.005),(.338,.70,.018),stone,p,.005)
  for row in range(7):
   for col in range(3):orb('Rounded tactile warning stud',(x+(col-1)*.085,(row-3)*.087,.022),(.018,.018,.007),stone,p)
# Two bottles and a folded takeaway carton beside bench/bin, never random scatter.
for t,l in [(39.72,5.78),(39.9,5.70)]:
 p=newroot('Cosy_Street_ReturnBottle',P(t,l),street_angle)
 lathe('Molded return bottle',[(0,.035),(.015,.040),(.20,.04),(.235,.016),(.285,.016),(.294,.019)],glass,p,12)
 lathe('Paper bottle label',[(.075,.041),(.145,.041)],poster,p,12)
# Physical dead-end: road-width reflective municipal A-frames and cones make the
# final playable limit readable before the t42 collision boundary.
barrier=newroot('Cosy_Street_ApproachBarrier',P(41.5,0,.013),street_angle+math.pi/2)
for x in [-3.40,-1.15,1.15,3.40]:
 for sy in [-1,1]:
  line('Barrier splayed galvanized leg',(x,sy*.31,.015),(x,0,.87),.027,chrome,barrier)
  box('Barrier rubber stabilizing foot',(x,sy*.31,.025),(.17,.17,.05),rubber,barrier,.014)
 line('A-frame pivot pin',(x,-.065,.79),(x,.065,.79),.027,chrome,barrier)
 line('Barrier leg spreader',(x,-.18,.31),(x,.18,.31),.012,chrome,barrier)
for cx in [-2.0,2.0]:
 box('Weathered cream reflective barrier rail',(cx,0,.75),(3.95,.073,.29),chalk,barrier,.015)
 box('Lower barrier rail',(cx,.025,.36),(3.95,.055,.13),chalk,barrier,.01)
 for sideSign in [-1,1]:
  y=sideSign*.039
  for i in range(8):
   x=cx-1.84+i*.46
   mesh('Clipped diagonal red barrier stripe',[(x,y,.608),(x+.19,y,.608),(x+.36,y,.891),(x+.17,y,.891)],[(0,1,2,3)] if sideSign<0 else [(3,2,1,0)],posterred,barrier)
  for i in range(8):box('Red lower reflective marker',(cx-1.65+i*.46,sideSign*.056,.36),(.20,.003,.104),posterred,barrier,.001)
box('Street closure enamel notice',(0,.07,.45),(1.03,.043,.33),chalk,barrier,.012)
lettering('ARBETE PÅGÅR',(0,.098,.405),.080,wooddark,barrier)
for lateral in [-5.18,-4.55,4.55,5.18]:
 pcone=newroot('Cosy_Street_ApproachCone',P(40.8,lateral,.163 if abs(lateral)>4 else .013),street_angle)
 box('Heavy cone rubber foot',(0,0,.03),(.38,.38,.06),rubber,pcone,.025)
 lathe('Faded red orange cone vinyl',[(.06,.145),(.235,.102)],posterred,pcone,18)
 lathe('Cone cream reflective cuff',[(.235,.102),(.34,.073)],chalk,pcone,18)
 lathe('Cone tapered upper',( (.34,.073),(.54,.025),(.545,.018)),posterred,pcone,18)
# Close the former Folkets Park gate with the exact existing wall material family.
# This geometry is separately named so the root can remove the old gate entirely.
with bpy.data.libraries.load(str(ROOT/'.dream-loop/environment.blend'),link=False) as (src,dst):
 dst.materials=[name for name in ['Graffiti_Wall','Stone_Dark','Stone_Trim','Brick'] if name in src.materials]
wallm={m.name:m for m in dst.materials}
closure=newroot('Park_WallClosure',(23,6,0),0)
box('Continuous rendered park wall infill',(0,0,1.2),(.48,6.04,2.4),wallm['Graffiti_Wall'],closure,.012)
# Individual coping blocks have close joints and slightly varied edge wear.
for i in range(10):box('Individual granite wall coping',(0,-2.70+i*.6,2.44),(.70,.593,.18),wallm['Stone_Dark'],closure,.016)
for yy in [-2.86,2.86]:
 box('Brick infill end pier',(-.06,yy,1.32),(.79,.66,2.64),wallm['Brick'],closure,.009)
 box('Infill pier capstone',(-.06,yy,2.69),(.98,.83,.15),wallm['Stone_Trim'],closure,.015)
 for j in range(13):box('Recessed brick pier bed joint',(-.478,yy,j*.19+.12),(.013,.67,.019),wallm['Stone_Dark'],closure,.002)
for z in [.11,.32]:box('Brick wall damp proof plinth',(-.26,0,z),(.04,6.04,.14),wallm['Brick'],closure,.004)
# Object-sized collision hints for the host; flush paving/drains remain traversable.
bpy.context.view_layer.update()
for ob in bpy.context.scene.objects:
 if ob.parent or ob.type != 'EMPTY':continue
 sizes={'Cosy_Street_SlattedBench':.96,'Cosy_Street_PaleGreenBench':.91,'Cosy_Street_CityBicycle':.72,'Cosy_Street_NoticeBoard':.58,'Cosy_Street_PosterLightbox':.48,'Cosy_Street_UtilityCabinet':.40,'Cosy_Street_Bollard':.12,'Cosy_Street_ApproachCone':.21,'Cosy_Street_BicycleHoop':.43}
 for prefix,radius in sizes.items():
  if ob.name.startswith(prefix):circle_obstacle(ob,radius,prefix.replace('Cosy_Street_',''))
# Batch the entire ensemble into material draws separately for attached storefront
# and independent street props. This preserves architecture occlusion grouping.
bpy.context.view_layer.update();batches=defaultdict(list)
# Guard against props silently vanishing into the existing curved block ends.
for ob in bpy.context.scene.objects:
 if ob.type != 'MESH':continue
 rt=ob
 while rt.parent:rt=rt.parent
 if rt==shop:continue
 bad=[]
 for v in ob.data.vertices:
  q=ob.matrix_world@v.co;rr=math.hypot(q.x,q.y);aa=math.degrees(math.atan2(q.y,q.x))%360
  if q.z>.19 and ((27<rr<35 and 39<aa<134) or (29<rr<37 and 151<aa<218)):
   bad.append(tuple(round(c,2) for c in q));break
 if bad:print('FOOTPRINT WARNING',rt.name,ob.name,bad[0])

for ob in list(bpy.context.scene.objects):
 if ob.type!='MESH':continue
 rt=ob
 while rt.parent:rt=rt.parent
 zone='Building_North_Cosy' if rt==shop else 'Park_WallClosure' if rt==closure else 'Cosy_Street'
 for matIndex,m in enumerate(ob.data.materials):
  polys=[p for p in ob.data.polygons if p.material_index==matIndex]
  if not polys:continue
  vs=[tuple(ob.matrix_world@v.co) for v in ob.data.vertices];fs=[tuple(p.vertices) for p in polys]
  batches[(zone,m)].append((vs,fs))
for ob in list(bpy.context.scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
triangles=0
for (zone,m),pieces in batches.items():
 vs=[];fs=[]
 for verts,faces in pieces:
  off=len(vs);vs.extend(verts);fs.extend(tuple(off+i for i in f) for f in faces)
 me=bpy.data.meshes.new(zone+'_'+m.name);me.from_pydata(vs,[],fs);me.materials.append(m);me.update()
 ob=bpy.data.objects.new(zone+'_'+m.name,me);bpy.context.collection.objects.link(ob)
 # Recalculate consistent hard-surface normals; weighted normals preserve flat
 # planks while curved tires and pipes retain their small geometric facets.
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 me.calc_loop_triangles();triangles+=len(me.loop_triangles)
 # All geometries receive physical-size UVs for future surface texture passes.
 uv=me.uv_layers.new(name='SurfaceUV')
 for face in me.polygons:
  axis=max(range(3),key=lambda i:abs(face.normal[i]))
  for li in face.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[(axis+1)%3]*1.2,v[(axis+2)%3]*1.2)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/cosy-street.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/cosy-street.glb'),export_format='GLB',export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
(ROOT/'public/assets/cosy-street-obstacles.json').write_text(json.dumps(obstacles,indent=2))
print('COSY STREET RESULT',len(batches),'draws',triangles,'triangles')
# A bounded preview uses inexpensive Eevee; no persistent render job remains.
world=bpy.data.worlds.new('Preview ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.1,.13,.19,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;bpy.context.scene.world=world
for loc,power,size in [((r*math.cos(a)-4,r*math.sin(a)-2,7),1800,6),((r*math.cos(a)+3,r*math.sin(a)-2,4),650,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((r*math.cos(a),r*math.sin(a),1.5))-o.location).to_track_quat('-Z','Y').to_euler()
target=Vector((r*math.cos(a),r*math.sin(a),1.5));camPos=target+Vector((-7,-6,4));bpy.ops.object.camera_add(location=camPos);cam=bpy.context.object;cam.rotation_euler=(target-camPos).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.render.threads_mode='FIXED';scene.render.threads=3;scene.render.resolution_x=1100;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'.dream-loop/cosy-street-preview.png');bpy.ops.render.render(write_still=True)
