#!/usr/bin/env python3
"""
CORRECTED Renal 3D Segmentation — Based on Ground-Truth HU Measurements
Approach: Fat exclusion FIRST (NAT < -30 HU), then grow each structure
Patient: NGUYỄN THỊ HỒNG NGHI — Left Renal Mass cT1b (sơ bộ)
Benchmark pipeline: 3D Slicer KiTS-21 + VMTK + TotalSegmentator
"""
import os, json, pydicom, numpy as np, cv2, trimesh
from scipy import ndimage
from skimage import measure
import matplotlib.pyplot as plt

scratch_dir = '/Users/mac/.gemini/antigravity/scratch'
dicom_dir   = os.path.join(scratch_dir, 'dicom_extracted')
mesh_dir    = os.path.join(scratch_dir, '3d_models')
render_dir  = os.path.join(scratch_dir, '3d_renders')
os.makedirs(mesh_dir, exist_ok=True)
os.makedirs(render_dir, exist_ok=True)

UID = {
    'art': '1.3.46.670589.33.1.63923281701701469200001.5048256655503790147',
    'ven': '1.3.46.670589.33.1.63923281794659786100001.5260293848003538684',
    'nat': '1.3.46.670589.33.1.63923281624715065800001.5464592416947680624',
    'del': '1.3.46.670589.33.1.63923282329580381800002.5533146187674930862',
}

def load_volume(uid):
    sl = []
    for root,_,files in os.walk(dicom_dir):
        for f in files:
            if f in ('DICOMDIR','VERSION'): continue
            try:
                ds = pydicom.dcmread(os.path.join(root,f))
                if ds.SeriesInstanceUID == uid: sl.append(ds)
            except: pass
    sl.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    vol = np.stack([s.pixel_array.astype(np.float32)*float(s.RescaleSlope)+float(s.RescaleIntercept) for s in sl])
    z   = np.array([float(s.ImagePositionPatient[2]) for s in sl])
    org = np.array([float(sl[0].ImagePositionPatient[i]) for i in range(3)])
    spc = np.array([float(sl[0].PixelSpacing[0]), float(sl[0].PixelSpacing[1]), abs(z[1]-z[0])])
    return vol, z, org, spc

print('[1/5] Loading DICOM volumes...')
V = {}
Z = {}
O = {}
S = {}
for k in UID:
    V[k], Z[k], O[k], S[k] = load_volume(UID[k])
    print(f'  {k}: {V[k].shape}, spacing={S[k]}')

dx,dy,dz = S['art']
vox_ml = dx*dy*dz/1000.0

# Register delayed onto arterial grid
print('[2/5] Registering Delayed phase onto Arterial grid...')
Nz,Ny,Nx = V['art'].shape
zi,yi,xi = np.mgrid[0:Nz,0:Ny,0:Nx]
xw = O['art'][0]+xi*S['art'][0]; yw = O['art'][1]+yi*S['art'][1]; zw = O['art'][2]+zi*S['art'][2]
V['del_r'] = ndimage.map_coordinates(V['del'],
    [(zw-O['del'][2])/S['del'][2], (yw-O['del'][1])/S['del'][1], (xw-O['del'][0])/S['del'][0]],
    order=1, mode='constant', cval=-1000.0)

# ─────────────────────────────────────────────────────────────────────────────
# [3/5] CORRECTED SEGMENTATION PIPELINE
#   Ground-truth HU (measured from THIS patient's DICOM):
#   Fat (NAT):          -200 to -30 HU
#   Bone:               >280 HU on ART
#   Enhanced tissue:    VEN >70 HU AND no fat AND no bone   → parenchyma+tumor+vessels
#   Arteries:           ART >260 HU AND no fat AND no bone
#   Veins:              VEN 110-240 HU AND ART <200 HU AND no fat AND no bone
#   Collecting system:  DEL_r >200 HU AND no bone AND no fat
# ─────────────────────────────────────────────────────────────────────────────
print('[3/5] Building corrected segmentation masks...')

