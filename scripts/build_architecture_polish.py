"""Reference-led Malmö apartment architecture. Original Blender geometry, existing generated mineral texture.
Replaces Building_North_* and Building_West_* from environment-final.glb. Coordinates Blender Z-up.
"""
import bpy, bmesh, math, random, json
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
rng=random.Random(38129)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parts=defaultdict(lambda:[[],[],[],[]]);mats={}
def material(name,color,rough=.8,metal=0,emit=0,texture=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emit:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
 if texture:
  image=bpy.data.images.load(str(ROOT/'public/assets/granite-grain.png'),check_existing=True);image.pack();tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=image;m.node_tree.links.new(tx.outputs['Color'],p.inputs['Base Color'])
 mats[name]=m
material('Cosy_LimeIvory',(.72,.67,.53),.94)
material('Cosy_LimeOchre',(.48,.34,.20),.95)
material('Cosy_RoseRustication',(.44,.235,.175),.93)
material('Cosy_StoneBase',(.265,.27,.245),.91)
material('Cosy_PaleLimestone',(.58,.57,.47),.91)
material('Cosy_WhitePaint',(.57,.57,.49),.68)
material('Cosy_RedCopper',(.245,.075,.048),.53,.43)
material('Cosy_Terracotta',(.285,.098,.057),.92)
material('Cosy_TileShadow',(.125,.05,.029),.94)
material('Cosy_Glass',(.025,.047,.049),.28,.25)
material('Cosy_WarmRoom',(.71,.375,.11),.98,0,.65)
material('Cosy_DimRoom',(.32,.25,.16),.99,0,.2)
material('Cosy_DarkRoom',(.035,.049,.058),.22,.30)
material('Cosy_CurtainCream',(.40,.345,.25),.98)
material('Cosy_CurtainBlue',(.085,.14,.16),.98)
material('Cosy_DarkWood',(.085,.060,.036),.92)
material('Cosy_Iron',(.042,.057,.048),.63,.58)
material('Cosy_Brass',(.35,.215,.07),.49,.6)
material('Cosy_LampGlass',(1,.55,.16),.52,0,2)
material('Cosy_ShopBack',(.095,.065,.034),.96,0,.15)
material('Cosy_ShopAmber',(.55,.25,.055),.84,0,.7)
material('Cosy_ProductCream',(.47,.405,.27),.94)
material('Cosy_ProductOchre',(.245,.13,.041),.93)
material('Cosy_ProductGreen',(.055,.095,.053),.61)
texture_factors={'Cosy_LimeIvory':(1.0,1.0,.93,1),'Cosy_LimeOchre':(.70,.54,.35,1),'Cosy_RoseRustication':(.63,.37,.31,1),'Cosy_PaleLimestone':(.83,.86,.76,1),'Cosy_StoneBase':(.40,.43,.41,1)}
if (ROOT/'public/assets/lime-plaster.png').exists():
 image=bpy.data.images.load(str(ROOT/'public/assets/lime-plaster.png'),check_existing=True);image.pack()
 for name,factor in texture_factors.items():
  m=mats[name];nodes=m.node_tree.nodes;bs=nodes.get('Principled BSDF');tx=nodes.new('ShaderNodeTexImage');tx.image=image
  mul=nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;mul.inputs[2].default_value=factor
  m.node_tree.links.new(tx.outputs['Color'],mul.inputs[1]);m.node_tree.links.new(mul.outputs['Color'],bs.inputs['Base Color'])
  bump=nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.004;bump.inputs['Strength'].default_value=.28;m.node_tree.links.new(tx.outputs['Color'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])


def mesh(mat,vs,fs,g,uv=None,tint=1):
 vv,ff,uu,cc=parts[(g,mat)];offset=len(vv);vv.extend([tuple(v) for v in vs])
 for f in fs:
  ff.append(tuple(offset+i for i in f))
  for i in f:
   p=vs[i];uu.append(uv[i] if uv else (p[0]*.31+p[1]*.17,p[2]*.31));cc.append((tint,tint,tint,1))
def box(mat,loc,size,ang,g,bevel=0,tint=1):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
 if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=1,affect='EDGES')
 bm.verts.ensure_lookup_table();bm.verts.index_update();cs=math.cos(ang);sn=math.sin(ang)
 vs=[(loc[0]+v.co.x*cs-v.co.y*sn,loc[1]+v.co.x*sn+v.co.y*cs,loc[2]+v.co.z) for v in bm.verts];fs=[tuple(v.index for v in f.verts) for f in bm.faces];mesh(mat,vs,fs,g,tint=tint);bm.free()
