##################################################
import os
import sys
import shutil
import pandas as pd
import numpy as np
import kneed
import matplotlib.pyplot as plt


def info(msg):
    return "{}{}{}".format("\033[96m", msg, "\033[0m")


def model_selection(
    diploid_objs: list,
    tetraploid_objs: list,
    wd: str,
    v=1,
):
    """
    1. per solution instance, compute likelihoods of observed RDR and BAF given CNP.
    2. select best solution based on elbow detection on likelihood curves.
    3. WGD ver no WGD by principle of parsimony.
    """

    def compute_expected_fcn(row, n):
        fcn = float(row["u_normal"]) * 2
        fcn_b = float(row["u_normal"])
        for nn in range(1, n):
            a, b = str(row[f"cn_clone{nn}"]).split("|")
            a = int(a)
            b = int(b)
            fcn += float(row[f"u_clone{nn}"]) * (a + b)
            fcn_b += float(row[f"u_clone{nn}"]) * b
        return [fcn, fcn_b]

    def ll_gauss_profile(res, floor_rss=1e-12):
        n = res.size
        if n == 0:
            return 0.0
        rss = float(np.sum(res * res))
        rss = max(rss, floor_rss)
        return -0.5 * n * (1.0 + np.log(2 * np.pi) + np.log(rss / n))

    if len(diploid_objs) == 0 and len(tetraploid_objs) == 0:
        raise ValueError(
            "ERROR! no solution found for either diploid or tetraploid setting!"
        )

    sys.stdout.write(info("Model selection\n"))

    ploidy2scores = {}
    for [ploidy, ploidy_objs] in [
        ["diploid", diploid_objs],
        ["tetraploid", tetraploid_objs],
    ]:
        if len(ploidy_objs) == 0:
            sys.stdout.write(info(f"no {ploidy} solutions\n"))
            continue

        ploidy_objs_add1 = [
            (1, (np.inf, ploidy_objs[0][1][1]), ploidy_objs[0][-1])
        ] + ploidy_objs
        ns = []
        lls = []
        for n, (obj, gamma), outprefix in ploidy_objs_add1:
            n = int(n)
            bbcs = pd.read_table(f"{outprefix}.bbc.ucn.tsv", sep="\t")
            if n > 1:
                bbcs[["exp-FCN", "exp-FCN-b"]] = bbcs.apply(
                    func=lambda r: compute_expected_fcn(r, n),
                    axis=1,
                    result_type="expand",
                )
            else:
                bbcs["exp-FCN"] = 2.0
                bbcs["exp-FCN-b"] = 1.0
            ll = 0.0
            for (cluster_id, sample_id), bbc_sub in bbcs.groupby(
                by=["CLUSTER", "SAMPLE"], sort=False
            ):
                obs_fcns = bbc_sub["RD"].to_numpy() * float(gamma.loc[sample_id])
                obs_bafs = bbc_sub["BAF"].to_numpy()
                exp_fcns = bbc_sub["exp-FCN"].to_numpy()
                exp_fcns_b = bbc_sub["exp-FCN-b"].to_numpy()
                exp_bafs = np.divide(
                    exp_fcns_b,
                    exp_fcns,
                    where=exp_fcns > 0,
                    out=np.full(len(bbc_sub), 0.5),
                )

                res_fcns = obs_fcns - exp_fcns
                ll_fcn = ll_gauss_profile(res_fcns[np.isfinite(res_fcns)])
                res_bafs = obs_bafs - exp_bafs
                ll_baf = ll_gauss_profile(res_bafs[np.isfinite(res_bafs)])
                ll += ll_fcn + ll_baf
            ns.append(n)
            lls.append(ll)
            if v > 0:
                sys.stdout.write(info(f"{ploidy}: n={n}, obj={obj}, loglik={ll}\n"))
        chosen_n = ns[1]  # first n>1 solution
        ns = np.array(ns, dtype=np.int32)
        neg_lls = -1 * np.array(lls)
        if len(ns) > 2:
            kl_negll = kneed.KneeLocator(
                x=ns, y=neg_lls, curve="convex", direction="decreasing"
            )
            chosen_n_negll = (
                int(kl_negll.elbow) if kl_negll.elbow is not None else ns[0]
            )
            chosen_n = max(ns[1], chosen_n_negll)

        sys.stdout.write(info(f"{ploidy}: choose n={chosen_n}\n"))
        chosen_outprefix = [
            outprefix for n, _, outprefix in ploidy_objs if int(n) == chosen_n
        ][0]
        ploidy2scores[ploidy] = [chosen_n, ns, neg_lls]
        # save chosen sol
        out_bbc = os.path.join(wd, f"chosen.{ploidy}.bbc.ucn")
        out_seg = os.path.join(wd, f"chosen.{ploidy}.seg.ucn")
        shutil.copy2(f"{chosen_outprefix}.bbc.ucn.tsv", out_bbc)
        shutil.copy2(f"{chosen_outprefix}.seg.ucn.tsv", out_seg)

    # choose ploidy by parsimony of clones
    final_ploidy = min(ploidy2scores.keys(), key=lambda p: ploidy2scores[p][0])
    final_n = ploidy2scores[final_ploidy][0]
    sys.stdout.write(
        info(f"final model selection: ploidy={final_ploidy}, n={final_n}\n")
    )

    # plot model-selections
    decision = "chosen: "
    fig = plt.figure(figsize=(4, 3))
    if "diploid" in ploidy2scores:
        plt.plot(
            ploidy2scores["diploid"][1],
            ploidy2scores["diploid"][2],
            marker="o",
            label="Diploid",
        )
        n = ploidy2scores["diploid"][0]
        decision += f"diploid_n{n};"
    if "tetraploid" in ploidy2scores:
        plt.plot(
            ploidy2scores["tetraploid"][1],
            ploidy2scores["tetraploid"][2],
            marker="o",
            label="Tetraploid",
        )
        n = ploidy2scores["tetraploid"][0]
        decision += f"tetraploid_n{n};"
    decision += f"\nfinal_decision: {final_ploidy}_n{final_n}"
    plt.xlabel("#clones")
    plt.ylabel("neg-loglik")
    plt.title(f"elbow curve\n{decision}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(wd, "elbow_curve.png"), dpi=100)
    plt.close(fig)

    # save final selected solutions
    shutil.copy2(
        os.path.join(wd, f"chosen.{final_ploidy}.bbc.ucn"),
        os.path.join(wd, "best.bbc.ucn"),
    )
    shutil.copy2(
        os.path.join(wd, f"chosen.{final_ploidy}.seg.ucn"),
        os.path.join(wd, "best.seg.ucn"),
    )

    return final_ploidy, final_n, ploidy2scores
