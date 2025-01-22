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
        if any(category.get("slug") == "ui-frameworks" for category in package.get("categories", [])):
            name = sanitize_package_name(package.get("name", ""))
            version = package.get("version")
            if name and version:
                dependencies[name] = version
                print(f"[INFO] Included UI framework: {name} ({version})")


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


import subprocess

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
            stdout=subprocess.PIPE,  # Capture standard output
            stderr=subprocess.PIPE,  # Capture standard error
            text=True, 
            check=False
        )

        # Print the audit results to the terminal
        print(result.stdout)

        # Save the audit report to a file
        with open("audit-report.txt", "w") as f:
            f.write(result.stdout)
            print("[INFO] Saved audit report to audit-report.txt.")
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