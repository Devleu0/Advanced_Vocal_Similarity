"""database/ 의 영상별 임베딩으로 파이프라인 품질을 평가합니다.

사용법: python evaluate.py [--db database]
설정(config.py)을 바꾼 뒤 임베딩을 다시 추출하고 이 스크립트로 전/후를 비교하세요.
"""
import argparse
import glob
import os

import torch

import config
from evaluation import evaluate


def load_embeddings(db_dir):
    embs, labels, names = [], [], []
    for adir in sorted(d for d in glob.glob(os.path.join(db_dir, "*")) if os.path.isdir(d)):
        files = sorted(glob.glob(os.path.join(adir, "emb_*.pt")))
        if not files:
            continue
        names.append(os.path.basename(adir))
        for f in files:
            embs.append(torch.load(f, weights_only=True))
            labels.append(len(names) - 1)
    return (torch.stack(embs), torch.tensor(labels), names) if embs else (None, None, names)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=config.DB_DIR)
    args = parser.parse_args()

    embs, labels, names = load_embeddings(args.db)
    if embs is None:
        print("임베딩이 없습니다. 먼저 main.py 를 실행하세요.")
        return
    print(f"아티스트 {len(names)}명, 영상 {len(embs)}개")
    print(f"{'setting':10s} {'EER↓':>7s} {'top1-acc↑':>10s} {'intra':>7s} {'inter':>7s} {'gap↑':>7s}")
    for center in (False, True):
        m = evaluate(embs, labels, center=center)
        tag = "centered" if center else "raw"
        print(f"{tag:10s} {m['eer']:7.3f} {m['accuracy']:10.3f} "
              f"{m['intra']:7.3f} {m['inter']:7.3f} {m['gap']:7.3f}")


if __name__ == "__main__":
    main()
