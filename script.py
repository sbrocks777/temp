from bs4 import BeautifulSoup as bs
import pandas as pd
import requests

base_url = 'https://www.uniapply.com/schools/schools-in-delhi/'

def get_html_doc( url):
    html_doc = requests.get(url)
    soup = bs(html_doc.content, 'html.parser')
    return soup

def get_school_list( url):
    data = []
    soup = get_html_doc(url)
    sections = soup.find_all('section', class_='item-list')
    pagination = soup.find('ul', class_='pagination')

    if pagination:
        nxt = pagination.find_all('li', class_='page-item')[-1].text[0:4] == 'Next'
    else:
        nxt = False

    for section in sections:
        data.append({
            'title': section.find('h4').text,
            'link': section.find('h4').a['href'],
            'school_image': section.find('div', class_='schoolImage').a.picture.source['srcset'],
            'class_offered': section.find_all('div', class_='list-info-item')[0].find_all('span')[1].text,
            'sf_ratio': section.find_all('div', class_='list-info-item')[-1].find_all('span')[1].text,
            'next': nxt,
            })
        return data

def get_school_details( url):
    soup = get_html_doc(url)
    school_details = {}

    key_stats = get_key_stats(soup)
    hall_of_fame = get_hall_of_fame(soup)
    fc = get_facilities(soup)
    gallery = get_gallery(soup)
    address = get_address(soup)

    school_details = key_stats
    key_stats.update(fc)
    key_stats.update({'hall_of_fame':hall_of_fame})
    key_stats.update({'gallery': gallery})
    key_stats.update(address)

    return school_details


def get_key_stats( soup):
    key_stats = {}
    section = soup.find('section', id='key_school_stats_tab')
    data_list = section.find_all('div', class_='data-list')
    for data in data_list:
        key_stats[data.small.text] = data.big.text.replace(' ', '', 1)[:-1]
    return key_stats

def get_hall_of_fame( soup):
    hall_of_fame = []
    section = soup.find('section', id='institute_result_tab')
    awards = soup.find_all('div', class_='award-row')
    for award in awards:
        hall_of_fame.append(award.big.text.replace(' ', '', 1)[:-1])
    return hall_of_fame

def get_facilities( soup):
    facilities = []
    fc = {}
    list_fc = soup.find_all('div', class_='list-fc')
    ## for all available and not available
    # for item in list_fc:
    #     fc[item.h6.text] = {ele.text: 'available' if 'avaiable' in ele['class'] else 'not available' for ele in item.find_all('li')}
    for item in list_fc:
        fc[item.h6.text] = [ele.text.replace(' ', '', 1) for ele in item.find_all('li', class_='avaiable')]
    return fc

def get_gallery( soup):
    gallery = []
    section = soup.find('section', id='galary_tab')
    try:
        pic_container = section.find_all('a')
        for pic_url in pic_container:
            gallery.append(pic_url['href'])
    except:
        nav = soup.find('nav', class_="breadcrumb-nav breadcrumb-banner")
        li = nav.find_all('li')[-1].text
        print(f"No Gallery: {li}")
    return gallery

def get_address(soup):
    temp = []
    section = soup.find('section', id='address_tab')
    address_divs = section.find_all('div', class_='schoolAddress')
    for ad in address_divs:
        temp.append(ad.text if ad else 'N/A')
    temp[0] = temp[0].replace('\n', '\b').replace('\t', '')
    return dict(zip(['address', 'email', 'website', 'phone_no'], temp))

def get_all_page_data( url, nxt, count, data):
    if nxt == False:
        return data
    count += 1
    curr_url = f"{url}?page={count}"

    school_list = get_school_list(curr_url)
    if school_list:
        for item in school_list:
            details = get_school_details(item['link'])
            details.update({
                'school_name': item['title'], 
                'school_image': item['school_image'],
                'class_offered': item['class_offered'],
                'sf_ratio': item['sf_ratio']
                })
            data.append(details)
            nxt = item['next']
        print(curr_url)
    else:
        nxt = False
        print('No more pages available.')
    return get_all_page_data(url, nxt, count, data)

def get_first_100( url, count, data):
    if count == 100:
        return data
    count += 1
    curr_url = f"{url}?page={count}"

    school_list = get_school_list(curr_url)
    for item in school_list:
        details = get_school_details(item['link'])
        details.update({
            'school_name': item['title'], 
            'school_image': item['school_image'],
            'class_offered': item['class_offered'],
            'sf_ratio': item['sf_ratio']
            })
        data.append(details)
    print(curr_url)
    return get_first_100(url, count, data)


first_100 = get_all_page_data(base_url, True, 0, [])
df = pd.DataFrame(first_100)
df.to_csv('db.csv', index=False)
