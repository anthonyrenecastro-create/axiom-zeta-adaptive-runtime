#!/usr/bin/env python3
"""
Enterprise Features Verification Script

Verifies that all enterprise features are properly installed and configured.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()


def verify_feature_files() -> Dict[str, List[Tuple[str, bool]]]:
    """Verify all feature files exist."""
    features = {
        "API Documentation": [
            ("utils/api_docs.py", True)
        ],
        "TLS/HTTPS Configuration": [
            ("utils/tls_config.py", True)
        ],
        "Dependency Scanning": [
            (".github/dependabot.yml", True),
            (".github/workflows/security-scan.yml", True)
        ],
        "Distributed Tracing": [
            ("utils/distributed_tracing.py", True)
        ],
        "Circuit Breakers": [
            ("utils/circuit_breaker.py", True)
        ],
        "A/B Testing": [
            ("utils/ab_testing.py", True)
        ],
        "Canary Deployment": [
            ("k8s/canary-deployment.yaml", True),
            ("scripts/canary-deploy.sh", True)
        ],
        "Blue-Green Deployment": [
            ("k8s/blue-green-deployment.yaml", True),
            ("scripts/blue-green-deploy.sh", True)
        ],
        "Chaos Engineering": [
            ("utils/chaos_engineering.py", True),
            ("scripts/run_chaos_tests.py", True)
        ]
    }
    
    results = {}
    for feature, files in features.items():
        results[feature] = [(f, check_file_exists(f)) for f, _ in files]
    
    return results


def verify_dependencies() -> List[Tuple[str, bool]]:
    """Verify required dependencies are in requirements.txt."""
    required_deps = [
        "flask-swagger-ui",
        "opentelemetry-api",
        "opentelemetry-sdk",
        "opentelemetry-instrumentation-flask",
        "opentelemetry-exporter-jaeger",
        "opentelemetry-exporter-zipkin"
    ]
    
    try:
        with open("requirements.txt", "r") as f:
            content = f.read().lower()
        
        return [(dep, dep in content) for dep in required_deps]
    except FileNotFoundError:
        return [(dep, False) for dep in required_deps]


def verify_scripts_executable() -> List[Tuple[str, bool]]:
    """Verify deployment scripts are executable."""
    scripts = [
        "scripts/canary-deploy.sh",
        "scripts/blue-green-deploy.sh",
        "scripts/run_chaos_tests.py"
    ]
    
    results = []
    for script in scripts:
        path = Path(script)
        if path.exists():
            import os
            is_executable = os.access(path, os.X_OK)
            results.append((script, is_executable))
        else:
            results.append((script, False))
    
    return results


def print_results():
    """Print verification results."""
    print("=" * 70)
    print("ENTERPRISE FEATURES VERIFICATION")
    print("=" * 70)
    print()
    
    # Check feature files
    print("📁 Feature Files:")
    print("-" * 70)
    
    file_results = verify_feature_files()
    all_files_ok = True
    
    for feature, files in file_results.items():
        all_ok = all(exists for _, exists in files)
        status = "✅" if all_ok else "❌"
        print(f"\n{status} {feature}")
        
        for filepath, exists in files:
            file_status = "✓" if exists else "✗"
            print(f"   {file_status} {filepath}")
        
        if not all_ok:
            all_files_ok = False
    
    print()
    print("-" * 70)
    
    # Check dependencies
    print("\n📦 Dependencies:")
    print("-" * 70)
    
    dep_results = verify_dependencies()
    all_deps_ok = all(found for _, found in dep_results)
    
    for dep, found in dep_results:
        status = "✓" if found else "✗"
        print(f"   {status} {dep}")
    
    print("-" * 70)
    
    # Check script permissions
    print("\n🔧 Script Permissions:")
    print("-" * 70)
    
    script_results = verify_scripts_executable()
    all_scripts_ok = all(executable for _, executable in script_results)
    
    for script, executable in script_results:
        status = "✓" if executable else "✗"
        print(f"   {status} {script}")
        if not executable and Path(script).exists():
            print(f"      Run: chmod +x {script}")
    
    print("-" * 70)
    
    # Summary
    print("\n📊 Summary:")
    print("-" * 70)
    
    total_features = len(file_results)
    completed_features = sum(1 for files in file_results.values() if all(e for _, e in files))
    
    print(f"Features: {completed_features}/{total_features} complete")
    print(f"Dependencies: {sum(1 for _, f in dep_results if f)}/{len(dep_results)} found")
    print(f"Scripts: {sum(1 for _, e in script_results if e)}/{len(script_results)} executable")
    
    if all_files_ok and all_deps_ok and all_scripts_ok:
        print("\n✅ ALL CHECKS PASSED - ENTERPRISE READY!")
        print("=" * 70)
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED - REVIEW ABOVE")
        print("=" * 70)
        return 1


def main():
    """Main entry point."""
    try:
        sys.exit(print_results())
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
