# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

import ecircuit
import ecircuit.rendering
import ecircuit.simulation
import ecircuit.text2circuit
import ecircuit.text2pcb


def test_package_imports() -> None:
    assert callable(ecircuit.main)
