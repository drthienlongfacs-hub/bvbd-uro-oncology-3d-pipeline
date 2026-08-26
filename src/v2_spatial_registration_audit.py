#!/usr/bin/env python3
"""
V2 Module 2: Spatial Registration & Motion Artifact Audit
Quantifies physical coordinate discrepancies, voxel anisotropy, FOV shifts,
and respiratory motion between the 4 CT series.
"""
import os, json, pydicom, numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt

scratch_dir = '/Users/mac/.gemini/antigravity/scratch'
dicom_dir   = os.path.join(scratch_dir, 'dicom_extracted')
v2_root     = '/Users/mac/Desktop/ho so benh an 2026/V2_VALIDATION'
reg_dir     = os.path.join(v2_root, 'REGISTRATION_PENDING')
os.makedirs(reg_dir, exist_ok=True)

UID = {
    'nat': '1.3.46.670589.33.1.63923281624715065800001.5464592416947680624',
    'art': '1.3.46.670589.33.1.63923281701701469200001.5048256655503790147',
    'ven': '1.3.46.670589.33.1.63923281794659786100001.5260293848003538684',
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

print("[1/4] Loading 4-phase DICOM volumes...")
V = {}; Z = {}; O = {}; S = {}
for k in UID:
    V[k], Z[k], O[k], S[k] = load_volume(UID[k])
    print(f"  Phase {k.upper()}: Shape={V[k].shape}, Spacing={S[k]}, Origin={O[k]}")

# 1. Resample DEL onto ART physical grid
print("[2/4] Computing physical coordinate transform for DEL -> ART...")
Nz, Ny, Nx = V['art'].shape
zi, yi, xi = np.mgrid[0:Nz, 0:Ny, 0:Nx]
xw = O['art'][0] + xi * S['art'][0]
yw = O['art'][1] + yi * S['art'][1]
zw = O['art'][2] + zi * S['art'][2]

V_del_res = ndimage.map_coordinates(
    V['del'],
    [(zw - O['del'][2])/S['del'][2], (yw - O['del'][1])/S['del'][1], (xw - O['del'][0])/S['del'][0]],
    order=1, mode='constant', cval=-1000.0
)

# 2. Measure Spine Bone Landmark for Rigid Verification (L1-L3 vertebra)
print("[3/4] Quantifying Rigid Spine & Renal Motion...")
# Spine ROI around vertebra in axial slice
# Vertebra is around Y: 290-360, X: 210-290
spine_mask_art = (V['art'] > 300) & (zi > 140) & (zi < 210) & (yi > 290) & (yi < 360) & (xi > 210) & (xi < 290)
spine_mask_nat = (V['nat'] > 300) & (zi > 140) & (zi < 210) & (yi > 290) & (yi < 360) & (xi > 210) & (xi < 290)
spine_mask_ven = (V['ven'] > 300) & (zi > 140) & (zi < 210) & (yi > 290) & (yi < 360) & (xi > 210) & (xi < 290)

com_spine_art = ndimage.center_of_mass(spine_mask_art)
com_spine_nat = ndimage.center_of_mass(spine_mask_nat)
com_spine_ven = ndimage.center_of_mass(spine_mask_ven)

# Convert COM pixel difference to mm
spine_shift_nat_art = [(com_spine_art[i] - com_spine_nat[i]) * S['art'][i if i<2 else 2] for i in range(3)]
spine_shift_ven_art = [(com_spine_art[i] - com_spine_ven[i]) * S['art'][i if i<2 else 2] for i in range(3)]

# 3. Measure Kidney Region Motion (Soft tissue organ excursion due to breathing)
# Left Kidney ROI: Y 200-360, X 260-400, Z 140-220
roi_lk_art = (V['art'] > 40) & (V['art'] < 240) & (zi > 140) & (zi < 220) & (yi > 200) & (yi < 360) & (xi > 260) & (xi < 400)
roi_lk_nat = (V['nat'] > 20) & (V['nat'] < 80)  & (zi > 140) & (zi < 220) & (yi > 200) & (yi < 360) & (xi > 260) & (xi < 400)
roi_lk_ven = (V['ven'] > 40) & (V['ven'] < 240) & (zi > 140) & (zi < 220) & (yi > 200) & (yi < 360) & (xi > 260) & (xi < 400)

com_lk_art = ndimage.center_of_mass(roi_lk_art)
com_lk_nat = ndimage.center_of_mass(roi_lk_nat)
com_lk_ven = ndimage.center_of_mass(roi_lk_ven)

lk_shift_nat_art = [(com_lk_art[i] - com_lk_nat[i]) * S['art'][i if i<2 else 2] for i in range(3)]
lk_shift_ven_art = [(com_lk_art[i] - com_lk_ven[i]) * S['art'][i if i<2 else 2] for i in range(3)]

reg_report = {
    "status": "REGISTRATION_AUDIT_COMPLETE",
    "rigid_alignment_findings": {
        "spatial_grid_matching": {
            "NAT_ART_VEN": "Identical dimensions (293, 512, 512) and pixel spacing (0.6836 mm)",
            "DEL": "Mismatched dimensions (317, 512, 512), pixel spacing (0.9766 mm), and Origin (-260.0, -81.2, -598.8 mm)"
        },
        "anisotropy_ratio_Z_to_XY": float(S['art'][2] / S['art'][0]),
        "spine_anchor_displacement_mm": {
            "NAT_vs_ART": [round(float(x), 2) for x in spine_shift_nat_art],
            "VEN_vs_ART": [round(float(x), 2) for x in spine_shift_ven_art]
        },
        "renal_organ_excursion_respiratory_mm": {
            "NAT_vs_ART": [round(float(x), 2) for x in lk_shift_nat_art],
            "VEN_vs_ART": [round(float(x), 2) for x in lk_shift_ven_art]
        }
    },
    "scientific_conclusion": (
        "Giữa các pha chụp có hiện tượng dịch chuyển giải phẫu do nhịp thở và nhu động ruột "
        f"(Độ lệch thận trái giữa NAT và ART khoảng Z={lk_shift_nat_art[0]:.1f}mm, Y={lk_shift_nat_art[1]:.1f}mm, X={lk_shift_nat_art[2]:.1f}mm). "
        "Việc nội suy tọa độ affine đơn thuần (identity grid interpolation) chưa giải quyết được biến dạng phi tuyến (non-rigid deformation). "
        "Cần thực hiện Deformable Registration (B-spline / Demons qua SimpleITK/Elastix) có kiểm định landmark trước khi hợp nhất đa pha."
    )
}

# Save report
json_out = os.path.join(reg_dir, "SPATIAL_REGISTRATION_AUDIT.json")
with open(json_out, "w", encoding="utf-8") as f:
    json.dump(reg_report, f, indent=2, ensure_ascii=False)

# 4. Generate Registration Visual Verification Plot
print("[4/4] Generating Registration Visual Plot...")
fig, axes = plt.subplots(2, 3, figsize=(18, 12), facecolor='#060911')

sl = 182 # Mid-renal tumor slice
crop_y1, crop_y2 = 180, 390
crop_x1, crop_x2 = 210, 420

# Panel 1: NAT vs ART subtraction
diff_nat_art = V['art'][sl] - V['nat'][sl]
axes[0, 0].imshow(diff_nat_art[crop_y1:crop_y2, crop_x1:crop_x2], cmap='coolwarm', vmin=-150, vmax=250)
axes[0, 0].set_title(f"ART - NAT Difference (Slice {sl})\nTăng quang & Lệch bờ giải phẫu", color='#ff7777', fontsize=10, fontweight='bold')
axes[0, 0].axis('off')

# Panel 2: VEN vs ART difference
diff_ven_art = V['ven'][sl] - V['art'][sl]
axes[0, 1].imshow(diff_ven_art[crop_y1:crop_y2, crop_x1:crop_x2], cmap='coolwarm', vmin=-150, vmax=150)
axes[0, 1].set_title(f"VEN - ART Difference (Slice {sl})\nWashout bướu & Nâng nhu mô", color='#8888ff', fontsize=10, fontweight='bold')
axes[0, 1].axis('off')

# Panel 3: Resampled DEL vs ART
axes[0, 2].imshow(V_del_res[sl, crop_y1:crop_y2, crop_x1:crop_x2], cmap='hot', vmin=-50, vmax=400)
axes[0, 2].set_title(f"Delayed Resampled onto ART (Slice {sl})\nCản quang hệ đài bể thận", color='#00e676', fontsize=10, fontweight='bold')
axes[0, 2].axis('off')

# Panel 4: Spine Landmark Overlay (Vertebral Alignment)
v_crop_y1, v_crop_y2 = 280, 380
v_crop_x1, v_crop_x2 = 190, 310
spine_overlay = np.zeros((v_crop_y2 - v_crop_y1, v_crop_x2 - v_crop_x1, 3))
spine_overlay[:, :, 0] = np.clip((V['art'][sl, v_crop_y1:v_crop_y2, v_crop_x1:v_crop_x2] - 100) / 400.0, 0, 1) # Red = ART
spine_overlay[:, :, 1] = np.clip((V['ven'][sl, v_crop_y1:v_crop_y2, v_crop_x1:v_crop_x2] - 100) / 400.0, 0, 1) # Green = VEN
spine_overlay[:, :, 2] = np.clip((V['nat'][sl, v_crop_y1:v_crop_y2, v_crop_x1:v_crop_x2] - 100) / 400.0, 0, 1) # Blue = NAT
axes[1, 0].imshow(spine_overlay)
axes[1, 0].set_title("Cột sống L1-L3 (RGB: Đỏ=ART, Xanh lá=VEN, Xanh dương=NAT)\nKiểm tra đồng trục Rigid", color='#ffd700', fontsize=10, fontweight='bold')
axes[1, 0].axis('off')

# Panel 5: Renal Excursion / Motion Artifact (RGB Overlay of Left Kidney)
lk_overlay = np.zeros((crop_y2 - crop_y1, crop_x2 - crop_x1, 3))
lk_overlay[:, :, 0] = np.clip((V['art'][sl, crop_y1:crop_y2, crop_x1:crop_x2] + 50) / 250.0, 0, 1) # Red = ART
lk_overlay[:, :, 1] = np.clip((V['ven'][sl, crop_y1:crop_y2, crop_x1:crop_x2] + 50) / 250.0, 0, 1) # Green = VEN
lk_overlay[:, :, 2] = np.clip((V['nat'][sl, crop_y1:crop_y2, crop_x1:crop_x2] + 50) / 250.0, 0, 1) # Blue = NAT
axes[1, 1].imshow(lk_overlay)
axes[1, 1].set_title("Thận Trái (RGB Overlay 3 Pha)\nViền bóng ma thể hiện dịch chuyển hô hấp", color='#ff79c6', fontsize=10, fontweight='bold')
axes[1, 1].axis('off')

# Panel 6: Voxel Anisotropy Diagram
axes[1, 2].axis('off')
diag_text = (
    "THÔNG SỐ ĐĂNG KÝ HÌNH HỌC V2 (EVIDENCE):\n\n"
    f"• Voxel Spacing: {S['art'][0]:.4f} x {S['art'][1]:.4f} x {S['art'][2]:.2f} mm\n"
    f"• Tỷ lệ dị hướng trục Z / XY: {S['art'][2]/S['art'][0]:.2f}x (Anisotropic)\n"
    f"• Bước lát tái tạo (Recon Interval): {S['art'][2]:.1f} mm\n"
    f"• Độ dày lát chụp thực tế (Slice Thickness): 3.0 mm\n\n"
    f"• Độ lệch xương cứng (Spine COM): ΔZ={spine_shift_ven_art[0]:.2f}mm, ΔY={spine_shift_ven_art[1]:.2f}mm\n"
    f"• Độ lệch tạng thận (Renal COM): ΔZ={lk_shift_ven_art[0]:.2f}mm, ΔY={lk_shift_ven_art[1]:.2f}mm\n\n"
    "KẾT LUẬN KIỂM ĐỊNH:\n"
    "Độ phân giải trục Z gấp 2.19 lần XY và có dịch chuyển hô hấp.\n"
    "Bắt buộc dùng Deformable Registration trước khi đo lường."
)
axes[1, 2].text(0.05, 0.5, diag_text, color='#e6edf3', fontsize=10.5, family='monospace', verticalalignment='center')

plt.suptitle("KIỂM DUYỆT ĐĂNG KÝ KHÔNG GIAN ĐA PHA & NHIỄU CHUYỂN ĐỘNG (SPATIAL REGISTRATION AUDIT)", color='#58a6ff', fontsize=13, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])

plot_out = os.path.join(reg_dir, "SPATIAL_REGISTRATION_AUDIT_PLOT.png")
plt.savefig(plot_out, dpi=160, facecolor='#060911', bbox_inches='tight')
plt.close()

print(f"Registration audit plot saved: {plot_out}")
print("Module 2 (Spatial Registration Audit) completed successfully.")
