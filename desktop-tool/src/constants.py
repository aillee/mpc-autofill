import re
from enum import Enum, StrEnum, member
from functools import partial

import attr

import src.webdrivers as wd


class SourceType:
    AWS_S3 = "AWS S3"
    GOOGLE_DRIVE = "Google Drive"
    LOCAL_FILE = "Local File"

    @staticmethod
    def get_all() -> list[str]:
        return [SourceType.AWS_S3, SourceType.GOOGLE_DRIVE, SourceType.LOCAL_FILE]


class OrderFulfilmentMethod(StrEnum):
    new_project = "Create a new project (default)"
    append_to_project = "Add more cards to an existing project"
    continue_project = "Continue editing an existing project"

    def __str__(self) -> str:
        return self.value


class States(StrEnum):
    initialising = "Initialising"
    initialised = "Initialised"
    defining_order = "Defining Order"
    paging_to_fronts = "Paging to Fronts"
    paging_to_backs = "Paging to Backs"
    paging_to_review = "Paging to Review"
    inserting_fronts = "Inserting Fronts"
    inserting_backs = "Inserting Backs"
    finished = "Finished"


class Faces(StrEnum):
    front = "Front"
    back = "Back"


class Cardstocks(StrEnum):
    S27 = "(S27) Smooth"
    S30 = "(S30) Standard Smooth"
    S33 = "(S33) Superior Smooth"
    M31 = "(M31) Linen"
    P10 = "(P10) Plastic"


class BaseTags(StrEnum):
    details = "details"
    fronts = "fronts"
    backs = "backs"
    cardback = "cardback"
    filepath = "filepath"


class DetailsTags(StrEnum):
    quantity = "quantity"
    stock = "stock"
    foil = "foil"
    finish = "finish"


class CardFinish(StrEnum):
    """Canonical print types an order can name without using an MPC effect code."""

    none = "none"
    holographic = "holographic"
    shards = "shards"


class CardTags(StrEnum):
    id = "id"
    source_type = "sourceType"
    slots = "slots"
    name = "name"
    query = "query"


class Browsers(Enum):
    chrome = member(partial(wd.get_chrome_driver))
    brave = member(partial(wd.get_brave_driver))
    edge = member(partial(wd.get_edge_driver))
    # TODO: add support for firefox


# Google Drive API constants
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly", "https://www.googleapis.com/auth/drive.readonly"]
SERVICE_ACC_FILENAME = "client_secrets.json"


class ImageResizeMethods(Enum):
    NEAREST = 0
    BOX = 4
    BILINEAR = 2
    HAMMING = 5
    BICUBIC = 3
    LANCZOS = 1


# MakePlayingCards `dro_product_effect` option values.
#
# publish.js `renderEffectInfo()` fills that dropdown from
# GET https://www.makeplayingcards.com/api/publish/getproducteffectinfo.ashx
#     ?unitno=<hidd_itemid>&attachno=<dro_paper_type value>&minPieces=18&pieces=<bracket>
# on https://www.makeplayingcards.com/design/custom-blank-card.html
# (Custom Game Cards, 63x88mm, product code PC140626-01, hidd_itemid C380050185D1C1AF).
# Queried 2026-11-27 with attachno PA_014, the option value for "(S30) Standard Smooth",
# at brackets 18, 36, 55, and 612. The same EffectNo values came back for S27 (PA_016),
# S33 (PA_059), and M31 (PA_015):
#   EF_055  "Holographic (front)"                         EffectGroup HOLOGRAPHIC
#   EF_580  "Holographic silver foil shards (front)"      EffectGroup HGCSHARD
# Selenium selects EffectNo. "Full color print" is the empty-value default and is not
# in that response. P10 (PA_017) returned no print types.
HOLOGRAPHIC_FRONT_CODE = "EF_055"
SILVER_SHARDS_FRONT_CODE = "EF_580"

_EFFECT_CODE = re.compile(r"EF_[0-9A-Z]+")
_FINISH_ALIASES: dict[str, tuple[str, bool]] = {
    "none": (CardFinish.none, False),
    "nonfoil": (CardFinish.none, False),
    "non-foil": (CardFinish.none, False),
    "full color print": (CardFinish.none, False),
    "full colour print": (CardFinish.none, False),
    "holographic": (CardFinish.holographic, True),
    "holographic (front)": (CardFinish.holographic, True),
    "foil": (CardFinish.holographic, True),
    "shards": (CardFinish.shards, True),
    "holographic silver foil shards": (CardFinish.shards, True),
    "holographic silver foil shards (front)": (CardFinish.shards, True),
    "holographic silver foil shards front": (CardFinish.shards, True),
}


def resolve_finish(finish: str, foil: bool) -> tuple[str, bool] | None:
    """
    Map an XML `<finish>` string to a canonical finish and whether it is a foil print type.
    An empty finish means the element was omitted: `<foil>true</foil>` stays holographic.
    """

    text = finish.strip()
    if text == "":
        if foil:
            return CardFinish.holographic, True
        return CardFinish.none, False
    alias = _FINISH_ALIASES.get(text.lower())
    if alias is not None:
        return alias
    code = text.upper()
    if code == HOLOGRAPHIC_FRONT_CODE:
        return CardFinish.holographic, True
    if code == SILVER_SHARDS_FRONT_CODE:
        return CardFinish.shards, True
    if _EFFECT_CODE.fullmatch(code):
        return code, True
    return None


