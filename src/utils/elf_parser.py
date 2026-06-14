from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ELFInfo:
    arch: str
    bits: int  # 32 or 64
    is_little_endian: bool


_ELF_MACHINE = {
    0x03: "x86",
    0x3E: "x86_64",
    0x28: "ARM",
    0xB7: "AArch64",
}

_ABI_FROM_ARCH = {
    "ARM": "armeabi-v7a",
    "AArch64": "arm64-v8a",
    "x86": "x86",
    "x86_64": "x86_64",
}


def parse_elf_header(filepath: str | Path) -> ELFInfo | None:
    try:
        with open(filepath, "rb") as f:
            magic = f.read(4)
            if magic != b"\x7fELF":
                return None

            ei_class = struct.unpack("B", f.read(1))[0]
            ei_data = struct.unpack("B", f.read(1))[0]
            bits = 64 if ei_class == 2 else 32
            is_little_endian = ei_data == 1

            endian = "<" if is_little_endian else ">"
            f.seek(0x12 if bits == 32 else 0x12)
            f.seek(0x12)
            machine = struct.unpack(endian + "H", f.read(2))[0]
            arch = _ELF_MACHINE.get(machine, f"Unknown({machine:#x})")

            return ELFInfo(arch=arch, bits=bits, is_little_endian=is_little_endian)
    except (OSError, struct.error):
        return None


def detect_abi_from_elf(filepath: str | Path) -> str | None:
    info = parse_elf_header(filepath)
    if info is None:
        return None
    return _ABI_FROM_ARCH.get(info.arch)


def detect_abi_from_path(path: str) -> str | None:
    path_lower = path.lower()
    for abi in ("arm64-v8a", "armeabi-v7a", "x86_64", "x86", "armeabi"):
        if abi in path_lower:
            return abi
    return None
