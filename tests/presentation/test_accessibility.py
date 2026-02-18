"""
Tests d'accessibilité — WCAG 2.1 AA

Vérifie que les templates HTML, les traductions et les modèles de configuration
respectent les critères d'accessibilité numérique (RGAA / WCAG 2.1 AA).

Critères couverts :
    WCAG 1.1.1 — Contenu non textuel (alt sur les images)
    WCAG 1.3.1 — Informations et relations (labels liés aux champs)
    WCAG 1.4.4 — Redimensionnement du texte (viewport meta)
    WCAG 3.1.1 — Langue de la page (attribut lang sur <html>)
    WCAG 3.1.2 — Langue des parties (i18n, gettext, locales .po)
    WCAG 4.1.2 — Nom, rôle, valeur (attributs ARIA)
"""

import re
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Chemins vers les ressources testées
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
TEMPLATES_DIR = REPO_ROOT / "src" / "geneweb" / "presentation" / "web" / "templates"
LOCALES_DIR = REPO_ROOT / "locales"

# Templates avec des formulaires (inputs doivent avoir des labels)
FORM_TEMPLATES = ["add_family.html", "server_config.html"]

# Tous les templates HTML du projet
ALL_TEMPLATES = list(TEMPLATES_DIR.glob("*.html"))

# Templates standalone (ne font pas extends — donc déclarent leur propre <html>)
STANDALONE_TEMPLATES = [
    tpl for tpl in ALL_TEMPLATES
    if "{%" not in tpl.read_text(encoding="utf-8").split("\n")[0]
    and "{% extends" not in tpl.read_text(encoding="utf-8")[:200]
]


# ===========================================================================
# Helpers
# ===========================================================================

def read_template(name: str) -> str:
    """Retourne le contenu brut d'un template HTML."""
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _extract_label_for_values(html: str) -> set:
    """Retourne tous les identifiants cibles de <label for='...'> dans le HTML."""
    return set(re.findall(r'<label[^>]+for=["\']([^"\']+)["\']', html))


def _extract_input_ids(html: str) -> set:
    """Retourne tous les id d'éléments <input>, <select> et <textarea>."""
    return set(re.findall(r'<(?:input|select|textarea)[^>]+id=["\']([^"\']+)["\']', html))


# ===========================================================================
# 1. Tests des templates HTML (WCAG 1.1.1, 1.3.1, 1.4.4, 3.1.1, 4.1.2)
# ===========================================================================

