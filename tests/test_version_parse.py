"""Tests for semver parsing and version utilities."""

from smt_index.util import SemVer, sort_versions


class TestSemVerParse:
    """Tests for SemVer.parse()."""

    def test_full_version(self) -> None:
        v = SemVer.parse("1.2.3")
        assert v is not None
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_two_part_version(self) -> None:
        v = SemVer.parse("2.5")
        assert v is not None
        assert v.major == 2
        assert v.minor == 5
        assert v.patch == 0

    def test_single_part_version(self) -> None:
        v = SemVer.parse("3")
        assert v is not None
        assert v.major == 3
        assert v.minor == 0
        assert v.patch == 0

    def test_v_prefix_lowercase(self) -> None:
        v = SemVer.parse("v1.0.0")
        assert v is not None
        assert v.major == 1

    def test_v_prefix_uppercase(self) -> None:
        v = SemVer.parse("V2.1")
        assert v is not None
        assert v.major == 2
        assert v.minor == 1

    def test_invalid_version_letters(self) -> None:
        assert SemVer.parse("abc") is None

    def test_invalid_version_empty(self) -> None:
        assert SemVer.parse("") is None

    def test_invalid_version_mixed(self) -> None:
        assert SemVer.parse("1.a.2") is None


class TestSemVerComparison:
    """Tests for SemVer comparison operators."""

    def test_equality(self) -> None:
        assert SemVer(1, 2, 3) == SemVer(1, 2, 3)
        assert SemVer(1, 0, 0) == SemVer(1, 0, 0)

    def test_less_than_major(self) -> None:
        assert SemVer(1, 0, 0) < SemVer(2, 0, 0)

    def test_less_than_minor(self) -> None:
        assert SemVer(1, 1, 0) < SemVer(1, 2, 0)

    def test_less_than_patch(self) -> None:
        assert SemVer(1, 1, 1) < SemVer(1, 1, 2)

    def test_greater_than(self) -> None:
        assert SemVer(2, 0, 0) > SemVer(1, 9, 9)

    def test_sorting(self) -> None:
        versions = [SemVer(1, 0, 0), SemVer(3, 0, 0), SemVer(2, 0, 0)]
        sorted_v = sorted(versions)
        assert sorted_v == [SemVer(1, 0, 0), SemVer(2, 0, 0), SemVer(3, 0, 0)]


class TestSemVerStr:
    """Tests for SemVer string representation."""

    def test_str_full(self) -> None:
        assert str(SemVer(1, 2, 3)) == "1.2.3"

    def test_str_zeros(self) -> None:
        assert str(SemVer(1, 0, 0)) == "1.0.0"


class TestSemVerFromPathParts:
    """Tests for SemVer.from_path_parts()."""

    def test_three_parts(self) -> None:
        v = SemVer.from_path_parts(["3", "0", "1"])
        assert v is not None
        assert str(v) == "3.0.1"

    def test_two_parts(self) -> None:
        v = SemVer.from_path_parts(["2", "1"])
        assert v is not None
        assert str(v) == "2.1.0"

    def test_one_part_invalid(self) -> None:
        assert SemVer.from_path_parts(["1"]) is None

    def test_empty_invalid(self) -> None:
        assert SemVer.from_path_parts([]) is None

    def test_non_numeric_invalid(self) -> None:
        assert SemVer.from_path_parts(["a", "b"]) is None


class TestSortVersions:
    """Tests for sort_versions utility."""

    def test_sort_descending(self) -> None:
        versions = ["1.0.0", "3.0.0", "2.0.0"]
        result = sort_versions(versions, reverse=True)
        assert result == ["3.0.0", "2.0.0", "1.0.0"]

    def test_sort_ascending(self) -> None:
        versions = ["1.0.0", "3.0.0", "2.0.0"]
        result = sort_versions(versions, reverse=False)
        assert result == ["1.0.0", "2.0.0", "3.0.0"]

    def test_invalid_versions_at_end(self) -> None:
        versions = ["2.0.0", "invalid", "1.0.0"]
        result = sort_versions(versions, reverse=True)
        assert result[0] == "2.0.0"
        assert result[1] == "1.0.0"
        assert result[2] == "invalid"

    def test_complex_sorting(self) -> None:
        versions = ["1.1.0", "1.0.0", "1.1.1", "2.0.0"]
        result = sort_versions(versions, reverse=True)
        assert result == ["2.0.0", "1.1.1", "1.1.0", "1.0.0"]
