# Deadpos Analyzer

[![C/C++ CI](https://github.com/miguel-ambrona/deadpos/actions/workflows/c-cpp.yml/badge.svg?branch=master)](https://github.com/miguel-ambrona/deadpos/actions/workflows/c-cpp.yml)

Tool for designing, analyzing and solving chess compositions based on
dead reckoning.

## Installation

After cloning the repository and from the `src/` directory:

1. Run `make get-stockfish` to download and compile
[Stockfish](https://github.com/official-stockfish/Stockfish).
Then install Stockfish with `make install-stockfish`.

2. Run `make get-cha` to download and compile
[CHA](https://github.com/miguel-ambrona/D3-Chess).
Then install CHA with `make install-cha`.

3. Compile the tool with `make`.

4. Run the tests with `make test`.

