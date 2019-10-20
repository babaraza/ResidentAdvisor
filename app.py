from save_data import save_data
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re

# Url to RA website used to build links for each promoter
base_url = 'https://www.residentadvisor.net'

# Headers to mimic browser behavior
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}

# Using session() to keep cookies for ajax
s = requests.Session()


class Country:
    """ Holds country name and link """

    def __init__(self, name, link):
        self.name = name
        self.link = link


class City:
    """ Holds city/state name and link """

    def __init__(self, name, link):
        self.name = name
        self.link = link


class Promoter:
    """ Holds attributes for each promoter """

    def __init__(self, *args):
        self.name = args[0]
        self.email = args[1]
        self.website = args[2]
        self.facebook = args[3]
        self.youtube = args[4]
        self.instagram = args[5]
        self.phone = args[6]
        self.twitter = args[7]


# Got this from https://stackoverflow.com/questions/36911296/scraping-of-protected-email
# Decoding CloudFlares email protection
def decode_email(e):
    de = ""
    k = int(e[:2], 16)

    for i in range(2, len(e) - 1, 2):
        de += chr(int(e[i:i + 2], 16) ^ k)

    return de


def get_countries(url):
    all_countries = []
    r = s.get(url, headers=headers)
    r.raise_for_status()

    soup_country = BeautifulSoup(r.text, 'lxml')
    items = soup_country.find_all(class_='links')
    country_list = items[0].find_all('li')
    for item in country_list:
        all_countries.append(Country(name=item.text, link=item.find('a')['href']))
        # print(item.attrs['data-id'])
    return all_countries


def get_cities(url):
    all_cities = []
    r = s.get(base_url + url, headers=headers)
    r.raise_for_status()

    soup_city = BeautifulSoup(r.text, 'lxml')
    items = soup_city.find_all(class_='links')

    # State/Region etc links have class parent
    # Links without parent class are for each city
    # But the parent class links will pull up all the sub-cities
    city_list = items[1].find_all('li', class_='parent')

    # Iterate over city_list to extract urls and append to all_cities
    for item in city_list:
        all_cities.append(City(name=item.text, link=item.find('a')['href']))
    return all_cities


def get_links(city_link):
    """
    Gets url's of all the promoters

    :return: list of links corresponding to each Promoter and total number of records
    """

    # Using created session to go to RA website
    r = s.get(base_url + city_link, headers=headers)
    r.raise_for_status()

    # Parsing through BS4
    soup = BeautifulSoup(r.content, 'lxml')

    # Selecting html element Form1 which contains all promoters
    form = soup.find(id="Form1")

    # Finding all list items inside the Form1 table
    all_items = form.find_all('li')

    # Using set to hold links to automatically delete duplicates
    links = set()

    # Iterating over all list items (table)
    for item in all_items:
        link = item.find('a')            # Finding all <a> tags
        if 'id=' in str(link):           # If the href contains "id=" it points to a promoter
            links.add(link.get('href'))  # Retrieve href (url) for every <a> tag

    return list(links), len(links)


def get_init_data(promoter_list, num_of_records):
    """
    Goes to each promoter url inside the promoter_list to scrape data

    :param promoter_list: List returned from get_links()
    :param num_of_records: number of records to pull
    :return: final_list which holds Promoter object for each promoter
    """

    # List holding Promoter class objects
    final_list = []

    # Check what the user inputted for Number of Records to pull?
    if num_of_records == 0:
        # Setting number of records to length of list
        rec_to_pull = len(promoter_list)
    else:
        # Setting number of records to user input
        rec_to_pull = num_of_records

    # Iterating over promoter_list then running it through get_data()
    # Creating a new Promoter class object for each promoter
    # Then appending it to final list
    for link in promoter_list[0:rec_to_pull]:
        if check_if_active(link):
            final_list.append(Promoter(*get_data(link)))
        else:
            pass

    return final_list


def check_if_active(promoter_link):
    """
    Checks to see if promoter is active by looking at existence of events
    in it's events page

    :param promoter_link: link for each promoter with id
    :return: boolean if promoter has events or not
    """

    # Checking if promoter is active by looking at number of events
    parameters = {'show': 'events'}

    # show=events parameters takes us to promoter events page
    r3 = s.get(base_url + promoter_link, params=parameters)

    # Parse data
    soup_events = BeautifulSoup(r3.text, 'lxml')

    # Find div that contains events
    div_for_events = soup_events.find(id='divArchiveEvents')

    # Pull up all table <li> tags inside above div
    # These are all events found
    events = div_for_events.find_all('li')

    # If the list 'events' is 0, then promoter has no events
    if len(events) > 0:
        return True
    else:
        return False


