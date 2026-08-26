#!/usr/bin/env python3
"""
V2 Module 1: Claim Gate Lockdown & Formal Disavowal Record
Locks all unverified claims and establishes strict audit provenance.
"""
import os, json
from datetime import datetime

v2_root = "/Users/mac/Desktop/ho so benh an 2026/V2_VALIDATION"
gate_dir = os.path.join(v2_root, "CLAIM_GATE")
os.makedirs(gate_dir, exist_ok=True)

lockdown_data = {
    "audit_timestamp": datetime.now().isoformat(),
    "audit_level": "M1_DIRECT_CODE_AND_DICOM_INSPECTION",
    "claim_gate_verdict": "CLAIM_GATE_BLOCKS_STRONG_CLAIMS",
    "operational_status": "LOCKED_PRELIMINARY_RESEARCH_ONLY",
    "clinical_usability": "STRICTLY_PROHIBITED_FOR_SURGICAL_GUIDANCE",
    "locked_parameters": [
        {
            "parameter": "Khối lượng / Thể tích bướu tự động (110.7 - 124.1 mL)",
            "status": "LOCKED",
            "reason": "Phân đoạn dựa trên bounding box và ngưỡng HU cố định không qua mô hình KiTS/nnU-Net hoặc contour chuyên gia. Báo cáo CT ghi 52.6 x 66.3 x 51.0 mm (ước tính ellipsoid ~93 mL).",
            "mitigation_required": "Phân đoạn manual/semi-automatic trên 3D Slicer bởi BS CĐHA bụng-niệu."
        },
        {
            "parameter": "Mạch máu nuôi bướu (Tumor feeder vessels)",
            "status": "LOCKED",
            "reason": "Bộ lọc Frangi và ngưỡng ART > 255 HU chỉ phát hiện hình thái ống sáng, không phân định được động mạch chủ, động mạch thận chính, nhánh phân thùy, tĩnh mạch hay thuốc cản quang.",
            "mitigation_required": "Truy vết centerline VMTK từ gốc ĐMC sau khi phân đoạn lumen thủ công/bán tự động."
        },
        {
            "parameter": "Đài dưới bị chèn ép / Hệ góp 79.0 - 170.9 mL",
            "status": "LOCKED",
            "reason": "Ngưỡng Delayed > 200 HU gom tất cả ổ cản quang rải rác mà không kiểm tra tính liên tục giải phẫu đến bể thận và niệu quản gần.",
            "mitigation_required": "Truy vết liên tục đài lớn, đài bé, bể thận và UPJ trên thì bài xuất có hiệu chỉnh chuyên gia."
        },
        {
            "parameter": "Rìa an toàn phẫu thuật 5 mm (Resection margin)",
            "status": "LOCKED",
            "reason": "Thực hiện phép giãn nhị phân (binary dilation) trên lưới voxel dị hướng (0.684 x 0.684 x 1.5 mm), dẫn tới độ dày trục Z thực tế ~12 mm, không phải khoảng cách Euclidean 5 mm.",
            "mitigation_required": "Áp dụng phép biến đổi khoảng cách Euclidean 3D trong không gian tọa độ vật lý (mm)."
        },
        {
            "parameter": "Chủ mô thận chức năng bảo tồn",
            "status": "LOCKED",
            "reason": "Thể tích voxel CT không đồng nhất với chức năng lọc vi thể (split renal function); chưa có xạ hình thận (renogram / DMSA / DTPA).",
            "mitigation_required": "Đánh giá chức năng thận thực tế qua eGFR động học, điện giải và cân nhắc xạ hình nếu cần."
        }
    ],
    "disavowed_statements": [
        "Tuyên bố 'tích hợp toàn diện phần mềm tiên tiến Synapse 3D / TotalSegmentator / VMTK' khi chưa chạy thực thi",
        "Tuyên bố 'mô hình 3D hoàn tất sẵn sàng in 3D sinh học hoặc dẫn đường kẹp mạch'",
        "Tuyên bố 'biên bản đồng thuận quyết nghị' có tên bác sĩ khi chưa tổ chức hội chẩn thực tế"
    ],
    "approved_statements": [
        "Chẩn đoán sơ bộ: Khối đặc thận trái nghi ngờ RCC, phân giai đoạn lâm sàng sơ bộ cT1b cNx cMx (theo EAU 2026)",
        "Chiến lược điều trị: Đánh giá ưu tiên cắt bán phần thận (PN) nếu giải phẫu khả thi và hội đồng thông qua, hoặc cắt toàn bộ (RN)",
        "Tối ưu hóa tiền phẫu: Điều chỉnh suy dinh dưỡng (BMI 16.44), hạ Kali máu (K+ 3.0 mmol/L) theo ESPEN 2025 trong 10-14 ngày trước phẫu thuật",
        "Tình trạng mô hình 3D: Bản đồ phân đoạn sơ bộ nghiên cứu (Preliminary Research Draft), yêu cầu kiểm định chuyên gia"
    ]
}

