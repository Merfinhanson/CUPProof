# CUPProof MCP Server

An MCP server that lets an AI agent run a **range proof**: prove that a hidden number lies between two limits, without revealing the number.

It is inspired by **Cuproof**, the constant-size zero-knowledge range proof used inside the BAZKP biometric authentication scheme (PLOS ONE, article `pone.0286215`).

> **Honest status: educational demo, not production crypto.**
> The proof currently includes the six "square" numbers it is built from, so it is **not** zero-knowledge yet. It shows the correct flow (lock, prove, verify, reject cheaters), but it should not be used to protect real data.

## The idea in plain words

1. You lock a secret number in a sealed envelope (a *commitment*). Nobody can look inside it.
2. You build a proof that the number inside is between `low` and `high`.
3. A checker verifies the proof using only the envelope, the proof and the range. It never needs the secret.

The range check uses a classic trick: a number of the form `4x + 1` is a sum of three squares exactly when `x` is not negative. Squares are never negative, so showing the right squares proves `v` is not below `low` and not above `high`.

## The tools

| Tool | What it does |
| --- | --- |
| `commit(value)` | Locks a non-negative secret number in an envelope. The secret stays inside the server and is never returned. |
| `prove_range(commitment, low, high)` | Builds a proof that the number inside the envelope is within `[low, high]`. Refuses if it is not. |
| `verify_range(commitment, proof, low, high)` | Checks a proof. Returns `valid` true or false with a reason. |
| `demo_run(value, low, high)` | Runs the whole flow in one go, plus two cheating attempts, and shows every result together. |

## Setup

You need [uv](https://docs.astral.sh/uv/) installed. Then, in this folder:

```bash
uv sync
```

(`uv` downloads the right Python version automatically if you do not have it.)

## Try it in the MCP Inspector

```bash
uv run mcp dev server.py
```

Open the link it prints, switch the server to **Connected**, and use the **Tools** tab.

Tip: commitments live in the server's memory, so they disappear when the server restarts. Run `commit` again after any restart.

## Use it with an AI agent in VS Code

1. Open `.vscode/mcp.json` and change the path `D:\\mcp-server-demo` to the folder where this project lives on your computer.
2. Open the Chat panel in **Agent** mode and send a message such as:
   *"Use the cupproof tools to lock the number 4, prove it is between 0 and 10, then verify the proof, and explain what happened."*

## Known limitations

- The proof is not zero-knowledge yet (see the note at the top).
- Commitments are kept in memory only, and are lost on restart.
- The setup numbers are generated when the server starts, so each run uses fresh parameters.
