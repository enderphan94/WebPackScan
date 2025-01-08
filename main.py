import json
import subprocess
import re
import argparse


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


def filter_packages(json_data):
    valid_packages = {}
    for package in json_data.get("technologies", []):
        if not any(category.get("slug") == "javascript-libraries" for category in package.get("categories", [])):
            print(f"Skipping package not in 'javascript-libraries': {package['name']}")
            continue

        name = sanitize_package_name(package["name"])
        version = package.get("version")
        if version and is_package_available(name):
            valid_packages[name] = version
        else:
            print(f"Skipping invalid or unavailable package: {name}")
    return valid_packages


def sanitize_package_name(name):
    sanitized_name = re.sub(r"[^a-zA-Z0-9-_]", "-", name).lower()
    print(f"Sanitized package name: {name} -> {sanitized_name}")
    return sanitized_name


def create_package_json(dependencies, output_path):
    if not dependencies:
        print("No valid dependencies found. Exiting.")
        exit(0)  # Exit gracefully if no valid dependencies are present

    package_json = {
        "name": "vulnerability-check",
        "version": "1.0.0",
        "dependencies": dependencies
    }
    with open(output_path, "w") as f:
        json.dump(package_json, f, indent=4)
    print(f"Generated {output_path}.")


def install_dependencies():
    try:
        print("Creating package-lock.json...")
        subprocess.run(["npm", "install", "--package-lock-only"], check=True)  # Create lock file only
        print("Installing dependencies...")
        subprocess.run(["npm", "install"], check=False)  # Allow errors for invalid packages
    except subprocess.CalledProcessError as e:
        print(f"Error during npm install: {e}")
        exit(1)


def run_npm_audit():
    try:
        print("Running npm audit...")
        result = subprocess.run(["npm", "audit"], capture_output=True, text=True, check=False)

        # Print the full audit report
        print(result.stdout)

        # Save the audit report to a file
        with open("audit-report.txt", "w") as f:
            f.write(result.stdout)
            print("Saved audit report to audit-report.txt.")
    except subprocess.CalledProcessError as e:
        print(f"Error during npm audit: {e.stderr}")
        exit(1)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Check vulnerabilities in NPM packages based on JSON input.")
    parser.add_argument("input_file", type=str, help="Path to the input JSON file.")
    parser.add_argument(
        "--output-file",
        type=str,
        default="package.json",
        help="Path to the output package.json file (default: package.json)."
    )
    args = parser.parse_args()

    json_data = read_input_json(args.input_file)

    dependencies = filter_packages(json_data)

    create_package_json(dependencies, args.output_file)

    install_dependencies()

    run_npm_audit()


# Entry point
if __name__ == "__main__":
    main()