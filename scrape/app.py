import streamlit as st
import subprocess
import os
import json
import pandas as pd
import io
import base64

def run_scrapy_spider(spider_name):
    project_path = "scrape/scrape/scrape/spiders"
    subprocess.run(["scrapy", "crawl", spider_name], cwd=project_path)
def load_and_display_data(data_path):
    if os.path.exists(data_path):
        with open(data_path, 'r') as file:
            data = json.load(file)
        st.write("Scraped Data:")
        st.write(pd.DataFrame(data))
        return data
    else:
        st.write("No data available. Please run the spider first.")
st.title("Web Scraping with Scrapy")
selected_spider = st.selectbox("Select a Spider to Run", ["bina_az", "turbo_az"])
if st.button(f"Run {selected_spider.capitalize()} Spider"):
    run_scrapy_spider(selected_spider)
    st.write(f"{selected_spider.capitalize()} Spider has been run. Please reload the page to see the scraped data.")

data_path = f"scrape/scrape/scrape/spiders/{selected_spider}_output.json"
scraped_data = load_and_display_data(data_path)

def get_table_download_link(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    xlsx_data = output.getvalue()
    b64 = base64.b64encode(xlsx_data).decode()
    href = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}'
    return href

if st.button("Download as XLSX"):
    if scraped_data:
        df = pd.DataFrame(scraped_data)
        download_location = st.file_uploader("Choose a download location", type=["xlsx"], key="download_location")
        if download_location:
            xlsx_data = get_table_download_link(df)

            with open(download_location.name, 'wb') as file:
                file.write(base64.b64decode(xlsx_data.split(",")[1]))
            st.write(f"Downloaded XLSX file to: {download_location.name}")
