"""Generate synthetic ShopNhanh Mart data (Q3/2026, 5% customer sample) for project 01.

Run from anywhere: python utils/generate_data.py  -> writes data/*.csv

Planted signals (organic co-purchase A -> B; p = prob. B is added when A is in the basket):
  R1 P001 Mì gói (thùng 30)       -> P006 Trứng gà (hộp 10)     p=0.35  high volume
  R2 P027 Bột giặt (túi 3kg)       -> P028 Nước xả vải (1.6L)    p=0.40  expensive B -> most money
  R3 P031 Tã quần size L           -> P032 Khăn ướt (gói 100)    p=0.45  only segment gia_dinh_tre buys tã
  R4 P043 Cà phê hoà tan (hộp 18)  -> P008 Sữa đặc (lon)         p=0.30
  R5 P015 Bia lon (thùng 24)       -> P017 Snack khoai tây       p=0.50 Fri-Sun >= 18h, else 0.03
     HIDDEN: overall lift is modest; needs weekday/hour features to see it.
  R6 P021 Bánh trung thu (hộp 4)   -> P045 Trà ô long (hộp)      p=0.55; mooncake sold only 1-25/9
     HIDDEN: pair support over the quarter < 0.5%; only shows up in a September slice.
     Also irrelevant for Q4 slots (season over) -> save for Trung thu 2027.
Traps:
  gift    P060 Túi giữ nhiệt (quà tặng): unit_price 0, auto-added when subtotal >= 400k
          -> spurious high lift with expensive items (tã, sữa bột, bia thùng, bột giặt)
  bundle  bundle_id 'BDL-BIA6-DP': P016 Bia lốc 6 + P018 Đậu phộng sold as a fixed combo
          -> top lift in a naive ranking, but zero incremental value (already a combo)
  test    customer C000000 (QA account): 25 completed orders x 28-40 items
  dups    ~1.5% order_items rows and ~0.5% orders rows duplicated
  nulls   customers.segment 4%, customers.city 2%, orders.channel 3%
  orphan  order_items.product_id 'P999' (~0.3% lines); orders.customer_id not in customers (~1%)
  invalid quantity <= 0 (~0.3% lines)
  status  cancelled ~7%, returned ~2% (baskets should use completed orders)
"""
from pathlib import Path

import numpy as np
import pandas as pd

np.random.seed(42)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data'
OUT.mkdir(exist_ok=True)

N_CUSTOMERS = 4000
START, END = pd.Timestamp('2026-07-01'), pd.Timestamp('2026-09-30 23:59')
GIFT_THRESHOLD = 400_000

