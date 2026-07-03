# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""eCircuit: AI-powered electronic circuit design toolkit."""


def main() -> None:
    import sys

    from .cli import main as cli_main

    sys.exit(cli_main())
