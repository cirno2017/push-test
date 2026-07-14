# Project instructions

## Scope

This directory is a general-purpose Python engineering environment for numerical
work, data analysis, embedded-system tooling, automation, and MCP development.
Keep changes focused on the user's current task. Do not add large or speculative
dependencies.

## Python environment

- Use Python 3.12.10 from the local virtual environment at `.venv`.
- On Windows PowerShell, prefer explicit environment-local commands so work does
  not depend on activation or the shell's current `PATH`:
  - `C:\codex_workspace\.venv\Scripts\python.exe ...`
  - `C:\codex_workspace\.venv\Scripts\pytest.exe ...`
  - `C:\codex_workspace\.venv\Scripts\ruff.exe check .`
  - `C:\codex_workspace\.venv\Scripts\ruff.exe format .`
  - `C:\codex_workspace\.venv\Scripts\mypy.exe ...`
- Activation is optional: `.\.venv\Scripts\Activate.ps1`.
- Never install project packages into the system Python or global user
  site-packages.
- Before installing a new dependency, check whether the standard library or an
  installed package already solves the task.
- This directory currently has a virtual environment but no `pyproject.toml` or
  uv lock file. For a one-off required dependency, install into `.venv` with
  `C:\codex_workspace\.venv\Scripts\python.exe -m pip install <package>`. If the user asks to turn
  this into a maintained project, initialize uv and then use `uv add <package>`
  or `uv add --dev <package>` so dependencies are declared and locked.
- After dependency changes, run
  `C:\codex_workspace\.venv\Scripts\python.exe -m pip check` and verify imports.

## Installed tools and libraries

Use the existing packages where appropriate:

- Numerical and symbolic work: NumPy, SciPy, SymPy, and mpmath.
- Data and plotting: pandas and Matplotlib.
- Embedded work: pyserial, Construct, crcmod, IntelHex, and pyelftools.
- CLI and models: Rich, Typer, and Pydantic.
- Tests and quality: pytest, Hypothesis, Ruff, and mypy.
- Environment and MCP tooling: uv and `mcp>=1,<2`.

Do not assume optional packages are installed. Packages such as `control`,
`filterpy`, `cantools`, `python-can`, `openpyxl`, `python-docx`, `pypdf`,
`pymupdf`, `opencv-python`, `fastapi`, and standalone `httpx` should be added
only when a concrete task requires them. Pillow, httpx, Uvicorn, and some other
libraries may already exist as transitive dependencies; do not treat that as a
decision to build against them without first declaring the direct dependency in
a maintained project.

Do not install TensorFlow, PyTorch, Transformers, LangChain,
`opencv-contrib-python`, Selenium, or Playwright merely because they might be
useful later.

## Mathematical work

- Use NumPy and SciPy for numerical computation, signal processing, integration,
  optimization, interpolation, and linear algebra.
- Use SymPy for lightweight symbolic manipulation and C/C++ code generation.
- Use a configured Wolfram MCP server for difficult symbolic work or independent
  verification when it is available; the installed Python `mcp` package alone
  does not imply that the Wolfram server is configured.
- Cross-check sensitive numerical or symbolic results with an independent
  method, boundary cases, or numerical sampling.

## Data analysis and visualization

- Use pandas for CSV logs, time-series alignment, cleanup, grouping, and summary
  statistics.
- Use Matplotlib for sensor traces, control responses, FFTs, and before/after
  comparisons.
- Preserve source data. Write generated outputs to clearly named files and do
  not overwrite the only copy of an input unless the user explicitly requests
  it.

## Embedded-system work

- Use pyserial for UART discovery, logging, and automated communication.
- Use Construct for binary packet definitions and parsing.
- Use crcmod for non-standard CRC variants; prefer `binascii` or `zlib` when the
  standard library already supports the required algorithm.
- Use IntelHex for Intel HEX address ranges, merging, and validation.
- Use pyelftools for ELF sections, symbols, DWARF data, and Flash/RAM analysis.
- Before accessing hardware, identify the intended port and communication
  settings. Do not flash firmware, erase devices, or send potentially destructive
  hardware commands unless the current task explicitly requires it.
- Always test protocol encoders/decoders, CRC functions, serialization,
  endianness, malformed frames, and boundary lengths.
- For protocol round trips, include property tests such as
  `decode(encode(value)) == value` where applicable.

## Code quality and verification

- Add or update tests for behavioral changes and bug fixes.
- Run the smallest relevant test set first, then the broader suite when one
  exists.
- Before handing off Python changes, normally run:
  1. `C:\codex_workspace\.venv\Scripts\pytest.exe`
  2. `C:\codex_workspace\.venv\Scripts\ruff.exe check .`
  3. `C:\codex_workspace\.venv\Scripts\mypy.exe <relevant paths>` when typed code exists
- Use `C:\codex_workspace\.venv\Scripts\ruff.exe format .` only when formatting is in scope; do
  not create unrelated formatting churn.
- Report commands that were not run, failures, unavailable hardware, and any
  assumptions that could affect the result.

## Secrets and generated files

- Load secrets from environment variables or a local `.env` file when needed.
- Never expose secrets in logs, source files, test fixtures, or responses.
- Do not commit `.env`, `.venv`, caches, build outputs, or generated plots unless
  the user explicitly requests those artifacts.


所有临时文件必须放入 ./tmp
所有编译输出必须放入 ./build
禁止修改 CubeMX 自动生成区域