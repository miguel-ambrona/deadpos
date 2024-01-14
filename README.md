# Deadpos Analyzer 2

[![C/C++ CI](https://github.com/miguel-ambrona/deadpos/actions/workflows/c-cpp.yml/badge.svg?branch=master)](https://github.com/miguel-ambrona/deadpos/actions/workflows/c-cpp.yml)

Tool for designing, analyzing and solving chess compositions based on
dead reckoning.

## Installation

Make sure you have `curl`, `opam` and `python-chess`, which you can
install with:
  - `sudo apt install curl`
  - `sudo apt install opam && opam init -y`
  - `pip3 install python-chess`.

Then, after cloning the repository and from the `src/` directory:

1. Run `make get-stockfish` to download and compile
   [Stockfish](https://github.com/official-stockfish/Stockfish).
   Then install Stockfish with `sudo make install-stockfish`.

2. Run `make get-cha` to download and compile
   [CHA](https://github.com/miguel-ambrona/D3-Chess).
   Then install CHA with `sudo make install-cha`.

3. Run `make get-retractor` to download and build our retraction engine.

4. Compile the tool with `make`. (You may need to enable shared libraries
   with `sudo /sbin/ldconfig -v` first.)

5. Make sure everything worked fine by running `make test`.

## Usage

After completing the installation steps, run the tool with
`python3 deadpos.py` from the `src/` directory.
This will start a process which waits for queries from stdin.
A query must be a valid
[FEN](https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation),
followed by a list of commands separated by `>>=`.
(Input lines starting with `//` are ignored.)

The following commands are supported. They are all functions applied
to a position, which return a list of objects (typically, positions).
 - `retract` (or `r` for short): retracts a move.

 - `move` (or `m` for short): performs as forward move.

 - `legal`: analyzes the legality of the position and its history.
   This may label the position as:
     - *illegal* (FIDE illegal), when the position is unreachable from
        the starting position via a sequence of legal moves (that is,
        not considering FIDE Article 5.2.2 about "dead positions").
     - *zombie*, when it is FIDE legal, but all possible legal retractions
        are from dead positions.
     - No label on if FIDE legal and non-zombie.

   This command also analyzes whether a position is alive/dead when the
   position is the result of a retraction or it is part of a longer sequence
   of moves, possibly labeling the position as "dead".

 - `DP` : labels the position as "DP" (dead position) or "alive".

 - `flip`: flips the turn. This also resets the halfmove clock,
    and the en-passant flags to `?` (but preserves castling rights).
    The position(s) after a flip become the "game array", i.e., they
    are legal by default.

 - `turn`: returns the turn of the given position.

 - `castling` : returns the castling rights of the given position.

 - `ep` : returns the en-passant privileges of the given position.

 - A solve command. The following solve commands are supported:
     - `#[0-9]+[.5]?`: *forced mate* in the given number of moves.
     - `h#[0-9]+[.5]?`: *help mate* in the given number of moves.
     - `h=[0-9]+[.5]?`: *help stalemate* in the given number of moves.
     - `hdp[0-9]+[.5]?`: *help dead position* in the given number of moves.
     - `h~=[0-9]+[.5]?`: *help draw* (stalemate or dead) in the given number of
        moves.

   This transforms the position into the final position of every solution.
   (The monadic chain `>>=` may continue from those.)

   A solve command can be succeded (after a blank space) with a piece type in
   round brackets (to choose from `p`, `n`, `b`, `r`, `q`, `k`).
   This will constrain the last move to have been performed by a piece of the
   indicated type.

   On every query, the tool will produce one line output per solution found.
   If there exist shorter solutions that make the composition unsound, the tool
   is guaranteed to display at least one (but not all).

For example:
```
// Julio Sunyer, 1923 (The Chess Amateur)
>>> 4k3/8/8/7K/8/8/8/8 b - - >>= r >>= r >>= h#1
↶g6xRh5 ↶h8xQh5 e8g8 h5h7# 5rk1/8/6K1/7Q/8/8/8/8 w - - 1 2
nsols 1

// Andrew Buchanan, 2001 (1 Retros mailing list 24th Jan)
>>> k7/8/2K5/8/8/8/8/8 ? >>= legal >>= turn
b
nsols 1
```

## Further details

- Our routine considers all possible retractions leading to
  well-formed positions (exactly one king per side, no pawns on 1st or 8th rank,
  etc) even if they are illegal.
  Furthermore, in virtue of FIDE Article 5.2.2, all positions preceeding a
  *dead* position should be *alive*.
  Our retractor still displays those that are dead, but it labels them if
  the command `legal` is used.

- We perform minimal legality checks on a position, by checking whether it
  admits at least a retraction.
  This means at the moment our legality analysis is a semi-decision procedure.
  If a position is labeled as "illegal", it is definitely illegal.
  However, non-labeled positions could be legal and escape our current logic.
  *We are working on making this legality check more complete*.

- Even though we display illegal and dead (retracted from dead) positions,
  they do not carry on to the next command. For example, 6 possible well-formed
  retractions are shown after the following command:
  ```
  >>> 8/8/8/8/2Q5/k7/1pP5/K7 w - - >>= r >>= legal
  ↶b3b2 8/8/8/8/2Q5/kp6/2P5/K7 b - - ? 0
  ↶c3xPb2 illegal dead 8/8/8/8/2Q5/k1p5/1PP5/K7 b - - ? 0
  ↶c3xQb2 dead 8/8/8/8/2Q5/k1p5/1QP5/K7 b - - ? 0
  ↶c3xRb2 dead 8/8/8/8/2Q5/k1p5/1RP5/K7 b - - ? 0
  ↶c3xBb2 dead 8/8/8/8/2Q5/k1p5/1BP5/K7 b - - ? 0
  ↶c3xNb2 dead 8/8/8/8/2Q5/k1p5/1NP5/K7 b - - ? 0
  nsols 1
  ```
  However, 5 of them were labeled as either illegal or dead.
  If we then apply another command, e.g. `>>= h=1.5`, these 5 will not be
  considered in the analysis, only the very first one
  `8/8/8/8/2Q5/kp6/2P5/K7 b - - ? 0`.

- In case our dead position subroutine fails to determine whether a position
  is *dead*, the following error message will be raised:
  ```
  >>> B2b4/8/4k3/8/1p1p1p1p/1PpP1P1P/K1P4b/RB6 b - - 0 1 >>= DP
  RuntimeError: CHA failed on B2b4/8/4k3/8/1p1p1p1p/1PpP1P1P/K1P4b/RB6 b - - 0 1
  ```
  In a successful execution, every computation regarding dead positions is
  *sound* in the sense that the tool either finds a helpmate (proving the
  position is alive) or definitely proves that the position is dead.

- FEN tokens can be unspecified with `?`, in which case, the tool will consider
  all plausible values of that token. For example, the following considers that
  the en-passant flag takes values `-` or `g6`.
  ```
  >>> 6br/4Bp1k/5P2/5PpK/4B1P1/8/8/8 w - ? ? 100
  6br/4Bp1k/5P2/5PpK/4B1P1/8/8/8 w - - ? 100
  6br/4Bp1k/5P2/5PpK/4B1P1/8/8/8 w - g6 ? 100
  nsols 2
  ```

- Not all 6 FEN tokens are necessary. If fewer tokens are specified, the
  remaining will be filled with `?`.

- When the halfmove clock is specified, it will be considered in the computation
  of retractions. That is, if it is specified to be `0`, the last move must have
  been a capture or a pawn move. Analogously, when it is strictly positive, all
  retractions will be officer non-captures.
  For example:
  ```
  >>> k7/8/2K5/8/8/8/8/8 b - - 0 50 >>= r >>= legal
  ↶d7xPc6 k7/3K4/2p5/8/8/8/8/8 w - - ? 50
  ↶d7xQc6 k7/3K4/2q5/8/8/8/8/8 w - - ? 50
  ↶d7xRc6 k7/3K4/2r5/8/8/8/8/8 w - - ? 50
  ...
  nsols 21
  ```
  but
  ```
  >>> k7/8/2K5/8/8/8/8/8 b - - 1 50 >>= r >>= legal
  ↶d7c6 dead k7/3K4/8/8/8/8/8/8 w - - 0 50
  ↶d5c6 dead k7/8/8/3K4/8/8/8/8 w - - 0 50
  ↶b5c6 dead k7/8/8/1K6/8/8/8/8 w - - 0 50
  ↶c7c6 zombie k7/2K5/8/8/8/8/8/8 w - - 0 50
  ↶c5c6 dead k7/8/8/2K5/8/8/8/8 w - - 0 50
  ↶d6c6 dead k7/8/3K4/8/8/8/8/8 w - - 0 50
  ↶b6c6 zombie k7/8/1K6/8/8/8/8/8 w - - 0 50
  nsols 0
  ```

- The convention on solve commands is that White should make the last move.
  Thus, one of the two players is expected to perform the first move.
  For example, Black is expected to make the first move on `h#3`.
  Positions whose turn does not match the expected turn are discarded without
  further analysis. However, the expected turn can be flipped by including the
  term `half-duplex` next to the specification. For example:
  ```
  >>> 8/8/2B5/5Q2/8/4p2P/4k2K/8 w - - >>= h#3 half-duplex
  f5b1 e2f2 c6h1 e3e2 b1f1 e2f1n# 8/8/8/8/8/7P/4pk1K/5Q1B b - - 1 3
  nsols 1
  ```
  Furthermore, if the term `duplex` is specified, both WTM and BTM positions
  will be considered.

- For the impatient folk, you can run Deadpos with flag `--fast` to
  significantly speed-up the analysis of dead positions. This means the analysis
  may miss some complicated dead positions and there is no way to know about it.
  Use this flag if you want to find cooks (if they exist, they will probably
  be found with this method) or you are designing a problem. However, in order
  to mark a problem as C+ (computer tested) you should run the program without
  this flag.

- You can disable the progress bar with `--no-progress-bar`.


## Feedback

Please, open an issue if you have any suggestions.

Enjoy!
