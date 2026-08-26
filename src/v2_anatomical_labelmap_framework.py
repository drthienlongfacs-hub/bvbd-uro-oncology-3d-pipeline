#!/usr/bin/env python3
"""
V2 Module 4: 11-Layer Anatomical Protocol Specification & Expert Annotation Framework
Establishes the Gold-Standard DICOM SEG / NRRD multi-layer taxonomy,
acceptance metrics, and human-in-the-loop expert sign-off gates.
"""
import os, json

v2_root    = '/Users/mac/Desktop/ho so benh an 2026/V2_VALIDATION'
expert_dir = os.path.join(v2_root, 'EXPERT_ANNOTATION_PENDING')
label_dir  = os.path.join(v2_root, 'LABELMAPS_PRELIMINARY')
os.makedirs(expert_dir, exist_ok=True)
os.makedirs(label_dir, exist_ok=True)

taxonomy_11_layers = {
    "standard_version": "BVBD_URO_ONCOLOGY_11_LAYER_SPEC_V2",
    "target_cohort": "RENAL_CELL_CARCINOMA_PREOPERATIVE_PLANNING",
    "dicom_iod_target": "DICOM_SEGMENTATION_STORAGE_SOP_CLASS (1.2.840.10008.5.1.4.1.1.66.4)",
    "layers": [
        {
            "layer_id": 1,
            "label_name": "right_kidney_whole",
            "anatomy_vi": "Toàn bộ thận phải (Đối bên lành mạnh)",
            "snomed_concept": "64033007 (Kidney structure)",
            "primary_phase": "VENOUS_NEPHROGRAPHIC",
            "hu_range_expected": "30 to 240 HU",
            "validation_metric": "Dice >= 0.92, HD95 <= 3.0 mm"
        },
        {
            "layer_id": 2,
            "label_name": "left_kidney_whole",
            "anatomy_vi": "Toàn bộ thận trái (Bao gồm nhu mô + bướu + xoang)",
            "snomed_concept": "64033007 (Kidney structure)",
            "primary_phase": "VENOUS_NEPHROGRAPHIC",
            "hu_range_expected": "30 to 240 HU",
            "validation_metric": "Dice >= 0.90, HD95 <= 3.5 mm"
        },
        {
            "layer_id": 3,
            "label_name": "left_kidney_cortex",
            "anatomy_vi": "Vỏ thận trái (Cortex lành mạnh ngoài bướu)",
            "snomed_concept": "53787006 (Renal cortex)",
            "primary_phase": "ARTERIAL_CORTICOMEDULLARY (30-40s)",
            "hu_range_expected": "120 to 220 HU",
            "validation_metric": "Dice >= 0.85, HD95 <= 2.5 mm"
        },
        {
            "layer_id": 4,
            "label_name": "left_kidney_medulla",
            "anatomy_vi": "Tủy thận trái (Medullary pyramids)",
            "snomed_concept": "25253006 (Renal medulla)",
            "primary_phase": "VENOUS_NEPHROGRAPHIC (70-90s)",
            "hu_range_expected": "80 to 160 HU",
            "validation_metric": "Dice >= 0.80, HD95 <= 3.0 mm"
        },
        {
            "layer_id": 5,
            "label_name": "left_renal_sinus_fat",
            "anatomy_vi": "Xoang thận & Mỡ xoang thận (Renal sinus fat)",
            "snomed_concept": "245558003 (Renal sinus)",
            "primary_phase": "NON_CONTRAST & VENOUS",
            "hu_range_expected": "-120 to +20 HU",
            "validation_metric": "Dice >= 0.82, HD95 <= 2.5 mm"
        },
        {
            "layer_id": 6,
            "label_name": "left_tumor_enhancing_viable",
            "anatomy_vi": "Bướu thận trái phần sống/tăng quang (Viable RCC)",
            "snomed_concept": "41607009 (Renal cell carcinoma)",
            "primary_phase": "ARTERIAL & VENOUS",
            "hu_range_expected": "80 to 250 HU (Heterogeneous early enhancement)",
            "validation_metric": "Dice >= 0.85, HD95 <= 3.0 mm, Volume Error <= 5%"
        },
        {
            "layer_id": 7,
            "label_name": "left_tumor_necrotic_cystic",
            "anatomy_vi": "Lõi hoại tử / dịch hóa / nang trong bướu",
            "snomed_concept": "6574001 (Necrosis)",
            "primary_phase": "ALL_PHASES (Non-enhancing core)",
            "hu_range_expected": "0 to 35 HU",
            "validation_metric": "Dice >= 0.80, HD95 <= 3.0 mm"
        },
        {
            "layer_id": 8,
            "label_name": "collecting_system_pelvicalyceal",
            "anatomy_vi": "Hệ thống đài bể thận & Niệu quản đoạn gần",
            "snomed_concept": "25990002 (Renal pelvis), 245557008 (Renal calyx)",
            "primary_phase": "DELAYED_EXCRETORY (>10 min)",
            "hu_range_expected": "> 180 HU (Opacified urine)",
            "validation_metric": "Dice >= 0.85, Continuous Topology to UPJ confirmed"
        },
        {
            "layer_id": 9,
            "label_name": "arterial_tree_aorta_lra",
            "anatomy_vi": "Động mạch chủ bụng & Động mạch thận trái + Nhánh phân thùy",
            "snomed_concept": "2841007 (Renal artery)",
            "primary_phase": "ARTERIAL (30s)",
            "hu_range_expected": "> 250 HU",
            "validation_metric": "Centerline continuity verified from Aorta ostium"
        },
        {
            "layer_id": 10,
            "label_name": "venous_tree_ivc_lrv",
            "anatomy_vi": "Tĩnh mạch chủ dưới & Tĩnh mạch thận trái",
            "snomed_concept": "56400007 (Renal vein)",
            "primary_phase": "VENOUS (70-90s)",
            "hu_range_expected": "110 to 220 HU",
            "validation_metric": "IVC junction & ostium continuity verified"
        },
        {
            "layer_id": 11,
            "label_name": "perinephric_fat_gerota",
            "anatomy_vi": "Mỡ quanh thận trong cân Gerota (Loại trừ mỡ xoang và mỡ cạnh thận)",
            "snomed_concept": "245559006 (Perirenal fat)",
            "primary_phase": "NON_CONTRAST & VENOUS",
            "hu_range_expected": "-195 to -45 HU",
            "validation_metric": "Fascia boundary manually/semi-automatically bounded"
        }
    ],
    "expert_signoff_protocol": {
        "radiology_expert": "Bác sĩ Chẩn đoán Hình ảnh Bụng - Niệu (Review slice-by-slice & contour sign-off)",
        "urology_expert": "Phẫu thuật viên Tiết niệu (Review 3D spatial relationship & operative feasibility)",
        "qa_gates": [
            "Gate 1: Multi-planar overlay (Axial, Coronal, Sagittal) across all active slices",
            "Gate 2: Inter-observer agreement (Dice >= 0.85 across key landmarks)",
            "Gate 3: Centerline continuity & branch count audit for vascular anatomy",
            "Gate 4: Morphological continuity from minor calyces to ureteropelvic junction",
            "Gate 5: Formal MDT consensus recorded in EHR before any surgical decision"
        ]
    }
}

