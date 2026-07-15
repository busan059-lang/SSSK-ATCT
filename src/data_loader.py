"""라벨링된 종목토론방 CSV 로드 및 파생 컬럼(시각, 본문 길이) 생성."""

from pathlib import Path

import pandas as pd
import streamlit as st

REQUIRED_COLUMNS = {"nid", "title", "author", "date", "content", "sentiment"}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

DEFAULT_PATHS = {
    "삼성전자": DATA_DIR / "samsung_labeled.csv",
    "SK하이닉스": DATA_DIR / "hynix_labeled.csv",
}


def _enrich(df: pd.DataFrame, company: str) -> pd.DataFrame:
    df = df.copy()
    df["company"] = company

    if "content_clean" not in df.columns:
        df["content_clean"] = df["content"].astype(str)

    df["sentiment"] = df["sentiment"].astype(str).str.strip()
    df = df[df["sentiment"].isin(["찬티", "중립", "안티"])]

    df["date_parsed"] = pd.to_datetime(df["date"], format="%Y.%m.%d %H:%M", errors="coerce")
    df["hour"] = df["date_parsed"].dt.hour
    df["content_len"] = df["content_clean"].astype(str).str.len()

    return df


@st.cache_data(show_spinner=False)
def load_default_data() -> pd.DataFrame:
    frames = []
    for company, path in DEFAULT_PATHS.items():
        raw = pd.read_csv(path)
        frames.append(_enrich(raw, company))
    return pd.concat(frames, ignore_index=True)


def validate_columns(df: pd.DataFrame) -> list:
    missing = REQUIRED_COLUMNS - set(df.columns)
    return sorted(missing)