# ---------------------------------------------------------------- products
# (id, name, category, list_price, base popularity weight)
PRODUCTS = [
    ('P001', 'Mì gói tôm chua cay (thùng 30)', 'Mì & đồ khô', 115000, 6.0),
    ('P002', 'Gạo ST25 (túi 5kg)', 'Mì & đồ khô', 185000, 4.0),
    ('P003', 'Bún khô (gói 500g)', 'Mì & đồ khô', 22000, 2.0),
    ('P004', 'Phở khô (gói 500g)', 'Mì & đồ khô', 25000, 1.5),
    ('P006', 'Trứng gà (hộp 10)', 'Trứng & sữa', 35000, 5.0),
    ('P007', 'Sữa tươi không đường (lốc 4)', 'Trứng & sữa', 34000, 4.5),
    ('P008', 'Sữa đặc (lon 380g)', 'Trứng & sữa', 26000, 1.5),
    ('P009', 'Sữa chua (lốc 4)', 'Trứng & sữa', 28000, 3.5),
    ('P010', 'Phô mai (hộp 8 miếng)', 'Trứng & sữa', 42000, 1.2),
    ('P011', 'Nước suối (thùng 24)', 'Đồ uống', 95000, 3.0),
    ('P012', 'Nước ngọt có ga (lốc 6)', 'Đồ uống', 52000, 3.0),
    ('P013', 'Trà xanh đóng chai (lốc 6)', 'Đồ uống', 48000, 2.5),
    ('P014', 'Nước tăng lực (lốc 6)', 'Đồ uống', 60000, 1.5),
    ('P015', 'Bia lon (thùng 24)', 'Bia', 330000, 3.0),
    ('P016', 'Bia lon (lốc 6)', 'Bia', 88000, 1.0),
    ('P017', 'Snack khoai tây (gói lớn)', 'Snack & bánh kẹo', 32000, 2.5),
    ('P018', 'Đậu phộng rang (gói 200g)', 'Snack & bánh kẹo', 28000, 0.8),
    ('P019', 'Bánh quy bơ (hộp)', 'Snack & bánh kẹo', 65000, 1.5),
    ('P020', 'Kẹo dẻo (gói)', 'Snack & bánh kẹo', 20000, 1.5),
    ('P021', 'Bánh trung thu (hộp 4)', 'Snack & bánh kẹo', 320000, 0.0),  # seasonal, added below
    ('P022', 'Nước mắm (chai 500ml)', 'Gia vị', 45000, 3.0),
    ('P023', 'Dầu ăn (chai 1L)', 'Gia vị', 52000, 3.0),
    ('P024', 'Hạt nêm (gói 400g)', 'Gia vị', 38000, 2.5),
    ('P025', 'Nước tương (chai 500ml)', 'Gia vị', 22000, 2.0),
    ('P026', 'Đường trắng (gói 1kg)', 'Gia vị', 25000, 2.0),
    ('P027', 'Bột giặt (túi 3kg)', 'Giặt giũ & tẩy rửa', 165000, 2.5),
    ('P028', 'Nước xả vải (túi 1.6L)', 'Giặt giũ & tẩy rửa', 120000, 1.0),
    ('P029', 'Nước rửa chén (chai 750ml)', 'Giặt giũ & tẩy rửa', 32000, 3.0),
    ('P030', 'Nước lau sàn (chai 1L)', 'Giặt giũ & tẩy rửa', 45000, 1.5),
    ('P031', 'Tã quần size L (gói 54)', 'Mẹ & bé', 330000, 3.0),
    ('P032', 'Khăn ướt (gói 100 tờ)', 'Mẹ & bé', 45000, 1.5),
    ('P033', 'Sữa bột trẻ em (lon 900g)', 'Mẹ & bé', 520000, 2.0),
    ('P034', 'Sữa tắm em bé (chai 500ml)', 'Mẹ & bé', 120000, 1.0),
    ('P035', 'Rau cải (bó 500g)', 'Rau củ & trái cây', 18000, 4.0),
    ('P036', 'Cà chua (kg)', 'Rau củ & trái cây', 30000, 3.0),
    ('P037', 'Hành tây (kg)', 'Rau củ & trái cây', 28000, 2.0),
    ('P038', 'Chuối (nải)', 'Rau củ & trái cây', 30000, 2.5),
    ('P039', 'Táo (kg)', 'Rau củ & trái cây', 75000, 2.0),
    ('P040', 'Thịt heo ba rọi (500g)', 'Thịt cá', 85000, 3.5),
    ('P041', 'Ức gà (500g)', 'Thịt cá', 55000, 2.5),
    ('P042', 'Cá basa phi lê (500g)', 'Thịt cá', 60000, 2.0),
    ('P043', 'Cà phê hoà tan (hộp 18 gói)', 'Cà phê & trà', 55000, 3.0),
    ('P044', 'Cà phê rang xay (gói 500g)', 'Cà phê & trà', 140000, 1.5),
    ('P045', 'Trà ô long (hộp 250g)', 'Cà phê & trà', 150000, 0.4),
    ('P060', 'Túi giữ nhiệt ShopNhanh (quà tặng)', 'Quà tặng', 0, 0.0),
]
MARGIN = {'Mì & đồ khô': 0.12, 'Trứng & sữa': 0.15, 'Đồ uống': 0.20, 'Bia': 0.12,
          'Snack & bánh kẹo': 0.28, 'Gia vị': 0.22, 'Giặt giũ & tẩy rửa': 0.25, 'Mẹ & bé': 0.30,
          'Rau củ & trái cây': 0.30, 'Thịt cá': 0.18, 'Cà phê & trà': 0.25, 'Quà tặng': 0.0}
products = pd.DataFrame(PRODUCTS, columns=['product_id', 'product_name', 'category', 'list_price', 'w'])
products['gross_margin'] = products['category'].map(MARGIN)
PRICE = dict(zip(products.product_id, products.list_price))
PIDS = products.product_id.to_numpy()

