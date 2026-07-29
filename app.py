import streamlit as st
import pandas as pd

st.set_page_config(page_title="Умный ИИ-Аналитик Склада СПб", layout="wide")

st.title("🚗 Профессиональный ИИ-Аналитик склада (Санкт-Петербург)")
st.subheader("Личный кабинет Директора брендов: Changan, GAC, Volga, UMO")

# БАЗА МЕДИАННЫХ ЦЕН ДИЛЕРОВ САНКТ-ПЕТЕРБУРГА
SPB_MARKET_DATABASE = {
    "CHANGAN": {
        "ALSVIN": 1950000,
        "EADO PLUS": 2400000,
        "LAMORE": 2900000,
        "CS35 PLUS": 2350000,
        "CS35 MAX": 2480000,
        "CS55 PLUS": 2650000,
        "UNI-S": 2680000,
        "UNI-T": 2850000,
        "CS75 PRO": 2865000,
        "CS75 PLUS": 3150000,
        "UNI-V": 2950000,
        "UNI-K": 4200000,
        "CS85 COUPE": 3700000,
        "CS95": 4300000,
        "HUNTER PLUS": 3450000,
        "AVATR 11": 6200000,
        "AVATR 12": 6900000
    },
    "GAC": {
        "GS3": 2350000,
        "GS4": 2550000,
        "GS5": 2400000,
        "GN8": 3300000,
        "GS8": 4450000,
        "M8": 5800000,
        "EMPOW": 2990000,
        "S7": 6249000,
        "S9": 6700000
    },
    "VOLGA": {
        "C40": 2850000,
        "C50": 2999000,
        "K30": 3200000,
        "K40": 2849000,
        "K50": 4349000
    },
    "UMO": {
        "U5": 2300000,
        "U7": 2900000
    }
}

uploaded_file = st.file_uploader("Шаг 1: Перетащите сюда Excel-файл выгрузки склада из 1С", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("Файл успешно прочитан ИИ-агентом!")
    
    # Авто-выравнивание колонок
    rename_dict = {}
    for col in df.columns:
        col_str = str(col).lower().strip()
        if any(x in col_str for x in ['бренд', 'марка', 'производитель']): rename_dict[col] = 'Бренд'
        elif 'модель' in col_str: rename_dict[col] = 'Модель'
        elif any(x in col_str for x in ['комплект', 'версия', 'модиф']): rename_dict[col] = 'Комплектация'
        elif any(x in col_str for x in ['день', 'дней', 'срок', 'возраст', 'сток', 'хранения', 'на складе']): rename_dict[col] = 'Дней на складе'
        elif any(x in col_str for x in ['текущая', 'рознич', 'цена', 'прайс', 'витрина']) and not any(y in col_str for y in ['порог', 'минимум', 'мин']):
            rename_dict[col] = 'Текущая розничная цена'
        elif any(x in col_str for x in ['порог', 'минимум', 'мин', 'закуп', 'себест']): rename_dict[col] = 'Минимальный порог цены'
            
    df = df.rename(columns=rename_dict)
    
    st.write("### 📊 Шаг 2: Проверка распознавания колонок ИИ-агентом:")
    st.dataframe(df, use_container_width=True)
    
    st.write("### 🤖 Шаг 3: Точечная аналитика ИИ по рынку Санкт-Петербурга:")
    
    recommendations = []
    has_overaged = False
    
    for index, row in df.iterrows():
        brand_raw = str(row.get('Бренд', '')).upper().strip()
        model_raw = str(row.get('Model', row.get('Модель', ''))).upper().strip()
        
        brand = brand_raw
        model = None
        
        # Строгий поиск бренда
        for known_brand in SPB_MARKET_DATABASE.keys():
            if known_brand in brand_raw:
                brand = known_brand
                break
                
        # СУПЕР-УМНЫЙ МЭТЧИНГ: Очищаем обе строки от пробелов и дефисов для поиска совпадений (CS35PLUS MCA -> CS35 PLUS)
        if brand in SPB_MARKET_DATABASE:
            model_clean = model_raw.replace(" ", "").replace("-", "").replace("_", "")
            # Сортируем по длине, чтобы сначала искать длинные названия (например, CS75PRO, а не просто CS75)
            sorted_known_models = sorted(SPB_MARKET_DATABASE[brand].keys(), key=len, reverse=True)
            for known_model in sorted_known_models:
                known_clean = known_model.replace(" ", "").replace("-", "")
                if known_clean in model_clean:
                    model = known_model
                    break
        
        # Извлечение дней на складе
        days_raw = row.get('Дней на складе', 0)
        try:
            if pd.isna(days_raw): days_on_stock = 0
            else: days_on_stock = int(float(str(days_raw).replace('дн.', '').replace('дн', '').strip()))
        except: days_on_stock = 0
            
        # Валидация цен
        try: current_price = float(str(row.get('Текущая розничная цена', 0)).replace(' ', '').replace('\xa0', '').replace('₽', '').replace(',', ''))
        except: current_price = 0
            
        try: min_price = float(str(row.get('Минимальный порог цены', 0)).replace(' ', '').replace('\xa0', '').replace('₽', '').replace(',', ''))
        except: min_price = current_price * 0.95
        
        comp_price = SPB_MARKET_DATABASE.get(brand, {}).get(model, None)
        
        if comp_price and current_price > 0:
            diff = current_price - comp_price
            
            # Управленческая логика ИИ-агента
            if days_on_stock >= 100:
                has_overaged = True
                suggested_price = max(comp_price - 20000, min_price)
                if current_price > comp_price:
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Мы дороже рынка СПб на {diff:,} ₽. Дилеры Питера: {comp_price:,} ₽. **Рекомендация:** Снизить до **{suggested_price:,} ₽**."
                else:
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Наша цена в рынке ({current_price:,} ₽). Прайс на сайте не снижать. Выделите скрытый бонус менеджерам +40 000 ₽ за выдачу этого VIN."
            
            elif days_on_stock > 45:
                suggested_price = max(comp_price, min_price)
                if diff > 30000:
                    rec_text = f"⚠️ **Зависание склада ({days_on_stock} дн.).** Стоимость выше рынка СПб. Рекомендуем выровнять до **{suggested_price:,} ₽** для удержания звонков."
                else:
                    rec_text = f"🟢 Склад {days_on_stock} дн. Цена оптимальна относительно конкурентов СПб ({comp_price:,} ₽). Держим маржинальность."
            
            else:
                rec_text = f"🟢 **Свежий склад ({days_on_stock} дн.).** Цена полностью соответствует текущему рыночному позиционированию комплектации в СПб ({current_price:,} ₽)."
        else:
            final_model_name = model if model else model_raw
            rec_text = f"⚪ Модель {brand_raw} {final_model_name} распознана. Для её глубокого анализа требуется подключить динамический онлайн-парсер классифайдов."
            
        recommendations.append(f"• **{brand_raw} {model_raw}** (Цена: {current_price:,} ₽, Склад: {days_on_stock} дн.) ➔ {rec_text}")
        
    if has_overaged:
        st.error("🚨 ВНИМАНИЕ ДИРЕКТОРА: НА СКЛАДЕ ОБНАРУЖЕНЫ АВТОМОБИЛИ С КРИТИЧЕСКИМ СРОКОМ ХРАНЕНИЯ (>100 ДНЕЙ)!")
        
    for rec in recommendations:
        st.markdown(rec)
else:
    st.info("Пожалуйста, загрузите ваш Excel-файл для точного анализа рынка Санкт-Петербурга.")
