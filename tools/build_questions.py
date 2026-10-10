# -*- coding: utf-8 -*-
"""Tạo data/hcm202.json từ file Word ngân hàng câu hỏi HCM202.

Định dạng trong file Word:
  #Câu hỏi …
  A. đáp án            (có thể viết thường a. b. c.; đôi khi "B. … C. …" trên cùng một dòng)
  D. đáp án cuối@      (dấu @ đánh dấu hết phần đáp án)
  A                    (chữ cái của đáp án đúng; "A, B" nếu nhiều đáp án)
  (Kiểu hỏi khác: …) / =>…   (ghi chú cách hỏi khác)
  #(Kiểu hỏi khác: …)  (khối có đáp án riêng = một câu hỏi diễn đạt lại câu trước)

Chạy: python tools/build_questions.py "C:/duong/dan/HCM202.docx"
"""
import html
import json
import os
import re
import sys
import zipfile
from collections import Counter, OrderedDict

OPT = re.compile(r"^([A-Ha-h])\s*[.)]\s*(.*)$")
INLINE = re.compile(r"\s+([B-H])\.\s+")
ANS = re.compile(r"^([A-Ha-h](?:\s*[,;&]?\s*[A-Ha-h])*)\s*\.?$")
# Tên / số điện thoại người đóng góp kèm trong câu: (NHUNG HOÀNG), (073-356-8678)
NOISE = re.compile(r"\s*\((?:[A-ZĐÀ-Ỹ][A-ZĐÀ-Ỹ ]{3,}|[\d\-. ]{8,})\)\s*")
ALT = re.compile(r"^\(?(?:Kiểu|Câu) hỏi khác", re.I)
ALT_PREFIX = re.compile(r"^\(?(?:Kiểu|Câu) hỏi khác\s*[:;]\s*", re.I)


def read_lines(path):
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    body = xml[xml.index("<w:body>"):]
    out = []
    for chunk in body.split("</w:p>"):
        t = "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", chunk))
        t = html.unescape(t).replace("\u00a0", " ").strip()
        if t:
            out.append(t)
    return out


def balance(s):
    """Bỏ ngoặc mở/đóng lẻ ở đầu/cuối (sót lại từ ghi chú trong tài liệu)."""
    s = s.strip()
    if s.startswith("(") and s.count("(") > s.count(")"):
        s = s[1:].strip()
    if s.endswith(")") and s.count(")") > s.count("("):
        s = s[:-1].strip()
    return s


def clean(s):
    s = NOISE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return balance(s)


def parse(lines):
    blocks, cur = [], None
    for ln in lines:
        if ln.startswith("#"):
            cur = [ln[1:].strip()]
            blocks.append(cur)
        elif cur is not None:
            cur.append(ln)

    questions = []
    for b in blocks:
        head, i = [], 0
        while i < len(b) and not OPT.match(b[i]):
            head.append(b[i])
            i += 1
        is_alt = False
        if head and ALT.match(head[0]):
            if len(head) == 1:
                head[0] = ALT_PREFIX.sub("", head[0])
                is_alt = True
            elif questions:
                questions[-1]["notes"].append("Kiểu hỏi khác: " + clean(ALT_PREFIX.sub("", head.pop(0))))
        opts, answer, notes, last = OrderedDict(), None, [], None
        while i < len(b):
            ln = b[i]
            m = OPT.match(ln)
            if m and answer is None and len(ln) > 2:
                text = m.group(2)
                seg = INLINE.split(text)
                opts[m.group(1).upper()] = seg[0]
                for k in range(1, len(seg) - 1, 2):
                    opts[seg[k]] = seg[k + 1]
                last = list(opts)[-1]
            elif answer is None and opts and ANS.match(ln):
                answer = sorted(set(re.findall(r"[A-H]", ln.upper())))
            elif opts and answer is None and last:
                opts[last] += " " + ln
            else:
                notes.append(ln)
            i += 1
        q = clean(" ".join(head))
        if not q or len(opts) < 2:
            continue
        options = {k: clean(v.rstrip().rstrip("@").strip().strip('"')) for k, v in opts.items()}
        options = {k: v for k, v in options.items() if v}
        if answer and not set(answer) <= set(options):
            answer = None
        note = " ".join(clean(n) for n in notes if clean(n))
        note = ALT_PREFIX.sub("Kiểu hỏi khác: ", note)
        note = re.sub(r"\s*\(?(?:Kiểu|Câu) hỏi khác\s*[:;]\s*", " · Kiểu hỏi khác: ", note).strip(" ·")
        note = note.replace("=>", "→").replace(")", "").strip()
        nl = [note] if note else []
        if is_alt:
            nl.insert(0, "Đây là một cách hỏi khác của câu trước.")
        questions.append({"question": q, "options": options, "answers": answer or [], "notes": nl})

    # gộp câu trùng (cùng câu hỏi + cùng bộ đáp án)
    seen, out = {}, []
    for q in questions:
        norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()
        key = (norm(q["question"]), tuple(sorted(norm(v) for v in q["options"].values())))
        if key in seen:
            if not seen[key]["answers"] and q["answers"]:
                seen[key]["answers"] = q["answers"]
            continue
        seen[key] = q
        out.append(q)
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit('Cách dùng: python tools/build_questions.py "HCM202.docx"')
    qs = parse(read_lines(sys.argv[1]))
    items = []
    for i, q in enumerate(qs, 1):
        ans = q["answers"]
        expl = (
            "Đáp án đúng: " + "; ".join(f"{a}. {q['options'][a]}" for a in ans) + "."
            if ans
            else "Tài liệu gốc chưa ghi đáp án cho câu này."
        )
        items.append(
            {
                "id": i,
                "type": "mcq",
                "question": q["question"],
                "options": q["options"],
                "answers": ans,
                "choose": max(1, len(ans)),
                "note": " ".join(q["notes"]) or None,
                "alt": None,
                "explanation": expl,
                "exam": "HCM202",
            }
        )
    data = {
        "title": "HCM202 – Tư tưởng Hồ Chí Minh",
        "code": "HCM202",
        "subject": "HCM202",
        "total": len(items),
        "questions": items,
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "hcm202.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    c = Counter(len(x["answers"]) for x in items)
    print(f"{len(items)} câu -> {os.path.normpath(out)}; không có đáp án: {c[0]}, nhiều đáp án: {sum(v for k, v in c.items() if k > 1)}")


if __name__ == "__main__":
    main()
