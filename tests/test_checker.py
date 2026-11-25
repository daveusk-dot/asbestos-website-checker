"""Run with:  python -m unittest discover -s tests -v   (from the repo root)"""
import csv
import functools
import http.server
import os
import sys
import tempfile
import threading
import unittest

# Local test servers must not go through any proxy.
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import checker  # noqa: E402
import niche as niche_mod  # noqa: E402
from page import Page  # noqa: E402
from report import build_markdown  # noqa: E402

GOOD_PAGE = """<html><head><title>Asbestos Surveys Near Me - Birmingham</title>
<meta name="description" content="UKAS accredited asbestos surveys and testing across the West Midlands, quick turnaround."></head>
<body><h1>Asbestos surveys</h1><a href="tel:01214960000">Call</a>
<p>We offer asbestos removal. Note that we do surveys only in some areas. Proud to work with ARCA.</p>
<a href="/gone">Old page</a></body></html>"""

CUSTOM_NICHE = """
name: Test trade
required_mentions:
  - id: guarantee
    label: Guarantees
    terms: [guarantee]
    advice: Mention your guarantee.
"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class NicheTests(unittest.TestCase):
    def test_bundled_niches_load(self):
        self.assertIn("asbestos", niche_mod.list_niches())
        n = niche_mod.load_niche("asbestos")
        self.assertTrue(n.trust_marks.strong)
        self.assertEqual(n.required_mentions[0].id, "insurance")

    def test_template_is_valid_but_not_listed(self):
        niche_mod.load_niche(os.path.join(niche_mod.NICHE_DIR, "_template.yaml"))
        self.assertNotIn("_template", niche_mod.list_niches())

    def test_generic_default(self):
        n = niche_mod.load_niche(None)
        self.assertIsNone(n.trust_marks)
        self.assertEqual(n.required_mentions, [])

    def test_unknown_niche_and_bad_keys(self):
        with self.assertRaises(niche_mod.NicheConfigError):
            niche_mod.load_niche("does-not-exist")
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("name: x\ntrust_mark: {}\n")   # typo: should be trust_marks
        try:
            with self.assertRaises(niche_mod.NicheConfigError):
                niche_mod.load_niche(f.name)
        finally:
            os.unlink(f.name)


class PageTests(unittest.TestCase):
    def codes(self, html, niche=None):
        p = Page("https://example.co.uk/", "example.co.uk", niche=niche)
        p.analyze(html)
        return {i["code"] for i in p.issues}

    def test_asbestos_niche_flags_niche_issues(self):
        codes = self.codes(GOOD_PAGE, niche_mod.load_niche("asbestos"))
        self.assertIn("no_insurance", codes)
        self.assertIn("conflict_services", codes)
        self.assertIn("weak_accreditation", codes)   # "ARCA" alone is only a hint
        self.assertNotIn("no_contact", codes)        # tel: link found

    def test_generic_niche_has_no_niche_issues(self):
        codes = self.codes(GOOD_PAGE)
        self.assertFalse({"no_insurance", "conflict_services", "weak_accreditation", "no_accreditation"} & codes)

    def test_custom_niche(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(CUSTOM_NICHE)
        try:
            n = niche_mod.load_niche(f.name)
        finally:
            os.unlink(f.name)
        self.assertIn("no_guarantee", self.codes(GOOD_PAGE, n))
        self.assertNotIn("no_guarantee", self.codes(GOOD_PAGE.replace("</body>", "<p>5 year guarantee</p></body>"), n))


class ReportTests(unittest.TestCase):
    def test_report_uses_niche_advice_and_business_name(self):
        n = niche_mod.load_niche("asbestos")
        p = Page("https://example.co.uk/", "example.co.uk", niche=n)
        p.analyze(GOOD_PAGE)
        summary = {
            "start_url": "https://example.co.uk/", "business": "Acme Surveys", "date": "2026-11-25",
            "pages": [p.as_dict()], "errors": [], "site_issues": [],
        }
        md = build_markdown(summary)
        self.assertIn("**Business:** Acme Surveys", md)
        self.assertIn("Fully insured", md)               # advice came from the niche file
        self.assertIn("Insurance / public liability not mentioned", md)


class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(cls.tmp, "site"))
        with open(os.path.join(cls.tmp, "site", "index.html"), "w") as f:
            f.write(GOOD_PAGE)
        handler = functools.partial(QuietHandler, directory=os.path.join(cls.tmp, "site"))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_read_batch_file_formats(self):
        csv_path = os.path.join(self.tmp, "a.csv")
        with open(csv_path, "w") as f:
            f.write("url,name,niche,max_pages\nexample.co.uk,Acme,asbestos,5\n")
        txt_path = os.path.join(self.tmp, "b.txt")
        with open(txt_path, "w") as f:
            f.write("# comment\nhttps://one.co.uk\ntwo.co.uk\n")
        a = checker.read_batch_file(csv_path)
        self.assertEqual(a[0], {"url": "https://example.co.uk", "name": "Acme", "niche": "asbestos", "max_pages": 5})
        b = checker.read_batch_file(txt_path)
        self.assertEqual([s["url"] for s in b], ["https://one.co.uk", "https://two.co.uk"])

    def test_batch_run_continues_after_failures(self):
        batch = os.path.join(self.tmp, "sites.csv")
        with open(batch, "w") as f:
            f.write("url,name,niche\n")
            f.write(f"http://127.0.0.1:{self.port}/,Good Co,asbestos\n")
            f.write("http://127.0.0.1:1/,Dead Co,asbestos\n")
            f.write(f"http://127.0.0.1:{self.port}/,Bad Niche Co,no-such-niche\n")
        out = os.path.join(self.tmp, "out")
        rows = checker.run_batch(batch, out, delay=0, site_delay=0, respect_robots=False)

        self.assertEqual([r["status"] for r in rows], ["ok", "unreachable", "error"])
        self.assertIn("not found", rows[2]["error"])
        report = os.path.join(out, rows[0]["report"])
        self.assertTrue(os.path.isfile(report))
        self.assertTrue(os.path.isfile(os.path.join(os.path.dirname(report), "audit.json")))
        with open(report) as f:
            self.assertIn("**Business:** Good Co", f.read())
        with open(os.path.join(out, "summary.csv"), newline="") as f:
            saved = list(csv.DictReader(f))
        self.assertEqual(len(saved), 3)
        self.assertIn("no_insurance", saved[0]["top_issues"])


if __name__ == "__main__":
    unittest.main()
