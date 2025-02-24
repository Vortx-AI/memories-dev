# GCP Standalone Deployment Test Suite

This test suite validates the configuration files for GCP standalone deployment, ensuring that all hardware, infrastructure, and security settings are correctly specified.

## Overview

The test suite includes validation for:
- Hardware configurations (CPU, GPU, Memory, Network)
- Infrastructure settings
- Storage configurations
- Network settings
- Security configurations
- Performance optimizations
- Monitoring settings

## Prerequisites

- Python 3.8 or higher
- GCP Service Account with necessary permissions
- Access to the target GCP project

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Set up GCP credentials:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

2. Configure test environment variables:
```bash
export GCP_PROJECT_ID="your-project-id"
export TEST_SERVICE_ACCOUNT="test-service-account@your-project.iam.gserviceaccount.com"
```

## Running Tests

1. Run all tests:
```bash
python run_tests.py --config-dir ../config --test-config config_test.yaml
```

2. Run specific test suites:
```bash
python run_tests.py --config-dir ../config --test-config config_test.yaml --suite hardware_tests
```

## Test Reports

Test reports are generated in JSON format and stored in `/tmp/test-results/`. Each report includes:
- Timestamp
- Total number of tests
- Number of passed tests
- Number of failed tests
- Success rate

## Test Suites

### Hardware Tests
- CPU configuration validation (Intel and AMD)
- GPU configuration validation (NVIDIA)
- Memory configuration validation
- Network interface validation

### Infrastructure Tests
- Machine type validation
- Availability zone configuration
- Resource allocation validation

### Storage Tests
- Disk configuration validation
- Performance settings validation
- Backup configuration validation

### Network Tests
- VPC configuration validation
- Firewall rules validation
- Network performance settings validation

### Security Tests
- Service account validation
- Shielded VM configuration validation
- Security settings validation

### Performance Tests
- CPU performance settings validation
- Memory optimization validation
- Network performance validation

### Monitoring Tests
- Metrics collection validation
- Alert policy validation
- Logging configuration validation

## Notifications

Test failures are reported via:
- Slack (#deployment-tests channel)
- Email (ops@memories-app.com)

## Cleanup

Test resources are automatically cleaned up after test completion. Logs are retained for 7 days in the specified output directory.

## Contributing

1. Follow the existing test structure when adding new tests
2. Update the test configuration file (config_test.yaml) with new test cases
3. Add corresponding validation methods to the ConfigurationValidator class
4. Update this README with any new test categories or requirements

## Troubleshooting

Common issues and solutions:

1. Authentication Errors:
   - Verify GOOGLE_APPLICATION_CREDENTIALS is correctly set
   - Ensure service account has required permissions

2. Configuration Loading Errors:
   - Check file paths in --config-dir argument
   - Verify YAML syntax in configuration files

3. Test Failures:
   - Check test report for specific failure details
   - Verify configuration values match expected values in test cases

## Support

For issues or questions, contact:
- Slack: #deployment-tests
- Email: ops@memories-app.com 