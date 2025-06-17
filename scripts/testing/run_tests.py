"""
Test Runner for X Engagement Bot

Comprehensive test runner for the production monitoring system.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests(test_type="unit", verbose=True, coverage=False):
    """Run tests with specified options."""
    
    # Ensure we're in the project directory
    os.chdir(Path(__file__).parent)
    
    # Add src to path for test imports
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path('src').absolute()) + ':' + env.get('PYTHONPATH', '')
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term'])
    
    # Add test markers
    if test_type:
        cmd.extend(['-m', test_type])
    
    # Add test directory
    cmd.append('tests/')
    
    # Add short traceback format
    cmd.extend(['--tb=short'])
    
    print(f"Running tests: {' '.join(cmd)}")
    print("=" * 60)
    
    # Run tests
    result = subprocess.run(cmd, env=env)
    
    return result.returncode == 0


def run_specific_test_file(test_file, verbose=True):
    """Run a specific test file."""
    
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path('src').absolute()) + ':' + env.get('PYTHONPATH', '')
    
    cmd = ['python', '-m', 'pytest', f'tests/unit/{test_file}']
    
    if verbose:
        cmd.append('-v')
    
    cmd.extend(['--tb=short'])
    
    print(f"Running specific test: {test_file}")
    print("=" * 60)
    
    result = subprocess.run(cmd, env=env)
    return result.returncode == 0


def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "unit":
            success = run_tests("unit", verbose=True)
        elif command == "integration": 
            success = run_tests("integration", verbose=True)
        elif command == "all":
            success = run_tests(None, verbose=True)
        elif command == "coverage":
            success = run_tests("unit", verbose=True, coverage=True)
        elif command.endswith(".py"):
            success = run_specific_test_file(command, verbose=True)
        else:
            print(f"Unknown command: {command}")
            print("Available commands: unit, integration, all, coverage, <test_file.py>")
            sys.exit(1)
    else:
        # Default: run unit tests
        success = run_tests("unit", verbose=True)
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()