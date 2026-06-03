import json
import re
from pathlib import Path
from typing import Any

from config import settings

# 扩展情绪标签（兼容旧版 happy/calm/sad）
VALID_EMOTIONS = (
    "happy",
    "calm",
    "sad",
    "melancholy",
    "possessive",
    "cold",
    "gentle",
)
_EMOTION_PATTERN = "|".join(VALID_EMOTIONS)
_EMOTION_RE = re.compile(rf"\[emotion:({_EMOTION_PATTERN})\]\s*$", re.IGNORECASE)
_MOOD_DELTA_RE = re.compile(r"\[mood_delta:([+-]?\d+)\]\s*", re.IGNORECASE)

_MOOD_OUTPUT_INSTRUCTION = (
    "【氛围标记】根据本轮对话氛围，在末行 [emotion:…] 之后另起标记 [mood_delta:+N] 或 [mood_delta:-N]（N 为 1~10 整数）。"
    "博士哄你开心、体谅你时给正数；冒犯、冷漠、威胁时给负数。"
    "禁止在对白里提及好感度、开心度、红包、状态栏；标记仅供系统读取。"
)

_TAG_THINK = "think"
_TAG_REDACTED = "redacted_thinking"
_OPEN_THINK = "<" + _TAG_THINK + ">"
_CLOSE_THINK = "</" + _TAG_THINK + ">"
_REDACTED_OPEN = "<" + _TAG_REDACTED + ">"
_REDACTED_CLOSE = "</" + _TAG_REDACTED + ">"

# 情绪 -> 声音复刻 2.0 的 <cot> 自然语言指令（语气/神态/心理）
EMOTION_COT_HINTS: dict[str, str] = {
    "happy": "用轻快、略带笑意的语气",
    "calm": "用平静、沉静的语气，语速平稳",
    "sad": "用低沉、略带哀伤的语气，像在压抑情绪",
    "melancholy": "用忧郁、克制的语气，轻轻叹息",
    "possessive": "用轻柔而偏执的语气，像低声呢喃",
    "cold": "用冷淡、疏离的语气，句子短促",
    "gentle": "用温柔、轻声的语气，像在安慰对方",
}

# 情绪 -> 语音合成 1.0 的 audio_params.emotion（官方英文代号）
EMOTION_TTS1: dict[str, str] = {
    "happy": "happy",
    "calm": "happy",
    "sad": "sad",
    "melancholy": "sad",
    "possessive": "excited",
    "cold": "hate",
    "gentle": "happy",
}

# 单向 HTTP 官方格式：<cot text="情感描述">对白</cot>
_COT_TEXT_ATTR_RE = re.compile(
    r"<cot\s+text\s*=\s*[\"']([^\"']*)[\"']\s*>(.*?)</cot>",
    re.DOTALL | re.IGNORECASE,
)
# 旧式 / 双流式：<cot>描述</cot>对白
_COT_LEGACY_RE = re.compile(
    r"<cot>\s*(.*?)\s*</cot>",
    re.DOTALL | re.IGNORECASE,
)
_COT_TAG_RE = re.compile(
    r"<cot\s+text\s*=\s*[\"'][^\"']*[\"']\s*>.*?</cot>\s*|<cot>.*?</cot>\s*",
    re.DOTALL | re.IGNORECASE,
)
# 双流式内联标签 {{"additions":...} }}（末尾 }} 前有空格）
_BRACE_TAG_RE = re.compile(r"\{\{.*?\}\s*\}\s*\}?\s*", re.DOTALL)
_TTS_COT_META_RE = re.compile(r"\[tts_cot:(.*?)\]\s*$", re.DOTALL | re.IGNORECASE)
# 动作/环境旁白：仅全角（）（经 normalize_roleplay_brackets 统一）
_PAREN_ASIDE_RE = re.compile(r"（([^）]*)）")
# 引号/书名号类括号（不含 ASCII [ ]，避免误伤 [emotion:] 等控制标记）
_QUOTE_BRACKET_RE = re.compile(
    r"[「『【［《〈]([^」』】］》〉]*)[」』】］》〉]"
)
_HALF_PAREN_RE = re.compile(r"\(([^()]{1,50})\)")
_COT_TEXT_ATTR_OPEN_RE = re.compile(
    r"<cot\s+text\s*=\s*[\"']([^\"']*)[\"']\s*>",
    re.IGNORECASE,
)
_COT_CLOSE_RE = re.compile(r"</cot>\s*", re.IGNORECASE)

