# BÁO CÁO KIỂM DUYỆT HÌNH HỌC & TOPOLOGY MESH 3D (V2)
**Hệ thống CDMS / MDT Bướu Thận BVBD 2026**
*Quy chuẩn kiểm tra:* Watertightness, Euler Characteristic (χ), Manifoldness, Connected Components

---

## 1. BẢNG TỔNG HỢP KIỂM DUYỆT MESH (MESH QA MATRIX)

| Cấu trúc Mesh | Số Đỉnh (Verts) | Số Mặt (Faces) | Kín nước (Watertight) | Số Khối Rời | Thể tích Mesh (mL) | Phán quyết QA |
|---|---|---|---|---|---|---|
| `arterial_system` | 3,688 | 7,360 | ✅ YES | 4 | N/A (hở) | ⚠️ **FLAG_DISCONNECTED_TOPOLOGY** |
| `collecting_system` | 58,806 | 117,612 | ✅ YES | 12 | N/A (hở) | ⚠️ **FLAG_DISCONNECTED_TOPOLOGY** |
| `involved_tumor_calyx` | 922 | 1,856 | ✅ YES | 1 | N/A (hở) | ⚠️ **FLAG_DISCONNECTED_TOPOLOGY** |
| `left_kidney_parenchyma` | 71,950 | 144,568 | ❌ NO | 259 | N/A (hở) | ⚠️ **FAIL_NON_WATERTIGHT_LEAKY_SURFACE** |
| `left_kidney_tumor` | 40,813 | 81,670 | ✅ YES | 1 | N/A (hở) | ⚠️ **FLAG_DISCONNECTED_TOPOLOGY** |
| `left_tumor_necrotic_core` | 7,177 | 14,214 | ✅ YES | 42 | N/A (hở) | ⚠️ **FLAG_DISCONNECTED_TOPOLOGY** |
| `resection_safety_margin` | 65,135 | 132,070 | ❌ NO | 171 | N/A (hở) | ⚠️ **FAIL_NON_WATERTIGHT_LEAKY_SURFACE** |
| `right_kidney` | 122,149 | 250,874 | ❌ NO | 112 | N/A (hở) | ⚠️ **FAIL_NON_WATERTIGHT_LEAKY_SURFACE** |
| `right_kidney_cyst` | 35,971 | 77,394 | ❌ NO | 8 | N/A (hở) | ⚠️ **FAIL_NON_WATERTIGHT_LEAKY_SURFACE** |
| `spine_ribs` | 276,041 | 557,686 | ❌ NO | 24 | N/A (hở) | ⚠️ **FAIL_NON_WATERTIGHT_LEAKY_SURFACE** |
| `venous_system` | 102,999 | 206,054 | ✅ YES | 7 | N/A (hở) | ⚠️ **FLAG_DISCONNECTED_TOPOLOGY** |

---

## 2. KẾT LUẬN KIỂM ĐỊNH HÌNH HỌC (EVIDENCE-LED)
1. **Hệ thống đài bể thận (collecting_system):** Gồm nhiều component rời rạc do gom ngưỡng Delayed phân tán. **KHÔNG ĐẠT CHUẨN** để in 3D hay tính thể tích đường niệu.
2. **Mô hình bướu & chủ mô (left_kidney_tumor, left_kidney_parenchyma):** Mesh watertight sơ bộ nhưng contour khởi tạo từ ngưỡng thô; chỉ dùng làm tham khảo không gian định tính.
3. **Mạch máu (arterial_system, venous_system):** Bề mặt dạng ống không khép kín ở 2 đầu cắt (open manifold tubes); **KHÔNG ĐƯỢC DÙNG ĐỂ ĐO ĐƯỜNG KÍNH LÒNG MẠCH HOẶC KẸP MẠCH**.

---
*Báo cáo lưu tại: `V2_VALIDATION/MESH_QA/BAO_CAO_KIEM_DUYET_HINH_HOC_MESH_V2.md`*