def tube(mat,points,radii,g,n=8):
 vv=[]
 for i,pt in enumerate(points):
  p=Vector(pt);d=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized();u=d.cross(Vector((0,0,1)))
  if u.length<.01:u=Vector((1,0,0))
  u.normalize();v=d.cross(u).normalized()
  for j in range(n):vv.append(p+radii[i]*(u*math.cos(j*math.tau/n)+v*math.sin(j*math.tau/n)))
 fs=[tuple(range(n-1,-1,-1))]
 for i in range(len(points)-1):
  for j in range(n):fs.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
 fs.append(tuple((len(points)-1)*n+j for j in range(n)));mesh(mat,vv,fs,g)
def polar(r,a,z):return Vector((r*math.cos(a),r*math.sin(a),z))
def band(mat,r0,r1,a0,a1,z0,z1,g):
 n=max(1,math.ceil((a1-a0)*r0/.38));vv=[]
 for j in range(n+1):
  a=a0+(a1-a0)*j/n
  for r,z in [(r0,z0),(r1,z0),(r1,z1),(r0,z1)]:vv.append(polar(r,a,z))
 fs=[(3,2,1,0)]
 for j in range(n):
  for k in range(4):fs.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
 fs.append(tuple(n*4+i for i in range(4)));mesh(mat,vv,[tuple(reversed(f)) for f in fs],g)
