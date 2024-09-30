import asyncio
from collections import defaultdict
import itertools
import json
import logging

import aiohttp
from packaging import version

from package_compare.types import RequestData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = "https://rdb.altlinux.org/api/export/branch_binary_packages/"


class PackageComparatorAsync:
    branch_sisyphus = "sisyphus"
    branch_p10 = "p10"
    __slots__ = ("data",)

    def __init__(self) -> None:
        self.data: dict[str, dict[str, dict[str, str]]] = {
            self.branch_sisyphus: {},
            self.branch_p10: {},
        }

    async def fetch_packages(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for branch in [self.branch_sisyphus, self.branch_p10]:
                url = f"{API_BASE_URL}{branch}"
                logger.info(f"Fetching packages from {url}")
                tasks.append(self._fetch_branch_packages(session, branch, url))
            await asyncio.gather(*tasks)
        logger.info("Successfully fetched and processed package data.")

    async def _fetch_branch_packages(self, session: aiohttp.ClientSession, branch: str, url: str) -> None:
        async with session.get(url) as response:
            if response.status != 200:
                logger.error(f"Failed to fetch data for branch '{branch}'. Status code: {response.status}")
                raise Exception(f"API request failed for branch '{branch}'")
            packages: RequestData = await response.json()
            self.data[branch] = self._process_packages(packages)

    def _process_packages(self, packages: RequestData):
        processed = defaultdict(dict)
        for pkg in packages["packages"]:
            logger.info(pkg.get("version"))
            name = pkg.get("name")
            version_release = f"{pkg.get('version')}-{pkg.get('release')}"
            arch = pkg.get("arch")
            if name and version_release and arch:
                processed[arch][name] = version_release
        return processed

    async def compare_packages(self):
        comparison = {}
        for arch in set(
            itertools.chain(
                self.data[self.branch_sisyphus].keys(),
                self.data[self.branch_p10].keys(),
            )
        ):
            comparison[arch] = {
                "only_in_p10": [],
                "only_in_sisyphus": [],
                "p10_newer": [],
                "sisyphus_newer": [],
            }
            packages_sisyphus = self.data[self.branch_sisyphus].get(arch, {})
            packages_p10 = self.data[self.branch_p10].get(arch, {})

            all_packages = set(packages_sisyphus.keys()).union(set(packages_p10.keys()))
            for pkg in all_packages:
                ver_sis = packages_sisyphus.get(pkg)
                ver_p10 = packages_p10.get(pkg)
                if ver_sis and not ver_p10:
                    comparison[arch]["only_in_sisyphus"].append(pkg)
                elif ver_p10 and not ver_sis:
                    comparison[arch]["only_in_p10"].append(pkg)
                elif ver_sis and ver_p10:
                    if self._compare_versions(ver_sis, ver_p10) > 0:
                        comparison[arch]["sisyphus_newer"].append(pkg)
                    elif self._compare_versions(ver_sis, ver_p10) < 0:
                        comparison[arch]["p10_newer"].append(pkg)
            comparison[arch] = {k: v for k, v in comparison[arch].items() if v}
        return comparison

    def _compare_versions(self, ver1: str, ver2: str) -> int:
        try:
            ver1_obj = version.parse(ver1.split("-")[0])
            ver2_obj = version.parse(ver2.split("-")[0])
            if ver1_obj > ver2_obj:
                return 1
            elif ver1_obj < ver2_obj:
                return -1
            else:
                if ver1.split("-")[1] > ver2.split("-")[1]:
                    return 1
                elif ver1.split("-")[1] < ver2.split("-")[1]:
                    return -1
                else:
                    return 0
        except Exception:
            try:
                if version.parse(".".join(char for char in ver1.split("-")[0] if char.isdigit())) > version.parse(
                    ".".join(char for char in ver2.split("-")[0] if char.isdigit())
                ):
                    return 1
                elif version.parse(".".join(char for char in ver1.split("-")[0] if char.isdigit())) < version.parse(
                    ".".join(char for char in ver2.split("-")[0] if char.isdigit())
                ):
                    return -1
                else:
                    return 0
            except Exception as e:
                logger.error(f"Error comparing versions '{ver1}' and '{ver2}': {e}")
                return 0

    async def generate_report(self):
        await self.fetch_packages()
        comparison = await self.compare_packages()
        report = json.dumps(comparison, indent=4)
        return report
