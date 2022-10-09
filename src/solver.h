#include "stockfish.h"
#include "util.h"

#ifndef SOLVER_H_INCLUDED
#define SOLVER_H_INCLUDED

namespace SOLVER {

enum Goal { MATE, DRAW, DEAD };

int help_mate(Position &pos, Depth n, UTIL::Search &search);

int help_draw(Position &pos, Depth n, UTIL::Search &search);

int help_dead(Position &pos, Depth n, UTIL::Search &search);

int force_mate(Position &pos, Depth n, UTIL::Search &search);

int force_draw(Position &pos, Depth n, UTIL::Search &search);

int force_dead(Position &pos, Depth n, UTIL::Search &search);

} // namespace SOLVER

#endif // #ifndef SOLVER_H_INCLUDED