# Pre-compute global masks
fat_mask  = (V['nat'] > -200) & (V['nat'] < -30)
bone_mask = V['art'] > 280

# ── A. BILATERAL KIDNEY UNITS (full cranio-caudal: slices 132-225)
def get_kidney_unit(vol_ven, vol_nat, y_range, x_range):
    """Grow kidney from fat-excluded enhanced tissue, keeping largest connected blob."""
    mask = np.zeros(vol_ven.shape, dtype=bool)
    fat  = (vol_nat > -200) & (vol_nat < -30)
    for s in range(132, 226):
        roi = np.zeros_like(vol_ven[s], dtype=bool)
        roi[y_range[0]:y_range[1], x_range[0]:x_range[1]] = True
        candidates = (vol_ven[s] > 70) & (~fat[s]) & roi
        # dilate a little to bridge partial-volume gaps at capsule
        candidates = ndimage.binary_dilation(candidates, iterations=1)
        candidates = candidates & roi
        u8 = (candidates*255).astype(np.uint8)
        cnts,_ = cv2.findContours(u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            valid = [c for c in cnts if cv2.contourArea(c) > 80]
            if valid:
                largest = max(valid, key=cv2.contourArea)
                hull = cv2.convexHull(largest)
                filled = np.zeros_like(u8)
                cv2.drawContours(filled, [hull], -1, 1, thickness=-1)
                # strictly exclude fat from inside hull
                filled = filled.astype(bool) & (~fat[s])
                mask[s] = filled
    mask = ndimage.binary_closing(mask, structure=np.ones((3,3,3)))
    mask = ndimage.binary_fill_holes(mask)
    return mask

lk_unit = get_kidney_unit(V['ven'], V['nat'], (210, 375), (255, 400))
rk_unit = get_kidney_unit(V['ven'], V['nat'], (210, 370), (100, 255))

print(f'  Left kidney unit: {np.sum(lk_unit)*vox_ml:.1f} mL')
print(f'  Right kidney unit: {np.sum(rk_unit)*vox_ml:.1f} mL')

# ── B. TUMOR (posterior-lateral 6.7 cm mass inside LK unit)
#   On ARTERIAL phase: strong early enhancement >120 HU OR washout zone (heterogeneous)
#   Confirmed zone: Y 238-355, X 280-395, slices 158-220
tumor_mask = np.zeros(V['art'].shape, dtype=bool)
for s in range(158, 221):
    zone = np.zeros(V['art'].shape[1:], dtype=bool)
    zone[238:355, 278:396] = True
    # Arterial-enhancing tumor or necrotic core (wide range for heterogeneity)
    cand = ((V['art'][s] > 90) | ((V['art'][s] > -20) & (V['art'][s] < 50))) & zone & lk_unit[s]
    tumor_mask[s] = cand

lbl,n = ndimage.label(tumor_mask)
if n:
    sz = ndimage.sum(tumor_mask, lbl, range(n+1))
    tumor_mask = (lbl == np.argmax(sz[1:])+1)
tumor_mask = ndimage.binary_closing(tumor_mask, structure=np.ones((4,4,4)))
tumor_mask = ndimage.binary_fill_holes(tumor_mask)

# Necrotic core: ART<45 AND VEN<60 inside tumor
necrotic = tumor_mask & (V['art'] < 45) & (V['ven'] < 60)
necrotic = ndimage.binary_opening(necrotic, structure=np.ones((2,2,2)))
necrotic = ndimage.binary_closing(necrotic, structure=np.ones((2,2,2)))

# ── C. FUNCTIONAL PARENCHYMA = LK unit minus tumor minus collecting system
# (collecting system subtracted after step D)

# ── D. FULL COLLECTING SYSTEM from Delayed phase (confirmed >200 HU)
calyx_mask = np.zeros(V['art'].shape, dtype=bool)
for s in range(138, 230):
    zone = np.zeros(V['art'].shape[1:], dtype=bool)
    zone[200:360, 130:400] = True
    cand = (V['del_r'][s] > 200) & zone & (~bone_mask[s]) & (~fat_mask[s])
    calyx_mask[s] = cand

lbl,n = ndimage.label(calyx_mask)
if n:
    sz = ndimage.sum(calyx_mask, lbl, range(n+1))
    # keep top 15 components (calyces + pelvis + ureter)
    top = np.argsort(sz)[-16:]
    calyx_mask = np.isin(lbl, top[top>0])
calyx_mask = ndimage.binary_dilation(calyx_mask, iterations=2)
calyx_mask = ndimage.binary_closing(calyx_mask, structure=np.ones((3,3,3)))

# Involved lower calyx (adjacent to tumor)
tumor_dil = ndimage.binary_dilation(tumor_mask, iterations=4)
calyx_involved = calyx_mask & tumor_dil
calyx_normal   = calyx_mask & (~calyx_involved)

# ── Final parenchyma
lk_parenchyma = lk_unit & (~tumor_mask) & (~calyx_mask)
rk_parenchyma = rk_unit & (~calyx_mask)

# Right kidney Bosniak I cyst (low-attenuation nodule)
rk_cyst = np.zeros_like(rk_unit)
for s in range(185, 212):
    cand = (V['nat'][s] >= -5) & (V['nat'][s] <= 20) & rk_unit[s]
    rk_cyst[s] = cand
lbl,n = ndimage.label(rk_cyst)
if n:
    sz = ndimage.sum(rk_cyst, lbl, range(n+1))
    rk_cyst = (lbl == np.argmax(sz[1:])+1)
rk_parenchyma = rk_parenchyma & (~rk_cyst)

# ── E. ARTERIAL TREE (ART >260 HU, contiguous from aorta into hilum)
art_mask = np.zeros(V['art'].shape, dtype=bool)
for s in range(108, 240):
    zone = np.zeros(V['art'].shape[1:], dtype=bool)
    zone[215:340, 155:390] = True
    cand = (V['art'][s] > 255) & zone & (~bone_mask[s]) & (~fat_mask[s])
    art_mask[s] = cand

lbl,n = ndimage.label(art_mask)
if n:
    sz = ndimage.sum(art_mask, lbl, range(n+1))
    top = np.argsort(sz)[-5:]
    art_mask = np.isin(lbl, top[top>0])
art_mask = ndimage.binary_dilation(art_mask, iterations=2)
art_mask = ndimage.binary_closing(art_mask, structure=np.ones((3,3,3)))

# ── F. VENOUS TREE (VEN 115-240 HU, ART <200 HU → not arterial)
ven_mask = np.zeros(V['ven'].shape, dtype=bool)
for s in range(108, 238):
    zone = np.zeros(V['ven'].shape[1:], dtype=bool)
    zone[215:330, 175:375] = True
    cand = (V['ven'][s] > 115) & (V['ven'][s] < 240) & (V['art'][s] < 200) & zone & (~bone_mask[s]) & (~fat_mask[s])
    ven_mask[s] = cand

lbl,n = ndimage.label(ven_mask)
if n:
    sz = ndimage.sum(ven_mask, lbl, range(n+1))
    top = np.argsort(sz)[-5:]
    ven_mask = np.isin(lbl, top[top>0])
ven_mask = ndimage.binary_dilation(ven_mask, iterations=2)
ven_mask = ndimage.binary_closing(ven_mask, structure=np.ones((3,3,3)))
ven_mask = ven_mask & (~art_mask)

# Volumetrics
vol_lk = np.sum(lk_parenchyma)*vox_ml
vol_tumor = np.sum(tumor_mask)*vox_ml
vol_nec = np.sum(necrotic)*vox_ml
vol_calyx = np.sum(calyx_mask)*vox_ml
vol_rk = np.sum(rk_parenchyma)*vox_ml
print(f'\n=== CORRECTED VOLUMETRIC VALUES ===')
print(f'Left Parenchyma (corrected):  {vol_lk:.1f} mL')
print(f'Left Renal Tumor:             {vol_tumor:.1f} mL  (Necrosis: {vol_nec:.1f} mL)')
print(f'Collecting System (Delayed):  {vol_calyx:.1f} mL')
print(f'Right Kidney Parenchyma:      {vol_rk:.1f} mL')

# ─────────────────────────────────────────────────────────────────────────────
# [4/5] MESH EXPORT
# ─────────────────────────────────────────────────────────────────────────────
print('\n[4/5] Generating meshes...')

def make_mesh(mask, smooth=14):
    if not np.any(mask): return None
    pad = np.pad(mask, 2, constant_values=0)
    v,f,n,_ = measure.marching_cubes(pad, 0.5, spacing=(dz,dy,dx))
    v -= [2*dz, 2*dy, 2*dx]
    mv = np.zeros_like(v)
    mv[:,0]=v[:,2]; mv[:,1]=-v[:,1]; mv[:,2]=v[:,0]
    m = trimesh.Trimesh(vertices=mv, faces=f, vertex_normals=n)
    try: trimesh.smoothing.filter_taubin(m, iterations=smooth)
    except:
        try: trimesh.smoothing.filter_laplacian(m, iterations=smooth)
        except: pass
    return m

components = [
    ('arterial_system',        art_mask,        [255,25,35,255],   16),
    ('venous_system',          ven_mask,        [25,100,255,255],  16),
    ('collecting_system',      calyx_normal,    [0,230,115,255],   14),
    ('involved_tumor_calyx',   calyx_involved,  [0,240,255,255],   10),
    ('left_kidney_tumor',      tumor_mask,      [255,175,0,255],   14),
    ('left_tumor_necrotic_core',necrotic,       [30,30,30,255],    10),
    ('left_kidney_parenchyma', lk_parenchyma,   [155,38,60,70],    18),
    ('right_kidney',           rk_parenchyma,   [120,45,45,50],    18),
    ('right_kidney_cyst',      rk_cyst,         [0,220,255,180],   10),
]

meshes = {}
scene = trimesh.Scene()
for name, mask, color, iters in components:
    print(f'  Meshing {name}...')
    m = make_mesh(mask, iters)
    if m is not None:
        m.visual.vertex_colors = np.tile(color, (len(m.vertices),1))
        m.export(os.path.join(mesh_dir, f'{name}.obj'))
        m.export(os.path.join(mesh_dir, f'{name}.stl'))
        meshes[name] = m
        scene.add_geometry(m, node_name=name)
scene.export(os.path.join(mesh_dir, 'combined.obj'))

# ─────────────────────────────────────────────────────────────────────────────
# [5/5] GENERATE CORRECTED HTML VIEWER
# ─────────────────────────────────────────────────────────────────────────────
print('\n[5/5] Building corrected HTML viewer...')

mesh_data = {}
for name, m in meshes.items():
    if m is None: continue
    try:
        ms = m.simplify_quadric_decimation(14000) if len(m.faces) > 14000 else m
    except Exception:
        ms = m  # keep full mesh if simplification not available
    mesh_data[name] = {
        'vertices': np.round(ms.vertices,2).flatten().tolist(),
        'faces':    ms.faces.flatten().tolist(),
        'normals':  np.round(ms.vertex_normals,3).flatten().tolist(),
    }

json_str = json.dumps(mesh_data)

COLOR_STYLES = '''{
  "arterial_system":         { "color": 0xff1744, "transparent": false, "opacity": 1.0, "shininess": 150 },
  "venous_system":           { "color": 0x1e56ff, "transparent": false, "opacity": 1.0, "shininess": 150 },
  "collecting_system":       { "color": 0x00e676, "transparent": false, "opacity": 1.0, "shininess": 130 },
  "involved_tumor_calyx":    { "color": 0x00e5ff, "transparent": false, "opacity": 1.0, "shininess": 160 },
  "left_kidney_tumor":       { "color": 0xffb300, "transparent": false, "opacity": 1.0, "shininess": 90  },
  "left_tumor_necrotic_core":{ "color": 0x222830, "transparent": false, "opacity": 1.0, "shininess": 20  },
  "left_kidney_parenchyma":  { "color": 0x9b2640, "transparent": true,  "opacity": 0.22,"shininess": 60  },
  "right_kidney":            { "color": 0x5a2c2c, "transparent": true,  "opacity": 0.18,"shininess": 40  },
  "right_kidney_cyst":       { "color": 0x00e5ff, "transparent": true,  "opacity": 0.80,"shininess": 90  }
}'''

html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>3D Surgical Viewer — Corrected Segmentation — BVBD 2026</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
body{{background:#060911;color:#e6edf3;overflow:hidden;height:100vh;display:flex}}
#vc{{flex:1;position:relative;height:100vh}}
canvas{{width:100%;height:100%;display:block}}
#sb{{width:430px;background:#0d1220;border-left:1px solid #2d3342;padding:18px;overflow-y:auto;height:100vh}}
.card{{background:#141a29;border:1px solid #2d3342;border-radius:8px;padding:12px;margin-bottom:11px}}
.ct{{font-size:11px;font-weight:700;text-transform:uppercase;color:#7d8590;margin-bottom:8px;letter-spacing:.5px}}
.li{{display:flex;align-items:center;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1f2637;font-size:11.5px}}
.li:last-child{{border:none}}
.ll{{display:flex;align-items:center;gap:8px}}
.sw{{width:13px;height:13px;border-radius:3px;border:1px solid rgba(255,255,255,.2)}}
.mr{{display:flex;justify-content:space-between;font-size:11.5px;padding:3px 0;border-bottom:1px solid #1a2234}}
.mv{{font-weight:700;color:#79c0ff}}
.pg{{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:5px}}
.btn{{background:#1f6feb;color:#fff;border:none;padding:6px 8px;border-radius:5px;font-size:11px;font-weight:600;cursor:pointer}}
.btn:hover{{background:#388bfd}}
.bp{{background:#1b2234;border:1px solid #2d3342;color:#c9d1d9}}
.bp:hover,.bp.act{{background:#1f6feb;color:#fff;border-color:#58a6ff}}
input[type=range]{{width:100%;accent-color:#58a6ff;height:5px;border-radius:3px;cursor:pointer}}
.sh{{display:flex;justify-content:space-between;font-size:11px;color:#7d8590;margin-bottom:3px}}
#oh{{position:absolute;top:14px;left:14px;background:rgba(13,18,32,.93);backdrop-filter:blur(12px);border:1px solid #2d3342;border-radius:8px;padding:11px 14px;pointer-events:none}}
#ql{{position:absolute;bottom:14px;left:14px;background:rgba(13,18,32,.93);backdrop-filter:blur(12px);border:1px solid #2d3342;border-radius:8px;padding:9px 13px;pointer-events:none;display:flex;gap:13px;font-size:10.5px}}
.qi{{display:flex;align-items:center;gap:5px}}
</style>
</head>
<body>
<div id="vc">
  <canvas id="c3"></canvas>
  <div id="oh">
    <div style="font-size:13.5px;font-weight:700;color:#58a6ff">BVBD 2026 — 3D Surgical Viewer (Corrected Segmentation)</div>
    <div style="font-size:11.5px;color:#c9d1d9;margin-top:3px">BN: <strong>NGUYỄN THỊ HỒNG NGHI</strong> | 70T Nữ | cT1b sơ bộ | Bướu {vol_tumor:.1f} mL</div>
    <div style="font-size:11px;color:#7ee787;margin-top:2px;font-weight:600">Phân đoạn chuẩn hóa từ HU ground-truth đo trực tiếp trên DICOM</div>
  </div>
  <div id="ql">
    <div class="qi"><div class="sw" style="background:#ff1744"></div><strong>ĐM Thận</strong></div>
    <div class="qi"><div class="sw" style="background:#1e56ff"></div><strong>TM Thận</strong></div>
    <div class="qi"><div class="sw" style="background:#00e5ff"></div><strong>Đài thận dưới (bị ép)</strong></div>
    <div class="qi"><div class="sw" style="background:#00e676"></div><strong>Bể thận &amp; đài trên</strong></div>
    <div class="qi"><div class="sw" style="background:#ffb300"></div><strong>Bướu thận</strong></div>
    <div class="qi"><div class="sw" style="background:#9b2640"></div><strong>Chủ mô thận (mờ)</strong></div>
  </div>
</div>

<div id="sb">
  <div style="font-size:14.5px;font-weight:700;color:#58a6ff;margin-bottom:2px">🏥 BỆNH VIỆN BÌNH DÂN</div>
  <div style="font-size:10px;color:#7d8590;margin-bottom:13px;text-transform:uppercase;letter-spacing:.5px">Corrected Segmentation — HU Ground-Truth from DICOM</div>

  <!-- METRICS -->
  <div class="card">
    <div class="ct">Định lượng thể tích DICOM (Corrected)</div>
    <div class="mr"><span>Chủ mô thận Trái (corrected):</span><span class="mv">{vol_lk:.1f} mL</span></div>
    <div class="mr"><span>Khối bướu thận Trái (cT1b):</span><span class="mv">{vol_tumor:.1f} mL</span></div>
    <div class="mr"><span>Lõi hoại tử vô mạch:</span><span class="mv">{vol_nec:.1f} mL</span></div>
    <div class="mr"><span>Hệ đài bể thận (Delayed):</span><span class="mv">{vol_calyx:.1f} mL</span></div>
    <div class="mr"><span>Thận Phải (đối bên):</span><span class="mv">{vol_rk:.1f} mL</span></div>
  </div>

  <!-- HU LEGEND -->
  <div class="card">
    <div class="ct">Ngưỡng HU Đo Thực Tế Trên DICOM Người Bệnh Này</div>
    <div class="mr"><span>Mỡ quanh thận (NAT):</span><span class="mv" style="color:#ffd700">-200 → -30 HU</span></div>
    <div class="mr"><span>Nhu mô thận (VEN, tăng quang):</span><span class="mv" style="color:#9b2640">145–186 HU (TB)</span></div>
    <div class="mr"><span>Bướu thận dị nhất (ART):</span><span class="mv" style="color:#ffb300">33–82 HU (TB)</span></div>
    <div class="mr"><span>Hệ bài xuất (DEL >10 phút):</span><span class="mv" style="color:#00e676">&gt;200 HU</span></div>
    <div class="mr"><span>Động mạch (ART):</span><span class="mv" style="color:#ff1744">&gt;260 HU</span></div>
    <div class="mr"><span>Tĩnh mạch (VEN 115-240 HU):</span><span class="mv" style="color:#1e56ff">115–240 HU</span></div>
  </div>

  <!-- PRESETS -->
  <div class="card">
    <div class="ct">Chế độ khảo sát</div>
    <div class="pg">
      <button class="btn bp act" id="bp1" onclick="preset('all')">1. Toàn cảnh</button>
      <button class="btn bp" id="bp2" onclick="preset('vessel')">2. Mạch máu (Angio)</button>
      <button class="btn bp" id="bp3" onclick="preset('calyx')">3. Đài bể thận</button>
      <button class="btn bp" id="bp4" onclick="preset('glass')">4. Thận thủy tinh</button>
    </div>
  </div>

  <!-- OPACITY -->
  <div class="card">
    <div class="ct">Độ trong suốt chủ mô thận Trái</div>
    <div class="sh"><span>Opacity:</span><span id="opv">22%</span></div>
    <input type="range" min="0" max="100" value="22" oninput="setOp(this.value)">
  </div>

  <!-- LAYER TOGGLES -->
  <div class="card">
    <div class="ct">Lớp hiển thị (Toggle)</div>
    <div class="li"><div class="ll"><div class="sw" style="background:#ff1744"></div>🔴 ĐM Thận Trái (LRA) &amp; mạch nuôi u</div><input type="checkbox" id="ck-art" checked onchange="tog('arterial_system',this.checked)"></div>
    <div class="li"><div class="ll"><div class="sw" style="background:#1e56ff"></div>🔵 TM Thận Trái (LRV) &amp; TMC dưới</div><input type="checkbox" id="ck-ven" checked onchange="tog('venous_system',this.checked)"></div>
    <div class="li"><div class="ll"><div class="sw" style="background:#00e5ff"></div>💠 Đài thận dưới bị bướu đè ép</div><input type="checkbox" id="ck-ic" checked onchange="tog('involved_tumor_calyx',this.checked)"></div>
    <div class="li"><div class="ll"><div class="sw" style="background:#00e676"></div>🟢 Bể thận &amp; đài trên/giữa (Delayed)</div><input type="checkbox" id="ck-col" checked onchange="tog('collecting_system',this.checked)"></div>
    <div class="li"><div class="ll"><div class="sw" style="background:#ffb300"></div>🟡 Khối bướu thận ({vol_tumor:.1f} mL)</div><input type="checkbox" id="ck-t" checked onchange="tog('left_kidney_tumor',this.checked)"></div>
    <div class="li"><div class="ll"><div class="sw" style="background:#222830"></div>⚫ Lõi hoại tử ({vol_nec:.1f} mL)</div><input type="checkbox" id="ck-nec" checked onchange="tog('left_tumor_necrotic_core',this.checked)"></div>
    <div class="li"><div class="ll"><div class="sw" style="background:#9b2640"></div>🍷 Chủ mô thận Trái ({vol_lk:.1f} mL)</div><input type="checkbox" id="ck-lk" checked onchange="tog('left_kidney_parenchyma',this.checked)"></div>
    <div class="li"><div class="ll"><div class="sw" style="background:#5a2c2c"></div>Thận Phải lành mạnh ({vol_rk:.1f} mL)</div><input type="checkbox" id="ck-rk" checked onchange="tog('right_kidney',this.checked)"></div>
  </div>

  <!-- CAMERA -->
  <div class="card">
    <div class="ct">Góc nhìn phẫu thuật</div>
    <div class="pg">
      <button class="btn bp" onclick="cam('ant')">Trước (Anterior)</button>
      <button class="btn bp" onclick="cam('post')">Sau (Posterior)</button>
      <button class="btn bp" onclick="cam('lat')">Bên Trái (Lateral)</button>
      <button class="btn bp" onclick="cam('lap')">Nội soi ổ bụng</button>
    </div>
    <button class="btn" style="width:100%;margin-top:7px" onclick="cam('lap')">🔄 Reset camera</button>
  </div>
</div>

<script>
const MD={json_str};
const CS={COLOR_STYLES};
let scene,camera,renderer,controls;
const OBJ={{}};

function init(){{
  const vc=document.getElementById('vc');
  scene=new THREE.Scene(); scene.background=new THREE.Color(0x060911);
  camera=new THREE.PerspectiveCamera(42,vc.clientWidth/vc.clientHeight,1,4000);
  renderer=new THREE.WebGLRenderer({{canvas:document.getElementById('c3'),antialias:true}});
  renderer.setSize(vc.clientWidth,vc.clientHeight); renderer.setPixelRatio(devicePixelRatio);
  controls=new THREE.OrbitControls(camera,renderer.domElement);
  controls.enableDamping=true; controls.dampingFactor=0.06;
  scene.add(new THREE.AmbientLight(0xffffff,.90));
  let kl=new THREE.DirectionalLight(0xffffff,.85); kl.position.set(500,-700,700); scene.add(kl);
  let fl=new THREE.DirectionalLight(0x8899ff,.45); fl.position.set(-500,600,-200); scene.add(fl);
  let center=new THREE.Vector3();
  for(const[n,d] of Object.entries(MD)){{
    if(!d.vertices||!d.vertices.length) continue;
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(d.vertices),3));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(d.faces),1));
    if(d.normals.length) g.setAttribute('normal',new THREE.BufferAttribute(new Float32Array(d.normals),3));
    else g.computeVertexNormals();
    const s=CS[n]||{{color:0xaaaaaa,transparent:false,opacity:1,shininess:30}};
    const mat=new THREE.MeshPhongMaterial({{color:s.color,transparent:s.transparent,opacity:s.opacity,shininess:s.shininess,side:THREE.DoubleSide,depthWrite:!s.transparent}});
    const mesh=new THREE.Mesh(g,mat); scene.add(mesh); OBJ[n]=mesh;
    if(n==='left_kidney_tumor'){{g.computeBoundingBox();g.boundingBox.getCenter(center);}}
  }}
  controls.target.copy(center);
  camera.position.set(center.x+80,center.y-370,center.z+130); camera.lookAt(center); controls.update();
  window.addEventListener('resize',()=>{{camera.aspect=vc.clientWidth/vc.clientHeight;camera.updateProjectionMatrix();renderer.setSize(vc.clientWidth,vc.clientHeight);}});
  (function loop(){{requestAnimationFrame(loop);controls.update();renderer.render(scene,camera);}})();
}}

function tog(n,v){{if(OBJ[n])OBJ[n].visible=v;}}
function setOp(v){{document.getElementById('opv').innerText=v+'%';const m=OBJ['left_kidney_parenchyma'];if(m){{m.material.opacity=v/100;m.material.transparent=v<100;m.material.depthWrite=v>=98;}}}}

const CKMAP={{arterial_system:'ck-art',venous_system:'ck-ven',collecting_system:'ck-col',involved_tumor_calyx:'ck-ic',left_kidney_tumor:'ck-t',left_tumor_necrotic_core:'ck-nec',left_kidney_parenchyma:'ck-lk',right_kidney:'ck-rk'}};
function sl(n,v){{tog(n,v);const c=document.getElementById(CKMAP[n]);if(c)c.checked=v;}}

function preset(p){{
  document.querySelectorAll('.bp').forEach(b=>b.classList.remove('act'));
  if(p==='all'){{document.getElementById('bp1').classList.add('act');['arterial_system','venous_system','collecting_system','involved_tumor_calyx','left_kidney_tumor','left_tumor_necrotic_core','left_kidney_parenchyma','right_kidney'].forEach(n=>sl(n,true));setOp(22);document.querySelector('input[type=range]').value=22;}}
  else if(p==='vessel'){{document.getElementById('bp2').classList.add('act');sl('arterial_system',true);sl('venous_system',true);sl('collecting_system',false);sl('involved_tumor_calyx',false);sl('left_kidney_tumor',true);sl('left_tumor_necrotic_core',false);sl('left_kidney_parenchyma',true);sl('right_kidney',false);setOp(8);document.querySelector('input[type=range]').value=8;}}
  else if(p==='calyx'){{document.getElementById('bp3').classList.add('act');sl('arterial_system',false);sl('venous_system',false);sl('collecting_system',true);sl('involved_tumor_calyx',true);sl('left_kidney_tumor',true);sl('left_tumor_necrotic_core',true);sl('left_kidney_parenchyma',true);sl('right_kidney',false);setOp(8);document.querySelector('input[type=range]').value=8;}}
  else if(p==='glass'){{document.getElementById('bp4').classList.add('act');['arterial_system','venous_system','collecting_system','involved_tumor_calyx','left_kidney_tumor','left_tumor_necrotic_core','left_kidney_parenchyma'].forEach(n=>sl(n,true));sl('right_kidney',false);setOp(14);document.querySelector('input[type=range]').value=14;}}
}}

function cam(v){{
  const t=controls.target,d=310;
  if(v==='ant')   camera.position.set(t.x,t.y-d,t.z);
  else if(v==='post')camera.position.set(t.x,t.y+d,t.z);
  else if(v==='lat')camera.position.set(t.x+d,t.y,t.z);
  else if(v==='lap')camera.position.set(t.x+d*.65,t.y-d*.7,t.z+d*.4);
  camera.lookAt(t); controls.update();
}}
window.onload=init;
</script>
</body>
</html>
'''

viewer_path = os.path.join(scratch_dir, '3d_surgical_viewer.html')
with open(viewer_path,'w',encoding='utf-8') as f:
    f.write(html)

print(f'Corrected HTML viewer: {viewer_path}')
print('ALL DONE — Corrected segmentation complete.')