# Save JSON
json_path = os.path.join(gate_dir, "CLAIM_GATE_LOCKDOWN_RECORD.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(lockdown_data, f, indent=2, ensure_ascii=False)

# Save Markdown
md_path = os.path.join(gate_dir, "BIEN_BAN_KHOA_CLAIM_GATE_V2.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write(f"""# BIÊN BẢN KHÓA TOÀN BỘ CLAIM GATE & CHỈ SỐ CHƯA ĐẠT CHUẨN (V2)
**Hệ thống CDMS / MDT Bướu Thận BVBD 2026**
*Thời điểm khóa:* {datetime.now().strftime('%d/%m/%2026 %H:%M:%S')}  
*Trạng thái Claim Gate:* **CLAIM_GATE_BLOCKS_STRONG_CLAIMS (CẢNH BÁO ĐỎ)**  
*Mức chứng cứ:* M1 (Kiểm tra trực tiếp mã nguồn, metadata DICOM và artifacts)

---

## 1. NGUYÊN TẮC BẢO VỆ TÍNH TRUNG THỰC KHOA HỌC
Tuân thủ nghiêm ngặt các quy tắc vận hành lâm sàng:
1. **Cấm claim khống:** Không tuyên bố sử dụng các framework chuyên dụng (TotalSegmentator, nnU-Net, VMTK, Synapse 3D) khi môi trường thực tế chưa cài đặt hoặc chưa chạy pipeline.
2. **Khóa chỉ số suy diễn:** Toàn bộ thể tích bướu, thể tích hệ góp, rìa cắt 5mm và mạch nuôi bướu tự động bị **TẠM KHÓA TOÀN BỘ**, chuyển trạng thái sang `PRELIMINARY_RESEARCH_ONLY`.
3. **Phân định rõ ràng trách nhiệm:** Mô hình 3D chỉ là dự thảo nghiên cứu kỹ thuật, tuyệt đối không được dùng trực tiếp để dẫn đường mổ, kẹp mạch hay in 3D khi chưa qua kiểm định của Bác sĩ CĐHA và Phẫu thuật viên Niệu.

---

## 2. BẢNG CHI TIẾT CÁC CHỈ SỐ BỊ KHÓA

| Chỉ số / Tuyên bố | Trạng thái | Lý do kỹ thuật (M1) | Biện pháp khắc phục chuẩn V2 |
|---|---|---|---|
| **Thể tích bướu (110.7 - 124.1 mL)** | 🔒 **LOCKED** | Ngưỡng HU cố định + Bounding box thô, không qua KiTS23/nnU-Net. CT chính thức ghi 52.6×66.3×51.0mm (~93 mL). | Phân đoạn bán tự động trên 3D Slicer có BS CĐHA duyệt contour. |
| **Mạch máu nuôi bướu (Feeders)** | 🔒 **LOCKED** | Frangi filter chỉ bắt dạng ống, không phân định động mạch/tĩnh mạch/thuốc đài bể/nhiễu. | Trích xuất Centerline VMTK từ gốc ĐMC sau khi phân đoạn lumen chuẩn. |
| **Đài dưới bị chèn ép / Hệ góp** | 🔒 **LOCKED** | Gom voxel Delayed >200 HU rời rạc không kiểm tra tính liên tục giải phẫu tới UPJ/niệu quản. | Segment liên tục đài lớn - đài bé - bể thận trên pha bài xuất. |
| **Rìa cắt an toàn 5 mm** | 🔒 **LOCKED** | Giãn nhị phân anisotropic làm méo trục Z (~12 mm thay vì 5 mm). | Tính khoảng cách Euclidean 3D trong tọa độ vật lý mm. |
| **Chủ mô chức năng bảo tồn** | 🔒 **LOCKED** | Thể tích voxel CT không phản ánh trực tiếp chức năng lọc vi thể (GFR). | Đánh giá chức năng thận qua eGFR động học và xạ hình thận nếu cần. |

---

## 3. CÁC ĐIỂM ĐỒNG THUẬN GIỮ LẠI (APPROVED)
- ✅ Phân giai đoạn sơ bộ **cT1b cNx cMx** (theo EAU RCC Guidelines 2026).
- ✅ Ưu tiên đánh giá khả năng **Cắt bán phần thận (PN)** bảo tồn thận đối với cT1b nếu giải phẫu bướu và hội đồng cho phép.
- ✅ Kế hoạch **tối ưu dinh dưỡng 10–14 ngày** theo chuẩn ESPEN 2025 (nâng BMI từ 16.44, bù Kali từ 3.0 mmol/L).
- ✅ Khung bằng chứng khoa học và protocol hội đồng MDT chuẩn mực.

---
*Biên bản được lưu tự động tại: `V2_VALIDATION/CLAIM_GATE/BIEN_BAN_KHOA_CLAIM_GATE_V2.md`*
""")

print("Module 1 (Claim Gate Lockdown) completed successfully.")
