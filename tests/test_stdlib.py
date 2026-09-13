"""Tests for the Cosmic standard library."""
import pytest
import math


class TestMath:
    def test_sqrt(self):
        from cosmic.stdlib.math import sqrt
        assert sqrt(4) == 2.0

    def test_floor(self):
        from cosmic.stdlib.math import floor
        assert floor(3.7) == 3

    def test_ceil(self):
        from cosmic.stdlib.math import ceil
        assert ceil(3.2) == 4

    def test_gcd(self):
        from cosmic.stdlib.math import gcd
        assert gcd(12, 8) == 4

    def test_factorial(self):
        from cosmic.stdlib.math import factorial
        assert factorial(5) == 120

    def test_fib(self):
        from cosmic.stdlib.math import fib
        assert fib(10) == 55
        assert fib(0) == 0
        assert fib(1) == 1

    def test_is_prime(self):
        from cosmic.stdlib.math import is_prime
        assert is_prime(2) is True
        assert is_prime(7) is True
        assert is_prime(4) is False
        assert is_prime(1) is False

    def test_primes(self):
        from cosmic.stdlib.math import primes
        assert primes(10) == [2, 3, 5, 7]

    def test_factorize(self):
        from cosmic.stdlib.math import factorize
        assert factorize(12) == [2, 2, 3]

    def test_is_palindrome(self):
        from cosmic.stdlib.math import is_palindrome
        assert is_palindrome(121) is True
        assert is_palindrome(123) is False

    def test_clamp(self):
        from cosmic.stdlib.math import clamp
        assert clamp(5, 0, 10) == 5
        assert clamp(-5, 0, 10) == 0
        assert clamp(15, 0, 10) == 10

    def test_lerp(self):
        from cosmic.stdlib.math import lerp
        assert lerp(0, 10, 0.5) == 5.0

    def test_divisors(self):
        from cosmic.stdlib.math import divisors
        assert divisors(12) == [1, 2, 3, 4, 6, 12]


class TestStrings:
    def test_upper(self):
        from cosmic.stdlib.strings import upper
        assert upper("hello") == "HELLO"

    def test_lower(self):
        from cosmic.stdlib.strings import lower
        assert lower("HELLO") == "hello"

    def test_reverse(self):
        from cosmic.stdlib.strings import reverse
        assert reverse("hello") == "olleh"

    def test_is_palindrome(self):
        from cosmic.stdlib.strings import is_palindrome
        assert is_palindrome("racecar") is True
        assert is_palindrome("hello") is False

    def test_slugify(self):
        from cosmic.stdlib.strings import slugify
        assert slugify("Hello World") == "hello-world"

    def test_truncate(self):
        from cosmic.stdlib.strings import truncate
        assert truncate("hello world", 5) == "he..."

    def test_snake_to_camel(self):
        from cosmic.stdlib.strings import snake_to_camel
        assert snake_to_camel("hello_world") == "helloWorld"

    def test_camel_to_snake(self):
        from cosmic.stdlib.strings import camel_to_snake
        assert camel_to_snake("helloWorld") == "hello_world"

    def test_levenshtein(self):
        from cosmic.stdlib.strings import levenshtein
        assert levenshtein("kitten", "sitting") == 3

    def test_levenshtein_same(self):
        from cosmic.stdlib.strings import levenshtein
        assert levenshtein("hello", "hello") == 0

    def test_word_count(self):
        from cosmic.stdlib.strings import word_count
        assert word_count("hello world foo") == 3

    def test_is_empty(self):
        from cosmic.stdlib.strings import is_empty
        assert is_empty("") is True
        assert is_empty("a") is False


class TestCollections:
    def test_flatten(self):
        from cosmic.stdlib.collections import flatten
        assert flatten([[1, 2], [3, [4, 5]]]) == [1, 2, 3, 4, 5]

    def test_unique(self):
        from cosmic.stdlib.collections import unique
        assert unique([1, 2, 2, 3, 3, 3]) == [1, 2, 3]

    def test_chunk(self):
        from cosmic.stdlib.collections import chunk
        assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

    def test_group_by(self):
        from cosmic.stdlib.collections import group_by
        result = group_by([1, 2, 3, 4], lambda x: x % 2)
        assert result[0] == [2, 4]
        assert result[1] == [1, 3]

    def test_partition(self):
        from cosmic.stdlib.collections import partition
        even, odd = partition([1, 2, 3, 4], lambda x: x % 2 == 0)
        assert even == [2, 4]
        assert odd == [1, 3]

    def test_compact(self):
        from cosmic.stdlib.collections import compact
        assert compact([0, 1, None, 2, "", 3]) == [1, 2, 3]

    def test_take(self):
        from cosmic.stdlib.collections import take
        assert take([1, 2, 3, 4, 5], 3) == [1, 2, 3]

    def test_drop(self):
        from cosmic.stdlib.collections import drop
        assert drop([1, 2, 3, 4, 5], 2) == [3, 4, 5]

    def test_memoize(self):
        from cosmic.stdlib.collections import memoize
        call_count = [0]
        @memoize
        def expensive(n):
            call_count[0] += 1
            return n * n
        assert expensive(5) == 25
        assert expensive(5) == 25
        assert call_count[0] == 1

    def test_cartesian_product(self):
        from cosmic.stdlib.collections import cartesian_product
        result = cartesian_product([1, 2], ['a', 'b'])
        assert len(result) == 4
        assert (1, 'a') in result


