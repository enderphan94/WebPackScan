# Check NPM Packages Vulnerability  

A Python tool to identify vulnerabilities in NPM packages extracted from websites using Wappalyzer.

**Features**

- Extracts package information using Wappalyzer.
- Filters JavaScript libraries and verifies their availability in the NPM registry.
- Generates a package.json file for valid dependencies.
- Runs npm audit to detect vulnerabilities and saves a detailed report.

**Prerequisites**

1.	Install Node.js and NPM: Node.js Downloads.
2.	Install Python (3.6+).
3.	Install Wappalyzer:

```
git clone https://github.com/tunetheweb/wappalyzer.git
cd wappalyzer
npm install
```


# Usage

## Manual

Place main.py and scan.sh scripts in the wappalyzer folder

```./scan.sh <http://<url>>```

## Docker

```
docker pull enderphan94/webpack:latest
docker run --rm enderphan94/webpack <https://url>
```

**Console Output**

```
[RESULT] Technologies:
Name                            Version
------------------------------  ---------
PHP                             N/A
Bootstrap                       4.6.2
PayPal                          N/A
Google Ads                      N/A
theTradeDesk                    N/A
Hotjar                          N/A
Google Tag Manager              N/A
CookieFirst                     N/A
Akamai Bot Manager              N/A
Quantcast Measure               N/A
Microsoft Advertising           N/A
LazySizes                       N/A
jQuery                          3.7.1
Google Analytics                N/A
Facebook Pixel                  2.9.180
core-js                         3.32.2
reCAPTCHA                       N/A
Priority Hints                  N/A
Google Ads Conversion Tracking  N/A
Sectigo                         N/A
Akamai                          N/A
Webpack                         N/A
PWA                             N/A

Sanitized package name: Lodash -> lodash
Skipping package not in 'javascript-libraries': Contact Form 7
Generated package.json.
Creating package-lock.json...
Installing dependencies...
Running npm audit...
npm audit report
...
Saved audit report to audit-report.txt.
```