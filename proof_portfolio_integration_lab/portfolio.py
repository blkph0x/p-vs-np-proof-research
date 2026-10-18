
from itertools import product
import math

def bits_needed(n):
    return max(1,math.ceil(math.log2(max(2,n))))

def cnf_bits(clauses,literals,nvars):
    # Simple self-delimiting accounting model: each literal carries var id + sign,
    # each clause carries a small delimiter/length overhead.
    return literals*(bits_needed(nvars)+1)+clauses*(bits_needed(literals+1)+1)

def native_atom_bits(nrefs,nvars,tag_bits=8,extra_bits=1):
    return tag_bits+nrefs*bits_needed(nvars)+extra_bits

# ---------- Exact semantic audit helpers ----------

def alltrue_A(a):
    return all(a)

def B_opposite_parity(a):
    # Contradicts the parity of the all-true assignment.
    q=len(a)
    return (sum(a)&1)!=(q&1)

def B_sum_le_qminus1(a):
    return sum(a)<=len(a)-1

def B_not_j(a,j=0):
    return not a[j]

def I_conjunction(a):
    return all(a)

def I_parity_of_alltrue(a):
    return (sum(a)&1)==(len(a)&1)

def I_pb_alltrue(a):
    return sum(a)>=len(a)

def I_literal(a,j=0):
    return bool(a[j])

def check_interpolant(q,A,B,I):
    for a in product([0,1],repeat=q):
        Aok=A(a); Bok=B(a); Iok=I(a)
        if Aok and not Iok:
            return False
        if Bok and Iok:
            return False
    return True

def receiver_candidates(q,receiver):
    """
    Same source A = all variables true.
    Return exact candidate descriptions known to satisfy A => I.
    Receiver decides which are sufficient for contradiction.
    """
    nbits=bits_needed(q)
    raw={
        "language":"CNF-conjunction",
        "message_bits":cnf_bits(q,q,q),
        "setup_work":q,
        "recurring_work":q,
        "semantic":"AND_all"
    }
    cands=[raw]
    # Literal consequences are all valid consequences of A.
    if receiver.startswith("not-"):
        j=int(receiver.split("-")[1])
        cands.append({
            "language":"literal",
            "message_bits":nbits+1,
            "setup_work":1,
            "recurring_work":1,
            "semantic":f"x{j}"
        })
    if receiver=="opposite-parity":
        cands.append({
            "language":"XOR",
            "message_bits":native_atom_bits(q,q,8,1),
            "setup_work":q,
            "recurring_work":1,
            "semantic":"parity"
        })
    if receiver=="sum<=q-1":
        cands.append({
            "language":"PB",
            "message_bits":native_atom_bits(q,q,8,bits_needed(q+1)),
            "setup_work":q,
            "recurring_work":1,
            "semantic":"sum>=q"
        })
    return cands

def candidate_semantics(name,q,receiver):
    if name=="CNF-conjunction": return I_conjunction
    if name=="literal":
        j=int(receiver.split("-")[1])
        return lambda a: I_literal(a,j)
    if name=="XOR": return I_parity_of_alltrue
    if name=="PB": return I_pb_alltrue
    raise ValueError(name)

def receiver_B(receiver):
    if receiver=="opposite-parity": return B_opposite_parity
    if receiver=="sum<=q-1": return B_sum_le_qminus1
    if receiver.startswith("not-"):
        j=int(receiver.split("-")[1])
        return lambda a: B_not_j(a,j)
    raise ValueError(receiver)


def source_candidates(q):
    """
    Candidates generated from source A = AND_i x_i, independent of receiver.
    """
    cands=[{
        "language":"CNF-conjunction",
        "message_bits":cnf_bits(q,q,q),
        "setup_work":q,"recurring_work":q,
        "semantic":"AND_all"
    }]
    for j in range(q):
        cands.append({
            "language":"literal",
            "var":j,
            "message_bits":bits_needed(q)+1,
            "setup_work":1,"recurring_work":1,
            "semantic":f"x{j}"
        })
    cands.append({
        "language":"XOR",
        "message_bits":native_atom_bits(q,q,8,1),
        "setup_work":q,"recurring_work":1,
        "semantic":"parity"
    })
    cands.append({
        "language":"PB",
        "message_bits":native_atom_bits(q,q,8,bits_needed(q+1)),
        "setup_work":q,"recurring_work":1,
        "semantic":"sum>=q"
    })
    return cands

def source_candidate_semantics(c,q):
    if c["language"]=="CNF-conjunction": return I_conjunction
    if c["language"]=="literal":
        j=c["var"]; return lambda a: I_literal(a,j)
    if c["language"]=="XOR": return I_parity_of_alltrue
    if c["language"]=="PB": return I_pb_alltrue
    raise ValueError(c["language"])

# ---------- Forced-interpolant language families ----------

