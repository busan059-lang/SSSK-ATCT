"""차트 색상/스타일 상수 (dataviz 스킬의 검증된 카테고리 팔레트에서 발췌)."""

import streamlit as st

SENTIMENT_ORDER = ["찬티", "중립", "안티"]

# 국내 주식시장 관례(상승=적색, 하락=청색)에 맞춘 매핑. 두 값 모두
# dataviz 스킬 팔레트의 diverging pair(blue<->red) + 중립 gray에서 그대로 사용.
SENTIMENT_COLORS = {
    "찬티": "#e34948",   # red
    "중립": "#9a988f",   # neutral gray
    "안티": "#2a78d6",   # blue
}

COMPANIES = ["삼성전자", "SK하이닉스"]

# 감성 색상과 겹치지 않도록 카테고리 팔레트의 다른 슬롯(violet / orange)을 사용
COMPANY_COLORS = {
    "삼성전자": "#4a3aa7",     # violet
    "SK하이닉스": "#eb6834",  # orange
}


def plotly_layout_kwargs():
    """Streamlit 라이트/다크 테마에 맞춰 plotly 차트 배경/폰트 색을 맞춘다."""
    base = st.get_option("theme.base") or "light"
    if base == "dark":
        return dict(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA", family="system-ui, -apple-system, 'Segoe UI', sans-serif"),
        )
    return dict(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#31333F", family="system-ui, -apple-system, 'Segoe UI', sans-serif"),
    )


def style_fig(fig, height=None, legend=True, hovermode="closest"):
    fig.update_layout(
        **plotly_layout_kwargs(),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
        if legend
        else dict(),
        showlegend=legend,
        hovermode=hovermode,
    )
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(gridcolor="rgba(128,128,128,0.15)", zerolinecolor="rgba(128,128,128,0.3)")
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)", zerolinecolor="rgba(128,128,128,0.3)")
    return fig
