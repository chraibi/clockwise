from clockwise.cli import build_parser


def test_cli_defaults():
    args = build_parser().parse_args([])
    assert args.seeds == 10
    assert 0.0 in args.fractions