# Segment multipliers on base popularity: who buys what
SEG_MULT = {
    'gia_dinh_tre': {'Mẹ & bé': 1.0, 'Bia': 0.5, 'Rau củ & trái cây': 1.2, 'Thịt cá': 1.2},
    'gia_dinh':     {'Mẹ & bé': 0.0, 'Bia': 0.8, 'Rau củ & trái cây': 1.2, 'Thịt cá': 1.2},
    'van_phong':    {'Mẹ & bé': 0.0, 'Bia': 1.3, 'Cà phê & trà': 1.6, 'Rau củ & trái cây': 0.8},
    'sinh_vien':    {'Mẹ & bé': 0.0, 'Bia': 1.2, 'Mì & đồ khô': 1.4, 'Thịt cá': 0.7},
}
SEG_SHARE = {'gia_dinh_tre': 0.25, 'gia_dinh': 0.30, 'van_phong': 0.25, 'sinh_vien': 0.20}
SEG_BASKET_LAMBDA = {'gia_dinh_tre': 2.4, 'gia_dinh': 2.6, 'van_phong': 1.7, 'sinh_vien': 1.5}
SEG_ORDERS_MEAN = {'gia_dinh_tre': 4.6, 'gia_dinh': 4.0, 'van_phong': 3.4, 'sinh_vien': 3.0}
SEG_BUNDLE_P = {'gia_dinh_tre': 0.01, 'gia_dinh': 0.03, 'van_phong': 0.06, 'sinh_vien': 0.06}

seg_weights = {}
for seg, mult in SEG_MULT.items():
    w = products['w'] * products['category'].map(lambda c: mult.get(c, 1.0))
    seg_weights[seg] = (w / w.sum()).to_numpy()

# Planted organic rules: A -> (B, p)
RULES = {'P001': ('P006', 0.35), 'P027': ('P028', 0.40), 'P031': ('P032', 0.45), 'P043': ('P008', 0.30)}

# ---------------------------------------------------------------- customers
cust_ids = [f'C{i:06d}' for i in range(1, N_CUSTOMERS + 1)]
segments = np.random.choice(list(SEG_SHARE), N_CUSTOMERS, p=list(SEG_SHARE.values()))
cities = np.random.choice(['Hồ Chí Minh', 'Hà Nội', 'Đà Nẵng'], N_CUSTOMERS, p=[0.6, 0.3, 0.1])
signup = pd.Timestamp('2022-01-01') + pd.to_timedelta(np.random.randint(0, 1642, N_CUSTOMERS), unit='D')
customers = pd.DataFrame({'customer_id': cust_ids, 'signup_date': signup.date, 'city': cities, 'segment': segments})
# QA test account, looks like a normal office customer
customers.loc[len(customers)] = ['C000000', pd.Timestamp('2024-01-15').date(), 'Hồ Chí Minh', 'van_phong']

# ---------------------------------------------------------------- orders + items
HOUR_P = np.array([1, 0.5, 0.3, 0.2, 0.2, 0.5, 1.5, 3, 4, 4.5, 5, 6, 6.5, 5, 4, 3.5, 4, 5, 6.5, 7.5, 8, 7, 5, 2.5])
HOUR_P = HOUR_P / HOUR_P.sum()
n_days = (END.normalize() - START).days + 1

order_rows, item_rows = [], []
oid = 0


def add_line(o, pid, qty=None, price=None, bundle=None):
    if qty is None:
        qty = np.random.choice([1, 2, 3], p=[0.75, 0.18, 0.07])
    if price is None:
        price = PRICE[pid] * (0.9 if np.random.rand() < 0.15 else 1.0)
        price = round(price / 1000) * 1000
    item_rows.append([o, pid, qty, price, bundle])
    return qty * price


