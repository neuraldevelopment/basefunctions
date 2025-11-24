# Pandas Module Guide

## Overview

The **Pandas Module** in the `basefunctions` framework provides custom accessor extensions for `pandas` DataFrames and Series. These extensions add convenient attribute management functionality to standard pandas objects through the `.pf` accessor namespace.

The module leverages pandas' extension API to seamlessly integrate additional methods into DataFrame and Series objects without modifying the core pandas library.

---

## Table of Contents

1. [Installation & Import](#installation--import)
2. [Architecture Overview](#architecture-overview)
3. [Custom Accessors Explained](#custom-accessors-explained)
4. [DataFrame Extensions (`.pf`)](#dataframe-extensions-pf)
5. [Series Extensions (`.pf`)](#series-extensions-pf)
6. [Use Cases & Examples](#use-cases--examples)
7. [Integration with Existing Code](#integration-with-existing-code)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)
10. [Implementation Details](#implementation-details)

---

## Installation & Import

### Installation

The pandas module is part of the `basefunctions` package:

```bash
pip install basefunctions
```

### Import

The pandas accessors are automatically registered when you import `basefunctions`:

```python
import basefunctions
import pandas as pd

# The .pf accessor is now available on all DataFrames and Series
df = pd.DataFrame({'a': [1, 2, 3]})
df.pf.set_attrs('description', 'My dataset')
```

**Direct Import** (if you only need pandas extensions):

```python
from basefunctions import PandasDataFrame, PandasSeries
import pandas as pd

# Accessors are registered automatically upon import
```

---

## Architecture Overview

### Module Structure

```
src/basefunctions/pandas/
├── __init__.py          # Public exports
└── accessors.py         # Accessor implementations
```

### Component Hierarchy

```
_PandasAccessorBase (Base Class)
├── Common attribute methods
├── Used by both DataFrame and Series accessors
│
├── PandasDataFrame (@pd.api.extensions.register_dataframe_accessor("pf"))
│   └── Extends DataFrames with .pf accessor
│
└── PandasSeries (@pd.api.extensions.register_series_accessor("pf"))
    └── Extends Series with .pf accessor
```

### Key Design Principles

1. **Non-Invasive**: Uses pandas' official extension API
2. **Consistent**: Same `.pf` accessor for both DataFrames and Series
3. **Validation**: Type checking ensures correct object types
4. **Inheritance**: Shared functionality in base class to avoid duplication

---

## Custom Accessors Explained

### What are Pandas Accessors?

Pandas accessors allow you to extend DataFrame and Series objects with custom functionality using a namespace (e.g., `.pf`). This is the recommended way to add custom methods to pandas objects without monkey-patching.

### How Accessors Work

1. **Registration**: Accessors are registered using decorators
   ```python
   @pd.api.extensions.register_dataframe_accessor("pf")
   class PandasDataFrame:
       ...
   ```

2. **Initialization**: The accessor class receives the pandas object
   ```python
   def __init__(self, pandas_obj: pd.DataFrame):
       self._obj = pandas_obj  # Reference to the DataFrame
   ```

3. **Usage**: Access methods via the registered namespace
   ```python
   df.pf.set_attrs('key', 'value')  # .pf is the accessor namespace
   ```

### Why Use the `.pf` Namespace?

- **Namespace Isolation**: Avoids conflicts with existing pandas methods
- **Clarity**: Clear indication that you're using basefunctions extensions
- **Consistency**: Same accessor name for DataFrame and Series

---

## DataFrame Extensions (`.pf`)

DataFrames gain access to the `.pf` accessor with attribute management methods.

### Available Methods

All methods from `_PandasAccessorBase`:

- `get_attrs(name)` - Retrieve attribute value
- `set_attrs(name, value)` - Set attribute value
- `has_attrs(names, abort=True)` - Check attribute existence
- `list_attrs()` - List all attribute names
- `del_attrs(name)` - Delete attribute

### Basic Usage

```python
import pandas as pd
import basefunctions

# Create a DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['NYC', 'LA', 'SF']
})

# Set custom attributes
df.pf.set_attrs('source', 'user_database')
df.pf.set_attrs('created_at', '2025-01-08')
df.pf.set_attrs('version', 1.0)

# Retrieve attributes
source = df.pf.get_attrs('source')
print(f"Data source: {source}")  # Output: Data source: user_database

# List all attributes
attrs = df.pf.list_attrs()
print(f"Available attributes: {attrs}")
# Output: Available attributes: ['source', 'created_at', 'version']

# Check if attributes exist
if df.pf.has_attrs(['source', 'version']):
    print("Required metadata is present")

# Delete attributes
df.pf.del_attrs('version')
```

---

## Series Extensions (`.pf`)

Series objects also get the `.pf` accessor with identical functionality.

### Available Methods

Same methods as DataFrame extensions:

- `get_attrs(name)`
- `set_attrs(name, value)`
- `has_attrs(names, abort=True)`
- `list_attrs()`
- `del_attrs(name)`

### Basic Usage

```python
import pandas as pd
import basefunctions

# Create a Series
series = pd.Series([10, 20, 30, 40], name='sales')

# Set custom attributes
series.pf.set_attrs('unit', 'USD')
series.pf.set_attrs('region', 'North America')
series.pf.set_attrs('quarter', 'Q1 2025')

# Retrieve attributes
unit = series.pf.get_attrs('unit')
print(f"Currency: {unit}")  # Output: Currency: USD

# List all attributes
attrs = series.pf.list_attrs()
print(f"Series metadata: {attrs}")
# Output: Series metadata: ['unit', 'region', 'quarter']

# Check if attributes exist
if series.pf.has_attrs('region'):
    region = series.pf.get_attrs('region')
    print(f"Data is from: {region}")
```

---

## Use Cases & Examples

### Use Case 1: Data Provenance Tracking

Track where data comes from and how it was processed:

```python
import pandas as pd
import basefunctions
from datetime import datetime

# Load data
df = pd.read_csv('data.csv')

# Track provenance
df.pf.set_attrs('source_file', 'data.csv')
df.pf.set_attrs('loaded_at', datetime.now().isoformat())
df.pf.set_attrs('loaded_by', 'etl_pipeline_v2')

# After processing
df_cleaned = df.dropna()
df_cleaned.pf.set_attrs('source_file', df.pf.get_attrs('source_file'))
df_cleaned.pf.set_attrs('loaded_at', df.pf.get_attrs('loaded_at'))
df_cleaned.pf.set_attrs('cleaning_applied', True)
df_cleaned.pf.set_attrs('processing_step', 'dropna')

# Later: check data lineage
print(f"Original source: {df_cleaned.pf.get_attrs('source_file')}")
print(f"Loaded at: {df_cleaned.pf.get_attrs('loaded_at')}")
print(f"Processing: {df_cleaned.pf.get_attrs('processing_step')}")
```

### Use Case 2: Validation & Quality Checks

Ensure required metadata exists before processing:

```python
def process_dataset(df):
    """Process dataset with required metadata validation."""

    # Ensure required metadata exists
    required_attrs = ['source', 'schema_version', 'validated']

    try:
        df.pf.has_attrs(required_attrs, abort=True)
    except ValueError as e:
        print(f"Missing metadata: {e}")
        return None

    # Safe to proceed
    source = df.pf.get_attrs('source')
    version = df.pf.get_attrs('schema_version')

    print(f"Processing {source} (schema v{version})")
    # ... processing logic

    return df

# Usage
df = pd.DataFrame({'value': [1, 2, 3]})
df.pf.set_attrs('source', 'api_endpoint')
df.pf.set_attrs('schema_version', '2.1')
df.pf.set_attrs('validated', True)

processed_df = process_dataset(df)
```

### Use Case 3: Unit and Metadata Preservation

Preserve units and metadata through transformations:

```python
# Create time series with units
temperature = pd.Series([20.5, 21.0, 19.8, 22.1], name='temperature')
temperature.pf.set_attrs('unit', 'Celsius')
temperature.pf.set_attrs('sensor_id', 'TMP001')
temperature.pf.set_attrs('location', 'Server Room A')

# Convert to Fahrenheit
def celsius_to_fahrenheit(series):
    """Convert temperature preserving metadata."""
    fahrenheit = series * 9/5 + 32

    # Preserve original metadata
    fahrenheit.pf.set_attrs('unit', 'Fahrenheit')
    fahrenheit.pf.set_attrs('sensor_id', series.pf.get_attrs('sensor_id'))
    fahrenheit.pf.set_attrs('location', series.pf.get_attrs('location'))
    fahrenheit.pf.set_attrs('converted_from', 'Celsius')

    return fahrenheit

temp_f = celsius_to_fahrenheit(temperature)
print(f"Temperature in {temp_f.pf.get_attrs('unit')}")
print(f"Sensor: {temp_f.pf.get_attrs('sensor_id')}")
print(f"Location: {temp_f.pf.get_attrs('location')}")
```

### Use Case 4: Configuration Embedding

Embed processing configuration with the data:

```python
# Load and configure dataset
df = pd.read_csv('sales.csv')

# Embed configuration
config = {
    'aggregation_level': 'daily',
    'currency': 'USD',
    'fiscal_year_start': 'April',
    'include_weekends': False
}

for key, value in config.items():
    df.pf.set_attrs(key, value)

# Later: use configuration
def aggregate_sales(df):
    """Aggregate sales using embedded configuration."""
    level = df.pf.get_attrs('aggregation_level')
    currency = df.pf.get_attrs('currency')

    print(f"Aggregating at {level} level in {currency}")
    # ... aggregation logic

aggregate_sales(df)
```

### Use Case 5: Pipeline Context Passing

Pass context through data processing pipelines:

```python
def pipeline_step_1(df):
    """Extract data."""
    df.pf.set_attrs('pipeline_step', 'extract')
    df.pf.set_attrs('step_1_complete', True)
    return df

def pipeline_step_2(df):
    """Transform data."""
    # Verify previous step
    if not df.pf.has_attrs('step_1_complete', abort=False):
        raise RuntimeError("Step 1 not completed")

    df.pf.set_attrs('pipeline_step', 'transform')
    df.pf.set_attrs('step_2_complete', True)
    return df

def pipeline_step_3(df):
    """Load data."""
    # Verify all previous steps
    required = ['step_1_complete', 'step_2_complete']
    if not df.pf.has_attrs(required, abort=False):
        raise RuntimeError("Previous steps incomplete")

    df.pf.set_attrs('pipeline_step', 'load')
    df.pf.set_attrs('step_3_complete', True)
    return df

# Run pipeline
df = pd.DataFrame({'data': [1, 2, 3]})
df = pipeline_step_1(df)
df = pipeline_step_2(df)
df = pipeline_step_3(df)

print(f"Pipeline status: {df.pf.get_attrs('pipeline_step')}")
print(f"All attributes: {df.pf.list_attrs()}")
```

---

## Integration with Existing Code

### Seamless Integration

The `.pf` accessor works alongside standard pandas operations:

```python
import pandas as pd
import basefunctions

# Standard pandas operations
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

# Add metadata
df.pf.set_attrs('source', 'manual_entry')

# Standard operations preserve the DataFrame
df_filtered = df[df['A'] > 1]
df_grouped = df.groupby('A').sum()

# Note: attrs are not automatically copied in transformations
# You need to manually preserve them if needed
df_filtered.pf.set_attrs('source', df.pf.get_attrs('source'))
df_filtered.pf.set_attrs('filter_applied', 'A > 1')
```

### Compatibility

- **Pandas Version**: Works with pandas >= 0.23.0 (extension API introduced)
- **Python Version**: Requires Python >= 3.12 (basefunctions requirement)
- **No Conflicts**: The `.pf` namespace avoids conflicts with pandas methods

### Working with Copies

Remember that pandas operations often create copies:

```python
df = pd.DataFrame({'value': [1, 2, 3]})
df.pf.set_attrs('tag', 'original')

# This creates a copy - attrs are NOT automatically preserved
df_copy = df.copy()

# You need to manually copy attrs if needed
for attr_name in df.pf.list_attrs():
    df_copy.pf.set_attrs(attr_name, df.pf.get_attrs(attr_name))
```

**Helper Function** for copying attributes:

```python
def copy_attrs(source_df, target_df):
    """Copy all attributes from source to target DataFrame."""
    for attr_name in source_df.pf.list_attrs():
        target_df.pf.set_attrs(attr_name, source_df.pf.get_attrs(attr_name))
    return target_df

# Usage
df_new = df.copy()
df_new = copy_attrs(df, df_new)
```

---

## Best Practices

### 1. Use Descriptive Attribute Names

```python
# Good: Clear, descriptive names
df.pf.set_attrs('data_source', 'user_api')
df.pf.set_attrs('extraction_timestamp', '2025-01-08T10:30:00')
df.pf.set_attrs('schema_version', '2.1')

# Avoid: Vague or cryptic names
df.pf.set_attrs('src', 'api')
df.pf.set_attrs('ts', '2025-01-08')
df.pf.set_attrs('v', 2)
```

### 2. Validate Required Attributes Early

```python
def process_data(df):
    """Process data with validation."""
    # Validate at the start
    required = ['source', 'schema_version', 'validated']

    if not df.pf.has_attrs(required, abort=False):
        missing = [attr for attr in required if not df.pf.has_attrs(attr, abort=False)]
        raise ValueError(f"Missing required attributes: {missing}")

    # Safe to proceed
    # ... processing logic
```

### 3. Document Expected Attributes

```python
def load_sales_data(filepath):
    """
    Load sales data with standardized metadata.

    Sets the following attributes:
    - source_file: str - Original file path
    - loaded_at: str - ISO timestamp of load time
    - record_count: int - Number of records loaded
    - currency: str - Default 'USD'
    """
    df = pd.read_csv(filepath)

    df.pf.set_attrs('source_file', filepath)
    df.pf.set_attrs('loaded_at', datetime.now().isoformat())
    df.pf.set_attrs('record_count', len(df))
    df.pf.set_attrs('currency', 'USD')

    return df
```

### 4. Use Type-Safe Values

```python
# Store structured data as JSON-serializable values
df.pf.set_attrs('config', {'key': 'value', 'count': 10})
df.pf.set_attrs('tags', ['important', 'validated', 'production'])

# Avoid storing non-serializable objects
# df.pf.set_attrs('connection', database_connection_object)  # Bad practice
```

### 5. Clean Up Unused Attributes

```python
# Remove temporary attributes after use
df.pf.set_attrs('temp_processing_flag', True)
# ... do processing
df.pf.del_attrs('temp_processing_flag')

# Or check before deleting
if df.pf.has_attrs('temp_processing_flag', abort=False):
    df.pf.del_attrs('temp_processing_flag')
```

### 6. Preserve Attributes Through Pipelines

```python
def preserve_attrs_decorator(func):
    """Decorator to preserve DataFrame attributes through transformations."""
    def wrapper(df, *args, **kwargs):
        # Save attributes
        saved_attrs = {name: df.pf.get_attrs(name) for name in df.pf.list_attrs()}

        # Execute function
        result = func(df, *args, **kwargs)

        # Restore attributes
        for name, value in saved_attrs.items():
            result.pf.set_attrs(name, value)

        return result
    return wrapper

@preserve_attrs_decorator
def transform_data(df):
    """Transform data while preserving metadata."""
    return df * 2

# Usage
df = pd.DataFrame({'value': [1, 2, 3]})
df.pf.set_attrs('source', 'test')
df_transformed = transform_data(df)
print(df_transformed.pf.get_attrs('source'))  # Still 'test'
```

---

## API Reference

### Base Class: `_PandasAccessorBase`

Internal base class providing common functionality.

#### Methods

##### `get_attrs(name: str) -> Any`

Retrieve an attribute value by name.

**Parameters:**
- `name` (str): The name of the attribute to retrieve

**Returns:**
- `Any`: The value of the requested attribute, or `None` if not found

**Example:**
```python
value = df.pf.get_attrs('source')
```

---

##### `set_attrs(name: str, value: Any) -> Any`

Set an attribute to a specified value.

**Parameters:**
- `name` (str): The name of the attribute to set
- `value` (Any): The value to assign to the attribute

**Returns:**
- `Any`: The value that was set

**Example:**
```python
df.pf.set_attrs('version', '1.0')
df.pf.set_attrs('config', {'key': 'value'})
```

---

##### `has_attrs(names: str | List[str], abort: bool = True) -> bool`

Check if the object has specified attributes.

**Parameters:**
- `names` (str | List[str]): Single attribute name or list of names to check
- `abort` (bool, optional): If `True`, raises `ValueError` when attributes are missing. Default: `True`

**Returns:**
- `bool`: `True` if all attributes exist, `False` otherwise

**Raises:**
- `ValueError`: If `abort=True` and any attributes are missing

**Example:**
```python
# Check single attribute (raises error if missing)
df.pf.has_attrs('source')

# Check multiple attributes (raises error if any missing)
df.pf.has_attrs(['source', 'version', 'validated'])

# Check without raising error
if df.pf.has_attrs('optional_field', abort=False):
    print("Optional field exists")
```

---

##### `list_attrs() -> List[str]`

List all attribute names on the object.

**Returns:**
- `List[str]`: A list of all attribute names

**Example:**
```python
attrs = df.pf.list_attrs()
print(f"Available attributes: {attrs}")
```

---

##### `del_attrs(name: str) -> None`

Delete an attribute from the object.

**Parameters:**
- `name` (str): The name of the attribute to delete

**Returns:**
- `None`

**Example:**
```python
df.pf.del_attrs('temporary_field')

# Safe deletion (doesn't raise error if attribute doesn't exist)
if df.pf.has_attrs('temp', abort=False):
    df.pf.del_attrs('temp')
```

---

### DataFrame Accessor: `PandasDataFrame`

Registered as `.pf` accessor for DataFrames.

**Registration:**
```python
@pd.api.extensions.register_dataframe_accessor("pf")
```

**Inherits all methods from:** `_PandasAccessorBase`

**Usage:**
```python
import pandas as pd
import basefunctions

df = pd.DataFrame({'A': [1, 2, 3]})
df.pf.set_attrs('description', 'Sample data')
```

---

### Series Accessor: `PandasSeries`

Registered as `.pf` accessor for Series.

**Registration:**
```python
@pd.api.extensions.register_series_accessor("pf")
```

**Inherits all methods from:** `_PandasAccessorBase`

**Usage:**
```python
import pandas as pd
import basefunctions

series = pd.Series([10, 20, 30])
series.pf.set_attrs('unit', 'meters')
```

---

## Implementation Details

### Accessor Registration

The accessors are registered using pandas' official extension API:

```python
@pd.api.extensions.register_dataframe_accessor("pf")
class PandasDataFrame(_PandasAccessorBase):
    def __init__(self, pandas_obj: pd.DataFrame):
        super().__init__()
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        if not isinstance(obj, pd.DataFrame):
            raise RuntimeError(f"expected pandas dataframe object, received {type(obj)}")
```

### Validation

Each accessor validates the object type during initialization:

- **DataFrames**: Must be `pd.DataFrame` instances
- **Series**: Must be `pd.Series` instances
- Raises `RuntimeError` if validation fails

### Logging

The module uses basefunctions' logging system:

```python
basefunctions.setup_logger(__name__)
basefunctions.get_logger(__name__).error("invalid object type: %s", type(obj))
```

### Storage Mechanism

Attributes are stored in pandas' native `attrs` dictionary:

```python
# Under the hood
df.attrs['my_key'] = 'my_value'  # Direct pandas attrs
df.pf.set_attrs('my_key', 'my_value')  # Via accessor (same result)
```

### Thread Safety

The `.pf` accessor methods are **not inherently thread-safe** for concurrent modifications. If you need thread-safe attribute management:

```python
import threading

lock = threading.Lock()

def safe_set_attrs(df, name, value):
    """Thread-safe attribute setting."""
    with lock:
        df.pf.set_attrs(name, value)
```

### Performance Considerations

- **Attribute access** is fast (dictionary lookup)
- **No performance overhead** on standard pandas operations
- **Minimal memory footprint** (uses pandas' existing attrs dict)

---

## Advanced Examples

### Example 1: Multi-Step ETL Pipeline

```python
import pandas as pd
import basefunctions
from datetime import datetime

class ETLPipeline:
    """ETL pipeline with metadata tracking."""

    def __init__(self, name: str):
        self.name = name

    def extract(self, source: str) -> pd.DataFrame:
        """Extract data from source."""
        df = pd.read_csv(source)

        # Track extraction metadata
        df.pf.set_attrs('pipeline', self.name)
        df.pf.set_attrs('stage', 'extract')
        df.pf.set_attrs('source', source)
        df.pf.set_attrs('extracted_at', datetime.now().isoformat())
        df.pf.set_attrs('record_count', len(df))

        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data."""
        # Verify previous stage
        if df.pf.get_attrs('stage') != 'extract':
            raise ValueError("Must extract before transform")

        # Apply transformations
        df_transformed = df.dropna()

        # Preserve and update metadata
        for attr in df.pf.list_attrs():
            df_transformed.pf.set_attrs(attr, df.pf.get_attrs(attr))

        df_transformed.pf.set_attrs('stage', 'transform')
        df_transformed.pf.set_attrs('transformed_at', datetime.now().isoformat())
        df_transformed.pf.set_attrs('records_after_transform', len(df_transformed))

        return df_transformed

    def load(self, df: pd.DataFrame, destination: str) -> None:
        """Load data to destination."""
        # Verify previous stage
        if df.pf.get_attrs('stage') != 'transform':
            raise ValueError("Must transform before load")

        # Load data
        df.to_csv(destination, index=False)

        # Update metadata
        df.pf.set_attrs('stage', 'load')
        df.pf.set_attrs('destination', destination)
        df.pf.set_attrs('loaded_at', datetime.now().isoformat())

        # Log pipeline completion
        print(f"Pipeline '{self.name}' completed:")
        print(f"  Source: {df.pf.get_attrs('source')}")
        print(f"  Destination: {df.pf.get_attrs('destination')}")
        print(f"  Records: {df.pf.get_attrs('record_count')} → {df.pf.get_attrs('records_after_transform')}")

# Usage
pipeline = ETLPipeline('sales_etl')
df = pipeline.extract('sales_raw.csv')
df = pipeline.transform(df)
pipeline.load(df, 'sales_clean.csv')
```

### Example 2: Data Quality Validation

```python
import pandas as pd
import basefunctions

class DataQualityValidator:
    """Validate data quality and track results."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.df.pf.set_attrs('validation_results', {})

    def check_missing_values(self, threshold: float = 0.1) -> bool:
        """Check if missing values are below threshold."""
        missing_pct = self.df.isnull().sum().sum() / (len(self.df) * len(self.df.columns))
        passed = missing_pct < threshold

        results = self.df.pf.get_attrs('validation_results')
        results['missing_values'] = {
            'passed': passed,
            'missing_pct': missing_pct,
            'threshold': threshold
        }
        self.df.pf.set_attrs('validation_results', results)

        return passed

    def check_duplicates(self) -> bool:
        """Check for duplicate rows."""
        dup_count = self.df.duplicated().sum()
        passed = dup_count == 0

        results = self.df.pf.get_attrs('validation_results')
        results['duplicates'] = {
            'passed': passed,
            'duplicate_count': dup_count
        }
        self.df.pf.set_attrs('validation_results', results)

        return passed

    def check_schema(self, expected_columns: list) -> bool:
        """Check if DataFrame has expected columns."""
        actual_columns = set(self.df.columns)
        expected_columns = set(expected_columns)
        missing = expected_columns - actual_columns
        extra = actual_columns - expected_columns
        passed = len(missing) == 0

        results = self.df.pf.get_attrs('validation_results')
        results['schema'] = {
            'passed': passed,
            'missing_columns': list(missing),
            'extra_columns': list(extra)
        }
        self.df.pf.set_attrs('validation_results', results)

        return passed

    def validate_all(self, expected_columns: list) -> bool:
        """Run all validations."""
        checks = [
            self.check_missing_values(),
            self.check_duplicates(),
            self.check_schema(expected_columns)
        ]

        all_passed = all(checks)
        self.df.pf.set_attrs('validated', all_passed)
        self.df.pf.set_attrs('validated_at', datetime.now().isoformat())

        return all_passed

    def get_report(self) -> dict:
        """Get validation report."""
        return self.df.pf.get_attrs('validation_results')

# Usage
df = pd.DataFrame({'A': [1, 2, None], 'B': [4, 5, 6]})
validator = DataQualityValidator(df)

if validator.validate_all(['A', 'B']):
    print("Data quality check passed!")
else:
    print("Data quality issues found:")
    print(validator.get_report())
```

---

## Summary

The **Pandas Module** in basefunctions provides a clean, non-invasive way to add custom metadata and attribute management to pandas DataFrames and Series through the `.pf` accessor.

**Key Benefits:**

- **Metadata Tracking**: Track data provenance, processing steps, configuration
- **Validation**: Ensure required metadata exists before processing
- **Pipeline Context**: Pass context through data processing pipelines
- **Non-Invasive**: Uses pandas' official extension API
- **Consistent API**: Same interface for both DataFrames and Series

**Best For:**

- ETL pipelines requiring metadata tracking
- Data validation workflows
- Multi-step data transformations
- Configuration embedding with datasets
- Provenance and lineage tracking

**Getting Started:**

```python
import basefunctions
import pandas as pd

# Create DataFrame
df = pd.DataFrame({'data': [1, 2, 3]})

# Add metadata
df.pf.set_attrs('source', 'my_source')
df.pf.set_attrs('version', '1.0')

# Retrieve metadata
source = df.pf.get_attrs('source')
print(f"Data from: {source}")

# List all attributes
print(f"Attributes: {df.pf.list_attrs()}")
```

For more information, see the [basefunctions documentation](https://github.com/neuraldevelopment/basefunctions).


---

**Document Version**: 1.1
**Last Updated**: 2025-01-24
**Framework Version**: basefunctions 0.5.32
