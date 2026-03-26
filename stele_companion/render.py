# -*- coding: utf-8 -*-
"""
HTML 渲染模块 - 横版/竖版 HTML 输出
"""

import json
import sys
import html as html_mod

from .utils import (
    PUNCTUATION,
    THEME_COLORS,
    log_err,
    log_ok,
    log_info,
    log_step,
)


def render_html(
    annotated_path,
    output_path,
    format_type="horizontal",
    font_size="medium",
    theme="classic",
):
    """
    将标注数据渲染为 HTML。

    format_type:
      - horizontal : 横版（现代阅读顺序，左→右，A4纵向）
      - vertical    : 竖版（古文阅读顺序，上→下，右→左，A4横向）

    font_size:
      - small  : 22px（紧凑打印）
      - medium : 28px（默认，学习友好）
      - large  : 34px（大字体，老年友好）

    theme:
      - classic : 金色系（#fff3a0 淡黄底）
      - elegant : 红色系（#fde8e8 淡红底）
    """

    log_step(f"Phase 3: 渲染 HTML ({format_type})")
    log_info(f"加载标注数据: {annotated_path}")

    try:
        with open(annotated_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        log_err(f"标注文件 JSON 格式错误: {annotated_path}")
        log_err(f"  错误: {e}")
        sys.exit(1)
    except Exception as e:
        log_err(f"读取标注文件失败: {annotated_path}")
        log_err(f"  错误: {e}")
        sys.exit(1)

    if format_type == "horizontal":
        html = _render_horizontal(data, font_size, theme)
    else:
        html = _render_vertical(data, font_size, theme)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    log_ok(f"HTML 已生成: {output_path}")
    if format_type == "horizontal":
        log_info(f"提示: 浏览器打开后，Ctrl+P 打印 → A4 纵向，勾选「背景图形」")
    else:
        log_info(f"提示: 浏览器打开后，Ctrl+P 打印 → A4 横向，勾选「背景图形」")


def _font_size_css(size):
    s = {"small": "22px", "medium": "28px", "large": "34px"}.get(size, "28px")
    lh = {"small": "7.2mm", "medium": "8.5mm", "large": "10.2mm"}.get(size, "8.5mm")
    cid = {"small": "7px", "medium": "8px", "large": "10px"}.get(size, "8px")
    return s, lh, cid


def _render_horizontal(data, font_size="medium", theme="classic"):
    """渲染横版 HTML（现代阅读顺序）"""

    fs, lh, cid = _font_size_css(font_size)
    tc = THEME_COLORS.get(theme, THEME_COLORS["classic"])
    pg_color = tc["matched_bg_print"]

    # CSS
    css = f"""
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: "SimSun", "Songti SC", "Noto Serif CJK SC", serif;
        background: #f5f5f5;
        padding: 20px;
    }}
    .page {{
        width: 210mm;
        min-height: 297mm;
        padding: 15mm 15mm;
        margin: 0 auto 20px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        page-break-after: always;
    }}
    .page:last-child {{ page-break-after: avoid; }}
    .page-header {{
        height: 10mm;
        margin-bottom: 4mm;
        text-align: center;
        border-bottom: 0.5px solid #ddd;
        font-size: 9pt;
        color: #666;
        line-height: 10mm;
    }}
    .content {{
        display: flex;
        flex-wrap: wrap;
        gap: 5.0mm 1.0mm;
        align-content: flex-start;
        padding-bottom: 8mm;
    }}
    .char-wrap {{
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        vertical-align: top;
    }}
    .char, .punct {{
        font-size: {fs};
        line-height: {lh};
    }}
    .char.matched {{
        padding: 0 2px;
        margin: 0 -2px;
        background: linear-gradient(to bottom, {tc["matched_bg_end"]}, {tc["matched_bg"]});
        border-radius: 2px;
    }}
    .char.ztb {{
        /* 在字典中找到的字 */
        padding: 0 2px;
        margin: 0 -2px;
    }}
    .label {{
        font-size: {cid};
        color: {tc["char_id_color"]};
        font-family: Arial, sans-serif;
        white-space: nowrap;
        line-height: 1;
        pointer-events: none;
        margin-top: -2px;
    }}
    .punct {{
        color: #555;
    }}
    .char-id {{ display: none; }}
    .para-break {{
        width: 100%;
        height: 6mm;
        border-bottom: 0.5px dashed #ccc;
        margin: 2mm 0;
    }}
    .section-break {{
        width: 100%;
        border-bottom: 1px solid #bbb;
        padding: 4mm 0 2mm 0;
        margin-bottom: 3mm;
        text-align: center;
    }}
    .section-name {{
        font-size: 18pt;
        letter-spacing: 3px;
        color: #444;
    }}

    .stats {{
        max-width: 210mm;
        margin: 20px auto;
        padding: 15px;
        background: white;
        font-size: 10pt;
        color: #666;
        border-radius: 4px;
    }}
    .legend {{
        max-width: 210mm;
        margin: 10px auto;
        padding: 10px 15px;
        background: white;
        font-size: 9pt;
        color: #555;
        border-radius: 4px;
    }}
    .legend-item {{
        display: inline-block;
        margin-right: 16px;
    }}
    .legend-dot {{
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 2px;
        margin-right: 4px;
        vertical-align: middle;
    }}
    @media print {{
        @page {{ size: A4 portrait; margin: 5mm; }}
        body {{ background: white; padding: 0; }}
        .page {{ margin: 0; box-shadow: none; padding: 15mm 15mm; page-break-after: always; }}
        .page:last-child {{ page-break-after: avoid; }}
        .content {{ padding-bottom: 6mm; }}
        .char-wrap {{ overflow: visible; }}
        .stats, .legend {{ display: none; }}
        .para-break {{ border-bottom-color: #999; }}
        .char.matched {{
            background: {pg_color} !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
    }}
    """

    # 生成图例
    legend_html = '<div class="legend"><b>图例：</b>'
    for di in data.get("dicts", []):
        source_name = html_mod.escape(di.get("source", "字典"))
        legend_html += (
            f'<span class="legend-item">'
            f'<span class="legend-dot" style="background:{di["color"]};color:{di["color"]}"> </span>'
            f"{source_name}（{di.get('matched_count', 0)}字）"
            f"</span>"
        )
    if data.get("shared_chars"):
        shared_color_name = html_mod.escape(data.get("shared_color_name", "深紫色"))
        legend_html += (
            f'<span class="legend-item">'
            f'<span class="legend-dot" style="background:{data["shared_color"]};color:{data["shared_color"]}"> </span>'
            f"{shared_color_name}（{data['stats'].get('shared_count', 0)}字，共有字）"
            f"</span>"
        )
    legend_html += "</div>"

    # 生成正文
    content_parts = []
    for pi, para in enumerate(data["paragraphs"]):
        is_main = para.get("is_main", True)

        # 非主段（标题/开头）→ 居中大字 section-break + 正文开始时的分隔
        if not is_main:
            para_text = "".join(
                html_mod.escape(ci["char"])
                for ci in para["chars"]
                if not ci["char"].isspace() and ci["char"] not in PUNCTUATION
            )
            content_parts.append(
                f'<div class="section-break">'
                f'<span class="section-name">{para_text}</span>'
                f"</div>"
            )
            # 标题和正文之间加分隔
            content_parts.append('<div class="para-break"></div>')
            continue

        # 正文段落：inline 渲染
        for ci in para["chars"]:
            char = ci["char"]
            if char.isspace():
                continue

            if char in PUNCTUATION:
                content_parts.append(
                    f'<span class="punct">{html_mod.escape(char)}</span>'
                )
                continue

            if ci["matched"]:
                labels = ci.get("labels", [])
                if labels:
                    primary_color = labels[0]["color"]
                    label_text = " ".join(lb["label"] for lb in labels)
                    is_shared = len(labels) > 1
                    color_style = (
                        f"background:{data['shared_color']}"
                        if is_shared
                        else f"background: linear-gradient(to bottom, {primary_color}22, {primary_color}11)"
                    )
                    char_cls = "char matched"
                    content_parts.append(
                        f'<span class="char-wrap">'
                        f'<span class="{char_cls}" style="{color_style}">{html_mod.escape(char)}</span>'
                        f'<span class="label" style="color:{primary_color if not is_shared else data["shared_color"]}">{label_text}</span>'
                        f"</span>"
                    )
                else:
                    content_parts.append(
                        f'<span class="char matched">{html_mod.escape(char)}</span>'
                    )
            else:
                content_parts.append(
                    f'<span class="char">{html_mod.escape(char)}</span>'
                )

        # 段落分隔
        content_parts.append('<div class="para-break"></div>')

    content_html = "".join(content_parts)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{html_mod.escape(data["source"])} - 横版标注</title>
<style>{css}</style>
</head>
<body>
{legend_html}
<div class="page">
<div class="page-header">{html_mod.escape(data["source"])}</div>
<div class="content">{content_html}</div>
</div>
<div class="stats">
<p><b>来源：</b>{html_mod.escape(data["source"])} | <b>字典：</b>{", ".join(html_mod.escape(d.get("source", p)) for d, p in zip(data.get("dicts", []), data.get("dict_paths", [])))}</p>
<p><b>总字数：</b>{data["stats"]["total"]} | <b>已匹配：</b>{data["stats"]["matched"]} ({data["stats"]["match_rate"]}){f" | <b>共有字：</b>{data["stats"]["shared_count"]} ({data["stats"]["shared_rate"]})" if data.get("shared_chars") else ""}</p>
</div>
</body>
</html>"""
    return html


def _render_vertical(data, font_size="medium", theme="classic"):
    """渲染竖版 HTML（古文阅读顺序）"""

    fs, lh, cid = _font_size_css(font_size)
    tc = THEME_COLORS.get(theme, THEME_COLORS["classic"])
    pg_color = tc["matched_bg_print"]

    css = f"""
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: "SimSun", "Songti SC", "Noto Serif CJK SC", serif;
        background: #f5f5f5;
        padding: 15px;
    }}
    .page {{
        width: 297mm;
        min-height: 200mm;
        padding: 10mm 4mm 10mm 4mm;
        margin: 0 auto 20px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        page-break-after: always;
    }}
    .page:last-child {{ page-break-after: avoid; }}
    .page-header {{
        display: none;
    }}
    .vertical-content {{
        display: flex;
        flex-direction: row-reverse;
        justify-content: flex-start;
        gap: 6.0mm;
    }}
    .col {{
        display: inline-flex;
        flex-direction: column;
        gap: 1.0mm;
        align-items: center;
    }}
    .char-wrap {{
        display: inline;
        position: relative;
    }}
    .char, .punct {{
        font-size: {fs};
        line-height: {lh};
        display: inline;
    }}
    .char.matched {{
        padding: 0 2px;
        margin: 0 -2px;
        background: linear-gradient(to bottom, {tc["matched_bg_end"]}, {tc["matched_bg"]});
        border-radius: 2px;
    }}
    .char.ztb {{}}
    .label {{
        position: absolute;
        font-size: {cid};
        color: {tc["char_id_color"]};
        font-family: Arial, sans-serif;
        bottom: -3px;
        left: 50%;
        transform: translateX(-50%);
        white-space: nowrap;
        line-height: 1;
        pointer-events: none;
    }}
    .punct {{
        color: #555;
        writing-mode: vertical-rl;
        text-orientation: upright;
    }}
    .para-separator {{
        display: inline-block;
        min-width: 3mm;
        border-left: 1px dashed #bbb;
        margin: 0 1mm;
    }}
    .char-id {{ display: none; }}
    .stats {{
        max-width: 297mm;
        margin: 20px auto;
        padding: 15px;
        background: white;
        font-size: 10pt;
        color: #666;
        border-radius: 4px;
    }}
    .legend {{
        max-width: 297mm;
        margin: 10px auto;
        padding: 10px 15px;
        background: white;
        font-size: 9pt;
        color: #555;
        border-radius: 4px;
    }}
    .legend-item {{
        display: inline-block;
        margin-right: 16px;
    }}
    .legend-dot {{
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 2px;
        margin-right: 4px;
        vertical-align: middle;
    }}
    @media print {{
        @page {{ size: A4 landscape; margin: 5mm; }}
        body {{ background: white; padding: 0; }}
        .page {{ margin: 0; box-shadow: none; padding: 10mm 4mm 10mm 4mm; min-height: auto; page-break-after: always; }}
        .page:last-child {{ page-break-after: avoid; }}
        .stats, .legend {{ display: none; }}
        .char.matched {{
            background: {pg_color} !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        .para-separator {{ border-left-color: #999; }}
    }}
    """

    # 生成图例
    legend_html = '<div class="legend"><b>图例：</b>'
    for di in data.get("dicts", []):
        source_name = html_mod.escape(di.get("source", "字典"))
        legend_html += (
            f'<span class="legend-item">'
            f'<span class="legend-dot" style="background:{di["color"]};color:{di["color"]}"> </span>'
            f"{source_name}（{di.get('matched_count', 0)}字）"
            f"</span>"
        )
    if data.get("shared_chars"):
        shared_color_name = html_mod.escape(data.get("shared_color_name", "深紫色"))
        legend_html += (
            f'<span class="legend-item">'
            f'<span class="legend-dot" style="background:{data["shared_color"]};color:{data["shared_color"]}"> </span>'
            f"{shared_color_name}（{data['stats'].get('shared_count', 0)}字，共有字）"
            f"</span>"
        )
    legend_html += "</div>"

    # 分列（竖排从右到左，每列从上到下）
    CHARS_PER_COL = 19
    columns = []
    paragraphs = data["paragraphs"]
    for pi, para in enumerate(paragraphs):
        para_chars = [ci for ci in para["chars"] if not ci["char"].isspace()]
        current_col = []
        for ci in para_chars:
            char = ci["char"]
            if char in PUNCTUATION:
                current_col.append(("punct", char, ci))
            else:
                current_col.append(("char", char, ci))
            if len(current_col) >= CHARS_PER_COL:
                columns.append(current_col)
                current_col = []
        # 段落结束：追加剩余字符
        if current_col:
            columns.append(current_col)
        # 段落之间加分隔列
        if pi < len(paragraphs) - 1:
            columns.append(None)

    # 过滤掉最后的空列
    while columns and columns[-1] is None:
        columns.pop()

    # 分页（每页20列）
    COLS_PER_PAGE = 20
    pages = []
    current_page = []
    for col in columns:
        current_page.append(col)
        if len(current_page) >= COLS_PER_PAGE:
            pages.append(current_page)
            current_page = []
    if current_page:
        pages.append(current_page)

    # 生成每页 HTML
    page_parts = []
    for page_idx, page_cols in enumerate(pages, 1):
        col_htmls = []
        for col in page_cols:
            # 分隔列
            if col is None:
                col_htmls.append('<div class="para-separator"></div>')
                continue

            cell_htmls = []
            for cell_type, char, ci in col:
                if cell_type == "punct":
                    cell_htmls.append(
                        f'<span class="punct">{html_mod.escape(char)}</span>'
                    )
                elif ci["matched"]:
                    labels = ci.get("labels", [])
                    if labels:
                        primary_color = labels[0]["color"]
                        label_text = " ".join(lb["label"] for lb in labels)
                        is_shared = len(labels) > 1
                        color_style = (
                            f"background:{data['shared_color']}"
                            if is_shared
                            else f"background: linear-gradient(to bottom, {primary_color}22, {primary_color}11)"
                        )
                        cell_htmls.append(
                            f'<span class="char-wrap">'
                            f'<span class="char matched" style="{color_style}">{html_mod.escape(char)}</span>'
                            f'<span class="label" style="color:{primary_color if not is_shared else data["shared_color"]}">{label_text}</span>'
                            f"</span>"
                        )
                    else:
                        cell_htmls.append(
                            f'<span class="char matched">{html_mod.escape(char)}</span>'
                        )
                else:
                    cell_htmls.append(
                        f'<span class="char">{html_mod.escape(char)}</span>'
                    )

            col_htmls.append('<div class="col">' + "".join(cell_htmls) + "</div>")

        page_parts.append(
            f'<div class="page">'
            f'<div class="page-header">{data["source"]} - 第 {page_idx} 页 / 共 {len(pages)} 页</div>'
            f'<div class="vertical-content">' + "".join(col_htmls) + f"</div></div>"
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{html_mod.escape(data["source"])} - 竖版标注</title>
<style>{css}</style>
</head>
<body>
{legend_html}
{"".join(page_parts)}
<div class="stats">
<p><b>来源：</b>{html_mod.escape(data["source"])} | <b>字典：</b>{", ".join(html_mod.escape(d.get("source", p)) for d, p in zip(data.get("dicts", []), data.get("dict_paths", [])))}</p>
<p><b>总字数：</b>{data["stats"]["total"]} | <b>已匹配：</b>{data["stats"]["matched"]} ({data["stats"]["match_rate"]}){f" | <b>共有字：</b>{data["stats"]["shared_count"]} ({data["stats"]["shared_rate"]})" if data.get("shared_chars") else ""} | <b>总页数：</b>{len(pages)}</p>
</div>
</body>
</html>"""
    return html
