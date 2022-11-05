#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
import chess
import sys
import os

CHA = Popen(["../lib/cha/D3-Chess/src/cha"], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
CHA.stdout.readline()

def is_dead(board):
    global CHA
    inp = (board.fen() + " white\n").encode("utf-8")
    CHA.stdin.write(inp)
    CHA.stdin.flush()
    output = CHA.stdout.readline().strip().decode("utf-8")
    white_undetermined = "undetermined" in output

    if "unwinnable" not in output and not white_undetermined:
        return False

    inp = (board.fen() + " black\n").encode("utf-8")
    CHA.stdin.write(inp)
    CHA.stdin.flush()
    output = CHA.stdout.readline().strip().decode("utf-8")
    black_undetermined = "undetermined" in output

    if "unwinnable" not in output and not black_undetermined:
        return False

    if white_undetermined or black_undetermined:
        raise RuntimeError("CHA failed on " + board.fen())

    return "unwinnable" in output

(STALEMATE, DEAD, DRAW) = (0, 1, 2)

def key_fen(fen):
    return " ".join(fen.split(" ")[:4])

def cooperative_search(progress_bar, goal, board, n, solution, Table):
    depth = len(solution)
    dead = is_dead(board)
    stalemate = board.is_stalemate()
    legal_moves = [m for m in board.legal_moves]
    goal_completed = (goal == DRAW and (dead or stalemate)) or \
        (goal == DEAD and dead and not stalemate) or \
        (goal == STALEMATE and stalemate)

    if progress_bar and (depth <= 2 or n >= 4):
        print("progress level", depth, "next", len(legal_moves))

    if goal_completed:
        token = "stalemate" if stalemate else ("DP" if dead else "???")
        cook = "cook?" if n > 0 else ""
        print("solution", " ".join([str(m) for m in solution]), token, cook)
        return 1

    if n <= 0 or len(legal_moves) == 0 or dead:
        return 0

    fen_id = key_fen(board.fen())
    entry = Table.get(fen_id)
    if (entry != None and entry[0] >= n):
        return (0 if entry[0] != n else entry[1])

    cnt = 0

    for m in legal_moves:
        board.push(m)
        cnt += cooperative_search(progress_bar, goal, board, n - 1, solution[:] + [m], Table)
        board.pop()

    Table[fen_id] = (n, cnt)

    return cnt

if __name__ == '__main__':
    print("Python3 help draw solver")
    while True:
        try:
            line = input()
        except EOFError:
            break

        words = line.split(" ")
        command = words[0]
        fen = " ".join(words[1:]).strip().replace("?", "0")
        board = chess.Board(fen)
        if command[:2] == "h=":
            (goal, n_str) = (STALEMATE, command[2:])

        elif command[:3] == "hdp":
            (goal, n_str) = (DEAD, command[3:])

        elif command[:3] == "h~=":
            (goal, n_str) = (DRAW, command[3:])

        n = int(2 * float(n_str))
        nsols = cooperative_search("--progress-bar" in sys.argv, goal, board, n, [], {})
        print("nsols", nsols)
