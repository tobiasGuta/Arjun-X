#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import logging
from urllib.parse import urlparse

# Import internal modules
import arjun.core.config as mem
from arjun.core.colors import green, end, info, bad, good, run, res
from arjun.core.exporter import exporter
from arjun.core.utils import fetch_params, reader, prepare_requests, compatible_path, nullify
from arjun.core.engine import initialize, arjun_dir
from arjun.core.logger import setup_logger
from arjun.plugins.wl import detect_casing, covert_to_case

def parse_args():
    parser = argparse.ArgumentParser() 
    parser.add_argument('-u', help='Target URL', dest='url')
    parser.add_argument('-o', '-oJ', help='Path for json output file.', dest='json_file')
    parser.add_argument('-oT', help='Path for text output file.', dest='text_file')
    parser.add_argument('-oB', help='Output to Burp Suite Proxy. Default is 127.0.0.1:8080.', dest='burp_proxy', nargs='?', const='127.0.0.1:8080')
    parser.add_argument('-d', help='Delay between requests in seconds. (default: 0)', dest='delay', type=float, default=0)
    parser.add_argument('-t', help='Number of concurrent threads. (default: 5)', dest='threads', type=int, default=5)
    parser.add_argument('-w', help='Wordlist file path. (default: {arjundir}/db/large.txt)', dest='wordlist', default=f'{arjun_dir}/db/large.txt')
    parser.add_argument('-m', help='Request method to use: GET/POST/XML/JSON. (default: GET)', dest='method', default='GET')
    parser.add_argument('-i', help='Import target URLs from file.', dest='import_file', nargs='?', const=True)
    parser.add_argument('-T', help='HTTP request timeout in seconds. (default: 15)', dest='timeout', type=float, default=15)
    parser.add_argument('-c', help='Chunk size. The number of parameters to be sent at once', type=int, dest='chunks', default=250)
    parser.add_argument('-q', help='Quiet mode. No output.', dest='quiet', action='store_true')
    parser.add_argument('--rate-limit', help='Max number of requests to be sent out per second (default: 9999)', dest='rate_limit', type=int, default=9999)
    parser.add_argument('--headers', help='Add headers. Separate multiple headers with a new line.', dest='headers', nargs='?', const=True)
    parser.add_argument('--passive', help='Collect parameter names from passive sources like wayback, commoncrawl and otx.', dest='passive', nargs='?', const='-')
    parser.add_argument('--stable', help='Prefer stability over speed.', dest='stable', action='store_true')
    parser.add_argument('--include', help='Include this data in every request.', dest='include', default={})
    parser.add_argument('--disable-redirects', help='disable redirects', dest='disable_redirects', action='store_true')
    parser.add_argument('--casing', help='casing style for params e.g. like_this, likeThis, likethis', dest='casing')
    parser.add_argument('--stealth', help='Enable stealth mode (jitter, random UA).', dest='stealth', action='store_true')
    parser.add_argument('-oH', help='Path for HTML output file.', dest='html_file')
    # Kill switch argument seems implicit in code (mem.var.get('kill')), not in argparse. Adding strictly if needed but sticking to existing pattern.
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup Logger
    setup_logger(quiet=args.quiet)
    
    # Legacy: Set global config
    mem.var = vars(args)

    if args.quiet:
        # Override print with no-op if quiet
        # Note: Ideally we use logger everywhere, but keeping this for legacy compatibility
        global print
        print = nullify

    print('''%s    _
   /_| _ '
  (  |/ /(//) v%s
      _/      %s
''' % (green, __import__('arjun').__version__, end))

    # Configuration Adjustment
    mem.var['method'] = mem.var['method'].upper()
    if mem.var['method'] != 'GET':
        mem.var['chunks'] = 500
    if mem.var['stable'] or mem.var['delay']:
        mem.var['threads'] = 1
    if mem.var['wordlist'] in ('large', 'medium', 'small'):
        mem.var['wordlist'] = f'{arjun_dir}/db/{mem.var["wordlist"]}.txt'

    # Wordlist Preparation
    wordlist = []
    try:
        wordlist_file = compatible_path(mem.var['wordlist'])
        wordlist_set = set(reader(wordlist_file, mode='lines'))
        
        if mem.var['passive']:
            host = mem.var['passive']
            if host == '-' and args.url:
                host = urlparse(args.url).netloc
            elif host == '-' and not args.url:
                 # Should handle if no URL is present but import file is used
                 pass 
                 
            if host != '-' and host:
                print('%s Collecting parameter names from passive sources for %s, it may take a while' % (run, host))
                passive_params = fetch_params(host)
                wordlist_set.update(passive_params)
                print('%s Collected %s parameters, added to the wordlist' % (info, len(passive_params)))
                
        if args.casing:
            delimiter, casing = detect_casing(args.casing)
            wordlist = [covert_to_case(word, delimiter, casing) for word in wordlist_set]
        else:
            wordlist = list(wordlist_set)
            
    except FileNotFoundError:
        print('%s The specified wordlist file doesn\'t exist' % bad)
        exit(1)

    if len(wordlist) < mem.var['chunks']:
        mem.var['chunks'] = int(len(wordlist)/2)
        if mem.var['chunks'] < 1: mem.var['chunks'] = 1

    if not args.url and not args.import_file:
        print('%s No target(s) specified' % bad)
        exit(1)

    requests = prepare_requests(args)
    final_result = {}
    is_single = False if args.import_file else True

    try:
        mem.var['kill'] = False
        count = 0
        total_reqs = len(requests)
        for request in requests:
            url = request['url']
            print('%s Scanning %d/%d: %s' % (run, count+1, total_reqs, url))
            
            these_params = initialize(request, wordlist, single_url=is_single)
            
            count += 1
            mem.var['kill'] = False
            mem.var['bad_req_count'] = 0
            
            if these_params == 'skipped':
                print('%s Skipped %s due to errors' % (bad, url))
            elif these_params:
                final_result[url] = {}
                final_result[url]['params'] = these_params
                final_result[url]['method'] = request['method']
                final_result[url]['headers'] = request['headers']
                exporter(final_result)
                
                # Extract names for display
                param_names = [p['name'] for p in these_params]
                print('%s Parameters found: %-4s\n' % (good, ', '.join(param_names)))
                
                if not mem.var['json_file'] and not mem.var['html_file']:
                    # Separate results if not exporting to single file
                    final_result = {}
                    continue
            else:
                print('%s No parameters were discovered.\n' % info)
    except KeyboardInterrupt:
        print('\n%s User interrupted.' % info)
        exit(0)

if __name__ == '__main__':
    main()