class Face:
 def __init__(self,origin,angle,g):self.o=Vector(origin);self.t=Vector((math.cos(angle),math.sin(angle),0));self.d=Vector((-math.sin(angle),math.cos(angle),0));self.angle=angle;self.g=g
 def P(self,x,d,z):return self.o+self.t*x+self.d*d+Vector((0,0,z))
 def box(self,mat,x,d,z,w,depth,h,bevel=0,tint=1):box(mat,self.P(x,d,z),(w,depth,h),self.angle,self.g,bevel,tint)
 def panel(self,mat,coords,d=0,tint=1):mesh(mat,[self.P(x,d,z) for x,z in coords],[tuple(range(len(coords)))],self.g,uv=[(x/2.7,z/2.7) for x,z in coords],tint=tint)
 def line(self,mat,coords,rad):tube(mat,[self.P(*p) for p in coords],[rad]*len(coords),self.g)
 def window(self,x,z,w,h,seed,arched=False,door=False):
  rr=random.Random(seed);lit=rr.random()<(.64 if door else .43);room='Cosy_WarmRoom' if lit else ('Cosy_DimRoom' if rr.random()<.3 else 'Cosy_DarkRoom');sill=z-h/2;top=z+h/2;spring=top-(w*.27 if arched else 0)
  # 35cm reveal gives real darkness, with room behind asymmetric pleated curtains.
  if seed=='arrival-shop':
   self.box('Cosy_ShopBack',x,1.27,z,w,.04,h)
   # Return cheeks and ceiling make a real shallow shop interior, visible through the door glazing.
   for side in [-1,1]:self.box('Cosy_DarkWood',x+side*(w/2-.02),.76,z,.05,1.1,h)
   self.box('Cosy_DarkWood',x,.76,top-.03,w,1.1,.06)
   self.box('Cosy_ShopAmber',x-.55,.64,top-.12,.95,.13,.075)
   self.box('Cosy_DarkWood',x-.40,.53,sill+.72,1.75,.50,.48)
   self.box('Cosy_ProductCream',x-.40,.51,sill+.99,1.81,.54,.065)
   for shelf in range(3):
    zz=sill+.92+shelf*.54;self.box('Cosy_DarkWood',x+.14,.91,zz,2.43,.35,.065)
    for j in range(10):
     px=x-1.0+j*.225;hh=rr.uniform(.16,.32);dep=rr.uniform(.12,.22)
     self.box(['Cosy_ProductCream','Cosy_ProductOchre','Cosy_ProductGreen'][(j+shelf)%3],px,.86,zz+.04+hh/2,.13+rr.random()*.035,dep,hh,bevel=.016)
     if (j+shelf)%3==2:self.box('Cosy_Brass',px,.86,zz+.06+hh,.07,.08,.025)
   # Window-side café chair and a small paper notice give recognisable human scale.
   self.box('Cosy_ProductCream',x+.83,.18,sill+1.39,.31,.012,.40)
   for zz in [sill+1.31,sill+1.40,sill+1.49]:self.box('Cosy_DarkWood',x+.83,.166,zz,.22,.012,.018)
  else:self.box(room,x,.42,z,w,.035,h)
  for side in [-1,1]:self.box('Cosy_StoneBase',x+side*(w/2+.025),.20,z,.055,.43,h)
  frame='Cosy_DarkWood' if door else 'Cosy_WhitePaint'
  for side in [-1,1]:self.box(frame,x+side*(w/2-.035),.07,(sill+spring)/2,.065,.09,spring-sill,bevel=.009)
  for zz in [sill,z+.25]:self.box(frame,x,.065,zz,w,.085,.065,bevel=.008)
  self.box(frame,x,.05,(sill+spring)/2,.045,.095,spring-sill)
  if arched:
   self.line(frame,[(x+math.cos(t)*w/2,.07,spring+math.sin(t)*w*.27) for t in [j*math.pi/20 for j in range(21)]],.043)
   self.line('Cosy_PaleLimestone',[(x+math.cos(t)*(w/2+.105),-.055,spring+math.sin(t)*(w*.27+.105)) for t in [j*math.pi/24 for j in range(25)]],.079)
   self.box('Cosy_PaleLimestone',x,-.13,top+.08,.20,.19,.28,bevel=.025)
  else:
   self.box(frame,x,.055,top,w,.1,.065,bevel=.009)
   self.box('Cosy_PaleLimestone',x,-.07,top+.095,w+.22,.18,.12,bevel=.012)
  self.box('Cosy_PaleLimestone',x,-.14,sill-.085,w+.28,.44,.15,bevel=.018,tint=rr.uniform(.8,1))
  # Curved curtain sides with a different opening width for each room.
  if not door:
   for side in [-1,1]:
    width=w*rr.uniform(.14,.36);center=x+side*(w*.47-width*.5);vs=[]
    for j in range(13):
     u=center+(j/12-.5)*width;d=.24+.027*math.cos(j*math.pi/2)
     vs.extend([self.P(u,d,sill+.08+.018*math.sin(j)),self.P(u,d,top-.04)])
    mesh('Cosy_CurtainCream' if rr.random()<.7 else 'Cosy_CurtainBlue',vs,[(j*2+2,j*2+3,j*2+1,j*2) for j in range(12)],self.g,tint=rr.uniform(.75,1))
   if lit and rr.random()<.45:
    self.box('Cosy_DarkWood',x+w*.13,.33,sill+.43,w*.42,.025,.05)
    self.box('Cosy_DarkWood',x+w*.21,.32,sill+.63,.08,.045,.4)
    self.box('Cosy_CurtainCream',x+w*.21,.31,sill+.89,.28,.06,.16)
  if door:
   self.box('Cosy_Brass',x+.14,-.04,z-.27,.028,.045,.29,bevel=.008)
   for side in [-1,1]:self.box('Cosy_DarkWood',x+side*w*.245,.00,sill+.35,w*.38,.08,.52,bevel=.025)
  return lit
 def wallbay(self,w,z0,z1,winz,winw,winh,mat,seed,arch=False,door=False):
  lo=winz-winh/2;hi=winz+winh/2;spring=hi-(winw*.27 if arch else 0)
  self.box(mat,0,.23,(z0+lo)/2,w,.46,lo-z0,tint=.95)
  self.box(mat,0,.23,(hi+z1)/2,w,.46,z1-hi,tint=1)
  for s in [-1,1]:self.box(mat,s*(w+winw)/4,.23,(lo+hi)/2,(w-winw)/2,.46,hi-lo,tint=.97)
  if arch:
   # Solid arched spandrels over real openings (no arch pasted onto rectangle).
   for i in range(20):
    x0=-winw/2+winw*i/20;x1=-winw/2+winw*(i+1)/20
    zA=spring+winw*.27*math.sqrt(max(0,1-(x0/(winw/2))**2));zB=spring+winw*.27*math.sqrt(max(0,1-(x1/(winw/2))**2))
    self.panel(mat,[(x0,zA),(x1,zB),(x1,hi+.001),(x0,hi+.001)],0)
  self.window(0,winz,winw,winh,seed,arch,door)

