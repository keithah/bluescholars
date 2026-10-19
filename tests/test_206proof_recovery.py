from restore.recovery_206proof import select_latest_vanilla


def test_select_latest_vanilla_keeps_queries_and_excludes_later_editions():
    rows = [
        {"timestamp": "20101201000000", "original": "http://206proof.com/forum/", "statuscode": "200", "mimetype": "text/html"},
        {"timestamp": "20120401000000", "original": "http://206proof.com/forum/", "statuscode": "200", "mimetype": "text/html"},
        {"timestamp": "20120402000000", "original": "http://206proof.com/forum/?page=2", "statuscode": "200", "mimetype": "text/html"},
        {"timestamp": "20130801000000", "original": "http://206proof.com/forum/", "statuscode": "200", "mimetype": "text/html"},
        {"timestamp": "20120403000000", "original": "http://206proof.com/forum/bad", "statuscode": "404", "mimetype": "text/html"},
        {"timestamp": "20120404000000", "original": "http://206proof.com/forum/style.css", "statuscode": "200", "mimetype": "text/css"},
    ]

    selected = select_latest_vanilla(rows)

    assert [(r["timestamp"], r["original"]) for r in selected] == [
        ("20120401000000", "http://206proof.com/forum/"),
        ("20120402000000", "http://206proof.com/forum/?page=2"),
    ]


def test_select_latest_vanilla_keeps_host_alias_as_distinct_source_identity():
    rows = [
        {"timestamp": "20120101000000", "original": "http://206proof.com/forum/", "statuscode": "200", "mimetype": "text/html"},
        {"timestamp": "20120301000000", "original": "http://www.206proof.com/forum/", "statuscode": "200", "mimetype": "text/html"},
    ]
    assert len(select_latest_vanilla(rows)) == 2
