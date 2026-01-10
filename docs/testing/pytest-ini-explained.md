# pytest.ini Configuration Deep Dive

**Date**: 2026-01-10
**Purpose**: Explain every pytest.ini configuration option and its practical impact

---

## Configuration Breakdown

### 1. Asyncio Configuration

```ini
asyncio_default_fixture_loop_scope = function
```

**What it does**: Sets the default event loop scope for async fixtures to `function`

**Why it matters**:
- Each async test gets a **fresh event loop**
- Prevents event loop interference between tests
- Avoids "Event loop is closed" errors
- Critical for async database operations

**Without this**: You'd get deprecation warnings from pytest-asyncio:
```
DeprecationWarning: The event loop scope for asynchronous fixtures defaults to the "function" scope
```

**Reference**: https://pytest-asyncio.readthedocs.io/en/latest/reference/configuration.html

---

### 2. Test Discovery Patterns

```ini
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

**What it does**: Defines which files/classes/functions pytest considers as tests

**Impact**:
- **Files**: Only `test_*.py` are collected (e.g., `test_country_service.py`)
- **Classes**: Only `Test*` classes are collected (e.g., `TestCountryService`)
- **Functions**: Only `test_*` functions are collected (e.g., `test_create_country`)

**Experiment Results**:
```bash
$ pytest tests/unit/ --co -q | wc -l
48  # Found 48 tests matching these patterns
```

**Best Practice**: Follow these conventions consistently so pytest finds all tests

---

### 3. Minimum Pytest Version

```ini
minversion = 8.0
```

**What it does**: Requires pytest >= 8.0

**Why**:
- Ensures compatibility with features we use
- Fails fast with clear error if old pytest installed
- Documents minimum required version for new developers

**Impact**: If someone runs with pytest 7.x, they get:
```
ERROR: pytest 8.0 or newer is required
```

---

### 4. Python Path

```ini
pythonpath = .
```

**What it does**: Adds project root (`.`) to Python's import path

**Why critical**: Allows imports like `from app.models import Country` without installing package

**Without this**: Tests would fail with:
```python
ModuleNotFoundError: No module named 'app'
```

**Impact**: Makes development workflow easier - no `pip install -e .` needed

---

### 5. Test Output Options (`addopts`)

```ini
addopts =
    -ra
    --showlocals
    --strict-markers
    --strict-config
```

#### `-ra`: Show all test results summary

**What it does**: Shows summary of **all** test outcomes (passed, failed, skipped, errors)

**Example output**:
```
=========================== short test summary info ============================
FAILED tests/.../test_count_relationships_returns_correct_count
============================== 1 failed in 0.66s ===============================
```

**Other options**:
- `-rA`: Show all, including passed tests
- `-rf`: Show only failed
- `-rs`: Show only skipped

#### `--showlocals`: Show local variables in tracebacks

**What it does**: When a test fails, show the values of all local variables

**Example** (from our failed tests):
```python
country    = <MagicMock name='mock.execute().scalar_one_or_none()' id='127890296959872'>
country_id = UUID('ffe56722-e9e-4dc1-8831-5ce402101c89')
self       = <app.repositories.country_repository.CountryRepository object at 0x7450c7b86ba0>
```

**Debugging value**: **HUGE** - you can see exact values without adding print statements

**Trade-off**: Makes output longer, but worth it for debugging

#### `--strict-markers`: Fail on unknown markers

**What it does**: Raises error if you use a marker that isn't registered

**Example**:
```python
@pytest.mark.typo_marker  # Oops, should be "unit"
def test_something():
    pass
```

**Without `--strict-markers`**: Silent failure - marker ignored
**With `--strict-markers`**: Error - catches typos immediately

**Best practice**: Prevents silent failures from marker typos

#### `--strict-config`: Fail on configuration errors

**What it does**: Treats pytest.ini configuration problems as errors

**Impact**: Catches mistakes in pytest.ini early

**Example**: Misspelled option like `asyncio_default_fixture_loop_scop` (missing 'e')

---

### 6. Custom Markers

```ini
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests (require database)
    unit: marks tests as unit tests (mocked dependencies)
    bdd: marks tests as BDD scenarios
```

**What it does**: Registers custom markers to organize tests

**Usage**:

```python
@pytest.mark.integration
async def test_database_integration():
    # Uses real database
    pass

@pytest.mark.slow
def test_expensive_computation():
    # Takes > 1 second
    pass
```

**Running specific test types**:

```bash
# Run only unit tests
pytest -m unit

# Run everything except slow tests
pytest -m "not slow"

# Run integration tests only
pytest -m integration