class TestHTMLTemplatesAccessibility:
    """Parse les vrais fichiers HTML du projet et vérifie les critères WCAG."""

    # ------------------------------------------------------------------
    # WCAG 1.4.4 — Redimensionnement du texte
    # ------------------------------------------------------------------

    def test_base_html_has_viewport_meta(self):
        """
        WCAG 1.4.4 — base.html doit déclarer un viewport adaptatif.
        Tous les templates enfants ({% extends 'base.html' %}) en héritent.
        """
        content = read_template("base.html")
        assert 'name="viewport"' in content, (
            "base.html : <meta name='viewport'> absent (WCAG 1.4.4)"
        )
        assert "width=device-width" in content, (
            "base.html : le viewport doit inclure width=device-width"
        )

    def test_standalone_templates_have_viewport_meta(self):
        """
        WCAG 1.4.4 — Les templates standalone (sans extends) doivent chacun
        déclarer leur propre viewport. Les templates enfants l'héritent de base.html.
        """
        missing = []
        for tpl in STANDALONE_TEMPLATES:
            content = tpl.read_text(encoding="utf-8")
            if 'name="viewport"' not in content and "name='viewport'" not in content:
                missing.append(tpl.name)
        assert missing == [], (
            f"Templates standalone sans <meta name='viewport'> (WCAG 1.4.4) : {missing}"
        )

    # ------------------------------------------------------------------
    # WCAG 3.1.1 — Langue de la page
    # ------------------------------------------------------------------

    def test_base_html_declares_html_lang(self):
        """
        WCAG 3.1.1 — base.html doit déclarer lang sur <html>. Tous les templates
        qui font {% extends 'base.html' %} bénéficient de cet attribut.
        """
        content = read_template("base.html")
        assert re.search(r"<html\s[^>]*lang=", content), (
            "base.html : attribut lang absent sur <html> (WCAG 3.1.1)"
        )

    def test_standalone_templates_declare_html_lang(self):
        """
        WCAG 3.1.1 — Les templates standalone qui ne font pas extends doivent
        déclarer eux-mêmes l'attribut lang sur leur balise <html>.
        """
        missing = []
        for tpl in STANDALONE_TEMPLATES:
            content = tpl.read_text(encoding="utf-8")
            if not re.search(r"<html\s[^>]*lang=", content):
                missing.append(tpl.name)
        assert missing == [], (
            f"Templates standalone sans lang sur <html> (WCAG 3.1.1) : {missing}"
        )

    def test_start_html_lang_is_dynamic(self):
        """
        start.html utilise lang=%l (valeur dynamique injectée par le serveur)
        afin que la langue corresponde au choix de l'utilisateur.
        """
        content = read_template("start.html")
        assert "<html lang=%l>" in content, (
            "start.html doit avoir <html lang=%l> pour le rendu multi-langue dynamique"
        )

    def test_static_templates_lang_is_fr(self):
        """
        Les templates avec une langue fixe déclarent 'fr' comme langue
        par défaut cohérente avec la configuration serveur.
        """
        static_templates = ["server_config.html", "statistics.html"]
        for name in static_templates:
            content = read_template(name)
            assert 'lang="fr"' in content, (
                f"{name} : la langue par défaut déclarée doit être 'fr'"
            )

    def test_base_html_has_charset_utf8(self):
        """
        WCAG 3.1.1 (indirect) — base.html doit déclarer UTF-8 pour éviter
        les problèmes d'encodage avec les caractères accentués (é, à, ü, ø…).
        Les templates enfants héritent de cette déclaration.
        """
        content = read_template("base.html")
        assert 'charset="UTF-8"' in content or "charset='UTF-8'" in content, (
            "base.html : <meta charset='UTF-8'> absent"
        )

    def test_standalone_templates_have_charset_utf8(self):
        """
        Les templates standalone doivent déclarer leur propre charset UTF-8.
        """
        missing = []
        for tpl in STANDALONE_TEMPLATES:
            content = tpl.read_text(encoding="utf-8")
            if 'charset="UTF-8"' not in content and "charset='UTF-8'" not in content:
                missing.append(tpl.name)
        assert missing == [], (
            f"Templates standalone sans charset UTF-8 : {missing}"
        )

    # ------------------------------------------------------------------
    # WCAG 3.1.2 — 10 langues supportées dans start.html
    # ------------------------------------------------------------------

    def test_start_html_supported_langs_list(self):
        """
        WCAG 3.1.2 — start.html doit déclarer les 10 langues supportées
        dans l'array JavaScript `supportedLangs`.
        """
        content = read_template("start.html")
        required = ["de", "en", "es", "fr", "it", "lv", "nl", "no", "fi", "sv"]
        for lang_code in required:
            assert f'"{lang_code}"' in content, (
                f"start.html : code langue '{lang_code}' absent de supportedLangs"
            )

    def test_start_html_navigator_language_autodetect(self):
        """
        WCAG 3.1.2 — start.html doit auto-détecter la langue du navigateur
        via navigator.language pour une expérience accessible dès l'arrivée.
        """
        content = read_template("start.html")
        assert "navigator.language" in content, (
            "start.html : auto-détection de langue via navigator.language absente"
        )

    def test_start_html_language_fallback_to_english(self):
        """
        Un fallback vers l'anglais doit exister si la langue du navigateur
        n'est pas dans la liste supportée.
        """
        content = read_template("start.html")
        assert "fallback" in content.lower() or "userLang = 'en'" in content, (
            "start.html : le fallback vers 'en' pour les langues non supportées est absent"
        )

    # ------------------------------------------------------------------
    # WCAG 4.1.2 — Nom, rôle, valeur (ARIA sur le sélecteur de langue)
    # ------------------------------------------------------------------

    def test_start_html_dropdown_has_aria_haspopup(self):
        """
        WCAG 4.1.2 — Le bouton du sélecteur de langue doit déclarer
        aria-haspopup pour que les lecteurs d'écran annoncent le menu.
        """
        content = read_template("start.html")
        assert 'aria-haspopup="true"' in content, (
            "start.html : aria-haspopup='true' absent sur le bouton sélecteur de langue"
        )

    def test_start_html_dropdown_has_aria_expanded(self):
        """
        WCAG 4.1.2 — aria-expanded permet au lecteur d'écran d'annoncer
        si le menu déroulant est ouvert ou fermé.
        """
        content = read_template("start.html")
        assert 'aria-expanded="false"' in content, (
            "start.html : aria-expanded absent sur le bouton sélecteur de langue"
        )

    def test_start_html_dropdown_menu_has_aria_labelledby(self):
        """
        WCAG 4.1.2 — Le menu déroulant doit être lié à son bouton déclencheur
        via aria-labelledby pour une navigation clavier cohérente.
        """
        content = read_template("start.html")
        assert 'aria-labelledby="lang-dropdown"' in content, (
            "start.html : aria-labelledby absent sur le menu déroulant de langue"
        )

    def test_start_html_lang_dropdown_items_all_present(self):
        """
        Le sélecteur de langue de start.html doit proposer les 10 langues
        sous forme d'items de menu accessibles (<a class='dropdown-item'>).
        """
        content = read_template("start.html")
        lang_items = re.findall(r'data-lang="([a-z]{2})"', content)
        expected = {"de", "en", "es", "fr", "it", "lv", "nl", "no", "fi", "sv"}
        found = set(lang_items)
        missing = expected - found
        assert not missing, (
            f"start.html : langues manquantes dans le sélecteur : {missing}"
        )

    # ------------------------------------------------------------------
    # WCAG 1.1.1 — Texte alternatif sur les images
    # ------------------------------------------------------------------

    def test_start_html_img_has_alt(self):
        """
        WCAG 1.1.1 — L'image de l'arbre généalogique dans start.html
        doit avoir un attribut alt pour les utilisateurs de lecteurs d'écran.
        """
        content = read_template("start.html")
        img_tags = re.findall(r"<img[^>]+>", content)
        for img in img_tags:
            assert "alt=" in img, (
                f"start.html : <img> sans attribut alt trouvé : {img}"
            )

    def test_start_html_tree_img_alt_value(self):
        """
        L'image principale de l'arbre doit avoir un alt descriptif ('Tree')
        et non vide.
        """
        content = read_template("start.html")
        assert 'alt="Tree"' in content, (
            "start.html : l'image principale doit avoir alt=\"Tree\""
        )

    def test_all_templates_img_have_alt_attribute(self):
        """
        WCAG 1.1.1 — Aucune image dans les templates ne doit être dépourvue
        d'attribut alt (même les images décoratives doivent avoir alt='').
        """
        failures = []
        for tpl in ALL_TEMPLATES:
            content = tpl.read_text(encoding="utf-8")
            img_tags = re.findall(r"<img[^>]+>", content, re.IGNORECASE)
            for img in img_tags:
                if "alt=" not in img:
                    failures.append(f"{tpl.name}: {img[:80]}")
        assert failures == [], (
            f"Images sans attribut alt (WCAG 1.1.1) :\n" + "\n".join(failures)
        )

    # ------------------------------------------------------------------
    # WCAG 1.3.1 — Labels liés aux champs de formulaires
    # ------------------------------------------------------------------

    def test_add_family_all_labels_have_matching_inputs(self):
        """
        WCAG 1.3.1 — Dans add_family.html, chaque <label for='X'> doit avoir
        un élément de formulaire correspondant avec id='X'.
        """
        content = read_template("add_family.html")
        label_targets = _extract_label_for_values(content)
        input_ids = _extract_input_ids(content)
        orphan_labels = label_targets - input_ids
        assert not orphan_labels, (
            f"add_family.html : labels sans champ associé (WCAG 1.3.1) : {orphan_labels}"
        )

    def test_add_family_key_fields_have_labels(self):
        """
        WCAG 1.3.1 — Les champs principaux du formulaire d'ajout de famille
        doivent tous avoir un label explicitement lié.
        """
        content = read_template("add_family.html")
        required_pairs = {
            "pa1_fn": "First name",
            "pa1_sn": "Surname",
            "pa1_occupation": "Occupation",
            "pa2_fn": "First name",
            "pa2_sn": "Surname",
            "nsck": "Same sex couple",
        }
        for field_id, label_text in required_pairs.items():
            assert f'for="{field_id}"' in content, (
                f"add_family.html : label for='{field_id}' ('{label_text}') absent"
            )
            assert f'id="{field_id}"' in content, (
                f"add_family.html : input id='{field_id}' absent"
            )

    def test_server_config_all_labels_have_matching_inputs(self):
        """
        WCAG 1.3.1 — Dans server_config.html, chaque <label for='X'> doit
        avoir un champ correspondant avec id='X'.
        """
        content = read_template("server_config.html")
        label_targets = _extract_label_for_values(content)
        input_ids = _extract_input_ids(content)
        orphan_labels = label_targets - input_ids
        assert not orphan_labels, (
            f"server_config.html : labels sans champ associé (WCAG 1.3.1) : {orphan_labels}"
        )

    def test_server_config_lang_selector_has_label(self):
        """
        WCAG 1.3.1 — Le sélecteur de langue de la configuration serveur
        doit avoir un label lié (essentiel pour les lecteurs d'écran).
        """
        content = read_template("server_config.html")
        assert 'for="default_lang"' in content, (
            "server_config.html : label for='default_lang' absent"
        )
        assert 'id="default_lang"' in content, (
            "server_config.html : select id='default_lang' absent"
        )

    def test_server_config_ip_field_has_label(self):
        """
        WCAG 1.3.1 — Le champ de restriction IP doit avoir un label lié.
        """
        content = read_template("server_config.html")
        assert 'for="only"' in content and 'id="only"' in content, (
            "server_config.html : label/input pour le champ 'only' (IP) absent"
        )

    def test_server_config_7_lang_options(self):
        """
        Le sélecteur de langue de la config serveur doit proposer au moins 7 langues.
        """
        content = read_template("server_config.html")
        lang_options = re.findall(r'<option value="[a-z]{2}">', content)
        assert len(lang_options) >= 7, (
            f"server_config.html : seulement {len(lang_options)} options de langue "
            f"(minimum 7 attendu)"
        )


