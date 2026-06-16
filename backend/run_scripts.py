#!/usr/bin/env python3
"""
Convenience wrapper to run scripts from the scripts/ folder
Usage: python run_scripts.py --list
       python run_scripts.py --name generate_lms_batch_reports
       python run_scripts.py --all-language
       python run_scripts.py --all-lms
"""

import sys
import subprocess
import argparse
from pathlib import Path

# Add scripts folder to path
SCRIPTS_DIR = Path(__file__).parent / "scripts"


def list_scripts():
    """List all available scripts"""
    print("\n📜 Available Scripts:")
    print("=" * 50)
    
    scripts = sorted(SCRIPTS_DIR.glob("*.py"))
    
    print("\n🔧 Language Survey Scripts:")
    for s in scripts:
        if "language" in s.name or "cluster" in s.name:
            print(f"   • {s.name}")
    
    print("\n📊 LMS Scripts:")
    for s in scripts:
        if "lms" in s.name or "batch" in s.name:
            print(f"   • {s.name}")
    
    print("\n📋 Template Scripts:")
    for s in scripts:
        if "template" in s.name:
            print(f"   • {s.name}")
    
    print("\n🔄 Other Scripts:")
    for s in scripts:
        if not any(x in s.name for x in ["language", "lms", "batch", "template", "cluster"]):
            print(f"   • {s.name}")


def run_script(script_name: str):
    """Run a specific script"""
    script_path = SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_name}")
        print(f"   Available scripts: {[s.name for s in SCRIPTS_DIR.glob('*.py')]}")
        return False
    
    print(f"\n🚀 Running: {script_name}")
    print("=" * 50)
    
    result = subprocess.run([sys.executable, str(script_path)], cwd=Path(__file__).parent)
    return result.returncode == 0


def run_all_language():
    """Run all language survey scripts"""
    scripts = [
        "generate_cluster_template.py",
        "generate_dynamic_language_templates.py",
        "generate_language_uploader_template.py",
        "generate_dynamic_workbook.py",
    ]
    
    for script in scripts:
        print(f"\n📚 Running language script: {script}")
        if not run_script(script):
            print(f"⚠️ {script} had issues, continuing...")


def run_all_lms():
    """Run all LMS scripts"""
    scripts = [
        "generate_lms_templates.py",
        "generate_lms_batch_reports.py",
    ]
    
    for script in scripts:
        print(f"\n🎓 Running LMS script: {script}")
        if not run_script(script):
            print(f"⚠️ {script} had issues, continuing...")


def main():
    parser = argparse.ArgumentParser(description="Run scripts from the scripts/ folder")
    parser.add_argument("--list", "-l", action="store_true", help="List all available scripts")
    parser.add_argument("--name", "-n", help="Run a specific script by name")
    parser.add_argument("--all-language", "-al", action="store_true", help="Run all language survey scripts")
    parser.add_argument("--all-lms", "-alm", action="store_true", help="Run all LMS scripts")
    parser.add_argument("--all-templates", "-at", action="store_true", help="Run all template generation scripts")
    
    args = parser.parse_args()
    
    if args.list:
        list_scripts()
    elif args.name:
        run_script(args.name)
    elif args.all_language:
        run_all_language()
    elif args.all_lms:
        run_all_lms()
    elif args.all_templates:
        run_script("generate_templates.py")
        run_script("generate_lms_templates.py")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
