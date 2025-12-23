"""
Masinlar.az Data Analysis and Chart Generation Script
Analyzes car listing data and generates visualizations
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
from collections import Counter

# Set style for all plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create charts directory if not exists
CHARTS_DIR = 'charts'
os.makedirs(CHARTS_DIR, exist_ok=True)

def load_data():
    """Load the most recent CSV file"""
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'masinlar_az' in f]
    if not csv_files:
        raise FileNotFoundError("No masinlar_az CSV files found")

    # Get the most recent file
    latest_file = sorted(csv_files)[-1]
    print(f"Loading data from: {latest_file}")

    df = pd.read_csv(latest_file)
    return df

def clean_price(price_str):
    """Extract numeric price from string like '17 400 Azn'"""
    if pd.isna(price_str):
        return None
    match = re.search(r'([\d\s]+)', str(price_str).replace(' ', ''))
    if match:
        try:
            return int(match.group(1).replace(' ', ''))
        except:
            return None
    return None

def preprocess_data(df):
    """Clean and preprocess the data"""
    # Clean price column
    df['price_numeric'] = df['price'].apply(clean_price)

    # Clean year column
    df['year_numeric'] = pd.to_numeric(df['year'], errors='coerce')

    # Clean mileage column
    df['mileage_numeric'] = pd.to_numeric(df['mileage'], errors='coerce')

    # Clean engine size
    df['engine_numeric'] = pd.to_numeric(df['engine_size'], errors='coerce')

    # Extract city from contact_person
    def extract_city(contact):
        if pd.isna(contact):
            return 'Unknown'
        cities = ['Bakı', 'Sumqayıt', 'Gəncə', 'Xaçmaz', 'Şirvan', 'Ağdaş', 'Qazax', 'Sabirabad', 'Xırdalan']
        for city in cities:
            if city in str(contact):
                return city
        return 'Digər'

    df['city'] = df['contact_person'].apply(extract_city)

    return df

def generate_brand_distribution(df):
    """Generate top brands bar chart"""
    brand_counts = df['brand'].value_counts().head(15)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(brand_counts)), brand_counts.values, color=sns.color_palette("husl", len(brand_counts)))
    ax.set_xticks(range(len(brand_counts)))
    ax.set_xticklabels(brand_counts.index, rotation=45, ha='right')
    ax.set_xlabel('Brand')
    ax.set_ylabel('Number of Listings')
    ax.set_title('Top 15 Car Brands by Number of Listings')

    # Add value labels on bars
    for bar, val in zip(bars, brand_counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(val), ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/brand_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: brand_distribution.png")
    return brand_counts

def generate_price_distribution(df):
    """Generate price distribution histogram"""
    price_data = df['price_numeric'].dropna()
    price_data = price_data[(price_data > 0) & (price_data < 200000)]  # Filter outliers

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(price_data, bins=30, color='steelblue', edgecolor='white', alpha=0.7)
    ax.axvline(price_data.median(), color='red', linestyle='--', linewidth=2, label=f'Median: {price_data.median():,.0f} AZN')
    ax.axvline(price_data.mean(), color='orange', linestyle='--', linewidth=2, label=f'Mean: {price_data.mean():,.0f} AZN')
    ax.set_xlabel('Price (AZN)')
    ax.set_ylabel('Number of Listings')
    ax.set_title('Price Distribution of Car Listings')
    ax.legend()

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/price_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: price_distribution.png")
    return price_data.describe()

def generate_year_distribution(df):
    """Generate year distribution chart"""
    year_data = df['year_numeric'].dropna()
    year_data = year_data[(year_data >= 1990) & (year_data <= 2025)]
    year_counts = year_data.value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(year_counts.index.astype(int), year_counts.values, color='teal', alpha=0.7)
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Listings')
    ax.set_title('Car Listings by Manufacturing Year')
    ax.set_xticks(range(int(year_counts.index.min()), int(year_counts.index.max())+1, 2))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/year_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: year_distribution.png")
    return year_counts

def generate_fuel_type_pie(df):
    """Generate fuel type pie chart"""
    fuel_counts = df['fuel_type'].value_counts()
    fuel_counts = fuel_counts[fuel_counts > 1]  # Filter out single entries

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = sns.color_palette("husl", len(fuel_counts))
    wedges, texts, autotexts = ax.pie(fuel_counts.values, labels=fuel_counts.index,
                                       autopct='%1.1f%%', colors=colors, startangle=90)
    ax.set_title('Distribution by Fuel Type')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/fuel_type_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: fuel_type_distribution.png")
    return fuel_counts

def generate_transmission_pie(df):
    """Generate transmission type pie chart"""
    trans_counts = df['transmission'].value_counts()
    trans_counts = trans_counts[trans_counts > 1]

    fig, ax = plt.subplots(figsize=(8, 8))
    colors = ['#2ecc71', '#3498db', '#9b59b6']
    wedges, texts, autotexts = ax.pie(trans_counts.values, labels=trans_counts.index,
                                       autopct='%1.1f%%', colors=colors[:len(trans_counts)], startangle=90)
    ax.set_title('Distribution by Transmission Type')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/transmission_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: transmission_distribution.png")
    return trans_counts

def generate_body_type_chart(df):
    """Generate body type distribution"""
    body_counts = df['body_type'].value_counts().head(10)
    body_counts = body_counts[body_counts > 1]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(body_counts)), body_counts.values, color=sns.color_palette("viridis", len(body_counts)))
    ax.set_yticks(range(len(body_counts)))
    ax.set_yticklabels(body_counts.index)
    ax.set_xlabel('Number of Listings')
    ax.set_title('Distribution by Body Type')

    for bar, val in zip(bars, body_counts.values):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                str(val), ha='left', va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/body_type_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: body_type_distribution.png")
    return body_counts

def generate_price_by_brand(df):
    """Generate average price by brand chart"""
    brand_price = df.groupby('brand')['price_numeric'].agg(['mean', 'count'])
    brand_price = brand_price[brand_price['count'] >= 2].sort_values('mean', ascending=False).head(15)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(brand_price)), brand_price['mean'].values,
                  color=sns.color_palette("coolwarm", len(brand_price)))
    ax.set_xticks(range(len(brand_price)))
    ax.set_xticklabels(brand_price.index, rotation=45, ha='right')
    ax.set_xlabel('Brand')
    ax.set_ylabel('Average Price (AZN)')
    ax.set_title('Average Price by Brand (Top 15)')

    for bar, val in zip(bars, brand_price['mean'].values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500,
                f'{val:,.0f}', ha='center', va='bottom', fontsize=9, rotation=45)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/price_by_brand.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: price_by_brand.png")
    return brand_price

def generate_price_vs_year(df):
    """Generate price vs year scatter plot"""
    data = df[['year_numeric', 'price_numeric']].dropna()
    data = data[(data['year_numeric'] >= 1990) & (data['year_numeric'] <= 2025)]
    data = data[(data['price_numeric'] > 0) & (data['price_numeric'] < 200000)]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.scatter(data['year_numeric'], data['price_numeric'], alpha=0.6, c='steelblue', s=50)

    # Add trend line
    z = np.polyfit(data['year_numeric'], data['price_numeric'], 1)
    p = np.poly1d(z)
    ax.plot(data['year_numeric'].sort_values(), p(data['year_numeric'].sort_values()),
            "r--", linewidth=2, label='Trend Line')

    ax.set_xlabel('Manufacturing Year')
    ax.set_ylabel('Price (AZN)')
    ax.set_title('Price vs Manufacturing Year')
    ax.legend()

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/price_vs_year.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: price_vs_year.png")

def generate_city_distribution(df):
    """Generate city distribution chart"""
    city_counts = df['city'].value_counts()

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(len(city_counts)), city_counts.values,
                  color=sns.color_palette("Set2", len(city_counts)))
    ax.set_xticks(range(len(city_counts)))
    ax.set_xticklabels(city_counts.index, rotation=45, ha='right')
    ax.set_xlabel('City')
    ax.set_ylabel('Number of Listings')
    ax.set_title('Listings by City')

    for bar, val in zip(bars, city_counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(val), ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/city_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: city_distribution.png")
    return city_counts

def generate_color_distribution(df):
    """Generate car color distribution"""
    color_counts = df['color'].value_counts().head(10)
    color_counts = color_counts[color_counts > 1]

    # Map Azerbaijani colors to approximate color codes
    color_map = {
        'Ağ': '#FFFFFF', 'Qara': '#2C2C2C', 'Gümüşü': '#C0C0C0',
        'Göy': '#4169E1', 'Boz': '#808080', 'Qırmızı': '#DC143C',
        'Yaşıl': '#228B22', 'Mavi': '#1E90FF', 'Bej': '#F5F5DC',
        'Yaş Asfalt': '#36454F', 'Qızılı': '#FFD700', 'Tünd qırmızı': '#8B0000'
    }

    colors = [color_map.get(c, '#888888') for c in color_counts.index]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(color_counts)), color_counts.values, color=colors, edgecolor='black')
    ax.set_yticks(range(len(color_counts)))
    ax.set_yticklabels(color_counts.index)
    ax.set_xlabel('Number of Listings')
    ax.set_title('Top 10 Car Colors')

    for bar, val in zip(bars, color_counts.values):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                str(val), ha='left', va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/color_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: color_distribution.png")
    return color_counts

def generate_mileage_distribution(df):
    """Generate mileage distribution"""
    mileage_data = df['mileage_numeric'].dropna()
    mileage_data = mileage_data[(mileage_data > 0) & (mileage_data < 500000)]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(mileage_data, bins=25, color='coral', edgecolor='white', alpha=0.7)
    ax.axvline(mileage_data.median(), color='blue', linestyle='--', linewidth=2,
               label=f'Median: {mileage_data.median():,.0f} km')
    ax.set_xlabel('Mileage (km)')
    ax.set_ylabel('Number of Listings')
    ax.set_title('Mileage Distribution')
    ax.legend()

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/mileage_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: mileage_distribution.png")
    return mileage_data.describe()

def generate_price_by_fuel(df):
    """Generate average price by fuel type"""
    fuel_price = df.groupby('fuel_type')['price_numeric'].agg(['mean', 'count'])
    fuel_price = fuel_price[fuel_price['count'] >= 2].sort_values('mean', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(fuel_price)), fuel_price['mean'].values,
                   color=sns.color_palette("RdYlGn", len(fuel_price)))
    ax.set_yticks(range(len(fuel_price)))
    ax.set_yticklabels(fuel_price.index)
    ax.set_xlabel('Average Price (AZN)')
    ax.set_title('Average Price by Fuel Type')

    for bar, val in zip(bars, fuel_price['mean'].values):
        ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
                f'{val:,.0f}', ha='left', va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/price_by_fuel.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Generated: price_by_fuel.png")
    return fuel_price

def generate_insights(df):
    """Generate key insights from the data"""
    insights = {}

    # Total listings
    insights['total_listings'] = len(df)

    # Price statistics
    price_data = df['price_numeric'].dropna()
    price_data = price_data[(price_data > 0) & (price_data < 500000)]
    insights['avg_price'] = price_data.mean()
    insights['median_price'] = price_data.median()
    insights['min_price'] = price_data.min()
    insights['max_price'] = price_data.max()

    # Top brand
    insights['top_brand'] = df['brand'].value_counts().index[0]
    insights['top_brand_count'] = df['brand'].value_counts().values[0]

    # Year statistics
    year_data = df['year_numeric'].dropna()
    insights['avg_year'] = year_data.mean()
    insights['newest_year'] = year_data.max()
    insights['oldest_year'] = year_data.min()

    # Fuel type distribution
    insights['fuel_distribution'] = df['fuel_type'].value_counts().to_dict()

    # Transmission distribution
    insights['transmission_distribution'] = df['transmission'].value_counts().to_dict()

    # Mileage statistics
    mileage_data = df['mileage_numeric'].dropna()
    mileage_data = mileage_data[(mileage_data > 0) & (mileage_data < 1000000)]
    if len(mileage_data) > 0:
        insights['avg_mileage'] = mileage_data.mean()
        insights['median_mileage'] = mileage_data.median()

    # City distribution
    insights['city_distribution'] = df['city'].value_counts().to_dict()

    # Most expensive brand
    brand_avg_price = df.groupby('brand')['price_numeric'].mean()
    insights['most_expensive_brand'] = brand_avg_price.idxmax()
    insights['most_expensive_brand_avg'] = brand_avg_price.max()

    return insights

def main():
    """Main function to generate all charts and insights"""
    import numpy as np  # Import here to avoid issues if not installed
    global np
    np = __import__('numpy')

    print("=" * 60)
    print("Masinlar.az Data Analysis")
    print("=" * 60)

    # Load and preprocess data
    df = load_data()
    df = preprocess_data(df)

    print(f"\nTotal listings: {len(df)}")
    print(f"Columns: {', '.join(df.columns)}")
    print("\n" + "=" * 60)
    print("Generating charts...")
    print("=" * 60 + "\n")

    # Generate all charts
    brand_counts = generate_brand_distribution(df)
    price_stats = generate_price_distribution(df)
    year_counts = generate_year_distribution(df)
    fuel_counts = generate_fuel_type_pie(df)
    trans_counts = generate_transmission_pie(df)
    body_counts = generate_body_type_chart(df)
    brand_price = generate_price_by_brand(df)
    generate_price_vs_year(df)
    city_counts = generate_city_distribution(df)
    color_counts = generate_color_distribution(df)
    mileage_stats = generate_mileage_distribution(df)
    fuel_price = generate_price_by_fuel(df)

    # Generate insights
    insights = generate_insights(df)

    print("\n" + "=" * 60)
    print("KEY INSIGHTS")
    print("=" * 60)
    print(f"\nTotal Listings: {insights['total_listings']}")
    print(f"\nPrice Statistics:")
    print(f"  - Average Price: {insights['avg_price']:,.0f} AZN")
    print(f"  - Median Price: {insights['median_price']:,.0f} AZN")
    print(f"  - Price Range: {insights['min_price']:,.0f} - {insights['max_price']:,.0f} AZN")
    print(f"\nTop Brand: {insights['top_brand']} ({insights['top_brand_count']} listings)")
    print(f"Most Expensive Brand: {insights['most_expensive_brand']} (Avg: {insights['most_expensive_brand_avg']:,.0f} AZN)")
    print(f"\nYear Statistics:")
    print(f"  - Average Year: {insights['avg_year']:.0f}")
    print(f"  - Range: {insights['oldest_year']:.0f} - {insights['newest_year']:.0f}")

    if 'avg_mileage' in insights:
        print(f"\nMileage Statistics:")
        print(f"  - Average: {insights['avg_mileage']:,.0f} km")
        print(f"  - Median: {insights['median_mileage']:,.0f} km")

    print("\n" + "=" * 60)
    print(f"All charts saved to '{CHARTS_DIR}/' directory")
    print("=" * 60)

    return insights

if __name__ == "__main__":
    main()
