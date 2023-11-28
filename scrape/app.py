import streamlit as st
import subprocess
import os
import json
import pandas as pd
import io
import base64
from threading import Thread


@st.cache_data(allow_output_mutation=True)
def run_scrapy_spider(spider_name):
    project_path = "scrape/scrape/scrape/spiders/"
    subprocess.run(["scrapy", "crawl", spider_name], cwd=project_path)


def run_spider_and_notify(spider_name):
    run_scrapy_spider(spider_name)
    st.success(
        f"{spider_name} Spider has completed. You can now download the data.")


def load_and_display_data(data_path):
    if os.path.exists(data_path):
        with open(data_path, 'r') as file:
            data = json.load(file)
        st.write("Scraped Data:")
        st.write(pd.DataFrame(data))
        return data
    else:
        st.write("No data available. Please run the spider first.")


def get_table_download_link(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    xlsx_data = output.getvalue()
    b64 = base64.b64encode(xlsx_data).decode()
    href = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}'
    return href


st.title("Web Scraping with Scrapy")
selected_spider = st.selectbox("Select a Spider to Run", [
    "bina_az",
    "turbo_az",
    "emlak_az",
    "ipoteka_az",
    "vipemlak_az",
    "birja_com",
    "arenda_az",
    "h2h_az",
    "boss_az",
    "qarabazar_az",
    "birja-in_az",
    "bul_az",
    "ucuztap_az",
    "unvan_az",
    "yeniemlak_az",
    "rahatemlak_az",
    "lalafo_az"
])

if st.button(f"Run {selected_spider} Spider"):
    st.info(f"Running {selected_spider} Spider. This may take some time...")
    run_spider_and_notify(selected_spider)

data_path = f"scrape/scrape/scrape/spiders/{selected_spider}_output.json"
scraped_data = load_and_display_data(data_path)

if st.button("Download as XLSX"):
    if scraped_data:
        df = pd.DataFrame(scraped_data)
        download_location = st.text_input(
            "Enter download location (e.g., /path/to/folder/filename.xlsx):")
        if download_location:
            xlsx_data = get_table_download_link(df)

            with open(download_location, 'wb') as file:
                file.write(base64.b64decode(xlsx_data.split(",")[1]))
            st.success(f"Downloaded XLSX file to: {download_location}")
