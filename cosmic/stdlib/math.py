"""Mathematical functions, constants, and number theory utilities for the Cosmic Standard Library."""
from __future__ import annotations
import math
import random as _random
from typing import Any

pi = math.pi
e = math.e
tau = math.tau
inf = math.inf
nan = math.nan

sqrt = math.sqrt
cbrt = getattr(math, 'cbrt', lambda x: x ** (1/3))
pow = pow
log = math.log
log2 = math.log2
log10 = math.log10
sin = math.sin
cos = math.cos
tan = math.tan
asin = math.asin
acos = math.acos
atan = math.atan
atan2 = math.atan2
degrees = math.degrees
radians = math.radians
floor = math.floor
ceil = math.ceil
trunc = math.trunc
gcd = math.gcd

def lcm(*args: int) -> int:
    """Return the least common multiple of the given integers."""
    if not args:
        raise ValueError("lcm() requires at least one argument")
    result = args[0]
    for n in args[1:]:
        result = result * n // math.gcd(result, n)
    return result

factorial = math.factorial
isqrt = math.isqrt

def isclose(a: float, b: float, rel_tol: float = 1e-9, abs_tol: float = 0.0) -> bool:
    """Check if two floats are close within tolerance."""
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max bounds."""
    return max(min_val, min(max_val, value))

def lerp(start: float, end: float, t: float) -> float:
    """Linearly interpolate between start and end at parameter t."""
    return start + (end - start) * t

def map_range(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """Map a value from one range to another."""
    if in_max == in_min:
        raise ValueError("map_range: in_min and in_max must not be equal")
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def approx_eq(a: float, b: float, tolerance: float = 1e-9) -> bool:
    """Check if two floats are approximately equal."""
    return abs(a - b) < tolerance

def fib(n: int) -> int:
    """Return the nth Fibonacci number iteratively."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def primes(limit: int) -> list[int]:
    """Return all primes up to limit using the Sieve of Eratosthenes."""
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, limit + 1, i):
                sieve[j] = False
    return [i for i in range(2, limit + 1) if sieve[i]]

def is_prime(n: int) -> bool:
    """Check if n is a prime number."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def factorize(n: int) -> list[int]:
    """Return the prime factors of n as a list (with repeats)."""
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors

def prime_factors(n: int) -> dict[int, int]:
    """Return prime factors of n mapped to their exponents."""
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors

def divisors(n: int) -> list[int]:
    """Return all divisors of n in sorted order."""
    if n == 0:
        return []
    divs = []
    for i in range(1, int(abs(n)**0.5) + 1):
        if n % i == 0:
            divs.append(i)
            if i != abs(n) // i:
                divs.append(abs(n) // i)
    return sorted(divs)

def divisors_count(n: int) -> int:
    """Return the number of divisors of n."""
    return len(divisors(n))

def digit_sum(n: int) -> int:
    """Return the sum of digits of n."""
    return sum(int(d) for d in str(abs(n)))

def is_palindrome(n: int) -> bool:
    """Check if n reads the same forwards and backwards."""
    s = str(n)
    return s == s[::-1]

def collatz_steps(n: int) -> int:
    """Return the number of steps to reach 1 via the Collatz conjecture."""
    steps = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps

def comb(n: int, k: int) -> int:
    """Return the number of combinations of n items taken k at a time."""
    return math.comb(n, k)

def perm(n: int, k: int) -> int:
    """Return the number of permutations of n items taken k at a time."""
    return math.perm(n, k)

def to_hex(n: int) -> str:
    """Convert an integer to its hexadecimal string representation."""
    return hex(n)

def to_octal(n: int) -> str:
    """Convert an integer to its octal string representation."""
    return oct(n)

def to_binary(n: int) -> str:
    """Convert an integer to its binary string representation."""
    return bin(n)

def from_hex(s: str) -> int:
    """Convert a hexadecimal string to an integer."""
    return int(s, 16)

def bit_count(n: int) -> int:
    """Count the number of set bits in n."""
    return bin(n).count('1')

def gcd_list(numbers: list[int]) -> int:
    """Return the greatest common divisor of a list of integers."""
    if not numbers:
        raise ValueError("gcd_list() requires at least one number")
    from functools import reduce
    return reduce(math.gcd, numbers)

def mean(numbers: list[float]) -> float:
    """Return the arithmetic mean of a list of numbers."""
    return sum(numbers) / len(numbers) if numbers else 0.0

def median(numbers: list[float]) -> float:
    """Return the median of a list of numbers."""
    s = sorted(numbers)
    n = len(s)
    if n == 0:
        return 0.0
    if n % 2 == 0:
        return (s[n//2 - 1] + s[n//2]) / 2
    return s[n//2]

def stdev(numbers: list[float]) -> float:
    """Return the standard deviation of a list of numbers."""
    m = mean(numbers)
    variance = sum((x - m) ** 2 for x in numbers) / len(numbers) if numbers else 0.0
    return math.sqrt(variance)

def variance(numbers: list[float]) -> float:
    """Return the variance of a list of numbers."""
    m = mean(numbers)
    return sum((x - m) ** 2 for x in numbers) / len(numbers) if numbers else 0.0

def random_int(min_val: int, max_val: int) -> int:
    """Return a random integer between min_val and max_val inclusive."""
    return _random.randint(min_val, max_val)

def random_float(min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Return a random float between min_val and max_val."""
    return _random.uniform(min_val, max_val)

def random_choice(items: list) -> Any:
    """Return a randomly selected element from a list."""
    return _random.choice(items)

def shuffle(items: list) -> list:
    """Return a new shuffled copy of the list."""
    result = list(items)
    _random.shuffle(result)
    return result

def random_sample(items: list, k: int) -> list:
    """Return k unique random elements from the list."""
    return _random.sample(items, k)