def lantern(f,x,z):
 f.box('Cosy_Iron',x,-.07,z,.16,.12,.47,bevel=.02)
 f.box('Cosy_Brass',x,-.27,z+.01,.25,.27,.045,bevel=.015)
 f.box('Cosy_LampGlass',x,-.30,z+.19,.18,.16,.30,bevel=.012)
 for side in [-1,1]:f.box('Cosy_Iron',x+side*.11,-.32,z+.2,.024,.20,.35)
 f.box('Cosy_Iron',x,-.29,z+.39,.30,.31,.07,bevel=.025)
 f.box('Cosy_Iron',x,-.29,z+.46,.15,.18,.07,bevel=.018)

def balcony(f,z):
 f.box('Cosy_PaleLimestone',0,-.53,z,1.92,1.13,.15,bevel=.03)
 for x in [-.87,.87]:f.line('Cosy_Iron',[(x,-.03,z+.1),(x,-1.0,z+.1),(x,-1,z+1.05)],.025)
 for h in [.22,1.03]:f.box('Cosy_Iron',0,-1,z+h,1.82,.04,.04)
 for j in range(13):
  x=-.87+j*1.74/12;f.line('Cosy_Iron',[(x,-1,z+.19),(x+.025*math.sin(j),-1,z+.72),(x,-1,z+1.04)],.013)
 for x in [-.72,.72]:f.line('Cosy_Iron',[(x,.04,z-.48),(x,-.78,z-.06)],.033)

def roof(g,r,a0,a1,z):
 n=round((a1-a0)*r/.32);rows=10
 for row in range(rows):
  rlo=r-.26+row*.31;rhi=rlo+.345;zlo=z+(rlo-r+.26)*1.03;zhi=z+(rhi-r+.26)*1.03
  for i in range(n):
   aa=a0+(a1-a0)*i/n;ab=a0+(a1-a0)*(i+1)/n-.00022
   vs=[polar(rlo,aa,zlo),polar(rhi,aa,zhi),polar(rhi,ab,zhi),polar(rlo,ab,zlo)]
   mesh('Cosy_Terracotta',vs,[(0,1,2,3)],g,tint=rng.uniform(.7,1.1))
   mesh('Cosy_TileShadow',[vs[0]-Vector((0,0,.033)),vs[0],vs[3],vs[3]-Vector((0,0,.033))],[(0,1,2,3)],g)
 # Rear roof quieter low-poly, visible on orbit.
 N=max(16,math.ceil((a1-a0)*r/1.1));vv=[]
 for i in range(N+1):
  a=a0+(a1-a0)*i/N
  for rad,zz in [(r+2.8,z+3.2),(r+5.2,z+3.2),(r+8,z)]:vv.append(polar(rad,a,zz))
 mesh('Cosy_Terracotta',vv,[(i*3+j,i*3+j+1,(i+1)*3+j+1,(i+1)*3+j) for i in range(N) for j in range(2)],g)
 for a in [a0,a1]:mesh('Cosy_RedCopper',[polar(rad,a,zz) for rad,zz in [(r-.26,z),(r+2.8,z+3.2),(r+5.2,z+3.2),(r+8,z)]],[(0,1,2,3)],g)

