#!/usr/bin/env python3
"""
Complete Project Startup Script
Starts both frontend and backend services for the Investment Research Platform
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("\n" + "="*60)
    print("🚀 AI Investment Research Platform")
    print("   Full-Stack ML Platform Startup")
    print("="*60)

def check_dependencies():
    """Check if required dependencies are available"""
    print("\n📋 Checking dependencies...")
    
    # Check Python dependencies
    try:
        import uvicorn
        import fastapi
        print("✅ Backend Python dependencies: OK")
    except ImportError as e:
        print(f"❌ Backend Python dependencies missing: {e}")
        print("   Run: pip install -r backend/requirements.txt")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found")
        return False
    
    # Check npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm: {result.stdout.strip()}")
        else:
            print("❌ npm not found")
            return False
    except FileNotFoundError:
        print("❌ npm not found")
        return False
    
    return True

def setup_frontend():
    """Set up frontend dependencies"""
    print("\n📦 Setting up frontend...")
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("📥 Installing frontend dependencies...")
        try:
            result = subprocess.run(
                ["npm", "install"], 
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Frontend dependencies installed")
            else:
                print(f"❌ Frontend setup failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Frontend setup error: {e}")
            return False
    else:
        print("✅ Frontend dependencies already installed")
    
    return True

def start_backend():
    """Start the backend server"""
    print("\n🔧 Starting backend server...")
    backend_dir = Path("backend")
    
    try:
        # Start backend server
        backend_process = subprocess.Popen(
            [sys.executable, "start_backend.py"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✅ Backend server starting...")
        return backend_process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the frontend development server"""
    print("\n🎨 Starting frontend development server...")
    frontend_dir = Path("frontend")
    
    try:
        # Start frontend dev server
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✅ Frontend server starting...")
        return frontend_process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def monitor_processes(backend_proc, frontend_proc):
    """Monitor both processes and handle output"""
    def print_output(proc, name, color_code):
        for line in iter(proc.stdout.readline, ''):
            if line:
                print(f"\033[{color_code}m[{name}]\033[0m {line.strip()}")
    
    # Start monitoring threads
    if backend_proc:
        backend_thread = threading.Thread(
            target=print_output, 
            args=(backend_proc, "BACKEND", "34")  # Blue
        )
        backend_thread.daemon = True
        backend_thread.start()
    
    if frontend_proc:
        frontend_thread = threading.Thread(
            target=print_output, 
            args=(frontend_proc, "FRONTEND", "32")  # Green
        )
        frontend_thread.daemon = True
        frontend_thread.start()

def main():
    """Main startup function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing dependencies.")
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        print("\n❌ Frontend setup failed.")
        sys.exit(1)
    
    # Start servers
    backend_proc = start_backend()
    time.sleep(3)  # Give backend time to start
    
    frontend_proc = start_frontend()
    time.sleep(2)  # Give frontend time to start
    
    if not backend_proc or not frontend_proc:
        print("\n❌ Failed to start one or more services.")
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        sys.exit(1)
    
    # Print success message
    print("\n🎉 All services started successfully!")
    print("\n📊 Access your services:")
    print("   Frontend: http://localhost:3000")
    print("   Backend API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("\n👤 Create an account or login with your existing credentials")
    print("\n❌ Press Ctrl+C to stop all services")
    
    # Monitor processes
    monitor_processes(backend_proc, frontend_proc)
    
    try:
        # Wait for processes
        while True:
            if backend_proc.poll() is not None:
                print("\n❌ Backend process stopped unexpectedly")
                break
            if frontend_proc.poll() is not None:
                print("\n❌ Frontend process stopped unexpectedly")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all services...")
        
        # Terminate processes
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        
        # Wait for clean shutdown
        time.sleep(2)
        
        # Force kill if still running
        if backend_proc and backend_proc.poll() is None:
            backend_proc.kill()
        if frontend_proc and frontend_proc.poll() is None:
            frontend_proc.kill()
        
        print("✅ All services stopped successfully")

if __name__ == "__main__":
    main()
