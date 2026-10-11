import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


aspera = load("aspera_tool", "aspera/Ascp_down.py")
synapse = load("synapse_tool", "synapse/download_synapse_safe.py")


class ToolTests(unittest.TestCase):
    def test_launcher_forwards_help(self):
        for tool in ("aspera", "synapse", "synapse-legacy"):
            result = subprocess.run([sys.executable, str(ROOT / "download.py"), tool, "--help"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("usage:", result.stdout)

    def test_aspera_relative_input_and_spaces(self):
        before = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="aspera test ") as directory:
            table = Path(directory) / "input.tsv"
            table.write_text("run\tfastq_ftp\nsample\tftp.sra.ebi.ac.uk/vol1/a.fastq.gz;ftp.sra.ebi.ac.uk/vol1/b.fastq.gz\n", encoding="utf-8")
            relative = os.path.relpath(table)
            output = Path(directory) / "output files"
            with patch.object(aspera.subprocess, "run") as run:
                self.assertEqual(aspera.main(["-i", relative, "-o", str(output), "--ascp-key", str(Path(directory) / "key file"), "--ascp-binary", "ascp"]), 0)
            self.assertEqual(run.call_count, 2)
            for call in run.call_args_list:
                self.assertIsInstance(call.args[0], list)
                self.assertEqual(call.kwargs["cwd"], str(output.resolve()))
                self.assertNotIn("shell", call.kwargs)
        self.assertEqual(Path.cwd(), before)

    def test_aspera_failure_status(self):
        with patch.object(aspera.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "ascp")), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(aspera.download_with_ascp("ftp.sra.ebi.ac.uk/vol1/a.gz", "key", "ascp", "."), 1)

    def test_synapse_recursive_and_failed_subfolder(self):
        client = Mock()
        client.getChildren.side_effect = [[
            {"id": "syn2", "name": "ok.gz", "type": "org.sagebionetworks.repo.model.FileEntity"},
            {"id": "syn3", "name": "folder", "type": "org.sagebionetworks.repo.model.Folder"},
        ], RuntimeError("access denied")]
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            stats = synapse.download_recursive(client, "syn1", directory)
        self.assertEqual((stats["files"], stats["failed"]), (1, 1))
        client.get.assert_called_once()

    def test_synapse_rejects_parent_path(self):
        client = Mock()
        client.getChildren.return_value = [{"id": "syn2", "name": "../outside", "type": "org.sagebionetworks.repo.model.Folder"}]
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            stats = synapse.download_recursive(client, "syn1", directory)
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(client.getChildren.call_count, 1)

    def test_synapse_missing_token_exits_nonzero(self):
        with patch.object(synapse, "get_auth_token", return_value=None), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(synapse.main(["--synapse-id", "syn1"]), 1)

    def test_legacy_downloads_manifest_versions(self):
        legacy = load("synapse_legacy", "synapse/legacy/download_synapse_legacy.py")
        client = Mock()
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.csv"
            manifest.write_text("ID,versionNumber\nsyn1,2\n", encoding="utf-8")
            client.get_download_list_manifest.return_value = str(manifest)
            with patch.dict(os.environ, {"SYNAPSE_AUTH_TOKEN": "test-only-placeholder"}), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(legacy.main(["--output", directory], client=client), 0)
            self.assertEqual(client.get.call_args.kwargs["version"], 2)
            client.remove_from_download_list.assert_not_called()


class NovogeneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "novogene"))
        import app
        cls.module = app
        cls.client = app.app.test_client()
        app.app.config["TESTING"] = True

    def test_pages_and_settings(self):
        for path in ("/", "/tasks", "/api/settings", "/api/settings/check-first-run", "/api/settings/system-info"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.assertEqual(self.module.Config.HOST, "127.0.0.1")

    def test_directory_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.client.post("/api/settings/validate-dir", json={"path": directory})
            self.assertTrue(result.json["valid"], result.json)

    def test_lnd_login_uses_stdin_and_no_shell(self):
        from scripts.download_manager import DownloadManager
        from scripts.email_parser import NovoGeneInfo
        manager = DownloadManager(sys.executable)
        info = NovoGeneInfo("oss://sample", "sample", 'test-only-"$value', "", "", "", "", "")
        with tempfile.TemporaryDirectory() as directory:
            task = manager.create_task(info, directory)
            with patch("scripts.download_manager.subprocess.run", return_value=Mock(returncode=0)) as run:
                self.assertTrue(manager._login(task))
            self.assertEqual(run.call_args.kwargs["input"], info.password + "\n")
            self.assertNotIn("shell", run.call_args.kwargs)
            self.assertNotIn(info.password, str(run.call_args.args))

    def test_listing_keeps_process_directory(self):
        from scripts.download_manager import DownloadManager
        from scripts.email_parser import NovoGeneInfo
        manager = DownloadManager(sys.executable)
        info = NovoGeneInfo("oss://sample", "sample", "test-only", "", "", "", "", "")
        before = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            task = manager.create_task(info, directory)
            with patch("scripts.download_manager.subprocess.run", return_value=Mock(returncode=0, stdout="sample.fastq.gz")):
                self.assertTrue(manager._list_files(task))
            self.assertEqual((Path(directory) / "file_list.txt").read_text(), "sample.fastq.gz")
        self.assertEqual(Path.cwd(), before)

    def test_md5_failure_is_reported(self):
        from scripts.download_manager import DownloadManager
        from scripts.email_parser import NovoGeneInfo
        manager = DownloadManager(sys.executable)
        info = NovoGeneInfo("oss://sample", "sample", "test-only", "", "", "", "", "", "")
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "checksums.md5").write_text("invalid checksum", encoding="utf-8")
            task = manager.create_task(info, directory)
            with patch("scripts.download_manager.subprocess.run", return_value=Mock(returncode=1)):
                self.assertFalse(manager._validate_files(task))


if __name__ == "__main__":
    unittest.main()
