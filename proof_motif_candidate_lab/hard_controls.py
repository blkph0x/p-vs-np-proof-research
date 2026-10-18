
from itertools import combinations,product
from miner import norm_clause,lit,var,mine_all,candidate_catalog

def edge_pairs(n):
    return list(combinations(range(n),2))

def clique_coloring_cnf(n,k):
    """
    A(edge,x): graph contains a k-clique via k position selectors.
    B(edge,y): graph is (k-1)-colorable.
    Shared variables are graph-edge atoms.
    """
    edges=edge_pairs(n)
    evar={e:i for i,e in enumerate(edges)}
    nextv=len(edges)

    x={}
    for i in range(k):
        for v in range(n):
            x[i,v]=nextv;nextv+=1

    colors=k-1
    y={}
    for v in range(n):
        for c in range(colors):
            y[v,c]=nextv;nextv+=1

    A=[]
    # Each clique position selects exactly one vertex.
    for i in range(k):
        A.append(norm_clause(lit(x[i,v],True) for v in range(n)))
        for u,v in combinations(range(n),2):
            A.append(norm_clause((lit(x[i,u],False),lit(x[i,v],False))))
    # Distinct positions cannot select same vertex.
    for i,j in combinations(range(k),2):
        for v in range(n):
            A.append(norm_clause((lit(x[i,v],False),lit(x[j,v],False))))
    # Chosen distinct vertices must have graph edge.
    for i,j in combinations(range(k),2):
        for u in range(n):
            for v in range(n):
                if u==v:continue
                e=tuple(sorted((u,v)))
                A.append(norm_clause((lit(x[i,u],False),lit(x[j,v],False),lit(evar[e],True))))

    B=[]
    # Every vertex receives exactly one of k-1 colors.
    for v in range(n):
        B.append(norm_clause(lit(y[v,c],True) for c in range(colors)))
        for c,d in combinations(range(colors),2):
            B.append(norm_clause((lit(y[v,c],False),lit(y[v,d],False))))
    # Adjacent vertices cannot share a color.
    for u,v in edges:
        ev=evar[(u,v)]
        for c in range(colors):
            B.append(norm_clause((lit(ev,False),lit(y[u,c],False),lit(y[v,c],False))))

    return {
        "A":A,"B":B,"shared":set(evar.values()),
        "nvars":nextv,"edgevars":evar,"x":x,"y":y
    }

def has_k_clique(n,k,edge_bits):
    edges=edge_pairs(n)
    E={edges[i] for i,b in enumerate(edge_bits) if b}
    for S in combinations(range(n),k):
        if all(tuple(sorted((u,v))) in E for u,v in combinations(S,2)):
            return True
    return False

def colorable(n,c,edge_bits):
    edges=edge_pairs(n)
    E={edges[i] for i,b in enumerate(edge_bits) if b}
    for colors in product(range(c),repeat=n):
        if all(colors[u]!=colors[v] for u,v in E):
            return True
    return False

def exhaustive_graph_separation(n,k):
    m=len(edge_pairs(n))
    for bits in product([0,1],repeat=m):
        if has_k_clique(n,k,bits) and colorable(n,k-1,bits):
            return False
    return True

def shared_candidates(clauses,shared):
    mined=mine_all(clauses)
    cat=candidate_catalog(mined,clauses)
    return [c for c in cat if set(c["support"])<=set(shared)], mined, cat