def parity_costs(q):
    # A=even parity, B=odd parity => interpolant forced to be parity exactly.
    clauses=1<<(q-1)
    lits=q*clauses
    return {
        "CNF":{"clauses":clauses,"literals":lits,"bits":cnf_bits(clauses,lits,q)},
        "XOR":{"atoms":1,"bits":native_atom_bits(q,q,8,1),"states":2},
        "AUTOMATON":{"states":2,"bits":2*q+8},
    }

def amo_costs(q):
    clauses=q*(q-1)//2
    lits=2*clauses
    return {
        "CNF":{"clauses":clauses,"literals":lits,"bits":cnf_bits(clauses,lits,q)},
        "PB":{"atoms":1,"bits":native_atom_bits(q,q,8,bits_needed(q+1)),"states":3},
        "AUTOMATON":{"states":3,"bits":3*q+8},
    }

def amk_costs(q,k):
    # Direct no-aux CNF consists of all (k+1)-negative clauses.
    clauses=math.comb(q,k+1)
    lits=(k+1)*clauses
    return {
        "CNF":{"clauses":clauses,"literals":lits,"bits":cnf_bits(clauses,lits,q)},
        "PB":{"atoms":1,"bits":native_atom_bits(q,q,8,bits_needed(q+1)),"states":k+2},
        "AUTOMATON":{"states":k+2,"bits":(k+2)*q+8},
    }

def parity_pred(a): return (sum(a)&1)==0
def amo_pred(a): return sum(a)<=1
def amk_pred(k): return lambda a: sum(a)<=k

def check_complement_split(q,pred):
    for a in product([0,1],repeat=q):
        A=pred(a);B=not pred(a);I=pred(a)
        if A and not I:return False
        if B and I:return False
    return True


# ---------- Quotient / global-theory candidates ----------

def quotient_or_costs(w,q):
    """
    Raw Hall/OR clause width w plus equality partition with q classes.
    Theory-aware resolution compresses message to q representatives in w-q steps.
    """
    raw_bits=cnf_bits(1,w,w)
    quotient_bits=cnf_bits(1,q,w)
    return {
        "raw_CNF":{"width":w,"bits":raw_bits,"setup_work":0,"recurring_work":w},
        "quotient_CNF":{"width":q,"bits":quotient_bits,
                        "setup_work":w-q,"recurring_work":q,
                        "resolution_steps":w-q},
        "quotient_PB":{"width":q,
                       "bits":native_atom_bits(q,w,8,bits_needed(q+1)),
                       "setup_work":w-q+q,
                       "recurring_work":1,
                       "resolution_steps":w-q},
    }

def matching_costs(n,edge_count=None):
    """
    Perfect-matching interpolant over n x n edge atoms.
    CNF figure is a standard exact-one encoding upper bound, not a minimum lower bound.
    Native theory message stores graph + MATCHING tag.
    """
    if edge_count is None: edge_count=n*n
    nvars=n*n
    alo=2*n
    amo=2*n*(n*(n-1)//2)
    cnf_clauses=alo+amo
    cnf_lits=alo*n+2*amo
    native_bits=16 + edge_count*(2*bits_needed(n))
    return {
        "CNF_exact_one_upper":{"clauses":cnf_clauses,"literals":cnf_lits,
                               "bits":cnf_bits(cnf_clauses,cnf_lits,nvars)},
        "MATCHING":{"atoms":1,"bits":native_bits,
                    "verify_work":"poly_matching"},
    }

# ---------- Online rent/buy controller ----------

def two_mode_online(raw_recurring,spec_setup,spec_recurring,repetitions):
    """
    Ski-rental style: rent raw until cumulative recurring premium pays for setup.
    Then buy specialized mode. Exact stationary two-mode accounting.
    """
    raw_recurring=float(raw_recurring)
    spec_setup=float(spec_setup)
    spec_recurring=float(spec_recurring)
    if spec_recurring>=raw_recurring:
        return {
            "buy_at":None,
            "online_cost":repetitions*raw_recurring,
            "offline_cost":repetitions*raw_recurring,
            "ratio":1.0,
        }
    premium=raw_recurring-spec_recurring
    # Rent k=floor(B/premium) times; then buy before the next occurrence.
    # If setup is cheaper than one premium, k=0 and we buy immediately.
    threshold=math.floor(spec_setup/premium) if spec_setup>0 else 0
    if repetitions<=threshold:
        online=repetitions*raw_recurring
        buy_at=None
    else:
        online=threshold*raw_recurring+spec_setup+(repetitions-threshold)*spec_recurring
        buy_at=threshold+1
    offline=min(repetitions*raw_recurring,
                spec_setup+repetitions*spec_recurring)
    return {
        "buy_at":buy_at,
        "threshold":threshold,
        "online_cost":online,
        "offline_cost":offline,
        "ratio":online/offline if offline else 1.0,
    }

def best_candidate(cands):
    """
    One-shot receiver-aware selector: minimize transmitted bits, then setup work.
    Only candidates already certified semantically are passed here.
    """
    return min(cands,key=lambda x:(x["message_bits"],x["setup_work"],x["recurring_work"]))
