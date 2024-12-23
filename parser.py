import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

if not os.path.exists('data'):
    os.makedirs('data')

def get_population():
    url = "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', class_='wikitable')
    
    data = []
    count = 0
    
    for row in table.find_all('tr')[1:]:
        if count >= 50:
            break
            
        columns = row.find_all('td')
        
        if len(columns) < 2:
            continue
            
        country_column = next((col for col in columns if col.find('a', title=True)), None)
        if not country_column:
            continue
            
        country = country_column.find('a')['title']
        
        population_column = next((col for col in columns if col.get('style') and 'text-align:right' in col.get('style')), None)
        if population_column:
            population = population_column.text.strip().replace(',', '')
            
            data.append([country, int(population)])
            count += 1
    
    df = pd.DataFrame(data, columns=['country', 'population'])
    df.to_csv('data/population.csv', index=False)
    print(f"Сохранено {len(df)} стран")
    return df

def get_area():
    url = "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_area"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    print("\nПолучение данных о площади стран...")
    
    table = soup.find('table', {'class': 'wikitable sortable sticky-header col2left'})
    
    if table is None:
        print("Ошибка: таблица не найдена")
        return pd.DataFrame(columns=['country', 'area'])
    
    area_data = {}
    count = 0
    
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        
        if len(cols) < 3:
            continue
            
        country_col = cols[1]
        country_link = country_col.find('a')
        if not country_link:
            continue
        country = country_link.text.strip()
        
        try:
            area_text = cols[2].text.strip()
            area = float(area_text.split()[0].replace(',', ''))
            
            area_data[country] = area
            count += 1
            
        except (ValueError, IndexError):
            print(f"Ошибка при обработке площади для страны {country}")
            continue
            
    print(f"Обработано {count} стран")
    
    df = pd.DataFrame(list(area_data.items()), columns=['country', 'area'])
    df.to_csv('data/area.csv', index=False)
    
    return df

def get_gdp():
    print("\nПолучение данных о ВВП стран...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Ошибка при получении страницы: {response.status_code}")
        return pd.DataFrame()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    gdp_data = parse_gdp_table(soup)
    
    if not gdp_data:
        print("Не удалось получить данные о ВВП")
        return pd.DataFrame()
        
    df = pd.DataFrame(list(gdp_data.items()), columns=['country', 'gdp'])
    df['gdp'] = df['gdp'].round(3)
    print(f"Создан DataFrame с {len(df)} строками")
    return df

def parse_gdp_table(soup):
    gdp_data = {}
    
    table = soup.find('table', {'class': ['wikitable', 'sortable', 'sticky-header-multi', 'static-row-numbers', 'jquery-tablesorter']})
    if not table:
        print("Таблица не найдена!")
        return gdp_data
    print("Таблица найдена")
        
    rows = table.find_all('tr')[2:]
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 2:
            country_cell = cols[0]
            country = ''
            
            for part in country_cell.contents:
                if not hasattr(part, 'name') or part.name != 'span':
                    if hasattr(part, 'text'):
                        country = country + part.text.strip()
                    else:
                        country = country + str(part).strip()
            
            country = country.strip()
            if country == '':
                link = country_cell.find('a')
                if link:
                    country = link.text.strip()
            
            if country != '':
                try:
                    gdp_text = cols[1].text.strip()
                    gdp_text = gdp_text.replace(',', '')
                    gdp = float(gdp_text)
                    gdp = round(gdp / 1000, 3)
                    gdp_data[country] = gdp
                    print(f"Добавлено: {country} - {gdp} billion")
                except:
                    print(f"Ошибка при обработке {country}")
                    continue
    
    print(f"Всего обработано стран: {len(gdp_data)}")
    return gdp_data

def analyze_data(df):
    numbers = []
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64']:
            numbers.append(col)
            
    for col in numbers:
        df[col] = df[col].round(3)
    
    stats = df[numbers].describe().round(3)

def smart_round(value):
    if value == 0:
        return 0
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return round(value)
    elif abs_value >= 1:
        return round(value, 2)
    else:
        return round(value, 5)

