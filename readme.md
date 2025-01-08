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

**Step 1: Extract Packages**

Use Wappalyzer to crawl a website and save the data:

```node src/drivers/npm/cli.js https://example.com >> input.json```

**Step 2: Run the Script**

Run the vulnerability checker:

```python script_name.py input.json```

**Step 3: Customize Output (Optional)**

Specify a custom name for the generated package.json:

```python script_name.py input.json --output-file custom-package.json```

**Output**
- package.json: Contains valid dependencies.
- audit-report.txt: Detailed vulnerability report.

**Example**

```
node src/drivers/npm/cli.js https://example.com >> input.json
python script_name.py input.json
```

**Console Output**

```
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