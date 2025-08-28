# SalesTracker - GitHub Copilot Development Instructions

**ALWAYS FOLLOW THESE INSTRUCTIONS FIRST**. Only use additional search and context gathering if the information in these instructions is incomplete or found to be incorrect.

## Project Overview

SalesTracker is a Python web application that monitors product prices from retailers like Lululemon and Nike, sending personalized daily email notifications. The project has multiple variants (original, improved, enhanced) with a modern enhanced framework supporting extensible retailer integrations.

## Essential Setup & Dependencies

### Environment Requirements
- Python 3.8+ (tested on 3.12)
- All dependencies installed via `pip3 install -r requirements.txt`
- Installation takes ~3 minutes: `time bash install.sh` (includes dependency install + tests)

### Core Dependencies
```bash
pip3 install -r requirements.txt
# Key packages: requests==2.31.0, beautifulsoup4==4.12.3, flask==3.1.2, schedule==1.2.1
```

## Build & Test Commands (CRITICAL TIMINGS)

### Testing - NEVER CANCEL, SET LONG TIMEOUTS
```bash
# Enhanced framework tests: 5 seconds, 28 tests, 100% pass rate
time python3 test_enhanced_framework.py  # TIMEOUT: 60+ seconds

# Original framework tests: <1 second, 11 tests (2 network skips expected)
time python3 test_sale_tracker.py        # TIMEOUT: 30+ seconds

# Web app tests: <1 second, 4 tests  
time python3 test_web_app.py             # TIMEOUT: 30+ seconds
```

### Code Quality - NEVER CANCEL
```bash
# Black formatting: <1 second, may reformat 22 files
time black .                             # TIMEOUT: 60+ seconds

# Import sorting: <1 second, may fix 19 files  
time isort .                             # TIMEOUT: 60+ seconds

# Linting: Use command line flags to avoid config file issues
flake8 --extend-ignore=E203,E501,W503,F401 --max-line-length=127 --exclude=.git,__pycache__,.pytest_cache,.venv,venv,deprecated .
```

### Installation & Health Check
```bash
# Full installation: ~1.5 seconds
time bash install.sh                     # TIMEOUT: 300+ seconds

# System health check: instant
python3 cli_enhanced.py health
```

## Application Variants & Usage

### Enhanced Version (RECOMMENDED)
```bash
# CLI interface with rich functionality
python3 cli_enhanced.py --help
python3 cli_enhanced.py health            # System health check
python3 cli_enhanced.py config            # View full configuration  
python3 cli_enhanced.py retailers         # Show retailer information
python3 cli_enhanced.py test-scraping     # Test scraping (network failures expected in sandbox)

# Web application (Flask debug mode)
python3 web_app_enhanced.py              # Starts on port 5000, takes ~12s to initialize
```

### Original/Improved Versions
```bash
# Original CLI
python3 cli.py --help
python3 cli.py test-scraping

# Original web app  
python3 web_app.py                       # Starts on port 5000
```

## Manual Validation Requirements

### Always Test These Scenarios After Changes:
1. **CLI Health Check**: `python3 cli_enhanced.py health` must show "All systems healthy!"
2. **Configuration Display**: `python3 cli_enhanced.py config` must show complete config without errors
3. **Test Suite**: All test suites must pass with expected skip counts
4. **Web App Startup**: Apps must start and show initialization logs (network failures expected)
5. **Code Quality**: Run `black .` and `isort .` - should complete without Python errors

## Project Structure & Key Files

### Core Components (23 Python files, 4 documentation files)
```
SalesTracker/
├── Enhanced Framework (MODERN - USE THIS)
│   ├── cli_enhanced.py          # Rich CLI with health checks, config display
│   ├── web_app_enhanced.py      # Enhanced web application
│   ├── main_enhanced.py         # Enhanced core logic
│   ├── config_enhanced.py       # Enhanced configuration system
│   └── retailers/               # Extensible retailer framework
│       ├── base.py             # Base retailer class
│       ├── registry.py         # Retailer registry with caching
│       ├── lululemon.py        # Lululemon implementation  
│       └── nike.py             # Nike implementation
├── Original Framework
│   ├── cli.py                  # Original CLI
│   ├── web_app.py              # Original web app
│   ├── main_improved.py        # Improved main logic
│   └── config.py               # Original configuration
├── Templates & UI
│   ├── templates/dashboard.html         # Original dashboard
│   └── templates/enhanced_dashboard.html # Enhanced dashboard  
├── Storage & Data
│   ├── recipients_store.py     # Email recipients management
│   └── subscriptions_store.py  # Product subscriptions
└── Tests & Configuration
    ├── test_enhanced_framework.py       # Enhanced tests (28 tests)
    ├── test_sale_tracker.py           # Original tests (11 tests)
    ├── test_web_app.py                # Web app tests (4 tests)
    ├── pyproject.toml                 # Modern Python config
    ├── setup.cfg                      # Legacy config (has flake8 issue)
    └── install.sh                     # Installation script
```

