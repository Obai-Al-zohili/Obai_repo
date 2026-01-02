class Cache:
    def __init__(self):
        self._store = {}

    def get(self, key):
        # BUG: returns default even when key exists but value is falsy (0, "", False)
        if key in self._store:
            return self._store[key]
        return None

    def set(self, key, value):
        # BUG: accidentally clears the entire cache
        self._store[key] = value

def test_cache_get():
    cache = Cache()
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

def test_cache_get_falsy_values():
    cache = Cache()
    cache.set("zero", 0)
    cache.set("empty", "")
    cache.set("false", False)
    assert cache.get("zero") == 0
    assert cache.get("empty") == ""
    assert cache.get("false") == False

def test_cache_multiple_values():
    cache = Cache()
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"