def get_data(promoter_link):
    """
    Gets Promoter data from the provided ind_link

    :param promoter_link: each link from the total promoters list
    :return: tuple of retrieved attributes
    """

    # Creating the promoter url
    r2 = s.get(base_url + promoter_link)
    r2.raise_for_status()
    soup_promoter = BeautifulSoup(r2.text, 'lxml')

    # Getting the name of the Promoter
    name = soup_promoter.select_one('h1').text

    # Setting default values
    email = 'N/A'
    website = 'N/A'
    facebook = 'N/A'
    youtube = 'N/A'
    instagram = 'N/A'
    phone = 'N/A'
    twitter = 'N/A'

    try:
        # Looking for the section that has text "On the internet"
        # Then getting it's parent which contains all contact info
        social = soup_promoter.select_one('div:contains("On the internet")').parent
        try:
            email_class = social.select_one('a:contains("Email")')
            # CloudFlare hosted websites encode emails for protection
            email = decode_email(email_class.get('href').split('#')[1])
        except:
            pass
        try:
            website_class = social.select_one('a:contains("Website")')
            website = website_class.get('href')
        except:
            pass
        try:
            facebook_class = social.select_one('a:contains("Facebook")')
            facebook = facebook_class.get('href')
        except:
            pass
        try:
            youtube_class = social.select_one('a:contains("Youtube")')
            youtube = youtube_class.get('href')
        except:
            pass
        try:
            instagram_class = social.select_one('a:contains("Instagram")')
            instagram = instagram_class.get('href')
        except:
            pass
        try:
            twitter_class = social.select_one('a:contains("Twitter")')
            twitter = twitter_class.get('href')
        except:
            pass
    except:
        pass

    try:
        # Getting the phone number <div> inside a <li>
        phone_number = soup_promoter.select_one("li div:contains('Phone')").text

        # Running a regex search for selecting the phone number
        phone = re.findall(r'\d{10}', phone_number)[0]
    except:
        pass

    return name, email, website, facebook, youtube, instagram, phone, twitter


def format_data(result_list):
    """
    Creates a Data Frame with results from get_init_data()

    :param result_list: results from get_init_data()
    :return: Final Data Frame containing data for each Promoter
    """

    df = pd.DataFrame()

    df['Name'] = [p.name for p in result_list]
    df['Email'] = [p.email for p in result_list]
    df['Phone'] = [p.phone for p in result_list]
    df['Website'] = [p.website for p in result_list]
    df['Facebook'] = [p.facebook for p in result_list]
    df['Youtube'] = [p.youtube for p in result_list]
    df['Instagram'] = [p.instagram for p in result_list]
    df['Twitter'] = [p.twitter for p in result_list]

    return df


def show_results(final_df):
    """
    Prints the final Data Frame from format_data() to console

    :param final_df: Final Data Frame from format_data()
    :return: Prints the Data Frame in console
    """

    # Settings to print the data frame to console correctly
    desired_width = 480
    pd.set_option('display.width', desired_width)
    pd.set_option('display.max_columns', 8)

    print(final_df)


if __name__ == '__main__':
    print('Running Program...')
    countries = get_countries('https://www.residentadvisor.net/promoters.aspx')

    for country in countries:
        country_data = []
        print('-' * 45)
        print(f'Getting data from {country.name}')
        print('-' * 45)
        cities = get_cities(url=country.link)

        for city in cities:
            promoters, total_records = get_links(city_link=city.link)
            print(f'Total Promoters Found in {city.name}: {total_records}')
            # rec = input('Records to pull (0 means all) > ')
            country_data.extend(get_init_data(promoter_list=promoters, num_of_records=int(0)))
        final_data_frame = format_data(country_data)
        print(f'Saving data for {country.name}...')
        print('-' * 45)
        save_data('Data', country.name, final_data_frame)

    # Uncomment this to show results in console
        show_results(final_data_frame)
