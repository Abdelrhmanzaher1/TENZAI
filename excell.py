import streamlit as st
import pandas as pd
import openai
import re

# مفتاح API (حط مفتاحك الخاص هنا)
openai.api_key = "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"

def extract_prices(text):
    min_price = None
    max_price = None

    min_match = re.search(r'(السعر الأدنى|اقل سعر|minimum price)[^0-9]*([\d,.]+)', text, re.IGNORECASE)
    max_match = re.search(r'(السعر الأقصى|اعلى سعر|maximum price)[^0-9]*([\d,.]+)', text, re.IGNORECASE)

    if min_match:
        min_price = min_match.group(2).replace(',', '').strip()
    if max_match:
        max_price = max_match.group(2).replace(',', '').strip()

    return min_price, max_price

def analyze_item(name, description, specs, unit, quantity, city, country):
    prompt = (
        f"أنت مهندس تسعير خبير في السوق السعودي 2024-2025 لكل أنواع بنود المقاولات، بما في ذلك المدنية، الكهربائية، الميكانيكية، والتقنية.\n"
        f"يرجى تحليل البند التالي بدقة، مع التركيز على المواصفات التقنية، المواد، وأجور التركيب، وتقديم سعر أدنى وأقصى لكل وحدة (ريال سعودي).\n"
        f"✅ التزم بوحدة القياس المدخلة فقط: '{unit}'.\n"
        f"✅ لا تذكر أسعار إجمالية أو كميات، فقط سعر الوحدة.\n"
        f"✅ الأرقام يجب أن تعكس الواقع في السوق السعودي.\n\n"
        f"بيانات البند:\n"
        f"- اسم البند: {name}\n"
        f"- وصف البند: {description}\n"
        f"- المواصفات: {specs}\n"
        f"- وحدة القياس: {unit}\n"
        f"- الكمية: {quantity}\n"
        f"- المدينة: {city}\n"
        f"- الدولة: {country}\n\n"
        f"المطلوب:\n"
        f"1. شرح وتحليل مفصل للبند.\n"
        f"2. السعر الأدنى لكل وحدة (ريال سعودي).\n"
        f"3. السعر الأقصى لكل وحدة (ريال سعودي).\n"
        f"4. تأكيد الالتزام بوحدة القياس.\n"
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35,
            max_tokens=900,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ خطأ في التحليل: {e}"

def check_unit_in_analysis(analysis_text, unit):
    unit = unit.strip().lower()
    text = analysis_text.lower()
    return unit in text

def filter_price(price_str):
    try:
        price = float(price_str.replace(',', ''))
        if 0 < price < 1_000_000:
            return price
        else:
            return None
    except:
        return None

st.title("🔍 تسعير وتحليل بنود المقاولات - نسخة تحليل معمقة")

uploaded_file = st.file_uploader(
    "📤 ارفع ملف Excel يحتوي الأعمدة: 'اسم البند', 'وصف البند', 'المواصفات', 'وحدة القياس', 'الكمية', 'المدينة', 'الدولة'",
    type=["xlsx"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    for col in ['تحليل البند', 'السعر الأدنى', 'السعر الأقصى', 'وحدة القياس مطابقة']:
        if col not in df.columns:
            df[col] = ""

    with st.spinner("🔄 جاري التحليل والتسعير المفصل..."):
        for i, row in df.iterrows():
            analysis = analyze_item(
                row.get('اسم البند', ''),
                row.get('وصف البند', ''),
                row.get('المواصفات', ''),
                row.get('وحدة القياس', ''),
                row.get('الكمية', ''),
                row.get('المدينة', ''),
                row.get('الدولة', '')
            )
            min_price, max_price = extract_prices(analysis)
            unit_ok = check_unit_in_analysis(analysis, row.get('وحدة القياس', ''))

            min_price_val = filter_price(min_price)
            max_price_val = filter_price(max_price)

            df.at[i, 'تحليل البند'] = analysis
            df.at[i, 'السعر الأدنى'] = min_price_val if min_price_val else "غير منطقي"
            df.at[i, 'السعر الأقصى'] = max_price_val if max_price_val else "غير منطقي"
            df.at[i, 'وحدة القياس مطابقة'] = "نعم" if unit_ok else "لا"

    if "لا" in df['وحدة القياس مطابقة'].values:
        st.warning("⚠️ بعض البنود لم تلتزم بوحدة القياس المدخلة.")

    if (df['السعر الأدنى'] == "غير منطقي").any() or (df['السعر الأقصى'] == "غير منطقي").any():
        st.warning("⚠️ تم العثور على أسعار غير منطقية وتم الإشارة إليها.")

    df.to_excel("output.xlsx", index=False)
    st.success("✅ تم تحليل وتسعير البنود بنجاح.")
    st.download_button(
        "⬇️ تحميل الملف المحلل",
        data=open("output.xlsx", "rb").read(),
        file_name="output.xlsx"
    )
