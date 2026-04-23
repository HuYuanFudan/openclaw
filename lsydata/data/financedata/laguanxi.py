import ast
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple

import pandas as pd
from tqdm.auto import tqdm

# ============================================================
# 1) 路径配置
# ============================================================

INPUT_DIR = Path("/home/lushiyin/data/financedata/完整_已知实体匹配")
OUTPUT_DIR = Path("/home/lushiyin/data/financedata/完整_已知实体匹配_关系预测结果1")

# 新增：全局已处理头尾实体记录文件（忽略头尾顺序）
DONE_CSV_PATH = Path("/home/lushiyin/data/financedata/完整_已知实体匹配_关系预测结果/头尾实体.csv")

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:32b"
OLLAMA_TIMEOUT = 600

RELATIONS = [
    "无关系",
    "子公司",
    "起诉",
    "客户",
    "供应商",
    "担保",
    "质押"
]

MAX_ROWS_PER_FILE = None
MAX_EVIDENCE_CHARS = 4096


# ============================================================
# 2) Ollama 检查
# ============================================================

def check_ollama_available(host: str, model_name: str):
    tags_url = f"{host}/api/tags"
    resp = requests.get(tags_url, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    models = data.get("models", [])
    model_names = [m.get("name", "") for m in models]

    if model_name not in model_names:
        raise ValueError(
            f"Ollama 中未找到模型 {model_name}。\n"
            f"当前可用模型：{model_names}"
        )


# ============================================================
# 3) 工具函数
# ============================================================

def safe_text(x) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()


def normalize_name(x: str) -> str:
    x = safe_text(x)
    x = re.sub(r"\s+", "", x)
    x = x.replace("(", "（").replace(")", "）")
    return x


def parse_entity_list(cell) -> List[str]:
    if isinstance(cell, list):
        return [safe_text(x) for x in cell if safe_text(x)]

    s = safe_text(cell)
    if not s or s.lower() == "nan":
        return []

    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, (list, tuple, set)):
            return [safe_text(x) for x in obj if safe_text(x)]
    except Exception:
        pass

    parts = re.split(r"[;,；，、|/]", s)
    return [p.strip().strip('"').strip("'") for p in parts if p.strip()]


