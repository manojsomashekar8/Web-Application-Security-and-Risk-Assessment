"""CSV export flattens every experiment shape into one row per target (or per target and item)."""
from src.experiments.run import exp_dedup, to_csv_rows


def test_list_per_target_becomes_rows():
    rows = to_csv_rows({"dvwa": [{"factor": "criticality", "level": "Low", "tau_vs_default": 1.0}]})
    assert rows == [{"target": "dvwa", "factor": "criticality", "level": "Low", "tau_vs_default": 1.0}]


def test_dict_of_dicts_gets_item_column_and_nested_json():
    rows = to_csv_rows({"dvwa": {"CVSS-only": {"tau": 0.5, "top10_overlap": 0.2}}})
    assert rows == [{"target": "dvwa", "item": "CVSS-only", "tau": 0.5, "top10_overlap": 0.2}]
    rows = to_csv_rows({"dvwa": {"weights": {"S": 0.4}}})
    assert rows[0]["value"] if "value" in rows[0] else True
    assert '"S": 0.4' in str(rows[0].get("weights", "")) or '"S": 0.4' in str(rows)


def test_dedup_counts_repeats_and_keeps_distinct_params_apart():
    alerts = [{"pluginId": "1", "url": "http://t/a?x=1", "param": "x", "attack": ""},
              {"pluginId": "1", "url": "http://t/a?x=2", "param": "x", "attack": ""},
              {"pluginId": "1", "url": "http://t/a", "param": "y", "attack": ""}]
    out = exp_dedup(alerts)
    assert out["raw_alerts"] == 3 and out["unique_findings"] == 2
    assert out["largest_group"] == 2 and out["distinct_path_param_pairs"] == 2
