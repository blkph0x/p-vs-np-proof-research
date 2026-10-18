// Exhaustive connectivity audit for an explicitly supplied binary column matroid.
// Input: a text file containing n, k, then n decimal column masks.
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

using U = std::uint64_t;

struct Audit {
    std::uint64_t checked = 0;
    std::uint64_t central_checked = 0;
    U central_witness = 0;
    int central_min = std::numeric_limits<int>::max();
    int three_conn_violations = 0;
    int internal4_violations = 0;
    int small_3seps = 0;
    int nontrivial_3seps = 0;
    std::vector<std::uint64_t> central_hist;
};

int rank_values(const std::vector<std::uint32_t>& values) {
    std::uint32_t basis[32] = {};
    int rank = 0;
    for (std::uint32_t x : values) {
        while (x) {
            int bit = 31 - __builtin_clz(x);
            if (basis[bit]) x ^= basis[bit];
            else { basis[bit] = x; ++rank; break; }
        }
    }
    return rank;
}

int rank_side(U mask, const std::vector<std::uint32_t>& columns) {
    std::uint32_t basis[32] = {};
    int rank = 0;
    while (mask) {
        U bit = mask & (~mask + 1);
        int j = __builtin_ctzll(mask);
        mask ^= bit;
        std::uint32_t x = columns[j];
        while (x) {
            int top = 31 - __builtin_clz(x);
            if (basis[top]) x ^= basis[top];
            else { basis[top] = x; ++rank; break; }
        }
    }
    return rank;
}

U next_combination(U x) {
    U c = x & (~x + 1);
    U r = x + c;
    return (((r ^ x) >> 2) / c) | r;
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: matroid_audit columns.txt\n";
        return 2;
    }
    std::ifstream input(argv[1]);
    int n = 0, k = 0;
    if (!(input >> n >> k) || n < 8 || n > 30 || k < 1 || k > 30) {
        std::cerr << "invalid dimensions\n";
        return 2;
    }
    std::vector<std::uint32_t> columns(n);
    for (auto& column : columns) {
        unsigned long long value = 0;
        if (!(input >> value) || value == 0 || value >= (1ULL << k)) {
            std::cerr << "invalid column\n";
            return 2;
        }
        column = static_cast<std::uint32_t>(value);
    }
    if (rank_values(columns) != k) {
        std::cerr << "columns are not full row rank\n";
        return 3;
    }
    U all = (U(1) << n) - 1;
    Audit audit;
    audit.central_hist.assign(k + 1, 0);
    for (int size = 1; size <= n / 2; ++size) {
        U subset = (U(1) << size) - 1;
        while (subset <= all) {
            bool balanced = size == n / 2;
            if (!balanced || (subset & 1)) {
                U complement = all ^ subset;
                int rank_a = rank_side(subset, columns);
                int rank_b = rank_side(complement, columns);
                int lambda = rank_a + rank_b - k;
                ++audit.checked;
                if (balanced) {
                    ++audit.central_checked;
                    if (lambda < audit.central_min) {
                        audit.central_min = lambda;
                        audit.central_witness = subset;
                    }
                    if (lambda >= 0 && lambda <= k) ++audit.central_hist[lambda];
                }
                if (size >= 2 && n - size >= 2 && lambda <= 1) {
                    ++audit.three_conn_violations;
                }
                if (size >= 3 && n - size >= 3 && lambda == 2) {
                    if (size == 3) {
                        ++audit.small_3seps;
                        bool triangle = rank_a == 2;
                        bool triad = (3 - k + rank_b) == 2;
                        if (!triangle && !triad) ++audit.internal4_violations;
                    } else {
                        ++audit.nontrivial_3seps;
                        ++audit.internal4_violations;
                    }
                }
            }
            U next = next_combination(subset);
            if (next <= subset || next > all) break;
            subset = next;
        }
    }
    std::cout << "{\"n\":" << n << ",\"k\":" << k << ",\"columns\":[";
    for (int i = 0; i < n; ++i) { if (i) std::cout << ','; std::cout << columns[i]; }
    std::cout << "],\"checked_unordered_cuts\":" << audit.checked
              << ",\"central_checked\":" << audit.central_checked
              << ",\"central_min_lambda\":" << audit.central_min
              << ",\"central_witness_mask\":" << audit.central_witness
              << ",\"three_conn_violations\":" << audit.three_conn_violations
              << ",\"internal4_violations\":" << audit.internal4_violations
              << ",\"small_3seps\":" << audit.small_3seps
              << ",\"nontrivial_3seps\":" << audit.nontrivial_3seps
              << ",\"central_lambda_histogram\":[";
    for (std::size_t i = 0; i < audit.central_hist.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << audit.central_hist[i];
    }
    std::cout << "]}\n";
    return 0;
}
