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

## Usage

After compiling the tool, run `./deadpos` to start a process which waits for
commands from stdin. A command must be a valid stipulation followed by a valid
[FEN](https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation).

On every query, the tool will produce one line output per solution found.
If there exist shorter solutions that make the composition unsound, the tool
is guaranteed to display at least one (but not all).

The stipulation must follow this format `[h]?[#|=|dp][0-9]+[.5]?`,
e.g. `#5` stipulates *mate* in five moves or `hdp3.5` stipulates
*help dead position* in three and a half moves.

For example:

> **./deadpos**<br>
> Deadpos Analyzer version 1.0<br>
> **h#2 1RrB2b1/8/4n3/2n3p1/2K2b2/1p1rk3/6BR/8 b - -**<br>
> solution f4b8 g2d5 e6c7 d8g5#<br>
> solution d3d8 g2c6 c5d7 b8b3#<br>
> nsols 2<br>
> time 1207 ms<br>
> **hdp3.5 b4b2/1P1PP3/8/k7/6K1/8/6PP/8 w - - 0 1**<br>
> solution b7b8b a8g2 h2h3 g2h3 g4h3 f8e7 d7d8b DP<br>
> nsols 1<br>
> time 182450 ms<br>

Enjoy!