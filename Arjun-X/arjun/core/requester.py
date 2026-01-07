import json
import time
import random
import requests
import warnings
import cloudscraper
import logging
from fake_useragent import UserAgent
from typing import Dict, Any, Union, Optional
from requests import Response

import arjun.core.config as mem

from ratelimit import limits, sleep_and_retry
from arjun.core.utils import dict_to_xml

# Setup logger
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore') # Disable SSL related warnings

# Global session to maintain cookies/CF tokens
_session: Optional[Union[requests.Session, cloudscraper.CloudScraper]] = None
_ua = UserAgent()

def get_session() -> Union[requests.Session, cloudscraper.CloudScraper]:
    """
    Initialize and return the HTTP session (CloudScraper or generic Requests Session).
    """
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
        except Exception as e:
            logger.debug(f"CloudScraper failed to initialize: {e}. Fallback to requests.Session.")
            # Fallback if cloudscraper fails to init
            _session = requests.Session()
            # Disable verification for standard session if desired, though not checking verify=False in original code
            # _session.verify = False 
    return _session

def get_random_headers(base_headers: Dict[str, str]) -> Dict[str, str]:
    """
    Return a copy of headers with a randomized User-Agent if necessary.
    """
    headers = base_headers.copy()
    # Only rotate UA if not explicitly set by user or if it's the default
    if 'User-Agent' not in headers or headers['User-Agent'] == 'Arjun':
         try:
             headers['User-Agent'] = _ua.random
         except Exception:
             headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    return headers

@sleep_and_retry
@limits(calls=mem.var.get('rate_limit', 9999), period=1)
def requester(request: Dict[str, Any], payload: Dict[str, Any] = {}) -> Union[Response, str]:
    """
    Central function for making HTTP requests.
    
    Args:
        request: A dictionary containing request details (url, method, headers, etc.).
        payload: A dictionary of parameters to send.
        
    Returns:
        Union[Response, str]: The Response object on success, or an error string on failure.
    """
    session = get_session()

    if request.get('include') and len(request.get('include', '')) != 0:
        # Avoid modifying the default argument if payload was implicitly passed (though {} is immutable-ish in this context, good practice to copy if mutating)
        # But here 'payload' is passed by reference.
        payload.update(request['include'])
    
    # Jitter / Stealth logic
    if mem.var.get('stable'):
        delay = random.choice(range(3, 10))
        time.sleep(delay)
    elif mem.var.get('stealth'): # New stealth flag support
        time.sleep(random.uniform(0.5, 2.5))
    elif mem.var.get('delay'):
         time.sleep(mem.var['delay'])

    url = request['url']
    if mem.var.get('kill'):
        return 'killed'
    
    # Prepare headers with rotation
    headers = get_random_headers(request['headers'])
    
    timeout = mem.var.get('timeout', 15)

    try:
        if request['method'] == 'GET':
            response = session.get(url,
                params=payload,
                headers=headers,
                allow_redirects=False,
                timeout=timeout,
            )
        elif request['method'] == 'JSON':
            headers['Content-Type'] = 'application/json'
            include_data = mem.var.get('include')
            if include_data and '$arjun$' in include_data:
                # Replace placeholder with JSON string
                # Note: payload is a dict, we convert it to json string
                json_payload = json.dumps(payload).rstrip('}').lstrip('{')
                final_data = include_data.replace('$arjun$', json_payload)
                
                response = session.post(url,
                    data=final_data,
                    headers=headers,
                    allow_redirects=False,
                    timeout=timeout,
                )
            else:
                response = session.post(url,
                    json=payload,
                    headers=headers,
                    allow_redirects=False,
                    timeout=timeout,
                )
        elif request['method'] == 'XML':
            headers['Content-Type'] = 'application/xml'
            # Assuming 'include' is a template string in mem.var
            include_data = mem.var.get('include')
            if include_data: 
                final_data = include_data.replace('$arjun$', dict_to_xml(payload))
            else:
                # Fallback if no template? Original code assumed mem.var['include'] existed and had replace
                # If mem.var['include'] is empty/None, this would crash in original code.
                # We'll assume it handles it or wrap in try/except.
                final_data = dict_to_xml(payload)

            response = session.post(url,
                data=final_data,
                headers=headers,
                allow_redirects=False,
                timeout=timeout,
            )
        else:
            # Standard POST (x-www-form-urlencoded)
            response = session.post(url,
                data=payload,
                headers=headers,
                allow_redirects=False,
                timeout=timeout,
            )
        return response
    except Exception as e:
        # e might not be a string, so safe conversion
        error_msg = str(e)
        if any(s in error_msg for s in ('NameResolutionError', 'Temporary failure', 'Max retries exceeded', 'Connection reset')):
            logger.debug(f"Request Error to {url}: {error_msg}")
        else:
            logger.error(f"Request Error to {url}: {error_msg}")
        return error_msg
