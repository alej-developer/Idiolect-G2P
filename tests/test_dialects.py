"""
Pruebas unitarias para las variantes dialectales y diacronicas.
Unit tests for dialectal and diachronic varieties.
"""

import pytest
from idiolect_g2p.core.transducer import G2PTransducer
from idiolect_g2p.dialects.registry import GLOBAL_DIALECT_REGISTRY
from idiolect_g2p.dialects.peninsular import PeninsularStandardDialect
from idiolect_g2p.dialects.caribbean import CaribbeanStandardDialect, CaribbeanLambdacistDialect
from idiolect_g2p.dialects.rioplatense import RioplatenseSheistDialect, RioplatenseZheistDialect
from idiolect_g2p.dialects.andine import AndeanTraditionalDialect, AndeanAssibilatedDialect
from idiolect_g2p.dialects.andalusian import EasternAndalusianDialect
from idiolect_g2p.dialects.central_america import CostaRicanDialect
from idiolect_g2p.dialects.diachronic import GoldenAgeDialect


def test_peninsular_distinction() -> None:
    """Verifica que el dialecto peninsular distinga /θ/ vs /s̺/."""
    d = PeninsularStandardDialect()
    t = G2PTransducer(default_dialect=d)

    res_caza = t.transcribe_word("caza")
    res_casa = t.transcribe_word("casa")

    assert "θ" in res_caza.syllabified_ipa
    assert "s̺" in res_casa.syllabified_ipa
    assert res_caza.syllabified_ipa != res_casa.syllabified_ipa


def test_caribbean_lambdacism_and_aspiration() -> None:
    """Verifica lambdacismo (/ɾ/ -> [l]) y aspiracion (/s/ -> [h]) caribena."""
    d_lambdacist = CaribbeanLambdacistDialect()
    t = G2PTransducer(default_dialect=d_lambdacist)

    res_puerto = t.transcribe_word("puerto")
    assert "l" in res_puerto.syllable_phonemes[0] or "pwel" in res_puerto.syllabified_ipa

    res_mas = t.transcribe_word("más")
    assert "h" in res_mas.syllabified_ipa


def test_rioplatense_rehilamiento() -> None:
    """Verifica rehilamiento sordo [ʃ] y sonoro [ʒ] en Rioplatense."""
    d_sheist = RioplatenseSheistDialect()
    d_zheist = RioplatenseZheistDialect()

    t_sheist = G2PTransducer(default_dialect=d_sheist)
    t_zheist = G2PTransducer(default_dialect=d_zheist)

    res_calle_sh = t_sheist.transcribe_word("calle")
    res_calle_zh = t_zheist.transcribe_word("calle")

    assert "ʃ" in res_calle_sh.syllabified_ipa
    assert "ʒ" in res_calle_zh.syllabified_ipa


def test_andean_lleismo() -> None:
    """Verifica preservacion de /ʎ/ en el dialecto Andino Tradicional."""
    d = AndeanTraditionalDialect()
    t = G2PTransducer(default_dialect=d)

    res_caballo = t.transcribe_word("caballo")
    assert "ʎ" in res_caballo.syllabified_ipa


def test_costa_rican_assibilation() -> None:
    """Verifica asibilacion retrofleja en Costa Rica."""
    d = CostaRicanDialect()
    t = G2PTransducer(default_dialect=d)

    res_tres = t.transcribe_word("tres")
    assert "t͡ʂ" in res_tres.syllabified_ipa


def test_eastern_andalusian_vowel_opening() -> None:
    """Verifica abertura vocalica [ɛ] ante /s/ en Andaluz Oriental."""
    d = EasternAndalusianDialect()
    t = G2PTransducer(default_dialect=d)

    res_mes = t.transcribe_word("mes")
    assert "ɛ" in res_mes.syllabified_ipa


def test_golden_age_f_latin_aspiration() -> None:
    """Verifica retencion de [h] < F- latina en el Siglo de Oro."""
    d = GoldenAgeDialect()
    t = G2PTransducer(default_dialect=d)

    res_hacer = t.transcribe_word("hacer")
    assert "h" in res_hacer.syllabified_ipa
    assert "ʎ" in t.transcribe_word("lleno").syllabified_ipa


def test_registry_contains_all_regions() -> None:
    """Verifica que el registro contenga todas las variantes continentales e historicas."""
    dialects = GLOBAL_DIALECT_REGISTRY.list_all()
    assert len(dialects) >= 14
    codes = [d.code for d in dialects]
    assert "ES_PENINSULAR" in codes
    assert "MX_CENTRAL" in codes
    assert "CARIBBEAN_LAMBDACIST" in codes
    assert "RIOPLATENSE_SHEIST" in codes
    assert "ANDINE_TRADITIONAL" in codes
    assert "CHILEAN" in codes
    assert "DIACHRONIC_GOLDEN_AGE" in codes