def get_military_spending():
    print("\nПолучение данных о военных расходах...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    url = "https://en.wikipedia.org/wiki/List_of_countries_by_military_expenditures"
    response = requests.get(url, headers=headers)
    
    military_data = {}
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        print("Ищем таблицу...")
        
        tables = soup.find_all('table', {'class': 'wikitable'})
        print(f"Найдено таблиц: {len(tables)}")
        
        for table in tables:
            header_text = table.find('tr').get_text()
            print(f"Заголовок таблицы: {header_text}")
            if 'Spending' in header_text and 'Country' in header_text:
                print("Нашли нужную таблицу!")
                rows = table.find_all('tr')[1:]
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 3:
                        try:
                            country_cell = cols[1]
                            country = country_cell.get_text(strip=True)
                            if '[' in country:
                                country = country.split('[')[0].strip()
                            
                            spending_text = cols[2].get_text(strip=True)
                            if spending_text:
                                spending = float(spending_text)
                                military_data[country] = spending
                                print(f"Добавлено: {country} - {spending} billion $")
                        except Exception as e:
                            print(f"Ошибка в строке: {[col.get_text(strip=True) for col in cols]}")
                            print(f"Ошибка: {e}")
                            continue
                break
    
    if not military_data:
        print("Не удалось получить данные о военных расходах")
    
    df = pd.DataFrame(list(military_data.items()), columns=['country', 'military_spending'])
    print(f"Получено данных о военных расходах: {len(df)} стран")
    return df

def get_hdi():
    print("\nПолучение данных об индексе человеческого развития...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    url = "https://en.wikipedia.org/wiki/List_of_countries_by_Human_Development_Index"
    response = requests.get(url, headers=headers)
    
    hdi_data = {}
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        print("Ищем таблицу...")
        
        tables = soup.find_all('table', {'class': 'wikitable'})
        print(f"Найдено таблиц: {len(tables)}")
        
        for table in tables:
            header_text = table.find('tr').get_text()
            print(f"Заголовок таблицы: {header_text}")
            if 'HDI value' in header_text and 'Country' in header_text:
                print("Найдена нужная таблица!")
                rows = table.find_all('tr')[1:]
                print(f"Найдено строк: {len(rows)}")
                
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    try:
                        if len(cols) >= 4:
                            country_col = row.find('th')
                            if country_col and country_col.find('a'):
                                country = country_col.find('a').get_text(strip=True)
                                hdi_value = cols[3].get_text(strip=True)
                                
                                if hdi_value and hdi_value != 'HDI value':
                                    hdi_data[country] = float(hdi_value)
                                    print(f"Добавлено: {country} - {hdi_value}")
                    except Exception as e:
                        print(f"Ошибка в строке: {[col.get_text(strip=True) for col in cols]}")
                        print(f"Ошибка: {e}")
                        continue
                break
    
    if not hdi_data:
        print("Не удалось получить данные об HDI")
    
    df = pd.DataFrame(list(hdi_data.items()), columns=['country', 'hdi'])
    print(f"Получено данных об HDI: {len(df)} стран")
    return df

def main():
    if not os.path.exists('data'):
        os.makedirs('data')
        
    print("Собираем данные о населении...")
    pop_df = get_population()
    
    print("Собираем данные о площади...")
    area_df = get_area()
    
    print("Собираем данные о ВВП...")
    gdp_df = get_gdp()
    
    print("Собираем данные о военных расходах...")
    military_df = get_military_spending()
    
    print("Собираем данные о HDI...")
    hdi_df = get_hdi()
    
    print("Объединяем данные...")
    final_df = pop_df.merge(area_df, on='country', how='left')
    final_df = final_df.merge(gdp_df, on='country', how='left')
    final_df = final_df.merge(military_df, on='country', how='left')
    final_df = final_df.merge(hdi_df, on='country', how='left')
    
    total_gdp = final_df['gdp'].sum()
    
    for i in range(len(final_df)):
        if not pd.isna(final_df.loc[i, 'population']) and not pd.isna(final_df.loc[i, 'area']):
            density = final_df.loc[i, 'population'] / final_df.loc[i, 'area']
            final_df.loc[i, 'density'] = smart_round(density)
            
        if not pd.isna(final_df.loc[i, 'gdp']) and not pd.isna(final_df.loc[i, 'population']):
            gdp_per_capita = final_df.loc[i, 'gdp'] * 1e9 / final_df.loc[i, 'population']
            final_df.loc[i, 'gdp_per_capita'] = smart_round(gdp_per_capita)
            
            gdp_share = (final_df.loc[i, 'gdp'] / total_gdp) * 100
            final_df.loc[i, 'gdp_share'] = smart_round(gdp_share)
    
    final_df['population'] = final_df['population'].apply(smart_round)
    final_df['area'] = final_df['area'].apply(smart_round)
    final_df['gdp'] = final_df['gdp'].apply(smart_round)
    final_df['military_spending'] = final_df['military_spending'].apply(smart_round)
    final_df['hdi'] = final_df['hdi'].apply(smart_round)
    
    final_df.to_csv('data/merged_data.csv', index=False)
    pop_df.to_csv('data/population.csv', index=False)
    area_df.to_csv('data/area.csv', index=False)
    gdp_df.to_csv('data/gdp.csv', index=False)
    military_df.to_csv('data/military_spending.csv', index=False)
    hdi_df.to_csv('data/hdi.csv', index=False)
    
    print("Анализируем данные...")
    analyze_data(final_df)
    
    print("\nГотово! Результаты сохранены в папках 'data' и 'plots'")

if __name__ == "__main__":
    main()