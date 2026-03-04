#!/usr/bin/env python3
"""
Setup Verification Script
Checks if all dependencies and configurations are correct before running the application
"""
import sys
import os
import subprocess
from pathlib import Path


class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE} {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 9:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.9+")
        return False


def check_system_dependencies():
    """Check system dependencies"""
    print_header("Checking System Dependencies")
    
    dependencies = {
        'tesseract': 'Tesseract OCR',
        'pdfinfo': 'Poppler (pdf2image)'
    }
    
    all_ok = True
    for cmd, name in dependencies.items():
        try:
            subprocess.run([cmd, '--version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         check=True)
            print_success(f"{name} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error(f"{name} is NOT installed")
            all_ok = False
    
    return all_ok


def check_python_packages():
    """Check Python packages"""
    print_header("Checking Python Packages")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'langchain',
        'langchain_groq',
        'pinecone',
        'sentence_transformers',
        'transformers',
        'PyPDF2',
        'python-docx',
        'pytesseract'
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package} - OK")
        except ImportError:
            print_error(f"{package} - NOT FOUND")
            all_ok = False
    
    return all_ok


def check_environment_variables():
    """Check environment variables"""
    print_header("Checking Environment Variables")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print_error(".env file not found")
        print_info("Run: cp .env.example .env")
        return False
    
    print_success(".env file exists")
    
    # Check required variables
    required_vars = ['GROQ_API_KEY', 'PINECONE_API_KEY']
    all_ok = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f'your_{var.lower()}_here':
            print_success(f"{var} is set")
        else:
            print_error(f"{var} is NOT set or is placeholder")
            all_ok = False
    
    return all_ok


def check_directory_structure():
    """Check directory structure"""
    print_header("Checking Directory Structure")
    
    required_dirs = [
        'app',
        'app/services',
        'app/routes',
        'app/utils',
        'app/models',
        'data/uploads'
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_success(f"{dir_path}/ - OK")
        else:
            print_error(f"{dir_path}/ - NOT FOUND")
            all_ok = False
    
    return all_ok


def check_api_connectivity():
    """Check API connectivity"""
    print_header("Checking API Connectivity (Optional)")
    
    # Only check if environment variables are set
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv('GROQ_API_KEY')
    pinecone_key = os.getenv('PINECONE_API_KEY')
    
    if not groq_key or groq_key.startswith('your_'):
        print_warning("Groq API key not configured - Skipping connectivity check")
        return None
    
    if not pinecone_key or pinecone_key.startswith('your_'):
        print_warning("Pinecone API key not configured - Skipping connectivity check")
        return None
    
    # Test Pinecone
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=pinecone_key)
        pc.list_indexes()
        print_success("Pinecone connection - OK")
    except Exception as e:
        print_error(f"Pinecone connection failed: {str(e)}")
        return False
    
    print_info("Groq API check requires making actual API calls")
    print_info("Will be verified when you run the application")
    
    return True


def print_summary(results):
    """Print verification summary"""
    print_header("Verification Summary")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"Total Checks: {total}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    if skipped > 0:
        print_warning(f"Skipped: {skipped}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All critical checks passed!{Colors.END}")
        print(f"\n{Colors.GREEN}You can now run the application:{Colors.END}")
        print(f"{Colors.BLUE}  python -m app.main{Colors.END}")
        print(f"{Colors.BLUE}or{Colors.END}")
        print(f"{Colors.BLUE}  uvicorn app.main:app --reload{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some checks failed!{Colors.END}")
        print(f"\n{Colors.YELLOW}Please fix the issues above before running the application.{Colors.END}")


def main():
    """Main verification function"""
    print(f"\n{Colors.BOLD}Document Q&A System - Setup Verification{Colors.END}")
    print(f"{Colors.BOLD}Version 1.0.0{Colors.END}")
    
    results = {
        'Python Version': check_python_version(),
        'System Dependencies': check_system_dependencies(),
        'Python Packages': check_python_packages(),
        'Environment Variables': check_environment_variables(),
        'Directory Structure': check_directory_structure(),
        'API Connectivity': check_api_connectivity()
    }
    
    print_summary(results)
    
    # Return exit code
    if any(r is False for r in results.values()):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Verification cancelled by user{Colors.END}")
        sys.exit(1)
