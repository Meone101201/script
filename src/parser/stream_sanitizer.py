"""
Streaming XML Sanitizer for RBXLX Parser.
Filters out illegal XML 1.0 control characters and decodes invalid UTF-8 sequences incrementally.
"""

import codecs
import re
from typing import BinaryIO

# XML 1.0 Section 2.2 Character Range:
# Valid: #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
# Illegal control characters: \x00-\x08, \x0b-\x0c, \x0e-\x1f
ILLEGAL_XML_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


class CleanReader:
    """
    Wraps a raw binary stream to produce a safe UTF-8 byte stream for XML parsers like Expat.
    Avoids XML not well-formed (invalid token) crashes when encountering raw binary bytes
    or control characters in Roblox place files.
    """

    def __init__(self, raw_stream: BinaryIO, chunk_size: int = 65536):
        self.raw = raw_stream
        self.chunk_size = chunk_size
        self.decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.buffer = b""
        self._eof_reached = False

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = self.chunk_size

        while len(self.buffer) < size and not self._eof_reached:
            raw_chunk = self.raw.read(max(self.chunk_size, size))
            if not raw_chunk:
                self._eof_reached = True
                if self.decoder:
                    final_text = self.decoder.decode(b"", final=True)
                    if final_text:
                        clean_text = ILLEGAL_XML_CHARS_RE.sub("\ufffd", final_text)
                        self.buffer += clean_text.encode("utf-8")
                    self.decoder = None
                break

            text = self.decoder.decode(raw_chunk)
            clean_text = ILLEGAL_XML_CHARS_RE.sub("\ufffd", text)
            self.buffer += clean_text.encode("utf-8")

        res = self.buffer[:size]
        self.buffer = self.buffer[size:]
        return res
