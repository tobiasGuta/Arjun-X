<h1 align="center">
  <br>
  <a href="https://github.com/s0md3v/Arjun"><img src="https://image.ibb.co/c618nq/arjun.png" alt="Arjun"></a>
  <br>
  Arjun-X
  <br>
</h1>

<h4 align="center">Professional Grade HTTP Parameter Discovery Suite</h4>

> **Note:** This is the enhanced **Arjun-X** edition. It has been re-architected for professional use, featuring a modern codebase, type safety, improved stealth capabilities, and smart risk scoring.

<p align="center">
  <a href="#">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/license-MIT-green.svg">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/status-stable-brightgreen.svg">
  </a>
</p>

---

### What is Arjun-X?

Arjun-X is a specialized tool designed to discover hidden HTTP query parameters in URL endpoints. Web applications often use invisible parameters (`debug`, `admin`, `test`, `id`) that can open vectors for specific attacks like XSS, SQL Injection, or Privilege Escalation.

Arjun-X automates the discovery process by sending requests with huge lists of parameter names, but it does so intelligently—compressing thousands of attempts into just a few dozen requests using a specialized divide-and-conquer algorithm.

### Key Features

#### Professional Grade Core
- **Modern Architecture**: Completely refactored codebase using modular design patterns.
- **Type Safety**: Fully type-hinted execution flow for maximum stability.
- **Robust Logging**: Specialized logging system replaces basic print statements for better debugging.
- **Modern Packaging**: Compliant with PEP 517/518 using `pyproject.toml`.

#### Advanced Stealth & Evasion
- **Stealth Mode (`--stealth`)**: Bypasses WAFs/Cloudflare by introducing random jitter and intelligent User-Agent rotation.
- **Heuristic Scanning**: Passively extracts parameters from JavaScript files and other sources before active probing.

#### Stability & Resilience
- **Smart Error Recovery**: Automatically detects and recovers from transient network failures (DNS, connection resets) with intelligent retries.
- **Adaptive Execution**: Prevents scan failures by handling temporary connectivity drops gracefully without interrupting the workflow.

#### Smart Intelligence
- **Risk Scoring**: Automatically scores discovered parameters based on sensitivity (e.g., `admin` > `utm_source`) and behavior.
- **Auto-Vulnerability Checks**: Performs lightweight verification for Reflection (XSS) and Errors (SQLi) on discovered parameters.

#### Reporting
- **HTML Reports**: Generates rich, color-coded HTML reports for clients/managers.
- **Burp Suite Integration**: Export results directly to Burp Proxy.
- **JSON/Text Support**: Flexible output formats for pipeline integration.

---

### Installation

**Prerequisites:** Python 3.8+

#### Standard Installation
```bash
git clone https://github.com/your-repo/Arjun-X.git
cd Arjun-X
pip install .
```

#### Development Installation
For developers who want to modify the core:
```bash
pip install -e .
```

---

### Usage

#### Basic Scan
Find parameters for a single URL:
```bash
arjun -u https://api.example.com/v1/user
```

#### Stealth Scan (Recommended for WAFs)
Enable jitter and random User-Agents:
```bash
arjun -u https://api.example.com/v1/user --stealth
```

#### Generate Professional Report
Save the output to an HTML file for review:
```bash
arjun -u https://api.example.com/v1/user -oH report.html
```

#### JSON Output with POST Method
Send JSON payloads instead of GET parameters:
```bash
arjun -u https://api.example.com/login -m JSON -o result.json
```

---

### Command Line Options

| Option | Argument | Description |
|------|---------|------------|
| `-h`, `--help` | — | Show this help message and exit |
| `-u` | `URL` | Target URL |
| `-o`, `-oJ` | `JSON_FILE` | Path for JSON output file |
| `-oT` | `TEXT_FILE` | Path for text output file |
| `-oB` | `[BURP_PROXY]` | Output to Burp Suite Proxy (default: `127.0.0.1:8080`) |
| `-d` | `DELAY` | Delay between requests in seconds (default: `0`) |
| `-t` | `THREADS` | Number of concurrent threads (default: `5`) |
| `-w` | `WORDLIST` | Wordlist file path (default: `{arjundir}/db/large.txt`) |
| `-m` | `METHOD` | Request method: `GET`, `POST`, `XML`, `JSON` (default: `GET`) |
| `-i` | `[IMPORT_FILE]` | Import target URLs from file |
| `-T` | `TIMEOUT` | HTTP request timeout in seconds (default: `15`) |
| `-c` | `CHUNKS` | Chunk size (number of parameters sent at once) |
| `-q` | — | Quiet mode (no output) |
| `--rate-limit` | `RATE_LIMIT` | Max requests per second (default: `9999`) |
| `--headers` | `[HEADERS]` | Add headers (separate multiple headers with a new line) |
| `--passive` | `[PASSIVE]` | Collect parameter names from passive sources (wayback, commoncrawl, otx) |
| `--stable` | — | Prefer stability over speed |
| `--include` | `INCLUDE` | Include this data in every request |
| `--disable-redirects` | — | Disable redirects |
| `--casing` | `CASING` | Casing style for params (e.g. `like_this`, `likeThis`, `likethis`) |
| `--stealth` | — | Enable stealth mode (jitter, random User-Agent) |
| `-oH` | `HTML_FILE` | Path for HTML output file |


---

### Screenshots

#### CLI Output with Risk Scoring

<img width="682" height="248" alt="Screenshot 2025-11-21 170834" src="https://github.com/user-attachments/assets/fe557438-47d2-4814-b28f-4b9b983530a2" />

<img width="624" height="202" alt="Screenshot 2025-11-21 171018" src="https://github.com/user-attachments/assets/4c0058ed-6c00-485d-9c31-00fd395b90cb" />

### Report HTML

<img width="1904" height="461" alt="image" src="https://github.com/user-attachments/assets/74b9baaf-7151-446e-9347-c7b1c4267728" />

### Video

https://github.com/user-attachments/assets/614394c2-1363-4d01-b014-263b42059690

### Credits

Based on the original work by [s0md3v](https://github.com/s0md3v).
- **Wordlists**: Merged from CommonCrawl, SecLists, and Param-Miner.
- **Special Payloads**: Adapted from data-payloads.

**License**: MIT
