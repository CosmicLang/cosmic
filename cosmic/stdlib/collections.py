"""Collection types, iterators, and data structure utilities for the Cosmic Standard Library."""
from __future__ import annotations
from typing import Any, Callable, Iterator, TypeVar, Generic, Optional
from dataclasses import dataclass, field
import heapq

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


def range_(start: int, stop: int | None = None, step: int = 1) -> list[int]:
    """Return a list from range (eagerly evaluated)."""
    if stop is None:
        stop = start
        start = 0
    return list(range(start, stop, step))


def enumerate_(iterable: Any, start: int = 0) -> list[tuple[int, Any]]:
    """Return a list of (index, value) tuples."""
    return list(enumerate(iterable, start))


def zip_(*iterables: Any) -> list[tuple]:
    """Return a list of tuples by zipping iterables together."""
    return list(zip(*iterables))


def map_(func: Callable, iterable: Any) -> list:
    """Apply func to each item and return the results as a list."""
    return list(map(func, iterable))


def filter_(func: Callable, iterable: Any) -> list:
    """Return items for which func returns true."""
    return list(filter(func, iterable))


def reduce_(func: Callable, iterable: Any, initial: Any = None) -> Any:
    """Reduce iterable using func with optional initial value."""
    from functools import reduce
    if initial is not None:
        return reduce(func, iterable, initial)
    return reduce(func, iterable)


def sorted_(iterable: Any, key: Callable | None = None, reverse: bool = False) -> list:
    """Return a new sorted list from the iterable."""
    return sorted(iterable, key=key, reverse=reverse)


def reversed_(iterable: Any) -> list:
    """Return a new list with elements in reverse order."""
    return list(reversed(iterable))


def any_(iterable: Any) -> bool:
    """Return True if any element is truthy."""
    return any(iterable)


def all_(iterable: Any) -> bool:
    """Return True if all elements are truthy."""
    return all(iterable)


def min_(*args: Any, key: Callable | None = None) -> Any:
    """Return the minimum value from the given arguments."""
    if len(args) == 0:
        raise TypeError("min_() requires at least one argument")
    if len(args) == 1:
        return min(args[0], key=key) if key else min(args[0])
    return min(args, key=key) if key else min(args)


def max_(*args: Any, key: Callable | None = None) -> Any:
    """Return the maximum value from the given arguments."""
    if len(args) == 0:
        raise TypeError("max_() requires at least one argument")
    if len(args) == 1:
        return max(args[0], key=key) if key else max(args[0])
    return max(args, key=key) if key else max(args)


def sum_(iterable: Any, start: int | float = 0) -> int | float:
    """Return the sum of iterable with optional start value."""
    return sum(iterable, start)


def abs_(x: int | float) -> int | float:
    """Return the absolute value of x."""
    return abs(x)


def round_(x: float, ndigits: int = 0) -> float:
    """Round x to the given number of decimal places."""
    return round(x, ndigits)


def flatten(iterable: Any) -> list:
    """Flatten one level of nesting in an iterable."""
    result = []
    seen_ids = set()
    for item in iterable:
        item_id = id(item)
        if item_id in seen_ids:
            result.append(item)
            continue
        if hasattr(item, '__iter__') and not isinstance(item, (str, bytes)):
            seen_ids.add(item_id)
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def unique(iterable: Any) -> list:
    """Return unique elements preserving order."""
    seen = set()
    result = []
    for item in iterable:
        try:
            key = item
            if isinstance(item, list):
                key = tuple(item)
            elif isinstance(item, dict):
                key = tuple(sorted(item.items()))
            if key not in seen:
                seen.add(key)
                result.append(item)
        except TypeError:
            result.append(item)
    return result


def chunk(iterable: Any, size: int) -> list[list]:
    """Split iterable into chunks of the given size."""
    result = []
    chunk_ = []
    for item in iterable:
        chunk_.append(item)
        if len(chunk_) == size:
            result.append(chunk_)
            chunk_ = []
    if chunk_:
        result.append(chunk_)
    return result