# 情绪 -> TTS 语速微调（数值越小语速越慢）
EMOTION_SPEED_DELTA = {
    "happy": 0.05,
    "calm": 0.0,
    "sad": -0.08,
    "melancholy": -0.07,
    "possessive": -0.04,
    "cold": -0.05,
    "gentle": -0.03,
}

# 红蒂：用户话语 -> 模式推断关键词
_RED_PLEAD_KEYWORDS = (
    "逃", "离开", "走", "怕", "害怕", "危险", "别过来", "放开", "滚", "远离", "别碰",
)
_RED_GENTLE_KEYWORDS = (
    "留", "陪", "海里", "血亲", "一起", "别走", "回家", "同化", "大群", "永远",
    "再说", "真的", "认真", "骗", "一遍",
)

# 蓝蒂：用户话语 -> 模式推断
_BLUE_VULNERABLE_KEYWORDS = (
    "幽灵鲨", "歌蕾蒂娅", "同伴", "担心", "对不起", "弥补", "愧疚", "难过", "累", "休息",
)
_BLUE_COLD_KEYWORDS = (
    "海嗣", "同化", "大群", "血亲", "神", "伊莎玛拉",
)


def load_personas() -> list[dict[str, Any]]:
    path = settings.personas_path
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_persona(persona_id: str) -> dict[str, Any] | None:
    for p in load_personas():
        if p["id"] == persona_id:
            return p
    personas = load_personas()
    return personas[0] if personas else None


def strip_think_tags(text: str) -> str:
    for open_tag, close_tag in (
        (_OPEN_THINK, _CLOSE_THINK),
        (_REDACTED_OPEN, _REDACTED_CLOSE),
    ):
        while open_tag in text and close_tag in text:
            start = text.find(open_tag)
            end = text.find(close_tag, start)
            if end == -1:
                break
            text = text[:start] + text[end + len(close_tag) :]
    return text.strip()


def _escape_cot_attr(value: str) -> str:
    return value.replace('"', "").replace("\n", " ").strip()[:40]


def normalize_roleplay_brackets(text: str) -> str:
    """
    统一为全角旁白括号（…）：LLM 若写了「」、半角 () 等，转为（），
    内容由 extract_paren_asides 剥离后仅写入气泡下方 stage，不送入 TTS。
    """
    if not text:
        return text
    t = _QUOTE_BRACKET_RE.sub(r"（\1）", text)
    t = _HALF_PAREN_RE.sub(r"（\1）", t)
    return t


def extract_paren_asides(text: str) -> tuple[str, list[str]]:
    """剥离全角（）旁白：净对白供 TTS/气泡正文，旁白列表供 stage 展示。"""
    asides = [m.group(1).strip() for m in _PAREN_ASIDE_RE.finditer(text) if m.group(1).strip()]
    cleaned = _PAREN_ASIDE_RE.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned, asides


def merge_stage_caption(tone: str, asides: list[str]) -> str:
    """合并语气（cot）与括号旁白，供气泡下方一行展示。"""
    parts: list[str] = []
    if tone.strip():
        parts.append(tone.strip())
    for a in asides:
        s = a.strip()
        if s and s not in parts:
            parts.append(s)
    return " · ".join(parts)


def extract_stage_directions(text: str, emotion: str = "calm") -> str:
    """从 <cot text="…">、旧式 <cot>、全角（）旁白提取神态，供聊天气泡下方展示。"""
    text = normalize_roleplay_brackets(strip_think_tags(text))
    tone_parts = re.findall(
        r"<cot\s+text\s*=\s*[\"']([^\"']*)[\"']",
        text,
        re.IGNORECASE,
    )
    tone_parts.extend(
        re.findall(r"<cot>\s*(.*?)\s*</cot>", text, re.IGNORECASE | re.DOTALL)
    )
    m = _TTS_COT_META_RE.search(text + "\n")
    if m:
        tone_parts.append(m.group(1).strip())
    tone = " · ".join(p.strip() for p in tone_parts if p and p.strip())
    asides = [
        m.group(1).strip()
        for m in _PAREN_ASIDE_RE.finditer(text)
        if m.group(1).strip()
    ]
    if not tone and not asides:
        return EMOTION_COT_HINTS.get(emotion, "")
    return merge_stage_caption(tone, asides)


def _is_clone_voice(voice_type: str) -> bool:
    return voice_type.startswith("S_")


def _strip_brace_inline_tags(text: str) -> str:
    """移除 {{"additions":...} }} 内联块（嵌套 JSON，需按结尾 } }} 切）。"""
    t = text
    while "{{" in t:
        start = t.find("{{")
        end = t.find("} }}", start)
        if end != -1:
            end += 4
        else:
            end = t.find("}}", start)
            if end == -1:
                break
            end += 2
        t = t[:start] + t[end:]
    return t