def turret(g,r,a,z):
 center=polar(r+.42,a,0);rr=1.72;N=8
 # Bay projects 1.25m over the pavement, set above ground floor.
 for k in range(N):
  aa=a+math.tau*k/N;bb=a+math.tau*(k+1)/N;pa=center+polar(rr,aa,0);pb=center+polar(rr,bb,0);mid=(pa+pb)/2;ang=math.atan2((pb-pa).y,(pb-pa).x)
  # Outside visible four sides; hidden rear faces solid avoid overdraw.
  f=Face(mid,ang,g);width=(pb-pa).length
  if (mid-center).dot(polar(1,a,0))<.8:
   for fl in range(4):f.wallbay(width,3.5+3*fl,6.5+3*fl,5.0+3*fl,width*.60,1.82,'Cosy_LimeIvory',f'{g}turret{k}{fl}')
  else:f.box('Cosy_LimeIvory',0,.15,9.5,width,.3,12)
  for h in [3.55,6.5,9.5,12.5,15.55]:f.box('Cosy_PaleLimestone',0,-.08,h,width+.1,.25,.12,bevel=.01)
 # Bell-shaped copper dome with standing seams: curved profile and lantern cupola.
 profile=[(1.93,15.68),(1.83,16.03),(1.42,16.70),(.95,17.18),(.72,17.60),(.70,18.05),(.37,18.30),(.16,18.65),(.035,19.00)]
 vs=[]
 for rad,zz in profile:
  for k in range(16):vs.append(center+polar(rad,a+k*math.tau/16,zz))
 fs=[]
 for j in range(len(profile)-1):
  for k in range(16):fs.append((j*16+k,j*16+(k+1)%16,(j+1)*16+(k+1)%16,(j+1)*16+k))
 mesh('Cosy_RedCopper',vs,fs,g)
 for k in range(16):tube('Cosy_RedCopper',[center+polar(rad+.017,a+k*math.tau/16,zz) for rad,zz in profile],[.016]*len(profile),g,5)
 tube('Cosy_Iron',[center+Vector((0,0,18.87)),center+Vector((0,0,19.48))],[.025,.016],g,6)