# Save JSON Spec
json_spec = os.path.join(expert_dir, "ANATOMICAL_SEGMENTATION_SPEC_11LAYERS.json")
with open(json_spec, "w", encoding="utf-8") as f:
    json.dump(taxonomy_11_layers, f, indent=2, ensure_ascii=False)

# Save Markdown Document
md_spec = os.path.join(expert_dir, "QUY_CHUAN_PHAN_DOAN_11_LOP_GIAI_PHAU_V2.md")
with open(md_spec, "w", encoding="utf-8") as f:
    f.write(f"""# QUY CHUẨN PHÂN ĐOẠN 11 LỚP GIẢI PHẪU THẬN & KHUNG KIỂM ĐỊNH CHUYÊN GIA (V2)
**Hệ thống CDMS / MDT Bướu Thận BVBD 2026**
*Tiêu chuẩn:* DICOM Segmentation IOD / NRRD Labelmap Standard

---

## 1. DANH MỤC 11 LỚP GIẢI PHẪU BẮT BUỘC (MANDATORY 11-LAYER TAXONOMY)

| ID | Tên Lớp (Label) | Cấu trúc Giải phẫu | Pha CT Chuẩn | Ngưỡng HU Dự kiến | Tiêu chuẩn Nghiệm thu (QA Gate) |
|:---:|---|---|:---:|:---:|---|
| **1** | `right_kidney_whole` | Toàn bộ thận phải (Lành) | Venous | 30–240 HU | Dice ≥ 0.92, HD95 ≤ 3.0 mm |
| **2** | `left_kidney_whole` | Toàn bộ thận trái | Venous | 30–240 HU | Dice ≥ 0.90, HD95 ≤ 3.5 mm |
| **3** | `left_kidney_cortex` | Vỏ thận trái | Arterial | 120–220 HU | Dice ≥ 0.85, HD95 ≤ 2.5 mm |
| **4** | `left_kidney_medulla` | Tủy thận trái | Venous | 80–160 HU | Dice ≥ 0.80, HD95 ≤ 3.0 mm |
| **5** | `left_renal_sinus_fat` | Xoang thận & Mỡ xoang | NAT / Venous | -120 đến +20 HU | Dice ≥ 0.82, HD95 ≤ 2.5 mm |
| **6** | `left_tumor_enhancing_viable` | Bướu thận phần sống | Arterial / Venous | 80–250 HU | Dice ≥ 0.85, Sai số thể tích ≤ 5% |
| **7** | `left_tumor_necrotic_cystic` | Lõi hoại tử / Dịch hóa | All Phases | 0–35 HU | Dice ≥ 0.80, Không tăng quang |
| **8** | `collecting_system_pelvicalyceal` | Đài bể thận & Niệu quản | Delayed (>10m) | > 180 HU | Hình thái đài bể thận liên tục tới UPJ |
| **9** | `arterial_tree_aorta_lra` | ĐM Chủ & ĐM Thận Trái | Arterial | > 250 HU | Centerline liên tục từ lỗ ĐM chủ |
| **10** | `venous_tree_ivc_lrv` | TM Chủ Dưới & TM Thận Trái | Venous | 110–220 HU | Centerline liên tục đổ về TMC dưới |
| **11** | `perinephric_fat_gerota` | Mỡ quanh thận (Gerota) | NAT / Venous | -195 đến -45 HU | Giới hạn thủ công/bán tự động bởi cân thận |

---

## 2. QUY TRÌNH KIỂM DUYỆT 5 CỔNG (5-GATE EXPERT SIGNOFF PROTOCOL)
1. **Cổng 1 (Multi-planar Check):** Chiếu chồng (Overlay) nhãn phân đoạn trên cả 3 bình diện (Axial, Coronal, Sagittal) qua toàn bộ các lát cắt có cấu trúc.
2. **Cổng 2 (Dual-Expert Review):** Độc lập rà soát bởi ít nhất 1 Bác sĩ CĐHA Bụng - Niệu và 1 Phẫu thuật viên Tiết niệu.
3. **Cổng 3 (Vascular Topology Gate):** Kiểm tra cây mạch máu có nguồn gốc từ ĐMC, kiểm đếm chính xác số lượng ĐM thận, loại trừ hoàn toàn việc nhầm lẫn TM hay thuốc cản quang.
4. **Cổng 4 (Urothelial Continuity Gate):** Hệ thống đài bể thận phải có hình thái đài lớn - đài bé rõ ràng, liên tục tới khúc nối bể thận - niệu quản (UPJ), loại bỏ các điểm cản quang ngoài đường niệu.
5. **Cổng 5 (Clinical Sign-off Gate):** Chỉ các chỉ số trích xuất từ nhãn đã được ký duyệt chính thức mới được đưa vào biên bản hội chẩn MDT và hồ sơ bệnh án.

---
*Văn bản lưu tại: `V2_VALIDATION/EXPERT_ANNOTATION_PENDING/QUY_CHUAN_PHAN_DOAN_11_LOP_GIAI_PHAU_V2.md`*
""")

print("Module 4 (11-Layer Anatomical Protocol) completed successfully.")
