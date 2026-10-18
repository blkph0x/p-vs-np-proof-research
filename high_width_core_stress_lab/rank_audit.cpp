// Reproducible independent-enumeration audit for binary column matroids.
// Compile: g++ -O3 -std=c++17 -Wall -Wextra rank_audit.cpp -o rank_audit
// Usage: ./rank_audit n k seed full|balanced
// 'full' exhausts all subset sizes <=n/2 to audit internal 4-connectivity;
// 'balanced' exhausts exactly the n/2-size cuts for a certified pathwidth lower bound.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <set>
#include <vector>
using U = uint64_t;
static U rng_state;
U splitmix64() {
    U z = (rng_state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}
int rank_vectors(const std::vector<uint32_t> &xs, int k) {
    uint32_t basis[32] = {};
    int rank=0;
    for(uint32_t x:xs){
        while(x){
            int b = 31-__builtin_clz(x);
            if(basis[b])x^=basis[b];
            else {basis[b]=x;++rank;break;}
        }
    }
    (void)k;
    return rank;
}
int rank_side(U s,const std::vector<uint32_t>&cols){
    uint32_t basis[32]={};
    int r=0;
    while(s){
        unsigned j=__builtin_ctzll(s);s &= s-1;
        uint32_t x=cols[j];
        while(x){
            int p=31-__builtin_clz(x);
            if(basis[p])x^=basis[p];
            else {basis[p]=x;++r;break;}
        }
    }
    return r;
}
struct Audit{
    U checked=0,central_checked=0,central_witness=0;
    int central_min=std::numeric_limits<int>::max();
    int three_conn_violations=0,internal4_violations=0;
    int small_3seps=0,nontrivial_3seps=0;
    int max_low_sep_size=0;
    std::vector<U> central_hist;
};
inline U next_comb(U x){
    U c=x&-x;
    U r=x+c;
    return (((r^x)>>2)/c)|r;
}
int main(int argc,char**argv){
    if(argc!=5){std::cerr<<"usage: n k seed full|balanced\n";return 1;}
    int n=std::atoi(argv[1]),k=std::atoi(argv[2]);
    rng_state=std::strtoull(argv[3],nullptr,10);
    std::string mode(argv[4]);
    if(n<8||n>30||(n%2)||k<3||k>=n||k>30||(mode!="full"&&mode!="balanced")){
        std::cerr<<"Require even n in [8,30], k in [3,n-1], mode full|balanced\n";return 2;
    }
    std::vector<uint32_t> cols;
    U mask=(1ULL<<k)-1;
    for(int trials=0;(int)cols.size()<n && trials<100000;trials++){
        uint32_t v=uint32_t(splitmix64()&mask);
        if(v && std::find(cols.begin(),cols.end(),v)==cols.end())cols.push_back(v);
    }
    if((int)cols.size()!=n){std::cerr<<"not enough distinct nonzero columns\n";return 3;}
    if(rank_vectors(cols,k)!=k){
        std::cerr<<"generated matrix not full row rank\n";return 4;
    }
    auto start=std::chrono::steady_clock::now();
    const U all=(1ULL<<n)-1ULL;
    Audit a; a.central_hist.assign(k+1,0);
    for(int size=1;size<=n/2;size++){
        if(mode=="balanced" && size!=n/2)continue;
        U S=(1ULL<<size)-1ULL;
        while(S<=all){
            // For exactly balanced cuts S and ~S both have n/2 elements;
            // visit only one, with first column in S.
            bool half=(size==n/2);
            if(!half || (S&1ULL)){
                U T=all^S;
                int rA=rank_side(S,cols),rB=rank_side(T,cols);
                int lam=rA+rB-k;
                a.checked++;
                if(half){
                    a.central_checked++;
                    if(lam<a.central_min){a.central_min=lam;a.central_witness=S;}
                    if(lam>=0 && lam<=(int)k)a.central_hist[lam]++;
                }
                if(mode=="full"){
                    if(size>=2 && n-size>=2 && lam<=1)a.three_conn_violations++;
                    if(size>=3 && n-size>=3 && lam==2){
                        if(size==3){
                            a.small_3seps++;
                            // For 3-element S: triangle if r(S)==2, or
                            // triad if dual rank r*(S)=3-k+r(E\S)==2.
                            if(!(rA==2 || (3-k+rB)==2))a.internal4_violations++;
                        }else{
                            a.nontrivial_3seps++;
                            a.internal4_violations++;
                        }
                    }
                }
            }
            U next=next_comb(S);
            if(next<=S || next>all)break;
            S=next;
        }
    }
    auto end=std::chrono::steady_clock::now();
    double sec=std::chrono::duration<double>(end-start).count();
    std::cout<<"{\"n\":"<<n<<",\"k\":"<<k<<",\"seed\":"<<std::strtoull(argv[3],nullptr,10)
      <<",\"mode\":\""<<mode<<"\",\"columns\":[";
    for(int i=0;i<n;i++){if(i)std::cout<<",";std::cout<<cols[i];}
    std::cout<<"],\"checked_unordered_cuts\":"<<a.checked
      <<",\"central_checked\":"<<a.central_checked
      <<",\"central_min_lambda\":"<<a.central_min
      <<",\"central_witness_mask\":"<<a.central_witness
      <<",\"three_conn_violations\":"<<a.three_conn_violations
      <<",\"internal4_violations\":"<<a.internal4_violations
      <<",\"small_3seps\":"<<a.small_3seps
      <<",\"nontrivial_3seps\":"<<a.nontrivial_3seps
      <<",\"central_lambda_histogram\":[";
    for(int i=0;i<=k;i++){if(i)std::cout<<",";std::cout<<a.central_hist[i];}
    std::cout<<"],\"seconds\":"<<std::setprecision(8)<<sec<<"}\n";
}
