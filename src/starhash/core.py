import logging
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

import rich_click as click
from click import Context, FloatRange
from ff3 import FF3Cipher
from healpy import ang2pix, nside2npix, nside2resol, pix2ang
from rich.logging import RichHandler

from starhash import __version__

logger = logging.getLogger(__name__)

# Reference implementation details
STARHASH_KEY = b"starhash!"
STARHASH_TWEAK = b"opensource"
HEALPIX_NSIDE = 65536
WORD_SEPARATOR = "-"

# Paths to bundled wordlists
EFF_LARGEWORDLIST_PATH = files("starhash.data").joinpath("eff_largewordlist.txt")
ASTROWORDLIST_PATH = files("starhash.data").joinpath("astronames_boost.txt")
COMBOLIST_PATH = files("starhash.data").joinpath("combolist.txt")


def setup_logger(level: int | str = logging.DEBUG) -> None:
    """
    Add a rich-formatted logger for development purposes with color output.
    """
    logger.setLevel(level=level)

    handler = RichHandler(
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True,
        show_time=True,
        show_level=True,
        show_path=True,
    )
    handler.setLevel(level=level)

    formatter = logging.Formatter(fmt="%(message)s", datefmt="[%Y-%m-%d %H:%M:%S]")
    handler.setFormatter(formatter)

    logger.addHandler(handler)


class StarHash:
    """Class to generate human-readable names from astronomical coordinates."""

    def __init__(
        self,
        key: bytes = STARHASH_KEY,
        tweak: bytes = STARHASH_TWEAK,
        healpix_nside: int = HEALPIX_NSIDE,
        wordlist_path: Path | Traversable = COMBOLIST_PATH,
        k_words: int = 3,
        init_logger: bool = False,
    ) -> None:
        self.word_separator = WORD_SEPARATOR
        self.wordlist: list[str] = []
        self.k_words = k_words
        self.wordlist_path = wordlist_path
        self.num_words: int = 0
        self.healpix_nside = healpix_nside
        self.healpix_resol = nside2resol(self.healpix_nside, arcmin=True)
        self.npix = nside2npix(self.healpix_nside)

        # Set size of padding appropriate to max healpix idx
        self.padding_length = len(str(self.npix))

        if init_logger:
            setup_logger(logging.DEBUG)

        self.coverage = 0
        logger.debug(
            "healpix grid properties: %i pixels with size %.1f arcsec",
            self.npix,
            self.healpix_resol * 60,
        )

        # Pad key to correct length
        self.key = key.ljust(32, b"\x00").hex()

        # Tweak must be 8 bytes long
        self.tweak = tweak[:8].hex()

        self.cipher = FF3Cipher(key=self.key, tweak=self.tweak)
        self.load_wordlist()

    def load_wordlist(self) -> None:
        """Load the word list specified in the class."""
        with self.wordlist_path.open() as f:
            self.wordlist = f.read().splitlines()
        self.num_words = len(self.wordlist)
        logger.debug("%s unique words in word list", self.num_words)
        self.coverage = pow(self.num_words, self.k_words) / self.npix
        logger.debug("Grid coverage factor: %.3f x", self.coverage)

        if self.coverage < 1:
            raise IncompleteHEALPixCoverageError

    def coordinate_to_words(self, ra: float, dec: float) -> str:
        idx = ang2pix(self.healpix_nside, ra, dec, lonlat=True)
        stridx = str(idx).zfill(self.padding_length)

        idx_encrypted = int(self.cipher.encrypt(stridx))

        # Repeated modulo division recovers the indices
        words: list[str] = []
        temp = idx_encrypted
        for _ in range(self.k_words):
            words.append(self.wordlist[temp % self.num_words])

            temp //= self.num_words

        return self.word_separator.join(words)

    def words_to_coordinate(self, input_word_str: str) -> tuple[float, float]:
        indices = [self.wordlist.index(w) for w in input_word_str.split(self.word_separator)]

        # Undo the modulo procedure above to recover the original index
        idx_encrypted = sum(word_idx * (self.num_words**i) for i, word_idx in enumerate(indices))

        stridx_encrypted = str(idx_encrypted).zfill(self.padding_length)
        stridx_decrypted = self.cipher.decrypt(stridx_encrypted)
        idx = int(stridx_decrypted)

        if idx > self.npix:
            raise InvalidHEALPixIndexError

        ra, dec = pix2ang(self.healpix_nside, idx, lonlat=True)

        return ra, dec


def collate_wordlist() -> list[str]:
    wordlist = []
    with EFF_LARGEWORDLIST_PATH.open() as f:
        logger.debug("Loading EFF wordlist")

        for line in f.read().splitlines():
            if "#" not in line:
                try:
                    wordlist.append(line.split("\t")[1].replace(" ", "").replace("-", " "))
                except IndexError:
                    logger.exception(line)
                    continue
    with ASTROWORDLIST_PATH.open() as f:
        logger.debug("Loading astronomical wordlist")
        wordlist.extend(f.read().splitlines())

    return sorted(set(wordlist))


class IncompleteHEALPixCoverageError(Exception):
    """The chosen StarHash parameters do not fully cover the chosen HEALPix grid."""


class InvalidHEALPixIndexError(Exception):
    """The given coordinates map to an invalid HEALPix index."""


@click.group(context_settings={"show_default": True})
@click.version_option(__version__, prog_name="starhash-cli")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging output")
@click.pass_context
def cli(ctx: Context, verbose: bool) -> None:
    ctx.obj = StarHash(init_logger=verbose)


@cli.command()
@click.option("--ra", "-r", type=FloatRange(min=0, max=360), required=True)
@click.option("--dec", "-d", type=FloatRange(min=-90, max=90), required=True)
@click.pass_obj
def get_name_from_coord(sh: StarHash, ra: float, dec: float) -> None:
    """Get name corresponding to ra, dec."""
    name = sh.coordinate_to_words(ra, dec)
    click.echo(name)


@cli.command()
@click.argument("name", type=str)
@click.pass_obj
def get_coord_from_name(sh: StarHash, name: str) -> None:
    """Get ra and dec corresponding to name."""
    ra, dec = sh.words_to_coordinate(name)
    click.echo(f"{ra} {dec}")


if __name__ == "__main__":
    cli()