## Development Workflow

### Code Changes Process
1. **Always run health check first**: `python3 cli_enhanced.py health`
2. **Run relevant tests**: Enhanced framework tests for retailer changes, web app tests for UI changes
3. **Format code**: `black .` then `isort .` (required for CI)
4. **Manual validation**: Test CLI commands and web app startup
5. **Final test run**: All test suites before committing

### Adding New Retailers
The enhanced framework makes this easy:
1. Create new class in `retailers/` inheriting from `BaseRetailer`
2. Implement `is_supported_url()` and `extract_product_info()` methods  
3. Register in `retailers/__init__.py`
4. Add comprehensive tests following existing patterns
5. Update configuration in `config_enhanced.py`

## Known Issues & Limitations

### Expected Failures (DO NOT FIX)
- **Network requests fail in sandboxed environments** - scraping tests will show connection errors to lululemon.com/nike.com
- **Docker build fails due to SSL certificates** - expected in sandbox, works in production  
- **Live scraping tests skip** - network connectivity issues, not code problems
- **Flake8 config file issues** - use command line flags instead of setup.cfg

### Working Features  
- ✅ All test suites pass (with expected network skips)
- ✅ CLI interfaces work fully (health, config, retailers commands) 
- ✅ Web applications start successfully
- ✅ Code formatting and import sorting
- ✅ Enhanced retailer framework (28 comprehensive tests)
- ✅ Configuration management and validation
- ✅ Email recipient and subscription management

## CI/CD Integration

### GitHub Actions Workflow
- **Code Quality**: Black, isort, flake8 (with proper command line flags)
- **Testing**: Multi-version Python testing (3.8, 3.9, 3.10, 3.11)
- **Security**: Bandit security scanning, dependency vulnerability checks
- **Performance**: Retailer detection performance tests
- **Integration**: CLI command testing, import validation

### Pre-commit Requirements
```bash
# These must pass before committing:
black .                    # Code formatting  
isort .                    # Import organization
python3 test_enhanced_framework.py  # Enhanced tests
python3 cli_enhanced.py health      # System validation
```

## Performance Characteristics

### Measured Timings (Set timeouts with 50%+ buffer)
- **Enhanced test suite**: 5 seconds (28 tests) - TIMEOUT: 60+ seconds
- **Original test suite**: <1 second (11 tests) - TIMEOUT: 30+ seconds  
- **Black formatting**: 1 second (22 files) - TIMEOUT: 60+ seconds
- **Import sorting**: 0.15 seconds (19 files) - TIMEOUT: 30+ seconds
- **Install script**: 1.5 seconds - TIMEOUT: 300+ seconds
- **Web app startup**: 12+ seconds (with scraping initialization) - TIMEOUT: 60+ seconds

### Never Cancel These Operations
- All test suite runs (may appear to hang during network timeouts)
- Web application startup (takes time for initial scraping)
- Code formatting operations (processes many files)
- Health checks (validates multiple systems)

## Validation Checklist

After any changes, ALWAYS verify:
- [ ] `python3 cli_enhanced.py health` shows "All systems healthy!"
- [ ] `python3 test_enhanced_framework.py` passes all 28 tests  
- [ ] `python3 test_sale_tracker.py` passes 9+ tests (2 network skips OK)
- [ ] `black .` and `isort .` complete without errors
- [ ] Web apps start and show initialization logs
- [ ] CLI help commands work (`python3 cli_enhanced.py --help`)

## Common Commands Reference

```bash
# Quick development cycle
python3 cli_enhanced.py health && \
python3 test_enhanced_framework.py && \
black . && isort . && \
python3 cli_enhanced.py config

# Full validation cycle  
bash install.sh && \
python3 test_enhanced_framework.py && \
python3 test_sale_tracker.py && \
python3 test_web_app.py && \
black . && isort . && \
python3 cli_enhanced.py health

# Web application testing
python3 web_app_enhanced.py &    # Starts in background
sleep 15                         # Wait for initialization  
curl http://localhost:5000       # Test basic connectivity
kill %1                         # Stop background process
```

## Emergency Troubleshooting

If tests fail unexpectedly:
1. **Check Python version**: `python3 --version` (needs 3.8+)
2. **Reinstall dependencies**: `pip3 install -r requirements.txt`
3. **Run health check**: `python3 cli_enhanced.py health`  
4. **Check disk space**: Tests create temporary files
5. **Validate environment**: Network issues cause expected failures in sandbox

For build/format failures:
1. **Check file permissions**: `chmod +x cli*.py install.sh`
2. **Clear Python cache**: `rm -rf __pycache__/ */__pycache__/`
3. **Use command line tools**: Skip setup.cfg config files if problematic

Remember: Network failures in scraping are expected in sandboxed environments and do not indicate code problems.