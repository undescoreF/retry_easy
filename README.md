# retry_easy

[![PyPI version](https://badge.fury.io/py/retry_easy.svg)](https://pypi.org/project/retry_easy/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![CI](https://github.com/undescoreF/retry_easy/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/retry_easy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, zero-dependency retry decorator for synchronous and asynchronous Python functions.

---

## Features

- No external runtime dependencies (standard library only)
- Supports both synchronous and asynchronous functions
- Configurable retry attempts, backoff, and jitter
- Fully typed (`ParamSpec`, `TypeVar`) and compatible with `mypy --strict`
- Safe handling of cancellation (`asyncio.CancelledError`)
- Small, readable implementation 

---

## Installation

```bash
pip install retry_easy
```

> On Python < 3.10, `typing-extensions` is required for `ParamSpec`. It is installed automatically.

---

## Quick Start

### Synchronous example

```python
from retry_easy import retry
import requests

@retry(attempts=3, delay=1.0, backoff=2.0)
def fetch_data():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()
```

### Asynchronous example

```python
import asyncio
from retry_easy import retry

@retry(
    attempts=5,
    delay=0.5,
    exceptions=(ConnectionError, TimeoutError),
    jitter=0.2,
)
async def call_service():
    await asyncio.sleep(0.1)
    raise ConnectionError("Service temporarily unavailable")
```

---

## API Reference

| Parameter    | Type                          | Default        | Description |
|--------------|-------------------------------|----------------|-------------|
| attempts     | int                           | 3              | Number of attempts (≥ 1) |
| delay        | float                         | 1.0            | Initial delay in seconds (≥ 0) |
| backoff      | float                         | 1.0            | Multiplier applied after each failure |
| exceptions   | tuple[type[Exception], ...]   | (Exception,)   | Exceptions that trigger a retry |
| jitter       | float                         | 0.0            | Random delay added to avoid synchronization |

### Jitter behavior

```python
wait_time = current_delay + random.uniform(0, jitter)
```

---

## Why retry_easy?

| Use case                      | Typical approach         | retry_easy |
|------------------------------|--------------------------|------------|
| Simple retry logic           | manual try/except loops  | decorator  |
| Async support                | ad-hoc implementations   | built-in   |
| Lightweight dependency       | heavy libraries          | stdlib only |
| Type safety                  | partial typing           | full typing |

This library targets the common use case: simple, readable retry logic without external dependencies.

---

## Development

```bash
git clone https://github.com/yourusername/retry_easy.git
cd retry_easy

pip install -e ".[dev]"

pytest tests/ -v
mypy src/
ruff check src/ tests/
```

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a branch (`feature/my-change`)
3. Commit changes with clear messages
4. Open a Pull Request
5. Ensure CI passes (tests, lint, type checks)

---

## License

MIT License. See `LICENSE` for details.