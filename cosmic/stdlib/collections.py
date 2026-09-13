"""Cosmic Standard Library — collections module."""
from __future__ import annotations
from typing import Any, Callable, Iterator, TypeVar, Generic, Optional
from dataclasses import dataclass, field
from collections import OrderedDict
import heapq

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


def range_(start: int, stop: int | None = None, step: int = 1) -> list[int]:
    if stop is None:
        stop = start
        start = 0
    return list(range(start, stop, step))


def enumerate_(iterable: Any, start: int = 0) -> list[tuple[int, Any]]:
    return list(enumerate(iterable, start))


def zip_(*iterables: Any) -> list[tuple]:
    return list(zip(*iterables))


def map_(func: Callable, iterable: Any) -> list:
    return list(map(func, iterable))


def filter_(func: Callable, iterable: Any) -> list:
    return list(filter(func, iterable))


def reduce_(func: Callable, iterable: Any, initial: Any = None) -> Any:
    from functools import reduce
    if initial is not None:
        return reduce(func, iterable, initial)
    return reduce(func, iterable)


def sorted_(iterable: Any, key: Callable | None = None, reverse: bool = False) -> list:
    return sorted(iterable, key=key, reverse=reverse)


def reversed_(iterable: Any) -> list:
    return list(reversed(iterable))


def any_(iterable: Any) -> bool:
    return any(iterable)


def all_(iterable: Any) -> bool:
    return all(iterable)


def min_(*args: Any, key: Callable | None = None) -> Any:
    if len(args) == 1:
        return min(args[0], key=key) if key else min(args[0])
    return min(args, key=key) if key else min(args)


def max_(*args: Any, key: Callable | None = None) -> Any:
    if len(args) == 1:
        return max(args[0], key=key) if key else max(args[0])
    return max(args, key=key) if key else max(args)


def sum_(iterable: Any, start: int | float = 0) -> int | float:
    return sum(iterable, start)


def abs_(x: int | float) -> int | float:
    return abs(x)


def round_(x: float, ndigits: int = 0) -> float:
    return round(x, ndigits)


def flatten(iterable: Any) -> list:
    result = []
    for item in iterable:
        if hasattr(item, '__iter__') and not isinstance(item, (str, bytes)):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def unique(iterable: Any) -> list:
    seen = set()
    result = []
    for item in iterable:
        key = item
        if isinstance(item, list):
            key = tuple(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def chunk(iterable: Any, size: int) -> list[list]:
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
    result = []
    iterators = [iter(it) for it in iterables]
    while True:
        for it in iterators:
            try:
                result.append(next(it))
            except StopIteration:
                return result
    return result


def group_by(iterable: Any, key_func: Callable) -> dict:
    groups = {}
    for item in iterable:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups


def count_by(iterable: Any, key_func: Callable) -> dict:
    counts = {}
    for item in iterable:
        key = key_func(item)
        counts[key] = counts.get(key, 0) + 1
    return counts


def partition(iterable: Any, predicate: Callable) -> tuple[list, list]:
    true_list, false_list = [], []
    for item in iterable:
        if predicate(item):
            true_list.append(item)
        else:
            false_list.append(item)
    return true_list, false_list


def take(iterable: Any, n: int) -> list:
    return list(iterable)[:n]


def drop(iterable: Any, n: int) -> list:
    return list(iterable)[n:]


def compact(iterable: Any) -> list:
    return [x for x in iterable if x]


def flatten_deep(iterable: Any) -> list:
    result = []
    for item in iterable:
        if hasattr(item, '__iter__') and not isinstance(item, (str, bytes)):
            result.extend(flatten_deep(item))
        else:
            result.append(item)
    return result


@dataclass
class TreeMap(Generic[K, V]):
    _data: dict[K, V] = field(default_factory=dict)

    def get(self, key: K, default: V | None = None) -> V | None:
        return self._data.get(key, default)

    def put(self, key: K, value: V) -> None:
        self._data[key] = value

    def remove(self, key: K) -> V | None:
        return self._data.pop(key, None)

    def contains(self, key: K) -> bool:
        return key in self._data

    def keys(self) -> list[K]:
        return list(self._data.keys())

    def values(self) -> list[V]:
        return list(self._data.values())

    def items(self) -> list[tuple[K, V]]:
        return list(self._data.items())

    def size(self) -> int:
        return len(self._data)

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def clear(self) -> None:
        self._data.clear()

    def merge(self, other: TreeMap[K, V]) -> TreeMap[K, V]:
        result = TreeMap()
        result._data = {**self._data, **other._data}
        return result

    def filter(self, predicate: Callable[[K, V], bool]) -> TreeMap[K, V]:
        result = TreeMap()
        for k, v in self._data.items():
            if predicate(k, v):
                result._data[k] = v
        return result

    def map_values(self, func: Callable[[V], Any]) -> TreeMap[K, Any]:
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
        self._items.append(item)

    def dequeue(self) -> T:
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self._items.pop(0)

    def peek(self) -> T:
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self._items[0]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:
        return len(self._items)

    def to_list(self) -> list[T]:
        return list(self._items)


@dataclass
class Stack(Generic[T]):
    _items: list[T] = field(default_factory=list)

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self._items.pop()

    def peek(self) -> T:
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self._items[-1]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:
        return len(self._items)

    def to_list(self) -> list[T]:
        return list(reversed(self._items))


@dataclass
class PriorityQueue(Generic[T]):
    _heap: list = field(default_factory=list)
    _counter: int = 0

    def push(self, item: T, priority: int = 0) -> None:
        heapq.heappush(self._heap, (priority, self._counter, item))
        self._counter += 1

    def pop(self) -> T:
        if self.is_empty():
            raise IndexError("PriorityQueue is empty")
        _, _, item = heapq.heappop(self._heap)
        return item

    def peek(self) -> T:
        if self.is_empty():
            raise IndexError("PriorityQueue is empty")
        return self._heap[0][2]

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def size(self) -> int:
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
        if self.head is None:
            self.head = LinkedList.Node(data)
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = LinkedList.Node(data)
        self._size += 1

    def prepend(self, data: T) -> None:
        self.head = LinkedList.Node(data, self.head)
        self._size += 1

    def delete(self, data: T) -> bool:
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
        current = self.head
        while current:
            if current.data == data:
                return True
            current = current.next
        return False

    def to_list(self) -> list[T]:
        result = []
        current = self.head
        while current:
            result.append(current.data)
            current = current.next
        return result

    def size(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    def reverse(self) -> None:
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
    import copy
    return copy.deepcopy(obj)


def memoize(func: Callable) -> Callable:
    cache = {}
    def wrapper(*args):
        key = args
        if key not in cache:
            cache[key] = func(*args)
        return cache[key]
    wrapper.cache = cache
    return wrapper


def chain(*iterables: Any) -> Iterator:
    for it in iterables:
        yield from it


def sliding_window(iterable: Any, size: int) -> list[list]:
    it = list(iterable)
    return [it[i:i+size] for i in range(len(it) - size + 1)]


def cartesian_product(*iterables: Any) -> list[tuple]:
    result = [[]]
    for iterable in iterables:
        result = [x + [y] for x in result for y in iterable]
    return [tuple(x) for x in result]
