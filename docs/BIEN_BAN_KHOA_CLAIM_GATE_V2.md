# BIÊN BẢN KHÓA TOÀN BỘ CLAIM GATE & CHỈ SỐ CHƯA ĐẠT CHUẨN (V2)
**Hệ thống CDMS / MDT Bướu Thận BVBD 2026**
*Thời điểm khóa:* 26/08/2026 14:52:19  
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
