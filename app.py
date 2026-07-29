import streamlit as st
import pandas as pd

st.set_page_config(page_title="Аналитика Склада ДЦ СПб", layout="wide")

st.title("🚗 ИИ-Аналитик склада новых автомобилей (Санкт-Петербург)")
st.subheader("Личный кабинет Директора брендов: Changan, GAC, Volga, UMO")

# Кнопка загрузки файла
uploaded_file = st.file_uploader("Шаг 1: Перетащите сюда Excel-файл выгрузки склада из 1С", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Чтение данных из вашего Excel
    df = pd.read_excel(uploaded_file)
    st.success("Файл успешно загружен и прочитан ИИ-агентом!")
    
    st.write("### 📊 Шаг 2: Текущее состояние вашего склада:")
    st.dataframe(df, use_container_width=True)
    
    st.write("### 🤖 Шаг 3: Аналитика рынка и рекомендации ИИ-Агента (Регион: Санкт-Петербург):")
    
    # Симуляция базы данных парсера по СПб (актуально на 2026 год)
    market_prices = {
        "Changan": {"CS75PRO": 2750000, "UNI-V": 3150000, "CS35 MAX": 2720000},
        "GAC": {"GS8": 4250000, "GS3": 2350000},
        "Volga": {"C40": 2950000},
        "UMO": {"U5": 2400000}
    }
    
    recommendations = []
    has_overaged = False
    
    # ИИ начинает построчный анализ вашего файла
    for index, row in df.iterrows():
        brand = str(row.get('Бренд', '')).strip()
        model = str(row.get('Модель', '')).strip()
        days_on_stock = int(row.get('Дней на складе', 0))
        current_price = float(row.get('Текущая розничная цена', 0))
        min_price = float(row.get('Минимальный порог цены', 0))
        
        # Поиск цены конкурентов в СПб
        comp_price = market_prices.get(brand, {}).get(model, None)
        
        if comp_price:
            diff = current_price - comp_price
            
            # Логика ИИ в зависимости от дней на складе
            if days_on_stock > 100:
                has_overaged = True
                # Агрессивное снижение для зависшего склада
                suggested_price = max(comp_price - 30000, min_price)
                if suggested_price < current_price:
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Конкуренты в СПб продают за {comp_price:,} ₽. Рекомендуем агрессивное снижение цены до **{suggested_price:,} ₽** (ваш минимум: {min_price:,} ₽)."
                else:
                    rec_text = f"🚨 **Критический сток ({days_on_stock} дн.)!** Достигнут минимум цены ({min_price:,} ₽). Требуется ручное согласование дополнительной скидки РОПом за Трейд-ин."
            
            elif days_on_stock > 45:
                # Мягкое снижение для среднего склада
                suggested_price = max(comp_price, min_price)
                if diff > 0:
                    rec_text = f"⚠️ **Зависание склада ({days_on_stock} дн.).** Мы дороже рынка СПб на {diff:,} ₽. Рекомендуем выровнять цену до **{suggested_price:,} ₽**."
                else:
                    rec_text = f"🟢 Склад {days_on_stock} дн. Цена в рынке. Изменения не требуются."
            
            else:
                # Свежий склад - держим маржу
                if brand in ["Volga", "UMO"]:
                    rec_text = f"✨ **Новинка ({brand} {model}). Свежий склад.** Спрос в СПб стабильный. Рекомендуем держать цену **{current_price:,} ₽** для максимизации маржи."
                else:
                    rec_text = f"🟢 Свежий склад ({days_on_stock} дн.). Цена оптимальна."
        else:
            rec_text = f"⚪ Нет актуальных данных по конкурентам СПб для модели {brand} {model}. Цена остается прежней."
            
        recommendations.append(f"**{brand} {model}** (Текущая цена: {current_price:,} ₽) ➔ {rec_text}")
    
    # Вывод предупреждения, если есть зависший склад
    if has_overaged:
        st.error("⚠️ ОБНАРУЖЕНЫ АВТОМОБИЛИ С КРИТИЧЕСКИМ СРОКОМ ХРАНЕНИЯ (>100 ДНЕЙ)!")
    
    # Печать рекомендаций
    for rec in recommendations:
        st.markdown(rec)
else:
    st.info("Пожалуйста, загрузите ваш Excel-файл со списком автомобилей для начала анализа рынка Санкт-Петербурга.")
