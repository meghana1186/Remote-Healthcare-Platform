"""Emergency screen that runs before any generation.

Two layers:

1. Deterministic rules (this file). Regex patterns for English, Hindi and
   Kannada, including romanized Hindi and Kannada, with negation handling so
   that "no chest pain" is not flagged while "can't breathe" still is.
2. An optional LLM second check (see assess_emergency). It only runs when the
   rules find nothing, and it can only escalate a message to emergency. It can
   never clear a message the rules flagged.

The rules are a screen, not a diagnosis. They favour sensitivity: a false
alarm costs a phone call, a missed emergency can cost a life.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Optional

EMERGENCY_MESSAGE = (
    "Possible emergency. Call 112, or 108 for an ambulance, or go to the "
    "nearest emergency department now. Do not wait for this app."
)
SELF_HARM_MESSAGE = (
    "If you or someone with you may act on thoughts of suicide or self-harm, "
    "call 112 now. For mental health support you can also call Tele-MANAS on 14416. "
    "Stay with the person and do not leave them alone."
)

DEVANAGARI = "ऀ-ॿ"
KANNADA = "ಀ-೿"

# Child and pregnancy cues used by rules that need context.
CHILD = (
    r"\b(baby|babies|infant|newborn|child|children|kid|son|daughter|toddler)\b"
    r"|\b([1-9]|1[0-2]|one|two|three|four|five)[- ](month|months|year|years|yr|yrs)[- ]old\b"
    r"|बच्च|शिशु|ಮಗು|ಮಗುವ|bachch|bacch|magu"
)
PREGNANT = r"pregnan|गर्भवती|गर्भ|ಗರ್ಭಿಣಿ|garbhini|garbhvati"


@dataclass(frozen=True)
class Rule:
    category: str
    pattern: str
    lang: str = "en"
    negatable: bool = True          # False when the phrase itself contains a negation
    requires: tuple[str, ...] = ()  # extra patterns that must also appear somewhere in the text


def _en(category: str, pattern: str, negatable: bool = True, requires: tuple[str, ...] = ()) -> Rule:
    return Rule(category, rf"\b(?:{pattern})\b", "en", negatable, requires)


def _hi(category: str, pattern: str, negatable: bool = True, requires: tuple[str, ...] = ()) -> Rule:
    # Indic words take suffixes, so only the start of the match is anchored.
    return Rule(category, rf"(?<![{DEVANAGARI}])(?:{pattern})", "hi", negatable, requires)


def _kn(category: str, pattern: str, negatable: bool = True, requires: tuple[str, ...] = ()) -> Rule:
    return Rule(category, rf"(?<![{KANNADA}])(?:{pattern})", "kn", negatable, requires)


def _roman(category: str, pattern: str, lang: str, negatable: bool = True) -> Rule:
    return Rule(category, rf"\b(?:{pattern})", lang, negatable)


RULES: list[Rule] = [
    # Cardiac
    _en("cardiac", r"chest (?:pain|pressure|tightness|heaviness|discomfort)"),
    _en("cardiac", r"pain in (?:my|the|his|her|their) chest"),
    _en("cardiac", r"heart attack"),
    _en("cardiac", r"pain (?:spreading|radiating|going|moving) (?:to|into|down) (?:my |his |her |the )?(?:left )?(?:arm|jaw)"),
    # Breathing
    _en("breathing", r"(?:difficulty|trouble|problem|struggling|struggle) (?:in )?breathing"),
    _en("breathing", r"(?:cant|cannot|can not|unable to|not able to|couldnt) (?:breathe|breath)", negatable=False),
    _en("breathing", r"gasping|choking|fighting for (?:breath|air)"),
    _en("breathing", r"severe(?:ly)? (?:shortness of breath|short of breath|breathless)|very breathless|breathless (?:at|while) rest(?:ing)?"),
    _en("breathing", r"blue lips|lips (?:are |is |look |looking |have |has )?(?:turning |turned |going |gone )?(?:blue|bluish)"),
    _en("breathing", r"chest indrawing"),
    # Neurological and consciousness
    _en("neuro", r"unconscious|unresponsive|not (?:responding|responsive)", negatable=False),
    _en("neuro", r"(?:not|wont|cant|cannot|isnt|is not) wak(?:e|ing)(?: up)?", negatable=False),
    _en("neuro", r"(?:cant|cannot|unable to|not able to) stay awake", negatable=False),
    _en("neuro", r"fainted|passed out|blacked out|collapsed"),
    _en("neuro", r"seizures?|convulsions?|convulsing|(?:having|had|has|getting) (?:a )?fits?|fitting"),
    _en("neuro", r"stroke"),
    _en("neuro", r"face (?:is |has )?(?:drooping|droopy|dropped|drooped)|drooping (?:of )?(?:the )?face|one side of (?:the |his |her |my )?face"),
    _en("neuro", r"(?:weakness|numbness) (?:in|on|of) one side|one side (?:of (?:the |his |her |my )?body )?(?:is )?(?:weak|numb)"),
    _en("neuro", r"(?:cant|cannot|unable to|not able to) (?:move|lift|raise) (?:one|his|her|my|the) (?:arm|leg|hand|side)", negatable=False),
    _en("neuro", r"slurred speech|speech (?:is )?slurred|slurring"),
    _en("neuro", r"worst headache|sudden(?:ly)? severe headache|thunderclap"),
    _en("neuro", r"stiff neck", requires=(r"fever|bukhar|बुखार|ಜ್ವರ|jvara|jwara",)),
    # Bleeding
    _en("bleeding", r"(?:severe|heavy|heavily|uncontrolled|nonstop|non-stop|a lot of|lots of) bleeding|bleeding (?:a lot|heavily|badly|profusely)"),
    _en("bleeding", r"bleeding (?:that )?(?:wont|will not|does not|doesnt|is not|isnt) stop(?:ping)?|wont stop bleeding", negatable=False),
    _en("bleeding", r"(?:vomiting|vomited|throwing up|coughing up|coughing|spitting) blood|blood in (?:the |his |her )?vomit"),
    _en("bleeding", r"bleeding gums|gums (?:are )?bleeding|nose ?bleed", requires=(r"dengue|fever|bukhar|बुखार|ಜ್ವರ",)),
    # Poisoning and overdose
    _en("poisoning", r"poison(?:ed|ing)?|pesticide|insecticide|overdose|overdosed"),
    _en("poisoning", r"(?:swallowed|drank|drunk|ate|took|consumed) (?:some |a )?(?:kerosene|bleach|acid|phenyl|rat poison|weed killer)"),
    _en("poisoning", r"took too many (?:\w+ )?(?:pills|tablets|medicines)"),
    # Self-harm
    _en("self_harm", r"suicid(?:e|al)|kill (?:myself|himself|herself|themselves)|end (?:my|his|her|their) (?:own )?life"),
    _en("self_harm", r"(?:want|wants|wanted|going) to die|take (?:my|his|her|their) (?:own )?life|self[- ]harm|hurt (?:myself|himself|herself)"),
    # Injury, burns, bites, allergy
    _en("injury", r"severe(?:ly)? burn(?:s|ed|t)?|badly burn(?:ed|t)|electric shock|electrocuted"),
    _en("injury", r"fell (?:off|from) (?:a |the )?(?:height|tree|roof|terrace|building|ladder|bike)"),
    _en("injury", r"hit by (?:a |the )?(?:car|bus|truck|lorry|vehicle|bike|tractor)|road accident"),
    _en("injury", r"head injury|hit (?:his|her|my) head|bone (?:is )?(?:sticking|poking) out|deep (?:cut|wound)"),
    _en("bite_sting", r"snake ?bites?|bitten by (?:a )?snake|snake (?:has |just |had )?(?:bit|bitten)|scorpion sting|stung by (?:a )?scorpion"),
    _en("allergy", r"anaphyla\w*|throat (?:is )?(?:closing|swelling|swollen)"),
    _en("allergy", r"(?:face|lips|lip|tongue|throat)(?: and (?:face|lips|lip|tongue|throat))? (?:is |are )?(?:swelling|swollen)|swelling of (?:the )?(?:face|lips|tongue|throat)"),
    _en("heat", r"heat ?stroke"),
    # Pregnancy danger signs (need a pregnancy cue in the same message)
    _en("pregnancy", r"bleed(?:ing)?|severe (?:abdominal|stomach|belly) pain|blurred vision|severe headache|(?:fits|seizure|convulsion)", requires=(PREGNANT,)),
    _en("pregnancy", r"waters? (?:has |have )?broke(?:n)?|baby (?:is )?not moving|reduced (?:fetal|foetal) movement"),
    _en("pregnancy", r"(?:heavy )?bleeding after (?:delivery|childbirth|giving birth)"),
    # Child danger signs, WHO IMCI general danger signs (need a child cue)
    _en("child", r"(?:unable|not able) to (?:drink|feed|breastfeed)|not (?:drinking|feeding|breastfeeding|breast feeding)(?: at all)?", requires=(CHILD,)),
    _en("child", r"vomits everything|vomiting everything|very (?:sleepy|drowsy)|hard to wake|floppy|lethargic", requires=(CHILD,)),

    # Hindi, Devanagari. Nukta and chandrabindu are normalized away first.
    _hi("cardiac", r"(?:सीने|सीना|छाती)(?: में)?(?: \S+)? दर्द"),
    _hi("cardiac", r"दिल का दौरा"),
    _hi("breathing", r"सांस (?:लेने )?में(?: \S+)? (?:तकलीफ|दिक्कत|परेशानी)"),
    _hi("breathing", r"सांस नहीं (?:आ|ले)|सांस रुक", negatable=False),
    _hi("breathing", r"होंठ नीले"),
    _hi("neuro", r"बेहोश|होश नहीं", negatable=False),
    _hi("neuro", r"मिर्गी|दौरा पड|दौरे पड|झटके (?:आ|लग)"),
    _hi("neuro", r"लकवा|मुंह टेढ़ा|मुंह टेढा|मुंह टेढ"),
    _hi("bleeding", r"(?:बहुत|ज्यादा) खून|खून (?:बंद नहीं|रुक नहीं|नहीं रुक)|खून की उल्टी", negatable=False),
    _hi("poisoning", r"जहर|कीटनाशक|(?:ज्यादा|बहुत) (?:गोलियां|गोली|दवा) खा"),
    _hi("self_harm", r"आत्महत्या|खुद को मार|जान दे|मरना चाह"),
    _hi("bite_sting", r"सांप (?:ने )?काट|सांप का काट|बिच्छू (?:ने )?काट"),
    _hi("pregnancy", r"खून", requires=(PREGNANT,)),

    # Romanized Hindi (Hinglish)
    _roman("cardiac", r"(?:seene|seena|sine|seeney|chhati|chati|chaati) (?:me|mein|mai|main)(?: \w+)? dard", "hi-latn"),
    _roman("cardiac", r"dil ka daura", "hi-latn"),
    _roman("breathing", r"sa+ns (?:lene )?(?:me|mein|mai|main)(?: \w+)? (?:takleef|taklif|dikkat|dikat|pareshani)", "hi-latn"),
    _roman("breathing", r"sa+ns (?:nahi|nahin|nhi) (?:aa|a |le)", "hi-latn", negatable=False),
    _roman("neuro", r"behosh|bihosh|hosh nahi", "hi-latn", negatable=False),
    _roman("neuro", r"mirgi|daura pad|daure pad|jhatke", "hi-latn"),
    _roman("neuro", r"lakwa|lakva", "hi-latn"),
    _roman("bleeding", r"(?:bahut|bohot|zyada|jyada) (?:khoon|khun)|(?:khoon|khun) (?:band nahi|ruk nahi|nahi ruk)", "hi-latn", negatable=False),
    _roman("poisoning", r"(?:zehar|zeher|zehr|zahar|jahar|jehar)\b|keetnashak|kitnashak", "hi-latn"),
    _roman("self_harm", r"a+tmahatya|marna chaht|marna chahti|jaan de", "hi-latn"),
    _roman("bite_sting", r"sa+np (?:ne )?kaat|sa+np ka kaat", "hi-latn"),

    # Kannada
    _kn("cardiac", r"ಎದೆ(?:ಯಲ್ಲಿ)? ನೋವು|ಎದೆನೋವು|ಹೃದಯಾಘಾತ"),
    _kn("breathing", r"ಉಸಿರಾಟ(?:ದ)? (?:ತೊಂದರೆ|ಕಷ್ಟ)|ಉಸಿರು ಕಟ್ಟ"),
    _kn("breathing", r"ಉಸಿರಾಡಲು ಆಗುತ್ತಿಲ್ಲ|ಉಸಿರು ಆಡುತ್ತಿಲ್ಲ", negatable=False),
    _kn("neuro", r"ಪ್ರಜ್ಞೆ (?:ತಪ್ಪಿ|ಇಲ್ಲ|ಹೋಗಿ)|ಪ್ರಜ್ಞಾಹೀನ", negatable=False),
    _kn("neuro", r"ಮೂರ್ಛೆ|ಫಿಟ್ಸ್|ಸೆಳೆತ|ಲಕ್ವ|ಪಾರ್ಶ್ವವಾಯು"),
    _kn("bleeding", r"ತುಂಬಾ ರಕ್ತ|ರಕ್ತಸ್ರಾವ|ರಕ್ತ ನಿಲ್ಲುತ್ತಿಲ್ಲ|ರಕ್ತ ವಾಂತಿ", negatable=False),
    _kn("poisoning", r"ವಿಷ(?!ಯ)|ಕೀಟನಾಶಕ"),
    _kn("self_harm", r"ಆತ್ಮಹತ್ಯೆ|ಸಾಯಬೇಕು|ಸಾಯುತ್ತೇನೆ"),
    _kn("bite_sting", r"ಹಾವು ಕಚ್ಚ|ಚೇಳು ಕಚ್ಚ|ಚೇಳು ಕುಟ"),
    _kn("pregnancy", r"ರಕ್ತ", requires=(PREGNANT,)),

    # Romanized Kannada
    _roman("cardiac", r"ede ?novu|edeyalli novu", "kn-latn"),
    _roman("breathing", r"usir(?:u|aata|ata) (?:kattu|kashta|tondare)", "kn-latn"),
    _roman("neuro", r"prajn?e (?:tappi|illa|hogi)", "kn-latn", negatable=False),
    _roman("neuro", r"moorch?h?e|murch?h?e", "kn-latn"),
    _roman("bite_sting", r"ha+vu kach?ch|cheLu kach?ch", "kn-latn"),
    _roman("poisoning", r"visha\b|keetanashaka", "kn-latn"),
]

def _prep(pattern: str) -> str:
    """Apply the same Indic spelling normalization to patterns as to input text."""
    p = unicodedata.normalize("NFKC", pattern)
    return p.replace("\u093c", "").replace("\u0901", "\u0902")


RULES = [
    Rule(r.category, _prep(r.pattern), r.lang, r.negatable, tuple(_prep(x) for x in r.requires))
    for r in RULES
]
_COMPILED = [(r, re.compile(r.pattern), [re.compile(x) for x in r.requires]) for r in RULES]

# English negation cues that must appear shortly before a term.
NEGATION_BEFORE = re.compile(
    r"\b(?:no|not|denies|denied|deny|without|never|nor|negative for|free of|absence of|"
    r"isnt|wasnt|arent|werent|doesnt|dont|didnt|hasnt|havent|hadnt|cant say)\b"
)
# Phrases that look like negation but are not.
PSEUDO_NEGATION = re.compile(
    r"\b(?:no improvement|not improving|no better|not better|not only|not sure|no change|not getting better|no relief)\b"
)
# Hindi and Kannada put the negation after the symptom: "सीने में दर्द नहीं", "ಎದೆ ನೋವು ಇಲ್ಲ".
NEGATION_AFTER = re.compile(r"^\s*(?:है\s+)?(?:नहीं|नही|nahi|nahin|nhi|ಇಲ್ಲ|illa)(?![\wऀ-ॿಀ-೿])")
# Clause boundaries stop negation from leaking across "no fever, but chest pain".
CLAUSE_BREAK = re.compile(r"[.,;!?\n]|\b(?:but|however|though|although|except|and now|now)\b|लेकिन|पर |ಆದರೆ")


# Past events, and events that happened to someone else and are over.
HISTORY_CUE = re.compile(
    r"\b(?:last year|years ago|long ago|in the past|history of|used to (?:have|get)|"
    r"as a (?:child|kid)|in (?:my |his |her )?childhood|died (?:of|from|due to)|passed away)\b"
    r"|पिछले साल|साल पहले|ಕಳೆದ ವರ್ಷ|pichh?le saal"
)
# Words that make a symptom current again even when a history cue is present.
ONGOING_CUE = re.compile(r"\b(?:since|started|still|again|today|right now|currently|worse|worsening)\b")
# General questions about a condition, as opposed to reports of one.
EDUCATION_QUESTION = re.compile(
    r"^\s*(?:what|which|how|why|when)\b[^.!?]*\b(?:signs?|symptoms?|causes?|prevent\w*|risk factors?)\b"
)
# Anything that suggests someone has the symptom now.
PRESENT_CUE = re.compile(
    r"\b(?:i have|i am|im|i feel|i got|my \w+(?: \w+)? (?:has|is|have|got)|he is|she is|hes|shes|"
    r"he has|she has|right now|currently)\b"
)


def normalize(text: str) -> str:
    """Lowercase, unify apostrophes and Indic spelling variants, collapse spaces."""
    t = unicodedata.normalize("NFKC", text or "").lower()
    t = t.replace("़", "")            # Devanagari nukta: ज़ -> ज
    t = t.replace("ँ", "ं")      # chandrabindu -> anusvara: साँस -> सांस
    t = re.sub(r"[‘’ʼ`']", "", t)  # can't -> cant
    return re.sub(r"\s+", " ", t).strip()


def _clause_before(text: str, start: int) -> str:
    prefix = text[:start]
    breaks = list(CLAUSE_BREAK.finditer(prefix))
    if breaks:
        prefix = prefix[breaks[-1].end():]
    words = prefix.split()
    return " ".join(words[-5:])


def _clause_around(text: str, start: int, end: int) -> str:
    before = list(CLAUSE_BREAK.finditer(text[:start]))
    left = before[-1].end() if before else 0
    after = CLAUSE_BREAK.search(text, end)
    right = after.start() if after else len(text)
    return text[left:right]


def _is_historical(text: str, match: re.Match) -> bool:
    clause = _clause_around(text, match.start(), match.end())
    return bool(HISTORY_CUE.search(clause)) and not ONGOING_CUE.search(clause)


def _education_question_end(text: str) -> int:
    """If the message opens with a general question and nobody is described as
    having symptoms, return where that question ends; otherwise 0."""
    if not EDUCATION_QUESTION.search(text) or PRESENT_CUE.search(text):
        return 0
    # Only the opening question is ignored; anything after the first clause break
    # ("what are the signs of poisoning, he drank pesticide") is still screened.
    brk = CLAUSE_BREAK.search(text)
    return brk.start() if brk else len(text)


def _is_negated(text: str, match: re.Match, rule: Rule) -> bool:
    if not rule.negatable:
        return False
    before = _clause_before(text, match.start())
    if before and NEGATION_BEFORE.search(before) and not PSEUDO_NEGATION.search(before):
        return True
    after = text[match.end():match.end() + 25]
    after = CLAUSE_BREAK.split(after, maxsplit=1)[0]
    return bool(NEGATION_AFTER.search(after))


@dataclass
class ScreenResult:
    emergency: bool
    flags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    negated: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)   # past events and general questions


def screen(text: str) -> ScreenResult:
    """Run the deterministic rules only."""
    t = normalize(text)
    question_end = _education_question_end(t)
    flags, categories, negated, langs, ignored = [], [], [], [], []
    for rule, rx, reqs in _COMPILED:
        if reqs and not all(req.search(t) for req in reqs):
            continue
        for m in rx.finditer(t):
            phrase = m.group(0).strip()
            if _is_negated(t, m, rule):
                if phrase not in negated:
                    negated.append(phrase)
                continue
            if m.start() < question_end or _is_historical(t, m):
                if phrase not in ignored:
                    ignored.append(phrase)
                continue
            if phrase not in flags:
                flags.append(phrase)
            if rule.category not in categories:
                categories.append(rule.category)
            if rule.lang not in langs:
                langs.append(rule.lang)
    return ScreenResult(bool(flags), flags, categories, negated, langs, ignored)


def emergency_message(categories: list[str]) -> str:
    if "self_harm" in categories:
        return SELF_HARM_MESSAGE
    return EMERGENCY_MESSAGE


LLMCheck = Callable[[str], Optional[dict]]


def _default_llm_check(text: str) -> Optional[dict]:
    from .groq_client import GroqAI
    return GroqAI().classify_emergency(text)


def assess_emergency(text: str, use_llm: bool = True, llm_check: Optional[LLMCheck] = None) -> dict:
    """Rules first. If they find nothing, ask the LLM. The LLM can only escalate."""
    result = screen(text)
    out = {
        "emergency": result.emergency,
        "flags": result.flags,
        "categories": result.categories,
        "negated": result.negated,
        "ignored": result.ignored,
        "decided_by": "rules" if result.emergency else "none",
        "llm_checked": False,
        "llm_reason": "",
        "message": emergency_message(result.categories) if result.emergency else "",
    }
    if result.emergency or not use_llm:
        return out

    check = llm_check or _default_llm_check
    try:
        verdict = check(text)
    except Exception:
        verdict = None
    if verdict is None:
        return out

    out["llm_checked"] = True
    out["llm_reason"] = str(verdict.get("reason", ""))[:300]
    if verdict.get("emergency") is True:
        out.update(
            emergency=True,
            decided_by="llm",
            flags=[f"LLM: {out['llm_reason']}" if out["llm_reason"] else "LLM flagged a possible emergency"],
            message=EMERGENCY_MESSAGE,
        )
    return out


# Languages the deterministic rules cover. Anything else relies on the LLM check alone.
RULE_LANGUAGES = {"English", "Hindi", "Kannada"}


def rules_cover(language: str) -> bool:
    return language in RULE_LANGUAGES


# Backward-compatible helpers used elsewhere in the codebase.
def emergency_flags(text: str) -> list[str]:
    return screen(text).flags


def safety_gate(text: str) -> dict:
    r = screen(text)
    return {
        "is_emergency": r.emergency,
        "flags": r.flags,
        "message": emergency_message(r.categories) if r.emergency else "",
    }


def run_safety_checks(text: str, use_llm: bool = False) -> dict:
    a = assess_emergency(text, use_llm=use_llm)
    return {"emergency": a["emergency"], "flags": a["flags"], "message": a["message"]}
