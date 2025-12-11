code_map = {
    "AB": "01",
    "BC": "02",
    "MB": "03",
    "NB": "04",
    "NL": "05",
    "NS": "07",
    "ON": "08",
    "PE": "09",
    "QC": "10",
    "SK": "11",
    "YT": "12",
    "NT": "13",
    "NU": "14",
}


class Plugin:
    def postal_code_pre(self, parser, item):
        country_code = item["countryCode"]
        if country_code != "CA":
            return

        admin_code = item.get("admin1Code")
        if admin_code in code_map:
            item["admin1Code"] = code_map[admin_code]
        elif admin_code:
            parser.logger.warning(
                "Unknown Canadian province/territory code '%s' for postal code %s",
                admin_code,
                item.get("postalCode", "unknown"),
            )
            # Keep the original code if not in map
            item["admin1Code"] = admin_code
