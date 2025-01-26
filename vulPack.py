import os
import json
import subprocess
import re
import argparse
from pathlib import Path
from tabulate import tabulate

def read_input_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file - {file_path}")
        exit(1)

def print_technologies(json_data):
    technologies = [
        {
            "Name": tech["name"],
            "Version": tech["version"] if tech["version"] else "N/A"
        }
        for tech in json_data.get("technologies", [])
        if tech["confidence"] == 100
    ]
    if technologies:
        print("\n[RESULT] Technologies:")
        print(tabulate(technologies, headers="keys", tablefmt="pretty"))
        print("\n")
    else:
        print("\n[ERROR] No technologies found with confidence 100.")

def is_package_available(package_name):
    try:
        subprocess.run(
            ["npm", "info", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_valid_versions(package_name):
    try:
        result = subprocess.run(
            ["npm", "view", package_name, "versions", "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        versions = json.loads(result.stdout)
        return versions if isinstance(versions, list) else []
    except subprocess.CalledProcessError:
        print(f"[Error]: Unable to fetch versions for package {package_name}.")
        return []


def filter_packages(json_data):
    valid_packages = {}
    for package in json_data.get("technologies", []):
        if not any(category.get("slug") == "javascript-libraries" for category in package.get("categories", [])):
            print(f"[INFO] Skipping package not in 'javascript-libraries': {package['name']}")
            continue

        name = sanitize_package_name(package["name"])
        version = package.get("version")
        if not version:
            print(f"[INFO] Skipping package with no version specified: {name}")
            continue

        if is_package_available(name):
            valid_versions = get_valid_versions(name)
            if version in valid_versions:
                valid_packages[name] = version
            else:
                print(f"[INFO] Skipping package {name} with invalid version {version}. Valid versions: {valid_versions}")
        else:
            print(f"[INFO] Skipping unavailable package: {name}")
    return valid_packages


def include_ui_frameworks(json_data, dependencies):
    for package in json_data.get("technologies", []):
        # Check if the package belongs to the "ui-frameworks" category
        if any(category.get("slug") == "ui-frameworks" for category in package.get("categories", [])):
            name = sanitize_package_name(package.get("name", ""))
            version = package.get("version")

            if not name:
                print(f"[INFO] Skipping UI framework with no name.")
                continue

            if not version:
                print(f"[INFO] Skipping UI framework {name} with no version specified.")
                continue

            if is_package_available(name):
                valid_versions = get_valid_versions(name)
                if version in valid_versions:
                    dependencies[name] = version
                    print(f"[INFO] Included valid UI framework: {name}@{version}")
                else:
                    print(f"[INFO] Skipping UI framework {name} with invalid version {version}. Valid versions: {valid_versions}")
            else:
                print(f"[INFO] Skipping unavailable UI framework: {name}")


def extract_metadata(json_data):
    metadata = []
    for package in json_data.get("technologies", []):
        if any(category.get("slug") == "ui-frameworks" for category in package.get("categories", [])):
            metadata.append({
                "name": package.get("name"),
                "version": package.get("version"),
                "description": package.get("description"),
                "slug": "ui-frameworks"
            })
    return metadata


def sanitize_package_name(name):
    sanitized_name = re.sub(r"[^a-zA-Z0-9-_]", "-", name).lower()
    print(f"[INFO] Sanitized package name: {name} -> {sanitized_name}")
    return sanitized_name


def create_package_json(dependencies, metadata, output_path):
    if not dependencies:
        print("[ERROR] No valid dependencies found. Creating an empty package.json for scanning.")
        dependencies = {}

    package_json = {
        "name": "vulnerability-check",
        "version": "1.0.0",
        "dependencies": dependencies,
        "metadata": metadata  # Add metadata section for ui-frameworks
    }
    with open(output_path, "w") as f:
        json.dump(package_json, f, indent=4)
    print(f"[INFO] Generated {output_path}.")



def install_dependencies():
    try:
        print("[INFO] Creating package-lock.json...")
        result_lock = subprocess.run(
            ["npm", "install", "--package-lock-only"], 
            stdout=subprocess.PIPE,  # Suppress terminal output
            stderr=subprocess.PIPE, 
            text=True, 
            check=True
        )
        
        print("[INFO] Installing dependencies...")
        result_install = subprocess.run(
            ["npm", "install"], 
            stdout=subprocess.PIPE,  # Suppress terminal output
            stderr=subprocess.PIPE, 
            text=True, 
            check=False  # Allow errors
        )
        
        # Optionally, process or log captured outputs if needed
        if result_install.returncode != 0:
            print(f"[WARNING] npm install completed with warnings/errors:\n{result_install.stderr}")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error during npm install: {e.stderr.strip()}")
        exit(1)


def run_npm_audit():
    try:
        print("[INFO] Checking for vulnerable packages...")
        result = subprocess.run(
            ["npm", "audit"], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, 
            check=False
        )

        # Extract and print only the vulnerability information
        output_lines = result.stdout.split('\n')
        vulnerability_info = []
        capturing = False
        current_package = None
        severity_count = None

        for line in output_lines:
            # Skip npm audit report header
            if line.startswith('# npm audit report'):
                continue
            # Capture severity count
            elif 'severity vulnerability' in line or 'severity vulnerabilities' in line:
                severity_count = line.strip()
                break
            # Skip empty lines unless we're in capturing mode
            elif line.strip() == '':
                if capturing and vulnerability_info:
                    vulnerability_info.append(line)
                continue
            # Skip fix information lines
            elif any(skip_text in line for skip_text in ['fix available', 'Will install', 'node_modules/']):
                continue
            # Capture package version line
            elif not line.startswith(' ') and '  ' in line:  # Package version line
                current_package = f"[VULNERABLE] {line.strip()}"  # Add [VULNERABLE] prefix
                vulnerability_info.append(current_package)
                capturing = True
            # Capture severity and vulnerability information
            elif 'Severity:' in line or (capturing and line.strip()):
                vulnerability_info.append(line.strip())

        if vulnerability_info:
            print('\n'.join(vulnerability_info))
            if severity_count:
                print(severity_count)

        # Save the filtered audit report to a file
        with open("audit-report.txt", "w") as f:
            f.write('\n'.join(vulnerability_info))
            if severity_count:
                f.write('\n' + severity_count)
            print("[INFO] Saved filtered audit report to audit-report.txt.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error during npm audit: {e.stderr}")
        exit(1)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Check vulnerabilities in NPM packages based on JSON input.")
    parser.add_argument("input_file", type=str, help="Path to the input JSON file.")
    args = parser.parse_args()

    # Read the input JSON
    json_data = read_input_json(args.input_file)

    # Create a folder for the scan based on the input file name
    input_file_name = Path(args.input_file).stem
    output_folder = os.path.join(os.getcwd(), input_file_name)
    os.makedirs(output_folder, exist_ok=True)

    # Change the working directory to the output folder
    os.chdir(output_folder)

    # Filter dependencies and include ui-frameworks
    dependencies = filter_packages(json_data)
    include_ui_frameworks(json_data, dependencies)

    # Extract metadata
    metadata = extract_metadata(json_data)

    # Create package.json with dependencies and metadata
    package_json_path = os.path.join(output_folder, "package.json")
    create_package_json(dependencies, metadata, package_json_path)

    # print tech
    print_technologies(json_data)

    # Run npm install and npm audit
    install_dependencies()
    run_npm_audit()


if __name__ == "__main__":
    main()