def _strip_cot_wrapper_tags(t: str) -> str:
    """移除 cot 标签壳；支持未闭合的 <cot text=\"…\">对白。"""
    t = _COT_TEXT_ATTR_RE.sub(r"\2", t)
    t = _COT_LEGACY_RE.sub("", t)
    t = _COT_TEXT_ATTR_OPEN_RE.sub("", t)
    t = _COT_CLOSE_RE.sub("", t)
    return t


def _clean_cot_segments_for_tts(body: str) -> str:
    """闭合 cot 段内去掉括号旁白，避免 TTS 朗读动作描写。"""
    def _repl(m: re.Match[str]) -> str:
        hint = _escape_cot_attr(m.group(1))
        speech, _ = extract_paren_asides(m.group(2))
        if not speech:
            return ""
        return f'<cot text="{hint}">{speech}</cot>'

    if _COT_TEXT_ATTR_RE.search(body):
        return _COT_TEXT_ATTR_RE.sub(_repl, body)
    return body


def _join_cot_speeches(speeches: list[str]) -> str:
    """合并多段对白，避免「。，」等重复标点。"""
    parts: list[str] = []
    for i, raw in enumerate(speeches):
        s = raw.strip()
        if not s:
            continue
        if i < len(speeches) - 1:
            s = s.rstrip("。．.!！?？")
        parts.append(s)
    if not parts:
        return ""
    return parts[0] if len(parts) == 1 else "，".join(parts)


def collapse_cot_tags_for_tts(
    text: str, emotion: str = "calm", cot_hint: str = ""
) -> str:
    """
    将多条 <cot text=\"…\"> 合并为一条，避免 tag_parser 按段切换语气造成语音断裂。
    官方示例在段间使用「，」；本项目对同一句回复统一为单一语气描述。
    """
    if not text or not _COT_TEXT_ATTR_RE.search(text):
        return text
    matches = list(_COT_TEXT_ATTR_RE.finditer(text))
    if len(matches) <= 1:
        return text

    hints: list[str] = []
    speeches: list[str] = []
    for m in matches:
        hints.append(m.group(1).strip())
        speech, _ = extract_paren_asides(m.group(2))
        if speech.strip():
            speeches.append(speech.strip())
    if not speeches:
        return text

    unique_hints = {h for h in hints if h}
    unified_hint = _escape_cot_attr(
        cot_hint.strip()
        or (hints[0] if len(unique_hints) == 1 else "")
        or EMOTION_COT_HINTS.get(emotion, EMOTION_COT_HINTS["calm"])
    )
    combined = _join_cot_speeches(speeches)
    return f'<cot text="{unified_hint}">{combined}</cot>'


def strip_display_markup(text: str) -> str:
    """移除 TTS 控制标签与括号旁白，保留净对白，供字幕/聊天气泡展示。"""
    t = strip_think_tags(text)
    t = _strip_cot_wrapper_tags(t)
    t = _strip_brace_inline_tags(t)
    t = _BRACE_TAG_RE.sub("", t)
    t = _TTS_COT_META_RE.sub("", t)
    t = _EMOTION_RE.sub("", t)
    t = _MOOD_DELTA_RE.sub("", t)
    t, _ = extract_paren_asides(t)
    return t.strip()


def parse_mood_delta(text: str) -> tuple[int, str]:
    """解析 [mood_delta:±N]，返回 (delta, 去除标记后的文本)。"""
    t = strip_think_tags(text)
    m = _MOOD_DELTA_RE.search(t)
    if not m:
        return 0, t
    try:
        delta = int(m.group(1))
    except ValueError:
        delta = 0
    delta = max(-10, min(10, delta))
    t = _MOOD_DELTA_RE.sub("", t).strip()
    return delta, t


def parse_emotion_and_clean(text: str) -> tuple[str, str, str, str]:
    """解析 LLM 回复：展示文本、情绪、TTS 朗读文本（无控制标签）、cot 补充。"""
    text = strip_think_tags(text)
    emotion = "calm"
    cot_hint = ""

    m = _TTS_COT_META_RE.search(text)
    if m:
        cot_hint = m.group(1).strip()
        text = text[: m.start()].strip()

    m = _EMOTION_RE.search(text)
    if m:
        emotion = m.group(1).lower()
        text = _EMOTION_RE.sub("", text).strip()

    text = normalize_roleplay_brackets(text)
    display = strip_display_markup(text)
    return display, emotion, text.strip(), cot_hint


