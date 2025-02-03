from io import StringIO
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def get_match_report_links(url):
    """
    Scrapes a webpage for match report links within a table.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        dict: A dictionary where keys are row indexes and values are the corresponding URLs.
    """
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')

    if table is None:
        return {}

    match_report_links = {}
    for i, row in enumerate(table.find_all('tr')):
        cells = row.find_all('td')
        for cell in cells:
            a_tag = cell.find('a', string='Match Report')
            if a_tag:
                link = a_tag.get('href')
                if link:
                    if not link.startswith('http'):
                        base_url = url.split('/')[0] + '//' + url.split('/')[2]
                        link = base_url + link
                    match_report_links[i-1] = link
    return match_report_links

def get_table_with_urls(url):
    """
    Gets the table from the URL using pandas.read_html and replaces "Match Report" text with URLs.

    Args:
        url (str): The URL of the webpage.

    Returns:
        pandas.DataFrame: The DataFrame with URLs in the "Match Report" column.
    """
    try:
        dfs = pd.read_html(url)
        if not dfs:
            return None
        df = dfs[0]  # Assuming the first table is the one we want
    except ValueError:
        return None

    match_report_links = get_match_report_links(url)

    # Find the column that contains "Match Report"
    match_report_column = None
    for col in df.columns:
        if df[col].astype(str).str.contains('Match Report').any():
            match_report_column = col
            break

    if match_report_column is not None:
        # Iterate through the rows and replace "Match Report" with the URL
        for index, row in df.iterrows():
            if index in match_report_links:
                df.loc[index, match_report_column] = match_report_links[index]

    return df


def read_match_report(url):
    """
    Reads the match report from a URL.

    Args:
        url (str): The URL of the match report.

    Returns:
        pandas.DataFrame: The match report table.



    The match reports retiurns a list of dataframes, each dataframe is a table from the match report
    DF[0] is the first table and shows the Home team 11
    DF[1] is the second table and shows the Away team 11
    DF[2] is the third table and shows the match stats with first column home and second away
    DF[3] is the fourth table and shows the player summary stats for the home team
    DF[4] is the fifth table and shows the player passing stats for the home team
    DF[5] is the sixth table and shows the player passing types stats for the home team
    DF[6] is the seventh table and shows the player defense stats for the home team
    DF[7] is the eigth table and shows the player possession stats for the home team
    DF[8] is the ninth table and shows the player misc stats for the home team
    DF[9] is the tenth table and shows the GK  stats for the home team
    DF[10] is the eleventh table and shows the player summary stats for the away team
    DF[11] is the twelveth table and shows the player passing stats for the away team
    DF[12] is the thirteenth table and shows the player passing types stats for the away team
    DF[13] is the fourteenth table and shows the player defense stats for the away team
    DF[14] is the fifteenth table and shows the player possession stats for the away team
    DF[15] is the sixteenth table and shows the player misc stats for the away team
    DF[16] is the seventeenth table and shows the GK  stats for the away team

    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = requests.get(url).text.replace('<!--','').replace('-->','')
        dataframes = pd.read_html(StringIO(html_content))
        Match_stats = {}
        for df in dataframes:
            # drop top header row
            if df.columns.nlevels > 1:
                df.columns = df.columns.droplevel(0)
            

        Match_stats['Home Summary'] = dataframes[3]
        Match_stats['Home misc'] = dataframes[8]
        Match_stats['Home Passing'] = dataframes[4]
        Match_stats['Away Summary'] = dataframes[10]
        Match_stats['Away misc'] = dataframes[15]
        Match_stats['Away Passing'] = dataframes[11]
        return Match_stats 

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



# Example usage
if __name__ == "__main__":
    europa_url = "https://fbref.com/en/comps/19/schedule/Europa-League-Scores-and-Fixtures"
    europa_attributes = {'id':'sched_2024-2025_19_1'}
    df_with_urls = get_table_with_urls(europa_url)
    match_report = 'https://fbref.com/en/matches/791569a7/BodoGlim'
    
    data = read_match_report(match_report)
    
    #print(data[0])
    #print('all tables')
    #print(data)

    #if df_with_urls is not None:
    #    data = read_match_report(df_with_urls.iloc[0]['Match Report'])
    #    if data is not None:
    #        for table_name, df in data.items():
    #            print(f"\nTable: {table_name}")
    #            print(df.head(1))
    #if df_with_urls is not None:
    #    print(read_match_report(df_with_urls.iloc[0]['Match Report'])[].head(10))
    #else:
    #    print("No table found or an error occurred.")
