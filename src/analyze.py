"""Azerbaijan new-car market from public Turbo.az listings: structure, pricing and listing tactics.

Reads data/listings.csv (see extract.py), writes outputs/*.csv and images/*.png.
Sellers are grouped into types; no individual seller is named in any output.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR, IMG_DIR = ROOT / "outputs", ROOT / "images"

SURFACE = "#fcfcfb"
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
NEUTRAL = "#c3c2b7"
BLUE, ORANGE = "#2a78d6", "#eb6834"
ORIGIN_COLORS = {"China": "#2a78d6", "Japan": "#eb6834", "Korea": "#1baf7a",
                 "Europe": "#eda100", "USA": "#e87ba4", "Russia": "#008300"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "Segoe UI", "font.size": 12, "text.color": INK,
    "axes.edgecolor": BASELINE, "axes.labelcolor": INK_2,
    "xtick.color": MUTED, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
})

# Not passenger cars: motorcycles, ATVs, golf carts, trucks, buses, classic cars
EXCLUDE_BRANDS = {
    "ATV", "Anyang Kinland", "BENDA", "Bajaj", "CFMOTO", "Cengo", "Dayun", "Ducati", "FAW", "GAZ",
    "General Auto", "HOWO", "Haojue", "Harley-Davidson", "IJ", "Isuzu", "Jaguar", "KYC", "Kawasaki",
    "Mikilon", "Moskvich", "Muravey", "Nama", "Polaris", "QJMotor", "Royal Enfield", "Saab", "SamAuto",
    "Shacman", "Shining Golf Cart", "TVS", "Tufan", "Ural", "Vespa", "Vmoto", "Voge", "Volta", "Yadea",
    "Yamaha",
}
EXCLUDE_MODELS = {
    ("Hyundai", "County"), ("Hyundai", "HD-78"), ("Hyundai", "H 100"), ("Hyundai", "Mighty EX5"),
    ("Hyundai", "Mighty GT11"), ("JAC", "Ankai"), ("JAC", "LD1A2"), ("JAC", "LD3A3"), ("JAC", "LE745"),
    ("JAC", "LE79Z"), ("JAC", "Sunray"), ("JAC", "X200"), ("JMC", "Carrying 4x2"), ("JMC", "Conquer 4x2"),
    ("JMC", "D60"), ("JMC", "D77"), ("JMC", "Touring"), ("Chevrolet", "Damas"), ("Chevrolet", "Labo"),
    ("DongFeng", "Captain C"), ("DongFeng", "DLQ5075ZLJ5"), ("BMW", "F 900 GS"), ("BMW", "M 1000 R"),
    ("BMW", "S 1000 XR"), ("Honda", "H’ness CB350 DLX"), ("Kia", "K2500"), ("Peugeot", "Boxer"),
    ("Fiat", "Ducato"),
}
ORIGIN = {
    "China": ["Avatr", "BAW", "BYD", "Baic", "Bestune", "Changan", "Chery", "DFSK", "Denza", "DongFeng",
              "GAC", "GWM (Great Wall Motor)", "Geely", "Haval", "Hongqi", "IM", "JAC", "JAECOO", "JETOUR",
              "JMC", "KAIYI", "Karry", "Leapmotor", "Li Auto", "Lynk & Co", "M-Hero", "MG", "Maextro",
              "Maple", "Neta", "ROX (Polar Stone)", "Seres Aito", "Soueast", "Voyah", "Wuling", "XPeng",
              "Xiaomi", "ZEEKR"],
    "Japan": ["Toyota", "Lexus", "Nissan", "Infiniti", "Mazda", "Mitsubishi", "Honda", "Suzuki"],
    "Korea": ["Hyundai", "Kia", "Genesis"],
    "Europe": ["Mercedes", "Mercedes-Maybach", "BMW", "Mini", "Audi", "Volkswagen", "Skoda", "Porsche",
               "Bentley", "Land Rover", "Volvo", "Maserati", "Ferrari", "Fiat", "Peugeot", "Citroen", "Opel",
               "Lotus"],
    "USA": ["Tesla", "Chevrolet", "Cadillac", "GMC"],
    "Russia": ["LADA (VAZ)", "UAZ"],
}
BRAND_ORIGIN = {b: o for o, brands in ORIGIN.items() for b in brands}
# Brands the author works with professionally. They stay in the market view, but their official-dealer
# listings are left out of every seller-type and price comparison (confidentiality).
EMPLOYER_BRANDS = {"Mercedes", "Mercedes-Maybach", "Changan", "Lynk & Co", "Skoda", "Avatr", "XPeng", "Leapmotor"}


def load() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "listings.csv")
    df = df[~df["brand"].isin(EXCLUDE_BRANDS)]
    df = df[~df.apply(lambda r: (r["brand"], r["model"]) in EXCLUDE_MODELS, axis=1)]
    df = df[(df["year"] >= 2024) & (df["km"] <= 1000) & (df["price_azn"] >= 5000)].copy()
    df["origin"] = df["brand"].map(BRAND_ORIGIN)
    missing = df.loc[df["origin"].isna(), "brand"].unique()
    assert not len(missing), f"brands without origin: {missing}"
    df["seller_type"] = np.select(
        [df["official"] == 1, df["is_dealer"] == 1], ["Official dealer", "Other dealer"], "Private seller")
    tags = df["tags"].fillna("")
    df["promoted"] = tags.str.contains("VIP|Premium")
    df["credit"] = tags.str.contains("Kredit")
    df["on_order"] = tags.str.contains("Sifarişlə")
    df["electric"] = df["engine_l"].isna()
    df["model_key"] = df["brand"] + " " + df["model"]
    engine = df["engine_l"].map(lambda e: "EV" if pd.isna(e) else f"{e:.1f}L")
    df["variant"] = df["model_key"] + " " + engine + " " + df["year"].astype(str)
    df["employer_official"] = df["brand"].isin(EMPLOYER_BRANDS) & (df["seller_type"] == "Official dealer")
    return df


def headline(fig, title: str, subtitle: str, n: int) -> None:
    fig.text(0.04, 0.95, title, fontsize=18, fontweight="bold", va="top")
    fig.text(0.04, 0.885, subtitle, fontsize=12, color=INK_2, va="top")
    fig.text(0.04, 0.02, f"Source: public Turbo.az listings of new passenger cars, scraped 2 Oct 2026 (n = {n:,}). "
             "Listing prices, not transaction prices. Official-dealer listings of brands the author works with are excluded "
             "from seller and price comparisons.", fontsize=9, color=MUTED)


def save(fig, name: str) -> None:
    IMG_DIR.mkdir(exist_ok=True)
    fig.savefig(IMG_DIR / name, dpi=100)
    plt.close(fig)


def bare_x(ax) -> None:
    ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)


def market_by_origin(df: pd.DataFrame) -> pd.DataFrame:
    t = df.groupby("origin").agg(listings=("slug", "size"), brands=("brand", "nunique"),
                                 models=("model_key", "nunique"), median_price=("price_azn", "median"))
    t["share_pct"] = 100 * t["listings"] / t["listings"].sum()
    t = t.sort_values("listings", ascending=False)

    fig, axes = plt.subplots(1, 3, figsize=(16, 9), sharey=True)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.76, bottom=0.10, wspace=0.25)
    y = range(len(t))[::-1]
    colors = [ORIGIN_COLORS[o] for o in t.index]
    for ax, (col, title, fmt) in zip(axes, [("share_pct", "Share of listings", "{:.1f}%"),
                                            ("models", "Models listed", "{:.0f}"),
                                            ("median_price", "Median price, AZN", "{:,.0f}")]):
        ax.barh(list(y), t[col], color=colors, height=0.62)
        ax.set_title(title, color=INK_2)
        bare_x(ax)
        ax.set_xlim(0, t[col].max() * 1.3)
        for yi, v in zip(y, t[col]):
            ax.text(v + t[col].max() * 0.02, yi, fmt.format(v), va="center", fontsize=12, color=INK_2)
    axes[0].set_yticks(list(y), t.index, fontsize=13)
    china, japan, eu = t.loc["China"], t.loc["Japan"], t.loc["Europe"]
    lo, hi = eu.median_price / japan.median_price, eu.median_price / china.median_price
    headline(fig, f"Chinese brands make up {china.share_pct:.0f}% of new-car listings in Azerbaijan",
             f"{int(china.brands)} Chinese brands and {int(china.models)} models on sale. Japanese brands are second "
             f"by volume; the median European car is listed at {lo:.1f}–{hi:.1f}× the price.", len(df))
    save(fig, "01_market_by_origin.png")
    return t.round(1)


def top_models(df: pd.DataFrame) -> pd.DataFrame:
    t = (df.groupby(["model_key", "origin"]).agg(listings=("slug", "size"), median_price=("price_azn", "median"))
         .reset_index().sort_values("listings", ascending=False).head(15))
    top_share = 100 * t["listings"].sum() / len(df)

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.subplots_adjust(left=0.20, right=0.80, top=0.80, bottom=0.08)
    y = range(len(t))[::-1]
    ax.barh(list(y), t["listings"], color=[ORIGIN_COLORS[o] for o in t["origin"]], height=0.66)
    ax.set_yticks(list(y), t["model_key"], fontsize=12)
    bare_x(ax)
    ax.set_xlim(0, t["listings"].max() * 1.15)
    for yi, (_, r) in zip(y, t.iterrows()):
        ax.text(r.listings + 3, yi, f"{r.listings}", va="center", fontsize=11, color=INK)
        ax.text(t["listings"].max() * 1.22, yi, f"{r.median_price:,.0f} AZN", va="center", fontsize=11, color=INK_2)
    ax.text(t["listings"].max() * 1.22, len(t) - 0.2, "median price", fontsize=10, color=MUTED)
    handles = [plt.Rectangle((0, 0), 1, 1, color=ORIGIN_COLORS[o]) for o in t["origin"].unique()]
    ax.legend(handles, t["origin"].unique(), loc="lower right", frameon=False, fontsize=11)
    headline(fig, f"15 models carry {top_share:.0f}% of all new-car listings",
             "Most-listed new car models, number of active listings.", len(df))
    save(fig, "02_top_models.png")
    return t


RNG = np.random.default_rng(7)
N_BOOT = 4000


def _gap(a: np.ndarray, b: np.ndarray) -> float:
    return 100 * (np.median(b) / np.median(a) - 1)


def gap_with_ci(official: np.ndarray, other: np.ndarray) -> tuple[float, float, float, float]:
    """Median gap (other vs official, %), 95% bootstrap CI and a two-sided permutation p-value."""
    est = _gap(official, other)
    boots = np.array([_gap(RNG.choice(official, len(official)), RNG.choice(other, len(other)))
                      for _ in range(N_BOOT)])
    pooled, k = np.concatenate([official, other]), len(official)
    perm = np.empty(N_BOOT)
    for i in range(N_BOOT):
        RNG.shuffle(pooled)
        perm[i] = _gap(pooled[:k], pooled[k:])
    p = (np.sum(np.abs(perm) >= abs(est)) + 1) / (N_BOOT + 1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return est, lo, hi, p


def _official_gap(d: pd.DataFrame, key: str, with_ci: bool = False) -> pd.DataFrame:
    rows = []
    for k, grp in d.groupby(key):
        off = grp.loc[grp["seller_type"] == "Official dealer", "price_azn"].to_numpy(float)
        oth = grp.loc[grp["seller_type"] == "Other dealer", "price_azn"].to_numpy(float)
        if len(off) < 3 or len(oth) < 3:
            continue
        row = {key: k, "model_key": grp["model_key"].iat[0], "official_n": len(off), "other_n": len(oth),
               "official_median": np.median(off), "other_median": np.median(oth), "gap_pct": _gap(off, oth)}
        if with_ci:
            _, row["ci_low"], row["ci_high"], row["p_value"] = gap_with_ci(off, oth)
        rows.append(row)
    return pd.DataFrame(rows).set_index(key)


def official_vs_other(df: pd.DataFrame) -> pd.DataFrame:
    """Naive gap (any version of the model) vs like-for-like gap (same engine and model year), with 95% CIs."""
    d = df[~df["price_estimated"].astype(bool) & (df["seller_type"] != "Private seller")]
    naive = _official_gap(d, "model_key")
    like = _official_gap(d, "variant", with_ci=True)
    like["n"] = like["official_n"] + like["other_n"]
    like = like.sort_values("n").groupby("model_key").tail(1).reset_index().set_index("model_key")
    t = naive[["gap_pct"]].rename(columns={"gap_pct": "naive_gap_pct"}).join(
        like[["variant", "gap_pct", "ci_low", "ci_high", "p_value", "official_n", "other_n"]]
        .rename(columns={"gap_pct": "like_for_like_gap_pct"}), how="inner")
    # Significant only if the bootstrap CI excludes 0 AND the permutation test agrees (tiny groups make
    # bootstrap CIs of medians degenerate). Holm correction for testing several models at once.
    t["significant"] = ((t["ci_high"] < 0) | (t["ci_low"] > 0)) & (t["p_value"] < 0.05)
    order = t["p_value"].sort_values().index
    m = len(t)
    holm = np.maximum.accumulate([min(1, p * (m - i)) for i, p in enumerate(t.loc[order, "p_value"])])
    t.loc[order, "p_holm"] = holm
    t = t.sort_values("like_for_like_gap_pct")

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.subplots_adjust(left=0.20, right=0.76, top=0.78, bottom=0.10)
    y = np.arange(len(t))
    sig = t["significant"].to_numpy()
    ax.axvline(0, color=INK_2, lw=1)
    ax.hlines(y, t["ci_low"], t["ci_high"], color=BLUE, lw=6, alpha=0.25)
    ax.scatter(t["naive_gap_pct"], y, s=80, color=NEUTRAL, zorder=3, edgecolor=SURFACE, linewidth=2)
    ax.scatter(t.loc[sig, "like_for_like_gap_pct"], y[sig], s=110, zorder=4, color=BLUE,
               edgecolor=SURFACE, linewidth=2)
    ax.scatter(t.loc[~sig, "like_for_like_gap_pct"], y[~sig], s=110, zorder=4, facecolor=SURFACE,
               edgecolor=BLUE, linewidth=2)
    ax.set_yticks(y, t.index, fontsize=11)
    ax.grid(axis="x", color=GRID)
    ax.set_axisbelow(True)
    ax.set_xlabel("Non-official dealers' median price vs official dealer, %  (left = cheaper elsewhere)")
    lim = max(abs(t[["naive_gap_pct", "ci_low", "ci_high"]]).max().max() * 1.1, 10)
    ax.set_xlim(-lim, lim)
    for yi, (m, r) in zip(y, t.iterrows()):
        ax.text(lim * 1.04, yi, f"{r.variant.replace(m + ' ', '')} · n = {r.official_n}/{r.other_n} · p = {r.p_value:.3f}",
                va="center", fontsize=10, color=INK_2 if r.significant else MUTED)
    handles = [plt.Line2D([], [], marker="o", ls="", color=NEUTRAL, markersize=9),
               plt.Line2D([], [], marker="o", ls="", color=BLUE, markersize=10),
               plt.Line2D([], [], marker="o", ls="", markerfacecolor=SURFACE, markeredgecolor=BLUE, markersize=10),
               plt.Line2D([], [], color=BLUE, lw=6, alpha=0.25)]
    ax.legend(handles, ["Any version (naive)", "Same version, significant (p < 0.05)", "Same version, not significant",
                        "95% bootstrap CI"], loc="lower left", bbox_to_anchor=(0, 1.0), ncol=4, frameon=False,
              fontsize=10)
    biggest = (t["naive_gap_pct"] - t["like_for_like_gap_pct"]).abs().idxmax()
    b = t.loc[biggest]
    headline(fig, f"{biggest}: {abs(b.naive_gap_pct):.0f}% cheaper elsewhere, or {abs(b.like_for_like_gap_pct):.0f}%? "
             "Depends on what you compare",
             f"Comparing the same version shrinks most gaps: {int(t['significant'].sum())} of {len(t)} are statistically "
             "significant (permutation test). 3+ listings per seller type.", len(df))
    save(fig, "03_official_vs_other_dealers.png")
    return t.round(3)


def _spread(x: np.ndarray) -> float:
    return 100 * (np.percentile(x, 90) / np.percentile(x, 10) - 1)


def price_dispersion(df: pd.DataFrame) -> pd.DataFrame:
    d = df[~df["price_estimated"].astype(bool)]
    rows = []
    for v, grp in d.groupby("variant"):
        p = grp["price_azn"].to_numpy(float)
        if len(p) < 15:
            continue
        boots = [_spread(RNG.choice(p, len(p))) for _ in range(N_BOOT)]
        rows.append({"variant": v, "n": len(p), "p10": np.percentile(p, 10), "median": np.median(p),
                     "p90": np.percentile(p, 90), "spread_pct": _spread(p),
                     "spread_ci_low": np.percentile(boots, 2.5), "spread_ci_high": np.percentile(boots, 97.5)})
    t = pd.DataFrame(rows).set_index("variant").sort_values("spread_pct").tail(15)

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.subplots_adjust(left=0.20, right=0.78, top=0.80, bottom=0.10)
    y = np.arange(len(t))
    rel_lo = 100 * (t["p10"] / t["median"] - 1)
    rel_hi = 100 * (t["p90"] / t["median"] - 1)
    ax.hlines(y, rel_lo, rel_hi, color=BLUE, lw=8, alpha=0.35)
    ax.scatter(np.zeros(len(t)), y, s=90, color=BLUE, zorder=3, edgecolor=SURFACE, linewidth=2)
    ax.axvline(0, color=BASELINE, lw=1)
    ax.set_yticks(y, t.index, fontsize=11)
    ax.grid(axis="x", color=GRID)
    ax.set_axisbelow(True)
    ax.set_xlabel("Listing price relative to the version's median, % (10th to 90th percentile)")
    xmax = ax.get_xlim()[1]
    for yi, (_, r) in zip(y, t.iterrows()):
        ax.text(xmax + 1, yi, f"{r.spread_pct:.0f}% (95% CI {r.spread_ci_low:.0f}–{r.spread_ci_high:.0f}) · n = {int(r.n)}",
                va="center", fontsize=10, color=INK_2)
    top = t.loc[t["spread_ci_low"].idxmax()]  # the widest spread we can be confident about
    headline(fig, f"Same model, same engine, same year: {top.name} listings sit {top.spread_pct:.0f}% apart",
             "Price spread within one version (P90 vs P10) with 95% bootstrap CI, versions with 15+ listings. "
             "Trim level explains part of it.", len(df))
    save(fig, "04_price_dispersion.png")
    return t.round(1)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    den = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return 100 * (c - h), 100 * (c + h)


def two_prop(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float, float, float]:
    """Difference in percentage points with 95% CI (Wald) and two-sided z-test p-value."""
    from math import erfc, sqrt
    p1, p2 = k1 / n1, k2 / n2
    se = sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    pp = (k1 + k2) / (n1 + n2)
    z = (p1 - p2) / sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    return 100 * (p1 - p2), 100 * (p1 - p2 - 1.96 * se), 100 * (p1 - p2 + 1.96 * se), erfc(abs(z) / sqrt(2))


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """One row per seller, version and price: the same car listed several times counts once."""
    return df.drop_duplicates(["seller", "variant", "price_azn"])


def statistical_checks(df: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    dd = dedupe(df)
    for label, data, cdata in [("all listings", df, comp), ("deduplicated", dd, dedupe(comp))]:
        n = len(data)
        for name, k in [("Chinese brands' share of listings", int((data["origin"] == "China").sum())),
                        ("Battery-electric share", int(data["electric"].sum()))]:
            lo, hi = wilson(k, n)
            rows.append({"check": f"{name} ({label})", "estimate": 100 * k / n, "ci_low": lo, "ci_high": hi,
                         "p_value": np.nan, "n": n})
        top15 = data["model_key"].value_counts().head(15).sum()
        rows.append({"check": f"Top-15 models' share of listings ({label})", "estimate": 100 * top15 / n,
                     "ci_low": np.nan, "ci_high": np.nan, "p_value": np.nan, "n": n})
        off, oth = cdata[cdata["seller_type"] == "Official dealer"], cdata[cdata["seller_type"] == "Other dealer"]
        for feat, name in [("promoted", "Paid promotion"), ("credit", "Credit offered")]:
            est, lo, hi, p = two_prop(int(off[feat].sum()), len(off), int(oth[feat].sum()), len(oth))
            rows.append({"check": f"{name}: official minus other dealers, pp ({label})", "estimate": est,
                         "ci_low": lo, "ci_high": hi, "p_value": p, "n": len(off) + len(oth)})
    print(f"duplicates removed: {len(df) - len(dd):,} of {len(df):,} listings")
    return pd.DataFrame(rows).set_index("check").round(4)


def listing_tactics(df: pd.DataFrame) -> pd.DataFrame:
    order = ["Official dealer", "Other dealer", "Private seller"]
    t = df.groupby("seller_type").agg(listings=("slug", "size"), promoted=("promoted", "mean"),
                                      credit=("credit", "mean"), on_order=("on_order", "mean")).reindex(order)
    for c in ["promoted", "credit", "on_order"]:
        t[c] = 100 * t[c]

    fig, axes = plt.subplots(1, 3, figsize=(16, 9), sharey=True)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.76, bottom=0.10, wspace=0.2)
    y = range(len(t))[::-1]
    for ax, (col, title) in zip(axes, [("promoted", "Paid promotion (VIP / Premium)"),
                                        ("credit", "Credit offered"), ("on_order", "Sold on order")]):
        ax.barh(list(y), t[col], color=[BLUE, NEUTRAL, NEUTRAL], height=0.6)
        ax.set_title(title, color=INK_2)
        ax.set_xlim(0, 115)
        bare_x(ax)
        for yi, v in zip(y, t[col]):
            ax.text(v + 2, yi, f"{v:.0f}%", va="center", fontsize=13, color=INK)
    axes[0].set_yticks(list(y), [f"{s}\n{n:,} listings" for s, n in zip(t.index, t["listings"])], fontsize=12)
    headline(fig, f"Official dealers pay to promote {t.loc['Official dealer', 'promoted']:.0f}% of their listings",
             "Share of listings with each feature, by seller type. Promotion is a marketing spend signal "
             "visible from outside.", len(df))
    save(fig, "05_listing_tactics.png")
    return t.round(1)


def promotion_vs_price(df: pd.DataFrame) -> pd.DataFrame:
    d = df[~df["price_estimated"].astype(bool) & (df["seller_type"] != "Private seller")].copy()
    d["rel_price"] = 100 * (d["price_azn"] / d.groupby("model_key")["price_azn"].transform("median") - 1)
    d = d[d.groupby("model_key")["slug"].transform("size") >= 10]
    t = d.groupby(["seller_type", "promoted"])["rel_price"].agg(["median", "size"]).round(1)
    return t


def electric_share(df: pd.DataFrame) -> pd.DataFrame:
    t = df.groupby("origin").agg(listings=("slug", "size"), electric=("electric", "mean"))
    t["electric_pct"] = 100 * t["electric"]
    t = t[t["listings"] >= 20].sort_values("electric_pct")

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.subplots_adjust(left=0.10, right=0.85, top=0.80, bottom=0.10)
    y = range(len(t))
    ax.barh(list(y), t["electric_pct"], color=[ORIGIN_COLORS[o] for o in t.index], height=0.6)
    ax.set_yticks(list(y), t.index, fontsize=13)
    bare_x(ax)
    ax.set_xlim(0, t["electric_pct"].max() * 1.3)
    for yi, (_, r) in zip(y, t.iterrows()):
        ax.text(r.electric_pct + 0.4, yi, f"{r.electric_pct:.1f}%  ({int(r.electric * r.listings)} of {int(r.listings)})",
                va="center", fontsize=12, color=INK_2)
    total = 100 * df["electric"].mean()
    headline(fig, f"Only {total:.1f}% of new-car listings are fully electric",
             "Listings without an engine volume (battery-electric). Plug-in and range-extender hybrids "
             "have an engine and are not counted here. Origins with 20+ listings.", len(df))
    save(fig, "06_electric_share.png")
    return t.round(1)


def main() -> None:
    df = load()
    comp = df[~df["employer_official"]]  # for seller-type and price comparisons
    OUT_DIR.mkdir(exist_ok=True)
    results = {
        "01_market_by_origin": market_by_origin(df),
        "02_top_models": top_models(df),
        "03_official_vs_other_dealers": official_vs_other(comp),
        "04_price_dispersion": price_dispersion(comp),
        "05_listing_tactics": listing_tactics(comp),
        "05b_promotion_vs_price": promotion_vs_price(comp),
        "06_electric_share": electric_share(df),
        "07_statistical_checks": statistical_checks(df, comp),
    }
    for name, t in results.items():
        t.to_csv(OUT_DIR / f"{name}.csv")
    print(f"passenger listings: {len(df):,} | brands: {df.brand.nunique()} | models: {df.model_key.nunique()}")
    for name, t in results.items():
        print(f"\n== {name}\n{t.to_string()}")


if __name__ == "__main__":
    main()
