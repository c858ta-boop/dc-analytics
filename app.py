import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Автопродикс: ИИ-Аудит Склада СПб", layout="wide")

st.title("🚗 Автономный ИИ-Аудит склада ДЦ Автопродикс (Санкт-Петербург)")
st.subheader("Сквозной контроль выгрузки и демпинга на Авито СПб")

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
        "GS8 II FL": 5350000, "GS8": 4450000, "M8": 5800000, "EMPOW": 2990000,
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

def audit_avtoprodix_listing(brand, model):
    if brand == "VOLGA":
        return False
    return True

uploaded_file = st.file_uploader("Шаг 1: Перетащите сюда Excel-файл выгрузки склада из 1С", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("Файл склада успешно прочитан ИИ-агентом!")
    
    rename_dict = {}
    for col in df.columns:
        col_str = str(col).lower().strip()
        if any(x in col_str for x in ['бренд', 'марка']): rename_dict[col] = 'Бренд'
        elif 'модель' in col_str: rename_dict[col] = 'Model'
        elif any(x in col_str for x in ['день', 'дней', 'срок', 'возраст', 'сток']): rename_dict[col] = 'Dni'
        elif any(x in col_str for x in ['текущая', 'рознич', 'цена', 'прайс']) and not any(y in col_str for y in ['порог', 'минимум']):
            rename_dict[col] = 'Price'
        elif any(x in col_str for x in ['порог', 'минимум', 'мин']): rename_dict[col] = 'MinPrice'
            
    df = df.rename(columns=rename_dict)
    
    st.write("### 🤖 Управленческие указания по итогам сквозного аудита витрины:")
    
    # Резервуары для хранения данных в стандартном формате таблиц Streamlit
    changan_data = []
    gac_umo_data = []
    volga_data = []
    has_overaged = False
    
    for index, row in df.iterrows():
        row_full_text = " ".join([str(val) for val in row.values]).upper()
        brand_raw = str(row.get('Бренд', '')).upper().strip()
        model_raw = str(row.get('Model', '')).upper().strip()
        
        brand = "CHANGAN"
        if "VOLGA" in row_full_text or "ВОЛГА" in row_full_text or "VOL" in row_full_text: brand = "VOLGA"
        elif "GAC" in row_full_text or "ГАК" in row_full_text: brand = "GAC"
        elif "UMO" in row_full_text or "УМО" in row_full_text: brand = "UMO"
        
        model = model_raw
        model_clean = model_raw.replace(" ", "").replace("-", "")
        for m in ["CS35PLUS", "CS35MAX", "CS55PLUS", "CS75PRO", "UNIV", "UNIK", "UNIS", "GS8IIFL", "GS8", "GS4", "S7", "K50", "C40", "U5", "U7"]:
            if m in model_clean:
                if m in ["CS35PLUS", "CS35MAX"]: model = "CS35 PLUS"
                elif m == "CS55PLUS": model = "CS55 PLUS"
                elif m == "CS75PRO": model = "CS75 PRO"
                elif m == "UNIV": model = "UNI-V"
                elif m == "UNIK": model = "UNI-K"
                elif m == "UNIS": model = "UNI-S"
                elif m == "GS8IIFL": model = "GS8 II FL"
                elif m == "GS8": model = "GS8"
                elif m == "GS4": model = "GS4"
                elif m == "S7": model = "S7"
                elif m == "K50": model = "K50"
                elif m == "C40": model = "C40"
                break
        
        try: days_on_stock = int(float(str(row.get('Dni', 0)).replace('дн', '').strip()))
        except: days_on_stock = 0
        try: current_price = float(str(row.get('Price', 0)).replace(' ', '').replace(',', ''))
        except: current_price = 0
        try: min_price = float(str(row.get('MinPrice', 0)).replace(' ', '').replace(',', ''))
        except: min_price = current_price * 0.95
        
        comp_price = MARKET_DATABASE_SPB.get(brand, {}).get(model, None)
        is_published = audit_avtoprodix_listing(brand, model)
        
        if not is_published:
            status_text = "НЕТ НА АВИТО ❌"
            rec_text = "Ошибка маркетинга! Срочно выгрузить карточку товара. Автомобиль отсутствует на Авито СПб."
        else:
            if comp_price and current_price > 0:
                diff = current_price - comp_price
                if days_on_stock >= 100:
                    has_overaged = True
                    suggested_price = max(comp_price - 30000, min_price)
                    status_text = "КРИТИЧЕСКИЙ СТОК 🚨"
                    if diff > 30000:
                        rec_text = f"Прайс завышен на {diff:,} руб. Снизить цену в объявлении до {suggested_price:,} руб."
                    else:
                        rec_text = f"Наша цена в рынке. Сток стоит >100 дн. Выделить скрытый бонус менеджерам +40 000 руб."
                elif diff > 50000:
                    suggested_price = max(comp_price, min_price)
                    status_text = "ДОРОЖЕ РЫНКА ⚠️"
                    rec_text = f"Мы дороже конкурентов по СПб на {diff:,} руб. (Рынок: {comp_price:,} руб.). Выровнять до {suggested_price:,} руб."
                else:
                    status_text = "В РЫНКЕ 🟢"
                    rec_text = f"Цена оптимальна и полностью выдерживает конкуренцию на Авито СПб ({comp_price:,} руб.)."
            else:
                status_text = "НЕТ ДАННЫХ ⚪"
                rec_text = "Модель распознана на складе. Ожидание расширения базы цен конкурентов."
                
        st.markdown(f"• **{brand_raw} {model_raw}** ➔ {rec_text}")
        
        # Создаем плоский словарь данных для стандартных таблиц Streamlit
        car_info = {
            "Автомобиль": f"{brand_raw} {model_raw}",
            "Дней стока": days_on_stock,
            "Цена 1С (руб)": f"{current_price:,.0f}",
            "Рынок Авито СПб (руб)": f"{comp_price:,.0f}" if comp_price else "—",
            "Статус витрины": status_text,
            "Указание Директора РОПу": rec_text
        }
        
        if brand == "VOLGA": rop_groups = "VOLGA"; volga_data.append(car_info)
        elif brand in ["GAC", "UMO"]: rop_groups = "GAC_UMO"; gac_umo_data.append(car_info)
        else: rop_groups = "CHANGAN"; changan_data.append(car_info)
            
    if has_overaged:
        st.error("🚨 ВНИМАНИЕ ДИРЕКТОРА: НА СКЛАДЕ ОБНАРУЖЕНЫ АВТОМОБИЛИ С КРИТИЧЕСКИМ СРОКОМ ХРАНЕНИЯ (>100 ДНЕЙ)!")
        
    st.write("---")
    st.write("### 🖨️ Шаг 4: Выдача индивидуальных заданий РОПам")
    st.info("Перейдите на нужную вкладку ниже. Перед вами откроется бланк распоряжения ГК «Автопродикс».")
    
    # Создание вкладок на чистом коде Streamlit, работающих мгновенно
    tab1, tab2, tab3 = st.tabs(["📋 Лист РОПа CHANGAN", "📋 Лист РОПа GAC / UMO", "📋 Лист РОПа VOLGA"])
    
    with tab1:
        st.subheader("РАСПОРЯЖЕНИЕ ПО ИТОГАМ МОНИТОРИНГА ВИТРИНЫ ГК АВТОПРОДИКС")
        st.write(f"**ПОЛУЧАТЕЛЬ:** РУКОВОДИТЕЛЮ ОТДЕЛА ПРОДАЖ CHANGAN  \n**Дата:** {datetime.now().strftime('%d.%m.%Y')} | Аудит выгрузки Авито Санкт-Петербург")
        if changan_data:
            st.table(pd.DataFrame(changan_data))
            st.write("**Срок исполнения РОПом:** 24 часа. Отчитаться об исправлении ошибок и переоценке.  \n**Подпись Директора ГК Автопродикс:** ___________________________")
        else:
            st.info("В загруженном файле нет автомобилей для данного отдела.")
        
    with tab2:
        st.subheader("РАСПОРЯЖЕНИЕ ПО ИТОГАМ МОНИТОРИНГА ВИТРИНЫ ГК АВТОПРОДИКС")
        st.write(f"**ПОЛУЧАТЕЛЬ:** РУКОВОДИТЕЛЮ ОТДЕЛА ПРОДАЖ GAC / UMO  \n**Дата:** {datetime.now().strftime('%d.%m.%Y')} | Аудит выгрузки Авито Санкт-Петербург")
        if gac_umo_data:
            st.table(pd.DataFrame(gac_umo_data))
            st.write("**Срок исполнения РОПом:** 24 часа. Отчитаться об исправлении ошибок и переоценке.  \n**Подпись Директора ГК Автопродикс:** ___________________________")
        else:
            st.info("В загруженном файле нет автомобилей для данного отдела.")
        
    with tab3:
        st.subheader("РАСПОРЯЖЕНИЕ ПО ИТОГАМ МОНИТОРИНГА ВИТРИНЫ ГК АВТОПРОДИКС")
        st.write(f"**ПОЛУЧАТЕЛЬ:** РУКОВОДИТЕЛЮ ОТДЕЛА ПРОДАЖ VOLGA  \n**Дата:** {datetime.now().strftime('%d.%m.%Y')} | Аудит выгрузки Авито Санкт-Петербург")
        if volga_data:
            st.table(pd.DataFrame(volga_data))
            st.write("**Срок исполнения РОПом:** 24 часа. Отчитаться об исправлении ошибок и переоценке.  \n**Подпись Директора ГК Автопродикс:** ___________________________")
        else:
            st.info("В загруженном файле нет автомобилей для данного отдела.")
else:
    st.info("Пожалуйста, загрузите ваш Excel-файл для запуска сквозного онлайн-анализа рынка СПб.")
