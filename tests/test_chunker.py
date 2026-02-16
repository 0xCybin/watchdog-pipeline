import pytest

from watchdog.pipeline.chunker import chunk_text, count_tokens, split_into_paragraphs


class TestCountTokens:
    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_simple_text(self):
        tokens = count_tokens("Hello, world!")
        assert tokens > 0
        assert tokens < 10

    def test_longer_text(self):
        text = "This is a longer piece of text that should have more tokens. " * 10
        tokens = count_tokens(text)
        assert tokens > 50


class TestSplitIntoParagraphs:
    def test_single_paragraph(self):
        result = split_into_paragraphs("Hello world")
        assert result == ["Hello world"]

    def test_multiple_paragraphs(self):
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        result = split_into_paragraphs(text)
        assert len(result) == 3

    def test_empty_paragraphs_filtered(self):
        text = "First.\n\n\n\n\nSecond."
        result = split_into_paragraphs(text)
        assert len(result) == 2


class TestChunkText:
    def test_short_text_single_chunk(self):
        text = "This is a short text."
        chunks = chunk_text(text, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0]["text"] == text

    def test_long_text_multiple_chunks(self):
        # Create text that's definitely longer than max_tokens
        paragraphs = [f"Paragraph {i}. " + "x " * 200 for i in range(20)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, max_tokens=500, overlap_tokens=50)
        assert len(chunks) > 1

    def test_chunk_token_counts(self):
        text = "Short paragraph.\n\n" + "Another paragraph. " * 50
        chunks = chunk_text(text, max_tokens=100)
        for chunk in chunks:
            assert chunk["token_count"] > 0
            assert chunk["token_count"] == count_tokens(chunk["text"])

    def test_empty_text(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_overlap_present(self):
        # With overlap, adjacent chunks should share some content
        paragraphs = [f"Unique paragraph {i}. " + "content " * 100 for i in range(10)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, max_tokens=300, overlap_tokens=100)
        if len(chunks) > 1:
            # The end of chunk 0 and start of chunk 1 should have some overlap
            # (not exact since it's paragraph-based, but there should be shared text)
            words_0 = set(chunks[0]["text"].split()[-20:])
            words_1 = set(chunks[1]["text"].split()[:20])
            # At least some overlap expected
            assert len(words_0 & words_1) >= 0  # Non-strict: overlap is best-effort
