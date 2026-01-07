import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import arjun.core.config as mem
from arjun.core.colors import green, end, info, bad, good, run, res
from arjun.core.utils import fetch_params, stable_request, random_str, slicer, confirm, populate, reader, compatible_path
from arjun.core.anomaly import define, compare
from arjun.core.requester import requester
from arjun.core.bruter import bruter
from arjun.core.scanner import ParameterScorer, AutoTester
from arjun.plugins.heuristic import heuristic

# Determine project root
arjun_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def narrower(request, factors, param_groups):
    """
    Takes a list of parameters and narrows it down to parameters that cause anomalies
    Returns a list of anomalous parameters.
    """
    anomalous_params = []
    # Ensure threads is an int (it might come as a string from args if not typed properly, but args.threads is int)
    max_workers = int(mem.var.get('threads', 5))
    threadpool = ThreadPoolExecutor(max_workers=max_workers)
    
    futures = (threadpool.submit(bruter, request, factors, params) for params in param_groups)
    
    total_groups = len(param_groups)
    
    for i, result in enumerate(as_completed(futures)):
        res = result.result()
        if res:
            anomalous_params.extend(slicer(res))
        if mem.var.get('kill'):
            return anomalous_params
        print('%s Processing chunks: %i/%-6i' % (info, i + 1, total_groups), end='\r')
        
    return anomalous_params


def initialize(request, wordlist, single_url=False):
    """
    Handles parameter finding process for a single request object.
    Returns 'skipped' (on error) or a list of confirmed parameters on success.
    """
    url = request['url']
    if not url.startswith('http'):
        print('%s %s is not a valid URL' % (bad, url))
        return 'skipped'
        
    print('%s Probing the target for stability' % run)
    
    # Check stable request
    request['url'] = stable_request(url, request['headers'])
    mem.var['healthy_url'] = True
    
    if not request['url']:
        return 'skipped'
    
    # Health check
    fuzz = "z" + random_str(6)
    response_1 = requester(request, {fuzz[:-1]: fuzz[::-1][:-1]})
    
    # Basic status check
    if isinstance(response_1, str): # Error happened
         mem.var['healthy_url'] = False
         print('%s Error requester: %s' % (bad, response_1))
    else:
         mem.var['healthy_url'] = response_1.status_code not in (400, 413, 418, 429, 503)
         
    if not mem.var['healthy_url']:
        code = response_1.status_code if not isinstance(response_1, str) else "Error"
        print('%s Target returned HTTP %s, this may cause problems.' % (bad, code))
        
    if single_url:
        print('%s Analysing HTTP response for anomalies' % run)
        
    response_2 = requester(request, {fuzz[:-1]: fuzz[::-1][:-1]})
    
    if isinstance(response_1, str) or isinstance(response_2, str):
        return 'skipped'

    # Heuristic analysis
    found, words_exist = heuristic(response_1, wordlist)

    # Anomaly definition
    factors = define(response_1, response_2, fuzz, fuzz[::-1], wordlist)
    zzuf = "z" + random_str(6)
    response_3 = requester(request, {zzuf[:-1]: zzuf[::-1][:-1]})
    
    # Anomaly baseline refinement
    loop_limit = 10
    loops = 0
    while True:
        if isinstance(response_3, str):
             break
        reason = compare(response_3, factors, {zzuf[:-1]: zzuf[::-1][:-1]})[2]
        if not reason:
            break
        factors[reason] = None
        loops += 1
        if loops > loop_limit:
            break # Avoid infinite loops
            
    if found:
        num = len(found)
        if words_exist:
            print('%s Extracted %i parameters from response for testing' % (good, num))
        else:
            s = 's' if num > 1 else ''
            print('%s Extracted %i parameter%s from response for testing: %s' % (good, num, s, ', '.join(found)))
            
    if single_url:
        print('%s Logicforcing the URL endpoint' % run)
        
    populated = populate(wordlist)
    
    # Load specials
    special_file = os.path.join(arjun_dir, 'db', 'special.json')
    if os.path.exists(special_file):
        with open(special_file, 'r') as f:
            populated.update(json.load(f))
            
    # Slicing
    chunk_size = int(len(wordlist)/mem.var.get('chunks', 250))
    if chunk_size < 1: chunk_size = 1
    
    param_groups = slicer(populated, chunk_size)
    prev_chunk_count = len(param_groups)
    last_params = []
    
    # Main Bruting Loop
    while True:
        param_groups = narrower(request, factors, param_groups)
        
        # Stability check if chunks increased (weird behavior)
        if len(param_groups) > prev_chunk_count:
            response_3 = requester(request, {zzuf[:-1]: zzuf[::-1][:-1]})
            if not isinstance(response_3, str) and compare(response_3, factors, {zzuf[:-1]: zzuf[::-1][:-1]})[0] != '':
                print('%s Webpage is returning different content on each request. Skipping.' % bad)
                return []
                
        if mem.var.get('kill'):
            return 'skipped'
            
        param_groups = confirm(param_groups, last_params)
        prev_chunk_count = len(param_groups)
        
        if not param_groups:
            break
            
    confirmed_params = []
    scorer = ParameterScorer()
    tester = AutoTester(request)

    for param in last_params:
        reason = bruter(request, factors, param, mode='verify')
        if reason:
            name = list(param.keys())[0]
            
            # Scoring
            score = scorer.score_parameter(name)
            risk = scorer.get_risk_level(score)
            
            # Auto-Testing
            test_results = tester.test_parameter(name)

            param_data = {
                'name': name,
                'score': score,
                'risk': risk,
                'vulns': test_results
            }
            confirmed_params.append(param_data)

            if single_url:
                print('%s parameter detected: %s, based on: %s' % (res, name, reason))
                print(f'    Risk: {risk} (Score: {score})')
                for tr in test_results:
                    print(f'    [!] {tr}')
                    
    return confirmed_params