for label,r,st,en,upper in [('North',27,39,134,'Cosy_LimeIvory'),('West',29,151,218,'Cosy_LimeOchre')]:
 g='Building_'+label;a0=math.radians(st);a1=math.radians(en);count=round((a1-a0)*r/2.85);step=(a1-a0)/count;ground='Cosy_RoseRustication' if label=='North' else 'Cosy_StoneBase'
 # Back shell preserved within existing 8m footprint.
 # The approach reveals the rear return: real window openings replace the former blank extrusion.
 for i in range(count):
  a=a0+(i+.5)*step;rf=Face(polar(r+8,a,0),a+math.pi/2,g);bw=2*(r+8)*math.tan(step/2)+.015
  rf.wallbay(bw,-.05,3.6,1.9,1.30,2.1,'Cosy_StoneBase',f'rear{label}{i}')
  for fl in range(4):rf.wallbay(bw,3.6+fl*3,6.6+fl*3,5.04+fl*3,1.28,1.91,upper,f'rear{label}{i}{fl}')
  for zz in [3.58,6.50,12.52,15.58]:rf.box('Cosy_PaleLimestone',0,-.055,zz,bw,.15,.1)
 # Continuous buried plinth closes pavement contact; visible masonry rises only20cm.
 band('Cosy_StoneBase',r-.025,r+.48,a0,a1,-.06,.205,g)
 band('Cosy_StoneBase',r+7.53,r+8.035,a0,a1,-.06,.205,g)
 for i in range(count):
  a=a0+(i+.5)*step;f=Face(polar(r,a,0),a-math.pi/2,g);w=2*r*math.tan(step/2)+.012
  f.wallbay(w,.16,3.60,1.85,1.64,2.75,ground,label+str(i),True,i%5==3)
  if i%5==3:lantern(f,-1.13,2.50)
  for j in range(4):
   zz=5.04+j*3
   bay_overlay=label=='North' and any(abs(a-math.radians(ta))*r<2.38 for ta in [68,128])
   if bay_overlay:f.box(upper,0,.23,zz+.06,w,.46,3.0)
   else:f.wallbay(w,3.6+j*3,6.6+j*3,zz,1.19 if label=='North' else 1.25,1.91,upper,label+str(i)+'f'+str(j))
   # Shallow carved spandrel panels and alternating pediments break the modular rhythm.
   if not bay_overlay and (j==0 or (j==2 and i%3==1)):
    f.box('Cosy_PaleLimestone',0,-.041,zz-1.21,1.3,.08,.30,bevel=.02)
    f.box(upper,0,-.086,zz-1.21,1.12,.04,.20,bevel=.014,tint=.90)
   if label=='West' and i%4==1 and j in [0,1,2]:balcony(f,zz-1.05)
  # Rusticated ground piers, foot damp courses, drainpipe and relief cornice blocks.
  for z in [.45,.84,1.23,1.62,2.01,2.4,2.79,3.18]:
   for side in [-1,1]:f.box(ground,side*(w/2-.25),-.018,z,.44,.054,.028,tint=.72)
  f.box('Cosy_StoneBase',0,-.045,.34,w,.10,.36,tint=.82)
  if i%4==0:
   x=w*.43;f.line('Cosy_RedCopper',[(x,-.09,.22),(x,-.09,14.8),(x,-.31,15.65)],.045)
   for zz in [1,4,7,10,13]:f.box('Cosy_Iron',x,-.13,zz,.13,.10,.04)
  for x in [-w*.34,0,w*.34]:f.box('Cosy_PaleLimestone',x,-.17,15.31,.14,.24,.18,bevel=.015)
  if i%3==1:
   # Recessed roof dormer with real side cheeks and shallow copper cap.
   df=Face(polar(r+.10,a,0),a-math.pi/2,g);df.wallbay(1.45,16.15,17.62,16.88,1.07,1.20,upper,'d'+label+str(i))
   for side in [-1,1]:df.box('Cosy_RedCopper',side*.76,.85,16.93,.09,1.7,1.50)
   df.box('Cosy_RedCopper',0,.76,17.67,1.68,1.80,.12,bevel=.02)
 for z,dr,h in [(3.57,.14,.13),(6.5,.065,.075),(12.52,.09,.075),(15.45,.21,.13),(15.59,.32,.16)]:band('Cosy_PaleLimestone',r-dr,r+.1,a0,a1,z,z+h,g)
 roof(g,r,a0,a1,15.77)
 # Return walls have real upper windows. North street shop centered radius30.3.
 for a,isend in [(a0,False),(a1,True)]:
  # Face horizontal follows radial. Positive depth points inside angular sector.
  angle=a if not isend else a+math.pi;origin=polar(r+4,a,0);rf=Face(origin,angle,g)
  rf.box('Cosy_StoneBase',0,.20,.11,8.06,.50,.34)
  for j in range(4):
   for side in [-1,1]:
    sf=Face(origin+rf.t*(side*2),angle,g)
    for fl in range(4):sf.wallbay(4,3.6+fl*3,6.6+fl*3,5.04+fl*3,1.22,1.91,upper,f'{label}{a}{side}{fl}')
   break
  # A broad shop door / window in the near north return; remaining end wall is masonry.
  offset=(30.3-(r+4))*(1 if not isend else -1)
  if label=='North' and isend:
   rf.box(ground,(-4+offset-1.5)/2,.25,1.9,offset-1.5+4,.5,3.4)
   rf.box(ground,(4+offset+1.5)/2,.25,1.9,4-offset-1.5,.5,3.4)
   rf.box(ground,offset,.25,3.36,3,.5,.49)
   rf.box('Cosy_StoneBase',offset,.25,.23,3,.5,.18)
   rf.window(offset,1.70,3,2.76,'arrival-shop',False,True)
   for xx in [offset-1.83,offset+1.83]:lantern(rf,xx,2.44)
  else:
   for side in [-1,1]:
    sf=Face(origin+rf.t*(side*2),angle,g);sf.wallbay(4,.16,3.6,1.85,1.66,2.73,ground,f'{label}end{side}',True,True)
  for zz in [3.57,6.50,12.52,15.58]:rf.box('Cosy_PaleLimestone',0,-.11,zz,8.1,.25,.13,bevel=.015)
 if label=='North':
  cf=Face(polar(r-.27,math.radians(99),0),math.radians(99)-math.pi/2,g)
  top=[(-4.3,15.9),(-3.8,16.04),(-3.32,16.35),(-2.95,16.93),(-2.52,17.55),(-1.91,18.02),(-1.2,18.35),(0,18.55),(1.2,18.35),(1.91,18.02),(2.52,17.55),(2.95,16.93),(3.32,16.35),(3.8,16.04),(4.3,15.9)]
  cuts=sorted(set([p[0] for p in top]+[-1.82,-.88,.88,1.82]))
  def topz(x):
   for (xa,za),(xb,zb) in zip(top,top[1:]):
    if xa-1e-6<=x<=xb+1e-6:return za+(zb-za)*(x-xa)/(xb-xa)
   return 15.9
  for xa,xb in zip(cuts,cuts[1:]):
   zm=(xa+xb)/2;za=topz(xa);zb=topz(xb)
   if any(abs(zm-wx)<.47 for wx in [-1.35,1.35]):
    cf.panel('Cosy_LimeIvory',[(xa,15.6),(xb,15.6),(xb,15.99),(xa,15.99)],0)
    cf.panel('Cosy_LimeIvory',[(xa,17.29),(xb,17.29),(xb,zb),(xa,za)],0)
   else:cf.panel('Cosy_LimeIvory',[(xa,15.6),(xb,15.6),(xb,zb),(xa,za)],0)
  cf.line('Cosy_PaleLimestone',[(x,-.07,z) for x,z in top],.105)
  cf.line('Cosy_PaleLimestone',[(x*.91,-.08,z-.22) for x,z in top[2:-2]],.034)
  for x in [-1.35,1.35]:
   cf.window(x,16.64,.94,1.30,'gable'+str(x))
  # Shallow shield, paired scrolls and raised keystone relief.
  cf.box('Cosy_PaleLimestone',0,-.085,17.78,.53,.12,.50,bevel=.1)
  for side in [-1,1]:
   cf.line('Cosy_PaleLimestone',[(side*(.40+j*.045),-.09,17.80+.10*math.sin(j*.48)) for j in range(24)],.026)
  for degrees in [68,128]:turret(g,r,math.radians(degrees),15.7)

