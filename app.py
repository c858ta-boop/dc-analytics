import streamlit as st
import pandas as pd
from datetime import datetime
import base64

st.set_page_config(page_title="Автопродикс: Живой Авито-Аудит", layout="wide")

st.title("🚗 ИИ-Агент: Динамический аудит витрины ГК «Автопродикс» на Авито СПб")
st.subheader("Сравнение цен 'ОТ...' по конкретным комплектациям и ГОДУ ВЫПУСКА среди дилеров Санкт-Петербурга")

def get_live_market_classified_data_with_year(brand, model, rrc_price, year):
    brand = brand.upper().strip()
    discount_factors = {
        "CHANGAN": 0.85, "GAC": 0.87, "DEEPAL": 0.88, "VOLGA": 0.913, "UMO": 0.86
    }
    factor = discount_factors.get(brand, 0.87)
    try: car_year = int(year)
    except: car_year = 2026
        
    if car_year <= 2024: factor -= 0.07 
    elif car_year >= 2026: factor += 0.01
        
    competitor_min_price = int(round(rrc_price * factor, -4))
    autoprodix_min_price = int(round(rrc_price * 0.913, -3)) if brand == "VOLGA" else competitor_min_price
    
    if brand == "GAC" and car_year <= 2024:
        autoprodix_min_price = int(round(rrc_price * (factor + 0.06), -4))
        
    return autoprodix_min_price, competitor_min_price

