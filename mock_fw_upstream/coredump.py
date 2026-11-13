# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the Apache 2.0 license found in the
# LICENSE file in the root directory of this source tree.

import errno
import logging

logger = logging.getLogger(__name__)

COREDUMP_SIZE = 0x2000


class CoredumpManager:
    def __init__(self, size: int = COREDUMP_SIZE):
        if size < 8:
            raise ValueError("Coredump must fit both test tags")
        self._coredump = bytearray(size)

        # Test tags
        self._coredump[0:4] = b"\xde\xad\xbe\xef"
        self._coredump[-4:] = b"\xde\xad\xbe\xef"

    def get_coredump_length(self) -> int:
        return len(self._coredump)

    def read_coredump(self, buffer: bytearray, offset: int, length: int) -> int:
        size = self.get_coredump_length()
        if offset < 0 or offset >= size:
            logger.error(f"Invalid offset {offset} (must be 0-{size - 1})")
            return errno.EINVAL

        if length <= 0:
            logger.error(f"Invalid length {length} (must be > 0)")
            return errno.EINVAL

        if offset + length > size:
            logger.error(
                f"Read exceeds COREDUMP bounds: offset={offset}, length={length}, "
                f"end={offset + length} > size={size}"
            )
            return errno.EOVERFLOW

        buffer[:length] = self._coredump[offset : offset + length]
        return 0