tri=0
for (g,mat),(vs,fs,uvs,cols) in parts.items():
 name=g+'_Polish_'+mat;me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(mats[mat]);me.update();uv=me.uv_layers.new(name='UVMap');ca=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for u,c,v,col in zip(uv.data,ca.data,uvs,cols):u.uv=v;c.color=col
 if mat in ['Cosy_LimeIvory','Cosy_LimeOchre','Cosy_RoseRustication','Cosy_PaleLimestone','Cosy_StoneBase']:
  for poly in me.polygons:
   normal=poly.normal;axis=Vector((-normal.y,normal.x,0))
   if axis.length<.01:axis=Vector((1,0,0))
   axis.normalize()
   for li in poly.loop_indices:
    p=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(p.dot(axis)/4,p.z/4 if abs(normal.z)<.7 else p.y/4)
 # Closed primitive normals are already valid; polygon façade panels need exterior (negative depth).
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);tri+=sum(len(f)-2 for f in fs)

# Stable contact occlusion baked into COLOR_0; no screen-space pass is needed.
from mathutils.bvhtree import BVHTree
import time
vAll=[];fAll=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 offset=len(vAll);vAll.extend([v.co.copy() for v in ob.data.vertices]);fAll.extend([tuple(offset+i for i in f.vertices) for f in ob.data.polygons])
bvh=BVHTree.FromPolygons(vAll,fAll);samples=[];RAYS=16;golden=math.pi*(3-math.sqrt(5))
for j in range(RAYS):
 rr=math.sqrt((j+.5)/RAYS);samples.append((rr*math.cos(j*golden),rr*math.sin(j*golden),math.sqrt(1-rr*rr)))