def interleave(*iterables: Any) -> list:
    """Interleave elements from multiple iterables."""
    result = []
    iterators = [iter(it) for it in iterables]
    while True:
        for it in iterators:
            try:
                result.append(next(it))
            except StopIteration:
                return result


def group_by(iterable: Any, key_func: Callable) -> dict:
    """Group items by the result of key_func."""
    groups = {}
    for item in iterable:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups


def count_by(iterable: Any, key_func: Callable) -> dict:
    """Count items by the result of key_func."""
    counts = {}
    for item in iterable:
        key = key_func(item)
        counts[key] = counts.get(key, 0) + 1
    return counts


def partition(iterable: Any, predicate: Callable) -> tuple[list, list]:
    """Split items into those matching predicate and those that don't."""
    true_list, false_list = [], []
    for item in iterable:
        if predicate(item):
            true_list.append(item)
        else:
            false_list.append(item)
    return true_list, false_list


def take(iterable: Any, n: int) -> list:
    """Take the first n items from iterable."""
    return list(iterable)[:n]


def drop(iterable: Any, n: int) -> list:
    """Drop the first n items and return the rest."""
    return list(iterable)[n:]


def compact(iterable: Any) -> list:
    """Remove falsy values from iterable."""
    return [x for x in iterable if x]


def flatten_deep(iterable: Any) -> list:
    """Flatten nested iterables recursively."""
    return flatten(iterable)


@dataclass
class TreeMap(Generic[K, V]):
    _data: dict[K, V] = field(default_factory=dict)

    def get(self, key: K, default: V | None = None) -> V | None:
        """Return the value for key, or default if not found."""
        return self._data.get(key, default)

    def put(self, key: K, value: V) -> None:
        """Insert or update a key-value pair."""
        self._data[key] = value

    def remove(self, key: K) -> V | None:
        """Remove and return the value for key, or None."""
        return self._data.pop(key, None)

    def contains(self, key: K) -> bool:
        """Check if the key exists in the map."""
        return key in self._data

    def keys(self) -> list[K]:
        """Return all keys in the map."""
        return list(self._data.keys())

    def values(self) -> list[V]:
        """Return all values in the map."""
        return list(self._data.values())

    def items(self) -> list[tuple[K, V]]:
        """Return all key-value pairs."""
        return list(self._data.items())

    def size(self) -> int:
        """Return the number of entries."""
        return len(self._data)

    def is_empty(self) -> bool:
        """Check if the map is empty."""
        return len(self._data) == 0

    def clear(self) -> None:
        """Remove all entries from the map."""
        self._data.clear()

    def merge(self, other: TreeMap[K, V]) -> TreeMap[K, V]:
        """Return a new map with entries from both maps."""
        result = TreeMap()
        result._data = {**self._data, **other._data}
        return result

    def filter(self, predicate: Callable[[K, V], bool]) -> TreeMap[K, V]:
        """Return a new map containing only entries matching the predicate."""
        result = TreeMap()
        for k, v in self._data.items():
            if predicate(k, v):
                result._data[k] = v
        return result

    def map_values(self, func: Callable[[V], Any]) -> TreeMap[K, Any]:
        """Return a new map with values transformed by func."""
        result = TreeMap()
        for k, v in self._data.items():
            result._data[k] = func(v)
        return result

    def __contains__(self, key: K) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"TreeMap({self._data})"


@dataclass
class Queue(Generic[T]):
    _items: list[T] = field(default_factory=list)

    def enqueue(self, item: T) -> None:
        """Add an item to the end of the queue."""
        self._items.append(item)

    def dequeue(self) -> T:
        """Remove and return the item at the front of the queue."""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self._items.pop(0)

    def peek(self) -> T:
        """Return the item at the front without removing it."""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self._items[0]

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self._items) == 0

    def size(self) -> int:
        """Return the number of items in the queue."""
        return len(self._items)

    def to_list(self) -> list[T]:
        """Return a list of items in queue order."""
        return list(self._items)


