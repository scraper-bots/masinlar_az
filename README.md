---

**Table of Contents:**

- [Description](#description)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Description

The Scrapy-Streamlit Web App is a Python-based project that combines the power of Scrapy for web scraping and Streamlit for creating a user-friendly web application to view and interact with the scraped data. It allows you to run Scrapy spiders, display the scraped data in a Pandas DataFrame, and download the data in XLSX format, making web scraping tasks easy and accessible.

This web app serves as a convenient tool for users who want to scrape data from websites and visualize the results without diving into code or running complex command-line tools. You can run specific Scrapy spiders, view the data in tabular format, and download it for further analysis.

## Features

- **Spider Selection**: Choose from a list of available Scrapy spiders ("bina_az" and "turbo_az") to scrape specific websites.

- **Run Spiders**: Execute the selected Scrapy spider with a single click.

- **Data Display**: View the scraped data in a user-friendly Pandas DataFrame format.

- **Download as XLSX**: Download the scraped data as an XLSX file for further analysis.

## Prerequisites

Before using this web app, ensure you have the following prerequisites installed on your system:

- Python 3.x
- Scrapy
- Streamlit
- Pandas
- XLSXWriter (used for XLSX download feature)

## Installation

1. Clone or download this project from the GitHub repository: [https://github.com/Ismat-Samadov/scrapy_streamlit](https://github.com/Ismat-Samadov/scrapy_streamlit)

2. Navigate to the project directory in your terminal.

3. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Scrapy-Streamlit web app:

   ```bash
   streamlit run app.py
   ```

2. In the web app, select a spider ("bina_az" or "turbo_az") from the dropdown menu.

3. Click the "Run [Spider Name] Spider" button to initiate the web scraping process.

4. Once the spider has completed, you can view the scraped data in tabular format.

5. Click the "Download as XLSX" button to save the data in XLSX format.

## Project Structure

The project directory includes the following components:

- `spiders/`: Directory containing Scrapy spider scripts.
- `items.py`: Scrapy item definitions.
- `middlewares.py`: Custom Scrapy middleware (if applicable).
- `pipelines.py`: Custom Scrapy pipelines (if applicable).
- `settings.py`: Scrapy project settings.
- `scrapy.cfg`: Scrapy project configuration file.
- `app.py`: The main Streamlit web app.
- `README.md`: Project documentation.
- `requirements.txt`: List of required Python packages.

## Contributing

Feel free to contribute to this project by forking it and submitting pull requests with improvements, bug fixes, or new features. Please follow best practices and maintain clear and concise code.

---

