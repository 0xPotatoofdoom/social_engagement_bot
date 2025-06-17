"""
Deploy 24/7 AI x Blockchain Monitoring System
Complete deployment script with environment setup and health checks
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

# Global variable for compose command
COMPOSE_CMD = ['docker', 'compose']

def check_requirements():
    """Check if all requirements are met for deployment"""
    
    print("🔧 Checking deployment requirements...")
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker installed")
        else:
            print("❌ Docker not found")
            return False
    except FileNotFoundError:
        print("❌ Docker not installed")
        return False
    
    # Check Docker Compose (try both old and new syntax)
    compose_cmd = None
    try:
        result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose installed (v2)")
            compose_cmd = ['docker', 'compose']
        else:
            # Try old syntax
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Docker Compose installed (v1)")
                compose_cmd = ['docker-compose']
            else:
                print("❌ Docker Compose not found")
                return False
    except FileNotFoundError:
        print("❌ Docker Compose not installed")
        return False
    
    # Store compose command for later use
    global COMPOSE_CMD
    COMPOSE_CMD = compose_cmd
    
    # Check environment file
    env_file = Path('.env')
    if env_file.exists():
        print("✅ Environment file found")
    else:
        print("❌ .env file not found")
        return False
    
    # Check required environment variables
    required_vars = [
        'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET', 'X_BEARER_TOKEN',
        'CLAUDE_API_KEY', 'SENDER_EMAIL', 'SENDER_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables present")
    
    return True

def create_directories():
    """Create required directories"""
    
    print("📁 Creating directories...")
    
    directories = [
        'data',
        'data/strategic_accounts',
        'data/metrics', 
        'data/logs',
        'logs',
        'dashboard'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True, parents=True)
        print(f"✅ Created {directory}")

def create_dashboard():
    """Create simple metrics dashboard"""
    
    dashboard_dir = Path('dashboard')
    dashboard_dir.mkdir(exist_ok=True)
    
    # Simple HTML dashboard
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI x Blockchain Monitoring Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     color: white; padding: 20px; border-radius: 10px; text-align: center; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                      gap: 20px; margin: 20px 0; }
            .metric-card { background: white; padding: 20px; border-radius: 8px; 
                          box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
            .metric-label { color: #666; margin-top: 5px; }
            .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
            .status.running { background: #d4edda; color: #155724; }
            .status.stopped { background: #f8d7da; color: #721c24; }
            .refresh { margin: 20px 0; text-align: center; }
            .btn { background: #3498db; color: white; padding: 10px 20px; 
                  border: none; border-radius: 5px; cursor: pointer; }
        </style>
        <script>
            function refreshData() {
                fetch('/data/performance_metrics.json')
                    .then(response => response.json())
                    .then(data => updateDashboard(data))
                    .catch(error => console.error('Error:', error));
            }
            
            function updateDashboard(data) {
                if (data.length > 0) {
                    const latest = data[data.length - 1];
                    document.getElementById('opportunities').textContent = latest.opportunities_found || 0;
                    document.getElementById('high-priority').textContent = latest.high_priority_opportunities || 0;
                    document.getElementById('api-calls').textContent = latest.api_calls_made || 0;
                    document.getElementById('efficiency').textContent = (latest.api_efficiency || 0).toFixed(1) + '%';
                    document.getElementById('last-update').textContent = new Date(latest.timestamp).toLocaleString();
                }
            }
            
            setInterval(refreshData, 60000); // Refresh every minute
            window.onload = refreshData;
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 AI x Blockchain Monitoring Dashboard</h1>
                <p>Real-time strategic opportunity detection</p>
            </div>
            
            <div class="status running">
                <strong>System Status:</strong> Monitoring Active
                <br><strong>Last Update:</strong> <span id="last-update">Loading...</span>
            </div>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value" id="opportunities">-</div>
                    <div class="metric-label">Total Opportunities Found</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-value" id="high-priority">-</div>
                    <div class="metric-label">High Priority Opportunities</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-value" id="api-calls">-</div>
                    <div class="metric-label">API Calls Made</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-value" id="efficiency">-</div>
                    <div class="metric-label">API Efficiency</div>
                </div>
            </div>
            
            <div class="refresh">
                <button class="btn" onclick="refreshData()">🔄 Refresh Data</button>
                <button class="btn" onclick="window.open('/data/roi_dashboard.png', '_blank')">📊 ROI Analysis</button>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>📋 Quick Actions</h3>
                <ul>
                    <li><strong>View Logs:</strong> <code>docker logs ai_blockchain_monitor</code></li>
                    <li><strong>Check Health:</strong> <code>curl http://localhost:8080/health</code></li>
                    <li><strong>Stop Monitoring:</strong> <code>docker-compose -f docker-compose.monitoring.yml down</code></li>
                    <li><strong>Update System:</strong> <code>docker-compose -f docker-compose.monitoring.yml up --build -d</code></li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(dashboard_dir / 'index.html', 'w') as f:
        f.write(html_content)
    
    print("✅ Dashboard created at dashboard/index.html")

def build_and_deploy():
    """Build and deploy the monitoring system"""
    
    print("🚀 Building and deploying monitoring system...")
    
    try:
        # Build the image
        print("📦 Building Docker image...")
        result = subprocess.run(
            COMPOSE_CMD + ['-f', 'docker-compose.monitoring.yml', 'build'], 
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Build failed: {result.stderr}")
            return False
        
        print("✅ Docker image built successfully")
        
        # Deploy the system
        print("🚀 Starting monitoring system...")
        result = subprocess.run(
            COMPOSE_CMD + ['-f', 'docker-compose.monitoring.yml', 'up', '-d'], 
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Deployment failed: {result.stderr}")
            return False
        
        print("✅ Monitoring system deployed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

def wait_for_health_check():
    """Wait for the system to be healthy"""
    
    print("🔍 Waiting for system health check...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            import requests
            response = requests.get('http://localhost:8080/health', timeout=5)
            if response.status_code == 200:
                print("✅ System is healthy and running")
                return True
        except:
            pass
        
        time.sleep(2)
        print(f"⏳ Attempt {attempt + 1}/{max_attempts}...")
    
    print("❌ Health check timeout - check logs for issues")
    return False

def show_deployment_status():
    """Show current deployment status"""
    
    print("\n🎯 AI x Blockchain Monitoring System Status")
    print("=" * 60)
    
    try:
        # Check container status
        result = subprocess.run(
            COMPOSE_CMD + ['-f', 'docker-compose.monitoring.yml', 'ps'], 
            capture_output=True, text=True
        )
        
        print("📦 Container Status:")
        print(result.stdout)
        
        # Show recent logs
        print("\n📋 Recent Logs (last 10 lines):")
        result = subprocess.run([
            'docker', 'logs', '--tail', '10', 'ai_blockchain_monitor'
        ], capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        else:
            print("No logs available yet")
        
        print(f"\n🌐 Access Points:")
        print(f"   Health Check: http://localhost:8080/health")
        print(f"   Dashboard: http://localhost:8081")
        print(f"   Metrics API: http://localhost:8081/data/performance_metrics.json")
        
        print(f"\n📊 Monitoring Configuration:")
        print(f"   Monitoring Interval: 30 minutes")
        print(f"   Metrics Save: 1 hour")
        print(f"   Daily Reports: 24 hours")
        
        print(f"\n⚙️ Management Commands:")
        print(f"   View Logs: docker logs -f ai_blockchain_monitor")
        print(f"   Stop System: docker compose -f docker-compose.monitoring.yml down")
        print(f"   Restart: docker compose -f docker-compose.monitoring.yml restart")
        print(f"   Update: docker compose -f docker-compose.monitoring.yml up --build -d")
        
    except Exception as e:
        print(f"Error getting status: {e}")

def generate_roi_analysis():
    """Generate initial ROI analysis"""
    
    print("💰 Generating ROI analysis...")
    
    try:
        subprocess.run([sys.executable, 'roi_analysis.py'], check=True)
        print("✅ ROI analysis completed")
    except subprocess.CalledProcessError:
        print("⚠️ ROI analysis failed - will retry after monitoring data is collected")
    except FileNotFoundError:
        print("⚠️ ROI analysis script not found")

def main():
    """Main deployment function"""
    
    print("🚀 AI x Blockchain Monitoring System Deployment")
    print("=" * 70)
    print(f"📅 Deployment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Pre-deployment checks
    if not check_requirements():
        print("\n❌ Pre-deployment checks failed")
        print("Fix the issues above and try again")
        return False
    
    # Create directories
    create_directories()
    
    # Create dashboard
    create_dashboard()
    
    # Build and deploy
    if not build_and_deploy():
        print("\n❌ Deployment failed")
        return False
    
    # Wait for health check
    if not wait_for_health_check():
        print("\n⚠️ System deployed but health check failed")
        print("Check logs for issues: docker logs ai_blockchain_monitor")
    
    # Generate ROI analysis
    generate_roi_analysis()
    
    # Show status
    show_deployment_status()
    
    print(f"\n🎉 DEPLOYMENT COMPLETE!")
    print("=" * 50)
    print("✅ 24/7 AI x Blockchain monitoring is now active")
    print("📧 You'll receive email alerts for high-priority opportunities")
    print("📊 Dashboard available at: http://localhost:8081")
    print("💰 ROI analysis will update automatically as data is collected")
    
    print(f"\n🎯 Next Steps:")
    print("1. Monitor email for opportunity alerts")
    print("2. Check dashboard for real-time metrics")
    print("3. Review ROI analysis after 7 days of data")
    print("4. Decide on API tier upgrade based on proven value")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)