"""Trace closed black drawing outlines; red drill symbols are metadata, not bores."""
from collections import deque
from PIL import Image
from .core import SceneError


def components(points):
    points=set(points);groups=[]
    while points:
        seed=points.pop();group={seed};todo=[seed]
        while todo:
            x,y=todo.pop()
            for p in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if p in points:points.remove(p);group.add(p);todo.append(p)
        groups.append(group)
    return groups


def boundary(mask):
    edges={}
    for x,y in mask:
        for neighbor,a,b in [((x,y-1),(x,y),(x+1,y)),((x+1,y),(x+1,y),(x+1,y+1)),
                             ((x,y+1),(x+1,y+1),(x,y+1)),((x-1,y),(x,y+1),(x,y))]:
            if neighbor not in mask:edges.setdefault(a,[]).append(b)
    loops=[]
    while edges:
        start=next(iter(edges));p=start;loop=[]
        while True:
            loop.append(p)
            if p not in edges:raise SceneError('Open contour')
            q=edges[p].pop()
            if not edges[p]:del edges[p]
            p=q
            if p==start:break
        # Remove only collinear points; retain raster curvature evidence.
        loop=[p for i,p in enumerate(loop) if
              (p[0]-loop[i-1][0])*(loop[(i+1)%len(loop)][1]-p[1]) !=
              (p[1]-loop[i-1][1])*(loop[(i+1)%len(loop)][0]-p[0])]
        loops.append(loop)
    return loops


def area(loop):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(loop,loop[1:]+loop[:1])))/2


def trace(image, roi):
    with Image.open(image) as im:
        crop=im.convert('RGB').crop(roi)
    w,h=crop.size
    black={(x,y) for y in range(h) for x in range(w) if max(crop.getpixel((x,y)))<120}
    free={(x,y) for y in range(h) for x in range(w)}-black
    groups=components(free)
    inside=[g for g in groups if not any(x in {0,w-1} or y in {0,h-1} for x,y in g)]
    if not inside:raise SceneError('No closed outline found; cannot infer a contour')
    # Main material island is the largest enclosed white region.
    material=max(inside,key=len)
    # Combine material and its surrounding strokes, then use largest boundary.
    filled=set(material)
    for x,y in material:
        filled.update(p for p in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)] if p in black)
    loops=boundary(filled)
    outer=max(loops,key=area)
    # Closed central void is identified geometrically; symbol size never sets bore diameter.
    holes=[loop for loop in loops if loop is not outer and area(loop)>4]
    red={(x,y) for y in range(h) for x in range(w)
         if (lambda p:p[0]>180 and p[1]<100 and p[2]<100)(crop.getpixel((x,y)))}
    markers=[{'center_px':[sum(p[0] for p in g)/len(g),sum(p[1] for p in g)/len(g)],
              'diameter_mm':None,'status':'CẦN XÁC NHẬN'} for g in components(red) if len(g)>1]
    return {'roi':list(roi),'outline_px':outer,'voids_px':holes,'drill_markers':markers,
            'confidence':'inferred','quantization_px':1,
            'radius_status':'CẦN XÁC NHẬN: contour depicts reliefs; no calibrated cutter radius',
            'source_image':str(image)}
