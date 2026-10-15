# ShopNhanh — Chọn 5 combo "Thường được mua cùng" cho ShopNhanh Mart
## Mini Coursework Business Brief · Project 01

---

### Company Background

**ShopNhanh** là sàn thương mại điện tử Việt Nam. Mảng **ShopNhanh Mart** (đi chợ online: đồ khô, sữa, rau thịt, hoá phẩm, mẹ & bé) hoạt động ở Hồ Chí Minh, Hà Nội và Đà Nẵng, xử lý khoảng **90.000 đơn/tháng** với giá trị đơn trung bình (AOV) khoảng **310.000 VND**, tương đương doanh thu khoảng **28 tỷ VND/tháng**.

Vấn đề là giỏ hàng không lớn lên: mỗi đơn chỉ có khoảng 3 sản phẩm, gần như không đổi trong nhiều quý. Phí ship và chi phí vận hành tính theo đơn, nên **mỗi sản phẩm mua kèm thêm vào đơn có sẵn gần như là lợi nhuận gộp thuần**.

---

### The Business Problem

Trên trang sản phẩm và trong giỏ hàng có widget **"Thường được mua cùng"**. Hiện widget hiển thị *top bán chạy* giống hệt nhau cho mọi khách, nên tỷ lệ khách bấm thêm chỉ khoảng 1%.

Cho **Q4/2026 (tháng 10–12)**, team Category được cấu hình **đúng 5 combo thủ công** dạng **A → B**: khi trong giỏ có sản phẩm A, widget gợi ý sản phẩm B (không giảm giá). Mỗi slot chọn sai là cơ hội bị mất trọn một quý.

Pilot năm ngoái cho thấy tỷ lệ khách **thêm B** khi được gợi ý tỉ lệ thuận với mức độ "hợp" tự nhiên của cặp sản phẩm:

```
take_rate(A → B) = 0.20 × confidence(A → B)
```

Lợi nhuận gộp tăng thêm mỗi tháng của một combo, tính trên toàn bộ khách:

```
value_month (VND) = 20 × (số đơn có A nhưng không có B) / 3
                  × take_rate(A → B) × giá bán trung bình của B × gross_margin của B
```

- `× 20`: dữ liệu là **mẫu ngẫu nhiên 5% khách hàng**.
- `/ 3`: dữ liệu gồm **3 tháng** (Q3/2026).

---

### Your Task

Team Category cần một notebook trả lời được 3 câu hỏi sau:

1. **Dữ liệu có sạch không?** Kiểm tra chất lượng, làm sạch và join 4 bảng thành một bảng dòng hàng (`lines`) và một bảng giỏ hàng (`baskets`, 1 dòng = 1 đơn).
2. **Khách đang mua gì, khi nào, ai mua?** Sales EDA: doanh thu theo tuần, theo category, AOV và số sản phẩm/đơn, theo segment/thành phố, theo ngày trong tuần × giờ.
3. **Nên chọn 5 combo nào?** Tính support / confidence / lift cho mọi cặp A → B, tìm cả những combo chỉ mạnh trong một khung thời gian, rồi chọn **5 combo cho Q4** kèm `value_month` của từng combo.

**Đơn vị phân tích:** một **giỏ hàng** là tập sản phẩm *khác nhau* trong **một đơn đã giao thành công**. Kỳ dữ liệu từ **2026-07-01 đến 2026-09-30**.

---

### Data Available

| File | Mô tả | 1 dòng = |
|---|---|---|
| `customers.csv` | Thông tin khách: thành phố, segment | 1 khách |
| `orders.csv` | Đơn hàng: thời gian, kênh, thanh toán, trạng thái | 1 đơn |
| `order_items.csv` | Dòng hàng trong đơn: sản phẩm, số lượng, đơn giá | 1 sản phẩm trong 1 đơn |
| `products.csv` | Danh mục sản phẩm: tên, category, giá niêm yết, biên lợi nhuận gộp | 1 sản phẩm |

Chi tiết từng cột xem trong `data_dictionary.md`.

---

### Success Criteria

- **Primary metric:** tổng `value_month` của 5 combo bạn chọn, tính trên dữ liệu đã làm sạch.
  - **Usable:** ≥ **35 triệu VND/tháng**.
  - **Strong:** ≥ **45 triệu VND/tháng**.
- **Ràng buộc cho mỗi combo** (để combo có nghĩa với khách, không phải trùng hợp):
  - `support(A, B) ≥ 0.5%` số giỏ hàng, và `lift(A → B) ≥ 1.2`;
  - mỗi sản phẩm A chỉ có 1 combo, và mỗi cặp sản phẩm chỉ dùng 1 lần (không chọn cả A → B lẫn B → A);
  - A và B phải là sản phẩm **khách tự chọn mua** và **còn bán trong Q4**.
- **Data quality:** liệt kê các vấn đề dữ liệu tìm được và cách bạn xử lý từng vấn đề. Có **ít nhất 6** vấn đề.
- **Deliverable:** file `combo_recommendations.csv` gồm 5 dòng với các cột `product_a`, `product_b`, `support`, `confidence`, `lift`, `value_month`.

---

### Guidance

- **Join và aggregate:** `order_items` có nhiều dòng cho mỗi đơn. Muốn biết AOV hay số sản phẩm/đơn, bạn phải `groupby('order_id')` trước rồi mới join với `orders`.
- **Lift cao chưa chắc là combo tốt.** Hãy tự hỏi: khách có *tự chọn* cả hai sản phẩm không? Cặp này có đang được bán chung sẵn rồi không? Sản phẩm còn bán ở Q4 không?
- **Hướng của rule quan trọng.** `A → B` và `B → A` có confidence khác nhau và `value_month` khác nhau. Hãy tính cả hai chiều.
- **Không phải dòng hàng nào cũng do khách chọn**, và không phải tài khoản nào cũng là khách thật. Phân phối số sản phẩm/đơn và đơn giá sẽ cho bạn manh mối.
- **Một vài combo chỉ mạnh trong một lát cắt** (ngày trong tuần, giờ, tháng). Hãy tạo feature thời gian từ `order_datetime` rồi chạy lại phân tích trên từng lát cắt.
- **Phương pháp:** lab `1_market_basket_analysis.ipynb` (DSAI-1 Lesson 1) đếm support, confidence và lift bằng `dict` và `itertools.combinations`. Với khoảng 14.000 đơn cách đó vẫn chạy được; dùng pandas (`merge` bảng giỏ hàng với chính nó theo `order_id`) sẽ nhanh hơn.
