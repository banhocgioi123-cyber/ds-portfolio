# ShopNhanh Mart — Data Dictionary

Kỳ dữ liệu: **2026-07-01 → 2026-09-30**, mẫu ngẫu nhiên 5% khách hàng.

> **Project này không có cột target.** Đối tượng phân tích là **giỏ hàng**: tập các `product_id` khác nhau trong một đơn có `status = completed`. Giỏ hàng được tạo từ `order_items` ⨝ `orders`.

---

## customers.csv
1 dòng = 1 khách hàng.

| Column | Type | Description |
|---|---|---|
| `customer_id` | string | Mã khách hàng (vd. `C000123`) |
| `signup_date` | date | Ngày tạo tài khoản |
| `city` | string | Thành phố giao hàng mặc định: `Hồ Chí Minh`, `Hà Nội`, `Đà Nẵng` (có giá trị thiếu) |
| `segment` | string | Phân khúc do team CRM gán: `gia_dinh_tre` (gia đình có con nhỏ), `gia_dinh`, `van_phong`, `sinh_vien` (có giá trị thiếu) |

---

## orders.csv
1 dòng = 1 đơn hàng.

| Column | Type | Description |
|---|---|---|
| `order_id` | string | Mã đơn (vd. `O0001234`) |
| `customer_id` | string | Khách đặt đơn, khoá ngoại tới `customers.customer_id` |
| `order_datetime` | datetime | Thời điểm đặt đơn, định dạng `YYYY-MM-DD HH:MM` |
| `channel` | string | Kênh đặt: `app` hoặc `web` (có giá trị thiếu) |
| `payment_method` | string | `cod` (trả tiền mặt khi nhận), `ewallet`, `card` |
| `status` | string | `completed` (giao thành công), `cancelled` (huỷ trước khi giao), `returned` (khách trả hàng) |
| `shipping_fee` | int | Phí ship khách trả (VND); miễn phí khi đơn từ 300.000 VND |

---

## order_items.csv
1 dòng = 1 sản phẩm trong 1 đơn. Một đơn có nhiều dòng.

| Column | Type | Description |
|---|---|---|
| `order_id` | string | Khoá ngoại tới `orders.order_id` |
| `product_id` | string | Khoá ngoại tới `products.product_id` |
| `quantity` | int | Số lượng |
| `unit_price` | int | Đơn giá thực bán (VND), có thể thấp hơn `list_price` khi có khuyến mãi |
| `bundle_id` | string | Mã combo cố định nếu dòng hàng được bán trong một combo có giá riêng; để trống nếu bán lẻ |

---

## products.csv
1 dòng = 1 sản phẩm.

| Column | Type | Description |
|---|---|---|
| `product_id` | string | Mã sản phẩm (vd. `P001`) |
| `product_name` | string | Tên sản phẩm |
| `category` | string | Ngành hàng |
| `list_price` | int | Giá niêm yết (VND) |
| `gross_margin` | float | Biên lợi nhuận gộp của ngành hàng (vd. `0.25` = 25% giá bán) |
