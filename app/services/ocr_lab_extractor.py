#!/usr/bin/env python3
"""
Combined OCR + Lab Report Extractor

- OCR pipeline (pdfplumber + Tesseract via pdf2image/Poppler)
- Parsing/output schema inspired by a multilingual lab-extractor

This is used as a fallback when the standard extraction returns no results.
"""

import json
import os
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import logging

import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------- OCR helpers ----------------------------

def conda_bin_path() -> Optional[Path]:
    prefix = os.environ.get("CONDA_PREFIX")
    if prefix:
        cand = Path(prefix) / "Library" / "bin"
        if cand.exists():
            return cand
    return None


def guess_tesseract_path() -> Optional[str]:
    """Find Tesseract executable path (cross-platform)"""
    import platform
    
    # Check conda environment first
    cbin = conda_bin_path()
    if cbin:
        tesseract_name = "tesseract.exe" if platform.system() == "Windows" else "tesseract"
        t = cbin / tesseract_name
        if t.exists():
            return str(t)
    
    # Windows-specific paths
    if platform.system() == "Windows":
        for p in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]:
            if Path(p).exists():
                return p
    
    # Linux/Unix paths
    elif platform.system() in ["Linux", "Darwin"]:
        for p in [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",  # macOS with Homebrew
        ]:
            if Path(p).exists():
                return p
    
    # Fallback to system PATH
    return shutil.which("tesseract")


def guess_poppler_bin() -> Optional[str]:
    """Find Poppler bin directory (cross-platform)"""
    import platform
    
    # Check conda environment first
    cbin = conda_bin_path()
    if cbin:
        pdftoppm_name = "pdftoppm.exe" if platform.system() == "Windows" else "pdftoppm"
        if (cbin / pdftoppm_name).exists():
            return str(cbin)
    
    # Try to find pdftoppm in system PATH
    ppm = shutil.which("pdftoppm")
    if ppm:
        return str(Path(ppm).parent)
    
    # Windows-specific paths
    if platform.system() == "Windows":
        for p in [
            r"C:\poppler-25.07.0\Library\bin",
            r"C:\Program Files\poppler\Library\bin",
            r"C:\Program Files (x86)\poppler\Library\bin",
            r"C:\poppler\Library\bin",
        ]:
            if Path(p).exists():
                return p
    
    # Linux/Unix paths - Poppler tools are usually in standard bin directories
    elif platform.system() in ["Linux", "Darwin"]:
        for p in [
            "/usr/bin",
            "/usr/local/bin",
            "/opt/homebrew/bin",  # macOS with Homebrew
        ]:
            if Path(p).exists() and (Path(p) / "pdftoppm").exists():
                return p
    
    return None


def extract_with_pdfplumber(pdf_path: Path) -> List[Dict[str, Any]]:
    pages_out = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            embedded = page.extract_text() or ""
            has_images = bool(getattr(page, "images", []))
            pages_out.append(
                {
                    "page_number": idx,
                    "embedded_text": embedded,
                    "has_images_flag": has_images,
                }
            )
    return pages_out


def combine_text(embedded: str, ocr_text: str) -> str:
    embedded = (embedded or "").strip()
    ocr_text = (ocr_text or "").strip()
    if embedded and ocr_text:
        if " ".join(embedded.split()).lower() != " ".join(ocr_text.split()).lower():
            return f"{embedded}\n\n---\n[OCR]\n{ocr_text}"
        return embedded
    return embedded or ocr_text


