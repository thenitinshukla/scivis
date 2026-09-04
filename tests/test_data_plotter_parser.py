from pathlib import Path
import numpy as np
import pytest
from scientific_visualization.data_plotter.parser import Delimiter, parse_text_file

def test_parse_csv_with_header_comments_and_invalid(tmp_path):
    p = tmp_path / "sample.csv"
    p.write_text("# comment\nTime,Energy\n0,1\n1,bad\n2,3\n", encoding="utf-8")
    result = parse_text_file(p, Delimiter.AUTO)
    assert result.has_header is True
    assert result.columns == ["Time", "Energy"]
    assert result.skipped_comments == 1
    assert np.isnan(result.values[1, 1])

def test_parse_whitespace_txt_without_header(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("0 1\n1 2\n2 3\n", encoding="utf-8")
    result = parse_text_file(p)
    assert result.has_header is False
    assert result.values.shape == (3, 2)
    assert result.delimiter == " "

def test_parse_empty_file_fails(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        parse_text_file(p)


def test_batch_multiple_files(tmp_path):
    from scientific_visualization.data_plotter.batch import parse_many
    a = tmp_path / "a.csv"
    b = tmp_path / "b.txt"
    a.write_text("x,y\n1,2\n2,4\n", encoding="utf-8")
    b.write_text("x y\n1 3\n2 6\n", encoding="utf-8")
    result = parse_many([str(a), str(b)])
    assert len(result.datasets) == 2
    assert not result.errors


def test_aligned_whitespace_header_preserves_multiword_column_names(tmp_path):
    from scientific_visualization.data_plotter.parser import parse_text_file
    p = tmp_path / "results.txt"
    p.write_text(
        "Node    Total GPUs      Simulation time\n"
        "1       4       2258.420700163\n"
        "4       16      579.611673147\n"
    )
    result = parse_text_file(p)
    assert result.has_header
    assert result.columns == ["Node", "Total GPUs", "Simulation time"]
    assert result.values.shape == (2, 3)