# Run unit AND integration (but not BDD or slow)
pytest -m "unit or integration"
```

**Current Status**: Markers defined but not yet applied to tests
**Organization**: We currently organize by directory (`tests/unit/`, `tests/integration/`)

---

### 7. Coverage Configuration

```ini
[coverage:run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
```

#### `[coverage:run]` - What to measure

- **`source = app`**: Only measure coverage for `app/` directory
- **`omit`**: Exclude tests, migrations, and cache from coverage

#### `[coverage:report]` - How to display results

- **`precision = 2`**: Show percentages to 2 decimal places (98.56%)
- **`show_missing = True`**: Show line numbers that aren't covered
- **`skip_covered = False`**: Show all files, even 100% covered ones

**Running with coverage**:

```bash
# Terminal report with missing lines
pytest --cov=app --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=app --cov-report=html
# Then open htmlcov/index.html
```

**Example output from our repository tests**:
```
Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
app/repositories/__init__.py                 0      0   100%
app/repositories/country_repository.py      66      1    98%   183
----------------------------------------------------------------------
TOTAL                                       66      1    98%
```

**Interpretation**:
- 66 statements in country_repository.py
- 1 statement not covered (line 183)
- 98% coverage (exceeds our >90% target!)
- Line 183 is the `if country is None` check in `count_relationships` (never reached because NotImplementedError is raised)

---

## Practical Experiments Run

### Experiment 1: Test Organization by Directory
```bash
$ pytest tests/unit/services/ --co -q | wc -l
23  # 23 service layer tests

$ pytest tests/unit/repositories/ --co -q | wc -l
25  # 25 repository layer tests
```

**Conclusion**: We organize by directory rather than markers (for now)

### Experiment 2: Coverage on Specific Module
```bash
$ pytest tests/unit/repositories/ --cov=app/repositories --cov-report=term-missing
```

**Result**: 98% coverage on repository layer (only 1 line unreachable)

### Experiment 3: Observing `--showlocals` in Action

Running a failing test shows exact variable values at point of failure - invaluable for debugging async code where print statements don't work well.

---

## Gotchas and Surprises

### 1. Markers vs Directory Organization

**Discovery**: We defined markers (`unit`, `integration`) but haven't applied them to tests yet

**Current approach**: Organize by directory structure
- `tests/unit/` - Unit tests with mocked dependencies
- `tests/integration/` - Integration tests with Testcontainers
- `tests/features/` - BDD scenarios

**Future consideration**: Add markers when we need to run mixed test types across directories

### 2. `datetime.utcnow()` Deprecation Warnings

**Issue**: Many warnings about `datetime.utcnow()` being deprecated

**Root cause**: Our Country model uses `datetime.utcnow()` in `__init__`:
```python
if 'created_at' not in kwargs:
    self.created_at = datetime.utcnow()  # Deprecated!
```

**Fix**: Replace with `datetime.now(datetime.UTC)`

**Impact**: 20+ warnings cluttering test output

**Action item**: Add to technical debt / next code review

### 3. AsyncMock Warnings

**Issue**: Warnings about `session.add()` coroutine not being awaited

**Root cause**: AsyncMock treats all methods as async, even non-async ones like `session.add()`

**Impact**: Non-critical, disappears in integration tests with real database

**Decision**: Leave as-is until integration tests are implemented

---

## Performance Considerations

### Test Execution Time

```
48 unit tests in ~1.05 seconds
```

**Breakdown**:
- Test collection: ~0.68s
- Test execution: ~0.37s

**Future**:
- Integration tests will be slower (Testcontainers spin-up)
- Consider `@pytest.mark.slow` for tests >1 second
- Use `pytest -m "not slow"` for quick feedback loop

### Coverage Overhead

Adding `--cov` increases execution time by ~15-20%

**Best practice**: Run coverage periodically, not on every test run

---

## Recommendations

### 1. Fix `datetime.utcnow()` Deprecation

**Priority**: Medium
**File**: `app/models/country.py:80`
**Fix**: Replace `datetime.utcnow()` with `datetime.now(datetime.UTC)`

### 2. Consider Adding Test Markers

**When**: After integration tests are implemented
**Why**: To run `pytest -m "unit"` vs `pytest -m "integration"` selectively

### 3. Add Coverage Thresholds

**Future enhancement** to pytest.ini:
```ini
[coverage:report]
fail_under = 90.00
```

This makes the test suite fail if coverage drops below 90%

### 4. Create Coverage Badge

**After Azure deployment**: Add coverage badge to README showing test coverage %

---

## Quick Reference

```bash
# Run all tests
pytest

# Run only unit tests (by directory)
pytest tests/unit/

# Run with coverage
pytest --cov=app --cov-report=html

# Run failing tests first (faster feedback)
pytest --failed-first

# Run only failed tests from last run
pytest --last-failed

# Stop on first failure
pytest -x

# Show test names being collected
pytest --collect-only

# Verbose output
pytest -v

# Very verbose (show each test as it runs)
pytest -vv

# Run specific test
pytest tests/unit/services/test_country_service.py::TestCountryServiceCreate::test_create_country_with_valid_data_succeeds

# Run tests matching pattern
pytest -k "create_country"

# Show available markers
pytest --markers
```

---

## Resources

- **pytest docs**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **pytest-bdd**: https://pytest-bdd.readthedocs.io/
- **Coverage.py**: https://coverage.readthedocs.io/

---

## Conclusion

Our pytest.ini configuration is **well-designed** for this project:

✅ **Asyncio safety** - Event loop isolation
✅ **Strict mode** - Catches configuration errors
✅ **Helpful debugging** - Shows local variables in failures
✅ **Coverage tracking** - Measures and reports code coverage
✅ **Organized markers** - Ready for mixed test types

**Next steps**:
1. Fix `datetime.utcnow()` deprecation
2. Set up Testcontainers for integration tests
3. Apply markers to integration tests when created
4. Add coverage threshold to fail below 90%
