#!/usr/bin/env python3
"""Original 19-part Duke-style model pilot. No retail files or live game override.

All nodes have identity transforms and local-pivot mesh coordinates. The preview
uses ILLUSTRATIVE T-pose offsets, not offsets measured from an owned PS1 disc.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct
from character_model import DUKE_PARTS, validate_model

COLORS={
 "skin":(.89,.59,.43),"skin_shadow":(.62,.36,.27),
 "shirt":(.62,.11,.13),"shirt_shadow":(.33,.06,.08),
 "denim":(.17,.29,.48),"denim_dark":(.095,.17,.30),
 "black":(.052,.056,.063),"glass":(.035,.07,.09),
 "gold":(.91,.72,.22),"hair_shadow":(.59,.43,.12),
 "boots":(.20,.14,.105),"sole":(.085,.072,.065),
 "metal":(.48,.51,.55)
}
# Positions below compose an authoring preview only: the PS1 HIE has not
# been used to calibrate real pivots or the scene's overall scale.
POSE={
 0:(0,0,0),9:(0,.56,0),16:(0,1.19,0),20:(0,.55,-.28),
 10:(-.60,.77,0),11:(-1.01,.77,0),12:(-1.38,.77,0),
 13:(.60,.77,0),14:(1.01,.77,0),15:(1.38,.77,0),
 1:(-.22,-.33,0),2:(-.22,-.73,0),3:(-.22,-1.08,.02),4:(-.22,-1.2,.18),
 5:(.22,-.33,0),6:(.22,-.73,0),7:(.22,-1.08,.02),8:(.22,-1.2,.18),
 21:(.22,-1.1,.18)
}
parts={i:defaultdict(list) for i in DUKE_PARTS}

def tri(i,color,a,b,c):
    parts[i][color].append((a,b,c))

def ellipsoid(i,color,center,radius,n=14,m=8):
    cx,cy,cz=center;rx,ry,rz=radius
    def xyz(a,b):
        p=math.pi*a/m;t=2*math.pi*b/n
        return (cx+rx*math.sin(p)*math.cos(t),
                cy+ry*math.cos(p),cz+rz*math.sin(p)*math.sin(t))
    for a in range(m):
        for b in range(n):
            p=xyz(a,b);q=xyz(a+1,b);r=xyz(a+1,b+1);s=xyz(a,b+1)
            if a:tri(i,color,p,q,s)
            if a<m-1:tri(i,color,q,r,s)

def box(i,color,center,size):
    cx,cy,cz=center;sx,sy,sz=(v/2 for v in size)
    v=[(cx+x*sx,cy+y*sy,cz+z*sz) for x,y,z in
       ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
        (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    for a,b,c,d in ((0,3,2,1),(4,5,6,7),(0,4,7,3),
                    (1,2,6,5),(3,7,6,2),(0,1,5,4)):
        tri(i,color,v[a],v[b],v[c]);tri(i,color,v[a],v[c],v[d])

def make_geometry():
    ellipsoid(0,"denim",(0,0,0),(.34,.22,.24))
    box(0,"black",(0,.16,0),(.62,.085,.46))
    box(0,"metal",(0,.16,.25),(.14,.09,.045))
    ellipsoid(9,"shirt",(0,0,0),(.48,.41,.28))
    ellipsoid(9,"shirt_shadow",(0,-.23,.07),(.38,.16,.23))
    box(9,"black",(0,.20,.28),(.13,.19,.045))
    ellipsoid(16,"skin",(0,0,0),(.22,.29,.21),16,10)
    ellipsoid(16,"skin_shadow",(0,-.18,.045),(.17,.12,.17))
    ellipsoid(16,"gold",(0,.27,-.02),(.23,.12,.22),16,8)
    box(16,"gold",(0,.32,0),(.40,.12,.31))
    box(16,"hair_shadow",(0,.25,.17),(.43,.045,.07))
    for x in (-.12,.12):
        box(16,"glass",(x,.052,.209),(.19,.088,.043))
        box(16,"black",(x,.109,.211),(.205,.023,.046))
    box(16,"black",(0,.054,.23),(.09,.023,.045))
    ellipsoid(16,"skin",(0,-.028,.22),(.06,.08,.07),12,6)
    box(16,"skin_shadow",(0,-.155,.182),(.14,.026,.024))
    for a,b,c,s in ((10,11,12,-1),(13,14,15,1)):
        ellipsoid(a,"skin",(s*.12,0,0),(.29,.175,.20))
        ellipsoid(a,"shirt_shadow",(-s*.17,0,0),(.105,.18,.19))
        ellipsoid(b,"skin",(s*.12,0,0),(.285,.14,.145))
        box(b,"black",(s*.32,0,0),(.11,.24,.26))
        ellipsoid(c,"skin",(s*.07,0,0),(.18,.12,.135))
        ellipsoid(c,"skin_shadow",(s*.08,-.112,.085),(.066,.09,.06))
    for a,b,c,d in ((1,2,3,4),(5,6,7,8)):
        ellipsoid(a,"denim",(0,-.12,0),(.23,.37,.24))
        ellipsoid(b,"denim",(0,-.10,0),(.18,.33,.19))
        box(b,"denim_dark",(0,-.29,0),(.32,.10,.32))
        ellipsoid(c,"boots",(0,0,0),(.18,.19,.18))
        ellipsoid(d,"boots",(0,-.01,.12),(.21,.145,.35))
        box(d,"sole",(0,-.125,.14),(.43,.065,.70))
    # Nodes 20 and 21 remain empty attachment joints.

def glb():
    buf=bytearray();views=[];accessors=[];meshes=[];nodes=[]
    colors=list(COLORS);count=0
    def append(data):
        while len(buf)%4:buf.append(0)
        offset=len(buf);buf.extend(data)
        idx=len(views);views.append({"buffer":0,"byteOffset":offset,
                                    "byteLength":len(data),"target":34962})
        return idx
    for part,name in DUKE_PARTS.items():
        prims=[]
        for color,faces in parts[part].items():
            xyz=bytearray();normals=bytearray()
            lo=[1e8]*3;hi=[-1e8]*3
            for a,b,c in faces:
                u=[b[k]-a[k] for k in range(3)]
                v=[c[k]-a[k] for k in range(3)]
                n=(u[1]*v[2]-u[2]*v[1],
                   u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                length=math.sqrt(sum(t*t for t in n)) or 1.0
                for p in (a,b,c):
                    xyz.extend(struct.pack("<3f",*p))
                    normals.extend(struct.pack("<3f",*(t/length for t in n)))
                    for k in range(3):lo[k]=min(lo[k],p[k]);hi[k]=max(hi[k],p[k])
            pos=append(xyz);normal=append(normals);first=len(accessors)
            accessors.extend([
                {"bufferView":pos,"componentType":5126,"count":3*len(faces),
                 "type":"VEC3","min":lo,"max":hi},
                {"bufferView":normal,"componentType":5126,"count":3*len(faces),"type":"VEC3"}
            ])
            prims.append({"attributes":{"POSITION":first,"NORMAL":first+1},
                          "material":colors.index(color),"mode":4})
            count+=len(faces)
        node={"name":f"part_{part:02d}_{name}"}
        if prims:
            node["mesh"]=len(meshes)
            meshes.append({"name":name,"primitives":prims})
        nodes.append(node)
    while len(buf)%4:buf.append(0)
    material=[{"name":c,"doubleSided":True,"pbrMetallicRoughness":
               {"baseColorFactor":[*COLORS[c],1.0],
                "metallicFactor":0.0,"roughnessFactor":0.92}} for c in colors]
    doc={"asset":{"version":"2.0","generator":"original-duke-rigid-pilot"},
         "scene":0,"scenes":[{"nodes":list(range(19))}],
         "nodes":nodes,"meshes":meshes,"materials":material,
         "accessors":accessors,"bufferViews":views,"buffers":[{"byteLength":len(buf)}]}
    js=json.dumps(doc,separators=(",",":")).encode("utf-8")
    js+=b" "*(-len(js)%4)
    chunks=struct.pack("<II",len(js),0x4e4f534a)+js
    chunks+=struct.pack("<II",len(buf),0x004e4942)+buf
    return struct.pack("<4sII",b"glTF",2,12+len(chunks))+chunks,count

def preview(output):
    from PIL import Image,ImageDraw
    image=Image.new("RGB",(1500,640),(24,29,37));draw=ImageDraw.Draw(image)
    for panel,(label,angle) in enumerate((("Frente",0),("Perfil",math.pi/2),
                                           ("3/4",math.pi/5))):
        x0=panel*500
        draw.rounded_rectangle((x0+10,12,x0+490,628),radius=14,
                               fill=(37,43,53),outline=(79,92,102),width=2)
        draw.text((x0+30,30),label,fill=(235,237,239))
        screen=[];cx=x0+250;cy=306;scale=217
        for part,groups in parts.items():
            offset=POSE[part]
            for color,faces in groups.items():
                for face in faces:
                    pts=[]
                    for v in face:
                        x,y,z=(v[i]+offset[i] for i in range(3))
                        xx=x*math.cos(angle)+z*math.sin(angle)
                        zz=z*math.cos(angle)-x*math.sin(angle)
                        pts.append((xx,y,zz))
                    coords=[(cx+round(x*scale),cy-round(y*scale-z*9))
                            for x,y,z in pts]
                    depth=sum(p[2] for p in pts)/3
                    color3=tuple(int(255*c) for c in COLORS[color])
                    screen.append((depth,coords,color3))
        for _,polygon,color in sorted(screen,key=lambda x:x[0]):
            draw.polygon(polygon,fill=color)
        draw.text((x0+30,591),"Modelo autoral de teste - sem disco PS1",
                  fill=(165,177,184))
    image.save(output)

def build(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    # Repeated generator calls in tests or an editor session must be byte-identical.
    for group in parts.values(): group.clear()
    make_geometry()
    binary,count=glb()
    (out/"duke-pilot.glb").write_bytes(binary)
    manifest={"schema":1,"asset_id":"duke-db00-pilot",
      "target":{"group":"DB00","hierarchy":1,"joints":19},
      "model":{"file":"duke-pilot.glb",
               "sha256":hashlib.sha256(binary).hexdigest(),
               "max_triangles":12000},
      "rig":{"mode":"rigid-parts",
             "parts":{str(k):f"part_{k:02d}_{v}" for k,v in DUKE_PARTS.items()}}}
    (out/"model.json").write_text(json.dumps(manifest,indent=2)+"\n")
    report=validate_model(out/"model.json")
    if report["triangles"]!=count:raise RuntimeError("triangle count mismatch")
    preview(out/"duke-pilot-preview.png")
    (out/"pilot-report.json").write_text(json.dumps({
        **report,"original_geometry":True,
        "uses_retail_assets":False,
        "game_hie_pivots_calibrated":False,
        "runtime_override_active":False
    },indent=2)+"\n")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    result=build(p.parse_args().out)
    print(json.dumps(result,indent=2,sort_keys=True))