@attr.s
class TargetSite:
    """
    A simple dataclass representing a site within the MakePlayingCards group which the desktop tool can target.
    Any interactions with the site that aren't customisable through this class are presumed to work identically
    across all sites which the tool can target.
    """

    # region URLs
    base_url: str = attr.ib()
    starting_url_route: str = attr.ib()
    login_url_route: str = attr.ib(default="login.aspx")
    logout_url_route: str = attr.ib(default="logout.aspx")
    saved_projects_url_route: str = attr.ib(default="design/dn_temporary_designes.aspx")
    insert_fronts_url_route: str = attr.ib(default="products/playingcard/design/dn_playingcards_front_dynamic.aspx")
    accept_settings_url_route: str = attr.ib(default="products/pro_item_process_flow.aspx")
    # endregion
    # region project configuration
    supports_foil: bool = attr.ib(default=True)
    quantity_dropdown_element_id: str = attr.ib(default="dro_choosesize")
    cardstock_dropdown_element_id: str = attr.ib(default="dro_paper_type")
    print_type_dropdown_element_id: str = attr.ib(default="dro_product_effect")
    foil_dropdown_element_value: str = attr.ib(default=HOLOGRAPHIC_FRONT_CODE)
    shards_dropdown_element_value: str = attr.ib(default=SILVER_SHARDS_FRONT_CODE)
    cardstock_site_name_mapping: dict[Cardstocks, str] = attr.ib(
        default={cardstock: cardstock.value for cardstock in Cardstocks}
    )
    # endregion
    # region save states
    saved_successfully_text: str = attr.ib(default="Saved successfully")
    # endregion

    def format_url(self, url: str) -> str:
        return f"{self.base_url}/{url}"

    @property
    def starting_url(self) -> str:
        return self.format_url(self.starting_url_route)

    @property
    def login_url(self) -> str:
        return self.format_url(self.login_url_route)

    @property
    def logout_url(self) -> str:
        return self.format_url(self.logout_url_route)

    @property
    def saved_projects_url(self) -> str:
        return self.format_url(self.saved_projects_url_route)

    @property
    def insert_fronts_url(self) -> str:
        return self.format_url(self.insert_fronts_url_route)

    @property
    def accept_settings_url(self) -> str:
        return self.format_url(self.accept_settings_url_route)


class TargetSites(Enum):
    MakePlayingCards = TargetSite(
        base_url="https://www.makeplayingcards.com", starting_url_route="design/custom-blank-card.html"
    )
    PrinterStudio = TargetSite(
        base_url="https://www.printerstudio.com",
        starting_url_route="personalized/custom-playing-cards-blank-cards.html",
        supports_foil=False,
        cardstock_site_name_mapping={
            Cardstocks.S30: "Standard (smooth)",
            Cardstocks.S33: "Superior (smooth)",
            Cardstocks.M31: "Premium (linen)",
            Cardstocks.P10: "Plastic (100%)",
        },
    )
    PrinterStudioUK = TargetSite(
        base_url="https://www.printerstudio.co.uk",
        starting_url_route="personalised/custom-playing-cards-blank-cards.html",
        supports_foil=False,
        cardstock_site_name_mapping={
            Cardstocks.S30: "Standard (smooth)",
            Cardstocks.S33: "Superior (smooth)",
            Cardstocks.M31: "Premium (linen)",
            Cardstocks.P10: "Plastic (100%)",
        },
    )
    PrinterStudioDE = TargetSite(
        base_url="https://www.printerstudio.de",
        starting_url_route="machen/blanko-spielkarten-63x88mm-personalisieren.html",
        supports_foil=False,
        saved_successfully_text="Speicherung erfolgreich",
        cardstock_site_name_mapping={
            Cardstocks.S30: "Standard (glatt)",
            Cardstocks.S33: "Super (glatt)",
            Cardstocks.M31: "Premium (linen)",
            Cardstocks.P10: "Kunststoff",
        },
    )
    PrinterStudioES = TargetSite(
        base_url="https://www.printerstudio.es",
        starting_url_route="personalizado/tarjetas-personalizadas-en-blanco.html",
        supports_foil=False,
        saved_successfully_text="Guardado satisfactoriamente",
        cardstock_site_name_mapping={
            Cardstocks.S30: "Estándar (suave)",
            Cardstocks.S33: "Superior (suave)",
            Cardstocks.M31: "De priméra calidad (lino)",
            Cardstocks.P10: "Plástico (suave)",
        },
    )
    PrinterStudioFR = TargetSite(
        base_url="https://www.printerstudio.fr",
        starting_url_route="personnalise/cartes-de-jeu-sur-mesure-cartes-blanches.html",
        supports_foil=False,
        saved_successfully_text="Enregistré avec succès",
        cardstock_site_name_mapping={
            Cardstocks.S30: "Standard (lisse)",
            Cardstocks.S33: "Supérieur (lisse)",
            Cardstocks.M31: "Premium (lin)",
            Cardstocks.P10: "Plastique (100%)",
        },
    )


DPI_HEIGHT_RATIO = 300 / 1110  # TODO: share this between desktop tool and backend


PROJECT_MAX_SIZE = 612  # shared between target sites
THREADS = 5  # shared between CardImageCollections

POST_LAUNCH_HTML_FILENAME = "post-launch.html"
