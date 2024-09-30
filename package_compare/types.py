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


class Comparison(TypedDict):
    only_in_p10: list[str]
    only_in_sisyphus: list[str]
    p10_newer: list[str]
    sisyphus_newer: list[str]
