import csv
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus
import streamlit as st

BASE = Path(__file__).parent
st.set_page_config(page_title='FoodWise UK', page_icon='🍜', layout='wide')
st.title('🍜 FoodWise UK')
st.caption('Compare food delivery offers — sample data only until approved integrations are connected.')

@st.cache_data
def load_offers():
    with (BASE / 'offers.csv').open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def calculate(row, basket, code):
    subtotal = float(row['item_price_gbp']) * basket
    delivery = float(row['delivery_fee_gbp'])
    service = float(row['service_fee_gbp'])
    discount = 0.0
    eligible = False
    if code and code.strip().upper() == row['coupon_code'].upper() and subtotal >= float(row['coupon_min_spend_gbp']):
        discount = min(subtotal * float(row['coupon_percent']) / 100, float(row['coupon_cap_gbp']))
        eligible = True
    return round(max(0, subtotal - discount) + delivery + service, 2), round(discount, 2), eligible

with st.sidebar:
    st.header('Your order')
    food = st.text_input('Food item', 'chicken biryani')
    postcode = st.text_input('UK delivery postcode', 'S80 1AA').strip().upper()
    qty = st.number_input('Quantity', min_value=1, max_value=20, value=1)
    coupon = st.text_input('Coupon code (optional)', placeholder='Try SAMPLE10')
    sort = st.selectbox('Sort by', ['Lowest final price', 'Highest taste rating', 'Best value score'])
    st.info('Postcode is a placeholder in sample mode. Live delivery eligibility is not checked.')

rows = []
for offer in load_offers():
    if food.strip().lower() not in offer['food_item'].lower():
        continue
    total, discount, eligible = calculate(offer, qty, coupon)
    rating = float(offer['taste_rating'])
    rows.append({**offer, 'total': total, 'discount': discount, 'eligible': eligible, 'rating': rating, 'value_score': round(rating / max(total, 0.01), 3)})

if not rows:
    st.warning('No matching sample dishes. Try “chicken biryani”, “pizza”, or “burger”.')
else:
    if sort == 'Lowest final price':
        rows.sort(key=lambda r: r['total'])
    elif sort == 'Highest taste rating':
        rows.sort(key=lambda r: -r['rating'])
    else:
        rows.sort(key=lambda r: -r['value_score'])
    best = rows[0]
    st.success(f"Top match: {best['restaurant']} on {best['platform']} — £{best['total']:.2f} ({sort.lower()})")
    st.caption('Prices, ratings, coupon codes and restaurants below are fictional demonstration records, not live listings.')
    for r in rows:
        with st.container(border=True):
            a, b, c = st.columns([3, 1, 1])
            with a:
                st.subheader(f"{r['food_item']} · {r['restaurant']}")
                st.write(f"**{r['platform']}** · Sample taste score: {r['rating']:.1f}/5 · Sample review count: {r['review_count']}")
                st.caption(f"Item £{float(r['item_price_gbp']):.2f} × {qty} · Delivery £{float(r['delivery_fee_gbp']):.2f} · Service £{float(r['service_fee_gbp']):.2f}")
                st.caption(f"Example coupon: {r['coupon_code']} ({r['coupon_percent']}% off, minimum £{float(r['coupon_min_spend_gbp']):.2f}, cap £{float(r['coupon_cap_gbp']):.2f}); {'applied' if r['eligible'] else 'not applied'}")
            with b:
                st.metric('Estimated total', f"£{r['total']:.2f}")
                st.caption(f"Discount: £{r['discount']:.2f}")
            with c:
                url = {'Uber Eats': 'https://www.ubereats.com/gb', 'Deliveroo': 'https://deliveroo.co.uk/', 'Just Eat': 'https://www.just-eat.co.uk/'}[r['platform']]
                st.link_button('Open platform', url)
    st.caption('The links open each platform homepage, not a verified dish listing. Always check checkout totals and eligibility.')

st.divider()
st.subheader('Integration status')
st.write('🟡 CSV sample adapter: active · ⚪ Uber Eats partner API: not connected · ⚪ Deliveroo partner API: not connected · ⚪ Just Eat partner API: not connected')
st.caption(f"Page rendered at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}; this is not a price update timestamp.")