def get_combined_pages_text(
    pdf_path: Path,
    dpi: int = 220,
    lang: str = "por+eng+spa",
    psm: int = 6,
    oem: int = 1,
    poppler_path: Optional[str] = None,
    first_page: Optional[int] = None,
    last_page: Optional[int] = None,
    ocr_mode: str = "auto",
) -> List[str]:
    """
    Return combined text per page, ensuring page 1 is always included.
    - auto: OCR only pages with weak/no embedded text or with images
    - all: OCR all pages
    - none: never OCR (embedded text only)
    """
    embedded_results = extract_with_pdfplumber(pdf_path)

    # Determine pages (1-based) to process
    total_pages = len(embedded_results)
    start = first_page or 1
    end = last_page or total_pages
    pages_idx = list(range(start, end + 1))

    def need_ocr(entry: Dict[str, Any]) -> bool:
        text = (entry.get("embedded_text") or "").strip()
        has_images = bool(entry.get("has_images_flag"))
        # Heuristic: very short or empty text, or page with images likely scanned
        return (len(text) < 80) or has_images

    pages_to_ocr = set()
    if ocr_mode == "all":
        pages_to_ocr = set(pages_idx)
    elif ocr_mode == "auto":
        for i in pages_idx:
            entry = embedded_results[i - 1]
            if need_ocr(entry):
                pages_to_ocr.add(i)
    else:  # none
        pages_to_ocr = set()

    # OCR selected pages and map back by index
    ocr_text_by_page: Dict[int, str] = {}
    if pages_to_ocr:
        ranges: List[Tuple[int, int]] = []
        sorted_pages = sorted(pages_to_ocr)
        s = e = sorted_pages[0]
        for p in sorted_pages[1:]:
            if p == e + 1:
                e = p
            else:
                ranges.append((s, e))
                s = e = p
        ranges.append((s, e))

        cfg = f"--psm {psm} --oem {oem}"
        for (s, e) in ranges:
            images: List[Image.Image] = convert_from_path(
                str(pdf_path),
                dpi=dpi,
                fmt="png",
                poppler_path=poppler_path,
                first_page=s,
                last_page=e,
            )
            for offset, img in enumerate(images):
                page_no = s + offset
                txt = pytesseract.image_to_string(img, lang=lang, config=cfg)
                ocr_text_by_page[page_no] = (txt or "").replace("\r\n", "\n")

    # Combine page-by-page
    pages: List[str] = []
    for i in pages_idx:
        embedded = embedded_results[i - 1]["embedded_text"] if i - 1 < len(embedded_results) else ""
        ocr_text = ocr_text_by_page.get(i, "")
        if ocr_mode == "none":
            combined = embedded
        elif i in pages_to_ocr:
            combined = combine_text(embedded, ocr_text)
        else:
            combined = embedded
        pages.append(combined)
    return pages


# ---------------------------- Parser helpers ----------------------------

SUPERS = "⁰¹²³⁴⁵⁶⁷⁸⁹"

def strip_accents(s: str) -> str:
    if not s:
        return s
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s: str) -> str:
    return strip_accents(s or "").lower().strip()


