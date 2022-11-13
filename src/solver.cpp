#include "solver.h"
#include "cha.h"
#include "stockfish.h"

// Perform a cooperative search of depth [n] looking for a checkmate
// or a dead draw (depending on the template parameter).
//
// Print in UCI format a line for each solution found
// (Lines which include transpositions are printed only once.)
// Return the total number of solutions of length exactly [n].
template <SOLVER::Goal GOAL>
int cooperative_search(Position &pos, Depth n, UTIL::Search &search) {

  int nb_legal_moves = MoveList<LEGAL>(pos).size();
  bool zero_moves = nb_legal_moves == 0;
  bool checkmate = zero_moves && pos.checkers();
  bool stalemate = zero_moves && !pos.checkers();
  bool dead = CHA::is_dead(pos);

  bool goal_completed =
    (GOAL == SOLVER::MATE && checkmate) ||
    (GOAL == SOLVER::DRAW && dead) ||
    (GOAL == SOLVER::DEAD && dead && !stalemate);

  if (search.progress_bar() && (search.search_depth() <= 2 || n >= 4))
    std::cout << "progress level " << search.search_depth()
              << " next " << nb_legal_moves << std::endl;

  if (goal_completed && n % 2 == 0) {
    search.print_solution(dead, stalemate, false);
    return 1;
  }

  if (n <= 0 || zero_moves || dead)
    return 0;

  // To store an entry from the transposition table (TT)
  TTEntry *tte = nullptr;
  bool found;
  StateInfo st;

  tte = TT.probe(pos.key(), found);

  if (found && tte->depth() >= n)
    return tte->depth() == n ? tte->eval() : 0;

  int cnt = 0;

  // Iterate over all legal moves
  for (const ExtMove &m : MoveList<LEGAL>(pos)) {
    pos.do_move(m, st);
    search.push(m);
    cnt += cooperative_search<GOAL>(pos, n - 1, search);
    search.pop();
    pos.undo_move(m);
  }

  tte->save(pos.key(), VALUE_NONE, false, BOUND_NONE, n, MOVE_NONE, (Value)cnt);
  return cnt;
}

template <SOLVER::Goal GOAL>
int competitive_search(Position &pos, Depth n, UTIL::Search &search) {

  int nb_legal_moves = MoveList<LEGAL>(pos).size();
  bool zero_moves = nb_legal_moves == 0;
  bool checkmate = zero_moves && pos.checkers();
  bool stalemate = zero_moves && !pos.checkers();
  bool dead = CHA::is_dead(pos);

  bool goal_completed =
    (GOAL == SOLVER::MATE && checkmate) ||
    (GOAL == SOLVER::DRAW && dead) ||
    (GOAL == SOLVER::DEAD && dead && !stalemate);

  if (search.progress_bar() && (search.search_depth() <= 2 || n >= 4))
    std::cout << "progress level " << search.search_depth()
              << " next " << nb_legal_moves << std::endl;

  if (goal_completed && n % 2 == 0) {
      // search.print_solution(dead, stalemate);
      return 1;
  }

  if (n <= 0 || zero_moves || dead)
    return 0;

  // To store an entry from the transposition table (TT)
  TTEntry *tte = nullptr;
  bool found;
  StateInfo st;
  tte = TT.probe(pos.key(), found);

  if (found && tte->depth() >= n)
    return tte->depth() == n ? tte->eval() : 0;

  int cnt = 0;

  // If search depth is even (the intended winner's turn) collect all solutions
  if (search.search_depth() % 2 == 0) {
    for (const ExtMove &m : MoveList<LEGAL>(pos)) {
      pos.do_move(m, st);
      search.push(m);
      int nb_sols = competitive_search<GOAL>(pos, n - 1, search);
      if (nb_sols > 0 && search.search_depth() == 1) {
        bool partial = (n != 1);
        search.print_solution(dead, stalemate, partial);
      }
      cnt += nb_sols;
      search.pop();
      pos.undo_move(m);
    }
  }
  // Otherwise (the intended loser's turn) keep the branch with fewer solutions
  else {
    int min = -1;
    for (const ExtMove &m : MoveList<LEGAL>(pos)) {
      pos.do_move(m, st);
      search.push(m);
      cnt = competitive_search<GOAL>(pos, n - 1, search);
      search.pop();
      pos.undo_move(m);
      if (min < 0 || cnt < min)
        min = cnt;
    }
    cnt = min;
  }

  tte->save(pos.key(), VALUE_NONE, false, BOUND_NONE, n, MOVE_NONE, (Value)cnt);
  return cnt;
};

int SOLVER::help_mate(Position &pos, Depth n, UTIL::Search &search) {
  TT.clear();
  int sol = cooperative_search<MATE>(pos, n, search);
  return sol;
};

int SOLVER::help_draw(Position &pos, Depth n, UTIL::Search &search) {
  TT.clear();
  return cooperative_search<DRAW>(pos, n, search);
};

int SOLVER::help_dead(Position &pos, Depth n, UTIL::Search &search) {
  TT.clear();
  return cooperative_search<DEAD>(pos, n, search);
};

int SOLVER::force_mate(Position &pos, Depth n, UTIL::Search &search) {
  TT.clear();
  return competitive_search<MATE>(pos, n, search);
};

int SOLVER::force_draw(Position &pos, Depth n, UTIL::Search &search) {
  TT.clear();
  return competitive_search<DRAW>(pos, n, search);
};

int SOLVER::force_dead(Position &pos, Depth n, UTIL::Search &search) {
  TT.clear();
  return competitive_search<DEAD>(pos, n, search);
};
