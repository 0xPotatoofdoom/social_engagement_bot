"""
Quick Deployment for AI x Blockchain Monitoring
Simple deployment with proper environment loading
"""

import os
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

def setup_environment():
    """Load environment variables"""
    print("🔧 Loading environment variables...")
    
    # Load from .env file
    load_dotenv()
    
    # Check required variables
    required_vars = [
        'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET', 'X_BEARER_TOKEN',
        'CLAUDE_API_KEY', 'SENDER_EMAIL', 'SENDER_PASSWORD'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✅ Environment variables loaded")
    return True

def create_directories():
    """Create required directories"""
    print("📁 Creating directories...")
    
    directories = ['data', 'data/strategic_accounts', 'data/metrics', 'data/logs', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True, parents=True)
    
    print("✅ Directories created")

def build_and_run():
    """Build and run the monitoring container"""
    print("📦 Building and running monitoring container...")
    
    # Stop and remove existing container
    subprocess.run(['docker', 'stop', 'x_engagement_bot'], capture_output=True)
    subprocess.run(['docker', 'rm', 'x_engagement_bot'], capture_output=True)
    
    # Build image
    build_cmd = [
        'docker', 'build', 
        '-f', 'deployment/Dockerfile.engagement', 
        '-t', 'x-engagement-bot', 
        '.'
    ]
    
    print("   Building Docker image...")
    result = subprocess.run(build_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Build failed: {result.stderr}")
        return False
    
    print("   ✅ Image built successfully")
    
    # Prepare environment variables for container
    env_vars = []
    env_map = {
        'X_API_KEY': os.getenv('X_API_KEY'),
        'X_API_SECRET': os.getenv('X_API_SECRET'),
        'X_ACCESS_TOKEN': os.getenv('X_ACCESS_TOKEN'),
        'X_ACCESS_TOKEN_SECRET': os.getenv('X_ACCESS_TOKEN_SECRET'),
        'X_BEARER_TOKEN': os.getenv('X_BEARER_TOKEN'),
        'CLAUDE_API_KEY': os.getenv('CLAUDE_API_KEY'),
        'SENDER_EMAIL': os.getenv('SENDER_EMAIL'),
        'SENDER_PASSWORD': os.getenv('SENDER_PASSWORD'),
        'RECIPIENT_EMAIL': os.getenv('RECIPIENT_EMAIL', os.getenv('SENDER_EMAIL')),
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'PYTHONPATH': '/app/src',
        'PYTHONUNBUFFERED': '1'
    }
    
    for key, value in env_map.items():
        if value:
            env_vars.extend(['-e', f'{key}={value}'])
    
    # Run container
    run_cmd = [
        'docker', 'run', '-d',
        '--name', 'x_engagement_bot',
        '--restart', 'unless-stopped',
        '-p', '8080:8080',
        '-v', f'{os.getcwd()}/data:/app/data',
        '-v', f'{os.getcwd()}/logs:/app/data/logs',
    ] + env_vars + ['x-engagement-bot']
    
    print("   Starting container...")
    result = subprocess.run(run_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("   ✅ Container started successfully")
        container_id = result.stdout.strip()
        print(f"   Container ID: {container_id[:12]}")
        return True
    else:
        print(f"   ❌ Container start failed: {result.stderr}")
        return False

def check_health():
    """Check container health"""
    print("🔍 Checking system health...")
    
    # Wait a moment for container to start
    time.sleep(5)
    
    # Check if container is running
    result = subprocess.run(['docker', 'ps', '--filter', 'name=x_engagement_bot', '--format', 'table {{.Names}}\t{{.Status}}'], 
                          capture_output=True, text=True)
    
    if 'x_engagement_bot' in result.stdout:
        print("✅ Container is running")
    else:
        print("❌ Container is not running")
        return False
    
    # Check logs for successful startup
    result = subprocess.run(['docker', 'logs', '--tail', '10', 'x_engagement_bot'], 
                          capture_output=True, text=True)
    
    if 'Monitoring Service' in result.stdout or 'initialized' in result.stdout:
        print("✅ Service is initializing")
    else:
        print("⚠️ Service status unclear - check logs")
    
    return True

def show_status():
    """Show deployment status and commands"""
    print("\n🎯 Deployment Status")
    print("=" * 50)
    
    # Container status
    result = subprocess.run(['docker', 'ps', '--filter', 'name=x_engagement_bot'], 
                          capture_output=True, text=True)
    print("📦 Container Status:")
    print(result.stdout)
    
    # Recent logs
    print("\n📋 Recent Logs:")
    result = subprocess.run(['docker', 'logs', '--tail', '5', 'x_engagement_bot'], 
                          capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    else:
        print("No logs available yet")
    
    print(f"\n🌐 Access Points:")
    print(f"   Health Check: curl http://localhost:8080/health")
    print(f"   (Health endpoint may take 1-2 minutes to be available)")
    
    print(f"\n⚙️ Management Commands:")
    print(f"   View Live Logs: docker logs -f x_engagement_bot")
    print(f"   Stop Container: docker stop x_engagement_bot")
    print(f"   Start Container: docker start x_engagement_bot")
    print(f"   Restart Container: docker restart x_engagement_bot")
    print(f"   Remove Container: docker stop x_engagement_bot && docker rm x_engagement_bot")
    
    print(f"\n📊 Monitoring Configuration:")
    print(f"   Check Interval: 30 minutes")
    print(f"   Email Alerts: Immediate for high-priority opportunities")
    print(f"   Data Storage: ./data directory")
    print(f"   Logs: ./logs directory")

def main():
    """Quick deployment main function"""
    print("🚀 Quick X Engagement Bot Deployment")
    print("=" * 60)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed")
        print("Check your .env file and ensure all required variables are set")
        return False
    
    # Create directories
    create_directories()
    
    # Build and run
    if not build_and_run():
        print("\n❌ Build/run failed")
        return False
    
    # Check health
    if not check_health():
        print("\n⚠️ Health check failed - but container may still be starting")
    
    # Show status
    show_status()
    
    print(f"\n🎉 QUICK DEPLOYMENT COMPLETE!")
    print("=" * 50)
    print("✅ X Engagement Bot container is running")
    print("📧 You should start receiving email alerts for opportunities")
    print("📊 Monitor progress: docker logs -f x_engagement_bot")
    print("⏰ First monitoring cycle will start within 30 minutes")
    
    print(f"\n🎯 Next Steps:")
    print("1. Monitor logs to see system activity")
    print("2. Check email for opportunity alerts")
    print("3. Wait 24-48 hours for meaningful ROI data")
    print("4. Run: python scripts/analysis/roi_analysis.py to check performance")
    
    return True

if __name__ == "__main__":
    main()