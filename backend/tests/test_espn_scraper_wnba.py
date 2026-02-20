from app.services.data_fetchers.espn_scraper import ESPNScraper


def test_espn_scraper_resolves_wnba_base_url():
    scraper = ESPNScraper()
    assert scraper._get_base_url("wnba").endswith("/sports/basketball/wnba")
    assert scraper._get_base_url("basketball_wnba").endswith("/sports/basketball/wnba")


def test_espn_scraper_resolves_wnba_team_abbreviation():
    scraper = ESPNScraper()
    assert scraper._get_team_abbr("Las Vegas Aces", "wnba") == "LV"
    assert scraper._get_team_abbr("New York Liberty", "basketball_wnba") == "NY"
