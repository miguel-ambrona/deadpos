#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
import chess
import sys
import os

CHA = Popen(["../lib/cha/D3-Chess/src/cha"], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
CHA.stdout.readline()

RETRACT_TABLE = {}
SHERLOCK_TABLE = {}
DEAD_TABLE = {}
LEGAL_TABLE = {}
ZOMBIE_TABLE = {}

SHERLOCK = Popen(["../lib/sherlock/_build/default/retractor/retractor.exe"], \
                  stdout=PIPE, stdin=PIPE, stderr=STDOUT)

NODES = 0

def retract(fen):
    '''
    Returns a fen of all possible pseudo-legal retractions of the
    given position.
    '''
    global SHERLOCk
    global RETRACT_TABLE

    retracted = RETRACT_TABLE.get(fen)
    if retracted != None:
        return retracted

    inp = ("retract " + fen + "\n").encode("utf-8")
    SHERLOCK.stdin.write(inp)
    SHERLOCK.stdin.flush()
    fens = []
    while True:
        output = SHERLOCK.stdout.readline().strip().decode("utf-8")
        if "nsols" in output or len(output) <= 1:
            break
        retracted_fen, retraction = output.split('retraction')
        fens.append((retracted_fen.strip(), retraction.strip()))

    RETRACT_TABLE[fen] = fens

    return fens

def is_illegal_sherlock(fen):
    '''
    Returns True if the position is illegal and False if Sherlock cannot
    determine the illegality of the position.
    '''
    global SHERLOCK
    global SHERLOCK_TABLE

    found = SHERLOCK_TABLE.get(fen)
    if found != None:
        return found

    inp = ("legal " + fen + "\n").encode("utf-8")
    SHERLOCK.stdin.write(inp)
    SHERLOCK.stdin.flush()
    illegal = False
    reason = ""
    while True:
        output = SHERLOCK.stdout.readline().strip().decode("utf-8")
        if "nsols" in output or len(output) <= 1:
            break
        illegal = illegal or "illegal" in output
        if "illegal"in output:
            reason += " ".join(output.split(" ")[1:]).strip()

    SHERLOCK_TABLE[fen] = (illegal, reason)

    return (illegal, reason)

def is_dead(fen):
    '''
    Returns true iff the given position is dead.
    Fails if the liveness of the position cannot be determined.
    '''
    global CHA
    global DEAD_TABLE

    key = " ".join(fen.split(" ")[:4])
    dead = DEAD_TABLE.get(key)
    if dead != None:
        return dead

    inp = (fen + " white\n").encode("utf-8")
    try:
      CHA.stdin.write(inp)
      CHA.stdin.flush()
    except:
        CHA = Popen(["../lib/cha/D3-Chess/src/cha"], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        CHA.stdout.readline()
        return is_dead(fen)

    output = CHA.stdout.readline().strip().decode("utf-8")
    white_undetermined = "undetermined" in output

    if "unwinnable" not in output and not white_undetermined:
        DEAD_TABLE[key] = False
        return False

    inp = (fen + " black\n").encode("utf-8")
    CHA.stdin.write(inp)
    CHA.stdin.flush()
    output = CHA.stdout.readline().strip().decode("utf-8")
    black_undetermined = "undetermined" in output

    if "unwinnable" not in output and not black_undetermined:
        DEAD_TABLE[key] = False
        return False

    if white_undetermined or black_undetermined:
        raise RuntimeError("CHA failed on " + fen)

    dead = "unwinnable" in output
    DEAD_TABLE[key] = dead
    return dead

def is_legal(fen, depth = 1):
    '''
    Returns true iff the given position admits a retraction of the given depth.
    This is not a complete method for legality, but it is sound in the sense
    that an output of False is always correct.
    '''

    global LEGAL_TABLE

    key = " ".join(fen.split(" ")[:5]) + " " + str(depth)
    legal = LEGAL_TABLE.get(key)
    if legal != None:
        return legal

    if depth <= 0:
        return True
    if not chess.Board(fen.replace("?", "0")).is_valid():
        return False
    for (retracted_fen, retraction) in retract(fen):
        if is_legal(retracted_fen, depth - 1):
            LEGAL_TABLE[key] = True
            return True
    LEGAL_TABLE[key] = False
    return False

def is_zombie(fen, depth = 1):
    '''
    Returns true iff the given position is zombie. Namely, it is legal, but all
    its possible retractions lead to a dead position.
    '''

    global ZOMBIE_TABLE

    key = " ".join(fen.split(" ")[:5]) + " " + str(depth)
    zombie = ZOMBIE_TABLE.get(key)
    if zombie != None:
        return zombie

    if not is_legal(fen, depth):
        return False

    for (retracted_fen, retraction) in retract(fen):
        if not is_dead(retracted_fen) and is_legal(retracted_fen, depth - 1):
            ZOMBIE_TABLE[key] = False
            return False
    ZOMBIE_TABLE[key] = True
    return True

def explain_dead(board, depth = 10):
    global NODES

    UCI_NOTATION = "--uci" in sys.argv
    INTERRUPTED_MSG = "explanation interrupted for being too long"

    if depth == 10:
        NODES = 0

    if board.is_stalemate():
        return "="

    elif board.is_insufficient_material():
        return " insufficient material"

    elif depth <= 0 or NODES > 30:
        return " " + INTERRUPTED_MSG

    assert is_dead(board.fen())

    legal_moves = [m for m in board.legal_moves]

    m = legal_moves[0]
    explanation = str(m) if UCI_NOTATION else board.lan(m)
    board.push(m)
    rest_m1_explanation = explain_dead(board, depth - 1)
    if rest_m1_explanation == "=":
        explanation += "="
    board.pop()

    for m in legal_moves[1:]:
        NODES += 1
        m_str = str(m) if UCI_NOTATION else board.lan(m)
        board.push(m)
        explanation_after_m = explain_dead(board, depth - 1)
        token = " " if explanation_after_m != "=" else ""
        explanation += " (" + m_str + token + explanation_after_m + ")"
        board.pop()

    if rest_m1_explanation != "=":
        token = ""
        if rest_m1_explanation[0] != " ":
            token = " "
        explanation += token + rest_m1_explanation

    if len(explanation) > 100:
        return INTERRUPTED_MSG

    return explanation

def explain_alive(fen, depth = 10):
    UCI_NOTATION = "--uci" in sys.argv

    inp = (fen + " white\n").encode("utf-8")
    CHA.stdin.write(inp)
    CHA.stdin.flush()
    output = CHA.stdout.readline().strip().decode("utf-8")

    mate_with_white = None
    mate_with_black = None

    if "unwinnable" not in output:
        mate_with_white = output.replace("winnable", "living alternative").split("#")[0] + "#"

    inp = (fen + " black\n").encode("utf-8")
    CHA.stdin.write(inp)
    CHA.stdin.flush()
    output = CHA.stdout.readline().strip().decode("utf-8")

    if "unwinnable" not in output:
        mate_with_black = output.replace("winnable", "living alternative").split("#")[0] + "#"

    len_white = 0 if not mate_with_white else len(mate_with_white)
    len_black = 0 if not mate_with_black else len(mate_with_black)

    if 0 < len_white < len_black or len_black == 0:
        line = mate_with_white

    else:
        line = mate_with_black

    if UCI_NOTATION:
        return line

    else:
        output = ["living alternative"]
        board = chess.Board(fen)
        for m in line.split(" ")[2:]:
            m = m.replace("#", "")
            output.append(board.lan(board.parse_uci(m)))
            board.push_uci(m)
        return " ".join(output)


(STALEMATE, DEAD, DRAW) = (0, 1, 2)

def key_fen(fen):
    return " ".join(fen.split(" ")[:4])

def cooperative_search(progress_bar, use_tt, goal, board, n, solution, Table):
    depth = len(solution)
    stalemate = board.is_stalemate()
    legal_moves = [m for m in board.legal_moves]

    goal_completed = False
    if n % 2 == 0:
        if goal == STALEMATE:
            goal_completed = stalemate
        else:
            dead = is_dead(board.fen())
            goal_completed = (goal == DRAW and (dead or stalemate)) or \
                (goal == DEAD and dead and not stalemate)

    if progress_bar and (depth <= 2 or n >= 1):
        print("progress level", depth, "next", len(legal_moves))

    if goal_completed:
        token = "stalemate" if stalemate else ("DP" if dead else "???")
        cook = "cook?" if n > 0 else ""
        print("solution", " ".join([str(m) for m in solution]), token, cook)
        return 1

    if n <= 0 or len(legal_moves) == 0:
        return 0

    if use_tt:
        fen_id = key_fen(board.fen())
        entry = Table.get(fen_id)
        if (entry != None and entry[0] >= n):
            return (0 if entry[0] != n else entry[1])

    cnt = 0

    for m in legal_moves:
        board.push(m)
        cnt += cooperative_search(progress_bar, use_tt, goal, board, n - 1, solution[:] + [m], Table)
        board.pop()

    if use_tt:
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

        pbar = "--progress-bar" in sys.argv
        use_tt = not "--show-all" in sys.argv
        nsols = cooperative_search(pbar, use_tt, goal, board, n, [], {})
        print("nsols", nsols)