# ===========================================================================
# 2. Tests de la fonction gettext() (WCAG 3.1.2)
# ===========================================================================

class TestGettextTranslationFunction:
    """
    Vérifie que la fonction gettext() du routeur person.py traduit
    correctement les clés d'interface de l'anglais vers le français.
    """

    @pytest.fixture(autouse=True)
    def import_gettext(self):
        """Importe la fonction à tester une seule fois."""
        from src.geneweb.presentation.web.routers.person import gettext
        self.gettext = gettext

    def test_basic_info_translates_to_french(self):
        assert self.gettext("Basic Info") == "Informations de base"

    def test_spouse_and_children_translates_to_french(self):
        assert self.gettext("Spouse and Children") == "Conjoint et Enfants"

    def test_genealogy_tree_label_translates(self):
        assert self.gettext("Genealogy Tree (3 Generations)") == "Arbre généalogique (3 générations)"

    def test_siblings_label_translates(self):
        assert self.gettext("Siblings") == "Frères et Sœurs"

    def test_born_label_translates(self):
        assert self.gettext("Born") == "Né(e)"

    def test_in_preposition_translates(self):
        assert self.gettext("in") == "à"

    def test_died_label_translates(self):
        assert self.gettext("Died") == "Décédé(e)"

    def test_occupation_label_translates(self):
        assert self.gettext("Occupation") == "Profession"

    def test_on_preposition_translates(self):
        assert self.gettext("on") == "le"

    def test_with_preposition_translates(self):
        assert self.gettext("with") == "avec"

    def test_no_siblings_message_translates(self):
        assert self.gettext("No siblings found.") == "Aucun frère ou sœur trouvé."

    def test_unknown_key_falls_back_to_original(self):
        """Clé inconnue → retour du texte original (pas d'exception)."""
        assert self.gettext("Unknown key xyz") == "Unknown key xyz"

    def test_empty_string_fallback(self):
        """Chaîne vide → retour de la chaîne vide."""
        assert self.gettext("") == ""

    def test_all_translations_return_non_empty_string(self):
        """Aucune traduction ne doit retourner une chaîne vide."""
        known_keys = [
            "Basic Info", "Spouse and Children",
            "Genealogy Tree (3 Generations)", "Siblings",
            "Born", "in", "Died", "Occupation", "on", "with",
            "No siblings found.",
        ]
        for key in known_keys:
            result = self.gettext(key)
            assert isinstance(result, str), f"gettext('{key}') doit retourner str"
            assert len(result) > 0, f"gettext('{key}') retourne une chaîne vide"

    def test_translations_are_in_french(self):
        """Vérifie que les traductions contiennent des caractères accentués français."""
        french_chars = {"é", "à", "è", "ê", "ô", "î", "û", "ç", "œ"}
        translated_values = [
            self.gettext("Basic Info"),
            self.gettext("Siblings"),
            self.gettext("Born"),
            self.gettext("No siblings found."),
        ]
        combined = "".join(translated_values)
        found = french_chars.intersection(set(combined))
        assert found, (
            "Les traductions ne contiennent aucun caractère accentué français — "
            "vérifier que le dictionnaire n'est pas vide"
        )


