import requests 
import backend 
import xml.etree.ElementTree as ET

def get_cve_rss():
    session = requests.Session()
    rss_feed = session.get('https://supportportal.juniper.net/knowledgerss?type=Security', verify=False)
    
    with open('cve_xml.xml', 'w') as w_cve:
        w_cve.write(rss_feed.text)
    w_cve.close()

    session.close()

    return session

def convert_xml_to_json(session):
    session = get_cve_rss()

    
    
    session.close()
    return cve_objects 


convert_xml_to_json(get_cve_rss)