import unittest
from HtmlTestRunner import HTMLTestRunner

if __name__ == "__main__":
    # Załaduj testy
    suite = unittest.TestLoader().discover('.', pattern="test_*.py")

    # Wygeneruj raport HTML
    runner = HTMLTestRunner(output='reports', report_name="TestReport")
    runner.run(suite)