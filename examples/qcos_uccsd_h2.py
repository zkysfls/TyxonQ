"""H2 UCCSD circuit on 移动云量子真机 using only {h, rx, rz, cx} gates.

This example builds a UCCSD ansatz for H2 (STO-3G, 4 qubits, Jordan-Wigner)
and submits it to the WuYue cloud platform.
"""

import math
from tyxonq import Circuit


def pauli_evolution(c, pauli_string, theta):
    """Apply exp(-i * theta * P) where P is a Pauli string.

    Uses only {h, rz, cx} gates.
    - X basis: H
    - Y basis: Rz(-pi/2) then H  (equivalent to Sdg + H)
    - Z basis: no change

    Args:
        c: TyxonQ Circuit
        pauli_string: list of (qubit, pauli) tuples, e.g. [(0,'X'), (1,'Y'), (2,'Z')]
        theta: rotation angle
    """
    qubits = [q for q, _ in pauli_string]

    # Basis rotation into Z basis
    for q, p in pauli_string:
        if p == "X":
            c.h(q)
        elif p == "Y":
            c.rz(q, -math.pi / 2)
            c.h(q)

    # CNOT ladder to compute parity
    for i in range(len(qubits) - 1):
        c.cx(qubits[i], qubits[i + 1])

    # Rz rotation on last qubit
    c.rz(qubits[-1], theta)

    # Reverse CNOT ladder
    for i in range(len(qubits) - 2, -1, -1):
        c.cx(qubits[i], qubits[i + 1])

    # Reverse basis rotation
    for q, p in pauli_string:
        if p == "X":
            c.h(q)
        elif p == "Y":
            c.h(q)
            c.rz(q, math.pi / 2)


def build_h2_uccsd(theta):
    """Build H2 UCCSD circuit (4 qubits, STO-3G, Jordan-Wigner).

    The double excitation operator T2 - T2† for exciting electrons
    from orbitals (0,1) to (2,3) decomposes under Jordan-Wigner into
    8 Pauli string terms, each implemented via pauli_evolution.

    Only uses {h, rx, rz, cx} gates.
    """
    c = Circuit(4)

    # Step 1: Prepare Hartree-Fock state |1100>
    # (2 electrons occupying lowest orbitals)
    c.rx(0, math.pi)
    c.rx(1, math.pi)

    # Step 2: Apply UCCSD double excitation
    # exp(theta * (a†2 a†3 a1 a0 - h.c.))
    #
    # Jordan-Wigner decomposition into 8 Pauli strings:
    terms = [
        ([(0, "X"), (1, "X"), (2, "X"), (3, "Y")], +1),
        ([(0, "X"), (1, "X"), (2, "Y"), (3, "X")], -1),
        ([(0, "X"), (1, "Y"), (2, "X"), (3, "X")], -1),
        ([(0, "Y"), (1, "X"), (2, "X"), (3, "X")], -1),
        ([(0, "X"), (1, "Y"), (2, "Y"), (3, "Y")], +1),
        ([(0, "Y"), (1, "X"), (2, "Y"), (3, "Y")], +1),
        ([(0, "Y"), (1, "Y"), (2, "X"), (3, "Y")], +1),
        ([(0, "Y"), (1, "Y"), (2, "Y"), (3, "X")], -1),
    ]

    for pauli_ops, sign in terms:
        pauli_evolution(c, pauli_ops, sign * theta / 8)

    # Step 3: Measure all qubits
    c.measure_z(0).measure_z(1).measure_z(2).measure_z(3)

    return c


if __name__ == "__main__":
    # UCCSD amplitude for H2 at equilibrium bond length (~0.735 A)
    # This value is close to the optimal from classical CCSD
    theta = 0.2286

    circuit = build_h2_uccsd(theta)

    print(f"H2 UCCSD circuit: {circuit.num_qubits} qubits, {len(circuit.ops)} gates")
    print(f"Double excitation amplitude: theta = {theta}")
    print()

    # Run on WuYue cloud
    results = circuit.run(
        provider="qcos",
        device="WuYue-QPUSim-FullAmpSim",
        shots=1000,
        access_key="eb8c13826141446a92697e1bb3129b39",
        secret_key="1fc9f716d75a445ab079d3cbcb3ab9ec",
        sdk_code="NBQaBwDVuyI5mCGr+RFeHfP9PcuRYeBl",
        timeout=100,
        calculate_type=1,
        wait_async_result=True,
    )

    counts = results[0]["result"]
    print("Measurement results:")
    for bitstring, count in sorted(counts.items(), key=lambda x: -int(x[1])):
        print(f"  |{bitstring}> : {count}")
