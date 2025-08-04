#!/usr/bin/env python3
"""
Setup script for YourHealth1Place FastAPI Backend
This script helps with initial configuration and setup of the multi-service architecture.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🏥 YourHealth1Place FastAPI Backend Setup")
    print("=" * 60)
    print("This script will help you set up the multi-service architecture")
    print("with Supabase, AWS, and Akeyless integration.")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def setup_environment():
    """Set up environment file"""
    print("\n🔧 Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("⚠️  .env file already exists. Skipping...")
        return
    
    if not env_example.exists():
        print("❌ env.example file not found")
        sys.exit(1)
    
    # Copy env.example to .env
    with open(env_example, 'r') as src, open(env_file, 'w') as dst:
        dst.write(src.read())
    
    print("✅ Environment file created (.env)")
    print("📝 Please edit .env with your actual configuration values")

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating necessary directories...")
    
    directories = [
        "logs",
        "data",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def print_setup_instructions():
    """Print setup instructions for external services"""
    print("\n" + "=" * 60)
    print("🔧 MANUAL SETUP REQUIRED")
    print("=" * 60)
    
    print("\n📋 Supabase Setup:")
    print("1. Create a Supabase project at https://supabase.com")
    print("2. Get your project URL and API keys")
    print("3. Create the following tables in Supabase:")
    print("   - user_profiles (for personal information)")
    print("   - user_settings (for lightweight metadata)")
    print("4. Update SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY in .env")
    
    print("\n☁️ AWS Setup:")
    print("1. Create an AWS account and set up IAM user")
    print("2. Create S3 bucket for health data storage")
    print("3. Set up AWS Athena database and workgroup")
    print("4. Configure KMS encryption for S3 bucket")
    print("5. Update AWS_* variables in .env")
    
    print("\n🔐 Akeyless Setup:")
    print("1. Create an Akeyless account at https://akeyless.io")
    print("2. Set up access credentials")
    print("3. Create encryption keys for different data types:")
    print("   - health-data-vital_signs")
    print("   - health-data-lab_results")
    print("   - health-data-medications")
    print("4. Update AKEYLESS_* variables in .env")
    
    print("\n🗄️ Database Setup:")
    print("1. Install PostgreSQL or use a cloud service")
    print("2. Create a database for the application")
    print("3. Update DATABASE_URL in .env")
    print("4. Run database migrations: alembic upgrade head")

def print_next_steps():
    """Print next steps after setup"""
    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS")
    print("=" * 60)
    
    print("\n1. 📝 Edit .env file with your configuration")
    print("2. 🗄️ Set up external services (see instructions above)")
    print("3. 🔄 Run database migrations:")
    print("   alembic upgrade head")
    print("4. 🚀 Start the application:")
    print("   python run.py")
    print("5. 📚 Access API documentation:")
    print("   http://localhost:8000/docs")
    
    print("\n" + "=" * 60)
    print("✅ Setup complete! Follow the manual setup instructions above.")
    print("=" * 60)

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Setup environment
    setup_environment()
    
    # Create directories
    create_directories()
    
    # Print setup instructions
    print_setup_instructions()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main() 