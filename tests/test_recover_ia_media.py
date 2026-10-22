from pathlib import Path

from scripts.recover_ia_media import _valid_media, SELECTED, aggregate_items


def test_validates_archive_ogg_audio_signature_and_mime(tmp_path: Path) -> None:
    payload = tmp_path / "broadcast.ogg"
    payload.write_bytes(b"OggS" + b"\x00" * 12)

    assert _valid_media(payload, "audio/ogg", "broadcast.ogg")
    assert _valid_media(payload, "application/ogg", "broadcast.ogg")
    assert not _valid_media(payload, "text/html", "broadcast.ogg")


def test_rejects_html_disguised_as_ogg(tmp_path: Path) -> None:
    payload = tmp_path / "broadcast.ogg"
    payload.write_bytes(b"<html>archive error</html>")

    assert not _valid_media(payload, "audio/ogg", "broadcast.ogg")


def test_selects_smallest_original_amateur_hour_program_master() -> None:
    assert SELECTED["AmateurHourEpisode2WhyWerePissed_6"] == ["WhyWerePissed.ogg"]


def test_preserves_track_level_blue_scholars_catalog_files() -> None:
    assert SELECTED["Duck_Down_-_Download_The_Right_Thing-2009"] == [
        "13-Blue_Scholars_-_Hi_808.ogg",
        "15-Blue_Scholars_-_Coo.ogg",
    ]
    assert SELECTED["pandacd-442-the-remix-files-volume-7"] == [
        "01-Thomax-Fire_For_The_People_REMIX_(Blue_Scholars).mp3"
    ]
    assert SELECTED["sc21wa-Teach_Truth_-_Unbanning_Books_in_Public_Schools"] == [
        "Teach_Truth_-_Unbanning_Books_in_Public_Schools.mp3"
    ]


def test_aggregate_media_summary_uses_all_durable_files() -> None:
    summary = aggregate_items({
        "one": {"licenseurl": "CC", "files": {
            "a": {"filename": "song.mp3", "bytes": 10, "sha256": "same"},
            "b": {"filename": "mix.ogg", "bytes": 8, "sha256": "other"},
        }},
        "two": {"files": {
            "c": {"filename": "copy.mp3", "bytes": 10, "sha256": "same"},
        }},
    })
    assert summary["items"] == 2
    assert summary["source_files"] == 3
    assert summary["unique_payloads"] == 2
    assert summary["source_bytes"] == 28
    assert summary["unique_bytes"] == 18
    assert summary["new_file_types"] == {"MP3": 2, "OGG": 1}