# ===========================================================================
# 3. Tests des fichiers de localisation .po (WCAG 3.1.2)
# ===========================================================================

class TestLocalesPoFiles:
    """
    Vérifie l'intégrité des catalogues de traduction .po
    pour le français et l'anglais.
    """

    FR_PO = LOCALES_DIR / "fr" / "LC_MESSAGES" / "messages.po"
    EN_PO = LOCALES_DIR / "en" / "LC_MESSAGES" / "messages.po"

    REQUIRED_MSGIDS = [
        "Anniversaries",
        "Home",
        "Birthdays",
        "Anniversaries of dead people",
        "Wedding anniversaries",
        "Today",
        "Tomorrow",
        "No birthday today.",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    @staticmethod
    def _parse_po(path: Path) -> dict:
        """Parse un fichier .po et retourne un dict {msgid: msgstr}."""
        content = path.read_text(encoding="utf-8")
        entries = {}
        # Cherche les paires msgid/msgstr (hors header vide)
        pairs = re.findall(
            r'msgid\s+"([^"]+)"\s+msgstr\s+"([^"]*)"',
            content,
            re.MULTILINE,
        )
        for msgid, msgstr in pairs:
            entries[msgid] = msgstr
        return entries

    def test_fr_locale_file_exists(self):
        assert self.FR_PO.exists(), f"Fichier .po français introuvable : {self.FR_PO}"

    def test_en_locale_file_exists(self):
        assert self.EN_PO.exists(), f"Fichier .po anglais introuvable : {self.EN_PO}"

    def test_fr_locale_header_declares_language_fr(self):
        """Le header du fichier .po français doit déclarer Language: fr."""
        content = self.FR_PO.read_text(encoding="utf-8")
        assert "Language: fr" in content, (
            "locales/fr/messages.po : en-tête Language: fr absent"
        )

    def test_en_locale_header_declares_language_en(self):
        content = self.EN_PO.read_text(encoding="utf-8")
        assert "Language: en" in content, (
            "locales/en/messages.po : en-tête Language: en absent"
        )

    def test_fr_locale_has_all_required_msgids(self):
        """
        Tous les msgid d'interface obligatoires doivent être présents
        dans le catalogue français.
        """
        entries = self._parse_po(self.FR_PO)
        missing = [mid for mid in self.REQUIRED_MSGIDS if mid not in entries]
        assert not missing, (
            f"locales/fr/messages.po : msgid manquants : {missing}"
        )

    def test_en_locale_has_all_required_msgids(self):
        entries = self._parse_po(self.EN_PO)
        missing = [mid for mid in self.REQUIRED_MSGIDS if mid not in entries]
        assert not missing, (
            f"locales/en/messages.po : msgid manquants : {missing}"
        )

    def test_fr_locale_no_empty_msgstr_for_required_keys(self):
        """
        WCAG 3.1.2 — Aucune traduction obligatoire ne doit être vide
        dans le catalogue français.
        """
        entries = self._parse_po(self.FR_PO)
        empty = [k for k in self.REQUIRED_MSGIDS if entries.get(k, None) == ""]
        assert not empty, (
            f"locales/fr/messages.po : msgstr vides pour : {empty}"
        )

    def test_fr_locale_has_all_12_months(self):
        """
        Les 12 mois doivent être traduits en français pour l'affichage
        des anniversaires dans l'interface.
        """
        entries = self._parse_po(self.FR_PO)
        months_en = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        months_fr = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
        ]
        for en, fr in zip(months_en, months_fr):
            assert entries.get(en) == fr, (
                f"locales/fr/messages.po : '{en}' → attendu '{fr}', "
                f"obtenu '{entries.get(en)}'"
            )

    def test_both_locales_have_same_msgids(self):
        """
        Les catalogues fr et en doivent couvrir les mêmes clés pour éviter
        les chaînes non traduites dans l'une des langues.
        """
        fr_entries = self._parse_po(self.FR_PO)
        en_entries = self._parse_po(self.EN_PO)
        fr_keys = set(fr_entries.keys())
        en_keys = set(en_entries.keys())
        only_fr = fr_keys - en_keys
        only_en = en_keys - fr_keys
        assert not only_fr, f"Clés présentes dans fr mais pas dans en : {only_fr}"
        assert not only_en, f"Clés présentes dans en mais pas dans fr : {only_en}"

    def test_fr_locale_utf8_encoding(self):
        """Le fichier .po français doit être encodé en UTF-8 (charset déclaré)."""
        content = self.FR_PO.read_text(encoding="utf-8")
        assert "charset=utf-8" in content, (
            "locales/fr/messages.po : Content-Type charset=utf-8 absent"
        )