def dedupe_keep_order(items: List[str]) -> List[str]:
    out = []
    seen = set()
    for x in items:
        x = safe_text(x)
        if not x:
            continue
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def truncate_evidence(text: str, max_chars: int = MAX_EVIDENCE_CHARS) -> str:
    text = safe_text(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def build_pair_key(a: str, b: str) -> Tuple[str, str]:
    """
    无向实体对：
    (A, B) 和 (B, A) 视为同一个 key
    """
    a_norm = normalize_name(a)
    b_norm = normalize_name(b)
    return tuple(sorted([a_norm, b_norm]))


def load_existing_pairs_ignore_order(done_csv_path: Path) -> Set[Tuple[str, str]]:
    """
    从 done_csv_path 中读取 ['head_entity', 'tail_entity']，
    构造成忽略头尾顺序的实体对集合
    """
    existing_pairs = set()

    if not done_csv_path.exists():
        return existing_pairs

    df_old = None
    for enc in ["utf-8-sig", "utf-8", "gb18030", "gbk"]:
        try:
            df_old = pd.read_csv(done_csv_path, encoding=enc)
            break
        except Exception:
            continue

    if df_old is None or df_old.empty:
        return existing_pairs

    if "head_entity" not in df_old.columns or "tail_entity" not in df_old.columns:
        raise ValueError(f"{done_csv_path} 缺少列 ['head_entity', 'tail_entity']")

    for _, row in df_old.iterrows():
        head = row.get("head_entity", "")
        tail = row.get("tail_entity", "")
        head_norm = normalize_name(head)
        tail_norm = normalize_name(tail)

        if head_norm and tail_norm:
            existing_pairs.add(build_pair_key(head_norm, tail_norm))

    return existing_pairs


def append_done_pair(done_csv_path: Path, head: str, tail: str):
    """
    实时追加一条已处理实体对到 done_csv_path
    """
    done_csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_first_write = not done_csv_path.exists()

    row_df = pd.DataFrame([{
        "head_entity": head,
        "tail_entity": tail
    }])

    row_df.to_csv(
        done_csv_path,
        mode="w" if is_first_write else "a",
        header=is_first_write,
        index=False,
        encoding="utf-8-sig"
    )


def get_evidence_from_row(row) -> str:
    """
    clean_body 为空时，用 merged_text 代替
    """
    clean_body = safe_text(row.get("clean_body", ""))
    if clean_body:
        return clean_body

    merged_text = safe_text(row.get("merged_text", ""))
    return merged_text


# ============================================================
# 4) Prompt 与预测
# ============================================================

def build_prompt(head: str, tail: str, evidence: str, relations: List[str]) -> str:
    prompt = f"""你是金融领域的关系分类专家，专门判断两家企业之间存在何种关系。根据给定证据，从候选关系中，选择两企业之间的关系

任务：
根据给定证据，判断“企业 A”和“企业 B”之间最可能的关系。

要求：
1. 只能从候选关系列表中选择一个，可能存在多种关系，但要求输出最相关的，候选关系的排列顺序不代表概率高低；
2. 只能输出一个数字编号；
3. 不要输出解释、分析过程或其他文字；
4. 如果证据不足、关系不明确，输出“无关系”对应的编号；
5. 不要因为头实体和尾实体同时出现在证据中，就强行判断为存在关系。

企业 A：{head}
企业 B：{tail}

候选关系及解释如下：
1.无关系：企业 A 与企业 B 没有关系 或 企业 A 与企业 B 不符合以下关系
2.子公司：企业 A 是企业 B 的子公司
3.起诉：企业 A 与企业 B 有司法诉讼关系
4.客户：企业 A 是企业 B 的客户
5.供应商：企业 A 是企业 B 的供应商
6.担保：企业 A 为企业 B 在某件事情上做担保
7.质押：企业 A 质押资产给企业 B

证据：
{evidence}

答案编号："""
    return prompt


def parse_relation_from_output(output_text: str, relations: List[str]) -> str:
    m = re.search(r"\d+", output_text)
    if m:
        idx = int(m.group()) - 1
        if 0 <= idx < len(relations):
            return relations[idx]
    return "无关系"


def predict_relation(
    head: str,
    tail: str,
    evidence: str,
    relations: List[str],
    host: str,
    model_name: str,
) -> Dict[str, str]:
    evidence = truncate_evidence(evidence)
    prompt = build_prompt(head, tail, evidence, relations)

    url = f"{host}/api/chat"
    payload = {
        "model": model_name,
        "stream": False,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "options": {
            "temperature": 0,
            "num_predict": 8
        },
        "keep_alive": "10m"
    }

    resp = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    raw_answer = data.get("message", {}).get("content", "").strip()
    pred_relation = parse_relation_from_output(raw_answer, relations)

    return {
        "pred_relation": pred_relation,
        "raw_model_output": raw_answer
    }


# ============================================================
# 5) 单个 CSV 处理：按实体对展开
# ============================================================

def append_row_to_csv(row_dict: dict, output_path: Path, is_first_write: bool):
    row_df = pd.DataFrame([row_dict])
    row_df.to_csv(
        output_path,
        mode="w" if is_first_write else "a",
        header=is_first_write,
        index=False,
        encoding="utf-8-sig"
    )


def process_one_csv(
    csv_path: Path,
    output_path: Path,
    done_csv_path: Path,
    relations: List[str],
    max_rows: Optional[int] = None
) -> int:
    df = None
    for enc in ["utf-8-sig", "utf-8", "gb18030", "gbk"]:
        try:
            df = pd.read_csv(csv_path, encoding=enc, nrows=max_rows)
            break
        except Exception:
            continue

    if df is None:
        raise ValueError(f"读取失败：{csv_path}")

    required_cols = ["系统匹配公司名称", "已知实体匹配"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"{csv_path.name} 缺少列：{col}")

    # 注意：clean_body 不再强制要求存在；如果空则回退 merged_text
    if "clean_body" not in df.columns and "merged_text" not in df.columns:
        raise ValueError(f"{csv_path.name} 至少需要包含 clean_body 或 merged_text 其中之一")

    # 从 done_csv_path 读取已处理实体对（忽略头尾顺序）
    existing_pairs = load_existing_pairs_ignore_order(done_csv_path)

    # 当前输出文件是否第一次写入
    is_first_write = not output_path.exists()

    write_count = 0

    iterator = tqdm(
        df.iterrows(),
        total=len(df),
        desc=f"处理 {csv_path.name}",
        ncols=100
    )

    for _, row in iterator:
        head = safe_text(row["系统匹配公司名称"])

        # 证据：clean_body 为空时，用 merged_text 代替
        evidence = get_evidence_from_row(row)

        tails = parse_entity_list(row["已知实体匹配"])
        tails = dedupe_keep_order(tails)

        # 1) 系统匹配公司名称为空 -> 跳过
        if not head:
            continue

        # 2) 已知实体匹配为空 -> 跳过
        if not tails:
            continue

        # 去掉和 head 相同的实体；如果只剩自己，也跳过
        head_norm = normalize_name(head)
        tails = [t for t in tails if normalize_name(t) and normalize_name(t) != head_norm]
        if not tails:
            continue

        # 这里不再用 clean_body 是否为空做筛选
        # 但如果 clean_body 和 merged_text 都取不到，模型也没法跑，所以这里兜底跳过
        if not evidence:
            continue

        for tail in tails:
            pair_key = build_pair_key(head, tail)

            # 已做过的实体对，忽略头尾顺序
            if pair_key in existing_pairs:
                continue
            # print(f"开始推理: head={head} | tail={tail} | evidence_len={len(evidence)}")

            pred = predict_relation(
                head=head,
                tail=tail,
                evidence=evidence,
                relations=relations,
                host=OLLAMA_HOST,
                model_name=OLLAMA_MODEL
            )
            
            new_row = row.to_dict()
            new_row["head_entity"] = head
            new_row["tail_entity"] = tail
            new_row["evidence"] = evidence
            new_row["pred_relation"] = pred["pred_relation"]
            new_row["raw_model_output"] = pred["raw_model_output"]

            append_row_to_csv(
                row_dict=new_row,
                output_path=output_path,
                is_first_write=is_first_write
            )
            is_first_write = False

            # 实时更新 done_csv_path
            append_done_pair(done_csv_path, head, tail)

            # 内存集合也同步更新，避免同一轮内重复
            existing_pairs.add(pair_key)

            write_count += 1

    return write_count


# ============================================================
# 6) 批量处理整个文件夹
# ============================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DONE_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(INPUT_DIR.glob("*.csv"))
    if not csv_files:
        print(f"未找到 csv 文件：{INPUT_DIR}")
        return

    print("检查 Ollama 服务与模型中...")
    check_ollama_available(OLLAMA_HOST, OLLAMA_MODEL)
    print("Ollama 模型可用。")

    for csv_path in csv_files:
        try:
            output_path = OUTPUT_DIR / f"{csv_path.stem}_关系预测.csv"

            write_count = process_one_csv(
                csv_path=csv_path,
                output_path=output_path,
                done_csv_path=DONE_CSV_PATH,
                relations=RELATIONS,
                max_rows=MAX_ROWS_PER_FILE
            )

            print(f"完成：{csv_path.name} -> {output_path.name}，共 {write_count} 条实体对记录")

        except Exception as e:
            print(f"处理失败：{csv_path.name}，错误：{e}")


if __name__ == "__main__":
    main()