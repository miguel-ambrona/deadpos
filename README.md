# Deadpos Analyzer 2.0

[![C/C++ CI](https://github.com/miguel-ambrona/deadpos/actions/workflows/c-cpp.yml/badge.svg?branch=master)](https://github.com/miguel-ambrona/deadpos/actions/workflows/c-cpp.yml)

Tool for designing, analyzing and solving chess compositions based on
dead reckoning.

## Installation

After cloning the repository and from the `src/` directory:

1. Run `make get-stockfish` to download and compile
[Stockfish](https://github.com/official-stockfish/Stockfish).
Then install Stockfish with `sudo make install-stockfish`.

2. Run `make get-cha` to download and compile
[CHA](https://github.com/miguel-ambrona/D3-Chess).
Then install CHA with `sudo make install-cha`.

3. Run `make get-retractor` to download and build our retraction engine.

4. Compile the tool with `make`.

5. Make sure everything worked fine by running `make test`.

## Usage

After completing the installation steps, run the tool with
`python3 deadpos.py` from the `src/` directory.
This will start a process which waits for queries from stdin.
A query must be a valid
[FEN](https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation),
followed by a list of commands separated by `>>=`.
(Input lines starting with `//` are ignored.)

The following commands are supported:
 - `r[0-9]+`: retracts as many half moves as the integer indicates in all
    open goals.
    The retraction routine does not perform any legality checks on the
    retracted position (which may contain non-standard material or immaginary
    checks). However, if the given position is **dead**, all retracted positions
    will be **alive**.

 - `flip`: flips the turn of all open goals.

 - A solve command (which stops the potential `>>=` chain). The following solve
   commands are supported:
     - `#[0-9]+[.5]?`: *forced mate* in the given number of moves.
     - `h#[0-9]+[.5]?`: *help mate* in the given number of moves.
     - `h=[0-9]+[.5]?`: *help stalemate* in the given number of moves.
     - `hdp[0-9]+[.5]?`: *help dead position* in the given number of moves.
     - `h~=[0-9]+[.5]?`: *help draw* (stalemate or dead) in the given number of moves.

On every query, the tool will produce one line output per solution found.
If there exist shorter solutions that make the composition unsound, the tool
is guaranteed to display at least one (but not all).

For example:
```
// Mrs. W. J. Baird, 1907 (133 Twentieth Century Retractor)
>>> 1R6/1bNB2n1/pk2P3/pN2p2p/3pP2K/3P3p/5B1P/6n1 b - - >>= r1 >>= #2
e8c7 then b5d4 ... #
nsols 1
```
or
```
// Julio Sunyer, 1923 (The Chess Amateur)
>>> 4k3/8/8/7K/8/8/8/8 b - - >>= r2 >>= h#1
g6xRh5 h8xQh5 then e8g8 h5h7#
nsols 1
```

## Further details

- In case our dead position subroutine fails to determine whether a position
  is *dead*, the following error message will be raised:
  ```
  >>> B2b4/8/4k3/8/1p1p1p1p/1PpP1P1P/K1P4b/RB6 b - - 0 1 >>= hdp0
  RuntimeError: CHA failed on B2b4/8/4k3/8/1p1p1p1p/1PpP1P1P/K1P4b/RB6 b - - 0 1
  ```
  In a successful execution, every computation regarding dead positions is
  *sound* and *correct* in the sense that the tool either finds a helpmate
  (proving the position is alive) or definitely proves that the position is dead.

- FEN tokens can be unspecified with `?`, in which case, the tool will consider
  all plausible values of that token. For example, the following considers that
  the en-passant flag takes values `-` or `g6`.
  ```
  >>> 6br/4Bp1k/5P2/5PpK/4B1P1/8/8/8 w - ? ? 100 >>= r1
  6br/4Bppk/5P2/5P1K/4B1P1/8/8/8 b - - ? 99 g7g5
  nsols 1
  ```

- Not all 6 FEN tokens are necessary. If fewer tokens are specified, the
  remaining will be filled with `?`. For example:
  ```
  >>> 8/7Q/8/4BB2/2PP1P2/3NkN2/PP2P1P1/4K2R w >>= r1
  8/7Q/8/4BB2/2PPkP2/3N1N2/PP2P1P1/4K2R b K - ? 0 e4e3
  8/7Q/8/4BB2/2PPkP2/3NPN2/PP2P1P1/4K2R b K - ? 0 e4xPe3
  8/7Q/8/4BB2/2PPkP2/3NQN2/PP2P1P1/4K2R b K - ? 0 e4xQe3
  8/7Q/8/4BB2/2PPkP2/3NRN2/PP2P1P1/4K2R b K - ? 0 e4xRe3
  8/7Q/8/4BB2/2PPkP2/3NBN2/PP2P1P1/4K2R b K - ? 0 e4xBe3
  8/7Q/8/4BB2/2PPkP2/3NNN2/PP2P1P1/4K2R b K - ? 0 e4xNe3
  nsols 6
  ```

- When the halfmove clock is specified, it will be considered in the computation
  of retractions. That is, if it is specified to be `0`, the last move must have
  been a capture or a pawn move. Analogously, when it is strictly positive, all
  retractions will be officer non-captures.
  For example:
  ```
  >>> k7/8/2K5/8/8/8/8/8 b - - 0 50 >>= r1
  k7/3K4/2p5/8/8/8/8/8 w - - ? 50 d7xPc6
  k7/3K4/2q5/8/8/8/8/8 w - - ? 50 d7xQc6
  k7/3K4/2r5/8/8/8/8/8 w - - ? 50 d7xRc6
  ...
  k7/8/1Kr5/8/8/8/8/8 w - - ? 50 b6xRc6
  nsols 21
  ```
  but
  ```
  >>> k7/8/2K5/8/8/8/8/8 b - - 1 50 >>= r1
  nsols 0
  ```

- For impatients, you can run *Deadpos* with flag `--fast` to significtly
  speed-up the analysis of dead positions. This means the analysis may miss
  some complicated dead positions and there is no way to know about it.
  Use this flag if you want to find cooks (if they exist, they will probably
  be found anyway) or you are designing a problem, but in order to mark a
  problem as C+ (computer tested) you should run the program without this flag.

- You can disable the progress bar with `--no-progress-bar`.

## Feedback

Please, open an issue if you have any suggestions.

Enjoy!
