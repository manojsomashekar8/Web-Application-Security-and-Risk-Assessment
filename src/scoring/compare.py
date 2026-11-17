"""Ranking comparison metrics: Kendall's tau-a and top-k overlap (pure Python, no scipy)."""


def kendall_tau(a: dict, b: dict) -> float:
    """a, b map item -> rank. Computed over items present in both."""
    items = sorted(set(a) & set(b))
    n = len(items)
    if n < 2:
        return 1.0
    s = 0
    for i in range(n):
        for j in range(i + 1, n):
            x, y = items[i], items[j]
            s += (1 if (a[x] - a[y]) * (b[x] - b[y]) > 0 else -1 if (a[x] - a[y]) * (b[x] - b[y]) < 0 else 0)
    return s / (n * (n - 1) / 2)


def top_k_overlap(a: dict, b: dict, k: int = 10) -> float:
    ta = {i for i, r in a.items() if r <= k}
    tb = {i for i, r in b.items() if r <= k}
    return len(ta & tb) / min(k, len(a), len(b)) if a and b else 0.0
