import argparse
import asyncio

from package_compare.compare import PackageComparatorAsync


async def main():
    parser = argparse.ArgumentParser(description="Compare binary packages between 'sisyphus' and 'p10' branches.")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output file to save the JSON report. If not specified, prints to stdout.",
    )
    args = parser.parse_args()

    comparator = PackageComparatorAsync()
    report = await comparator.generate_report()

    with open(args.output, "w") as f:
        f.write(report)
    print(f"Report saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
