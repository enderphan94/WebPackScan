import os
import json
import subprocess
import re
import argparse
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from tabulate import tabulate
from urllib.parse import urlparse

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
            "Version": tech["version"] if tech.get("version") else "None"
        }
        for tech in json_data.get("technologies", [])
        if tech["confidence"] == 100
    ]
    if technologies:
        print("\n[TECHNOLOGIES]")
        print(tabulate(technologies, headers="keys", tablefmt="pretty"))
    else:
        print("\n[TECHNOLOGIES]")
        print("No technologies found with confidence 100.")

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
    dependencies = {}
    for tech in json_data.get("technologies", []):
        name = tech.get("name", "").lower()
        version = tech.get("version")
        if version:
            dependencies[name] = version
    return dependencies

def include_ui_frameworks(json_data, dependencies):
    ui_frameworks = {
        "bootstrap": "^4.1.0",
        "foundation-sites": "^6.7.5",
        "materialize-css": "^1.0.0",
        "semantic-ui": "^2.4.2",
        "bulma": "^0.9.4"
    }

    for tech in json_data.get("technologies", []):
        name = tech.get("name", "").lower()
        version = tech.get("version")
        if name in ui_frameworks and version:
            dependencies[name] = version

def run_npm_audit():
    try:
        print("\n[VULNERABLE PACKAGES]")
        result = subprocess.run(["npm", "audit"], 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              text=True,
                              check=False)
        
        # Parse and clean up the output
        lines = result.stdout.split('\n')
        output_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and npm headers
            if not line or any(skip in line.lower() for skip in [
                'npm audit report', 
                'npm audit fix',
                'will install',
                'node_modules/',
                'to address',
                'fix available'
            ]):
                i += 1
                continue
            
            # Check for package name patterns
            if (
                (' - ' in line or '<=' in line) or  # Version range pattern
                ('crypto-js' in line.lower()) or    # Special case for crypto-js
                (i + 1 < len(lines) and lines[i + 1].strip().startswith('Severity:'))  # Next line is severity
            ):
                output_lines.append(line)  # Add package name
                
                # Add severity if next line
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('Severity:'):
                    output_lines.append(lines[i + 1].strip())
                    i += 2
                    continue
            
            # Add vulnerability descriptions
            elif 'github.com/advisories' in line:
                output_lines.append(line)
            
            # Add severity lines
            elif line.startswith('Severity:'):
                output_lines.append(line)
            
            # Add summary line (always at the end)
            elif 'severity vulnerabilit' in line:
                output_lines.append(line)
            
            i += 1
        
        # Print cleaned output
        print('\n'.join(output_lines))

    except subprocess.CalledProcessError as e:
        if e.returncode != 1:  # npm audit returns 1 when it finds vulnerabilities
            print("[ERROR] Failed to run npm audit")
            exit(1)

def extract_metadata(json_data):
    metadata = {}
    if "urls" in json_data:
        metadata["urls"] = json_data["urls"]
    return metadata

def create_package_json(dependencies, metadata, output_path):
    package_data = {
        "name": "scan-result",
        "description": "Vulnerability scan result",
        "dependencies": dependencies
    }
    
    try:
        with open(output_path, 'w') as f:
            json.dump(package_data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to create package.json: {str(e)}")
        exit(1)

def install_dependencies():
    try:
        subprocess.run(["npm", "install", "--package-lock-only"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install dependencies")
        exit(1)

def main():
    parser = argparse.ArgumentParser(description="Check vulnerabilities in NPM packages based on JSON input.")
    parser.add_argument("input_file", type=str, help="Path to the input JSON file.")
    args = parser.parse_args()

    # Read the input JSON
    json_data = read_input_json(args.input_file)
    if not json_data:
        return

    # Create output folder
    input_file_name = Path(args.input_file).stem
    output_folder = os.path.join(os.getcwd(), input_file_name)
    os.makedirs(output_folder, exist_ok=True)
    os.chdir(output_folder)

    # Process dependencies
    dependencies = filter_packages(json_data)
    include_ui_frameworks(json_data, dependencies)

    # Extract metadata and create package.json
    metadata = extract_metadata(json_data)
    package_json_path = os.path.join(output_folder, "package.json")
    create_package_json(dependencies, metadata, package_json_path)

    # Print technologies
    print_technologies(json_data)

    # Install dependencies and run audit
    install_dependencies()
    run_npm_audit()


if __name__ == "__main__":
    main()