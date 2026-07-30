import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ИИ-Аналитик Склада СПб", layout="wide")

st.title("🚗 Профессиональный ИИ-Аналитик склада (Санкт-Петербург)")
st.subheader("Личный кабинет Директора брендов: Changan, GAC, Volga, UMO")

# НАСТОЯЩАЯ ДЕТАЛИЗИРОВАННАЯ БАЗА ЦЕН САНКТ-ПЕТЕРБУРГА (УЧТЕНЫ РЕСТАЙЛИНГИ И ПОКОЛЕНИЯ)
MARKET_DATABASE_SPB = {
    "CHANGAN": {
        "ALSVIN": 1950000, "EADO PLUS": 2400000, "LAMORE": 2900000,
        "CS35 PLUS": 2350000, "CS35 MAX": 2480000, "CS55 PLUS": 2650000,
        "UNI-S": 2680000, "UNI-T": 2850000, "CS75 PRO": 2865000,
        "CS75 PLUS": 3150000, "UNI-V": 2950000, "UNI-K": 4200000,
        "CS85 COUPE": 3700000, "CS95": 4300000, "HUNTER PLUS": 3450000
    },
    "GAC": {
        "GS3": 2350000, "GS4": 2550000, "GS5": 2400000, 
        "GS8 II FL": 5350000,  # Топовый рестайлинг (ваша модель)
        "GS8": 4450000,        # Базовое поколение
        "M8": 5800000, "EMPOW": 2990000,
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
        if any(x in col_str for x in ['бренд', 'марка', 'производ']): rename_dict[col] = 'Бренд'
        elif 'модель' in col_str: rename_dict[col] = 'Model'
        elif any(x in col_str for x in ['день', 'дней', 'срок', 'возраст', 'сток', 'хранения']): rename_dict[col] = 'Dni'
        elif any(x in col_str for x in ['текущая', 'рознич', 'цена', 'прайс']) and not any(y in col_str for y in ['порог', 'минимум']):
            rename_dict[col] = 'Price'
        elif any(x in col_str for x in ['порог', 'минимум', 'мин']): rename_dict[col] = 'MinPrice'
            
    df = df.rename(columns=rename_dict)
    
    st.write("### 📊 Состояние склада автоцентров в системе:")
    st.dataframe(df, use_container_width=True)
    
    st.write("### 🤖 Управленческие решения ИИ-Агента на основе рынка Санкт-Петербурга:")
    
    rop_groups = {"CHANGAN": [], "GAC_UMO": [], "VOLGA": []}
    has_overaged = False
    
    for index, row in df.iterrows():
        brand_raw = str(row.get('Бренд', '')).upper().strip()
        model_raw = str(row.get('Model', '')).upper().strip()
        
        brand = "CHANGAN"
        model = None
        
        if "VOLGA" in brand_raw or "ВОЛГА" in brand_raw or "VOL" in brand_raw: brand = "VOLGA"
        elif "GAC" in brand_raw or "ГАК" in brand_raw: brand = "GAC"
        elif "UMO" in brand_raw or "УМО" in brand_raw: brand = "UMO"
        elif "CHANGAN" in brand_raw or "ЧАНГАН" in brand_raw or "CHAN" in brand_raw: brand = "CHANGAN"
                
        if brand in MARKET_DATABASE_SPB:
            model_clean = model_raw.replace(" ", "").replace("-", "")
            # Ищем сначала сложные индексы (типа GS8 II FL, а не просто GS8)
            sorted_known_models = sorted(MARKET_DATABASE_SPB[brand].keys(), key=len, reverse=True)
            for known_model in sorted_known_models:
                known_clean = known_model.replace(" ", "").replace("-", "")
                if known_clean in model_clean:
                    model = known_model
                    break
        
        try: days_on_stock = int(float(str(row.get('Dni', 0)).replace('дн', '').strip()))
        except: days_on_stock = 0
        try: current_price = float(str(row.get('Price', 0)).replace(' ', '').replace(',', ''))
        except: current_price = 0
        try: min_price = float(str(row.get('MinPrice', 0)).replace(' ', '').replace(',', ''))
        except: min_price = current_price * 0.95
        
        comp_price = MARKET_DATABASE_SPB.get(brand, {}).get(model, None)
        
        if comp_price and current_price > 0:
            diff = current_price - comp_price
            
            # НОВАЯ КОРРЕКТНАЯ ЛОГИКА АНАЛИЗА
            # Сценарий 1: Критический склад (>100 дней) независимо от цены
            if days_on_stock >= 100:
                has_overaged = True
                suggested_price = max(comp_price - 30000, min_price)
                status_text, status_style = "КРИТИЧЕСКИЙ СТОК", "color: red; font-weight: bold;"
                if diff > 0:
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Мы дороже рынка СПб на {diff:,} ₽. Требуется снизить цену до **{suggested_price:,} ₽**."
                else:
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Цена в рынке, но машина зависла. Выделить скрытый бонус менеджерам +40 000 ₽."
            
            # Сценарий 2: Завышенная цена (Превышение рынка более чем на 50 000 руб), даже если склад свежий!
            elif diff > 50000:
                suggested_price = max(comp_price, min_price)
                status_text, status_style = "ЗАВЫШЕНА ЦЕНА", "color: orange; font-weight: bold;"
                rec_text = f"⚠️ **Завышена цена рынка!** Автомобиль стоит всего {days_on_stock} дн., но мы дороже конкурентов в СПб на {diff:,} ₽ (Рынок: {comp_price:,} ₽). Рекомендуем снизить до **{suggested_price:,} ₽**, иначе машина зависнет."
            
            # Сценарий 3: Зависание склада по времени (45-100 дней) при нормальной цене
            elif days_on_stock > 45:
                status_text, status_style = "ЗАВИСАНИЕ ПО ВРЕМЕНИ", "color: orange;"
                rec_text = f"⚠️ **Зависание стока ({days_on_stock} дн.).** Цена соответствует рынку СПб ({comp_price:,} ₽), но оборачиваемость падает. Согласуйте локальный подарок клиенту."
            
            # Сценарий 4: Свежий склад и нормальная цена
            else:
                status_text, status_style = "СВЕЖИЙ СТОК", "color: green;"
                rec_text = f"🟢 **Свежий склад ({days_on_stock} дн.).** Цена полностью соответствует рыночному позиционированию комплектации в СПб ({comp_price:,} ₽)."
        else:
            status_text, status_style = "НЕТ ДАННЫХ", "color: black;"
            rec_text = f"⚪ Модель {brand_raw} {model_raw} принята. Требуется расширение базы."
            
        st.markdown(f"• **{brand_raw} {model_raw}** ➔ {rec_text}")
        
        row_html = f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{brand_raw} {model_raw}</b></td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{days_on_stock}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{current_price:,.0f} ₽</td>
            <td style="padding: 8px; border: 1px solid #ddd; {status_style}">{status_text}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{rec_text}</td>
        </tr>
        """
        
        if brand == "VOLGA": rop_groups["VOLGA"].append(row_html)
        elif brand in ["GAC", "UMO"]: rop_groups["GAC_UMO"].append(row_html)
        else: rop_groups["CHANGAN"].append(row_html)
            
    if has_overaged:
        st.error("🚨 ВНИМАНИЕ ДИРЕКТОРА: НА СКЛАДЕ ОБНАРУЖЕНЫ АВТОМОБИЛИ С КРИТИЧЕСКИМ СРОКОМ ХРАНЕНИЯ (>100 ДНЕЙ)!")
        
    st.write("---")
    st.write("### 🖨️ Шаг 4: Выдача индивидуальных заданий РОПам")
    
    def make_html_report(manager_title, rows):
        if not rows: return "<p style='padding:20px; text-align:center; color:gray;'>В загруженном файле нет автомобилей для данного отдела.</p>"
        return f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; background-color: white; color: black; border: 2px solid #333; border-radius: 5px;">
            <h2 style="text-align: center; margin-bottom: 5px; color: black;">ПОЛУЧАТЕЛЬ: {manager_title}</h2>
            <h3 style="text-align: center; margin-top: 0; color: #555;">РАСПОРЯЖЕНИЕ ПО КОРРЕКТИРОВКЕ ЦЕН И СТОКА ДЦ</h3>
            <p style="text-align: center; font-size: 13px; color: #666;">Дата: {datetime.now().strftime('%d.%m.%Y')} | Регион: Санкт-Петербург</p>
            <hr style="border: 1px solid #333;">
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; color: black;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #333; text-align: left;">Автомобиль</th>
                        <th style="padding: 8px; border: 1px solid #333; text-align: center;">Дней стока</th>
                        <th style="padding: 8px; border: 1px solid #333; text-align: right;">Цена 1С</th>
                        <th style="padding: 8px; border: 1px solid #333; text-align: left;">Статус склада</th>
                        <th style="padding: 8px; border: 1px solid #333; text-align: left;">Указание Директора (ИИ-анализ)</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
            <br><br>
            <p style="font-size: 13px; color: black;"><b>Срок исполнения поручения РОПом:</b> 24 часа. О результатах изменения витрины отчитаться.</p>
            <p style="font-size: 13px; color: black;"><b>Подпись Директора ДЦ:</b> ___________________________</p>
        </div>
        """

    tab1, tab2, tab3 = st.tabs(["📋 Лист РОПа CHANGAN", "📋 Лист РОПа GAC / UMO", "📋 Лист РОПа VOLGA"])
    with tab1: st.components.v1.html(make_html_report("РУКОВОДИТЕЛЮ ОТДЕЛА ПРОДАЖ CHANGAN", rop_groups["CHANGAN"]), height=500, scrolling=True)
    with tab2: st.components.v1.html(make_html_report("РУКОВОДИТЕЛЮ ОТДЕЛА ПРОДАЖ GAC / UMO", rop_groups["GAC_UMO"]), height=500, scrolling=True)
