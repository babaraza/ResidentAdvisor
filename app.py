from bs4 import BeautifulSoup
import requests
import pandas as pd
import re


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


# Url to RA website used to build links for each promoter
base_url = 'https://www.residentadvisor.net'

# Initial URL used to get list of promoters
url = 'https://www.residentadvisor.net/promoter.aspx'

# Headers to mimic browser behavior
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}

# Using session() to keep cookies for ajax
s = requests.Session()

# List holding Promoter class objects
final_list = []


def get_links():
    """
    Gets url's of all the promoters

    :return: list of links corresponding to each Promoter and total number of records
    """

    # Using created session to go to RA website
    r = s.get(url, headers=headers)
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

        link = item.find('a')               # Finding all <a> tags
        if 'id=' in str(link):              # If the href contains "id=" it points to a promoter
            links.add(link.get('href'))     # Retrieve href (url) for every <a> tag

    return list(links), len(links)


def get_init_data(prom_list, num_of_records):
    """
    Goes to each promoter url inside the prom_list  to scrape data

    :param prom_list: List returned from get_links()
    :param num_of_records: number of records to pull
    :return: final_list which holds Promoter object for each promoter
    """

    # Check what the user inputted for Number of Records to pull?
    if num_of_records == 0:
        rec_to_pull = len(prom_list)  # Setting number of records to length of list
    else:
        rec_to_pull = num_of_records  # Setting number of records to user input

    # Iterating over prom_list then running it through get_data()
    # Creating a new Promoter class object for each promoter
    # Then appending it to final list
    for link in prom_list[0:rec_to_pull]:
        final_list.append(Promoter(*get_data(link)))


def get_data(ind_link):
    """
    Gets Promoter data from the provided ind_link

    :param ind_link: each link from the total promoters list
    :return: tuple of retrieved attributes
    """

    # Creating the promoter url
    r2 = s.get(base_url + ind_link)
    r2.raise_for_status()
    soup2 = BeautifulSoup(r2.text, 'lxml')

    # Getting the name of the Promoter
    name = soup2.select_one('h1').text

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
        social = soup2.select_one('div:contains("On the internet")').parent
        try:
            email_class = social.select_one('a:contains("Email")')
            email = email_class.get('href').split(':')[1]
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
        phone_number = soup2.select_one("li div:contains('Phone')").text

        # Running a regex search for selecting the phone number
        phone = re.findall(r'\d{10}', phone_number)[0]
    except:
        pass

    return name, email, website, facebook, youtube, instagram, phone, twitter


def show_results():
    """
    Takes the final_list and creates a dataframe with the results

    """

    df = pd.DataFrame()

    desired_width = 480
    pd.set_option('display.width', desired_width)
    pd.set_option('display.max_columns', 8)

    df['Name'] = [p.name for p in final_list]
    df['Email'] = [p.email for p in final_list]
    df['Website'] = [p.website for p in final_list]
    df['Facebook'] = [p.facebook for p in final_list]
    df['Youtube'] = [p.youtube for p in final_list]
    df['Instagram'] = [p.instagram for p in final_list]
    df['Phone'] = [p.phone for p in final_list]
    df['Twitter'] = [p.twitter for p in final_list]

    print(df)

    # TODO: Add excel functionality


if __name__ == '__main__':
    promoters, total_records = get_links()
    print(f'Total Promoters Found: {total_records}')
    rec = input('Records to pull (0 means all) > ')
    get_init_data(prom_list=promoters, num_of_records=int(rec))
    show_results()
