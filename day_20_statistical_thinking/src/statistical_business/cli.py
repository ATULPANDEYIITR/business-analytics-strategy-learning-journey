# File: src/statistical_business/cli.py

from __future__ import annotations

"""Command-line interface for the educational business statistics toolkit."""

import argparse
import json

from .business import analyze_ab_test, customer_lifetime_value
from .core import correlation, describe, linear_regression


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statistical Thinking for Business Decisions"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    describe_parser = subparsers.add_parser("describe")
    describe_parser.add_argument("values", nargs="+", type=float)

    correlation_parser = subparsers.add_parser("correlation")
    correlation_parser.add_argument("--x", nargs="+", type=float, required=True)
    correlation_parser.add_argument("--y", nargs="+", type=float, required=True)

    regression_parser = subparsers.add_parser("regression")
    regression_parser.add_argument("--x", nargs="+", type=float, required=True)
    regression_parser.add_argument("--y", nargs="+", type=float, required=True)
    regression_parser.add_argument("--predict", type=float, required=True)

    ab_parser = subparsers.add_parser("ab-test")
    ab_parser.add_argument("--control-conversions", type=int, required=True)
    ab_parser.add_argument("--control-visitors", type=int, required=True)
    ab_parser.add_argument("--treatment-conversions", type=int, required=True)
    ab_parser.add_argument("--treatment-visitors", type=int, required=True)

    clv_parser = subparsers.add_parser("clv")
    clv_parser.add_argument("--order-value", type=float, required=True)
    clv_parser.add_argument("--frequency", type=float, required=True)
    clv_parser.add_argument("--margin", type=float, required=True)
    clv_parser.add_argument("--retention", type=float, required=True)

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "describe":
        result = describe(args.values)

    elif args.command == "correlation":
        result = {"correlation": correlation(args.x, args.y)}

    elif args.command == "regression":
        model = linear_regression(args.x, args.y)
        result = {
            "slope": model.slope,
            "intercept": model.intercept,
            "r_squared": model.r_squared,
            "prediction": model.predict(args.predict),
        }

    elif args.command == "ab-test":
        result = analyze_ab_test(
            args.control_conversions,
            args.control_visitors,
            args.treatment_conversions,
            args.treatment_visitors,
        ).__dict__

    else:
        result = {
            "customer_lifetime_value": customer_lifetime_value(
                args.order_value,
                args.frequency,
                args.margin,
                args.retention,
            )
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
