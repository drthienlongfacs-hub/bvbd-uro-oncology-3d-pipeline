# QUY CHUẨN PHÂN ĐOẠN 11 LỚP GIẢI PHẪU THẬN & KHUNG KIỂM ĐỊNH CHUYÊN GIA (V2)
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
