# GoetGevonden Python API Wrapper

A Python client library for the [GoetGevonden API](https://api.goetgevonden.nl), providing programmatic access to **De resoluties van de Staten-Generaal** (Resolutions of the States-General of the Dutch Republic).

## About GoetGevonden

GoetGevonden ("well found" in Dutch) is a digital humanities project that makes historical documents from the Dutch Republic accessible through a modern API. The platform is built on the Broccoli text annotation framework and currently hosts the **Republic** project.

### The Republic Project

The Republic project provides access to the resolutions of the States-General of the Dutch Republic, spanning from 1576 to 1796. These resolutions document the decisions made by the highest governmental body of the Dutch Republic during the Early Modern period, offering invaluable insights into:

- Political decision-making and governance
- Diplomatic relations and foreign policy
- Economic policies and trade regulations
- Military affairs and colonial administration
- Religious matters and social policies

The resolutions are fully searchable and annotated, making them accessible to researchers, historians, and anyone interested in Dutch history.

## Installation

### From source

```bash
git clone https://github.com/goetgevonden/goetgevonden-python.git
cd goetgevonden-python
pip install -e .
```

### Development installation

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from goetgevonden import GoetGevondenClient

# Create a client (defaults to the Republic project)
client = GoetGevondenClient()

# Get server information
info = client.get_about()
print(f"Connected to {info.app_name} v{info.version}")

# List available projects
projects = client.list_projects()
print(f"Available projects: {projects}")

# Search for resolutions mentioning Amsterdam
results = client.search_text("Amsterdam")
print(f"Found {results.total} resolutions mentioning Amsterdam")

# Iterate through results
for hit in results.hits:
    source = hit.get("_source", {})
    print(f"- {source.get('title', 'No title')}")
```

## Features

- Full-text search across historical documents
- Date range filtering
- Pagination support
- Aggregation queries
- View configurations
- Annotation retrieval
- Type hints and dataclasses for IDE support
- Context manager support for proper resource cleanup
- Comprehensive error handling

## Usage Examples

### Basic Search

```python
from goetgevonden import GoetGevondenClient

client = GoetGevondenClient()

# Get available indices first
indices = client.get_indices()
print(f"Available indices: {list(indices.keys())}")

# Search with terms filter (most common use case)
results = client.search(
    index_name="republic-2025-05-01",  # Use the active index
    terms={"locationName": "Amsterdam"},
    size=10
)
print(f"Total results: {results.total}")
```

### Search with Date Range

```python
from goetgevonden import GoetGevondenClient, IndexRange

client = GoetGevondenClient()

# Search within a specific time period using sessionYear
results = client.search(
    index_name="republic-2025-05-01",
    date_range=IndexRange(name="sessionYear", from_value="1600", to_value="1650"),
    size=10
)

print(f"Found {results.total} resolutions between 1600-1650")

# You can also filter by specific session date
results = client.search(
    index_name="republic-2025-05-01",
    date_range=IndexRange(name="sessionDate", from_value="1620-01-01", to_value="1620-12-31"),
    size=10
)
```

### Advanced Search with Filters

```python
from goetgevonden import GoetGevondenClient, IndexRange, SortOrder

client = GoetGevondenClient()

# Advanced search combining multiple filters
results = client.search(
    project_id="republic",
    index_name="republic-2025-05-01",
    terms={
        "locationName": "Amsterdam",
        "resolutionType": "ordinaris"
    },
    date_range=IndexRange(name="sessionYear", from_value="1650", to_value="1700"),
    from_=0,
    size=20,
    sort_by="sessionDate",
    sort_order=SortOrder.ASC,
)

for hit in results.hits:
    print(f"ID: {hit.get('_id')}")
    print(f"  Type: {hit.get('resolutionType')}")
    print(f"  Year: {hit.get('sessionYear')}")
```

### Available Search Fields

The Republic index supports the following searchable fields:

| Field | Type | Description |
|-------|------|-------------|
| `textType` | keyword | Type of text (e.g., "handgeschreven") |
| `resolutionType` | keyword | Resolution type (e.g., "ordinaris") |
| `propositionType` | keyword | Proposition type |
| `delegateName` | keyword | Name of delegate |
| `personName` | keyword | Person names mentioned |
| `roleName` | keyword | Role names |
| `locationName` | keyword | Location names (e.g., "Amsterdam") |
| `organisationName` | keyword | Organisation names |
| `commissionName` | keyword | Commission names |
| `sessionWeekday` | keyword | Day of the week |
| `sessionDate` | date | Full session date |
| `sessionDay` | byte | Day of month |
| `sessionMonth` | byte | Month number |
| `sessionYear` | short | Year |

### Working with Aggregations

```python
from goetgevonden import GoetGevondenClient

client = GoetGevondenClient()

# Search with aggregations to get faceted results
results = client.search(
    text="Holland",
    aggregations={
        "years": {
            "date_histogram": {
                "field": "date",
                "interval": "year"
            }
        }
    }
)

if results.aggregations:
    print("Results by year:")
    for bucket in results.aggregations.get("years", {}).get("buckets", []):
        print(f"  {bucket['key']}: {bucket['doc_count']} documents")
```

### Retrieving Annotations

```python
from goetgevonden import GoetGevondenClient

client = GoetGevondenClient()

# Get annotations for a specific document
annotations = client.get_annotations(
    body_id="some-document-id",
    project_id="republic"
)

print(annotations)
```

### Getting Project Views

```python
from goetgevonden import GoetGevondenClient

client = GoetGevondenClient()

# Get available view configurations
views = client.get_views("republic")

for name, config in views.items():
    print(f"View: {name}")
    print(f"  Scope: {config.scope}")
    for constraint in config.anno:
        print(f"  Constraint: {constraint.path} = {constraint.value}")
```

### Context Manager Usage

```python
from goetgevonden import GoetGevondenClient

# Use as context manager for automatic cleanup
with GoetGevondenClient() as client:
    results = client.search_text("Amsterdam")
    print(f"Found {results.total} results")
# Session is automatically closed
```

### Custom Configuration

```python
from goetgevonden import GoetGevondenClient
import requests

# Create a custom session with specific settings
session = requests.Session()
session.headers.update({"User-Agent": "MyResearchProject/1.0"})

# Use custom session and timeout
client = GoetGevondenClient(
    base_url="https://api.goetgevonden.nl",
    timeout=60,
    session=session
)
```

## API Reference

### GoetGevondenClient

The main client class for interacting with the API.

#### Constructor

```python
GoetGevondenClient(
    base_url: str = "https://api.goetgevonden.nl",
    timeout: int = 30,
    session: requests.Session | None = None
)
```

#### Methods

| Method | Description |
|--------|-------------|
| `get_about()` | Get server information |
| `list_projects()` | List available projects |
| `get_project_body_types(project_id)` | Get body types for a project |
| `get_views(project_id)` | Get view configurations |
| `get_annotations(body_id, project_id, ...)` | Get annotations for a document |
| `search(project_id, text, terms, ...)` | Advanced search with full options |
| `search_text(query, project_id, ...)` | Simple text search |
| `search_by_date(start_date, end_date, ...)` | Search within date range |
| `get_indices(project_id)` | List indices for a project |
| `close()` | Close the HTTP session |

### Models

| Model | Description |
|-------|-------------|
| `AboutInfo` | Server information |
| `SearchResult` | Search results with hits and aggregations |
| `IndexQuery` | Search query parameters |
| `IndexRange` | Date or numeric range filter |
| `ViewConfiguration` | View configuration settings |
| `ViewAnnoConstraint` | Annotation constraint for views |
| `Annotation` | Document annotation data |

### Enums

| Enum | Values | Description |
|------|--------|-------------|
| `SortOrder` | `ASC`, `DESC` | Sort direction |
| `ViewScope` | `OVERLAP`, `WITHIN` | View scope type |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `GoetGevondenError` | Base exception for all errors |
| `APIError` | API returned an error response |
| `ConnectionError` | Failed to connect to the API |
| `TimeoutError` | Request timed out |
| `NotFoundError` | Resource not found (404) |
| `ValidationError` | Invalid request parameters |

## Error Handling

```python
from goetgevonden import (
    GoetGevondenClient,
    APIError,
    ConnectionError,
    NotFoundError,
    TimeoutError
)

client = GoetGevondenClient()

try:
    results = client.search_text("Amsterdam")
except ConnectionError as e:
    print(f"Could not connect to the API: {e}")
except TimeoutError as e:
    print(f"Request timed out: {e}")
except NotFoundError as e:
    print(f"Resource not found: {e}")
except APIError as e:
    print(f"API error {e.status_code}: {e}")
```

## Development

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=goetgevonden --cov-report=html
```

### Type Checking

```bash
mypy goetgevonden
```

### Linting

```bash
ruff check goetgevonden
ruff format goetgevonden
```

## Requirements

- Python 3.10+
- requests >= 2.28.0

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Links

- [GoetGevonden Website](https://goetgevonden.nl)
- [API Documentation](https://api.goetgevonden.nl)
- [Republic Project](https://republic.huygens.knaw.nl/)

## Acknowledgments

This project provides access to the Republic dataset, which is part of the digital humanities infrastructure developed by the Huygens Institute for the History of the Netherlands. The resolutions of the States-General represent a crucial source for understanding the political history of the Dutch Republic.