def normalize_cot_tag_parser_text(raw: str, emotion: str, cot_hint: str) -> str:
    """
    转为单向 HTTP 官方格式：<cot text="情感">对白</cot>
    支持 LLM 已写 text= 格式，或旧式 <cot>描述</cot>对白。
    """
    body = _EMOTION_RE.sub("", strip_think_tags(raw)).strip()
    if not body:
        return ""

    if _COT_TEXT_ATTR_RE.search(body):
        return collapse_cot_tags_for_tts(
            _clean_cot_segments_for_tts(body), emotion, cot_hint
        )

    # 未闭合 <cot text="…">对白（…旁白）
    m_open = re.search(
        r"<cot\s+text\s*=\s*[\"']([^\"']*)[\"']\s*>(.*)$",
        body,
        re.DOTALL | re.IGNORECASE,
    )
    if m_open and "</cot>" not in body.lower():
        hint = _escape_cot_attr(m_open.group(1))
        speech, _ = extract_paren_asides(m_open.group(2).strip())
        if speech:
            return f'<cot text="{hint}">{speech}</cot>'

    segments: list[str] = []
    last = 0
    for m in _COT_LEGACY_RE.finditer(body):
        hint = _escape_cot_attr(m.group(1))
        seg_start = m.end()
        next_m = _COT_LEGACY_RE.search(body, seg_start)
        seg_end = next_m.start() if next_m else len(body)
        speech, _ = extract_paren_asides(body[seg_start:seg_end].strip())
        if speech and hint:
            segments.append(f'<cot text="{hint}">{speech}</cot>')
        last = seg_end
    if segments:
        merged = collapse_cot_tags_for_tts("".join(segments), emotion, cot_hint)
        if merged != "".join(segments):
            return merged
        return "，".join(segments) if len(segments) > 1 else segments[0]

    ctx = _escape_cot_attr(
        cot_hint or EMOTION_COT_HINTS.get(emotion, EMOTION_COT_HINTS["calm"])
    )
    speech = strip_display_markup(body)
    if not speech:
        return ""
    return f'<cot text="{ctx}">{speech}</cot>'


