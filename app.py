import streamlit as st
import pandas as pd
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
    html_print_rows = ""  # Текст для печати
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
                    status_style = "color: red; font-weight: bold;"
                    status_text = "КРИТИЧЕСКИЙ СТОК"
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Мы дороже рынка СПб на {diff:,} ₽. Рекомендация: Снизить цену до **{suggested_price:,} ₽**."
                else:
                    status_style = "color: red; font-weight: bold;"
                    status_text = "КРИТИЧЕСКИЙ СТОК"
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Цена соответствует рынку. Рекомендация РОПу: Выделить скрытый бонус менеджерам +40 000 ₽."
            elif days_on_stock > 45:
                suggested_price = max(comp_price, min_price)
                if diff > 50000:
                    status_style = "color: orange; font-weight: bold;"
                    status_text = "ЗАВИСАНИЕ"
                    rec_text = f"⚠️ **Зависание склада ({days_on_stock} дн.).** Дороже рынка на {diff:,} ₽. Рекомендуем выровнять прайс до **{suggested_price:,} ₽**."
                else:
                    status_style = "color: green;"
                    status_text = "В РЫНКЕ"
                    rec_text = f"🟢 Склад {days_on_stock} дн. Цена оптимальна относительно конкурентов СПб ({comp_price:,} ₽)."
            else:
                status_style = "color: gray;"
                status_text = "СВЕЖИЙ СТОК"
                rec_text = f"🟢 **Свежий склад ({days_on_stock} дн.).** Цена полностью соответствует рынку Санкт-Петербурга ({comp_price:,} ₽)."
        else:
            status_style = "color: black;"
            status_text = "НЕТ ДАННЫХ"
            rec_text = f"⚪ Модель принята. Требуется расширение базы."
            
        st.markdown(f"• **{brand_raw} {model_raw}** ➔ {rec_text}")
        
        # Собираем красивую HTML таблицу для печати на русском языке
        html_print_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{brand_raw} {model_raw}</b></td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{days_on_stock}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{current_price:,.0f} ₽</td>
            <td style="padding: 8px; border: 1px solid #ddd; {status_style}">{status_text}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{rec_text}</td>
        </tr>
        """
        
    if has_overaged:
        st.error("🚨 ВНИМАНИЕ ДИРЕКТОРА: НА СКЛАДЕ ОБНАРУЖЕНЫ АВТОМОБИЛИ С КРИТИЧЕСКИМ СРОКОМ ХРАНЕНИЯ (>100 ДНЕЙ)!")
        
    # --- БЛОК ДЛЯ ИДЕАЛЬНОЙ ПЕЧАТИ ---
    st.write("---")
    st.write("### 🖨️ Шаг 4: Версия для печати на утреннюю планерку")
    
    # Собираем полноценную страницу для печати
    html_report = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: white; color: black; border: 2px solid #333; border-radius: 5px;">
        <h2 style="text-align: center; margin-bottom: 5px;">ОФИЦИАЛЬНЫЙ ОТЧЕТ ДЛЯ УТРЕННЕЙ ПЛАНЕРКИ ДЦ</h2>
        <p style="text-align: center; font-size: 14px; color: #555;">Дата: {datetime.now().strftime('%d.%m.%Y')} | Регион: Санкт-Петербург</p>
        <hr style="border: 1px solid #333;">
        
        <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 10px; border: 1px solid #333; text-align: left;">Автомобиль</th>
                    <th style="padding: 10px; border: 1px solid #333; text-align: center;">Дней стока</th>
                    <th style="padding: 10px; border: 1px solid #333; text-align: right;">Цена 1С</th>
                    <th style="padding: 10px; border: 1px solid #333; text-align: left;">Статус</th>
                    <th style="padding: 10px; border: 1px solid #333; text-align: left;">Решение ИИ-агента</th>
                </tr>
            </thead>
            <tbody>
                {html_print_rows}
            </tbody>
        </table>
        
        <br><br><br>
        <p style="font-size: 14px;"><b>Резолюция Директора ДЦ:</b> ____________________________________________________________________</p>
        <p style="font-size: 12px; color: #777; text-align: right; margin-top: 30px;">Сформировано автономным ИИ-агентом</p>
    </div>
    """
    
    # Показываем красивый бланк прямо на сайте
    st.write("👉 Нажмите сочетание клавиш **Ctrl + P** (или **Cmd + P** на Mac) прямо на этой странице браузера, чтобы отправить бланк ниже на принтер или сохранить в PDF.")
    st.components.v1.html(html_report, height=600, scrolling=True)

else:
    st.info("Пожалуйста, загрузите ваш Excel-файл для точного коммерческого анализа рынка Санкт-Петербурга.")