# ===========================================================================
# 4. Tests des modèles de configuration — langue persistante (WCAG 3.1.2)
# ===========================================================================

class TestConfigModelsDefaultLang:
    """
    Vérifie que la langue est configurable et persistée en base de données
    pour GenealogyConfig et ServerConfig.
    """

    def test_genealogy_config_has_default_lang_column(self):
        """
        GenealogyConfig doit avoir une colonne default_lang pour configurer
        la langue par défaut d'une généalogie.
        """
        from src.geneweb.infrastructure.config_models import GenealogyConfig
        columns = {col.key for col in GenealogyConfig.__table__.columns}
        assert "default_lang" in columns, (
            "GenealogyConfig : colonne 'default_lang' absente (WCAG 3.1.2)"
        )

    def test_server_config_has_default_lang_column(self):
        """
        ServerConfig doit avoir une colonne default_lang pour configurer
        la langue globale du serveur.
        """
        from src.geneweb.infrastructure.config_models import ServerConfig
        columns = {col.key for col in ServerConfig.__table__.columns}
        assert "default_lang" in columns, (
            "ServerConfig : colonne 'default_lang' absente (WCAG 3.1.2)"
        )

    def test_genealogy_config_default_lang_default_value_is_fr(self):
        """
        La valeur par défaut de default_lang dans GenealogyConfig doit être 'fr'
        pour garantir un comportement prévisible à la création.
        """
        from src.geneweb.infrastructure.config_models import GenealogyConfig
        col = GenealogyConfig.__table__.columns["default_lang"]
        assert col.default is not None, (
            "GenealogyConfig.default_lang : aucune valeur par défaut définie"
        )
        assert col.default.arg == "fr", (
            f"GenealogyConfig.default_lang : défaut attendu 'fr', obtenu '{col.default.arg}'"
        )

    def test_server_config_default_lang_default_value_is_fr(self):
        """
        La valeur par défaut de default_lang dans ServerConfig doit être 'fr'.
        """
        from src.geneweb.infrastructure.config_models import ServerConfig
        col = ServerConfig.__table__.columns["default_lang"]
        assert col.default is not None, (
            "ServerConfig.default_lang : aucune valeur par défaut définie"
        )
        assert col.default.arg == "fr", (
            f"ServerConfig.default_lang : défaut attendu 'fr', obtenu '{col.default.arg}'"
        )

    def test_genealogy_config_default_lang_is_string_type(self):
        """default_lang doit être un type String (pas Integer, pas Boolean)."""
        from sqlalchemy import String
        from src.geneweb.infrastructure.config_models import GenealogyConfig
        col = GenealogyConfig.__table__.columns["default_lang"]
        assert isinstance(col.type, String), (
            f"GenealogyConfig.default_lang : type attendu String, obtenu {type(col.type)}"
        )

    def test_server_config_default_lang_is_string_type(self):
        from sqlalchemy import String
        from src.geneweb.infrastructure.config_models import ServerConfig
        col = ServerConfig.__table__.columns["default_lang"]
        assert isinstance(col.type, String), (
            f"ServerConfig.default_lang : type attendu String, obtenu {type(col.type)}"
        )
