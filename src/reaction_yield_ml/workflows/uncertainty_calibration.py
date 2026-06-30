#!/usr/bin/env python3
from reaction_yield_ml.uncertainty.estimate_uncertainty import main, parse_args


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
