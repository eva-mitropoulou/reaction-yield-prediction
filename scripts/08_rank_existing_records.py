#!/usr/bin/env python3
from reaction_yield_ml.reporting.rank_existing_records import main, parse_args


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
