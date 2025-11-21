import json
import time
import random
import requests
import warnings
import cloudscraper
from fake_useragent import UserAgent

import arjun.core.config as mem

from ratelimit import limits, sleep_and_retry
from arjun.core.utils import dict_to_xml

warnings.filterwarnings('ignore') # Disable SSL related warnings

# Global session to maintain cookies/CF tokens
_session = None
_ua = UserAgent()

def get_session():
    global _session
    if _session is None:
        try:
            _session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
        except Exception:
            # Fallback if cloudscraper fails to init
            _session = requests.Session()
    return _session

def get_random_headers(base_headers):
    headers = base_headers.copy()
    # Only rotate UA if not explicitly set by user or if it's the default
    if 'User-Agent' not in headers or headers['User-Agent'] == 'Arjun':
         try:
             headers['User-Agent'] = _ua.random
         except:
             headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    return headers

@sleep_and_retry
@limits(calls=mem.var['rate_limit'], period=1)
def requester(request, payload={}):
    """
    central function for making http requests
    returns str on error otherwise response object of requests library
    """
    session = get_session()

    if request.get('include') and len(request.get('include', '')) != 0:
        payload.update(request['include'])
    
    # Jitter / Stealth logic
    if mem.var.get('stable'):
        mem.var['delay'] = random.choice(range(3, 10))
        time.sleep(mem.var['delay'])
    elif mem.var.get('stealth'): # New stealth flag support
        time.sleep(random.uniform(0.5, 2.5))
    else:
        time.sleep(mem.var['delay'])

    url = request['url']
    if mem.var['kill']:
        return 'killed'
    
    # Prepare headers with rotation
    headers = get_random_headers(request['headers'])

    try:
        if request['method'] == 'GET':
            response = session.get(url,
                params=payload,
                headers=headers,
                # verify=False,
                allow_redirects=False,
                timeout=mem.var['timeout'],
            )
        elif request['method'] == 'JSON':
            headers['Content-Type'] = 'application/json'
            if mem.var['include'] and '$arjun$' in mem.var['include']:
                payload = mem.var['include'].replace('$arjun$',
                    json.dumps(payload).rstrip('}').lstrip('{'))
                response = session.post(url,
                    data=payload,
                    headers=headers,
                    # verify=False,
                    allow_redirects=False,
                    timeout=mem.var['timeout'],
                )
            else:
                response = session.post(url,
                    json=payload,
                    headers=headers,
                    # verify=False,
                    allow_redirects=False,
                    timeout=mem.var['timeout'],
                )
        elif request['method'] == 'XML':
            headers['Content-Type'] = 'application/xml'
            payload = mem.var['include'].replace('$arjun$',
                dict_to_xml(payload))
            response = session.post(url,
                data=payload,
                headers=headers,
                # verify=False,
                allow_redirects=False,
                timeout=mem.var['timeout'],
            )
        else:
            response = session.post(url,
                data=payload,
                headers=headers,
                # verify=False,
                allow_redirects=False,
                timeout=mem.var['timeout'],
            )
        return response
    except Exception as e:
        print(f"Request Error: {e}")
        return str(e)
