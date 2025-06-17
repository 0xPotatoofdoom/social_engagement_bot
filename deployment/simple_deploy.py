"""
Simple Docker Deployment (Alternative Method)
Direct Docker commands if docker-compose has issues
"""

import os
import subprocess
import time
from pathlib import Path

def create_directories():
    """Create required directories"""
    directories = ['data', 'data/strategic_accounts', 'data/metrics', 'data/logs', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True, parents=True)
        print(f"✅ Created {directory}")

def build_image():
    """Build Docker image directly"""
    print("📦 Building Docker image...")
    
    cmd = [
        'docker', 'build', 
        '-f', 'Dockerfile.monitoring', 
        '-t', 'ai-blockchain-monitor', 
        '.'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Docker image built successfully")
        return True
    else:
        print(f"❌ Build failed: {result.stderr}")
        return False

def run_container():
    """Run the monitoring container directly"""
    print("🚀 Starting monitoring container...")
    
    # Load environment variables
    env_vars = []
    required_vars = [
        'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET', 'X_BEARER_TOKEN',
        'CLAUDE_API_KEY', 'SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAIL'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            env_vars.extend(['-e', f'{var}={value}'])
    
    # Add default environment variables
    env_vars.extend([
        '-e', 'SMTP_SERVER=smtp.gmail.com',
        '-e', 'SMTP_PORT=587',
        '-e', 'MONITORING_INTERVAL=1800',  # 30 minutes
        '-e', 'PYTHONPATH=/app/src',
        '-e', 'PYTHONUNBUFFERED=1'
    ])
    
    cmd = [
        'docker', 'run', '-d',
        '--name', 'ai_blockchain_monitor',
        '--restart', 'unless-stopped',
        '-p', '8080:8080',
        '-v', f'{os.getcwd()}/data:/app/data',
        '-v', f'{os.getcwd()}/logs:/app/data/logs',
    ] + env_vars + ['ai-blockchain-monitor']
    
    # Stop existing container if running
    subprocess.run(['docker', 'stop', 'ai_blockchain_monitor'], capture_output=True)
    subprocess.run(['docker', 'rm', 'ai_blockchain_monitor'], capture_output=True)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Container started successfully")
        print(f"Container ID: {result.stdout.strip()}")
        return True
    else:
        print(f"❌ Container start failed: {result.stderr}")
        return False

def check_health():
    """Check if container is healthy"""
    print("🔍 Checking container health...")
    
    for attempt in range(15):
        try:
            result = subprocess.run(['docker', 'logs', '--tail', '5', 'ai_blockchain_monitor'], 
                                  capture_output=True, text=True)
            
            if 'Monitoring Service' in result.stdout or 'initialized' in result.stdout:
                print("✅ Container is starting up")
                return True
        except:
            pass
        
        time.sleep(2)
        print(f"⏳ Attempt {attempt + 1}/15...")
    
    print("⚠️ Container health check inconclusive - check logs manually")
    return False

def show_status():
    """Show container status and commands"""
    print("\n🎯 Monitoring System Status")
    print("=" * 50)
    
    # Show container status
    result = subprocess.run(['docker', 'ps', '--filter', 'name=ai_blockchain_monitor'], 
                          capture_output=True, text=True)
    print("📦 Container Status:")
    print(result.stdout)
    
    # Show recent logs
    print("\n📋 Recent Logs:")
    result = subprocess.run(['docker', 'logs', '--tail', '10', 'ai_blockchain_monitor'], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    print(f"\n🌐 Access Points:")
    print(f"   Health Check: curl http://localhost:8080/health")
    
    print(f"\n⚙️ Management Commands:")
    print(f"   View Logs: docker logs -f ai_blockchain_monitor")
    print(f"   Stop: docker stop ai_blockchain_monitor")
    print(f"   Start: docker start ai_blockchain_monitor")
    print(f"   Restart: docker restart ai_blockchain_monitor")
    print(f"   Remove: docker stop ai_blockchain_monitor && docker rm ai_blockchain_monitor")

def main():
    """Simple deployment main function"""
    print("🚀 Simple AI x Blockchain Monitoring Deployment")
    print("=" * 60)
    
    # Check environment
    if not os.getenv('X_API_KEY'):
        print("❌ Missing environment variables. Load .env file first:")
        print("   export $(cat .env | xargs)")
        return False
    
    # Create directories
    create_directories()
    
    # Build image
    if not build_image():
        return False
    
    # Run container
    if not run_container():
        return False
    
    # Check health
    check_health()
    
    # Show status
    show_status()
    
    print(f"\n🎉 SIMPLE DEPLOYMENT COMPLETE!")
    print("✅ Monitoring container is running")
    print("📊 Check logs: docker logs -f ai_blockchain_monitor")
    
    return True

if __name__ == "__main__":
    main()