#!/usr/bin/env python3
from reaction_yield_ml.data.audit_dataset import main, parse_args


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