@dataclass
class Stack(Generic[T]):
    _items: list[T] = field(default_factory=list)

    def push(self, item: T) -> None:
        """Push an item onto the top of the stack."""
        self._items.append(item)

    def pop(self) -> T:
        """Remove and return the top item from the stack."""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self._items.pop()

    def peek(self) -> T:
        """Return the top item without removing it."""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self._items[-1]

    def is_empty(self) -> bool:
        """Check if the stack is empty."""
        return len(self._items) == 0

    def size(self) -> int:
        """Return the number of items in the stack."""
        return len(self._items)

    def to_list(self) -> list[T]:
        """Return items from top to bottom."""
        return list(reversed(self._items))


@dataclass
class PriorityQueue(Generic[T]):
    _heap: list = field(default_factory=list)
    _counter: int = 0

    def push(self, item: T, priority: int = 0) -> None:
        """Add an item with the given priority (lower is higher priority)."""
        heapq.heappush(self._heap, (priority, self._counter, item))
        self._counter += 1

    def pop(self) -> T:
        """Remove and return the highest-priority item."""
        if self.is_empty():
            raise IndexError("PriorityQueue is empty")
        _, _, item = heapq.heappop(self._heap)
        return item

    def peek(self) -> T:
        """Return the highest-priority item without removing it."""
        if self.is_empty():
            raise IndexError("PriorityQueue is empty")
        return self._heap[0][2]

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self._heap) == 0

    def size(self) -> int:
        """Return the number of items in the queue."""
        return len(self._heap)


@dataclass
class LinkedList(Generic[T]):
    class Node:
        def __init__(self, data: T, next_node: Optional['LinkedList.Node'] = None):
            self.data = data
            self.next = next_node

    head: Optional[Node] = None
    _size: int = 0

    def append(self, data: T) -> None:
        """Append an element to the end of the list."""
        if self.head is None:
            self.head = LinkedList.Node(data)
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = LinkedList.Node(data)
        self._size += 1

    def prepend(self, data: T) -> None:
        """Prepend an element to the beginning of the list."""
        self.head = LinkedList.Node(data, self.head)
        self._size += 1

    def delete(self, data: T) -> bool:
        """Delete the first occurrence of data. Return True if found."""
        if self.head is None:
            return False
        if self.head.data == data:
            self.head = self.head.next
            self._size -= 1
            return True
        current = self.head
        while current.next:
            if current.next.data == data:
                current.next = current.next.next
                self._size -= 1
                return True
            current = current.next
        return False

    def find(self, data: T) -> bool:
        """Check if data exists in the list."""
        current = self.head
        while current:
            if current.data == data:
                return True
            current = current.next
        return False

    def to_list(self) -> list[T]:
        """Convert the linked list to a Python list."""
        result = []
        current = self.head
        while current:
            result.append(current.data)
            current = current.next
        return result

    def size(self) -> int:
        """Return the number of elements in the list."""
        return self._size

    def is_empty(self) -> bool:
        """Check if the list is empty."""
        return self._size == 0

    def reverse(self) -> None:
        """Reverse the list in place."""
        prev = None
        current = self.head
        while current:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
        self.head = prev

    def __repr__(self) -> str:
        return f"LinkedList({self.to_list()})"


def deep_copy(obj: Any) -> Any:
    """Return a deep copy of the object."""
    import copy
    return copy.deepcopy(obj)


def memoize(func: Callable) -> Callable:
    """Cache function results based on arguments."""
    cache = {}
    def wrapper(*args):
        key = args
        if key not in cache:
            cache[key] = func(*args)
        return cache[key]
    wrapper.cache = cache
    return wrapper


def chain(*iterables: Any) -> Iterator:
    """Chain iterables into a single iterator."""
    for it in iterables:
        yield from it


def sliding_window(iterable: Any, size: int) -> list[list]:
    """Return sliding windows of the given size."""
    it = list(iterable)
    return [it[i:i+size] for i in range(len(it) - size + 1)]


def cartesian_product(*iterables: Any) -> list[tuple]:
    """Return the Cartesian product of the given iterables."""
    result = [[]]
    for iterable in iterables:
        result = [x + [y] for x in result for y in iterable]
    return [tuple(x) for x in result]