def strip_paren_from_raw(text: str) -> str:
    """在保留 cot 标签的前提下，去掉各段对白里的括号旁白（供 TTS 原始串预处理）。"""
    if _COT_TEXT_ATTR_RE.search(text):
        cleaned, _ = extract_paren_asides(_clean_cot_segments_for_tts(text))
        return cleaned
    m_open = re.search(
        r"(<cot\s+text\s*=\s*[\"'][^\"']*[\"']\s*>)(.*)$",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if m_open and "</cot>" not in text.lower():
        prefix, rest = m_open.group(1), m_open.group(2)
        speech, _ = extract_paren_asides(rest.strip())
        return f"{prefix}{speech}</cot>" if speech else ""
    cleaned, _ = extract_paren_asides(text)
    return cleaned


def emotion_context_for_tts(
    emotion: str,
    cot_hint: str = "",
    raw: str = "",
) -> str:
    """供 V3 单向接口 additions.context_texts（勿写入 req_params.text）。"""
    if cot_hint.strip():
        return cot_hint.strip()
    parts = re.findall(r"<cot>\s*(.*?)\s*</cot>", raw, re.IGNORECASE | re.DOTALL)
    if parts:
        return " · ".join(p.strip() for p in parts if p.strip())
    return EMOTION_COT_HINTS.get(emotion, EMOTION_COT_HINTS["calm"])


def prepare_tts_text(
    text: str,
    emotion: str = "calm",
    voice_type: str = "",
    cot_hint: str = "",
) -> str:
    """
    生成送入单向 HTTP req_params.text 的内容。
    复刻音色 + use_tag_parser：官方 <cot text="…">对白</cot>；
    否则：纯对白（情感走 additions.context_texts）。
    """
    if settings.doubao_use_tag_parser and _is_clone_voice(voice_type):
        tagged = normalize_cot_tag_parser_text(text, emotion, cot_hint)
        if tagged:
            return tagged
    return strip_display_markup(text)


def speed_for_emotion(base_speed: float, emotion: str) -> float:
    delta = EMOTION_SPEED_DELTA.get(emotion, 0.0)
    return max(0.5, min(2.0, base_speed + delta))


def _emotion_instruction(persona: dict[str, Any]) -> str:
    allowed = persona.get("emotions") or list(VALID_EMOTIONS)
    tags = " ".join(f"[emotion:{e}]" for e in allowed)
    return (
        "【TTS 播报格式 — 必须遵守】\n"
        "1. **可朗读对白**只写在 <cot text=\"语气描述\">对白</cot> 内，不要在对白外加括号。\n"
        "2. **不可朗读**的动作、环境、神态补充一律用全角括号（…）写在 cot 外或句末；"
        "括号内文字只显示在气泡下方，不会念出来。禁止「」、半角()、[]。\n"
        "3. 每轮只用一组 cot 包裹全部要对博士说出口的台词；哼唱/歌词也写在 cot 内，勿用括号包住歌词。\n"
        "4. 可选 [tts_cot:更细的语气描述] 在情绪标签上一行。\n"
        f"5. 最后一行单独标注情绪标签，仅从以下选一：{tags}\n"
        "6. 禁止 {{\"additions\"…}} 与旧式 <cot>描述</cot>对白 混用。"
    )


def resolve_mode(
    persona: dict[str, Any],
    user_text: str,
    history: list[dict[str, str]] | None = None,
    explicit_mode: str | None = None,
) -> str:
    """
    解析对话模式：优先用户指定；否则按关键词与上轮 assistant 推断。
    explicit_mode: 具体模式名，或 'auto' 表示自动推断。
    """
    modes: list[str] = persona.get("modes") or []
    if not modes:
        return ""

    if explicit_mode and explicit_mode not in ("auto", "") and explicit_mode in modes:
        return explicit_mode

    pid = persona.get("id", "")

    if pid == "skadi_corrupting":
        if any(k in user_text for k in _RED_PLEAD_KEYWORDS):
            return "plead" if "plead" in modes else modes[0]
        if any(k in user_text for k in _RED_GENTLE_KEYWORDS):
            return "gentle" if "gentle" in modes else modes[0]
        # 上轮 assistant 在哀求，用户安慰 -> 切回温柔
        if history:
            last = next((h for h in reversed(history) if h.get("role") == "assistant"), None)
            if last and any(w in last.get("content", "") for w in ("逃", "走吧", "别靠近")):
                if any(w in user_text for w in ("好", "陪", "不", "留", "没事")):
                    return "gentle" if "gentle" in modes else modes[0]
        return "gentle" if "gentle" in modes else modes[0]

    if pid == "skadi":
        if any(k in user_text for k in _BLUE_VULNERABLE_KEYWORDS):
            return "vulnerable" if "vulnerable" in modes else modes[0]
        if any(k in user_text for k in _BLUE_COLD_KEYWORDS):
            return "cold" if "cold" in modes else modes[0]
        return "cold" if "cold" in modes else modes[0]

    return modes[0]


def build_system_prompt(
    persona: dict[str, Any],
    mode: str = "",
    doctor_state: dict[str, Any] | None = None,
) -> str:
    parts = [persona["system_prompt"]]
    mode_prompts = persona.get("mode_prompts") or {}
    mode_labels = persona.get("mode_labels") or {}
    if mode and mode in mode_prompts:
        label = mode_labels.get(mode, mode)
        parts.append(f"【当前模式：{label}】{mode_prompts[mode]}")
    if doctor_state is not None:
        from services.doctor_state import build_doctor_state_block

        block = build_doctor_state_block(persona.get("id", ""), doctor_state)
        if block:
            parts.append(block)
    parts.append(_MOOD_OUTPUT_INSTRUCTION)
    parts.append(_emotion_instruction(persona))
    return "\n".join(parts)


def build_messages(
    persona: dict[str, Any],
    user_text: str,
    history: list[dict[str, str]] | None = None,
    mode: str = "",
    doctor_state: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    resolved_mode = mode or resolve_mode(persona, user_text, history, "auto")
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": build_system_prompt(persona, resolved_mode, doctor_state),
        },
    ]

    for item in persona.get("few_shot", []):
        messages.append({"role": item["role"], "content": item["content"]})

    mode_shots = (persona.get("mode_few_shot") or {}).get(resolved_mode, [])
    for item in mode_shots:
        messages.append({"role": item["role"], "content": item["content"]})

    if history:
        for h in history[-10:]:
            role = h.get("role", "user")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": h.get("content", "")})
    messages.append({"role": "user", "content": user_text})
    return messages


def persona_public_meta(persona: dict[str, Any]) -> dict[str, Any]:
    """供 API / 前端展示的人物元信息。"""
    modes = persona.get("modes") or []
    mode_labels = persona.get("mode_labels") or {}
    return {
        "id": persona["id"],
        "name": persona["name"],
        "avatar": persona.get("avatar", ""),
        "description": persona.get("description", ""),
        "default_voice": persona.get("default_voice"),
        "default_speed": persona.get("default_speed", 1.0),
        "modes": modes,
        "mode_labels": {m: mode_labels.get(m, m) for m in modes},
        "emotions": persona.get("emotions") or list(VALID_EMOTIONS),
    }
