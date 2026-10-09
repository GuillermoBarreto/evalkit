# evalkit

A tiny YAML-driven eval harness for LLM prompts and agents. Write your expected behaviors as a YAML suite, run them against a provider, and get a pass/fail report — the same regression-test habit you already have for code, applied to prompts.

## Why

Prompts drift. A small wording tweak, a model swap, or a new system prompt can silently change what your app says. evalkit gives you cheap, repeatable prompt regression tests: deterministic judges (exact, contains, regex), offline fixtures for CI, and a real API provider when you want live runs.

## Install

```bash
pip install -e ".[dev]"
```

Requires Python 3.10+.

## Usage

1. Write a suite (`suite.yaml`):

```yaml
- name: greets-by-name
  prompt: "Greet Ada warmly in one sentence."
  expected: "Ada"
  judge: contains

- name: exact-format
  prompt: "Reply with exactly: OK"
  expected: "OK"
  judge: exact

- name: numeric-answer
  prompt: "Answer with a number between 1 and 10."
  expected: "^\\d+$"
  judge: regex
```

2. Run it offline against canned fixtures (great for CI):

```bash
evalkit run suite.yaml --provider dict --fixtures fixtures.json --report report.json
```

`fixtures.json` is a prompt → output mapping:

```json
{
  "Greet Ada warmly in one sentence.": "Hello, Ada! Great to see you."
}
```

3. Run it live against any OpenAI-compatible API (key via environment variable):

```bash
export EVALKIT_API_KEY=your-key-here
evalkit run suite.yaml --provider openai-compatible --model gpt-4o-mini
```

The exit code is `0` when every case passes and `1` otherwise, so it plugs straight into CI.

Try the bundled example with no setup:

```bash
evalkit run examples/evals.yaml --provider dict --fixtures examples/fixtures.json
```

Lint a suite without spending any model calls — duplicate names, empty
`expected` values that always pass, and unknown judges:

```bash
evalkit validate suite.yaml
evalkit validate suite.yaml --strict   # exit 1 on warnings, for CI
```

Compare two runs to catch regressions after a model swap, prompt tweak, or
dependency upgrade:

```bash
evalkit run suite.yaml --provider dict --fixtures fixtures.json --report new.json
evalkit diff old.json new.json
```

`diff` prints which cases regressed (passed → failed), which got fixed,
and any added or removed cases, plus the pass-rate delta. It exits `1`
when there are regressions and `0` otherwise, so it works as a CI gate —
save the report from your last known-good run as the baseline.

Reports written with `--report` include a per-judge breakdown (`by_judge`)
in the summary, so you can see which judge type is failing most.

## Roadmap

- [x] Suite linting via `evalkit validate`
- [x] Run diffing: compare two reports to catch regressions (`evalkit diff`)
- Retries with backoff and per-case timeouts
- JSONL datasets and dataset transforms
- LLM-as-judge providers
- Parallel case execution and cost/latency tracking
