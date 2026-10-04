import secrets
from math import isqrt

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("CUPProof")


# =====================================================================
# PART 1: SETUP. Makes the big public numbers n, g, h.
# Just paste this, no need to understand it yet.
# =====================================================================
def _is_prime(x, rounds=25):
    if x < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29):
        if x % p == 0:
            return x == p
    d, s = x - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        a = 2 + secrets.randbelow(x - 3)
        y = pow(a, d, x)
        if y in (1, x - 1):
            continue
        for _ in range(s - 1):
            y = pow(y, 2, x)
            if y == x - 1:
                break
        else:
            return False
    return True


def _random_prime(bits):
    while True:
        c = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if _is_prime(c):
            return c


n = _random_prime(256) * _random_prime(256)       # public
g = pow(2 + secrets.randbelow(n - 3), 2, n)        # public
h = pow(2 + secrets.randbelow(n - 3), 2, n)        # public

# The server's private notebook: envelope -> (secret value, random r).
# The AI never sees what is inside.
_vault = {}


# =====================================================================
# PART 2: HELPER. Finds three numbers whose squares add up to x.
# =====================================================================
def three_squares(x):
    """Find (a, b, c) with a*a + b*b + c*c == x, or None if impossible."""
    if x < 0:
        return None
    for a in range(isqrt(x) + 1):
        for b in range(a, isqrt(x) + 1):
            rest = x - a * a - b * b
            if rest < 0:
                break
            c = isqrt(rest)
            if c * c == rest and c >= b:
                return (a, b, c)
    return None


# =====================================================================
# PART 3: THE THREE BUTTONS
# =====================================================================
@mcp.tool()
def commit(value: int) -> dict:
    """Lock a secret non-negative number in a sealed envelope (a commitment).
    Use this FIRST. Returns the public envelope; the secret stays on the server."""
    if value < 0:
        return {"ok": False, "reason": "value must be 0 or more"}
    r = secrets.randbelow(n)
    envelope = (pow(g, value, n) * pow(h, r, n)) % n
    _vault[str(envelope)] = (value, r)
    return {"ok": True, "commitment": str(envelope)}


@mcp.tool()
def prove_range(commitment: str, low: int, high: int) -> dict:
    """Build a proof that the number inside a commitment is between low and high
    (inclusive). Call AFTER commit(), passing the commitment it returned.
    If the secret is outside the range, no proof can be built.
    EDUCATIONAL DEMO: this simplified proof is NOT zero-knowledge."""
    if commitment not in _vault:
        return {"ok": False, "reason": "unknown commitment, call commit() first"}
    v, r = _vault[commitment]

    v1 = 4 * v - 4 * low + 1     # can only be a sum of squares if v >= low
    v2 = 4 * high - 4 * v + 1    # can only be a sum of squares if v <= high
    squares1 = three_squares(v1)
    squares2 = three_squares(v2)
    if squares1 is None or squares2 is None:
        return {"ok": False, "reason": "secret is outside the range, cannot build a proof"}

    r1, r2 = 4 * r, -4 * r
    pieces = [*squares1, *squares2, r1, r2]
    return {
        "ok": True,
        "proof": ",".join(str(p) for p in pieces),
        "note": "Educational demo proof. It reveals the squares, so it is NOT zero-knowledge.",
    }


@mcp.tool()
def verify_range(commitment: str, proof: str, low: int, high: int) -> dict:
    """Check a range proof. Returns valid true/false and a reason.
    The checker only uses the public commitment, the proof and the claimed range."""
    try:
        u1, u2, u3, u4, u5, u6, r1, r2 = (int(p) for p in proof.split(","))
        V = int(commitment)

        # The guard builds two new envelopes by himself, without opening V:
        V1 = (pow(V, 4, n) * pow(g, 1 - 4 * low, n)) % n     # envelope of 4v - 4*low + 1
        V2 = (pow(g, 4 * high + 1, n) * pow(V, -4, n)) % n   # envelope of 4*high - 4v + 1

        # Do they really open to "sum of three squares"?
        s1 = u1 * u1 + u2 * u2 + u3 * u3
        s2 = u4 * u4 + u5 * u5 + u6 * u6
        ok1 = V1 == (pow(g, s1, n) * pow(h, r1, n)) % n
        ok2 = V2 == (pow(g, s2, n) * pow(h, r2, n)) % n
    except (ValueError, TypeError):
        return {"valid": False, "reason": "proof or commitment is malformed"}

    if ok1 and ok2:
        return {"valid": True, "reason": "the committed number is within [%d, %d]" % (low, high)}
    return {"valid": False, "reason": "proof does not match this commitment and range"}
# =====================================================================
# PART 4: ONE-CLICK DEMO. Runs the whole flow and shows everything at once.
# =====================================================================
@mcp.tool()
def demo_run(value: int, low: int, high: int) -> dict:
    """Run the whole flow in one go for demonstration: lock a secret value in an
    envelope, try to prove it is within [low, high], verify the proof, then try
    two cheating attempts. Shows every result together."""
    c = commit(value)
    if not c["ok"]:
        return c
    com = c["commitment"]
    p = prove_range(com, low, high)

    result = {
        "step1_envelope": com[:20] + "...(long number)",
        "step2_proof_built": p["ok"],
    }
    if not p["ok"]:
        result["why_not"] = p["reason"]
        return result

    proof = p["proof"]
    pieces = proof.split(",")
    result["step2_squares_in_proof"] = pieces[:6]
    result["step3_verify_honest"] = verify_range(com, proof, low, high)["valid"]

    # Cheat 1: claim a range that does NOT contain the secret
    result["cheat1_claim_smaller_range"] = verify_range(com, proof, low, value - 1)["valid"]

    # Cheat 2: change one number inside the proof
    pieces[0] = str(int(pieces[0]) + 1)
    result["cheat2_tampered_proof"] = verify_range(com, ",".join(pieces), low, high)["valid"]
    return result