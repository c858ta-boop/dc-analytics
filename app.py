import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="ИИ-Аналитик Склада СПб", layout="wide")

st.title("🚗 Профессиональный ИИ-Аналитик склада (Санкт-Петербург)")
st.subheader("Личный кабинет Директора брендов: Changan, GAC, Volga, UMO")

MARKET_DATABASE_SPB = {
    "CHANGAN": {
        "ALSVIN": 1950000, "EADO PLUS": 2400000, "LAMORE": 2900000,
        "CS35 PLUS": 2350000, "CS35 MAX": 2480000, "CS55 PLUS": 2650000,
        "UNI-S": 2680000, "UNI-T": 2850000, "CS75 PRO": 2865000,
        "CS75 PLUS": 3150000, "UNI-V": 2950000, "UNI-K": 4200000,
        "CS85 COUPE": 3700000, "CS95": 4300000, "HUNTER PLUS": 3450000,
        "AVATR 11": 6200000, "AVATR 12": 6900000
    },
    "GAC": {
        "GS3": 2350000, "GS4": 2550000, "GS5": 2400000, 
        "GS8": 4450000, "M8": 5800000, "EMPOW": 2990000,
        "S7": 6249000, "S9": 6700000
    },
    "VOLGA": {
        "C40": 2850000, "C50": 2999000, "K30": 3200000, 
        "K40": 2849000, "K50": 4649000
    },
    "UMO": {
        "U5": 2300000, "U7": 2900000
    }
}

