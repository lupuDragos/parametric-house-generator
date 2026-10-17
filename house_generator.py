import bpy, math

W   = 12.30
D   = 12.20

SEG = [(0.00, 3.30, 12.20), (3.30, 4.90, 10.60), (4.90, 8.20, 9.10), (8.20, W, 8.40)]
Z1  = 2.50
ZW  = 4.35

YRG, ZRG = 4.20, 6.60
P_F, P_S = 1.0 / 3.0, 0.23
def zroof(y):
    return ZRG - (YRG - y) * P_F if y < YRG else ZRG - (y - YRG) * P_S
ZE_F = zroof(0.0)
OV, OVG, TR = 0.60, 0.90, 0.20
TER_D = 2.00
PX = [0.0, 0.40, 2.90, 3.30, 7.80, 8.20, 11.90, 12.30]
XG = PX[5]

LX0, LX1, LXR, LZR = 7.80, W, 10.05, 7.40

RX0, RX1 = 4.95, 6.55
RXR = (RX0 + RX1) / 2.0
RYF = SEG[2][2] - 0.30
RZE, RZR = 5.55, 6.50
Z_BRAU = 1.85

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
    for d in list(coll):
        coll.remove(d)

def _base(name, rgb, rough=0.7, metal=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = 'BLEND'
    return m, nt, b

def _coords(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return tc.outputs["Object"]

def mat_plain(name, rgb, rough=0.7, metal=0.0, alpha=1.0):
    return _base(name, rgb, rough, metal, alpha)[0]

def mat_stucco(name, rgb, rough=0.9, scale=38.0, strength=0.22):
    m, nt, b = _base(name, rgb, rough)
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 6.0
    nt.links.new(_coords(nt), n.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m

def mat_boards(name, rgb_dark, rgb_light, axis, period=0.115, rough=0.78):
    m, nt, b = _base(name, rgb_light, rough)
    w = nt.nodes.new("ShaderNodeTexWave")
    w.wave_type = 'BANDS'
    w.bands_direction = axis
    w.wave_profile = 'SAW'
    w.inputs["Scale"].default_value = 1.0 / period
    w.inputs["Distortion"].default_value = 0.0
    nt.links.new(_coords(nt), w.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.10
    ramp.color_ramp.elements[0].color = (*rgb_dark, 1)
    ramp.color_ramp.elements[1].position = 0.22
    ramp.color_ramp.elements[1].color = (*rgb_light, 1)
    nt.links.new(w.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.01
    nt.links.new(w.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m

def mat_tiles(name, rgb, mortar, bw=0.62, bh=0.30, rough=0.42, rot_z=0.0):
    m, nt, b = _base(name, rgb, rough)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (math.radians(90), 0, math.radians(rot_z))
    nt.links.new(_coords(nt), mp.inputs["Vector"])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Color1"].default_value = (*rgb, 1)
    br.inputs["Color2"].default_value = (rgb[0]*0.92, rgb[1]*0.92, rgb[2]*0.93, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.012
    br.inputs["Brick Width"].default_value = bw
    br.inputs["Row Height"].default_value = bh
    nt.links.new(mp.outputs["Vector"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.01
    nt.links.new(br.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m

def mat_roof(name, rgb, seam=0.62):
    m, nt, b = _base(name, rgb, 0.55, 0.30)
    w = nt.nodes.new("ShaderNodeTexWave")
    w.wave_type = 'BANDS'
    w.bands_direction = 'X'
    w.wave_profile = 'SAW'
    w.inputs["Scale"].default_value = 1.0 / seam
    nt.links.new(_coords(nt), w.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.015
    nt.links.new(w.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 2.2
    n.inputs["Detail"].default_value = 4.0
    nt.links.new(_coords(nt), n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (rgb[0]*0.72, rgb[1]*0.70, rgb[2]*0.66, 1)
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = (*rgb, 1)
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m

def srgb(r, g, b):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b))

M_TENC  = mat_stucco("Tencuiala", srgb(208, 203, 193))
M_PILAS = mat_stucco("Pilastru",  srgb(226, 222, 212), strength=0.15)
M_GALB  = mat_stucco("Galben",    srgb(238, 226, 165), strength=0.12)
M_SOCLU = mat_stucco("Soclu",     srgb(150, 148, 142), rough=0.95, scale=22.0, strength=0.35)
M_LEMN_Y = mat_boards("LambriuY", srgb(84, 19, 18), srgb(128, 32, 30), 'Y')
M_LEMN_X = mat_boards("LambriuX", srgb(84, 19, 18), srgb(128, 32, 30), 'X')
M_LEMN   = mat_plain("LemnRosu", srgb(120, 30, 28), 0.76)
M_TABLA  = mat_roof("TablaZinc", srgb(150, 152, 150))
M_TABLA_P= mat_plain("TablaPlan", srgb(160, 162, 159), 0.55, 0.30)
M_ZINC   = mat_plain("Zinc",      srgb(192, 196, 194), 0.35, 0.75)
M_PAZIE  = mat_plain("Pazie",     srgb(92, 38, 30), 0.78)
M_RAMA   = mat_plain("RamaFer",   srgb(115, 24, 26), 0.60)
M_ALB    = mat_plain("Alb",       srgb(238, 238, 232), 0.50)
M_STICLA = mat_plain("Sticla",    srgb(88, 118, 150), 0.04)
M_GARAJ  = mat_boards("UsaGaraj", srgb(44, 26, 14), srgb(88, 54, 30), 'X', period=0.13, rough=0.62)
M_FIER   = mat_plain("Fier",      srgb(22, 22, 24), 0.55, 0.40)
M_MARM   = mat_tiles("Marmura",   srgb(146, 126, 134), srgb(186, 178, 182))
M_MARM_P = mat_plain("MarmuraPlan", srgb(146, 126, 134), 0.45)
M_MARM_D = mat_tiles("MarmuraDiag", srgb(150, 130, 138), srgb(190, 182, 186), bw=0.20, bh=0.20, rot_z=45.0)
M_PARD   = mat_tiles("Pardoseala", srgb(186, 162, 150), srgb(214, 204, 196), bw=0.30, bh=0.30, rough=0.55)
M_GRINDA = mat_plain("Grinda",    srgb(196, 188, 172), 0.80)
M_CAPRIOR= mat_plain("Caprior",   srgb(104, 66, 42), 0.85)
M_IARBA  = mat_stucco("Iarba",    srgb(68, 96, 38), rough=0.98, scale=6.0, strength=0.5)
M_BETON  = mat_stucco("Beton",    srgb(172, 170, 163), rough=0.94, scale=14.0, strength=0.30)
M_CARAM  = mat_plain("Caramida",  srgb(150, 85, 65), 0.85)

FACES = [(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
COLL  = bpy.context.collection

def mesh(name, verts, faces, m):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(m)
    COLL.objects.link(ob)
    return ob

def box(name, x0, y0, z0, x1, y1, z1, m):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    return mesh(name, v, FACES, m)

def slab(name, quad, t, m):
    v = list(quad) + [(x, y, z - t) for (x, y, z) in quad]
    return mesh(name, v, FACES, m)

def prism(name, poly, axis, a0, a1, m):
    n = len(poly)
    if axis == 'x':
        v = [(a0, u, z) for (u, z) in poly] + [(a1, u, z) for (u, z) in poly]
    else:
        v = [(u, a0, z) for (u, z) in poly] + [(u, a1, z) for (u, z) in poly]
    faces = [tuple(range(n))[::-1], tuple(range(n, 2*n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    return mesh(name, v, faces, m)

def z_teren(x, y):

    if y < -9.0:
        base = 0.30
    elif y < -6.0:
        base = 0.30 - (y + 9.0) / 3.0 * 0.70
    elif y < 0.0:
        base = -0.40
    elif y < D:
        base = -0.40 - y / D * 0.45
    else:
        base = -0.85 - (y - D) * 0.01
    tilt = 0.60 * (x / W - 0.5)
    f = min(1.0, max(0.0, (y + 9.0) / 3.0))
    return base + tilt * f

TXS = [-22, -12, -7.5, -3, 0, 3, 6, 9, 12.2, 16, 22, 32]
TYS = TXS
gx = [-20, -12, -6, -2, 0, 2, 4, 6, 8, 10, 12.3, 15, 20, 30]
gy = [-22, -14, -7.5, -4, -1.5, 0, 3, 6, 9, 12.2, 15, 20, 30]
verts, faces = [], []
for j, yy in enumerate(gy):
    for i, xx in enumerate(gx):
        verts.append((xx, yy, z_teren(xx, yy)))
nx = len(gx)
for j in range(len(gy) - 1):
    for i in range(nx - 1):
        a = j * nx + i
        faces.append((a, a + 1, a + nx + 1, a + nx))
mesh("Teren", verts, faces, M_IARBA)

prism("Rampa", [(-7.6, 0.32), (0.06, 0.02), (0.06, -1.6), (-7.6, -1.6)], 'x', 8.05, 12.55, M_BETON)

for i, (x0, x1, dep) in enumerate(SEG):
    y0 = 0.0 if x0 >= XG else TER_D
    box(f"Parter_seg{i}", x0, y0, 0.0, x1, dep, Z1, M_TENC)

box("Terasa_lat_garaj", XG - 0.045, 0.40, -0.30, XG - 0.005, TER_D - 0.005, Z1 - 0.005, M_GALB)

for i, (x0, x1, dep) in enumerate(SEG):
    y0 = -0.07 if x0 >= XG else TER_D + 0.005
    xa = x0 - 0.07 if i == 0 else x0
    xb = x1 + 0.07
    box(f"Soclu_seg{i}", xa, y0, -1.7, xb, dep + 0.07, 0.30, M_SOCLU)

box("Terasa_pardoseala", PX[0] - 0.14, -0.50, -1.7, XG + 0.02, TER_D, -0.30, M_PARD)
box("Terasa_bordura",    PX[0] - 0.14, -0.50, -0.30, XG + 0.02, -0.42, -0.26, M_MARM_P)
box("Terasa_fund",  PX[0], TER_D - 0.04, -0.30, XG, TER_D, Z1, M_GALB)
box("Terasa_tavan", PX[0], -0.02, Z1 - 0.03, XG, TER_D, Z1, M_GALB)
box("Usa_intrare",  2.05, TER_D - 0.11, -0.30, 2.95, TER_D - 0.02, 1.98, M_ALB)
box("Usa_geam",     2.16, TER_D - 0.13, 0.95, 2.84, TER_D - 0.11, 1.84, M_STICLA)
box("Usa_traversa", 2.05, TER_D - 0.135, 0.90, 2.95, TER_D - 0.115, 0.96, M_ALB)

for k in range(4):
    zt = -0.30 - 0.15 * (k + 1)
    box(f"Treapta_{k}", 0.55 + 0.0, -0.50 - 0.30 * (k + 1), -1.7, 2.35, -0.50 - 0.30 * k, zt + 0.15, M_MARM_P)

for k, (a, b) in enumerate(((PX[0], PX[1]), (PX[2], PX[3]), (PX[4], PX[5]))):
    box(f"Stalp_{k}",   a, -0.02, -0.30, b, 0.42, Z1, M_MARM_D)
    box(f"Stalp_{k}_b", a - 0.03, -0.05, -0.30, b + 0.03, 0.45, 0.10, M_MARM_P)

box("Brau_N", XG, -0.07, Z_BRAU, W - 0.045, 0.05, Z1, M_MARM)
box("Brau_N_grinda", PX[0] - 0.07, -0.07, Z_BRAU, XG, 0.46, Z1, M_MARM)
box("Brau_W", W - 0.04, -0.07, Z_BRAU, W + 0.07, 0.90, Z1, M_MARM_P)
box("Brau_terasa_int", PX[1], TER_D - 0.06, Z_BRAU, XG, TER_D + 0.01, Z1, M_MARM_P)

box("Usa_garaj", PX[5], -0.05, 0.02, PX[6], 0.10, 2.12, M_GARAJ)
box("Usa_garaj_rost", (PX[5] + PX[6]) / 2 - 0.012, -0.06, 0.02, (PX[5] + PX[6]) / 2 + 0.012, 0.10, 2.12, M_FIER)
box("Usa_garaj_toc",  PX[5] - 0.06, -0.06, 2.12, PX[6] + 0.06, 0.10, 2.22, M_LEMN)
for zk in (0.45, 1.10, 1.75):
    box(f"Balama_st_{zk}", PX[5] + 0.03, -0.075, zk - 0.03, PX[5] + 0.55, -0.05, zk + 0.03, M_FIER)
    box(f"Balama_dr_{zk}", PX[6] - 0.55, -0.075, zk - 0.03, PX[6] - 0.03, -0.05, zk + 0.03, M_FIER)

for i, (x0, x1, dep) in enumerate(SEG):

    poly = [(0.0, Z1), (0.0, ZE_F - 0.03), (YRG, ZRG - 0.03), (dep, zroof(dep) - 0.03), (dep, Z1)]
    prism(f"Mans_seg{i}", poly, 'x', x0, x1, M_TENC)

for i, (x0, x1, dep) in enumerate(SEG):
    box(f"Banda_S{i}", x0, dep, Z1 - 0.07, x1, dep + 0.03, Z1 + 0.06, M_PILAS)
box("Banda_E", -0.03, TER_D, Z1 - 0.07, 0.0, D, Z1 + 0.06, M_PILAS)
box("Banda_W", W, 0.0, Z1 - 0.07, W + 0.03, SEG[-1][2], Z1 + 0.06, M_PILAS)
for i in range(len(SEG) - 1):
    xb = SEG[i][1]
    box(f"Banda_tr{i}", xb, SEG[i+1][2], Z1 - 0.07, xb + 0.03, SEG[i][2], Z1 + 0.06, M_PILAS)

box("Lambriu_N", LX0 - 0.05, -0.06, 2.90, W + 0.02, 0.01, ZE_F - 0.05, M_LEMN_X)
box("Lambriu_N_mic", PX[1] - 0.10, -0.06, 2.90, PX[2] + 0.10, 0.01, ZE_F - 0.05, M_LEMN_X)

_rb = 0.18
for _nm, _y0, _z0, _y1, _z1 in (("jos",  0.45 - _rb, 3.25 - _rb, 1.70 + _rb, 3.25),
                                ("sus",  0.45 - _rb, 4.15,       1.70 + _rb, 4.15 + _rb),
                                ("fata", 0.45 - _rb, 3.25,       0.45,       4.15),
                                ("spate", 1.70,      3.25,       1.70 + _rb, 4.15)):
    box(f"Rama_W_{_nm}", W - 0.01, _y0, _z0, W + 0.045, _y1, _z1, M_LEMN_Y)

def pilastru(axis, pos, u, z0, z1, wdt=0.34, prof=0.04, m=M_PILAS):
    n = f"Pil_{axis}{pos:.1f}_{u:.2f}"
    if axis == 'x':
        box(n, pos - prof, u - wdt/2, z0, pos + prof, u + wdt/2, z1, m)
    else:
        box(n, u - wdt/2, pos - prof, z0, u + wdt/2, pos + prof, z1, m)

pilastru('x', 0.0, TER_D + 0.20, 0.30, ZW, wdt=0.40)
pilastru('x', 0.0, D - 0.20, 0.30, ZW, wdt=0.40)
for u in (4.90, 7.95):
    pilastru('x', 0.0, u, 0.30, Z1 - 0.10, wdt=0.36)

pilastru('x', W, 0.22, 0.30, ZW, wdt=0.44)
pilastru('x', W, SEG[-1][2] - 0.22, 0.30, ZW, wdt=0.44)

for i, (x0, x1, dep) in enumerate(SEG):
    pilastru('y', dep, x0 + 0.24, 0.30, ZW, wdt=0.48)
    pilastru('y', dep, x1 - 0.24, 0.30, ZW, wdt=0.48)

pilastru('y', 0.0, W - 0.20, Z1 + 0.10, 2.85, wdt=0.40)

def thick(name, pts, t, m):
    n = len(pts)
    v = list(pts) + [(x, y, z - t) for (x, y, z) in pts]
    faces = [tuple(range(n)), tuple(range(2*n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((j, i, i + n, j + n))
    return mesh(name, v, faces, m)

def gable_tri(name, axis, a0, a1, u0, u1, ur, ze, zr, m):
    return prism(name, [(u0, ze), (ur, zr), (u1, ze)], axis, a0, a1, m)

XA, XB = -OVG, W + OVG

thick("Acop_fata", [(XA, -OV, zroof(-OV)), (XB, -OV, zroof(-OV)), (XB, YRG, ZRG), (XA, YRG, ZRG)], TR, M_TABLA)

for i, (x0, x1, dep) in enumerate(SEG):
    xa = XA if i == 0 else x0
    xb = XB if i == len(SEG) - 1 else x1
    ye = dep + OV
    thick(f"Acop_spate{i}", [(xa, YRG, ZRG), (xb, YRG, ZRG), (xb, ye, zroof(ye)), (xa, ye, zroof(ye))], TR, M_TABLA)
    if i < len(SEG) - 1:
        yn = SEG[i+1][2] + OV
        thick(f"Acop_consola{i}", [(x1, yn, zroof(yn)), (x1 + OV, yn, zroof(yn)),
                                   (x1 + OV, ye, zroof(ye)), (x1, ye, zroof(ye))], TR, M_TABLA)

box("Coama", XA, YRG - 0.10, ZRG - 0.02, XB, YRG + 0.10, ZRG + 0.05, M_ZINC)

def gable_red(name, x, dep, thick_x, m):
    ys = YRG + (ZRG - ZW) / P_S
    poly = [(0.0, ZW), (0.0, ZE_F), (YRG, ZRG)]
    if ys < dep:
        poly.append((ys, ZW))
    else:
        poly.append((dep, zroof(dep)))
        poly.append((dep, ZW))
    prism(name, poly, 'x', x, x + thick_x, m)

gable_red("Fronton_E", -0.02, SEG[0][2], 0.05, M_LEMN_Y)
gable_red("Fronton_W", W - 0.03, SEG[-1][2], 0.05, M_LEMN_Y)

def lucarna_fata(name, x0, x1, xr, zr, y_lvl, lov=0.35, lov_e=None, n_pane=3):
    lov_e = lov if lov_e is None else lov_e
    pf = (zr - ZE_F) / ((x1 - x0) / 2.0)
    ze_v, ze_e = ZE_F - lov * pf, ZE_F - lov_e * pf
    ze = ze_v

    y_end = y_lvl + (zr - (ZE_F + y_lvl * P_F)) / (1.0 + P_F)
    z_end = ZE_F + y_end * P_F + 0.02
    R0, R1, R2 = (xr, -OVG, zr), (xr, y_lvl, zr), (xr, y_end, z_end)
    for side, xe, ze in (("st", x0 - lov, ze_v), ("dr", x1 + lov_e, ze_e)):
        thick(f"{name}_{side}_A", [(xe, -OVG, ze), (xe, y_lvl, ze), R1, R0], TR, M_TABLA_P)
        thick(f"{name}_{side}_B", [(xe, y_lvl, ze), (xe, y_end, ze), R2], TR, M_TABLA_P)
        thick(f"{name}_{side}_C", [(xe, y_lvl, ze), R2, R1], TR, M_TABLA_P)
    gable_tri(f"{name}_fronton", 'y', -0.02, 0.26, x0, x1, xr, ZE_F - 0.02, zr, M_LEMN_X)
    box(f"{name}_coama", xr - 0.09, -OVG, zr - 0.02, xr + 0.09, y_lvl, zr + 0.05, M_ZINC)
    prism(f"{name}_finial", [(-OVG - 0.05, zr), (-OVG + 0.02, zr + 0.42), (-OVG + 0.09, zr)],
          'x', xr - 0.03, xr + 0.03, M_ZINC)
    top = [(x0 - lov, ze_v), (xr, zr), (x1 + lov_e, ze_e)]
    prism(f"{name}_pazie", top + [(u, z - 0.22) for (u, z) in reversed(top)], 'y', -OVG - 0.025, -OVG + 0.025, M_PAZIE)
    for kk in range(1, n_pane + 1):
        f = kk / (n_pane + 1.0)
        for xe, ze_s in ((x0 - lov + (xr - x0 + lov) * f, ze_v),
                         (x1 + lov_e - (x1 + lov_e - xr) * f, ze_e)):
            z = ze_s + (zr - ze_s) * f - TR
            box(f"{name}_pana_{kk}_{xe:.2f}", xe - 0.09, -OVG - 0.12, z - 0.24, xe + 0.09, 0.40, z - 0.02, M_GRINDA)
    return ze_v

lze = lucarna_fata("LucG", LX0, LX1, LXR, LZR, 1.80, lov_e=0.0)

SX0, SX1, SOUT = -0.30, 3.35, OV + 0.55
thick("Streasina_st", [(SX0, -OV + 0.02, zroof(-OV + 0.02)), (SX1, -OV + 0.02, zroof(-OV + 0.02)),
                       (SX1, -SOUT, zroof(-SOUT)), (SX0, -SOUT, zroof(-SOUT))], TR, M_TABLA)
box("Paz_st_fata", SX0, -SOUT - 0.05, zroof(-SOUT) - 0.24, SX1, -SOUT + 0.01, zroof(-SOUT) + 0.005, M_PAZIE)
for xs in (SX0, SX1):
    top = [(-SOUT, zroof(-SOUT)), (-OV, zroof(-OV))]
    prism(f"Paz_st_lat_{xs:.1f}", top + [(u, z - 0.24) for (u, z) in reversed(top)], 'x', xs - 0.025, xs + 0.025, M_PAZIE)
box("Jgheab_st", SX0, -SOUT - 0.16, zroof(-SOUT) - 0.39, SX1, -SOUT - 0.04, zroof(-SOUT) - 0.26, M_ZINC)
for kk in range(5):
    xg = SX0 + 0.25 + kk * (SX1 - SX0 - 0.50) / 4.0
    thick(f"Grinda_st_{kk}", [(xg - 0.07, -SOUT + 0.06, zroof(-SOUT + 0.06) - TR - 0.01),
                              (xg + 0.07, -SOUT + 0.06, zroof(-SOUT + 0.06) - TR - 0.01),
                              (xg + 0.07, 0.40, zroof(0.40) - TR - 0.01),
                              (xg - 0.07, 0.40, zroof(0.40) - TR - 0.01)], 0.22, M_GRINDA)

RZB = zroof(RYF) - 0.15
box("LucSp_fata", RX0, RYF - 0.22, RZB, RX1, RYF, RZE, M_LEMN_X)
gable_tri("LucSp_fronton", 'y', RYF - 0.22, RYF, RX0, RX1, RXR, RZE - 0.01, RZR, M_LEMN_X)
RYB = 7.40
for side, xe in (("st", RX0 - 0.28), ("dr", RX1 + 0.28)):
    thick(f"LucSp_{side}", [(xe, RYF + 0.30, RZE - 0.08), (xe, RYB, zroof(RYB) - 0.06),
                             (RXR, RYB, zroof(RYB) + 0.02), (RXR, RYF + 0.30, RZR)], 0.16, M_TABLA_P)
box("LucSp_geam", RXR - 0.30, RYF - 0.03, RZB + 0.15, RXR + 0.30, RYF + 0.01, RZE - 0.12, M_STICLA)
for kk in (1, 2):
    f = kk / 3.0
    for xe in (RX0 - 0.28 + (RXR - RX0 + 0.28) * f, RX1 + 0.28 - (RX1 + 0.28 - RXR) * f):
        z = (RZE - 0.08) + (RZR - RZE + 0.08) * f - 0.16
        box(f"LucSp_pana_{kk}_{xe:.2f}", xe - 0.07, RYF - 0.10, z - 0.20, xe + 0.07, RYF + 0.40, z - 0.02, M_GRINDA)

def pazie_profile(name, x, dep):
    top = [(-OV, zroof(-OV)), (YRG, ZRG), (dep + OV, zroof(dep + OV))]
    poly = top + [(u, z - 0.24) for (u, z) in reversed(top)]
    prism(name, poly, 'x', x - 0.025, x + 0.025, M_PAZIE)

pazie_profile("Pazie_E", XA, SEG[0][2])
pazie_profile("Pazie_W", XB, SEG[-1][2])
for i in range(len(SEG) - 1):
    x1, dep = SEG[i][1], SEG[i][2]
    yn = SEG[i+1][2] + OV
    top = [(yn, zroof(yn)), (dep + OV, zroof(dep + OV))]
    prism(f"Pazie_tr{i}", top + [(u, z - 0.24) for (u, z) in reversed(top)], 'x', x1 + OV - 0.025, x1 + OV + 0.025, M_PAZIE)

box("Pazie_fata_a", XA, -OV - 0.05, zroof(-OV) - 0.24, -0.30, -OV + 0.01, zroof(-OV) + 0.005, M_PAZIE)
box("Pazie_fata_b", 3.35, -OV - 0.05, zroof(-OV) - 0.24, XB, -OV + 0.01, zroof(-OV) + 0.005, M_PAZIE)
for i, (x0, x1, dep) in enumerate(SEG):
    xa = XA if i == 0 else x0
    xb = XB if i == len(SEG) - 1 else x1 + OV
    ye = dep + OV
    box(f"Pazie_spate{i}", xa, ye - 0.01, zroof(ye) - 0.24, xb, ye + 0.05, zroof(ye) + 0.005, M_PAZIE)
lt = [(RX0 - 0.28, RZE - 0.08), (RXR, RZR), (RX1 + 0.28, RZE - 0.08)]
prism("Pazie_lucSp", lt + [(u, z - 0.18) for (u, z) in reversed(lt)], 'y', RYF + 0.30 - 0.02, RYF + 0.30 + 0.02, M_PAZIE)

def rafter(name, x, y_out, y_in, pitch_sign):
    def zt(y):
        return zroof(y) - TR - 0.01
    thick(name, [(x, y_out, zt(y_out)), (x + 0.10, y_out, zt(y_out)),
                 (x + 0.10, y_in, zt(y_in)), (x, y_in, zt(y_in))], 0.15, M_CAPRIOR)

xx = XA + 0.30
k = 0
while xx < XB - 0.2:
    rafter(f"Capr_F{k}", xx, -OV + 0.03, 0.35, +1)
    xx += 0.72; k += 1
for i, (x0, x1, dep) in enumerate(SEG):
    xa = XA + 0.30 if i == 0 else x0 + 0.12
    xb = XB - 0.2 if i == len(SEG) - 1 else x1 + OV - 0.1
    xx = xa; k = 0
    while xx < xb:
        rafter(f"Capr_S{i}_{k}", xx, dep + OV - 0.03, dep - 0.35, -1)
        xx += 0.72; k += 1

def pane_along(name, x_out, x_in, dep, n_front=3, n_back=4):
    pts = []
    for kk in range(1, n_front + 1):
        f = kk / (n_front + 1.0)
        pts.append(-OV + (YRG + OV) * f)
    for kk in range(1, n_back + 1):
        f = kk / (n_back + 1.0)
        pts.append(YRG + (dep + OV - YRG) * f)
    for kk, y in enumerate(pts):
        z = zroof(y) - TR
        box(f"{name}_{kk}", min(x_out, x_in), y - 0.10, z - 0.26, max(x_out, x_in), y + 0.10, z - 0.02, M_GRINDA)

pane_along("Pana_E", XA - 0.12, 0.40, SEG[0][2], n_front=4, n_back=5)
pane_along("Pana_W", XB + 0.12, W - 0.40, SEG[-1][2], n_front=3, n_back=3)
for i in range(len(SEG) - 1):
    x1, dep = SEG[i][1], SEG[i][2]
    yn = SEG[i+1][2] + OV
    for kk in range(2):
        y = yn + (dep + OV - yn) * (kk + 1) / 3.0
        z = zroof(y) - TR
        box(f"Pana_tr{i}_{kk}", x1 - 0.30, y - 0.09, z - 0.24, x1 + OV + 0.10, y + 0.09, z - 0.02, M_GRINDA)

def vent(name, axis, a, u_c, z_b, size, m=M_ALB):
    h, t = size * 0.72, 0.075
    o = [(u_c - size/2, z_b), (u_c, z_b + h), (u_c + size/2, z_b)]
    i = [(u_c - size/2 + t*1.6, z_b + t), (u_c, z_b + h - t*1.4), (u_c + size/2 - t*1.6, z_b + t)]
    a0, a1 = a - 0.05, a + 0.05
    for k3 in range(3):
        p, q, r, s = o[k3], i[k3], o[(k3+1) % 3], i[(k3+1) % 3]
        v = ([(a0, p[0], p[1]), (a0, r[0], r[1]), (a0, s[0], s[1]), (a0, q[0], q[1])] if axis == 'x'
             else [(p[0], a0, p[1]), (r[0], a0, r[1]), (s[0], a0, s[1]), (q[0], a0, q[1])])
        v += ([(a1, y, z) for (_, y, z) in v] if axis == 'x' else [(x, a1, z) for (x, _, z) in v])
        mesh(f"{name}_{k3}", v, FACES, m)
    if axis == 'x':
        box(f"{name}_ax", a0, u_c - 0.04, z_b + t, a1, u_c + 0.04, z_b + h - t, m)
    else:
        box(f"{name}_ax", u_c - 0.04, a0, z_b + t, u_c + 0.04, a1, z_b + h - t, m)

    prism(f"{name}_g", i, axis, a0 + 0.005, a1 - 0.005, M_STICLA)

vent("Vent_E", 'x', 0.02, YRG, ZW + 0.62, 1.30)
vent("Vent_W", 'x', W - 0.02, YRG, ZW + 0.40, 1.05)
vent("Vent_luc", 'y', 0.02, LXR, ZE_F + 0.70, 1.20)

def gutter(name, x0, x1, y_out, y_in, z):
    box(name, x0, min(y_out, y_in), z - 0.13, x1, max(y_out, y_in), z, M_ZINC)
gutter("Jgheab_fata_a", XA, -0.30, -OV - 0.16, -OV - 0.04, zroof(-OV) - 0.26)
gutter("Jgheab_fata_b", 3.35, XB, -OV - 0.16, -OV - 0.04, zroof(-OV) - 0.26)
for i, (x0, x1, dep) in enumerate(SEG):
    xa = XA if i == 0 else x0
    xb = XB if i == len(SEG) - 1 else x1 + OV
    ye = dep + OV
    gutter(f"Jgheab_spate{i}", xa, xb, ye + 0.04, ye + 0.16, zroof(ye) - 0.26)

def downpipe(name, x, y, z_top, z_bot=-0.9):
    r = 0.055
    v = [(x + dx, y + dy, zz) for zz in (z_bot, z_top) for (dx, dy) in ((-r,-r),(r,-r),(r,r),(-r,r))]
    mesh(name, v, FACES, M_ZINC)
    box(name + "_cot", x - r, y - r - (0.55 if y < 5 else -0.05), z_top - 0.02,
        x + r, y + r + (0.05 if y < 5 else 0.55), z_top + 0.10, M_ZINC)

downpipe("Burlan_F1", PX[4] + 0.20, -0.07, zroof(-OV) - 0.30, -0.35)
downpipe("Burlan_F2", W + 0.07, 0.25, zroof(-OV) - 0.30, -0.10)
downpipe("Burlan_F3", -0.07, 0.30, zroof(-OV) - 0.30, -0.9)
downpipe("Burlan_F4", PX[3] + 0.08, -0.07, zroof(-OV) - 0.30, -0.35)

for nm, (lx, lz) in {"Lampa_intrare": (0.62, 2.18), "Lampa_garaj": (8.55, 2.22)}.items():
    box(nm, lx - 0.07, -0.20, lz - 0.06, lx + 0.07, -0.07, lz + 0.06, M_FIER)
    box(nm + "_glob", lx - 0.05, -0.18, lz - 0.04, lx + 0.05, -0.09, lz + 0.04, M_ALB)

box("Aerisire", 11.35, 2.55, zroof(2.6) - 0.05, 11.47, 2.67, zroof(2.6) + 0.42, M_ZINC)

for nm, (bx, dep) in {"Burlan_S3": (11.85, SEG[3][2]), "Burlan_S2": (8.05, SEG[2][2]),
                      "Burlan_S1": (4.76, SEG[1][2]), "Burlan_S0": (1.60, SEG[0][2])}.items():
    downpipe(nm, bx, dep + 0.07, zroof(dep + OV) - 0.30, -1.35)

def window(name, face, u0, u1, z0, z1, pos, cols=2, rows=1,
           surround=M_ALB, muntin=M_ALB, cadru=0.06, glass=M_STICLA, mullion_every=0, mw=0.018,
           trim=M_RAMA, trim_b=0.055):
    d = 0.11
    if face in ('N', 'S'):
        y0, y1 = (pos - d, pos + 0.02) if face == 'N' else (pos - 0.02, pos + d)
        gy = y0 + 0.04 if face == 'N' else y1 - 0.06
        box(name + "_g", u0 + cadru, gy, z0 + cadru, u1 - cadru, gy + 0.02, z1 - cadru, glass)
        for (a, b, c, e) in ((u0, u1, z0, z0 + cadru), (u0, u1, z1 - cadru, z1),
                             (u0, u0 + cadru, z0 + cadru, z1 - cadru), (u1 - cadru, u1, z0 + cadru, z1 - cadru)):
            box(name + "_f", a, y0, c, b, y1, e, surround)
        for kk in range(1, cols):
            x = u0 + (u1 - u0) * kk / cols
            if mullion_every and kk % mullion_every == 0:
                box(name + "_ml", x - mw * 1.7, y0, z0, x + mw * 1.7, y1, z1, trim)
            else:
                box(name + "_mv", x - mw, y0 + 0.01, z0, x + mw, y1 - 0.01, z1, muntin)
        for kk in range(1, rows):
            z = z0 + (z1 - z0) * kk / rows
            box(name + "_mh", u0, y0 + 0.01, z - mw, u1, y1 - 0.01, z + mw, muntin)

        if face == 'N':
            box(name + "_glaf", u0 - 0.03, y0 - 0.04, z0 - 0.035, u1 + 0.03, y0 - 0.005, z0 - 0.005, M_ZINC)
        else:
            box(name + "_glaf", u0 - 0.03, y1 + 0.005, z0 - 0.035, u1 + 0.03, y1 + 0.04, z0 - 0.005, M_ZINC)
    else:
        x0, x1 = (pos - 0.02, pos + d) if face == 'E' else (pos - d, pos + 0.02)

        g0, g1 = (pos - 0.007, pos - 0.001) if face == 'E' else (pos + 0.001, pos + 0.007)
        box(name + "_g", g0, u0 + cadru, z0 + cadru, g1, u1 - cadru, z1 - cadru, glass)
        for (a, b, c, e) in ((u0, u1, z0, z0 + cadru), (u0, u1, z1 - cadru, z1),
                             (u0, u0 + cadru, z0 + cadru, z1 - cadru), (u1 - cadru, u1, z0 + cadru, z1 - cadru)):
            box(name + "_f", x0, a, c, x1, b, e, surround)
        for kk in range(1, cols):
            y = u0 + (u1 - u0) * kk / cols
            if mullion_every and kk % mullion_every == 0:
                box(name + "_ml", x0, y - mw * 1.7, z0, x1, y + mw * 1.7, z1, trim)
            else:
                box(name + "_mv", x0 + 0.01, y - mw, z0, x1 - 0.01, y + mw, z1, muntin)
        for kk in range(1, rows):
            z = z0 + (z1 - z0) * kk / rows
            box(name + "_mh", x0 + 0.01, u0, z - mw, x1 - 0.01, u1, z + mw, muntin)
        if face == 'E':
            box(name + "_glaf", x0 - 0.04, u0 - 0.03, z0 - 0.035, x0 - 0.005, u1 + 0.03, z0 - 0.005, M_ZINC)
        else:
            box(name + "_glaf", x1 + 0.005, u0 - 0.03, z0 - 0.035, x1 + 0.04, u1 + 0.03, z0 - 0.005, M_ZINC)

    if trim is not None and trim_b > 0:
        b = trim_b
        ramele = ((u0 - b, z0 - b, u1 + b, z0), (u0 - b, z1, u1 + b, z1 + b),
                  (u0 - b, z0, u0, z1), (u1, z0, u1 + b, z1))
        for kk, (a, c, bb, e) in enumerate(ramele):
            if face == 'N':
                box(f"{name}_tr{kk}", a, pos - 0.035, c, bb, pos + 0.005, e, trim)
            elif face == 'S':
                box(f"{name}_tr{kk}", a, pos - 0.005, c, bb, pos + 0.035, e, trim)
            elif face == 'E':
                box(f"{name}_tr{kk}", pos - 0.035, a, c, pos + 0.005, bb, e, trim)
            else:
                box(f"{name}_tr{kk}", pos - 0.005, a, c, pos + 0.035, bb, e, trim)

def ancadrament(name, face, u0, u1, z0, z1, pos, b=0.15, prof=0.035):
    o = 0.10
    if face in ('N', 'S'):
        y0, y1 = (pos - prof, pos + 0.01) if face == 'N' else (pos - 0.01, pos + prof)
        for (a, c, bb, e) in ((u0-o-b, z0-o-b, u1+o+b, z0-o), (u0-o-b, z1+o, u1+o+b, z1+o+b),
                              (u0-o-b, z0-o, u0-o, z1+o), (u1+o, z0-o, u1+o+b, z1+o)):
            box(name, a, y0, c, bb, y1, e, M_PILAS)
    else:
        x0, x1 = (pos - 0.01, pos + prof) if face == 'E' else (pos - prof, pos + 0.01)
        for (a, c, bb, e) in ((u0-o-b, z0-o-b, u1+o+b, z0-o), (u0-o-b, z1+o, u1+o+b, z1+o+b),
                              (u0-o-b, z0-o, u0-o, z1+o), (u1+o, z0-o, u1+o+b, z1+o)):
            box(name, x0, a, c, x1, bb, e, M_PILAS)

def jardiniera(name, face, u0, u1, z, pos, m=M_LEMN):
    if face == 'E':
        box(name, pos - 0.28, u0 - 0.05, z - 0.26, pos + 0.04, u1 + 0.05, z, m)
    elif face == 'W':
        box(name, pos - 0.04, u0 - 0.05, z - 0.26, pos + 0.28, u1 + 0.05, z, m)
    elif face == 'S':
        box(name, u0 - 0.05, pos - 0.04, z - 0.26, u1 + 0.05, pos + 0.28, z, m)
    else:
        box(name, u0 - 0.05, pos - 0.28, z - 0.26, u1 + 0.05, pos + 0.04, z, m)

window("N_band_mica", 'N', PX[1] + 0.05, PX[2] - 0.05, 2.98, 4.30, 0.0, cols=9, rows=3, mullion_every=3)
window("N_2", 'N', 4.45, 5.80, 3.00, 3.95, 0.0, cols=2, rows=3)
window("N_loggia", 'N', 7.75, 11.85, 2.98, 4.32, 0.0, cols=12, rows=3, mullion_every=3)

window("T_1", 'N', 4.95, 6.20, 0.95, 2.05, TER_D, cols=2)
window("T_2", 'N', 1.10, 1.75, 1.05, 2.00, TER_D, cols=1)

for nm, a, b in (("E_p_1", 2.70, 4.35), ("E_p_2", 5.65, 7.40)):
    window(nm, 'E', a, b, 1.08, 2.14, 0.0, cols=2)
    ancadrament(nm + "_a", 'E', a, b, 1.08, 2.14, 0.0)
    jardiniera(nm + "_j", 'E', a, b, 1.08, 0.0)

window("E_m_1", 'E', 2.75, 4.35, 3.00, 3.95, 0.0, cols=2)
window("E_m_2", 'E', 5.60, 7.25, 3.00, 3.95, 0.0, cols=2)

_e3 = (0.60, 1.92, 2.98, 4.32)

window("E_m_3", 'E', _e3[0], _e3[1], _e3[2], _e3[3], 0.0,
       cols=4, rows=3, mullion_every=2, cadru=0.038, mw=0.014)

window("W_m_A", 'W', 0.45, 1.70, 3.25, 4.15, W, cols=2, rows=3)
window("W_m_B", 'W', 2.25, 3.45, 3.25, 4.15, W, cols=2, rows=2)
window("W_p_1", 'W', 2.65, 3.70, 1.50, 2.02, W, cols=2)
for u in (2.25, 4.25):
    pilastru('x', W, u, 0.30, Z1 - 0.10, wdt=0.34)

D0, D1, D2, D3 = SEG[0][2], SEG[1][2], SEG[2][2], SEG[3][2]

window("S3_m", 'S', 9.45, 10.45, 3.50, 4.55, D3, cols=2, rows=2)
window("S3_p", 'S', 8.80, 10.00, 1.30, 1.92, D3, cols=2)

window("S2_m", 'S', 6.70, 7.65, 3.30, 4.25, D2, cols=2)
jardiniera("S2_m_j", 'S', 6.70, 7.65, 3.30, D2, m=M_ALB)
window("S2_p", 'S', 6.50, 7.70, 1.17, 1.72, D2, cols=2)

window("S1_p", 'S', 4.35, 4.75, 1.35, 1.85, D1, cols=1)

window("S0_m1", 'S', 2.30, 2.72, 3.45, 4.00, D0, cols=1)
window("S0_m2", 'S', 0.70, 1.12, 3.45, 4.00, D0, cols=1)
window("S0_p",  'S', 1.65, 2.02, 1.57, 2.19, D0, cols=1)

M_GARD   = mat_boards("GardLemn", srgb(72, 56, 42), srgb(104, 84, 64), 'X', period=0.14, rough=0.92)
M_POARTA = mat_plain("PoartaFier", srgb(58, 42, 32), 0.45, 0.35)
M_STALPG = mat_stucco("StalpPoarta", srgb(150, 138, 126), rough=0.92, scale=18.0, strength=0.3)

def gard_uluci(name, a0, a1, fix, axis, h=1.15, pas=0.135, lat=0.092):
    n = max(1, int((a1 - a0) / pas))
    for i in range(n):
        a = a0 + i * pas
        zg = z_teren(a, fix) if axis == 'x' else z_teren(fix, a)
        poly = [(a, zg - 0.12), (a + lat, zg - 0.12), (a + lat, zg + h - 0.09),
                (a + lat / 2, zg + h), (a, zg + h - 0.09)]
        if axis == 'x':
            prism(f"{name}_u{i}", poly, 'y', fix - 0.016, fix + 0.016, M_GARD)
        else:
            prism(f"{name}_u{i}", poly, 'x', fix - 0.016, fix + 0.016, M_GARD)

    seg = 2.0
    ns = max(1, int((a1 - a0) / seg))
    for j in range(ns):
        b0 = a0 + j * seg
        b1 = min(a1, b0 + seg)
        zg = z_teren((b0 + b1) / 2, fix) if axis == 'x' else z_teren(fix, (b0 + b1) / 2)
        for zr in (zg + 0.24, zg + 0.88):
            if axis == 'x':
                box(f"{name}_s{j}_{zr:.2f}", b0, fix + 0.016, zr - 0.035, b1, fix + 0.062, zr + 0.035, M_GARD)
            else:
                box(f"{name}_s{j}_{zr:.2f}", fix + 0.016, b0, zr - 0.035, fix + 0.062, b1, zr + 0.035, M_GARD)

    k = 0
    a = a0
    while a < a1:
        zg = z_teren(a, fix) if axis == 'x' else z_teren(fix, a)
        if axis == 'x':
            box(f"{name}_st{k}", a - 0.05, fix + 0.016, zg - 0.15, a + 0.05, fix + 0.086, zg + h + 0.03, M_GARD)
        else:
            box(f"{name}_st{k}", fix + 0.016, a - 0.05, zg - 0.15, fix + 0.086, a + 0.05, zg + h + 0.03, M_GARD)
        a += 2.4; k += 1

gard_uluci("Gard_spate", -8.0, 20.0, 16.2, 'x')
gard_uluci("Gard_est",   12.0, 16.2, 19.5, 'y')

YP, ZP = -9.0, 0.30
def bara_diag(name, x0, z0, x1, z1, t, y0, y1, m=M_POARTA):
    prism(name, [(x0, z0), (x0 + t, z0), (x1 + t, z1), (x1, z1)], 'y', y0, y1, m)

def panou_fier(name, x0, x1, h=1.70, plin=0.42):
    y0, y1 = YP - 0.03, YP + 0.03
    box(f"{name}_plin", x0, y0, ZP, x1, y1, ZP + plin, M_POARTA)
    box(f"{name}_sus",  x0, y0, ZP + h - 0.06, x1, y1, ZP + h, M_POARTA)
    box(f"{name}_mij",  x0, y0, ZP + plin, x1, y1, ZP + plin + 0.05, M_POARTA)
    nb = max(1, int((x1 - x0) / 0.145))
    for i in range(1, nb):
        x = x0 + (x1 - x0) * i / nb
        box(f"{name}_v{i}", x - 0.012, y0 + 0.008, ZP + plin, x + 0.012, y1 - 0.008, ZP + h - 0.06, M_POARTA)
    nc = max(1, int((x1 - x0) / 0.62))
    for i in range(nc):
        xa = x0 + (x1 - x0) * i / nc
        xb = x0 + (x1 - x0) * (i + 1) / nc
        bara_diag(f"{name}_d{i}a", xa, ZP + plin + 0.06, xb, ZP + h - 0.10, 0.018, y0 + 0.004, y1 - 0.004)
        bara_diag(f"{name}_d{i}b", xb, ZP + plin + 0.06, xa, ZP + h - 0.10, 0.018, y0 + 0.004, y1 - 0.004)

panou_fier("Poarta", 7.05, 13.10)
panou_fier("Gard_fier", -0.60, 6.85)
for nm, xs in (("Stalp_p1", -0.75), ("Stalp_p2", 6.92), ("Stalp_p3", 13.22)):
    box(nm, xs - 0.11, YP - 0.11, ZP - 0.5, xs + 0.11, YP + 0.11, ZP + 1.86, M_STALPG)

M_FANT   = mat_tiles("Fantana", srgb(196, 184, 162), srgb(216, 208, 192), bw=0.34, bh=0.34, rough=0.55)
M_SINDR  = mat_plain("Sindrila", srgb(128, 48, 38), 0.88)
M_LEMN_F = mat_boards("LemnFoisor", srgb(96, 70, 46), srgb(132, 100, 68), 'X', period=0.12, rough=0.88)

FX, FY = 17.3, 13.4
_zf = z_teren(FX, FY)
box("Fantana_corp",  FX - 0.38, FY - 0.38, _zf - 0.30, FX + 0.38, FY + 0.38, _zf + 0.80, M_FANT)
box("Fantana_capac", FX - 0.45, FY - 0.45, _zf + 0.80, FX + 0.45, FY + 0.45, _zf + 0.89, M_BETON)
box("Pompa_teava",   FX - 0.05, FY - 0.05, _zf + 0.89, FX + 0.05, FY + 0.05, _zf + 1.52, M_ZINC)
box("Pompa_gura",    FX - 0.05, FY - 0.34, _zf + 1.30, FX + 0.05, FY - 0.04, _zf + 1.41, M_ZINC)
box("Pompa_parghie", FX - 0.03, FY + 0.04, _zf + 1.46, FX + 0.03, FY + 0.46, _zf + 1.53, M_FIER)

GX, GY, GL = -7.2, -5.8, 1.32
_zg = z_teren(GX, GY)
box("Foisor_pardoseala", GX - GL, GY - GL, _zg - 0.12, GX + GL, GY + GL, _zg + 0.12, M_BETON)
for sx in (-1, 1):
    for sy in (-1, 1):
        px, py = GX + sx * (GL - 0.14), GY + sy * (GL - 0.14)
        box(f"Foisor_stalp{sx}{sy}", px - 0.07, py - 0.07, _zg + 0.12, px + 0.07, py + 0.07, _zg + 2.28, M_LEMN_F)
for nm, (a0, b0, a1, b1) in {"n": (GX - GL, GY - GL, GX + GL, GY - GL + 0.10),
                             "s": (GX - GL, GY + GL - 0.10, GX + GL, GY + GL),
                             "v": (GX - GL, GY - GL, GX - GL + 0.10, GY + GL),
                             "e": (GX + GL - 0.10, GY - GL, GX + GL, GY + GL)}.items():
    box(f"Foisor_grinda_{nm}", a0, b0, _zg + 2.28, a1, b1, _zg + 2.42, M_LEMN_F)
_zr, _ov = _zg + 2.42, 0.38
_c = [(GX - GL - _ov, GY - GL - _ov), (GX + GL + _ov, GY - GL - _ov),
      (GX + GL + _ov, GY + GL + _ov), (GX - GL - _ov, GY + GL + _ov)]
mesh("Foisor_acoperis", [(x, y, _zr) for (x, y) in _c] + [(GX, GY, _zr + 1.08)],
     [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2, 1)], M_SINDR)

import random as _rnd_mod
M_SCOARTA = mat_stucco("Scoarta",  srgb(88, 74, 60), rough=0.95, scale=26.0, strength=0.5)
M_FRUNZE  = mat_stucco("Frunzis",  srgb(62, 96, 44), rough=0.92, scale=9.0, strength=0.8)
M_FRUNZE2 = mat_stucco("Frunzis2", srgb(78, 112, 52), rough=0.92, scale=11.0, strength=0.8)
M_VITA    = mat_stucco("Vita",     srgb(70, 104, 48), rough=0.94, scale=13.0, strength=0.9)
M_FLOARE_R= mat_plain("FloareRosie", srgb(158, 32, 34), 0.82)
M_FLOARE_G= mat_plain("FloareGalb",  srgb(196, 154, 40), 0.82)

def _sfera(name, loc, r, mat, turtire=1.0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale[2] = turtire
    ob.data.materials.append(mat)
    return ob

def copac(name, x, y, h=6.5, rt=0.10, rc=1.5, seed=0):
    rnd = _rnd_mod.Random(seed)
    z0 = z_teren(x, y)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=rt, depth=h, location=(x, y, z0 + h / 2))
    tr = bpy.context.active_object
    tr.name = f"{name}_trunchi"
    tr.data.materials.append(M_SCOARTA)
    for i in range(4):
        dx, dy = rnd.uniform(-0.75, 0.75), rnd.uniform(-0.75, 0.75)
        dz = rnd.uniform(-0.6, 0.9)
        _sfera(f"{name}_coroana{i}", (x + dx, y + dy, z0 + h * 0.80 + dz),
               rc * rnd.uniform(0.62, 1.02), M_FRUNZE if i % 2 else M_FRUNZE2, turtire=0.78)

for i, (cx, cy, ch) in enumerate([(1.2, 15.4, 6.6), (5.0, 15.0, 7.2), (8.6, 15.6, 6.8),
                                  (12.0, 15.1, 7.4), (15.4, 15.5, 6.4)]):
    copac(f"Pom_sp{i}", cx, cy, h=ch, rt=0.085, rc=0.92, seed=10 + i)

copac("Pom_fata1", 1.8, -6.8, h=7.4, rt=0.16, rc=2.3, seed=31)
copac("Pom_fata2", 10.8, -7.6, h=6.8, rt=0.14, rc=2.0, seed=32)
copac("Pom_est",  21.5, 9.5, h=7.8, rt=0.17, rc=2.4, seed=33)

def vita(name, a0, a1, fix, axis, h=1.5, pas=0.75, seed=0):
    rnd = _rnd_mod.Random(seed)
    n = max(1, int((a1 - a0) / pas))
    for i in range(n + 1):
        a = a0 + i * pas
        x, y = (a, fix) if axis == 'x' else (fix, a)
        z0 = z_teren(x, y)
        for j in range(2):
            _sfera(f"{name}_{i}_{j}", (x + rnd.uniform(-0.2, 0.2), y + rnd.uniform(-0.2, 0.2),
                                       z0 + h * (0.55 + 0.45 * j) + rnd.uniform(-0.1, 0.1)),
                   rnd.uniform(0.5, 0.72), M_VITA, turtire=0.85)

vita("Vita_est", 12.4, 16.0, 18.9, 'y', seed=5)
vita("Vita_vest", 3.4, 7.4, -1.9, 'x', seed=6)

for jn, (ya, yb) in enumerate(((2.70, 4.25), (5.60, 7.15))):
    rnd = _rnd_mod.Random(40 + jn)
    k = 0
    yy = ya + 0.12
    while yy < yb - 0.10:
        _sfera(f"Muscata{jn}_{k}", (-0.14, yy, 1.16), 0.085, M_FRUNZE, turtire=0.75)
        _sfera(f"Muscata{jn}_{k}f", (-0.14 + rnd.uniform(-0.05, 0.05), yy, 1.235), 0.055, M_FLOARE_R)
        yy += 0.17; k += 1

rnd = _rnd_mod.Random(77)
for i in range(26):
    fx = -0.55 - rnd.uniform(0.0, 1.05)
    fy = 3.1 + rnd.uniform(0.0, 5.0)
    fz = z_teren(fx, fy)
    _sfera(f"Tufa_{i}", (fx, fy, fz + 0.30), rnd.uniform(0.26, 0.42), M_FRUNZE2, turtire=0.8)
    _sfera(f"Floare_{i}", (fx + rnd.uniform(-0.15, 0.15), fy + rnd.uniform(-0.15, 0.15), fz + 0.56),
           rnd.uniform(0.05, 0.085), M_FLOARE_G if i % 3 else M_FLOARE_R)

world = bpy.data.worlds.new("W")
bpy.context.scene.world = world
world.use_nodes = True
nt = world.node_tree
bg = nt.nodes["Background"]
bg.inputs[0].default_value = (0.55, 0.66, 0.86, 1)
bg.inputs[1].default_value = 0.55
bg_cam = nt.nodes.new("ShaderNodeBackground")
bg_cam.inputs[0].default_value = (*srgb(110, 160, 228), 1)
bg_cam.inputs[1].default_value = 1.0
lp  = nt.nodes.new("ShaderNodeLightPath")
mix = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
nt.links.new(bg.outputs[0], mix.inputs[1])
nt.links.new(bg_cam.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], nt.nodes["World Output"].inputs["Surface"])

def sun(name, energy, rgb, rx, rz, angle=1.5):
    ld = bpy.data.lights.new(name, type='SUN')
    ld.energy, ld.color, ld.angle = energy, rgb, math.radians(angle)
    ob = bpy.data.objects.new(name, ld)
    ob.rotation_euler = (math.radians(rx), 0, math.radians(rz))
    COLL.objects.link(ob)
    return ob

sun("Soare",    5.2, (1.0, 0.955, 0.880), 50, -35)
sun("Umplere1", 1.6, (0.74, 0.82, 1.0), 40, 150, 6)
sun("Umplere2", 1.2, (0.84, 0.88, 1.0), 55, 75, 6)

ter_data = bpy.data.lights.new("TerasaBounce", type='AREA')
ter_data.shape, ter_data.size, ter_data.size_y = 'RECTANGLE', 7.0, 1.8
ter_data.energy, ter_data.color = 120.0, (1.0, 0.93, 0.72)
ter = bpy.data.objects.new("TerasaBounce", ter_data)
ter.location = (4.2, 0.55, Z1 - 0.35)
ter.rotation_euler = (math.radians(55), 0, 0)
COLL.objects.link(ter)

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 32
cam = bpy.data.objects.new("Camera", cam_data)
COLL.objects.link(cam)
sc = bpy.context.scene
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1920, 1200
try:
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = -0.10
    sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
try:
    sc.eevee.use_gtao = True
    sc.eevee.use_shadows = True
    sc.eevee.taa_render_samples = 48
except Exception:
    pass

result = {"obiecte": len(bpy.data.objects),
          "streasina_fata": round(ZE_F, 2),
          "streasini_spate": [round(zroof(s[2]), 2) for s in SEG]}
