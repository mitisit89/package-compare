from typing import TypedDict


class PackageInfo(TypedDict):
    name: str
    epoch: int
    version: str
    release: str
    arch: str
    disttag: str
    buildtime: int
    source: str


class RequestData(TypedDict):
    request_args: dict[str, str] | dict[None, None]
    length: int
    packages: list[PackageInfo]