def normalize_units(s: str) -> str:
    if not s:
        return s
    s = s.replace("\u00a0", " ")
    for bad, good in [
        ("x109 / L", "x10^9/L"),
        ("x10 9 / L", "x10^9/L"),
        ("x109/ L", "x10^9/L"),
        ("x109 /L", "x10^9/L"),
        ("x 109 / L", "x10^9/L"),
        (" / ", "/"),
    ]:
        s = s.replace(bad, good)
    s = re.sub(r"x\s*10\s*\^?\s*9(?:\s*/\s*L)?", "x10^9/L", s, flags=re.IGNORECASE)
    s = re.sub(r"x\s*109(?:\s*/\s*L)?", "x10^9/L", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def protect_x10_units(s: str) -> str:
    return re.sub(r"x\s*10[\^¹²³]?\s*\d*\s*/?\s*[A-Za-zµ/]+", "xTEN", s)


UNIT_ABS = (
    r"(?:"
    r"x\s*10(?:\^?\s*\d+|[" + SUPERS + r"]+)(?:/L)?|"
    r"g/dL|mg/dL|mmol/L|µmol/L|μmol/L|nmol/L|pmol/L|ng/mL|pg/mL|mIU/L|mUI/L|UI/L|U/L|/µL|/uL|/L|fL|pg|mEq/L|seg\."
    r")"
)
UNIT_ANY = rf"(?:{UNIT_ABS}|%)"

VALUE_WITH_UNIT_RE = re.compile(rf"(?:^|\s)(?P<val>[<>]=?\s*\d[\d.,]*)\s*(?P<u>{UNIT_ANY})\b")
RANGE_OR_CMP_RE = re.compile(r"(?:[\d.,]+\s*-\s*[\d.,]+|[<>]=?\s*[\d.,]+)")

MULTI_DATE_RE = re.compile(
    r"\b(?:(?P<d1>\d{2})[./-](?P<m1>\d{2})[./-](?P<y1>\d{2,4})|(?P<y2>\d{4})[./-](?P<m2>\d{2})[./-](?P<d2>\d{2}))\b"
)

TEXT_VALUE_PATTERNS = [
    r"Não\s+revelou(?:\s*\([^)]+\))?", r"Nao\s+revelou(?:\s*\([^)]+\))?",
    r"No\s+revel[oó]", r"No\s+detectado", r"No\s+se\s+detect[oó]", r"Ausente",
    r"Presente", r"Presencia", r"Presenza", r"Prezent",
    r"Raros(?:\s*\([^)]+\))?", r"Escasos", r"Pocos", r"Occasionali?",
    r"Vest[ií]gios", r"Vestigios", r"Tracce", r"Urme",
    r"Límpid[ao]", r"Limpid[eo]", r"Claro", r"Clara", r"Chiaro",
    r"Amarela(?:\s+clara)?", r"Amarill[oa]", r"Giallo", r"Galben[ăa]?",
    r"Negativo", r"Positivo",
    r"Not\s+detected", r"None\s+detected", r"Absent", r"Present",
    r"Rare", r"Few", r"Occasional",
    r"Trace(?:s)?", r"Traces?", r"Spur(?:e|en)?", r"Spor", r"Spår", r"Ślad(?:y)?",
    r"Clear", r"Limpid", r"Clair", r"Klar", r"Helder", r"Bistr[ăa]?",
    r"Yellow", r"Jaune", r"Gelb", r"Geel", r"Gul", r"Żółty",
    r"Negativ(?:e|o|t)?", r"Positiv(?:e|o|t)?",
]
TEXT_VALUE_RE = re.compile("|".join(TEXT_VALUE_PATTERNS), re.IGNORECASE)

HIST_VALUE_RE = re.compile(
    r"(?:"
    + TEXT_VALUE_RE.pattern
    + r"|(?:[<>]=?\s*)?[\d.,]+(?:\s*/\s*(?:campo|field|HPF))?)",
    re.IGNORECASE,
)

META_NAME_RE = re.compile(
    r"^(?:"
    r"hospital|clin(?:ic|iqu)e|cl[ií]nica|krankenhaus|klin(?:ik|ika)|"
    r"lab(?:or(?:atorio|atoire|oratorium)|or)|laborat[óo]rio|laboratuvar|"
    r"tel(?:ephone|efo[oó]n|[eé]fono|efon|efonnummer)?|tlf\.?|telefon|téléphone|"
    r"www\.|http|https|e-?mail|correo|mail|email|"
    r"data\b|fecha\b|date\b|datum\b|dato\b"
    r")",
    re.IGNORECASE,
)

START_BLOCKLIST = tuple(
    norm(s)
    for s in [
        "Referência",
        "Referência normal",
        "Insuficiência:",
        "Recomendações",
        "Recomendações:",
        "PHEV",
        "Deficiência",
        "Deficiência:",
    ]
)


def is_blocklisted_line(raw: str) -> bool:
    if not raw:
        return False
    r = norm(raw).strip()
    for prefix in START_BLOCKLIST:
        if r.startswith(prefix):
            return True
    return False


def is_blocklisted_metric_name(name: str) -> bool:
    n = norm(name)
    n = re.sub(r"[:\s]+$", "", n)
    if n in {"deficiencia"}:
        return True
    blocked_substrings = [
        "(met", "tarde", "manha", "manana", "afternoon", "morning",
        "insuficien", "insufficien", "insuffizien", "insufficienz",
    ]
    return any(k in n for k in blocked_substrings)


# ---------------------------- Dates ----------------------------

def canonicalize_date(ds: Any) -> str:
    if isinstance(ds, tuple):
        s = next((x for x in ds if x), "")
    else:
        s = str(ds or "")
    if not s:
        return ""
    m = MULTI_DATE_RE.search(s)
    if not m:
        return s
    if m.group("y2"):
        y = int(m.group("y2"))
        mo = int(m.group("m2"))
        d = int(m.group("d2"))
    else:
        d = int(m.group("d1"))
        mo = int(m.group("m1"))
        y = int(m.group("y1"))
        if y < 100:
            y += 2000 if y < 50 else 1900
    try:
        return f"{d:02d}-{mo:02d}-{y:04d}"
    except Exception:
        return s


DATE_LABELS = [
    r"data\s+colheita", r"data\s+da\s+colheita", r"data\s+do\s+relat[oó]rio",
    r"fecha\s+de\s+extracci[oó]n", r"fecha\s+del?\s+informe",
    r"collection\s+date", r"report\s+date", r"result\s+date",
]


def extract_report_date(first_page_text: str, full_text: str) -> str:
    t = norm(first_page_text)
    for lbl in DATE_LABELS:
        for m in re.finditer(lbl, t, flags=re.IGNORECASE):
            start = max(0, m.end())
            window = first_page_text[start: start + 160]
            md = MULTI_DATE_RE.search(window)
            if md:
                return canonicalize_date(md.group(0))
    md = MULTI_DATE_RE.search(first_page_text)
    if md:
        return canonicalize_date(md.group(0))
    md = MULTI_DATE_RE.search(full_text)
    return canonicalize_date(md.group(0)) if md else ""


# ---------------------------- Name splitters ----------------------------

def split_name_and_tail_safe(line: str) -> Tuple[Optional[str], Optional[str]]:
    m_val = VALUE_WITH_UNIT_RE.search(line)
    if m_val:
        idx = m_val.start()
        return line[:idx].strip().lstrip("-:•·").strip(), line[idx:].strip()

    m_text = TEXT_VALUE_RE.search(line)
    if m_text:
        idx = m_text.start()
        return line[:idx].strip().lstrip("-:•·").strip(), line[idx:].strip()

    m_num = re.search(r"[<>]?\s*\d", line)
    if m_num:
        tail = line[m_num.start():]
        if VALUE_WITH_UNIT_RE.search(tail) or RANGE_OR_CMP_RE.search(tail):
            return line[: m_num.start()].strip().lstrip("-:•·").strip(), line[m_num.start():].strip()

    return None, None


def pick_central_from_left(left: str):
    cand_re = re.compile(rf"(?P<val>[<>]?\s*[\d.,]+)\s*(?P<unit>{UNIT_ANY})?")
    cands = list(cand_re.finditer(left))
    if not cands:
        return None, None
    for m in cands:
        u = (m.group("unit") or "").strip()
        if u and re.fullmatch(UNIT_ABS, u):
            val = m.group("val").replace(" ", "").replace(",", ".")
            return val, normalize_units(u)
    m = cands[0]
    val = m.group("val").replace(" ", "").replace(",", ".")
    return val, normalize_units((m.group("unit") or "").strip())


# ---------------------------- Parse helpers ----------------------------

def parse_numeric_metric_line(line: str, page_hist_dates: List[str], report_date: str):
    line = normalize_units(line)
    if is_blocklisted_line(line):
        return None

    name, tail = split_name_and_tail_safe(line)

    if not name:
        return None

    if is_blocklisted_metric_name(name):
        return None

    nl = norm(name)
    if META_NAME_RE.search(name) or nl.startswith("exmo") or nl.startswith("hfe"):
        return None

    tail_clean = protect_x10_units(tail or "")

    mref = None
    last_range = None
    for m in re.finditer(r"[\d.,]+\s*-\s*[\d.,]+", tail_clean):
        last_range = m
    if last_range:
        mref = last_range
    else:
        last_cmp = None
        for m in re.finditer(r"[<>]=?\s*[\d.,]+", tail_clean):
            last_cmp = m
        if last_cmp:
            mref = last_cmp

    if mref:
        left = tail_clean[: mref.start()].strip()
        reference = (mref.group(0) or "").strip()
        right = tail_clean[mref.end():].strip()
        left_original = (tail or "")[: mref.start()].strip()
    else:
        left = tail_clean
        right = ""
        reference = ""
        left_original = (tail or "")

    central_val, central_unit = pick_central_from_left(left_original)
    if not central_val:
        return None

    right_vals = [h.strip() for h in HIST_VALUE_RE.findall(right)]
    left_vals = []
    for m in HIST_VALUE_RE.finditer(left):
        tok = m.group(0).strip()
        if tok.replace(" ", "").replace(",", ".") == central_val:
            continue
        if reference and tok in reference:
            continue
        left_vals.append(tok)
    hist_vals = right_vals if right_vals else left_vals

    rows = [{
        "metric_name": name,
        "date_of_value": report_date,
        "value": central_val,
        "unit": central_unit or "",
        "reference": reference,
    }]

    if hist_vals and page_hist_dates:
        for i, hv in enumerate(hist_vals[:2]):
            if i < len(page_hist_dates):
                rows.append({
                    "metric_name": name,
                    "date_of_value": page_hist_dates[i],
                    "value": hv,
                    "unit": central_unit or "",
                    "reference": reference,
                })
    return rows


def parse_urine_metric_line(line: str, report_date: str, page_hist_dates: List[str]):
    if is_blocklisted_line(line):
        return None

    name, tail = split_name_and_tail_safe(line)

    if not name or not tail:
        return None

    if is_blocklisted_metric_name(name):
        return None

    nl = norm(name)
    if META_NAME_RE.search(name) or nl.startswith("exmo") or nl.startswith("hfe"):
        return None

    all_texts = [m.group(0).strip() for m in TEXT_VALUE_RE.finditer(tail)]
    if not all_texts:
        return None

    central_val = all_texts[0]
    hist_vals = all_texts[1:]

    rows = [{
        "metric_name": name,
        "date_of_value": report_date,
        "value": central_val,
        "unit": "",
        "reference": "",
    }]

    if hist_vals and page_hist_dates:
        for i, hv in enumerate(hist_vals[:2]):
            if i < len(page_hist_dates):
                rows.append({
                    "metric_name": name,
                    "date_of_value": page_hist_dates[i],
                    "value": hv,
                    "unit": "",
                    "reference": "",
                })
    return rows


# ---------------------------- Section detection ----------------------------

def detect_type(line: str, current_type: str) -> str:
    t = norm(line)
    if any(k in t for k in [
        "hematolog", "hemograma", "hematologe", "hématolog", "hämatolog", "ematolog"
    ]):
        return "HEMATOLOGIA"
    if any(k in t for k in [
        "bioquim", "biochim", "biochem", "biokem", "biokjem", "biochemie"
    ]):
        return "BIOQUIMICA"
    if any(k in t for k in [
        "urina", "urine", "urin ", "urin-", "urinalys", "urinaliz"
    ]):
        return "URINA E DOSEAMENTOS URINÁRIOS"
    return current_type


# ---------------------------- Core parse ----------------------------

def parse_from_pages(pages_text: List[str], lab_override: str = "") -> List[Dict]:
    """Parse lab data from OCR-extracted pages"""
    
    full_text = "\n".join(pages_text)
    first_page = pages_text[0] if pages_text else ""

    report_date = extract_report_date(first_page, full_text)

    # Best-effort lab name
    lab_name = ""
    try:
        lab_name = next((l for l in full_text.splitlines() if "labor" in norm(l)), "")
    except Exception:
        pass
    if lab_override:
        lab_name = lab_override

    records: List[Dict] = []
    current_type = ""

    for page_text in pages_text:
        if not page_text:
            continue

        page_dates = [canonicalize_date(m.group(0)) for m in MULTI_DATE_RE.finditer(page_text)]
        page_hist_dates = [d for d in page_dates if d and d != report_date][-2:]

        raw_lines = [normalize_units(l) for l in page_text.splitlines() if l.strip()]
        last_metric_name = ""

        for raw in raw_lines:
            if is_blocklisted_line(raw):
                continue

            current_type = detect_type(raw, current_type)

            if META_NAME_RE.search(raw.strip(": ").strip()):
                continue

            rowset = parse_numeric_metric_line(raw, page_hist_dates, report_date)

            if not rowset and current_type == "URINA E DOSEAMENTOS URINÁRIOS":
                rowset = parse_urine_metric_line(raw, report_date, page_hist_dates)

            if not rowset:
                if last_metric_name and re.search(r"\d", raw) and not is_blocklisted_line(last_metric_name):
                    combo = f"{last_metric_name} {raw}"
                    rowset = parse_numeric_metric_line(combo, page_hist_dates, report_date)
                if not rowset and (re.search(r"[A-Za-zÁ-úÀ-ÿ]+", raw) and not re.search(r"\d", raw) and len(raw) < 100):
                    candidate = raw.strip(': ').strip()
                    cn = norm(candidate)
                    if not META_NAME_RE.search(candidate) and re.search(r"[(:,)]", candidate) and not (cn.startswith("exmo") or cn.startswith("hfe")):
                        last_metric_name = candidate
                    else:
                        last_metric_name = ""
            else:
                last_metric_name = ""

            if rowset:
                for r in rowset:
                    out = {
                        "lab_name": lab_name or "",
                        "type_of_analysis": current_type,
                        **r,
                    }
                    records.append(out)

    # Deduplicate
    seen = set()
    deduped = []
    for r in records:
        key = (r["type_of_analysis"], r["metric_name"], r["date_of_value"], r["value"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    return deduped


# ---------------------------- Main extraction function ----------------------------

def extract_lab_data_with_ocr(pdf_bytes: bytes, filename: str) -> List[Dict]:
    """
    Extract lab data from PDF using OCR fallback.
    
    Args:
        pdf_bytes: PDF file content as bytes
        filename: Original filename
        
    Returns:
        List of extracted lab records
    """
    try:
        import platform
        system = platform.system()
        
        # Configure Tesseract
        tesseract_path = guess_tesseract_path()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            install_cmd = {
                "Linux": "sudo apt-get install tesseract-ocr tesseract-ocr-por tesseract-ocr-spa tesseract-ocr-eng",
                "Darwin": "brew install tesseract tesseract-lang",
                "Windows": "Download from: https://github.com/UB-Mannheim/tesseract/wiki"
            }
            cmd = install_cmd.get(system, "Install Tesseract-OCR")
            logger.error(f"Tesseract-OCR not found. Install: {cmd}")
            raise RuntimeError(f"Tesseract-OCR not found. {cmd}")
            
        poppler_bin = guess_poppler_bin()
        if not poppler_bin:
            install_cmd = {
                "Linux": "sudo apt-get install poppler-utils",
                "Darwin": "brew install poppler",
                "Windows": "Download from: https://github.com/oschwartz10612/poppler-windows/releases"
            }
            cmd = install_cmd.get(system, "Install Poppler")
            logger.error(f"Poppler not found. Install: {cmd}")
            raise RuntimeError(f"Poppler not found. {cmd}")
        
        # Save bytes to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = Path(tmp_file.name)
        
        try:
            # Extract text with OCR
            pages_text = get_combined_pages_text(
                pdf_path=tmp_path,
                dpi=220,
                lang="por+eng+spa",
                psm=6,
                oem=1,
                poppler_path=poppler_bin,
                first_page=None,
                last_page=None,
                ocr_mode="auto",
            )
            
            # Parse the extracted text
            data = parse_from_pages(pages_text, lab_override="")
            
            logger.info(f"OCR extraction completed: {len(data)} records found")
            return data
            
        finally:
            # Clean up temporary file
            try:
                tmp_path.unlink()
            except Exception:
                pass
                
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return []

