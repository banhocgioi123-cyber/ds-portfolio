"""Reference solution in ~60 lines: clean -> pair rules -> money value -> pick 5 combos.

Last line: METRIC top5_value_mvnd <million VND gross profit / month, scaled to 100% of customers>
"""
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
D = Path(__file__).resolve().parents[1] / 'data'
SCALE, MONTHS, TAKE_K = 20, 3, 0.20          # 5% sample, Q3 = 3 months, take_rate = 0.20 * confidence
MIN_SUPPORT, MIN_LIFT = 0.005, 1.2
PLANTED = {('P001', 'P006'), ('P027', 'P028'), ('P031', 'P032'), ('P043', 'P008'), ('P015', 'P017')}

products = pd.read_csv(D / 'products.csv')
orders_raw = pd.read_csv(D / 'orders.csv', parse_dates=['order_datetime'])
items_raw = pd.read_csv(D / 'order_items.csv')


def rules(orders, items):
    """All A -> B rules for the given orders. N = number of orders (baskets)."""
    baskets = items[items.order_id.isin(orders.order_id)][['order_id', 'product_id']].drop_duplicates()
    n = orders.order_id.nunique()
    cnt = baskets.groupby('product_id').size()
    pairs = baskets.merge(baskets, on='order_id', suffixes=('_a', '_b'))
    pairs = pairs[pairs.product_id_a != pairs.product_id_b]
    r = pairs.groupby(['product_id_a', 'product_id_b']).size().rename('n_ab').reset_index()
    r['n_a'] = r.product_id_a.map(cnt)
    r['support'] = r.n_ab / n
    r['confidence'] = r.n_ab / r.n_a
    r['lift'] = r.confidence / (r.product_id_b.map(cnt) / n)
    return r


def value(r, items):
    """Monthly gross profit (VND, full customer base) of showing B next to A."""
    price = items.groupby('product_id').unit_price.mean()
    margin = products.set_index('product_id').gross_margin
    return SCALE * (r.n_a - r.n_ab) / MONTHS * TAKE_K * r.confidence * r.product_id_b.map(price) * r.product_id_b.map(margin)


def pick5(r):
    """Greedy: best value first, each A once, each unordered pair once."""
    chosen, used_a, used_pair = [], set(), set()
    for row in r.sort_values('value', ascending=False).itertuples():
        pair = frozenset((row.product_id_a, row.product_id_b))
        if row.product_id_a in used_a or pair in used_pair:
            continue
        chosen.append(row)
        used_a.add(row.product_id_a)
        used_pair.add(pair)
        if len(chosen) == 5:
            break
    return pd.DataFrame(chosen)


# ---- clean
orders = orders_raw.drop_duplicates()
orders = orders[(orders.status == 'completed') & (orders.customer_id != 'C000000')]
items = items_raw.drop_duplicates()
items = items[(items.quantity > 0) & items.product_id.isin(products.product_id)
              & items.bundle_id.isna() & (items.unit_price > 0)]

r = rules(orders, items)
r['value'] = value(r, items)
cand = r[(r.support >= MIN_SUPPORT) & (r.lift >= MIN_LIFT)]
top5 = pick5(cand)
name = products.set_index('product_id').product_name
print(top5.assign(a=top5.product_id_a.map(name), b=top5.product_id_b.map(name))
      [['a', 'b', 'support', 'confidence', 'lift', 'value']].round(3).to_string(index=False))

# ---- diagnostics: planted recall + what a naive analysis would pick
top10 = set(zip(*cand.sort_values('value', ascending=False).head(10)[['product_id_a', 'product_id_b']].values.T))
print(f'planted rules in clean top-10 by value: {len(PLANTED & top10)}/{len(PLANTED)}')
naive = rules(orders_raw, items_raw)
naive = naive[naive.support >= MIN_SUPPORT].sort_values('lift', ascending=False).head(5)
print('naive top-5 by lift (raw data):', list(zip(naive.product_id_a, naive.product_id_b, naive.lift.round(1))))
naive_val = r.set_index(['product_id_a', 'product_id_b']).value.reindex(list(zip(naive.product_id_a, naive.product_id_b)))
bad = {'P060', 'P016', 'P018', 'P021'}  # gift, bundle, seasonal -> invalid slot, worth 0
naive_val[[a in bad or b in bad for a, b in naive_val.index]] = 0
print(f'naive top-5 value: {naive_val.fillna(0).sum() / 1e6:.1f} M VND/month')
by_count = pick5(cand.assign(value=cand.n_ab))
print(f'top-5 by pair count value: {r.set_index(["product_id_a", "product_id_b"]).value.reindex(list(zip(by_count.product_id_a, by_count.product_id_b))).sum() / 1e6:.1f} M VND/month')
def one(r, a, b):
    return r[(r.product_id_a == a) & (r.product_id_b == b)].iloc[0] if ((r.product_id_a == a) & (r.product_id_b == b)).any() else None


sept = orders[(orders.order_datetime.dt.month == 9) & (orders.order_datetime.dt.day <= 25)]
q6, s6 = one(r, 'P021', 'P045'), one(rules(sept, items), 'P021', 'P045')
print(f'R6 mooncake->tea: quarter support {q6.support:.4f} | Sept 1-25 support {s6.support:.4f}, lift {s6.lift:.1f}')
we = orders[(orders.order_datetime.dt.dayofweek >= 4) & (orders.order_datetime.dt.hour >= 18)]
q5, w5 = one(r, 'P015', 'P017'), one(rules(we, items), 'P015', 'P017')
print(f'R5 beer->snack: overall lift {q5.lift:.2f} conf {q5.confidence:.2f} | Fri-Sun >=18h lift {w5.lift:.2f} conf {w5.confidence:.2f}')

print(f'METRIC top5_value_mvnd {top5.value.sum() / 1e6:.2f}')
