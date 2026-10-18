// Exhaustive rank-five binary row-basis oracle.
//
// The program deliberately uses a separate implementation from exact_oracle.py:
// it enumerates GL(r,2) by incremental span construction and evaluates each
// candidate from the original column vectors.  It emits a small JSON record
// containing both the count-first and exceptional-rank-first optima.

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

struct Candidate {
    std::vector<int> objective;
    std::vector<unsigned> transform;
    int exceptional_rank = 0;
    int exceptional_count = 0;
    int excess = 0;
    int total = 0;
    bool set = false;
};

static int gf2_rank(const std::vector<unsigned>& values) {
    unsigned basis[32] = {};
    int result = 0;
    for (unsigned value : values) {
        while (value != 0) {
            int pivot = 31 - __builtin_clz(value);
            if (basis[pivot] != 0) {
                value ^= basis[pivot];
            } else {
                basis[pivot] = value;
                ++result;
                break;
            }
        }
    }
    return result;
}

static unsigned parity(unsigned value) {
    return __builtin_popcount(value) & 1U;
}

static std::vector<unsigned> transformed_columns(
    const std::vector<unsigned>& columns,
    const std::vector<unsigned>& transform,
    int rank) {
    std::vector<unsigned> result;
    result.reserve(columns.size());
    for (unsigned column : columns) {
        unsigned transformed = 0;
        for (int row = 0; row < rank; ++row) {
            transformed |= parity(transform[row] & column) << row;
        }
        result.push_back(transformed);
    }
    return result;
}

class Search {
  public:
    Search(const std::vector<unsigned>& rows, int n)
        : rank_(static_cast<int>(rows.size())), n_(n), columns_(n, 0) {
        for (int column = 0; column < n_; ++column) {
            unsigned value = 0;
            for (int row = 0; row < rank_; ++row) {
                value |= ((rows[row] >> column) & 1U) << row;
            }
            columns_[column] = value;
        }
    }

    void run() {
        std::vector<unsigned> transform;
        std::vector<unsigned> span{0};
        enumerate(transform, span);
    }

    std::uint64_t evaluated() const { return evaluated_; }
    const Candidate& count_best() const { return count_best_; }
    const Candidate& rank_best() const { return rank_best_; }

  private:
    void enumerate(std::vector<unsigned>& transform,
                   const std::vector<unsigned>& span) {
        if (static_cast<int>(transform.size()) == rank_) {
            evaluate(transform);
            return;
        }
        const unsigned limit = 1U << rank_;
        for (unsigned row = 0; row < limit; ++row) {
            if (std::find(span.begin(), span.end(), row) != span.end()) {
                continue;
            }
            std::vector<unsigned> next_span = span;
            next_span.reserve(span.size() * 2);
            for (unsigned member : span) {
                next_span.push_back(member ^ row);
            }
            transform.push_back(row);
            enumerate(transform, next_span);
            transform.pop_back();
        }
    }

    void evaluate(const std::vector<unsigned>& transform) {
        const std::vector<unsigned> columns = transformed_columns(columns_, transform, rank_);
        std::vector<unsigned> exceptional;
        int exceptional_count = 0;
        int excess = 0;
        int total = 0;
        for (unsigned column : columns) {
            const int weight = __builtin_popcount(column);
            total += weight;
            if (weight > 2) {
                ++exceptional_count;
                exceptional.push_back(column);
                excess += weight - 2;
            }
        }
        const int exceptional_rank = gf2_rank(exceptional);
        const std::vector<int> count_objective{exceptional_count, excess, total};
        const std::vector<int> rank_objective{
            exceptional_rank, exceptional_count, excess, total};
        Candidate candidate;
        candidate.transform = transform;
        candidate.exceptional_rank = exceptional_rank;
        candidate.exceptional_count = exceptional_count;
        candidate.excess = excess;
        candidate.total = total;
        candidate.objective = count_objective;
        if (!count_best_.set || count_objective < count_best_.objective ||
            (count_objective == count_best_.objective && transform < count_best_.transform)) {
            candidate.set = true;
            count_best_ = candidate;
        }
        candidate.objective = rank_objective;
        if (!rank_best_.set || rank_objective < rank_best_.objective ||
            (rank_objective == rank_best_.objective && transform < rank_best_.transform)) {
            candidate.set = true;
            rank_best_ = candidate;
        }
        ++evaluated_;
    }

    int rank_;
    int n_;
    std::vector<unsigned> columns_;
    std::uint64_t evaluated_ = 0;
    Candidate count_best_;
    Candidate rank_best_;
};

static void print_vector(const std::vector<int>& values) {
    std::cout << '[';
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << values[i];
    }
    std::cout << ']';
}

static void print_transform(const std::vector<unsigned>& values) {
    std::cout << '[';
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << values[i];
    }
    std::cout << ']';
}

static void print_candidate(const Candidate& candidate) {
    std::cout << "{\"objective\":";
    print_vector(candidate.objective);
    std::cout << ",\"row_transform\":";
    print_transform(candidate.transform);
    std::cout << ",\"exceptional_rank\":" << candidate.exceptional_rank
              << ",\"exceptional_count\":" << candidate.exceptional_count
              << ",\"excess\":" << candidate.excess
              << ",\"total\":" << candidate.total << '}';
}

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: rank5_exact n row0 row1 ... row4\n";
        return 2;
    }
    const int n = std::stoi(argv[1]);
    std::vector<unsigned> rows;
    for (int index = 2; index < argc; ++index) {
        rows.push_back(static_cast<unsigned>(std::stoul(argv[index])));
    }
    if (n < 0 || n > 31 || rows.size() != 5) {
        std::cerr << "rank-five input requires 0 <= n <= 31 and five rows\n";
        return 2;
    }
    for (unsigned row : rows) {
        if ((row >> n) != 0) {
            std::cerr << "row exceeds n coordinates\n";
            return 2;
        }
    }
    Search search(rows, n);
    search.run();
    std::cout << "{\"status\":\"EXACT\",\"rank\":5,\"n\":" << n
              << ",\"transforms_evaluated\":" << search.evaluated()
              << ",\"count_first\":";
    print_candidate(search.count_best());
    std::cout << ",\"rank_first\":";
    print_candidate(search.rank_best());
    std::cout << "}\n";
    return 0;
}
