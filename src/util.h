#ifndef UTIL_H_INCLUDED
#define UTIL_H_INCLUDED

namespace UTIL {

constexpr int MAX_VARIATION_LENGTH = 300;

class Search {
public:
  Search() = default;

  void init();

  Depth search_depth() const;

  void push(Move m);
  void pop();

  void print_solution(bool dead, bool stalemate, bool partial) const;

  bool progress_bar() const;
  void set_progress_bar(bool value);

  bool transposition_table() const;
  void set_transposition_table(bool value);

private:
  Move solution[MAX_VARIATION_LENGTH];
  Color winner;
  Depth depth;
  bool progressBar;
  bool transpositionTable;
};

inline void Search::init() { depth = 0; }

inline Depth Search::search_depth() const { return depth; }

inline void Search::push(Move m) {
  if (depth < MAX_VARIATION_LENGTH)
    solution[depth] = m;
  depth++;
}

inline void Search::pop() { depth--; }

inline void Search::print_solution(bool dead, bool stalemate, bool partial) const {
  std::cout << "solution";
  for (int i = 0; i < std::min(depth, MAX_VARIATION_LENGTH); i++)
    std::cout << " " << UCI::move(solution[i], false);
  if (partial)
    std::cout << " ... ";
  if (!dead)
    std::cout << "#";
  else if (stalemate)
    std::cout << " stalemate";
  else
    std::cout << " DP";
  std::cout << std::endl;
}

inline bool Search::progress_bar() const { return progressBar; }

inline void Search::set_progress_bar(bool value) {
  progressBar = value;
}

inline bool Search::transposition_table() const { return transpositionTable; }

inline void Search::set_transposition_table(bool value) {
  transpositionTable = value;
}

} // namespace UTIL

#endif // #ifndef UTIL_H_INCLUDED
