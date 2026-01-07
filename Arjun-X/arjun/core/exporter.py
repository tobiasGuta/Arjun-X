import json
import requests

import arjun.core.config as mem
from arjun.core.utils import populate

from arjun.core.utils import create_query_string

def get_param_names(params):
    """Helper to extract just names from rich param objects"""
    if not params: return []
    if isinstance(params[0], dict) and 'name' in params[0]:
        return [p['name'] for p in params]
    return params

def json_export(result):
    """
    exports result to a file in JSON format
    """
    with open(mem.var['json_file'], 'w+', encoding='utf8') as json_output:
        json.dump(result, json_output, sort_keys=True, indent=4)


def burp_export(result):
    """
    exports results to Burp Suite by sending request to Burp proxy
    """
    proxy = ('' if ':' in mem.var['burp_proxy'] else '127.0.0.1:') + mem.var['burp_proxy']
    proxies = {
        'http': 'http://' + proxy,
        'https': 'https://' + proxy
    }
    for url, data in result.items():
        param_names = get_param_names(data['params'])
        if data['method'] == 'GET':
            requests.get(url, params=populate(param_names), headers=data['headers'], proxies=proxies, verify=False)
        elif data['method'] == 'POST':
            requests.post(url, data=populate(param_names), headers=data['headers'], proxies=proxies, verify=False)
        elif data['method'] == 'JSON':
            requests.post(url, json=populate(param_names), headers=data['headers'], proxies=proxies, verify=False)


def text_export(result):
    """
    exports results to a text file, one url per line
    """
    with open(mem.var['text_file'], 'a+', encoding='utf8') as text_file:
        for url, data in result.items():
            clean_url = url.lstrip('/')
            param_names = get_param_names(data['params'])
            
            if data['method'] == 'JSON':
                text_file.write(clean_url + '\t' + json.dumps(populate(param_names)) + '\n')
            else:
                query_string = create_query_string(param_names)
                if '?' in clean_url:
                    query_string = query_string.replace('?', '&', 1)
                if data['method'] == 'GET':
                    text_file.write(clean_url + query_string + '\n')
                elif data['method'] == 'POST':
                    text_file.write(clean_url + '\t' + query_string + '\n')

def html_export(result):
    """
    exports results to a HTML file
    """
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Arjun Scan Report</title>
        <style>
            body { font-family: sans-serif; margin: 20px; background: #f0f0f0; }
            .container { max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
            .target { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 4px; }
            .target h2 { margin-top: 0; color: #2196F3; font-size: 18px; word-break: break-all; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #eee; }
            th { background-color: #f8f9fa; color: #555; }
            .risk-CRITICAL { color: #d32f2f; font-weight: bold; }
            .risk-HIGH { color: #f57c00; font-weight: bold; }
            .risk-MEDIUM { color: #fbc02d; font-weight: bold; }
            .risk-LOW { color: #388e3c; font-weight: bold; }
            .vuln-tag { display: inline-block; background: #ffebee; color: #c62828; padding: 2px 6px; border-radius: 4px; font-size: 12px; margin-right: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Arjun Scan Report</h1>
            {content}
        </div>
    </body>
    </html>
    """
    
    content = ""
    for url, data in result.items():
        params_html = ""
        for p in data['params']:
            vulns = "".join([f'<span class="vuln-tag">{v}</span>' for v in p.get('vulns', [])])
            params_html += f"""
            <tr>
                <td>{p['name']}</td>
                <td class="risk-{p.get('risk', 'LOW')}">{p.get('risk', 'LOW')}</td>
                <td>{p.get('score', 0)}</td>
                <td>{vulns}</td>
            </tr>
            """
            
        content += f"""
        <div class="target">
            <h2>{data['method']} {url}</h2>
            <table>
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Risk</th>
                        <th>Score</th>
                        <th>Findings</th>
                    </tr>
                </thead>
                <tbody>
                    {params_html}
                </tbody>
            </table>
        </div>
        """
        
    with open(mem.var['html_file'], 'w+', encoding='utf8') as f:
        f.write(html_template.replace('{content}', content))

def exporter(result):
    """
    main exporter function that calls other export functions
    """
    if mem.var['json_file']:
        json_export(result)
    if mem.var['text_file']:
        text_export(result)
    if mem.var['burp_proxy']:
        burp_export(result)
    if mem.var.get('html_file'):
        html_export(result)
