import hypothesis.strategies as st
from astropy.coordinates import SkyCoord
from hypothesis import given, settings

from starhash.core import StarHash


@st.composite
def valid_coordinates(draw: st.DrawFn) -> tuple[float, float]:
    """Generate valid coordinates."""
    ra = draw(st.floats(min_value=0, max_value=360.0, allow_nan=False, allow_infinity=False))
    dec = draw(st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False))
    return ra, dec


class TestRoundtrip:
    """Test that conversion between name and coordinates works."""

    @given(valid_coordinates())
    @settings(max_examples=1000, print_blob=True)
    def test_roundtrip(self, coords: tuple[float, float]) -> None:
        """Checks that we get the same coordinates back within 1 healpix resolution."""
        ra, dec = coords
        starhash = StarHash()

        words = starhash.coordinate_to_words(ra, dec)
        recovered_ra, recovered_dec = starhash.words_to_coordinate(words)

        orig_coord = SkyCoord(ra, dec, unit="deg")
        recovered_coord = SkyCoord(recovered_ra, recovered_dec, unit="deg")
        separation = orig_coord.separation(recovered_coord).to_value("arcmin")

        # Square pixels, so max distance allowable is from centre to corner
        # i.e. 1.4 * pixel resolution
        assert separation < 1.4 * starhash.healpix_resol
