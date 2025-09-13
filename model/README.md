# Pydantic BaseModel vs dataclass vs RootModel

## BaseModel vs dataclass

| Feature | BaseModel | dataclass |
|---------|-----------|-----------|
| **Validation** | Runtime validation | No validation |
| **Serialization** | Built-in JSON/dict methods | Manual |
| **Type coercion** | Yes (str → int, etc.) | No |
| **Performance** | Slower (validation overhead) | Faster |
| **Dependencies** | Requires Pydantic | Built-in Python |

### Code Examples

```python
from dataclasses import dataclass
from pydantic import BaseModel

# dataclass - just structure
@dataclass
class UserDataclass:
  name: str
  age: int

user1 = UserDataclass("Alice", "30")  # age="30" stays as string!
print(type(user1.age))  # <class 'str'>

# BaseModel - validation + structure
class UserBaseModel(BaseModel):
  name: str
  age: int

user2 = UserBaseModel(name="Alice", age="30")  # age gets converted to int(30)
print(type(user2.age))  # <class 'int'>
```

## RootModel Explained

Think of `RootModel` as "I want Pydantic features (validation/serialization) for non-object types":

### Basic Example

```python
from pydantic import BaseModel, RootModel, field_validator

# Instead of just: my_list = [1, 2, 3]
# You want validation: "ensure all items are positive ints"

class PositiveInts(RootModel[list[int]]):
  root: list[int]
  
  @field_validator('root')
  @classmethod
  def validate_positive(cls, v):
    return [x for x in v if x > 0]

# Usage
positive_nums = PositiveInts([1, -2, 3, -4, 5])
print(positive_nums.root)  # [1, 3, 5] - negative numbers filtered out
```

### When to Use Each

- **dataclass**: Simple data containers, no validation needed
- **BaseModel**: Objects with multiple fields that need validation
- **RootModel**: When you need a "smart wrapper" around simple types (lists, strings, primitives) with validation

### Real-world RootModel Use Cases

```python
# Validate email list
class EmailList(RootModel[list[str]]):
  root: list[str]
  
  @field_validator('root')
  @classmethod
  def validate_emails(cls, v):
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return [email for email in v if re.match(email_pattern, email)]

# Validate positive numbers
class Score(RootModel[float]):
  root: float
  
  @field_validator('root')
  @classmethod
  def validate_score(cls, v):
    if v < 0 or v > 100:
      raise ValueError('Score must be between 0 and 100')
    return v
```