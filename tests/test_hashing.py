from watchdog.utils.hashing import sha256_bytes


class TestHashing:
    def test_deterministic(self):
        data = b"test data"
        assert sha256_bytes(data) == sha256_bytes(data)

    def test_different_inputs(self):
        assert sha256_bytes(b"hello") != sha256_bytes(b"world")

    def test_correct_length(self):
        result = sha256_bytes(b"test")
        assert len(result) == 64  # SHA-256 hex digest is 64 chars

    def test_known_hash(self):
        # SHA-256 of empty bytes
        assert sha256_bytes(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