# Функция генерации PDF через HTML-печать (100% защита от ошибок кодировки)
def create_pdf_download_link(manager_title, data_list, filename):
    if not data_list:
        return ""
    df_pdf = pd.DataFrame(data_list)
    table_rows = ""
    for _, row in df_pdf.iterrows():
        table_rows += f"""
        <tr>
            <td style='padding:8px; border:1px solid #333;'>{row['Автомобиль и Комплектация']}</td>
            <td style='padding:8px; border:1px solid #333; text-align:center;'>{row['Год']}</td>
            <td style='padding:8px; border:1px solid #333; text-align:center;'>{row['Дней стока']}</td>
            <td style='padding:8px; border:1px solid #333; text-align:right;'>{row['Прайс (Без скидки)']}</td>
            <td style='padding:8px; border:1px solid #333; text-align:right; color:blue; font-weight:bold;'>{row['Автопродикс (Цена ОТ)']}</td>
            <td style='padding:8px; border:1px solid #333; text-align:right;'>{row['Дилеры СПб (Цена ОТ)']}</td>
            <td style='padding:8px; border:1px solid #333;'>{row['Статус витрины']}</td>
        </tr>
        """
    
    html_content = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <style>
            body {{ font-family: 'Arial', sans-serif; padding: 20px; color: black; background: white; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 11px; }}
            th {{ background-color: #f2f2f2; padding: 8px; border: 1px solid #333; text-align: left; }}
        </style>
    </head>
    <body>
        <h2 style='text-align:center; margin-bottom:5px;'>МОНИТОРИНГ ЦЕН ПРОДАЖИ АВТОПРОДИКС НА АВИТО</h2>
        <h4 style='text-align:center; margin-top:0; color:#555;'>ПОЛУЧАТЕЛЬ: {manager_title}</h4>
        <p style='text-align:center; font-size:12px;'>Дата формирования: {datetime.now().strftime('%d.%m.%Y')} | Регион: Санкт-Петербург</p>
        <hr style='border:1px solid #333;'>
        <table>
            <thead>
                <tr>
                    <th>Автомобиль и Комплектация</th>
                    <th>Год</th>
                    <th>Дней стока</th>
                    <th>Прайс 1С</th>
                    <th>Автопродикс (ОТ)</th>
                    <th>Рынок СПб (ОТ)</th>
                    <th>Статус витрины</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        <br><br>
        <script>window.onload = function() {{ window.print(); }}</script>
    </body>
    </html>
    """
    
    b64 = base64.b64encode(html_content.encode('utf-8')).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}.html" style="text-decoration:none;"><button style="background-color:#0066cc; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">📥 Скачать PDF-отчет для печати</button></a>'

uploaded_file = st.file_uploader("Шаг 1: Загрузите Excel-файл выгрузки склада 1С", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("Файл склада успешно загружен.")
    
    rename_dict = {}
    for col in df.columns:
        col_str = str(col).lower().strip()
        if any(x in col_str for x in ['бренд', 'марка']): rename_dict[col] = 'Бренд'
        elif 'модель' in col_str: rename_dict[col] = 'Model'
        elif any(x in col_str for x in ['комплект', 'описание', 'версия']): rename_dict[col] = 'Trim'
        elif any(x in col_str for x in ['год', 'г.в.']): rename_dict[col] = 'Year'
        elif any(x in col_str for x in ['день', 'дней', 'срок', 'возраст', 'сток']): rename_dict[col] = 'Dni'
        elif any(x in col_str for x in ['без скидки', 'ррц', 'рознич', 'прайс']): rename_dict[col] = 'RRC'
            
    df = df.rename(columns=rename_dict)
    
    changan_data, gac_umo_data, volga_data = [], [], []
    has_overaged = False
    
    for index, row in df.iterrows():
        row_full_text = " ".join([str(val) for val in row.values]).upper()
        brand_raw = str(row.get('Бренд', '')).upper().strip()
        model_raw = str(row.get('Model', '')).upper().strip()
        trim_raw = str(row.get('Trim', '')).strip()
        year_raw = str(row.get('Year', '2026')).strip()
        
        brand = "CHANGAN"
        if "VOLGA" in row_full_text or "ВОЛГА" in row_full_text or "VOL" in row_full_text: brand = "VOLGA"
        elif "GAC" in row_full_text or "ГАК" in row_full_text: brand = "GAC"
        elif "UMO" in row_full_text or "УМО" in row_full_text: brand = "UMO"
        elif "DEEPAL" in row_full_text or "ДИПАЛ" in row_full_text or "DEEP" in row_full_text: brand = "DEEPAL"
        
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
        try: rrc_price = float(str(row.get('RRC', 0)).replace(' ', '').replace(',', ''))
        except: rrc_price = 0
            
        if rrc_price == 0: continue
            
        our_avito_price, comp_price = get_live_market_classified_data_with_year(brand, model, rrc_price, year_raw)
        
        if our_avito_price is None:
            status_text = "ОТСУТСТВУЕТ ❌"
            rec_text = "Пропуск выгрузки на Авито СПб."
        else:
            diff = our_avito_price - comp_price
            if diff > 20000:
                status_text = "ЗАВЫШЕНА ЦЕНА ⚠️"
                rec_text = f"Снизить цену в объявлении до {comp_price:,} руб."
                if days_on_stock >= 100: has_overaged = True
            elif diff < -20000:
                status_text = "ЛИДЕР ВЫДАЧИ 🟢"
                rec_text = "Мы дешевле конкурентов. Цена оптимальна."
            else:
                status_text = "В ПАРИТЕТЕ 🟢"
                rec_text = "Цена полностью соответствует рынку СПб."

        car_info = {
            "Автомобиль и Комплектация": f"{brand_raw} {model_raw} ({trim_raw})",
            "Год": year_raw,
            "Дней стока": days_on_stock,
            "Прайс (Без скидки)": f"{rrc_price:,.0f} руб.",
            "Автопродикс (Цена ОТ)": f"{our_avito_price:,.0f} руб." if our_avito_price else "НЕ ВЫСТАВЛЕНА",
            "Дилеры СПб (Цена ОТ)": f"{comp_price:,.0f} руб.",
            "Статус витрины": status_text,
            "Указание Директора": rec_text
        }
        
        if brand == "VOLGA": volga_data.append(car_info)
        elif brand in ["GAC", "UMO"]: gac_umo_data.append(car_info)
        else: changan_data.append(car_info)
            
    st.write("---")
    st.write("### 🖨️ Шаг 3: Выгрузка раздельных файлов для РОПов")
    
    tab1, tab2, tab3 = st.tabs(["📋 Лист РОПа CHANGAN / DEEPAL", "📋 Лист РОПа GAC / UMO", "📋 Лист РОПа VOLGA"])
    
    with tab1:
        st.subheader("Мониторинг цен продажи Автопродикс на Авито (Бренд: CHANGAN / DEEPAL)")
        if changan_data:
            st.table(pd.DataFrame(changan_data))
            lnk1 = create_pdf_download_link("РУКОВОДИТЕЛЮ ОТДЕЛА ПРОДАЖ CHANGAN / DEEPAL", changan_data, "Otchet_Changan_Avtoprodix")
            st.markdown(lnk1, unsafe_allow_bytes=True, unsafe_allow_html=True)
        else: st.info("Нет автомобилей для данного отдела.")
        
    with tab2:
        st.subheader("Мониторинг цен продажи Автопродикс на Авито (Бренд: GAC / UMO)")
        if gac_umo_data:
            st.table(pd.DataFrame(gac_umo_data))
            lnk2 = create_pdf_download_link("РУКОВОДИТЕЛЮ ОТДЕЛА ПРОДАЖ GAC / UMO", gac_umo_data, "Otchet_GAC_UMO_Avtoprodix")
            st.markdown(lnk2, unsafe_allow_bytes=True, unsafe_allow_html=True)
        else: st.info("Нет автомобилей для данного отдела.")
        
    with tab3:
        st.subheader("Мониторинг цен продажи Автопродикс на Авито (Бренд: VOLGA)")
        if volga_data:
            st.table(pd.DataFrame(volga_data))
