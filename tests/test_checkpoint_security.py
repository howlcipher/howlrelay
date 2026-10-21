"""Adversarial checkpoint inputs use synthetic data only."""
import json
import os
import subprocess
from pathlib import Path

import pytest

from howlrelay.adapters.checkpoint import CheckpointCollector
from tests.test_checkpoint_collector import FIXTURE, bundle


@pytest.mark.parametrize('field,value', [
    ('safe_to_resume', 'false'), ('completed', 123), ('remaining', [1]),
    ('task_id', None), ('status', 'invented'), ('last_verified_commit', 'xyz'),
    ('worker', {'role': 2}), ('unknown', True),
    ('created_at', '2026-W43-3T12:00:00Z'),
    ('verification', {'independent': 'true', 'checks': []}),
])
def test_rejects_invalid_schema(tmp_path, field, value):
    target = bundle(tmp_path) / 'checkpoint.json'
    data = json.loads(target.read_text())
    data[field] = value
    target.write_text(json.dumps(data))
    assert CheckpointCollector().collect(tmp_path) == []


def test_rejects_missing_required_fields(tmp_path):
    (tmp_path / 'checkpoint.json').write_text(json.dumps({
        'schema_version': 'howlforge.checkpoint/v1', 'safe_to_resume': True,
        'remaining': ['synthetic instruction'],
    }))
    assert CheckpointCollector().collect(tmp_path) == []


def test_symlink_cannot_escape(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    (repo / 'checkpoint.json').symlink_to(FIXTURE.resolve())
    assert CheckpointCollector().collect(repo) == []


@pytest.mark.skipif(os.name != 'posix', reason='POSIX FIFO')
def test_fifo_does_not_block(tmp_path):
    os.mkfifo(tmp_path / 'checkpoint.json')
    result = subprocess.run([
        os.sys.executable, '-c',
        'from pathlib import Path; from howlrelay.adapters.checkpoint import '
        'CheckpointCollector; assert CheckpointCollector().collect(Path('
        + repr(str(tmp_path)) + ')) == []',
    ], env={**os.environ, 'PYTHONPATH': str(Path(
        __import__('howlrelay.adapters.checkpoint', fromlist=['x']).__file__
    ).parents[2])}, timeout=2)
    assert result.returncode == 0


def test_rejects_oversized_file(tmp_path):
    data = json.loads(FIXTURE.read_text())
    data['notes'] = 'x' * (1024 * 1024 + 1)
    (tmp_path / 'checkpoint.json').write_text(json.dumps(data))
    assert CheckpointCollector().collect(tmp_path) == []


def test_swapped_parent_directory_is_not_followed(tmp_path):
    target = bundle(tmp_path)
    collector = CheckpointCollector()
    (path,) = collector.discover(tmp_path)
    target.rename(target.with_name('original'))
    target.symlink_to(FIXTURE.parent.resolve(), target_is_directory=True)
    with pytest.raises(OSError):
        collector.load(path, tmp_path)


def test_discovery_entry_budget(tmp_path, monkeypatch):
    import howlrelay.adapters.checkpoint as module
    monkeypatch.setattr(module, '_MAX_ENTRIES', 3)
    for i in range(10):
        bundle(tmp_path, str(i))
    assert len(CheckpointCollector().discover(tmp_path)) <= 3


def test_checkpoint_provenance_is_not_authority(tmp_path):
    import hashlib
    target = bundle(tmp_path) / 'checkpoint.json'
    (evidence,) = CheckpointCollector().collect(tmp_path)
    assert evidence.metadata['source_sha256'] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert evidence.metadata['authorization'] == 'none; worker assertion only'


def test_descriptor_declares_checkpoint_schema():
    from howlrelay.cli.main import main
    import contextlib
    import io
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        assert main(['interop', '--json']) == 0
    descriptor = json.loads(output.getvalue())
    for command in descriptor['commands']:
        if command['path'] in [['handoff'], ['status'], ['brief']]:
            assert 'howlforge.checkpoint/v1' in command['accepts']