cache={};started=time.time()
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 mat=ob.data.materials[0].name
 if any(k in mat for k in ['Room','Glass','Curtain','ShopBack','ShopAmber']):continue
 me=ob.data;ca=me.color_attributes['Color'];values=[]
 for poly in me.polygons:
  normal=poly.normal.normalized();axis=Vector((0,0,1)) if abs(normal.z)<.92 else Vector((1,0,0));u=normal.cross(axis).normalized();v=normal.cross(u)
  for li in poly.loop_indices:
   p=me.vertices[me.loops[li].vertex_index].co;key=tuple(round(x,4) for x in (*p,*normal));val=cache.get(key)
   if val is None:
    origin=p+normal*.009;occ=0
    for sx,sy,sz in samples:
     hit,hn,face,dist=bvh.ray_cast(origin,u*sx+v*sy+normal*sz,1.0)
     if hit is not None:occ+=.5+.5*(1-dist)
    val=max(.5,1-.64*occ/RAYS)
    if mat in ['Cosy_RoseRustication','Cosy_StoneBase']:val*=1-.16*math.exp(-max(0,p.z)/.42)
    cache[key]=val
   c=ca.data[li].color;ca.data[li].color=(c[0]*val,c[1]*val,c[2]*val,1);values.append(val)
 print('Contact AO',ob.name,len(values),round(time.time()-started,1),flush=True)

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/architecture-polish.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/architecture-polish.glb'),export_format='GLB',export_yup=True,export_apply=True,export_vertex_color='NAME',export_vertex_color_name='Color',export_cameras=False,export_lights=False)
import struct
out=ROOT/'public/assets/architecture-polish.glb';raw=out.read_bytes();ln=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+ln]);binary=raw[20+ln:]
for mat in doc['materials']:
 if mat['name'] in texture_factors:
  mat['pbrMetallicRoughness']['baseColorFactor']=texture_factors[mat['name']];mat.pop('normalTexture',None)
js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);out.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+binary)
report={'meshes':len(parts),'triangles':tri,'replaces':['environment Building_North_*','environment Building_West_*'],'groups':['Building_North','Building_West'],'boundsFootprints':{'North':[27,35,39,134],'West':[29,37,151,218]},'turretsDegrees':[68,128],'arrivalShop':{'BlenderAngle':134,'radialCenter':30.3,'width':3,'bottom':.32,'top':3.08},'materialNote':'Generated lime-plaster.png embedded in five masonry materials with 4m UV scale and explicit ivory/ochre/rose factors. Set runtime bumpMap=map and bumpScale=.003. Do not override basecolor. Vertex COLOR_0 contains16ray1m contact AO. Window emissions warm and restrained.'}
(ROOT/'.dream-loop/architecture-polish-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