for cid, seg in zip(customers.customer_id[:-1], customers.segment[:-1]):
    for _ in range(np.random.poisson(SEG_ORDERS_MEAN[seg])):
        oid += 1
        o = f'O{oid:07d}'
        ts = START + pd.Timedelta(days=int(np.random.randint(n_days)), hours=int(np.random.choice(24, p=HOUR_P)),
                                  minutes=int(np.random.randint(60)))
        weekend_evening = ts.dayofweek >= 4 and ts.hour >= 18  # Fri-Sun from 18h
        size = 1 + np.random.poisson(SEG_BASKET_LAMBDA[seg])
        basket = set(np.random.choice(PIDS, size=min(size, 12), replace=False, p=seg_weights[seg]))
        # planted rules (only add B; A comes from popularity)
        for a, (b, p) in RULES.items():
            if a in basket and np.random.rand() < p:
                basket.add(b)
        if 'P015' in basket and np.random.rand() < (0.50 if weekend_evening else 0.03):
            basket.add('P017')  # R5: beer + snack, weekend evenings only
        if ts.month == 9 and ts.day <= 25 and np.random.rand() < 0.03:
            basket.add('P021')  # mooncake season
            if np.random.rand() < 0.55:
                basket.add('P045')  # R6: mooncake + oolong tea
        subtotal = sum(add_line(o, pid) for pid in sorted(basket))
        if np.random.rand() < SEG_BUNDLE_P[seg]:  # trap: fixed combo, both lines share bundle_id
            subtotal += add_line(o, 'P016', 1, 80000, 'BDL-BIA6-DP') + add_line(o, 'P018', 1, 18000, 'BDL-BIA6-DP')
        if subtotal >= GIFT_THRESHOLD:  # trap: system-added gift
            add_line(o, 'P060', 1, 0)
        status = np.random.choice(['completed', 'cancelled', 'returned'], p=[0.91, 0.07, 0.02])
        ship = 0 if subtotal >= 300_000 else int(np.random.choice([15000, 20000]))
        order_rows.append([o, cid, ts, np.random.choice(['app', 'web'], p=[0.7, 0.3]),
                           np.random.choice(['cod', 'ewallet', 'card'], p=[0.45, 0.35, 0.20]), status, ship])

# trap: QA test account with huge baskets
for _ in range(25):
    oid += 1
    o = f'O{oid:07d}'
    ts = START + pd.Timedelta(days=int(np.random.randint(n_days)), hours=int(np.random.randint(9, 17)))
    for pid in np.random.choice(PIDS[:-1], size=np.random.randint(28, 41), replace=False):
        add_line(o, pid, 1)
    order_rows.append([o, 'C000000', ts, 'web', 'card', 'completed', 0])

orders = pd.DataFrame(order_rows, columns=['order_id', 'customer_id', 'order_datetime', 'channel',
                                           'payment_method', 'status', 'shipping_fee'])
items = pd.DataFrame(item_rows, columns=['order_id', 'product_id', 'quantity', 'unit_price', 'bundle_id'])

# ---------------------------------------------------------------- traps
n = len(orders)
orphan_cust = np.random.choice(n, int(0.01 * n), replace=False)  # deleted accounts
orders.loc[orphan_cust, 'customer_id'] = [f'C9{i:05d}' for i in np.random.randint(0, 99999, len(orphan_cust))]
orders.loc[np.random.rand(n) < 0.03, 'channel'] = np.nan

m = len(items)
items.loc[np.random.choice(m, int(0.003 * m), replace=False), 'product_id'] = 'P999'
bad_qty = np.random.choice(m, int(0.003 * m), replace=False)
items.loc[bad_qty, 'quantity'] = np.random.choice([0, -1], len(bad_qty))

customers.loc[np.random.rand(len(customers)) < 0.04, 'segment'] = np.nan
customers.loc[np.random.rand(len(customers)) < 0.02, 'city'] = np.nan

orders = pd.concat([orders, orders.sample(frac=0.005, random_state=42)])
items = pd.concat([items, items.sample(frac=0.015, random_state=42)])
orders = orders.sample(frac=1, random_state=42).reset_index(drop=True)
items = items.sample(frac=1, random_state=42).reset_index(drop=True)
orders['order_datetime'] = orders['order_datetime'].dt.strftime('%Y-%m-%d %H:%M')

products[['product_id', 'product_name', 'category', 'list_price', 'gross_margin']].to_csv(OUT / 'products.csv', index=False)
customers.to_csv(OUT / 'customers.csv', index=False)
orders.to_csv(OUT / 'orders.csv', index=False)
items.to_csv(OUT / 'order_items.csv', index=False)
print(f'customers {len(customers)} | orders {len(orders)} | order_items {len(items)} | products {len(products)}')
