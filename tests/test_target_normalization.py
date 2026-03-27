from dorkvault.services.target_normalization import (
    normalize_domain_target,
    normalize_target_input,
)


def test_normalize_domain_target_extracts_hostname_from_full_url() -> None:
    assert normalize_domain_target("https://ictcloudv.lk/") == "ictcloudv.lk"
    assert normalize_domain_target("https://www.example.com/login") == "www.example.com"
    assert normalize_domain_target("http://api.example.com/v1/users") == "api.example.com"


def test_normalize_domain_target_preserves_plain_domain_input() -> None:
    assert normalize_domain_target("example.com") == "example.com"
    assert normalize_domain_target("  example.com/  ") == "example.com"


def test_normalize_target_input_only_changes_domain_variables() -> None:
    domain_result = normalize_target_input(
        "https://www.example.com/login",
        variable_name="domain",
    )
    keyword_result = normalize_target_input(
        "https://www.example.com/login",
        variable_name="keyword",
    )

    assert domain_result.normalized_value == "www.example.com"
    assert domain_result.was_normalized is True
    assert domain_result.helper_text == "Using normalized domain: www.example.com"
    assert keyword_result.normalized_value == "https://www.example.com/login"
    assert keyword_result.was_normalized is False
    assert keyword_result.helper_text == ""
