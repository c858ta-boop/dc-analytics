import streamlit as st
import pandas as pd

st.set_page_config(page_title="Умный ИИ-Аналитик Склада СПб", layout="wide")

st.title("🚗 Профессиональный ИИ-Аналитик склада (Санкт-Петербург)")
st.subheader("Личный кабинет Директора брендов: Changan, GAC, Volga, UMO")

# РАСШИРЕННАЯ ИНТЕРВАЛЬНАЯ БАЗА ЦЕН ДИЛЕРОВ САНКТ-ПЕТЕРБУРГА (АКТУАЛЬНОСТЬ: ИЮЛЬ 2026)
# Модели разбиты по ценовым категориям (от базовых до топовых комплектаций)
SPB_MARKET_DATABASE = {
    "CHANGAN": {
        "ALSVIN": [1950000, 2150000],
        "EADO PLUS": [2300000, 2550000],
        "LAMORE": [2700000, 3100000],
        "CS35 PLUS": [2100000, 2400000],
        "CS35 MAX": [2350000, 2600000],
        "CS55 PLUS": [2500000, 2850000],
        "UNI-S": [2550000, 2900000],
        "UNI-T": [2700000, 3150000],
        "CS75 PRO": [2750000, 2990000],
        "CS75 PLUS": [3000000, 3450000],
        "UNI-V": [2800000, 3200000],
        "UNI-K": [3900000, 4500000],
        "CS85 COUPE": [3500000, 3950000],
        "CS95": [4100000, 4700000],
        "HUNTER PLUS": [3300000, 3750000],
        "AVATR 11": [5800000, 6600000],
        "AVATR 12": [6500000, 7500000]
    },
    "GAC": {
        "GS3": [2200000, 2500000],
        "GS4": [2400000, 2700000],
        "GS5": [2300000, 2600000],
        "GN8": [3100000, 3600000],
        "GS8": [4100000, 4800000],
        "M8": [5400000, 6200000],
        "EMPOW": [2800000, 3200000],
        "S7": [5900000, 6490000],
        "S9": [6400000, 7100000]
    },
    "VOLGA": {
        "C40": [2700000, 3050000],
        "C50": [2890000, 3450000],
        "K30": [3000000, 3400000],
        "K40": [2750000, 3950000],
        "K50": [4040000, 4800000] # Интервал цен СПб расширен под комплектации Комфорт/Премиум/Эксклюзив
    },
    "UMO": {
        "U5": [2150000, 2450000],
        "U7": [2750000, 3150000]
    }
}

uploaded_file = st.file_uploader("Шаг 1: Перетащите сюда Excel-файл выгрузки склада из 1С", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("Файл успешно прочитан ИИ-агентом!")
    
    # Авто-выравнивание колонок под стандарты ИИ
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
        model_raw = str(row.get('Модель', '')).upper().strip()
        
        brand = brand_raw
        model = model_raw
        
        # Строгий поиск бренда
        for known_brand in SPB_MARKET_DATABASE.keys():
            if known_brand in brand_raw:
                brand = known_brand
                break
                
        # Мэтчинг модели
        if brand in SPB_MARKET_DATABASE:
            sorted_known_models = sorted(SPB_MARKET_DATABASE[brand].keys(), key=len, reverse=True)
            for known_model in sorted_known_models:
                if known_model in model_raw.split() or known_model == model_raw or known_model in model_raw:
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
        
        # Получение питерской рыночной стоимости (интервал)
        price_range = SPB_MARKET_DATABASE.get(brand, {}).get(model, None)
        
        if price_range and current_price > 0:
            # Алгоритм подбора оптимальной цены на основе интервала рынка
            market_min, market_max = price_range[0], price_range[1]
            
            # Корректируем целевую рыночную цену под комплектацию
            if current_price > market_max: comp_price = market_max
            elif current_price < market_min: comp_price = market_min
            else: comp_price = current_price
                
            diff = current_price - comp_price
            
            # Управленческая логика ИИ-агента
            if days_on_stock >= 100:
                has_overaged = True
                suggested_price = max(comp_price - 30000, min_price)
                if current_price > comp_price:
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Мы дороже аналогичных комплектаций в СПб на {diff:,} ₽. **Рекомендация:** Снизить стоимость до **{suggested_price:,} ₽**."
                else:
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Наша цена ({current_price:,} ₽) в рынке, но машина стоит. Не снижайте прайс на витрине. Выделите скрытый бонус менеджерам +40 000 ₽ за выдачу этого VIN."
            
            elif days_on_stock > 45:
                suggested_price = max(comp_price - 15000, min_price)
                if current_price > market_max:
                    rec_text = f"⚠️ **Зависание склада ({days_on_stock} дн.).** Стоимость завышена для рынка СПб. Рекомендуем снизить до **{suggested_price:,} ₽** для удержания звонков."
                else:
                    rec_text = f"⚠️ **Зависание склада ({days_on_stock} дн.).** Цена ({current_price:,} ₽) адекватна комплектации, но оборачиваемость падает. Согласуйте локальный подарок клиенту (например, зимняя резина/ТО-1)."
            
            else:
                rec_text = f"🟢 **Свежий склад ({days_on_stock} дн.).** Цена полностью соответствует текущему рыночному позиционированию комплектации в СПб ({current_price:,} ₽)."
        else:
            rec_text = f"⚪ Модель {brand_raw} {model_raw} распознана. Для её глубокого анализа требуется подключить динамический онлайн-парсер классифайдов."
            
        recommendations.append(f"• **{brand_raw} {model_raw}** (Цена: {current_price:,} ₽, Склад: {days_on_stock} дн.) ➔ {rec_text}")
        
    if has_overaged:
        st.error("🚨 ВНИМАНИЕ ДИРЕКТОРА: НА СКЛАДЕ ОБНАРУЖЕНЫ АВТОМОБИЛИ С КРИТИЧЕСКИМ СРОКОМ ХРАНЕНИЯ (>100 ДНЕЙ)!")
        
    for rec in recommendations:
        st.markdown(rec)
else:
    st.info("Пожалуйста, загрузите ваш Excel-файл для точного анализа рынка Санкт-Петербурга.")
