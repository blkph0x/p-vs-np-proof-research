# Independent order-discovery review

The bounded filled-graph search was replayed from the original scopes. It found width-three orders for the cumulative-parity chains and those orders drove independently verified exact weighted-DAG certificates through 128 blocks. It returned NO for the complete graph at width two and the cycle at width one, and UNKNOWN for the explicitly capped path search. A NO result is used only after all legal branches under the cap are exhausted; a state-cap stop carries no order or value.
