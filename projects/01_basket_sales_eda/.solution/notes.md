# Project 01 — Solution notes (đừng mở trước khi nộp bài)

Lời giải mẫu: `python .solution/baseline.py` (chạy từ thư mục project).

## Planted signals (organic co-purchase)

| Rule | Cơ chế trong generator | Kết quả trên dữ liệu sạch |
|---|---|---|
| R1 Mì gói (P001) ↔ Trứng gà (P006) | thêm trứng với p = 0.35 khi có mì | support ~8%, lift ~2.1, volume cao nhất |
| R2 Bột giặt (P027) ↔ Nước xả vải (P028) | p = 0.40 | lift ~7 |
| R3 Tã (P031) ↔ Khăn ướt (P032) | p = 0.45; chỉ segment `gia_dinh_tre` mua tã | lift ~17 |
| R4 Cà phê hoà tan (P043) ↔ Sữa đặc (P008) | p = 0.30 | lift ~4, nhưng B rẻ nên ít tiền |
| R5 Bia thùng (P015) ↔ Snack (P017) | p = 0.50 vào **thứ 6–CN từ 18h**, ngược lại 0.03 | cả quý: lift ~2.0, conf ~0.18; cuối tuần tối: lift ~4.5, conf ~0.52 |
| R6 Bánh trung thu (P021) ↔ Trà ô long (P045) | bánh chỉ bán 1–25/9; p = 0.55 | support cả quý ~0.37%, dưới ngưỡng 0.5%; trong 1–25/9 support ~1.4%, lift ~15 |

R5 và R6 là hai tín hiệu **chỉ thấy sau khi tạo feature thời gian** (Section 7).
- R6 **không** được chọn cho Q4 vì mùa đã hết; đáp án tốt là đề xuất lưu combo này cho Trung thu 2027.
- R5 tốt nhất nên đề xuất hiển thị combo theo khung giờ.

**Hướng của rule:** 5 combo giá trị nhất đều có chiều *rẻ → đắt*: khăn ướt → tã, trứng → mì, nước xả → bột giặt, snack → bia, sữa đặc → cà phê. Lý do là B đắt hơn thì `price_B × margin_B` lớn hơn. Lab tính cả hai chiều. Học viên dùng self-merge rồi lọc `a < b` (chỉ còn một chiều) sẽ chỉ được khoảng 23 tr/tháng, dưới ngưỡng usable.

## Đáp án tham khảo (baseline)

| A → B | support | conf | lift | value_month |
|---|---|---|---|---|
| Khăn ướt → Tã quần L | 0.014 | 0.49 | 17.1 | ~13.2 tr |
| Trứng gà → Mì gói | 0.082 | 0.40 | 2.1 | ~12.4 tr |
| Nước xả vải → Bột giặt | 0.034 | 0.54 | 6.9 | ~11.8 tr |
| Snack khoai tây → Bia thùng | 0.014 | 0.16 | 2.0 | ~8.2 tr |
| Sữa đặc → Cà phê hoà tan | 0.033 | 0.44 | 4.2 | ~4.6 tr |
| **Tổng** | | | | **~50 triệu VND/tháng** (~150 tr/quý) |

So sánh các cách chọn (đã chấm theo ràng buộc; combo vi phạm tính 0):
- **Top-5 theo lift trên dữ liệu thô:** ~25 tr. Danh sách gồm cả hai chiều tã/khăn ướt và combo cố định bia lốc 6/đậu phộng.
- **Top-5 theo `n_ab`:** ~36 tr.
- **Khoảng chấp nhận được** cho bài làm đúng: 45–56 tr. Chênh lệch nhỏ đến từ việc dùng `list_price` hay đơn giá thực, và việc giữ hay bỏ đơn `returned`.

## Traps

| # | Trap | Số lượng | Xử lý đúng |
|---|---|---|---|
| 1 | Dòng trùng | 75 dòng `orders`, 840 dòng `order_items` | `drop_duplicates()` |
| 2 | Giá trị thiếu | `segment` 150, `city` 83, `channel` 469 | Gán `unknown`, không xoá đơn (giỏ hàng vẫn hợp lệ) |
| 3 | Orphan FK | 150 đơn có `customer_id` không tồn tại; 170 dòng `product_id = P999` | Giữ đơn (segment `unknown`); bỏ dòng P999 |
| 4 | Số lượng không hợp lệ | 169 dòng có `quantity` ≤ 0 | Bỏ dòng |
| 5 | Trạng thái đơn | ~1.050 `cancelled`, ~260 `returned` | Giỏ hàng chỉ lấy `completed` |
| 6 | **Quà tặng hệ thống** P060 | ~4.200 dòng, giá 0, tự thêm khi tạm tính ≥ 400k (có ở ~30% đơn) | Bỏ khỏi giỏ hàng. Nếu giữ lại, rule `Túi giữ nhiệt → Sữa bột` đứng đầu với ~52 tr/tháng, một con số hoàn toàn vô nghĩa |
| 7 | **Combo cố định** `BDL-BIA6-DP` | ~1.160 dòng | Bỏ các dòng có `bundle_id`, hoặc loại cặp P016–P018: lift ~9.7 nhưng giá trị tăng thêm bằng 0 vì đã là combo |
| 8 | **Tài khoản QA** `C000000` | 25 đơn, mỗi đơn 28–40 sản phẩm | Bỏ. Phát hiện được qua histogram `n_products` và số đơn mỗi khách. Nếu giữ, mỗi cặp được cộng thêm ~0.1% support, đủ đẩy vài cặp ngẫu nhiên vượt ngưỡng |

Trap 6 và 7 đóng vai trò cột "leakage" của project này: **association do chính hệ thống hoặc khuyến mãi tạo ra, không phải nhu cầu thật của khách**.

## 3 lỗi phổ biến nhất

1. **Chia cho số dòng hàng thay vì số giỏ hàng** khi tính support, hoặc không `drop_duplicates()` cặp `(order_id, product_id)` trước khi đếm. Cả hai làm support và confidence sai.
2. **Xếp hạng theo lift rồi dừng.** Cách này chọn cặp hiếm, combo cố định, hàng mùa vụ, quên mất `value_month` và hướng của rule.
3. **Không phát hiện quà tặng P060**, nên rule `Túi giữ nhiệt → …` lọt vào top. Một biến thể của lỗi này: không bỏ đơn `cancelled`/`returned`, khiến tổng doanh thu bị thổi phồng khoảng 9%.

## Gợi ý chấm

- **Section 3–4 (22 điểm):** tìm được ≥ 6/8 trap là đủ điểm. Tìm được trap 6–8 là dấu hiệu tốt nhất.
- **Section 6.5:** phải gọi tên được ít nhất 2 trong 3 nguồn: quà tặng, combo cố định, hàng mùa vụ.
- **Section 7:** phải thấy R5 mạnh lên vào cuối tuần buổi tối, và R6 chỉ xuất hiện trong tháng 9.
- **Section 8:** tổng ≥ 45 tr là strong; 35–45 tr là usable (thường do xếp hạng theo `n_ab` hoặc confidence thay vì `value_month`, hoặc chọn sai chiều 1–2 combo); dưới 35 tr thường do chỉ tính một chiều, hoặc vi phạm ràng buộc.