class TestTesting:
    def test_assert_equal(self):
        from cosmic.stdlib.testing import assert_equal
        assert_equal(1, 1)

    def test_assert_equal_fail(self):
        from cosmic.stdlib.testing import assert_equal
        with pytest.raises(AssertionError):
            assert_equal(1, 2)

    def test_assert_true(self):
        from cosmic.stdlib.testing import assert_true
        assert_true(True)

    def test_assert_raises(self):
        from cosmic.stdlib.testing import assert_raises
        assert_raises(ValueError, int, "abc")

    def test_assert_in(self):
        from cosmic.stdlib.testing import assert_in
        assert_in(1, [1, 2, 3])

    def test_test_suite(self):
        from cosmic.stdlib.testing import TestSuite
        suite = TestSuite("test")
        suite.add("passing", lambda: None if False else None)
        results = suite.run(verbose=False)
        assert len(results) == 1
        assert results[0].passed


class TestCrypto:
    def test_md5(self):
        from cosmic.stdlib.crypto import md5
        assert md5("hello") == "5d41402abc4b2a76b9719d911017c592"

    def test_sha256(self):
        from cosmic.stdlib.crypto import sha256
        h = sha256("hello")
        assert len(h) == 64

    def test_base64(self):
        from cosmic.stdlib.crypto import base64_encode, base64_decode
        encoded = base64_encode("hello")
        decoded = base64_decode(encoded)
        assert decoded == b"hello"

    def test_random_string(self):
        from cosmic.stdlib.crypto import random_string
        s = random_string(16)
        assert len(s) == 16

    def test_uuid4(self):
        from cosmic.stdlib.crypto import uuid4
        u = uuid4()
        assert len(u) == 36


class TestDateTime:
    def test_now(self):
        from cosmic.stdlib.datetime import DateTime
        now = DateTime.now()
        assert now.year > 2000

    def test_add_days(self):
        from cosmic.stdlib.datetime import DateTime
        dt = DateTime.today()
        dt2 = dt.add_days(7)
        assert dt2.day == (dt.day + 7) if dt.day + 7 <= 30 else (dt.day + 7 - 30)

    def test_to_iso(self):
        from cosmic.stdlib.datetime import DateTime
        dt = DateTime.today()
        iso = dt.to_iso()
        assert "T" in iso

    def test_weekday(self):
        from cosmic.stdlib.datetime import DateTime
        dt = DateTime.today()
        wd = dt.weekday()
        assert 0 <= wd <= 6


class TestPath:
    def test_join(self):
        from cosmic.stdlib.path import join
        result = join("a", "b", "c.txt")
        assert "a" in result
        assert "b" in result
        assert "c.txt" in result

    def test_ext(self):
        from cosmic.stdlib.path import ext
        assert ext("file.txt") == ".txt"
        assert ext("file") == ""

    def test_stem(self):
        from cosmic.stdlib.path import stem
        assert stem("file.txt") == "file"

    def test_exists(self):
        from cosmic.stdlib.path import exists
        assert exists("/") is True
        assert exists("/nonexistent_path_xyz") is False


class TestRegex:
    def test_match(self):
        from cosmic.stdlib.regex import match
        result = match(r"\d+", "abc123def")
        assert result is None

    def test_search(self):
        from cosmic.stdlib.regex import search
        result = search(r"\d+", "abc123def")
        assert result is not None
        assert result.group() == "123"

    def test_findall(self):
        from cosmic.stdlib.regex import findall
        result = findall(r"\d+", "a1b2c3")
        assert result == ["1", "2", "3"]

    def test_sub(self):
        from cosmic.stdlib.regex import sub
        result = sub(r"\d+", "X", "a1b2c3")
        assert result == "aXbXcX"

    def test_compile(self):
        from cosmic.stdlib.regex import compile
        pat = compile(r"\d+")
        result = pat.search("abc123")
        assert result is not None
