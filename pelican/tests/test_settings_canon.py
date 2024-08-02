#
#  Focused on settings.py/canonicalization_module_name()
#
#
# To see collection/ordering of a fixture for a specific function, execute:
#
#  pytest -n0 --setup-plan \
#  test_settings_canon.py::TestSettingsCanonical::test_first_char

from pelican.settings import canonicalize_module_name, validate_module_name


##########################################################################
#  All about the handling of module name
##########################################################################
class TestSettingsCanon:
    """validate_module_name()"""

    ##########################################################################
    #  Function-specific (per unit test) fixtures with focus on module name
    ##########################################################################
    def test_reject_first_digit_pass(self):
        bad_module_name = "1st_search"

        assert validate_module_name(bad_module_name) is False

    def test_reject_last_digit_pass(self):
        bad_module_name = "paramount2"

        assert validate_module_name(bad_module_name) is False

    def test_reject_not_identifier_pass(self):
        bad_module_name = "bad-module"

        assert validate_module_name(bad_module_name) is False

    def test_reject_multiple_underscores_pass(self):
        bad_module_name = "bad__module"

        assert validate_module_name(bad_module_name) is False


class TestSettingsCanonNormalize:
    """canonicalization_module_name()"""

    def test_normalize_dash(self):
        """Replace all dash into underscore"""
        funky_modname = "zippy-ity-doo-dah"
        expected_modname = "zippy_ity_doo_dah"

        assert canonicalize_module_name(funky_modname) == expected_modname

    def test_normalize_period(self):
        """Replace any and all period into an underscore"""
        funky_modname = "how.deep.the.rabbit.hole.goes"
        expected_modname = "how_deep_the_rabbit_hole_goes"

        assert canonicalize_module_name(funky_modname) == expected_modname

    def test_normalize_double_underscore(self):
        """Reduce double underscore symbols into a single underscore"""
        funky_modname = "snake_case__makes__a_____great_case"
        expected_modname = "snake_case_makes_a_great_case"

        assert canonicalize_module_name(funky_modname) == expected_modname

    def test_normalize_lowercase(self):
        """Force to all lower-case"""
        funky_modname = "SnAke_CaSe_MaKeS_a_gReaT_casE"
        expected_modname = "snake_case_makes_a_great_case"

        assert canonicalize_module_name(funky_modname) == expected_modname


# Python: Minimum required versions: 2.3, 3.0  (vermin v1.6.0)
