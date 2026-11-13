# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the Apache 2.0 license found in the
# LICENSE file in the root directory of this source tree.

import logging

from mock_fw_upstream.mock_fw_state import fw_state, RemoteRegion
from mock_fw_upstream.utils import bytes_to_int

logger = logging.getLogger(__name__)

DMA_ADDRESS_LIMIT: int = 1 << 64


def _resolve_dma_addr(dma_addr: bytes, length: int) -> tuple[RemoteRegion, int]:
    addr = bytes_to_int(dma_addr)
    if length < 0 or addr >= DMA_ADDRESS_LIMIT or length > DMA_ADDRESS_LIMIT - addr:
        raise RuntimeError("Invalid DMA range")
    region = find_remote_region(dma_addr)
    if region is None:
        raise RuntimeError("Could not find remote region")
    offset = addr - bytes_to_int(region.gpa)
    if length > region.size - offset:
        raise RuntimeError("DMA range exceeds remote region")
    if region.mm is None or region.mm.closed or length > len(region.mm) - offset:
        raise RuntimeError("DMA range exceeds live mmap")
    return region, offset


def dma_read(dma_addr: bytes, length: int) -> bytes:
    region, offset = _resolve_dma_addr(dma_addr, length)
    data = region.mm[offset : offset + length]
    logger.debug(
        f"DMA read: addr={bytes_to_int(dma_addr):#x}, offset={offset:#x}, "
        f"length={length}"
    )
    return data


def dma_write(dma_addr: bytes, data: bytes, length: int) -> None:
    if length != len(data):
        raise RuntimeError("DMA write length does not match payload")
    region, offset = _resolve_dma_addr(dma_addr, length)
    region.mm[offset : offset + length] = data
    logger.debug(
        f"DMA write: addr={bytes_to_int(dma_addr):#x}, offset={offset:#x}, "
        f"length={length}"
    )


def find_remote_region(dma_addr: bytes) -> RemoteRegion | None:
    addr = bytes_to_int(dma_addr)
    for region in fw_state.remote_regions:
        gpa = bytes_to_int(region.gpa)
        if (
            0 < region.size <= DMA_ADDRESS_LIMIT - gpa
            and gpa <= addr < gpa + region.size
        ):
            logger.debug(f"Found remote region {region.fd}")
            return region

    logger.error(f"Could not find remote region that contains DMA address {addr:#x}")
    return None
