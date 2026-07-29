import streamlit as st
import pandas as pd

st.set_page_config(page_title="Умный ИИ-Аналитик Склада СПб", layout="wide")

st.title("🚗 Профессиональный ИИ-Аналитик склада (Санкт-Петербург)")
st.subheader("Личный кабинет Директора брендов: Changan, GAC, Volga, UMO")

SPB_MARKET_DATABASE = {
    "CHANGAN": {
        "CS35 MAX": 2450000,
        "CS55 PLUS": 2650000,
        "UNI-S": 2720000,
        "CS75PRO": 2850000,
        "UNI-V": 2950000,
        "UNI-K": 4100000,
        "HUNTER PLUS": 3450000,
        "AVATR 11": 6100000
    },
    "GAC": {"GS3": 2350000, "GS8": 4350000, "M8": 5800000},
    "VOLGA": {"C40": 2850000, "K30": 3200000, "K40": 3600000},
    "UMO": {"U5": 2300000, "U7": 2900000}
}

uploaded_file = st.file_uploader("Шаг 1: Перетащите сюда Excel-файл выгрузки склада из 1С", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("Файл успешно прочитан ИИ-агентом!")
    
    # Полный список автомобильных синонимов для распознавания колонок 1С
    rename_dict = {}
    for col in df.columns:
        col_str = str(col).lower().strip()
        if any(x in col_str for x in ['бренд', 'марка', 'производитель']):
            rename_dict[col] = 'Бренд'
        elif 'модель' in col_str:
            rename_dict[col] = 'Модель'
        elif any(x in col_str for x in ['комплект', 'версия', 'модиф']):
            rename_dict[col] = 'Комплектация'
        elif any(x in col_str for x in ['день', 'дней', 'срок', 'возраст', 'сток', 'хранения', 'на складе']):
            rename_dict[col] = 'Дней на складе'
        elif any(x in col_str for x in ['текущая', 'рознич', 'цена', 'прайс', 'витрина']) and not any(y in col_str for y in ['порог', 'минимум', 'мин']):
            rename_dict[col] = 'Текущая розничная цена'
        elif any(x in col_str for x in ['порог', 'минимум', 'мин', 'закуп', 'себест']):
            rename_dict[col] = 'Минимальный порог цены'
            
    df = df.rename(columns=rename_dict)
    
    st.write("### 📊 Шаг 2: Проверка распознавания колонок ИИ-агентом:")
    st.dataframe(df, use_container_width=True)
    
    # Проверка на случай, если колонка дней склада всё равно не распозналась
    if 'Дней на складе' not in df.columns:
        st.error(f"⚠️ Ошибка: ИИ не смог найти колонку с днями склада. Доступные колонки в вашем файле: {list(df.columns)}")
        st.info("Пожалуйста, переименуйте колонку с днями склада в вашем Excel в 'Дней на складе' и загрузите файл заново.")
    
    st.write("### 🤖 Шаг 3: Точечная аналитика ИИ по рынку Санкт-Петербурга:")
    
    recommendations = []
    has_overaged = False
    
    for index, row in df.iterrows():
        brand = str(row.get('Бренд', '')).upper().strip()
        model = str(row.get('Модель', '')).upper().strip()
        
        # Очистка названия модели для мэтчинга
        for known_model in SPB_MARKET_DATABASE.get(brand, {}).keys():
            if known_model in model:
                model = known_model
                break
        
        # Надежное извлечение дней на складе с очисткой от текста и пробелов
        days_raw = row.get('Дней на складе', 0)
        try:
            if pd.isna(days_raw):
                days_on_stock = 0
            else:
                days_on_stock = int(float(str(days_raw).replace('дн.', '').replace('дн', '').strip()))
        except:
            days_on_stock = 0
            
        try: current_price = float(str(row.get('Текущая розничная цена', 0)).replace(' ', ''))
        except: current_price = 0
            
        try: min_price = float(str(row.get('Минимальный порог цены', 0)).replace(' ', ''))
        except: min_price = current_price * 0.95
        
        comp_price = SPB_MARKET_DATABASE.get(brand, {}).get(model, None)
        
        if comp_price and current_price > 0:
            diff = current_price - comp_price
            
            # Логика триггеров по дням склада
            if days_on_stock >= 100:
                has_overaged = True
                suggested_price = max(comp_price - 30000, min_price)
                if current_price > comp_price:
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Мы дороже рынка СПб на {diff:,} ₽. Конкуренты продают за {comp_price:,} ₽. **Рекомендация:** Снизить цену до **{suggested_price:,} ₽**."
                else:
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Цена в рынке ({current_price:,} ₽), но машина стоит. Не снижайте цену на сайте. Выделите менеджерам закрытый бонус +40 000 ₽ за продажу этого VIN."
            
            elif days_on_stock > 45:
                suggested_price = max(comp_price, min_price)
                if diff > 30000:
                    rec_text = f"⚠️ **Зависание склада ({days_on_stock} дн.).** Мы дороже рынка СПб. Средняя цена конкурентов: {comp_price:,} ₽. Рекомендуем скорректировать до **{suggested_price:,} ₽**."
                else:
                    rec_text = f"🟢 Склад {days_on_stock} дн. Цена оптимальна относительно конкурентов СПб ({comp_price:,} ₽). Удерживаем маржу."
            
            else:
                rec_text = f"🟢 **Свежий склад ({days_on_stock} дн.).** Цена соответствует рынку Санкт-Петербурга ({comp_price:,} ₽)."
        else:
            rec_text = f"⚪ Модель {brand} {model} распознана. Для анализа требуются данные по цене конкурентов."
            
        recommendations.append(f"• **{brand} {model}** (Цена: {current_price:,} ₽, Склад: {days_on_stock} дн.) ➔ {rec_text}")
        
    if has_overaged:
        st.error("🚨 ВНИМАНИЕ ДИРЕКТОРА: НА СКЛАДЕ ОБНАРУЖЕНЫ АВТОМОБИЛИ С КРИТИЧЕСКИМ СРОКОМ ХРАНЕНИЯ (>100 ДНЕЙ)!")
        
    for rec in recommendations:
        st.markdown(rec)
else:
    st.info("Пожалуйста, загрузите ваш Excel-файл для точного анализа рынка Санкт-Петербурга.")