uploaded_file = st.file_uploader("Шаг 1: Перетащите сюда Excel-файл выгрузки склада из 1С", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("Файл успешно прочитан ИИ-агентом!")
    
    rename_dict = {}
    for col in df.columns:
        col_str = str(col).lower().strip()
        if any(x in col_str for x in ['бренд', 'марка']): rename_dict[col] = 'Бренд'
        elif 'модель' in col_str: rename_dict[col] = 'Модель'
        elif any(x in col_str for x in ['день', 'дней', 'срок', 'возраст', 'сток', 'хранения']): rename_dict[col] = 'Дней на складе'
        elif any(x in col_str for x in ['текущая', 'рознич', 'цена', 'прайс']) and not any(y in col_str for y in ['порог', 'минимум']):
            rename_dict[col] = 'Текущая розничная цена'
        elif any(x in col_str for x in ['порог', 'минимум', 'мин']): rename_dict[col] = 'Минимальный порог цены'
            
    df = df.rename(columns=rename_dict)
    
    st.write("### 📊 Состояние склада автоцентров в системе:")
    st.dataframe(df, use_container_width=True)
    
    st.write("### 🤖 Управленческие решения ИИ-Агента на основе рынка Санкт-Петербурга:")
    
    recommendations = []
    pdf_text_lines = [] # База для печатного отчета
    has_overaged = False
    
    for index, row in df.iterrows():
        brand_raw = str(row.get('Бренд', '')).upper().strip()
        model_raw = str(row.get('Модель', '')).upper().strip()
        
        brand = brand_raw
        model = None
        
        for known_brand in MARKET_DATABASE_SPB.keys():
            if known_brand in brand_raw:
                brand = known_brand
                break
                
        if brand in MARKET_DATABASE_SPB:
            model_clean = model_raw.replace(" ", "").replace("-", "")
            sorted_known_models = sorted(MARKET_DATABASE_SPB[brand].keys(), key=len, reverse=True)
            for known_model in sorted_known_models:
                known_clean = known_model.replace(" ", "").replace("-", "")
                if known_clean in model_clean:
                    model = known_model
                    break
        
        try: days_on_stock = int(float(str(row.get('Дней на складе', 0)).replace('дн', '').strip()))
        except: days_on_stock = 0
        try: current_price = float(str(row.get('Текущая розничная цена', 0)).replace(' ', '').replace(',', ''))
        except: current_price = 0
        try: min_price = float(str(row.get('Минимальный порог цены', 0)).replace(' ', '').replace(',', ''))
        except: min_price = current_price * 0.95
        
        comp_price = MARKET_DATABASE_SPB.get(brand, {}).get(model, None)
        
        if comp_price and current_price > 0:
            diff = current_price - comp_price
            
            if days_on_stock >= 100:
                has_overaged = True
                suggested_price = max(comp_price - 30000, min_price)
                if current_price > comp_price:
                    status_type = "КРИТИЧЕСКИЙ СТОК"
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Мы дороже рынка СПб на {diff:,} ₽. Рекомендация: Снизить цену до **{suggested_price:,} ₽**."
                else:
                    status_type = "КРИТИЧЕСКИЙ СТОК"
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Цена соответствует рынку. Рекомендация РОПу: Выделить скрытый бонус менеджерам +40 000 ₽."
            elif days_on_stock > 45:
                suggested_price = max(comp_price, min_price)
                if diff > 50000:
                    status_type = "ЗАВИСАНИЕ"
                    rec_text = f"⚠️ **Зависание склада ({days_on_stock} дн.).** Дороже рынка на {diff:,} ₽. Рекомендуем выровнять прайс до **{suggested_price:,} ₽**."
                else:
                    status_type = "В РЫНКЕ"
                    rec_text = f"🟢 Склад {days_on_stock} дн. Цена оптимальна относительно конкурентов СПб ({comp_price:,} ₽)."
            else:
                status_type = "СВЕЖИЙ СТОК"
                rec_text = f"🟢 **Свежий склад ({days_on_stock} дн.).** Цена полностью соответствует рынку Санкт-Петербурга ({comp_price:,} ₽)."
        else:
            status_type = "НЕТ ДАННЫХ"
            rec_text = f"⚪ Модель принята. Требуется расширение базы."
            
        recommendations.append(f"• **{brand_raw} {model_raw}** ➔ {rec_text}")
        # Форматируем строку для PDF (чистый текст без markdown-звездочек)
        pdf_text_lines.append(f"- {brand_raw} {model_raw} ({days_on_stock} дн., {current_price:,.0f} руб.) [{status_type}] -> {rec_text.replace('**', '').replace('🚨', '').replace('⚠️', '').replace('🟢', '')}")
        
    if has_overaged:
        st.error("🚨 ВНИМАНИЕ ДИРЕКТОРА: НА СКЛАДЕ ОБНАРУЖЕНЫ АВТОМОБИЛИ С КРИТИЧЕСКИМ СРОКОМ ХРАНЕНИЯ (>100 ДНЕЙ)!")
        
    for rec in recommendations:
        st.markdown(rec)
        
    # --- СБОРКА И ГЕНЕРАЦИЯ PDF КОРРЕКТНЫМ СПОСОБОМ ---
    st.write("---")
    st.write("### 🖨️ Шаг 4: Экспорт отчета для утреннего совещания")
    
    if st.button("Сгенерировать официальный PDF-отчет"):
        pdf = FPDF()
        pdf.add_page()
        
        # Используем стандартный безопасный шрифт FPDF, который гарантированно не упадет
        pdf.set_font("Helvetica", size=12)
        
        # Шапка официального документа
        pdf.cell(200, 10, txt="RAPORT FOR MORNING MEETING / ANALYTICS DEPT", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%d.%m.%Y')} | Region: St. Petersburg", ln=True, align='C')
        pdf.cell(200, 10, txt="========================================================", ln=True, align='C')
        pdf.ln(10)
        
        # Переводим кириллицу в безопасную транслитерацию для Helvetica, чтобы не было кракозябр
        def trans(text):
            rules = {"А":"A","Б":"B","В":"V","Г":"G","Д":"D","Е":"E","Ё":"E","Ж":"Zh","З":"Z","И":"I","Й":"Y","К":"K","Л":"L","М":"M","Н":"N","О":"O","П":"P","Р":"R","С":"S","Т":"T","У":"U","Ф":"F","Х":"Kh","Ц":"Ts","Ч":"Ch","Ш":"Sh","Щ":"Shch","Ъ":"","Ы":"Y","Ь":"","Э":"E","Ю":"Yu","Я":"Ya","а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"kh","ц":"ts","ч":"ch","ш":"sh","щ":"shch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya","₽":"руб","«":'"',"»":'"',"ё":"e"}
            return "".join(rules.get(c, c) for c in text)

        if has_overaged:
            pdf.cell(200, 10, txt="!!! WARNING: CRITICAL OVERAGED STOCK DETECTED (>100 DAYS) !!!", ln=True)
            pdf.ln(5)
            
        for line in pdf_text_lines:
            # Записываем каждую рекомендацию безопасной строкой
            pdf.multi_cell(0, 10, txt=trans(line))
            
        pdf.ln(15)
        pdf.cell(200, 10, txt="Director's resolution: ___________________________", ln=True)
        
        # Превращаем документ в байты для кнопки скачивания
        pdf_bytes = pdf.output(dest='S')
        
        st.download_button(
            label="📥 Скачать готовый PDF для печати",
            data=pdf_bytes,
            file_name=f"Сводка_Склад_СПб_{datetime.now().strftime('%d_%m_%Y')}.pdf",
            mime="application/pdf"
        )
else:
    st.info("Пожалуйста, загрузите ваш Excel-файл для точного коммерческого анализа рынка Санкт-Петербурга.")
