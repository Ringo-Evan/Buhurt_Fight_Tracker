# Integration Tests

Integration tests for Buhurt Fight Tracker using **Testcontainers** with real PostgreSQL databases.

---

## Prerequisites

### Required Software

1. **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
   - Download: https://www.docker.com/products/docker-desktop/
   - Must be running before executing integration tests

2. **Python 3.11+** with dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

### Verify Docker

```bash
# Check Docker is installed and running
docker --version
docker ps  # Should show container list (not an error)
```

If you see "Cannot connect to the Docker daemon", Docker Desktop isn't running.

---

## Running Integration Tests

### Run All Integration Tests

```bash
# Run all integration tests with verbose output
pytest tests/integration/ -v

# Or use marker
pytest -m integration -v
```

### Run Specific Test File

```bash
pytest tests/integration/repositories/test_country_repository_integration.py -v
```

### Run Specific Test

```bash
pytest tests/integration/repositories/test_country_repository_integration.py::TestCountryRepositoryIntegrationCreate::test_create_country_persists_to_database -v
```

### Run with Coverage

```bash
pytest tests/integration/ --cov=app --cov-report=html
```

---

## How Testcontainers Works

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  pytest Test Session                                │
│                                                      │
│  1. pytest starts → reads conftest.py               │
│  2. postgres_container fixture (session scope)      │
│     └─> Spins up PostgreSQL 16 Docker container     │
│                                                      │
│  3. For each test function:                         │
│     ├─> db_engine fixture (function scope)          │
│     │   └─> Creates SQLAlchemy async engine         │
│     │   └─> Runs CREATE TABLE for all models        │
│     │                                                │
│     ├─> db_session fixture (function scope)         │
│     │   └─> Provides fresh AsyncSession             │
│     │                                                │
│     ├─> Run test                                    │
│     │                                                │
│     └─> Cleanup:                                    │
│         ├─> Rollback uncommitted changes            │
│         ├─> DROP all tables                         │
│         └─> Dispose engine                          │
│                                                      │
│  4. Test session ends                               │
│     └─> Destroy PostgreSQL container                │
└─────────────────────────────────────────────────────┘
```

### Key Features

- **Real Database**: Tests run against actual PostgreSQL, not mocks
- **Test Isolation**: Each test gets fresh schema (CREATE/DROP tables)
- **Session Scoping**: Container starts once, reused across all tests
- **Auto Cleanup**: Container automatically destroyed when tests complete
- **Reproducible**: Same PostgreSQL version every time (postgres:16)

---

## Test Organization

```
tests/integration/
├── README.md                               # This file
├── repositories/
│   └── test_country_repository_integration.py  # Country repository tests
├── services/                               # (Future) Service layer integration tests
└── api/                                    # (Future) API endpoint integration tests
```

### Current Test Coverage

**Country Repository** (`test_country_repository_integration.py`):
- ✅ Create operations (single, bulk, constraints)
- ✅ Retrieval operations (by ID, by code, list all)
- ✅ Soft delete operations
- ✅ Update operations
- ✅ Permanent delete operations

**Total**: 14 integration tests

---

## Performance Characteristics

### Timing Breakdown

| Phase | Duration | Scope |
|-------|----------|-------|
| Container startup | 2-5 sec | Once per session |
| Schema creation | 0.1 sec | Per test function |
| Test execution | 0.1-0.2 sec | Per test |
| Schema teardown | 0.1 sec | Per test function |

### Expected Performance

- **Full integration test suite**: ~5-10 seconds
- **Single integration test**: ~0.3-0.5 seconds
- **Unit tests (for comparison)**: <1 second total

### Performance Tips

1. **Session-scoped container** reduces overhead (startup once)
2. **Function-scoped schema** ensures test isolation
3. **Run unit tests first** for fast feedback loop
4. **Run integration tests** before committing changes

---

## Troubleshooting

### Error: "Cannot connect to the Docker daemon"

**Cause**: Docker Desktop not running

**Solution**:
1. Start Docker Desktop (Windows/Mac)
2. Or start Docker daemon (Linux): `sudo systemctl start docker`
3. Verify with `docker ps`

### Error: "Port already in use"

**Cause**: Previous container not cleaned up

**Solution**:
```bash
# List all containers
docker ps -a

# Remove testcontainers
docker rm -f $(docker ps -a | grep testcontainers | awk '{print $1}')
```

### Error: "Image not found: postgres:16"

**Cause**: Image not pulled yet

**Solution**:
```bash
# Pull PostgreSQL 16 image
docker pull postgres:16
```

### Tests Running Slowly

**Causes**:
1. First run downloads postgres:16 image (~100MB)
2. Docker Desktop resource limits too low
3. Antivirus scanning Docker volumes

**Solutions**:
1. Wait for image download (first run only)
2. Increase Docker Desktop resources (Settings → Resources)
3. Exclude Docker volumes from antivirus

---

## Writing New Integration Tests

### Template

```python
import pytest
from app.repositories.country_repository import CountryRepository

@pytest.mark.integration
@pytest.mark.asyncio
async def test_your_feature(db_session):
    \"\"\"
    Test description.

    Arrange: Setup test data
    Act: Perform action
    Assert: Verify results
    \"\"\"
    # Arrange
    repository = CountryRepository(db_session)

    # Act
    result = await repository.your_method()

    # Assert
    assert result is not None
```

### Best Practices

1. **Mark tests**: Always use `@pytest.mark.integration`
2. **Use fixtures**: `db_session`, `sample_country_data`, etc.
3. **Test real behavior**: Verify database constraints, transactions, etc.
4. **Assert both ways**: Check in-memory object AND re-query database
5. **Descriptive names**: `test_create_country_enforces_unique_code_constraint`
6. **Document Why**: Explain what database behavior you're verifying

### What to Test in Integration Tests

✅ **Do test**:
- Database constraints (unique, foreign key, check)
- Transaction behavior (commit, rollback)
- Data persistence (write and re-read)
- Cascading deletes/updates
- Complex queries (joins, aggregations)

❌ **Don't test** (use unit tests instead):
- Business logic validation
- Error handling with mocks
- Edge cases that don't need database

---

## Fixtures Reference

### Database Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `postgres_container` | session | PostgreSQL Docker container |
| `db_engine` | function | SQLAlchemy async engine |
| `db_session` | function | Async session for database ops |

### Data Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `sample_country_data` | function | Single country dict |
| `sample_country_data_list` | function | List of 5 countries |
| `random_uuid` | function | Random UUID v4 |
| `context` | function | BDD scenario context |

See `tests/conftest.py` for fixture implementations.

---

## Next Steps

### When Team Entity is Implemented

Add integration tests for:
- Team creation with country foreign key
- Cascade behavior (deleting country with teams)
- JOIN queries (teams with countries)

### Future Enhancements

1. **Service layer integration tests**
   - Test service + repository + database together
   - Verify transaction boundaries

2. **API integration tests**
   - Test HTTP endpoints with TestClient
   - Use same Testcontainers database

3. **Performance benchmarks**
   - Measure query execution time
   - Identify N+1 query problems

---

## Resources

- **Testcontainers Python**: https://testcontainers-python.readthedocs.io/
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **Docker**: https://docs.docker.com/

---

**Ready to run integration tests?**

1. Start Docker Desktop
2. Run: `pytest tests/integration/ -v`
3. Watch Testcontainers spin up PostgreSQL and run tests!
