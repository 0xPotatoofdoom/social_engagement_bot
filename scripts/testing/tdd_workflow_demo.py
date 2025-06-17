#!/usr/bin/env python3
"""
TDD Workflow Demonstration
Shows how proper TDD would have caught the dual email bug
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and display results"""
    print(f"\n🔧 {description}")
    print(f"Running: {cmd}")
    print("-" * 50)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ PASSED")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ FAILED")
        if result.stderr:
            print(result.stderr)
        if result.stdout:
            print(result.stdout)
    
    return result.returncode == 0

def main():
    """Demonstrate proper TDD workflow"""
    print("🎯 TDD Workflow Demonstration")
    print("How we should have caught the dual email bug")
    print("=" * 60)
    
    # Set Python path
    os.environ['PYTHONPATH'] = '/Users/matt/Dev/pod_x_bot/src'
    
    print("\n📋 STEP 1: Write Integration Test First")
    print("✅ Created: tests/integration/test_single_email_flow.py")
    print("This test verifies ONLY ONE email is sent per cycle")
    
    print("\n📋 STEP 2: Run Integration Test")
    integration_passed = run_command(
        "python -m pytest tests/integration/test_single_email_flow.py -v",
        "Run integration test for single email flow"
    )
    
    print("\n📋 STEP 3: Run All Unit Tests")
    unit_passed = run_command(
        "python -m pytest tests/unit/ -v --tb=short",
        "Run existing unit tests"
    )
    
    print("\n📋 STEP 4: Verify Email System Tests")
    email_passed = run_command(
        "python -m pytest tests/unit/test_email_alert_system.py::TestEmailAlertSystem::test_concise_email_structure -v",
        "Run concise email structure test"
    )
    
    print("\n📊 TDD WORKFLOW RESULTS")
    print("=" * 40)
    
    if integration_passed:
        print("✅ Integration Test: PASSED - Single email flow working")
    else:
        print("❌ Integration Test: FAILED - Would have caught dual email bug!")
    
    if unit_passed:
        print("✅ Unit Tests: PASSED - Individual components working")
    else:
        print("⚠️  Unit Tests: Some issues found")
    
    if email_passed:
        print("✅ Email Tests: PASSED - Concise format working")
    else:
        print("⚠️  Email Tests: Issues with concise format")
    
    print("\n🎯 KEY INSIGHTS:")
    print("• Integration tests catch system-level bugs unit tests miss")
    print("• Email flow testing prevents dual sends")
    print("• TDD workflow ensures all tests pass before deployment")
    print("• Proper test coverage = fewer production bugs")
    
    if integration_passed and unit_passed and email_passed:
        print("\n🚀 READY FOR DEPLOYMENT")
        print("All tests pass - safe to deploy to production")
    else:
        print("\n🛑 NOT READY FOR DEPLOYMENT")
        print("Fix failing tests before deploying")
    
    print("\n💡 LESSON LEARNED:")
    print("The dual email bug happened because we had:")
    print("❌ Unit tests (individual methods)")
    print("❌ Missing integration tests (system flow)")
    print("✅ Now we have both levels of testing!")

if __name__ == "__main__":
    main()